# Grimório de Tibia — guia técnico para quem mexe no site

Site de fãs de Tibia, em **português de Portugal (PT-PT)**, centrado em hunts por vocação. É uma página estática servida pelo XAMPP (Apache) em
`C:\xampp\htdocs\grimorio\` e partilhada publicamente (http://<IP>/grimorio/). O dono quer: o Grimório como fonte principal (sem links para outros
sites — páginas internas para tudo), foco em hunts SOLO (grupo só quando há 2+ jogadores selecionados), sempre por vocação, bem estruturado e ilustrado,
e um modo visual "Modern" muito trabalhado (neon, animações em tudo) ao lado do "Original".

## Ficheiros
- `index.html` (~2 MB): TUDO — CSS, HTML, JSON embebido `G` e a app JS dentro de `<script>\n(function(){ ... })();</script>`.
- `data/*.json` (carregados quando precisos com `dload(n)`/`dsafe(n)` → `data/<n>.json`): items.json (por nome em minúsculas), creatures.json,
  npcs.json, quests.json, spawns.json, npcpos.json, crdmg.json (dano que cada criatura faz), e os novos spells.json, achievements.json, mounts.json,
  outfits.json, search.json (índice global de pesquisa) — ver o formato no próprio ficheiro.
- Sprites: allitems.png (itens, 32×32, índice `ix`), creatures.png, npcs.png (+ npcs2.png), spells.png (+ spells2.png), loot.png, huntmaps.png,
  mounts.png/outfits.png (64×64), maps/floor-XX-map.png (mapa; origem 31744,30976). creatures.png e npcs2.png têm células de 64 px em 32 colunas
  (`G.cr[k]`, `ix2` em npcs.json; `npcSpr(n,ph)` procura em G.np e depois em npcs2.png; com `ph` devolve o ícone de espaço fixo `.ph-ic`).
  Quando regeneras um PNG de sprites, muda o ?v= em todos os URLs desse PNG (hoje `?v=20261018r2`; huntmaps.png tem o seu próprio).
- `api/market.php?world=<Mundo>`: preços do Market por mundo (proxy com cache de 6 h do TibiaMarket). Resposta: `{world,updated,fetched,stale,items:{"<id>":[sell_offer,buy_offer,month_avg_sell,month_avg_buy,day_avg_sell,day_avg_buy,month_sold,month_bought]}}`.
- `.htaccess`: HTML sem cache, JSON permitido (o .htaccess da raiz é de um MyAAC antigo), `RewriteEngine On`, deflate.
- Backups: `C:\xampp\_backups\`. Ferramentas: `C:\xampp\_tools\` (este guia, `smoke.mjs`, `build_search.py`, `client_outfits.py` = desenha outfits/objetos a partir do cliente Tibia instalado, só leitura). Trabalho temporário: `C:\xampp\_work\`.

## Dados principais em `G`
- `G.items`: equipamento `{id (id do cliente = id do Market), n, s (slot: helmet|amulet|armor|legs|boots|ring|weapon|shield|extra), l (nível), ix, v (vocações: "k","p","s","d","m" juntas, ex. "ds"), arm, def, edef, atk, wel [el,val], wd [el,min,max], hit, sk {ml, ml_fire, sword, dist, fist, shield...}, ab {elemento:%}, spd, rg [vida,mana], is (slots de imbuement), it (imbuements aceites), chg, dur, h2 (duas mãos), b (tipo de arma), ex [texto], mn (mantra), ns (sem stats), tp}`.
- `G.mon[k]` = [nome, hp, xp, ix, imunidades, resistências {el:%}, loot [[ix,nome,%,valor]], boss]. `G.mc`/`G.mcn`: classe do Bestiary.
- `G.places[pid]` = {n, mons, q (quest de acesso), d (risco 1–3), eff {el:% de dano}, team, w (da TibiaWiki), xs, ls, city, acc, note}.
- `G.hunts[voc]` = linhas {c (pid), place, l, xp, lo, how, f (preenchida), w, v (nível verificado)}. Regra: linhas f: l nunca abaixo do nível real mais baixo de outra vocação, exceto as linhas com v:1 (nível confirmado na TibiaWiki ou na verificação online). `G.pm[pid].h` = [[criatura, quantidade]] do mapa.
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
- Hunts: `huntRows(voc, L)` (L = nível máximo da variante do TibiaPal; sem L = nível da personagem + 5; nível/XP/lucro da mesma variante), `huntCard(h)`, `huntSheet(h)`, `setupHTML`, `hsetsHTML(pid)` (sets ofensivo/consistente/defensivo), `huntProfile(pid)` (dano da hunt).
- Equipamento: `scoreItem(c,it,mode,prot)` (mode combat|speed|off|bal|def; prot = elemento ou perfil {el:peso}), `ranked`, `pickSet`, `bisSet`, `setTotals`,
  `setSumHTML`, `renderBis` (painel inicial), `renderEquip`/`renderSlot`/`renderInventory`, `pickOpen` (botão direito), `itemLookHTML` + `[data-look="<id>"]` (look ao passar por cima).
- Pesquisa global: `gsOpen()` abre a lista que desce da barra (`#gsPop`); índice = `gsIndex()` (do G: hunts, quests, criaturas, itens, loot, charms, imbuements) + `data/search.json` (gerado por `python -I C:\xampp\_tools\build_search.py` — volta a correr sempre que mudares ficheiros de dados). Resultados `[data-gs="cat:key"]`.
- Páginas internas novas: rotas `#feitico/<slug>`, `#npc/<slug>`, `#conquista/<slug>`, `#montaria/<slug>`, `#outfit/<slug>` → `openWiki(kind,slug)` desenha em `#wikiPage` (painel `wiki2`) com `WKR.feitico/npc/conquista/montaria/outfit`; `wkHref(kind,nome)` dá o link. Listas no menu Wiki (com filtros, 120 cartões `.wcard` de cada vez): `#feiticos` → `renderSpellList()` (estado `ST.ui.spl`), `#npcs` → `renderNpcList()` (`ST.ui.npl`; vende/compra/ensina/viagens calculados uma vez em `WLS.np`; só aí carrega items.json), `#colecoes` → `renderColList()` (`ST.ui.col`, separadores conquistas/montarias/outfits via `tabsUI`, `wlColTab(k)`). `navOf(p)` dá o item do menu ativo (item→itens, criatura→criaturas, wiki2→feiticos/npcs/colecoes pelo hash); `secOf` e `renderNav` usam-no. Quests só da TibiaWiki: `openQuestW(nome)`.
- Links internos para NPCs e feitiços: `elink(kind,nome[,inner])` (kind `npc`|`feitico`; nome pode ser lista de candidatos), `elinkKey`, `elinkTxt(texto)` (liga NPCs citados em frases); índice `LINKX` montado por `linkIdxLoad()` (npcs.json + spells.json). Nunca dentro de `<button>` ou de outro link.
- Helpers: `$`, `esc`, `nf` (números pt-PT), `gp`, `fmt`, `fold` (sem acentos), `slug`, `cap1`, `spr(it)`, `sprOr`, `itemSpr(nome)`, `crSpr(k,size)`, `npcSpr`, `chip(el)`, `ELN` (nomes PT dos elementos), `SKN`, `SLOTNAME`, `DOLL`, `IC` (ícones SVG), `VI(voc)`.
- Modern: tudo sob `html[data-ui="modern"]`; motor `md*` (mdStart, mdPanel, mdPage, mdHero, mdCount, mdVT, mdTipHide...). `title` vira tooltip `.md-tip` no Modern.

## Regras de código (aprendidas a custo)
1. **Nomes únicos.** Antes de criar uma função/const global no IIFE, procura se o nome já existe (`grep -n "function NOME(\|const NOME\b\|let NOME\b"`). Duas `function x` = a última ganha e parte a outra (aconteceu com `lookHTML`).
2. **Ordem de arranque.** O arranque (`renderAll(); bootSync(); route(); setUI(...)`) está no FIM do script. Código de topo que corre antes disso não pode usar `const` definidas mais abaixo (TDZ). Funções chamadas no arranque devem ser `function` declaradas.
3. **Os dois modos.** O Original é o design antigo: muda o mínimo e só para corrigir/organizar. O Modern tem CSS próprio, sempre com `html[data-ui="modern"]` à frente e atenção à especificidade (ex.: `.btn{position:relative}` do Modern ganha a regras simples).
4. **Telemóvel.** Testa sempre a 375 px: nada a sair para o lado (sem scroll horizontal), toques ≥ 44 px, `prefers-reduced-motion` respeitado.
5. **Sem links externos** em conteúdo (só texto de crédito às fontes, sem `<a href="http...">`). Tudo o que é item/criatura/NPC/feitiço deve abrir uma página ou painel interno.
6. **Texto** em PT-PT, curto e claro, sem jargão técnico para o jogador. Nunca mostres nomes de jogadores vindos do Hunt Analyser.
7. **Não mexas** na configuração do Apache, do Windows, firewall ou serviços. Não instales pacotes nem executes código de terceiros descarregado.
8. **Edições ao index.html** por scripts Python com substituições ancoradas (`assert s.count(antigo)==1`), escrita em UTF-8 com `newline=''`. Depois:
   `node --check` do JS extraído (entre `'<script>\n(function(){'` e o `'</script>'` seguinte) e o teste `smoke.mjs`.

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
  os `msedge`/`chrome` com o nome da pasta na linha de comando) e apaga a pasta. No arranque corre `C:\xampp\_tools\reap.ps1`: fecha os browsers de testes mortos
  (o dono já não é um node vivo, ex. teste cortado à força) e apaga as pastas mortas sem browser com mais de 15 min (sem `owner.pid`, só conta como morta com mais
  de 15 min). É a única regra de limpeza do reap.ps1 (uma só passagem de `Remove-Item -LiteralPath`, dentro do `-Budget`).
  Nunca toca em testes a correr, por isso podes correr vários smokes em paralelo. Não é preciso limpar à mão; se quiseres: `powershell -NoProfile -ExecutionPolicy Bypass -File C:\xampp\_tools\reap.ps1`.
- Disco: com menos de 1 GB livre o smoke não abre o browser e sai com código 2 (`errors: ['disco quase cheio (N MB livres)']`); com menos de 2 GB avisa em
  `warnings` (`pouco espaço em disco`). Liberta espaço antes de continuar: com o disco cheio o site público também falha (cache do `api/market.php`, logs).
- Pasta de ensaio (só local): `C:\xampp\htdocs\_grimorio_staging\` → `http://localhost/_grimorio_staging/`.
