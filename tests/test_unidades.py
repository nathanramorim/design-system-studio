"""Unidades: normalização de cores, var(), leitura de CSS, Google Fonts, seletores e papéis."""

from __future__ import annotations

from extrator import cores, folhas, tipografia
from extrator.componentes import tipo_do_seletor
from extrator.pagina import familias_google, ler


def test_cores_em_normaliza_formatos():
    assert cores.cores_em("#abc") == [("#AABBCC", 1.0)]
    assert cores.cores_em("#11223380")[0][0] == "#112233" and round(cores.cores_em("#11223380")[0][1], 2) == 0.5
    assert cores.cores_em("rgb(4 168 180)") == [("#04A8B4", 1.0)]
    assert cores.cores_em("rgba(4, 168, 180, .4)") == [("#04A8B4", 0.4)]
    assert cores.cores_em("rgb(100% 0% 0% / 50%)") == [("#FF0000", 0.5)]
    assert cores.cores_em("hsl(30, 100%, 50%)") == [("#FF8000", 1.0)]
    assert cores.cores_em("hsl(0.5turn 100% 50%)") == [("#00FFFF", 1.0)]
    assert cores.cores_em("1px solid white") == [("#FFFFFF", 1.0)]
    assert cores.cores_em("url(#abc) no-repeat") == []
    assert cores.cores_em("white-space") == []


def test_resolver_var_aninhado_e_reserva():
    mapa = {"--a": "var(--b)", "--b": "#123456"}
    assert cores.resolver_var("1px solid var(--a)", mapa) == "1px solid #123456"
    assert cores.resolver_var("var(--falta, rgb(1 2 3))", mapa) == "rgb(1 2 3)"
    assert cores.cores_em(cores.resolver_var("var(--loop)", {"--loop": "var(--loop)"})) == [], "ciclo termina sem cor"


def test_cromatica_por_canais():
    assert cores.cromatica("#04A8B4") and cores.cromatica("#E4B25A")
    assert not cores.cromatica("#F1ECE4") and not cores.cromatica("#A0A8B4") and not cores.cromatica("#090B10")


def test_folhas_lidas_com_aninhamento_media_e_import():
    css = """/* c */ @import url("a.css") screen; @import 'b.css';
    :root{--x:#fff}
    @media (max-width:600px){ .btn{color:red} @supports (display:grid){.card{gap:4px}} }
    .btn{background:url(data:image/png;base64,AA=);color:var(--x)!important; &:hover{color:blue} .ico{width:1px}}
    @keyframes k{from{opacity:0}to{opacity:1}}
    @font-face{font-family:"X";src:url(x.woff2)}"""
    regras, fontes, imports = folhas.ler(css, "t")
    assert imports == ["a.css", "b.css"]
    assert [(r.seletor, r.contexto) for r in regras] == [
        (":root", ()),
        (".btn", ("@media (max-width:600px)",)),
        (".card", ("@media (max-width:600px)", "@supports (display:grid)")),
        (".btn", ()),
        (".btn:hover", ()),
        (".btn .ico", ()),
    ]
    assert regras[3].declaracoes[0] == ("background", "url(data:image/png;base64,AA=)")
    assert fontes == [{"font-family": '"X"', "src": "url(x.woff2)"}]


def test_google_fonts_css_e_css2():
    assert familias_google("https://fonts.googleapis.com/css2?family=Geist:wght@400;600&family=Fira+Code&display=swap") == [
        "Geist", "Fira Code",
    ]
    assert familias_google("https://fonts.googleapis.com/css?family=Open+Sans:400,700|Roboto") == ["Open Sans", "Roboto"]


def test_tipo_do_seletor():
    casos = {
        ".btn-primary:hover": "botoes", "button": "botoes", "input[type=submit]": "botoes", "nav a": "links",
        ".card .card__title": "cartoes", ".card h3": "cartoes", ".form-control": "campos", "textarea": "campos",
        ".site-header": "cabecalho", "footer p": "rodape", ".hero": None, "body": None, "h1": None,
    }
    for seletor, tipo in casos.items():
        assert tipo_do_seletor(seletor) == tipo, seletor


def test_papeis_de_site_neutro():
    regras, _, _ = folhas.ler("body{background:#ffffff;color:#222} p{color:#666}", "t")
    paleta = cores.analisar(regras, [])
    assert paleta.papeis["fundo"].hex == "#FFFFFF" and paleta.papeis["texto"].hex == "#222222"
    assert paleta.papeis["primaria"].hex == "#222222" and "neutro" in paleta.papeis["primaria"].motivo
    assert paleta.papeis["texto_suave"].hex == "#666666"


def test_fundo_sem_body_usa_o_mais_usado():
    regras, _, _ = folhas.ler(".a{background:#101820}.b{background:#101820}.c{background:#ffffff}", "t")
    papel = cores.analisar(regras, []).papeis["fundo"]
    assert papel.hex == "#101820" and "mais usada em fundos" in papel.motivo


def test_familia_principal_ignora_pilha_do_sistema():
    regras, _, _ = folhas.ler('body{font-family:-apple-system,"Segoe UI","Open Sans",sans-serif}', "t")
    tipos = tipografia.analisar(regras, [], [], {})
    assert tipos.papeis["texto"].familia == "Open Sans"
    regras, _, _ = folhas.ler('body{font-family:-apple-system,"Segoe UI",Roboto,sans-serif}', "t")
    assert tipografia.analisar(regras, [], [], {}).papeis["texto"].familia == "fontes do sistema"


def test_svg_inline_do_cabecalho_preserva_maiusculas():
    pagina = ler(
        '<header><a class="marca" href="/"><svg viewBox="0 0 10 10"><linearGradient id="g"></linearGradient>'
        '<script>alert(1)</script><path d="M0 0"/></svg></a></header>',
        "https://exemplo.invalid/",
    )
    markup, cabecalho, logo = pagina.svgs[0]
    assert cabecalho and logo
    assert "<linearGradient" in markup and "</linearGradient>" in markup and "viewBox" in markup
    assert "alert" not in markup
