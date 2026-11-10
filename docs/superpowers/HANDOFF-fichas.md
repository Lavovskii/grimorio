# Passagem de trabalho: fichas objetivas de hunts e bosses

Para uma sessão nova do Claude Code continuar o trabalho sem precisar da conversa anterior. Data: 10/11/2026.

## Como começar

1. Abre uma sessão no repositório `Lavovskii/grimorio`, no ramo **`fichas-hunts-bosses`**:
   `git fetch origin fichas-hunts-bosses:refs/remotes/origin/fichas-hunts-bosses && git checkout -B fichas-hunts-bosses origin/fichas-hunts-bosses`
2. Cola este pedido na sessão nova:

```
Lê docs/superpowers/HANDOFF-fichas.md e segue-o. Começa pela ronda 2 do grilling (secção «Perguntas em aberto»)
e só depois executa o plano, com as paragens de aprovação que lá estão.
```

## O que se quer

O dono do site quer fichas de hunts e de bosses **objetivas**, iguais nos dois casos:
- **mapa do sítio ao lado de «Como lá chegar»**, com caminhos bem desenvolvidos: troços, mapas que se expandem com os
  passos numerados, e os NPCs com quem é preciso falar (onde estão, o que dizer, quanto custa);
- **pré-requisitos** com ligação às quests (guias do Questski);
- **criaturas** e **loot principal**, com os preços do Market do mundo da personagem (já atualizados pelo
  `api/market.php`, cache de 6 h);
- só **charms e preys** como recomendações;
- só cinco números: **XP/h, lucro/h, nível recomendado, resistências e índice de dificuldade** (nos bosses, XP e valor
  por kill);
- **sem** equipamento, Wheel, gemas, setup, sessões reais, separadores.

## Documentos (lê por esta ordem)

| Ficheiro | Para quê |
|---|---|
| `CLAUDE.md` | Regras de conversa: modo caveman sempre ligado, PT-PT. |
| `_dev/GRIMORIO.md` | Regras do site, dados, testes e traduções. Obrigatório antes de mexer no código. |
| `docs/superpowers/specs/2026-11-10-fichas-hunts-bosses-design.md` | O desenho (o quê e porquê), incluindo as **Decisões da ronda 1**. |
| `docs/superpowers/plans/2026-11-10-fichas-hunts-bosses.md` | O plano: 17 tarefas em 3 partes (A dados, B ficha, C caminhos por lotes). |
| `docs/superpowers/specs/2026-11-07-bosses-quests-design.md` | Desenho anterior (rotação diária de bosses, passos do Questski por personagem). **Fora deste trabalho**; vem a seguir. |

## Decisões já tomadas (ronda 1, aceites pelo dono)

Q1 Equipamento e Wheel saem só das fichas · Q2 a ficha continua no painel · Q3 fichas de locais uma vez em `places`,
com `{ref}` · Q4 caminhos no i18n de conteúdo (inglês) · Q5 pré-requisitos com o estado da quest inteira; por passo
fica para o desenho de 7/11 · Q6 dificuldade fixa nas hunts, pelo nível nos bosses · Q7 um agente por tarefa com
revisão; aprovações no fim da parte A, da parte B e em cada lote da C · Q8 parte C pela TibiaWiki (`api.php`), lotes
de 25, em paralelo depois da Task 2. Detalhe: secção «Decisões da ronda 1» da spec.

## Perguntas em aberto (ronda 2 do grilling: faz estas antes de escrever código)

Usa a skill `grilling`: as perguntas numeradas, cada uma com a recomendação, e espera pelas respostas.

1. **O Questski passa a ler as fichas de locais do `data/caminhos.json`?** Hoje lê `quests/data/places.json`.
   Recomendação: não. O Questski fica como está; o `build_caminhos.py` lê o `places.json` através do
   `hunt-access.json`/`boss-access.json`. Corrigir um local continua a ser no `places.json` e regenerar.
2. **O comparar hunts (bandeja e tabela) fica igual?** Usa XP, lucro, risco e acesso. Recomendação: sim, só troca
   «Risco» pela dificuldade 1–5 do `GrimFicha.huntDiff`, para não haver dois índices diferentes no site.
3. **Hunts sem linha para a vocação ativa** (abertas pela pesquisa) mostram a ficha sem XP/h nem lucro/h, com «—».
   Recomendação: sim.
4. **Lotes da parte C abertos ao mesmo tempo que a parte B:** cada lote é um PR para o ramo `fichas-hunts-bosses`
   (não para o `main`), para o merge final levar tudo junto. Recomendação: sim.

Se as respostas mudarem o plano, atualiza o plano com a skill `superpowers:writing-plans` e pede outra vez a aprovação
antes de executar.

## Skills a usar

| Momento | Skill | Nota |
|---|---|---|
| Sempre | `superpowers:using-superpowers` | Arranque. |
| Sempre | `caveman:caveman` | Respostas curtas em PT-PT (regra do `CLAUDE.md`). |
| Sempre que escreves código | `ponytail` (nível `full`) | Mudança mínima que resolve tudo; está em `.claude/skills/ponytail`. |
| Ronda 2 e qualquer dúvida de desenho | `grilling` (ou `grill-me`) + `superpowers:brainstorming` | Árvore de decisões por rondas; brainstorming só se aparecer algo novo para desenhar. |
| Mudar o plano | `superpowers:writing-plans` | O dono aprova o plano antes da execução. |
| Executar | `superpowers:subagent-driven-development` | Um agente por tarefa, revisão entre tarefas (ronda 1, Q7). O dono pediu este método: podes lançar subagentes. |
| Alternativa | `superpowers:executing-plans` | Se o dono preferir tudo na mesma sessão. |
| Em cada tarefa | `superpowers:test-driven-development` | Os testes de cada tarefa estão no plano: primeiro o teste a falhar. |
| Quando algo falha | `superpowers:systematic-debugging` | Antes de mudar código. |
| Antes de dizer «feito» | `superpowers:verification-before-completion` | Correr os comandos e mostrar a saída. |
| Fim de cada parte | `superpowers:requesting-code-review` | Revisão do ramo antes de pedir a aprovação ao dono. |
| Fim de tudo | `superpowers:finishing-a-development-branch` | PR para o `main`; merge só com o OK do dono. |
| Tasks 4 e 5 (aspeto) | `ui-ux-pro-max:ui-ux-pro-max`, `example-skills:frontend-design` | Rever a ficha (contraste, toque, hierarquia) dentro do tema atual. |
| Testes no browser | `example-skills:webapp-testing` | Playwright já instalado. |

## Paragens para aprovação (o dono decide em cada uma)

1. Depois da ronda 2: o plano final.
2. Fim da parte A (Tasks 1–2): saída do `python3 -I _dev/build_caminhos.py --report` e dos testes.
3. Fim da parte B (Tasks 3–6): capturas antes/depois a 1440 e 390 px (hunt `ok`, `part`, `none`; boss com guia, de
   raid, sem posição), saída do `_dev/fichas_browser.cjs`.
4. Cada lote da parte C: um PR com o `--report` antes e depois.
5. Merge para o `main`: só com o OK explícito. O site só muda quando o dono faz `git pull` no servidor.

## Notas do ambiente (aprendidas nas sessões anteriores)

- **GitHub:** o `gh pr create` falha (GraphQL bloqueado). Usa a API REST: `gh api repos/Lavovskii/grimorio/pulls -f title=… -f head=… -f base=… -F body=@ficheiro.md`, e para o merge `gh api -X PUT repos/Lavovskii/grimorio/pulls/<n>/merge -f merge_method=squash`.
- **Fetch:** a refspec do remoto é restrita. Atualiza com `git fetch origin <ramo>:refs/remotes/origin/<ramo>`. Depois de um push novo, `git config branch.<ramo>.remote origin` e `branch.<ramo>.merge refs/heads/<ramo>` para o aviso de «unpushed» não aparecer.
- **Nunca** `pkill -f` com um padrão que aparece no próprio comando (mata a shell). Para parar um servidor de teste, usa a ferramenta de tarefas ou o PID.
- **Python** que lê ficheiros descarregados: `python3 -I`. Descargas numa pasta própria do scratchpad.
- **TibiaWiki:** a página normal dá 403; a API funciona: `https://tibia.fandom.com/api.php?action=parse&page=<Nome>&prop=wikitext&format=json`.
- **Servidor local:** `python3 -m http.server 8765 --bind 127.0.0.1` na raiz do repositório. O `_dev/smoke.mjs` é só para Windows (usa Edge e PowerShell); aqui usa o `_dev/fichas_browser.cjs` do plano (Playwright: `require('playwright')`, `chromium.launch()` sem opções).
- **CSP:** o `.htaccess` não muda; nada de pedidos a domínios novos.
- **Nada de dados pessoais** no repositório nem nos commits.

## Estado do ramo `fichas-hunts-bosses`

- Plano e spec (com as decisões da ronda 1).
- Skills do projeto em `.claude/skills/` (`grill-me`, `grilling`, `ponytail`; origem e licença no `README.md` da pasta).
- Ainda **nenhum código** do plano.
