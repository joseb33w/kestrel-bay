# KESTREL BAY — Game-Feel / Mobile-UX review (FIX build re-test)

**VERDICT: FAIL (0 P0, 6 P1)** — the data-level fixes landed and work (display-name region toasts, story
subtitle survives, spawn no longer walled, SMUGGLERS DOWN gated to the cove, inventory line clean, driver in the cab).
Touch is fully live, damage is non-modal, the chase cam is right. What still blocks a phone PR is ENGINE-level
camera/HUD behaviour that the re-synced template did **not** fix — and two of them are worse than the last report
measured: the camera inside every 3 m room collapses to a hero-filling frame at NEUTRAL pitch (not only on pitch-down),
and the story subtitle (the slot the last report told you to move story text INTO) is laid out over the JUMP/SHEATHE/USE
thumb buttons in both orientations.

Evidence: every claim was driven on `/workspace/repo/out` served locally (wasm MIME, `/godot-assets/` proxied to
preview.myapping.com) in headless Chromium/SwiftShader with a touch-emulating mobile context (CDP
`Input.dispatchTouchEvent` — the real touch path, not mouse), at **390×844 portrait** and **860×400 landscape**.
Screenshots: `/workspace/verify/gf/*.png` (harness: `/tmp/gf/*.mjs`, logs `/tmp/gf/*.log`). Container ran at
**1–5 fps**; cell/GLB streaming is frame-budgeted so a cell took 20–130 s to appear here (it is sub-second on a phone) —
I waited 130 s before judging anything. For far places (pub, cove, slope foot, boat) I served a **test copy of
world.json with only `quay_spawn` changed** (and, for one slope run, `vehicles[0].pos`); the project was not touched.
I judged framing/layout/controls only — never colour, exposure or smoothness.

---

## Re-test of the previous report (docs/gamefeel_report.md)

| Prev | Status | Evidence |
|---|---|---|
| P1-1 story toasts clobbered by region toast | ✅ **fixed for the story line** (subtitle slot, 7 s, survives "The Harbour") / ⚠️ residual: the chain toast "Find the Harbour Master…" is still wiped by "The Harbour" at ~1.5 s of its 5 s hold | `p-begin+0.7s.png` (chain toast) → `p-begin+2.5s.png` ("The Harbour" replaced it; subtitle still up) → `p-begin+8.5s.png` (subtitle still up) |
| P1-2 raw region ids | ✅ **fixed** — "The Harbour", "The Kestrel Arms" rendered; all 8 `regions[].name` are display strings; `r_light`/`r_cove`/`r_cove_spawn`/`r_cove_path` targets match (r_cove + r_cove_spawn fired live at the cove) | `p-begin+2.5s.png`, `toast-cross+0.3s.png`, `/tmp/gf/cove.log` |
| P1-3 camera walled at spawn | ✅ **fixed** — 4 yaws + 2 pitch extremes at (39.5,36): no slab, no prop in the lens, shed_a ≥4 m clear of the arm | `p-spawn-yaw0/90/180/270.png`, `l-spawn-yaw0/90/180/270.png`, `p-spawn-pitch-*.png` |
| P1-4 stats illegible | ❗ **still open (engine)** — `stats` Label still has no shadow/outline; invisible over sky/shingle | `zoom-p-stats-on-sky.png`, `boat-before-board.png`, `l-spawn-yaw0.png` |
| P1-5 quest font 17 → ~9 CSS px | ❗ **still open (engine)**; data half done (descs shortened to one line each) but both open objectives still print | `p-spawn-yaw0.png` top-left |
| P1-6 interior pitch-down = full-frame hero | ❗ **still open and broader** — see P1-1 below: it is the NEUTRAL pitch now, plus a floor clip on pitch-up | `office-inside-*.png`, `pub2-inside-*.png` |
| P2-1 SMUGGLERS DOWN placement/gating | ✅ bottom_left, hidden at start, shown at the cove, clear of buttons / ⚠️ residual: still drawn ABOVE the title overlay before `start` fires | `cove-arrive.png` (shown), `p-spawn-yaw0.png` (hidden), `l-title.png` + `l-begin+0.8s.png` (on title) |
| P2-2 inventory line | ✅ "Inv: [Boat Hook]", no WEAPON> cycle button | `p-spawn-yaw0.png` |
| P2-3 spawn faces office back wall | ✅ changed — default view is quay + truck; office is off-axis | `p-spawn-yaw0.png` |
| P2-4 driver torso through cab roof | ✅ driver now seated inside the cab (visible through the rear window) | `zoom-truck-driver.png` |

---

## Findings, most severe first

### ❗ P1-1 — Inside every 3 m room the camera collapses onto the hero at NEUTRAL pitch; behind-view is a floor smear; pitch-up clips under the floor (engine)
**Symptom (harbour office 9×7×3.0 m and pub 14×10×3.2 m, both orientations).**
- Neutral pitch, one step inside: hero fills **65–80 % of frame height**, wall/slab in front, no room readable
  (`office-inside-neutral.png`, `office-inside-yaw+90.png`, `pub2-inside-neutral.png`).
- Yaw the camera to look back at the door (a normal "where's the exit" move): the arm collapses below 1.35 m, the hero
  is hidden and the whole frame is floor tiles + a slice of furniture — a headless "where am I" frame
  (`office-inside-yaw+180.png`, `pub2-inside-yaw+180.png`).
- Pitch-up swipe in the office: the camera drops BELOW the interior floor and looks up through the (single-sided,
  back-face-culled) slab: outside cobbles + slab edge in the lower third, hero far away up the stairwell
  (`office-inside-pitchup.png`). That is a mesh clip, not just a tight frame.
- Pitch-down is still the hat-and-shoulders frame reported last time (`office-inside-pitchdown.png`).
**Root cause (engine, `main.gd`).** `CAM_DIST 8.5` at `cam_pitch −0.55` wants the lens **4.4 m above the head pivot
(CAM_HEAD 1.5) = ~6 m above the floor**; under a 3.0 m ceiling the SpringArm can only reach
≈(3.0 − 0.3 margin − 1.5)/sin 0.55 ≈ **2.3 m**, at which a 1.78 m hero is ~65 % of a 62° vertical FOV. The hero is only
hidden below `cd > 1.35`. The pitch-up clip means the interior floor plate / stair core is not stopping the arm
(margin 0.3 vs a thin slab, or the stairwell void) — verify which body the arm passed. Data (`floor_height: 3.0`,
`interior.floor_z`) is per brief and fine; nothing in world.json can address this.
**Fix (engine).** Detect an overhead hit (short upward ray from the head, or `cam_spring.get_hit_length() < CAM_DIST`
with the hit above the pivot) and while indoors: clamp pitch to ≈ −0.15…−0.25 and target arm ≈ 3.5–4 m, ease back
outdoors; fade the hero (dither/alpha) between 1.35 and ~2.4 m instead of a hard hide; make the SpringArm ignore
ceilings/upper-floor slabs (layer them separately) so it slides along the wall instead of the ceiling; include the
interior floor slab in the arm's mask/margin so pitch-up cannot go under it. Same rig serves the chandlery/house
interiors (3.0 m, not separately driven) and the cave arena (5 m — headroom ≈6 m, mostly OK).

### ❗ P1-2 — Default camera pitch puts the horizon at the top edge: the opening frame is a slab + truck, and everything above the horizon (sea, cliffs, town, lighthouse) is off-screen until the player pitches up (engine; data cannot fix)
**Symptom.** At default pitch (−0.55 rad = −31.5°) with `fov 62` (KEEP_HEIGHT → 62° vertical in BOTH orientations)
the top edge ray is at **−0.5°**: nothing above the horizon is ever in frame. At spawn yaw 90° and 180° the frame is
**100 % cobble** (`p-spawn-yaw90.png`, `p-spawn-yaw180.png`); the opening frame (yaw 0) is a pale slab, the truck's
cab and a grey strip (`p-spawn-yaw0.png`, `l-spawn-yaw0.png`) — it does not read as a harbour, and the 2-storey office
27 m away would subtend 12° above the horizon, i.e. clipped off the top. In portrait the horizontal FOV is only **31°**,
so it is a keyhole onto the floor. One pitch-up swipe shows the intended picture — cliffs, bushes, sky, buildings
(`p-spawn-pitch-up.png`, `l-spawn-pitch-up.png`) — which proves the world is there and the default framing hides it.
The boat-side frame (`boat-before-board.png`, also default pitch, but the ground drops to water) is the only frame
that reads "harbour", and only because the terrain falls away.
**Root cause.** `main.gd` `var cam_pitch := −0.55`, `cam.fov = 62.0`, default `keep_aspect`. Data: `quay_spawn` is
[x,z] only (no spawn yaw) and `cam_yaw` starts at 0 (look −z); the harbour water lies WEST of the quay
(`heights.csv`: water x<0, z<12), so no −z-facing spawn can frame it — this is not fixable from world.json.
**Fix (engine).** Default `cam_pitch ≈ −0.35` (≈ 9° of above-horizon in frame; still a readable ground plane), and
in portrait widen the vertical FOV (≈ 70–75°, or `KEEP_WIDTH` with a clamp) so the keyhole opens; optionally honour a
`spawn_yaw`/`quay_spawn:[x,z,yaw]` so a world can open on its hero shot. Data follow-up once that exists: face the
spawn west toward the boat/office/net shed.

### ❗ P1-3 — The story subtitle is laid out over the thumb buttons in both orientations (engine)
**Symptom.** `r_start`'s subtitle ("Rain again. The blue truck is on the quay; the road up climbs behind the net
shed.") — the slot P1-1's fix moved story text into — renders across the button grid: portrait line 1 abuts JUMP,
line 3 sits on SHEATHE's top edge (`zoom-p-subtitle-overlap.png`, `p-begin+0.7s.png`); landscape "climbs behind" is
drawn **across the SHEATHE button** and the box spans the USE/ATTACK rows (`zoom-l-subtitle-overlap.png`,
`l-spawn-yaw0.png`). Every `subtitle` in the world (`r_light`, `r_cove`, `r_cove_path`) uses the same slot.
**Root cause.** `game_shell.gd:858–861` `_sub_lbl` size `vp.x*0.56` at x `vp.x*0.22`, y `vp.y*0.72` — the comment says
"clear of the thumb grid" but the grid's left column starts at `vp.x − 2·bw − m − mr` (≈0.54·vp in portrait, ≈0.69 in
landscape) and rows start at `vp.y*0.69` (portrait) / `0.48` (landscape). No layout query of the buttons.
**Fix (engine).** Place the subtitle ABOVE the button grid (`y = row3 − label_h − 16`) and cap its width to the
button column (`x from ml to col_l − 16`), or centre it in the free band between the quest label and row3; give it
the same `_place_clear` treatment the rules-HUD gets. Data has no lever (no position key on `subtitle`).

### ❗ P1-4 — Boss bar overprints the stats line and the minimap in portrait (engine)
**Symptom.** Within `show_within 40` of the ringleader, "THE RINGLEADER" is drawn over "XP 0/30 Gold 0" and the boss HP
bar runs under the minimap's left edge (`zoom-cove-hud-top.png`, `cove-arrive.png`, `cove-t1.png`).
**Root cause.** `game_shell.gd:862–872` `_boss_root` at `y=44`, width `min(520, vp.x*0.7)` centred → x 108–612 of 720
in portrait, while stats occupy x 12–~330 / y 12–100 and the minimap x 521–708 / y 12–199.
**Fix (engine).** In portrait (vp.x < vp.y) drop the boss bar below the minimap/quest block (y ≈ `below_mm` or
`vp.y*0.14`) and cap width to `vp.x − 2·mm`; or shrink to the band between stats and minimap (x 340–510). Data has
no lever (`boss` block has no position).

### ❗ P1-5 — Top-left stats block still illegible (engine; unchanged from previous P1-4)
`main.gd:3778–3781` `stats` still `font_color (0.9,1,0.9)` with no `font_shadow_color`/outline. Over sky it is gone
(`zoom-p-stats-on-sky.png`), over shingle/pale stone nearly so (`boat-before-board.png`). The HP number lives here.
**Fix (engine).** Add shadow/outline (as the quest label and rules-HUD labels already have) or a 0.45-alpha backing.

### ❗ P1-6 — Quest label still ~9 CSS px and prints every open objective (engine; previous P1-5)
`game_shell.gd:133` `_label("", 17, …)` → 17 × 390/720 ≈ 9 px on the phone; both `settle_in` objectives shown at once.
Data mitigation is in (one-line descs). **Fix (engine).** ≥ 22 units; show only the current step.

### ⚠️ P2-1 — Chain toast still clobbered by the region toast (residual of previous P1-1)
"Find the Harbour Master - his office is on the quay" (5 s) is replaced by "The Harbour" ~1.5 s in
(`p-begin+2.5s.png`). Harmless now that the objective is in the quest label, but the single-slot `_toast` is the same
bug. **Fix (data):** drop `chain[0].toast` (redundant with the quest label). Engine: queue toasts / don't let a 2.2 s
region toast pre-empt a longer authored one.

### ⚠️ P2-2 — `SMUGGLERS DOWN 0` drawn above the title overlay until `start` fires (residual of previous P2-1)
`l-title.png`, `l-begin+0.8s.png` (bright label over a black transition frame). `hud_hide` cannot run before `start`.
**Fix (engine):** rules-HUD readouts respect `shell.input_locked()`/title visibility, or accept an initial
`"hidden": true` on `hud[]` entries. Also the title `bg` alpha 0.94 lets the button grid/stats ghost through
(`p-title.png`) — cosmetic.

### ⚠️ P2-3 — BEGIN before `_world_ready` shows the un-teleported hero at start_cell for a beat
`toast-begin+1.5s.png`: hero at (24,24) with "Inv: Gutting Knife, [Boat Hook]" and SMUGGLERS DOWN visible, then the
mode applies and teleports to `quay_spawn`. `_choose()` only calls `_apply_mode()` if `_world_ready`; otherwise the
world shows first. In this 1-fps container that gap was seconds; on a phone it is likely a frame or two, but a fast
tapper on a slow network will see it. **Fix (engine):** keep the title veil up until `_apply_mode` has run.

---

## Dimension results

| Dimension | Result | Evidence |
|---|---|---|
| 1. Camera never walls the view — spawn/quay | ✅ | 4 yaws × 2 aspects + pitch extremes at (39.5,36); shed_a, benches, lamp posts, drums all clear of the arm |
| 1. Camera — interiors (office, pub) | ❗ P1-1 | hero 65–80 % at neutral, floor smear behind, floor clip on pitch-up |
| 1. Camera — default framing | ❗ P1-2 | horizon at top edge; yaw-90/180 = 100 % cobble |
| 1b. Orbit / pitch | ✅ | 142 css-px right-half drag → Δyaw **+1.573 rad** (portrait) / **+1.534** (landscape); pitch-down outdoors = hero small + ground (`p-spawn-pitch-down.png`); pitch-up = horizon kept, no sky-only frame (`p-spawn-pitch-up.png`) |
| 1c. Vehicle chase cam (truck) | ✅ | boarded via touch USE at 2.7 m (`in_vehicle true`, cam_yaw snapped to 3.14 = behind), DISMOUNT appears in the left column; cam behind/above while driving (`truck-boarded.png`, `truck-drive-1.png`, `slope-boarded.png`); driver seated in cab |
| 1d. Switchback slope framing | ⚠️ not framed | see "could not verify" |
| 1e. Boat chase cam | ⚠️ not framed | see "could not verify" |
| 2. HUD fits a phone — grid | ✅ | `GOGI_HUD_GRID` portrait rows 1074/1222/1370 of 1558, landscape 345/457/568 of 720 → all three rows on-screen both aspects; landscape bottom edge 662/720 |
| 2. HUD — overlaps | ❗ P1-3, P1-4 | subtitle × buttons; boss bar × stats/minimap |
| 2. HUD — legibility | ❗ P1-5, P1-6 | stats no shadow; quest 9 px |
| 2. HUD — SMUGGLERS DOWN | ✅ | bottom_left, hidden until the cove, clear of buttons/joystick (`cove-arrive.png`) |
| 2. No debug text | ✅ | no fps/coords/print-to-screen in any frame; `hud_debug` off; `dismount_rect` etc. only in the JS snapshot |
| 2. Title screen | ✅ (⚠️ P2-2 leak) | kicker/name/tagline/BEGIN/caption/hint fit at both aspects (`p-title.png`, `l-title.png`); BEGIN reachable one-handed |
| 3. Touch one-handed | ✅ | left-half hold moved the player **13.68 m along camera-forward (cos 1.00)** in 5 s; JUMP tap → vy **+5.9**, apex +1.7 m, landed (`toast.out` samples); ATTACK tap → `anim attack`; USE tap opened/closed doors and boarded the truck; a 120 px drag STARTING on USE → **Δyaw 0.000** |
| 3b. Hold joystick → USE → release | ✅ | USE fired mid-walk (door), released → **0.00 m** drift in 2.5 s, anim idle (`pub2-after-release.png`); no modal panels exist in this world so the `_release_touch_state()` lock path is code-verified only |
| 4. Transient vs persistent | ✅ | "The Harbour" and "The Kestrel Arms" appear on entry and are gone by +5 s (`toast-cross+0.3s.png` → `toast-cross+5s.png`); nothing pinned except the quest label (by design) and the gated SMUGGLERS DOWN; `r_cove`/`r_cove_spawn` fired at the cove (`cove.log`) |
| 5. Damage non-modal | ✅ | at the cove HP went 100 → 4 → died → `r_died` respawn toast, no dialog/banner; `take_damage` = SFX + 0.15 shake + direction arc (`_flash_hurt` is a no-op — feedback is subtle but non-modal) (`cove-arrive.png`, `cove-look90.png`, `cove.log`) |
| First minute | ⚠️ | truck IS discoverable in the opening frame (top-left, both aspects) and the story subtitle survives the region toast; but the frame does not read as a harbour (P1-2) and the subtitle sits on the buttons (P1-3) |

## Could not verify (sandbox limits)
- **Switchback chase cam**: with the truck parked at the slope foot (test copy) it rolled back / jammed among the
  fish-crate + dinghy props at ~(55,48) under 1–3 fps physics and never climbed the 27 % grade (56,56)→(72,56)
  (`slope2-drive-*.png`). I cannot tell container physics from a traction problem — **QA cross-note**: confirm the
  `car` profile climbs that grade on device (Jory's "don't stall it on the switchback" line suggests the author knows).
- **Boat chase cam**: standing on the shingle 5.6 m from the boat origin (−7,2.7) two touch USE presses did not board
  (`boat-before-board.png`); the player then swam. **QA cross-note**: check the boarding reach from the mooring/jetty.
- Chandlery / chapel / house interiors and the cave arena were not driven; the P1-1 rig behaviour is geometric
  (ceiling < 6 m) so it applies to every 3.0–3.2 m interior; the chapel (7.4 m) and cave (5 m) should mostly clear.
- Kestrel Point / Chapel Hill / The Moor / Cove Path toasts not walked (same `_update_region` path as the two verified).
- Real-device notch/home-indicator insets (`_safe_insets()` is zero on web), true multi-touch feel, 60 fps latency,
  colour/exposure (SwiftShader).
- Streaming artefacts seen here and NOT filed as feel defects: ground/collider under the spawn absent for 60–70 s
  (`ray −1`, player held by analytic ground-stick, `l-ground-60s.png`), buildings appearing 100 s+ after arrival,
  straight chunk seams (`cove-t6.png`). At phone frame rates these are sub-second; QA owns streaming.
- Art cross-notes (not my dimension): tall spiky green "cactus"-like tufts on the cliff/slope (`slope-boarded.png`),
  a heather clump on the asphalt directly in front of the pub door (`toast-cross+0.3s.png`), pub window glass rendering
  as opaque white quads (`pub2-inside-neutral.png`).
