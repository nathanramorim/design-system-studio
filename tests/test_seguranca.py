"""Segurança: recusa de endereço privado e de esquema, redirecionamento, limites de bytes e de tempo e limpeza."""

from __future__ import annotations

import time

import pytest
from conftest import EXEMPLO, atrasar, extrair, gotejar, responder, rodar, sem_tamanho, servidor, servir_pasta
from extrator.componentes import segura
from extrator.rede import EnderecoRecusado, conferir_ip
from extrator.svg import higienizar


@pytest.mark.parametrize(
    "url",
    [
        "http://10.0.0.1/",
        "http://192.168.1.1/",
        "http://172.16.0.1/",
        "http://169.254.169.254/latest/meta-data/",
        "http://100.64.0.1/",
        "http://0.0.0.0/",
        "http://[fd00::1]/",
        "http://[::ffff:10.0.0.1]/",
    ],
)
def test_recusa_rede_privada_mesmo_com_permitir_local(tmp_path, url):
    r = rodar("--url", url, "--saida", tmp_path, "--permitir-local")
    assert r.returncode == 2, r.stderr
    assert "recusado" in r.stderr
    assert not (tmp_path / "DESIGN.md").exists()


@pytest.mark.parametrize(
    "url", ["http://127.0.0.1/", "http://localhost/", "http://[::1]/", "http://2130706433/", "http://127.1/"]
)
def test_recusa_loopback_sem_permitir_local(tmp_path, url):
    r = rodar("--url", url, "--saida", tmp_path)
    assert r.returncode == 2, r.stderr
    assert "recusado" in r.stderr


@pytest.mark.parametrize(
    "url", ["file:///etc/passwd", "ftp://exemplo.invalid/", "javascript:alert(1)", "//sem-esquema.invalid", "https://user:senha@exemplo.invalid/"]
)
def test_recusa_esquema_e_credencial(tmp_path, url):
    r = rodar("--url", url, "--saida", tmp_path)
    assert r.returncode == 2, r.stderr


def test_redirecionamento_para_rede_privada_e_recusado(tmp_path):
    with servidor({"/": responder(302, "", Location="http://10.0.0.1/admin")}) as url:
        r = extrair(url, tmp_path)
    assert r.returncode == 2
    assert "10.0.0.1" in r.stderr


def test_recurso_na_rede_privada_vira_aviso(tmp_path):
    pagina = '<html><head><link rel="stylesheet" href="http://192.168.0.10/estilo.css"></head><body></body></html>'
    with servidor({"/": responder(200, pagina)}) as url:
        r = extrair(url, tmp_path)
    assert r.returncode == 0, r.stderr
    assert "AVISO | css | folha ignorada" in r.stdout and "recusado" in r.stdout


def test_pagina_acima_do_limite_de_bytes_sai_1(tmp_path):
    with servir_pasta(EXEMPLO) as url:
        r = extrair(url, tmp_path, "--limite-bytes", "1024")
    assert r.returncode == 1
    assert "limite de 1024" in r.stderr


def test_pagina_sem_content_length_para_no_limite(tmp_path):
    with servidor({"/": sem_tamanho(b"<html>" + b"a" * 50_000 + b"</html>")}) as url:
        r = extrair(url, tmp_path, "--limite-bytes", "4096")
    assert r.returncode == 1
    assert "passou do limite de 4096 bytes" in r.stderr


def test_folha_grande_vira_aviso(tmp_path):
    pagina = '<html><head><link rel="stylesheet" href="/grande.css"></head><body></body></html>'
    grande = "a{color:#123456}" * 20_000
    with servidor({"/": responder(200, pagina), "/grande.css": responder(200, grande, "text/css")}) as url:
        r = extrair(url, tmp_path, "--limite-bytes", "100000")
    assert r.returncode == 0, r.stderr
    assert "AVISO | css |" in r.stdout and "acima do limite de 100000" in r.stdout


def test_servidor_lento_sai_1(tmp_path):
    with servidor({"/": atrasar(4)}) as url:
        inicio = time.monotonic()
        r = extrair(url, tmp_path, "--tempo", "1")
    assert r.returncode == 1
    assert "limite de tempo" in r.stderr
    assert time.monotonic() - inicio < 30


def test_gotejamento_respeita_o_prazo_total(tmp_path):
    with servidor({"/": gotejar(0.2, 200)}) as url:
        inicio = time.monotonic()
        r = extrair(url, tmp_path, "--tempo", "1")
        duracao = time.monotonic() - inicio
    assert r.returncode == 1
    assert "limite de tempo" in r.stderr
    assert duracao < 20, "o prazo vale para o pedido todo, não por pedaço"


def test_conferir_ip():
    for ip in ("8.8.8.8", "2606:4700::1111"):
        conferir_ip(ip)
    conferir_ip("127.0.0.1", permitir_local=True)
    for ip in ("127.0.0.1", "10.1.2.3", "::1", "fe80::1", "224.0.0.1", "::ffff:192.168.0.1"):
        with pytest.raises(EnderecoRecusado):
            conferir_ip(ip)
    with pytest.raises(EnderecoRecusado):
        conferir_ip("10.1.2.3", permitir_local=True)


def test_svg_sem_script_nem_eventos():
    sujo = (
        '<svg viewBox="0 0 10 10" onload="alert(1)"><script>alert(2)</script>'
        '<foreignObject><div>x</div></foreignObject><a href="javascript:alert(3)"><rect width="5" height="5"/></a></svg>'
    )
    limpo = higienizar(sujo)
    assert limpo and "alert" not in limpo and "script" not in limpo.lower() and "foreignObject" not in limpo
    assert 'xmlns="http://www.w3.org/2000/svg"' in limpo
    assert higienizar('<!DOCTYPE svg [<!ENTITY a "b">]><svg>&a;</svg>') is None
    assert higienizar("<html><body>não é svg</body></html>") is None


def test_css_perigoso_nao_e_copiado():
    assert not segura("width", "expression(alert(1))")
    assert not segura("background", "url(javascript:alert(1))")
    assert not segura("behavior", "url(x.htc)")
    assert segura("background", "url(fundo.png) no-repeat")


def test_pagina_que_nao_e_html_sai_1(tmp_path):
    with servidor({"/": responder(200, '{"a": 1}', "application/json")}) as url:
        r = extrair(url, tmp_path)
    assert r.returncode == 1
    assert "não é HTML" in r.stderr
