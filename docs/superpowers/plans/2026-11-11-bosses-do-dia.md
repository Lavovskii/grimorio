# Bosses do dia, permanentes e eventos — plano curto

Data: 11/11/2026. Aprovado pelo dono (grilling de 11/11, Q1–Q6 «sim»). Ramo `bosses-do-dia`, um PR para o `main`.
Versão pequena do desenho de 7/11 (ramo `bosses-quests-personagem`); o resto desse desenho (passos das quests por
personagem, rotações rápida/dinheiro, painel de world changes) fica para depois.

## Decisões

- **Q1 Permanentes · Eventos · Todos** na página `#bosses`, com Permanentes por omissão. Evento = world change, mini world
  change, evento sazonal (Halloween, aniversário, Masquerade, …) e raid. Permanente = o resto (alavanca/sala, spawn fixo).
  O filtro junta-se ao que já existe (sozinho / em equipa / mais tarde / todos) e fica guardado como os outros (`ST.ui`).
- **Q2 Classificação** num campo novo `ev` de cada boss no `data/bosses.json`: `"wc"` (world change ou mini world change),
  `"saz"` (evento sazonal), `"raid"`; sem `ev` = permanente. Gerado pelo `_dev/build_bosses.py` a partir da TibiaWiki
  (API `api.php`: `spawntype` com «Raid»/«Event»; membros das categorias «World Changes», «Mini World Changes» e «Events»,
  e os bosses ligados nessas páginas), com `_dev/bosses_eventos.json` (escrito à mão, tem prioridade: `{"<chave>": "wc" |
  "saz" | "raid" | null}`). Na dúvida, fica permanente e entra na lista «a rever» do relatório do script. Ligações de
  passagem (ex.: «Double Loot Events» cita Horestis e Lloyd) não contam: só páginas de world change, de mini world change
  e de eventos sazonais.
- **Q3 Recomendação do dia**: bloco no topo, como os destaques das hunts, com até 4 bosses **permanentes**, que a
  personagem faz **sozinha** (`GrimBoss.judge` → `st === "solo"`) e que não estão em cooldown, sem repetir:
  1. **Boss em destaque hoje** — o boosted boss do dia (TibiaData `GET /v4/boostablebosses`, campo `boostable_bosses.boosted.name`; confirmado a 11/11: hoje «Eradicator»),
     só se for permanente e sozinho; senão o bloco diz qual é e porque não entra;
  2. **Melhor lucro** — maior valor por kill (`lootPerKill`, preços do Market do mundo da personagem);
  3. **Mais XP** — maior `b.xp`;
  4. **Mais rápido** — menor `r.ttk`.
  Cada um abre a ficha do boss (`bossSheet`). Os mesmos destaques aparecem como etiqueta na linha do boss.
- **Q4 «Feito hoje»**: botão em cada linha e na ficha; guarda `c.bcd[k] = timestamp` na personagem. Enquanto
  `agora < ts + b.cd horas`, o boss sai da recomendação e mostra «volta às HH:MM» (hora local); sem `cd`, volta no server
  save seguinte (10:00 CET/CEST, como o `gameDay` do site). Tocar de novo desfaz.
- **Q5 Eventos vistos ontem**: no filtro Eventos (e no Todos), um boss de evento morto ontem no mundo da personagem
  (`kstatLoad(world)`, `last_day_killed > 0`, com o plural do TibiaData) leva «visto ontem no teu mundo». Nota fixa no
  topo do filtro: «Fica um dia atrasado: não há API oficial.» Sem mundo na personagem, a nota pede para o escolher.
- **Q6** Um PR para o `main`; uma paragem no fim (capturas a 1440 e 390 px e testes); merge feito quando tudo passar.

## Tarefas

1. **Dados** — `_dev/build_bosses.py` (campo `ev`, ficheiro manual, relatório «eventos: N wc, N saz, N raid; a rever: …»),
  `_dev/bosses_eventos.json`, `data/bosses.json` regenerado. Teste em `_dev/bosses_test.mjs`: Groam e Furyosa são `wc`,
  The Mutated Pumpkin e Zorvorax são `saz`, Ferumbras e Barbaria são `raid`, Abyssador e Count Vlarkorth não têm `ev`,
  Horestis é `wc` (não «Double Loot»), Lloyd não tem `ev`.
2. **Página** — filtro Permanentes/Eventos/Todos, bloco «Bosses do dia», etiquetas, «Feito hoje», «visto ontem». Funções
  puras novas no `shared/bosses.js` (testadas em node): `isEvent(b)`, `dailyPicks(rows, boostedKey, now)`, `cdLeft(ts, cdH,
  now)`. Teste no browser em `_dev/fichas_browser.cjs` (bloco novo): filtro, 4 destaques sem repetir, «Feito hoje» tira
  o boss e mostra «volta às», desfazer, boosted intercetado, kstat intercetado com um boss de evento morto ontem.
3. **Traduções e docs** — textos novos no `i18n/src/ui-extra.json` e nas 7 línguas; `_dev/BOSSES.md` e `_dev/GRIMORIO.md`;
  `?v=` novo.

## Regras

`_dev/GRIMORIO.md` (edições ancoradas ao `index.html`, `node --check`, `gjson --check`, `?v=`, PT-PT, sem domínios novos:
o TibiaData já está no CSP), letra ≥ 12 px, alvos ≥ 44 px, sem scroll lateral a 390 px. Nunca afirmar que um evento está
ativo sem prova (só as mortes de ontem).
