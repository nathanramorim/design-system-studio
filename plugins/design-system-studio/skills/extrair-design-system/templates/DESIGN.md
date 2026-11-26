# Design system: ${nome}

**Fonte:** ${url}, lida em ${data} pelo design-system-studio ${versao} (extração determinística, sem IA).
**Uso:** referência. A marca, o logo, as imagens e as fontes pertencem ao dono do site.

## Arquivos
| Arquivo | Conteúdo |
|---|---|
| `tokens.css` | `@font-face` do site, custom properties do `:root` como estão e os tokens propostos (`--ds-*`) |
| `components.css` | Regras dos componentes reconhecidos, copiadas do CSS do site |
| `index.html` | Vitrine. Abre direto no navegador, sem servidor e sem script |
| `assets/` | Logo, favicon e ícones baixados do site |

## Decisões
Propostas pelas regras da extração. Confira na vitrine e ajuste o que a página real contradisser.

| Papel | Token | Valor | Por quê |
|---|---|---|---|
${decisoes}

## Tom e voz
A extração não lê o tom. Descreva aqui, em duas ou três frases, como a marca fala, a partir dos títulos e dos botões do site.

## Paleta
${resumo_cores}

| Token | Cor | Usos | Em fundos | Em texto | Em bordas | Custom properties do site |
|---|---|---|---|---|---|---|
${paleta}

${transparencias}

## Tipografia
| Papel | Família | Token | Por quê |
|---|---|---|---|
${papeis_fonte}

| Família | Usos | Origem |
|---|---|---|
${familias}

${escala}

## Espaçamento, raios e sombras
| Token | Valor | Usos |
|---|---|---|
${medidas}

## Componentes
${componentes}

## Marca
${marca}

## Captura
${captura}

## Como usar
1. Ligue `tokens.css` e depois `components.css`.
2. Use os tokens `--ds-*` no código novo. As custom properties do site ficam com os nomes originais para os componentes copiados funcionarem.
3. Copie a marcação de exemplo da vitrine (`index.html`).
4. Logo, fontes e imagens são do dono do site: use como referência e peça autorização antes de publicar.

## Limites desta extração
- O JavaScript do site não roda: estilos montados por script não aparecem.
- Tamanhos em `rem` e `em` consideram 16px.
- Cores em `oklch`, `lab` e `color-mix` não entram na contagem.
${avisos}
