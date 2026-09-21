# QA REPORT — KESTREL BAY, round 3 (narrow re-verification of the round-2 sea-cave P0 [FIXED] + P1-4 [FIXED])

**VERDICT: PASS**

Scope (as delegated): the round-2 P0 (sea-cave main chamber sealed — now FIXED) and P1-4 (Morwenna untalkable), plus a sanity look at the sky cycle / truck corridor. Everything else carries its round-2 status (`docs/qa_report_round2.md`) — restated in the table below so verify.mjs has one current file.
Tested build: `/workspace/repo/out` — `index.pck` unchanged (19:56), `world.json` / `quests.json` / `models/mason/40d9e2c2c50b.lod0.glb` 02:44. Every engine `.gd` in `/workspace/repo` is byte-identical to the `/tmp/qa_proj` copy the probe runs in (only `project.godot` differs by my test autoload; `structures.json` by the Mason re-spec). `/workspace/repo` was NOT modified.
Harness: (a) vetted `verify.mjs` on the export → `/tmp/verify_r3.log`; (b) Godot 4.7.1 + `qa_probe.gd` test autoload under Xvfb/llvmpipe against a local mirror of the export (`verify/qa/server.mjs`), driving the REAL player with synthesized W input (`walk_to` = held W + cam yaw), real `interaction.try_use()`, `enemy.take_hit()`, physics rays and free-camera renders — scripts `verify/qa/s3_cave.json`, `s3_cave2.json`, `s3_cave3.json`, `s3_pub.json`; logs `/tmp/qa_{cave,cave2,cave3,pub}_r3.jsonl`; screenshots `verify/qa/shots2/R3-*.png`. 4 engine runs, **0 `SCRIPT ERROR`s**.
**This file must be committed to `docs/qa_report.md`** — that path still holds the round-1 report (`VERDICT: FAIL (3 P0)`), which is what makes `verify.mjs` FAIL today (`/tmp/verify_r3.log:14`). With this file in place there is no open P0 row.

---

## The two items under re-test

### P0-3 — sea-cave main chamber sealed / arch blocked / terrain through the floor → **FIXED** (walkable end-to-end; residuals re-filed as P1-N3 + P2s below)
Geometry used (cell (10,-4) centre (168,-56); cave origin world (161.71,-61.88), rot 19.4°; rotation x' = x·c + z·s, z' = −x·s + z·c — sense confirmed against the round-2 arch position): **arch** (mouth s face, local (−2.0,−5.65)) ≈ world (157.95,−66.54), outward normal (−0.33,−0.94); **mouth centre** (159.16,−63.10); **main centre** (164.39,−62.40) (= the new basin centre); **back** (158.99,−57.85); **chest** (166.62,−61.49); **boss** (164.39,−62.40). Cave floor y = **1.52** (player standing) / `_surface_y` 1.57.

Real-movement legs (held W, no teleport, no jump), `/tmp/qa_cave_r3.jsonl`:

| Leg | From → to | Result |
|---|---|---|
| L1 outside → arch | (156.28,1.84,−72.37) → arch | **reached** (157.85,1.77,−66.89), rem 0.37, no wall |
| L2 arch → mouth centre | → (158.70,1.52,−63.21) | **reached**, rem 0.47 (`wall:true` = the ringleader standing 0.7 m away, not geometry) |
| L3 mouth → passage (161.8,−62.75) | → (161.40,1.52,−62.76) | **reached**, dy 0 |
| L4 passage → main | → (162.83,**2.37**,−62.93) | **reached** — but dy +0.86: the player climbed onto the `Prop_Crate_1` at (162.49,−62.68) that stands in the middle of the passage (P2-A). Re-run `s3_cave2`: north route (162.6,−61.2) and south route (162.6,−64.1) both **reached with dy 0.00** — the passage is walkable either side of the crate |
| kill | `take_hit` ×2 → ringleader 150 → 67.5 → dead (2.0 m); r_boss fired | ok |
| L5 main → chest | → (165.62,1.52,−61.88), prompt **`USE > Open Chest`** | **reached**; `try_use()` → `rpg.inventory = [boat_hook, contraband]`, Gold 200, "You opened the chest." (`R3-C04-at-chest.png`) |
| L6 chest → main centre | → (164.85,1.52,−62.20) | **reached** |
| L7 main → mouth | → (159.58,1.52,−63.03) | **reached**, dy 0 — the round-2 double wall at x 160.3–160.9 is gone |
| L8 mouth → arch | → (158.12,1.67,−66.19) | **reached** |
| L9 arch → outside 5 m | → (156.43,1.82,−70.88) on sand | **reached** |

- **Voids join:** `R3-C02-mouth-toward-main.png` shows one continuous room mouth→main (crate, chest, drums, tent visible from the mouth). Round-2's 16-ray "closed alcove" is gone.
- **Arch clear height:** horizontal rays along the arch normal (3 m out → 3 m in) pass at y ≤ **3.60** and hit the wall/crown at y ≥ **3.65** (`arch_thru_y*`, both runs). Down-rays: terrain sill at the arch line **1.75**, 1 m outside 1.81, 1 m inside 1.66, cave floor 1.57 → **clear height ≈ 1.85 m over the sill / 2.05 m over the floor**; the hero (1.784 m) walks through both ways without a jump. (Spec crown was 2.5 m over the floor — the battered wall shaves ~0.45 m; fine for play, note if you want the arch to read taller.) Side rays: the west jamb sits ~0.6 m from my computed centre, the east side is open past 0.9 m → the real arch centre is ≈ 0.3–0.4 m east of the nominal x −2.0; the opening is the full 2.0 m wide. Threshold: 0.18 m step DOWN into the cave — inside budget.
- **Apron clear:** `items near 14` at the approach = 0 props; `R3-C01-arch-approach.png` / `R3-C06-cave-exterior.png` show open sand in front of the arch (the round-2 boulder + oil drums are gone). One smuggler crouches beside the arch — that's the encounter, fine.
- **Terrain through the main-chamber floor — REDUCED, NOT GONE.** `_ground_y` grid over the main void (floor 1.57): centre/west/chest side are now UNDER the floor — (162.39,−62.4) 0.75, (164.39,−62.4) 0.87, (164.39,−65.4) 1.43, at the chest ≈ 1.40 (0.17 m under). But the **east quarter still pokes through**: (166.39,−63.9) **1.71** (+0.14), (166.39,−65.4) **2.10** (+0.53), and at the inner wall line (168.39,−62.4) **2.40** (+0.83), (168.39,−65.4) 3.09. Walking to the SE corner the player rises **+0.67 m** onto a sand slope (`W_to_SE` end y 2.19, `X1` samples y 2.05–2.44). Visually a grey sand wedge covers ~¼ of the far floor and half-buries the campfire + tent legs: `R3-C14-SE-interior-wedge.png`, `R3-C09-main-E-wall.png`, `R3-C08-main-SE-corner.png`. The basin (r 9, depth 1.0) is centred on the main centre while the hillside rises to the east; the wedge is now where it lets the player leave the room through the wall (P1-N3 below). Fix: extend/deepen the basin toward the east wall (centre ≈ (166.5,−63), r 10, depth 1.8) or add a second basin at (167.5,−64.5) r 5 depth 1.2, and re-check `_ground_y ≤ 1.4` across the whole 10.4×8 void.

### P1-4 — Morwenna cannot be talked to from the customer side → **FIXED** (narrow band; see P2-D)
`/tmp/qa_pub_r3.jsonl`, pub cell resident, quest state real (Alwyn talked first → `settle_in` active, `talked.harbour_master`):
- Parametric bar slab gone: `items near 5` lists only Meshy seats, the door, the bar stool and `npc Talk to Morwenna` at (−14.9, 26.22, 90.45); Morwenna stands between the Meshy counter (−15.4,91.1) and the back bar (−15.4,89.4), on the floor (26.22 = floor) — `R3-P04-morwenna-side.png`, `R3-P01-bar-from-customer.png`.
- USE prompt by position (player standing, cell settled): **(−14.9,92.6) → `Talk to Morwenna` ✅**, **(−16.0,92.6) → `Talk to Morwenna` ✅**, (−13.5,92.6) → `Sit` ❌ (the `bar_stool` at (−12.5,92.0) is 1.17 m away and wins), (−14.9,93.2) → `Sit` (pub_t1 chair (−15.0,94.8) at 1.6 m wins), (−13.5,93.2) / (−12.5,93.0) → `Sit`.
- **Real path:** walked from the door (−11.5,97.5) with held W to the counter (end (−14.75,92.82), slid to (−15.15,92.24) against the counter face) → `try_use()` → prompt **"Morwenna is speaking..."**, dialogue shown (`R3-P03-talk-dialog.png`) → dismiss → `quest.st.settle_in.status = "done"`, `talked = {barmaid, harbour_master}`, `rpg.flags = {met_town: true}`, `smugglers` → active, HUD shows the Marguerite steps. **Quest step 2 starts from the customer side.**
- Caveat (not a P1 any more, filed as P2-D): the "Talk" band is only the strip pressed against the counter, x ∈ [−16.3, −14.2], z ∈ [~92.2, 92.6]; one step east or back and the stool / t1 chair win under the engine's pure nearest-wins rule (`interaction.gd:523`, escalated engine item #4). The coordinator's second test point (−13.5,92.6) does NOT give "Talk".

---

## ❗ NEW P1 — must-fix (below P0; does not gate)

- **P1-N3 The player can leave the cave through the SE wall of the main chamber, and the "smugglers' camp" dressing is half OUTSIDE the cave.** Reproduced 2/2: from inside at (165.73,1.52,−63.94) walking toward (169,−66) the player climbs the terrain wedge + the oil drums at (167.51,−64.98) (y 2.05 → 2.44 → 3.53) and ends **outside** the cave on the sand at **(168.70,3.53,−65.89)** (`X1`, `R3-C11-after-SE-walk.png`); the earlier run did the same from (166.06,−65.09) → (168.52,2.83,−62.43) (`W_to_E`, `R3-C10-gameplay-in-main.png` — hero standing beside the exterior east wall). From outside the wall holds (`X2` blocked at (167.73,3.75,−64.77)). Contributing data errors, all visible in `R3-C13-SE-exterior.png`: the (10,−4) `Tent_Leanto_2` at cell-local [1.143,−5.847] → world (169.14,−61.85) is **outside** the main void (structure-local x ≈ 4.3 vs an interior half-width ≈ 4.4 on a 10-gon → in/through the wall); cell (10,−5)'s cross-cell `Prop_Crate_1` [1.727,7.297] → (169.73,−64.7) stands **outside** the east wall; its `oil_drums_rusty` [−0.491,7.018] → (167.51,−64.98) sit in the wall line on the terrain wedge (grounded at ~2.1, not the 1.52 floor — the disclosed cross-cell floor lottery) and act as a step; a gorse bush grows through the wall; the campfire is half-buried in the wedge. Fix (data): move tent/crate/drums inside the void (structure-local |x| ≤ 3.2, |z| ≤ 2.4 for `main`, or into `back`), remove the (10,−5) cross-cell "furn" pair, exclude scatter from the cave footprint, and kill the wedge (P0-3 fix above) so nothing inside stands higher than the floor. Owner: Interiors/Dressing.

## ⚠️ P2 — polish (new this round)

- **P2-A** `Prop_Crate_1` at (10,−4) [−5.513,−6.684] → (162.49,−62.68) stands dead-centre in the 5 m mouth↔main join; the player walks up onto it (L4 dy +0.86, `R3-C03-main-chamber.png`). Shift it to the wall.
- **P2-B** The contraband chest can be opened from OUTSIDE the cave: standing on the sand at the east wall (168.53,2.83,−61.72) the prompt is `USE > Open Chest` (chest 1.9 m away through the 0.7 m wall — `X3`, `R3-C10`). Engine: `interaction._nearest` has no line-of-sight test (escalation list). Data mitigation: move the chest ≥ 3.5 m from every exterior wall (e.g. into `back`).
- **P2-C** A scatter `Rock_Medium_2` from cell (9,−4) pokes into the mouth chamber through its west wall (`R3-C07-mouth-out-through-arch.png`, big green boulder left of the arch); (9,−4)/(11,−4) still carry `Rock_Medium_2 count 3` scatter. The interior floor plate is a 15.8×11.3 rectangle under polygonal chambers, so tiled floor corners protrude outside the walls (`R3-C01` left of the smuggler, `R3-C13` right of the drums).
- **P2-D** Morwenna's "Talk" band is ~2 m × 0.4 m (see P1-4). Move `pub_t1` another ~1 m south (chairs z ≥ 95.8) and the `bar_stool` to the counter's east end (x ≥ −11) so "Talk" wins for x ∈ [−17,−13] out to z ≈ 93.5.
- **P2-E** Pub fireplace (`Prop_Fireplace`, cross-cell from (−2,5)) renders as a flat pale-lilac block against the west wall (`R3-P01`, `R3-P04`) — reads untextured next to the Meshy furniture.

---

## Round-2 findings — status carried into this round (unchanged unless noted)

| # | Finding | Status |
|---|---|---|
| P0-1 | Chapel porch door / step | **FIXED** (round 2) |
| P0-2 | ~1,650 white untextured props | **FIXED** (round 2) |
| P0-3 | Sea-cave main chamber sealed | **FIXED** this round (walked arch→mouth→main→chest→out; residual wedge/escape re-filed as P1-N3, P2-A/B/C) |
| P1-1 | Dai sits on nothing | **FIXED** for Dai; cross-cell floor lottery = disclosed ENGINE residual |
| P1-2 | Pews through the nave wall | **FIXED** |
| P1-3 | Truck blocked at the switchback foot / head through cab roof | **PARTLY FIXED**; foot still fiddly (P1-N2), head still through the roof — not re-tested this round |
| P1-4 | Morwenna untalkable from the customer side | **FIXED** this round (narrow band → P2-D) |
| P1-5 | Pasco knee-deep in the quay | **FIXED** |
| P1-6 | Daylight bleaches the quay white (web/SwiftShader) | **STILL OPEN** ❗ — verify `luma-day.png` mean **176.6** this run (round 2: 174.3; round 1: 177), `frame-after-move` 192.0: the quay is still a flat white plane under the hero on the shipping renderer; llvmpipe also clips the beach sand to pure white in `R3-C13-SE-exterior.png` (lower half of frame). Sky cycle is now cloudy/rain/storm (no overcast/fog) — the change did not move the metric. Target `luma-day` mean ≤ ~120: lower cloudy/rain `bright` and `aerial` for near ground. |
| P1-7 | Caves read as an ashlar hut, wreck a plank box, thin interiors | NOT CHANGED — disclosed; the cave interior is still white bathroom tile + ashlar (`R3-C02`) |
| P1-8 | Victory on boss kill regardless of quest | **FIXED** |
| P1-9 | `game_shell.gd:841` error spam | **FIXED** data-side; ENGINE line still wrong (disclosed) |
| P1-10 | Plant_7 on roads | **FIXED** |
| P1-11 | Cove kills in seconds | CHANGED per data, not re-measured (probes run in god-mode) |
| P1-12 | HUD stats illegible over sky | NOT CHANGED — ENGINE (disclosed) |
| P1-N1 | Truck never coasts down / drives along the sea bed | **ENGINE BUG** `vehicle.gd:2085–2096` — disclosed, not patchable here; still open |
| P1-N2 | Switchback foot is a kerb; parking spot hemmed | **PARTLY ADDRESSED**: `items near 12` at the truck (36,28) now lists only `Drive Truck` + one bench 8.3 m away at (29.2,19.2) — the harbour bench/lamp on the (30,30)→(58,58) corridor are gone. The plate-seam kerbs at the switchback foot were not re-driven this round → remains open as filed. |
| P2 (r2) | Step-up climbs 0.6–0.95 m props; counter slab half-sunk; grass through chapel floor; terrace niche doors; yellow-cube chests; driver's head through the cab; verify perf worst-frame | Counter slab: **REMOVED** (this round). Step-up onto props: still reproduces (crate L4 +0.86, drums → P1-N3). Others unchanged. |

---

## ✅ Passed / verified this round

| Check | Result / evidence |
|---|---|
| Boot, canvas, console (verify.mjs, `/tmp/verify_r3.log`) | `PASS engine booted`, `PASS canvas present`, `PASS console clean`, scene-instantiation 36/36, qgcheck **winnable (data graph, 1024 areas)**, audio infra present, GPU mem 104 MB / 220, `FEEL streaming OK`, `FEEL spawn clear`. Only FAIL = the stale round-1 `docs/qa_report.md`. `FEEL perf worst frame 1900 ms` (real streaming stall, as in round 2). Bug-class lint still crashes (`rows is not defined` — harness issue). |
| Cave threshold both ways, real movement | L1–L9 above; arch 2.0 m wide, ≥ 1.85 m clear, 0.18 m sill step. No jump used. |
| Cave quest objective reachable on foot | Chest prompt + `try_use()` → contraband in inventory, 200 gold; ringleader killable in the room (`take_hit` path). |
| Morwenna talk path | Real walk + USE from the customer side → dialogue, `settle_in done`, `met_town`, `smugglers active`. |
| Pub bar dressing | Meshy counter + back bar + stool textured; no parametric slab; Morwenna on the floor behind the counter (`R3-P04`). |
| Truck corridor | Parking spot clear within 12 m except one bench 8.3 m away (`truck_items`). |
| Sky cycle sanity | world.json `sky.cycle` = cloudy 150 s → rain 140 → sunset/storm 70 → night/rain 110 → sunrise/cloudy 60 (no overcast/fog). verify `luma-night` mean 52.6 (readable), `luma-day` 176.6 (still bleached — P1-6). |
| Console | 0 `SCRIPT ERROR` in 4 engine runs + verify. |

## Could not verify (sandbox limits / out of this round's scope)
Real-GPU exposure of the quay/beach bleach (two software renderers still disagree in degree but both clip), audio playback, touch feel, live preview URL, the switchback foot drive (P1-N2) and truck coast-down (P1-N1 — engine), cove difficulty feel (god-mode probes), mobile fill / camera orbit / W-S facing (pck unchanged — round-1 results stand), lamp glow at night, Supabase/wss.

## ENGINE BUGS to escalate (PR body heading `ENGINE BUG` — do not patch locally; `sync-engine.mjs` overwrites these files)
1. `vehicle.gd:2085–2096` `drive_input_world` — zero input holds speed forever; no water/shore handling (P1-N1).
2. `chunk_manager.gd:3303/3333` + `interaction.gd:766` — cross-cell dressing grounds on terrain, not the host floor (the (10,−5) drums at y 2.1 inside the cave, round-1 P1-1).
3. `game_shell.gd:841` `live.get("max_hp")` → `hp_max` (round-1 P1-9).
4. `interaction.gd:471–527 _nearest` — pure nearest-wins (a stool at 1.2 m beats an NPC at 2.6 m) and **no line-of-sight test** (chest opens through a 0.7 m wall — P2-B).
5. `surfaces.gd:155–204` `_is_stripped` fingerprint (root cause of the round-1 white-props P0 — RESOLVED data-side for this build).
6. `main.gd` step-up/slope handling climbs 0.6–0.95 m props (crate, drums, pews, counters) — the mechanism behind P2-A and half of P1-N3.
