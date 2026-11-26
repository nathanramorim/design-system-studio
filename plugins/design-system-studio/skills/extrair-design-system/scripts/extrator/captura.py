"""Captura: tira uma captura de tela com o Chrome headless pelo protocolo DevTools (CDP), só com a stdlib.

O JavaScript do site fica desligado (flag de inicialização e `Emulation.setScriptExecutionDisabled`
antes de navegar). O perfil do Chrome é temporário e apagado no fim.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import shutil
import socket
import struct
import subprocess
import tempfile
import time
import urllib.request
from pathlib import Path

from . import USER_AGENT

GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"


class FalhaCaptura(RuntimeError):
    """O Chrome não abriu, não respondeu ou não navegou."""


def achar_chrome() -> str | None:
    candidatos = [
        os.environ.get("CHROME_BIN", ""),
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        shutil.which("google-chrome") or "",
        shutil.which("google-chrome-stable") or "",
        shutil.which("chromium") or "",
        shutil.which("chromium-browser") or "",
        shutil.which("chrome") or "",
    ]
    return next((c for c in candidatos if c and Path(c).exists()), None)


class _WebSocket:
    """Cliente WebSocket mínimo para o CDP: frames mascarados e mensagens fragmentadas."""

    def __init__(self, porta: int, caminho: str, tempo: float):
        self.sock = socket.create_connection(("127.0.0.1", porta), timeout=tempo)
        chave = base64.b64encode(os.urandom(16)).decode()
        self.sock.sendall(
            (
                f"GET {caminho} HTTP/1.1\r\nHost: 127.0.0.1:{porta}\r\nUpgrade: websocket\r\n"
                f"Connection: Upgrade\r\nSec-WebSocket-Key: {chave}\r\nSec-WebSocket-Version: 13\r\n\r\n"
            ).encode()
        )
        cabeca = bytearray()
        while b"\r\n\r\n" not in cabeca:
            pedaco = self.sock.recv(4096)
            if not pedaco:
                raise FalhaCaptura("o Chrome fechou a conexão no handshake")
            cabeca.extend(pedaco)
        topo, _, resto = bytes(cabeca).partition(b"\r\n\r\n")
        self.buf = bytearray(resto)
        linhas = topo.decode("latin-1").split("\r\n")
        aceite = base64.b64encode(hashlib.sha1((chave + GUID).encode()).digest()).decode()
        if " 101 " not in linhas[0] or not any(linha.lower() == f"sec-websocket-accept: {aceite}".lower() for linha in linhas):
            raise FalhaCaptura("handshake do WebSocket recusado")

    def _ler(self, n: int) -> bytes:
        while len(self.buf) < n:
            pedaco = self.sock.recv(max(65536, n - len(self.buf)))
            if not pedaco:
                raise FalhaCaptura("o Chrome fechou a conexão")
            self.buf.extend(pedaco)
        dados = bytes(self.buf[:n])
        del self.buf[:n]
        return dados

    def enviar(self, texto: str) -> None:
        carga = texto.encode()
        n = len(carga)
        cabeca = bytearray([0x81])
        if n < 126:
            cabeca.append(0x80 | n)
        elif n < 65536:
            cabeca.append(0x80 | 126)
            cabeca += struct.pack(">H", n)
        else:
            cabeca.append(0x80 | 127)
            cabeca += struct.pack(">Q", n)
        mascara = os.urandom(4)
        self.sock.sendall(bytes(cabeca) + mascara + bytes(b ^ mascara[i % 4] for i, b in enumerate(carga)))

    def receber(self) -> bytes:
        mensagem = bytearray()
        while True:
            b1, b2 = self._ler(2)
            fim, opcode, n = b1 & 0x80, b1 & 0x0F, b2 & 0x7F
            if n == 126:
                n = struct.unpack(">H", self._ler(2))[0]
            elif n == 127:
                n = struct.unpack(">Q", self._ler(8))[0]
            mascara = self._ler(4) if b2 & 0x80 else None
            carga = self._ler(n) if n else b""
            if mascara:
                carga = bytes(b ^ mascara[i % 4] for i, b in enumerate(carga))
            if opcode == 0x8:
                raise FalhaCaptura("o Chrome encerrou a conexão")
            if opcode in (0x9, 0xA):
                continue
            mensagem = bytearray(carga) if opcode in (0x1, 0x2) else mensagem + carga
            if fim:
                return bytes(mensagem)

    def fechar(self) -> None:
        try:
            self.sock.close()
        except OSError:
            pass


class _Aba:
    def __init__(self, ws: _WebSocket):
        self.ws, self.proximo, self.eventos = ws, 0, []

    def chamar(self, metodo: str, parametros: dict | None = None, tempo: float = 30) -> dict:
        self.proximo += 1
        meu = self.proximo
        self.ws.enviar(json.dumps({"id": meu, "method": metodo, "params": parametros or {}}))
        prazo = time.monotonic() + tempo
        while True:
            self.ws.sock.settimeout(max(0.5, prazo - time.monotonic()))
            msg = json.loads(self.ws.receber())
            if msg.get("id") == meu:
                if "error" in msg:
                    raise FalhaCaptura(f"{metodo}: {msg['error'].get('message', msg['error'])}")
                return msg.get("result", {})
            if "method" in msg:
                self.eventos.append(msg["method"])
            if time.monotonic() > prazo:
                raise FalhaCaptura(f"{metodo} passou do tempo")

    def esperar(self, evento: str, tempo: float) -> None:
        prazo = time.monotonic() + tempo
        while evento not in self.eventos:
            restante = prazo - time.monotonic()
            if restante <= 0:
                raise FalhaCaptura(f"a página não terminou de carregar em {tempo:g} s")
            self.ws.sock.settimeout(restante)
            msg = json.loads(self.ws.receber())
            if "method" in msg:
                self.eventos.append(msg["method"])


def capturar(url: str, destino: Path, largura: int = 1440, altura: int = 900, tempo: float = 30.0) -> Path:
    """Grava um PNG da primeira dobra da página. Lança FalhaCaptura se não conseguir."""
    chrome = achar_chrome()
    if not chrome:
        raise FalhaCaptura("Google Chrome ou Chromium não encontrado (defina CHROME_BIN)")
    perfil = tempfile.mkdtemp(prefix="design-system-studio-")
    processo = subprocess.Popen(
        [
            chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--mute-audio", "--no-first-run",
            "--no-default-browser-check", "--disable-extensions", "--blink-settings=scriptEnabled=false",
            f"--user-data-dir={perfil}", "--remote-debugging-port=0", "about:blank",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    ws = None
    try:
        arquivo_porta = Path(perfil) / "DevToolsActivePort"
        prazo = time.monotonic() + tempo
        while not arquivo_porta.exists() or not arquivo_porta.read_text().strip():
            if processo.poll() is not None or time.monotonic() > prazo:
                raise FalhaCaptura("o Chrome não abriu a porta de depuração")
            time.sleep(0.1)
        porta = int(arquivo_porta.read_text().splitlines()[0])
        pedido = urllib.request.Request(f"http://127.0.0.1:{porta}/json/new?about:blank", method="PUT")
        info = json.loads(urllib.request.urlopen(pedido, timeout=15).read())
        ws = _WebSocket(porta, "/" + info["webSocketDebuggerUrl"].split("/", 3)[3], tempo)
        aba = _Aba(ws)
        aba.chamar("Emulation.setScriptExecutionDisabled", {"value": True})
        aba.chamar("Emulation.setUserAgentOverride", {"userAgent": USER_AGENT})
        aba.chamar(
            "Emulation.setDeviceMetricsOverride",
            {"width": largura, "height": altura, "deviceScaleFactor": 1, "mobile": False},
        )
        aba.chamar("Page.enable")
        resultado = aba.chamar("Page.navigate", {"url": url}, tempo=tempo)
        if resultado.get("errorText"):
            raise FalhaCaptura(f"o Chrome não abriu a página: {resultado['errorText']}")
        aba.esperar("Page.loadEventFired", tempo)
        png = base64.b64decode(aba.chamar("Page.captureScreenshot", {"format": "png"}, tempo=tempo)["data"])
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_bytes(png)
        return destino
    except (OSError, ValueError, KeyError) as erro:
        raise FalhaCaptura(f"falha ao falar com o Chrome: {erro}") from erro
    finally:
        if ws:
            ws.fechar()
        if processo.poll() is None:
            processo.terminate()
            try:
                processo.wait(timeout=5)
            except subprocess.TimeoutExpired:
                processo.kill()
                processo.wait()
        for _ in range(20):
            shutil.rmtree(perfil, ignore_errors=True)
            if not Path(perfil).exists():
                break
            time.sleep(0.25)
