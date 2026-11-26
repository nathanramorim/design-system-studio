"""components.css: as regras dos componentes reconhecidos, copiadas do CSS do site e agrupadas por tipo."""

from __future__ import annotations

from .. import VERSAO
from ..modelo import Extracao
from .texto import comentario_css


def _regra(seletor: str, declaracoes, contexto: tuple[str, ...]) -> str:
    recuo = "  " * len(contexto)
    corpo = "\n".join(f"{recuo}  {nome}: {valor};" for nome, valor in declaracoes)
    texto = f"{recuo}{seletor} {{\n{corpo}\n{recuo}}}"
    for nivel in range(len(contexto) - 1, -1, -1):
        fora = "  " * nivel
        texto = f"{fora}{contexto[nivel]} {{\n{texto}\n{fora}}}"
    return texto


def gerar(ex: Extracao) -> str:
    data = ex.data.strftime("%d/%m/%Y")
    partes = [
        f"/* Design system de {comentario_css(ex.nome)}, componentes. Copiados do CSS de {comentario_css(ex.url)} "
        f"em {data} pelo design-system-studio {VERSAO}. Dependem de tokens.css (custom properties do site). */"
    ]
    if not ex.componentes:
        partes.append("/* Nenhum componente reconhecido pelos seletores comuns (botões, links, cartões, campos, cabeçalho, rodapé). */")
    for comp in ex.componentes:
        regras = "\n".join(_regra(" ".join(s.split()), d, c) for s, d, c in comp.regras)
        partes.append(f"/* ========== {comp.nome}: {len(comp.regras)} regras ========== */\n{regras}")
    return "\n\n".join(partes) + "\n"
