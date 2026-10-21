# Tibia Questski

Guias passo-a-passo, em português, de todas as quests do Tibia que se podem começar até ao nível 100
(requisito de nível ≤ 100 ou sem requisito),
com mini-mapas, coordenadas, mapa interativo, capturas de ecrã, diálogos dos NPCs e progresso guardado.

## Abrir o site

Duplo clique em `start.bat`: abre o site em <http://localhost:8080> e deixa uma janela aberta a servi-lo
(fecha-a para desligar). Usa o Python 3 se estiver instalado (`serve.py`); se não estiver, usa o servidor em
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
site/              o site estático (index.html, css/, js/, data/, assets/)
  data/            gerado pelo build: index.json, quests/<slug>.json, images.json, npcs.json
  assets/map/      pisos do mapa do Tibia (TibiaMaps)
  assets/wiki/     sprites e capturas descarregadas da TibiaWiki
guides/            os guias escritos (um JSON por quest) — a fonte de verdade do conteúdo
tools/             scripts para atualizar os dados
```

## Atualizar os dados

```bash
python tools/fetch_wiki.py      # descarrega as páginas das quests da TibiaWiki
python tools/fetch_npcs.py      # posições de todos os NPCs
python tools/prepare_briefs.py  # gera os "briefs" (fonte para escrever/rever guias)
python tools/validate.py --all  # valida todos os guias em guides/
python tools/build.py           # gera site/data e descarrega as imagens novas
```

O formato dos guias está descrito em `tools/GUIDE_FORMAT.md`.

### Wiki interna

Todos os itens, criaturas, NPCs, feitiços, locais e achievements referidos nos guias têm página própria
em `#/wiki/...` (sem links externos). Cada item tem a secção **Como obter**: quests e passo exato com
coordenadas, NPCs que o vendem/compram (com a posição no mapa), criaturas que o largam com a % de drop,
vida, experiência e locais de spawn, e locais exatos indicados na wiki.

```bash
python tools/build_wiki.py            # descarrega o que falta da TibiaWiki e gera site/data/wiki/
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

A arte original está em `site/assets/logo-original.webp`. A partir dela, `tools/make_logo_assets.py` gera
o logótipo com fundo transparente (`logo-full.webp`, página inicial), a versão sem letras para a barra de topo
(`logo-mark.webp`) e os ícones (`favicon.png`, `apple-touch-icon.png`). Para trocar de logótipo:

```bash
python tools/make_logo_assets.py caminho/para/nova-arte.png
```

## Créditos

Conteúdo baseado na [TibiaWiki](https://tibia.fandom.com/) (CC BY-SA). Mapa de [TibiaMaps.io](https://tibiamaps.io/).
Tibia é uma marca da CipSoft GmbH; este é um projeto de fãs sem afiliação.
