# Tibia Questski — guide writing spec

You are writing quest guides for **Tibia Questski**, a Portuguese (PT-PT) Tibia quest website.
Each guide is one JSON file `guides/<slug>.json`, built from the brief `tools/briefs/<slug>.md`
(the brief holds the TibiaWiki overview page + the full spoiler page for that quest).

Read the reference guide first: `guides/sams-old-backpack-quest.json` (and its brief
`tools/briefs/sams-old-backpack-quest.md`). Match its structure, tone and level of detail.

## Goal

A player who has never done the quest must be able to finish it **by following the steps
in order, without opening any other site**. So:

- One action per step (travel, talk, kill, use, open, solve, …). Split long paragraphs.
- Say *where* (coordinates, floor, direction: norte/sul/leste/oeste, "sobe 2 andares"),
  *what to say* (exact NPC keywords), *what to bring*, *what can kill you*, and *what you get*.
- Keep every useful detail from the spoiler: puzzle solutions, lever orders, required items,
  timers, cooldowns, "if X happens do Y", rewards choices, achievements, missions/sub-quests.
- Puzzle solutions, lever sequences, answers to riddles, lists of words → write them out fully
  (use a `table` when it is tabular, e.g. task lists, reward choices, answers).
- Never invent facts. If the brief does not say it, do not write it. You may add generic,
  obviously-true Tibia advice (bring rope/shovel, potions, etc.).

## Language

- European Portuguese (PT-PT), informal **tu** imperative: "Vai", "Fala com", "Diz", "Sobe", "Mata", "Usa".
  Use PT-PT vocabulary (ecrã, utilizador, andar/piso, baú, alavanca, escadas, buraco, porta de quest).
- Keep **in English**: NPC names, item names, creature names, place names, spells, achievement
  names and everything the player must **type** to NPCs (keywords). NPC quoted lines stay in English.
- Clear, friendly, direct. No filler, no marketing tone.

## Inline markup (allowed inside any text string)

| Markup | Renders as |
|---|---|
| `**bold**`, `*italic*` | bold / italic |
| `{npc:Name}` | NPC chip with sprite + click shows its map position (Name = exact wiki NPC title) |
| `{item:Wiki Title}` or `{item:Wiki Title\|shown text}` | item sprite + name, links to wiki |
| `{creature:Wiki Title}` or `{creature:Wiki Title\|shown text}` | creature sprite + name |
| `{spell:Spell Name}` | spell link |
| `{wiki:Page Title\|shown text}` | plain TibiaWiki link (places, quests, mechanics) |
| `{key:word}` | keyword chip the player must say to an NPC (e.g. `{key:hi}`, `{key:mission}`) |
| `{coord:x,y,z}` | inline coordinate link (opens the map) |

Wiki titles are the targets of the `[[links]]` in the brief (e.g. `[[Skull (Item)|Skulls]]` →
`{item:Skull (Item)|Skulls}`). Never leave wiki markup (`[[ ]]`, `{{ }}`, `'''`) in the output.

## Coordinates

The brief already converted wiki coordinates to absolute Tibia coordinates:
`[COORD x=32980 y=31740 z=7 | here]` and `[MINIMAP x=.. y=.. z=.. marks=(x,y) (x,y)]`.

- Use **only** coordinates that appear in the brief, or NPC positions from
  `python tools/npc.py "NPC Name"` (prints x/y/z for any NPC). Never guess coordinates.
- Attach every relevant coordinate to the step where the player needs it (`coords` array, with a
  short PT `label`). For a MINIMAP with several marks use the step `map` field with `marks`.
- z = floor: 7 is ground level, lower numbers are above ground (6 = 1 andar acima), higher numbers
  are underground (8 = 1 andar abaixo). Mention floors in the text when helpful.
- When a step is "talk to NPC X", set `"npc": "X"`; the site shows X's position automatically.
- `start` = where the quest begins (usually the first NPC or the entrance).

## Images

`images` may only use files referenced in the brief as `[[File:...]]` / `[[Image:...]]`
(the validator checks this). Use them generously for screenshots, maps and puzzle pictures,
each with a PT `caption`. Do **not** list plain item/creature sprites as images — use the
`{item:..}` / `{creature:..}` tokens instead (they render the sprite automatically).

## JSON schema

```jsonc
{
  "slug": "file-name-without-.json",           // required, equals the brief slug
  "category": "historia",                      // required: historia (multi-step story/mission quest) |
                                               //   tesouro (chest/item quest) | outfit (outfit/addon) |
                                               //   acesso (unlocks area/transport/NPC) | tarefas (tasks, repeatable) |
                                               //   troca (exchange quest) | world-change | evento (seasonal/event) |
                                               //   tutorial (Rookgaard/Dawnport/Newhaven intro)
  "region": "Thais",                           // required, one of: Rookgaard, Dawnport, Thais, Carlin, Ab'Dendriel,
                                               //   Kazordoon, Venore, Edron, Darashia, Ankrahmun, Port Hope, Liberty Bay,
                                               //   Svargrond, Yalahar, Farmine, Gray Beach, Rathleton, Roshamuul, Krailos,
                                               //   Issavi, Feyrist, Marapur, Vários   (closest city / main area)
  "difficulty": 2,                             // required 1..5 for a player at the recommended level
  "duration": "30–45 min",                     // required, PT estimate
  "summary": "...",                            // required, 2–4 sentences PT: story + what you get
  "legend_pt": "...",                          // PT translation of the infobox "legend" (if any)
  "start": {"x":0,"y":0,"z":7,"label":"PT"},   // where it starts
  "requirements": ["PT ..."],                  // level, premium, vocation, previous quests, access, items
  "items_needed": [{"item":"Rope"}, {"item":"Skull (Item)","qty":8,"note":"PT"}, {"text":"PT free text"}],
  "rewards": [{"item":"Dwarven Armor"}, {"item":"Platinum Coin","qty":10}, {"text":"PT free text"}],
  "achievements": ["Achievement Name"],
  "dangers": ["Creature Wiki Title", "..."],   // creatures you meet
  "npcs": ["NPC Wiki Title", "..."],           // NPCs involved
  "tips": ["PT ..."],                          // general tips before starting
  "sections": [                                // required: missions/parts in order
    {
      "title": "1. PT title",
      "intro": "PT (optional)",
      "steps": [
        {
          "title": "PT short title (optional)",
          "text": "PT instructions with inline markup",            // required
          "npc": "NPC Name",                                       // optional
          "dialogue": [{"you":"hi"}, {"npc":"English NPC line"}],  // optional, key lines only
          "coords": [{"x":0,"y":0,"z":7,"label":"PT"}],            // optional
          "map": {"x":0,"y":0,"z":7,"marks":[{"x":0,"y":0,"label":"PT"}]}, // optional
          "images": [{"file":"Wiki File.png","caption":"PT"}],     // optional
          "table": {"head":["..."], "rows":[["..."]]},             // optional
          "warning": "PT danger/irreversible-mistake warning",      // optional
          "tip": "PT tip",                                          // optional
          "reward": "PT what you get at this step"                  // optional
        }
      ]
    }
  ],
  "notes": ["PT extra notes, FAQ, history-free"]                   // optional
}
```

Dialogue: include the keywords the player must type, in order, plus the key NPC lines (shortened
with "[...]" when long). Long transcripts are not needed in full.

Short quests (single chest, world changes, events) can be short, but still: how to get there
(coords), what's in the way, what to click, what you get. World changes / events: explain what
triggers it, what changes, where, and how to take part.

## Validate

After writing each file run:

```
python tools/validate.py guides/<slug>.json
```

Fix every `error`. Warnings about NPC names: check spelling with `python tools/npc.py "partial name"`.
Only write files inside `guides/`. Do not edit anything else.
