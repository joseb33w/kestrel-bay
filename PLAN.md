# Goal

Build **Kestrel Bay** — a grey, rain-soaked open-world fishing town on steep coastal cliffs — as a
Godot 4.7.1 data-driven world (`godot-tmpl-rpg`, chunk mode) exported for the mobile web and
native-playable via `world.json`:

- terrain sculpted so the town sits on a +26 m plateau, the sea cliff drops hard to the water, a
  cove holds the harbour at +1.5 m, a switchback road climbs the cove head, a headland carries the
  lighthouse, a chapel hill rises behind the town, and a second narrow inlet holds the wrecked
  trawler and the smugglers' sea caves;
- every building compiled with Mason (real openings, walkable interiors, plinths on slopes);
  enterable: lighthouse (stairs to the top), pub (rooms upstairs), harbour office, net shed,
  chapel, one house, the wreck, the caves — every other house/shed sealed;
- Meshy characters throughout (player, harbour master, barmaid, fishermen — two of them seated on
  benches, a pub regular seated at the bar — villagers, melee + rifle smugglers), spoken NPC chat;
- a drivable truck (assembled body + wheel) and a boat; a boat-hook start weapon and a shotgun
  found on the wreck; smugglers that rush (melee) and stand off (rifle range);
- behaviour as data: quests.json + `rules`/`vars`/`hud`/`director` blocks, no game scripts.

# Files to touch

- `world.json` (Architect layout → patched with compiled Mason records, NPC personas, weapons,
  regions music/ambient, rules/vars/hud/director), `quests.json`, `structures.json` (Mason specs)
- `models/*.glb` (Meshy characters/vehicles/props + Mason `<hash>.lod0.glb` buildings),
  `models/meshy_assets.jsonl`, `models/mason_assets.jsonl`
- `audio/*.ogg` (realistic-tier ambient/music/SFX swapped in for the chiptune defaults)
- `project.godot` (name only), `export_presets.cfg` (viewport-fit=cover), `README.md`, `.gitignore`
- engine scripts (`*.gd`) are the template's — unmodified

# Verification approach

- Mason walk gate on every compiled building (exit 0, floors_built == declared, doors in the
  size gate); terrain heights at every building footprint corner via a headless Godot dump of
  `GTerrain.height` (no floating corners beyond the 8 m plinth limit, doors on the uphill side)
- qgcheck winnability on `world.json` + `quests.json`
- `verify.mjs` smoke + FEEL probes on the exported `out/` (boot, console, frames, pck ≤ 80 MB,
  GPU-memory gate, engine currency, rule vocabulary) — must exit 0 on the shipped export
- targeted checks: hero facing while walking toward camera, attack drives a real HP delta with
  particles/flash, enemy closes distance and damages the player, NPC chat contract fetch + panel
  opens headlessly, portrait + landscape fill, vehicle board
- QA + Game-Feel specialist passes on the content-complete build; P0/P1 remediated before PR

# Out of scope

- Multiplayer / auth / any Supabase backend (single-player, `user://` saves only)
- True enemy projectiles with cover-seeking AI (engine enemies are stand-off melee at
  `enemy_range`; rifle smugglers fire from range visually, disclosed in the PR)
- Diagonal road strips (roads are ns/ew cell legs; the switchback is a staircase of legs)
