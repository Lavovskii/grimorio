# Sessões reais para a calibração

As sessões reais afinam os números das hunts (XP/h, lucro/h e o ajuste ao nível) no `_dev/calibrar.py`. Ficam em
`_dev/sessoes/`, um ficheiro por recolha, e o `_dev/import_sessoes.py` valida-as. Plano: parte D de
`docs/superpowers/plans/2026-11-10-fichas-hunts-bosses.md` (Tasks 19 e 20). Visão geral da calibração (ficheiros,
`data/calib.json`, rotina semanal): secção «Calibração (r35-D)» do `_dev/GRIMORIO.md`.

**Regra de ouro: nunca nomes.** Nem de personagens, nem de mundos, nem de guilds, em nenhum ficheiro, commit, PR ou chat.
Só entram números agregáveis por hunt, vocação e nível. Uma linha com um campo `name`, `char`, `personagem` (ou outro de
nome) é recusada e o importador sai com erro.

## Formato

Um ficheiro JSON por recolha, com o nome `AAAA-MM-DD-<origem>.json` (ex.: `2026-11-12-huntanalyser.json`):

```json
[
  {"pid": "w_podzilla", "voc": "sorcerer", "lvl": 925, "xph": 12622912, "loh": 2174091, "min": 120, "data": "2026-11-12", "src": "huntanalyser"}
]
```

| Campo | O que é |
|---|---|
| `pid` | Chave da hunt em `G.places` (ex.: `w_podzilla`). |
| `voc` | `knight`, `paladin`, `sorcerer`, `druid` ou `monk`. |
| `lvl` | Nível da personagem no início da sessão. |
| `xph` | XP por hora (a XP crua da sessão ÷ horas). |
| `loh` | Lucro por hora em gp (loot − supplies), pode ser negativo; `null` se não se sabe. |
| `min` | Duração em minutos (sessões com menos de 15 minutos saem). |
| `data` | Dia da sessão, `AAAA-MM-DD`. |
| `src` | `huntanalyser`, `tibiaroute` ou `manual`. |

Também serve CSV com as mesmas colunas e cabeçalho (`pid,voc,lvl,xph,loh,min,data,src`; `loh` vazio = sem valor).
Nenhum outro campo é aceite.

O importador também recusa: `pid` desconhecido, vocação ou origem desconhecida, números em falta, e sessões com mais de
4000 mortes por hora (XP/h ÷ XP média por morte da zona, a regra do `G.ha`): essas não são solo nem desta zona.

## Comandos

```
python3 -I _dev/import_sessoes.py      # valida tudo o que está em _dev/sessoes/ e mostra o resumo
python3 -I _dev/calibrar.py            # junta as sessões ao G.ha e grava data/calib.json e _dev/calib_relatorio.md
python3 -I _dev/calibrar.py --check    # confirma que o data/calib.json está em dia (precisa do _dev/cache/ks-<gen>.json)
python3 -I _dev/calib_test.py          # testes
```

O agregado fica no `data/calib.json` (`ha`), no formato do `G.ha`: `{pid: {v: {voc: [sessões, nível mínimo, nível
mediano, XP/h, lucro/h]}}}` (medianas). Hoje as sessões entram no `k` (ajuste ao nível), nas mortes/h (`kz`) e no
relatório; o site ainda não mostra o `ha` importado.

A rotina semanal na cloud (secção «Calibração (r35-D)» do `_dev/GRIMORIO.md`) corre o `import_sessoes.py` e o
`calibrar.py` com o que já estiver em `_dev/sessoes/` e abre um PR se o `data/calib.json` mudar. Ela **não** recolhe
sessões: a recolha é só a de baixo, à mão.

## Recolha no Hunt Analyser (sessão local, com o Chrome do dono)

Este passo não corre na cloud nem na rotina semanal: precisa do Chrome do dono, no PC dele, com a sessão do Hunt
Analyser já aberta. O dono está autorizado a entrar com a conta do site. **A palavra-passe nunca vai para ficheiros,
commits, PRs nem chats**: se a sessão tiver expirado, o dono entra à mão e só depois o Claude continua.

**TODO (dono): endereço da lista de sessões públicas do Hunt Analyser = `<por preencher>`.** Sem ele, o passo 3 não se
faz (não adivinhar o endereço).

1. No PC do dono, abrir uma sessão do Claude Code no clone do repositório, com o Claude in Chrome ligado ao Chrome dele.
2. O dono abre o Hunt Analyser no Chrome e confirma que já tem a sessão iniciada.
3. Abrir a lista de sessões públicas (o endereço do TODO acima) e filtrar por **solo** (sessões em grupo ficam de fora).
4. Em cada sessão, ler só: hunt, vocação, nível, XP/h, lucro/h, duração e dia. Não copiar o nome da personagem, o
   mundo nem nada que identifique o jogador; não fazer capturas de ecrã para o repositório.
5. Fazer a correspondência do nome da hunt com o `pid`: pelo `G.places[pid].n`, pelos nomes oficiais em
   `G.places[pid].wn` e pelos nomes do TibiaPal (`G.hunts[voc][].place`). Sem correspondência segura, a sessão fica de fora.
6. Gravar só os campos do formato em `_dev/sessoes/AAAA-MM-DD-huntanalyser.json`, com `"src": "huntanalyser"`.
7. Correr `python3 -I _dev/import_sessoes.py` (tem de sair com 0), `python3 -I _dev/calibrar.py` e
   `python3 -I _dev/calib_test.py`; rever o `_dev/calib_relatorio.md` (o `k` e as hunts com mais de 25 % de diferença)
   antes de fazer commit. O commit leva o ficheiro de `_dev/sessoes/`, o `data/calib.json` e o relatório, num ramo
   próprio e com PR para o `main` (nunca direto no `main`).
8. Antes do commit, procurar nomes por engano: `git diff --cached` só pode ter números, `pid`s e vocações.

Para evitar contar a mesma sessão duas vezes, cada recolha deve começar no dia a seguir à anterior (o `G.ha` já tem as
sessões recolhidas antes da parte D).
