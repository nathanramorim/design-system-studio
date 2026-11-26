#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""extrair.py: extrai o design system de um site pela URL, de forma determinística e sem IA.

Uso:
  uv run scripts/extrair.py --url https://www.exemplo.com.br --saida PASTA [--nome MARCA] [--captura]
                            [--sobrescrever] [--limite-bytes N] [--tempo S] [--data AAAA-MM-DD] [--json]
                            [--permitir-local]

Gera em PASTA: DESIGN.md, tokens.css, components.css, index.html (vitrine) e assets/.
Saída: uma linha por etapa, "NIVEL | etapa | detalhe" (OK ou AVISO), e "RESULTADO: ...".
Com --json: {"ok", "url", "saida", "nome", "avisos", "resumo"}.
Códigos: 0 estrutura gerada; 1 a página principal não veio; 2 uso inválido ou endereço recusado.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from extrator import VERSAO, captura, componentes, cores, folhas, marca, medidas, pagina, tipografia  # noqa: E402
from extrator.modelo import Extracao  # noqa: E402
from extrator.rede import Cliente, EnderecoRecusado, FalhaDeRede, Limites, validar_url  # noqa: E402
from extrator.saida import componentes_css, design_md, tokens_css, vitrine  # noqa: E402

MODELOS = Path(__file__).resolve().parent.parent / "templates"
TIPOS_HTML = ("text/html", "application/xhtml+xml", "")


class UsoInvalido(ValueError):
    """Opção ou pasta de saída inválida."""


def _args(argv):
    p = argparse.ArgumentParser(
        prog="extrair.py",
        description="Extrai o design system de um site (DESIGN.md, tokens.css, components.css, index.html e assets/).",
    )
    p.add_argument("--url", required=True, help="endereço http ou https do site")
    p.add_argument("--saida", required=True, help="pasta onde a estrutura é gravada")
    p.add_argument("--nome", help="nome da marca (padrão: og:site_name, título da página ou domínio)")
    p.add_argument("--captura", action="store_true", help="tira uma captura com o Chrome headless (JavaScript desligado)")
    p.add_argument("--sobrescrever", action="store_true", help="regrava uma pasta que já tem DESIGN.md")
    p.add_argument("--limite-bytes", type=int, default=2_000_000, help="limite por arquivo baixado (padrão: 2000000)")
    p.add_argument("--tempo", type=float, default=15.0, help="limite de tempo por pedido, em segundos (padrão: 15)")
    p.add_argument("--data", help="data da extração no DESIGN.md, AAAA-MM-DD (padrão: hoje)")
    p.add_argument("--json", action="store_true", help="saída em JSON")
    p.add_argument("--permitir-local", action="store_true", help="aceita o loopback (127.0.0.1, ::1), para testes")
    return p.parse_args(argv)


def _data(texto: str | None) -> dt.date:
    if not texto:
        return dt.date.today()
    try:
        return dt.date.fromisoformat(texto)
    except ValueError as erro:
        raise UsoInvalido(f"--data deve ser AAAA-MM-DD: {texto!r}") from erro


def _nome(args_nome: str | None, pag: pagina.Pagina) -> str:
    if args_nome and args_nome.strip():
        return " ".join(args_nome.split())[:80]
    for chave in ("og:site_name", "application-name"):
        if pag.meta.get(chave):
            return pag.meta[chave][:80]
    if pag.titulo:
        primeiro = re.split(r"\s+[|\-\u2013\u2014\u00b7:]\s+", pag.titulo)[0].strip()
        if primeiro:
            return primeiro[:80]
    host = urllib.parse.urlsplit(pag.url).hostname or "site"
    return host.removeprefix("www.")


def _plural(n: int, singular: str, plural: str) -> str:
    return f"{n} {singular if n == 1 else plural}"


def _conferir_saida(saida: Path, sobrescrever: bool) -> None:
    if saida.exists() and not saida.is_dir():
        raise UsoInvalido(f"--saida aponta para um arquivo: {saida}")
    if (saida / "DESIGN.md").exists() and not sobrescrever:
        raise UsoInvalido(f"{saida / 'DESIGN.md'} já existe; use --sobrescrever para regravar")


def extrair(args) -> tuple[Extracao, Path, list[tuple[str, str, str]]]:
    if args.limite_bytes < 1024 or args.tempo <= 0:
        raise UsoInvalido("--limite-bytes precisa ser de pelo menos 1024 e --tempo maior que zero")
    data = _data(args.data)
    validar_url(args.url)
    saida = Path(args.saida)
    _conferir_saida(saida, args.sobrescrever)
    cliente = Cliente(
        Limites(bytes_por_arquivo=args.limite_bytes, bytes_total=max(12_000_000, args.limite_bytes * 6), tempo=args.tempo),
        permitir_local=args.permitir_local,
    )
    linhas: list[tuple[str, str, str]] = []
    resposta = cliente.baixar(args.url, aceitar="text/html,application/xhtml+xml;q=0.9,*/*;q=0.1")
    if resposta.tipo not in TIPOS_HTML:
        raise FalhaDeRede(f"a página não é HTML ({resposta.tipo})")
    linhas.append(("OK", "pagina", f"HTTP {resposta.status}, {len(resposta.corpo)} bytes, {resposta.url}"))

    pag = pagina.ler(resposta.texto(), resposta.url)
    css = folhas.coletar(cliente, pag)
    linhas.append(("OK", "css", f"{len(css.baixadas)} folhas ({css.por_import} por @import), {len(css.regras)} regras"))
    avisos = [("css", a) for a in css.avisos]

    mapa = cores.mapa_custom(css.regras)
    paleta = cores.analisar(css.regras, pag.estilos_inline, pag.meta.get("theme-color", ""))
    tipos = tipografia.analisar(css.regras, css.fontes, css.google_fonts, mapa)
    med = medidas.analisar(css.regras, mapa)
    comps = componentes.analisar(css.regras, pag.elementos, pag.url)
    p = paleta.papeis
    linhas.append((
        "OK", "cores",
        f"{_plural(len(paleta.cores), 'cor', 'cores')}; fundo {p['fundo'].hex}, texto {p['texto'].hex}, "
        f"primária {p['primaria'].hex}, destaque {p['destaque'].hex}",
    ))
    nomes = {"texto": "texto", "titulos": "títulos", "mono": "código"}
    familias = ", ".join(f"{f.familia} ({nomes[papel]})" for papel, f in tipos.papeis.items())
    linhas.append(("OK", "fontes", f"{familias}; {_plural(len(tipos.tamanhos), 'tamanho', 'tamanhos')}"))
    linhas.append(("OK", "medidas", ", ".join(_plural(len(v), s, p) for v, s, p in (
        (med.raios, "raio", "raios"), (med.sombras, "sombra", "sombras"), (med.espacos, "espaço", "espaços")))))
    resumo_comp = ", ".join(f"{c.nome.lower()} {len(c.regras)}" for c in comps) or "nenhum reconhecido"
    linhas.append(("OK", "componentes", resumo_comp))

    pasta_assets = saida / "assets"
    marca.limpar(pasta_assets)
    avisos_marca: list[str] = []
    ativos = marca.coletar(cliente, pag, pasta_assets, avisos_marca)
    avisos += [("marca", a) for a in avisos_marca]
    linhas.append(("OK", "marca", ", ".join(f"{a.papel} {a.arquivo}" for a in ativos) or "nenhuma imagem"))

    arquivo_captura = None
    if args.captura:
        try:
            captura.capturar(resposta.url, pasta_assets / "captura.png", tempo=max(30.0, args.tempo))
            arquivo_captura = "captura.png"
            linhas.append(("OK", "captura", "assets/captura.png (1440x900, sem JavaScript)"))
        except captura.FalhaCaptura as erro:
            avisos.append(("captura", str(erro)))

    ex = Extracao(
        url=resposta.url,
        nome=_nome(args.nome, pag),
        data=data,
        paleta=paleta,
        tipografia=tipos,
        medidas=med,
        componentes=comps,
        ativos=ativos,
        folhas=len(css.baixadas),
        por_import=css.por_import,
        regras=len(css.regras),
        captura=arquivo_captura,
        avisos=[f"{etapa}: {texto}" for etapa, texto in avisos],
    )
    saida.mkdir(parents=True, exist_ok=True)
    (saida / "tokens.css").write_text(tokens_css.gerar(ex), encoding="utf-8")
    (saida / "components.css").write_text(componentes_css.gerar(ex), encoding="utf-8")
    (saida / "DESIGN.md").write_text(design_md.gerar(ex, MODELOS), encoding="utf-8")
    (saida / "index.html").write_text(vitrine.gerar(ex, MODELOS), encoding="utf-8")
    linhas += [("AVISO", etapa, texto) for etapa, texto in avisos]
    return ex, saida, linhas


def _resumo(ex: Extracao) -> dict:
    return {
        "versao": VERSAO,
        "cores": len(ex.paleta.cores),
        "papeis": {papel: p.hex for papel, p in ex.paleta.papeis.items()},
        "fontes": {papel: f.familia for papel, f in ex.tipografia.papeis.items()},
        "tamanhos": [v for v, _ in ex.tipografia.tamanhos],
        "componentes": {c.tipo: len(c.regras) for c in ex.componentes},
        "assets": [a.arquivo for a in ex.ativos],
        "folhas": ex.folhas,
        "regras": ex.regras,
        "captura": ex.captura,
    }


def main(argv=None) -> int:
    args = _args(argv)
    for fluxo in (sys.stdout, sys.stderr):
        if hasattr(fluxo, "reconfigure"):
            fluxo.reconfigure(encoding="utf-8")
    try:
        ex, saida, linhas = extrair(args)
    except (UsoInvalido, EnderecoRecusado) as erro:
        print(f"ERRO | uso | {erro}", file=sys.stderr)
        return 2
    except FalhaDeRede as erro:
        print(f"ERRO | pagina | {erro}", file=sys.stderr)
        return 1
    avisos = [linha for linha in linhas if linha[0] == "AVISO"]
    if args.json:
        dados = {
            "ok": True,
            "url": ex.url,
            "saida": str(saida),
            "nome": ex.nome,
            "avisos": [f"{etapa}: {texto}" for _, etapa, texto in avisos],
            "resumo": _resumo(ex),
        }
        print(json.dumps(dados, ensure_ascii=False, indent=2))
    else:
        for nivel, etapa, detalhe in linhas:
            print(f"{nivel} | {etapa} | {detalhe}")
        plural = "aviso" if len(avisos) == 1 else "avisos"
        print(f"RESULTADO: estrutura gerada em {saida} ({len(avisos)} {plural})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
