#!/usr/bin/env python3
"""Kestrel Bay interior dressing generator.

Everything is authored in BUILDING-LOCAL Godot coords (x right, z = +n/back, -z = s/front door face),
then rotated by the building's rot and offset by its pos into cell-local coords, and re-binned into
whichever cell actually contains the world point (props clamp at +-7.5, NPCs at +-7.0 of a cell).
"""
import json, math, sys, copy
from collections import defaultdict

MESHY = "/cloud-q7026dnarajiwk7glrcg/models/meshy/"
LIB = "props/vostok_extra/"
CELL = 16.0

# footprint sizes (x, z) in the asset's own frame, measured from the GLBs
SIZE = {
 "pub_bar_counter": (4.0, 0.97), "pub_back_bar": (3.2, 0.45), "bar_stool": (0.54, 0.54),
 "pub_table_round": (0.81, 0.81), "pub_chair": (0.44, 0.46), "harbour_desk": (1.8, 0.91),
 "office_chair_wooden": (0.74, 0.71), "ledger_shelf": (1.2, 0.4), "chapel_pew": (2.53, 0.59),
 "chapel_altar": (1.72, 0.8), "chapel_lectern": (0.57, 0.55), "iron_bed": (0.84, 1.9),
 "wardrobe_pine": (1.0, 0.58), "welsh_dresser": (1.4, 0.51), "kitchen_table_set": (1.6, 0.9),
 "washstand": (1.08, 0.52), "coat_rack_oilskins": (1.29, 0.35), "rope_coil_large": (1.2, 1.2),
 "buoy_cluster": (1.26, 1.3), "anchor_old": (1.48, 0.2), "cart_wooden": (1.2, 2.18),
 "water_trough_stone": (1.6, 0.7), "harbour_bench": (1.8, 0.71), "lobster_pots": (1.6, 0.88),
 "fish_crates": (1.2, 0.85), "net_pile": (2.2, 2.2), "oil_drums_rusty": (1.8, 1.79),
 "MS_Fireplace_Tower": (1.0, 1.01), "MS_Dartboard": (0.8, 0.06), "MS_Candle": (0.3, 0.3),
 "MS_Carpet": (1.2, 2.0), "MS_Cabinet_Basic": (1.0, 0.4), "MS_Crate": (1.96, 1.0),
 "MS_Pallet": (1.4, 0.9), "MS_Sawbuck": (1.4, 1.4), "MS_Plank_Pile": (2.14, 4.08),
 "MS_Cable_Reel": (1.0, 2.0), "MS_Campfire": (1.38, 1.3), "MS_Tent_Civilian": (2.28, 2.28),
}
def url(name):
    return (LIB if name.startswith("MS_") else MESHY) + name + ".glb"

world = json.load(open("/workspace/repo/world.json"))
# NPC roster by id: the live world.json first (the coordinator is merging as we go), then the
# /workspace/world.json snapshot the roster was authored in. Position/seated/activity are re-derived.
ROSTER = {}
for src in ("/workspace/world.json", "/workspace/repo/world.json"):
    for c in json.load(open(src))["cells"]:
        if isinstance(c.get("npc"), dict) and c["npc"].get("id"):
            ROSTER[c["npc"]["id"]] = c["npc"]
def npc_of(npc_id):
    n = copy.deepcopy(ROSTER[npc_id])
    for k in ("pos", "seated", "activity", "holds"): n.pop(k, None)
    if "model" in n: n["model"] = MESHY + n["model"].rsplit("/", 1)[-1]
    return n

# ------------------------------------------------------------------ geometry helpers
def to_cell(b, lx, lz):
    """building-local -> offset from the building's cell centre (engine convention)."""
    yaw = math.radians(b["rot"])
    c, s = math.cos(yaw), math.sin(yaw)
    return (b["pos"][0] + lx * c + lz * s, b["pos"][1] - lx * s + lz * c)

def rebin(b, ox, oz):
    """offset from cell (gx,gz) centre -> (cell, local) honouring the +-8 cell edge."""
    gx, gz = b["cell"]
    dx = math.floor((ox + 8.0) / CELL); dz = math.floor((oz + 8.0) / CELL)
    return (gx + dx, gz + dz), (round(ox - dx * CELL, 3), round(oz - dz * CELL, 3))

def rect_corners(cx, cz, hx, hz, yaw):
    c, s = math.cos(yaw), math.sin(yaw)
    out = []
    for sx, sz in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        lx, lz = sx * hx, sz * hz
        out.append((cx + lx * c + lz * s, cz - lx * s + lz * c))
    return out

def penetration(a, b):
    A, B = rect_corners(*a), rect_corners(*b)
    mn = 1e9
    for r in (a, b):
        c, s = math.cos(r[4]), math.sin(r[4])
        for ax, az in ((c, -s), (s, c)):
            a0 = min(x * ax + z * az for x, z in A); a1 = max(x * ax + z * az for x, z in A)
            b0 = min(x * ax + z * az for x, z in B); b1 = max(x * ax + z * az for x, z in B)
            gap = min(a1, b1) - max(a0, b0)
            if gap <= 0: return 0.0
            mn = min(mn, gap)
    return mn

# ------------------------------------------------------------------ the buildings (from enterables.json)
B = {}
LIVE = {}
for _c in world["cells"]:
    for _p in _c.get("props", []) + ([_c["landmark"]] if "landmark" in _c else []):
        if isinstance(_p, dict) and _p.get("mason_type") and _p.get("footprint"):
            LIVE.setdefault(_p["mason_type"], (tuple(_c["cell"]), tuple(_p["pos"]), float(_p.get("rot", 0))))

def building(name, cell, pos, rot, fp, wall_t, floors, fh, clear, circle=None):
    # the LIVE world.json wins over the delegation's enterables.json — buildings have moved under us
    if name in LIVE:
        lc, lp, lr = LIVE[name]
        if lc != tuple(cell) or tuple(lp) != tuple(pos) or lr != rot:
            if "--live" in sys.argv:
                print(f"NOTE {name}: enterables said cell {cell} pos {pos} rot {rot}; world.json has cell {lc} pos {lp} rot {lr} -> using world.json (--live)")
                cell, pos, rot = lc, lp, lr
            else:
                print(f"NOTE {name}: world.json currently has cell {lc} pos {lp} rot {lr}, enterables.json says cell {cell} pos {pos} rot {rot} -> authoring to enterables.json (re-run with --live to follow world.json)")
    elif name in LIVE or True:
        if name not in LIVE: print(f"NOTE {name}: not present in the live world.json right now -> authoring to enterables.json")
    B[name] = dict(name=name, cell=cell, pos=pos, rot=rot, fp=fp, wall_t=wall_t, floors=floors, fh=fh,
                   clear=clear, circle=circle, items=[], npcs=[])

# keep-clear rects are (cx, cz, hx, hz, storey) in building-local; storey None = every storey
def R(x0, x1, z0, z1, storey=0):
    return ((x0 + x1) / 2, (z0 + z1) / 2, (x1 - x0) / 2, (z1 - z0) / 2, storey)

# PUB 14x10 rot 180: interior x+-6.55 z+-4.55. front door s centre 0; back door n centre -4.
# stair enclosure x -6.55..-5.45, z -2.9..+1.3 (+1.5 m standing room toward the front wall).
building("pub", (-1, 5), (-3.5, 5.5), 180, (14, 10), 0.45, 2, 3.2, [
    R(-0.75, 0.75, -5.0, -3.35),           # front door + 1.2 m
    R(-4.65, -3.35, 3.35, 5.0),            # back door + 1.2 m
    R(-6.55, -5.45, -4.4, 1.3, None),      # stair hall + landing (both storeys)
    R(-6.55, -4.55, 1.3, 2.2, 1),          # upstairs newel/arrival strip
])
# HARBOUR OFFICE 9x7 rot 315: interior x+-4.05 z+-3.05; door s centre -2.2; stair along x on n wall
# flight z 1.75..3.0, x -2.3..2.0 foot WEST (landing x -3.2..-2.3), head EAST (upstairs x 2.0..2.9).
building("harbour_office", (1, 1), (3.8, -7.5), 315, (9, 7), 0.45, 2, 3.0, [
    R(-2.9, -1.5, -3.5, -1.85),
    R(-3.2, 2.0, 1.75, 3.05, 0),           # flight + foot landing (ground)
    R(-2.5, 2.9, 1.75, 3.05, 1),           # stairwell strip upstairs + head landing
    R(1.1, 2.9, 0.85, 1.75, 1),            # step-off room at the head
])
# CHANDLERY 10x8 rot 180: interior x+-4.55 z+-3.55; door s centre -3.4; stair along x on n wall
# flight z 2.25..3.5, x -2.3..2.0 foot WEST.
building("chandlery", (0, 5), (7.45, 6.5), 180, (10, 8), 0.45, 2, 3.0, [
    R(-4.1, -2.7, -4.0, -2.35),
    R(-3.2, 2.0, 2.25, 3.55, 0),
    R(-2.5, 2.9, 2.25, 3.55, 1),
    R(1.1, 2.9, 1.35, 2.25, 1),
])
# HOUSE_E 8x7 rot 180: interior x+-3.55 z+-3.05; door s centre -2.0; stair along x on n wall
# flight z 1.75..3.0, x -2.2..1.9 foot WEST.
building("house_e", (-3, 5), (5.0, 7.0), 180, (8, 7), 0.45, 2, 2.9, [
    R(-2.65, -1.35, -3.5, -1.85),
    R(-3.1, 1.9, 1.75, 3.05, 0),
    R(-2.4, 2.8, 1.75, 3.05, 1),
    R(1.0, 2.8, 0.85, 1.75, 1),
])
# NET SHED 18x10 rot 135: interior x+-8.65 z+-4.65; double door s centre 0 w 2.4 -> keep a lane.
building("net_shed", (0, 1), (3.76, -3.76), 135, (18, 10), 0.35, 1, 5.5, [
    R(-1.5, 1.5, -5.0, 0.0),
])
# CHAPEL 10x26.9 rot 0: nave floor z -6.65..7.65 (tower mass to -6.65), chancel x+-3 z 7.45..12.95.
building("chapel", (1, 9), (4.0, 6.0), 0, (10.0, 26.9), 0.5, 1, 7.4, [
    R(-5.0, 5.0, -13.45, -6.65),           # porch + tower: nothing there
    R(-0.7, 0.7, -6.65, 7.65),             # nave axis aisle
])
# LIGHTHOUSE round r 3.6 inside, rot 243.4; door s; flights x+-0.625 w 0.95 z -1.9..1.9 (+0.9 landings)
building("lighthouse", (-9, 9), (-1.0, -3.0), 243.4, (8, 8), 0.4, 6, 3.4, [
    R(-0.7, 0.7, -4.0, -2.4),
    R(0.15 - 0.9, 1.1 + 0.9, -3.7, 3.7, 0),                 # flight 1 + 0.9 m clearance (ground)
    R(-2.0, 2.0, -3.7, 3.7, 1), R(-2.0, 2.0, -3.7, 3.7, 2),   # both flights above
], circle=3.6)
# FISH MARKET 12x8 rot 180: interior x+-5.55 z+-3.55; arches s at -4,0,4 and n at 0 (w 2.0)
building("fish_market", (8, 1), (6.0, 4.0), 180, (12, 8), 0.45, 1, 4.5, [
    R(-5.15, -2.85, -4.0, -2.35), R(-1.15, 1.15, -4.0, -2.35), R(2.85, 5.15, -4.0, -2.35),
    R(-1.15, 1.15, 2.35, 4.0),
    R(-1.15, 1.15, -2.35, 2.35),           # the through-route between the s and n arches
])
# WRECK hold 23x7 rot 109.4; gash s centre -3 (w 1.6)
building("wreck", (9, -6), (-1.74, -0.34), 109.4, (24, 8), 0.4, 1, 4.6, [
    R(-3.8, -2.2, -4.0, -2.4),
])
# SEA CAVES: main chamber only, void 13.1 x 9.6 centred (3.75, 0.5) -> handled by an ellipse test
building("sea_caves", (10, -4), (-6.29, -5.88), 19.4, (22, 16), 0.7, 1, 5.0, [])

def add(bname, asset, lx, lz, phi=0, y=0.0, storey=0, **kw):
    B[bname]["items"].append(dict(asset=asset, lx=lx, lz=lz, phi=phi, y=y, storey=storey, kw=kw))

def add_npc(bname, npc, lx, lz, y=0.0, **fields):
    npc = copy.deepcopy(npc); npc.update(fields)
    B[bname]["npcs"].append(dict(npc=npc, lx=lx, lz=lz, y=y))

# ================================================================== THE KESTREL ARMS (pub)
# Back band (local z +1.5..+4.55, x -3..+6.5) is the bar. Prop fronts are +z in their own frame.
# Back bar against the n wall (front toward -z = into the room -> phi 180). x centre +4.4 puts the
# bar's far end 0.15 m off the e gable, which is what lets Dai's stool fall in cell (-2,5).
add("pub", "pub_back_bar", 3.9, 4.10, 180, group="pub_bar")
add("pub", "pub_bar_counter", 3.9, 2.40, 180, group="pub_bar")       # customer side faces -z (the room)
for x in (5.5, 3.9, 2.6):
    add("pub", "bar_stool", x, 1.50, 0, sit=True, group="pub_bar")   # Dai sits on the 5.5 one (end of the bar)
# gable fireplace on the e gable (x +6.55), hearth facing -x -> phi 270
add("pub", "MS_Fireplace_Tower", 6.05, -1.50, 270)
# dartboard on the n wall between the bar and the back door, 1.55 m up (a 1.6 lift would snap upstairs)
add("pub", "MS_Dartboard", -0.5, 4.51, 180, y=1.55, collider=False)
# tables: t1 by the fire, t2 mid room, t3 by the front windows, t4 near the stair side
def pub_table(name, tx, tz, chairs, candle=False):
    add("pub", "pub_table_round", tx, tz, 0, group=name)
    for dx, dz, phi in chairs:
        add("pub", "pub_chair", tx + dx, tz + dz, phi, sit=True, group=name)
    if candle:
        add("pub", "MS_Candle", tx, tz, 0, y=0.8, collider=False, group=name)
pub_table("pub_t1", 3.5, -1.5, [(0, 0.7, 180), (-0.7, 0, 90)], candle=True)
pub_table("pub_t2", -1.5, -1.3, [(0, 0.7, 180), (0, -0.65, 0), (0.7, 0, 270)])
pub_table("pub_t3", 2.0, -3.5, [(0, -0.7, 0), (0.7, 0, 270), (-0.7, 0, 90)], candle=True)
pub_table("pub_t4", -3.9, 0.6, [(0, 0.7, 180), (0, -0.7, 0), (0.7, 0, 270)])
# coat rack beside the front door (front wall, east of the door zone; windows at +-2.4/+-4.4)
add("pub", "coat_rack_oilskins", -1.35, -4.32, 0)
# UPSTAIRS (y 3.2): notional party walls at x -2.5 / +2.5, corridor along the n wall (z > 2.5)
add("pub", "iron_bed", 5.55, -1.9, 270, y=3.2, storey=1)             # head to the e gable
add("pub", "washstand", 6.24, -3.8, 270, y=3.2, storey=1, group="pub_roomC")   # against the e gable
add("pub", "MS_Candle", 6.24, -3.8, 0, y=3.2 + 0.95, storey=1, collider=False, group="pub_roomC")
add("pub", "wardrobe_pine", 3.1, -4.21, 0, y=3.2, storey=1)           # front wall, clear of the +4.4 window
add("pub", "iron_bed", 1.7, -3.55, 0, y=3.2, storey=1)                # head to the front wall (room B)
add("pub", "washstand", 0.0, -4.24, 0, y=3.2, storey=1)               # under the centre upper window
add("pub", "wardrobe_pine", -1.7, -4.21, 0, y=3.2, storey=1)
add("pub", "MS_Carpet", 0.5, -1.0, 90, y=3.2, storey=1, collider=False)
# NPCs
morwenna = npc_of("barmaid"); dai = npc_of("regular")
add_npc("pub", morwenna, 3.4, 3.4, activity="idle")                  # behind the bar, in the service gap
add_npc("pub", dai, 5.5, 1.50, y=0.3, seated=True)                  # on the end stool (stool top 0.75, hips 0.46)

# ================================================================== HARBOUR OFFICE
# NPCs have no authored yaw in this engine (interaction.add_npc) - every character faces WORLD +z,
# which in this rot-315 office is local NE, i.e. AWAY from the s door. "Behind the desk" would have
# Alwyn staring at the back wall, so he stands at the door side of his desk bent over the charts,
# facing it, with his chair pulled out behind it.
add("harbour_office", "harbour_desk", 1.6, 0.9, 180, group="office_desk")       # visitor side to the door
add("harbour_office", "office_chair_wooden", 2.9, 0.9, 270, sit=True, group="office_desk")   # at the desk end
add("harbour_office", "MS_Candle", 1.4, 0.9, 0, y=0.85, collider=False, group="office_desk")
add("harbour_office", "ledger_shelf", 3.8, -0.6, 270)                          # e wall
add("harbour_office", "MS_Cabinet_Basic", 3.8, 2.2, 270)                       # e wall under the stair head (mesh extends into room)
add("harbour_office", "rope_coil_large", 2.7, -2.4, 0)                         # SE corner (3.35 would clamp)
add("harbour_office", "MS_Fireplace_Tower", -3.55, -0.8, 90)                   # w wall, hearth facing +x
add("harbour_office", "coat_rack_oilskins", -0.7, -2.83, 0)                    # s wall, east of the door
add("harbour_office", "kitchen_table_set", -0.8, -1.7, 0, y=3.0, storey=1, group="office_kitchen")
add("harbour_office", "pub_chair", -0.8, -0.95, 180, y=3.0, storey=1, sit=True, group="office_kitchen")
add("harbour_office", "pub_chair", -0.8, -2.45, 0, y=3.0, storey=1, sit=True, group="office_kitchen")
add("harbour_office", "iron_bed", 3.05, -2.0, 270, y=3.0, storey=1)            # head to the e wall
add("harbour_office", "MS_Cabinet_Basic", -3.8, -1.5, 90, y=3.0, storey=1)
alwyn = npc_of("harbour_master")
add_npc("harbour_office", alwyn, 1.0, -0.1, activity="idle")                   # at the desk, facing his charts (NE)

# ================================================================== CHANDLERY
add("chandlery", "pub_bar_counter", 3.27, -0.2, 270, group="shop_counter")     # along the e wall, front to -x
add("chandlery", "MS_Candle", 3.27, 0.8, 0, y=1.15, collider=False, group="shop_counter")
add("chandlery", "ledger_shelf", -4.3, -2.2, 90)                                # w wall stock shelves
add("chandlery", "ledger_shelf", -4.3, -0.6, 90)
add("chandlery", "buoy_cluster", -3.9, 1.4, 0)
add("chandlery", "coat_rack_oilskins", -1.65, -3.33, 0)                        # s wall between door and window
add("chandlery", "rope_coil_large", 0.9, -2.9, 0)                              # under the shop window
add("chandlery", "rope_coil_large", 3.9, -2.9, 0)
add("chandlery", "MS_Crate", 0.0, 0.6, 0)                                      # stock island
add("chandlery", "MS_Crate", 0.0, 1.75, 0)
add("chandlery", "fish_crates", 0.0, -0.9, 0)
add("chandlery", "lobster_pots", -1.9, -0.9, 90)
add("chandlery", "MS_Crate", 3.2, 2.55, 0)                                     # under the stair head
add("chandlery", "anchor_old", 3.75, 3.35, 0)                                  # leaning on the n wall
add("chandlery", "iron_bed", 3.55, -2.4, 270, y=3.0, storey=1)
add("chandlery", "wardrobe_pine", 1.9, -3.21, 0, y=3.0, storey=1)
add("chandlery", "kitchen_table_set", -1.5, -0.8, 0, y=3.0, storey=1, group="chandler_kitchen")
add("chandlery", "pub_chair", -1.5, 0.0, 180, y=3.0, storey=1, sit=True, group="chandler_kitchen")
add("chandlery", "welsh_dresser", -4.25, 0.5, 90, y=3.0, storey=1)

# ================================================================== HOUSE_E (fisherman's home)
add("house_e", "kitchen_table_set", 0.3, 0.4, 0, group="house_table")
add("house_e", "pub_chair", 0.3, 1.15, 180, sit=True, group="house_table")
add("house_e", "pub_chair", 0.3, -0.35, 0, sit=True, group="house_table")
add("house_e", "pub_chair", 1.25, 0.4, 270, sit=True, group="house_table")
add("house_e", "MS_Carpet", 0.3, 0.4, 90, collider=False, group="house_table")
add("house_e", "MS_Fireplace_Tower", 3.05, -1.6, 270)                          # e gable (chimney side)
add("house_e", "welsh_dresser", 3.25, 0.6, 270)                                # e wall north of the fire
add("house_e", "coat_rack_oilskins", -0.6, -2.83, 0)                           # s wall east of the door
add("house_e", "iron_bed", 2.55, -1.8, 270, y=2.9, storey=1)
add("house_e", "wardrobe_pine", 0.5, -2.71, 0, y=2.9, storey=1)
add("house_e", "washstand", -1.3, -2.74, 0, y=2.9, storey=1, group="house_wash")
add("house_e", "MS_Candle", -1.3, -2.74, 0, y=2.9 + 0.95, storey=1, collider=False, group="house_wash")

# ================================================================== NET SHED (working loft)
add("net_shed", "net_pile", -7.2, 3.3, 0)
add("net_shed", "net_pile", -4.6, 3.3, 0)
add("net_shed", "net_pile", 4.0, 0.5, 0)
add("net_shed", "harbour_bench", -0.8, 4.25, 180, sit=True)                    # n wall, facing the hall
add("net_shed", "MS_Sawbuck", -0.5, 2.8, 0)
add("net_shed", "MS_Plank_Pile", 3.5, 3.3, 90)
add("net_shed", "MS_Cable_Reel", 7.4, 3.4, 0)
add("net_shed", "rope_coil_large", -7.9, 0.5, 0)
add("net_shed", "rope_coil_large", -4.8, 0.0, 0)
add("net_shed", "buoy_cluster", -7.9, -2.9, 0)
add("net_shed", "buoy_cluster", 5.0, -2.2, 0)
add("net_shed", "lobster_pots", -3.2, -4.1, 0)
add("net_shed", "lobster_pots", -5.2, -4.1, 0)
add("net_shed", "lobster_pots", 4.9, -4.1, 0)
add("net_shed", "fish_crates", -6.9, -4.1, 0)
add("net_shed", "fish_crates", 3.0, -4.1, 0)
add("net_shed", "cart_wooden", 7.7, -0.5, 0)
add("net_shed", "oil_drums_rusty", 7.4, -3.4, 0)
# OUTSIDE: Pasco stays on the quay by the door (local z -6.6 is 1.6 m outside the s wall) with a net pile
add("net_shed", "net_pile", 5.0, -6.4, 0, outside=True)
pasco = npc_of("netman")
add_npc("net_shed", pasco, 2.97, -6.59, activity="idle_work", holds=MESHY + "mending_net_hand.glb")

# ================================================================== CHAPEL
for z in (-1.9, -0.8, 0.3, 1.4, 2.6, 3.7):        # (z 1.5..2.5 skipped: that band is the +-7.5 cell clamp)
    for x in (-2.0, 2.0):
        add("chapel", "chapel_pew", x, z, 0, sit=True)
add("chapel", "chapel_lectern", 1.3, 6.8, 180)
add("chapel", "chapel_altar", 0.0, 12.4, 180, group="altar")
add("chapel", "MS_Candle", -0.55, 12.4, 0, y=1.05, collider=False, group="altar")
add("chapel", "MS_Candle", 0.55, 12.4, 0, y=1.05, collider=False, group="altar")
enys = npc_of("verger")
add_npc("chapel", enys, -2.0, -3.4, activity="idle")                            # behind the back pews

# ================================================================== LIGHTHOUSE
add("lighthouse", "MS_Cabinet_Basic", -3.1, 0.3, 90, group="keeper_cabinet")
add("lighthouse", "MS_Candle", -3.0, 0.3, 0, y=1.0, collider=False, group="keeper_cabinet")
add("lighthouse", "coat_rack_oilskins", -2.3, -2.3, 45)
add("lighthouse", "MS_Crate", 2.55, 0.8, 90)
add("lighthouse", "kitchen_table_set", 2.9, 0.0, 90, y=3.4, storey=1, group="keeper_table")
add("lighthouse", "pub_chair", 2.9, 1.35, 180, y=3.4, storey=1, sit=True, group="keeper_table")
add("lighthouse", "iron_bed", -2.7, 0.0, 0, y=6.8, storey=2)
add("lighthouse", "washstand", 2.9, -0.5, 270, y=6.8, storey=2)
tamsin = npc_of("keeper")
add_npc("lighthouse", tamsin, -2.2, 1.6, activity="idle")

# ================================================================== FISH MARKET
add("fish_market", "fish_crates", 2.0, -2.4, 0)                                # in front of the east s pier
add("fish_market", "fish_crates", -3.0, 3.1, 0)                                # n wall stalls
add("fish_market", "fish_crates", 3.0, 3.1, 0)
add("fish_market", "lobster_pots", -4.6, 3.1, 0)
add("fish_market", "lobster_pots", 4.6, 3.1, 0)
add("fish_market", "MS_Crate", 4.9, 0.0, 90)                                   # e end wall
add("fish_market", "MS_Crate", -4.9, -0.3, 90)                                 # w end wall
add("fish_market", "MS_Pallet", 4.7, -1.9, 0)
add("fish_market", "MS_Pallet", -4.7, -1.9, 0)
add("fish_market", "water_trough_stone", -4.85, 1.8, 90)
add("fish_market", "cart_wooden", 2.4, 0.6, 0)
add("fish_market", "harbour_bench", -3.1, 0.3, 180, sit=True)                  # facing the quay arches

# ================================================================== WRECK hold + SEA CAVES main chamber
add("wreck", "MS_Crate", 2.0, 2.3, 0)
add("wreck", "MS_Crate", 5.0, 2.3, 0)
add("wreck", "oil_drums_rusty", -6.5, 1.8, 0)
add("wreck", "rope_coil_large", -6.0, -2.3, 0)
add("sea_caves", "MS_Campfire", 5.0, 1.4, 0, collider=False)
add("sea_caves", "MS_Tent_Civilian", 7.0, 2.5, 0)
add("sea_caves", "MS_Crate", 1.0, -0.5, 0)
add("sea_caves", "MS_Crate", 0.5, 2.8, 90)
add("sea_caves", "MS_Crate", 8.5, 0.0, 0)
add("sea_caves", "oil_drums_rusty", 6.5, -1.0, 0)
add("sea_caves", "oil_drums_rusty", 2.5, 3.0, 0)

# ================================================================== quay fishermen (outdoor, seat under them)
QUAY = [((0, 0), npc_of("old_salt"), (-6.62, -2.38)), ((2, 2), npc_of("deckhand"), (0.06, -3.06))]

# ================================================================== checks + emit
problems = []
cells = defaultdict(lambda: {"props": [], "npc": None})
unbinned = defaultdict(list)
for b in B.values():
    hx, hz = b["fp"][0] / 2 - b["wall_t"], b["fp"][1] / 2 - b["wall_t"]
    placed = []
    for it in b["items"]:
        sx, sz = SIZE[it["asset"]]
        yaw = math.radians(it["phi"])
        rect = (it["lx"], it["lz"], sx / 2, sz / 2, yaw)
        tag = f'{b["name"]}/{it["asset"]}@({it["lx"]},{it["lz"]})'
        outside = it["kw"].pop("outside", False)
        if not outside:
            # inside the inner faces (rect) or the circle / chamber ellipse
            if b["name"] == "sea_caves":
                for cx, cz in rect_corners(*rect):
                    nx, nz = (cx - 3.75) / 6.55, (cz - 0.5) / 4.8
                    if nx * nx + nz * nz > 0.9: problems.append(f"{tag}: outside the main chamber ellipse ({nx*nx+nz*nz:.2f})")
            elif b["circle"]:
                for cx, cz in rect_corners(*rect):
                    if math.hypot(cx, cz) > b["circle"]: problems.append(f"{tag}: corner outside r={b['circle']} ({math.hypot(cx,cz):.2f})")
            else:
                for cx, cz in rect_corners(*rect):
                    if abs(cx) > hx + 0.02 or abs(cz) > hz + 0.02: problems.append(f"{tag}: corner ({cx:.2f},{cz:.2f}) in the wall (inner +-{hx},+-{hz})")
            for cr in b["clear"]:
                if cr[4] is not None and cr[4] != it["storey"]: continue
                pen = penetration(rect, (cr[0], cr[1], cr[2], cr[3], 0.0))
                if pen > 0.05 and not (it["asset"] == "MS_Candle"):
                    problems.append(f"{tag}: {pen:.2f} m into keep-clear zone {cr}")
            for other, orect, ostorey, ogroup in placed:
                if ostorey != it["storey"]: continue
                g = it["kw"].get("group")
                if g and g == ogroup: continue
                pen = penetration(rect, orect)
                if pen > 0.05: problems.append(f"{tag} overlaps {other} by {pen:.2f}")
            placed.append((it["asset"], rect, it["storey"], it["kw"].get("group")))
        ox, oz = to_cell(b, it["lx"], it["lz"])
        cell, (px, pz) = rebin(b, ox, oz)
        if abs(px) > 7.5 or abs(pz) > 7.5: problems.append(f"{tag}: cell-local ({px},{pz}) would be CLAMPED")
        rot = round((b["rot"] + it["phi"]) % 360, 1)
        prop = {"url": url(it["asset"]), "pos": [px, round(it["y"], 3), pz] if it["y"] else [px, pz], "rot": rot}
        prop.update(it["kw"])
        prop["furn"] = True
        cells[cell]["props"].append(prop)
        # verification-only twin: every prop in its BUILDING's cell with the raw (unclamped) offset,
        # so the gate (which only compares props with buildings of the same cell) sees all of them
        raw = dict(prop); raw["pos"] = [round(ox, 3), round(it["y"], 3), round(oz, 3)] if it["y"] else [round(ox, 3), round(oz, 3)]
        unbinned[tuple(b["cell"])].append(raw)
    for n in b["npcs"]:
        ox, oz = to_cell(b, n["lx"], n["lz"])
        cell, (px, pz) = rebin(b, ox, oz)
        if abs(px) > 7.0 or abs(pz) > 7.0: problems.append(f'NPC {n["npc"]["id"]}: cell-local ({px},{pz}) would be CLAMPED')
        if cells[cell]["npc"] is not None: problems.append(f'NPC {n["npc"]["id"]}: cell {cell} already has npc {cells[cell]["npc"]["id"]}')
        # an NPC inside must be clear of the furniture (capsule r 0.5) and the keep-clear zones
        if b["name"] != "net_shed" and not n["npc"].get("seated"):
            nrect = (n["lx"], n["lz"], 0.45, 0.45, 0.0)
            for other, orect, ostorey, _ in placed:
                if ostorey == 0 and penetration(nrect, orect) > 0.05: problems.append(f'NPC {n["npc"]["id"]} stands in {other}')
            for cr in b["clear"]:
                if cr[4] in (None, 0) and penetration(nrect, (cr[0], cr[1], cr[2], cr[3], 0.0)) > 0.05: problems.append(f'NPC {n["npc"]["id"]} in keep-clear {cr}')
        npc = n["npc"]
        npc["pos"] = [px, round(n["y"], 3), pz] if n["y"] else [px, pz]
        cells[cell]["npc"] = npc
        print(f'NPC {npc["id"]:14s} -> cell {cell} pos {npc["pos"]}  (building {b["name"]} local ({n["lx"]},{n["lz"]}))')

for cell, npc, pos in QUAY:
    npc["pos"] = list(pos); npc["seated"] = True
    if cells[cell]["npc"] is not None: problems.append(f"quay npc clash in {cell}")
    cells[cell]["npc"] = npc
    # bench front is +z in the GLB (backrest at -z) and an NPC faces +z: rot 0 puts him ON the seat, facing out
    cells[cell]["props"].append({"url": url("harbour_bench"), "pos": list(pos), "rot": 0, "sit": True, "furn": True})

out = {"cells": []}
for cell in sorted(cells):
    e = {"cell": list(cell), "props": cells[cell]["props"]}
    if cells[cell]["npc"] is not None: e["npc"] = cells[cell]["npc"]
    out["cells"].append(e)
json.dump(out, open("/workspace/dressing.json", "w"), indent=1)
json.dump({"cells": [{"cell": list(k), "props": v} for k, v in unbinned.items()]}, open("/tmp/check/dressing_unbinned.json", "w"), indent=1)
print(f"\n{sum(len(c['props']) for c in cells.values())} props in {len(cells)} cells, "
      f"{sum(1 for c in cells.values() if c['npc'])} npcs")
print("\nLOCAL CHECK:", "clean" if not problems else f"{len(problems)} problem(s)")
for p in problems: print("  -", p)
sys.exit(1 if problems else 0)
