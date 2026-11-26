"""Vitrine: HTML válido, sem script, referências locais existentes e texto do site sempre escapado."""

from __future__ import annotations

import urllib.parse
from html.parser import HTMLParser

from conftest import EXEMPLO, extrair, servir_pasta
from extrator.saida.vitrine import SECOES


class _Vitrine(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tags: list[str] = []
        self.refs: list[str] = []
        self.ids: set[str] = set()
        self.lang = ""
        self.abertas: list[str] = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self.tags.append(tag)
        if tag == "html":
            self.lang = a.get("lang", "")
        if a.get("id"):
            self.ids.add(a["id"])
        for chave in ("src", "href"):
            if a.get(chave):
                self.refs.append(a[chave])
        if tag not in ("meta", "link", "img", "input", "br", "hr"):
            self.abertas.append(tag)

    def handle_endtag(self, tag):
        if tag in self.abertas:
            while self.abertas.pop() != tag:
                pass


def _ler(pasta):
    leitor = _Vitrine()
    leitor.feed((pasta / "index.html").read_text(encoding="utf-8"))
    return leitor


def test_vitrine_valida_e_sem_script(extraido):
    saida, _, _ = extraido
    texto = (saida / "index.html").read_text(encoding="utf-8")
    assert texto.startswith("<!doctype html>")
    v = _ler(saida)
    assert "script" not in v.tags
    assert v.lang == "pt-BR"
    assert not v.abertas, f"tags sem fechar: {v.abertas}"
    assert {i for i, _ in SECOES} <= v.ids
    assert "tokens.css" in v.refs and "components.css" in v.refs


def test_referencias_locais_existem_e_externas_so_fontes(extraido):
    saida, _, _ = extraido
    for ref in _ler(saida).refs:
        partes = urllib.parse.urlsplit(ref)
        if ref.startswith("#"):
            continue
        if partes.scheme:
            assert partes.scheme == "https" and partes.hostname == "fonts.googleapis.com", ref
            continue
        assert (saida / partes.path).is_file(), ref


def test_amostras_usam_as_classes_do_site(extraido):
    saida, _, _ = extraido
    texto = (saida / "index.html").read_text(encoding="utf-8")
    for trecho in ('class="btn btn-primario"', 'class="card cartao-destaque"', 'class="campo"', 'class="site-header"', 'class="rodape"'):
        assert trecho in texto, trecho
    assert 'src="assets/logo.svg"' in texto and "<svg" not in texto, "logo só por <img>"


def test_texto_do_site_e_escapado(tmp_path):
    with servir_pasta(EXEMPLO) as url:
        r = extrair(url, tmp_path, "--nome", '<script>alert("x")</script>')
    assert r.returncode == 0, r.stderr
    v = _ler(tmp_path)
    assert "script" not in v.tags
    assert "&lt;script&gt;" in (tmp_path / "index.html").read_text(encoding="utf-8")
