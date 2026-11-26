#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""empacotar.py: gera o ZIP da skill extrair-design-system para enviar no app do Claude (claude.ai).

O claude.ai pede um ZIP com a pasta da skill na raiz (extrair-design-system/SKILL.md). O pacote é
determinístico: mesma árvore, mesmo ZIP (ordem fixa, data fixa, sem __pycache__ nem .DS_Store).

Uso:
  uv run scripts/empacotar.py [--saida dist/extrair-design-system.zip]
  python3 scripts/empacotar.py   (onde não houver uv)
"""

from __future__ import annotations

import argparse
import hashlib
import sys
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SKILL = RAIZ / "plugins" / "design-system-studio" / "skills" / "extrair-design-system"
NOME = SKILL.name
IGNORAR_PASTAS = {"__pycache__", ".pytest_cache", ".ruff_cache"}
IGNORAR_ARQUIVOS = {".DS_Store"}
DATA_FIXA = (2026, 1, 1, 0, 0, 0)


def arquivos(pasta: Path) -> list[Path]:
    """Arquivos da skill em ordem fixa, sem caches nem lixo do sistema."""
    lista = []
    for caminho in sorted(pasta.rglob("*")):
        relativo = caminho.relative_to(pasta)
        if any(parte in IGNORAR_PASTAS for parte in relativo.parts):
            continue
        if caminho.is_file() and caminho.name not in IGNORAR_ARQUIVOS:
            lista.append(caminho)
    return lista


def empacotar(saida: Path, pasta: Path = SKILL) -> Path:
    """Grava o ZIP com a pasta da skill na raiz e devolve o caminho."""
    if not (pasta / "SKILL.md").is_file():
        raise FileNotFoundError(f"SKILL.md não encontrado em {pasta}")
    saida.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(saida, "w", compression=zipfile.ZIP_DEFLATED) as zipado:
        for caminho in arquivos(pasta):
            info = zipfile.ZipInfo(f"{pasta.name}/{caminho.relative_to(pasta).as_posix()}", DATA_FIXA)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            zipado.writestr(info, caminho.read_bytes())
    return saida


def main(argv: list[str] | None = None) -> int:
    args = argparse.ArgumentParser(description="Gera o ZIP da skill para o claude.ai.")
    args.add_argument("--saida", type=Path, default=RAIZ / "dist" / f"{NOME}.zip")
    opcoes = args.parse_args(argv)
    try:
        zip_ = empacotar(opcoes.saida)
    except FileNotFoundError as erro:
        print(f"ERRO: {erro}", file=sys.stderr)
        return 1
    with zipfile.ZipFile(zip_) as zipado:
        total = len(zipado.namelist())
    soma = hashlib.sha256(zip_.read_bytes()).hexdigest()[:12]
    print(f"OK: {zip_} ({total} arquivos, {zip_.stat().st_size // 1024} KB, sha256 {soma})")
    print("Envie em claude.ai: Customize > Skills > + > Create skill > Upload a skill.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
