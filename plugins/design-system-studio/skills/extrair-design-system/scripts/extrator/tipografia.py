"""Tipografia: famílias (font-family, @font-face e Google Fonts), papéis, escala de tamanhos e pesos."""

from __future__ import annotations

import re
import urllib.parse
from collections import Counter
from dataclasses import dataclass, field

from .cores import resolver_var, usos
from .folhas import Regra
from .pagina import familias_google

GENERICAS = {
    "serif", "sans-serif", "monospace", "cursive", "fantasy", "system-ui", "ui-serif", "ui-sans-serif",
    "ui-monospace", "ui-rounded", "math", "emoji", "fangsong", "inherit", "initial", "unset", "revert",
}
SISTEMA = {
    "-apple-system", "blinkmacsystemfont", "segoe ui", "helvetica neue", "helvetica", "arial", "roboto",
    "noto sans", "ubuntu", "cantarell", "oxygen", "fira sans", "droid sans", "liberation sans",
    "apple color emoji", "segoe ui emoji", "segoe ui symbol", "noto color emoji", "menlo", "monaco",
    "consolas", "courier new", "courier", "sf mono", "sfmono-regular", "liberation mono", "georgia",
    "times new roman", "times",
}
TAMANHO_FONT = re.compile(r"(?:^|\s)(\d*\.?\d+(?:px|rem|em|pt|%)|[\w-]+\([^)]*\))(?:/\S+)?\s+(.+)$")
TITULOS = {"h1", "h2", "h3"}
MONO = {"code", "pre", "kbd", "samp"}
PILHA_MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"
PILHA_SISTEMA = "system-ui, -apple-system, \"Segoe UI\", Roboto, sans-serif"


@dataclass
class Familia:
    nome: str
    usos: int = 0
    pilhas: Counter = field(default_factory=Counter)
    origens: set[str] = field(default_factory=set)

    @property
    def pilha(self) -> str:
        if self.pilhas:
            return sorted(self.pilhas.items(), key=lambda t: (-t[1], t[0]))[0][0]
        generica = "monospace" if "mono" in self.nome.lower() else "sans-serif"
        return f'"{self.nome}", {generica}'


@dataclass(frozen=True)
class PapelFonte:
    familia: str
    pilha: str
    motivo: str


@dataclass
class Tipografia:
    familias: list[Familia]
    papeis: dict[str, PapelFonte]
    tamanhos: list[tuple[str, int]]
    fluidos: list[tuple[str, int]]
    pesos: list[tuple[str, int]]
    font_faces: list[dict[str, str]]
    google_fonts: list[str]
    google_fonts_urls: list[str]


def lista_de_familias(valor: str) -> list[str]:
    nomes, atual, aspas = [], [], ""
    for c in valor:
        if aspas:
            if c == aspas:
                aspas = ""
            else:
                atual.append(c)
        elif c in "\"'":
            aspas = c
        elif c == ",":
            nomes.append("".join(atual))
            atual = []
        else:
            atual.append(c)
    nomes.append("".join(atual))
    return [" ".join(n.split()) for n in nomes if n.strip()]


def _px(valor: str) -> float | None:
    m = re.fullmatch(r"(\d*\.?\d+)(px|rem|em|pt)", valor.strip().lower())
    if not m:
        return None
    numero = float(m.group(1))
    return {"px": numero, "rem": numero * 16, "em": numero * 16, "pt": numero * 4 / 3}[m.group(2)]


def formatar_px(px: float) -> str:
    return f"{int(px)}px" if px == int(px) else f"{px:.1f}px"


def _subjeitos(seletor: str) -> list[str]:
    return [re.split(r"\s*[>+~]\s*|\s+", p.strip())[-1].lower() for p in seletor.split(",") if p.strip()]


def _tem(seletor: str, tags: set[str], classes: tuple[str, ...]) -> bool:
    for sujeito in _subjeitos(seletor):
        tag = re.match(r"[a-z][\w-]*", sujeito)
        if tag and tag.group(0) in tags:
            return True
        if any(any(k in c for k in classes) for c in re.findall(r"\.([\w-]+)", sujeito)):
            return True
    return False


def analisar(regras: list[Regra], fontes_css: list[dict[str, str]], google: list[str], mapa: dict[str, str]) -> Tipografia:
    familias: dict[str, Familia] = {}
    declaradas: set[str] = set()

    def familia(nome: str) -> Familia:
        chave = nome.lower()
        if chave not in familias:
            familias[chave] = Familia(nome)
        return familias[chave]

    faces: list[dict[str, str]] = []
    for face in fontes_css:
        nomes = lista_de_familias(face.get("font-family", ""))
        if not nomes:
            continue
        familia(nomes[0]).origens.add("@font-face")
        declaradas.add(nomes[0].lower())
        faces.append(_face(face, nomes[0]))
    google_familias: list[str] = []
    for url in google:
        for nome in familias_google(url):
            familia(nome).origens.add("Google Fonts")
            declaradas.add(nome.lower())
            if nome not in google_familias:
                google_familias.append(nome)

    def principal(pilha: list[str]) -> str | None:
        for nome in pilha:
            chave = nome.lower()
            if chave in declaradas or (chave not in GENERICAS and chave not in SISTEMA):
                return nome
        return None

    tamanhos: Counter[str] = Counter()
    fluidos: Counter[str] = Counter()
    pesos: Counter[str] = Counter()
    papel_texto = papel_titulo = papel_mono = None

    for regra in regras:
        for propriedade, valor in regra.declaracoes:
            if propriedade.startswith("--"):
                continue
            valor = resolver_var(valor, mapa).replace("!important", "").strip()
            pilha_txt = None
            if propriedade == "font-family":
                pilha_txt = valor
            elif propriedade == "font":
                m = TAMANHO_FONT.search(valor)
                if m:
                    pilha_txt = m.group(2)
                    _tamanho(m.group(1), tamanhos, fluidos)
            elif propriedade == "font-size":
                _tamanho(valor, tamanhos, fluidos)
            elif propriedade == "font-weight" and re.fullmatch(r"\d{3}|bold|bolder|normal|lighter", valor):
                pesos[valor] += 1
            if not pilha_txt:
                continue
            pilha = lista_de_familias(pilha_txt)
            nome = principal(pilha)
            if nome is None:
                if pilha and pilha[0].lower() not in ("inherit", "initial", "unset", "revert"):
                    sistema = familia("fontes do sistema")
                    sistema.usos += 1
                    sistema.pilhas[pilha_txt] += 1
                    sistema.origens.add("font-family")
                    nome = "fontes do sistema"
                else:
                    continue
            else:
                f = familia(nome)
                f.usos += 1
                f.pilhas[", ".join(_citar(n) for n in pilha)] += 1
                f.origens.add("font-family")
            seletor = regra.seletor
            if any(p.strip().lower() in ("html", "body", ":root") for p in seletor.split(",")) and not regra.contexto:
                papel_texto = (nome, seletor)
            elif _tem(seletor, TITULOS, ("title", "titulo", "heading", "display")) and papel_titulo is None:
                papel_titulo = (nome, seletor)
            if (_tem(seletor, MONO, ("mono", "code")) or "monospace" in pilha_txt) and papel_mono is None:
                papel_mono = (nome, seletor)

    ordenadas = sorted(familias.values(), key=lambda f: (-f.usos, f.nome.lower()))
    papeis = _papeis(familias, ordenadas, papel_texto, papel_titulo, papel_mono)
    escala = sorted(tamanhos.items(), key=lambda t: (-t[1], _px(t[0]) or 0))[:10]
    escala.sort(key=lambda t: _px(t[0]) or 0)
    return Tipografia(
        ordenadas,
        papeis,
        escala,
        sorted(fluidos.items(), key=lambda t: (-t[1], t[0]))[:5],
        sorted(pesos.items(), key=lambda t: (-t[1], t[0])),
        faces,
        google_familias,
        list(dict.fromkeys(google)),
    )


def _citar(nome: str) -> str:
    return nome if nome.lower() in GENERICAS or re.fullmatch(r"[A-Za-z-]+", nome) else f'"{nome}"'


def _tamanho(valor: str, tamanhos: Counter, fluidos: Counter) -> None:
    valor = valor.strip()
    px = _px(valor)
    if px is not None and px > 0:
        tamanhos[formatar_px(px)] += 1
    elif re.match(r"(clamp|min|max|calc)\(", valor):
        fluidos[" ".join(valor.split())] += 1


def _face(face: dict[str, str], nome: str) -> dict[str, str]:
    base = face.get("_base", "")
    src = face.get("src", "")
    if base and base != "inline":
        src = re.sub(
            r"""url\(\s*(['"]?)(.*?)\1\s*\)""",
            lambda m: m.group(0) if m.group(2).startswith("data:") else f'url("{urllib.parse.urljoin(base, m.group(2))}")',
            src,
        )
    return {
        "font-family": f'"{nome}"',
        "src": src,
        "font-weight": face.get("font-weight", ""),
        "font-style": face.get("font-style", ""),
        "font-display": face.get("font-display", ""),
    }


def _papeis(familias, ordenadas, texto, titulo, mono) -> dict[str, PapelFonte]:
    papeis: dict[str, PapelFonte] = {}

    def papel(nome: str, motivo: str) -> PapelFonte:
        f = familias[nome.lower()]
        return PapelFonte(f.nome, f.pilha, motivo)

    if texto:
        papeis["texto"] = papel(texto[0], f"`font-family` do `{texto[1]}`")
    elif ordenadas and ordenadas[0].usos:
        papeis["texto"] = papel(ordenadas[0].nome, f"família mais usada ({usos(ordenadas[0].usos)})")
    else:
        papeis["texto"] = PapelFonte("fontes do sistema", PILHA_SISTEMA, "nenhuma família declarada")
    if titulo and titulo[0] != papeis["texto"].familia:
        papeis["titulos"] = papel(titulo[0], f"`font-family` de `{titulo[1]}`")
    else:
        papeis["titulos"] = PapelFonte(papeis["texto"].familia, papeis["texto"].pilha, "mesma família do texto")
    if mono:
        papeis["mono"] = papel(mono[0], f"`font-family` de `{mono[1]}`")
    else:
        papeis["mono"] = PapelFonte("fontes mono do sistema", PILHA_MONO, "nenhuma fonte mono declarada")
    return papeis
