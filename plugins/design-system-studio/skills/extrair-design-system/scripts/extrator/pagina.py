"""Página: lê o HTML (sem executar script) e devolve o que interessa ao design system."""

from __future__ import annotations

import re
import urllib.parse
from dataclasses import dataclass, field
from html.parser import HTMLParser
from xml.sax.saxutils import escape

VAZIAS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
RELS_ICONE = {"icon", "shortcut icon", "apple-touch-icon", "apple-touch-icon-precomposed", "mask-icon"}
GOOGLE_FONTS = {"fonts.googleapis.com"}


@dataclass(frozen=True)
class Imagem:
    url: str
    alt: str
    dica_logo: bool
    no_cabecalho: bool


@dataclass(frozen=True)
class Icone:
    url: str
    rel: str
    tamanho: int
    tipo: str


@dataclass
class Pagina:
    url: str
    titulo: str = ""
    meta: dict[str, str] = field(default_factory=dict)
    folhas: list[tuple[str, str]] = field(default_factory=list)
    estilos_inline: list[str] = field(default_factory=list)
    icones: list[Icone] = field(default_factory=list)
    imagens: list[Imagem] = field(default_factory=list)
    svgs: list[tuple[str, bool, bool]] = field(default_factory=list)
    google_fonts: list[str] = field(default_factory=list)
    elementos: list[tuple[str, tuple[str, ...]]] = field(default_factory=list)

    def absoluta(self, endereco: str) -> str:
        return urllib.parse.urljoin(self.url, endereco.strip())


def _tem_dica(valor: str, palavras: tuple[str, ...]) -> bool:
    valor = valor.lower()
    return any(p in valor for p in palavras)


def _tamanho(sizes: str) -> int:
    maior = 0
    for parte in sizes.lower().split():
        if parte == "any":
            return 10_000
        largura, _, _ = parte.partition("x")
        if largura.isdigit():
            maior = max(maior, int(largura))
    return maior


class _Leitor(HTMLParser):
    def __init__(self, pagina: Pagina):
        super().__init__(convert_charrefs=True)
        self.p = pagina
        self.pilha: list[tuple[str, bool, bool]] = []
        self._estilo: list[str] | None = None
        self._titulo: list[str] | None = None
        self._svg: list[str] | None = None
        self._svg_nomes: list[str] = []
        self._svg_contexto: tuple[bool, bool] = (False, False)
        self._descartar = 0

    @property
    def no_cabecalho(self) -> bool:
        return any(c for _, c, _ in self.pilha)

    @property
    def dica_logo(self) -> bool:
        return any(d for _, _, d in self.pilha)

    def handle_starttag(self, tag, attrs):
        self._abrir(tag, attrs, fecha=False)

    def handle_startendtag(self, tag, attrs):
        self._abrir(tag, attrs, fecha=True)

    def _abrir(self, tag, attrs, fecha):
        a = {k.lower(): (v or "") for k, v in attrs}
        if self._svg is not None:
            self._gravar_svg_abertura(tag, a, fecha)
            return
        classes = tuple(a.get("class", "").split())
        rotulo = " ".join((a.get("id", ""), a.get("class", ""), a.get("aria-label", "")))
        cabecalho = tag == "header" or a.get("role") == "banner" or _tem_dica(rotulo, ("header", "navbar", "topbar"))
        logo = _tem_dica(rotulo, ("logo", "brand", "marca"))
        if len(self.p.elementos) < 4000 and tag not in ("html", "head", "meta", "link", "script", "style"):
            self.p.elementos.append((tag, classes))
        if tag == "base" and a.get("href"):
            self.p.url = self.p.absoluta(a["href"])
        elif tag == "meta":
            chave = (a.get("property") or a.get("name") or "").lower()
            if chave and chave not in self.p.meta:
                self.p.meta[chave] = a.get("content", "").strip()
        elif tag == "link":
            self._link(a)
        elif tag == "img" and a.get("src"):
            dica = logo or self.dica_logo or _tem_dica(a.get("src", "") + " " + a.get("alt", ""), ("logo",))
            self.p.imagens.append(Imagem(self.p.absoluta(a["src"]), a.get("alt", "").strip(), dica, self.no_cabecalho))
        elif tag == "svg" and not fecha and (self.no_cabecalho or self.dica_logo or logo):
            self._svg = []
            self._svg_nomes = []
            self._svg_contexto = (self.no_cabecalho or cabecalho, self.dica_logo or logo)
            self._gravar_svg_abertura(tag, a, fecha)
            return
        elif tag == "style":
            self._estilo = []
        elif tag == "title":
            self._titulo = []
        if a.get("style"):
            self.p.estilos_inline.append(a["style"])
        if not fecha and tag not in VAZIAS:
            self.pilha.append((tag, cabecalho, logo))

    def _link(self, a: dict[str, str]) -> None:
        rel = " ".join(a.get("rel", "").lower().split())
        href = a.get("href", "").strip()
        if not href:
            return
        url = self.p.absoluta(href)
        if urllib.parse.urlsplit(url).hostname in GOOGLE_FONTS:
            self.p.google_fonts.append(url)
            return
        if "stylesheet" in rel.split() and "alternate" not in rel.split():
            self.p.folhas.append(("link", url))
        elif rel in RELS_ICONE:
            self.p.icones.append(Icone(url, rel, _tamanho(a.get("sizes", "")), a.get("type", "").lower()))

    def _gravar_svg_abertura(self, tag, a, fecha):
        bruto = self.get_starttag_text() or f"<{tag}>"
        nome = re.match(r"<\s*([\w:.-]+)", bruto)
        nome = nome.group(1) if nome else tag
        if tag in ("script", "foreignobject"):
            if not fecha:
                self._descartar += 1
            return
        if self._descartar:
            return
        self._svg.append(bruto)
        if not fecha and not bruto.rstrip().endswith("/>"):
            self._svg_nomes.append(nome)

    def handle_endtag(self, tag):
        if self._svg is not None:
            if tag in ("script", "foreignobject") and self._descartar:
                self._descartar -= 1
                return
            if self._descartar:
                return
            if self._svg_nomes and self._svg_nomes[-1].lower() == tag:
                self._svg.append(f"</{self._svg_nomes.pop()}>")
            if not self._svg_nomes:
                cabecalho, logo = self._svg_contexto
                self.p.svgs.append(("".join(self._svg), cabecalho, logo))
                self._svg = None
            return
        if tag == "style" and self._estilo is not None:
            self.p.folhas.append(("inline", "".join(self._estilo)))
            self._estilo = None
        elif tag == "title" and self._titulo is not None:
            self.p.titulo = " ".join("".join(self._titulo).split())
            self._titulo = None
        for i in range(len(self.pilha) - 1, -1, -1):
            if self.pilha[i][0] == tag:
                del self.pilha[i:]
                break

    def handle_data(self, data):
        if self._svg is not None:
            if not self._descartar:
                self._svg.append(escape(data))
        elif self._estilo is not None:
            self._estilo.append(data)
        elif self._titulo is not None:
            self._titulo.append(data)


def ler(html: str, url: str) -> Pagina:
    pagina = Pagina(url=url)
    leitor = _Leitor(pagina)
    leitor.feed(html)
    leitor.close()
    return pagina


def familias_google(url: str) -> list[str]:
    """Famílias de um link do Google Fonts (css e css2), sem baixar a folha."""
    consulta = urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)
    familias: list[str] = []
    for valor in consulta.get("family", []):
        for item in valor.split("|"):
            nome = item.split(":", 1)[0].replace("+", " ").strip()
            if nome and nome not in familias:
                familias.append(nome)
    return familias
