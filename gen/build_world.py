#!/usr/bin/env python3
"""Kestrel Bay world assembler.

Inputs:  the Architect's layout (/workspace/world.json) or the repo world as fallback,
         compiled Mason records (models/mason/mason_assets.jsonl + structures.json),
         Meshy assets present in models/meshy/, dressing.json (optional).
Output:  /workspace/repo/world.json
"""
import json, math, random, sys, os, copy, collections

NEW_BID = "cloud-q7026dnarajiwk7glrcg"
OLD_BID = "cloud-cbnqgdi78kdlrr3elmbb"
REPO = "/workspace/repo"
ARCH = "/workspace/world.json"
DRESS = "/workspace/dressing.json"
MESHY_DIR = f"{REPO}/models/meshy"
M = f"/{NEW_BID}/models/meshy/"

def meshy(name):
    return M + name + ".glb"

def have_meshy(name):
    return os.path.exists(f"{MESHY_DIR}/{name}.glb")

# ---------------- vegetation catalogue (library, single-mesh, sized) ----------------
P = "props/"
TREE_A = P + "mega_nature/CommonTree_3.glb"   # 4.1 x 9.4 m, 3.5k tris, textured
TREE_B = P + "mega_nature/CommonTree_1.glb"   # 4.3 x 7.3 m, 6.3k, textured (props only)
PINE_A = P + "mega_nature/Pine_1.glb"        # 4.9 x 7.3 m, 3.9k, textured
PINE_B = P + "mega_nature/Pine_5.glb"        # 6.4 x 8.7 m, 1.6k, textured
DEAD_A = P + "kenney_nature/Tree_Bare_2.glb"  # 1.8 x 5.7 m, 106, textured
DEAD_B = P + "kenney_nature/Tree_Bare_1.glb"
BUSH_A = P + "q_unature/Bush_1.glb"        # 1.3 m, 364
BUSH_B = P + "q_unature/Bush_2.glb"        # 1.35 m, 268
BERRY  = P + "q_unature/BushBerries_1.glb" # 1.4 m, 892
SHRUB  = P + "mega_nature/Plant_1_Big.glb" # 1.8 x 2.35 m, 360
FERN   = P + "mega_nature/Fern_1.glb"      # 2.8 x 0.84 m, 288
GRASS_S = P + "q_unature/Grass.glb"        # 0.37 x 1.0 m, 192
GRASS_W = P + "mega_nature/Grass_Wispy_Short.glb"  # 1.3 x 1.07 m, 494
REEDS  = P + "mega_nature/Grass_Common_Tall.glb"   # 0.9 x 1.87 m, 326
GROUND = P + "mega_nature/Plant_7.glb"     # 1.0 x 0.25 m, 48
MUSH   = P + "mega_nature/Mushroom_Common.glb"
ROCK1  = P + "mega_nature/Rock_Medium_1.glb"  # 3.2 m boulder, 342
ROCK2  = P + "mega_nature/Rock_Medium_2.glb"  # 3.0 m, 244
ROCK3  = P + "mega_nature/Rock_Medium_3.glb"  # 3.4 m, 522
PEBBLE = P + "mega_nature/Pebble_Round_1.glb"

def veg_urls():
    """Meshy vegetation with library fallbacks."""
    return {
        "hawthorn": meshy("hawthorn_windswept") if have_meshy("hawthorn_windswept") else P + "mega_nature/TwistedTree_2.glb",
        "hawthorn_scale": 1.0 if have_meshy("hawthorn_windswept") else 0.4,
        "gorse": meshy("gorse_bush") if have_meshy("gorse_bush") else BUSH_B,
        "heather": meshy("heather_clump") if have_meshy("heather_clump") else BERRY,
        "bracken": meshy("bracken_clump") if have_meshy("bracken_clump") else FERN,
    }

def S(url, count, collider=None):
    d = {"url": url, "count": int(count)}
    if collider is not None:
        d["collider"] = collider
    return d

def biome_scatter(biome, V, light):
    """Scatter entries per biome. `light` = the cell holds buildings/roads: only ground-hugging cover."""
    if biome in ("sea", "quay", "inlet_water"):
        return []
    if light:
        if biome in ("town", "quay", "farm"):
            return [S(GRASS_S, 5, False)]
        if biome in ("road_verge", "garden", "copse", "wood"):
            return [S(GRASS_S, 10, False), S(BUSH_A, 3, False)]
        return [S(GRASS_W, 8, False), S(GRASS_S, 6, False)]
    g, h, b = V["gorse"], V["heather"], V["bracken"]
    table = {
        "shore":      [S(ROCK1, 3), S(ROCK3, 2), S(PEBBLE, 30, False), S(GRASS_W, 8, False), S(g, 4, False)],
        "cliff":      [S(ROCK2, 3), S(g, 14, False), S(h, 10, False), S(GRASS_W, 16, False), S(BUSH_A, 6, False), S(DEAD_A, 1)],
        "town":       [S(GRASS_S, 6, False)],
        "garden":     [S(BUSH_A, 6, False), S(BERRY, 3, False), S(SHRUB, 3, False), S(GRASS_S, 14, False)],
        "field":      [S(GRASS_S, 30, False), S(GROUND, 24, False), S(GRASS_W, 10, False), S(BUSH_A, 3, False)],
        "farm":       [S(GRASS_S, 10, False), S(BUSH_A, 3, False)],
        "wood":       [S(TREE_A, 9), S(PINE_B, 12), S(DEAD_A, 3), S(BUSH_A, 12, False), S(b, 14, False),
                       S(SHRUB, 6, False), S(GROUND, 20, False), S(MUSH, 5, False), S(ROCK2, 2)],
        "copse":      [S(TREE_A, 5), S(PINE_B, 3), S(DEAD_A, 2), S(BUSH_A, 8, False), S(b, 6, False), S(GRASS_S, 20, False),
                       S(GROUND, 12, False), S(ROCK1, 2)],
        "heath":      [S(h, 22, False), S(g, 10, False), S(GRASS_W, 24, False), S(ROCK2, 3), S(GROUND, 14, False), S(DEAD_A, 1)],
        "moor_rock":  [S(ROCK1, 4), S(ROCK2, 4), S(ROCK3, 3), S(PEBBLE, 30, False), S(h, 16, False), S(GRASS_W, 16, False), S(g, 5, False)],
        "marsh":      [S(REEDS, 36, False), S(GRASS_W, 20, False), S(b, 6, False), S(GROUND, 20, False), S(ROCK2, 2), S(DEAD_B, 2)],
        "road_verge": [S(GRASS_S, 24, False), S(BUSH_A, 6, False), S(GRASS_W, 8, False)],
        "headland":   [S(GRASS_W, 20, False), S(g, 10, False), S(ROCK1, 5), S(PEBBLE, 16, False), S(h, 10, False), S(GRASS_S, 10, False)],
        "inlet":      [S(ROCK1, 6), S(ROCK3, 4), S(g, 5, False), S(GRASS_W, 8, False), S(PEBBLE, 20, False)],
    }
    return copy.deepcopy(table.get(biome, [S(GRASS_S, 12, False), S(GROUND, 10, False)]))

def biome_trees(biome, V):
    """Full-size tree PROPS per biome: list of (url, scale, collider, weight)."""
    hw, hs = V["hawthorn"], V["hawthorn_scale"]
    if biome == "wood":
        return [(PINE_A, 1.0, "trunk", 3), (TREE_B, 1.0, "trunk", 2), (hw, hs, "trunk", 1)]
    if biome == "copse":
        return [(TREE_A, 1.15, "trunk", 2), (hw, hs, "trunk", 1)]
    if biome in ("garden",):
        return [(TREE_A, 1.0, "trunk", 1)]
    if biome in ("field", "road_verge"):
        return [(hw, hs, "trunk", 1), (TREE_A, 1.0, "trunk", 1)]
    if biome in ("heath",):
        return [(hw, hs, "trunk", 1)]
    if biome in ("marsh",):
        return [(DEAD_B, 1.0, "trunk", 1), (ROCK2, 1.0, "box", 1)]
    if biome in ("moor_rock", "shore", "inlet"):
        return [(ROCK1, 1.0, "box", 2), (ROCK3, 1.2, "box", 1), (ROCK2, 1.0, "box", 1)]
    if biome in ("cliff", "headland"):
        return [(ROCK1, 1.0, "box", 1), (hw, hs, "trunk", 2), (DEAD_A, 1.0, "trunk", 1)]
    return []

def biome_ground(biome):
    return {
        "shore":      {"preset": "sand", "color": [0.40, 0.37, 0.32], "rough": 0.98, "bump": 0.5, "tile": 4.0},
        "cliff":      {"preset": "rock", "color": [0.31, 0.30, 0.29], "rough": 0.97, "bump": 0.8, "tile": 3.0},
        "quay":       {"preset": "cobble", "color": [0.26, 0.26, 0.27], "rough": 0.92, "bump": 0.65, "tile": 1.1},
        "town":       {"preset": "cobble", "color": [0.27, 0.27, 0.27], "rough": 0.92, "bump": 0.65, "tile": 1.1},
        "garden":     {"preset": "grass", "color": [0.30, 0.36, 0.22], "rough": 1.0, "bump": 0.5, "tile": 5.0},
        "field":      {"preset": "grass", "color": [0.29, 0.35, 0.21], "rough": 1.0, "bump": 0.5, "tile": 5.0},
        "farm":       {"preset": "mud", "color": [0.31, 0.26, 0.19], "rough": 0.75, "bump": 0.5, "tile": 4.0},
        "wood":       {"preset": "dirt", "color": [0.26, 0.24, 0.18], "rough": 0.98, "bump": 0.6, "tile": 4.0},
        "copse":      {"preset": "grass", "color": [0.27, 0.32, 0.20], "rough": 1.0, "bump": 0.5, "tile": 5.0},
        "heath":      {"preset": "grass", "color": [0.30, 0.29, 0.19], "rough": 1.0, "bump": 0.55, "tile": 4.5},
        "moor_rock":  {"preset": "rock", "color": [0.30, 0.29, 0.27], "rough": 0.97, "bump": 0.8, "tile": 3.0},
        "marsh":      {"preset": "mud", "color": [0.24, 0.24, 0.17], "rough": 0.6, "bump": 0.4, "tile": 4.5},
        "road_verge": {"preset": "grass", "color": [0.31, 0.37, 0.22], "rough": 1.0, "bump": 0.5, "tile": 5.0},
        "headland":   {"preset": "grass", "color": [0.28, 0.32, 0.21], "rough": 1.0, "bump": 0.5, "tile": 4.0},
        "inlet":      {"preset": "sand", "color": [0.38, 0.36, 0.32], "rough": 0.98, "bump": 0.55, "tile": 4.0},
        "sea":        {"preset": "sand", "color": [0.30, 0.30, 0.27], "rough": 0.98, "bump": 0.4, "tile": 5.0},
    }.get(biome, {"preset": "grass", "color": [0.29, 0.36, 0.22], "rough": 1.0, "bump": 0.5, "tile": 5.0})

# ---------------- geometry helpers ----------------
def rot_local(dx, dz, deg):
    """Godot yaw about +Y applied to a building-local offset: x' = x c + z s, z' = -x s + z c."""
    r = math.radians(deg); c, s = math.cos(r), math.sin(r)
    return dx * c + dz * s, -dx * s + dz * c

def in_rot_rect(px, pz, cx, cz, w, d, deg, margin=0.0):
    r = math.radians(deg); c, s = math.cos(r), math.sin(r)
    dx, dz = px - cx, pz - cz
    # inverse rotation
    lx = dx * c - dz * s
    lz = dx * s + dz * c
    return abs(lx) <= w / 2 + margin and abs(lz) <= d / 2 + margin

def blockers(cell):
    """Rotated rectangles (cx,cz,w,d,rot) + road strips for a cell, cell-local."""
    rects = []
    for src in ([cell.get("landmark")] if cell.get("landmark") else []) + cell.get("props", []) + cell.get("structures", []):
        if not isinstance(src, dict):
            continue
        fp = src.get("footprint")
        if fp:
            p = src.get("pos", [0, 0])
            rects.append((float(p[0]), float(p[-1]), float(fp[0]) * float(src.get("scale", 1.0)),
                          float(fp[1]) * float(src.get("scale", 1.0)), float(src.get("rot", 0.0))))
    roads = []
    for r in cell.get("roads", []) or []:
        roads.append((r.get("dir", "ns"), float(r.get("width", 6))))
    pts = []
    for p in cell.get("props", []):
        if isinstance(p, dict) and not p.get("footprint") and "pos" in p:
            pts.append((float(p["pos"][0]), float(p["pos"][-1])))
    for k in ("npc", "chest", "boss"):
        if isinstance(cell.get(k), dict) and "pos" in cell[k]:
            pts.append((float(cell[k]["pos"][0]), float(cell[k]["pos"][-1])))
    return rects, roads, pts

def spot_free(x, z, rects, roads, pts, half=8.0, bmargin=2.0, rmargin=1.5, pmargin=1.8):
    if abs(x) > half - 1.2 or abs(z) > half - 1.2:
        return False
    for (cx, cz, w, d, rot) in rects:
        if in_rot_rect(x, z, cx, cz, w, d, rot, bmargin):
            return False
    for (dr, wd) in roads:
        hw = wd / 2 + rmargin
        if dr in ("ns", "x") and abs(x) <= hw:
            return False
        if dr in ("ew", "x") and abs(z) <= hw:
            return False
    for (px, pz) in pts:
        if (px - x) ** 2 + (pz - z) ** 2 < pmargin ** 2:
            return False
    return True


# ---------------- terrain sampling (from the headless dump) ----------------
import numpy as _np
_H = _np.load("/tmp/H.npy"); _meta = json.load(open("/tmp/Hmeta.json"))
def terrain_h(x, z):
    i = (x - _meta["x0"]) / _meta["step"]; j = (z - _meta["z0"]) / _meta["step"]
    i0 = int(max(0, min(_meta["nx"] - 2, math.floor(i)))); j0 = int(max(0, min(_meta["nz"] - 2, math.floor(j))))
    fx = min(1.0, max(0.0, i - i0)); fz = min(1.0, max(0.0, j - j0))
    return float(_H[j0, i0] * (1 - fx) * (1 - fz) + _H[j0, i0 + 1] * fx * (1 - fz) + _H[j0 + 1, i0] * (1 - fx) * fz + _H[j0 + 1, i0 + 1] * fx * fz)

def _smooth(t):
    c = min(1.0, max(0.0, t)); return c * c * (3 - 2 * c)

def terrain_h2(x, z, basins):
    """terrain_h plus any basins/cones I add to world.terrain.features in this pass."""
    h = terrain_h(x, z)
    for b in basins:
        d = math.hypot(x - b["pos"][0], z - b["pos"][1])
        if d < b["radius"]:
            if b.get("type", "basin") == "cone":
                h += b["height"] * _smooth(1.0 - d / b["radius"])
            else:
                h -= b["depth"] * _smooth(1.0 - d / b["radius"])
    return h

def footprint_heights(wx, wz, w, d, rot, basins, n=7):
    hs = []
    for i in range(n):
        for j in range(n):
            lx = -w / 2 + w * i / (n - 1); lz = -d / 2 + d * j / (n - 1)
            ox, oz = rot_local(lx, lz, rot)
            hs.append(terrain_h2(wx + ox, wz + oz, basins))
    return min(hs), max(hs)

def door_approach_h(wx, wz, w, d, rot, face, centre, basins):
    """Lowest terrain across the approach samples the engine uses (0..1.8 m outboard)."""
    lo = 1e9
    for out in (0.0, 0.6, 1.2, 1.8):
        if face == "s": lx, lz = centre, -d / 2 - out
        elif face == "n": lx, lz = centre, d / 2 + out
        elif face == "e": lx, lz = w / 2 + out, centre
        else: lx, lz = -w / 2 - out, centre
        ox, oz = rot_local(lx, lz, rot)
        lo = min(lo, terrain_h2(wx + ox, wz + oz, basins))
    return lo

def way_in(spec):
    for o in spec.get("openings", []):
        if float(o.get("sill", 0)) <= 0.4 and not o.get("niche"):
            return o
    return None

def all_building_rects(w):
    """World-space rotated rects of every building (landmark or mason prop) across all cells."""
    out = []
    for c in w["cells"]:
        cx, cz = c["cell"][0] * 16 + 8, c["cell"][1] * 16 + 8
        srcs = ([c["landmark"]] if c.get("landmark") else []) + [p for p in c.get("props", []) if isinstance(p, dict) and p.get("footprint")]
        for s in srcs:
            p = s.get("pos", [0, 0])
            out.append((cx + float(p[0]), cz + float(p[-1]), float(s["footprint"][0]), float(s["footprint"][1]), float(s.get("rot", 0)), s.get("mason_type"), tuple(c["cell"])))
    return out

def rects_overlap(a, b, margin=0.0):
    """Separating-axis test on two rotated rects (cx,cz,w,d,rot)."""
    def corners(r):
        cx, cz, w, d, rot = r[:5]
        pts = []
        for sx, sz in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            ox, oz = rot_local(sx * (w / 2 + margin), sz * (d / 2 + margin), rot)
            pts.append((cx + ox, cz + oz))
        return pts
    def axes(r):
        rot = r[4]; c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
        return [(c, -s), (s, c)]
    ca, cb = corners(a), corners(b)
    for ax in axes(a) + axes(b):
        pa = [x * ax[0] + z * ax[1] for x, z in ca]; pb = [x * ax[0] + z * ax[1] for x, z in cb]
        if max(pa) < min(pb) or max(pb) < min(pa):
            return False
    return True

def road_hit_world(w, rect, margin=1.0):
    """Does a world rect cross any road strip (roads are cell-local axis strips)?"""
    cx, cz, wd, dp, rot = rect[:5]
    bycell = {tuple(c["cell"]): c for c in w["cells"]}
    pts = []
    for i in range(7):
        for j in range(7):
            lx = -wd / 2 + wd * i / 6; lz = -dp / 2 + dp * j / 6
            ox, oz = rot_local(lx, lz, rot); pts.append((cx + ox, cz + oz))
    for (px, pz) in pts:
        gx, gz = int(math.floor(px / 16)), int(math.floor(pz / 16))
        c = bycell.get((gx, gz))
        if not c: continue
        lx, lz = px - gx * 16 - 8, pz - gz * 16 - 8
        for r in c.get("roads", []) or []:
            hw = float(r.get("width", 6)) / 2 + margin
            if r.get("dir") in ("ns", "x") and abs(lx) <= hw: return True
            if r.get("dir") in ("ew", "x") and abs(lz) <= hw: return True
    return False

# ---------------- mason records ----------------
def load_mason():
    specs = {s["id"]: s for s in json.load(open(f"{REPO}/structures.json"))}
    recs = {}
    for line in open(f"{REPO}/models/mason/mason_assets.jsonl"):
        line = line.strip()
        if not line:
            continue
        r = json.loads(line)
        recs[r["id"]] = r
    return specs, recs

def building_record(mtype, specs, recs, pos, rot, extra=None):
    sp = specs[mtype]; rc = recs[mtype]
    rec = {"url": f"/{NEW_BID}/models/mason/{rc['hash']}.lod0.glb", "mason_type": mtype,
           "pos": [round(float(pos[0]), 2), round(float(pos[-1]), 2)], "rot": rot,
           "footprint": sp["footprint"], "collider": "mesh", "material": sp.get("material", "stone"),
           "floors": int(rc.get("floors_built") or sp.get("floors", 1)),
           "floor_height": sp.get("floor_height", 3.2)}
    if "interior" in sp and not (isinstance(sp["interior"], dict) and sp["interior"].get("sealed")):
        iv = {"floor_z": float(rc.get("floor_z", sp["interior"].get("floor_z", 0.2)))}
        st = sp["interior"].get("stair") if isinstance(sp["interior"], dict) else None
        if st:
            iv["stair"] = {k: st[k] for k in ("width", "axis", "rise", "riser", "tread") if k in st}
        rec["interior"] = iv
    rec["openings"] = sp.get("openings", [])
    rec["leaves"] = int(rc.get("leaves", 0))
    if extra:
        rec.update(extra)
    return rec


def find_slot(w, mtype, spec, cells_pref, basins, rots=(0, 90, 180, 270), exclude_types=()):
    fw, fd = float(spec["footprint"][0]), float(spec["footprint"][1])
    wi = way_in(spec); face = wi.get("face", "s") if wi else "s"; centre = float(wi.get("centre", 0)) if wi else 0.0
    rects = [r for r in all_building_rects(w) if r[5] not in exclude_types]
    bycell = {tuple(c["cell"]): c for c in w["cells"]}
    best = None
    for key in cells_pref:
        c = bycell.get(key)
        if not c: continue
        ccx, ccz = key[0] * 16 + 8, key[1] * 16 + 8
        pts = [(float(p["pos"][0]) + ccx, float(p["pos"][-1]) + ccz) for p in c.get("props", []) if isinstance(p, dict) and not p.get("footprint")]
        for lx in range(-7, 8):
            for lz in range(-7, 8):
                for rot in rots:
                    rect = (ccx + lx, ccz + lz, fw, fd, rot)
                    if any(rects_overlap(rect, r, 1.6) for r in rects): continue
                    if road_hit_world(w, rect, 1.5): continue
                    mn, mx = footprint_heights(rect[0], rect[1], fw, fd, rot, basins)
                    if mx - mn > 1.0: continue
                    # door front: a 6 m apron in front of the way in must be clear of buildings and touch a road
                    if face == "s": ax, az = centre, -fd / 2 - 5.0
                    elif face == "n": ax, az = centre, fd / 2 + 5.0
                    elif face == "e": ax, az = fw / 2 + 5.0, centre
                    else: ax, az = -fw / 2 - 5.0, centre
                    ox, oz = rot_local(ax, az, rot)
                    apron = (rect[0] + ox, rect[1] + oz, 6.0 if face in ("n", "s") else 10.0, 10.0 if face in ("n", "s") else 6.0, rot)
                    if any(rects_overlap(apron, r, 0.5) for r in rects): continue
                    if not road_hit_world(w, apron, 0.0): continue
                    # clutter under the footprint is allowed (I drop it later) but count it as cost
                    cost = sum(1 for (px, pz) in pts if in_rot_rect(px, pz, rect[0], rect[1], fw, fd, rot, 1.0)) * 0.5 + (mx - mn)
                    if best is None or cost < best[0]:
                        best = (cost, key, [lx, lz], rot)
    return best

PROP_SIZE = {}
for _l in open("/workspace/meshy_sizes.txt"):
    _f = _l.split()
    try:
        _sz = _f[3][6:-1].split(","); PROP_SIZE[_f[0]] = max(float(_sz[0]), float(_sz[2]))
    except Exception:
        pass
PROP_SIZE.update({"MS_Crate.glb": 0.9, "MS_Pallet.glb": 1.3, "MS_Plank_Pile.glb": 2.2, "MS_Cable_Reel.glb": 1.2, "MS_Barrier_Road.glb": 2.0,
    "MS_Firewood_A.glb": 1.2, "MS_Sawbuck.glb": 1.4, "MS_Board_Message.glb": 1.4, "MS_Mailbox.glb": 0.5, "MS_Planter_Box.glb": 2.0,
    "MS_Trash.glb": 0.8, "MS_Brick_Pile.glb": 1.5, "MS_Composter.glb": 1.2, "MS_Tent_Civilian.glb": 2.3, "MS_Campfire.glb": 1.2,
    "Prop_Hay_1.glb": 0.9, "Prop_Cart_1.glb": 3.4, "Prop_Cart_1_Hay.glb": 3.4, "Prop_Barrel_1.glb": 0.5, "Prop_Well_1.glb": 1.4, "Prop_Boat_1.glb": 2.3})

def drop_props_under_buildings(w):
    """Remove clutter (non-building, non-dressing props) whose position lies inside any building footprint."""
    rects = all_building_rects(w)
    n = 0
    for c in w["cells"]:
        cx, cz = c["cell"][0] * 16 + 8, c["cell"][1] * 16 + 8
        keep = []
        for p in c.get("props", []):
            if not isinstance(p, dict) or p.get("footprint") or p.get("dressing") or len(p.get("pos", [])) == 3:
                keep.append(p); continue
            px, pz = cx + float(p["pos"][0]), cz + float(p["pos"][-1])
            sz = PROP_SIZE.get(str(p.get("url", "")).split("/")[-1], 1.2) * float(p.get("scale", 1.0))
            prect = (px, pz, sz, sz, float(p.get("rot", 0)))
            if any(rects_overlap(prect, r, 0.35) for r in rects):
                n += 1; continue
            keep.append(p)
        c["props"] = keep
    return n

# ---------------- main assembly ----------------
def main():
    base = json.load(open(f"{REPO}/world.json"))
    w = json.load(open(ARCH)) if os.path.exists(ARCH) else copy.deepcopy(base)
    specs, recs = load_mason()
    V = veg_urls()

    # 1. rewrite every asset path onto THIS build
    txt = json.dumps(w).replace(f"/{OLD_BID}/", f"/{NEW_BID}/")
    w = json.loads(txt)

    cells = w["cells"]
    bycell = {tuple(c["cell"]): c for c in cells}
    # ---- placement fixes ----
    basins = [{"type": "basin", "pos": [20, 150], "radius": 26, "depth": 4.2}]
    feats = w["terrain"].setdefault("features", [])
    if not any(f.get("type") == "basin" for f in feats):
        feats.extend(basins)
    # SEA CAVE: the cave straddles a N-S gully (both banks ~2.4 m above the arch approach). Grounded at
    # the approach, its floor sat up to 1.6 m UNDER the bank terrain along the E/W walls - a climbable
    # wedge inside the chambers (QA: out through the SE wall). A shingle bank under the arch approach
    # lifts the whole floor above every interior terrain sample; the plinth + underpin close the back.
    cave_cone = {"type": "cone", "pos": [158.72, -67.35], "radius": 11.0, "height": 1.8}
    basins.append(cave_cone); feats.append(cave_cone)
    # chapel: ONE composition on the flattened summit, door toward the town; drop the old bell tower + pews
    ch = bycell[(1, 9)]
    ch["landmark"] = {"mason_type": "chapel", "pos": [-4.0, -2.0], "rot": 0, "footprint": specs["chapel"]["footprint"]}
    for k in ((0, 9), (1, 9), (1, 10), (2, 9), (0, 10), (2, 10)):
        cc = bycell[k]
        cc["props"] = [p for p in cc.get("props", []) if not (p.get("mason_type") == "bell_tower" or len(p.get("pos", [])) == 3 or p.get("furn"))]

    # TERRAIN RE-CLASSIFICATION with the engine's real cell centres (gx*16+8): fix biome tags that
    # contradict the ground, and drop sealed buildings that ended up on steep ground or in the sea.
    LAND = {"shore", "cliff", "quay", "town", "garden", "field", "farm", "wood", "copse", "heath", "moor_rock", "marsh", "road_verge", "headland", "inlet"}
    retag = collections.Counter(); dropped_b = []
    for c in cells:
        cx, cz = c["cell"][0] * 16 + 8, c["cell"][1] * 16 + 8
        hs = [terrain_h2(cx + dx, cz + dz, basins) for dx in (-7, -3.5, 0, 3.5, 7) for dz in (-7, -3.5, 0, 3.5, 7)]
        mn, mx = min(hs), max(hs)
        b = c.get("biome", "field")
        if mx < 0.3 and b != "sea":
            c["biome"] = "sea"; retag[f"{b}->sea"] += 1
        elif mn < 0.3 and mx >= 0.3 and b == "sea":
            c["biome"] = "shore"; retag["sea->shore"] += 1
        elif mx - mn > 8 and b in ("field", "heath", "moor_rock", "farm", "wood", "copse", "garden", "road_verge", "town") and not c.get("roads"):
            c["biome"] = "cliff"; retag[f"{b}->cliff"] += 1
        # buildings on bad ground
        keep = []
        for p in c.get("props", []):
            if p.get("mason_type") and p["mason_type"] in specs and not specs[p["mason_type"]].get("interior"):
                fw, fd = specs[p["mason_type"]]["footprint"]
                bmn, bmx = footprint_heights(cx + p["pos"][0], cz + p["pos"][-1], fw, fd, float(p.get("rot", 0)), basins)
                if bmn < 0.5 or bmx - bmn > 3.6:
                    dropped_b.append((p["mason_type"], tuple(c["cell"]), round(bmx - bmn, 1), round(bmn, 1))); continue
            keep.append(p)
        c["props"] = keep
    print("retag:", dict(retag)); print("dropped buildings on bad ground:", dropped_b)
    # fish market: the quay banks fall ~4 m across a 12 m hall (terrain would cut through the floor) -> market house in town
    for c in cells:
        c["props"] = [p for p in c.get("props", []) if p.get("mason_type") != "fish_market"]
    town_cells = [tuple(c["cell"]) for c in cells if c.get("biome") == "town"]
    town_cells.sort(key=lambda k: (abs(k[0] - 1) + abs(k[1] - 6)))
    town_cells = [k for k in town_cells if abs(k[0] - 1) + abs(k[1] - 6) <= 5] + [k for k in town_cells if abs(k[0] - 1) + abs(k[1] - 6) > 5]
    slot = find_slot(w, "fish_market", specs["fish_market"], town_cells, basins)
    if slot:
        _, key, lpos, rot = slot
        bycell[key].setdefault("props", []).append({"mason_type": "fish_market", "pos": lpos, "rot": rot, "footprint": specs["fish_market"]["footprint"]})
        print("fish_market ->", key, lpos, rot)
    else:
        print("WARN no slot for fish_market")

    # SPAWN FRAMING: the follow-cam sits ~8.5 m behind the player on +Z and the walk-out is -Z.
    # Keep a 6 m wide lane from z 10 to z 38 around the start (24,24) free of clutter, and move the
    # lifeboat house off the camera's shoulder (its wall stood 3 m behind the lens).
    for c in cells:
        cx, cz = c["cell"][0] * 16 + 8, c["cell"][1] * 16 + 8
        keep = []
        for p in c.get("props", []):
            if p.get("mason_type") or len(p.get("pos", [])) == 3:
                keep.append(p); continue
            px, pz = cx + float(p["pos"][0]), cz + float(p["pos"][-1])
            if abs(px - 24.0) < 4.5 and 9.0 < pz < 39.0:
                continue
            if math.hypot(px - 24.0, pz - 32.5) < 6.5:
                continue
            keep.append(p)
        c["props"] = keep
    for p in bycell[(1, 2)].get("props", []):
        if p.get("mason_type") == "lifeboat_house":
            p["pos"] = [2.8, 5.8]
    # the new shed_b in (2,1) stood on the truck's parking spot
    bycell[(2, 1)]["props"] = [p for p in bycell[(2, 1)].get("props", []) if p.get("mason_type") != "shed_b"]

    # OPENING FRAME: spawn on the quay axis looking down the harbour with the truck 8 m ahead
    # (the cell-centre spawn stared at the office's back wall). Clear the lane and the camera's shoulder.
    w["quay_spawn"] = [39.5, 36.0]
    for m in w["director"].get("modes", []):
        m["spawn"] = "quay_spawn"
    c22 = bycell[(2, 2)]
    if c22.get("landmark") and c22["landmark"].get("mason_type") == "shed_a":
        c22["landmark"]["pos"] = [7.0, 7.0]
    c22["props"] = [p for p in c22.get("props", []) if not ((p.get("url", "").endswith("MS_Pallet.glb") and abs(p["pos"][0] + 0.95) < 0.1) or (p.get("url", "").endswith("net_pile.glb") and abs(p["pos"][0] - 3.26) < 0.1))]
    for c in cells:
        cx, cz = c["cell"][0] * 16 + 8, c["cell"][1] * 16 + 8
        keep = []
        for p in c.get("props", []):
            if p.get("mason_type") or len(p.get("pos", [])) == 3:
                keep.append(p); continue
            px, pz = cx + float(p["pos"][0]), cz + float(p["pos"][-1])
            if abs(px - 39.5) < 3.5 and 22.0 < pz < 40.0 and not p.get("sit"):
                continue
            if math.hypot(px - 39.5, pz - 44.5) < 5.0:
                continue
            keep.append(p)
        c["props"] = keep

    print("dropped clutter under buildings:", drop_props_under_buildings(w))
    road_drop = 0
    for c in cells:
        if not c.get("roads"): continue
        keep = []
        for p in c.get("props", []):
            if p.get("footprint") or len(p.get("pos", [])) == 3 or p.get("furn"):
                keep.append(p); continue
            x, z = float(p["pos"][0]), float(p["pos"][-1]); hit = False
            for r in c["roads"]:
                hw = float(r.get("width", 6)) / 2 + 1.2
                if r.get("dir") in ("ns", "x") and abs(x) <= hw: hit = True
                if r.get("dir") in ("ew", "x") and abs(z) <= hw: hit = True
            if hit: road_drop += 1; continue
            keep.append(p)
        c["props"] = keep
    print("clutter dropped off road strips:", road_drop)
    # enterable slope report: door approach vs the highest terrain under the footprint
    for r in all_building_rects(w):
        mt = r[5]
        if mt not in specs or not way_in(specs[mt]) or specs[mt].get("interior") is None:
            continue
        wi = way_in(specs[mt])
        ah = door_approach_h(r[0], r[1], r[2], r[3], r[4], wi.get("face", "s"), float(wi.get("centre", 0)), basins)
        mn, mx = footprint_heights(r[0], r[1], r[2], r[3], r[4], basins)
        flag = "  <-- terrain above floor" if mx - ah > 0.6 else ""
        print(f"ENTERABLE {mt:15s} cell {r[6]} approach {ah:6.2f} footprint {mn:6.2f}..{mx:6.2f} plinth {ah-mn:5.2f}{flag}")

    # DOOR APRONS: three enterables stand on ~24-degree banks with their doors uphill (the only
    # orientation whose floor stays above the terrain). The engine grounds the floor at the wall line,
    # so the ground 1.8 m out is ~0.8 m higher than the threshold — more than a step. A shallow
    # basin centred just outside each door levels a small apron (a cut yard) so the doorstep reads
    # as a step, not a bank.
    def door_samples(r, wi, bas):
        face = wi.get("face", "s"); cen = float(wi.get("centre", 0)); fw, fd, rot = r[2], r[3], r[4]
        out = []
        for o in (0.0, 0.6, 1.2, 1.8):
            if face == "s": lx, lz = cen, -fd / 2 - o
            elif face == "n": lx, lz = cen, fd / 2 + o
            elif face == "e": lx, lz = fw / 2 + o, cen
            else: lx, lz = -fw / 2 - o, cen
            ox, oz = rot_local(lx, lz, rot); out.append((o, r[0] + ox, r[1] + oz))
        return out
    for r in all_building_rects(w):
        mt = r[5]
        if mt not in specs or not way_in(specs[mt]) or specs[mt].get("interior") is None:
            continue
        wi = way_in(specs[mt]); fz = float(specs[mt]["interior"].get("floor_z", 0.2))
        pts = door_samples(r, wi, basins)
        def worst_rise(bas):
            hs = [terrain_h2(x, z, bas) for _o, x, z in pts]
            g0 = min(hs)
            return max((g0 + fz - hh for hh in hs), key=abs)
        wr = worst_rise(basins)
        if abs(wr) <= 0.34:
            continue
        # basin centre 4.5 m outboard along the door normal
        _o, x0_, z0_ = pts[0]; _o3, x3_, z3_ = pts[3]
        nx_, nz_ = (x3_ - x0_) / 1.8, (z3_ - z0_) / 1.8
        placed = False
        best_c = None
        for R in (7.0, 9.0, 11.0):
            for D10 in range(4, 42, 2):
                cand_b = {"type": "basin", "pos": [round(x0_ + nx_ * (R * 0.64), 2), round(z0_ + nz_ * (R * 0.64), 2)], "radius": R, "depth": D10 / 10}
                wr2 = abs(worst_rise(basins + [cand_b]))
                if best_c is None or wr2 < best_c[0]:
                    best_c = (wr2, cand_b)
                if wr2 <= 0.18:
                    break
            if best_c and best_c[0] <= 0.18:
                break
        if best_c and best_c[0] <= 0.3:
            basins.append(best_c[1]); feats.append(best_c[1]); placed = True
            print(f"APRON {mt}: basin r{best_c[1]['radius']} depth {best_c[1]['depth']} at {best_c[1]['pos']} -> worst rise {best_c[0]:.2f} (was {wr:.2f})")
        if not placed:
            print(f"WARN no apron fits {mt} (worst {wr:.2f})")
    dressing = json.load(open(DRESS)) if os.path.exists(DRESS) else None


    # The Dressing pass authored the chapel against its earlier placement (cell (1,9) local [4,6]);
    # the chapel now sits on the summit at local [-4,-2] -> shift its dressing by (-8,-8) and re-bin.
    if False and dressing and "cells" in dressing:
        moved = []
        for dc in dressing["cells"]:
            if list(dc["cell"]) in ([1, 9], [1, 10]):
                ccx, ccz = dc["cell"][0] * 16 + 8, dc["cell"][1] * 16 + 8
                for p in dc.get("props", []):
                    wx, wz = ccx + p["pos"][0] - 8.0, ccz + p["pos"][-1] - 8.0
                    gx, gz = int(math.floor(wx / 16)), int(math.floor(wz / 16))
                    np_ = dict(p); lp = [round(wx - gx * 16 - 8, 3)] + ([p["pos"][1]] if len(p["pos"]) == 3 else []) + [round(wz - gz * 16 - 8, 3)]
                    np_["pos"] = lp; moved.append(((gx, gz), np_))
                if "npc" in dc:
                    n = dc["npc"]; wx, wz = ccx + n["pos"][0] - 8.0, ccz + n["pos"][-1] - 8.0
                    gx, gz = int(math.floor(wx / 16)), int(math.floor(wz / 16))
                    n = dict(n); n["pos"] = [round(wx - gx * 16 - 8, 3)] + ([n["pos"][1]] if len(n["pos"]) == 3 else []) + [round(wz - gz * 16 - 8, 3)]
                    moved.append(((gx, gz), {"__npc": n}))
                dc["props"] = []; dc.pop("npc", None)
        for key, item in moved:
            tgt = next((dc for dc in dressing["cells"] if tuple(dc["cell"]) == key), None)
            if tgt is None:
                tgt = {"cell": list(key), "props": []}; dressing["cells"].append(tgt)
            if "__npc" in item:
                tgt["npc"] = item["__npc"]
            else:
                tgt.setdefault("props", []).append(item)
        print("chapel dressing re-binned:", collections.Counter(k for k, _ in moved))
    if dressing and "cells" in dressing:
        for dc in dressing["cells"]:
            if list(dc["cell"]) == [2, 2]:
                for p in dc.get("props", []):
                    if abs(p["pos"][0] - 0.06) < 0.05 and abs(p["pos"][-1] + 3.06) < 0.05:
                        p["pos"] = [6.0, -2.5]
                if "npc" in dc and dc["npc"].get("id") == "deckhand":
                    dc["npc"]["pos"] = [6.0, -2.5]
    MH = "props/mod_house/"
    dai_npc = None; verger_npc = None
    if dressing and "cells" in dressing:
        for dc in dressing["cells"]:
            if dc.get("npc", {}).get("id") == "regular": dai_npc = dict(dc["npc"]); dai_npc["pos"] = [-0.5, -3.8]
            if dc.get("npc", {}).get("id") == "verger": verger_npc = dict(dc["npc"])

    if dressing and "cells" in dressing:
        for dc in dressing["cells"]:
            key = tuple(dc["cell"])
            if key == (-2, 5):
                # Dai and his stool move into the pub's own cell (cross-cell dressing lands on terrain, engine floor registry)
                dc["props"] = [p for p in dc.get("props", []) if not p["url"].endswith("bar_stool.glb")]
                dc.pop("npc", None)
            if key == (-1, 5):
                dc["props"] = [p for p in dc.get("props", []) if not p["url"].endswith("bar_stool.glb")]
                for p in dc["props"]:
                    if p.get("group") == "pub_t1":
                        p["pos"][-1] = round(p["pos"][-1] + 0.5, 2)
                        # the chair on the bar side of table 1 sat in the only band the player can talk
                        # to Morwenna from (counter front .. USE range); seat it on the wall side instead
                        if p["url"].endswith("pub_chair.glb") and p.get("rot") == 0:
                            p["pos"] = [-7.7, 7.5]; p["rot"] = 90
                if "npc" in dc and dc["npc"].get("id") == "barmaid":
                    dc["npc"]["pos"] = [-6.9, 2.45]
            if key == (-1, 6):
                # Dai on the bench outside the pub door (its own cell, on terrain: no cross-cell floor lottery)
                dc["props"] = [p for p in dc.get("props", []) if not p["url"].endswith("bar_stool.glb")]
                dc["props"].append({"url": meshy("harbour_bench"), "pos": [-0.5, -3.8], "rot": 0, "sit": True, "furn": True})
                dc["npc"] = dai_npc
            if key in ((0, 1), (1, 1), (0, 0), (1, 0)):
                # the net shed shrank 18 -> 15.8 m: the two props that stood at its gable ends now sit in the wall
                dc["props"] = [p for p in dc.get("props", []) if not (p.get("furn") and (p["url"].endswith("buoy_cluster.glb") or p["url"].endswith("oil_drums_rusty.glb")) and key in ((0, 1), (1, 1), (0, 0), (1, 0)) and (abs(p["pos"][0]) > 4.5 or abs(p["pos"][-1]) > 6.0))]
            if key == (0, 1) and "npc" in dc and dc["npc"].get("id") == "netman":
                dc["npc"]["pos"] = [-6.3, -1.4]
                for p in dc.get("props", []):
                    if p["url"].endswith("net_pile.glb") and abs(p["pos"][0] + 4.3) < 0.2:
                        p["pos"] = [-7.0, -3.4]
            if key in ((1, 9), (1, 10)):
                dc["props"] = []; dc.pop("npc", None)
        # chapel: 15.9 m composition centred at world (20,150): nave z 146.3..154.8, chancel 153.65..157.95
        c19 = next(dc for dc in dressing["cells"] if tuple(dc["cell"]) == (1, 9))
        pews = []
        for i, wz in enumerate((148.4, 150.4, 152.4)):
            for wx in (18.1, 21.9):
                pews.append({"url": meshy("chapel_pew"), "pos": [round(wx - 24, 2), round(wz - 152, 2)], "rot": 0, "sit": True, "group": "pews", "furn": True})
        c19["props"] = pews + [
            {"url": meshy("chapel_lectern"), "pos": [17.6 - 24, 153.9 - 152], "rot": 180, "furn": True},
            {"url": meshy("chapel_altar"), "pos": [20.0 - 24, 156.6 - 152], "rot": 180, "group": "altar", "furn": True},
            {"url": MH + "Prop_Misc_Lamp.glb", "pos": [19.4 - 24, 1.05, 156.6 - 152], "scale": 0.6, "collider": False, "group": "altar", "furn": True},
            {"url": MH + "Prop_Misc_Lamp.glb", "pos": [20.6 - 24, 1.05, 156.6 - 152], "scale": 0.6, "collider": False, "group": "altar", "furn": True},
        ]
        c19["npc"] = dict(verger_npc, pos=[23.0 - 24, 147.6 - 152], activity="idle")
    stats = collections.Counter()
    for c in cells:
        key = tuple(c["cell"])
        rng = random.Random(key[0] * 7919 + key[1] * 104729 + 17)
        biome = c.get("biome", "field")
        # 2. drop hand-authored underpins (engine plinth replaces them)
        c["rows"] = [r for r in c.get("rows", []) if not (r.get("underpin") or r.get("furn"))]
        if not c["rows"]:
            c.pop("rows", None)
        # 3. resolve buildings (mason_type -> compiled record)
        if c.get("landmark") and c["landmark"].get("mason_type"):
            l = c["landmark"]
            mt = l["mason_type"]
            if mt in recs:
                c["landmark"] = building_record(mt, specs, recs, l["pos"], l.get("rot", 0))
                stats["landmark"] += 1
            else:
                print("WARN landmark type not compiled:", mt, key)
        newprops = []
        for p in c.get("props", []):
            if isinstance(p, dict) and p.get("mason_type"):
                mt = p["mason_type"]
                if mt not in recs:
                    print("WARN prop building type not compiled:", mt, key); continue
                newprops.append(building_record(mt, specs, recs, p["pos"], p.get("rot", 0)))
                stats["building"] += 1
            else:
                newprops.append(p)
        c["props"] = newprops
        # 4. dressing merge: replace interior furniture + npc for dressed cells
        if dressing and "cells" in dressing:
            dk = json.dumps(list(key))
            for dc in dressing["cells"]:
                if list(dc["cell"]) == list(key):
                    c["props"] = [p for p in c["props"] if not (p.get("furn") or p.get("dressing") or len(p.get("pos", [])) == 3)]
                    for p in dc.get("props", []):
                        p = dict(p); p["dressing"] = True
                        c["props"].append(p)
                    if "npc" in dc:
                        c["npc"] = dict(dc["npc"]); c["npc"]["_dressed"] = True
                    if "npcs" in dc:
                        c["npcs"] = dc["npcs"]
                    stats["dressed"] += 1
        # 5. ground
        c["ground"] = biome_ground(biome)
        # 6. vegetation
        rects, roads, pts = blockers(c)
        has_build = bool(rects)
        has_enterable = any(isinstance(x, dict) and x.get("interior") for x in ([c.get("landmark")] if c.get("landmark") else []) + c["props"])
        light = has_build or bool(roads)
        if biome == "sea":
            c.pop("scatter", None)
        elif has_enterable and biome in ("town", "quay", "farm"):
            c.pop("scatter", None)
        else:
            sc = biome_scatter(biome, V, light)
            if has_enterable:
                sc = [e for e in sc if e["url"] in (GRASS_S,)]
            if sc:
                c["scatter"] = sc
            else:
                c.pop("scatter", None)
        # tree props
        trees = biome_trees(biome, V)
        if trees and biome != "sea":
            want = {"wood": 6, "copse": 3, "garden": 1, "field": 2, "road_verge": 2, "heath": 2, "marsh": 2,
                    "moor_rock": 3, "cliff": 2, "shore": 1, "headland": 2, "inlet": 1}.get(biome, 0)
            if biome in ("field", "heath") and rng.random() < 0.3:
                want -= 1
            room = 20 - len(c["props"]) - (6 if has_enterable else 0)
            want = max(0, min(want, room))
            placed = 0
            tries = 0
            pool = [t for t in trees for _ in range(t[3])]
            while placed < want and tries < 60:
                tries += 1
                x = rng.uniform(-6.5, 6.5); z = rng.uniform(-6.5, 6.5)
                if not spot_free(x, z, rects, roads, pts, bmargin=3.0, rmargin=2.5, pmargin=3.0):
                    continue
                url, scl, col, _wgt = rng.choice(pool)
                p = {"url": url, "pos": [round(x, 2), round(z, 2)], "rot": rng.randrange(0, 360), "collider": col}
                if abs(scl - 1.0) > 0.01:
                    p["scale"] = round(scl * rng.uniform(0.9, 1.1), 2)
                c["props"].append(p); pts.append((x, z)); placed += 1
                stats["tree_props"] += 1
        if not c["props"]:
            c.pop("props", None)
        stats[f"biome:{biome}"] += 1

    # dressing may have MOVED an NPC into another cell: drop the stale copy
    seen_npc = {}
    for c in cells:
        if isinstance(c.get("npc"), dict):
            seen_npc.setdefault(c["npc"].get("id"), []).append(c)
    for nid, lst in seen_npc.items():
        if len(lst) > 1:
            keepers = [c for c in lst if c["npc"].get("_dressed")] or lst[-1:]
            for c in lst:
                if c is not keepers[0]:
                    c.pop("npc", None); print("dropped stale npc", nid, c["cell"])
    for c in cells:
        if isinstance(c.get("npc"), dict):
            c["npc"].pop("_dressed", None)

    # COLLIDING UNDERPIN under every building that stands on a slope. The engine's plinth is a
    # visual skirt with NO collider (and its door slot runs the full depth), so on a bank the player
    # can walk under the raised floor. A slightly smaller box with a collider fills the same volume:
    # base on the terrain at the building centre, top at the building's grounded base.
    under_n = 0
    for c in cells:
        cx, cz = c["cell"][0] * 16 + 8, c["cell"][1] * 16 + 8
        for b in ([c["landmark"]] if c.get("landmark") else []) + [p for p in c.get("props", []) if isinstance(p, dict) and p.get("footprint")]:
            mt = b.get("mason_type")
            if mt not in specs:
                continue
            fw, fd = float(b["footprint"][0]), float(b["footprint"][1]); rot = float(b.get("rot", 0))
            wx, wz = cx + float(b["pos"][0]), cz + float(b["pos"][-1])
            wi = way_in(specs[mt]) if specs[mt].get("interior") else None
            if wi:
                base = door_approach_h(wx, wz, fw, fd, rot, wi.get("face", "s"), float(wi.get("centre", 0)), basins)
            else:
                base = terrain_h2(wx, wz, basins)
            mn, mx = footprint_heights(wx, wz, fw, fd, rot, basins)
            gc = terrain_h2(wx, wz, basins)
            h = base - gc - 0.05
            if base - mn <= 0.3 or (h <= 0.15 and gc - mn <= 0.5):
                continue
            parts0 = (specs[mt].get("parts") or [{}])[0]
            is_round = str(specs[mt].get("plan", parts0.get("plan", {})).get("shape", "")) == "round"
            if is_round or gc - mn <= 0.5:
                part = ({"shape": "cylinder", "radius": round(min(fw, fd) / 2 - 0.06, 2), "height": round(h, 2), "sides": 24}
                        if is_round else {"shape": "box", "size": [round(fw - 0.12, 2), round(h, 2), round(fd - 0.12, 2)]})
                part.update({"material": b.get("material", "stone"), "rot": rot, "collider": "mesh" if is_round else "box"})
                c.setdefault("rows", []).append({"part": part,
                    "from": [round(float(b["pos"][0]), 2), round(float(b["pos"][-1]), 2)], "to": [round(float(b["pos"][0]), 2), round(float(b["pos"][-1]), 2)],
                    "spacing": 50, "collider_underpin": True})
                under_n += 1
                continue
            # the ground falls away under one end: a single box grounded at the centre leaves a gap under
            # the low side, so fill each quadrant from its own ground level up to the same base
            for qx in (-fw / 4, fw / 4):
                for qz in (-fd / 4, fd / 4):
                    ox, oz = rot_local(qx, qz, rot)
                    qh = base - terrain_h2(wx + ox, wz + oz, basins) - 0.05
                    if qh <= 0.15:
                        continue
                    part = {"shape": "box", "size": [round(fw / 2 - 0.06, 2), round(qh, 2), round(fd / 2 - 0.06, 2)],
                            "material": b.get("material", "stone"), "rot": rot, "collider": "box"}
                    # rows are clamped to their own cell: file the box under the cell the point is in
                    qwx, qwz = wx + ox, wz + oz
                    host = bycell.get((math.floor(qwx / 16), math.floor(qwz / 16)), c)
                    hcx, hcz = host["cell"][0] * 16 + 8, host["cell"][1] * 16 + 8
                    at = [round(qwx - hcx, 2), round(qwz - hcz, 2)]
                    host.setdefault("rows", []).append({"part": part, "from": at, "to": at, "spacing": 50, "collider_underpin": True})
            under_n += 1
    print("colliding underpins:", under_n)

    # NO VOSTOK: every props/vostok_extra/*.glb ships with its textures stripped (glTF default
    # 0.8 grey, no image) and the engine's on-load repair never fires (the importer converts that
    # 0.8 linear to 0.906 sRGB, so the fingerprint test misses) -> white plastic. Swap every use for
    # a coloured/textured asset or drop it.
    MV = "props/mod_village/"; MH = "props/mod_house/"; KN = "props/kenney_nature/"
    SUB = {
        "MS_Crate.glb": {"url": MV + "Prop_Crate_1.glb", "scale": 0.85},
        "MS_Plank_Pile.glb": {"url": KN + "Timber_Stack_1.glb", "scale": 1.4},
        "MS_Cable_Reel.glb": {"url": meshy("rope_coil_large")},
        "MS_Firewood_A.glb": {"url": KN + "Timber_Stack_1.glb"}, "MS_Firewood_B.glb": {"url": KN + "Timber_Stack_1.glb"},
        "MS_Firewood_C.glb": {"url": KN + "Log_2.glb"}, "MS_Firewood_D.glb": {"url": KN + "Log_2.glb"},
        "MS_Sawbuck.glb": {"url": KN + "Log_2.glb", "scale": 1.3},
        "MS_Planter_Box.glb": {"url": MV + "Prop_Barrel_1.glb", "scale": 1.3},
        "MS_Composter.glb": {"url": MV + "Prop_Barrel_1.glb", "scale": 1.5},
        "MS_Tent_Civilian.glb": {"url": KN + "Tent_Leanto_2.glb", "scale": 0.65},
        "MS_Campfire.glb": {"url": KN + "Campfire_Teepee.glb", "scale": 1.2},
        "MS_Fireplace_Tower.glb": {"url": MH + "Prop_Fireplace.glb", "scale": 0.7},
        "MS_Candle.glb": {"url": MH + "Prop_Misc_Lamp.glb", "scale": 0.6},
        "MS_Carpet.glb": {"url": MH + "Prop_Misc_Rug_Rectangle.glb"},
        "MS_Cabinet_Basic.glb": {"url": MH + "Prop_Bedroom_Dresser_Single.glb", "scale": 0.8},
        "MS_Pole_Light_Rural.glb": {"url": meshy("lamp_post_harbour")},
        "MS_Chair_Sun.glb": {"url": meshy("pub_chair")},
        "MS_Table_Cabin.glb": {"url": meshy("kitchen_table_set")},
    }
    DROP = {"MS_Pallet.glb", "MS_Barrier_Road.glb", "MS_Board_Message.glb", "MS_Mailbox.glb", "MS_Trash.glb", "MS_Brick_Pile.glb",
            "MS_Sign_Public_Road_Ends.glb", "MS_Dartboard.glb", "MS_Mattress_Soft.glb", "MS_Mattress_Hard.glb", "MS_Fence_Wood_Pole.glb",
            "MS_Retro_Radio.glb", "MS_Sofa.glb", "MS_Fridge.glb", "MS_Bus_Stop_Rural.glb", "MS_Totem_Welcome.glb", "MS_Sign_Billboard.glb"}
    sub_n = collections.Counter()
    for c in cells:
        keep = []
        for p in c.get("props", []):
            u = str(p.get("url", ""))
            if "vostok" in u:
                fn = u.split("/")[-1]
                if fn in DROP:
                    sub_n["drop:" + fn] += 1; continue
                if fn in SUB:
                    p = dict(p); p["url"] = SUB[fn]["url"]
                    if "scale" in SUB[fn]:
                        p["scale"] = round(float(p.get("scale", 1.0)) * SUB[fn]["scale"], 2)
                    sub_n["sub:" + fn] += 1
                else:
                    sub_n["drop?:" + fn] += 1; continue
            keep.append(p)
        c["props"] = keep
        rows = []
        for r in c.get("rows", []) + [dict(x, _ring=True) for x in c.get("rings", [])]:
            pt = r.get("part", {}); u = str(pt.get("url", ""))
            if "vostok" in u:
                fn = u.split("/")[-1]
                if fn == "MS_Fence_Wood.glb":
                    npart = {"shape": "box", "size": [1.9, 1.0, 0.08], "material": "timber", "collider": "box"}
                    if "rot" in pt: npart["rot"] = pt["rot"]
                    r = dict(r); r["part"] = npart; sub_n["fence->box"] += 1
                elif fn in SUB:
                    npart = dict(pt); npart["url"] = SUB[fn]["url"]
                    if "scale" in SUB[fn]: npart["scale"] = round(float(pt.get("scale", 1.0)) * SUB[fn]["scale"], 2)
                    r = dict(r); r["part"] = npart; sub_n["rowsub:" + fn] += 1
                else:
                    sub_n["rowdrop:" + fn] += 1; continue
            rows.append(r)
        c["rows"] = [r for r in rows if not r.get("_ring")]
        c["rings"] = [dict((k, v) for k, v in r.items() if k != "_ring") for r in rows if r.get("_ring")]
        if not c["rings"]: c.pop("rings", None)
        if not c["rows"]: c.pop("rows", None)
    print("vostok purge:", dict(sub_n))
    left = sum(1 for c in cells for p in c.get("props", []) if "vostok" in str(p.get("url", ""))) + sum(1 for c in cells for r in c.get("rows", []) if "vostok" in json.dumps(r))
    print("vostok refs left:", left)
    # TRUCK CORRIDOR: keep the quay axis from the truck to the switchback foot clear of clutter (±5 m).
    for c in cells:
        cx, cz = c["cell"][0] * 16 + 8, c["cell"][1] * 16 + 8
        keep = []
        for p in c.get("props", []):
            if p.get("mason_type") or len(p.get("pos", [])) == 3 or p.get("furn"):
                keep.append(p); continue
            px, pz = cx + float(p["pos"][0]), cz + float(p["pos"][-1])
            t = (px + pz) / math.sqrt(2); d = (px - pz) / math.sqrt(2)
            if 38.0 <= t <= 84.0 and abs(d) <= 5.0:
                continue
            keep.append(p)
        c["props"] = keep
    # 7. the cove: boss inside the cave, <=6 live, checkpoint + respawn rule
    cave = bycell[(10, -4)]
    # the arch (mouth s face, mouth centre x -2.0) must have a clear approach; nothing from the
    # neighbouring cells may stand inside the cave's rotated footprint (it spans into (9,-4))
    cwx, cwz = 168 - 6.29, -56 - 5.88
    ax_, az_ = rot_local(-2.0, -5.65, 19.4); arch_w = (cwx + ax_, cwz + az_)
    nx_, nz_ = rot_local(0.0, -1.0, 19.4)
    for c in cells:
        if abs(c["cell"][0] - 10) > 1 or abs(c["cell"][1] + 4) > 2: continue
        cx, cz = c["cell"][0] * 16 + 8, c["cell"][1] * 16 + 8
        keep = []
        for p in c.get("props", []):
            if p.get("footprint"):
                keep.append(p); continue
            px, pz = cx + float(p["pos"][0]), cz + float(p["pos"][-1])
            if in_rot_rect(px, pz, cwx, cwz, 15.8, 11.3, 19.4, 2.0 if p.get("furn") else 1.5):
                continue   # the cave is re-dressed below; the (10,-5) crate/drums stood in its east wall
            if p.get("furn"):
                keep.append(p); continue
            dx, dz = px - arch_w[0], pz - arch_w[1]
            along = dx * nx_ + dz * nz_; across = abs(-dx * nz_ + dz * nx_)
            if -1.0 < along < 9.0 and across < 4.0:
                continue
            keep.append(p)
        c["props"] = keep
        c["scatter"] = [e for e in c.get("scatter", []) if "Rock" not in e["url"]]
    # den dressing in cave-local metres (engine frame: the arch is on the -z face at x -2; chambers
    # mouth (-2,-2) 3.8x2.8, main (2.7,0.4) 4.5x3.3, back (-3.9,2.9) 3.3x2.2). The cave straddles three
    # cells and a cross-cell prop only finds the floor if this cell built first, so everything stays
    # inside (10,-4): the main chamber's north two-thirds + the mouth's north-east. Chest >= 2 m off a
    # wall (USE range 2.9, no line-of-sight test in the engine) and off the mouth->main line.
    def cave_local(sx, sz):
        ox, oz = rot_local(sx, sz, 19.4)
        cl = [round(-6.29 + ox, 3), round(-5.88 + oz, 3)]
        assert -7.7 <= cl[0] <= 7.7 and -7.7 <= cl[1] <= 7.7, ("cave prop outside its cell", sx, sz, cl)
        return cl
    cave["props"] = [p for p in cave.get("props", []) if not p.get("furn")] + [
        {"url": meshy("oil_drums_rusty"), "pos": cave_local(-1.0, 0.0), "rot": 19.4, "furn": True},
        {"url": KN + "Campfire_Teepee.glb", "pos": cave_local(4.8, 2.2), "rot": 19.4, "furn": True},
        {"url": MV + "Prop_Crate_1.glb", "pos": cave_local(5.8, 0.8), "rot": 109.4, "furn": True},
        {"url": KN + "Tent_Leanto_2.glb", "pos": cave_local(1.0, 2.6), "rot": 199.4, "scale": 0.65, "furn": True},
    ]
    cave.pop("enemies", None); cave.pop("enemy_type", None); cave.pop("enemy_model", None)
    cave.pop("enemy_hp", None); cave.pop("enemy_damage", None)
    cave["boss"] = {"id": "ringleader", "type": "ringleader", "model": meshy("smuggler_melee"),
                    "pos": cave_local(4.8, 0.2), "hp": 150, "damage": 12, "range": 2.2, "height": 1.85}
    # contraband in the main chamber, 2.1 m off the nearest wall: not openable from outside
    cave["chest"] = {"pos": cave_local(2.4, 1.6), "contents": ["contraband"], "gold": 200}
    for k, n, dmg in (((9, -6), 2, 8), ((9, -5), 2, 5), ((10, -5), 1, 5)):
        bycell[k]["enemies"] = n
        bycell[k]["enemy_damage"] = dmg
    bycell[(9, -5)]["enemy_range"] = 9; bycell[(10, -5)]["enemy_range"] = 9
    # a second, closer checkpoint region at the cove head + potion stash by the wreck
    regs = w["regions"]
    if not any(r["name"] == "The Cove Path" for r in regs):
        regs.append({"name": "The Cove Path", "center": [160, -20], "radius": 22, "ambient": "wind"})
    rules = w["rules"]
    rids = {r["id"] for r in rules}
    if "r_cove_path" not in rids:
        rules.append({"id": "r_cove_path", "when": {"event": "enter_region", "target": "The Cove Path"},
                      "then": [{"set_spawn": [160, 0, -22]}, {"hud_show": "smugglers_down"},
                               {"subtitle": {"text": "The path down to the inlet. Voices from the wreck - not fishermen.", "hold": 6}}],
                      "once": True})
    if "r_died" not in rids:
        rules.append({"id": "r_died", "when": {"event": "player_died"},
                      "then": [{"respawn": True}, {"toast": "You come round on the shingle. Try again."}, {"sound": "hurt"}]})
    for r in rules:
        if r["id"] == "r_cove_spawn":
            r["then"] = [{"hud_show": "smugglers_down"}]

    # Game-Feel mitigations (data levers only): the single-slot toast is clobbered by the region toast,
    # so drop the redundant chain toast (the quest label carries it); keep subtitles to one short line
    # because the engine lays the subtitle slot over the thumb buttons.
    for m in w["director"].get("modes", []):
        for st in m.get("chain", []):
            if st.get("id") == "settle_in":
                st.pop("toast", None)
    for r in w["rules"]:
        if r["id"] == "r_start":
            r["then"][0] = {"subtitle": {"text": "Rain again. The blue truck is on the quay.", "hold": 6}}
        if r["id"] == "r_light":
            r["then"][0] = {"subtitle": {"text": "Kestrel Point. The stairs go all the way up.", "hold": 5}}
        if r["id"] == "r_cove_path":
            r["then"][2] = {"subtitle": {"text": "The path down to the inlet. Voices from the wreck.", "hold": 5}}
    w["vars"]["smugglers_down"]["max"] = 6
    # daylight bleach: "overcast"/"fog" push the sky and aerial haze to white on the web tier; keep the
    # grey-rainy mood with cloudy days, rain and a storm instead
    w["sky"] = {"loop": True, "cycle": [
        {"time": "day", "weather": "cloudy", "seconds": 150}, {"time": "day", "weather": "rain", "seconds": 140},
        {"time": "sunset", "weather": "storm", "seconds": 70}, {"time": "night", "weather": "rain", "seconds": 110},
        {"time": "sunrise", "weather": "cloudy", "seconds": 60}]}
    w["director"].pop("boss", None)
    w["director"].pop("victory", None)
    if "r_win" not in rids:
        rules.append({"id": "r_win", "when": {"event": "quest_done", "target": "smugglers"},
                      "then": [{"toast": "The cove is clear. Kestrel Bay is yours to wander."}, {"sound": "victory"}, {"win": True}], "once": True})
    for m in w["director"].get("modes", []):
        for st in m.get("chain", []):
            if st.get("id") == "smugglers":
                st.pop("on_done", None)

    # 8. quest text tightened
    q = json.load(open(f"{REPO}/quests.json"))
    for qq in q["quests"]:
        qq["steps"] = [st for st in qq["steps"] if st["id"] != "boss"]
        for st in qq["steps"]:
            st["desc"] = {"master": "Find Alwyn in the harbour office", "pub": "Ask Morwenna at the Kestrel Arms",
                          "reach": "Reach the wreck down the coast", "gun": "Take the shotgun from the stash",
                          "clear": "Deal with the 5 smugglers", "boss": "Take down the ringleader in the cave",
                          "loot": "Take the contraband from the cave"}.get(st["id"], st["desc"])
    json.dump(q, open(f"{REPO}/quests.json", "w"), indent=1)

    w["character_source"] = "meshy"
    w.pop("density_grandfathered", None)
    json.dump(w, open(f"{REPO}/world.json", "w"), separators=(",", ":"))
    print(dict(stats))
    print("bytes", os.path.getsize(f"{REPO}/world.json"))

if __name__ == "__main__":
    main()
