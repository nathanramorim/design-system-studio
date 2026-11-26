# Captura de tela

`--captura` abre o Google Chrome ou o Chromium sem interface, com perfil temporário, e grava `assets/captura.png` (1440 por 900, a primeira dobra). O `DESIGN.md` e a vitrine passam a mostrar a imagem.

- **Sem JavaScript:** a flag `--blink-settings=scriptEnabled=false` e o comando `Emulation.setScriptExecutionDisabled` do CDP valem antes de navegar. Sites que só montam a página por script aparecem em branco ou incompletos, e isso também é informação útil.
- **Só stdlib:** o script fala com o Chrome pelo protocolo DevTools (WebSocket próprio), sem Playwright nem Selenium.
- **Onde está o Chrome:** caminhos padrão do macOS, do Windows e do Linux, ou a variável `CHROME_BIN`.
- **Rede:** o Chrome carrega imagens e folhas como um navegador comum; a conferência de endereço do script vale para a página pedida.
- **Se falhar** (Chrome ausente, página que não termina de carregar em 30 s), a extração segue e a falha vira aviso.
