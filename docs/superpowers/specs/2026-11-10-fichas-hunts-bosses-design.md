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
6. **Índice de dificuldade de 1 a 5**, igual para toda a gente (descreve a hunt, não a personagem).
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
- Mexer na lista de hunts além do cartão (filtros, ordenação, comparar hunts).
- A rotação diária de bosses (`docs/superpowers/specs/2026-11-07-bosses-quests-design.md`, ainda por aprovar).
- Traçar o caminho a pé no mapa (linhas). Os pontos são factos documentados; uma linha entre eles não é.

## Anti-objetivos (falha mesmo que funcione)

- Inventar um caminho. Onde não há passos confirmados, a ficha diz «por documentar» e mostra só o que se sabe.
- Um ponto no mapa apresentado como entrada quando é só a zona.
- Perder informação de acesso que hoje existe (`G.hv`, `G.routes`, `p.acc`, fichas de locais).
- Texto abaixo de 12 px, alvos de toque abaixo de 44 px, scroll horizontal, partir as 8 línguas ou os PCs fracos.

## Restrições

- Regras do projeto em `_dev/GRIMORIO.md` (edições ancoradas ao `index.html`, `node --check`, G só pelo `gjson.py`,
  i18n pelo `_dev/i18n.py`, `?v=` novo em cada ficheiro mudado, PT-PT).
- Sem bibliotecas novas. O mapa é `<canvas>` sobre os PNG dos andares, como hoje.
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
{ "v": 1, "gen": "AAAA-MM-DD", "h": { "<pid>": Caminho }, "b": { "<chave do boss>": Caminho } }

Caminho = { "st": "ok" | "rev" | "part" | "none",
            "from": "Thais" | null,
            "pos": [x, y, z] | null, "pa": 0 | 1,
            "pre": [Pre], "legs": [Troco],
            "refs": [ { "slug": "grimvale-quest", "sec": 10, "t": "11. Paradise Lost: chegar a Oskayaat",
                        "quest": "Grimvale Quest" } ] }      // passos de guias do Questski que levam lá (opcional)
Troco   = { "t": "Chegar a Issavi", "steps": [Passo] }
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
cair, a probabilidade e o valor (a regra de preços do site: `priceOf`). Nos bosses, o `top` do `lootPerKill`.

### Resistências

Os 7 elementos do `p.eff` (média das criaturas), cada um com a percentagem de dano que levam, do mais fraco para o
mais resistente; imune (`eff.min` = 0) e cura assinalados. Nos bosses, o `el` da criatura.

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
