extends RefCounted
## PER-AVATAR ANIMATION STATE — the hero locomotion/action state machine, one instance
## per animated character.
##
## WHY THIS IS A MODULE AND NOT FOUR GLOBALS IN main.gd
## It used to be `_hero_ap` / `_hero_anim` / `_hero_air_t` / `_hero_attack_t` held on main,
## which meant exactly ONE character in the scene could animate. The local player got the
## full idle/walk/run/jump/attack/swim machine; every REMOTE player in a multiplayer room
## was a frozen rest pose sliding across the ground, because there was nowhere to put a
## second character's state. Instancing this is what lets peers animate.
##
## THE INPUTS ARE INJECTED, THE LOGIC IS NOT. `update()` takes a motion dictionary rather
## than reading a CharacterBody3D, because the local player and a network peer answer
## "how fast am I going" differently (physics body vs interpolated transform) and NOTHING
## ELSE about them differs. Branching on local-vs-peer inside the state machine is how the
## two would drift apart the first time a threshold is tuned — the same trap
## _normalize_avatar_height records in its own comment ("they were two similar blocks, and
## one of them silently lost its scaling step").
##
##   motion := {
##     "speed":    float,   # horizontal speed (m/s)
##     "vy":       float,   # vertical velocity (m/s)
##     "on_floor": bool,    # grounded this frame
##     "swimming": bool,    # floating in deep water
##     "mounted":  bool,    # seated/riding -> GPose owns the pose, we stand down
##   }

var ap: AnimationPlayer = null   # the avatar's AnimationPlayer (retargeted OR embedded clips)
var anim := ""                   # current semantic anim kind (idle/walk/run/attack)
var air_t := 0.0                 # seconds continuously off the floor — coyote buffer so brief bumps/curbs don't flip to the fall (dive) clip
var attack_t := 0.0              # remaining melee-attack-clip hold (s)


## Bind this state to an avatar, retargeting a clip set if the model ships none. Returns
## true when there is something to play. The caller owns any body-specific follow-up (the
## local hero re-applies GPose.swim; a peer has no body to pose).
func attach(node: Node3D) -> bool:
	var found := AnimRig._find_ap(node)
	if found == null or found.get_animation_list().is_empty():
		# retarget a FULLER clip set so the hero idles / walks / runs / attacks instead of freezing
		# on a single idle pose. Aliases whose source clip is missing are simply skipped by AnimRig,
		# and play() degrades run->walk->idle, so a thinner library still animates.
		found = AnimRig.attach(node, {
			"idle": "Idle_A", "walk": "Walking_A", "run": "Running_A",
			"attack": "Melee_1H_Attack_Chop",
			"jump": "Jump_Full_Short", "fall": "Jump_Idle",
		}, ["idle", "walk", "run", "fall"])
	if found == null or found.get_animation_list().is_empty():
		return false
	ap = found
	anim = ""
	attack_t = 0.0
	play("idle")
	return true


## Semantic kind -> a real clip name on this rig. Works for BOTH the retargeted alias set
## (exact name) and a model that embeds its OWN clips (substring match), so library AND
## Meshy creature avatars animate. "" = no such clip.
func resolve(kind: String) -> String:
	if ap == null or not is_instance_valid(ap):
		return ""
	if ap.has_animation(kind):
		return kind
	# THE SYNONYM TABLE IS THE ENGINE'S VOCABULARY, and it was narrower than the pipeline promised.
	# The Meshy playbook tells builds to name clips `hit`, `death` and `dance` "by the keyword the
	# engine resolves" — but only idle/walk/run/jump/fall/attack/swim had entries. Everything else
	# fell through to the literal `[kind]`, which is a SUBSTRING test: a clip Meshy returned as
	# "Dying" or "Hurt_B" did not match "death" or "hit" and the action silently did nothing.
	# Meshy's action library has 500+ ids across DailyActions / Fighting / BodyMovements / Dancing,
	# and almost none of them were reachable by name.
	var keys: Array = {
		"idle": ["idle"], "walk": ["walk"],
		"run": ["run", "sprint", "jog"],
		"jump": ["jump", "leap", "hop"],
		"fall": ["fall", "jump_idle", "air"],
		"attack": ["attack", "melee", "chop", "slash", "punch", "strike", "swing", "kick", "stab"],
		"swim": ["swim", "tread", "paddle", "float"],
		"hit": ["hit", "hurt", "damage", "impact", "flinch", "stagger"],
		"death": ["death", "die", "dying", "dead", "defeat", "collapse"],
		"dance": ["dance", "dancing", "boogie"],
		"sit": ["sit", "seated", "sitting"],
		"wave": ["wave", "greet", "hello", "salute"],
		"talk": ["talk", "speak", "convers", "chat"],
		"cheer": ["cheer", "celebrat", "victory", "applau", "clap"],
		"crouch": ["crouch", "crawl", "sneak", "duck"],
		"climb": ["climb", "ladder"],
		"work": ["work", "hammer", "mine", "chop_wood", "craft", "dig"],
	}.get(kind, [kind])
	# MATCH ON WORD TOKENS, NOT RAW SUBSTRINGS. A plain `k in clip_name` is how a widened
	# vocabulary quietly breaks things: "Soldier_Idle" contains "die", "Transition" contains "sit",
	# and "Drunk_Walk" contains "run". Each of those would have resolved the WRONG clip and the
	# character would have died on a greeting. Splitting the name and matching a token PREFIX keeps
	# "Dying" -> death and "Hurt_B" -> hit while refusing all three of those.
	for c in ap.get_animation_list():
		var cl := String(c).to_lower()
		for t in cl.replace("-", "_").replace(".", "_").replace(" ", "_").split("_"):
			for k in keys:
				if t.begins_with(k):
					return String(c)
	return ""


# ---- MOTION FEEL -----------------------------------------------------------------------------
# Two things made every character in every game read as "gamey" rather than real, and neither is
# the animation data — both are how it is PLAYED.
#
# FOOT SLIDING. A clip plays at the rate it was authored at while the body moves at whatever
# move_speed says, so the feet skate across the ground. BASE_MOVE_SPEED is 6.0 m/s and `set_speed`
# can take it to 24, against a run cycle authored for roughly 4.5 — so the faster the hero goes,
# the more the legs lag behind the motion. Scaling playback by the ratio locks the stride to the
# ground, which is the single biggest difference between "a model moving" and "someone running".
# Clamped, because a clip played at 3x reads as comedy and one at 0.2x reads as broken.
#
# THRESHOLD FLICKER. walk/run switched on a bare `spd > 3.0`, so a half-pushed stick sitting near
# that value re-triggered a 0.15 s crossfade every few frames — a visible stutter in the legs that
# looks like a rig problem and is not. Separate enter/exit thresholds fix it.
const WALK_NOMINAL := 1.5    # m/s a walk cycle reads as at 1.0x
const RUN_NOMINAL  := 4.5    # m/s a run cycle reads as at 1.0x
const RATE_MIN     := 0.70
const RATE_MAX     := 1.60
const RUN_ENTER    := 3.4    # hysteresis band around the old single 3.0 threshold
const RUN_EXIT     := 2.6
const MOVE_ENTER   := 0.35
const MOVE_EXIT    := 0.20


## How long to blend INTO a clip. A landed hit and a launch have to read as instant; settling into
## idle looks better taking its time. One number for everything made fast actions feel mushy.
func _blend_for(kind: String) -> float:
	if kind == "attack" or kind == "jump":
		return 0.06
	if kind == "idle":
		return 0.22
	return 0.12


## Lock the stride to the ground. Only locomotion is rate-matched; everything else plays at 1.0,
## and the reset matters because speed_scale is a property of the whole AnimationPlayer — leave it
## at 1.4 from a sprint and the next attack swings 40% too fast.
func _match_rate(kind: String, spd: float) -> void:
	if ap == null or not is_instance_valid(ap):
		return
	var nominal := 0.0
	if kind == "walk":
		nominal = WALK_NOMINAL
	elif kind == "run":
		nominal = RUN_NOMINAL
	var want := 1.0 if nominal <= 0.0 else clampf(spd / nominal, RATE_MIN, RATE_MAX)
	if absf(ap.speed_scale - want) > 0.01:
		ap.speed_scale = want


## Switch to a semantic anim with a short crossfade. Falls back run->walk->idle so a rig
## missing a clip animates instead of snapping to a frozen pose.
func play(kind: String) -> void:
	if ap == null or not is_instance_valid(ap) or kind == anim:
		return
	var clip := resolve(kind)
	if clip == "" and kind == "run":
		clip = resolve("walk")
	if clip == "" and kind != "idle":
		clip = resolve("idle")
	if clip == "":
		return
	# Embedded GLB locomotion clips import with loop_mode = NONE — walk/run then play ONE cycle and FREEZE
	# on the last frame while the body keeps moving, so the hero slid forward stuck in a single pose
	# ("floating, legs not moving, frozen"). The retargeted KayKit set gets looped at attach, but a Meshy
	# avatar's OWN clips don't. Force the cyclic clips to loop here; jump/attack/death stay one-shot.
	if kind == "idle" or kind == "walk" or kind == "run" or kind == "swim":
		var loop_anim := ap.get_animation(clip)
		if loop_anim != null and loop_anim.loop_mode == Animation.LOOP_NONE:
			loop_anim.loop_mode = Animation.LOOP_LINEAR
	anim = kind
	if kind != "walk" and kind != "run":
		ap.speed_scale = 1.0     # see _match_rate — a stale sprint rate must not leak into a swing
	ap.play(clip, _blend_for(kind))


## Per-frame state machine (on foot only — a seated/mounted rider is posed by GPose).
## The attack clip plays out its window uninterrupted; otherwise moving -> run (walk fallback).
func update(delta: float, motion: Dictionary) -> void:
	if ap == null or not is_instance_valid(ap):
		return
	if bool(motion.get("mounted", false)):
		return
	# SWIM: while floating in deep water, stroke a swim clip (or, on a rig without one, hold the GPose.swim
	# tread pose) instead of the run cycle re-stamping over it every frame ("walking on water").
	if bool(motion.get("swimming", false)):
		var sc := resolve("swim")
		if sc != "" and anim != "swim":
			play("swim")
		return
	attack_t = maxf(0.0, attack_t - delta)
	if attack_t > 0.0:
		return   # let the swing clip / a one-shot action finish before locomotion resumes
	# COYOTE BUFFER: a hero running over city curbs / uneven ground loses floor contact for a frame or
	# two, which flipped the "fall" clip (a floating dive pose) on/off every few frames — reading as the
	# character FLOATING / diving while it ran. Only switch to jump/fall once genuinely airborne (>0.14s
	# off the floor, or clearly launched upward), so a bump keeps the run/walk clip and stays upright.
	#
	# Airborne pose ONLY when actually off the floor. The old code also fired on `velocity.y > 2.0`
	# while GROUNDED — running over city curbs / floor-snap pops spikes vy, so the hero kept flicking
	# into the jump-leap clip (this model's `jump` lifts the hips to y≈254, a ~1.5 m pop) and the
	# `fall` path falls back to idle (an idle pose mid-air). Both READ AS FLOATING while running.
	# Grounded (even bumpy) now always plays locomotion; off-floor & rising -> the jump leap; off-floor
	# & descending -> fall through to run/walk (the model has NO fall clip, and idle-in-air floats too).
	air_t = 0.0 if bool(motion.get("on_floor", true)) else air_t + delta
	if air_t > 0.12 and float(motion.get("vy", 0.0)) > 0.5:
		play("jump")
		return
	# HYSTERESIS, not a single threshold — see the constants above.
	var spd := float(motion.get("speed", 0.0))
	var want := "idle"
	if anim == "run":
		want = "idle" if spd < MOVE_EXIT else ("walk" if spd < RUN_EXIT else "run")
	elif anim == "walk":
		want = "run" if spd >= RUN_ENTER else ("idle" if spd < MOVE_EXIT else "walk")
	else:
		want = "run" if spd >= RUN_ENTER else ("walk" if spd >= MOVE_ENTER else "idle")
	play(want)
	_match_rate(want, spd)


## Play a one-shot ACTION / emote clip (dance, wave, cheer, sit, taunt, …) then auto-return
## to locomotion after `hold` seconds. `clip` is any clip NAME on the rig OR a semantic key
## resolve() understands. This is the hook that lets the game give the character ALL types of
## animations beyond the built-in idle/walk/run/jump/attack set — call it on any event.
func action(clip: String, hold := 1.2) -> void:
	if ap == null or not is_instance_valid(ap):
		return
	var resolved := resolve(clip)
	if resolved == "" and ap.has_animation(clip):
		resolved = clip
	if resolved == "":
		return
	attack_t = hold   # reuse the "don't override locomotion" gate for the action's duration
	anim = "action"
	ap.play(resolved, 0.15)
