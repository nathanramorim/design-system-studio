# feat-43c3-03: Empacotamento, README e versão 0.1.0

**Branch:** `feat/43c3-extrator` (única da iniciativa)
**Depende de:** feat-43c3-01, feat-43c3-02
**Status:** `review_pending`
**Origem:** `sdd/discovery/43c3-extrator/plan.md`

## Objetivo
Marketplace na raiz, `plugin.json`, `AGENTS.md` e `GEMINI.md` do plugin, `pyproject.toml` e `uv.lock`, README gerado com o readme-studio (banner SVG, selos e tabela de versões), release note 0.1.0 e licença MIT. Sem workflow de CI.

## Modelo do módulo
`completo` (`ARQ-11`), conforme `criteria.md`.

## Decisões do projeto aplicadas
Sem CI; validação local; repositório público (ver `criteria.md`).

## O que já existe
| Procurei | Onde | Achei | Decisão | Justificativa |
|---|---|---|---|---|
| README comercial | Plugin `readme-studio` | `gerar_banner.py` e modelo de README | reusar | Pedido do dono |

## Dependências novas
`pytest` e `ruff` no grupo `dev`.

## Rules e IDs da Constituição Aplicáveis
TST-01, TST-05, COD-02, DUP-02

## Critérios de Aceitação Executáveis
```bash
uv run --with pytest pytest -q tests/test_skill.py tests/test_publico.py
uv run --with ruff ruff check
```
- [x] versão 0.1.0 igual em `plugin.json`, `pyproject.toml` e README
- [x] nenhum dado de cliente nem caminho pessoal no repositório
