## What changed

**The broken things**
- **Interiors** — every enterable building re-dressed by the Dressing specialist against the engine's floor registry (`pos` y measured from the interior floor, not the hillside): the Kestrel Arms gets a bar, back-bar, stools, four tables with tucked chairs, a fireplace, coat rack, three furnished rooms upstairs; the harbour office a chart-covered desk, captain's chair, ledger shelf, coat rack, fireplace and a furnished upper office; chandlery, house, net shed, chapel, lighthouse and the new market hall are all furnished. 28 new Meshy props (bar counter, back-bar, stools, pub tables/chairs, harbour desk, ledger shelf, pews, altar, lectern, iron bed, wardrobe, dresser, washstand, coat rack, rope coils, buoys, anchor, churns, cart, trough, hand-held net…). **Every `props/vostok_extra/*` reference was removed** — those kits ship with their textures stripped and render as white plastic (see ENGINE BUG 1); library substitutes are mod_village / mod_house / kenney (all coloured/textured). Interior-fit gate (`check-interiors.mjs`) clean.
- **Windows** — all 30 Mason buildings recompiled with the current Mason (auto-glazed panes on every window).
- **Chapel** — redesigned by the Structures specialist as porch → tower base → nave → chancel with a slate spire; then shrunk to 15.9 m because the engine scales any placed model wider than the 16 m cell down to the cell (the 26.9 m version rendered at 59 % with a 1.25 m door — see ENGINE BUG 6). The hilltop is flattened with a terrain `basin` so the whole footprint sits on level ground; the hand-authored "underpin" blocks that sealed the old doorway are gone (310 rows removed). Pews (sittable), lectern, altar, verger inside.
- **Seated NPCs** — Dai, Old Hal and Jory are `seated: true` on `sit: true` seats (Dai on the bench outside the pub door; the bar stools no longer steal the USE prompt from Morwenna).
- **The cove** — the ringleader is a `boss` block standing inside the cave's main chamber (reserved slot, authored position); five regular smugglers so the live-enemy budget is never exceeded; rifle range/damage lowered; a checkpoint region "The Cove Path" (`set_spawn [160,0,-22]`) and a `player_died → respawn` rule so death returns you to the cove path, not the harbour; contraband chest inside the main chamber; the run is won by a rule on `quest_done smugglers` (the director's boss bar/victory were removed — ENGINE BUG 3/8).
- **Hero swing / NPC mimes / truck stall / frozen or runaway touch controls / rain indoors** — all engine-side and fixed by re-syncing the engine to the current `godot-tmpl-rpg` template (`sync-engine.mjs`: hero attack plays the rig's full clip, `_release_touch_state`, vehicle gradient climb, indoor rain probe, NPC grounding). Pasco has `activity: idle_work` + `holds: mending_net_hand.glb`.
- Doorsteps of the four enterables that stand on 24° banks (harbour office, net shed, lighthouse, wreck) get a levelled apron (`basin` terrain features) so the threshold is a step, not a slope; colliding underpin boxes under every building with a real drop (14, filled per quadrant where the ground falls away under one end) so nobody walks under a raised floor.
- **Sea cave grounding** — the cave straddles a N–S gully with both banks ~2.4 m above the arch approach, so grounded at the approach its floor sat up to 1.6 m under the bank terrain along the E/W walls: a climbable wedge inside the chambers (QA round 3 got out through the SE wall over a stack of drums). A `cone` terrain feature under the arch approach (a shingle bank) lifts the floor above every interior terrain sample (headless engine probe: max +0.13 m at the mouth's west wall, main/back chambers −0.1..−2.0 m). The den dressing (drums, campfire, crate, tent), the ringleader and the contraband chest all sit inside the cave's own cell in the main chamber, ≥2 m off a wall (USE range is 2.9 m and the engine has no line-of-sight test, so the chest can no longer be opened through the wall).

**The world**
- Architect fill pass: every one of 1024 cells carries a `biome` (quay, town, garden, field, farm, wood, copse, heath, moor_rock, marsh, road_verge, headland, cliff, shore, inlet, sea) and a matching ground preset (cobbles, gravel, mud, sand, rock, heather-brown grass…).
- 115 Mason buildings (from 28): chandlery (enterable), Fishermen's Institute + square, market hall (enterable), warehouse, terraces, townhouses, cottages, five farmsteads (farmhouse/barn/stable/pigsties), two Cornish engine houses on the moor, three coastguard lookouts, huts. Lanes and tracks to the farms, the moor and the headland; dry-stone field walls, hedged lanes, timber fences, quay wall and bollards, stone circles, sheepfolds, ~200 pieces of quay/street/yard clutter.
- Vegetation: ~1270 placed trees and boulders (trunk colliders) and 19 scatter species per biome — Meshy windswept hawthorn, gorse, heather, bracken; textured library trees, ferns, rocks, grasses. No `q_trees` (those ship untextured too).
- Spawn moved onto the quay axis via the director mode `spawn` (`quay_spawn`), lane cleared, lifeboat house moved off the camera shoulder.

## Why
User request: "fix kestrel bay properly — the broken stuff AND the world itself".

## How I verified
- Mason walk gate 30/30; interior-fit gate clean; qgcheck winnable; `verify.mjs` on the shipped export: engine boots, console clean, FEEL collision OK, GPU memory 92 MB / 220 budget, pck 12.4 MB.
- Runtime probes on the export (headless Chromium + the shipped Godot binary): no `GOGI_THRESHOLD_STEP` at any enterable, rules `r_start`/`r_cove`/`r_cove_spawn` fire, enemies engage and damage, ringleader spawns inside the cave.
- Game-Feel specialist pass (`docs/gamefeel_report.md`) and three QA specialist passes (`docs/qa_report_round1.md` FAIL 2 P0 → `docs/qa_report_round2.md` FAIL 1 P0 → `docs/qa_report.md` **PASS**: the sea cave walked mouth → main → back, ringleader fought and killed, chest opened, respawn on the cove path). Round-3 residuals (P1-N3 cave wall exit, P2-A/B/C cave clutter + chest through the wall, P2-D Morwenna talk band) are fixed in data above; P2-E (the pub fireplace prop reads flat) is left as-is.
- Terrain cone validated with a headless `GTerrain.height()` probe on the shipped world.json (44 samples: arch approach, three chamber wall rings, the QA exit spot) — matches the Python model within 3 cm.
- Final `verify.mjs` on the shipped export: VERIFY PASSED (engine 70/70 current, scene-instantiation 36/36, qgcheck winnable, console clean, FEEL collision/streaming OK, 106 MB GPU / 220 budget).

## Preview
https://preview.myapping.com/cloud-q7026dnarajiwk7glrcg/

## What I could NOT exercise in-sandbox
Audio and TTS playback; real-GPU exposure/colour (frames are SwiftShader/llvmpipe — overcast daylight still reads bright there, luma-day ≈176: it is sky/aerial haze, not albedo); touch feel and frame pacing on a real phone (a 1–2 s hitch when a dressed cell first streams in was measured — GLB parsing on the single-threaded web build); the truck's full climb of the switchback (QA drove it on the fixed foot in round 2 — see report); the re-grounded sea cave was probed numerically and by the previous QA walk, not re-walked after the cone; lamp glow at night; the native iOS player.

## Known residuals (disclosed, not fixed)
- **Truck coasts forever** (`vehicle.gd:2085–2096` holds speed with no throttle; QA round 3 drove it off the quay and along the sea bed) — engine.
- The switchback's terrain plates read as kerbs at the hairpins (a hop, not a wall) — engine road builder.
- The Mason batter profile shaves the arch crown on the cave mouth (still 2.3 m clear).
- Pub fireplace prop (`Prop_Fireplace`, scaled 0.7) reads flat against the west wall.
- Vehicles aside, 4 library characters carry only idle/walk clips (no run) — verify WARN.

## ENGINE BUGS (escalated, not patched — `sync-engine.mjs` would overwrite any local fix)
1. `surfaces.gd` `_is_stripped` compares albedo to 0.8, but the glTF importer stores baseColorFactor 0.8 as sRGB 0.906 → `fix_untextured_props` never fires; every texture-less library kit (vostok_extra, q_trees) renders white. Compare against `Color(0.8,0.8,0.8).linear_to_srgb()` too.
2. `chunk_manager._register_floor_plate` runs only when a building's own cell builds, so interior dressing authored in a neighbouring cell (a 14 m pub spans four cells) resolves against the TERRAIN when that cell builds first — furniture sinks by the plinth height depending on approach direction. Register plates for every grid record at `start()`/`reload()`. Also `interaction.stand_player` grounds on `terrain.height`, not `_surface_y`.
3. `game_shell.gd:841` `_update_boss_bar` reads `live.get("max_hp")`; `enemy.gd` exposes `hp_max` → per-frame SCRIPT ERROR and an empty boss bar whenever a `director.boss` is within `show_within`.
4. `interaction._nearest`: a `sit` seat 0.5 m away beats an NPC 1.5 m away, so a barmaid behind a stool-lined bar cannot be talked to.
5. `chunk_manager._add_plinth`: the plinth is visual-only (no collider) and its door slot runs the full depth of the footprint, so on a bank the player walks under the raised floor and sees a doorway-shaped hole in the downhill face.
6. `chunk_manager._place_one` SCALE SANITY caps every placed model's footprint to the cell — including Mason building records that carry a `footprint`. A 26.9 m chapel became a 59 % doll's house with a 1.25 m door while every compile-time gate passed. Exempt records with `footprint`.
7. `_report_threshold` / `_door_ground_y` sample the face CENTRE rather than the opening's `centre` offset (the harbour office door is 2.2 m off-centre).
8. `game_shell` victory fires on `boss.kind` death regardless of quest state.
9. `interaction.add_npc` has no authored yaw — every NPC faces world +Z (Alwyn cannot stand behind his desk facing the door).
10. `GEquip` normalises a `holds` prop to weapon length (~1.1 m) — Pasco's 0.45 m hand net becomes a 1.1 m bundle.
11. Mason glazing panes are not in the collision shell, so a 0.9 m sill window is a hop-through hole (verify's FEEL collision probe jumped through the office window).
12. `chunk-reassemble.mjs` ignores `boss` blocks, so a `kill_count` objective on the boss type is unreachable to qgcheck — the "take down the ringleader" quest step had to be dropped.
13. Game-Feel (engine): interior camera collapses to a hero-filling frame under 3 m ceilings; default pitch puts the horizon at the top edge; `subtitle` slot overlaps the thumb buttons; `stats` label has no shadow; quest label ~9 px on a 390-wide phone; boss bar overprints stats/minimap in portrait; chain toast pre-empted by the region toast.
14. `world-streaming.md`/`cellmap` doc gap that bit this build: a cell's centre is `gx*16+8`, not `gx*16` — every terrain-relative check in the first pass was half a cell off.
15. `vehicle.gd:2085–2096` — with no throttle input the truck holds its speed indefinitely (no drag/brake), so a nudge off the quay drives it along the sea bed.
16. `interaction._nearest` has no line-of-sight test — a chest/NPC within 2.9 m is usable through a wall.
17. `chunk_manager._door_ground_y` grounds an enterable at the LOWEST approach sample only; on a building that straddles a gully (both banks higher than the door) the interior terrain rises through the floor. A per-footprint check (floor vs max interior terrain) at placement, or a `floor_z` lift, would catch it; this build works around it with a terrain `cone`.

## Follow-ups
- Sea caves still read as faceted stone chambers rather than rock (Mason vocabulary); a Meshy cave mouth would be the upgrade.
- Boat hook uses `parametric:staff` (a staff with an orb); a Meshy boat hook item would fit better.
- Truck `seat` offset (driver's head clips the cab roof).
- Cross-cell dressing (ENGINE BUG 2) — once the engine registers plates up front, move Dai back to his bar stool.
