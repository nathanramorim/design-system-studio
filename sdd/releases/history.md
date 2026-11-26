# Release Notes — design-system-studio

Este arquivo registra o histórico de entregas de produto deste projeto.

## Entregas

### 0.1.0 (26/11/2026, iniciativa 43c3)
- Skill `extrair-design-system` e comando `/extrair-design-system`: a partir da URL, gera `DESIGN.md`, `tokens.css`, `components.css`, a vitrine `index.html` e `assets/`; a IA revisa e completa.
- `extrair.py` só stdlib, um módulo por responsabilidade: rede com endereço público conferido em cada pedido e redirecionamento, limites de bytes e de tempo; CSS com `@import`; cores (hex, rgb, hsl e nomes) com `var()` resolvido e papéis por regra explicável; fontes (`font-family`, `@font-face` e Google Fonts); raios, sombras e espaços; componentes por seletor; logo, favicon e ícones; captura opcional pelo CDP com JavaScript desligado; `--json` e códigos 0, 1 e 2.
- Site fictício `site-exemplo`, 64 testes com servidor local e validação local com `uv run --with pytest pytest -q` e `uv run --with ruff ruff check`; sem CI.
