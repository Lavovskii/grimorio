# Como colaborar no Grimório

Guia curto para quem mexe no site. Antes de mexer no código, lê o `_dev/GRIMORIO.md`.

## 1. Fluxo de trabalho (ramos e Pull Requests)

1. Começa sempre da `main` atualizada: `git checkout main` e `git pull`.
2. Cria um ramo por tarefa, com um nome claro: `git checkout -b hunts-roshamuul`.
3. Faz commits pequenos, cada um com uma mensagem que diga o que muda (ex.: `Hunts: corrigir níveis de Roshamuul`).
4. Envia o ramo: `git push -u origin hunts-roshamuul`.
5. Abre um Pull Request no GitHub. O outro revê; o merge só se faz depois de os testes passarem.
6. **Nunca faças push direto para a `main`.**

## 2. Testar

Com o Apache do XAMPP ligado, na raiz do clone:

```
node _dev/smoke.mjs --hash <página> [--mode original] [--w 375 --h 812] [--voc knight|paladin|druid|monk]
```

- Por omissão abre o site em `localhost/grimorio/` (com o clone noutra pasta, passa o endereço completo com `--url`).
- `<página>` é o que vem depois do `#` no endereço: `inicio`, `hunts`, `itens`, `item/magic-plate-armor`…
- Tem de dar `errors: []` e `hscroll: false` em `inicio` e `hunts` (e nas páginas que mudaste), nos dois modos
  (Modern, que é o de omissão, e `--mode original`) e nas duas larguras (`--w 375 --h 812` e `--w 1440 --h 900`).
- `--shot teste.png` grava uma captura; `--eval "código"` corre JavaScript na página (com `return`).

Depois de mexer no JavaScript, confirma que não tem erros de sintaxe (no Git Bash, na raiz do clone):

```
python -I -c "import sys;s=open('index.html',encoding='utf-8').read();a=s.index('<script>\n(function(){');b=s.index('</script>',a);open(sys.argv[1],'w',encoding='utf-8').write(s[a+9:b])" "$TEMP/grim-app.js" && node --check "$TEMP/grim-app.js"
```

## 3. Dados

- O `G` (o `<script id="G">` do `index.html`) tem **uma entrada por linha**, para o Git juntar sem conflitos
  as alterações dos dois. Só se muda com `load_G`/`save_G` de `_dev/gjson.py`, nunca com `json.dumps` à mão.
- Nunca o edites à mão sem correr a seguir `python -I _dev/gjson.py --check`: sai com 1 e diz a linha e a coluna
  se o JSON ficar estragado (ou fora do formato).
- Depois de mudar `data/*.json`, corre `python -I _dev/build_search.py` (o índice da pesquisa global).
- Depois de resolver um conflito no `index.html`: `python -I _dev/gjson.py --check` e o `smoke.mjs`.
- Poções, munições e runas novas para a linha 'Supplies': `python -I _dev/build_supplies.py` (lê a TibiaWiki).

## 4. Regras

- Lê o `_dev/GRIMORIO.md` antes de mexer no código: lá estão as funções principais e as regras.
- Nomes únicos: antes de criar uma função, `const`, classe CSS ou id, procura se o nome já existe.
- Os dois modos: o Original muda o mínimo; o CSS do Modern começa sempre por `html[data-ui="modern"]`.
- Telemóvel: a 375 px sem scroll para o lado e toques de 44 px.
- Texto para o jogador em português de Portugal, curto e claro.
- Sem links para outros sites no conteúdo: itens, criaturas, NPCs e feitiços abrem páginas internas.

## 5. Questski (guias de quests)

- O site está em `quests/` e a fonte em `_questski/` (guias em `guides/`, um JSON por quest; fichas de locais em `places/`).
  O formato dos guias está em `_questski/tools/GUIDE_FORMAT.md`; o dos locais em `_questski/tools/PLACES_FORMAT.md`.
- Depois de mudar um guia: `python _questski/tools/validate.py <ficheiro>`, `python _questski/tools/build.py`
  e `python -I _dev/build_guias.py` (volta a ligar os guias às quests do Grimório).
- Testar: `export MSYS_NO_PATHCONV=1` e depois
  `node _dev/smoke.mjs --url http://localhost/grimorio/quests/ --hash "/quest/<slug>" [--mode original] [--w 375 --h 812]`.
- O Modern do Questski está em `quests/css/modern.css` (tudo começa por `html[data-ui="modern"]`); o Original é o
  `quests/css/style.css`, com o tema claro/escuro do próprio Questski.
- A ligação ao Grimório (personagem, quests concluídas, links) está em `quests/js/ponte.js`; o switch do topo em `shared/sites.css`.
  Se mudares o formato do estado do Grimório (`grimorio-tibia-v4`), atualiza também o `ponte.js`.
