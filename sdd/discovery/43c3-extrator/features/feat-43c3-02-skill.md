# feat-43c3-02: Skill, referências e comando

**Branch:** `feat/43c3-extrator` (única da iniciativa)
**Depende de:** feat-43c3-01
**Status:** `queued`
**Origem:** `sdd/discovery/43c3-extrator/plan.md`

## Objetivo
Escrever `SKILL.md` (quando usar, passo a passo, revisão do `DESIGN.md`, conferência da vitrine, marca registrada, códigos de saída), `references/` (um tema por arquivo) e `commands/extrair-design-system.md`.

## Modelo do módulo
`completo` (`ARQ-11`), conforme `criteria.md`.

## Decisões do projeto aplicadas
A IA roda o script e só revisa; referências curtas, uma por tema; uso como referência (ver `criteria.md`).

## O que já existe
| Procurei | Onde | Achei | Decisão | Justificativa |
|---|---|---|---|---|
| Formato de skill com referências e tabela de códigos | Plugins públicos do dono | Padrão estável | reusar | Mesmo jeito de ler e ativar |

## Dependências novas
Nenhuma.

## Rules e IDs da Constituição Aplicáveis
ARQ-06, COD-05, DUP-01

## Critérios de Aceitação Executáveis
```bash
uv run --with pytest pytest -q tests/test_skill.py
```
- [ ] frontmatter com nome e descrição até 1.024 caracteres
- [ ] toda referência citada existe e toda referência existente é citada
