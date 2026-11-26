# Revisão do DESIGN.md e da vitrine

O script entrega a base. A revisão da IA fecha o que só leitura humana resolve.

## Roteiro
1. **Abra a vitrine** (`index.html`) e, se houver, a captura (`assets/captura.png`). Compare com o site no ar.
2. **Papéis de cor:** a primária é mesmo a cor dos botões e links principais? O destaque aparece em selos e chamadas? Se a página contradisser, troque o valor do token em `tokens.css` e escreva o motivo na tabela "Decisões".
3. **Fontes:** se a família do texto saiu "fontes do sistema" mas o site mostra uma fonte própria, ela pode vir de script ou de folha bloqueada. Registre como decisão, com a evidência.
4. **Componentes:** confira se as amostras parecem com o site. Regras de cabeçalho fixo e larguras grandes ficam contidas na vitrine, mas podem precisar de ajuste no uso real.
5. **Tom e voz:** escreva duas ou três frases a partir dos títulos, botões e chamadas do site (formal ou próximo, frases curtas ou longas, uso de termos técnicos).
6. **Avisos:** cada linha "Aviso da extração" no fim do `DESIGN.md` vira ação (subir um limite com o ok da pessoa, achar o logo à mão) ou fica como limite conhecido.

## O que não fazer
- Não apagar a coluna "Por quê": quem ler depois precisa saber de onde veio cada valor.
- Não inventar tokens que o site não usa para "completar" a escala.
- Não rodar de novo com `--sobrescrever` depois de revisar, sem guardar a revisão: ela se perde.
