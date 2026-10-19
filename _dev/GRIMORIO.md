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
- Sprites: allitems.png (itens, 32×32, índice `ix`), creatures.png, npcs.png (+ npcs2.png), spells.png (+ spells2.png), loot.png, huntmaps.png,
  mounts.png/outfits.png (64×64), maps/floor-XX-map.png (mapa; origem 31744,30976). creatures.png e npcs2.png têm células de 64 px em 32 colunas
  (`G.cr[k]`, `ix2` em npcs.json; `npcSpr(n,ph)` procura em G.np e depois em npcs2.png; com `ph` devolve o ícone de espaço fixo `.ph-ic`).
  Quando regeneras um PNG de sprites, muda o ?v= em todos os URLs desse PNG (hoje `?v=20261018r2`; huntmaps.png tem o seu próprio).
- `api/market.php?world=<Mundo>`: preços do Market por mundo (proxy com cache de 6 h do TibiaMarket). Resposta: `{world,updated,fetched,stale,items:{"<id>":[sell_offer,buy_offer,month_avg_sell,month_avg_buy,day_avg_sell,day_avg_buy,month_sold,month_bought]}}`.
- `.htaccess`: HTML sem cache, JSON permitido (o .htaccess da raiz é de um MyAAC antigo), `RewriteEngine On`, deflate, e 404 a tudo o que
  começa por `.git` (a pasta pública é um clone do repositório; `RewriteRule` e, sem mod_rewrite, `RedirectMatch`). `_dev/` tem o seu `.htaccess` (403, também para os `*.json`,
  que o `<FilesMatch "\.json$">` da raiz deixaria ler).
  `.editorconfig`: UTF-8 e fins de linha LF (o `.gitattributes` tem `* -text`: o Git guarda os ficheiros tal e qual).
- Backups: `C:\xampp\_backups\`. Ferramentas: `C:\xampp\_tools\` (este guia, `smoke.mjs`, `gjson.py`, `build_search.py`, `apply_hunt_fixes.py`,
  `build_huntmaps.py`, `client_outfits.py` = desenha outfits/objetos a partir do cliente Tibia instalado, só leitura) e `C:\xampp\_work\fix_hunt_mons.py`;
  as cópias no `_dev/` do site são iguais (copia-as quando as mudares). Corridas a partir de `_dev/` sem raiz, usam a pasta-mãe (o clone); os
  registos (`apply.log`, `fix_hunt_mons.log`) vão para `%GRIM_WORK%` ou para a pasta temporária. O `apply_hunt_fixes.py` volta a pôr os valores
  dos fix-*.json (notas, acessos…) por cima do que mudou depois: corre-o primeiro com `--dry` e lê o registo. Trabalho temporário: `C:\xampp\_work\`.

## Dados principais em `G`
- `G.items`: equipamento `{id (id do cliente = id do Market), n, s (slot: helmet|amulet|armor|legs|boots|ring|weapon|shield|extra), l (nível), ix, v (vocações: "k","p","s","d","m" juntas, ex. "ds"), arm, def, edef, atk, wel [el,val], wd [el,min,max], hit, sk {ml, ml_fire, sword, dist, fist, shield...}, ab {elemento:%}, spd, rg [vida,mana], is (slots de imbuement), it (imbuements aceites), chg, dur, h2 (duas mãos), b (tipo de arma), ex [texto], mn (mantra), ns (sem stats), tp}`.
- `G.mon[k]` = [nome, hp, xp, ix, imunidades, resistências {el:%}, loot [[ix,nome,%,valor]], boss]. Resistências: `G.mon[k][5] = 100 − el` da TibiaWiki (`el` = % de dano que a criatura leva, em data/creatures.json) nos 7 elementos; 100 = imune, acima de 100 = o elemento cura a criatura (ex.: fogo 200 na Ravenous Lava Lurker). `G.places[pid].eff` = média de 100 − resistência nas criaturas de `p.mons` (e `eff.min` = o mínimo), a fórmula de `eff()` em apply_hunt_fixes.py. `G.mc`/`G.mcn`: classe do Bestiary.
- `G.places[pid]` = {n, mons, q (quest de acesso), d (risco 1–3), eff {el:% de dano}, team, w (da TibiaWiki), xs, ls, city, acc, note}.
- `G.hunts[voc]` = linhas {c (pid), place, l, xp, lo, how, f (preenchida), w, v (nível verificado)}. `how`: nos mages é a rotação do TibiaPal; no knight, no paladin e no monk é o tipo de arma ou munição do TibiaPal (coluna 5, ex. "Fire, Ice", "Diamond Arrows, Ethereal"), lido por `huntEls(how)` (elementos citados, por palavra inteira), `compatFor(voc,place,how)` (melhor elemento entre vd.els e a arma/munição elemental ou, nos druids e sorcerers, as runas citadas na rotação — r4-t3; `via` = o melhor vem da arma, da munição ou das runas; `imm`, `heal`) e `setupHTML` (linha "Ataca com" e linha "Arma"/"Munição"/"Rotação"); o `elemHTML` põe o "usa este" no elemento que o setupHTML escolheu (`ELPICK`, por place e vocação). Regra: linhas f: l nunca abaixo do nível real mais baixo de outra vocação, exceto as linhas com v:1 (nível confirmado na TibiaWiki ou na verificação online). `G.pm[pid].h` = [[criatura, quantidade]] do mapa.
- `G.hv[pid]` = {t (transporte), rq (requisitos), st (passos), v ("ok" | "fix" | outro)}: o bloco "Acesso" do separador "Como chegar" (`vRoute`; etiqueta confirmado/revisto/por confirmar).
  Só texto para o jogador: as notas da verificação (n, ed, mf, e, s, ok e o texto original de rq/st antes da limpeza) ficam em `_dev/hv_notas.json`;
  um conselho para o jogador (boss, perigo, atalho) vai para `G.places[pid].note` ("Notas").
- `G.hm[pid]` coordenadas; `G.voc[voc]` (n, promo, els, pots, charms, imbs, allsp = feitiços); `G.quests`, `G.charms`, `G.wheel`, `G.equip` (TibiaPal), `G.vr`, `G.ha`.

## Estado e funções úteis (dentro do IIFE)
- `ST` (localStorage `grimorio-tibia-v4`): `{v:4, active, chars:[...], custom:[], ui:{p, ...}}`; `C()` = personagem ativa; `save()`; `renderAll()`.
- Personagem: `{id,name,voc,level,pct,ml,skill,world,tib,hs,done,charms,imb,owned{id:true},sets:[{id,name,mode,prot,slots{slot:{id,imb}}}],aset,hset:"bis"|"mine"}`.
- Navegação: `SECS` (secções e subpáginas), `go(p)` (fecha o painel e põe o hash igual à página com replaceState), rotas por hash `#item/<slug>`, `#criatura/<slug>` em `route()`
  (decode com try, secções em minúsculas, `?…` ignorado, hash desconhecido volta ao da página; `hasKey(o,k)` contra chaves do Object.prototype). Histórico: cada entrada
  tem `history.state.gd` (profundidade; `NAVD` no JS); usa sempre `history.replaceState(history.state, …)`, nunca `null`. '← Voltar' (`[data-back]`) só faz history.back() se NAVD>0.
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
  munição do how; algumas poções e munições ainda não estão em items.json e ficam sem preço). `lootQty(a)`, `lootPerKill(k,CR,w)` →
  `{v (gp por kill), top:[[nome,gp,pct]], miss, none}` (k = chave de creatures.json), `lootAgg(pid,CR,w)` e `gpPerXp(pid,CR,w)` = gp por
  1000 XP (criaturas de `G.places[pid].mons` sem bosses, quantidade de `G.pm[pid].h`); loot por hora ≈ XP/h × gpPerXp / 1000.
  Separador 'Loot e lucro' da ficha: `<div class="lp" data-lootp=pid data-xp data-lo data-lsrc data-how [data-g data-sb]>` preenchido por
  `initLoot(root)` (chamado no clique dos separadores, ao lado de `initRoutes`/`initQuests`) → `lpHTML`; calculadora só na ficha solo
  (`[data-hcalc]`, `lpCalcRun`/`lpCalcSave`), gravada em `c.calc[pid] = {hrs, q:{chave:[quantidade, preço só se mudado, nome]}, loot (só
  se mudado), fee, t}` (no máximo 50 hunts). Página do item: `[data-mkt]` = ids separados por vírgula (`mktFill` escreve o valor e o
  `<span>` seguinte), `#itemAdv` reescrito com `itemAdvHTML` quando o Market chega. Look: `lookShow` redesenha quando cada dado chega.
- Hunts: `huntRows(voc, L)` (L = nível máximo da variante do TibiaPal; sem L = nível da personagem + 5; nível/XP/lucro da mesma variante), `huntCard(h)`, `huntSheet(h)`, `setupHTML`, `hsetsHTML(pid)` (sets ofensivo/consistente/defensivo), `huntProfile(pid)` (dano da hunt).
  Magos (r4-t3): o `HOWEL` conhece as runas (gfb, sd, avalanche, stoneshower, thunderstorm), Forked Glacier/Thorns e Shatterstorm (físico);
  o `compatFor` e o `setupHTML` contam o elemento das runas citadas na rotação ('Ataca com … com runas de …'). No `huntRows`, uma linha
  com XP medida pelo TibiaPal para a vocação (sem f nem w) nunca fica 'bad' (passa a 'meh', '(o TibiaPal mediu esta hunt…)').
  Charms: `G.charms` tem os 25 charms `{n,t,c,d,f}`; `f` = 'el:<elemento>' (Freeze, Zap, Wound, Poison, Enflame, Divine Wrath, Curse),
  'hp5' (Overpower), 'mana25' (Overflux) ou null. `charmFor(c,k)` → `[{k,dmg}]` dano por ativação na criatura k de `G.mon` (TibiaWiki):
  elementais e Wound = min(5 % da vida da criatura, 2 × nível) × dano %; Overpower = min(5 % de `hpOf(c)`, 8 % da vida) × físico %;
  Overflux = min(2,5 % de `manaOf(c)`, 8 % da vida) × físico % (todas as vocações; ≤ 0 fica de fora). A linha 'Charm' do setupHTML
  (`suCharm`) dá um charm diferente a cada uma das 3 criaturas principais (`G.pm[pid].h` ∩ `place.mons`, sem bosses, por xp × n), porque
  no jogo um charm só pode estar numa criatura de cada vez; ' ou X' a menos de 5 %; sem criaturas, a média da zona (`CHARM_EL`, Wound se
  faltar). Setup: pares `<div class="su su-el|rot|charm|safe|sup">` com `.su-ic` (mosaicos só no Modern; no Original `.su` é
  display:contents), `suRot` (chips, feitiços e munição com link, 'ver rotação ›') e a linha 'Supplies' (`suSup` com `supRows` e
  `buyOf`; o id `su-sup-N` é preenchido depois de items.json, do Market e do índice de links).
- Equipamento: `scoreItem(c,it,mode,prot)` (mode combat|speed|off|bal|def; prot = elemento ou perfil {el:peso}), `ranked`, `pickSet`, `bisSet`, `setTotals`,
  `setSumHTML`, `renderBis` (painel inicial), `renderEquip`/`renderSlot`/`renderInventory`, `pickOpen` (botão direito), `itemLookHTML` + `[data-look="<id>"]` (look ao passar por cima).
  Sets automáticos (r4-t5): paladino com a arma em 'Automático' (`c.wtype` vazio): o `pickSet` usa arco a partir do nível 100
  (abaixo, lanças e estrelas; com o filtro 'só os que tenho' e nenhum arco, todos os tipos); na ficha, `huntWType(c,pid)` dá o tipo
  da munição do TibiaPal (`how` da linha de G.hunts.paladin: bolt → besta, arrow → arco, spear/star → arremesso) ao `huntSet`, que
  faz os 3 sets e o 'Guardar nos meus sets'. Munição: `AMMO` {bow|crossbow: [[nível, ataque]]} das munições sem elemento (TibiaWiki)
  e `ammoAtk(b,L)`; o `scoreItem` soma-a ao atk dos arcos e das bestas (o `setSumHTML` mostra 'Ataque N + munição'). Durações:
  anéis e amuletos com menos de 15 min ficam fora do `pickSet` (no botão direito continuam, com 'dura N min'); no `scoreItem` um
  item com dur pesa ×0,35 (< 15 min), ×0,6 (< 30), ×0,8 (< 60) ou ×0,9. Mantra do monk: `it.mn` × 2,5 (× 1,5 no ofensivo, × 0,7
  no defensivo, × 0,5 em velocidade). Escudos de knight nos magos: defesa × 0,1. Proteção de afogamento só conta com 20 %+ de
  dano drown na hunt. Mão esquerda: `slotLab(c,k)` ('Escudo / aljava', 'Livro / escudo', 'Escudo') no #bis, no #doll e nos sets
  da ficha; o `SLOTNAME`/`DOLL` ficam iguais (o renderSlot e o pickOpen usam-nos). No botão direito (`pickList`), o paladino
  em 'Automático' a partir do 100 vê os arcos primeiro e as bestas e o arremesso num grupo à parte (`.pk-g`).
- Pesquisa global: `gsOpen()` abre a lista que desce da barra (`#gsPop`); índice = `gsIndex()` (do G: hunts, quests, criaturas, itens, loot, charms, imbuements) + `data/search.json` (gerado por `python -I C:\xampp\_tools\build_search.py` — volta a correr sempre que mudares ficheiros de dados). Resultados `[data-gs="cat:key"]`.
- Páginas internas novas: rotas `#feitico/<slug>`, `#npc/<slug>`, `#conquista/<slug>`, `#montaria/<slug>`, `#outfit/<slug>` → `openWiki(kind,slug)` desenha em `#wikiPage` (painel `wiki2`) com `WKR.feitico/npc/conquista/montaria/outfit`; `wkHref(kind,nome)` dá o link. Listas no menu Wiki (com filtros, 120 cartões `.wcard` de cada vez): `#feiticos` → `renderSpellList()` (estado `ST.ui.spl`), `#npcs` → `renderNpcList()` (`ST.ui.npl`; vende/compra/ensina/viagens calculados uma vez em `WLS.np`; só aí carrega items.json), `#colecoes` → `renderColList()` (`ST.ui.col`, separadores conquistas/montarias/outfits via `tabsUI`, `wlColTab(k)`). `navOf(p)` dá o item do menu ativo (item→itens, criatura→criaturas, wiki2→feiticos/npcs/colecoes pelo hash); `secOf` e `renderNav` usam-no. Quests só da TibiaWiki: `openQuestW(nome)`.
- Links internos para NPCs e feitiços: `elink(kind,nome[,inner])` (kind `npc`|`feitico`; nome pode ser lista de candidatos), `elinkKey`, `elinkTxt(texto)` (liga NPCs citados em frases); índice `LINKX` montado por `linkIdxLoad()` (npcs.json + spells.json). Nunca dentro de `<button>` ou de outro link.
- Helpers: `$`, `esc`, `nf` (números pt-PT), `gp`, `fmt`, `fold` (sem acentos), `slug`, `cap1`, `spr(it)`, `sprOr`, `itemSpr(nome)`, `crSpr(k,size)`, `npcSpr`, `chip(el)`, `ELN` (nomes PT dos elementos), `SKN`, `SLOTNAME`, `DOLL`, `IC` (ícones SVG), `VI(voc)`.
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
