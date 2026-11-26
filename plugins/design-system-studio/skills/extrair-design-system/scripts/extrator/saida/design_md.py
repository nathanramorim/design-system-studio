"""DESIGN.md: preenche o modelo `templates/DESIGN.md` com o que foi extraído e o porquê de cada papel."""

from __future__ import annotations

from pathlib import Path
from string import Template

from .. import VERSAO
from ..modelo import Extracao
from .texto import codigo, md
from .tokens_css import MAX_CORES, PAPEIS_COR, tokens_propostos

NOMES_COR = {
    "fundo": "Fundo", "superficie": "Superfície", "texto": "Texto", "texto_suave": "Texto suave",
    "primaria": "Primária", "destaque": "Destaque",
}
NOMES_FONTE = {"texto": "Texto", "titulos": "Títulos", "mono": "Código"}


def _linhas(linhas: list[str], vazio: str) -> str:
    return "\n".join(linhas) if linhas else vazio


def _decisoes(ex: Extracao) -> str:
    linhas = []
    for papel, nome in PAPEIS_COR:
        p = ex.paleta.papeis.get(papel)
        if p:
            linhas.append(f"| {NOMES_COR[papel]} | `--ds-cor-{nome}` | `{p.hex}` | {md(p.motivo)} |")
    return "\n".join(linhas)


def _paleta(ex: Extracao) -> str:
    linhas = []
    for n, c in enumerate(ex.paleta.cores[:MAX_CORES], start=1):
        tokens = ", ".join(codigo(t) for t in c.tokens[:4]) or "(nenhuma)"
        linhas.append(f"| `--ds-cor-{n}` | `{c.hex}` | {c.usos} | {c.fundo} | {c.texto} | {c.borda} | {tokens} |")
    return _linhas(linhas, "| (nenhuma) | | | | | | |")


def _transparencias(ex: Extracao) -> str:
    if not ex.paleta.transparencias:
        return "Nenhuma cor com transparência."
    itens = ", ".join(f"`{valor}` ({usos})" for valor, usos in ex.paleta.transparencias)
    return f"Transparências mais usadas (usos): {itens}."


def _fontes(ex: Extracao) -> tuple[str, str, str]:
    papeis = [
        f"| {NOMES_FONTE[papel]} | {md(p.familia)} | `--ds-fonte-{papel}` | {md(p.motivo)} |"
        for papel, p in ex.tipografia.papeis.items()
    ]
    familias = [
        f"| {md(f.nome)} | {f.usos} | {md(', '.join(sorted(f.origens)))} |" for f in ex.tipografia.familias[:10]
    ]
    partes = []
    if ex.tipografia.tamanhos:
        escala = ", ".join(f"`{v}` ({u})" for v, u in ex.tipografia.tamanhos)
        partes.append(f"Escala de tamanhos (usos), do menor para o maior: {escala}. Tokens `--ds-tamanho-1` em diante.")
    else:
        partes.append("Nenhum tamanho de fonte fixo encontrado.")
    if ex.tipografia.fluidos:
        partes.append("Tamanhos fluidos: " + ", ".join(codigo(v) for v, _ in ex.tipografia.fluidos) + ".")
    if ex.tipografia.pesos:
        partes.append("Pesos (usos): " + ", ".join(f"`{v}` ({u})" for v, u in ex.tipografia.pesos) + ".")
    if ex.tipografia.google_fonts:
        partes.append("Google Fonts ligado pela página: " + ", ".join(md(f) for f in ex.tipografia.google_fonts) + ".")
    return (
        "\n".join(papeis),
        _linhas(familias, "| (nenhuma) | | |"),
        "\n\n".join(partes),
    )


def _medidas(ex: Extracao) -> str:
    usos = {}
    for prefixo, valores in (("tamanho", ex.tipografia.tamanhos), ("raio", ex.medidas.raios),
                             ("sombra", ex.medidas.sombras), ("espaco", ex.medidas.espacos)):
        usos.update({(prefixo, v): u for v, u in valores})
    linhas = []
    for nome, valor in tokens_propostos(ex):
        prefixo = nome.split("-")[3]
        if prefixo in ("raio", "sombra", "espaco"):
            linhas.append(f"| `{nome}` | {codigo(valor)} | {usos.get((prefixo, valor), 0)} |")
    return _linhas(linhas, "| (nenhum) | | |")


def _componentes(ex: Extracao) -> str:
    if not ex.componentes:
        return "Nenhum componente reconhecido pelos seletores comuns (botões, links, cartões, campos, cabeçalho e rodapé)."
    linhas = ["| Componente | Regras copiadas | Seletores (primeiros) |", "|---|---|---|"]
    for comp in ex.componentes:
        seletores = []
        for seletor, _, _ in comp.regras:
            if seletor not in seletores:
                seletores.append(seletor)
        lista = ", ".join(codigo(s) for s in seletores[:6])
        linhas.append(f"| {comp.nome} | {len(comp.regras)} | {lista} |")
    return "\n".join(linhas)


def _marca(ex: Extracao) -> str:
    if not ex.ativos:
        return "Nenhuma imagem de marca encontrada."
    linhas = ["| Arquivo | Papel | Origem | Por quê |", "|---|---|---|---|"]
    for a in ex.ativos:
        linhas.append(f"| `assets/{a.arquivo}` | {md(a.papel)} | {md(a.origem)} | {md(a.motivo)} |")
    return "\n".join(linhas)


def gerar(ex: Extracao, modelos: Path) -> str:
    modelo = Template((modelos / "DESIGN.md").read_text(encoding="utf-8"))
    papeis_fonte, familias, escala = _fontes(ex)
    n = len(ex.paleta.cores)
    resumo = f"{n} cores opacas em {ex.regras} regras de {ex.folhas} folhas (inclui {ex.por_import} por `@import`) e do HTML."
    captura = "![Captura da primeira dobra, a 1440px](assets/captura.png)" if ex.captura else "Sem captura. Rode com `--captura` para incluir uma."
    avisos = "\n".join(f"- Aviso da extração: {md(a)}" for a in ex.avisos)
    return modelo.substitute(
        nome=md(ex.nome),
        url=ex.url,
        data=ex.data.strftime("%d/%m/%Y"),
        versao=VERSAO,
        decisoes=_decisoes(ex),
        resumo_cores=resumo,
        paleta=_paleta(ex),
        transparencias=_transparencias(ex),
        papeis_fonte=papeis_fonte,
        familias=familias,
        escala=escala,
        medidas=_medidas(ex),
        componentes=_componentes(ex),
        marca=_marca(ex),
        captura=captura,
        avisos=avisos,
    ).rstrip() + "\n"
