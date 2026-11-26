# feat-43c3-01: Extrator `extrair.py`

**Branch:** `feat/43c3-extrator` (única da iniciativa)
**Depende de:** Gate 1 (pedido direto do dono em 25/11/2026)
**Status:** `review_pending`
**Origem:** `sdd/discovery/43c3-extrator/plan.md`

## Objetivo
Criar `scripts/extrair.py` (CLI) e `scripts/extrator/` com um módulo por responsabilidade: rede (validação de URL, limites, redirecionamento), página (HTML), folhas (CSS e `@import`), cores, tipografia, medidas, componentes, marca (logo, favicon, ícones), captura (CDP, opcional) e escrita (com os modelos de `templates/`). O site fictício `exemplos/site-exemplo/` serve aos testes.

## Modelo do módulo
`completo` (`ARQ-11`), conforme `criteria.md`.

## Decisões do projeto aplicadas
Determinístico vira script; arquivos pequenos; uv com PEP 723; repositório público sem dado de cliente (ver `criteria.md`).

## O que já existe
| Procurei | Onde | Achei | Decisão | Justificativa |
|---|---|---|---|---|
| Equivalente reutilizável | Reuse Check do `criteria.md` | Formato de plugin e de design system do dono; cliente CDP stdlib | reusar o formato, reescrever o CDP enxuto | Sem duplicar (`DUP-01`) |

## Dependências novas
Python 3.11+, só stdlib (PEP 723, `dependencies = []`). Chrome opcional para `--captura`.

## Rules e IDs da Constituição Aplicáveis
ARQ-04, ARQ-06, COD-01, COD-03, SEG-01, SEG-05, TST-01

## Critérios de Aceitação Executáveis
```bash
uv run --with pytest pytest -q tests/test_extracao.py tests/test_seguranca.py tests/test_vitrine.py tests/test_unidades.py
uv run --with ruff ruff check
```
- [x] cores, fontes, tokens, componentes e logo extraídos do site fictício
- [x] limites de bytes e de tempo; recusa de endereço privado
- [x] vitrine válida e saída determinística
