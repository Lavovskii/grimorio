# Fichas objetivas de hunts e bosses — desenho

Data: 10/11/2026. Pedido do dono do site. Plano: `docs/superpowers/plans/2026-11-10-fichas-hunts-bosses.md`.

## Intenção

O dono abre uma hunt ou um boss e não encontra depressa o que precisa. A ficha de hoje mistura setup, sets de
equipamento, Wheel, gemas, sessões reais e cinco separadores. O pedido é uma ficha **objetiva**, igual para
hunts e bosses, que responde por esta ordem:

1. **Onde é e como lá chego** — o mapa do sítio ao lado do caminho, passo a passo.
2. **O que preciso antes** — pré-requisitos, com ligação às quests.
3. **O que lá encontro** — as criaturas e o loot principal.
4. **O que levo** — só as recomendações de charms e de preys.

E só cinco números: **XP por hora, lucro por hora, nível recomendado, resistências e índice de dificuldade.**
(O lucro foi acrescentado pelo dono a 10/11/2026, depois da primeira versão deste desenho.)

O foco maior é a qualidade dos caminhos: mapas que se expandem, cada passo com o seu ponto, e os NPCs com quem é
preciso falar (onde estão, o que dizer, quanto custa).

## O que existe hoje (10/11/2026)

- 327 hunts (`G.places`). Caminho em passos (`G.hv`) em 198; `G.routes` em 182; **129 só têm uma frase** (`p.acc`).
- Dos 850 passos do `G.hv`, 91 têm coordenadas e 25 têm o diálogo com o NPC.
- `data/hunt-access.json`: 77 hunts ligadas a 76 fichas de locais do Questski (texto com `{npc:}`, `{coord:}`, `{key:}`).
- `data/boss-access.json`: 316 bosses; 265 com ficha de local, 259 com passos de guias.
- Mapas: `maps/floor-NN-map.png`, `drawPos` (mini-mapa de um ponto), `openMap` (mapa grande), spawns em `data/spawns.json`.
- Posição: `G.hm[pid]` em 324 hunts; `pos` em 272 bosses.
- Charms: `charmPicks`. **Preys: não há nada.** Dificuldade: `p.d` de 1 a 3 («risco»).

## Objetivos

1. **Uma ficha só**, com a mesma estrutura para hunts e bosses:
   - cabeçalho: nome e nível recomendado;
   - **mapa + «Como lá chegar»** lado a lado (um por cima do outro no telemóvel);
   - os cinco números;
   - pré-requisitos;
   - criaturas (num boss: o próprio boss);
   - loot principal;
   - charms e preys (só nas hunts: bosses não têm Bestiary, por isso não levam charm nem prey).
2. **Caminho estruturado.** Um ficheiro novo, `data/caminhos.json`, com cada caminho em troços e passos. Cada passo
   pode ter um ponto no mapa e um NPC (nome, o que dizer, preço).
3. **Mapas que se expandem.** Cada troço tem «Ver no mapa»: abre um mapa com os passos numerados; tocar num passo
   centra o mapa nesse ponto e muda de andar.
4. **NPCs no caminho.** Um passo com NPC mostra o sprite, o nome com ligação à página do NPC, as palavras a dizer e o
   preço.
5. **Pré-requisitos ligados às quests.** Cada quest liga ao guia do Questski (à secção certa quando se sabe) e mostra
   se a personagem ativa já a fez. Nível, premium e itens aparecem na mesma lista.
6. **Índice de dificuldade de 1 a 5 para a personagem ativa** (vocação, nível e set; rondas 2–4, Q3/Q7/Q9). Substitui
   a regra antiga «igual para toda a gente».
6b. **XP/h e lucro/h ajustados à vocação e ao nível da personagem**, a partir das medições de todas as vocações e das
   sessões reais (rondas 2–4, Q3/Q5/Q6), em qualquer hunt.
7. **Recomendação de preys** por hunt (até 3 criaturas, com o bónus sugerido).
8. **Completar os caminhos.** As 129 hunts sem passos ganham caminho escrito à mão, e os passos existentes ganham
   pontos no mapa e NPCs, por lotes.

## O que sai da ficha

Da ficha da hunt saem: sessões reais (`haHTML`), mortes de ontem (`kstat`), composição por tipo de
criatura, o bloco «Setup» (`setupHTML`), os sets de equipamento (`hsetsHTML`), o bloco «Wheel, gemas e charms»
(`hwheelHTML`, ficam só os charms), as variantes do TibiaPal e os cinco separadores. Do boss saem a lista «Porquê e
como» e o botão do Bosstiary da ficha (o Bosstiary continua na linha da lista).

## Não-objetivos

- Tirar as páginas Equipamento e Wheel do site. **Leitura do pedido:** «retiramos os equips e a wheel» refere-se às
  fichas de hunts e bosses. As páginas próprias ficam (decisão do autor do plano; o dono confirma).
- Mexer na lista de hunts além do cartão (filtros, ordenação). No comparar hunts muda só a coluna «Risco», que passa
  a ser a dificuldade 1–5 (ronda 2, Q2).
- A rotação diária de bosses (`docs/superpowers/specs/2026-11-07-bosses-quests-design.md`, ainda por aprovar).
- Traçar o caminho a pé no mapa. A linha tracejada entre passos seguidos (ronda 3, Q8) mostra a **ordem** dos passos,
  não o percurso; a legenda diz isso.

## Anti-objetivos (falha mesmo que funcione)

- Inventar um caminho. Onde não há passos confirmados, a ficha diz «por documentar» e mostra só o que se sabe.
- Um ponto no mapa apresentado como entrada quando é só a zona.
- Perder informação de acesso que hoje existe (`G.hv`, `G.routes`, `p.acc`, fichas de locais).
- Texto abaixo de 12 px, alvos de toque abaixo de 44 px, scroll horizontal, partir as 8 línguas ou os PCs fracos.

## Restrições

- Regras do projeto em `_dev/GRIMORIO.md` (edições ancoradas ao `index.html`, `node --check`, G só pelo `gjson.py`,
  i18n pelo `_dev/i18n.py`, `?v=` novo em cada ficheiro mudado, PT-PT).
- Sem bibliotecas novas. O mapa é `<canvas>` sobre os PNG dos andares, com os marcadores numerados do minimapa do
  Questski (`drawMinimap`, `.mm-mark`), que passa para `shared/minimapa.js` e serve os dois sites (ronda 3, Q8).
- A lógica nova fica em `shared/fichas.js` (testável em node, como `shared/bosses.js`); o `index.html` só desenha.

## Caminhos considerados

1. **Ficha nova num só painel, dados de caminho num ficheiro próprio** (escolhido). A ficha deixa de ter separadores;
   o caminho vem de `data/caminhos.json`, gerado por `_dev/build_caminhos.py` a partir do que existe e de um ficheiro
   escrito à mão que tem prioridade. Permite completar os caminhos por lotes sem tocar no código.
2. **Limpar a ficha atual**, tirando blocos e mantendo os separadores e o texto livre do `G.hv`. Mais rápido, mas os
   passos continuam sem pontos nem NPCs, e o mapa não fica ao lado do caminho.
3. **Página própria por hunt** (`#hunt/<slug>`), em vez do painel. Melhor para a pesquisa da Google, mas é o projeto
   das páginas com endereço próprio e muda a navegação. Fica para depois; a ficha nova pode ser reutilizada lá.

## Decisões

### Modelo de dados (`data/caminhos.json`)

```
{ "v": 1, "gen": "AAAA-MM-DD", "h": { "<pid>": Caminho }, "b": { "<chave do boss>": Caminho },
  "places": { "<título>": Local } }      // cada ficha de local uma só vez (ronda 1, Q3)

Caminho = { "st": "ok" | "rev" | "part" | "none",
            "from": "Thais" | null,
            "pos": [x, y, z] | null, "pa": 0 | 1,
            "pre": [Pre], "legs": [Troco],
            "refs": [ { "slug": "grimvale-quest", "sec": 10, "t": "11. Paradise Lost: chegar a Oskayaat",
                        "quest": "Grimvale Quest" } ] }      // passos de guias do Questski que levam lá (opcional)
Troco   = { "t": "Chegar a Issavi", "steps": [Passo] } | { "ref": "<título de places>" }
Local   = { "title", "entrance": {x,y,z,label} | null, "arrive": [Passo], "leave": [Passo], "warnings": ["…"] }
Passo   = { "s": "texto", "c": [x, y, z] | null,
            "npc": { "n": "Captain Bluebear", "say": ["hi", "targuna", "yes"], "gp": 110 | null } | null }
Pre     = { "k": "quest", "n": "Grimvale Quest", "id": "<id do G.quests>" | null,
            "slug": "grimvale-quest" | null, "sec": 10 | null, "note": "até entregares a ocarina" | null }
        | { "k": "level", "n": 250, "rec": true | false }
        | { "k": "premium" } | { "k": "item", "n": "Pá" } | { "k": "text", "s": "…" }
```

- `st`: `ok` confirmado, `rev` revisto, `part` leva à zona mas falta o último troço, `none` por documentar.
- `pa = 1`: o ponto é a zona, não a entrada (nas hunts, quando o `G.hm[pid][3]` é `"a"`).
- Depois desta mudança, o site lê só o `data/caminhos.json`. O `hunt-access.json` e o `boss-access.json` continuam a
  ser gerados, mas passam a ser dados de entrada do `build_caminhos.py`.
- O texto dos passos aceita a marcação que o site já usa (`{npc:}`, `{key:}`, `{item:}`, `{wiki:}`, `{coord:x,y,z}`, `**negrito**`).
- Origem, por ordem: `_dev/caminhos_manual.json` (escrito à mão) › `G.hv` › `G.routes` › `p.acc` (fica `none`, um
  passo de texto). As fichas de locais do `hunt-access.json`/`boss-access.json` entram como primeiro troço
  («Chegar a <local>») quando o caminho não é manual.

### Índice de dificuldade (1 a 5)

Para hunts: `base = [1, 3, 4][d − 1]` (o `d` de `G.places`), ajustado pelo golpe mais forte das criaturas principais
(`m` do `data/crdmg.json`) a dividir por uma vida de referência no nível recomendado, `185 + 10 × (L − 8)`:
`+1` se a razão for ≥ 0,5; `−1` se for < 0,2 e `d` > 1. Limites 1 e 5. Sem dano conhecido, fica a base.
Nomes: 1 muito fácil, 2 fácil, 3 média, 4 difícil, 5 muito difícil.

Para bosses, pelo resultado do `GrimBoss.judge` da personagem ativa: sozinho com folga (vida efetiva ≥ 3 × golpe e
tempo ≤ metade do limite) 2; sozinho 3; em equipa ou vida desconhecida 4; mais tarde ou sem acesso 5. A ficha diz
«para o teu nível».

### XP e lucro por hora

Os mesmos números que a ficha mostra hoje (`h.xp` e `h.lo` do `huntRows`): com «≈» quando são estimados, lucro
negativo a vermelho, e as estrelas da TibiaWiki quando a hunt ainda não tem medição. O painel «Loot e lucro» (a conta
com os preços do Market) não volta: fica só o número. Nos bosses, o lugar do lucro por hora é o **valor por kill**
(`lootPerKill`, aos preços do mundo da personagem).

### Preys

Criaturas da hunt ordenadas por XP × quantidade (`G.pm[pid].h` com o XP do `G.mon`):
1. a 1.ª leva **Bónus de XP**;
2. a 2.ª leva **Bónus de dano**;
3. a que bate mais forte leva **Redução de dano** se o golpe for ≥ 35 % da vida de referência; senão a 3.ª por XP
   leva **Bónus de dano**.
Sem repetir criaturas; menos criaturas, menos preys. A ficha lembra que o 3.º slot de prey é da Store.

### Loot principal

Até 8 itens diferentes das criaturas da hunt, por `valor × probabilidade × quantidade`, com a criatura que o deixa
cair, a probabilidade e o valor. Nos bosses, o `top` do `lootPerKill`.

**Preços do Market do mundo da personagem, sempre do dia** (pedido do dono, 10/11/2026). Não é preciso nada novo para
os manter atualizados: o `api/market.php` já vai buscar os preços ao TibiaMarket por mundo e guarda-os 6 horas; o
browser guarda-os 2 horas (`mktLoad`). Quem abre uma ficha recebe preços com, no máximo, umas horas. A ficha usa a
regra de preços do site (`priceOf`: o Market quando é fiável e paga mais do que o NPC, senão o NPC) e diz de onde vem
cada valor e de quando é o scan do Market (o campo `updated` da resposta: «Market de Antica, hoje às 06:12»).
Sem mundo na personagem, ou com o Market em baixo: preço do NPC e a frase «Preços do NPC: o Market não respondeu.»
(ou «Escolhe o mundo da personagem para ver os preços do Market.»). O lucro por hora continua a ser o número medido
(TibiaPal ou sessões reais), não uma conta com os preços do dia.

### Resistências

Os 7 elementos do `p.eff` (média das criaturas), cada um com a percentagem de dano que levam, do mais fraco para o
mais resistente; imune (`eff.min` = 0) e cura assinalados. Nos bosses, o `el` da criatura.

## Decisões da ronda 1 (grilling, 10/11/2026; o dono respondeu «ok» às recomendações)

- **Q1** Equipamento e Wheel saem só das fichas; as páginas próprias ficam.
- **Q2** A ficha continua no painel (`#sheet`); o `fichaHTML` fica pronto para as páginas com endereço próprio, depois.
- **Q3** Fichas de locais uma só vez em `places`; os troços apontam com `{"ref": "<título>"}`.
- **Q4** O texto dos caminhos entra no circuito de conteúdo do i18n (`content.json`, tradução para inglês; as outras
  línguas caem no inglês). Cada lote da parte C traz a tradução inglesa dos seus passos.
- **Q5** Os pré-requisitos mostram o estado da quest inteira (`c.done`). O estado por passo («até entregares a ocarina»)
  fica para o desenho de 7/11 (passos do Questski por personagem), a fazer a seguir a este.
- **Q6** Dificuldade: nas hunts igual para todos; nos bosses, para o nível da personagem.
- **Q7** Um agente por tarefa, com revisão antes da seguinte. O dono aprova no fim da parte A, no fim da parte B (com
  capturas) e em cada lote da parte C (PR). Nada entra no `main` sem o OK dele.
- **Q8** Parte C: fontes = dados do site, guias do Questski e TibiaWiki pela API (`api.php`; a página normal dá 403).
  `ok` só com a wiki a confirmar todos os passos. Lotes de 25, em paralelo com a parte B depois da Task 2.

## Decisões das rondas 2 a 4 (grilling, 10/11/2026)

Estas decisões **mudam** a Q6 da ronda 1 e as secções «Índice de dificuldade» e «XP e lucro por hora» acima: onde
houver conflito, vale o que está aqui.

### Ronda 2

- **Q1** O Questski continua a ler `quests/data/places.json`; o `build_caminhos.py` lê-o através do `hunt-access.json` e
  do `boss-access.json`. Corrigir um local é no `places.json` e regenerar.
- **Q2** O comparar hunts (bandeja e tabela) fica igual, mas a coluna «Risco» passa a ser a dificuldade 1–5 do
  `GrimFicha.huntDiff`, para a personagem ativa (um só índice no site).
- **Q3** Os números e a dificuldade são **da personagem**: o objetivo é ver hunts medidas por outros jogadores e
  ajustá-las ao nível, à vocação e ao equipamento da personagem. Uma hunt difícil para uma vocação pode ser fácil para
  outra. Sem linha para a vocação ativa, a ficha estima na mesma (não mostra «—» só por isso).
- **Q4** Cada lote da parte C é um PR para o ramo `fichas-hunts-bosses`; o merge final para o `main` leva tudo.

### Ronda 3

- **Q5** O motor do `huntRows` (TibiaPal das 5 vocações, sessões reais `G.ha`, fator de vocação `compatFor` × `G.vr`,
  estimativa `mx` por mortes/h) passa para o `shared/fichas.js` como função pura (`GrimFicha.huntEst`) e serve
  **qualquer** hunt. Número que não é medição da vocação ativa leva «≈» e a origem («≈ a partir de paladins nível 300»).
- **Q6** Ajuste ao nível (opinião do autor, a afinar na parte D): `f = (L / Lm) ^ k`, `k = 0,5` por omissão, limitado a
  0,7–1,25, aplicado ao XP/h e ao lucro/h. `L` = nível da personagem; `Lm` = nível da medição (linha do TibiaPal: o
  `l` da linha; sessões reais: o nível mediano). Com `L < 0,6 × Lm` não se estima («abaixo do nível da medição»). A
  estimativa `mx` já usa o nível do jogador e não leva este fator. O mesmo número aparece em todo o site (cartões,
  ficha, comparar), para não haver dois valores para a mesma hunt.
- **Q7** Dificuldade = o mesmo motor nas hunts e nos bosses:
  - por criatura principal da hunt (`G.pm[pid].h` ∩ `mons`, sem bosses): golpe efetivo =
    `máx` por elemento de `d[el] × (1 − prot[el] / 100)` (`d` do `data/crdmg.json`; sem `d`, o `m` conta como físico);
  - `r` = o pior golpe efetivo ÷ a vida efetiva da personagem (`GrimBoss.effHP(voc, L, ml)`: vida × mitigação da
    vocação; magos com o Magic Shield);
  - `base = [1, 3, 4][d − 1]` (o `p.d` curado); `+2` se `r ≥ 1` (um golpe pode matar), `+1` se `r ≥ 0,5`, `−1` se
    `r < 0,2` e `d > 1`; mais o ajuste da parte D (`calib.dz[pid]`, −1/0/+1); limites 1 e 5;
  - **a distância não entra**: o `crdmg.json` não separa o físico corpo a corpo do físico à distância;
  - bosses: o `GrimBoss.judge` recebe as mesmas proteções (`opt.prot`) e aplica-as ao `md` quando há `b.dm`.
- **Q8** Mapa: o minimapa do Questski (canvas, marcadores numerados) em `shared/minimapa.js`, com uma linha tracejada
  entre passos seguidos no mesmo andar; ligação «Abrir no mapa do Questski» para o mapa grande (Leaflet, que não entra
  no Grimório).

### Ronda 4

- **Q9** Proteções da personagem: o set ativo (`c.sets` com `c.aset`) quando `c.hset === "mine"`; em todos os outros
  casos, o `bisSet(c)` (o best set que o site já calcula para o nível). Soma dos itens e dos imbuements
  (`setTotals`: `ab` + `abi`). A ficha diz qual usou: «Contas com o teu set "<nome>"» ou «…com o best set do nível N».
  Sem personagem: nível recomendado da hunt, vocação do filtro, sem proteções, com a nota «sem personagem: conta só a
  vida».
- **Q10** Motor de calibração `_dev/calibrar.py` → `data/calib.json` (lido pelo `GrimFicha`): (1) afina o `k` do
  ajuste de nível e as mortes/h por zona com as sessões reais e o TibiaPal; (2) extrapola para hunts sem medição a
  partir de hunts parecidas (mesma faixa de nível, número de spawns do `G.pm` e vida média das criaturas); (3)
  relatório das hunts cuja estimativa se afasta mais de 25 % das sessões reais.
- **Q11** Corre numa tarefa agendada na cloud que abre um PR; nada chega ao site sem aprovação.
- **Q12** O motor é a **parte D**, depois da B. A ficha (B) usa os valores de omissão; a D só afina.
- **Q13** Fontes: o `G.ha` atual; ficheiros de sessões importados em `_dev/sessoes/` (sem nomes de personagens, RGPD);
  a API do TibiaData (`api.tibiadata.com`, já no CSP); o Hunt Analyser pela conta do site, consultado no Chrome numa
  sessão local (o dono está autorizado a entrar). Só agregados entram no repositório.
- **Q14** TibiaData `killstatistics/<mundo>`: (1) sinal de perigo = jogadores mortos ÷ criaturas mortas, somado em
  todos os mundos, por criatura e depois por hunt (pesado pelo `G.pm`) → `calib.dz`; (2) «hunt muito disputada no teu
  mundo», calculado no browser com as estatísticas do mundo da personagem.
- **Q15** Rotina semanal (segunda, 05:41 UTC): corre o `_dev/calibrar.py` (TibiaData + `G.ha` + importados), grava o
  `data/calib.json` e o relatório e, se houver mudanças, abre um PR para o `main` com o relatório. Criada só depois de o
  script estar feito e testado.

## Deixado ao construtor

- O aspeto fino (espaços, cores) dentro do tema atual; a estrutura e a ordem estão fixas acima.
- A ordem dos lotes de conteúdo dentro de cada faixa de nível.
- Remover funções que fiquem sem uso (`grep` antes de apagar).

## Como se prova

- `node _dev/fichas_test.mjs` (modelo: dificuldade, preys, loot, viewport do mapa, marcação dos passos).
- `python3 -I _dev/build_caminhos.py --check` (ficheiro em dia, todas as hunts e bosses presentes, NPCs e pontos válidos).
- Browser (Playwright ou `smoke.mjs`): Hunts e Bosses a 1440 e 390 px, em pt-PT, en e de; sem erros, sem scroll lateral,
  letra ≥ 12 px, alvos ≥ 44 px; a ficha não contém «Setup», «Wheel» nem sets.
- `node _dev/travel_access_test.mjs` e `node _dev/bosses_test.mjs` continuam a passar (ou são atualizados na mesma tarefa).
