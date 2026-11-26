"""Extração do site fictício: cores, fontes, tokens, componentes, logo, contrato do CLI e determinismo."""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET

from conftest import EXEMPLO, extrair, responder, servidor, servir_pasta


def test_json_tem_o_contrato(extraido):
    _, _, dados = extraido
    assert set(dados) == {"ok", "url", "saida", "nome", "avisos", "resumo"}
    assert dados["ok"] is True and dados["nome"] == "Oficina Exemplo"
    assert dados["avisos"] == []


def test_papeis_das_cores(extraido):
    _, _, dados = extraido
    papeis = dados["resumo"]["papeis"]
    assert papeis["fundo"] == "#FBF8F3"
    assert papeis["texto"] == "#1E1B16"
    assert papeis["primaria"] == "#1F6F5C"
    assert papeis["destaque"] == "#E07A2F"
    assert papeis["superficie"] == "#F1ECE4"


def test_cores_normalizadas_e_var_resolvido(extraido):
    saida, _, _ = extraido
    design = (saida / "DESIGN.md").read_text(encoding="utf-8")
    assert "| `--ds-cor-1` | `#1F6F5C` | 7 |" in design, "var(--cor-marca) e rgb(31 111 92) somam na mesma cor"
    assert "`#FF8000`" in design, "hsl(30, 100%, 50%) vira #FF8000"
    assert "rgba(30, 27, 22, 0.12)" in design, "transparência listada à parte"
    assert "#ABCDEF" not in design, "a cor só existe no JavaScript, que nunca roda"


def test_fontes(extraido):
    saida, _, dados = extraido
    assert dados["resumo"]["fontes"] == {"texto": "Inter", "titulos": "Fraunces", "mono": "Oficina Mono"}
    design = (saida / "DESIGN.md").read_text(encoding="utf-8")
    assert "| Inter | 2 | Google Fonts, font-family |" in design
    assert "| Oficina Mono | 1 | @font-face, font-family |" in design
    assert dados["resumo"]["tamanhos"] == ["12px", "14px", "15px", "16px", "24px", "32px", "40px"]


def test_tokens_css(extraido):
    saida, _, _ = extraido
    tokens = (saida / "tokens.css").read_text(encoding="utf-8")
    assert "--cor-marca: #1F6F5C;" in tokens, "custom properties do :root como estão (vindas do @import)"
    assert "--ds-cor-primaria: #1F6F5C;" in tokens
    assert "--ds-fonte-titulos: Fraunces, Georgia, serif;" in tokens
    assert "--ds-raio-1: 10px;" in tokens and "--ds-sombra-1: 0 6px 20px rgba(30, 27, 22, 0.08);" in tokens
    assert '@font-face {\n  font-family: "Oficina Mono";' in tokens
    assert "--so-com-js" not in tokens


def test_componentes(extraido):
    saida, _, dados = extraido
    assert dados["resumo"]["componentes"] == {
        "botoes": 6, "links": 3, "cartoes": 3, "campos": 2, "cabecalho": 1, "rodape": 1,
    }
    css = (saida / "components.css").read_text(encoding="utf-8")
    for trecho in (
        "/* ========== Botões: 6 regras ========== */",
        ".btn-primario {\n  background: var(--cor-marca);",
        "@media (max-width: 600px) {\n  .btn {",
        ".card {", ".campo:focus {", ".site-header {", ".rodape {",
    ):
        assert trecho in css, trecho
    assert ".hero" not in css and "body {" not in css, "só componentes entram"


def test_logo_favicon_e_icones(extraido):
    saida, _, dados = extraido
    assert dados["resumo"]["assets"] == ["og-imagem.png", "favicon.svg", "icone-1.png", "logo.svg"]
    logo = ET.fromstring((saida / "assets" / "logo.svg").read_text(encoding="utf-8"))
    assert logo.tag.endswith("svg")
    assert (saida / "assets" / "icone-1.png").read_bytes().startswith(b"\x89PNG")
    assert "imagem com 'logo' no cabeçalho" in (saida / "DESIGN.md").read_text(encoding="utf-8")


def test_saida_sem_pendencia_de_modelo(extraido):
    saida, _, _ = extraido
    for nome in ("DESIGN.md", "index.html", "tokens.css", "components.css"):
        assert "${" not in (saida / nome).read_text(encoding="utf-8"), nome


def test_mesma_entrada_mesma_saida(tmp_path):
    with servir_pasta(EXEMPLO) as url:
        assert extrair(url, tmp_path / "a").returncode == 0
        assert extrair(url, tmp_path / "b").returncode == 0
    for arquivo in sorted((tmp_path / "a").rglob("*")):
        if arquivo.is_file():
            outro = tmp_path / "b" / arquivo.relative_to(tmp_path / "a")
            assert outro.read_bytes() == arquivo.read_bytes(), arquivo.name


def test_design_existente_pede_sobrescrever(tmp_path):
    with servir_pasta(EXEMPLO) as url:
        assert extrair(url, tmp_path).returncode == 0
        r = extrair(url, tmp_path)
        assert r.returncode == 2 and "--sobrescrever" in r.stderr
        assert extrair(url, tmp_path, "--sobrescrever").returncode == 0


def test_nome_pela_opcao(tmp_path):
    with servir_pasta(EXEMPLO) as url:
        r = extrair(url, tmp_path, "--nome", "Marca Teste", "--json")
    assert json.loads(r.stdout)["nome"] == "Marca Teste"
    assert (tmp_path / "DESIGN.md").read_text(encoding="utf-8").startswith("# Design system: Marca Teste")


MINIMO = """<!doctype html><html><head><title>Domínio de Exemplo</title>
<style>body{background:#eee;width:60vw;margin:15vh auto;font-family:system-ui,sans-serif}
h1{font-size:1.5em}a:link,a:visited{color:#348}</style></head>
<body><div><h1>Domínio de Exemplo</h1><p>Página mínima.</p><a href="https://exemplo.invalid/">Saiba mais</a></div></body></html>"""


def test_site_minimo_sem_logo_nem_css_externo(tmp_path):
    with servidor({"/": responder(200, MINIMO)}) as url:
        r = extrair(url, tmp_path, "--json")
    assert r.returncode == 0, r.stderr
    dados = json.loads(r.stdout)
    assert dados["nome"] == "Domínio de Exemplo"
    assert dados["resumo"]["papeis"]["fundo"] == "#EEEEEE"
    assert dados["resumo"]["papeis"]["primaria"] == "#334488"
    assert dados["resumo"]["fontes"]["texto"] == "fontes do sistema"
    assert any("logo não encontrado" in a for a in dados["avisos"])
    assert any("favicon" in a for a in dados["avisos"])
    vitrine = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert "Nenhum logo, favicon ou ícone encontrado." in vitrine
    assert "logo não encontrado" in (tmp_path / "DESIGN.md").read_text(encoding="utf-8")


def test_favicon_vazio_e_ignorado_sem_tentar_duas_vezes(tmp_path):
    pagina = '<html><head><link rel="icon" href="data:,"><title>Vazio</title></head><body></body></html>'
    with servidor({"/": responder(200, pagina)}) as url:
        r = extrair(url, tmp_path, "--json")
    avisos = json.loads(r.stdout)["avisos"]
    assert not any("data:" in a for a in avisos), avisos
    assert sum("favicon.ico" in a for a in avisos) == 1
