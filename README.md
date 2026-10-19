# Grimório de Tibia

Site de fãs de Tibia, em português de Portugal, centrado em **hunts solo por vocação**: que hunt fazer ao teu nível, com que set, que elemento usar, quanto rende, como lá chegar. Inclui também uma wiki interna (itens, criaturas, feitiços, NPCs, conquistas, montarias, outfits), equipamento e sets, rotação, hotkeys, Wheel, charms, imbuements e quests. Tem dois aspetos: **Original** e **Modern**, que se escolhe no rodapé.

Endereço público (servidor de casa): `http://<IP>/grimorio/`

## Como pôr a correr no teu PC

1. Instala o [XAMPP](https://www.apachefriends.org/) em `C:\xampp`, porque as ferramentas de desenvolvimento usam esse caminho.
2. Clona este repositório para `C:\xampp\htdocs\grimorio`:
   ```
   git clone <url-do-repositório> C:\xampp\htdocs\grimorio
   ```
3. Liga o Apache no XAMPP Control Panel e abre `http://localhost/grimorio/`.

Não é preciso compilar nada: é uma página estática (`index.html`). O único código de servidor é `api/market.php`, um proxy com cache para os preços do Market por mundo (precisa do PHP do XAMPP).

## Estrutura

| Caminho | O que é |
|---|---|
| `index.html` | A app inteira: CSS, HTML, dados embebidos (`<script id="G">`, JSON) e o JavaScript. |
| `data/*.json` | Dados carregados quando precisos: itens, criaturas, dano das criaturas, NPCs, quests, spawns, feitiços, conquistas, montarias, outfits e o índice da pesquisa global. |
| `*.png` | Folhas de sprites (itens, criaturas, NPCs, feitiços, montarias, outfits, miniaturas dos mapas das hunts). |
| `maps/` | Mapa do jogo por piso (`floor-XX-map.png`, 1 px = 1 casa, origem 31744,30976). |
| `api/market.php` | Proxy do TibiaMarket (cache de 6 h em `api/cache/`, que não vai para o Git). |
| `_dev/` | Ferramentas e guia técnico. O `.htaccess` bloqueia esta pasta ao público. |

**Antes de mexer no código, lê `_dev/GRIMORIO.md`.** Explica os dados, as funções principais e as regras que já nos custaram bugs: nomes de funções únicos, ordem de arranque, os dois modos, telemóvel, PT-PT e sem links externos.

## Ferramentas (`_dev/`)

- `smoke.mjs`: abre o site num Edge sem janela, cria personagens de teste e devolve os erros da consola e uma captura de ecrã. Exemplo:
  `node _dev/smoke.mjs --url http://localhost/grimorio/ --hash hunts --mode modern --w 375 --h 812 --shot teste.png`
- `gjson.py`: lê e grava os dados `G` do `index.html` com uma entrada por linha. `python -I _dev/gjson.py --check` confirma que o JSON lê bem e está no formato certo; `--format` reformata. Os outros scripts que mudam dados usam-no (`load_G`/`save_G`).
- `build_search.py`: regenera `data/search.json`. Corre-o depois de mudar ficheiros de `data/`.
- `fix_hunt_mons.py`: refaz as criaturas e as quantidades de cada hunt (`G.pm`) a partir da lista curada (`G.places[pid].mons`).
- `build_huntmaps.py`: refaz as miniaturas dos mapas das hunts (`huntmaps.png`). Depois muda o `?v=` de `huntmaps.png` no `index.html`, porque os browsers guardam a imagem antiga.
- `apply_hunt_fixes.py`: aplica correções de hunts verificadas, em ficheiros `fix-*.json`.
- `reap.ps1`: fecha browsers de testes que ficaram abertos.

As ferramentas usam caminhos `C:\xampp\...`. Se o teu XAMPP estiver noutro sítio, ajusta-os. Corridas a partir de `_dev/` sem indicar a raiz, usam a pasta do teu clone; os registos vão para a pasta da variável `GRIM_WORK` ou para a pasta temporária.

## Como trabalhamos os dois

- **Nunca trabalhem os dois diretamente na `main`.** Cada um cria um ramo por tarefa:
  ```
  git checkout -b hunts-roshamuul
  ...alterações...
  git add -A
  git commit -m "Hunts: corrigir níveis de Roshamuul"
  git push -u origin hunts-roshamuul
  ```
  Depois abre um Pull Request no GitHub, o outro revê e faz merge.
- **O site público corre a partir desta pasta no PC de casa.** Para publicar o que está na `main`, nesse PC: `git pull` dentro de `C:\xampp\htdocs\grimorio`.
- **Conflitos no `index.html`:** os dados `G` (o `<script id="G">`) têm uma entrada por linha (uma hunt, um item, uma criatura…), por isso o Git junta sozinho as alterações dos dois quando mexem em registos diferentes. Se houver conflito, resolve-o como noutro ficheiro qualquer e depois corre `python -I _dev/gjson.py --check` (diz a linha e a coluna se o JSON ficou estragado) e o `smoke.mjs`. Não mudes os dados com `json.dumps` à mão: os scripts gravam-nos com `save_G` de `_dev/gjson.py`, que mantém o formato.
- **A pasta pública é um clone do repositório:** o `.htaccess` responde 404 a tudo o que começa por `.git` (a pasta `.git`, o `.gitignore` e o `.gitattributes`), para ninguém descarregar o histórico nem ver o email de quem faz commits; o `_dev/` dá 403. O `.editorconfig` diz aos editores para gravar em UTF-8 com fins de linha LF.
- Antes de cada commit, corre o `smoke.mjs` em `inicio` e `hunts`, nos dois modos e a 375 px. Tem de dar `errors: []` e `hscroll: false`.

## Fontes dos dados

TibiaWiki (tibia.fandom.com), TibiaPal, TibiaData (personagens), TibiaMarket (preços), mapa e spawns do projeto Canary/OpenTibiaBR, e sprites do cliente oficial. Tibia é uma marca da CipSoft GmbH; o Grimório é um site de fãs sem ligação oficial.
