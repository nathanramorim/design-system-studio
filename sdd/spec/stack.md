# Stack — design-system-studio

## Dependências

| Camada | Escolha | Versão | Motivo |
|--------|---------|--------|--------|
| Runtime | Python via uv | 3.11+ | PEP 723, `dependencies = []` |
| DB | none | (nenhuma) | Sem estado |
| Testes e lint | pytest, ruff (grupo `dev`) | pytest ≥ 8.3, ruff ≥ 0.8 | Só no repositório, nunca no plugin |
| Captura | Google Chrome ou Chromium | qualquer recente | Opcional, pelo CDP |

## Layout do projeto
```
.claude-plugin/marketplace.json
plugins/design-system-studio/
  .claude-plugin/plugin.json  AGENTS.md  GEMINI.md
  commands/extrair-design-system.md
  skills/extrair-design-system/
    SKILL.md  references/  templates/  exemplos/site-exemplo/
    scripts/extrair.py  scripts/extrator/
tests/      pytest (servidor local num thread, CLI real via uv run)
docs/       banner do README
sdd/        Forge SDD
```
