# Fluxos — design-system-studio

## Extrair o design system de um site
```
Pessoa passa a URL
  ↓ skill extrair-design-system
uv run scripts/extrair.py --url <site> --saida <pasta> [--nome <marca>] [--captura]
  ↓ valida a URL, baixa HTML, CSS (com @import), logo e ícones, dentro dos limites
DESIGN.md, tokens.css, components.css, index.html, assets/
  ↓ a IA revisa o DESIGN.md (decisões e tom) e abre a vitrine no navegador
Entrega como referência, respeitando a marca
```

## Mudança (SDD)
```
branch por iniciativa → discovery → features → PR → merge na main → tag
```
