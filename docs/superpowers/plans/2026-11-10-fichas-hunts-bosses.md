# Fichas objetivas de hunts e bosses — Plano de implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Trocar a ficha das hunts e a dos bosses por uma ficha única e objetiva: mapa ao lado de «Como lá chegar», pré-requisitos ligados às quests, criaturas, loot principal, charms e preys, e só cinco números (XP/h, lucro/h, nível recomendado, resistências, dificuldade de 1 a 5).

**Architecture:** O caminho de cada hunt e de cada boss passa para um ficheiro novo, `data/caminhos.json`, gerado por `_dev/build_caminhos.py` a partir dos dados que já existem e de um ficheiro escrito à mão que tem prioridade. A lógica nova (dificuldade, preys, loot, resistências, enquadramento do mapa) fica em `shared/fichas.js`, testável em node. O `index.html` só desenha: uma função `fichaHTML` comum, usada pela ficha da hunt e pela do boss. No fim, os caminhos em falta são escritos por lotes, sem tocar no código.

**Tech Stack:** HTML/CSS/JS sem bibliotecas (o `index.html` é uma SPA de um só ficheiro), `<canvas>` sobre `maps/floor-NN-map.png`, Python 3 para os scripts de dados (`python3 -I`), node para os testes (`node:assert`, `node:vm`), Playwright para o teste no browser.

**Spec:** `docs/superpowers/specs/2026-11-10-fichas-hunts-bosses-design.md` (lê-a antes de começar; este plano parte dela).

## Global Constraints

- Lê `_dev/GRIMORIO.md` antes de mexer no código. As regras de lá valem em todas as tarefas.
- Texto do site em **português de Portugal**, curto, sem jargão. Escrita normal em commits e documentos.
- `index.html`: edições por script Python com substituições ancoradas (`assert s.count(antigo) == 1`), escrita em UTF-8 com `newline=''`. Depois de cada edição: `node --check` do JS extraído (entre `'<script>\n(function(){'` e o `'</script>'` seguinte) e `python3 -I _dev/gjson.py . --check`.
- O G (dados embebidos) só se grava com `load_G`/`save_G` do `_dev/gjson.py`. Este plano **não muda o G**.
- Letra ≥ 12 px, alvos de toque ≥ 44 px, contraste ≥ 4,5:1, sem scroll horizontal a 390 px. Funciona com `html.fx-lite` (sem animações novas).
- Sem bibliotecas novas. Sem pedidos a domínios novos (o CSP do `.htaccess` não muda).
- Ficheiro mudado que o site carrega leva `?v=20261110a` (ou a data do dia + letra) em todos os sítios onde é referido.
- Nunca inventar um caminho: sem passos confirmados, o estado é `none` e a ficha diz «por documentar».
- Um ponto com `pa = 1` nunca é apresentado como entrada: a legenda diz «zona aproximada».
- Texto novo visível passa pelo i18n (Tarefa 6): `i18n/src/ui-extra.json`, `python3 -I _dev/i18n.py extract`, `merge ui <língua>`, `build`, para en, pt-BR, es, de, pl, sv, nl.
- Ramo de trabalho: `fichas-hunts-bosses`, a partir do `main`. Um commit por tarefa. PR no fim de cada parte (A+B juntas, depois cada lote da parte C).
- Não mexer nas páginas Equipamento e Wheel, nos filtros das Hunts nem no comparar hunts.

## Review Focus

1. **Hunt sem caminho documentado** (129 hoje): a ficha abre, mostra o mapa da zona e a frase que existe, com «por documentar»; não fica vazia nem com erro. Teste na Tarefa 2 (`st == "none"`) e na Tarefa 4 (browser).
2. **`data/caminhos.json` não carrega** (offline, 404): a ficha mostra «Não consegui carregar o caminho» com «Tentar de novo», e o resto da ficha (números, criaturas, loot) aparece na mesma. Teste na Tarefa 3.
3. **Passos em andares diferentes**: o mapa do troço mostra o andar do passo escolhido e só os pontos desse andar; ao tocar noutro passo, muda de andar. Teste na Tarefa 1 (`viewport`) e na Tarefa 3.
4. **Hunt sem criaturas com dano conhecido ou sem loot com preço**: dificuldade fica na base, preys saem só as que dá para decidir, loot diz «sem dados»; nada de `NaN` nem `undefined`. Teste na Tarefa 1.
5. **Personagem sem a quest do pré-requisito, ou sem personagem**: o pré-requisito mostra «por fazer» com ligação ao guia; sem personagem ativa, mostra a lista sem estado. Teste na Tarefa 3 (`preHTML`).

---

## Estrutura de ficheiros

| Ficheiro | Papel |
|---|---|
| `shared/fichas.js` (novo) | `window.GrimFicha`: funções puras (dificuldade, preys, loot, resistências, viewport). Mesmo invólucro UMD do `shared/bosses.js`. |
| `_dev/fichas_test.mjs` (novo) | Testes do `shared/fichas.js` e do `data/caminhos.json`. |
| `_dev/build_caminhos.py` (novo) | Gera `data/caminhos.json`; `--check`, `--report`, `--lote`. |
| `_dev/caminhos_manual.json` (novo) | Caminhos escritos à mão (têm prioridade). Começa com `{"h": {}, "b": {}}`. |
| `data/caminhos.json` (novo, gerado) | O que o site lê. |
| `_dev/fichas_browser.cjs` (novo) | Teste no browser com Playwright (Hunts e Bosses, 2 larguras, 3 línguas). |
| `_dev/CAMINHOS.md` (novo) | Como escrever um caminho à mão (formato, fontes, regras, exemplo). |
| `index.html` (mudado) | `camData`, `camFill`, `camHTML`, `drawCam`, `preHTML`, `fichaHTML`, `huntSheet` (reescrita), `placeSheet`, `bossSheet`, CSS `.fx-*`/`.cam-*`. |
| `_dev/travel_access_test.mjs` (mudado) | Passa a testar o `camFill` em vez do `huntRoute`/`hAccessFill`. |
| `_dev/GRIMORIO.md`, `README.md` (mudados) | Secção nova e lista de ferramentas. |

---

# Parte A — Dados e modelo

### Task 1: Modelo `shared/fichas.js`

**Files:**
- Create: `shared/fichas.js`
- Test: `_dev/fichas_test.mjs`

**Interfaces:**
- Consumes: nada.
- Produces (`GrimFicha`):
  - `refHp(L: number): number`
  - `huntDiff(o: {d: 1|2|3, hit: number|null, L: number}): 1|2|3|4|5`
  - `bossDiff(o: {st: string, eff: number|null, md: number|null, ttk: number|null, tmax: number}): 2|3|4|5`
  - `DIFF: string[]` = `["", "muito fácil", "fácil", "média", "difícil", "muito difícil"]`
  - `PREY: {xp: "Bónus de XP", dmg: "Bónus de dano", red: "Redução de dano"}`
  - `preyPicks(mons: {k: string, n: string, xp: number, cnt: number, hit: number|null}[], L: number): {k: string, n: string, bonus: "xp"|"dmg"|"red"}[]`
  - `topLoot(mons: {k: string, n: string, cnt: number, loot: {n: string, pct: number, v: number}[]}[], max?: number): {n: string, pct: number, v: number, from: string}[]`
  - `resist(eff: object|null): {el: string, pct: number, imm: boolean, heal: boolean}[]`
  - `viewport(pts: [number, number, number][], sel: number, W: number, H: number): {z: number, x0: number, y0: number, s: 1|2|4|8, on: number[]}`

- [ ] **Step 1: Escreve o teste que falha** em `_dev/fichas_test.mjs`

```js
// Modelo das fichas (shared/fichas.js). Uso: node _dev/fichas_test.mjs
import { createRequire } from "module";
import assert from "node:assert/strict";
const F = createRequire(import.meta.url)("../shared/fichas.js");

// vida de referência
assert.equal(F.refHp(8), 185); assert.equal(F.refHp(100), 1105); assert.equal(F.refHp(1), 185);
// dificuldade das hunts
assert.equal(F.huntDiff({ d: 1, hit: null, L: 50 }), 1);
assert.equal(F.huntDiff({ d: 1, hit: 400, L: 50 }), 2);      // 400 / 605 ≥ 0,5
assert.equal(F.huntDiff({ d: 2, hit: 100, L: 100 }), 2);     // 100 / 1105 < 0,2
assert.equal(F.huntDiff({ d: 2, hit: 300, L: 100 }), 3);
assert.equal(F.huntDiff({ d: 3, hit: 900, L: 100 }), 5);
assert.equal(F.huntDiff({ d: 3, hit: 100, L: 400 }), 3);
assert.equal(F.huntDiff({ d: 9, hit: NaN, L: 100 }), 4);     // d fora de 1..3 conta como 3; dano inválido = sem dano
// dificuldade dos bosses
assert.equal(F.bossDiff({ st: "solo", eff: 9000, md: 3000, ttk: 100, tmax: 300 }), 2);
assert.equal(F.bossDiff({ st: "solo", eff: 7000, md: 3000, ttk: 100, tmax: 300 }), 3);
assert.equal(F.bossDiff({ st: "solo", eff: 9000, md: 3000, ttk: 200, tmax: 300 }), 3);
assert.equal(F.bossDiff({ st: "solo", eff: null, md: null, ttk: 100, tmax: 300 }), 3);
assert.equal(F.bossDiff({ st: "team", eff: 1, md: 1, ttk: 1, tmax: 300 }), 4);
assert.equal(F.bossDiff({ st: "unknown", eff: 1, md: 1, ttk: 1, tmax: 300 }), 4);
assert.equal(F.bossDiff({ st: "later", eff: 1, md: 1, ttk: 1, tmax: 300 }), 5);
assert.equal(F.bossDiff({ st: "locked", eff: 1, md: 1, ttk: 1, tmax: 300 }), 5);
assert.equal(F.DIFF[3], "média"); assert.equal(F.DIFF.length, 6);
// preys
const M = [{ k: "a", n: "A", xp: 1000, cnt: 3, hit: 200 }, { k: "b", n: "B", xp: 2000, cnt: 1, hit: 900 },
           { k: "c", n: "C", xp: 500, cnt: 1, hit: null }, { k: "d", n: "D", xp: 100, cnt: 1, hit: 100 }];
assert.deepEqual(F.preyPicks(M, 100), [{ k: "a", n: "A", bonus: "xp" }, { k: "b", n: "B", bonus: "dmg" }, { k: "c", n: "C", bonus: "dmg" }]); // B já está: a 3.ª por XP
const M2 = [M[0], { k: "b", n: "B", xp: 2000, cnt: 1, hit: 100 }, { k: "c", n: "C", xp: 500, cnt: 1, hit: 900 }];
assert.deepEqual(F.preyPicks(M2, 100).map(x => x.k + ":" + x.bonus), ["a:xp", "b:dmg", "c:red"]);   // 900 / 1105 ≥ 0,35
assert.deepEqual(F.preyPicks([M[0]], 100), [{ k: "a", n: "A", bonus: "xp" }]);
assert.deepEqual(F.preyPicks([], 100), []);
assert.deepEqual(F.preyPicks([{ k: "z", n: "Z", xp: 0, cnt: 0, hit: null }], 100), []);              // sem XP não se recomenda
// loot
const L = [{ k: "a", n: "A", cnt: 2, loot: [{ n: "Gold Coin", pct: 100, v: 1 }, { n: "Gem", pct: 1, v: 10000 }] },
           { k: "b", n: "B", cnt: 1, loot: [{ n: "Gem", pct: 5, v: 10000 }, { n: "Lixo", pct: 50, v: 0 }] }];
assert.deepEqual(F.topLoot(L), [{ n: "Gem", pct: 5, v: 10000, from: "B" }, { n: "Gold Coin", pct: 100, v: 1, from: "A" }]);
assert.equal(F.topLoot(L, 1).length, 1); assert.deepEqual(F.topLoot([]), []);
assert.deepEqual(F.topLoot([{ k: "a", n: "A", cnt: 1 }]), []);                                        // sem lista de loot
// resistências
const R = F.resist({ physical: 100, fire: 110, ice: 96, earth: 81, energy: 99, holy: 102, death: 50, min: { fire: 105, earth: 0, death: -20 } });
assert.equal(R.length, 7); assert.equal(R[0].el, "fire"); assert.equal(R[0].pct, 110);
assert.equal(R.find(x => x.el === "earth").imm, true); assert.equal(R.find(x => x.el === "death").heal, true);
assert.equal(R.find(x => x.el === "fire").imm, false); assert.deepEqual(F.resist(null), []);
// viewport do mapa
assert.deepEqual(F.viewport([[100, 200, 7]], 0, 720, 420), { z: 7, x0: 55, y0: 174, s: 8, on: [0] });
const V = F.viewport([[100, 200, 7], [300, 200, 7], [100, 200, 8]], 0, 720, 420);
assert.equal(V.z, 7); assert.deepEqual(V.on, [0, 1]); assert.equal(V.s, 2);   // 200 + 24 de margem cabe a 2 px por sqm (360), não a 4 (180)
assert.equal(F.viewport([[100, 200, 7], [300, 200, 7], [100, 200, 8]], 2, 720, 420).z, 8);
assert.equal(F.viewport([[0, 0, 7], [5000, 0, 7]], 0, 720, 420).s, 1);         // não cabe: escala mínima, centrado no passo escolhido
assert.equal(F.viewport([[0, 0, 7], [5000, 0, 7]], 1, 720, 420).x0, 5000 - 360);
assert.equal(F.viewport([], 0, 720, 420), null);
console.log("fichas: ok");
```

- [ ] **Step 2: Corre e confirma que falha**

Run: `node _dev/fichas_test.mjs`
Expected: FAIL com `Cannot find module '../shared/fichas.js'`

- [ ] **Step 3: Implementa `shared/fichas.js`**

Copia o invólucro UMD do topo e do fim do `shared/bosses.js` (exporta para `module.exports` e para `window.GrimFicha`). Regras que a assinatura e os testes não fixam:
- `refHp(L) = 185 + 10 * (max(8, L) − 8)`.
- `huntDiff`: `base = [1, 3, 4][d − 1]`; `r = hit / refHp(L)`; `+1` se `r ≥ 0,5`; `−1` se `r < 0,2` e `d > 1`; limites 1 e 5; `hit` nulo ou não finito = sem ajuste.
- `bossDiff`: `solo` com `eff ≥ 3 × md` e `ttk ≤ tmax / 2` → 2; `solo` → 3; `team` e `unknown` → 4; o resto → 5.
- `preyPicks`: ordena por `xp × cnt` (desc), ignora quem tem `xp × cnt ≤ 0`. 1.ª = `xp`, 2.ª = `dmg`. 3.ª: a criatura ainda não escolhida com o maior `hit`, se `hit / refHp(L) ≥ 0,35` → `red`; senão a seguinte por XP → `dmg`.
- `topLoot`: pontuação `v × pct / 100 × cnt`; ignora `v ≤ 0`; um item por nome, com a criatura de maior pontuação em `from` (e o `pct` dela); ordena por pontuação desc; `max` = 8 por omissão.
- `resist`: os 7 elementos `physical, fire, ice, earth, energy, holy, death`, ordenados por `pct` desc; `imm = min[el] === 0`; `heal = min[el] < 0`.
- `viewport`: `z = pts[sel][2]`; `on` = índices com esse `z`; caixa dos pontos `on` com 12 sqm de margem de cada lado; `s` = o maior de 8, 4, 2, 1 em que a caixa cabe em `W × H`; se nem a 1 couber, `s = 1` e centra no ponto `sel`; senão centra na caixa; `x0 = round(cx − W / s / 2)`, `y0 = round(cy − H / s / 2)`.

- [ ] **Step 4: Corre e confirma que passa**

Run: `node _dev/fichas_test.mjs`
Expected: `fichas: ok`

- [ ] **Step 5: Commit**

```bash
git add shared/fichas.js _dev/fichas_test.mjs
git commit -m "Fichas: modelo de dificuldade, preys, loot, resistências e viewport do mapa"
```

---

### Task 2: Gerador `data/caminhos.json`

**Files:**
- Create: `_dev/build_caminhos.py`, `_dev/caminhos_manual.json`, `data/caminhos.json` (gerado)
- Test: `_dev/fichas_test.mjs` (acrescenta um bloco)

**Interfaces:**
- Consumes: o G (`load_G` do `_dev/gjson.py`: `places`, `hv`, `routes`, `hm`, `quests`), `data/hunt-access.json` (`h`, `places`), `data/boss-access.json` (`b`, `places`), `data/bosses.json` (`b[k].pos`, `pa`, `q`, `ql`, `qr`, `loc`), `data/npcs.json` (chaves em minúsculas, com `x`, `y`, `z`), `data/guias.json` (`q2s`: id do G.quests → slug; `n2s`: nome normalizado → slug; `g`), `_dev/caminhos_manual.json`.
- Produces: `data/caminhos.json` no formato da spec (`{v: 1, gen, h, b}`), com **todas** as chaves de `G.places` em `h` e todas as de `data/bosses.json` em `b`. Linha de comando:
  - `python3 -I _dev/build_caminhos.py` → grava;
  - `--check` → sai com 1 se o ficheiro em disco for diferente do que geraria, ou se a validação falhar;
  - `--report` → conta por estado (`ok`/`rev`/`part`/`none`), passos com ponto e passos com NPC, hunts e bosses em separado;
  - `--lote N [--tam 25] [--tipo h|b] [--estado none,part,rev,ok]` → lista o N-ésimo grupo de chaves **sem entrada no manual** (e, com `--estado`, só as que têm um desses estados), ordenadas pelo nível mais baixo da hunt em `G.hunts` (bosses: por `qr`, depois nome), para a Parte C.

- [ ] **Step 1: Acrescenta o teste que falha** ao fim do `_dev/fichas_test.mjs` (antes do `console.log` final)

```js
import { readFileSync } from "node:fs";
const J = p => JSON.parse(readFileSync(new URL("../" + p, import.meta.url), "utf8"));
const CAM = J("data/caminhos.json"), BOS = J("data/bosses.json"), NPC = J("data/npcs.json");
const G = JSON.parse(readFileSync(new URL("../index.html", import.meta.url), "utf8").match(/<script[^>]*id="G"[^>]*>([\s\S]*?)<\/script>/)[1]);
assert.equal(CAM.v, 1);
assert.deepEqual(Object.keys(CAM.h).sort(), Object.keys(G.places).sort());
assert.deepEqual(Object.keys(CAM.b).sort(), Object.keys(BOS.b).sort());
const okC = c => Array.isArray(c) && c.length === 3 && c[0] > 31000 && c[0] < 34500 && c[1] > 30900 && c[1] < 33100 && c[2] >= 0 && c[2] <= 15;
for (const [k, c] of [...Object.entries(CAM.h), ...Object.entries(CAM.b)]) {
  assert(["ok", "rev", "part", "none"].includes(c.st), k);
  assert(c.pos === null || okC(c.pos), k + " pos");
  assert(Array.isArray(c.pre) && Array.isArray(c.legs), k);
  for (const p of c.pre) assert(["quest", "level", "premium", "item", "text"].includes(p.k), k + " pre");
  for (const l of c.legs) { assert(l.t && l.steps.length, k + " troço vazio");
    for (const s of l.steps) { assert(typeof s.s === "string" && s.s.trim(), k + " passo vazio");
      assert(s.c === null || okC(s.c), k + " ponto"); assert(!/\(\d{5},\s*\d{5}/.test(s.s), k + " coordenada no texto: " + s.s);
      if (s.npc) { assert(NPC[s.npc.n.toLowerCase()], k + " NPC desconhecido: " + s.npc.n); assert(s.npc.say.length >= 1, k); } } }
  if (c.st === "none") assert(c.legs.length <= 1, k + " none com passos");
}
// casos conhecidos (dados de 10/11/2026)
const T = CAM.h.targuna_inf;
assert.equal(T.st, "rev"); assert.equal(T.from, "Thais");
assert(T.pre.some(p => p.k === "level" && p.n === 12));
const emi = T.legs.flatMap(l => l.steps).find(s => s.npc && s.npc.n === "Emiliana");
assert.deepEqual(emi.npc.say, ["hi", "mission", "yes"]);
const blue = T.legs.flatMap(l => l.steps).find(s => s.npc && s.npc.n === "Captain Bluebear");
assert.deepEqual(blue.npc, { n: "Captain Bluebear", say: ["hi", "targuna", "yes"], gp: 110 });
assert(T.legs.flatMap(l => l.steps).some(s => s.c && s.c.join() === "31962,31898,7"));
assert(CAM.h.werelions.pre.some(p => p.k === "quest" && /Lion's Rock/.test(p.n) && p.slug));
assert(CAM.h.werelions.pre.some(p => p.k === "premium"));
assert(CAM.h.upperspike.legs[0].t.includes("Upper Spike"));                 // ficha de local como 1.º troço
assert(Object.values(CAM.h).filter(c => c.st === "none").length <= 129);
assert(CAM.b.abyssador.refs.some(r => r.slug === "bigfoots-burden-quest" && r.sec === 8));
assert(Object.values(CAM.h).every(c => c.st !== "none" || c.legs.length === 1)); // a frase do p.acc fica como único passo
```

- [ ] **Step 2: Corre e confirma que falha**

Run: `node _dev/fichas_test.mjs`
Expected: FAIL com `ENOENT … data/caminhos.json`

- [ ] **Step 3: Implementa `_dev/build_caminhos.py`** e cria `_dev/caminhos_manual.json` com `{"h": {}, "b": {}}`

Regras de conversão (o resto fica ao teu critério):

*Hunts (`h[pid]`)*
- Entrada no manual → usa-a tal como está (só validada). Senão:
- `pos = G.hm[pid][:3]` (ou `null`); `pa = 1` se `G.hm[pid][3] == "a"`, senão 0.
- Com `G.hv[pid].st`: `st = "ok"` se `v == "ok"`, `"rev"` se `v == "fix"`, senão `"part"`. Um troço `"Caminho"` com um passo por linha do `st`. Se houver `t` (transporte), é o 1.º passo.
- Sem `hv` mas com `G.routes[pid]` (`[de, viagem, passos, requisito]`): `st = "part"`, `from = de`, passos = `viagem` (se houver) + `passos`; o `requisito` vai para `pre` como texto.
- Sem nenhum: `st = "none"`, um troço `"O que se sabe"` com um passo = `G.places[pid].acc`.
- Ficha de local (`hunt-access.json`: `h[pid]` → nomes → `places[nome]`): cada uma entra **antes** como troço `"Chegar a <title>"`, com os passos do `arrive` (texto tal como está; a marcação `{coord:}` fica no texto e o 1.º `{coord:}` do passo vai também para `c`). Os `requirements` vão para `pre` como texto. Com ficha de local e `st == "none"`, o estado sobe para `"part"` e o troço «O que se sabe» mantém-se no fim.
- `from`: a 1.ª cidade da lista `CITIES` do `index.html` (linha `const CITIES=[["Thais",…`) que apareça no 1.º passo; senão `G.places[pid].city`; senão `null`.

*Passos*
- Coordenadas: tira do texto `(x,y,z)`, `(cerca de x,y)`, `em x,y` e `(x, y)` (5 dígitos cada); com `z`, vai para `c`; sem `z`, usa o `z` de `pos` (ou 7). O texto fica sem a coordenada e sem parênteses vazios. Tira também `(z=…)` e as marcas `map_point|auto_route|canary` (como o `vRoute` faz hoje).
- NPC: padrão `<Nome>: hi, a, b[, c] [(N gp)]`, em que `<Nome>` é o maior sufixo do texto antes dos dois pontos que exista em `data/npcs.json` (ex.: «Barco do Captain Bluebear em Thais: hi, targuna, yes (110 gp)» → `Captain Bluebear`; se o nome não está logo antes dos dois pontos, procura qualquer nome de NPC nesse troço de texto, o mais comprido primeiro). `say` = as palavras separadas por vírgula; `gp` = o número antes de «gp», ou `null`. Um passo com `A: … → B: …` parte-se em dois passos. Nome que não exista nos NPCs → sem `npc` (o texto fica igual).
- Sem `c` e com `npc`: `c` = posição do NPC no `data/npcs.json`.

*Pré-requisitos (`pre`)*, a partir de `hv.rq`, `G.places[pid].q` e `prem`:
- `^(conta )?premium$` (sem maiúsculas) → `{k: "premium"}`; também quando `G.places[pid].prem` é verdadeiro.
- `^Nível (\d+)` → `{k: "level", n, rec: "recomendado" no texto}`.
- `^Quest: <nome>( \(nota\))?` → `{k: "quest", n, id, slug, sec: null, note}`: `id` = quest do `G.quests` com esse nome (sem «The » inicial nem « Quest» final, sem maiúsculas); `slug` = `guias.q2s[id]`, senão `guias.n2s` pelo nome normalizado como o `gKey` do `index.html`; sem correspondência, `null`.
- `G.places[pid].q` (id do G.quests; `"marapur"` = as do `G.marapur`) → quest, se ainda não estiver.
- `^(pá|corda|picareta|…)$` e textos com «×» ou número + nome de item → `{k: "item", n}`. Na dúvida, `text`.
- Descartar: `^sem `, `não necess`, `nenhum` (como o `vRoute` faz hoje).
- Sem repetidos (quest pelo `id` ou `slug`; os outros pelo texto).

*Bosses (`b[k]`)*
- `pos`/`pa` do `data/bosses.json`. `pre`: `q` → quest (com `slug` pelo nome) e `ql` → `level` (`rec: false`), `qr` → `level` (`rec: true`) se diferente.
- Troços: as fichas de local do `boss-access.json` (`b[k].places`), como nas hunts. `refs` = `b[k].guides` (`{slug, sec: section, t: title, quest}`).
- `st`: `"part"` com troços ou `refs`; senão `"none"` e, se houver `loc`, um troço «O que se sabe» com um passo `Fica em <loc, …>.`.

*Validação* (falha a geração e o `--check`): as mesmas regras do teste do Step 1, mais: `slug` tem de existir em `guias.g`; `sec` tem de ser um índice válido de `quests/data/quests/<slug>.json` → `sections`.

- [ ] **Step 4: Gera e confirma que passa**

Run: `python3 -I _dev/build_caminhos.py && python3 -I _dev/build_caminhos.py --check && python3 -I _dev/build_caminhos.py --report && node _dev/fichas_test.mjs`
Expected: `--check` sai com 0; o `--report` mostra 327 hunts e 316 bosses; `fichas: ok`

- [ ] **Step 5: Commit**

```bash
git add _dev/build_caminhos.py _dev/caminhos_manual.json data/caminhos.json _dev/fichas_test.mjs
git commit -m "Caminhos: data/caminhos.json com troços, passos, pontos, NPCs e pré-requisitos"
```

---

# Parte B — A ficha

### Task 3: Peças comuns no `index.html` (caminho, mapa do troço, pré-requisitos)

**Files:**
- Modify: `index.html` — junto de `function travelPlaceHTML(` (peças novas), `function openSheet(` (2.º parâmetro), `function initRoutes(` (enche as caixas), o `<style>` principal (CSS novo, perto de `.vroute`), e o sítio onde se carrega o `shared/bosses.js` (carrega também `shared/fichas.js?v=20261110a`)
- Test: `_dev/travel_access_test.mjs` (reescrito), `_dev/fichas_browser.cjs` (novo)

**Interfaces:**
- Consumes: `GrimFicha.viewport` (Task 1); `data/caminhos.json` (Task 2); do `index.html`: `dload`, `hasKey`, `esc`, `qmd`, `travelTextHTML`, `elink`, `npcSpr`, `floorImg`, `floorTxt`, `mapBtn`, `guiaHref`, `qDone`, `C`, `I18N.tr`.
- Produces:
  - `openSheet(html: string, cls?: string)` — `cls` é posta na `.sh` e tirada no `openSheet` seguinte sem `cls` e no `closeSheet`.
  - `camData(): Promise<{v, h, b}>` — carrega uma vez; falha → a próxima chamada tenta de novo.
  - `camHTML(cam: Caminho, id: string): string` — o bloco «Como lá chegar».
  - `camFill(box: Element): Promise<void>` — enche `<div data-cam="h:<pid>">` ou `data-cam="b:<chave>"`; também enche o irmão `[data-campre]` com os pré-requisitos.
  - `drawCam(cv: HTMLCanvasElement, pts: [x,y,z][], sel: number): Promise<void>`
  - `preHTML(pre: Pre[], c: personagem|null): string`

- [ ] **Step 1: Reescreve `_dev/travel_access_test.mjs`** (o `huntRoute` e o `hAccessFill` vão sair na Task 4; este teste passa a guardar o comportamento novo)

Mantém as asserções sobre o Questski (bloco `qctx`, do `travelCardsFor` em diante) e sobre o `hunt-access.json`. Troca a parte do `huntRoute`/`hAccessFill` por:

```js
const CAM = JSON.parse(read('data/caminhos.json'));
const cx = { esc: x => String(x), hasKey: (o, k) => Object.hasOwn(o, k), qmd: x => x, travelTextHTML: x => x,
  elink: (k, n) => `<npc:${n}>`, npcSpr: () => '', mapBtn: () => '<map>', guiaHref: s => 'quests/#/quest/' + s,
  qDone: (c, id) => !!c.done[id], C: () => null, dload: async () => CAM, GrimFicha: { DIFF: [] } };
vm.createContext(cx);
vm.runInContext(take(html, '/* fichas:caminho */', '/* fichas:caminho:fim */'), cx);
// caminho com passos, NPC e pontos
const h1 = cx.camHTML(CAM.h.targuna_inf, 'h:targuna_inf');
assert.match(h1, /revisto/); assert.match(h1, /<npc:Emiliana>/); assert.match(h1, /<kbd>hi<\/kbd>/); assert.match(h1, /110 gp/);
assert.match(h1, /data-cammap="h:targuna_inf:\d+"/); assert.match(h1, /data-camstep="h:targuna_inf:\d+:\d+"/);
// hunt por documentar: diz que falta e não desenha mapa de troço
const none = Object.entries(CAM.h).find(([, c]) => c.st === 'none');
const h2 = cx.camHTML(none[1], 'h:' + none[0]);
assert.match(h2, /por documentar/); assert(!h2.includes('data-cammap='));
// zona aproximada nunca é «entrada»
const aprox = Object.entries(CAM.h).find(([, c]) => c.pa === 1 && c.pos);
assert(!/entrada/i.test(cx.camHTML(aprox[1], 'h:' + aprox[0]).replace(/<ol[\s\S]*?<\/ol>/g, '')));
// pré-requisitos
const pre = [{ k: 'quest', n: 'Grimvale Quest', id: 'grim', slug: 'grimvale-quest', sec: 10, note: 'até entregares a ocarina' },
  { k: 'level', n: 250, rec: true }, { k: 'premium' }, { k: 'item', n: 'Pá' }, { k: 'text', s: 'Grupo recomendado' }];
const p0 = cx.preHTML(pre, null);
assert.match(p0, /quests\/#\/quest\/grimvale-quest\/guia\/sec-10/); assert.match(p0, /até entregares a ocarina/); assert(!/por fazer|feita/.test(p0));
const p1 = cx.preHTML(pre, { level: 100, done: {} }); assert.match(p1, /por fazer/); assert.match(p1, /nível 250/i);
assert.match(cx.preHTML(pre, { level: 300, done: { grim: true } }), /feita/);
assert.match(cx.preHTML([], null), /Sem pré-requisitos/);
// enchimento e falha de rede
const box = { dataset: { cam: 'h:targuna_inf' }, isConnected: true, parentElement: { querySelector: () => null } };
await cx.camFill(box); assert.match(box.innerHTML, /Emiliana/);
cx.dload = async () => { throw new Error('offline'); }; vm.runInContext('CAMP=null;', cx);
const bad = { dataset: { cam: 'h:targuna_inf' }, isConnected: true, parentElement: { querySelector: () => null } };
await cx.camFill(bad); assert.match(bad.innerHTML, /Tentar de novo/); assert(!bad.dataset.loaded);
```

- [ ] **Step 2: Corre e confirma que falha**

Run: `node _dev/travel_access_test.mjs`
Expected: FAIL com `/* fichas:caminho */` (marca não encontrada)

- [ ] **Step 3: Implementa as peças no `index.html`**, entre os comentários `/* fichas:caminho */` e `/* fichas:caminho:fim */` (as funções e as variáveis desta tarefa ficam entre as duas marcas, para o teste as extrair; os `addEventListener` ficam **depois** da marca do fim, porque o teste corre sem `document`)

- `let CAMP = null;` e `camData()` como o `hAccessData` de hoje (valida `v === 1`, `h`, `b`; limpa `CAMP` na falha).
- `camHTML(cam, id)`:
  - cabeçalho: `<b>Como lá chegar</b>` + etiqueta do estado: `ok` → «confirmado» (`tag ok`), `rev` → «revisto» (`tag acc`), `part` → «falta o último troço» (`tag`), `none` → «por documentar» (`tag warn`); com `from`, «A partir de <cidade>».
  - por troço: `<h5>` com o título; se algum passo tem `c`, um `<details class="cam-map" data-cammap="<id>:<nº do troço>"><summary>Ver no mapa</summary><canvas class="cam-cv" width="720" height="420" …></canvas><p class="tiny muted">…andar…</p></details>` **antes** da lista;
  - `<ol class="cam-st">`: cada passo é o texto (`travelTextHTML`), e, com `c`, um botão `<button class="cam-pin" data-camstep="<id>:<troço>:<passo>" aria-label="Ver o passo N no mapa">N</button>` (N = número do passo dentro do troço); com `npc`, um bloco `.cam-npc`: `npcSpr(n, true)`, «Fala com » + `elink("npc", n)`, as palavras em `<kbd>` separadas por vírgula, e « · N gp» quando há preço;
  - `refs`: `<h5>Nos guias das quests</h5>` + lista de ligações `guiaHref(slug) + "/guia/sec-" + sec` com o título e a quest;
  - com `pa === 1` e `pos`: «O ponto no mapa é a zona aproximada.» (nunca a palavra «entrada»);
  - `none`: depois do passo único, «Ainda não temos este caminho passo a passo.».
- `drawCam(cv, pts, sel)`: `GrimFicha.viewport(pts, sel, cv.width, cv.height)`; fundo preto; `floorImg(z)` desenhado como no `drawPos` (origem do mapa: x − 31744, y − 30976); um pino numerado por ponto de `on` (círculo de 11 px com o número do passo; o escolhido maior e a cor de destaque); etiqueta do andar com `I18N.tr(floorTxt(z))` como no `drawPos`.
- Eventos (delegados no `document`): `toggle` em `.cam-map` aberta → `drawCam` com o 1.º passo com ponto; clique em `[data-camstep]` → abre a `.cam-map` do troço, `drawCam` com esse passo, `scrollIntoView({block: "nearest"})`. Os pontos de cada troço ficam num mapa `CAMPTS[id + ":" + troço] = [{c, n}]` preenchido pelo `camHTML`.
- `preHTML(pre, c)`: lista `<ul class="fx-pre">`; quest: ligação ao guia (com `sec` → `/guia/sec-<sec>`; sem `slug` → só o nome), a `note` a seguir, e, com `c` e `id`, «✓ feita» (`tag ok`) ou «por fazer» (`tag warn`); nível: «Nível N» (+ « recomendado»), com `c` → `tag ok`/`tag warn` conforme `c.level ≥ n`; premium: «Conta premium»; item: `qmd("{item:" + n + "}")`; texto: `qmd`. Lista vazia → `<p class="small muted">Sem pré-requisitos.</p>`.
- `camFill(box)`: como o `hAccessFill` de hoje (marca `dataset.loaded`, verifica `isConnected`, na falha apaga a marca e mostra «Não consegui carregar o caminho.» + `<button class="btn small ghost" data-camretry>Tentar de novo</button>`); enche também `box.parentElement.querySelector("[data-campre]")` com `preHTML(cam.pre, C())` se existir. Chave sem entrada → `camHTML({st: "none", pos: null, pa: 0, pre: [], legs: []}, id)`.
- `initRoutes(root)`: acrescenta `root.querySelectorAll("[data-cam]").forEach(camFill)`.
- `openSheet(html, cls)`: guarda a classe em `sh.querySelector(".sh").dataset.cls` para a tirar depois.
- CSS (tema atual, sem cores novas: usa as variáveis `--surface-2`, `--sunk`, `--accent`, `--gold`): `.sh.sh-ficha{width:min(980px,100%)}`; `.cam-st` com números; `.cam-pin` 44 × 44 px de área de toque (o círculo visível pode ter 28 px); `.cam-npc` em linha com o sprite; `.cam-cv{width:100%;height:auto;image-rendering:pixelated;border-radius:8px}`; `kbd` legível (≥ 12 px).

- [ ] **Step 4: Corre e confirma que passa**

Run: `node _dev/travel_access_test.mjs && python3 -I _dev/gjson.py . --check`, mais o `node --check` do JS extraído (ver Global Constraints)
Expected: sem erros

- [ ] **Step 5: Escreve `_dev/fichas_browser.cjs`** (Playwright; `require('playwright')`, `chromium.launch()` sem opções)

Uso: `node _dev/fichas_browser.cjs [--url http://127.0.0.1:8765/]` com `python3 -m http.server 8765 --bind 127.0.0.1` a correr na raiz do repositório. O script:
- semeia o `localStorage` com as personagens de teste do `_dev/smoke.mjs` (copia o objeto `STv` de lá) e `grimorio-lang`;
- para cada língua de `pt-PT, en, de` e largura de `1440, 390`: abre `#hunts`, espera pelos cartões, e devolve por página `{errs, hscroll, small, tiny}` como o `pubtest2.cjs` descrito no `_dev/GRIMORIO.md` (erros de consola e `pageerror`; `scrollWidth > innerWidth + 1`; elementos visíveis com letra < 12 px; botões/ligações visíveis com menos de 44 px de altura dentro de `#sheet`);
- sai com código 1 se alguma lista não estiver vazia. Nesta tarefa só abre a página; as tarefas 4 e 5 acrescentam os passos de abrir fichas.

Run: `node _dev/fichas_browser.cjs`
Expected: `ok` em 6 combinações

- [ ] **Step 6: Commit**

```bash
git add index.html shared/fichas.js _dev/travel_access_test.mjs _dev/fichas_browser.cjs
git commit -m "Fichas: caminho em troços com mapa por troço, NPCs e pré-requisitos"
```

---

### Task 4: Ficha da hunt

**Files:**
- Modify: `index.html` — `function huntSheet(h){` (reescrita), `function huntCard(` (linha dos números), o ramo `t==="h"` do clique em `[data-gs]` (usa `placeSheet`), o clique em `[data-hunt]` (`openSheet(huntSheet(h), "sh-ficha")`), CSS `.fx-*`
- Test: `_dev/fichas_browser.cjs` (acrescenta), `_dev/fichas_test.mjs` (sem mudanças)

**Interfaces:**
- Consumes: `camFill`, `preHTML`, `openSheet(html, cls)` (Task 3); `GrimFicha.huntDiff`, `preyPicks`, `topLoot`, `resist`, `DIFF`, `PREY` (Task 1); do `index.html`: `huntMap(h)`, `mapBtn`, `crSpr`, `mlink`, `ilink`, `ltSpr`, `chip`, `elName`, `gp`, `fmt`, `nf`, `priceOf`, `charmPicks`, `hCharmsHTML`, `hcmpBtn`, `crdLoad`, `CRDV`, `hcmpHit(pid)`, `G.pm`, `G.mon`, `G.places`, `G.hm`, `estTxt`.
- Produces:
  - `fichaHTML(m: {eyebrow: string, title: string, head?: string, map: string, cam: string, stats: {v: string, l: string}[], pre: string, mons: string, loot: string, tips: string, foot: string}): string`
  - `huntSheet(h): string` (mesma assinatura de hoje)
  - `placeSheet(pid: string): string` (hunt sem linha para a vocação: mesma ficha, sem XP/h)
  - `diffHTML(n: 1..5, extra?: string): string` — 5 marcas + «N/5 · <nome>»

- [ ] **Step 1: Acrescenta o teste que falha** ao `_dev/fichas_browser.cjs`

Em cada combinação, depois de `#hunts` carregar: clica no 1.º `[data-hunt]`, espera por `#sheet.on [data-cam][data-loaded]`, e verifica dentro de `#sheetBody`:
- existe `.fx-top` com 2 filhos (`.fx-map` e `.fx-cam`); a 1440 px estão lado a lado (`getBoundingClientRect().top` igual, ±4 px); a 390 px o mapa está por cima;
- `.fx-stats` tem exatamente 5 itens, por esta ordem (os rótulos são traduzidos pelo site; compara pela ordem, não pelo texto): XP/h, lucro/h, nível, resistências, dificuldade;
- numa hunt com `lo` negativo no `G.hunts` da vocação ativa (procura uma nos dados; se não houver, salta), o lucro tem a classe `warnt`;
- existem, por esta ordem no DOM: `.fx-top`, `.fx-stats`, `[data-campre]`, `.fx-mons`, `.fx-loot`, `.fx-tips`;
- **não** existem: `.tabs`, `.whatb`, `[data-hwheel]`, `.hsets`, `[data-kstat]`, `[data-lootp]`;
- `.fx-tips` tem um bloco de charms e um de preys; cada prey tem o nome de uma criatura e um dos três bónus;
- preços do loot: o teste intercepta `**/api/market.php*` (`page.route`) e responde com um JSON fixo (`{world, updated, items}` com o id do Market do 1.º item do loot e um `month_average_sell` alto, `month_sold` 50); a linha desse item passa a dizer «Market» e o valor do JSON, e a nota diz o mundo. Numa 2.ª corrida o route responde 503: a ficha mostra os preços do NPC e «o Market não respondeu». Sem `world` na personagem: a frase de escolher o mundo;
- clicar num `.cam-pin` abre a `.cam-map` e o `<canvas>` deixa de estar todo preto (`getImageData` com algum píxel ≠ 0 fora do pino);
- fecha a ficha; pesquisa geral por uma hunt que a vocação ativa não tem e confirma que a ficha abre com a mesma estrutura (sem o número de XP/h: «—»).
Repete com a 1.ª hunt cujo `data-pid` tenha `st == "none"` no `data/caminhos.json`: a ficha abre, mostra «por documentar» (pt-PT) e o mapa da zona.

Run: `node _dev/fichas_browser.cjs`
Expected: FAIL (`.fx-top` não existe)

- [ ] **Step 2: Implementa `fichaHTML`, `diffHTML`, `huntSheet` e `placeSheet`**

Estrutura fixa do `fichaHTML` (classes entre parênteses):
1. cabeçalho (`.sh-h`): `eyebrow`, `<h3>` com o título, `head` (botão de comparar);
2. `.fx-top`: `.fx-map` (`m.map`) e `.fx-cam` (`m.cam`); grelha de 2 colunas a partir de 760 px (`minmax(0,340px) minmax(0,1fr)`), 1 coluna abaixo;
3. `.fx-stats`: os 5 números, numa linha (em 2 colunas abaixo de 480 px, com a dificuldade a ocupar a linha toda);
4. `<section><h4>Pré-requisitos</h4>` + `m.pre`;
5. `<section class="fx-mons"><h4>Criaturas</h4>` + `m.mons`;
6. `<section class="fx-loot"><h4>Loot principal</h4>` + `m.loot`;
7. `<section class="fx-tips"><h4>Charms e preys</h4>` + `m.tips` (omitida se vazia);
8. `m.foot` (notas pequenas).

`huntSheet(h)`:
- `map`: `huntMap(h)` (o botão com a miniatura que já existe) + `mapBtn(…, "Abrir o mapa")` + o botão «Ver spawns no mapa» (`data-hspawn`) que já existe; com `G.hm[pid][3] === "a"`, a legenda «zona aproximada».
- `cam`: `<div data-cam="h:<pid>"><p class="tkload">A carregar o caminho…</p></div>`; `pre`: `<div data-campre></div>` (o `camFill` enche-o).
- `stats`: (1) `fmt(h.xp)` + «≈» quando `h.est`, ou «—», rótulo «XP/h»; (2) `fmt(h.lo)` + «≈» quando `h.est`, com a classe `warnt` quando `h.lo < 0`, ou «—», rótulo «lucro/h»; quando `h.xp == null` e a hunt tem as notas da TibiaWiki (`p.xs`/`p.ls`), os dois primeiros mostram as estrelas (`stars(p.xs)`, `stars(p.ls)`) com «(TibiaWiki)» no rótulo, como a ficha de hoje; (3) `h.l + "+"`, «nível recomendado»; (4) resistências: os 2 elementos de maior `pct` e o de menor do `GrimFicha.resist(p.eff)`, como chips (`chip(el)` + `pct %`), rótulo «resistências», e um `<details>` «Ver os 7 elementos» com a lista completa (imune / cura assinalados); (5) `diffHTML(GrimFicha.huntDiff({d: p.d, hit: hcmpHit(pid), L: h.l}))`, rótulo «dificuldade». O dano vem do `data/crdmg.json`: se `CRDV` ainda não carregou, mostra a base e chama `crdLoad().then(…)` para atualizar só esse número (como o `hcmpSheet` faz).
- `mons`: `G.pm[pid].h` com criatura conhecida: sprite (`crSpr`, 44 px), nome (`mlink`), vida e XP (`G.mon[k][1]`, `[2]`), «× n» quando n > 1. Sem dados: «Sem dados de criaturas para esta zona.».
- `loot`: `<div class="fx-loot-b" data-fxloot="<pid>">` desenhado já com os preços do NPC (o valor que vem no `G.mon[k][6]`, `[ix, nome, %, valor]`) e **refeito** quando os preços do Market chegam: `Promise.all([ITV ? null : dsafe("items"), mktLoad(c.world)])` (guarda o `items.json` em `ITV` como o `renderBosses` faz). Com os dois: valor = `priceOf(nome, c.world).v` quando for maior que 0, senão o do NPC; `GrimFicha.topLoot(…)` volta a ordenar com estes valores. Cada linha: `ltSpr`, `ilink(nome)`, probabilidade (mesma formatação do `monCard`), `gp(valor)`, «Market» ou «NPC» (de onde veio o valor), «de <criatura>». Por baixo, numa linha pequena: com Market, «Preços do Market de <mundo>, scan de <dia e hora de `MKV[w].updated`>»; sem mundo, «Escolhe o mundo da personagem para ver os preços do Market.»; Market falhou (`mktLoad` deu `null`), «Preços do NPC: o Market não respondeu.». Vazio: «Sem dados de loot.». Não há atualização própria a fazer: o `api/market.php` já vai ao TibiaMarket (cache de 6 h) e o browser guarda 2 h.
- `tips`: charms = `hCharmsHTML(c, p, h)` (só os charms; nada da Wheel nem das gemas); preys = `GrimFicha.preyPicks(…)` com `xp`/`cnt` do `G.pm`/`G.mon` e `hit` = `CRDV[k].m`; cada prey: sprite, nome, `GrimFicha.PREY[bonus]`; nota: «O 3.º slot de prey compra-se na Store.» quando há 3.
- `foot`: `estTxt(h)` e, com `p.note`, a nota da hunt.
- `head`: `hcmpBtn(h)`.

`placeSheet(pid)`: a mesma ficha com `h` mínimo (`{p: G.places[pid], r: {c: pid, place: G.places[pid].n}, l: nível mais baixo dessa hunt em G.hunts, xp: null, …}`), sem charms nem botão de comparar.

Cartão (`huntCard`): a linha `.hc-n` mantém o XP/h, o lucro e o nível, e ganha no fim « · dificuldade N/5»; o resto do cartão fica igual.

Sai da ficha (apaga as chamadas; apaga a função se o `grep` mostrar que não tem mais nenhum uso): `haHTML`, `[data-kstat]`/`initKstat` na ficha, a frase da composição por tipo, os `pills` de compatibilidade, o bloco «Setup» (`setupHTML`, `elemHTML` dentro dele), `hsetsHTML`, `hwheelHTML`, `tabsUI` na ficha, `[data-lootp]` na ficha, `questsTab`/`questsForHunt` na ficha, as variantes, `huntRoute`, `vRoute`, `routeHTML`, `hAccessData`, `hAccessFill`, o clique `[data-hretry]`.

- [ ] **Step 3: Corre tudo**

Run: `node _dev/fichas_browser.cjs && node _dev/travel_access_test.mjs && node _dev/fichas_test.mjs && python3 -I _dev/gjson.py . --check`, mais o `node --check` do JS extraído
Expected: tudo sem erros; o browser diz `ok` nas 6 combinações

- [ ] **Step 4: Vê com os teus olhos** — tira capturas da ficha a 1440 e a 390 px (3 hunts: uma com caminho `ok`, uma `part` com ficha de local, uma `none`) e confirma: o mapa está ao lado do caminho; nada cortado; os 5 números leem-se à primeira.

- [ ] **Step 5: Commit**

```bash
git add index.html _dev/fichas_browser.cjs
git commit -m "Hunts: ficha objetiva (mapa e caminho, 5 números, pré-requisitos, criaturas, loot, charms e preys)"
```

---

### Task 5: Ficha do boss

**Files:**
- Modify: `index.html` — `function bsRow(` (linha simples que abre a ficha), função nova `bossSheet(k)`, o `toggle` de `.bs-d` (sai), `bsMapHTML`/`bsAccessHTML`/`bsAccessFill`/`bsAccessData` (saem)
- Test: `_dev/fichas_browser.cjs` (acrescenta), `_dev/boss_access_test.mjs` (atualiza ou apaga as asserções sobre o `bsAccessHTML`)

**Interfaces:**
- Consumes: `fichaHTML`, `diffHTML`, `camFill`, `openSheet(html, "sh-ficha")` (Tasks 3 e 4); `GrimFicha.bossDiff`, `resist`; do `index.html`: `BSD`, `GrimBoss.judge` (o resultado `r` já calculado no `renderBosses`), `GrimBoss.CLS`, `GrimBoss.cdText`, `lootPerKill`, `bsT`, `crSpr`, `monHref`, `chip`.
- Produces: `bossSheet(k: string): string`; cada linha da lista tem `data-boss="<chave>"` num botão «Ver ficha» (e o nome do boss abre a mesma ficha).

- [ ] **Step 1: Acrescenta o teste que falha** ao `_dev/fichas_browser.cjs`

Em cada combinação: abre `#bosses`, espera pelas linhas `.bs-r`, clica no 1.º `[data-boss]`, espera por `#sheet.on [data-cam][data-loaded]` e verifica:
- a mesma ordem de blocos da hunt (`.fx-top`, `.fx-stats`, `[data-campre]`, `.fx-mons`, `.fx-loot`), **sem** `.fx-tips`;
- `.fx-stats` com 5 itens: XP por kill, valor por kill, nível recomendado (sozinho / em equipa), resistências, dificuldade;
- não há `<details class="bs-d">` na página;
- a linha da lista continua a ter o botão do Bosstiary (`[data-bstier]`) e este continua a rodar o estágio.
Corre também `node _dev/bosses_test.mjs` (o motor não muda).

Run: `node _dev/fichas_browser.cjs`
Expected: FAIL (`[data-boss]` não existe)

- [ ] **Step 2: Implementa `bossSheet(k)` e simplifica o `bsRow`**

`bossSheet(k)` (guarda os resultados do `renderBosses` num mapa `BSROW[k] = {b, r, lo}` para a ficha os ler):
- `eyebrow`: classe do Bosstiary (`GrimBoss.CLS[b.c]`) e o cooldown (`GrimBoss.cdText(b.cd)`); `title`: nome.
- `map`: com `b.pos`, o `<canvas class="qpos" data-qpos="x,y,z">` de hoje (desenhado ao abrir, com `drawPos`) + `mapBtn(…, "Abrir o mapa")`; com `b.pa`, «zona aproximada»; sem `pos`, «Posição por confirmar.».
- `cam`: `<div data-cam="b:<k>">…</div>`; `pre`: `<div data-campre></div>`.
- `stats`: (1) `nf(b.xp)` ou «—», «XP por kill»; (2) `≈ gp(lo.v)` ou «sem preço» (`lo.nodata`), «valor por kill»; (3) nível: `r.soloL` («sozinho») e `r.teamL` («em equipa»), o que houver; senão `b.qr`; rótulo «nível recomendado»; (4) resistências do `BSD.cr[k].el` (aqui o valor é a % de dano que leva: usa-o direto no formato do `GrimFicha.resist`, 100 = normal, 0 = imune); (5) `diffHTML(GrimFicha.bossDiff({st: r.st, eff: r.eff, md: b.md, ttk: r.ttk, tmax: limite da classe}), "para o teu nível")` (limites: Bane 150 s, Archfoe 300 s, Nemesis 600 s, como no `_dev/BOSSES.md`).
- `mons`: o próprio boss: sprite, vida (`r.hp` ou «desconhecida»), golpe máximo (`b.md`), o dano que faz por elemento (`b.dm`), e uma linha com o tipo de aparição: «Sala com alavanca» (`b.lv`), «Aparece em raids: não se marca» (`b.sp === "r"`), «Aparece no mundo, ao acaso» (`b.sp === "g"`).
- `loot`: `lo.top` (até 8) no mesmo formato da hunt; sem dados: «Sem dados de loot.».
- `tips`: vazio (bosses não levam charm nem prey; não mostrar o bloco).

`bsRow`: fica o sprite, o nome (botão que abre a ficha), a etiqueta do estado (sozinho/equipa/…), o valor por kill, o sítio, o botão «Ver ficha» (`data-boss`) e o botão do Bosstiary. Sai o `<details class="bs-d">` com «Porquê e como».

- [ ] **Step 3: Corre tudo**

Run: `node _dev/fichas_browser.cjs && node _dev/bosses_test.mjs && node _dev/boss_access_test.mjs && node _dev/travel_access_test.mjs && python3 -I _dev/gjson.py . --check`, mais o `node --check`
Expected: sem erros

- [ ] **Step 4: Vê com os teus olhos** — capturas a 1440 e 390 px de 3 bosses: um de alavanca com guia (`refs`), um de raid, um sem posição.

- [ ] **Step 5: Commit**

```bash
git add index.html _dev/fichas_browser.cjs _dev/boss_access_test.mjs
git commit -m "Bosses: a mesma ficha objetiva das hunts"
```

---

### Task 6: Traduções, versões e documentação

**Files:**
- Modify: `i18n/src/ui-extra.json`, `i18n/src/ui.json`, `i18n/src/ui/*.json`, `i18n/ui.*.js` (gerados), `index.html` (`?v=`), `shared/i18n.js` (`DV`), `_dev/GRIMORIO.md`, `README.md`
- Create: `_dev/CAMINHOS.md`

**Interfaces:**
- Consumes: todo o texto novo das Tasks 3–5.
- Produces: o site em 8 línguas sem texto novo por traduzir; documentação para a Parte C.

- [ ] **Step 1: Junta as chaves manuais** — texto que o tradutor não apanha sozinho (texto montado em JS com partes variáveis, `aria-label`, texto no `<canvas>`): acrescenta a `i18n/src/ui-extra.json` no formato `{"c": "<contexto>", "k": "<texto pt-PT>"}`. No mínimo: os 5 nomes da dificuldade, os 3 bónus de prey, os 4 estados do caminho, «Como lá chegar», «Ver no mapa», «Fala com », «zona aproximada», «por fazer», «feita», «Sem pré-requisitos.», «Tentar de novo», os rótulos dos 5 números (hunt e boss).

- [ ] **Step 2: Extrai, traduz e constrói**

Run: `python3 -I _dev/i18n.py extract`, depois para cada língua (en, pt-BR, es, de, pl, sv, nl) um ficheiro `{"<texto pt-PT>": "<tradução>"}` com **todas** as chaves novas e `python3 -I _dev/i18n.py merge ui <língua> <ficheiro>`, e por fim `python3 -I _dev/i18n.py build`.
Expected: o `extract` não lista chaves novas por traduzir depois do `merge`. Termos do jogo ficam em inglês (Bonus XP → «XP Bonus», prey, charm, nomes de NPCs, criaturas, itens e quests).

- [ ] **Step 3: Sobe as versões** — `?v=` do `shared/fichas.js`, do `shared/i18n.js` (`DV`) e dos `i18n/ui.*.js` em todos os sítios (`grep -rn "fichas.js\|i18n.js?v" index.html quests/index.html privacidade.html`).

- [ ] **Step 4: Testa nas 3 línguas**

Run: `node _dev/fichas_browser.cjs`
Expected: `ok` nas 6 combinações; em `en` e `de`, a ficha não tem nenhuma das frases pt-PT do Step 1 (o script compara o texto de `#sheetBody` com a lista do `ui-extra.json` acrescentada nesta tarefa).

- [ ] **Step 5: Documenta**

- `_dev/GRIMORIO.md`: secção nova «Fichas de hunts e bosses (r35)» com: a estrutura da ficha, as funções (`fichaHTML`, `huntSheet`, `placeSheet`, `bossSheet`, `camHTML`, `camFill`, `drawCam`, `preHTML`, `diffHTML`), o `shared/fichas.js`, o `data/caminhos.json` e como se regenera, os testes. Corrige a secção «Acessos de hunts e quests (09/11/2026)»: o site já não lê o `hunt-access.json` nem o `boss-access.json` (são entrada do `build_caminhos.py`). Tira as referências às funções apagadas.
- `_dev/CAMINHOS.md`: o guia da Parte C (formato do `_dev/caminhos_manual.json` com um exemplo completo; a marcação do texto; fontes aceites; as regras «nunca inventar» e «ponto aproximado»; os comandos `--lote`, `--report`, `--check`; a lista de verificação da Task 7).
- `README.md`: `_dev/build_caminhos.py`, `_dev/fichas_test.mjs` e `_dev/fichas_browser.cjs` na lista de ferramentas.

- [ ] **Step 6: Commit e PR**

```bash
git add -A i18n shared/i18n.js index.html quests/index.html privacidade.html _dev/GRIMORIO.md _dev/CAMINHOS.md README.md
git commit -m "Fichas: traduções em 7 línguas, versões e documentação"
git push -u origin fichas-hunts-bosses
```

Abre o PR «Fichas objetivas de hunts e bosses» (pela API REST: `gh api repos/Lavovskii/grimorio/pulls`), com as capturas antes/depois e a saída dos testes. **Não faças merge sem o dono dizer.**

---

# Parte C — Completar os caminhos (conteúdo, por lotes)

Sem código novo: cada lote acrescenta entradas ao `_dev/caminhos_manual.json`, regenera o `data/caminhos.json` e abre um PR. Pode começar logo depois da Task 2 e correr ao lado da Parte B.

### Task 7: Primeiro lote, que serve de modelo

**Files:**
- Modify: `_dev/caminhos_manual.json`, `data/caminhos.json` (gerado)
- Test: `python3 -I _dev/build_caminhos.py --check`, `node _dev/fichas_test.mjs`

**Interfaces:**
- Consumes: o formato `Caminho` da spec; `python3 -I _dev/build_caminhos.py --lote 1 --tam 10 --tipo h`.
- Produces: 10 hunts com caminho completo, e a lista de verificação que os lotes seguintes repetem.

- [ ] **Step 1: Tira a lista** — `python3 -I _dev/build_caminhos.py --lote 1 --tam 10 --tipo h --estado none` (as 10 hunts por documentar de nível mais baixo). Acrescenta-lhes, à mão, as duas hunts de Oskayaat (`weretigers` e `werecrocs`), porque foi o exemplo do dono: o acesso abre na Grimvale Quest (`slug` `grimvale-quest`), `sec` 10 («11. Paradise Lost: chegar a Oskayaat»), com a `note` «até entregares a ocarina».

- [ ] **Step 2: Para cada hunt, junta as fontes**, por esta ordem de confiança:
  1. o que o site já tem: `G.hv[pid]`, `G.routes[pid]`, `G.places[pid].acc`, a ficha de local do `hunt-access.json`, `_dev/hv_notas.json`;
  2. o guia do Questski da quest de acesso (`quests/data/quests/<slug>.json`: secções e passos, já em PT-PT, com NPCs e diálogos);
  3. a página do sítio na TibiaWiki (`https://tibia.fandom.com/wiki/<Nome>`: «Location», «Notes», `{{Mapper Coords}}`) e a página de cada NPC citado;
  4. posições: `data/npcs.json` (NPCs), `data/spawns.json` (criaturas), o mapa do site (`openMap`) para confirmar o andar.
  Fonte externa que contradiga o site: fica o que a TibiaWiki diz hoje, e anota-se em `_dev/hv_notas.json`.

- [ ] **Step 3: Escreve a entrada** em `_dev/caminhos_manual.json` → `h[pid]`, cumprindo:
  - começa numa cidade com depot (`from`); o 1.º troço leva à zona (barco, tapete, teleporte, a pé), o último à entrada da hunt;
  - um passo = uma ação (andar até X, falar com Y, usar Z, descer/subir); frases curtas em PT-PT; direções pelos pontos cardeais;
  - todo o passo de falar com um NPC tem `npc` com `say` (as palavras exatas, em inglês, como no jogo) e `gp` quando se paga;
  - todo o passo que muda de sítio de forma não óbvia (escada, buraco, teleporte, porta, alavanca) tem `c`;
  - pelo menos 1 ponto por troço; o último passo com ponto é a entrada ou o 1.º andar da hunt;
  - `pre`: quests com `slug` e, quando o acesso abre a meio, `sec` (índice da secção do guia) e `note` («até …»); nível mínimo e recomendado; premium; itens (pá, corda, chave, itens de quest);
  - `st`: `ok` só se a fonte 3 confirma **todos** os passos; senão `rev`; se faltar o último troço, `part` (e os troços que se sabem);
  - o que não se conseguir confirmar **não entra**: mais vale `part` do que um passo inventado.

- [ ] **Step 4: Valida**

Run: `python3 -I _dev/build_caminhos.py && python3 -I _dev/build_caminhos.py --check && node _dev/fichas_test.mjs && python3 -I _dev/build_caminhos.py --report`
Expected: sem erros; no `--report`, as hunts `none` desceram e os passos com ponto e com NPC subiram.

- [ ] **Step 5: Confirma no mapa** — abre cada uma das hunts no site (ou com o `_dev/fichas_browser.cjs` em modo captura) e olha para o mapa de cada troço: os pinos caem em chão caminhável, na ordem dos passos, no andar certo. Um pino no preto ou dentro de uma parede é um erro de coordenada: corrige.

- [ ] **Step 6: Escreve a lista de verificação** em `_dev/CAMINHOS.md` (secção «Antes de fechar um lote») com os Steps 2 a 5 resumidos, e o exemplo de uma das entradas deste lote.

- [ ] **Step 7: Commit e PR**

```bash
git add _dev/caminhos_manual.json data/caminhos.json _dev/CAMINHOS.md _dev/hv_notas.json
git commit -m "Caminhos: primeiro lote escrito à mão (10 hunts e Oskayaat)"
```

### Tasks 8 a 17: os lotes seguintes

Cada lote é uma tarefa igual à Task 7 (Steps 1 a 5 e 7), com um PR próprio. Pára e pergunta ao dono se um lote tiver mais de 5 hunts que só dão `part`.

| Tarefa | Comando para a lista | O quê | Feito quando |
|---|---|---|---|
| 8 a 11 | `--lote 1 --tam 25 --tipo h --estado none` | hunts por documentar (cerca de 100 no início), 25 por tarefa, das de nível mais baixo para cima | a lista vem vazia: 0 hunts `none` |
| 12 | `--lote 1 --tam 25 --tipo h --estado part` (repetir até acabar) | hunts que só chegam à zona (cerca de 45): falta o último troço | 0 hunts `part` sem entrada manual |
| 13 a 16 | `--lote 1 --tam 45 --tipo h --estado rev,ok` | hunts com passos do `G.hv` (cerca de 180): passar a manual, com pontos e NPCs | a lista vem vazia: todas as hunts têm entrada manual e ≥ 1 ponto por troço |
| 17 | `--lote 1 --tam 40 --tipo b` (repetir até acabar) | bosses: primeiro os de alavanca e de sala (`sp == "t"` no `data/bosses.json`), depois os outros | 0 bosses `none` com `sp == "t"` |

(O `--lote 1` repete-se porque a lista só tem chaves **sem** entrada manual: depois de um lote entrar, o lote 1 passa a ser o seguinte. Os números «cerca de» confirmam-se com o `--report` depois da Task 2.)

Nos lotes 13 a 16, o texto do `G.hv` é o ponto de partida: mantém o que está confirmado (`v == "ok"`), acrescenta os pontos e os NPCs, e parte os passos compridos em ações.

---

## Self-review (feito pelo autor do plano)

- **Cobertura da spec:** objetivo 1 → Tasks 3–5; 2 → Task 2; 3 e 4 → Task 3; 5 → Tasks 2 e 3; 6 e 7 → Tasks 1 e 4; 8 → Tasks 7–17; «o que sai da ficha» → Tasks 4 e 5; traduções e documentação → Task 6.
- **Nomes iguais em todo o plano:** `camData`, `camFill`, `camHTML`, `drawCam`, `preHTML`, `fichaHTML`, `diffHTML`, `huntSheet`, `placeSheet`, `bossSheet`; `GrimFicha.refHp/huntDiff/bossDiff/preyPicks/topLoot/resist/viewport/DIFF/PREY`; atributos `data-cam`, `data-campre`, `data-cammap`, `data-camstep`, `data-camretry`, `data-boss`; classes `.fx-top/.fx-map/.fx-cam/.fx-stats/.fx-mons/.fx-loot/.fx-tips/.fx-pre`, `.cam-map/.cam-st/.cam-pin/.cam-npc/.cam-cv`, `.sh-ficha`.
- **Review Focus:** os 5 casos têm teste nas Tasks 1, 2, 3 e 4.
