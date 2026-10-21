# Travel pass — "como chegar" e "como sair" em todos os guias

The site owner found that guides send the player to remote places (e.g. Hellgate in The Explorer Society
Quest, "Elven Poetry" mission) without saying how to get there and, worse, how to get back out.
Your job: make every guide complete on travel. Guides are PT-PT JSON files in `guides/<slug>.json`,
spec in `tools/GUIDE_FORMAT.md` (read it first).

## What to do for each guide

1. Read `guides/<slug>.json` fully. List every place the player has to go to: dungeons, caves,
   mines, towers, islands, sewers, ruins, sub-areas, other cities/continents, boss rooms.
2. For each place that is not simply "an NPC in a city", make sure the guide answers both:
   - **Como chegar** — starting from a city / depot / temple / boat: which boat, carpet or teleport
     (NPC + exact keywords to say, e.g. {key:hi}, {key:edron}, {key:yes}), which stairs/holes/ramps,
     doors, levers, keys, required items (rope, shovel, pick, machete, Levitate, parcels),
     level doors or access quests, and the entrance coordinates.
   - **Como sair** — how to get back out afterwards, especially for one-way entries (teleports in,
     holes without rope spots, Hellgate-like mazes, boss rooms, islands without boats back,
     places needing Levitate). Say where you end up (city/temple/boat) and what you need.
     If the way out is simply the same way back, say so explicitly and mention what is needed
     (e.g. "sobe pelas mesmas escadas e usa a {item:Rope} nos buracos").
3. Put this information where the player needs it:
   - Prefer new dedicated steps: "Chegar a <lugar>" right before the work there, and
     "Sair de <lugar>" right after it (titles in PT). For short trips, adding 1–2 sentences to the
     existing step is fine.
   - Add entrance/exit coordinates in `coords` (with PT labels) and route-map images in `images`.
   - If the route needs items not yet listed, add them to `items_needed` (e.g. Rope, Key 3012,
     Parcel, Levitate via `{spell:Levitate}` in requirements/tips).
   - Keep everything else unchanged. Do not remove content.

## Sources (never invent)

- The quest brief: `tools/briefs/<slug>.md` (often mentions entrances, ropes, teleports).
- Place pages and route pages from the wiki:
  - `python tools/place.py "Hellgate"` — a place page (location, "The way to …", exits, coordinates).
  - `python tools/place.py --routes hellgate` — lists TibiaWiki "Route:" pages; then
    `python tools/place.py "Route:Hellgate"` for the full step-by-step way in/out.
  - `python tools/place.py --find words` — find cached page titles.
  These print `[COORD x=.. y=.. z=..]` for map links (use them as coordinates) and list
  "IMAGES ON THIS PAGE" — those image names may be attached to steps (validator accepts them).
- NPC positions (boats, carpets, guards with keys): `python tools/npc.py "Captain Bluebear"`.
- Other guides already describing the same place: `grep -l "Hellgate" guides/*.json`, then reuse
  their wording/coordinates for consistency.
- General, well-known Tibia travel facts are fine (boats between cities via captains with the
  city name as keyword; temples; depots), but specific routes, coordinates, keys and one-way
  mechanics must come from the sources above. If nothing documents the exit, write the most
  honest instruction you can from the route description (e.g. "volta pelo mesmo caminho") and do
  not invent teleports or coordinates.

## Style

PT-PT, informal "tu", one action per step, NPC/item/place names and keywords in English, the same
inline markup as the rest of the guide ({npc:..}, {item:..}, {key:..}, {coord:x,y,z}, {wiki:..|..}).

## Validate

`cd /c/Users/finoa/Desktop/Questski && python tools/validate.py guides/<slug>.json` after each guide;
fix every error. Only edit files in `guides\`.
