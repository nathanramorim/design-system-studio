"""index.html: vitrine que abre sem servidor e sem script, a partir de `templates/vitrine.html`.

Todo texto vindo do site passa por escape. As imagens entram só por <img> (SVG nunca inline) e os
estilos de exemplo usam os tokens (`var(--ds-*)`), nunca valores do site em atributo.
"""

from __future__ import annotations

import re
from pathlib import Path
from string import Template

from .. import VERSAO
from ..cores import contraste, usos
from ..modelo import Extracao
from .texto import h
from .tokens_css import MAX_CORES, PAPEIS_COR, tokens_propostos

NOMES_COR = {
    "fundo": "Fundo", "superficie": "Superfície", "texto": "Texto", "texto_suave": "Texto suave",
    "primaria": "Primária", "destaque": "Destaque",
}
TEXTO_AMOSTRA = {
    "botoes": "Botão",
    "links": "Link de exemplo",
    "cartoes": "Título do cartão",
    "campos": "",
    "cabecalho": "Cabeçalho",
    "rodape": "Rodapé",
}
SECOES = (("marca", "Marca"), ("cores", "Cores"), ("tipografia", "Tipografia"), ("medidas", "Espaço, raios e sombras"),
          ("componentes", "Componentes"), ("captura", "Captura"))


def _rotulo(fundo: str) -> str:
    return "#000000" if contraste("#000000", fundo) >= contraste("#FFFFFF", fundo) else "#FFFFFF"


def _amostra_cor(hexa: str, titulo: str, detalhe: str) -> str:
    return (
        f'<div class="vt-cor" style="background:{hexa};color:{_rotulo(hexa)}">'
        f"<b>{h(titulo)}</b>{h(hexa)}<br>{h(detalhe)}</div>"
    )


def _secao(ident: str, titulo: str, corpo: str) -> str:
    return f'<section class="vt-secao" id="{ident}"><h2>{h(titulo)}</h2>\n{corpo}\n</section>'


def _marca(ex: Extracao) -> str:
    figuras = []
    for a in ex.ativos:
        if a.papel == "logo" and figuras and any(a.arquivo in f for f in figuras):
            continue
        figuras.append(f'<figure><img src="assets/{h(a.arquivo)}" alt="{h(a.papel)}"><figcaption>{h(a.papel)}: assets/{h(a.arquivo)}</figcaption></figure>')
    if not figuras:
        return '<p class="vt-nota">Nenhum logo, favicon ou ícone encontrado.</p>'
    nota = '<p class="vt-nota">Imagens do dono do site, baixadas como referência.</p>'
    return nota + '<div class="vt-imagens">' + "".join(figuras) + "</div>"


def _cores(ex: Extracao) -> str:
    papeis = [
        _amostra_cor(ex.paleta.papeis[p].hex, NOMES_COR[p], f"--ds-cor-{nome}")
        for p, nome in PAPEIS_COR
        if p in ex.paleta.papeis
    ]
    paleta = [_amostra_cor(c.hex, f"--ds-cor-{n}", usos(c.usos)) for n, c in enumerate(ex.paleta.cores[:MAX_CORES], start=1)]
    corpo = '<h3>Papéis</h3><div class="vt-grade">' + "".join(papeis) + "</div>"
    if paleta:
        corpo += '<h3>Paleta, da mais usada para a menos usada</h3><div class="vt-grade">' + "".join(paleta) + "</div>"
    else:
        corpo += '<p class="vt-nota">Nenhuma cor opaca encontrada no CSS.</p>'
    return corpo


def _tipografia(ex: Extracao) -> str:
    nomes = {"texto": "Texto", "titulos": "Títulos", "mono": "Código"}
    partes = []
    for papel, p in ex.tipografia.papeis.items():
        partes.append(
            f'<div class="vt-papel"><span class="vt-codigo">--ds-fonte-{papel}: {h(nomes[papel])}, {h(p.familia)}</span>'
            f'<p class="vt-fonte" style="font-family:var(--ds-fonte-{papel})">Aa Bb Cc 0123 Ação</p></div>'
        )
    tamanhos = [n for n, _ in tokens_propostos(ex) if n.startswith("--ds-tamanho-")]
    if tamanhos:
        linhas = "".join(
            f'<p style="font-size:var({n})">{h(n)}: O rápido design da marca</p>' for n in tamanhos
        )
        partes.append(f'<h3>Escala de tamanhos</h3><div class="vt-escala">{linhas}</div>')
    else:
        partes.append('<p class="vt-nota">Nenhum tamanho de fonte fixo encontrado.</p>')
    return "".join(partes)


def _medidas(ex: Extracao) -> str:
    tokens = tokens_propostos(ex)
    partes = []
    espacos = [(n, v) for n, v in tokens if n.startswith("--ds-espaco-")]
    if espacos:
        linhas = "".join(
            f'<div class="vt-linha"><span class="vt-codigo">{h(n)}: {h(v)}</span>'
            f'<div class="vt-barra" style="width:var({n})"></div></div>'
            for n, v in espacos
        )
        partes.append(f"<h3>Espaçamentos</h3>{linhas}")
    raios = [(n, v) for n, v in tokens if n.startswith("--ds-raio-")]
    if raios:
        caixas = "".join(
            f'<figure><div class="vt-caixa" style="border-radius:var({n})"></div><figcaption class="vt-codigo">{h(n)}: {h(v)}</figcaption></figure>'
            for n, v in raios
        )
        partes.append(f'<h3>Raios</h3><div class="vt-imagens">{caixas}</div>')
    sombras = [(n, v) for n, v in tokens if n.startswith("--ds-sombra-")]
    if sombras:
        caixas = "".join(
            f'<figure><div class="vt-caixa" style="box-shadow:var({n})"></div><figcaption class="vt-codigo">{h(n)}</figcaption></figure>'
            for n, _ in sombras
        )
        partes.append(f'<h3>Sombras</h3><div class="vt-imagens">{caixas}</div>')
    return "".join(partes) or '<p class="vt-nota">Nenhum espaçamento, raio ou sombra frequente encontrado.</p>'


def _elemento(tipo: str, tag: str, classes: tuple[str, ...], logo: str) -> str:
    classes = tuple(c for c in classes if re.fullmatch(r"[\w-]+", c))
    atributo = f' class="{h(" ".join(classes))}"' if classes else ""
    texto = h(TEXTO_AMOSTRA[tipo])
    if tipo == "campos":
        if tag == "textarea":
            return f'<textarea{atributo} aria-label="Mensagem" placeholder="Mensagem"></textarea>'
        if tag == "select":
            return f'<select{atributo} aria-label="Opção"><option>Opção</option></select>'
        return f'<input{atributo} type="text" aria-label="Nome" placeholder="Seu nome">'
    if tipo == "cartoes":
        return f'<div{atributo}><h3>{texto}</h3><p>Texto de apoio do cartão.</p></div>'
    if tipo in ("cabecalho", "rodape"):
        marca = f'<img class="vt-logo" src="{logo}" alt="">' if logo and tipo == "cabecalho" else ""
        nome = "header" if tipo == "cabecalho" else "footer"
        return f'<{nome}{atributo}>{marca}<span>{texto}</span> <a href="#componentes">Link</a></{nome}>'
    if tipo == "links":
        return f'<p>Um parágrafo com <a{atributo} href="#componentes">{texto}</a>.</p>'
    if tag == "a":
        return f'<a{atributo} href="#componentes">{texto}</a>'
    return f'<button{atributo} type="button">{texto}</button>'


def _componentes(ex: Extracao, logo: str) -> str:
    if not ex.componentes:
        return '<p class="vt-nota">Nenhum componente reconhecido pelos seletores comuns.</p>'
    partes = ['<p class="vt-nota">Marcação de exemplo com as classes encontradas; os estilos vêm de components.css.</p>']
    for comp in ex.componentes:
        amostras = "".join(f'<div class="vt-amostra">{_elemento(comp.tipo, t, c, logo)}</div>' for t, c in comp.amostras)
        seletores = []
        for seletor, _, _ in comp.regras:
            if seletor not in seletores:
                seletores.append(seletor)
        lista = h(", ".join(seletores[:8]))
        partes.append(f'<h3>{h(comp.nome)} ({len(comp.regras)} regras)</h3>{amostras}<p class="vt-codigo">{lista}</p>')
    return "".join(partes)


def gerar(ex: Extracao, modelos: Path) -> str:
    modelo = Template((modelos / "vitrine.html").read_text(encoding="utf-8"))
    logo_ativo = ex.ativo("logo")
    favicon_ativo = ex.ativo("favicon")
    logo = f"assets/{h(logo_ativo.arquivo)}" if logo_ativo else ""
    corpos = {
        "marca": _marca(ex),
        "cores": _cores(ex),
        "tipografia": _tipografia(ex),
        "medidas": _medidas(ex),
        "componentes": _componentes(ex, logo),
        "captura": (
            '<img class="vt-captura" src="assets/captura.png" alt="Captura da primeira dobra do site">'
            if ex.captura
            else '<p class="vt-nota">Sem captura. Rode com --captura para incluir uma.</p>'
        ),
    }
    google = "".join(
        f'<link rel="stylesheet" href="{h(url)}">\n' for url in ex.tipografia.google_fonts_urls if url.startswith("https://")
    )
    return modelo.substitute(
        titulo=h(f"Design system: {ex.nome}"),
        favicon=f'<link rel="icon" href="assets/{h(favicon_ativo.arquivo)}">\n' if favicon_ativo else "",
        google_fonts=google,
        logo=f'<img class="vt-logo" src="{logo}" alt="{h(ex.nome)}">' if logo else "",
        nome=h(f"Design system: {ex.nome}"),
        resumo=h(
            f"Extraído de {ex.url} em {ex.data.strftime('%d/%m/%Y')} pelo design-system-studio {VERSAO}, "
            "sem IA e sem rodar o JavaScript do site. Uso como referência: a marca é do dono do site."
        ),
        indice="".join(f'<a href="#{i}">{h(t)}</a>' for i, t in SECOES),
        secoes="\n".join(_secao(i, t, corpos[i]) for i, t in SECOES),
    )
