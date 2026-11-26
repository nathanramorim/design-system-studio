"""A skill se ativa pelo pedido certo e não aponta para arquivo que não existe."""

from __future__ import annotations

import re

from conftest import PLUGIN, SKILL


def _frontmatter() -> dict[str, str]:
    texto = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    bloco = re.match(r"^---\n(.*?)\n---\n", texto, re.S)
    assert bloco, "SKILL.md sem frontmatter"
    return dict(linha.split(": ", 1) for linha in bloco.group(1).splitlines() if ": " in linha)


def test_frontmatter_nome_e_descricao():
    fm = _frontmatter()
    assert fm["name"] == SKILL.name
    descricao = fm["description"]
    assert len(descricao) <= 1024, len(descricao)
    for termo in ("design system", "URL", "paleta", "fontes", "extrair.py", "DESIGN.md", "tokens.css", "vitrine"):
        assert termo.lower() in descricao.lower(), termo


def test_referencias_citadas_existem_e_todas_sao_citadas():
    texto = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    citadas = set(re.findall(r"references/([\w-]+\.md)", texto))
    existentes = {p.name for p in (SKILL / "references").glob("*.md")}
    assert citadas == existentes, citadas ^ existentes


def test_modelos_citados_existem():
    texto = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    nomes = set(re.findall(r"templates/([\w.-]+\.\w+)", texto))
    assert nomes == {p.name for p in (SKILL / "templates").iterdir()}, nomes


def test_opcoes_documentadas_batem_com_o_cli():
    texto = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    script = (SKILL / "scripts" / "extrair.py").read_text(encoding="utf-8")
    opcoes = set(re.findall(r'add_argument\("(--[\w-]+)"', script))
    for opcao in opcoes:
        assert f"`{opcao}`" in texto, opcao


def test_comando_aponta_para_a_skill():
    comando = (PLUGIN / "commands" / "extrair-design-system.md").read_text(encoding="utf-8")
    assert "skills/extrair-design-system/SKILL.md" in comando
    assert "extrair.py" in comando
