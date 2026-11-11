# Bosses por nível

A página **Bosses** (Hunts → Bosses) diz que bosses do Bosstiary cada personagem pode fazer no seu nível: sozinho, em equipa ou
mais tarde. Mostra também quanto dá cada um e o progresso no Bosstiary.

## Ficheiros
- `_dev/build_bosses.py` → `data/bosses.json`: os bosses das categorias Bane, Archfoe e Nemesis da TibiaWiki, um por linha.
  - Campos: classe, vida, XP, cooldown, tipo de spawn, alavanca, quest de acesso com o nível mínimo e o recomendado, sítios,
    dano máximo por turno e % de cada elemento no dano que faz.
  - `--loot` acrescenta ao `data/items.json` os itens do loot dos bosses que lá faltavam (ex.: Gold e Silver Token), para terem
    preço do NPC e do Market. Depois corre `build_search.py`.
  - `ev` (r36): `"wc"` (world change ou mini world change), `"saz"` (evento sazonal) ou `"raid"`; sem `ev` = permanente. Ver
    «Permanentes e eventos» mais abaixo. `--ev` refaz só este campo no `data/bosses.json` que está no disco (o resto fica
    igual, mesmo que a wiki de hoje dê outras posições).
- `_dev/bosses_eventos.json` (à mão): `{"<chave>": "wc" | "saz" | "raid" | null}`; tem prioridade sobre a TibiaWiki.
- `shared/bosses.js` (`window.GrimBoss`): o modelo (`judge`, `makeCurve`, Bosstiary) e os bosses do dia (`isEvent`, `cdLeft`,
  `dailyPicks`). Teste: `node _dev/bosses_test.mjs`.
- O loot e as resistências vêm do `data/creatures.json`; o valor por kill sai do `lootPerKill` do site, aos preços do mundo.

## O modelo (por boss, com a vocação e o nível)
1. **Acesso:** abaixo do nível mínimo da quest (`ql`) não entras. Nunca se recomenda abaixo do nível recomendado (`qr`), porque
   as fases e mecânicas dos bosses de quest não entram nas contas.
2. **Aguentar:** a vida efetiva tem de chegar a 2 golpes do dano máximo por turno (`md`) sozinho, ou a 1,3 em equipa.
   - Knight, paladino e monk: vida × 1,35 / 1,15 / 1,25 (defesa média aproximada).
   - Magos: vida + Magic Shield (7 × ML + 7,6 × nível + máx(300, 0,4 × nível)).
3. **Matar:** vida do boss ÷ (70% do dano por segundo de boss × o melhor multiplicador de elemento das linhas da vocação).
   - Limites sozinho: Bane 2,5 min, Archfoe 5 min, Nemesis 10 min.
   - Em equipa: 4 personagens iguais e 1,5 vezes o tempo.
4. **Falta de dados:**
   - sem vida conhecida, não há "sozinho";
   - sem dano máximo, "sozinho" só até 20 000 de vida.

O dano de boss é o `GrimRot.plan` (cenário boss, com os ataques automáticos) nos níveis `GrimBoss.ANCHORS`, com stats estimados.
A curva é escalada pelo dano real da personagem no seu nível (o ML ou skill da ficha e o equipamento: o set, ou o BiS do nível).

## Permanentes e eventos (r36)

O `build_bosses.py` dá a cada boss uma classe, por esta ordem (fica a 1.ª que existir):
1. `_dev/bosses_eventos.json`, escrito à mão;
2. `spawntype` com «Raid» → `raid`;
3. páginas das categorias «World Changes» e «Mini World Changes» (`wc`) e «Events» (`saz`) ligadas na localização ou nas
   notas do boss; as páginas que são listas não contam («World Changes», «Mini World Changes», «Raid» e as «… Events»,
   ex.: «Double Loot Events», «Rapid Respawn Events»);
4. bosses ligados nos campos `reward` e `dangers` da Infobox Quest de um world change ou mini world change (`wc`);
5. a quest do boss com `type = event` (`saz`, ex.: First Dragon Quest) ou `change`/`mwc` (`wc`).

Na dúvida fica permanente. O relatório do script acaba com «eventos: N wc, N saz, N raid; a rever: …»: um `spawntype`
«Event» sem nenhuma prova, ou um boss com duas classes (fica a 1.ª pela ordem acima). Revê-os e, se for preciso, escreve a
decisão no ficheiro à mão. Em 11/11/2026: 23 wc, 6 saz, 51 raid e 236 permanentes; a rever: Jaul («Event / Triggered»). À
mão: Arthom the Hunter, Oodok Witchmaster e The Mean Masher são `wc` (a wiki chama-lhes raid, mas só aparecem com o mini
world change); a Rotworm Queen é `raid` (o Awash só a cita como «possibly»).

## Bosses do dia (r36)

- Página `#bosses`: filtro Permanentes · Eventos · Todos (`ST.ui.bse`, Permanentes por omissão), junto ao filtro sozinho /
  em equipa / mais tarde / todos (`ST.ui.bsf`).
- Bloco «Bosses do dia» (Permanentes e Todos): `GrimBoss.dailyPicks(rows, boosted, agora)` dá até 4 bosses permanentes, que a
  personagem faz sozinha (`judge` → `solo`) e fora do cooldown, sem repetir: o boss em destaque do dia (TibiaData
  `/boostablebosses`, pelo `todayLoad` do Início; se não entrar, o bloco diz porquê: evento, não sozinho, cooldown ou fora da
  lista), o melhor lucro (`lootPerKill`), o que dá mais XP e o mais rápido (`ttk`). As linhas levam a mesma etiqueta.
- «Feito hoje» (linha, bloco e ficha): `c.bcd[chave] = quando`. Regra do cooldown, `GrimBoss.cdLeft(ts, cd, agora)`: volta em
  `ts + cd` horas; sem `cd`, no server save seguinte (10:00 de Berlim, CET ou CEST). Enquanto não volta, sai do bloco e a
  linha diz «volta às HH:MM» (hora local; a mais de 24 h, «volta a DD/MM às HH:MM»). Tocar de novo desfaz; as marcas que já
  passaram apagam-se no toque seguinte.
- Eventos: etiqueta do tipo (World change, Evento sazonal, Raid) e «visto ontem no teu mundo» quando o killstatistics do
  mundo da personagem (`kstatLoad`, nome ou plural do `kPlural`) tem `last_day_killed > 0`. Nota fixa: fica um dia atrasado,
  não há API oficial; sem mundo, pede para o escolher. Nunca se diz que um evento está ativo.

## Bosstiary (Cyclopedia, TibiaWiki)

| Categoria | Mortes Prowess / Expertise / Mastery | Pontos |
|---|---|---|
| Bane | 25 / 100 / 300 | 5 + 15 + 30 |
| Archfoe | 5 / 20 / 60 | 10 + 30 + 60 |
| Nemesis | 1 / 3 / 5 | 10 + 30 + 60 |

Bónus de loot do boss no slot:
- 25% a 0 pontos e +1% a cada 10, até 250 pontos (50%);
- depois +1% a cada 20, até 1250 pontos (100%);
- depois cada 1% pede mais 5 pontos do que o anterior (25, 30, 35…).

## Limitações

### Acessos documentados (novembro de 2026)

`python -I _dev/build_boss_access.py` gera `data/boss-access.json` a partir das
fichas de locais e guias já publicados em `quests/data/`. Correr depois de mudar
os bosses ou reconstruir o Questski; `--check` verifica se o resultado está atual.
`node _dev/boss_access_test.mjs` verifica as ligações e a regressão dos portais.

A ficha do boss carrega os acessos ao abrir: requisitos, chegada à zona, pontos
no mapa, saída e ligações às secções dos guias que referem explicitamente o boss.
As fichas de spawn dos bosses usam estes mesmos acessos, sem herdar a rota de
uma hunt vizinha. Não se deduz uma entrada, cidade ou transporte pela posição
geográfica da sala. O fallback `routeHTML` passa a dizer «Percurso por confirmar».

Limites: uma ficha de local pode ter troços por confirmar. As secções dos guias
podem conter preparativos, acesso e combate; a referência ao boss não certifica
um percurso completo. Os dados não distinguem ainda primeira visita de acesso
diário nem calculam uma rota pessoal em função de cada missão desbloqueada.

- O modelo é uma estimativa. Ficam de fora:
  - mecânicas (fases, curas, summons, campos);
  - mitigação real;
  - prey, charms e imbuements;
  - a qualidade da equipa.
- A TibiaWiki não tem a vida de alguns bosses recentes. As notas de estratégia (texto livre, em inglês) não entram.
- A quest de acesso vem da 1.ª quest ligada nas notas ou na localização da página do boss, mais a tabela `ACCESS` do
  `build_bosses.py` para os que não a ligam. Sem quest, não há nível de acesso.
- Posição no mapa (`pos`, r24): o 1.º `{{Mapper Coords}}` da localização na página do boss (exata); senão o 1.º spawn de
  `data/spawns.json` (exato); senão a entrada do 1.º sítio em `quests/data/places.json` do Questski ou o 1.º
  `{{Mapper Coords}}` da página desse sítio na TibiaWiki, e então `pa = 1` (aproximada: é a zona, o boss fica lá dentro).
  Em outubro de 2026: 272 de 316 com mapa (101 aproximados). Os outros estão em zonas instanciadas sem coordenadas na
  wiki (Warzones, Zarganash, Dream Scar…).
