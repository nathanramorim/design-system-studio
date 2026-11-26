# Plano 43c3: extrator de design system por URL

Uma onda com 3 tasks, de baixo para cima. O pedido direto do dono (25/11/2026) valeu como Gate 1. A revisão da Camada B (`/revisar`) fica com o orquestrador.

| Task | O quê | Depende de | Rules / IDs |
|---|---|---|---|
| 43c3-01 | `extrair.py` e `scripts/extrator/` (um módulo por responsabilidade), modelos de saída, site fictício e testes | (nenhuma) | `ARQ-04`, `ARQ-06`, `COD-01`, `COD-03`, `SEG-01`, `SEG-05`, `TST-01` |
| 43c3-02 | `SKILL.md`, referências (uma por tema) e o comando `/extrair-design-system` | 01 | `ARQ-06`, `COD-05`, `DUP-01` |
| 43c3-03 | Empacotamento: marketplace, `plugin.json`, `AGENTS.md`/`GEMINI.md`, pyproject e `uv.lock`, README do readme-studio com banner, release note 0.1.0 e licença MIT | 01, 02 | `TST-01`, `TST-05`, `COD-02`, `DUP-02` |

## Passos do dono (fora da IA)
1. Criar o repositório público no GitHub e fazer o push desta branch, com o PR para a `main`.
2. Instalar pelo marketplace (`/plugin marketplace add`) ou copiar a skill para `.agents/skills/`.
