---
description: Extrai o design system de um site pela URL (DESIGN.md, tokens.css, components.css, vitrine e assets) e revisa o resultado.
argument-hint: "<https://url-do-site> [pasta-de-saida] [nome da marca]"
---

Siga a skill `extrair-design-system` (`skills/extrair-design-system/SKILL.md` deste plugin) para: $ARGUMENTS

1. Rode `uv run skills/extrair-design-system/scripts/extrair.py --url <endereço> --saida <pasta>` (com `--nome` se a pessoa disser a marca e `--captura` se houver Chrome) e leia as linhas `OK` e `AVISO`.
2. Revise o `DESIGN.md` com `references/revisao.md` e abra a `index.html` no navegador para conferir.
3. Se o site não for da pessoa, lembre que logo, fontes e imagens são do dono e servem só de referência.
