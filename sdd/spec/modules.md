# Módulos — design-system-studio

## skill `extrair-design-system` (`plugins/design-system-studio/skills/extrair-design-system/`)
**Responsabilidade:** levar o agente da URL à estrutura de design system revisada.

- [x] `SKILL.md`: quando usar, passo a passo, revisão, marca registrada e códigos de saída
- [x] `references/`: um tema por arquivo
- [x] `templates/`: modelos do `DESIGN.md` e da vitrine, preenchidos pelo script
- [x] `exemplos/site-exemplo/`: site fictício usado nos testes

## extrator (`scripts/extrair.py` + `scripts/extrator/`)
**Responsabilidade:** baixar com segurança e extrair de forma determinística.

- `rede`, `pagina`, `folhas`, `cores`, `tipografia`, `medidas`, `componentes`, `marca`, `captura`, `escrita`
- Saída `NIVEL | etapa | detalhe` ou `--json`; códigos 0 (gerado), 1 (página não veio), 2 (uso inválido)
