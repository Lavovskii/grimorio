# Fichas de locais — "como chegar" / "como sair"

Every place the quest guides send the player to gets ONE travel card in `places/<slug>.json`.
The site shows the card automatically under every guide step that mentions the place (so a step
like "Vai à Isle of the Kings e entra nas catacumbas" always comes with how to get there and back),
and at the top of the place's wiki page.

Source material per place: `tools/places_src/<slug>.md` — the TibiaWiki page as text
(`[COORD x= y= z=]` = map points), the "Route:" page when there is one, and the arrive/leave steps
our guides already contain (already researched: reuse them, keep them consistent).
Extra lookups: `python tools/place.py "<page>"` (also lists route-map images you may attach),
`python tools/npc.py "<npc>"` (boat captains, carpets, guards: exact positions).

## Schema (`places/<slug>.json`, slug = the `slug:` line of the dossier)

```jsonc
{
  "title": "Isle of the Kings",            // the place title exactly as in the dossier heading
  "type": "ilha",                          // cidade | ilha | gruta | dungeon | montanha | zona | edificio | outro
  "near": "Carlin",                        // nearest city (English name)
  "summary": "PT, 1 frase: o que é e onde fica.",
  "entrance": {"x": 0, "y": 0, "z": 7, "label": "PT"},   // main entrance / arrival point (if known)
  "requirements": ["PT ..."],              // access quests, level doors, premium, keys (optional)
  "items": ["Rope", "Shovel"],             // wiki item titles needed to get in/out (optional)
  "arrive": ["PT passo 1", "PT passo 2"],  // REQUIRED: ordered, concrete, from the nearest city/boat/carpet/temple
  "leave": ["PT passo 1"],                 // REQUIRED: how to get back out to a city/boat/temple
  "coords": [{"x": 0, "y": 0, "z": 7, "label": "PT"}],    // other useful points (exits, rope spots, teleports)
  "images": [{"file": "Route map.png", "caption": "PT"}],  // route maps/screenshots (optional)
  "warnings": ["PT ..."]                   // one-way holes, timers, PvP, dangerous spawns on the way (optional)
}
```

Text fields use the same PT-PT style and inline markup as the guides (`tools/GUIDE_FORMAT.md`):
`{npc:..}`, `{item:..}`, `{creature:..}`, `{wiki:Page|text}`, `{key:hi}`, `{coord:x,y,z}`, `**bold**`.
Give NPC keywords for every boat/carpet/guard (`{key:hi}`, `{key:carlin}`, `{key:yes}`), floors
(piso 0 = térreo z7, subsolo = z8+, andares acima = z6-), directions (norte/sul/leste/oeste) and
required items. Cities: "arrive" = boats/carpets/roads that reach it; "leave" = the main ways out.

Never invent routes, keywords or coordinates. If the sources do not document the way out, write
the honest version ("Volta pelo mesmo caminho: …") or say the wiki does not describe it.

Validate every file: `cd /c/Users/finoa/Desktop/Questski && python tools/validate_places.py places/<slug>.json`
Only write files inside `places\`.
