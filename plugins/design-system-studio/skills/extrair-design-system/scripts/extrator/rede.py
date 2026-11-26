"""Rede: valida a URL, recusa endereços que não são públicos e baixa com limite de bytes e de tempo.

Cada pedido (página, folhas, @import, logo, ícones e cada redirecionamento) passa por aqui.
O endereço é conferido na resolução do nome e a conexão vai para o IP conferido, o que fecha
a porta para o DNS rebinding.
"""

from __future__ import annotations

import http.client
import ipaddress
import socket
import ssl
import time
import urllib.parse
from dataclasses import dataclass

from . import USER_AGENT

ESQUEMAS = ("http", "https")
PORTAS_PADRAO = {"http": 80, "https": 443}
REDIRECIONAMENTOS = (301, 302, 303, 307, 308)


class EnderecoRecusado(ValueError):
    """Esquema fora de http e https, ou endereço local, privado ou reservado."""


class FalhaDeRede(RuntimeError):
    """O recurso não veio: rede, status de erro ou resposta inválida."""


class LimiteExcedido(FalhaDeRede):
    """Passou do limite de bytes ou de tempo."""


@dataclass(frozen=True)
class Limites:
    bytes_por_arquivo: int = 2_000_000
    bytes_total: int = 12_000_000
    tempo: float = 15.0
    redirecionamentos: int = 5


@dataclass(frozen=True)
class Resposta:
    url: str
    status: int
    tipo: str
    charset: str | None
    corpo: bytes

    def texto(self) -> str:
        return self.corpo.decode(self.charset or "utf-8", errors="replace")


def validar_url(url: str) -> urllib.parse.SplitResult:
    """Confere o esquema e o formato. O endereço em si é conferido na resolução (`resolver`)."""
    partes = urllib.parse.urlsplit((url or "").strip())
    if partes.scheme.lower() not in ESQUEMAS:
        raise EnderecoRecusado(f"só http e https: {url!r}")
    if not partes.hostname:
        raise EnderecoRecusado(f"URL sem endereço: {url!r}")
    if partes.username or partes.password:
        raise EnderecoRecusado("URL com usuário ou senha não é aceita")
    try:
        _ = partes.port
    except ValueError as erro:
        raise EnderecoRecusado(f"porta inválida em {url!r}") from erro
    return partes


def conferir_ip(ip: str, permitir_local: bool = False) -> None:
    """Recusa tudo que não é endereço público. Com `permitir_local`, aceita só o loopback."""
    try:
        endereco = ipaddress.ip_address(ip.split("%", 1)[0])
    except ValueError as erro:
        raise EnderecoRecusado(f"endereço inválido: {ip}") from erro
    if isinstance(endereco, ipaddress.IPv6Address) and endereco.ipv4_mapped:
        endereco = endereco.ipv4_mapped
    if permitir_local and endereco.is_loopback:
        return
    if not endereco.is_global or endereco.is_multicast:
        raise EnderecoRecusado(f"endereço local, privado ou reservado recusado: {endereco}")


def resolver(host: str, porta: int, permitir_local: bool = False) -> list[str]:
    try:
        infos = socket.getaddrinfo(host, porta, type=socket.SOCK_STREAM)
    except (socket.gaierror, UnicodeError) as erro:
        raise FalhaDeRede(f"não foi possível resolver {host}: {erro}") from erro
    ips = sorted({info[4][0] for info in infos})
    if not ips:
        raise FalhaDeRede(f"{host} não tem endereço")
    for ip in ips:
        conferir_ip(ip, permitir_local)
    return ips


class _Conexao(http.client.HTTPConnection):
    """Conexão para um IP já conferido, com o nome original no Host e no TLS (SNI e certificado)."""

    def __init__(self, host: str, porta: int, ip: str, tempo: float, tls: bool, permitir_local: bool):
        super().__init__(host, porta, timeout=tempo)
        self._ip, self._tls, self._permitir_local = ip, tls, permitir_local

    def connect(self) -> None:
        sock = socket.create_connection((self._ip, self.port), self.timeout)
        conferir_ip(sock.getpeername()[0], self._permitir_local)
        if self._tls:
            sock = ssl.create_default_context().wrap_socket(sock, server_hostname=self.host)
        self.sock = sock


def _tipo_e_charset(cabecalho: str | None) -> tuple[str, str | None]:
    if not cabecalho:
        return "", None
    tipo, _, resto = cabecalho.partition(";")
    charset = None
    for parametro in resto.split(";"):
        nome, _, valor = parametro.strip().partition("=")
        if nome.lower() == "charset" and valor:
            charset = valor.strip().strip("\"'")
    return tipo.strip().lower(), charset


class Cliente:
    """Baixa recursos com os limites da sessão. `total` soma os bytes de todos os pedidos."""

    def __init__(self, limites: Limites | None = None, permitir_local: bool = False):
        self.limites = limites or Limites()
        self.permitir_local = permitir_local
        self.total = 0

    def baixar(self, url: str, aceitar: str = "*/*", limite: int | None = None) -> Resposta:
        limite = min(limite or self.limites.bytes_por_arquivo, self.limites.bytes_por_arquivo)
        prazo = time.monotonic() + self.limites.tempo
        atual = url
        for _ in range(self.limites.redirecionamentos + 1):
            status, cabecalhos, corpo = self._pedido(atual, aceitar, limite, prazo)
            if status in REDIRECIONAMENTOS and cabecalhos.get("location"):
                atual = urllib.parse.urljoin(atual, cabecalhos["location"])
                continue
            if not 200 <= status < 300:
                raise FalhaDeRede(f"HTTP {status} em {atual}")
            self.total += len(corpo)
            if self.total > self.limites.bytes_total:
                raise LimiteExcedido(f"passou do limite total de {self.limites.bytes_total} bytes da extração")
            tipo, charset = _tipo_e_charset(cabecalhos.get("content-type"))
            return Resposta(atual, status, tipo, charset, corpo)
        raise FalhaDeRede(f"mais de {self.limites.redirecionamentos} redirecionamentos a partir de {url}")

    def _pedido(self, url: str, aceitar: str, limite: int, prazo: float) -> tuple[int, dict[str, str], bytes]:
        partes = validar_url(url)
        esquema = partes.scheme.lower()
        porta = partes.port or PORTAS_PADRAO[esquema]
        ip = resolver(partes.hostname, porta, self.permitir_local)[0]
        caminho = urllib.parse.urlunsplit(("", "", partes.path or "/", partes.query, ""))
        restante = prazo - time.monotonic()
        if restante <= 0:
            raise LimiteExcedido(f"passou do limite de tempo de {self.limites.tempo:g} s em {url}")
        conexao = _Conexao(partes.hostname, porta, ip, restante, esquema == "https", self.permitir_local)
        try:
            conexao.request(
                "GET",
                caminho,
                headers={"User-Agent": USER_AGENT, "Accept": aceitar, "Accept-Encoding": "identity"},
            )
            resposta = conexao.getresponse()
            cabecalhos = {nome.lower(): valor for nome, valor in resposta.getheaders()}
            if resposta.status in REDIRECIONAMENTOS:
                return resposta.status, cabecalhos, b""
            declarado = cabecalhos.get("content-length", "")
            if declarado.isdigit() and int(declarado) > limite:
                raise LimiteExcedido(f"{url} tem {declarado} bytes, acima do limite de {limite}")
            corpo = bytearray()
            while True:
                restante = prazo - time.monotonic()
                if restante <= 0:
                    raise LimiteExcedido(f"passou do limite de tempo de {self.limites.tempo:g} s em {url}")
                if conexao.sock is not None:
                    conexao.sock.settimeout(restante)
                pedaco = resposta.read1(65536)
                if not pedaco:
                    break
                corpo.extend(pedaco)
                if len(corpo) > limite:
                    raise LimiteExcedido(f"{url} passou do limite de {limite} bytes")
            return resposta.status, cabecalhos, bytes(corpo)
        except (TimeoutError, socket.timeout) as erro:
            raise LimiteExcedido(f"passou do limite de tempo de {self.limites.tempo:g} s em {url}") from erro
        except (EnderecoRecusado, FalhaDeRede):
            raise
        except (OSError, http.client.HTTPException, ssl.SSLError) as erro:
            raise FalhaDeRede(f"falha ao baixar {url}: {erro}") from erro
        finally:
            conexao.close()
