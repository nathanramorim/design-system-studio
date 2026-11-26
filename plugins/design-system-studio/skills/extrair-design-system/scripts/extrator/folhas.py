"""Folhas de estilo: lê o CSS em regras e segue os @import, dentro dos limites da sessão."""

from __future__ import annotations

import re
import urllib.parse
from dataclasses import dataclass, field

from .pagina import GOOGLE_FONTS, Pagina
from .rede import Cliente, EnderecoRecusado, FalhaDeRede

MAX_FOLHAS = 25
MAX_PROFUNDIDADE = 4
AGRUPADORAS = ("@media", "@supports", "@layer", "@container", "@document", "@scope")
IMPORT = re.compile(r"""@import\s+(?:url\(\s*(['"]?)(.*?)\1\s*\)|(['"])(.*?)\3)""", re.I | re.S)


@dataclass(frozen=True)
class Regra:
    seletor: str
    declaracoes: tuple[tuple[str, str], ...]
    contexto: tuple[str, ...]
    origem: str


@dataclass
class Folhas:
    regras: list[Regra] = field(default_factory=list)
    fontes: list[dict[str, str]] = field(default_factory=list)
    google_fonts: list[str] = field(default_factory=list)
    baixadas: list[str] = field(default_factory=list)
    por_import: int = 0
    avisos: list[str] = field(default_factory=list)


def sem_comentarios(css: str) -> str:
    saida, i, aspas = [], 0, ""
    while i < len(css):
        c = css[i]
        if aspas:
            saida.append(c)
            if c == "\\" and i + 1 < len(css):
                saida.append(css[i + 1])
                i += 1
            elif c == aspas:
                aspas = ""
        elif c in "\"'":
            aspas = c
            saida.append(c)
        elif css.startswith("/*", i):
            fim = css.find("*/", i + 2)
            i = len(css) if fim < 0 else fim + 2
            saida.append(" ")
            continue
        else:
            saida.append(c)
        i += 1
    return "".join(saida)


def blocos(css: str) -> list[tuple[str, str | None]]:
    """Divide no nível de cima: (prelúdio, corpo) para blocos e (texto, None) para declarações."""
    itens: list[tuple[str, str | None]] = []
    i, inicio, parenteses, aspas = 0, 0, 0, ""
    while i < len(css):
        c = css[i]
        if aspas:
            if c == "\\":
                i += 1
            elif c == aspas:
                aspas = ""
        elif c in "\"'":
            aspas = c
        elif c == "(":
            parenteses += 1
        elif c == ")":
            parenteses = max(0, parenteses - 1)
        elif c == ";" and parenteses == 0:
            texto = css[inicio:i].strip()
            if texto:
                itens.append((texto, None))
            inicio = i + 1
        elif c == "{" and parenteses == 0:
            fim = _fecha(css, i)
            itens.append((css[inicio:i].strip(), css[i + 1 : fim]))
            i = fim
            inicio = fim + 1
        i += 1
    resto = css[inicio:].strip()
    if resto:
        itens.append((resto, None))
    return itens


def _fecha(css: str, abre: int) -> int:
    profundidade, aspas, i = 0, "", abre
    while i < len(css):
        c = css[i]
        if aspas:
            if c == "\\":
                i += 1
            elif c == aspas:
                aspas = ""
        elif c in "\"'":
            aspas = c
        elif c == "{":
            profundidade += 1
        elif c == "}":
            profundidade -= 1
            if profundidade == 0:
                return i
        i += 1
    return len(css)


def declaracao(texto: str) -> tuple[str, str] | None:
    nome, sep, valor = texto.partition(":")
    nome, valor = nome.strip(), valor.strip()
    if not sep or not nome or not valor or not re.fullmatch(r"-?-?[A-Za-z_][\w-]*", nome):
        return None
    return (nome if nome.startswith("--") else nome.lower()), valor


def _aninhado(pai: str, filho: str) -> str:
    base = f":is({pai})" if "," in pai else pai
    if "&" in filho:
        return filho.replace("&", base)
    return ", ".join(f"{base} {parte.strip()}" for parte in filho.split(","))


def ler(css: str, origem: str) -> tuple[list[Regra], list[dict[str, str]], list[str]]:
    """Regras, @font-face e endereços dos @import (como escritos) de uma folha."""
    regras: list[Regra] = []
    fontes: list[dict[str, str]] = []
    imports: list[str] = []
    _ler_nivel(sem_comentarios(css), (), origem, regras, fontes, imports, seletor_pai="")
    return regras, fontes, imports


def _ler_nivel(css, contexto, origem, regras, fontes, imports, seletor_pai):
    itens = blocos(css)
    if seletor_pai:
        proprias = tuple(par for texto, corpo in itens if corpo is None and (par := declaracao(texto)))
        if proprias:
            regras.append(Regra(seletor_pai, proprias, contexto, origem))
    for prelude, corpo in itens:
        cabeca = " ".join(prelude.split())
        minuscula = cabeca.lower()
        if corpo is None:
            if not seletor_pai and minuscula.startswith("@import"):
                achado = IMPORT.match(cabeca)
                if achado:
                    imports.append(achado.group(2) or achado.group(4) or "")
            continue
        if minuscula.startswith("@font-face"):
            face = {}
            for texto, _ in blocos(corpo):
                par = declaracao(texto)
                if par:
                    face[par[0]] = par[1]
            fontes.append(face)
        elif minuscula.startswith(AGRUPADORAS):
            novo = (*contexto, cabeca)
            _ler_nivel(corpo, novo, origem, regras, fontes, imports, seletor_pai)
        elif minuscula.startswith("@"):
            continue
        else:
            seletor = _aninhado(seletor_pai, cabeca) if seletor_pai else cabeca
            _ler_nivel(corpo, contexto, origem, regras, fontes, imports, seletor_pai=seletor)


def coletar(cliente: Cliente, pagina: Pagina) -> Folhas:
    """Baixa as folhas ligadas e as dos @import em ordem de cascata (o importado vem antes)."""
    resultado = Folhas(google_fonts=list(pagina.google_fonts))
    vistas: set[str] = set()

    def processar(css: str, origem: str, base: str, profundidade: int) -> None:
        regras, fontes, imports = ler(css, origem)
        for endereco in imports:
            alvo = urllib.parse.urljoin(base, endereco)
            if urllib.parse.urlsplit(alvo).hostname in GOOGLE_FONTS:
                resultado.google_fonts.append(alvo)
                continue
            if baixar(alvo, profundidade + 1):
                resultado.por_import += 1
        resultado.regras.extend(regras)
        resultado.fontes.extend({**f, "_base": base} for f in fontes)

    def baixar(url: str, profundidade: int) -> bool:
        if url in vistas:
            return False
        vistas.add(url)
        if profundidade > MAX_PROFUNDIDADE:
            resultado.avisos.append(f"{url} ignorada: @import com mais de {MAX_PROFUNDIDADE} níveis")
            return False
        if len(resultado.baixadas) >= MAX_FOLHAS:
            resultado.avisos.append(f"{url} ignorada: mais de {MAX_FOLHAS} folhas")
            return False
        try:
            resposta = cliente.baixar(url, aceitar="text/css,*/*;q=0.1")
        except (EnderecoRecusado, FalhaDeRede) as erro:
            resultado.avisos.append(f"folha ignorada: {erro}")
            return False
        if resposta.tipo in ("text/html", "application/xhtml+xml"):
            resultado.avisos.append(f"{url} ignorada: veio HTML, não CSS")
            return False
        resultado.baixadas.append(resposta.url)
        processar(resposta.texto(), resposta.url, resposta.url, profundidade)
        return True

    for tipo, valor in pagina.folhas:
        if tipo == "link":
            baixar(valor, 0)
        else:
            processar(valor, "inline", pagina.url, 0)
    return resultado
