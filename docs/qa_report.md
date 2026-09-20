# QA REPORT — KESTREL BAY (chunk-mode open world, godot-tmpl-rpg engine)

**VERDICT: FAIL (3 P0)**

Tested build: `/workspace/out` (index.pck 00:52, world.json as served — note the coordinator kept editing `world.json` during this QA: 01:43 → 01:51 → 03:21; structure/cells/NPC data identical across those revisions apart from the `rusty_sword`→"Gutting Knife" rename and ~7 KB of edits, so every finding below still applies to the current file).
Harness: (a) headless Chromium/SwiftShader on a local server that mirrors the live paths (`/cloud-…/` + `/godot-assets/` + engine proxied — the live URL itself serves an App-Store interstitial, not the game, so it cannot be driven), driving the real game with the on-screen USE/ATTACK buttons, KeyW/S and right-half drags (`/workspace/verify/qa/server.mjs`); (b) the shipped `/workspace/godot` binary running a **copy** of the project under Xvfb+llvmpipe with a test-only autoload that teleports the real player, synthesizes key input, calls the real `interaction.try_use()` / `main._attack()` and takes free-camera screenshots (`/tmp/qa_proj/qa_probe.gd`; the project in `/workspace` was NOT modified). Screenshots: `/workspace/verify/qa/*.png` (web = `NN-*.png`, native free-cam = `N##-*.png`).

---

## ❌ P0 — ship-blockers

### P0-1  Every authored NPC is buried underground — harbour master, barmaid, pub regular, both seated fishermen, netman, keeper, verger are INVISIBLE
- **Symptom:** "USE > Talk to Alwyn Rees" appears inside the harbour office and the talk fires (r_talk_master, TTS queue), but nobody is there (`12-inside-office.png`, `14-after-talk.png`, `16-office-floor-*.png`). Pub: "Talk to Morwenna"/"Talk to Dai" prompts, empty room (`N07`, `N08`, `N09-pub-*.png`). Quay benches empty (`N11-bench-oldsalt.png`). **Proof:** free camera placed UNDER the quay shows Old Hal sitting in mid-air 1.5 m below his bench (`N12-bench-underground.png`).
- **Evidence (native probe, model node global y):** harbour_master (25.89, **0.00002**, 18.11) vs terrain 2.54 / office floor 4.13; old_salt (1.38, **0.00004**, 5.62) terrain ≈1.6; deckhand (40.06, **0.0001**, 36.94); netman (20.83, **0.00005**, 15.0); barmaid/regular pos y 25.80 with the model likewise dropped to ≈0 (pub floor 26.22). All 8 authored NPCs sit at world y≈0. The `populate` wanderers (different code path) are fine (y 1.9–2.7).
- **Root cause:** `interaction.gd:add_npc` line 164 — `m3.position.y -= _subtree_aabb(m3).position.y`, but `_subtree_aabb` (line 1069) returns a **WORLD-space** AABB (`mi.global_transform * mi.get_aabb()`), so it subtracts `pos.y + local_min` and the model lands at `-local_min ≈ 0`. Secondary: NPC/chest y comes from `_ground_y` (terrain) not the interior floor (`chunk_manager.gd:1193, 1209`) — even with the AABB fixed, the harbour master would be 1.6 m under the plinth-raised office floor (floor 4.13 vs terrain 2.54) and the pub pair 0.4 m under theirs.
- **Side effect:** the invisible NPC capsule colliders (`add_npc` line 169–178, at terrain height) block the player as invisible walls (hit one at the lighthouse door: stuck at (-130.85,152.12) `wall=true` with the keeper 1 m away).
- **Fix:** subtract a LOCAL aabb (compute before `add_child`, or `aabb.position.y - m3.global_position.y`); seat NPCs/chests placed inside an `interior` building on the interior floor (ray down from `floor_y + 1` or use the landmark's grounded origin + `floor_z`). Also seat the pub bench that is sunk to its rail in the floor (`N09`).

### P0-2  The chapel cannot be entered (or left) — its own plinth/step block fills the lower half of the arched doorway
- **Symptom:** door opens ("USE > Close Door") but the player is blocked at z=151.09 (`wall=true`) from outside; teleported inside (floor 35.7) the player is blocked at z=152.17 walking out. Screenshot `N23-chapel-door.png`: a ~1 m stone block sits in front of the arch and the visible clear opening above it is ~1 m.
- **Evidence:** rays at x=20.3: z=150.0/149.0 terrain 35.76; z=150.5/151.0 top surface **36.72** (plinth body); door pivot y 35.75; interior floor 35.70. Outside ground = plinth top 36.67 → head hits the arch soffit; inside → 1 m step up that CharacterBody3D cannot climb.
- **Root cause:** plinth/underpin grounding of the chapel (cell [1,9], `pos [-4,7.5]`, footprint 20×26 on the cone hill) — the plinth is drawn/collided across the door face instead of stopping at the threshold; the building itself is seated ~1 m below the terrain at its door.
- **Fix:** ground the chapel at its door threshold (like the office) and cut the plinth at the door bay, or drop the plinth on the door face. Re-verify by walking in through the arch and back out.

### P0-3  The world reads as a grey-box prototype, not the "wet timber / rusted metal / proper detail, not flat grey boxes" town that was asked for
(world-streaming DENSITY FLOOR + geometry.md/art.md ambition bar; the verifier itself flagged SPARSE ~0.2 content/cell and 10 % filled)
- **Ground is a flat untextured plane over most of the map:** the cell `ground` presets **`"rock"` (170 cells — every cliff) and `"cobble"` (25 cells — the whole quay + town streets) do not exist in `surfaces.gd:SURFACES`**, so `_resolve()` falls back to the default flat grey mottle. The cove/cliffs render as smooth white-grey snow slopes (`N01-harbour-wide.png`, `N02-harbour-toward-sea.png`, `07-horizon-b.png`), the quay as a white plane (`05-quay-2.png`). Fix: use real presets (`stone`/`concrete`/`asphalt`/`sand`) or dict specs with a pattern.
- **Key buildings read as flat dark boxes:** net shed & boathouse are 18×10×5.5 m dark-brown slabs with faint plank lines and 3 window holes (`N03-netshed-close.png`, `07-horizon-d.png`, `N02`); the wreck is a flat light-grey shoebox with a deckhouse — nothing says "wrecked trawler run aground" (`N19-wreck-inside.png`); stone buildings are LEGO-ashlar boxes with unframed rectangular holes (`07-horizon-c.png`, `N06-highstreet.png`). Interiors are empty stone rooms — the pub has no bar/tables (`N07`), the office no desk.
- **Sparse:** the harbour is 4 sheds + truck + ~12 props; the town is ~10 buildings around one junction with large empty pavement blocks (`N05-town-wide.png`). No quay wall/jetty structure — the dock props are two flat plank pieces on the sand (`N11`).
- **"Switchback" road is a diagonal chain of `dir:"x"` crossroad slabs with dead-end stubs, on a 30–57 % grade** (ray-sampled: 5.3→13.3 m over 16 m, 13.3→19.2 over 16 m) — reads as grey plus-signs laid on a white hill (`N14-switchback.png`).
- **Palette contradicts "grey and rainy":** plateau is lurid spring green with red `Bush_Common` blobs (`N05`, `N18-lighthouse-ext.png`).
- **Scatter scale:** grass tufts are ~person-height next to the pub (`N06`), bushes near the lighthouse read building-sized (`N18`); rocks are flat pale cubes and several **float on the water surface** in the cove (`N22-boat.png`).
- What IS good: Meshy props/vehicles/characters (truck `N13-truck.png`, boat `N22`, bench, lamp, lobster pots, net pile, hero, seated fisherman model) are on-style and textured.

---

## ❗ P1 — must-fix

- **P1-1 Net shed quay-side door hangs 2.5 m above the quay.** Shed origin/floor y≈4.5 (grounded at the uphill door); terrain at the 'n' door (11.06,12.46) is 1.97 → the door is a hole in the wall above head height with no steps; no USE prompt from the ground (`20/21-netshed-door*.png`, `N03`: door outline above the underpin ledge). The 3 "underpin" rows (17.7 m timber slabs, 2.1–2.7 m tall) show as big ledges with bright top faces (`03-start-landscape.png`, `05-quay-a.png`). Same pattern (smaller) on the harbour office and boathouse.
- **P1-2 Wreck interior needs a JUMP to enter and the shotgun chest is buried.** Through the hull opening the player is stopped at (148.1,-85.8)/(149.0,-83.2) `wall=true` — a 0.4 m step (threshold 2.8 → deck 3.2) CharacterBody3D can't climb; only a Space-jump gets past. Shotgun chest at y=2.06 (terrain) vs deck 3.19 → 1.1 m under the deck, opened only by proximity ("Open Chest" at 1 m). Quest step "gun" depends on this.
- **P1-3 Boss may not spawn / cave appears empty.** `chunk_manager.gd LIVE_ENEMY_BUDGET := 6` but the inlet authors 3+3+2+1 = 9 across 4 adjacent cells. Approaching from the wreck side (the quest's route) spawns 3 melee + 3 rifle and **no ringleader** (all 4 camp cells resident, `enemies=6`, kinds all `smuggler`); approaching from the cave side spawns the ringleader + 5 rifles and no melee. Kill count needs 8 + boss → only completable by leaving the area and re-entering to respawn the camp. Also the ringleader spawns on the cell spawn ring at (167.8,-53.8) — outside the cave. Fix: ≤6 live per resident ring (e.g. 2+2+1+1) or spawn the boss inside the cave via a rule/`boss` block.
- **P1-4 "DEFEATED — TRY AGAIN" modal appears after the world's `respawn` rule already put the player back.** `main.gd:1387-1391` fires `player_died` (rule → `respawn_player` → `clear_defeat()` while `_lost` is still false) and THEN calls `_show_defeat()` → an input-blocking modal over a living, healed player (`N15-attack.png`); TRY AGAIN then `reset_run()`s the whole run, discarding the cove checkpoint. Fix ordering (show defeat first, then fire the rule) or skip `_show_defeat` when the rule respawned.
- **P1-5 Camera spring arm collides with the canyon walls all over the quay** → the camera is repeatedly shoved into the hero's face/back (`09-office-door3.png`, `19/21/23-netshed-*.png`, `05-quay-1.png`). Make the arm ignore terrain within ~2 m or shorten/raise the rig on steep ground.

## ⚠️ P2 — polish

- Quest step checkbox doesn't tick when a step completes: `quest.gd notify_talk/kill/area` never emit `objective_changed`, so "[ ] Find the Harbour Master" stayed unchecked after the talk until an unrelated refresh (`16-office-floor-b.png` vs `30-portrait-hud.png`).
- Lamp posts do not glow at night (`18-sky-now.png`, `N25-quay-night-eye.png`) — windows do; add emissive/omni to `lamp_post_harbour`/`MS_Pole_Light`.
- Template default weapon shows in inventory ("Rusty Sword" in the tested export; "Gutting Knife" after the 03:21 edit) — a knife the player never found.
- WEAPON > cycle button is dropped in portrait 390×844 (no room between minimap and grid); shown in landscape only (`03-start-landscape.png`). Chest auto-equip masks it.
- Vehicles can drive into the sea: the truck ran off the quay and ended at (-173,-9.7,-204) on the sea floor at the world boundary.
- Verifier WARN: 49 distinct GLBs > 32-entry streaming cache (thrash on roam); 4 skinned NPC models lack idle/walk sets (acceptable for seated/working poses).
- Interiors are blown to near-white under the room lights on llvmpipe (`N16`, `N17`) — judge on device, but consider lower `_room_light` energy for plaster interiors.
- HUD: `Inv:` line and quest text sit tight under the minimap in portrait but do not overlap; landscape OK.

---

## ✅ Passed / verified

| Check | Result / evidence |
|---|---|
| Boot, canvas, console | Engine boots on the mirrored server; **no SCRIPT ERROR / Parse Error / Uncaught** in web or native logs (only container audio/CORS noise). r_start fires. |
| Title → BEGIN → quay | Audio gate → title → BEGIN → HUD; `01-title.png`, `02-start-portrait.png`. |
| Movement + facing | KeyW walks (5.4 m/1.5 s); back to camera when walking away (`05-quay-1.png`), face to camera after walking toward it (`07-horizon-d.png`, `30-portrait-hud.png`). Run/idle clips resolve; no T-pose. |
| Camera orbit | right-half drag −100 px → cam_yaw +1.108 rad; pitch clamps sanely (`06/07-*.png`). |
| Input binding | ATTACK only from its button / `_attack`; look-drag and WASD never attack (project has no fire-on-LMB binding; `_input` only orbits). |
| Doors (Mason leaves) | Office/pub/lighthouse/house_e leaves prompt "USE > Door", swing, "USE > Close Door"; collider moves with leaf. |
| Harbour office | Enter via uphill door (27.5,13.4) → interior (26.5,4.14,17.9) → talk (r_talk_master toast, "Alwyn Rees is speaking…", `13-talk-master.png`) → walk back out. Wall collision: blocked at 4.9 m from centre with `wall=true` (`17-wall-push.png`); cannot walk under the downhill side (underpins are solid). |
| house_e | Enter (-33,97) → centre (-35.4,95) → out. ✅ |
| Pub | Both doors registered (items at (-12.09,98.02) & (-7.01,88.98)); interior reachable. Upstairs NOT walked (time) — stair spec present. |
| Lighthouse | 6 floors: stair flights continuous and open through each stairwell; walked 30.75 → 34.15 → 37.53 → 40.95 → 44.35 → 47.75 (top). `N16`, `N17`. |
| Truck | USE at (34,26.5) → `in_vehicle`, profile car; drives and steers (moved 8 m on W+A); Meshy body + wheels (`N13-truck.png`); driver hidden in cab (acceptable). r_boat fires on vehicle_enter. |
| Boat | USE at (-7.6,0.2) → boards; W for 13 s moved 70 m across the cove, rider stands on deck (`N22-boat.png`); dismount OK. |
| Enemies engage | At the inlet player HP 100 → 28 → death in ~25 s; melee smuggler closes to 1.6 m, rifles in cells (9,-5)/(10,-5) spawn with `attack_range 14`. Melee ATTACK: target hp 60 → 35 (boat hook 25). |
| World boundary | Terrain border walls exist (`_terrain_border_walls`); the runaway truck stopped at x=-173 against the -176 bound — world did not vanish. |
| Night/day | Night frame readable (moonlit ground, lit windows, silhouettes) `N25-quay-night-eye.png`; day exteriors not clipped (verifier luma clipped 0.0 %). |
| Mobile fill | 390×844 and 860×400 both fill all corners; HUD buttons inside the rect; no overlaps (`02`, `03`). |
| Native tier | `manifest.json webOnly:false`, world.json present; qgcheck green (static). |
| Character sourcing | Hero, all NPCs (incl. `default_npc_model`), enemies = Meshy (`models/meshy/*`); library used only for props/scatter. ✅ |
| Audio | AudioManager + bus layout present; `play_sfx("attack")`, region music/ambient authored. Playback unverifiable here. |

## Could not verify (sandbox limits)
Real GPU fidelity/exposure, audio + TTS playback, touch feel, the live preview URL (serves an App-Store interstitial in this container, so the deployed page was not exercised), pub upstairs walk, rifle smugglers actually firing from 14 m (they closed to melee range in the observed run), Supabase/wss.
