"""Marca: acha e baixa o logo, o favicon, os ícones e a og:image para `assets/`."""

from __future__ import annotations

import base64
import urllib.parse
from dataclasses import dataclass
from pathlib import Path

from .pagina import Pagina
from .rede import Cliente, EnderecoRecusado, FalhaDeRede
from .svg import higienizar

LIMITE_IMAGEM = 2_000_000
MAX_ICONES = 4
PADROES = ("logo.*", "favicon.*", "icone-*.*", "og-imagem.*", "captura.png")


class ImagemInvalida(ValueError):
    """O recurso não é uma imagem que dá para guardar."""


@dataclass(frozen=True)
class Ativo:
    papel: str
    arquivo: str
    origem: str
    motivo: str


def tipo_da_imagem(dados: bytes) -> str | None:
    cabeca = dados[:512].lstrip()
    if dados.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if dados.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if dados.startswith((b"GIF87a", b"GIF89a")):
        return "gif"
    if dados[:4] == b"RIFF" and dados[8:12] == b"WEBP":
        return "webp"
    if dados[:4] == b"\x00\x00\x01\x00":
        return "ico"
    if dados[4:12] in (b"ftypavif", b"ftypavis"):
        return "avif"
    if cabeca.startswith((b"<svg", b"<?xml", b"\xef\xbb\xbf<")) and b"<svg" in dados[:4096]:
        return "svg"
    return None


def _dados_de_uri(uri: str) -> bytes:
    cabeca, _, corpo = uri.partition(",")
    if ";base64" in cabeca.lower():
        return base64.b64decode(corpo, validate=False)
    return urllib.parse.unquote_to_bytes(corpo)


def _gravar(dados: bytes, pasta: Path, nome: str) -> str:
    tipo = tipo_da_imagem(dados)
    if tipo is None:
        raise ImagemInvalida("não é PNG, JPG, GIF, WebP, ICO, AVIF nem SVG")
    if tipo == "svg":
        limpo = higienizar(dados.decode("utf-8", errors="replace"))
        if limpo is None:
            raise ImagemInvalida("SVG inválido ou com DOCTYPE")
        dados = limpo.encode("utf-8")
    pasta.mkdir(parents=True, exist_ok=True)
    arquivo = f"{nome}.{tipo}"
    (pasta / arquivo).write_bytes(dados)
    return arquivo


def _buscar(cliente: Cliente, url: str) -> bytes:
    if url.startswith("data:"):
        dados = _dados_de_uri(url)
        if len(dados) > LIMITE_IMAGEM:
            raise ImagemInvalida(f"imagem embutida acima de {LIMITE_IMAGEM} bytes")
        return dados
    return cliente.baixar(url, aceitar="image/*,*/*;q=0.5", limite=LIMITE_IMAGEM).corpo


def coletar(cliente: Cliente, pagina: Pagina, pasta: Path, avisos: list[str]) -> list[Ativo]:
    ativos: list[Ativo] = []

    def tentar(url: str, nome: str, papel: str, motivo: str) -> Ativo | None:
        try:
            arquivo = _gravar(_buscar(cliente, url), pasta, nome)
        except (EnderecoRecusado, FalhaDeRede, ImagemInvalida, ValueError) as erro:
            avisos.append(f"{papel} ({_curta(url)}) não veio: {erro}")
            return None
        ativo = Ativo(papel, arquivo, _curta(url), motivo)
        ativos.append(ativo)
        return ativo

    og = pagina.meta.get("og:image", "")
    og_ativo = tentar(pagina.absoluta(og), "og-imagem", "og:image", "meta og:image") if og else None

    favicons = [i for i in pagina.icones if i.rel in ("icon", "shortcut icon")]
    favicons.sort(key=lambda i: (not (i.tipo == "image/svg+xml" or i.url.lower().endswith(".svg")), -i.tamanho))
    escolhido = None
    for icone in favicons:
        escolhido = tentar(icone.url, "favicon", "favicon", f'link rel="{icone.rel}"')
        if escolhido:
            break
    if not escolhido:
        reserva = urllib.parse.urljoin(pagina.url, "/favicon.ico")
        if not tentar(reserva, "favicon", "favicon", "/favicon.ico (sem link rel=icon)"):
            avisos.append("favicon não encontrado")

    usados = {escolhido and escolhido.origem}
    extras = [i for i in pagina.icones if _curta(i.url) not in usados]
    for n, icone in enumerate(extras[:MAX_ICONES], start=1):
        tentar(icone.url, f"icone-{n}", "ícone", f'link rel="{icone.rel}"')

    if not _logo(pagina, pasta, ativos, avisos, tentar):
        if og_ativo:
            ativos.append(Ativo("logo", og_ativo.arquivo, og_ativo.origem, "og:image (reserva: nenhum logo na página)"))
        else:
            avisos.append("logo não encontrado: nenhuma imagem ou SVG com 'logo' e nenhum SVG no cabeçalho")
    return ativos


def _logo(pagina: Pagina, pasta: Path, ativos: list[Ativo], avisos: list[str], tentar) -> bool:
    candidatos: list[tuple[str, object, str]] = []
    candidatos += [("img", i, "imagem com 'logo' no cabeçalho") for i in pagina.imagens if i.dica_logo and i.no_cabecalho]
    candidatos += [("svg", s, "SVG inline com 'logo'") for s in pagina.svgs if s[2]]
    candidatos += [("img", i, "imagem com 'logo' no nome, no alt ou na classe") for i in pagina.imagens if i.dica_logo]
    candidatos += [("svg", s, "primeiro SVG inline do cabeçalho") for s in pagina.svgs if s[1]]
    for tipo, item, motivo in candidatos:
        if tipo == "img":
            if tentar(item.url, "logo", "logo", motivo):
                return True
            continue
        try:
            arquivo = _gravar(item[0].encode("utf-8"), pasta, "logo")
        except ImagemInvalida as erro:
            avisos.append(f"logo (SVG inline) não veio: {erro}")
            continue
        ativos.append(Ativo("logo", arquivo, "SVG inline da página", motivo))
        return True
    return False


def _curta(url: str) -> str:
    return url if not url.startswith("data:") else url[:40] + "..."


def limpar(pasta: Path) -> None:
    """Apaga só os arquivos que o próprio extrator grava em `assets/`."""
    if not pasta.is_dir():
        return
    for padrao in PADROES:
        for arquivo in pasta.glob(padrao):
            if arquivo.is_file():
                arquivo.unlink()
