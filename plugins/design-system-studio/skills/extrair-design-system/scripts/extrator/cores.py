"""Cores: normaliza hex, rgb, hsl e nomes, resolve var() e propõe papéis por regra explicável."""

from __future__ import annotations

import colorsys
import re
from collections import Counter
from dataclasses import dataclass, field

from .componentes import tipo_do_seletor
from .folhas import Regra, blocos, declaracao

HEX = re.compile(r"#([0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3,4})(?![\w-])")
FUNCAO = re.compile(r"(?<![\w-])(rgba?|hsla?)\(\s*([^()]*)\)", re.I)
NOMES = {
    "white": "#FFFFFF", "black": "#000000", "red": "#FF0000", "green": "#008000", "blue": "#0000FF",
    "gray": "#808080", "grey": "#808080", "silver": "#C0C0C0", "navy": "#000080", "orange": "#FFA500",
    "yellow": "#FFFF00", "purple": "#800080", "teal": "#008080", "maroon": "#800000", "olive": "#808000",
    "lime": "#00FF00", "aqua": "#00FFFF", "cyan": "#00FFFF", "fuchsia": "#FF00FF", "magenta": "#FF00FF",
}
NOME = re.compile(r"(?<![\w-])(" + "|".join(NOMES) + r")(?![\w-])", re.I)
URL = re.compile(r"url\([^)]*\)", re.I)
FUNDO = {"background", "background-color", "background-image"}
BORDA = ("border", "outline")
OUTRAS = {"fill", "stroke", "box-shadow", "text-shadow", "caret-color", "accent-color", "column-rule"}
BASE = {"html", "body", ":root"}
VAR_PROFUNDIDADE = 8


@dataclass
class Cor:
    hex: str
    usos: int = 0
    fundo: int = 0
    texto: int = 0
    borda: int = 0
    interativo: int = 0
    tokens: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Papel:
    hex: str
    motivo: str


@dataclass
class Paleta:
    cores: list[Cor]
    papeis: dict[str, Papel]
    transparencias: list[tuple[str, int]]
    custom: dict[str, str]


def _canal(texto: str, escala: float) -> float | None:
    texto = texto.strip().lower()
    try:
        if texto == "none":
            return 0.0
        if texto.endswith("%"):
            return float(texto[:-1]) / 100 * escala
        return float(texto)
    except ValueError:
        return None


def _alfa(texto: str | None) -> float | None:
    if texto is None:
        return 1.0
    valor = _canal(texto, 1.0)
    return None if valor is None else max(0.0, min(1.0, valor))


def _matiz(texto: str) -> float | None:
    texto = texto.strip().lower()
    unidades = {"deg": 1.0, "grad": 0.9, "rad": 57.29577951308232, "turn": 360.0}
    for sufixo, fator in unidades.items():
        if texto.endswith(sufixo):
            try:
                return float(texto[: -len(sufixo)]) * fator
            except ValueError:
                return None
    try:
        return float(texto)
    except ValueError:
        return None


def _hex(r: float, g: float, b: float) -> str:
    return "#" + "".join(f"{max(0, min(255, int(c + 0.5))):02X}" for c in (r, g, b))


def _funcao(nome: str, argumentos: str) -> tuple[str, float] | None:
    partes = [p for p in re.split(r"[\s,/]+", argumentos.strip()) if p]
    if len(partes) not in (3, 4) or any(not re.fullmatch(r"[-+.\w%]+", p) for p in partes):
        return None
    alfa = _alfa(partes[3] if len(partes) == 4 else None)
    if nome.lower().startswith("rgb"):
        canais = [_canal(p, 255.0) for p in partes[:3]]
        if None in canais or alfa is None:
            return None
        return _hex(*canais), alfa
    h = _matiz(partes[0])
    s, luz = (_canal(p.rstrip("%"), 1.0) for p in partes[1:3])
    if h is None or s is None or luz is None or alfa is None:
        return None
    s, luz = (v / 100 for v in (s, luz))
    r, g, b = colorsys.hls_to_rgb((h % 360) / 360, max(0.0, min(1.0, luz)), max(0.0, min(1.0, s)))
    return _hex(r * 255, g * 255, b * 255), alfa


def tom_claro(valor: str) -> str:
    """Troca light-dark(claro, escuro) pelo tom claro, que é o padrão do navegador."""
    while (j := valor.lower().find("light-dark(")) >= 0:
        nivel, k, virgula = 0, j + 10, -1
        while k < len(valor):
            if valor[k] == "(":
                nivel += 1
            elif valor[k] == ")":
                nivel -= 1
                if nivel == 0:
                    break
            elif valor[k] == "," and nivel == 1 and virgula < 0:
                virgula = k
            k += 1
        claro = valor[j + 11 : virgula if virgula > 0 else k]
        valor = valor[:j] + claro.strip() + valor[k + 1 :]
    return valor


def cores_em(valor: str) -> list[tuple[str, float]]:
    """Cores de um valor CSS como (#RRGGBB, alfa). Ignora o conteúdo de url() e conta o tom claro de light-dark()."""
    valor = URL.sub(" ", tom_claro(valor))
    achadas: list[tuple[str, float]] = []
    for m in HEX.finditer(valor):
        h = m.group(1)
        if len(h) in (3, 4):
            h = "".join(c * 2 for c in h)
        alfa = int(h[6:8], 16) / 255 if len(h) == 8 else 1.0
        achadas.append(("#" + h[:6].upper(), alfa))
    for m in FUNCAO.finditer(valor):
        cor = _funcao(m.group(1), m.group(2))
        if cor:
            achadas.append(cor)
    for m in NOME.finditer(valor):
        achadas.append((NOMES[m.group(1).lower()], 1.0))
    return achadas


def resolver_var(valor: str, mapa: dict[str, str], profundidade: int = 0) -> str:
    """Troca var(--x, reserva) pelo valor da custom property, até 8 níveis."""
    if "var(" not in valor or profundidade > VAR_PROFUNDIDADE:
        return valor
    saida, i = [], 0
    while True:
        j = valor.find("var(", i)
        if j < 0:
            saida.append(valor[i:])
            return "".join(saida)
        saida.append(valor[i:j])
        nivel, k = 0, j + 3
        while k < len(valor):
            if valor[k] == "(":
                nivel += 1
            elif valor[k] == ")":
                nivel -= 1
                if nivel == 0:
                    break
            k += 1
        nome, _, reserva = valor[j + 4 : k].partition(",")
        substituto = mapa.get(nome.strip(), reserva.strip())
        saida.append(resolver_var(substituto, mapa, profundidade + 1))
        i = k + 1


def _partes_base(seletor: str) -> bool:
    return any(p.strip().lower() in BASE for p in seletor.split(","))


def mapa_custom(regras: list[Regra]) -> dict[str, str]:
    """Custom properties: as de :root, html e body valem; as de outros seletores entram só se faltarem."""
    raiz: dict[str, str] = {}
    outras: dict[str, str] = {}
    for regra in regras:
        for nome, valor in regra.declaracoes:
            if not nome.startswith("--"):
                continue
            if _partes_base(regra.seletor) and not regra.contexto:
                raiz[nome] = valor
            else:
                outras.setdefault(nome, valor)
    return {**outras, **raiz}


def raiz_custom(regras: list[Regra]) -> dict[str, str]:
    raiz: dict[str, str] = {}
    for regra in regras:
        if any(p.strip().lower() in (":root", "html") for p in regra.seletor.split(",")) and not regra.contexto:
            for nome, valor in regra.declaracoes:
                if nome.startswith("--"):
                    raiz[nome] = valor
    return raiz


def _de_cor(propriedade: str) -> bool:
    return "color" in propriedade or propriedade in FUNDO or propriedade in OUTRAS or propriedade.startswith(BORDA)


def hls(cor: str) -> tuple[float, float, float]:
    r, g, b = (int(cor[i : i + 2], 16) / 255 for i in (1, 3, 5))
    return colorsys.rgb_to_hls(r, g, b)


def cromatica(cor: str) -> bool:
    """Cromática quando o maior e o menor canal diferem em pelo menos 15% (cinzas, quase brancos e quase pretos ficam fora)."""
    canais = [int(cor[i : i + 2], 16) for i in (1, 3, 5)]
    return (max(canais) - min(canais)) / 255 >= 0.15


def usos(n: int) -> str:
    return "1 uso" if n == 1 else f"{n} usos"


def luminancia(cor: str) -> float:
    def canal(c: float) -> float:
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = (canal(int(cor[i : i + 2], 16) / 255) for i in (1, 3, 5))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contraste(a: str, b: str) -> float:
    claro, escuro = sorted((luminancia(a), luminancia(b)), reverse=True)
    return (claro + 0.05) / (escuro + 0.05)


def _distancia_matiz(a: str, b: str) -> float:
    d = abs(hls(a)[0] - hls(b)[0]) * 360
    return min(d, 360 - d)


def analisar(regras: list[Regra], estilos_inline: list[str], theme_color: str = "") -> Paleta:
    mapa = mapa_custom(regras)
    cores: dict[str, Cor] = {}
    transparencias: Counter[str] = Counter()
    base_fundo: tuple[str, str] | None = None
    base_texto: tuple[str, str] | None = None

    def cor(h: str) -> Cor:
        return cores.setdefault(h, Cor(h))

    fontes = [(r.seletor, r.declaracoes, r.contexto) for r in regras]
    for estilo in estilos_inline:
        pares = tuple(p for texto, corpo in blocos(estilo) if corpo is None and (p := declaracao(texto)))
        fontes.append(("[style]", pares, ()))

    for seletor, declaracoes, contexto in fontes:
        interativo = tipo_do_seletor(seletor) in ("botoes", "links")
        for propriedade, valor in declaracoes:
            if propriedade.startswith("--") or not _de_cor(propriedade):
                continue
            achadas = cores_em(resolver_var(valor, mapa))
            for h, alfa in achadas:
                if alfa < 0.99:
                    r, g, b = (int(h[i : i + 2], 16) for i in (1, 3, 5))
                    transparencias[f"rgba({r}, {g}, {b}, {alfa:.2f})"] += 1
                    continue
                c = cor(h)
                c.usos += 1
                c.fundo += propriedade in FUNDO
                c.texto += propriedade == "color"
                c.borda += propriedade.startswith(BORDA)
                c.interativo += interativo
            opacas = [h for h, alfa in achadas if alfa >= 0.99]
            if opacas and _partes_base(seletor) and not contexto:
                if propriedade in ("background", "background-color"):
                    base_fundo = (opacas[0], seletor)
                elif propriedade == "color":
                    base_texto = (opacas[0], seletor)

    for nome, valor in raiz_custom(regras).items():
        for h, alfa in cores_em(resolver_var(valor, mapa)):
            if alfa >= 0.99:
                cor(h).tokens.append(nome)

    ordenadas = sorted(cores.values(), key=lambda c: (-c.usos, c.hex))
    papeis = _papeis(ordenadas, base_fundo, base_texto, theme_color)
    return Paleta(ordenadas, papeis, sorted(transparencias.items(), key=lambda t: (-t[1], t[0]))[:8], raiz_custom(regras))


def _papeis(cores, base_fundo, base_texto, theme_color) -> dict[str, Papel]:
    papeis: dict[str, Papel] = {}
    fundos = sorted((c for c in cores if c.fundo), key=lambda c: (-c.fundo, c.hex))
    if base_fundo:
        papeis["fundo"] = Papel(base_fundo[0], f"`background` do `{base_fundo[1]}`")
    elif fundos:
        papeis["fundo"] = Papel(fundos[0].hex, f"cor mais usada em fundos ({usos(fundos[0].fundo)})")
    else:
        papeis["fundo"] = Papel("#FFFFFF", "nenhum fundo declarado; branco do navegador")
    fundo = papeis["fundo"].hex

    textos = sorted((c for c in cores if c.texto and c.hex != fundo), key=lambda c: (-c.texto, c.hex))
    legiveis = [c for c in textos if contraste(c.hex, fundo) >= 4.5]
    if base_texto:
        papeis["texto"] = Papel(base_texto[0], f"`color` do `{base_texto[1]}`")
    elif legiveis:
        papeis["texto"] = Papel(legiveis[0].hex, f"cor de texto mais usada com contraste de 4,5:1 ou mais ({usos(legiveis[0].texto)})")
    else:
        h = "#000000" if contraste("#000000", fundo) >= contraste("#FFFFFF", fundo) else "#FFFFFF"
        papeis["texto"] = Papel(h, "nenhuma cor de texto legível declarada; preto ou branco, o de maior contraste")
    texto = papeis["texto"].hex

    tema = next((h for h, _ in cores_em(theme_color)), "") if theme_color else ""

    def pontos(c: Cor) -> int:
        return c.usos + 2 * c.interativo + (3 if c.hex == tema else 0)

    cromaticas = sorted(
        (c for c in cores if cromatica(c.hex) and c.hex not in (fundo, texto) and c.usos),
        key=lambda c: (-pontos(c), c.hex),
    )
    if cromaticas:
        p = cromaticas[0]
        extra = " + 3 do theme-color" if p.hex == tema else ""
        papeis["primaria"] = Papel(
            p.hex, f"cor cromática de maior pontuação: {usos(p.usos)} + 2 × {p.interativo} em botões e links{extra} = {pontos(p)}"
        )
        distantes = [c for c in cromaticas[1:] if _distancia_matiz(c.hex, p.hex) >= 30]
        if distantes:
            d = distantes[0]
            papeis["destaque"] = Papel(
                d.hex, f"próxima cor cromática com matiz a {_distancia_matiz(d.hex, p.hex):.0f}° da primária ({pontos(d)} pontos)"
            )
        elif len(cromaticas) > 1:
            d = cromaticas[1]
            papeis["destaque"] = Papel(d.hex, f"segunda cor cromática, de matiz próximo à primária ({pontos(d)} pontos)")
        else:
            papeis["destaque"] = Papel(p.hex, "sem segunda cor cromática; repete a primária")
    else:
        papeis["primaria"] = Papel(texto, "nenhuma cor cromática; o site é neutro e a primária repete o texto")
        papeis["destaque"] = Papel(texto, "nenhuma cor cromática; repete o texto")

    usadas = {fundo, texto}
    neutros = [c for c in fundos if c.hex not in usadas and not cromatica(c.hex)]
    if neutros:
        papeis["superficie"] = Papel(neutros[0].hex, f"cor neutra mais usada em fundos depois do fundo ({usos(neutros[0].fundo)})")
    suaves = [c for c in textos if c.hex not in usadas and not cromatica(c.hex)]
    if suaves:
        papeis["texto_suave"] = Papel(suaves[0].hex, f"cor neutra mais usada em texto depois do texto ({usos(suaves[0].texto)})")
    return papeis
