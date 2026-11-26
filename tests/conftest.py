"""Fixtures: o site fictício servido por http.server num thread e o extrator chamado pela CLI real (uv run)."""

from __future__ import annotations

import functools
import http.server
import json
import shutil
import subprocess
import sys
import threading
import time
import urllib.parse
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
PLUGIN = RAIZ / "plugins" / "design-system-studio"
SKILL = PLUGIN / "skills" / "extrair-design-system"
SCRIPTS = SKILL / "scripts"
SCRIPT = SCRIPTS / "extrair.py"
EXEMPLO = SKILL / "exemplos" / "site-exemplo"
MODELOS = SKILL / "templates"
DATA = "2026-11-25"

sys.path.insert(0, str(SCRIPTS))


def rodar(*args: str | Path, timeout: float = 120) -> subprocess.CompletedProcess:
    uv = shutil.which("uv")
    cmd = [uv, "run", "--quiet", str(SCRIPT)] if uv else [sys.executable, str(SCRIPT)]
    return subprocess.run(
        [*cmd, *map(str, args)], capture_output=True, text=True, encoding="utf-8", timeout=timeout
    )


def extrair(url: str, saida: Path, *extras: str) -> subprocess.CompletedProcess:
    return rodar("--url", url, "--saida", saida, "--permitir-local", "--data", DATA, *extras)


class _Silencioso(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


@contextmanager
def servir_pasta(pasta: Path) -> Iterator[str]:
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(_Silencioso, directory=str(pasta)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        yield f"http://127.0.0.1:{srv.server_address[1]}/"
    finally:
        srv.shutdown()
        srv.server_close()


Rota = Callable[[http.server.BaseHTTPRequestHandler], None]


def responder(status: int, corpo: bytes | str = b"", tipo: str = "text/html; charset=utf-8", **cabecalhos: str) -> Rota:
    dados = corpo.encode("utf-8") if isinstance(corpo, str) else corpo

    def rota(h: http.server.BaseHTTPRequestHandler) -> None:
        h.send_response(status)
        h.send_header("Content-Type", tipo)
        for nome, valor in cabecalhos.items():
            h.send_header(nome.replace("_", "-"), valor)
        h.send_header("Content-Length", str(len(dados)))
        h.end_headers()
        h.wfile.write(dados)

    return rota


def atrasar(segundos: float) -> Rota:
    def rota(h: http.server.BaseHTTPRequestHandler) -> None:
        time.sleep(segundos)
        responder(200, "<html><body>tarde</body></html>")(h)

    return rota


def gotejar(intervalo: float, total: int) -> Rota:
    """Manda os cabeçalhos e depois um byte por vez: o socket nunca fica parado tempo bastante para estourar."""

    def rota(h: http.server.BaseHTTPRequestHandler) -> None:
        h.send_response(200)
        h.send_header("Content-Type", "text/html")
        h.send_header("Content-Length", str(total))
        h.end_headers()
        for _ in range(total):
            h.wfile.write(b"a")
            h.wfile.flush()
            time.sleep(intervalo)

    return rota


def sem_tamanho(corpo: bytes) -> Rota:
    """Resposta HTTP/1.0 sem Content-Length: só o limite na leitura segura o tamanho."""

    def rota(h: http.server.BaseHTTPRequestHandler) -> None:
        h.send_response(200)
        h.send_header("Content-Type", "text/html")
        h.send_header("Connection", "close")
        h.end_headers()
        h.wfile.write(corpo)
        h.close_connection = True

    return rota


@contextmanager
def servidor(rotas: dict[str, Rota]) -> Iterator[str]:
    class Handler(http.server.BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.0"

        def do_GET(self):
            rota = rotas.get(urllib.parse.urlsplit(self.path).path, responder(404, "não encontrado", "text/plain"))
            try:
                rota(self)
            except OSError:
                pass

        def log_message(self, *args):
            pass

    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        yield f"http://127.0.0.1:{srv.server_address[1]}/"
    finally:
        srv.shutdown()
        srv.server_close()


@pytest.fixture(scope="session")
def extraido(tmp_path_factory) -> tuple[Path, subprocess.CompletedProcess, dict]:
    """O site fictício extraído uma vez, com --json; os testes leem a pasta e o resumo."""
    saida = tmp_path_factory.mktemp("extraido") / "ds"
    with servir_pasta(EXEMPLO) as url:
        r = extrair(url, saida, "--json")
    assert r.returncode == 0, r.stderr
    return saida, r, json.loads(r.stdout)
