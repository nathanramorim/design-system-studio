"""Pacote para o claude.ai: pasta da skill na raiz, sem caches e determinístico."""

import hashlib
import importlib.util
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("empacotar", RAIZ / "scripts" / "empacotar.py")
empacotar = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(empacotar)


def test_zip_tem_a_pasta_da_skill_na_raiz(tmp_path):
    zip_ = empacotar.empacotar(tmp_path / "skill.zip")
    nomes = zipfile.ZipFile(zip_).namelist()
    assert "extrair-design-system/SKILL.md" in nomes
    assert all(nome.startswith("extrair-design-system/") for nome in nomes)
    assert any(nome.startswith("extrair-design-system/scripts/") for nome in nomes)


def test_zip_sem_cache_nem_lixo(tmp_path):
    nomes = zipfile.ZipFile(empacotar.empacotar(tmp_path / "skill.zip")).namelist()
    assert not any("__pycache__" in nome or nome.endswith(".DS_Store") for nome in nomes)


def test_zip_e_deterministico(tmp_path):
    a = empacotar.empacotar(tmp_path / "a.zip").read_bytes()
    b = empacotar.empacotar(tmp_path / "b.zip").read_bytes()
    assert hashlib.sha256(a).digest() == hashlib.sha256(b).digest()


def test_sem_skill_md_falha(tmp_path):
    pasta = tmp_path / "vazia"
    pasta.mkdir()
    try:
        empacotar.empacotar(tmp_path / "x.zip", pasta)
    except FileNotFoundError:
        return
    raise AssertionError("deveria falhar sem SKILL.md")
