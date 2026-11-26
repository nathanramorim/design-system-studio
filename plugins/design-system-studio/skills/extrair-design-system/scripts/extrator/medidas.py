"""Medidas: raios, sombras e espaçamentos mais frequentes."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass

from .cores import resolver_var
from .folhas import Regra
from .tipografia import formatar_px

ESPACO = re.compile(r"^(margin|padding)(-(top|right|bottom|left|inline|block)(-(start|end))?)?$|^(row-|column-)?gap$")
COMPRIMENTO = re.compile(r"(\d*\.?\d+)(px|rem|em)")


@dataclass
class Medidas:
    raios: list[tuple[str, int]]
    sombras: list[tuple[str, int]]
    espacos: list[tuple[str, int]]


def _partes(valor: str) -> list[str]:
    partes, atual, nivel = [], [], 0
    for c in valor:
        if c == "(":
            nivel += 1
        elif c == ")":
            nivel -= 1
        if c.isspace() and nivel == 0:
            if atual:
                partes.append("".join(atual))
                atual = []
        else:
            atual.append(c)
    if atual:
        partes.append("".join(atual))
    return partes


def _px(token: str) -> float | None:
    m = COMPRIMENTO.fullmatch(token.lower())
    if not m:
        return None
    numero = float(m.group(1))
    return numero if m.group(2) == "px" else numero * 16


def _ordem_px(valor: str) -> float:
    m = COMPRIMENTO.search(valor)
    if not m:
        return 1e9 if "%" in valor else 1e8
    return _px(m.group(0)) or 0


def analisar(regras: list[Regra], mapa: dict[str, str]) -> Medidas:
    raios: Counter[str] = Counter()
    sombras: Counter[str] = Counter()
    espacos: Counter[str] = Counter()
    for regra in regras:
        for propriedade, valor in regra.declaracoes:
            if propriedade.startswith("--"):
                continue
            valor = " ".join(resolver_var(valor, mapa).replace("!important", "").split())
            if not valor or valor in ("0", "none", "inherit", "initial", "unset"):
                continue
            if propriedade == "border-radius" or (propriedade.startswith("border-") and propriedade.endswith("-radius")):
                if valor not in ("0px",):
                    raios[valor] += 1
            elif propriedade == "box-shadow":
                sombras[valor] += 1
            elif ESPACO.match(propriedade):
                for token in _partes(valor):
                    px = _px(token)
                    if px and px > 0:
                        espacos[formatar_px(px)] += 1
    mais = sorted(raios.items(), key=lambda t: (-t[1], t[0]))[:6]
    mais.sort(key=lambda t: (_ordem_px(t[0]), t[0]))
    esp = sorted(espacos.items(), key=lambda t: (-t[1], t[0]))[:10]
    esp.sort(key=lambda t: _ordem_px(t[0]))
    return Medidas(mais, sorted(sombras.items(), key=lambda t: (-t[1], t[0]))[:5], esp)
