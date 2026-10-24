# Grimório de Tibia — guia técnico para quem mexe no site

Site de fãs de Tibia, em **português de Portugal (PT-PT)**, centrado em hunts por vocação. É uma página estática servida pelo XAMPP (Apache) em
`C:\xampp\htdocs\grimorio\` e partilhada publicamente (http://<IP>/grimorio/). O dono quer: o Grimório como fonte principal (sem links para outros
sites — páginas internas para tudo), foco em hunts SOLO (grupo só quando há 2+ jogadores selecionados), sempre por vocação, bem estruturado e ilustrado,
e um modo visual "Modern" muito trabalhado (neon, animações em tudo) ao lado do "Original".

## Ficheiros
- `index.html` (~2 MB): TUDO — CSS, HTML, JSON embebido `G` e a app JS dentro de `<script>\n(function(){ ... })();</script>`.
- **O `G` tem uma entrada por linha** (formato canónico "largura 200": um valor fica em JSON compacto quando cabe em 200 caracteres, senão
  abre `{`/`[` com um filho por linha e 1 espaço de recuo por nível; `</` e `<!--` escapados), para o Git juntar sem conflitos as alterações
  de duas pessoas a registos diferentes. **Só se edita com `load_G`/`save_G` de `gjson.py`** (`C:\xampp\_tools\gjson.py` = `_dev/gjson.py`),
  nunca com `json.dumps` à mão. `python -I _dev/gjson.py [raiz] --format` reformata (correr outra vez não muda nada). Depois de resolver um
  conflito no `index.html`: `python -I _dev/gjson.py --check` (sai com 1 e diz a linha e a coluna se o JSON não lê ou não está no formato)
  e o smoke. Se o JSON se estragar, a página mostra "Os dados do site têm um erro" (try/catch no topo do IIFE) em vez de ficar em branco.
- `data/*.json` (carregados quando precisos com `dload(n)`/`dsafe(n)` → `data/<n>.json`): items.json (por nome em minúsculas), creatures.json,
  npcs.json, quests.json, spawns.json, npcpos.json, crdmg.json (dano que cada criatura faz), e os novos spells.json, achievements.json, mounts.json,
  outfits.json, search.json (índice global de pesquisa) — ver o formato no próprio ficheiro.
  r6-t4: `build_crdmg.py` (`C:\xampp\_tools` = `_dev/`; `python -I build_crdmg.py <raiz> [--write] [--fetch]`) faz o crdmg.json da
  TibiaWiki e, para as criaturas das hunts que lá ficam sem d e sem u, do Canary (opentibiabr/canary: monster.attacks dos .lua,
  sem os executar; feitiços com nome pelo COMBAT_PARAM_TYPE do ficheiro do feitiço; `src:'canary'`). Caches em
  `C:\xampp\_work\crdmg` (keys.json, alts.json, extra_keys.json, dl\pages|alt|extra|extra2 da wiki, dl\canary\tree.json e files\);
  sem --fetch nada vai à rede. Só acrescenta: com --write entram as chaves do site que faltam e as que estavam sem d e sem u
  (o m da wiki fica); as outras ficam iguais. O fim lista as criaturas das hunts sem dano em nenhuma fonte (hoje 33: as de
  15.10–15.30, ex. Radiant*, Raubritter*, Norcferatu*, Varg, Gloom Maw, Crypt*, e as do Bookworld).
- Sprites: allitems.png (itens, 32×32, índice `ix`), creatures.png, npcs.png (+ npcs2.png), spells.png (+ spells2.png), loot.png, huntmaps.png,
  mounts.png/outfits.png (64×64), maps/floor-XX-map.png (mapa; origem 31744,30976). creatures.png e npcs2.png têm células de 64 px em 32 colunas
  (`G.cr[k]`, `ix2` em npcs.json; `npcSpr(n,ph)` procura em G.np e depois em npcs2.png; com `ph` devolve o ícone de espaço fixo `.ph-ic`).
  Quando regeneras um PNG de sprites, muda o ?v= em todos os URLs desse PNG (hoje `?v=20261018r2`; huntmaps.png tem o seu próprio).
  r6-t4: loot.png com 1024×1472 (`?v=20261019r6`). `build_loot_sprites.py [raiz] [--dry] [nome …]` (`C:\xampp\_tools` = `_dev/`;
  usa o client_outfits.py de C:\xampp\_tools) desenha a seguir ao maior índice de G.lt os itens de items.json sem imagem (os
  supplies do build_supplies.py e o Enchanted Werewolf Helmet): render_item + fit_cell(…, 32), modo P com a paleta de sempre
  (cor mais próxima; as células antigas ficam iguais byte a byte) e G.lt com save_G. Depois: ?v= e build_search.py.
- `api/market.php?world=<Mundo>`: preços do Market por mundo (proxy com cache de 6 h do TibiaMarket). Resposta: `{world,updated,fetched,stale,items:{"<id>":[sell_offer,buy_offer,month_avg_sell,month_avg_buy,day_avg_sell,day_avg_buy,month_sold,month_bought]}}`.
- `.htaccess`: HTML sem cache, JSON permitido (o .htaccess da raiz é de um MyAAC antigo), `RewriteEngine On`, deflate, e 404 a tudo o que
  começa por `.git` (a pasta pública é um clone do repositório; `RewriteRule` e, sem mod_rewrite, `RedirectMatch`). `_dev/` tem o seu `.htaccess` (403, também para os `*.json`,
  que o `<FilesMatch "\.json$">` da raiz deixaria ler).
  `.editorconfig`: UTF-8 e fins de linha LF (o `.gitattributes` tem `* -text`: o Git guarda os ficheiros tal e qual).
- Rotações (r12): `shared/rotacoes.js` (`GrimRot.plan`, `toHK`, `toRot`) + `data/rotacoes.json` (`_dev/build_rotacoes.py`) + teste
  `node _dev/rotacoes_test.mjs`. Modelo e regras: `_dev/ROTACOES.md`. A página `#rotacao` é 'Rotação e hotkeys' (o `#hotkeys` e o
  `ST.ui.p` antigo vão para lá). r14, sem escolhas: `renderRx` desenha `GrimRot.layout` (a barra que um jogador monta: uma linha de
  teclas por elemento, Q W E R F D T, a 2.ª com Shift; MABs no Q/W/E do knight, paladino e monk; G runa de alvo, H abertura do boss)
  com `rxTile`, o 'Como jogar' (`rxKb` põe as teclas em `<kbd>`) e `rxCmpHTML` (compara com a barra do Tibia). `rxGear(c)` dá os
  bónus do set da personagem (ou do `bisSet` se estiver vazio), `rxOpt(c,gr)` as opções do motor, `rxStatsLine` a linha das contas.
  Comparar: `<input type=file data-rxfile>` lê o `clientoptions.json` no browser, `GrimRot.readBars` tira só o `hotkeyOptions`
  (preset com o nome da personagem, senão o ativo) e guarda `c.tbar = {sets: {preset: [{k, acts:[{w}|{item}]}]}, sel}`;
  `[data-rxpre]` troca de preset, `[data-rxforget]` apaga. `GrimRot.review` dá as dicas (`RXTIP`: Atenção, Juntar, MAB, Dica, Nota).
  O `renderHotkeys` desenha Sobreviver (teclas 1–4, depois Shift+1–4), Stances e Utilidade (F1…). O `vd.rot` (presets do TibiaPal)
  fica no G mas já não aparece. O motor carrega no `<head>` (`shared/rotacoes.js?v=`). Textos novos ainda sem tradução no i18n.
- Bosses (r16): página `#bosses` (Hunts → Bosses), `renderBosses` só quando a página abre (carrega `bosses`, `rotacoes`, `items`,
  `creatures` e o Market do mundo). O motor é `shared/bosses.js` (`GrimBoss.judge`: estado solo|team|later|locked|unknown,
  `soloL`/`teamL`, tempo para matar), sobre `data/bosses.json` (`_dev/build_bosses.py`, TibiaWiki; `--loot` acrescenta ao items.json o
  loot dos bosses que faltava). A curva de dano é `bsCurve(c)` (GrimRot.plan, cenário boss, escalado pelo dano real com `rxGear`/
  `rxOpt`; cache `BSCACHE`). O loot por kill é `lootPerKill`. O Bosstiary é `c.bst = {chave: estágio 0–3}` (`[data-bstier]` roda
  o estágio), com pontos e bónus de loot em `GrimBoss`. O filtro é `ST.ui.bsf` (`BSF`). Modelo e limites: `_dev/BOSSES.md`;
  teste: `node _dev/bosses_test.mjs`.
- `CONTRIBUTING.md` (r5-t3): como colaborar no GitHub (um ramo por tarefa, Pull Request revisto pelo outro, testes com o smoke.mjs,
  o G só com `load_G`/`save_G` e `gjson.py --check`); o `README.md` aponta para ele. `build_supplies.py` (r5-t3; `C:\xampp\_tools` = `_dev/`):
  acrescenta a data/items.json as poções, munições e runas do `supRows` que faltam, lidas da TibiaWiki (Infobox Object + Module:ItemPrices/data,
  cache em disco); nunca muda uma chave que já existe. Depois, `build_search.py`.
- Backups: `C:\xampp\_backups\`. Ferramentas: `C:\xampp\_tools\` (este guia, `smoke.mjs`, `gjson.py`, `build_search.py`, `apply_hunt_fixes.py`,
  `build_huntmaps.py`, `client_outfits.py` = desenha outfits/objetos a partir do cliente Tibia instalado, só leitura) e `C:\xampp\_work\fix_hunt_mons.py`;
  as cópias no `_dev/` do site são iguais (copia-as quando as mudares). Corridas a partir de `_dev/` sem raiz, usam a pasta-mãe (o clone); os
  registos (`apply.log`, `fix_hunt_mons.log`) vão para `%GRIM_WORK%` ou para a pasta temporária. O `apply_hunt_fixes.py` volta a pôr os valores
  dos fix-*.json (notas, acessos…) por cima do que mudou depois: corre-o primeiro com `--dry` e lê o registo. Trabalho temporário: `C:\xampp\_work\`.
  r6-t1: a fix-26 dá as cidades das zonas novas (Isle of Ada → Bounac, Radiant → Venore), as quests (iksupan → galthen1, carnisylvans →
  lostqueen, asuramirror → lostbrother; 'Adventures of Galthen Quest' dá galthen2) e os mapas aproximados. Armadilhas do apply: uma entrada
  'fix' high/medium sem a chave quest e com a palavra 'quest' no problems TIRA o q da zona; com confidence 'high' e sem team, uma zona com
  team:true perde a equipa (usa 'medium'). Atenção: hoje o apply sem --dry ainda repõe notas antigas em 24 zonas e tira 4 linhas f da
  w_razachai_inner_sanctum (o registo não mostra as notas): compara o G antes e depois (`t1\apply_check.py` da ronda r6).

## Dados principais em `G`
- `G.items`: equipamento `{id (id do cliente = id do Market), n, s (slot: helmet|amulet|armor|legs|boots|ring|weapon|shield|extra), l (nível), ix, v (vocações: "k","p","s","d","m" juntas, ex. "ds"), arm, def, edef, atk, wel [el,val], wd [el,min,max], hit, sk {ml, ml_fire, sword, dist, fist, shield...}, ab {elemento:%}, spd, rg [vida,mana], is (slots de imbuement), it (imbuements aceites), chg, dur, h2 (duas mãos), b (tipo de arma), ex [texto], mn (mantra), ns (sem stats), tp}`.
- `G.mon[k]` = [nome, hp, xp, ix, imunidades, resistências {el:%}, loot [[ix,nome,%,valor]], boss]. Resistências: `G.mon[k][5] = 100 − el` da TibiaWiki (`el` = % de dano que a criatura leva, em data/creatures.json) nos 7 elementos; 100 = imune, acima de 100 = o elemento cura a criatura (ex.: fogo 200 na Ravenous Lava Lurker). `G.places[pid].eff` = média de 100 − resistência nas criaturas de `p.mons` (e `eff.min` = o mínimo), a fórmula de `eff()` em apply_hunt_fixes.py. `G.mc`/`G.mcn`: classe do Bestiary.
- `G.places[pid]` = {n, mons, q (quest de acesso), d (risco 1–3), eff {el:% de dano}, team (true ou uma lista de vocações que só a fazem em equipa), w (da TibiaWiki), xs, ls, city, acc, note}.
  r6-t1: `wn` = nomes oficiais da TibiaWiki que a pesquisa também procura (ex.: werecrocs ['Murky Caverns'], laststand ['Iksupan Waterways', …]);
  `asuravaults` = Asura Vaults (Port Hope, The Lost Brother): as linhas 'True Asuras' do TibiaPal (a Asura Citadel de Marapur ficou com linhas f:1).
- `G.hunts[voc]` = linhas {c (pid), place, l, xp, lo, how, f (preenchida), w, v (nível verificado)}. `how`: nos mages é a rotação do TibiaPal; no knight, no paladin e no monk é o tipo de arma ou munição do TibiaPal (coluna 5, ex. "Fire, Ice", "Diamond Arrows, Ethereal"), lido por `huntEls(how)` (elementos citados, por palavra inteira), `compatFor(voc,place,how)` (melhor elemento entre vd.els e a arma/munição elemental ou, nos druids e sorcerers, as runas citadas na rotação — r4-t3; `via` = o melhor vem da arma, da munição ou das runas; `imm`, `heal`) e `setupHTML` (linha "Ataca com" e linha "Arma"/"Munição"/"Rotação"); o `elemHTML` põe o "usa este" no elemento que o setupHTML escolheu (`ELPICK`, por place e vocação). Regra: linhas f: l nunca abaixo do nível real mais baixo de outra vocação, exceto as linhas com v:1 (nível confirmado na TibiaWiki ou na verificação online). `G.pm[pid].h` = [[criatura, quantidade]] do mapa.
- Níveis do TibiaPal (r5-t1): `python -I C:\xampp\_work\rounds\2026-10-19-r5\audit-hunts\tp_levels_check.py G.json` compara os níveis das linhas
  de `G.hunts` sem f nem w com o TibiaPal (`lote16/dl/tp_rows.json`) e deve dizer '0 zonas com níveis diferentes'. Nos fix-*.json, `team` também
  pode ser uma lista de vocações (o apply_hunt_fixes.py grava-a assim).
  r6-t2: `o:1` numa linha de G.hunts = número do TibiaPal de antes do rebalance de junho de 2026 (a página atual já não o mostra; xp e
  lo ficam). `python -I C:\xampp\_tools\tp_xp_check.py [raiz | G.json]` (= `_dev/tp_xp_check.py`) compara o XP/lucro das linhas sem f,
  w nem o com o TibiaPal (`lote16/dl/tp_rows.json`) e deve dizer '0 linhas diferentes'. `G.ha[pid]` = {s (soma das sessões solo), t
  (em grupo), v {voc: [sessões, nível mínimo, nível mediano, XP/h, lucro/h]}}: uma sessão com mais de 4000 mortes/h (XP/h ÷
  `avgXp(pid)`) não é solo nem desta zona e sai (registo em `C:\xampp\_work\hunts\ha_clean.log`); cada chave de G.ha existe em G.places.
- `G.hv[pid]` = {t (transporte), rq (requisitos), st (passos), v ("ok" | "fix" | outro)}: o bloco "Acesso" do separador "Como chegar" (`vRoute`; etiqueta confirmado/revisto/por confirmar).
  Só texto para o jogador: as notas da verificação (n, ed, mf, e, s, ok e o texto original de rq/st antes da limpeza) ficam em `_dev/hv_notas.json`;
  um conselho para o jogador (boss, perigo, atalho) vai para `G.places[pid].note` ("Notas").
  r6-t1: zona sem G.hv nem G.routes (as w_ da TibiaWiki) → o `huntRoute` faz o bloco 'Acesso' com o `p.acc` ('por confirmar', 'Requisitos:'
  com a quest, o botão 'Lore e guia ›' e 'Premium') e põe o percurso automático por baixo, com o título 'Percurso aproximado'.
- `G.hm[pid]` coordenadas; `G.voc[voc]` (n, promo, els, pots, charms, imbs, allsp = feitiços); `G.quests`, `G.charms`, `G.wheel`, `G.equip` (TibiaPal), `G.vr`, `G.ha`.

## Estado e funções úteis (dentro do IIFE)
- `ST` (localStorage `grimorio-tibia-v4`): `{v:4, active, chars:[...], custom:[], ui:{p, ...}}`; `C()` = personagem ativa; `save()`; `renderAll()`.
- Personagem: `{id,name,voc,level,pct,ml,skill,world,tib,hs,done,charms,imb,owned{id:true},sets:[{id,name,mode,prot,slots{slot:{id,imb}}}],aset,hset:"bis"|"mine"}`.
- Navegação: `SECS` (secções e subpáginas), `go(p)` (fecha o painel e põe o hash igual à página com replaceState), rotas por hash `#item/<slug>`, `#criatura/<slug>` em `route()`
  (decode com try, secções em minúsculas, `?…` ignorado, hash desconhecido volta ao da página; `hasKey(o,k)` contra chaves do Object.prototype). Histórico: cada entrada
  tem `history.state.gd` (profundidade; `NAVD` no JS); usa sempre `history.replaceState(history.state, …)`, nunca `null`. '← Voltar' (`[data-back]`) só faz history.back() se NAVD>0.
  Hunts por cidade e por tipo de criatura (r5-t2): `#hunts/cidade/<slug>` e `#hunts/tipo/<slug>` → `hfRoute(kind,slug)` (cidade = `slug()` de uma
  `G.places[*].city`; tipo = `slug()` da chave de `G.mcn` ou do nome PT do `clsName`) põe `ST.ui.hf = HF0()` com `city` ou `cls:[chave]` e a faixa
  'upto'; sem correspondência abre as Hunts sem filtro e o `#huntLead` começa por 'Cidade não encontrada.'. Filtro 'Cidade' = `f.city` (`[data-hcity]`,
  grupo 'Quem e onde'); `hfHash()` (só com a página das Hunts à vista e depois do 1.º `route()`) põe o hash da cidade ou do tipo quando é o único filtro,
  senão volta a `#hunts`; com um destes endereços aparece 'Copiar link'. Índice no fim da lista (`#huntIdx`, `hidxRender`: 'Hunts por cidade' e
  'Hunts por tipo de criatura'); na pesquisa, os ramos `hc`/`ht` ('Hunts em <Cidade>', 'Hunts de <tipo>', grupo 'h' com `gsGrp`); cartões com `data-pid`.
  `hasKey` está no topo do IIFE (logo a seguir ao `esc`): pode usar-se em qualquer função.
  `openSheet(html)`/`closeSheet(o)`: o `#sheet` passa para o body no arranque (z-index acima do header e da barra inferior também no Modern); abrir faz pushState
  `{sheet:1}` (o Voltar do telemóvel fecha-o), põe inert no resto da página, prende o Tab e devolve o foco a quem o abriu; ✕/fundo/Esc fazem history.back();
  quem navega a partir do painel chama `closeSheet({nav:true})` (sem history.back);
  `tabsUI([[id,título,html,contagem]])`; `pageHead(...)`; `adSlot(slot,tamanho,cls)`; `mapBtn(x,y,z,label)` / `openMap(...)` (mapa interno).
- Preços (r4-t2; uma só regra para o look, a página do item e a ficha da hunt; nunca `m[2]||m[4]||…` nem `fmt()` para dinheiro, que dá '0k'):
  `MKFEE(v)` = taxa do Market da TibiaWiki (2 % da oferta, mínimo 20 gp, máximo 250 000 gp, desde fevereiro de 2023) e `mktNet(v,q)` = v − taxa
  por unidade numa oferta de q unidades (q = 1 por omissão; `priceOf` usa 100 nos itens empilháveis, porque o mínimo de 20 gp é por oferta).
  `mktVal(m)` (m = `[so,bo,mas,mab,das,dab,ms,mb]` do api/market.php) → `{sell:{v,lab,n,ok,liq}|null, buy:{v,lab}|null}`: venda = média do mês
  com 3+ vendidos (ok; liq com 10+), 1–2 vendidos / média de hoje / oferta mais barata = `ok:false` ('pouco fiável'); compra só com compras
  feitas e entre venda/20 e venda×20. `mktIds(k,it)`/`mktRow(k,w,it)`: ids do item no Market (id do equipamento e depois `ids` de items.json).
  `priceOf(k,w)` → `{npc:[nome,valor]|null, mkt:sell|null, net, best:'npc'|'market'|'coin'|null, v}` (vender; `best` 'market' só com liq e
  net > NPC × 1,1; moedas `best:'coin'`; sem preço fiável `v:0`). `buyOf(k,w)` → `{npc:[nome,preço]|null, mkt:{v,lab}|null, best, v}`
  (comprar; Market quando fica 5 % ou mais abaixo do NPC). Ambas precisam de `ITV` (items.json) e de `MKV[w]` carregados (`mktLoad(w)`,
  10 s de tempo-limite; falha ou resposta vazia = null e volta a tentar ao fim de 60 s). `supRows(c,how)` → `[{k,n,kind:'pot'|'rune'|'ammo'}]`
  (poções da última linha de `G.voc[voc].pots` até ao nível; magos: runas citadas no how, senão as '(runa)' das hotkeys; paladino: 1.ª
  munição do how; as poções e munições estão em items.json desde a r5-t3: `build_supplies.py`). `lootQty(a)`, `lootPerKill(k,CR,w)` →
  `{v (gp por kill), top:[[nome,gp,pct]], miss, none}` (k = chave de creatures.json), `lootAgg(pid,CR,w)` e `gpPerXp(pid,CR,w)` = gp por
  1000 XP (criaturas de `G.places[pid].mons` sem bosses, quantidade de `G.pm[pid].h`); loot por hora ≈ XP/h × gpPerXp / 1000.
  Separador 'Loot e lucro' da ficha: `<div class="lp" data-lootp=pid data-xp data-lo data-lsrc data-how [data-g data-sb]>` preenchido por
  `initLoot(root)` (chamado no clique dos separadores, ao lado de `initRoutes`/`initQuests`) → `lpHTML`; calculadora só na ficha solo
  (`[data-hcalc]`, `lpCalcRun`/`lpCalcSave`), gravada em `c.calc[pid] = {hrs, q:{chave:[quantidade, preço só se mudado, nome]}, loot (só
  se mudado), fee, t}` (no máximo 50 hunts). Página do item: `[data-mkt]` = ids separados por vírgula (`mktFill` escreve o valor e o
  `<span>` seguinte), `#itemAdv` reescrito com `itemAdvHTML` quando o Market chega. Look: `lookShow` redesenha quando cada dado chega.
  r5-t3: `data-xp` do separador Loot e lucro = XP sem evento (`h.xp0` / `g.party0` do `groupRows`); `data-evk` = criatura do dia (só na ficha
  solo, com o evento 'Uma criatura'): o `lpHTML` faz loot × (1 + parte dela no loot da zona) (loot ×2) e escreve a nota 'Criatura do dia (loot ×2)'.
  r6-t4: também na ficha de grupo (o `.lp` do `groupSheet` leva o mesmo data-evk). `lootPerKill` → `nodata` (nenhuma linha de loot
  com % de drop, ou fora do creatures.json); `lootAgg` → `nd` (criaturas com kills sem loot conhecido; `kills[].nd`) e `g1k:null`
  quando são todas (o `gpPerXp` também): o `lpHTML` diz 'Sem dados de loot para as criaturas desta zona.' com os KPIs a '—' (nunca
  '≈ 0 gp'); com só algumas, a nota `.lp-nd` 'Sem loot conhecido: A, B, C e mais N (contam como 0 gp no loot por hora).' Os
  cartões, o filtro 'Dá lucro' e o comparar hunts não usam o g1k (usam o lo do TibiaPal).
- Hunts: `huntRows(voc, L)` (L = nível máximo da variante do TibiaPal; sem L = nível da personagem + 5; nível/XP/lucro da mesma variante), `huntCard(h)`, `huntSheet(h)`, `setupHTML`, `hsetsHTML(pid)` (sets ofensivo/consistente/defensivo), `huntProfile(pid)` (dano da hunt).
  Evento de XP (r5-t2): o de uma criatura só liga com `hasKey(G.mon,…)` (`evOn`, `evLabel`, `#evMon`); +100 % por omissão (TibiaWiki: a boosted
  dá o dobro da XP e do loot).
  Magos (r4-t3): o `HOWEL` conhece as runas (gfb, sd, avalanche, stoneshower, thunderstorm), Forked Glacier/Thorns e Shatterstorm (físico);
  o `compatFor` e o `setupHTML` contam o elemento das runas citadas na rotação ('Ataca com … com runas de …'). No `huntRows`, uma linha
  com XP medida pelo TibiaPal para a vocação (sem f nem w) nunca fica 'bad' (passa a 'meh', '(o TibiaPal mediu esta hunt…)').
  r6-t2: `huntRows(voc, L, pl)` (pl = nível do jogador, por omissão o de `C()`; o `groupRows` passa o de cada membro). `src`: 'tp'
  (TibiaPal), 'old' (linha o:1: est='old', sem a exceção 'meh', as sessões reais da vocação ganham-lhe), 'ha' (sessões da vocação),
  'est' (outra vocação; linhas o:1 só sem nenhuma atual), 'hao' (mediana das sessões reais de outras vocações com 3+ sessões e
  pl ≥ 3/4 do nível mediano, × o fator das estimativas) ou 'mx' (hunts 300+: K × `avgXp(pid)` × dano entre 0,6 e 1,1; K = 1000
  abaixo do 600, 1400 a partir do 850, linear no meio; no máximo 18 000 × pl ÷ vida média, o dano por hora da sessão real mais
  rápida, Podzilla, sorcerer 925; e no máximo o ritmo medido na zona: linhas atuais do TibiaPal de outras vocações e sessões reais
  com nível ≥ 0,6 × o da linha; lo null). `estx` = {n,v,m} ('hao') | {k,z} ('mx': mortes/h, medições) | {o:1} (estimativa de um número
  antigo). `avgMon(pid)` = [XP, vida] média por morte (G.pm.h ∩ mons, sem bosses, pesada pela quantidade; cache `AVGXP`); `avgXp`.
  Cartões: `hcEst(h)` (≈ com title, sup 'r' ou 'a' = `.rl.rla`); sem número, `<span class="hcx">` com as estrelas ou 'XP e
  lucro por medir'; a ficha acaba com `estTxt(h)`. O Loot e lucro recebe `data-lsrc='est'` nas estimativas 'hao' e 'mx'.
  Charms: `G.charms` tem os 25 charms `{n,t,c,d,f}`; `f` = 'el:<elemento>' (Freeze, Zap, Wound, Poison, Enflame, Divine Wrath, Curse),
  'hp5' (Overpower), 'mana25' (Overflux) ou null. `charmFor(c,k)` → `[{k,dmg}]` dano por ativação na criatura k de `G.mon` (TibiaWiki):
  elementais e Wound = min(5 % da vida da criatura, 2 × nível) × dano %; Overpower = min(5 % de `hpOf(c)`, 8 % da vida) × físico %;
  Overflux = min(2,5 % de `manaOf(c)`, 8 % da vida) × físico % (todas as vocações; ≤ 0 fica de fora). A linha 'Charm' do setupHTML
  (`suCharm`) dá um charm diferente a cada uma das 3 criaturas principais (`G.pm[pid].h` ∩ `place.mons`, sem bosses, por xp × n), porque
  no jogo um charm só pode estar numa criatura de cada vez; ' ou X' a menos de 5 %; sem criaturas, a média da zona (`CHARM_EL`, Wound se
  faltar). Setup: pares `<div class="su su-el|rot|charm|safe|sup">` com `.su-ic` (mosaicos só no Modern; no Original `.su` é
  display:contents), `suRot` (chips, feitiços e munição com link, 'ver rotação ›') e a linha 'Supplies' (`suSup` com `supRows` e
  `buyOf`; o id `su-sup-N` é preenchido depois de items.json, do Market e do índice de links).
  Página Charms (r5-t5): `CHARM_IC` (paths 24×24 em traço: os elementais pelo elemento do `f`, os outros pela chave) e `charmIc(k)` →
  `<span class="ch-ic md-only" style="--cc:…">` (var(--<elemento>), senão var(--gold) nos majors e var(--accent) nos minors).
  `renderCharms`: progresso `.ch-prog` em #charmProg/#minorProg ('x de n desbloqueados · faltam N charm points/echoes', N = soma do
  1.º número de `c` dos por marcar, `charmCost(k)`); nas listas a `<label>` só envolve o nome e a descrição `.d` (#chd-<chave>,
  aria-describedby) abre a linha (`li.open`); cartão #charmAll com os 25 charms (`<li id="cm-<chave>" tabindex="-1">`, selo 'na tua
  ordem' = `.cm-mine`). Os links do `suCharm` levam `data-cfocus="<chave>"`: o handler de `[data-go]` e a pesquisa (ramo `ch`) chamam
  `charmFocus(k)` (scrollIntoView do #cm-<chave>, suave só sem reduced-motion, foco e `.cfocus` durante 2,4 s).
  Quests (r5-t5): `renderQuests` põe os `.q` de cada `details.qgroup[data-qg]` num `<div class="qgrid">` (2 colunas no Modern a partir
  de 1100 px; no Original fica uma coluna), a checkbox dentro de `<label class="qchk">` (44×44 no toque), `#questBar.zero` com 0 feitas e
  `.qpop` (`QPOP`) no cartão acabado de marcar. A ≤620 px (os dois modos) `#sheet .tabs`, `#subtabs .seg.scroll`, `.eqtabs` e `.sltabs`
  partem em linhas (sem nada escondido fora do ecrã) e o ✕ da ficha (`.sh-x`) tem 44×44 e fundo opaco (`.sh-h` com padding-right:52px).
  r6-t5: Quests no Modern a partir de 1100 px: o 'Lore e guia ›' da `.meta` fica escondido (o `.qtitle` abre a ficha e mostra ' ›' ao
  passar), a `.meta` sobe para a linha do título e a descrição fica inteira por baixo (página ≤ 3300 px a 1440 e a 1366).
  Wheel (r6-t5): `wheelDom(w)` → {tl,tr,bl,br} 0–3 (o 'Vessel Resonance <Top|Bottom> <Left|Right>' I/II/III de w.conv) para a mini-roda
  `.wh-dom` (só Modern, 4 `path.wq[data-l]`), `wnum(s)` põe os números do planner em pt-PT ('1,050' → '1050', '11.25%' → '11,25%');
  vantagens em `.wpk` com `.wsep` (chips no Modern; no Original lê-se como texto), `.wh-prog` (--p) e 'N de M pontos · faltam K
  (nível X)' até à build seguinte, 'Estás aqui' na linha atual; a ≤620 px a #wheelTable passa a cartões (td[data-l]). `tr.dim` em
  #wheelTable/#defPots sem opacity (texto em --muted). `[data-copy]` com `data-copied="…"` escreve essa frase no `#copyLive`
  (p.sr-only role=status, antes do script); sem a API da área de transferência (http fora do localhost) copia por um textarea.
  Defesa (r6-t5): #defStats com os mosaicos `.stat` do Início (as regras Modern são `:is(.hero,#defStats) .stat`), `#blessSum`
  (`.bless-sum`), blessings com `npcSpr` e os preços da TibiaWiki em todos os níveis (enhanced = 260 × (L − 20) até ao 120), a
  tabela das poções `#defPots` gerada no `renderDefesa` (custo = preço NPC ÷ mana média; tr.now = poção de mana das hotkeys, tr.dim =
  as que a vocação não usa) e a lista `.def-tips`. Taxa do Market num só valor: `MKPCT` (2; TibiaWiki, 19/10/2026) no `MKFEE` e no
  `#defFee` da Defesa (o título 'Market −2 %' da tabela do `lpHTML` ainda é texto fixo).
- Equipamento: `scoreItem(c,it,mode,prot)` (mode combat|speed|off|bal|def; prot = elemento ou perfil {el:peso}), `ranked`, `pickSet`, `bisSet`, `setTotals`,
  `setSumHTML`, `renderBis` (painel inicial), `renderEquip`/`renderSlot`/`renderInventory`, `pickOpen` (botão direito), `itemLookHTML` + `[data-look="<id>"]` (look ao passar por cima).
  Pontos v2 (r8): o `scoreItem` devolve o que o item muda no combate, em %: D (dano: skills e ML pelo skill/ML da personagem,
  `chStats` estima-os pelo nível quando ficaram por omissão; arma pela fórmula do dano em `scBase`), P (dano recebido: proteções % ×
  perfil da hunt ou `SCPF`; armadura e defesa ÷ golpe físico médio do nível `H`), velocidade em % (`SCSPD`) e X (slots de imbuement
  0,15–1,5 % pelo nível; regeneração). Conta também perfect shot, cleave, damage reflection, magic shield capacity e life leech do
  `it.ex`, o ML holy do paladino, `it.crit` = [chance %, dano crítico %] e `it.lch` = [life leech %, mana leech %] (r8, da
  TibiaWiki: 23 armas e anéis, ex. Sanguine, Soul, Cobra, Lion). Modos: `SCMODE` [D,P,vel]. O jogador vê a nota 0–100 do `notaItem` (÷ `slotTop`: o melhor item do
  slot até ao nível, sem cargas nem < 15 min; cache `NOTAC`) no botão direito, nas listas do slot e no look.
  Pontos v3 (r10; o sorcerer 3000 tinha Dawnfire pantaloons e o Prismatic ring do 120 ao 3000 em quase todas as vocações):
  feitiços dos magos = nível/5 + `SCML` (9) × ML, das fórmulas da TibiaWiki (página Formulae: Hell's Core 7–14 × ML, Eternal Winter
  6–12…); knight e monk com a parte de feitiços `SCSPL` (Fierce Berserk ≈ 2,05 × (skill + 2 × ataque) + nível/5; `scPhys(B,A)`);
  `chStats` com curvas que crescem devagar (ML de mago 70/94/109/128 nos níveis 100/400/1000/3000; skill 90/114/130/149). Sem hunt,
  as proteções pesam pelo `G.dpf` (`scPF(c)`: perfil de dano das hunts da vocação na faixa de nível; `_dev/build_dpf.py`, volta a
  correr quando mudarem as hunts ou o crdmg.json), com o `SCPF` só de reserva. `SCW[voc]` = [peso do dano, peso da proteção]
  (knight 1/1,1; monk e paladino 1,5/0,8; magos 1,6/0,8), calibrado com as listas de equipamento do TibiaPal (`G.equip`): o set
  automático tem de usar um item da lista e não muito mais antigo do que o mais recente; com o v2 eram 434 de 500 casos, com o v3
  476 (sobram níveis 100–150, o Prismatic ring do monk entre 150 e 350, que é para todas as vocações e por isso não está nas listas
  do TibiaPal, e o knight com arma de duas mãos no 300). Mantra (só monk) = proteção fixa contra fogo, gelo, energia e terra, como a
  armadura (TibiaWiki), não dano. Magic Shield Capacity vale pouco (não tira dano, passa-o para a mana). No `pickSet`, entre os itens
  a menos de 4 % do melhor (1 % nas armas), fica o de nível mais alto (quase empates que só mudam no elemento protegido).
  Dados (r10): `_dev/fix_bis_items.py` dá os atributos aos 4 Flamingo Amulet (eram entradas do TibiaPal sem atributos) e o dano da
  versão normal às Stellar Moonsilver Sceptre e Channeler (6–6 da ficha incompleta da wiki). Os 1402 itens do G.items foram
  comparados com a TibiaWiki (nível, vocações, armadura, defesa, ataque, skills, proteções, slots, dano das wands, elemento, duas
  mãos, crítico, leech, velocidade, mantra): sem outras diferenças que contem para os sets.
  Sets automáticos (r4-t5): paladino com a arma em 'Automático' (`c.wtype` vazio): o `pickSet` usa arco a partir do nível 100
  (abaixo, lanças e estrelas; com o filtro 'só os que tenho' e nenhum arco, todos os tipos); na ficha, `huntWType(c,pid)` dá o tipo
  da munição do TibiaPal (`how` da linha de G.hunts.paladin: bolt → besta, arrow → arco, spear/star → arremesso) ao `huntSet`, que
  faz os 3 sets e o 'Guardar nos meus sets'. Munição: `AMMO` {bow|crossbow: [[nível, ataque]]} das munições sem elemento (TibiaWiki)
  e `ammoAtk(b,L)`; o `scoreItem` soma-a ao atk dos arcos e das bestas (o `setSumHTML` mostra 'Ataque N + munição'). Durações:
  anéis e amuletos com menos de 15 min ficam fora do `pickSet` (no botão direito continuam, com 'dura N min'); no `scoreItem` um
  item com dur pesa ×0,35 (< 15 min), ×0,6 (< 30), ×0,75 (< 1 h), ×0,85 (< 2 h) ou ×0,95 (r10: os de 3 h que se recarregam
  quase sem desconto). O mantra do monk é proteção (r10, ver em cima).
  r7: o `AMMO` tem o nome em 3.º lugar e mais Tarsal Arrow, Crystalline Arrow (90, 65), Vortex Bolt e Prismatic Bolt (90, 66); Infernal
  Bolt 72 (era 65). `AMMOA` = flechas de área [nível, nome, elemento, ataque] (TibiaWiki 15.25: Shatterstorm 27 no 50; Firestorm,
  Terrastorm, Froststorm e Thunderstorm 21 de dano do elemento, ataque físico 0, no 125; Diamond 37 no 150). Onyx Arrow 38 (r8). `ammoBest(b,L)` (alvo único, sem a
  Diamond), `ammoArea(b,L)`, `ammoChips(b,L,eff)` (chips 'Alvo único'/'Área'; com eff, a % que as criaturas levam e 'usa esta'; link só
  com o item no items.json). Linha 'Munição' no `setSumHTML` (com a personagem) e em cada set do `hsetsHTML` (`.hs-am`); `setTotals` dá
  `t.sb` (tipo do item da mão do escudo). Sem aljava (abaixo do 150 não há nenhuma com stats): `quivTip` no slot vazio e no chip 'Aljava'.
  r10: `palAmmo(c,set)` (paladino com arco/besta) divide a mão do escudo em aljava + munição para o nível: no #doll `.slot-pal` com
  `.slot.half` (aljava = o slot real) e `palAmHalf` (munição, link se tiver página); no #bis e nos sets da ficha `.bslot.pal2` em diagonal.
  Quiver, Red quiver e Blue quiver (nível 0, 400 gp nos NPCs) entraram no G.items/items.json com sprite em allitems.png (ix 1446–1448).
  Escudos de knight nos magos: defesa × 0,1. Proteção de afogamento só conta com 20 %+ de
  dano drown na hunt. Mão esquerda: `slotLab(c,k)` ('Escudo / aljava', 'Livro / escudo', 'Escudo') no #bis, no #doll e nos sets
  da ficha; o `SLOTNAME`/`DOLL` ficam iguais (o renderSlot e o pickOpen usam-nos). No botão direito (`pickList`), o paladino
  em 'Automático' a partir do 100 vê os arcos primeiro e as bestas e o arremesso num grupo à parte (`.pk-g`).
  Sets coerentes (r5-t4): knight em 'Automático' (sem `c.wtype`) → `knightWType(c)` = `c.wtype`, senão `c.hs.sk.k` (sword/axe/club), senão
  o tipo cujo `pickSet` de combate (sem perfil nem filtro) soma mais `scoreItem`; em cache no `KWTC` (Map, chave id|nível|hs.sk.k). O
  `pickSet` força-o logo a seguir ao bloco do paladino (com o filtro g e nenhuma arma desse tipo marcada até ao nível, o tipo da melhor
  arma marcada): o BiS, os 3 sets da ficha, 'Preencher com o melhor' e o botão direito ficam com um só tipo de arma; o `relSkills` do
  knight sem tipo também o usa (listas, look e sets com os mesmos pontos: o Axe ring não conta com espada). `WTYPES.knight[0]` =
  'Automático (o teu skill mais alto)'. Elemento da hunt: 5.º parâmetro `eff` em `scoreItem(c,it,mode,prot,eff)`, `ranked(c,slot,mode,prot,f,set,eff)` e
  `pickSet(c,mode,prot,g,eff)`; o `huntSet` passa `G.places[pid].eff`. Na arma, EF(x) = 1 sem eff; 0 se `eff.min[x]` < 0 (o elemento
  cura alguma criatura); senão max(0, eff[x] ?? 100)/100: dano `wd` × EF(wd[0]), atk + munição × EF('physical'), `wel[1]` × EF(wel[0]).
  Sem eff (Início, Equipamento, botão direito) nada muda. Regeneração `rg` × min(1, 100/nível); itens com dur fora dos anéis e amuletos
  (Void boots, Firewalker boots, Tiara of power, velas…) × 0,6 (os anéis e amuletos ficam com ×0,35/0,6/0,8/0,9). `setSumHTML(t,lab,c)`
  (#heroSet e #setSum passam a personagem): só as skills que contam (`setSkOk(c,t)`: peso > 0 no `relSkills` com o tipo de arma efetivo,
  o da arma do set ou o `knightWType`; os ml_* que o relSkills não pesa contam) e as outras num chip `.hs-sk.hs-nc` ('+21 axe · +21 club
  (não contam com sword)'); o mesmo filtro nas 3 skills da `.hset-kv`. Listas do slot da arma: `wGroup(c,slot)` → `{b,n,lab}` ou null
  (tipo escolhido): o `pickList` (`.pk-g`) e o `renderSlot` ('Melhores até ao nível': 8 do tipo do set, `<li class="ilist-g">` e 3 dos
  outros; 'Ver todos os N' conta todos) põem esse tipo primeiro; a `.note` diz o tipo usado no knight. Ficha: `.hset-note`.
  r6-t3: no monk, o ataque da arma conta com a ligação elemental (`it.bond`; as 36 armas fist têm: 16 energia, 11 físico, 9 terra):
  o `scoreItem` faz `EF(it.bond)` em vez de `EF('physical')`. `elPick(voc,p,how[,L])` (ao lado do `compatFor`, com o `elemList`,
  que passou para lá) = a regra do 'Ataca com' do `setupHTML` (o elemento citado no how do TibiaPal que rende mais, se ficar a 10
  pontos ou menos do melhor principal; senão o principal); devolve a linha do `elemList` ({x,v,main,imm,heal,low}). O `huntSet` do
  monk põe `mbond` = `elPick('monk', zona, how).x` numa cópia da personagem (nunca gravado) quando há uma arma fist dessa ligação até
  ao nível, e o `slotFits` só deixa essa ligação: os 3 sets e o 'Guardar nos meus sets' batem com o Setup; cada set do monk mostra
  'Arma: … · ligação … · as criaturas levam N%' (`.hset-wb`). O BiS do Início não tem eff nem mbond (fica igual).
  `itemKind(it)` (`IKIND`) = tipo do item para o jogador: Espada, Machado, Maça, Arco, Besta, Arremesso, Wand, Rod ('wand' só de
  druid = Rod), 'Wand / rod', Arma de monk; Escudo, Livro, Aljava; os outros slots = SLOTNAME. Usado no look, na página do item, no
  inventário, no #pathTable, nos imbuements, na lista de itens e no `.hs-sl`. `ELN`/`IMMN`: lifedrain = 'dreno de vida', manadrain =
  'dreno de mana' (o 'roubo de vida' dos jogadores é o life leech). `nfdec(n)` = número pt-PT com até 2 casas ('0,2 vida/0,7 mana
  por s'); velocidade com o sinal certo ('velocidade -5'). O `hsLookup` já não muda o `c.wtype` do knight: a escolha manual fica e o
  'Automático' segue o skill dos highscores pelo `knightWType`. Scripts que correm o `huntSet` em node (auditorias) precisam também
  do bloco `const HOWEL` … `/* tipos de criatura` (huntEls, compatFor, elemList, elPick) para o monk.
- Pesquisa global: `gsOpen()` abre a lista que desce da barra (`#gsPop`); índice = `gsIndex()` (do G: hunts, quests, criaturas, itens, loot, charms, imbuements) + `data/search.json` (gerado por `python -I C:\xampp\_tools\build_search.py` — volta a correr sempre que mudares ficheiros de dados). Resultados `[data-gs="cat:key"]`.
  r6-t1: as hunts entram no `gsIndex` com o `place` das linhas de G.hunts (nomes do TibiaPal, ex. 'Bulltaur Lair') e o `wn` como sinónimos
  (`h.al`); quando só o sinónimo bate, o `gsRow` acrescenta ' · também: <nome>' ao subtítulo.
- Páginas internas novas: rotas `#feitico/<slug>`, `#npc/<slug>`, `#conquista/<slug>`, `#montaria/<slug>`, `#outfit/<slug>` → `openWiki(kind,slug)` desenha em `#wikiPage` (painel `wiki2`) com `WKR.feitico/npc/conquista/montaria/outfit`; `wkHref(kind,nome)` dá o link. Listas no menu Wiki (com filtros, 120 cartões `.wcard` de cada vez): `#feiticos` → `renderSpellList()` (estado `ST.ui.spl`), `#npcs` → `renderNpcList()` (`ST.ui.npl`; vende/compra/ensina/viagens calculados uma vez em `WLS.np`; só aí carrega items.json), `#colecoes` → `renderColList()` (`ST.ui.col`, separadores conquistas/montarias/outfits via `tabsUI`, `wlColTab(k)`). `navOf(p)` dá o item do menu ativo (item→itens, criatura→criaturas, wiki2→feiticos/npcs/colecoes pelo hash); `secOf` e `renderNav` usam-no. Quests só da TibiaWiki: `openQuestW(nome)`.
- Links internos para NPCs e feitiços: `elink(kind,nome[,inner])` (kind `npc`|`feitico`; nome pode ser lista de candidatos), `elinkKey`, `elinkTxt(texto)` (liga NPCs citados em frases); índice `LINKX` montado por `linkIdxLoad()` (npcs.json + spells.json). Nunca dentro de `<button>` ou de outro link.
- Helpers: `$`, `esc`, `nf` (números pt-PT), `gp`, `fmt` (r5-t3: abaixo de 1000 mostra o número inteiro; a partir de 999 500 passa a kk), `fold` (sem acentos), `slug`, `cap1`, `spr(it)`, `sprOr`, `itemSpr(nome)`, `crSpr(k,size)`, `npcSpr`, `chip(el)`, `ELN` (nomes PT dos elementos), `SKN`, `SLOTNAME`, `DOLL`, `IC` (ícones SVG), `VI(voc)`.
- Modern: tudo sob `html[data-ui="modern"]`; motor `md*` (mdStart, mdPanel, mdPage, mdHero, mdCount, mdVT, mdTipHide...). `title` vira tooltip `.md-tip` no Modern.
  Títulos (r4-t4): `mdSplit(h2)` parte por palavras — cada palavra num `span.chw` (inline-block) com as letras `.ch` (`--i` = ordem
  na cascata) e o espaço num `.ch.chs` inline, por isso o título só muda de linha entre palavras; nada depende de `.ch` ser filho do h2.
  `.sr-only` = texto só para leitores de ecrã (ex.: ' · risco médio' e ': ' depois da categoria nos cartões de hunt, cujas bolinhas
  têm aria-hidden). Feitiços sem sprite em spells.png: `SPG` {nome em minúsculas: path SVG 24×24} → `sicon` desenha `.si.fb.sg` com
  o glifo (Modern) e as iniciais em `<b class="ini">` (Original); `spIdx` tenta o nome exato, depois a 1.ª alternativa ('a / b') e
  o nome sem ' up'/' down'. Barra das Hotkeys: `.hb-wrap` com setas `.hb-nav` (só Modern; `hbNavSync()` marca `.more-l`/`.more-r`).

## Regras de código (aprendidas a custo)
1. **Nomes únicos.** Antes de criar uma função/const global no IIFE, procura se o nome já existe (`grep -n "function NOME(\|const NOME\b\|let NOME\b"`). Duas `function x` = a última ganha e parte a outra (aconteceu com `lookHTML`).
2. **Ordem de arranque.** A primeira linha do IIFE é `"use strict";` — nada vai antes dela (uma diretiva só vale como 1.ª instrução; com ela,
   `x = 1` sem declaração dá erro em vez de criar uma global). A seguir vem o `const G` (com try/catch). O arranque (`renderAll(); bootSync(); route(); setUI(...)`) está no FIM do script. Código de topo que corre antes disso não pode usar `const` definidas mais abaixo (TDZ). Funções chamadas no arranque devem ser `function` declaradas.
3. **Os dois modos.** O Original é o design antigo: muda o mínimo e só para corrigir/organizar. O Modern tem CSS próprio, sempre com `html[data-ui="modern"]` à frente e atenção à especificidade (ex.: `.btn{position:relative}` do Modern ganha a regras simples).
4. **Telemóvel.** Testa sempre a 375 px: nada a sair para o lado (sem scroll horizontal), toques ≥ 44 px, `prefers-reduced-motion` respeitado.
   Grelhas de cartões com `minmax(min(Npx,100%),1fr)` (cabem a 320 px). Campos de texto, listas e áreas de texto ficam com 16 px em
   ecrãs de toque (regra `@media (pointer:coarse)` no fim do CSS): abaixo disso o iPhone faz zoom à página.
   **Letra e contraste (r8).** Escala de letra sem meios píxeis e nada abaixo de 12 px: 12, 13, 14, 15, 16, 17, 18, 20, 22, 24, 26,
   28, 30, 32, 36, 40 (o Questski também; exceção: o texto dentro do escudo de nível `.lvl-shield small`). Texto com contraste ≥ 4,5
   (≥ 3 a partir de 24 px): no tema claro `--holy` #7E630C, `--gold`/`--paladin` #7D5D0A, `--accent` #26693C; não esbater texto com
   `opacity` (esbate-se o ícone). Toque: o bloco `@media (pointer:coarse)` do fim do CSS dá 44 px aos botões pequenos e uma área de
   44 px (`::after`) aos links soltos; uma regra nova com `min-height` menor precisa de lá entrar com a mesma especificidade.
   **Modern no toque (r9).** Em `(hover:none) and (pointer:coarse)` o fundo fica parado e leve (sem canvas `#mdFx`, grão, dragão,
   runas, estrelas cadentes nem paralaxe; aurora sem blur), o topo e a barra de baixo opacos sem `backdrop-filter` e os `.hc`/`.wcard`
   sem `will-change`/3D: tudo junto esgotava a memória gráfica do telemóvel e os cartões piscavam. `MD_LITE` (JS) não arranca o canvas.
   Não voltar a pôr efeitos contínuos, blur ou uma camada de GPU por cartão no toque. O desktop não muda.
5. **Sem links externos** em conteúdo (só texto de crédito às fontes, sem `<a href="http...">`). Tudo o que é item/criatura/NPC/feitiço deve abrir uma página ou painel interno.
6. **Texto** em PT-PT, curto e claro, sem jargão técnico para o jogador. Nunca mostres nomes de jogadores vindos do Hunt Analyser.
7. **Não mexas** na configuração do Apache, do Windows, firewall ou serviços. Não instales pacotes nem executes código de terceiros descarregado.
8. **Edições ao index.html** por scripts Python com substituições ancoradas (`assert s.count(antigo)==1`), escrita em UTF-8 com `newline=''`.
   Os scripts que gravam o G usam `save_G` (ou `put_G`) de `gjson.py`, nunca `json.dumps` à mão. Depois:
   `node --check` do JS extraído (entre `'<script>\n(function(){'` e o `'</script>'` seguinte), `python -I gjson.py <raiz> --check` e o teste `smoke.mjs`.

## Testar sem o browser da sessão
`node C:\xampp\_tools\smoke.mjs --url http://localhost/<pasta>/ --hash inicio --mode modern --w 1440 --h 900 --shot C:\xampp\_work\x.png --eval "js"`
- Cria 5 personagens de teste (sorcerer 570 ativa por omissão; `--voc knight|paladin|druid|monk` muda a ativa), já "sincronizadas agora" (`syncedAt` e `hs.at`
  numéricos), por isso a página não faz pedidos ao TibiaData. Corre a página e devolve JSON com `errors` (exceções/erros de consola — deve ser `[]`), `warnings`,
  `eval`, `hscroll`, `hscrollInner`, `dir` (pasta do perfil) e grava a captura (lê-a com a ferramenta Read; se não a conseguir gravar, o erro vem em `errors` e o JSON sai na mesma).
  Código de saída: 0 sem erros, 1 com erros, 2 falha do teste (browser, tempo-limite de 60 s, disco cheio).
- `hscroll` (true = a página sai para o lado, é um defeito) compara a largura do documento com a largura pedida (`--w`), porque no telemóvel emulado o `innerWidth`
  cresce com o conteúdo (o teste antigo dava false com a página a sair). `hscrollInner` (até 10, deve ser `[]`) diz onde: primeiro os culpados `pai>filho`
  (o primeiro elemento que passa da largura com o pai ainda dentro, ex. `div.tablewrap>table`), depois as caixas com scroll horizontal próprio que não são de
  propósito (não conta `.seg.scroll`, `.tabs`, `.chars`, `.gsp-cats`, `.eqtabs`, `.settabs`, `.sltabs`, `.hotbar`/`#hotbar`, `.scroll-x`, `.tablewrap`).
- `--w 375 --h 812` = telemóvel (toque emulado). `--mode original` para o design antigo. `--full` captura a página inteira. `--wait 3500` se precisares que as contagens animadas acabem.
- `--eval` aceita código com `return` (corre dentro de uma função async), ex.: `--eval "document.querySelector('#picks [data-hunt]').click(); await new Promise(r=>setTimeout(r,800)); return document.querySelector('#sheet').innerText.slice(0,500)"`.
- Limpeza automática: cada teste usa `%TEMP%\grim-smoke-XXXXXX` (o nome vem em `dir`) com um `owner.pid`. No fim fecha o browser (Browser.close pelo CDP e depois
  os `msedge`/`chrome` com o nome da pasta na linha de comando) e apaga a pasta. No arranque corre o `reap.ps1` que está ao lado do smoke.mjs (`C:\xampp\_tools\reap.ps1`, ou `_dev/reap.ps1` num clone): fecha os browsers de testes mortos
  (o dono já não é um node vivo, ex. teste cortado à força) e apaga as pastas mortas sem browser com mais de 15 min (sem `owner.pid`, só conta como morta com mais
  de 15 min). É a única regra de limpeza do reap.ps1 (uma só passagem de `Remove-Item -LiteralPath`, dentro do `-Budget`).
  Nunca toca em testes a correr, por isso podes correr vários smokes em paralelo. Não é preciso limpar à mão; se quiseres: `powershell -NoProfile -ExecutionPolicy Bypass -File C:\xampp\_tools\reap.ps1`.
- Disco: com menos de 1 GB livre o smoke não abre o browser e sai com código 2 (`errors: ['disco quase cheio (N MB livres)']`); com menos de 2 GB avisa em
  `warnings` (`pouco espaço em disco`). Liberta espaço antes de continuar: com o disco cheio o site público também falha (cache do `api/market.php`, logs).
- Pasta de ensaio (só local): `C:\xampp\htdocs\_grimorio_staging\` → `http://localhost/_grimorio_staging/`.

## Wheel desenhada, páginas de item/criatura e a junção com o Questski (outubro de 2026)

**Wheel (`data/wheel.json`, `_dev/build_wheel.py`).** 36 fatias numa grelha 6×6 lida por linhas, na ordem do enum
`WheelSlots_t` do Canary e dos 36 primeiros bytes do código de exportação do jogo (letra da vocação + `0` + deflate cru
em base64url sem `=`; 12 bytes de gemas a seguir, 255 = vazio). Verde em cima à esquerda, vermelho em cima à direita, azul
em baixo à esquerda, roxo em baixo à direita; por domínio: 50 no centro, 2 × 75, 3 × 100, 2 × 150 e a de 200 a toda a volta
por fora. `slots[i] = [domínio, máximo, dedicação, convicção]` (dedicação hp/mp/cap/mit/hpmp; convicção vr, skill, mleech,
lleech, `sp:A`–`sp:E` = feitiço aumentado do grupo, `inst:G200`/`inst:P200`), `adj[i]` = fatias das quais pelo menos uma tem
de estar cheia (as de 50 não pedem nenhuma), `voc[v]` = vida/mana/cap por ponto, nomes dos feitiços por grupo, perks das de
200 e revelação de cada domínio; `aug`/`perk`/`revd` = textos pt-PT; `b[código]` = os 36 pontos de cada build do G.wheel e
`g[código]` = as gemas (só as que as têm). O build valida tudo contra as 70 builds (vida, mana, cap, mitigação 0,075 %/ponto,
convicções com grau, revelações e ligações) e deve dizer "builds com diferenças: 0".
JS (antes do `/* ---------- equipment`): `whLoad`, `whGeo(i)` (anel e ângulos), `whSum(voc,pts)`, `whSVG(voc,pts,{size,edit,budget})`,
`whSlotTxt` (dica), `whPanelHTML` (dedicação, convicção, vessels/gemas, revelação), `whGemMods`, `whPick(voc,pts,pid,risco)` (build
para uma hunt: a variante holy/físico ou energia/fogo/morte que rende mais nas criaturas), `hwheelHTML(pid,risco)` (bloco "Wheel,
gemas e charms" da ficha da hunt, com `charmPicks`/`hCharmsHTML`), `renderWheelX` (página da Wheel, editável: `WED`, `whEdit`,
`whPrune`, `whEncode`/`whDecode` com Compression/DecompressionStream 'deflate-raw').

**Páginas de item e de criatura.** `specBar([[rótulo,html]])` = faixa de números no topo (ignora os que faltam); `.pg2` = duas
colunas; `.pt` = tabela simples (ataques, loot, drops, preço, forge); `.rs`/`.rs-c` = fraquezas e resistências, uma célula por
elemento; `cpEn` traduz os textos dos ataques que vêm em inglês da TibiaWiki.

**Questski (`quests/`, fonte em `_questski/`).** App própria (vanilla JS, rotas `#/…`, estado `tq-*` no localStorage). Partilhado:
- `shared/sites.css`: o switch `.sitesw` (no `header.bar` do Grimório e no `header.topbar` do Questski) e a transição
  `@view-transition` entre os dois sites.
- `data/guias.json` (`_dev/build_guias.py`): `g` = guias `[slug, nome, nível mín., nível rec., premium, categoria, região, passos]`,
  `q2s` = id da quest do G.quests → slug, `n2s` = nome normalizado → slug (a mesma normalização em `gKey()` no Grimório).
- Grimório: `guiasLoad`, `guiaOf(id,nome)`, `guiaHref`, `guiaBtn`, `guiaPair` (depois de `qName`); categoria `g` na pesquisa
  (`GSC.g`); item de menu `["guias","Guias de quests","quests/"]` (o 3.º elemento = link, ver `isPanel()`); cartão do início
  `renderGuiasHome`/`guiasFor` (lê também o progresso do Questski, `tq-progress`). Um `storage` listener adota o estado novo
  quando o Questski, noutro separador, marca quests.
- Questski: `quests/js/ponte.js` (`window.QPonte`: `char()`, `grimDone(slug)`, `setGrimDone(slug,v)`, `grimHref(tipo,título)`,
  lê `grimorio-tibia-v4`, `../data/guias.json` e `../data/search.json`); em `app.js`, `QP` usa-o no `isDone`, no "Marcar como
  concluída", no filtro "O meu nível" (`S.filters.lvlChar` = nível vem da personagem) e na wiki ("Ver no Grimório" e o switch).
- O Original/Modern é o mesmo nos dois (`grimorio-ui`); o Modern do Questski está em `quests/css/modern.css`.
- Janela da quest (r11): `initQuests` usa o guia do Questski quando há (`guiaOf` → `guiaQ(slug)` lê `quests/data/quests/<slug>.json`):
  `guiaCardHTML` com o lore (`legend_pt`) em destaque (`.qlore`), requisitos, recompensas fechadas e, num `details.qguide` sempre fechado
  ('tem spoilers'), o resumo e o passo a passo (`qmd` converte `{npc:}`, `{item:}`, `{creature:}`, `{spell:}`, `{key:}`, `**`/`*`). O título
  leva ao Questski. Sem guia, fica o `questCardHTML`. No bloco Acesso das hunts, `questReqTag` torna clicável cada 'Quest: …'.
  `build_guias.py`: os nomes principais dos guias ganham aos `aka` (o 'The New Frontier' ia para o Tomes of Knowledge).
- Ferramentas do Questski: `_questski/tools/*.py` escrevem em `../quests/` (antes `site/`); `tools/cache/` não vai para o Git.
