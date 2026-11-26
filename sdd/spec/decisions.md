# Decisões — design-system-studio

## Resolvidas

| # | Decisão | Resolução | Motivo |
|---|---------|-----------|--------|
| R1 | Forma de entrega | Plugin com uma skill (`extrair-design-system`) e um comando (`/extrair-design-system`) | Mesmo padrão dos outros plugins do dono |
| R2 | Extração | `extrair.py` só stdlib, determinístico, sem IA e sem executar o JS do site | Reprodutível e seguro |
| R3 | Papéis das cores | Regras explicáveis (fundo do `body`, cor do texto do `body`, cor cromática mais usada com peso para botões e links, destaque com matiz distante) | A IA revisa sobre uma base que dá para conferir |
| R4 | Segurança de rede | Só http e https, endereço público conferido em cada pedido e redirecionamento, limites de bytes e de tempo | A URL vem de fora |
| R5 | Captura | Opcional, Chrome headless pelo CDP com JavaScript desligado | Visual real sem rodar o código do site |

## Abertas

| # | Questão |
|---|---------|
| D1 | Ler estilos de sites que só montam o CSS por JavaScript (hoje ficam de fora e o `DESIGN.md` avisa) |
