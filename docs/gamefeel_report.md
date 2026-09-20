# KESTREL BAY — Game-Feel / Mobile-UX review

**VERDICT: FAIL (0 P0, 6 P1)** — touch controls and the vehicle chase-cam are sound, but the phone player's
first minute is broken by UI/camera defects: the opening story text is never shown (clobbered by a raw region-id
toast), the default camera at spawn and around the harbour office is walled by a building slab / a net-pile prop,
the stats block is illegible over the pale stone the whole quay is made of, and the quest text renders at ~9 CSS px.
None of these is a ship-blocker class (touch is live, no full-frame mesh on every hit), all are must-fix before PR.

Evidence: every claim below was driven on the LIVE export (`…/cloud-cbnqgdi78kdlrr3elmbb/play` — byte-identical to
`/workspace/out/index.html` + `world.json`) in headless Chromium/SwiftShader with a touch-emulating mobile context
(CDP `Input.dispatchTouchEvent`), at **390×844 portrait** and **860×400 landscape**. Screenshots:
`/mnt/session/outputs/gamefeel/*.png` (also `/tmp/gf/shots/`). Frame rate in this GPU-less container was 1–4 fps,
so I judged framing/layout/controls only, never colour/exposure/smoothness.

---

## Findings, most severe first

### ❗ P1-1 — The opening story toasts are never seen; the player gets `harbour` instead (first-run + transient UI)
**Symptom.** Tap BEGIN → the only toast that appears is the word **`harbour`** (raw region id, lower-case) for ~2 s
(`p2-start-a.png`, `land-start-a.png`), then nothing (`p2-toastband-c.png`, `p2-start-d.png`). The chain toast
"Find the Harbour Master - his office is on the quay" and the `r_start` toast "Rain again. The blue truck is on the
quay; the road up climbs behind the net shed." are never visible in any of 4 captures spanning 0.4 s → 13 s.
**Root cause (engine, but data-fixable).** `game_shell.gd` has ONE toast slot (`_toast()` overwrites text + timer).
`_apply_mode()` toasts the chain line, then `fire("start")` → `r_start` toast replaces it immediately; ≤0.6 s later
`_update_region()` fires `enter_region harbour` and calls `_toast(best, 2.2)` — the region NAME wipes the story
toast. The same ordering (`fire("enter_region")` → then `_toast(name)`) means **`r_light`'s toast on entering
`headland` ("Kestrel Point. The lighthouse stairs go all the way up.") is also overwritten by the word `headland`
in the same frame** — verified by code read, same mechanism.
**Fix (world.json, data-level).**
1. `r_start.then[0]` → `{"subtitle": {"text": "Rain again. The blue truck is on the quay; the road up climbs behind the net shed.", "hold": 6}}` — the subtitle label (`_sub_lbl`, bottom third) is an independent slot the region toast cannot clobber. Same for `r_light` (→ `subtitle`). `r_cove` already uses `subtitle` and is fine.
2. Optionally drop the chain `toast` on `settle_in` (redundant with the persistent quest label) so the region toast has nothing to fight.
Engine note for the template owners: `_toast` should queue, or a region-name toast should not pre-empt a
longer-hold authored toast.

### ❗ P1-2 — Region toasts print raw ids: `harbour`, `smugglers_cove`, `chapel_hill`
**Symptom.** The region toast shows `regions[].name` verbatim (`p2-start-a.png`: "harbour"). Entering the cove will
print **`smugglers_cove`**, the hill **`chapel_hill`**, the moor `moor`, the pub `pub`. Underscored lower-case ids
on a phone screen read as debug text. (The toast IS transient — 2.2 s + fade — so ✅ on "not pinned".)
**Root cause.** `game_shell._update_region()` → `_toast(best, 2.2)` with no display-name field.
**Fix (world.json).** Rename regions to display strings and update every rule `target` that references them
(matching is exact-string in `rules._when_matches`): `"harbour"`→`"The Harbour"`, `"town"`→`"Kestrel Bay"`,
`"headland"`→`"Kestrel Point"` (+ `r_light.when.target`), `"chapel_hill"`→`"Chapel Hill"`,
`"smugglers_cove"`→`"Smugglers' Cove"` (+ `r_cove`, `r_cove_spawn` targets), `"moor"`→`"The Moor"`,
`"pub"`→`"The Kestrel Arms"`. `quests.json` `reach_area c9_-6` is a cell id, unaffected.

### ❗ P1-3 — Camera walled at spawn and around the harbour office (SpringArm collapses into a wall / a net pile)
**Symptoms (three, same cause).**
- **At spawn (24,24), default yaw:** the 8.5 m arm puts the camera at ≈(24,32.5) — inside the **boathouse**
  footprint (landmark cell [1,2], 12×7 @ (27.4,36.6) rot 135). In landscape the right third of the opening frame
  is a blank dark-brown slab (`land-start-a.png`, `land-hud.png`); in portrait it is the bottom-left corner
  (`p2-start-a.png`). The player's very first frame has a wall through it.
- **Facing away from the office's W wall by the net pile (22.2,18.5):** the arm is squeezed between the office
  and `net_pile.glb` @ (20.3,17.7) and the camera ends up INSIDE the net-pile mesh — the full frame is net
  texture + a cream wall slab, hero half-hidden (`p2-pitch-max.png`). This is the "popup mesh" frame.
- **Spawn view straight ahead** is the office's windowed back wall filling ~50 % of the frame 7 m away
  (`p2-start-d.png`); walking 6 m south the boathouse wall fills 60 % (`p3-open-neutral.png`). The quay spawn
  is boxed: office 7 m N, boathouse ~9 m S, net shed ~13 m W.
**Root cause.** Data: the start cell centre sits between two large landmarks with no 9 m of clear ground behind
it; bulky Meshy props (net pile, lobster pots, plank pile) are placed within 1–2 m of building walls. Engine:
SpringArm collides with props (mask) and only hides the HERO when collapsed (`cd > 1.35`), never the prop.
**Fix (world.json).** (a) Move the boathouse off the spawn axis (e.g. shift cell [1,2]'s landmark ≥ 12 m toward the
water or rotate it so its long side is not 4 m behind spawn), OR pick a start cell whose −z view is open harbour
water with ≥ 10 m of clear quay behind it. (b) Keep `net_pile`, `lobster_pots`, `MS_Plank_Pile` ≥ 2.5 m off every
building wall on the quay (cells 460/428/461). Engine-level (name it to template owners): fade/hide any prop the
SpringArm has collapsed against, like `_fade_near_camera_enemies()` does for enemies.

### ❗ P1-4 — Top-left stats block is illegible against pale stone / overcast sky (engine-level)
**Symptom.** "Lv 1 HP 100/100 XP 0/30 Gold 0 / Wpn / Inv" is pale green with no shadow or backing; over the
office's stone wall or the grey sky it vanishes (`p4-stats-on-stone-zoom.png`, `p8-truck-boarded.png`). The quest
label directly under it (which HAS a shadow) stays readable in the same frames, proving it is the missing outline.
In this world nearly every quay frame is pale stone or sky, so it is the common case, not an edge.
**Root cause.** `main.gd _build_hud`: `stats` Label — `font_color (0.9,1,0.9)`, no `font_shadow_color`/outline
(the rules-HUD label and quest label do set shadows). Engine-owned.
**Fix.** Engine: add `font_shadow_color`/`font_outline` (or a 0.45-alpha black backing) to `stats`. No clean data
mitigation short of `hud_hide: stats` (not recommended — HP would go with it).

### ❗ P1-5 — Quest label renders at ~9 CSS px on the phone (engine-level, data mitigation available)
**Symptom.** The persistent objective text (font 17 in a 720-unit viewport → 17 × 390/720 ≈ **9 px** on a
390-wide phone; stats 22 → 12 px) wraps to 4 lines and needs squinting (`p2-hud-topleft-zoom.png` is a 3× zoom).
Both objectives of `settle_in` are shown at once ("[ ] Find the Harbour Master… / [ ] Climb to the town and ask at
the Kestrel Arms") — the second is noise until the first is done.
**Root cause.** `game_shell.gd:133` `_label("", 17, …)` and `_relayout` width `min(430, vp.x*0.55)`; engine.
**Fix.** Engine: quest font ≥ 22 units. Data (quests.json): shorten step `desc` so one line fits —
"Find Alwyn in the harbour office" / "Ask at the Kestrel Arms up the hill" — and rely on the label showing only the
current step if the engine supports it (it currently prints `quest.current_objective()` = every open step).

### ❗ P1-6 — Interior pitch-down = full-frame hero (engine-level camera clamp)
**Symptom.** Inside the harbour office (7 m room, arm collapsed to ~1.5–2.5 m) a half-screen downward swipe
reaches `CAM_PITCH_MIN` and the hero's hat + back fill the entire frame, floor behind (`p9-office-pitchdown.png`).
The same swipe outdoors is fine (`p3-open-pitch-max.png`: hero small, ground visible). Neutral interior framing is
cramped but usable (`p9-office-inside-2.png`, `p9-office-pitchup.png`: stairs/ceiling/room readable, hero ~55 % of
frame height). On entering, the first interior frame is a point-blank floor smear with the hero hidden
(`p9-office-inside.png`) until you take a step.
**Root cause.** `main.gd` pitch floor −1.05 is tuned for the 8.5 m arm; when a wall shortens the arm the same
pitch puts the lens on the hero's shoulder; hero is only hidden below 1.35 m.
**Fix (engine).** Scale the pitch floor with the current arm length (e.g. clamp to −0.6 when `cd < 3`), or raise
the hero-fade threshold to ~2.2 m indoors. Data: nothing in world.json addresses this; interiors are 3.0 m floors
per the brief and that is fine.

### ⚠️ P2-1 — `SMUGGLERS DOWN 0` readout: wrong place in portrait, on the title screen, and irrelevant for the first 20 minutes
- Portrait: `pos: top_right` collides with the minimap, then the stats block, and `_place_clear` drops it to the
  very bottom-right edge **under ATTACK at y≈828/844** (`p2-start-a.png`; log `GOGI_HUD_FIT smugglers_down moved
  434,47 -> 434,1508`). In a standalone/PWA launch (`apple-mobile-web-app-capable`, `viewport-fit=cover`) that is the
  home-indicator band. Landscape is fine (left of the minimap, `land-hud.png`).
- It is drawn ABOVE the title overlay (`p1-title.png`, bottom-right) — HUD text visible on the title screen.
- It is pinned from second 0 on the quay where there are no smugglers; persistent clutter on a small screen.
**Fix (world.json).** `hud[0].pos` → `"bottom_left"` (clear of minimap/stats/buttons at both aspects — the left
half only hosts the invisible floating joystick) and gate it: `r_start.then` add `{"hud_hide": "smugglers_down"}`,
`r_cove_spawn.then` add `{"hud_show": "smugglers_down"}` (both actions exist in `rules.gd`).

### ⚠️ P2-2 — Inventory line is noise and mismatched: `Inv: Rusty Sword, [Boat Hook]`
The engine-default `rusty_sword` sits in the inventory; `world.weapons.rusty_sword` renames it "Gutting Knife"
but the HUD still prints "Rusty Sword" (stats refreshed before the weapon catalog merge; engine nit). It also makes
`weapon_count()==2`, which can surface a "WEAPON >" cycle button.
**Fix (world.json).** `r_start.then` add `{"remove_item": "rusty_sword"}` → line becomes `Inv: [Boat Hook]`,
one weapon, no cycle button. (Or drop the `rusty_sword` entry from `weapons` if you keep it.)

### ⚠️ P2-3 — First-run: spawn faces the office's BACK wall; the door is on the far (NE) side
The player spawns 7 m from the office looking at its windowed n-face; the only door (s-face, centre −2.2) is on
the NE side facing uphill, ~15 m walk around (`p2-start-d.png` vs `p7-office-door.png`). The n-face window at
sill 0.9 even reads like a doorway from a low camera (`p4-office-door.png`) and lures the player into the wall +
net-pile corner of P1-3. The door itself works: "USE > Door" prompt, opens, "USE > Close Door", 1.1 m clear
opening (`p8-office-door-open.png`), and the harbour master talk fires `r_talk_master` with a non-modal toast +
"Alwyn Rees is speaking…" (`p9-office-talk.png`). Time-to-first-interaction is fine once you know where to go.
**Fix (world.json).** Rotate the office 180° (`rot: 315` → `135`, footprint identical; re-check the plinth
`rows` and Mason's "door on the uphill side" rule) so the door faces the quay/spawn, or move `start_cell` so the
default −z view frames water + jetty + boat instead of a wall.
**QA cross-note:** in all five interior frames within 0.7 m of Alwyn (talk prompt live) no NPC body is visible —
only a thin white vertical bar stands where he should be (`p9-office-master.png`, `p9-office-inside-look.png`).
Check that `harbour_master.glb` actually loads/scales and is not under the raised (y≈4.1) interior floor.

### ⚠️ P2-4 — Truck: driver's torso pokes through the cab roof
`p8-truck-boarded.png` / `p8-truck-drive.png`: the hero sits visibly above the cab. Chase-cam itself is right
(settles to `vehicle.rotation.y + π`, truck framed from behind/above). **Fix (world.json):** author
`vehicles[0].seat: [x, y, z]` (self-local metres, `vehicle.gd` honours it verbatim) ~0.4 m lower / inside the cab.

---

## Dimension results

| Dimension | Result | Evidence |
|---|---|---|
| 1. Camera never walls the view | ❗ P1-3, P1-6 | spawn slab, net-pile popup, interior pitch-down |
| 1b. Orbit / pitch | ✅ | −100 px right-half touch drag → Δyaw **+1.108 rad** (spec ≈1.11). Outdoor pitch extremes: down = hero small + ground (`p3-open-pitch-max.png`); up (+0.25) = hero large against wall, horizon kept (`p4-pitchup-mouse.png`). No sky-stare, no scalp-only outdoors. |
| 1c. Vehicle chase cam | ✅ | truck boarded via touch USE at 3 m (`in_vehicle true`), drove 6 m, cam yaw 3.14 = behind (`p8-truck-drive.png`) |
| 1d. Switchback slope | ⚠️ not framed | reached the slope once at (21,45) y=7.3 with pitch at my own extreme (`p3`), inconclusive — see "could not verify" |
| 2. HUD fits a phone | ❗ P1-4, P1-5; ⚠️ P2-1, P2-2 | portrait + landscape captures; `GOGI_HUD_GRID` portrait `rows 1074/1222/1370` of 1558, landscape `345/457/568` of 720 → all three button rows on-screen at both aspects; landscape bottom edge 368/400 |
| 2b. No overlap / clipping | ✅ | stats↔HP bar touch but do not overlap (zoom), quest under bar, minimap clear, `GOGI_HUD_FIT` resolved (no `UNRESOLVED`) |
| 2c. No debug text | ✅ | no fps/coords/print-to-screen; `hud_debug` off; `dismount_rect` etc. only in the JS hook |
| 2d. Title screen | ✅ (⚠️ P2-1 leak) | kicker/name/tagline/BEGIN/caption/hint fit at 390×844 (`p1-title.png`) and 860×400 (`land-start-a.png`, hint bottom at 368/400 — tight if a browser toolbar eats height); name wraps to two lines at both aspects, acceptable |
| 3. Touch one-handed | ✅ | left-half touch-hold moved the player **5.84 m along camera-forward (cos 0.95)**; JUMP tap → `on_floor false`, y+; ATTACK tap → `anim: attack`; USE tap opened door / boarded truck / talked; a 120 px drag STARTING on the USE button gave **Δyaw 0.000** (button owns the touch) |
| 4. Transient vs persistent | ❗ P1-1/P1-2 (content), ✅ (mechanics) | region toast fades after 2.2 s (`p2-toastband-c.png` empty); quest label persistent by design; talk prompt disappears out of range; "Alwyn Rees is speaking…" clears when audio ends (not timed here) |
| 5. Damage non-modal | ✅ (code) | `take_damage` → SFX + 0.15 shake + direction arc; `_flash_hurt` is a no-op; `r_died` toast + respawn, no dialog. Not driven — no enemies near spawn in this container's time budget |

## Could not verify (sandbox limits)
- Real-device notch / home-indicator insets (web `_safe_insets()` returns zero; P2-1's bottom-edge placement is
  inferred from geometry, not a device).
- True multi-touch feel (joystick + look simultaneously) and gesture latency at 60 fps — container ran at 1–4 fps.
- Switchback road framing, boat chase-cam, pub interior and the cove/boss: travel time at 1–4 fps exceeded the
  budget; the camera behaviour there is the same SpringArm rig, so P1-3/P1-6 apply wherever walls are within 8.5 m.
- 430×932: same aspect as 390×844 to 0.2 % and the engine lays out in a 720-unit short side, so the viewport is
  720×1560 vs 720×1558 — layout is identical to the portrait captures; not separately rendered.
- Colour, exposure, texture quality (SwiftShader). The boathouse/net-shed "timber" reads as a flat dark-brown slab
  here; judge on a GPU before calling it a material bug.
