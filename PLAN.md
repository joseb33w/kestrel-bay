# Goal

Fix Kestrel Bay properly — the reported breakages AND the empty world — in one pass, keeping the
game DATA-driven (native-playable `world.json`, no game scripts):

- **Broken:** white/misplaced interior furniture (floating, sunk, in the street, two tables inside
  each other), near-empty rooms; window holes with no glass; an un-enterable chapel that does not
  read as a chapel; a pub regular lying in mid-air; an unreachable/absent smuggler ringleader and a
  cove fight that only ends in a teleport to the start; a hero whose body does not swing with the
  weapon; NPCs miming with empty hands; a truck that stalls on the switchback; sticky/frozen touch
  controls; rain falling indoors.
- **World:** no trees, three repeated bushes, blank pavement blocks, a ten-building town, a
  four-shed harbour, flat identical ground everywhere.

# Files to touch

- Engine (`*.gd`): re-synced to the current `godot-tmpl-rpg` template via `sync-engine.mjs`
  (fixes upstream: NPC grounding, floor registry for interior dressing, auto plinth with a door
  slot, hero attack clip length, vehicle climb on grades, indoor rain probe, untextured-prop
  material repair, `boss` block, `activity`/`holds`/`seated` NPC vocabulary). No hand patches.
- `structures.json` — Structures specialist: chapel redesigned as nave + porch + chancel + tower,
  14 new Mason types (chandlery, fish market, warehouse, farmhouse, barn, engine house, ...),
  existing enterables reviewed. Recompiled with Mason (windows now glazed) → `models/mason/`.
- `world.json` — Architect specialist fill pass (biome zoning, ground presets, new buildings,
  lanes/tracks, walls/fences/hedges/steps/clutter, underpin rows removed) → my generator adds
  biome vegetation scatter (trees/gorse/heather/bracken/rocks/grass), Meshy props, the cove/boss
  rework (`boss` block inside the cave, ≤6 live enemies, checkpoint + `player_died` → `respawn`),
  NPC `activity`/`holds`/`seated` fixes → Dressing specialist interiors (`pos` y from the FLOOR).
- `models/meshy/` — Meshy specialist: interior furniture kit, chapel fittings, harbour clutter,
  hand prop, coastal vegetation.
- `quests.json` (descs), `README.md`, `docs/qa_report.md`, `docs/gamefeel_report.md`.

# Verification approach

- Mason walk gate on every compiled building; `GOGI_THRESHOLD_STEP` must not print for any
  enterable at its placed site; interior-fit gate (`check-interiors.mjs`) on the dressing.
- qgcheck winnability; `verify.mjs` smoke + FEEL + packaging/GPU/engine-currency gates on the
  shipped `out/` (exit 0).
- Targeted checks: hero facing, attack HP delta + particles, enemy engages, boss spawns INSIDE the
  cave, chapel walk-in, truck climbs the switchback, portrait + landscape fill.
- Game-Feel + QA specialist passes on the content-complete export; P0/P1 remediated and re-proven.

# Out of scope

- Multiplayer / auth / Supabase (single-player, `user://` saves).
- Terrain re-sculpt (heights are kept so every existing building stays grounded).
- Any engine `.gd` patch — engine defects are reported under ENGINE BUG in the PR body.
