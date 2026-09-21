"""Kestrel Bay FILL / DENSIFY layout generator.
Reads /workspace/repo/world.json (+ cellmap.json, heights.csv) and writes /workspace/world.json.
"""
import sys, json, math, copy, collections
sys.path.insert(0, '/workspace')
from genlib import *
from genlib import _pt_poly_dist

W = World()
cells = W.cells
LOG = W.log
GRID_X = range(-11, 21)
GRID_Z = range(-13, 19)

# =====================================================================================
# 0. Row cleanup: drop underpin plinths + the mechanical cell-edge pattern walls
# =====================================================================================
KEEP_PATTERN = {(1, 8)}   # churchyard wall with its gate gap in front of the chapel
removed_underpin = removed_pattern = 0
for key, c in cells.items():
    new_rows = []
    for r in c.get('rows', []):
        p = r['part']
        if r.get('underpin'):
            removed_underpin += 1
            continue
        sz = tuple(p.get('size', []))
        if p.get('shape') == 'box' and sz in ((1.2, 0.9, 0.4), (0.4, 0.9, 1.2)) and key not in KEEP_PATTERN:
            removed_pattern += 1
            continue
        new_rows.append(r)
    c['rows'] = new_rows
print('removed underpin', removed_underpin, 'pattern walls', removed_pattern)

# =====================================================================================
# 1. BIOME ZONING
# =====================================================================================
INLET = {(9, -6), (9, -5), (10, -5), (10, -4)}
QUAY = {(0, 0), (1, 1), (2, 2), (1, 0), (0, 1), (2, 1), (1, 2), (2, 3)}
biome = {}
for key in cells:
    t = W.terrain(key)
    if key in INLET:
        biome[key] = 'inlet'
    elif key in QUAY:
        biome[key] = 'quay'
    elif t == 'sea':
        biome[key] = 'sea'
    elif t == 'shore':
        biome[key] = 'shore'
    elif t == 'steep':
        biome[key] = 'cliff'
    elif t == 'slope':
        biome[key] = 'cliff'
    else:
        biome[key] = 'heath'


def zone(tag, cells_list):
    for k in cells_list:
        k = tuple(k)
        if k in cells and biome[k] not in ('inlet', 'sea'):
            biome[k] = tag


def rect(x0, x1, z0, z1):
    return [(x, z) for x in range(x0, x1 + 1) for z in range(z0, z1 + 1)]


flat_cells = {k for k in cells if W.terrain(k) == 'flat'}
# --- cove head slopes near the smugglers' inlet: cliff already. Cove-side slope cells stay cliff.
# --- HEADLAND: flat cells touching the sea/shore/steep coast, west + south coasts
for k in list(cells):
    if biome[k] == 'heath' and W.terrain(k) in ('flat', 'slope'):
        gx, gz = k
        near_drop = any(biome.get((gx + dx, gz + dz)) in ('sea', 'shore') or W.terrain((gx + dx, gz + dz)) == 'steep'
                        for dx in (-1, 0, 1) for dz in (-1, 0, 1) if (gx + dx, gz + dz) in cells)
        if near_drop:
            biome[k] = 'headland'
# chapel hill (cone at 20,150) -> wood / copse on its flanks
zone('wood', [(0, 9), (0, 10), (0, 11), (-1, 10), (2, 9), (2, 10), (2, 11), (3, 9), (3, 10), (3, 11), (1, 11), (-1, 9)])
zone('copse', [(1, 9), (1, 10), (2, 8), (3, 8), (4, 8), (1, 12), (2, 12), (0, 12)])
# plantation belt north-east of town + along the east road
zone('wood', [(4, 9), (4, 10), (5, 9), (5, 10), (6, 9), (6, 10), (7, 9), (7, 10), (8, 10), (9, 10)])
zone('copse', [(5, 8), (6, 8), (8, 9), (9, 9), (4, 11), (5, 11), (6, 11)])
zone('wood', [(11, 10), (12, 10), (13, 10), (14, 10), (15, 10), (16, 10)])
zone('copse', [(13, 8), (14, 8), (17, 11), (18, 11), (12, 11), (11, 11), (14, 11), (15, 11)])
# fields north of town / around farms
zone('field', rect(-3, 3, 12, 13) + rect(-3, -1, 11, 11) + rect(-3, 6, 14, 17) + rect(-6, -5, 15, 18) + rect(-3, 3, 18, 18))
zone('field', rect(7, 9, 7, 8) + rect(11, 12, 7, 8) + rect(11, 12, 5, 6) + rect(7, 9, 2, 3) + rect(8, 8, 4, 4) + rect(10, 11, 1, 4) + rect(12, 15, 4, 4) + rect(12, 15, 1, 1) + rect(7, 7, -3, -2))
zone('field', rect(11, 15, 13, 13) + rect(11, 12, 15, 15) + rect(14, 15, 15, 15) + rect(17, 18, 12, 13) + rect(16, 18, 15, 16) + rect(17, 19, 8, 8) + rect(16, 20, 10, 11) + rect(17, 19, 7, 7))
# farmyards
zone('farm', [(-3, 12), (-3, 13), (3, 14), (3, 15), (13, 14), (13, 15), (12, 14), (17, 14), (17, 15), (13, 2), (13, 3), (14, 2), (14, 3), (13, 1)])
# town + gardens
TOWN = rect(-4, 9, 5, 7) + [(-4, 8), (-3, 8), (-2, 8), (0, 8), (1, 8), (10, 6), (10, 7), (10, 8), (10, 5), (11, 5), (5, 5), (6, 5), (5, 4), (6, 4), (6, 1), (6, 2), (6, 3), (6, 0), (7, 0), (8, 0), (9, 0), (10, 0),
                              (7, -1), (8, -1), (7, 1), (8, 1), (9, 1), (7, 2), (7, 4), (9, 4), (10, 4), (17, 10), (18, 10), (19, 10), (17, 8), (18, 8), (19, 8), (9, 5), (9, 3), (9, 2)]
zone('town', TOWN)
zone('garden', [(-3, 4), (-2, 4), (-1, 4), (-1, 8), (7, 8), (8, 8), (9, 8), (-5, 9), (7, 3), (8, 3), (8, 2), (10, 2), (10, 3), (-4, 9), (7, 5), (8, 5), (7, 6), (8, 6), (9, 6), (7, 7), (8, 7), (9, 7)])
zone('town', [(8, 4), (7, 5), (8, 5), (7, 6), (8, 6), (9, 6), (7, 7), (8, 7), (9, 7), (6, 6), (6, 7), (5, 7), (5, 6), (4, 7), (4, 6), (4, 5), (3, 5), (2, 5), (1, 5), (0, 5), (1, 6), (2, 6), (3, 6)])
# marsh hollows
zone('marsh', [(15, 5), (16, 5), (16, 6), (13, 16), (14, 16), (14, 17), (8, -2), (8, -3)])
# rocky moor: the far east and the south-east
zone('moor_rock', rect(17, 20, 0, 6) + rect(15, 20, -7, -1) + rect(17, 20, 17, 18) + rect(18, 20, 14, 16) + rect(19, 20, 12, 13) + rect(7, 9, 11, 13) + rect(5, 9, 15, 18) + rect(11, 12, 17, 18) + rect(15, 16, 17, 18))
zone('heath', rect(11, 16, 0, 0) + rect(16, 16, 1, 4) + rect(11, 14, 5, 6) + rect(13, 16, 7, 7) + rect(15, 16, 8, 8) + rect(11, 16, 11, 12) + rect(9, 9, 14, 18) + rect(4, 6, 12, 13))
zone('heath', rect(17, 18, 1, 2) + rect(19, 20, 4, 6) + rect(15, 16, -2, -1) + rect(17, 20, 17, 18) + rect(19, 20, 0, 1))
zone('marsh', [(18, -3), (19, -3), (18, -2)])
zone('copse', [(19, 2), (20, 2), (17, -1)])
for k in rect(15, 20, -7, -6) + rect(13, 14, -6, -6):
    if k in cells and W.terrain(k) == 'flat':
        biome[k] = 'headland'
# inlet keeps whatever it had; lighthouse cell
biome[(-9, 9)] = 'headland'
# The lone clifftop house cell (-5,9) is garden already; (-4,5) west end of town is town
biome[(-4, 5)] = 'town'
biome[(-1, -1)] = 'shore'

# =====================================================================================
# 2. ROADS / TRACKS (only on cells that have none)
# =====================================================================================
def track(spec, width=4):
    for k, d in spec:
        W.add_road(tuple(k), d, width)
        if biome[tuple(k)] in ('heath', 'moor_rock', 'field', 'copse', 'wood', 'headland', 'garden'):
            biome[tuple(k)] = 'road_verge'


# coast track: back lane (-4,8)x -> north -> west along gz=13 -> north along gx=-7 to the lookout
track([((-4, 9), 'ns'), ((-4, 10), 'ns'), ((-4, 11), 'ns'), ((-4, 12), 'ns'), ((-4, 13), 'x'), ((-5, 13), 'ew'), ((-6, 13), 'ew'), ((-7, 13), 'x'), ((-7, 14), 'ns'), ((-7, 15), 'ns')])
# farm lane north from the back lane (-2,8)x to Higher Trewint, on to Trewint Barton / the chapel hill foot
track([((-2, 9), 'ns'), ((-2, 10), 'ns'), ((-2, 11), 'ns'), ((-2, 12), 'x'), ((-2, 13), 'ns'), ((-2, 14), 'x'), ((-1, 14), 'ew'), ((0, 14), 'ew'), ((1, 14), 'ew'), ((2, 14), 'x')])
# moor lane north from the east-road junction (10,9)x to Penhale, Carn Farm and Wheal Kestrel
track([((10, 10), 'ns'), ((10, 11), 'ns'), ((10, 12), 'x'), ((11, 12), 'ew'), ((12, 12), 'ew'), ((13, 12), 'x'), ((13, 13), 'ns'), ((13, 14), 'x'), ((14, 14), 'ew'), ((15, 14), 'ew'), ((16, 14), 'ew'),
       ((10, 13), 'ns'), ((10, 14), 'ns'), ((10, 15), 'ns')])
# east lane behind the hamlet: from (6,5)x east along gz=5 then south along gx=9 and out to Polgrean + the cove head
track([((7, 5), 'ew'), ((8, 5), 'ew'), ((9, 5), 'x'), ((9, 4), 'ns'), ((9, 3), 'ns'), ((9, 2), 'x'), ((10, 2), 'ew'), ((11, 2), 'ew'), ((12, 2), 'x'), ((13, 2), 'ew'), ((14, 2), 'x'), ((14, 1), 'ns'), ((14, 0), 'x'),
       ((14, -1), 'ns'), ((14, -2), 'ns'), ((14, -3), 'x'), ((13, -3), 'ew'), ((15, -3), 'ew'), ((16, -3), 'ew'), ((14, -4), 'ns')], 4)
# hamlet road extended east to meet the Polgrean lane
track([((11, 0), 'ew'), ((12, 0), 'ew'), ((13, 0), 'ew')], 5)
# Kestrel Head footpath south from (6,0)x
track([((6, -1), 'ns'), ((6, -2), 'ns'), ((6, -3), 'ns')], 4)
# south farm-track spur from (12,2)x to the Polgrean bog fields
track([((12, 3), 'ns'), ((12, 1), 'ns')], 4)
for k in [(11, 9), (12, 9), (13, 9), (14, 9), (15, 9), (16, 9), (17, 9), (18, 9), (19, 9), (20, 9), (10, 9)]:
    if biome[k] not in ('town',):
        biome[k] = 'road_verge'
for k in [(-4, 9), (-2, 9), (-2, 10)]:
    biome[k] = 'road_verge'

# =====================================================================================
# 3. BUILDINGS
# =====================================================================================
B = []  # (type, x, z, rot, note, kwargs)


def bld(t, x, z, rot, note='', **kw):
    B.append((t, x, z, rot, note, kw))


# --- harbour (bank buildings; the canyon floor is ~17 m wide so bank plinths are unavoidable)
bld('fish_market', 34, 51, 315, 'quay head, arcade to the quay', max_fall=4.2)
bld('lifeboat_house', 14, 33, 315, 'NW bank, doors to the quay', max_fall=4.2)
bld('shed_b', 35, 17, 135, 'SE bank behind harbour office', max_fall=3.0)
bld('shed_a', 55, 39, 135, 'shed at the switchback foot', max_fall=3.0)
bld('hut_stone', 14, 0, 135, 'salt store between shed_b and office', max_fall=2.5, margin=2.4)
# --- High Street north side (front faces at z=101.5; east of x=83 set back to 103.5 behind the fence rows)
bld('house_d', -25, 105.5, 0, 'High St N')
bld('terrace', -8, 105, 0, 'High St N terrace')
bld('house_c', 9, 104.5, 0, 'High St N by chapel street')
bld('institute', 27, 106.8, 0, "Fishermen's Institute (front set back 0.7 m so the existing bench sits against its wall)")
bld('house_c', 73, 104.5, 0, 'High St N east of store')
bld('terrace', 118.5, 107, 0, 'East High St terrace')
bld('house_a', 136, 107, 0, 'East High St')
bld('house_f', 147, 107.5, 0, 'East High St brick house')
# --- High Street south side
bld('chandlery', 7.45, 86.5, 180, 'Chandlery (enterable) - 6 m clear north to the street', margin=2.9)
bld('cottage_white', 23.5, 88, 180, 'cottage by the Prospect (rim, 2.7 m fall)', max_fall=2.8)
bld('house_c', -65, 82, 180, 'west end house closing the gx=-4 vista')
bld('warehouse', 132, 72.5, 0, 'net loft / warehouse south of Back Lane East', max_fall=2.5)
bld('cottage_white', 112, 85.5, 180, 'Back Lane East / High St S')
bld('house_c', 123, 85.5, 180, 'Back Lane East / High St S')
bld('cottage_white', 134, 85.5, 180, 'Back Lane East / High St S')
# --- chapel street west side
bld('house_c', 9, 117, 270, 'chapel street')
# --- back-yard sheds behind the north side
bld('shed_a', -22, 116, 90, 'back yard shed')
bld('shed_a', 40, 118, 0, 'back yard shed behind institute square')
bld('shed_a', 118, 119, 0, 'back yard shed east terrace')
bld('shed_b', 141, 120, 180, 'back yard store')
# --- hamlet (east of the canyon) infill along the gx=6 road and the ew road
bld('house_c', 104.5, 43, 90, 'gx=6 road east side')
bld('cottage_white', 104.5, 57, 90, 'gx=6 road east side')
bld('house_a', 132, -8.5, 180, 'hamlet road south side')
bld('cottage_white', 143, -9, 180, 'hamlet road south side')
bld('shed_a', 153, -8.5, 180, 'hamlet road south side shed')
bld('house_c', 163, 8.5, 0, 'hamlet road north side east end')
bld('hut_stone', 120, 26, 0, 'pigsty behind the hamlet')
bld('shed_b', 134, 40, 90, 'shed on the gx=9 lane', margin=2.5)
# --- Carn Cross hamlet on the east road
bld('cottage_white', 272, 152.5, 0, 'Carn Cross N')
bld('house_c', 308, 152.5, 0, 'Carn Cross N east')
bld('cottage_white', 274, 135.5, 180, 'Carn Cross S')
bld('house_f', 289, 134.5, 180, 'Carn Cross S')
bld('stable', 303, 135.5, 180, 'Carn Cross smithy/stable')
bld('hut_stone', 262, 138, 180, 'Carn Cross hut')
# --- Farm A: Higher Trewint (lane x=-32)
bld('farmhouse', -46, 204, 0, 'Higher Trewint farmhouse')
bld('barn', -51, 187, 270, 'Higher Trewint barn')
bld('stable', -39.8, 173.5, 180, 'Higher Trewint stable')
bld('hut_stone', -53, 174, 0, 'Higher Trewint pigsty')
# --- Farm B: Trewint Barton (lane end (2,14) x=32)
bld('farmhouse', 49, 236, 0, 'Trewint Barton farmhouse')
bld('barn', 48, 213, 180, 'Trewint Barton barn')
bld('stable', 61, 224, 90, 'Trewint Barton stable')
bld('hut_stone', 37, 234, 0, 'Trewint Barton hut')
# --- Farm C: Penhale (lane end (13,14) x=208)
bld('farmhouse', 208, 238, 0, 'Penhale farmhouse')
bld('barn', 222, 212, 180, 'Penhale barn')
bld('stable', 195, 224, 270, 'Penhale stable')
bld('hut_stone', 196, 236, 0, 'Penhale hut')
# --- Farm D: Carn Farm (lane end x=264, gz=14)
bld('farmhouse', 272, 236, 0, 'Carn Farm farmhouse')
bld('barn', 272, 212, 180, 'Carn Farm barn')
bld('stable', 284, 224, 90, 'Carn Farm stable')
bld('hut_stone', 261, 235, 0, 'Carn Farm hut')
# --- Farm E: Polgrean (lane (13,2) ew z=32, (14,2) x)
bld('farmhouse', 208, 44, 180, 'Polgrean farmhouse')
bld('barn', 208, 17, 0, 'Polgrean barn')
bld('stable', 226, 44, 180, 'Polgrean stable')
bld('hut_stone', 196.5, 26.5, 0, 'Polgrean pigsty')
# --- engine houses
bld('engine_house', 176, 240, 90, 'Wheal Kestrel engine house (north moor)')
bld('hut_stone', 168, 252, 0, 'Wheal Kestrel count house')
bld('engine_house', 276, -48, 90, 'Wheal Grace engine house above the cove')
bld('hut_stone', 270, -36, 0, 'Wheal Grace store')
# --- lookouts
bld('lookout_hut', -114, 253, 90, 'coastguard lookout, north cliffs', max_fall=2.5)
bld('lookout_hut', 208, -78, 0, 'cove-head lookout', max_fall=2.5)
bld('lookout_hut', 96, -62, 180, 'Kestrel Head lookout', max_fall=2.5)
# --- lone moor cottages / huts
bld('cottage_white', 112, 208, 0, 'lone cottage N plantation edge')
bld('hut_stone', 224, 96, 0, 'moor hut')
bld('hut_stone', 288, 48, 0, 'moor hut east')
bld('cottage_white', 240, 272, 0, 'lone cottage far north')
bld('hut_stone', 96, 256, 0, 'shepherd hut')
bld('hut_stone', 304, -32, 0, 'moor hut SE')
bld('cottage_white', 128, 240, 90, 'lone cottage by the moor lane')
bld('hut_stone', 64, 192, 0, 'hut at the plantation')
bld('hut_stone', 256, 80, 0, 'moor hut')
bld('cottage_white', 182, 72, 0, 'lone cottage off the Polgrean lane')

placed = []


def try_place(t, x, z, rot, note, kw):
    kw = dict(kw)
    mf = kw.pop('max_fall', 2.5)
    mg = kw.pop('margin', 3.0)
    sr = kw.pop('search', 0)
    if sr:
        res = W.search(t, x - sr, x + sr, z - sr, z + sr, [rot], step=1.0, max_fall=mf, margin=mg, want=1)
        if res:
            x, z = res[0][2], res[0][3]
        else:
            LOG.append('SEARCH FAIL %s near (%s,%s) %s' % (t, x, z, note))
            return None
    err = W.check(t, x, z, rot, mf, mg)
    if err and err.startswith('point prop'):
        # drop the blocking decorative props (allowed) and retry
        key = cell_of(x, z)
        poly = rect_corners(x, z, *FOOT[t], rot)
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                k2 = (key[0] + dx, key[1] + dz)
                if k2 not in cells:
                    continue
                keep = []
                for p in cells[k2]['props']:
                    if 'mason_type' in p or p.get('sit') or p.get('furn') or p.get('group'):
                        keep.append(p)
                        continue
                    pos = p['pos']
                    wx, wz = to_world(pos[0], pos[-1], k2)
                    from genlib import _pt_poly_dist
                    if _pt_poly_dist(wx, wz, poly) < 1.2:
                        LOG.append('dropped prop %s in %s for %s' % (p.get('url', '').split('/')[-1], k2, t))
                    else:
                        keep.append(p)
                cells[k2]['props'] = keep
        W.points = [pt for pt in W.points if not (pt[3] == 'prop' and _pt_poly_dist(pt[0], pt[1], poly) < 1.2)]
    p = W.place(t, x, z, rot, max_fall=mf, margin=mg, note=note)
    if p:
        placed.append((t, x, z, rot, note))
    return p


for (t, x, z, rot, note, kw) in B:
    try_place(t, x, z, rot, note, kw)

# add the building props to the cells
for key, prop, poly in W.new_buildings:
    cells[key]['props'].append(prop)
    if biome[key] in ('heath', 'moor_rock', 'field', 'copse', 'wood', 'headland', 'road_verge', 'cliff'):
        pass  # lone buildings sit in their landscape; biome unchanged

# write new roads
for key, r in W.roads_new.items():
    cells[key]['roads'] = r

# =====================================================================================
# 4. GROUND per biome
# =====================================================================================
GROUND = {
    'sea': {"preset": "sand", "color": [0.52, 0.49, 0.42], "rough": 0.97, "bump": 0.5, "tile": 4.0},
    'shore': {"preset": "sand", "color": [0.5, 0.48, 0.43], "rough": 0.95, "bump": 0.6, "tile": 3.0},
    'cliff': {"preset": "rock", "color": [0.36, 0.36, 0.35], "rough": 0.9, "bump": 0.8, "tile": 3.0},
    'quay': {"preset": "cobble", "color": [0.36, 0.36, 0.37], "rough": 0.6, "bump": 0.7, "tile": 1.6},
    'town': {"preset": "cobble", "color": [0.4, 0.39, 0.38], "rough": 0.62, "bump": 0.65, "tile": 1.8},
    'garden': {"preset": "grass", "color": [0.3, 0.4, 0.22], "rough": 1.0, "bump": 0.5, "tile": 4.0},
    'field': {"preset": "grass", "color": [0.34, 0.45, 0.24], "rough": 1.0, "bump": 0.5, "tile": 5.0},
    'farm': {"preset": "mud", "color": [0.32, 0.27, 0.2], "rough": 0.95, "bump": 0.6, "tile": 3.0},
    'wood': {"preset": "dirt", "color": [0.28, 0.25, 0.19], "rough": 0.98, "bump": 0.6, "tile": 4.0, "pat": "mottle"},
    'copse': {"preset": "grass", "color": [0.28, 0.35, 0.2], "rough": 1.0, "bump": 0.5, "tile": 5.0},
    'heath': {"preset": "grass", "color": [0.3, 0.32, 0.18], "rough": 1.0, "bump": 0.55, "tile": 5.0, "pat": "mottle"},
    'moor_rock': {"preset": "dirt", "color": [0.33, 0.31, 0.26], "rough": 0.95, "bump": 0.75, "tile": 4.0, "pat": "mottle"},
    'marsh': {"preset": "mud", "color": [0.24, 0.26, 0.18], "rough": 0.9, "bump": 0.5, "tile": 3.0},
    'road_verge': {"preset": "grass", "color": [0.31, 0.37, 0.21], "rough": 1.0, "bump": 0.5, "tile": 5.0},
    'headland': {"preset": "grass", "color": [0.33, 0.38, 0.24], "rough": 1.0, "bump": 0.45, "tile": 6.0},
}
for key, c in cells.items():
    b = biome[key]
    c['biome'] = b
    if b == 'inlet':
        continue
    c['ground'] = copy.deepcopy(GROUND[b])
# gravel yards for the farm cells that carry a lane
for key in cells:
    if biome[key] == 'farm' and cells[key].get('roads'):
        cells[key]['ground'] = {"preset": "gravel", "color": [0.4, 0.38, 0.33], "rough": 0.95, "bump": 0.6, "tile": 3.0}

# =====================================================================================
# 5. ROWS: walls, hedges, fences, lamps, bollards
# =====================================================================================
WALL_X = {"shape": "box", "size": [2.0, 1.1, 0.45], "material": "stone", "rot": 0}
WALL_Z = {"shape": "box", "size": [2.0, 1.1, 0.45], "material": "stone", "rot": 90}
QWALL_X = {"shape": "box", "size": [2.0, 0.7, 0.6], "material": "stone", "rot": 0}
FENCE = {"url": VE + "MS_Fence_Wood.glb"}
HEDGE = {"url": "props/q_unature/Bush_1.glb", "collider": "none"}
LAMP = {"url": MESHY + "lamp_post_harbour.glb"}
BOLLARD = {"url": MESHY + "mooring_bollard.glb"}

row_pending = collections.defaultdict(list)   # key -> [(priority, row)]
CLEAR_PTS = [(24.0, 24.0, 9.0), (36.0, 28.0, 4.0), (-10.0, -2.0, 4.0)]
for px, pz, r, lab in W.points:
    if lab.startswith('npc') or lab == 'chest':
        CLEAR_PTS.append((px, pz, 1.5))


def blocked(x, z, margin_b=0.6):
    k = cell_of(x, z)
    if k not in cells:
        return True
    for opoly, lab in W.obstacles:
        if _pt_poly_dist(x, z, opoly) < margin_b:
            return True
    for rp in W.road_polys_near(x, z):
        if _pt_poly_dist(x, z, rp) < 0.4:
            return True
    for px, pz, r in CLEAR_PTS:
        if math.hypot(x - px, z - pz) < r:
            return True
    return False


def row_line(x0, z0, x1, z1, part, spacing, priority=5, jitter=None, gaps=(), min_parts=2, part_by_dir=False, avoid=True):
    """Lay a row of parts along a world line, split by cell and around obstacles.
    gaps: list of (t0, t1) in metres along the line to leave open (gateways)."""
    L = math.hypot(x1 - x0, z1 - z0)
    if L < 1e-6:
        return
    n = int(L / spacing) + 1
    ux, uz = (x1 - x0) / L, (z1 - z0) / L
    if part_by_dir:
        part = WALL_X if abs(ux) >= abs(uz) else WALL_Z
    if 'Fence' in part.get('url', ''):
        part = dict(part)
        part['rot'] = 0 if abs(ux) >= abs(uz) else 90
    runs = []
    cur = []
    for i in range(n + 1):
        t = min(i * spacing, L)
        x, z = x0 + ux * t, z0 + uz * t
        ok = not any(g0 <= t <= g1 for g0, g1 in gaps)
        if ok and avoid and blocked(x, z):
            ok = False
        k = cell_of(x, z)
        if ok and k in cells and (not cur or cur[-1][0] == k):
            cur.append((k, x, z))
        else:
            if cur:
                runs.append(cur)
            cur = [(k, x, z)] if (ok and k in cells) else []
        if t >= L:
            break
    if cur:
        runs.append(cur)
    for run in runs:
        if len(run) < min_parts:
            continue
        k = run[0][0]
        fx, fz = to_local(run[0][1], run[0][2], k)
        tx, tz = to_local(run[-1][1], run[-1][2], k)
        row = {"part": copy.deepcopy(part), "from": [fx, fz], "to": [tx, tz], "spacing": spacing}
        if jitter:
            row["jitter"] = jitter
        row_pending[k].append((priority, row))


def cell_edge(k, side):
    """World coords of a cell edge line, pulled 0.3 m inside the cell."""
    cx, cz = k[0] * CS, k[1] * CS
    e = CS / 2 - 0.3
    if side == 'S':
        return (cx - e, cz - e, cx + e, cz - e)
    if side == 'N':
        return (cx - e, cz + e, cx + e, cz + e)
    if side == 'W':
        return (cx - e, cz - e, cx - e, cz + e)
    return (cx + e, cz - e, cx + e, cz + e)


NEIGH = {'S': (0, -1), 'N': (0, 1), 'W': (-1, 0), 'E': (1, 0)}
ENCLOSED = {'field', 'garden', 'farm'}
rng_state = [4471]


def rnd():
    rng_state[0] = (rng_state[0] * 1103515245 + 12345) & 0x7fffffff
    return rng_state[0] / 0x7fffffff


# --- field / garden / farm enclosure walls
for k in sorted(cells):
    b = biome[k]
    if b not in ENCLOSED:
        continue
    for side, (dx, dz) in NEIGH.items():
        nk = (k[0] + dx, k[1] + dz)
        nb = biome.get(nk)
        owner_side = side in ('S', 'W')
        if nb in ENCLOSED and not owner_side:
            continue   # the neighbour draws this shared edge
        if nb in ('sea', 'shore', 'inlet'):
            continue
        if nb == 'town' and b == 'garden':
            continue   # gardens open onto the town block behind the houses
        if b == 'field' and nb == 'field':
            # 2x2-cell fields (32 m): internal subdivision walls only on even grid lines
            if side == 'S' and k[1] % 2 != 0:
                continue
            if side == 'W' and k[0] % 2 != 0:
                continue
        x0, z0, x1, z1 = cell_edge(k, side)
        gaps = []
        if rnd() < 0.55:
            g = 5.0 + rnd() * 5.0
            gaps.append((g, g + 3.6))
        if b == 'farm':
            part = FENCE
            row_line(x0, z0, x1, z1, part, 2.0, priority=4, gaps=gaps)
        else:
            row_line(x0, z0, x1, z1, WALL_X, 1.9, priority=4, gaps=gaps, part_by_dir=True)

# --- cliff-edge walls on headland cells and the harbour rim
for k in sorted(cells):
    if biome[k] != 'headland':
        continue
    for side, (dx, dz) in NEIGH.items():
        nk = (k[0] + dx, k[1] + dz)
        if nk in cells and (W.terrain(nk) in ('steep', 'shore', 'sea')):
            x0, z0, x1, z1 = cell_edge(k, side)
            row_line(x0, z0, x1, z1, WALL_X, 1.9, priority=3, part_by_dir=True)
# the Prospect: a rim wall along the south kerb of the High Street above the canyon
row_line(28, 92.4, 76.5, 92.4, WALL_X, 1.9, priority=2, gaps=((22, 25.6),))
# a wall along the rim of the canyon head behind the top of the switchback / east of the hamlet road
row_line(88.5, 88, 88.5, 73, WALL_Z, 1.9, priority=3)

# --- quay wall + bollards at the harbour mouth
row_line(-13, 6, -3, 1.5, QWALL_X, 1.9, priority=1, avoid=False)
row_line(-2, 1, 1.5, -3.5, QWALL_X, 1.9, priority=1, avoid=False)
row_line(-12.5, 7.2, -3.5, 2.8, BOLLARD, 6.0, priority=1, avoid=False)

# --- hedges along the lanes (both verges), fences where the lane passes a farm
for k in sorted(cells):
    r = cells[k].get('roads')
    if not r or biome[k] not in ('road_verge', 'farm', 'field', 'heath', 'garden'):
        continue
    d = r[0]['dir']
    w = r[0].get('width', 6)
    off = w / 2 + 1.5
    cx, cz = k[0] * CS, k[1] * CS
    part = FENCE if biome[k] == 'farm' else HEDGE
    sp = 2.0 if biome[k] == 'farm' else 1.6
    jit = None if biome[k] == 'farm' else 0.3
    if any('Fence' in rr['part'].get('url', '') for rr in cells[k]['rows']):
        continue
    if d == 'ns':
        for s_ in (-1, 1):
            nb = biome.get((k[0] + s_, k[1]))
            if nb in ENCLOSED:
                continue
            row_line(cx + s_ * off, cz - 7.5, cx + s_ * off, cz + 7.5, part, sp, priority=6, jitter=jit)
    elif d == 'ew':
        for s_ in (-1, 1):
            nb = biome.get((k[0], k[1] + s_))
            if nb in ENCLOSED:
                continue
            row_line(cx - 7.5, cz + s_ * off, cx + 7.5, cz + s_ * off, part, sp, priority=6, jitter=jit)
    # x cells: hedges only on the two longest free quadrant edges would need 8 rows -> skip

# --- lamp rows: High Street cells with no lamp yet (south pavement), the quay head, Back Lane East
for k in [(5, 6), (7, 6), (8, 6), (9, 6), (10, 6)]:
    cx, cz = k[0] * CS, k[1] * CS
    row_line(cx - 6, cz - 4.4, cx + 6, cz - 4.4, LAMP, 12.0, priority=2)
for k in [(7, 5), (8, 5)]:
    cx, cz = k[0] * CS, k[1] * CS
    row_line(cx - 6, cz + 3.6, cx + 6, cz + 3.6, LAMP, 12.0, priority=2)
row_line(26, 10, 44, 28, LAMP, 9.0, priority=2)   # SE bank foot

# --- sheepfolds (4 walls each with a gateway) + a second stone circle
def sheepfold(cx, cz, hw=5.0, hd=4.0):
    row_line(cx - hw, cz - hd, cx + hw, cz - hd, WALL_X, 1.9, priority=3, gaps=((hw - 1.8, hw + 1.8),))
    row_line(cx - hw, cz + hd, cx + hw, cz + hd, WALL_X, 1.9, priority=3)
    row_line(cx - hw, cz - hd, cx - hw, cz + hd, WALL_Z, 1.9, priority=3)
    row_line(cx + hw, cz - hd, cx + hw, cz + hd, WALL_Z, 1.9, priority=3)


sheepfold(128, 196)      # (8,12) rocky moor
sheepfold(274, 48)       # (17,3)
sheepfold(80, 258)       # (5,16)
sheepfold(300, -100)     # (19,-6) headland above the south cliffs
cells[(18, 16)].setdefault('rings', []).append({"part": {"shape": "box", "size": [0.8, 2.2, 0.6], "material": "stone"}, "half": [5, 5], "spacing": 3.5})
cells[(18, 16)]['biome'] = 'moor_rock'

# commit rows, respecting the 6-per-cell cap by priority
over = 0
for k, lst in row_pending.items():
    have = len(cells[k]['rows'])
    lst.sort(key=lambda t: t[0])
    room = 6 - have
    for pr, row in lst[:max(room, 0)]:
        cells[k]['rows'].append(row)
    if len(lst) > max(room, 0):
        over += len(lst) - max(room, 0)
        LOG.append('ROW CAP %s: dropped %d rows (have %d)' % (k, len(lst) - max(room, 0), have))
print('rows dropped for cap:', over)

# =====================================================================================
# 6. CLUTTER PROPS
# =====================================================================================
def prop_ok(key, lx, lz):
    wx, wz = to_world(lx, lz, key)
    if abs(lx) > 7.8 or abs(lz) > 7.8:
        return 'outside'
    for opoly, lab in W.obstacles:
        if _pt_poly_dist(wx, wz, opoly) < 0.6:
            return 'in building ' + lab
    for rp in W.road_polys_near(wx, wz):
        if _pt_poly_dist(wx, wz, rp) < 0.3:
            return 'road'
    for px, pz, r in CLEAR_PTS:
        if math.hypot(wx - px, wz - pz) < r:
            return 'clear zone'
    for p in cells[key]['props']:
        if 'mason_type' in p or p.get('furn'):
            continue
        pos = p['pos']
        if math.hypot(pos[0] - lx, pos[-1] - lz) < 0.9:
            return 'prop crowd'
    return None


def add_prop(key, name, lx, lz, rot=None, **kw):
    key = tuple(key)
    c = cells[key]
    n_outside = sum(1 for p in c['props'] if not (p.get('furn') or p.get('group')))
    if n_outside >= 14:
        LOG.append('PROP CAP %s %s' % (key, name))
        return
    err = prop_ok(key, lx, lz)
    if err:
        LOG.append('PROP SKIP %s %s at %s: %s' % (key, name, (lx, lz), err))
        return
    if name.startswith('MS_'):
        url = VE + name
    elif name.startswith('Prop_'):
        url = MV + name
    else:
        url = MESHY + name
    p = {"url": url, "pos": [round(lx, 2), round(lz, 2)]}
    if rot is not None:
        p["rot"] = rot
    p.update(kw)
    c['props'].append(p)
    W.points.append((to_world(lx, lz, key)[0], to_world(lx, lz, key)[1], 0.8, 'prop'))


def add_props_world(items):
    for name, wx, wz, rot, kw in items:
        key = cell_of(wx, wz)
        lx, lz = to_local(wx, wz, key)
        lx = max(-7.6, min(7.6, lx))
        lz = max(-7.6, min(7.6, lz))
        add_prop(key, name, lx, lz, rot, **kw)


bench = {"sit": True}
# --- harbour mouth and quay
add_props_world([
    ('Prop_Boat_1.glb', -9, 9, 40, {}), ('Prop_Boat_1.glb', -14, 9.5, 20, {}), ('MS_Plank_Pile.glb', -6, 6, 60, {}),
    ('lobster_pots.glb', -10, 4.5, 30, {}), ('rowing_dinghy.glb', -5.5, 3.5, 135, {}), ('net_pile.glb', 9, -9, 20, {}),
    ('MS_Crate.glb', 9, 1.5, 15, {}), ('oil_drums_rusty.glb', 12, -2, 0, {}), ('fish_crates.glb', 12.5, 3.5, 300, {}),
    ('harbour_bench.glb', 7, 3.5, 225, bench), ('MS_Board_Message.glb', 10, 5.5, 225, {}),
    ('MS_Cable_Reel.glb', 9.5, 24.5, 0, {}), ('lobster_pots.glb', 22, 34.5, 45, {}),
    ('oil_drums_rusty.glb', 30, 10, 0, {}), ('MS_Crate.glb', 31.5, 13, 30, {}), ('MS_Barrier_Road.glb', 33.5, 23.5, 45, {}),
    ('harbour_bench.glb', 28.5, 20.5, 135, bench), ('lamp_post_harbour.glb', 31, 8, None, {}),
    ('fish_crates.glb', 43, 36, 45, {}), ('fish_crates.glb', 45, 38.5, 30, {}), ('MS_Pallet.glb', 39, 36, 45, {}), ('lobster_pots.glb', 24, 44, 80, {}), ('lamp_post_harbour.glb', 34, 41, None, {}),
    ('MS_Cable_Reel.glb', 51.5, 43.5, 0, {}), ('oil_drums_rusty.glb', 53, 43.5, 0, {}), ('MS_Board_Message.glb', 40.5, 55, 315, {}),
    ('harbour_bench.glb', 24.5, 40, 315, bench), ('rowing_dinghy.glb', 43, 43, 45, {}), ('net_pile.glb', 51.5, 36, 0, {}),
    ('MS_Plank_Pile.glb', 39, 23.5, 135, {}), ('oil_drums_rusty.glb', 44, 24, 0, {}), ('MS_Sawbuck.glb', 29, 13.5, 45, {}),
    ('Prop_Boat_1.glb', 6, -10, 130, {}), ('MS_Plank_Pile.glb', 5, -11, 40, {}),
])
# --- High Street and Institute Square
add_props_world([
    ('Prop_Well_1.glb', 38.5, 102.5, 0, {}), ('MS_Board_Message.glb', 35, 102.5, 180, {}), ('harbour_bench.glb', 42, 101.5, 180, bench),
    ('MS_Planter_Box.glb', 36, 100.5, 0, {}), ('MS_Planter_Box.glb', 41, 100.5, 0, {}), ('lamp_post_harbour.glb', 33.5, 100.5, None, {}),
    ('MS_Mailbox.glb', 19.7, 100.6, 0, {}), ('MS_Planter_Box.glb', -22, 100.6, 0, {}), ('MS_Planter_Box.glb', -12, 100.6, 0, {}), ('MS_Planter_Box.glb', -4, 100.6, 0, {}),
    ('harbour_bench.glb', 30, 91.5, 0, bench), ('harbour_bench.glb', 44, 91.5, 0, bench), ('harbour_bench.glb', 60, 91.5, 0, bench), ('MS_Trash.glb', 52, 91.2, 0, {}),
    ('MS_Board_Message.glb', 66, 91.4, 0, {}), ('MS_Sign_Public_Road_Ends.glb', 74.5, 100.8, 180, {}),
    ('MS_Crate.glb', 1.5, 91.5, 20, {}),
    ('MS_Firewood_A.glb', 105.5, 101.9, 0, {}), ('Prop_Cart_1.glb', 130.5, 101.5, 90, {}), ('MS_Trash.glb', 152, 101.5, 0, {}), ('MS_Mailbox.glb', 143, 101.4, 0, {}),
    ('Prop_Barrel_1.glb', 122, 90.2, 0, {}), ('MS_Pallet.glb', 118, 89.6, 20, {}), ('MS_Crate.glb', 110, 90, 0, {}), ('oil_drums_rusty.glb', 106, 89.2, 0, {}),
    ('MS_Firewood_A.glb', 132.5, 90.6, 0, {}), ('MS_Composter.glb', 143.5, 90.2, 0, {}),
    ('MS_Planter_Box.glb', -60.5, 86.5, 90, {}), ('MS_Firewood_A.glb', -68.5, 86, 0, {}),
    ('MS_Mailbox.glb', 12.7, 121, 270, {}), ('MS_Firewood_A.glb', 13, 113.5, 90, {}), ('MS_Planter_Box.glb', 12.8, 130.5, 0, {}),
    ('MS_Composter.glb', -20, 112, 0, {}), ('MS_Firewood_A.glb', -6, 111, 0, {}), ('MS_Sawbuck.glb', 2, 111.5, 30, {}),
    ('MS_Brick_Pile.glb', 44, 112, 0, {}), ('MS_Trash.glb', 30, 112, 0, {}), ('MS_Composter.glb', 124, 113.5, 0, {}), ('MS_Firewood_A.glb', 112, 113, 0, {}),
    ('Prop_Cart_1_Hay.glb', 134, 116, 0, {}),
])
# --- the west end + back lane + churchyard
add_props_world([
    ('MS_Board_Message.glb', -58, 100.6, 180, {}), ('Prop_Barrel_1.glb', -36.5, 101, 0, {}), ('MS_Planter_Box.glb', -50, 100.6, 0, {}),
    ('harbour_bench.glb', -44, 124.5, 180, bench), ('MS_Trash.glb', -27, 124.5, 0, {}), ('MS_Firewood_A.glb', -56, 132, 0, {}),
    ('harbour_bench.glb', 4, 138, 90, bench), ('harbour_bench.glb', 24, 140, 270, bench),
])
# --- hamlet east of the canyon
add_props_world([
    ('MS_Firewood_A.glb', 108.5, 47, 0, {}), ('MS_Composter.glb', 109, 60.5, 0, {}), ('Prop_Barrel_1.glb', 100, 21, 0, {}),
    ('Prop_Cart_1.glb', 122, 3.5, 0, {}), ('MS_Firewood_A.glb', 119.5, 4.5, 0, {}), ('MS_Trash.glb', 132, 4, 0, {}),
    ('MS_Firewood_A.glb', 133, -4.1, 0, {}), ('MS_Planter_Box.glb', 144, -5.1, 0, {}), ('Prop_Barrel_1.glb', 156, -5, 0, {}),
    ('MS_Board_Message.glb', 100, -3.5, 90, {}), ('MS_Mailbox.glb', 160, 4.6, 180, {}),
    ('Prop_Hay_1.glb', 122, 32, 0, {}), ('Prop_Cart_1_Hay.glb', 128, 44, 90, {}), ('MS_Sawbuck.glb', 116, 22, 0, {}),
    ('harbour_bench.glb', 96, -58, 0, bench), ('MS_Campfire.glb', 100, -58, 0, {}),
])
# --- Carn Cross
add_props_world([
    ('MS_Firewood_A.glb', 277, 149.6, 0, {}), ('Prop_Barrel_1.glb', 303, 150.5, 0, {}), ('MS_Mailbox.glb', 284, 148.8, 0, {}),
    ('Prop_Cart_1.glb', 296, 137.5, 90, {}), ('MS_Firewood_A.glb', 279, 138.9, 0, {}), ('MS_Board_Message.glb', 268, 147.6, 0, {}),
    ('Prop_Hay_1.glb', 309, 136.5, 0, {}), ('MS_Sawbuck.glb', 293, 149.8, 0, {}),
])
# --- farmyards
def farmyard(items):
    add_props_world(items)


farmyard([  # Higher Trewint
    ('Prop_Cart_1_Hay.glb', -43, 188, 0, {}), ('Prop_Hay_1.glb', -44, 183, 0, {}), ('Prop_Barrel_1.glb', -41, 197.5, 0, {}), ('Prop_Barrel_1.glb', -39.5, 196.5, 30, {}),
    ('MS_Firewood_A.glb', -50.5, 197.6, 0, {}), ('MS_Sawbuck.glb', -46, 196, 20, {}), ('Prop_Well_1.glb', -37, 188, 0, {}), ('MS_Trash.glb', -48, 178.5, 0, {}),
])
farmyard([  # Trewint Barton
    ('Prop_Cart_1_Hay.glb', 44, 221, 90, {}), ('Prop_Hay_1.glb', 52, 219, 0, {}), ('Prop_Barrel_1.glb', 55, 230, 0, {}), ('MS_Firewood_A.glb', 45, 229.8, 0, {}),
    ('Prop_Well_1.glb', 40, 226, 0, {}), ('MS_Sawbuck.glb', 56, 227, 0, {}), ('MS_Composter.glb', 58.5, 216, 0, {}),
])
farmyard([  # Penhale
    ('Prop_Cart_1_Hay.glb', 212, 218, 0, {}), ('Prop_Hay_1.glb', 216, 229, 0, {}), ('Prop_Barrel_1.glb', 203, 230.5, 0, {}), ('MS_Firewood_A.glb', 212.5, 230.5, 0, {}),
    ('Prop_Well_1.glb', 200, 218, 0, {}), ('MS_Sawbuck.glb', 214, 229, 0, {}), ('MS_Trash.glb', 200, 213, 0, {}),
])
farmyard([  # Carn Farm
    ('Prop_Cart_1.glb', 268, 220, 0, {}), ('Prop_Hay_1.glb', 278, 217.5, 0, {}), ('Prop_Barrel_1.glb', 279, 230, 0, {}), ('MS_Firewood_A.glb', 267.5, 229.8, 0, {}),
    ('Prop_Well_1.glb', 262, 228, 0, {}), ('MS_Sawbuck.glb', 277, 228, 0, {}), ('MS_Composter.glb', 280, 213, 0, {}),
])
farmyard([  # Polgrean
    ('Prop_Cart_1_Hay.glb', 218, 36.5, 0, {}), ('Prop_Hay_1.glb', 201, 26.5, 0, {}), ('Prop_Barrel_1.glb', 203, 37.8, 0, {}), ('MS_Firewood_A.glb', 213, 37.8, 0, {}),
    ('Prop_Well_1.glb', 198, 40, 0, {}), ('MS_Sawbuck.glb', 214, 26, 0, {}), ('MS_Trash.glb', 219, 27, 0, {}),
])
# --- engine houses, lookouts, lone cottages
add_props_world([
    ('MS_Cable_Reel.glb', 172, 233, 0, {}), ('oil_drums_rusty.glb', 180, 233.5, 0, {}), ('MS_Brick_Pile.glb', 171, 247, 0, {}), ('MS_Board_Message.glb', 165, 245, 270, {}),
    ('MS_Cable_Reel.glb', 270, -42, 0, {}), ('MS_Brick_Pile.glb', 280, -41, 0, {}), ('oil_drums_rusty.glb', 266, -40, 0, {}),
    ('harbour_bench.glb', -110, 250, 90, bench), ('MS_Board_Message.glb', -110, 256, 90, {}),
    ('harbour_bench.glb', 204, -74, 0, bench), ('MS_Campfire.glb', 212, -74, 0, {}),
    ('MS_Firewood_A.glb', 117, 205.5, 0, {}), ('MS_Firewood_A.glb', 245, 269.5, 0, {}), ('MS_Firewood_A.glb', 132, 235, 0, {}), ('MS_Firewood_A.glb', 181, 68.2, 0, {}),
    ('Prop_Barrel_1.glb', 106.5, 205, 0, {}), ('MS_Composter.glb', 234.5, 270, 0, {}), ('MS_Sawbuck.glb', 176, 66, 20, {}), ('Prop_Hay_1.glb', 227, 93, 0, {}),
    ('MS_Tent_Civilian.glb', 130, 200, 30, {}), ('MS_Campfire.glb', 133, 197.5, 0, {}),   # a traveller's camp by the (8,12) sheepfold
    ('MS_Tent_Civilian.glb', 300, -94, 200, {}), ('MS_Campfire.glb', 297, -91, 0, {}),
])
# --- shore cells: upturned boats + driftwood
add_props_world([
    ('Prop_Boat_1.glb', -22, 12, 60, {}), ('MS_Plank_Pile.glb', -20, 8, 20, {}), ('lobster_pots.glb', -18, 14, 0, {}),
    ('Prop_Boat_1.glb', 8, -14, 120, {}), ('MS_Plank_Pile.glb', 12, -10, 70, {}), ('net_pile.glb', 14, -12, 0, {}),
])

# =====================================================================================
# 7. VALIDATE + WRITE
# =====================================================================================
out = W.w
out['cells'] = [cells[k] for k in sorted(cells, key=lambda k: (k[1], k[0]))]
# preserve the original cell order instead
orig_order = [tuple(c['cell']) for c in json.load(open('/workspace/repo/world.json'))['cells']]
out['cells'] = [cells[k] for k in orig_order]

# validation
problems = []
for k, c in cells.items():
    n_out = sum(1 for p in c['props'] if not (p.get('furn') or p.get('group')))
    if n_out > 14:
        problems.append('props>14 %s %d' % (k, n_out))
    if len(c['props']) > 20:
        problems.append('props>20 %s %d' % (k, len(c['props'])))
    if len(c['rows']) > 6:
        problems.append('rows>6 %s %d' % (k, len(c['rows'])))
    for r in c['rows']:
        L = math.hypot(r['to'][0] - r['from'][0], r['to'][1] - r['from'][1])
        if L / r['spacing'] + 1 > 40:
            problems.append('row>40 %s' % (k,))
    if 'biome' not in c or 'ground' not in c:
        problems.append('missing biome/ground %s' % (k,))
# overlap check over all buildings (existing + new)
polys = [(p, l) for p, l in W.obstacles]
for i in range(len(polys)):
    for j in range(i + 1, len(polys)):
        if polys_overlap(polys[i][0], polys[j][0], 0.0):
            problems.append('OVERLAP %s x %s' % (polys[i][1], polys[j][1]))
print('placed', len(placed), 'of', len(B))
print('problems', len(problems))
for p in problems[:40]:
    print('  ', p)
print('LOG:')
for l in LOG:
    print('  ', l)
json.dump(out, open('/workspace/world.json', 'w'), separators=(',', ':'))
print('wrote /workspace/world.json', len(out['cells']), 'cells')
counts = collections.Counter(t for t, *_ in placed)
print(counts)
print(collections.Counter(biome.values()))
