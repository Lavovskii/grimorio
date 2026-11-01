# Pele do cliente do Tibia — desenho (r34, proposta)

Estado: **plano aceite, ainda não aplicado ao site** (1/11/2026). O site não carrega nada desta pasta.

Ficheiros desta pasta:
- `DESENHO.md`: este documento.
- `maqueta-cliente.css`: a maqueta usada nas capturas de comparação. Não está ligada ao site; serve de ponto de
  partida para o `shared/cliente.css`.
- `icones.py`: desenha os ícones pixel-art do menu (12×12). `python3 -I _dev/pele-cliente/icones.py` gera
  `icons.json` e `sheet.html` nesta pasta (ignorados pelo Git).
- `icones.png`: a folha dos ícones, para ver sem correr o script.

Próximo passo: o plano de implementação por fases (secção «Deixado ao construtor»).

## Intenção

Quem joga Tibia deve abrir o Grimório (e o Questski, que já tem o mesmo tema desde a r31) e reconhecer o ambiente do
cliente do jogo: janelas escuras com barra de título, casas de inventário, barras de vida e mana, a consola de
mensagens, números com contorno como os do loot. Familiar, não igual: todas as peças são desenhadas de novo por nós,
nenhuma é copiada do cliente.

## Objetivos

1. **Janela do cliente** (`.tw`): um painel com barra de título fina (ícone pequeno + título em maiúsculas pequenas
   douradas) e corpo de pedra escura com moldura em bisel de 2 px. Substitui o aspeto das secções e cartões grandes.
2. **Casas de inventário** (`.slot`): quadrado escuro afundado, bisel claro em baixo/direita e escuro em cima/esquerda,
   sprite ao centro em `image-rendering: pixelated`. Usado em todos os sítios onde aparece um item ou criatura
   (listas, loot, boneco do equipamento, recompensas das quests).
3. **Barras de estado** (`.tbar`): vida (vermelha) e mana (azul) como as do cliente, com o número dentro; também para
   capacidade (castanho) e progresso (verde: nível, passos da quest, Bosstiary).
4. **Consola** (`.console`): fundo cinzento-escuro, linhas com cores de canal (branco informação, verde loot,
   laranja aviso, azul NPC, amarelo o que dizes). Usada nas notas, dicas e avisos; o chat dos NPCs do Questski já é
   quase isto e passa a ser a mesma peça.
5. **Números de loot** (`.tnum`): Verdana negrito com contorno preto de 1 px (como o texto flutuante do jogo), em
   branco, verde (lucro), vermelho (perda) ou amarelo (XP). Para XP/h, lucro/h, níveis, preços.
6. **Separadores do cliente** (`.ttabs`): abas pequenas de pedra com a ativa mais clara e unida ao painel, como as
   do Cyclopedia; substituem os botões `seg` nos filtros de página.
7. **Botões de pedra** (`.tbtn`): já temos os de metal; ficam com bisel de 1 px em vez de sombra suave, e o estado
   carregado afunda (bisel invertido), como no cliente.
8. **Ícones pixel-art**: os 25 ícones do menu redesenhados numa grelha de 12×12, a 2× (24 px), com contorno escuro e
   2–3 tons, em vez dos ícones de linha atuais. Originais, no estilo dos itens do jogo.
9. **Letra igual em todo o lado**: a Palatino não existe em Linux nem Android e o site muda de cara conforme o
   aparelho (o inspetor da Taste mediu isto). Uma letra serifada de licença livre (OFL), alojada no próprio site, para
   os títulos; o texto continua em Tahoma/Verdana (as letras do cliente).

## Não-objetivos

- Mudar o layout, o menu, as rotas ou o que cada página mostra (isso era o caminho 2).
- Imitar o ecrã de jogo, o minimapa real ou a disposição dos painéis do cliente.
- Novos efeitos animados.

## Anti-objetivos (falha mesmo que "funcione")

- **Cópia**: usar ficheiros do cliente (molduras, botões, ícones de interface, logótipo do Tibia) ou recriá-los
  píxel a píxel. Os sprites de itens e criaturas que o site já usa (`allitems.png`) continuam como estão.
- Ficar mais lento nos PCs fracos (`html.fx-lite`), ou com mais imagens a pintar a cada scroll.
- Texto abaixo de 12 px, contraste abaixo de 4,5:1, alvos de toque abaixo de 44 px.
- Partir as traduções (8 línguas) ou o Questski.

## Restrições

- As peças vivem num ficheiro partilhado (`shared/cliente.css`) carregado pelos dois sites, como o `shared/sites.css`.
- Molduras e biséis em CSS (`box-shadow` inset, `border-image` com SVG próprio pequeno), sem imagens grandes.
- Ícones pixel-art em SVG (retângulos numa grelha), um só ficheiro de símbolos, partilhado pelo `shared/nav.js`.
- A letra dos títulos: um só ficheiro WOFF2 (≈ 30–60 KB), `font-display: swap`.
- Regras do projeto: `_dev/GRIMORIO.md`, edições ancoradas ao `index.html`, `node --check`, smoke, versões `?v=`.

## Caminhos considerados

1. **Pele do cliente** (escolhido): as peças acima em todo o site, layout igual. Risco baixo, funciona no telemóvel,
   pode entrar por fases.
2. **Layout do cliente**: ecrã central, painéis à direita, consola em baixo. Mais parecido com o jogo, mas trabalho
   grande, mau no telemóvel e mais perto de copiar a interface.
3. **Pele + uma peça marcante por página**: o 1 mais um elemento próprio por página. Fica para depois, se o 1 agradar.

Escolha do dono do pedido: **caminho 1**, porque é o mais seguro e mostra o efeito em todo o site.

## Decidido

- Caminho 1. O dono viu as maquetes e pediu para juntar o plano ao repositório (1/11/2026).
- As artes são desenhadas em código (SVG/CSS) por nós. Não há gerador de imagens nesta sessão.

## Deixado ao construtor (com proposta)

- Qual letra OFL para os títulos (proposta: uma serifada clássica com acentos portugueses, polacos e suecos).
- A ordem das fases (proposta: peças base → Início e Hunts → resto do Grimório → Questski).
- Os tons exatos de cada canal da consola (contraste ≥ 4,5:1 contra o fundo da consola).

## Como se prova

- Capturas antes/depois a 1440 e 390 px do Início, das Hunts, de uma página de item e de uma quest.
- Smoke do Grimório e rastreio do Questski sem erros; letra mínima 12 px; sem scroll lateral; `fx-lite` igual ou
  mais leve (medido com `bench.cjs`).
