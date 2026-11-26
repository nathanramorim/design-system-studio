---
name: extrair-design-system
description: Use quando a pessoa quiser extrair, copiar como referência, documentar ou recriar o design system, a identidade visual, a paleta de cores, as fontes ou os componentes de um site a partir da URL. O script extrair.py baixa o HTML e o CSS (com @import), sem IA e sem rodar o JavaScript do site, e gera a estrutura padrão DESIGN.md, tokens.css, components.css, index.html (vitrine que abre sem servidor) e assets/ com logo, favicon e ícones. A IA revisa e completa o DESIGN.md (decisões e tom) e confere a vitrine no navegador. Ative também para "design system de um site", "tokens de um site", "paleta do site", "style guide a partir da URL" e "extrair cores e fontes".
---

# Skill: extrair-design-system

A extração é **determinística**: a mesma URL gera a mesma saída, e cada papel (fundo, texto, primária, destaque) vem de uma regra que o `DESIGN.md` explica. A IA não inventa cor nem fonte: ela revisa o que o script achou e completa o que só um leitor humano vê (decisões e tom).

`SKILL` abaixo é a pasta desta skill, onde está este arquivo. Rode sempre com `uv`, nunca com pip. O script só usa a stdlib e declara isso no cabeçalho (PEP 723).

## Antes de começar
- **Confirme o site e o uso:** a URL exata (com ou sem `www`), a pasta de saída e para que serve (refazer o próprio site, estudar uma referência, montar uma proposta).
- **Marca de terceiro é referência.** Se o site não for da pessoa, avise já na abertura: logo, fontes e imagens não podem ser publicados como dela (`references/marca-registrada.md`).
- **Nome da marca:** use o que a pessoa disser em `--nome`; sem isso, o script usa `og:site_name`, o título ou o domínio.

## Passo a passo
1. **Extrair.**
   ```bash
   uv run SKILL/scripts/extrair.py --url https://www.site.com.br --saida design-systems/site --nome "Marca"
   uv run SKILL/scripts/extrair.py --url https://www.site.com.br --saida design-systems/site --captura   # com captura de tela
   ```
   Leia as linhas `OK` e `AVISO`. Com `--json`, o resumo sai em JSON para outro agente.
2. **Revisar o `DESIGN.md`** com `references/revisao.md`: confira os papéis contra a vitrine e a captura, ajuste o que a página real contradisser e escreva a seção "Tom e voz".
3. **Abrir a vitrine** (`index.html`) no navegador, sem servidor. Confira cores, fontes, componentes e logo. Mostre à pessoa antes de qualquer decisão visual.
4. **Entregar:** a pasta, o que mudou na revisão e os avisos que ficaram (folha ignorada, logo não encontrado, captura que não veio).

## Regras que não se negociam
1. **Nada de inventar.** Cor, fonte, raio ou componente que não está no CSS não entra. Se faltou algo, diga o que faltou e por quê (o aviso do script mostra).
2. **Sem IA na extração:** não troque o resultado do script por "achismo". Ajuste só com evidência da vitrine, da captura ou do site.
3. **Marca registrada:** o uso é de referência. Logo, fontes pagas e imagens são do dono do site.
4. **Segurança:** só `http` e `https` públicos. Não use `--permitir-local` para contornar a recusa de um endereço que não é seu: ele existe para testes e para o servidor de desenvolvimento da própria pessoa.
5. **Não se passe por navegador.** Se o site recusar o User-Agent do script (403, desafio), relate o erro. Não troque o User-Agent.

## Opções do script
| Opção | Para quê |
|---|---|
| `--url` e `--saida` | Obrigatórias: o site e a pasta onde a estrutura é gravada |
| `--nome` | Nome da marca no `DESIGN.md` e na vitrine |
| `--captura` | Captura de tela com o Chrome headless, JavaScript desligado (`references/captura.md`) |
| `--sobrescrever` | Regrava uma pasta que já tem `DESIGN.md` (a revisão anterior se perde) |
| `--limite-bytes`, `--tempo` | Limite por arquivo (padrão 2 MB) e por pedido (padrão 15 s) |
| `--data` | Data fixa no `DESIGN.md` (AAAA-MM-DD), para comparar duas extrações |
| `--json` | Resumo em JSON: `ok`, `url`, `saida`, `nome`, `avisos`, `resumo` |
| `--permitir-local` | Aceita só o loopback (`127.0.0.1`, `::1`); rede privada continua recusada |

## Códigos de saída
| Código | Significa | O que fazer |
|---|---|---|
| 0 | Estrutura gerada (pode haver avisos) | Revisar o `DESIGN.md` e abrir a vitrine |
| 1 | A página principal não veio: rede, status de erro, não é HTML, passou do limite de bytes ou de tempo | Conferir a URL; se o site for grande ou lento, subir `--limite-bytes` ou `--tempo` com o ok da pessoa |
| 2 | Uso inválido: esquema fora de http e https, endereço local ou privado, `DESIGN.md` já existe sem `--sobrescrever` | Corrigir o comando |

## Referências (carregue só a que a etapa pede)
| Arquivo | Quando |
|---|---|
| `references/estrutura-de-saida.md` | O que vai em cada arquivo e como os tokens `--ds-*` são nomeados |
| `references/regras-de-extracao.md` | Como cada papel de cor, fonte, medida, componente e logo é escolhido |
| `references/revisao.md` | Roteiro para revisar o `DESIGN.md` e conferir a vitrine |
| `references/marca-registrada.md` | Uso como referência, autorização e o que não publicar |
| `references/seguranca-e-limites.md` | Endereços recusados, limites, User-Agent e o que fica de fora |
| `references/captura.md` | Captura de tela com o Chrome headless e o que fazer quando falha |

Exemplo completo, usado pelos testes: `SKILL/exemplos/site-exemplo/` (empresa fictícia). Os modelos que o script preenche estão em `SKILL/templates/` (`templates/DESIGN.md` e `templates/vitrine.html`).
