# Segurança e limites

## Endereços
- Só `http` e `https`, sem usuário e senha na URL.
- O nome é resolvido e **todos** os endereços precisam ser públicos: loopback, redes privadas (10/8, 172.16/12, 192.168/16), link-local (169.254/16, inclusive metadados de nuvem), 100.64/10, multicast, reservados e IPv4 mapeado em IPv6 são recusados.
- A conexão vai para o IP conferido, e o endereço do outro lado é conferido de novo depois de conectar (fecha o DNS rebinding).
- Vale para cada pedido: página, redirecionamento (até 5), folhas, `@import`, logo, ícones e `/favicon.ico`.
- `--permitir-local` libera só o loopback, para testes e para o servidor de desenvolvimento da própria pessoa.

## Limites
| Limite | Padrão | Ao passar |
|---|---|---|
| Bytes por arquivo | 2 MB (`--limite-bytes`) | Página principal: código 1. Folha ou imagem: aviso e segue |
| Bytes da extração toda | 12 MB (ou 6 vezes o limite por arquivo) | Código 1 ou aviso, como acima |
| Tempo por pedido | 15 s (`--tempo`), contando o pedido inteiro, não cada pedaço | Página principal: código 1. Recurso: aviso |
| Folhas | 25, até 4 níveis de `@import` | Aviso |
| Imagens | 2 MB cada, até 4 ícones | Aviso |

## O que nunca acontece
- O JavaScript do site não roda (a captura desliga o JavaScript no Chrome). Estilos montados por script não aparecem.
- Pedidos com compressão: o script pede `identity`, sem bomba de descompressão.
- O script não imprime cabeçalhos nem conteúdo baixado, só o resumo.

## User-Agent
`design-system-studio/<versão> (+https://github.com/nathanramorim/design-system-studio)`. Se o site recusar, o erro aparece como está.
