"""Core helpers for the Kestrel Bay fill pass: heights, footprints, obstacles, placement."""
import json, math, copy
import numpy as np

CS = 16.0
FOOT = {
    'house_a': [8, 7], 'house_b': [9, 7], 'house_c': [7, 6], 'terrace': [21, 7], 'store': [10, 8],
    'shed_a': [6, 5], 'shed_b': [9, 6], 'boathouse': [12, 7], 'cottage_white': [8, 6], 'house_d': [7, 8],
    'house_f': [8, 8], 'farmhouse': [12, 10], 'barn': [14, 8], 'stable': [10, 6], 'warehouse': [16, 9],
    'engine_house': [8, 10], 'lookout_hut': [5, 5], 'institute': [14, 9], 'hut_stone': [4, 4],
    'lifeboat_house': [12, 8], 'chandlery': [10, 8], 'fish_market': [12, 8],
}
MESHY = '/cloud-cbnqgdi78kdlrr3elmbb/models/meshy/'
VE = 'props/vostok_extra/'
MV = 'props/mod_village/'

# ---------------------------------------------------------------- heights
_lines = open('/workspace/heights.csv').read().strip().split('\n')
X0, X1, Z0, Z1, STEP = [float(v) for v in _lines[0].split(',')]
H = np.array([[float(v) for v in l.split(',')] for l in _lines[1:]])


def h(x, z):
    i = (z - Z0) / STEP
    j = (x - X0) / STEP
    i0 = int(np.clip(math.floor(i), 0, H.shape[0] - 2))
    j0 = int(np.clip(math.floor(j), 0, H.shape[1] - 2))
    fi = min(max(i - i0, 0.0), 1.0)
    fj = min(max(j - j0, 0.0), 1.0)
    return float(H[i0, j0] * (1 - fi) * (1 - fj) + H[i0 + 1, j0] * fi * (1 - fj)
                 + H[i0, j0 + 1] * (1 - fi) * fj + H[i0 + 1, j0 + 1] * fi * fj)


# ---------------------------------------------------------------- geometry
def cell_of(x, z):
    return (int(math.floor((x + CS / 2) / CS)), int(math.floor((z + CS / 2) / CS)))


def to_local(x, z, cell):
    return (round(x - cell[0] * CS, 2), round(z - cell[1] * CS, 2))


def to_world(lx, lz, cell):
    return (lx + cell[0] * CS, lz + cell[1] * CS)


def rect_corners(cx, cz, w, d, rot):
    """Rotated rectangle corners. rot=0: door (-Z). Godot yaw: +rot rotates -Z toward -X."""
    r = math.radians(rot)
    c, s = math.cos(r), math.sin(r)
    pts = []
    for px, pz in ((-w / 2, -d / 2), (w / 2, -d / 2), (w / 2, d / 2), (-w / 2, d / 2)):
        pts.append((cx + px * c + pz * s, cz - px * s + pz * c))
    return pts


def door_dir(rot):
    """World direction the s (-Z) face points after rot."""
    r = math.radians(rot)
    return (-math.sin(r), -math.cos(r))


def _axes(pts):
    ax = []
    for i in range(2):
        ex = pts[i + 1][0] - pts[i][0]
        ez = pts[i + 1][1] - pts[i][1]
        L = math.hypot(ex, ez) or 1.0
        ax.append((ex / L, ez / L))
    return ax


def polys_overlap(a, b, margin=0.0):
    """Separating-axis test for two convex quads, with a margin (min gap)."""
    for ax in _axes(a) + _axes(b):
        pa = [p[0] * ax[0] + p[1] * ax[1] for p in a]
        pb = [p[0] * ax[0] + p[1] * ax[1] for p in b]
        if max(pa) + margin <= min(pb) or max(pb) + margin <= min(pa):
            return False
    return True


def aabb_poly(x0, z0, x1, z1):
    return [(x0, z0), (x1, z0), (x1, z1), (x0, z1)]


def sample_fall(pts, step=1.0):
    """Max-min terrain height across the polygon (sampled), plus min height."""
    xs = [p[0] for p in pts]
    zs = [p[1] for p in pts]
    hs = []
    # sample in the rectangle's own frame
    cx = sum(xs) / 4
    cz = sum(zs) / 4
    ex = (pts[1][0] - pts[0][0], pts[1][1] - pts[0][1])
    ez = (pts[3][0] - pts[0][0], pts[3][1] - pts[0][1])
    n1 = max(2, int(math.hypot(*ex) / step) + 1)
    n2 = max(2, int(math.hypot(*ez) / step) + 1)
    for i in range(n1):
        for j in range(n2):
            u = i / (n1 - 1)
            v = j / (n2 - 1)
            x = pts[0][0] + ex[0] * u + ez[0] * v
            z = pts[0][1] + ex[1] * u + ez[1] * v
            hs.append(h(x, z))
    return max(hs) - min(hs), min(hs), max(hs)


def road_strips(cell, roads):
    """Axis-aligned world rects for a cell's road strips."""
    cx, cz = cell[0] * CS, cell[1] * CS
    out = []
    for r in roads:
        w = r.get('width', 6) / 2.0
        d = r['dir']
        if d in ('ns', 'x'):
            out.append(aabb_poly(cx - w, cz - CS / 2, cx + w, cz + CS / 2))
        if d in ('ew', 'x'):
            out.append(aabb_poly(cx - CS / 2, cz - w, cx + CS / 2, cz + w))
    return out


class World:
    def __init__(self, path='/workspace/repo/world.json'):
        self.w = json.load(open(path))
        self.cells = {tuple(c['cell']): c for c in self.w['cells']}
        self.cm = {tuple(c['cell']): c for c in json.load(open('/workspace/cellmap.json'))}
        self.obstacles = []   # (poly, label)
        self.points = []      # (x, z, radius, label) keep-clear circles
        self.new_buildings = []  # (cell, prop dict, world poly)
        self.roads_new = {}
        self.log = []
        self._collect()

    # ------------------------------------------------------------ obstacles
    def _collect(self):
        for key, c in self.cells.items():
            if 'landmark' in c:
                lm = c['landmark']
                fp = lm.get('footprint')
                if fp:
                    pos = lm.get('pos', [0, 0])
                    wx, wz = to_world(pos[0], pos[1], key)
                    self.obstacles.append((rect_corners(wx, wz, fp[0], fp[1], lm.get('rot', 0)), 'LM:%s@%s' % (lm.get('mason_type'), key)))
            for p in c.get('props', []):
                if 'mason_type' in p and p.get('footprint'):
                    wx, wz = to_world(p['pos'][0], p['pos'][1], key)
                    self.obstacles.append((rect_corners(wx, wz, p['footprint'][0], p['footprint'][1], p.get('rot', 0)), 'B:%s@%s' % (p['mason_type'], key)))
            for s in c.get('structures', []):
                wx, wz = to_world(s['pos'][0], s['pos'][1], key)
                self.obstacles.append((rect_corners(wx, wz, s['footprint'][0], s['footprint'][1], s.get('rot', 0)), 'S@%s' % (key,)))
            if 'npc' in c:
                n = c['npc']
                if isinstance(n, dict) and 'pos' in n:
                    wx, wz = to_world(n['pos'][0], n['pos'][1], key)
                    self.points.append((wx, wz, 2.0, 'npc:%s' % n.get('name')))
            if 'chest' in c:
                wx, wz = to_world(c['chest']['pos'][0], c['chest']['pos'][1], key)
                self.points.append((wx, wz, 1.5, 'chest'))
            for p in c.get('props', []):
                if 'mason_type' in p:
                    continue
                if p.get('sit') or p.get('furn'):
                    continue
                pos = p.get('pos', [0, 0])
                wx, wz = to_world(pos[0], pos[-1] if len(pos) == 3 else pos[1], key)
                self.points.append((wx, wz, 1.2, 'prop'))
        for v in self.w['vehicles']:
            self.points.append((v['pos'][0], v['pos'][1], 5.0, 'vehicle:%s' % v['name']))
        self.points.append((24.0, 24.0, 9.0, 'spawn'))

    def all_roads(self, key):
        c = self.cells[key]
        r = list(c.get('roads', []))
        r += self.roads_new.get(key, [])
        return r

    def road_polys_near(self, x, z):
        cx, cz = cell_of(x, z)
        out = []
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                k = (cx + dx, cz + dz)
                if k in self.cells:
                    out += road_strips(k, self.all_roads(k))
        return out

    def terrain(self, key):
        return self.cm[key]['terrain']

    # ------------------------------------------------------------ roads
    def add_road(self, key, d, width=4):
        c = self.cells[key]
        if c.get('roads'):
            ex = c['roads'][0]
            if ex['dir'] != d and not (ex['dir'] == 'x'):
                self.log.append('ROAD CONFLICT %s existing %s wanted %s' % (key, ex, d))
            return
        if key in self.roads_new:
            if self.roads_new[key][0]['dir'] != d:
                self.log.append('ROAD DUP %s %s vs %s' % (key, self.roads_new[key], d))
            return
        if self.terrain(key) == 'steep':
            self.log.append('ROAD ON STEEP %s' % (key,))
        self.roads_new[key] = [{'dir': d, 'width': width}]

    # ------------------------------------------------------------ placement
    def check(self, mtype, wx, wz, rot, max_fall=2.5, margin=3.0, min_h=1.2, ignore_points=()):
        w, d = FOOT[mtype]
        poly = rect_corners(wx, wz, w, d, rot)
        for opoly, lab in self.obstacles:
            if polys_overlap(poly, opoly, margin):
                return 'overlap %s' % lab
        for rp in self.road_polys_near(wx, wz):
            if polys_overlap(poly, rp, 0.5):
                return 'road'
        for px, pz, r, lab in self.points:
            if lab in ignore_points:
                continue
            # distance from point to polygon <= r ?
            if _pt_poly_dist(px, pz, poly) < r:
                return 'point %s' % lab
        fall, hmin, hmax = sample_fall(poly)
        if fall > max_fall:
            return 'fall %.1f' % fall
        if hmin < min_h:
            return 'water %.1f' % hmin
        return None

    def place(self, mtype, wx, wz, rot, max_fall=2.5, margin=3.0, note='', ignore_points=(), force=False):
        err = self.check(mtype, wx, wz, rot, max_fall, margin, ignore_points=ignore_points)
        if err and not force:
            self.log.append('FAIL %s at (%.1f,%.1f) rot %s: %s %s' % (mtype, wx, wz, rot, err, note))
            return None
        if err:
            self.log.append('FORCED %s at (%.1f,%.1f) rot %s: %s %s' % (mtype, wx, wz, rot, err, note))
        key = cell_of(wx, wz)
        lx, lz = to_local(wx, wz, key)
        w, d = FOOT[mtype]
        poly = rect_corners(wx, wz, w, d, rot)
        prop = {'mason_type': mtype, 'pos': [lx, lz], 'rot': rot, 'footprint': [w, d]}
        self.obstacles.append((poly, 'NEW:%s@%s' % (mtype, key)))
        self.new_buildings.append((key, prop, poly))
        return prop

    def search(self, mtype, x0, x1, z0, z1, rots, step=1.0, max_fall=2.5, margin=3.0, want=1, ignore_points=(), score=None):
        """Brute-force candidate centres; returns list of (fall, x, z, rot)."""
        found = []
        for rot in rots:
            xs = np.arange(x0, x1 + 1e-6, step)
            zs = np.arange(z0, z1 + 1e-6, step)
            for x in xs:
                for z in zs:
                    err = self.check(mtype, float(x), float(z), rot, max_fall, margin, ignore_points=ignore_points)
                    if err is None:
                        w, d = FOOT[mtype]
                        fall, hmin, hmax = sample_fall(rect_corners(x, z, w, d, rot))
                        sc = score(x, z, rot, fall) if score else fall
                        found.append((round(sc, 2), round(fall, 2), float(x), float(z), rot))
        found.sort()
        return found[:want] if want else found


def _pt_poly_dist(px, pz, poly):
    # inside test via cross products (convex, consistent winding)
    inside = True
    sign = None
    n = len(poly)
    dmin = 1e9
    for i in range(n):
        ax, az = poly[i]
        bx, bz = poly[(i + 1) % n]
        cr = (bx - ax) * (pz - az) - (bz - az) * (px - ax)
        s = cr >= 0
        if sign is None:
            sign = s
        elif s != sign:
            inside = False
        # segment distance
        vx, vz = bx - ax, bz - az
        L2 = vx * vx + vz * vz or 1.0
        t = max(0.0, min(1.0, ((px - ax) * vx + (pz - az) * vz) / L2))
        dmin = min(dmin, math.hypot(px - (ax + vx * t), pz - (az + vz * t)))
    return 0.0 if inside else dmin
