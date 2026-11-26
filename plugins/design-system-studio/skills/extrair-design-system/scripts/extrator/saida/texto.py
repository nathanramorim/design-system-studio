"""Escape de texto vindo do site para Markdown, HTML e comentários CSS."""

from __future__ import annotations

import html
import re


def md(texto: str) -> str:
    """Texto seguro numa célula de tabela Markdown."""
    return " ".join(str(texto).split()).replace("|", "\\|")


def codigo(texto: str) -> str:
    texto = md(texto)
    return f"`` {texto} ``" if "`" in texto else f"`{texto}`"


def h(texto: str) -> str:
    return html.escape(" ".join(str(texto).split()), quote=True)


def comentario_css(texto: str) -> str:
    return " ".join(str(texto).split()).replace("*/", "* /")


def valor_css_seguro(valor: str) -> bool:
    """Valor que pode virar token sem abrir declaração nova nem buscar recurso."""
    return not re.search(r"[;{}<>]|url\(|expression\(|javascript:", valor, re.I)
