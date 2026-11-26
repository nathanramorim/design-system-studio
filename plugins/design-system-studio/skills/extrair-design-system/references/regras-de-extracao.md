# Regras de extração

Todas as regras são fixas e ficam escritas no `DESIGN.md` de cada saída, na coluna "Por quê".

## Cores
1. Hex (3, 4, 6 e 8 dígitos), `rgb()`/`rgba()` (vírgula ou espaço, com `/` e porcentagem), `hsl()`/`hsla()` (deg, turn, rad e grad) e nomes básicos viram `#RRGGBB`. O conteúdo de `url()` é ignorado e `light-dark(claro, escuro)` conta o tom claro.
2. `var(--x, reserva)` é resolvido pelas custom properties do `:root`, `html` e `body` (as de outros seletores só entram se faltarem), até 8 níveis. Sem isso, em sites com tokens, cada cor apareceria uma vez só.
3. Contam as propriedades de cor (`color`, fundos, bordas, `outline`, `fill`, `stroke`, sombras) das folhas e dos atributos `style`. Cores com transparência vão para uma lista à parte.
4. **Fundo:** o `background` do `html`, `body` ou `:root` fora de `@media`; senão, a cor mais usada em fundos; senão, branco.
5. **Texto:** o `color` do `html`, `body` ou `:root`; senão, a cor de texto mais usada com contraste de 4,5:1 sobre o fundo; senão, preto ou branco.
6. **Primária:** a cor cromática (maior e menor canal diferem em 15% ou mais) de maior pontuação: usos + 2 por uso em botões e links + 3 se for o `theme-color`.
7. **Destaque:** a próxima cromática com matiz a 30° ou mais da primária; senão, a segunda cromática; senão, repete a primária.
8. **Superfície** e **texto suave:** a cor neutra mais usada em fundos (e em texto) depois do fundo (e do texto).

## Tipografia
- Famílias de `font-family`, do atalho `font`, de `@font-face` e dos links do Google Fonts (lidos pelo endereço, sem baixar a folha).
- A família principal de uma pilha é a primeira declarada em `@font-face` ou no Google Fonts, ou que não é genérica nem do sistema (Segoe UI, Roboto, Arial e afins). Pilha só de sistema vira "fontes do sistema".
- Papéis: texto pelo `html`/`body`; títulos por `h1` a `h3` ou classes com title, titulo, heading e display; código por `code`, `pre`, `kbd`, `samp` ou classe mono.
- Escala: os 10 tamanhos fixos mais usados (`rem` e `em` valem 16px). `clamp()`, `min()`, `max()` e `calc()` aparecem como tamanhos fluidos.

## Medidas
Raios (`border-radius`), sombras (`box-shadow`) e espaços (`margin`, `padding`, `gap`) mais frequentes, depois de resolver `var()`.

## Componentes
O seletor é lido do sujeito (último composto) para trás; o primeiro composto com tipo decide. Classe vale antes da tag, e uma classe com hífen vale pelo primeiro pedaço reconhecido (`card-titulo` é cartão).

| Tipo | Tags | Classes (inteiras ou em pedaços) |
|---|---|---|
| Botões | `button`, `[type=submit]` | btn, button, botao, cta |
| Links | `a` | link |
| Cartões | | card, cartao, tile |
| Campos | `input`, `textarea`, `select` | field, campo, input, form-control |
| Cabeçalho | `header` | header, navbar, topbar, cabecalho |
| Rodapé | `footer` | footer, rodape |

Até 40 regras por tipo. Declarações com `expression()`, `javascript:`, `behavior` e `-moz-binding` ficam de fora; `url()` relativo vira absoluto.

## Logo, favicon e ícones
1. Logo: imagem com "logo" (no endereço, no alt, na classe ou num ancestral) dentro do cabeçalho; depois SVG inline com essa dica; depois qualquer imagem com a dica; depois o primeiro SVG inline do cabeçalho; por fim, a `og:image`.
2. Favicon: `link rel="icon"`, preferindo SVG e depois o maior `sizes`; sem link, `/favicon.ico`.
3. Ícones: os outros `link rel` de ícone (apple-touch-icon, mask-icon), até 4.
4. O tipo vem dos bytes (PNG, JPG, GIF, WebP, ICO, AVIF, SVG), nunca só do cabeçalho. SVG passa por limpeza: sem `script`, `foreignObject` e atributos `on*`.
