# Tibia Questski

> **Faz parte do Grimório de Tibia.** O site do Questski está em `quests/` na raiz do repositório
> (endereço `/grimorio/quests/`, com o switch Grimório ⇄ Questski no topo) e esta pasta, `_questski/`,
> tem a fonte: os guias (`guides/`), as fichas de locais (`places/`) e as ferramentas (`tools/`).
> O `.htaccess` desta pasta não a deixa ver de fora. A ligação ao Grimório está explicada no fim deste ficheiro.

Guias passo-a-passo, em português, de todas as quests do Tibia que se podem começar até ao nível 100
(requisito de nível ≤ 100 ou sem requisito),
com mini-mapas, coordenadas, mapa interativo, capturas de ecrã, diálogos dos NPCs e progresso guardado.

## Abrir o site

Com o Apache do XAMPP ligado (como o resto do Grimório): <http://localhost/grimorio/quests/>.

Sem o XAMPP: duplo clique em `start.bat`. Serve a pasta do repositório inteira em <http://localhost:8080>
(Grimório em `/`, Questski em `/quests/`, que abre logo) e deixa uma janela aberta a servi-lo
(fecha-a para desligar). Os preços do Market do Grimório precisam do PHP do XAMPP. Usa o Python 3 se estiver instalado (`serve.py`); se não estiver, usa o servidor em
PowerShell que já vem com o Windows (`serve.ps1`), por isso funciona em qualquer PC com Windows sem instalar nada.
Abrir o `index.html` diretamente não funciona, porque os dados são carregados por `fetch`.

Num terminal: `python serve.py` ou `powershell -ExecutionPolicy Bypass -File serve.ps1`.

O progresso fica guardado no navegador de cada PC. Para o levar para outro PC, usa Progresso → Exportar
e depois Importar no outro.

## O que tem

- **Lista por nível** (barra lateral), do mais baixo para o mais alto, agrupada em faixas (1–9, 10–19, …, 90–100,
  e "Rec. 100+" para quests com requisito ≤ 100 mas recomendadas acima). Ordena por nível recomendado ou mínimo.
- **Filtros**: o teu nível (bloqueia/esconde o que ainda não podes fazer), Free/Premium, tipo de quest,
  esconder concluídas, e pesquisa (tecla `/`) por nome, NPC, recompensa ou local.
- **Região (cidade)**: escolhe uma cidade (barra lateral, cartões "Quests por região" na página inicial, ou a barra de
  regiões na página Quests; link direto `#/quests/regiao/Darashia`) para ver só as quests de lá. Por omissão mostra as
  quests cuja região principal é essa cidade; a opção "incluir as que passam por lá" junta as de outras regiões que têm
  passos na cidade ou arredores (calculado no build: cada coordenada dos passos é atribuída à cidade mais próxima).
- **Cada quest numa aba** própria no topo; dentro de cada quest há separadores Guia / Preparação / Recompensas / Mapa.
- **Passos** numerados com caixa para marcar como feito, mini-mapa de cada coordenada, botão para o mapa interativo,
  link para o TibiaMaps.io, capturas de ecrã (clica para ampliar), conversas com os NPCs (clica numa fala tua para a copiar),
  avisos de perigo, dicas e o que recebes em cada passo.
- **Pergaminho "Quest concluída!"** no fim do guia de cada quest (e no topo do separador Recompensas), ao estilo das
  wikis de RuneScape: desenrola-se quando chegas ao fim e mostra tudo o que ganhas — itens com sprite e quantidade,
  outras recompensas, achievements e acessos desbloqueados — com botão para marcar a quest como concluída.
  É gerado automaticamente a partir dos campos `rewards`, `achievements` e `unlocks` de cada guia.
- **Mapa** interativo de todos os pisos (▲▼ ou PageUp/PageDown), com o início de cada quest marcado pelo nível.
- **Acessos** (`#/acessos`, ou `#/acessos/warzone`): que quests desbloqueiam cada zona, transporte, NPC, loja
  ou funcionalidade, e em que missão/rank. Vista "por zona" ou "por quest". Cada quest mostra "Dá acesso a…" no topo
  (dados no campo `unlocks` dos guias — ver `tools/ACCESS_PASS.md`), e a ficha de cada local mostra "Acesso dado por".
- **Wiki interna** com ~7 200 páginas (itens, criaturas, NPCs, locais…) e pesquisa; nenhum link sai do site.
- **Progresso** guardado no navegador, com exportar/importar.
- **Tema claro** (pergaminho) e **escuro** (pedra e ouro), no botão ☀/☾.

## Estrutura

```
quests/                (na raiz do repositório) o site estático: index.html, css/, js/, data/, assets/
  js/app.js            a app (vanilla JS, rotas #/...)
  js/ponte.js          ligação ao Grimório (personagem, quests concluídas, links para a wiki do Grimório)
  data/                gerado pelo build: index.json, quests/<slug>.json, images.json, npcs.json, wiki/
  assets/map/          pisos do mapa do Tibia (TibiaMaps)
  assets/wiki/         sprites e capturas descarregadas da TibiaWiki
_questski/guides/      os guias escritos (um JSON por quest) — a fonte de verdade do conteúdo
_questski/places/      as fichas de locais (como chegar / como sair)
_questski/tools/       scripts para atualizar os dados (escrevem em ../quests/)
```

## Atualizar os dados

```bash
python tools/fetch_wiki.py      # descarrega as páginas das quests da TibiaWiki
python tools/fetch_npcs.py      # posições de todos os NPCs
python tools/prepare_briefs.py  # gera os "briefs" (fonte para escrever/rever guias)
python tools/validate.py --all  # valida todos os guias em guides/
python tools/build.py           # gera quests/data e descarrega as imagens novas
python -I ../_dev/build_guias.py  # volta a ligar os guias às quests do Grimório (data/guias.json)
```

O formato dos guias está descrito em `tools/GUIDE_FORMAT.md`.

### Wiki interna

Todos os itens, criaturas, NPCs, feitiços, locais e achievements referidos nos guias têm página própria
em `#/wiki/...` (sem links externos). Cada item tem a secção **Como obter**: quests e passo exato com
coordenadas, NPCs que o vendem/compram (com a posição no mapa), criaturas que o largam com a % de drop,
vida, experiência e locais de spawn, e locais exatos indicados na wiki.

```bash
python tools/build_wiki.py            # descarrega o que falta da TibiaWiki e gera quests/data/wiki/
python tools/build_wiki.py --offline  # só volta a processar o que já está em cache
```

### Fichas de locais (como chegar / como sair)

Cada local para onde os guias mandam o jogador (390, de Hellgate à Isle of the Kings) tem uma ficha em
`places/<slug>.json` com como chegar, como sair, requisitos, itens, avisos, coordenadas e mapas de rota.
O site mostra-a automaticamente debaixo de qualquer passo que mencione o local (uma vez por secção) e no topo
da página do local na wiki. Formato em `tools/PLACES_FORMAT.md`; `python tools/prepare_places.py` gera os
dossiês de fontes e `python tools/validate_places.py --all` valida.

Para quem escreve/revê guias: `python tools/place.py "Hellgate"` mostra a página de um local
(entradas, saídas, coordenadas, imagens), `python tools/place.py --routes` lista as páginas de rotas,
e `tools/TRAVEL_PASS.md` explica como documentar "como chegar" e "como sair" de cada sítio.

## Logótipo

A arte original está em `quests/assets/logo-original.webp`. A partir dela, `tools/make_logo_assets.py` gera
o logótipo com fundo transparente (`logo-full.webp`, página inicial), a versão sem letras para a barra de topo
(`logo-mark.webp`) e os ícones (`favicon.png`, `apple-touch-icon.png`). Para trocar de logótipo:

```bash
python tools/make_logo_assets.py caminho/para/nova-arte.png
```

## Créditos

Conteúdo baseado na [TibiaWiki](https://tibia.fandom.com/) (CC BY-SA). Mapa de [TibiaMaps.io](https://tibiamaps.io/).
Tibia é uma marca da CipSoft GmbH; este é um projeto de fãs sem afiliação.

## Ligação ao Grimório

O Questski e o Grimório estão no mesmo endereço, por isso partilham o `localStorage` do browser:

- **Switch no topo** (`shared/sites.css`, igual nos dois sites) e transição suave entre eles. Numa página da wiki que
  também existe no Grimório (item, criatura, NPC, feitiço, conquista), o switch e o botão "Ver no Grimório" abrem essa página lá.
- **Aspeto**: o Original/Modern escolhido no rodapé de qualquer um dos dois vale para os dois (chave `grimorio-ui`).
- **Personagem**: o filtro "O meu nível" usa sozinho o nível da personagem ativa do Grimório (`grimorio-tibia-v4`),
  até escreveres outro nível.
- **Quests concluídas**: marcar uma quest como concluída aqui marca-a também na personagem ativa do Grimório, quando a
  quest existe lá (e vice-versa). A correspondência está em `data/guias.json` (campo `q2s`), gerado por
  `python -I _dev/build_guias.py` a partir de `quests/data/index.json` e das quests do Grimório.
- **No Grimório**: a pesquisa global encontra os guias, e as quests, as hunts e as criaturas têm botões para o guia.

Notas para quem continua o trabalho:
- `tools/cache/` não vai para o Git (é a cache da TibiaWiki): `python tools/fetch_wiki.py` e `python tools/fetch_npcs.py`
  voltam a criá-la antes de `validate_places.py`, `prepare_briefs.py` e `build.py`.
- `python tools/validate.py --all` dá avisos em ~127 guias por imagens de rotas que não estão nos "briefs"
  (vêm das fichas de locais); já estava assim antes da junção.
