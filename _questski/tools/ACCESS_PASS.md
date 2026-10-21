# Access pass — "Dá acesso a…"

The site owner wants to know, for every quest, what it unlocks — e.g. "which quests give access to the
Warzones?" — shown on the quest page ("Dá acesso a …") and on a searchable "Acessos" page.

Add an `unlocks` list to each guide (`guides/<slug>.json`). Leave it out (or empty) when the quest
unlocks nothing permanent (pure item/treasure quests, events, most world changes).

```jsonc
"unlocks": [
  {
    "what": "Warzones 1, 2 e 3",          // REQUIRED, short PT name of what opens (area / transport / NPC / feature)
    "kind": "zona",                        // REQUIRED: zona | transporte | npc | loja | funcionalidade | missao
    "place": "Warzone 1",                  // optional: exact wiki/place title it refers to (for links), e.g. "Gnomegate"
    "when": "Ao chegar ao rank **Expert** (Rank II) da Bigfoot company.",  // optional PT: which mission/rank/step
    "note": "Precisas de Premium."        // optional PT: extra condition (premium, daily limit, cost…)
  }
]
```

Kinds:
- **zona** — areas, dungeons, hunting grounds, islands, cities, boss rooms, quest doors that stay open.
- **transporte** — boats/routes/carpets/teleport systems you can now use (e.g. Dalbrect to Isle of the Kings, GCTS, Steamship).
- **npc** — NPCs that will now talk/trade/travel with you (e.g. Djinn traders).
- **loja** — new trades/shops/exchanges.
- **funcionalidade** — mechanics: citizenship, outfit/addon access, daily tasks, bosses you can now fight, mounts…
- **missao** — other quests or missions it is a prerequisite for (name them).

How to work, per guide:
1. `cd /c/Users/finoa/Desktop/Questski && python tools/access_ctx.py <slug>` — prints the wiki reward line,
   the guide's rewards/notes/requirements, the steps that look relevant, and the place cards that list this
   quest as a requirement (strong evidence it unlocks that place).
2. If needed, read more of `guides/<slug>.json` or the brief `tools/briefs/<slug>.md`.
3. Write the `unlocks` list into the guide (top level, after "achievements"). One entry per thing unlocked;
   group sub-areas when natural ("Warzones 1, 2 e 3"). Be precise in `when` (rank/mission/step).
   Use `place` with the exact title as it appears in the wiki/place cards when there is one.
4. Validate: `python tools/validate.py guides/<slug>.json`.

Never invent: only what the guide, brief, wiki reward line or place cards say. PT-PT, same inline markup as
the guides. Keep JSON strings on one line. Only edit files in `guides\`.
