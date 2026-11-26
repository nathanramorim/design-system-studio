# Estrutura de saída

O script grava sempre os mesmos cinco itens na pasta de `--saida`.

| Item | Conteúdo |
|---|---|
| `DESIGN.md` | Fonte e data, decisões (papéis com o porquê), tom e voz (a IA escreve), paleta, tipografia, espaçamento, raios e sombras, componentes, marca, captura, como usar e limites |
| `tokens.css` | Três blocos: `@font-face` do site com endereços absolutos, custom properties do `:root` como estão e os tokens propostos `--ds-*` |
| `components.css` | Regras dos componentes reconhecidos, copiadas do CSS do site, um bloco por tipo e com o `@media` original |
| `index.html` | Vitrine que abre direto no navegador (`file://`), sem servidor e sem nenhum `<script>` |
| `assets/` | `logo.*`, `favicon.*`, `icone-N.*`, `og-imagem.*` e, com `--captura`, `captura.png` |

## Tokens propostos
| Prefixo | O quê |
|---|---|
| `--ds-cor-fundo`, `-superficie`, `-texto`, `-texto-suave`, `-primaria`, `-destaque` | Papéis (superfície e texto suave só quando existem) |
| `--ds-cor-1` a `--ds-cor-16` | Paleta, da cor mais usada para a menos usada |
| `--ds-fonte-texto`, `-titulos`, `-mono` | Pilhas de fonte por papel |
| `--ds-tamanho-N`, `--ds-raio-N`, `--ds-sombra-N`, `--ds-espaco-N` | Valores mais frequentes, do menor para o maior (sombras pela frequência) |

As custom properties do site ficam com os nomes originais porque as regras copiadas para `components.css` dependem delas. O prefixo `--ds-` evita colisão.

## Regravar
Com `DESIGN.md` na pasta, o script recusa (código 2) até receber `--sobrescrever`. Em `assets/`, só os arquivos que ele mesmo grava são apagados antes.
