# Overview — design-system-studio

Plugin com a skill `extrair-design-system`. O script `extrair.py` lê um site público pela URL e gera a estrutura de design system (`DESIGN.md`, `tokens.css`, `components.css`, vitrine `index.html` e `assets/`), de forma determinística e sem IA. A IA revisa e completa.

## Índice
- `stack.md` — tecnologias
- `modules.md` — componentes
- `flows.md` — fluxos principais
- `decisions.md` — decisões de design

---

## Arquitetura (C4 Model)

### Nível 1: Contexto
\`\`\`mermaid
graph TB
  User((Usuário)) --> Project[design-system-studio]
\`\`\`

### Nível 2: Containers
\`\`\`mermaid
graph LR
  App[Aplicação] --> DB[(Banco de Dados)]
\`\`\`
