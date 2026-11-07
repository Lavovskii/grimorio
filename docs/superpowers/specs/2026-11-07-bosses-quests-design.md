# Bosses do dia e quests por personagem — desenho

Data: 7/11/2026. Estado: **para aprovação**.

## Intenção

Quem abre a página dos bosses quer saber, sem esforço, **que bosses pode fazer agora** com a personagem que escolheu.
Hoje a página mistura bosses de alavanca com bosses de raid e de world change (que não se fazem quando se quer), e
não sabe que quests a personagem fez. O dono do pedido encontra «uma dificuldade sempre que abre».

Objetivo: uma rotação diária a solo, em duas versões (rápida e dinheiro), que só mostra os bosses a que a personagem
tem acesso, diz o que falta para desbloquear os outros, guarda os cooldowns e avisa das world changes que se conseguem
detetar.

## O que a API do Tibia deixa saber (verificado a 7/11/2026)

TibiaData v4 e v5, ficha da personagem: nome, nível, vocação, mundo, guild, último login, nº de títulos, conquistas
escolhidas para mostrar (da conta; vazias nas personagens testadas). **Não há quests, equipamento nem skills.** As skills
só aparecem nos Highscores (top 1000 do mundo). O tibia.com bloqueia pedidos automáticos (403). Conclusão: **as quests
feitas são marcadas pelo jogador**, como já acontece hoje.

## Objetivos

1. **Passos das quests por personagem.** O progresso do Questski (passos marcados) passa a pertencer à personagem
   ativa do Tibia Grimoire, como as quests completas já pertencem. Duas personagens no mesmo browser têm progressos
   separados.
2. **Acesso aos bosses pelo passo exato.** Cada boss de alavanca/sala diz qual quest e **qual passo** abre a entrada
   (ex.: Oskayaat, Ayana e Tamru: Grimvale Quest, secção 11 «Paradise Lost: chegar a Oskayaat», depois de entregar a
   ocarina). Estado por boss e personagem:
   - **Tens acesso** — o passo (ou a quest inteira) está marcado, ou o jogador carregou em «Já tenho acesso»;
   - **Falta: <quest> até <passo>** — com link direto para esse passo no Questski;
   - **Quest completa** — quando ainda não se sabe o passo exato (aviso: «pode bastar menos»).
3. **Rotação do dia**, com duas abas:
   - **Rápida:** bosses agrupados por zona e ordenados para viajar o menos possível.
   - **Dinheiro:** ordenados por gp por minuto (loot por kill aos preços do Market do mundo ÷ (kill + viagem)).
   - Entram só bosses de alavanca/sala com cooldown (`sp = "t"` e os que se confirmarem), com acesso, que o modelo
     `GrimBoss.judge` dá como «sozinho» no nível, e que não estão em cooldown.
   - Resumo: disponíveis agora, tempo da volta, loot estimado, pontos de Bosstiary.
   - O boss em destaque do dia (boostablebosses) é marcado.
4. **Cooldowns por personagem.** Botão «Feito hoje» em cada boss; guarda a hora; o boss sai da rotação e mostra
   «volta às HH:MM» (hora + cooldown do boss). Desfazer com o mesmo botão.
5. **Fora da rotação.** Bosses de raid, de aparição aleatória e de world change numa lista própria, fechada por
   omissão, com o motivo.
6. **Desbloqueia com…** Os bosses sem acesso, agrupados pela quest que os abre, ordenados pelo que a quest desbloqueia
   (nº de bosses × valor), com o nível recomendado da quest.
7. **World changes.** Painel com as que se detetam no mundo da personagem:
   - pelas mortes de ontem (TibiaData `killstatistics/{world}`, já usado no site): cada world change tem criaturas que
     só aparecem com ela; se morreram, esteve ativa;
   - pelo calendário, quando a regra é fixa (ex.: lua cheia de Grimvale, a confirmar na TibiaWiki);
   - para cada uma: estado (ativa / em breve / não detetada), até quando (server save seguinte, ou fim do período do
     calendário), o que há lá e se é recomendada ao nível da personagem.
   - Texto honesto: «não há API oficial; fica um dia atrasado».

## Não-objetivos

- Ler quests, equipamento ou skills do tibia.com (não é possível).
- Rotações em equipa (fica para depois; a página antiga continua a mostrar «em equipa»).
- Prever raids.
- Mexer no modelo de dano/tempo do `GrimBoss` além do necessário.

## Anti-objetivos (falha mesmo que funcione)

- Recomendar um boss a que a personagem não tem acesso, ou que só aparece com world change/raid.
- Perder o progresso do Questski de quem já o tinha (a migração tem de o guardar).
- Afirmar que uma world change está ativa sem prova (só mortes ou calendário).
- Texto abaixo de 12 px, alvos abaixo de 44 px, partir as 8 línguas, piorar os PCs fracos (`fx-lite`).

## Restrições

- Regras do projeto em `_dev/GRIMORIO.md`: `index.html` editado com substituições ancoradas, `node --check`, smoke,
  `?v=`, i18n pelo `ui-extra.json` + `_dev/i18n.py`.
- Os dois sites partilham o `localStorage` (mesmo endereço). O estado do Grimoire é `grimorio-tibia-v4`
  (`{v, active, chars:[{id,name,voc,level,done,...}]}`), o do Questski `tq-progress` (`{slug:{s:{"sec-step":1},done,t}}`).
- Os ids de passo do Questski são `"<secção>-<passo>"` (índices). Mudam se um guia for regenerado com outra ordem.

## Caminhos considerados

### A. Onde guardar os passos por personagem
1. **No estado do Grimoire** (`c.qp = {slug: {s, done, t}}` dentro de cada personagem), lido e escrito pelo Questski
   através do `QPonte`. **Escolhido (proposta):** uma só fonte; exportar/importar a personagem leva as quests; a página
   dos bosses lê tudo do mesmo sítio.
2. Uma chave nova do Questski por personagem (`tq-progress:<id>`). Mais simples no Questski, mas dois sítios a manter
   em sincronia e a exportação da personagem não leva os passos.
- Sem personagem ativa, o Questski continua a usar `tq-progress` (anónimo).
- Migração: na primeira abertura, o `tq-progress` existente passa para a personagem ativa (ou fica anónimo e é
  oferecido à primeira personagem criada); o original fica guardado em `tq-progress-bak`.

### B. De onde vem o passo exato de acesso
1. **Tabela curada** `_dev/acessos_bosses.json` (boss → quest slug, secção, passo, palavra de controlo), feita a partir
   das páginas dos bosses e das quests na TibiaWiki, começando pelos bosses que entram em rotações (alavanca/sala).
   **Escolhido (proposta).** O `build_bosses.py` junta-a ao `data/bosses.json` (`acc`) e falha se a palavra de
   controlo (ex.: «ocarina») já não estiver no texto do passo — protege contra guias regenerados.
2. Extração automática do texto da wiki. Não é fiável (texto livre, em inglês) e daria acessos errados.
- Sem entrada na tabela: «quest completa» (o que existe hoje), com o aviso.

### C. Deteção de world changes
1. **Mortes de ontem + calendário**, com a tabela `_dev/world_changes.json` (nome, criaturas-assinatura, duração,
   nível recomendado, o que há lá, link). **Escolhido (proposta):** usa o que o site já pede, sem chaves nem custos.
2. API de terceiros (RapidAPI «Tibia Mini World Changes»): precisa de chave, pode ser paga, fiabilidade desconhecida.
   Fica de fora.

## O que fica decidido

- Duas abas: Rápida e Dinheiro. Filtros: «Só sozinho» (ligado) e «Só com acesso» (ligado).
- «Feito hoje» e «Já tenho acesso» são por personagem e ficam no estado do Grimoire (`c.bcd = {boss: ts}`,
  `c.bacc = {boss: 1}`).
- Valores mostrados como estimativas (≈), com a fonte (modelo, preços do Market do mundo).
- A rotação fica no topo da página `#bosses` atual; a lista completa que já existe continua por baixo, como
  «Todos os bosses».
- Quem também lê o `tq-progress` hoje (`guiasFor` no `index.html`, a lista e o progresso do Questski, exportar/importar
  do Questski) passa a ler o progresso da personagem ativa; exportar/importar no Questski trabalha sobre essa personagem.
- Sem personagem ativa, a página dos bosses pede para escolher ou criar uma (como já faz noutras páginas).
- O layout segue as maquetas aprovadas na conversa (computador: lista + painel de world changes à direita;
  telemóvel: cartões).

## Deixado ao construtor (com proposta)

- **Tempo de viagem:** proposta de uma tabela pequena de zonas → minutos a partir do depot mais próximo; dentro da
  mesma zona, 1 min entre bosses. Afinar com o dono depois.
- **Ordem da rotação rápida:** proposta de agrupar por zona e ordenar as zonas pelo nº de bosses (mais primeiro).
- **Quais bosses sem `sp`** (83) entram na rotação: rever pela TibiaWiki; na dúvida, ficam fora.
- **Datas de calendário** (lua cheia de Grimvale e outras): confirmar a regra na TibiaWiki antes de a mostrar.
- **Primeira leva da tabela de acessos:** os bosses de alavanca/sala até nível 500 (≈ 70) e Oskayaat.

## Como se prova

- `node _dev/bosses_test.mjs` com casos novos: acesso por passo, cooldown, ordem das duas rotações, migração do
  progresso.
- Smoke do Grimoire e rastreio do Questski sem erros, em pt-PT, en e de, a 1440 e 390 px.
- Teste de duas personagens: marcar a ocarina com uma não dá acesso a Oskayaat à outra.
- Teste de migração: um `tq-progress` antigo aparece na personagem ativa e o `tq-progress-bak` existe.
