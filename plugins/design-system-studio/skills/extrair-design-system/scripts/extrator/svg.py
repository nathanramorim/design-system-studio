"""SVG: confere e limpa o SVG antes de gravar (sem script, sem foreignObject, sem eventos on*)."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET

SVG_NS = "http://www.w3.org/2000/svg"
XLINK_NS = "http://www.w3.org/1999/xlink"
REMOVIDOS = {"script", "foreignobject"}

ET.register_namespace("", SVG_NS)
ET.register_namespace("xlink", XLINK_NS)


def _local(nome: str) -> str:
    return nome.rsplit("}", 1)[-1].lower()


def higienizar(texto: str) -> str | None:
    """SVG limpo e com namespace, ou None se não for um SVG válido e seguro de ler."""
    texto = texto.strip().lstrip("﻿")
    if re.search(r"<!DOCTYPE|<!ENTITY", texto, re.I):
        return None
    texto = re.sub(r"^<\?xml[^>]*\?>\s*", "", texto)
    abertura = re.match(r"<svg\b[^>]*>", texto, re.I)
    if not abertura:
        return None
    tag = abertura.group(0)
    novo = tag
    if "xmlns=" not in tag:
        novo = novo[:4] + f' xmlns="{SVG_NS}"' + novo[4:]
    if "xlink:" in texto and "xmlns:xlink" not in tag:
        novo = novo[:4] + f' xmlns:xlink="{XLINK_NS}"' + novo[4:]
    texto = novo + texto[len(tag):]
    try:
        raiz = ET.fromstring(texto)
    except ET.ParseError:
        return None
    if _local(raiz.tag) != "svg":
        return None
    for pai in list(raiz.iter()):
        for filho in list(pai):
            if isinstance(filho.tag, str) and _local(filho.tag) in REMOVIDOS:
                pai.remove(filho)
    for elemento in raiz.iter():
        for nome in list(elemento.attrib):
            local = _local(nome)
            valor = elemento.attrib[nome].strip().lower()
            if local.startswith("on") or (local == "href" and valor.startswith(("javascript:", "data:text/html"))):
                del elemento.attrib[nome]
    return ET.tostring(raiz, encoding="unicode")
