"""tokens.css: @font-face do site, custom properties do :root como estão e os tokens propostos (`--ds-*`)."""

from __future__ import annotations

import re

from .. import VERSAO
from ..componentes import segura
from ..modelo import Extracao
from .texto import comentario_css, valor_css_seguro

MAX_CORES = 16
PAPEIS_COR = (
    ("fundo", "fundo"),
    ("superficie", "superficie"),
    ("texto", "texto"),
    ("texto_suave", "texto-suave"),
    ("primaria", "primaria"),
    ("destaque", "destaque"),
)


def tokens_propostos(ex: Extracao) -> list[tuple[str, str]]:
    """Lista (nome, valor) dos tokens `--ds-*`, na ordem do arquivo. A vitrine usa os mesmos nomes."""
    tokens: list[tuple[str, str]] = []
    for papel, nome in PAPEIS_COR:
        if papel in ex.paleta.papeis:
            tokens.append((f"--ds-cor-{nome}", ex.paleta.papeis[papel].hex))
    for n, cor in enumerate(ex.paleta.cores[:MAX_CORES], start=1):
        tokens.append((f"--ds-cor-{n}", cor.hex))
    for papel in ("texto", "titulos", "mono"):
        pilha = ex.tipografia.papeis[papel].pilha
        if valor_css_seguro(pilha):
            tokens.append((f"--ds-fonte-{papel}", pilha))
    grupos = (
        ("tamanho", ex.tipografia.tamanhos),
        ("raio", ex.medidas.raios),
        ("sombra", ex.medidas.sombras),
        ("espaco", ex.medidas.espacos),
    )
    for prefixo, valores in grupos:
        seguros = [valor for valor, _ in valores if valor_css_seguro(valor)]
        tokens += [(f"--ds-{prefixo}-{n}", valor) for n, valor in enumerate(seguros, start=1)]
    return tokens


def _faces(ex: Extracao) -> list[str]:
    blocos = []
    for face in ex.tipografia.font_faces:
        linhas = [f"  {nome}: {valor};" for nome, valor in face.items() if valor and segura(nome, valor) and "</" not in valor]
        if any(linha.strip().startswith("src:") for linha in linhas):
            blocos.append("@font-face {\n" + "\n".join(linhas) + "\n}")
    return blocos


def gerar(ex: Extracao) -> str:
    data = ex.data.strftime("%d/%m/%Y")
    partes = [
        f"/* Design system de {comentario_css(ex.nome)}, tokens. Fonte: {comentario_css(ex.url)}, "
        f"lida em {data} pelo design-system-studio {VERSAO} (extração determinística, sem IA). */"
    ]
    faces = _faces(ex)
    if faces:
        partes.append("/* Fontes declaradas pelo site (@font-face), com endereços absolutos. */\n" + "\n".join(faces))
    custom = [
        (nome, " ".join(valor.split()))
        for nome, valor in ex.paleta.custom.items()
        if re.fullmatch(r"--[\w-]+", nome) and segura(nome, valor) and "</" not in valor
    ]
    if custom:
        corpo = "\n".join(f"  {nome}: {valor};" for nome, valor in custom)
        partes.append(f"/* Custom properties do :root do site, como estão. */\n:root {{\n{corpo}\n}}")
    corpo = "\n".join(f"  {nome}: {valor};" for nome, valor in tokens_propostos(ex))
    partes.append(f"/* Tokens propostos pela extração (papéis explicados no DESIGN.md). */\n:root {{\n{corpo}\n}}")
    return "\n\n".join(partes) + "\n"
