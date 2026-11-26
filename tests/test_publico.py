"""Repositório público: versão igual nos manifestos e nada de dado pessoal, token ou caminho da máquina (chaves privadas: forge gate, P-13)."""

from __future__ import annotations

import json
import re
import subprocess

from conftest import PLUGIN, RAIZ

PROIBIDOS = {
    "e-mail": re.compile(r"[\w.+-]+@[\w-]+\.(?:com|br|net|org|io)\b"),
    "caminho pessoal": re.compile(r"/(?:Users|home)/[A-Za-z]"),
    "chave AWS": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "token GitHub": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b"),
}
IGNORADOS = ("uv.lock",)


def _arquivos():
    saida = subprocess.run(["git", "ls-files", "-co", "--exclude-standard"], cwd=RAIZ, capture_output=True, text=True, check=True)
    for nome in saida.stdout.splitlines():
        caminho = RAIZ / nome
        if caminho.is_file() and not nome.endswith(IGNORADOS) and caminho.suffix not in (".png", ".ico"):
            yield nome, caminho.read_text(encoding="utf-8", errors="replace")


def test_versao_igual_em_todo_lugar():
    plugin = json.loads((PLUGIN / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    mercado = json.loads((RAIZ / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
    versao = plugin["version"]
    assert plugin["name"] == mercado["plugins"][0]["name"] == "design-system-studio"
    assert (RAIZ / mercado["plugins"][0]["source"]).resolve() == PLUGIN.resolve()
    assert f'version = "{versao}"' in (RAIZ / "pyproject.toml").read_text(encoding="utf-8")
    assert f'VERSAO = "{versao}"' in (PLUGIN / "skills" / "extrair-design-system" / "scripts" / "extrator" / "__init__.py").read_text(encoding="utf-8")
    readme = (RAIZ / "README.md").read_text(encoding="utf-8").replace("%C3%A3", "ã")
    assert f"versão-{versao}" in readme and f"| {versao} |" in readme
    assert f"### {versao}" in (RAIZ / "sdd" / "releases" / "history.md").read_text(encoding="utf-8")


def test_sem_dado_pessoal_nem_segredo():
    achados = [
        f"{nome}: {tipo}"
        for nome, texto in _arquivos()
        for tipo, padrao in PROIBIDOS.items()
        if padrao.search(texto)
    ]
    assert not achados, achados


def test_sem_workflow_de_ci():
    assert not (RAIZ / ".github" / "workflows").exists()
