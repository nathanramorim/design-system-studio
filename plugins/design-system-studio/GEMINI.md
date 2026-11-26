# GEMINI.md: plugin design-system-studio

Plugin que extrai o design system de um site pela URL, com um script determinístico, e deixa a revisão para a IA.

O fluxo completo, as regras, as opções e o que fazer em cada código de saída estão em um só lugar:

**`skills/extrair-design-system/SKILL.md`**

Leia essa skill antes de agir. Este arquivo não repete o conteúdo dela.

Comando do plugin: `/extrair-design-system <URL>` (`commands/extrair-design-system.md`).

Em qualquer agente, o ponto de entrada é `uv run skills/extrair-design-system/scripts/extrair.py --help`.
