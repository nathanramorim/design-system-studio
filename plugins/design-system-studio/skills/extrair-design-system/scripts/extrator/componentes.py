"""Componentes: reconhece botões, links, cartões, campos, cabeçalho e rodapé pelos seletores e copia as regras."""

from __future__ import annotations

import re
import urllib.parse
from dataclasses import dataclass, field

TIPOS: dict[str, dict] = {
    "botoes": {"nome": "Botões", "tags": {"button"}, "classes": {"btn", "button", "botao", "cta"}},
    "links": {"nome": "Links", "tags": {"a"}, "classes": {"link"}},
    "cartoes": {"nome": "Cartões", "tags": set(), "classes": {"card", "cartao", "tile"}},
    "campos": {
        "nome": "Campos",
        "tags": {"input", "textarea", "select"},
        "classes": {"field", "campo", "input", "form-control", "textfield"},
    },
    "cabecalho": {"nome": "Cabeçalho", "tags": {"header"}, "classes": {"header", "navbar", "topbar", "cabecalho"}},
    "rodape": {"nome": "Rodapé", "tags": {"footer"}, "classes": {"footer", "rodape"}},
}
MAX_REGRAS = 40
TAGS_DE_AMOSTRA = {
    "botoes": {"a", "button", "input"},
    "links": {"a"},
    "cartoes": {"div", "article", "section", "li", "a", "aside"},
    "campos": {"input", "textarea", "select"},
    "cabecalho": {"header", "div", "nav"},
    "rodape": {"footer", "div"},
}
PERIGOSO = re.compile(r"expression\s*\(|javascript:|vbscript:", re.I)
PROIBIDAS = {"behavior", "-moz-binding"}
URL = re.compile(r"""url\(\s*(['"]?)(.*?)\1\s*\)""", re.I)
COMBINADORES = re.compile(r"\s*[>+~]\s*|\s+")


@dataclass
class Componente:
    tipo: str
    nome: str
    regras: list = field(default_factory=list)
    amostras: list[tuple[str, tuple[str, ...]]] = field(default_factory=list)


def _sujeito(parte: str) -> list[str]:
    """Compostos do seletor, do sujeito (último) para trás, sem pseudoclasses nem atributos."""
    limpa = re.sub(r"\[[^\]]*\]", "", re.sub(r"\([^()]*\)", "", parte))
    compostos = [c for c in COMBINADORES.split(limpa.strip()) if c]
    return [re.sub(r"::?[\w-]+", "", c) for c in reversed(compostos)]


def _tipo_do_composto(composto: str) -> str | None:
    for classe in re.findall(r"\.([\w-]+)", composto):
        classe = classe.lower()
        for tipo, regra in TIPOS.items():
            if classe in regra["classes"]:
                return tipo
        for pedaco in re.split(r"[-_]+", classe):
            for tipo, regra in TIPOS.items():
                if pedaco in regra["classes"]:
                    return tipo
    tag = re.match(r"[a-zA-Z][\w-]*", composto)
    if tag:
        for tipo, regra in TIPOS.items():
            if tag.group(0).lower() in regra["tags"]:
                return tipo
    return None


def tipo_do_seletor(seletor: str) -> str | None:
    """Tipo de componente do primeiro trecho do seletor que tiver um (sujeito primeiro)."""
    for parte in seletor.split(","):
        if re.search(r"\[type=['\"]?(submit|button)", parte, re.I):
            return "botoes"
        for composto in _sujeito(parte):
            tipo = _tipo_do_composto(composto)
            if tipo:
                return tipo
    return None


def _limpar(valor: str, base: str) -> str:
    def absoluta(m: re.Match) -> str:
        alvo = m.group(2).strip()
        if alvo.startswith(("data:", "#")):
            return m.group(0)
        return f'url("{urllib.parse.urljoin(base, alvo)}")'

    return URL.sub(absoluta, valor)


def segura(propriedade: str, valor: str) -> bool:
    return propriedade not in PROIBIDAS and not PERIGOSO.search(valor) and "</" not in valor


def analisar(regras: list, elementos: list[tuple[str, tuple[str, ...]]], url_pagina: str) -> list[Componente]:
    componentes = {tipo: Componente(tipo, dados["nome"]) for tipo, dados in TIPOS.items()}
    for regra in regras:
        tipo = tipo_do_seletor(regra.seletor)
        if not tipo or len(componentes[tipo].regras) >= MAX_REGRAS:
            continue
        base = url_pagina if regra.origem == "inline" else regra.origem
        declaracoes = tuple((p, _limpar(v, base)) for p, v in regra.declaracoes if segura(p, v))
        if declaracoes:
            componentes[tipo].regras.append((regra.seletor, declaracoes, regra.contexto))
    citadas = {
        tipo: {c for seletor, _, _ in comp.regras for c in re.findall(r"\.([\w-]+)", seletor)}
        for tipo, comp in componentes.items()
    }
    for tag, classes in elementos:
        tipo = _tipo_do_composto(tag + "".join(f".{c}" for c in classes))
        if not tipo or not componentes[tipo].regras or tag not in TAGS_DE_AMOSTRA[tipo]:
            continue
        item = (tag, tuple(c for c in classes if c in citadas[tipo]))
        amostras = componentes[tipo].amostras
        if item not in amostras and len(amostras) < 4:
            amostras.append(item)
    for comp in componentes.values():
        if comp.regras and not comp.amostras:
            comp.amostras = _amostras_dos_seletores(comp)
    return [c for c in componentes.values() if c.regras]


def _amostras_dos_seletores(comp: Componente) -> list[tuple[str, tuple[str, ...]]]:
    padrao = {"botoes": "button", "links": "a", "cartoes": "div", "campos": "input", "cabecalho": "header", "rodape": "footer"}
    amostras: list[tuple[str, tuple[str, ...]]] = []
    for seletor, _, _ in comp.regras:
        for parte in seletor.split(","):
            sujeito = _sujeito(parte)[0] if _sujeito(parte) else ""
            if _tipo_do_composto(sujeito) != comp.tipo:
                continue
            tag = re.match(r"[a-zA-Z][\w-]*", sujeito)
            classes = tuple(re.findall(r"\.([\w-]+)", sujeito))
            item = (tag.group(0).lower() if tag else padrao[comp.tipo], classes)
            if item not in amostras:
                amostras.append(item)
            if len(amostras) >= 4:
                return amostras
    return amostras
