# Discovery 43c3: extrator de design system por URL

## Contexto
Pedido do dono em 25/11/2026: "gerar uma skill que extrai o design system e cria uma estrutura dessa de qualquer site, só passando a URL, coloca isso em um repositório separado, segue o padrão de skill que já temos, com o readme studio e tudo mais, esse pode ser público".

"Estrutura dessa" é o formato de design system por marca que o dono já usa: `DESIGN.md`, `tokens.css`, `components.css`, `index.html` (vitrine) e `assets/`.

## Problema
| # | Achado |
|---|---|
| 1 | Montar o design system de um site existente é trabalho manual: abrir o DevTools, copiar cores, adivinhar a fonte e recortar o logo. Cada pessoa faz de um jeito |
| 2 | Sites modernos guardam as cores em custom properties (`var(--x)`). Contar só os hex do CSS dá contagem errada |
| 3 | Pedir a uma IA que "olhe o site" não é reprodutível. O mesmo site gera paletas diferentes a cada vez |
| 4 | Baixar páginas de qualquer URL abre riscos: endereço interno da rede, arquivo gigante, servidor lento e script do site |

## Para quem
| Quem | O que quer |
|---|---|
| Agente de IA (Claude Code ou agy) | Um comando que entregue a estrutura pronta e um roteiro curto para revisar |
| Quem desenha ou refaz um site | Ponto de partida fiel ao site atual, com paleta, fontes e componentes |
| Dono da marca | Que o uso seja de referência e que a marca registrada seja respeitada |

## Jornada
1. A pessoa pede: "extraia o design system de https://site".
2. O agente roda `uv run SKILL/scripts/extrair.py --url https://site --saida pasta [--nome Marca] [--captura]`.
3. O script baixa o HTML e as folhas CSS, conta e classifica, baixa o logo e o favicon e grava os 5 artefatos.
4. O agente revisa o `DESIGN.md` (decisões e tom), abre a vitrine no navegador e confere.
5. Entrega a pasta e avisa que logo, fontes e marca são do dono do site.

## Regras de negócio
1. **Determinístico, sem IA.** A mesma entrada gera a mesma saída. Cada papel de cor vem de uma regra que o `DESIGN.md` explica.
2. **Só stdlib.** Python 3.11+ via uv (PEP 723), sem pacote de terceiros.
3. **Seguro:** só `http` e `https`; recusa endereços locais, privados e reservados (também depois de redirecionar); limita bytes e tempo; nunca executa o JavaScript do site.
4. **Marca registrada:** a saída é referência. A skill orienta a não publicar logo e fontes de terceiros como próprios.
5. **Replicável e público:** nenhum dado de cliente, só o site fictício dos exemplos.

## Escopo
**Dentro**
- Plugin `design-system-studio` com a skill `extrair-design-system` e o comando `/extrair-design-system`.
- `extrair.py` com um módulo por responsabilidade (rede, HTML, CSS, cores, tipografia, medidas, componentes, marca, captura e escrita).
- Captura opcional (`--captura`) com Chrome headless via CDP, só stdlib e com JavaScript desligado.
- Site fictício, testes pytest com servidor local, ruff, README com banner e versão 0.1.0.

**Fora**
- Executar o JavaScript do site (estilos injetados por script não aparecem).
- Baixar as folhas do Google Fonts (a família sai do link).
- Publicar no GitHub e no marketplace (passo do dono). CI (decisão do dono: validação local).

## Riscos
| Risco | Mitigação |
|---|---|
| Heurística de papéis erra em sites atípicos | Regra explicada no `DESIGN.md` e revisão do agente pela skill |
| CSS gerado por JS (CSS-in-JS) | Aviso nos limites. A captura mostra o visual real |
| Site recusa o User-Agent próprio | O erro aparece como está. Nada de se passar por navegador |
| DNS rebinding | Endereço conferido na resolução e de novo depois de conectar |
