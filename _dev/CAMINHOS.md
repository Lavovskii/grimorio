# Caminhos escritos à mão (`_dev/caminhos_manual.json`)

Guia da parte C do plano `docs/superpowers/plans/2026-11-10-fichas-hunts-bosses.md`: completar, por lotes, o «Como lá
chegar» das fichas de hunts e bosses. Não há código novo: cada lote acrescenta entradas ao `_dev/caminhos_manual.json`,
regenera o `data/caminhos.json`, traduz os passos novos e abre um PR para o ramo `fichas-hunts-bosses`.

## Como funciona

- O site lê só o `data/caminhos.json` (gerado). Quem o faz é o `_dev/build_caminhos.py`, que usa, por ordem:
  `_dev/caminhos_manual.json` › `G.hv` › `G.routes` › `p.acc` (este último fica `none`, com um passo de texto).
- Uma entrada no manual **substitui por inteiro** o caminho gerado dessa hunt ou desse boss (não se junta a ele). Por isso
  a entrada tem de ter tudo: estado, ponto, pré-requisitos e troços.
- As fichas de locais do Questski (`quests/data/places.json`, através do `data/hunt-access.json` e do
  `data/boss-access.json`) entram como troço `{"ref": "<título>"}`. Corrigir um local é no Questski (`_questski/places/`),
  não aqui; depois `python -I _dev/build_hunt_access.py` / `build_boss_access.py` e o `build_caminhos.py`.

## Formato

O ficheiro tem duas listas: `h` (hunts, chave = o `pid` de `G.places`) e `b` (bosses, chave = a chave do `data/bosses.json`,
em minúsculas). Começa como `{"h": {}, "b": {}}`.

```
Caminho = { "st": "ok" | "rev" | "part" | "none",
            "from": "Thais" | null,                    // cidade com depot de onde se parte
            "pos": [x, y, z] | null, "pa": 0 | 1,      // ponto da hunt/sala; pa = 1 → é a zona, não a entrada
            "pre": [Pre], "legs": [Troço],
            "refs": [ { "slug", "sec", "t", "quest" } ] }   // opcional: passos de guias do Questski que levam lá
Troço   = { "t": "Título do troço", "steps": [Passo] } | { "ref": "<título de um local do Questski>" }
Passo   = { "s": "texto", "c": [x, y, z] | null,
            "npc": { "n": "Nome do NPC", "say": ["hi", "…", "yes"], "gp": 110 | null } | null }
Pre     = { "k": "quest", "n": "Nome da quest", "id": "<id do G.quests>" | null,
            "slug": "<slug do guia do Questski>" | null, "sec": <índice da secção do guia> | null, "note": "até …" | null }
        | { "k": "level", "n": 250, "rec": true | false }     // rec = recomendado (senão é o mínimo)
        | { "k": "premium" } | { "k": "item", "n": "Pá" } | { "k": "text", "s": "…" }
```

- `st`: `ok` só se a TibiaWiki confirma **todos** os passos; `rev` revisto (fontes do site e do Questski, sem confirmação
  completa); `part` leva à zona mas falta o último troço; `none` por documentar (no máximo um troço, sem passos inventados).
- `c` = o ponto do passo no mapa do jogo (`x` 31000–34500, `y` 30900–33100, `z` 0–15; 7 = superfície). A ficha desenha um
  mapa por troço com os pontos numerados pela ordem dos passos.
- `npc.n` tem de existir no `data/npcs.json`; `say` são as palavras exatas, em inglês, como se escrevem no jogo (nunca se
  traduzem); `gp` só quando se paga. O texto do passo pode repetir a fala: a ficha tira-a (`camSayCut`) porque o bloco
  «Fala com …» já a mostra.
- `slug` e `sec`: o guia tem de existir no `data/guias.json` e a secção tem de existir no guia (`sec` começa em 0; a ficha
  liga a `quests/#/quest/<slug>/guia/sec-<sec>`).

### Exemplo completo

Uma hunt com o caminho todo escrito à mão (os passos e os pontos são os que o site já tem para a Infernal Targuna:
`G.hv.targuna_inf` e `data/npcs.json`):

```json
{
 "h": {
  "targuna_inf": {
   "st": "rev",
   "from": "Thais",
   "pos": [32423, 32656, 13],
   "pa": 1,
   "pre": [
    {"k": "quest", "n": "Targuna", "id": "targuna", "slug": "targuna-quest", "sec": null, "note": null},
    {"k": "level", "n": 12, "rec": false},
    {"k": "text", "s": "Missão Burning Heart (Targuna Quest) com a {npc:Emiliana}: {key:hi}, {key:mission}, {key:yes}"}
   ],
   "legs": [
    {"t": "Chegar a Targuna", "steps": [
     {"s": "Barco do Captain Bluebear em Thais: hi, targuna, yes (110 gp)", "c": [32310, 32210, 6],
      "npc": {"n": "Captain Bluebear", "say": ["hi", "targuna", "yes"], "gp": 110}},
     {"s": "Templo de Targuna: vai ao depot", "c": null, "npc": null}
    ]},
    {"t": "Até à Crimson Court", "steps": [
     {"s": "Sobe as escadas à direita do depot até à Emiliana", "c": [31962, 31898, 7], "npc": null},
     {"s": "Emiliana: hi, mission, yes", "c": [31960, 31901, 6],
      "npc": {"n": "Emiliana", "say": ["hi", "mission", "yes"], "gp": null}},
     {"s": "Sobe mais um andar e entra no Energy Portal → Crimson Court", "c": null, "npc": null},
     {"s": "Desce um andar: Infernoids por toda a corte", "c": null, "npc": null}
    ]}
   ],
   "refs": []
  }
 },
 "b": {}
}
```

Com uma ficha de local do Questski no início, o 1.º troço é `{"ref": "Ab'Dendriel"}` (o título exato do local em
`data/caminhos.json` → `places`); a ficha mostra «Chegar a Ab'Dendriel», os passos de chegada, os avisos e «Como sair».
Um pré-requisito que só abre a meio de uma quest leva a secção e a nota, por exemplo
`{"k": "quest", "n": "Grimvale Quest", "id": null, "slug": "grimvale-quest", "sec": 10, "note": "até entregares a ocarina"}`
(confirma o `id` no `G.quests` e a secção no guia antes de a pôr).

## Texto dos passos

- Português de Portugal, frases curtas, **uma ação por passo** (andar até X, falar com Y, usar Z, descer, subir).
  Direções pelos pontos cardeais («a nordeste do templo»).
- Marcação aceite (a mesma do Questski): `{npc:Nome}`, `{item:Nome}` ou `{item:Nome|texto}`, `{creature:Nome}`,
  `{spell:Nome}`, `{wiki:Nome}`, `{key:palavra}` (palavras a escrever no jogo), `**negrito**` e `{coord:x,y,z}` (botão para
  o mapa grande). Uma coordenada nunca vai em texto simples («(32735, 31668)»): o `--check` recusa; usa o `c` do passo ou
  `{coord:…}`.
- Os nomes do jogo (NPCs, criaturas, itens, sítios, quests, feitiços) ficam em inglês, como no jogo.

## Fontes aceites

Por esta ordem de confiança:

1. O que o site já tem: `G.hv[pid]`, `G.routes[pid]`, `G.places[pid].acc`, a ficha de local do `hunt-access.json` /
   `boss-access.json` e as notas da verificação em `_dev/hv_notas.json`.
2. O guia do Questski da quest de acesso (`quests/data/quests/<slug>.json`: secções e passos, já em PT-PT, com NPCs e falas).
3. A página do sítio na TibiaWiki (`https://tibia.fandom.com/wiki/<Nome>`: «Location», «Notes», `{{Mapper Coords}}`) e a
   página de cada NPC citado.
4. Posições: `data/npcs.json` (NPCs), `data/spawns.json` (criaturas) e o mapa do site (`openMap`) para confirmar o andar.

Se uma fonte de fora contradiz o site, fica o que a TibiaWiki diz hoje, e anota-se a diferença em `_dev/hv_notas.json`.

## Regras

- **Nunca inventar.** O que não se consegue confirmar numa fonte não entra. Mais vale `part` (só até à zona) ou `none`
  do que um passo inventado. Nada de deduzir caminhos pela distância, pela cidade mais perto ou pelas criaturas.
- **Ponto aproximado.** Com `pa = 1` o ponto é a zona, não a entrada: a ficha diz «O ponto no mapa é a zona aproximada.» e
  nunca lhe chama entrada. Usa `pa = 1` sempre que o ponto não for a entrada confirmada (nas hunts, quando o
  `G.hm[pid][3]` é `"a"`).
- Começa numa cidade com depot (`from`); o 1.º troço leva à zona (barco, tapete, teleporte, a pé), o último à entrada.
- Todo o passo de falar com um NPC tem `npc` com `say` (e `gp` quando se paga). Todo o passo que muda de sítio de forma não
  óbvia (escada, buraco, teleporte, porta, alavanca) tem `c`. Pelo menos um ponto por troço; o último passo com ponto é a
  entrada ou o 1.º andar da hunt.
- Pré-requisitos: as quests com `slug` (e `sec` + `note` quando o acesso abre a meio), o nível mínimo e o recomendado,
  premium e os itens (pá, corda, chave, itens de quest).

## Comandos

```
python3 -I _dev/build_caminhos.py                    # regenera data/caminhos.json
python3 -I _dev/build_caminhos.py --check            # sai com 1 se estiver desatualizado ou inválido (diz onde)
python3 -I _dev/build_caminhos.py --report           # contagem por estado, passos com ponto e com NPC, KB
python3 -I _dev/build_caminhos.py --lote 1 --tam 10 --tipo h --estado none
                                                     # próximo grupo de chaves sem entrada no manual
                                                     # (hunts por nível mais baixo; bosses pelo nível recomendado)
node _dev/fichas_test.mjs                            # modelo e data/caminhos.json
```

O `--lote 1` repete-se de lote para lote: a lista só tem chaves **sem** entrada manual, por isso depois de um lote entrar o
lote 1 passa a ser o seguinte.

## Traduzir os passos novos

O texto dos passos aparece em inglês (e nas outras línguas, que usam o inglês de reserva) pelo dicionário de conteúdo:

```
python3 -I _dev/i18n.py extract
python3 -I _dev/i18n.py todo content en 400          # repetir até vir {}
python3 -I _dev/i18n.py merge content en lote.json   # {chave: tradução}
python3 -I _dev/i18n.py build
```

As chaves são o texto como aparece no ecrã (sem as marcas; um `{coord:}` parte a frase em duas), por isso a tradução é texto
simples: mantém os nomes do jogo e as palavras das falas iguais, para os links e os `<kbd>` voltarem ao sítio. Depois muda o
`DV` do `shared/i18n.js` e o `?v=` do `shared/i18n.js` no `index.html`, no `quests/index.html` e no `privacidade.html`.

## Antes de fechar um lote

1. **Fontes juntas** para cada hunt ou boss, pela ordem da secção «Fontes aceites»; diferenças anotadas em `_dev/hv_notas.json`.
2. **Entrada escrita** no `_dev/caminhos_manual.json` com as regras acima (um passo = uma ação, NPCs com `say`, pontos nos
   passos que mudam de sítio, pré-requisitos com o guia e a secção, `st` honesto).
3. **Valida e traduz:** `python3 -I _dev/build_caminhos.py && python3 -I _dev/build_caminhos.py --check &&
   node _dev/fichas_test.mjs && python3 -I _dev/build_caminhos.py --report` (as hunts `none` descem, os passos com ponto e
   com NPC sobem), e a tradução inglesa dos passos novos (secção anterior).
4. **Confirma no mapa:** abre cada ficha no site e o mapa de cada troço: os pinos caem em chão caminhável, pela ordem dos
   passos, no andar certo. Um pino no preto ou dentro de uma parede é uma coordenada errada: corrige.
5. **PR** para o ramo `fichas-hunts-bosses` com o `--report` antes e depois. Se um lote tiver mais de 5 hunts que só dão
   `part`, pára e pergunta ao dono.
