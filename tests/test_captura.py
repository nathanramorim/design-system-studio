"""Captura opcional com o Chrome headless (pulada quando não há Chrome na máquina)."""

from __future__ import annotations

import pytest
from conftest import EXEMPLO, extrair, servir_pasta
from extrator.captura import achar_chrome


@pytest.mark.skipif(achar_chrome() is None, reason="sem Google Chrome ou Chromium")
def test_captura_grava_png_e_cita_no_design(tmp_path):
    with servir_pasta(EXEMPLO) as url:
        r = extrair(url, tmp_path, "--captura")
    assert r.returncode == 0, r.stdout + r.stderr
    assert (tmp_path / "assets" / "captura.png").read_bytes().startswith(b"\x89PNG")
    assert "assets/captura.png" in (tmp_path / "DESIGN.md").read_text(encoding="utf-8")
    assert 'src="assets/captura.png"' in (tmp_path / "index.html").read_text(encoding="utf-8")
