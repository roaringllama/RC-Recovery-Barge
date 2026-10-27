"""Flat part outlines for the builder documents: one Shape per template, every number from design.py, geometry.py and the schedules.

No literals except 0, 1, 2, 1000 (a test enforces this). Coordinates are millimetres in the part's own frame, x to the right and y up,
moved so the outline's lower left corner is at (0, 0). A Shape holds the cut outline, cut-outs (holes and slots), guide marks that are
not cut (plank seams, groove, tube line, stations), the grain direction and short feature notes.
"""
import math
import design as D
from . import geometry as G
from . import schedules as S

RIGHT = math.degrees(math.pi / 2)                    # a square end, 90 deg
ARC_N = D.BLADE_ARC_PTS
QUARTER_N = max(2, ARC_N // (2 * 2 * 2))             # points on a quarter circle used for corner rounds


# ---- the Shape container ---------------------------------------------------------------------------------------------------------------------
class Shape:
    """outline: closed polygon [(x, y)]. cuts: [('circle', (cx, cy), r) | ('poly', pts)]. guides: [dict(kind, ..., style)]. planks: [polygon].
    grain: 'x' or 'y'. notes: feature text lines. points: [(x, y, text)] centre marks that are not holes (diameter not in the model)."""

    def __init__(self, outline, cuts=None, guides=None, planks=None, grain='x', notes=None, points=None):
        self.outline = [(float(x), float(y)) for x, y in outline]
        self.cuts = list(cuts or [])
        self.guides = list(guides or [])
        self.planks = [list(p) for p in (planks or [])]
        self.grain = grain
        self.notes = list(notes or [])
        self.points = list(points or [])

    def bbox(self):
        xs = [p[0] for p in self.outline]
        ys = [p[1] for p in self.outline]
        return min(xs), min(ys), max(xs), max(ys)

    def size(self):
        x0, y0, x1, y1 = self.bbox()
        return x1 - x0, y1 - y0

    def along_across(self):
        """(extent along the grain, extent across it)."""
        w, h = self.size()
        return (w, h) if self.grain == 'x' else (h, w)

    def area(self):
        a = poly_area(self.outline)
        for c in self.cuts:
            a -= math.pi * c[2] ** 2 if c[0] == 'circle' else poly_area(c[1])
        return a

    def map(self, fn):
        """New Shape with every point passed through fn(x, y) -> (x, y)."""
        pm = lambda pts: [fn(*p) for p in pts]
        cuts = [('circle', fn(*c[1]), c[2]) if c[0] == 'circle' else ('poly', pm(c[1])) for c in self.cuts]
        guides = []
        for g in self.guides:
            g2 = dict(g)
            for k in ('p', 'q', 'c'):
                if k in g2:
                    g2[k] = fn(*g2[k])
            if 'pts' in g2:
                g2['pts'] = pm(g2['pts'])
            guides.append(g2)
        return Shape(pm(self.outline), cuts, guides, [pm(p) for p in self.planks], self.grain, self.notes, [fn(p[0], p[1]) + (p[2],) for p in self.points])

    def normalized(self):
        x0, y0, _, _ = self.bbox()
        return self.map(lambda x, y: (x - x0, y - y0))

    def mirrored(self):
        """Left-right mirror about the bounding box centre (a starboard piece from a port one); polygon order is kept counter-clockwise."""
        x0, _, x1, _ = self.bbox()
        s = self.map(lambda x, y: (x0 + x1 - x, y))
        s.outline.reverse()
        s.planks = [list(reversed(p)) for p in s.planks]
        s.cuts = [(c[0], list(reversed(c[1]))) if c[0] == 'poly' else c for c in s.cuts]
        return s

    def rotated90(self):
        """Turned a quarter turn counter-clockwise; the grain axis follows."""
        s = self.map(lambda x, y: (-y, x))
        s.grain = 'y' if self.grain == 'x' else 'x'
        return s.normalized()


# ---- small geometry helpers --------------------------------------------------------------------------------------------------------------------
def poly_area(pts):
    return abs(sum(p[0] * q[1] - q[0] * p[1] for p, q in zip(pts, pts[1:] + pts[:1]))) / 2


def _dedupe(pts):
    out = []
    for p in pts:
        if not out or math.hypot(p[0] - out[-1][0], p[1] - out[-1][1]) > D.FIT_EPS:
            out.append((float(p[0]), float(p[1])))
    while len(out) > 1 and math.hypot(out[0][0] - out[-1][0], out[0][1] - out[-1][1]) <= D.FIT_EPS:
        out.pop()
    return out


def _ccw(pts):
    s = sum(p[0] * q[1] - q[0] * p[1] for p, q in zip(pts, pts[1:] + pts[:1]))
    return pts if s >= 0 else list(reversed(pts))


def arc(c, r, a0, a1, n=QUARTER_N):
    """Points on a circle arc from angle a0 to a1 (radians), n steps."""
    return [(c[0] + r * math.cos(a0 + (a1 - a0) * i / n), c[1] + r * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]


def rect(w, h):
    return [(0.0, 0.0), (w, 0.0), (w, h), (0.0, h)]


def rrect(x0, y0, x1, y1, r):
    """Rounded rectangle, counter-clockwise, corner radius r (square when r is 0)."""
    if r <= 0:
        return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    q = math.pi / 2
    pts = arc((x1 - r, y0 + r), r, -q, 0.0) + arc((x1 - r, y1 - r), r, 0.0, q) + arc((x0 + r, y1 - r), r, q, 2 * q) + arc((x0 + r, y0 + r), r, 2 * q, q * (1 + 2))
    return _dedupe(pts)


def circle_cut(cx, cy, r):
    return ('circle', (cx, cy), r)


def line_guide(p, q, style, text=''):
    return dict(kind='line', p=p, q=q, style=style, text=text)


def circle_guide(c, r, style, text=''):
    return dict(kind='circle', c=c, r=r, style=style, text=text)


def poly_guide(pts, style, text=''):
    return dict(kind='poly', pts=pts, style=style, text=text)


def clip_halfplane(poly, axis, value, keep_below):
    """Sutherland-Hodgman clip of a polygon to x <= value (axis 0) or y <= value (axis 1) when keep_below, else >=."""
    inside = (lambda p: p[axis] <= value + D.FIT_EPS) if keep_below else (lambda p: p[axis] >= value - D.FIT_EPS)
    out = []
    for i, p in enumerate(poly):
        q = poly[(i + 1) % len(poly)]
        if inside(p):
            out.append(p)
        if inside(p) != inside(q):
            t = (value - p[axis]) / (q[axis] - p[axis])
            out.append((p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1])))
    return _dedupe(out)


def split_polygon(poly, axis, n):
    """n equal slabs of a convex or simple polygon across `axis` (0 splits along x, 1 along y). Returns (pieces, seam values)."""
    lo = min(p[axis] for p in poly)
    hi = max(p[axis] for p in poly)
    cuts = [lo + (hi - lo) * i / n for i in range(n + 1)]
    pieces = []
    for a, b in zip(cuts, cuts[1:]):
        pc = clip_halfplane(poly, axis, a, False)
        pc = clip_halfplane(pc, axis, b, True) if pc else pc
        pieces.append(pc)
    return pieces, cuts[1:-1]


def level_split(outline, axis, n):
    """n equal slabs of a polygon across `axis` (planks as narrow as the stock allows when the outline is slanted), with the seam segments."""
    planks, cuts = split_polygon(outline, axis, n)
    seams = []
    for c in cuts:
        pts = [p for pk in planks for p in pk if abs(p[axis] - c) < D.FIT_EPS]
        o = 1 - axis
        lo, hi = min(p[o] for p in pts), max(p[o] for p in pts)
        seams.append(((lo, c), (hi, c)) if axis == 1 else ((c, lo), (c, hi)))
    return planks, seams


def station_panel(stations, n):
    """A panel given by stations [(u, lo, hi)] along its long axis: outline and n equal planks across it (seams interpolate between stations)."""
    low = [(u, lo) for u, lo, hi in stations]
    high = [(u, hi) for u, lo, hi in reversed(stations)]
    outline = _dedupe(low + high)
    planks = []
    for k in range(n):
        a = [(u, lo + (hi - lo) * k / n) for u, lo, hi in stations]
        b = [(u, lo + (hi - lo) * (k + 1) / n) for u, lo, hi in reversed(stations)]
        planks.append(_dedupe(a + b))
    seams = []
    for k in range(1, n):
        seams.append([(u, lo + (hi - lo) * k / n) for u, lo, hi in stations])
    return outline, planks, seams


def notched_rect(w, h, tl=None, tr=None, br=None, bl=None):
    """Rectangle w x h with corner notches: each corner is None, ('tri', leg) or ('sq', leg). Counter-clockwise from the left edge."""
    def corner(kind, a, pts_tri, pts_sq, plain):
        if kind is None:
            return [plain]
        return pts_tri(a) if kind[0] == 'tri' else pts_sq(a)
    pts = []
    pts += corner(bl and bl, bl and bl[1], lambda a: [(0.0, a), (a, 0.0)], lambda a: [(0.0, a), (a, a), (a, 0.0)], (0.0, 0.0))
    pts += corner(br and br, br and br[1], lambda a: [(w - a, 0.0), (w, a)], lambda a: [(w - a, 0.0), (w - a, a), (w, a)], (w, 0.0))
    pts += corner(tr and tr, tr and tr[1], lambda a: [(w, h - a), (w - a, h)], lambda a: [(w, h - a), (w - a, h - a), (w - a, h)], (w, h))
    pts += corner(tl and tl, tl and tl[1], lambda a: [(a, h), (0.0, h - a)], lambda a: [(a, h), (a, h - a), (0.0, h - a)], (0.0, h))
    return _dedupe(pts)


def long_grain(shape):
    """Grain along the longer side of the bounding box."""
    w, h = shape.size()
    shape.grain = 'x' if w >= h else 'y'
    return shape


# ---- hull skin panels (A-103) ------------------------------------------------------------------------------------------------------------------
def _stations_plan(xs, fn_lo, fn_hi):
    return [(x, float(fn_lo(x)), float(fn_hi(x))) for x in xs]


def station_lines(shape_dx, y_lo, y_hi, bbox_fn=None):
    """Frame station guide lines across a plan view part: one per frame with its F number."""
    out = []
    for i, x in enumerate(D.FRAME_X, 1):
        out.append(line_guide((x - shape_dx, y_lo), (x - shape_dx, y_hi), 'station', 'F%d' % i))
    return out


def _hatch_guides(dx, dy, sign=1, zone=None):
    """Hatch openings on a deck plan part drawn as dashed rectangles. dx, dy move plan coordinates (X, Y) to the part frame; sign mirrors Y."""
    out = []
    for h in G.hatch_rects():
        if zone and h['zone'] != zone:
            continue
        if zone == 'sponson' and h['yc'] < 0:
            continue
        if zone == 'center' and h['zone'] != 'center':
            continue
        y0, y1 = sorted((sign * h['y0'] - dy, sign * h['y1'] - dy))
        out.append(poly_guide(rect_pts(h['x0'] - dx, y0, h['x1'] - dx, y1), 'opening', h['name']))
    return out


def rect_pts(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def panel_shape(p, zd, plan=None):
    """Template shape of an A-103 panel row `p` (schedules.panels), or None when the panel is built from several marks elsewhere (DO, BP)."""
    mk = p['mark']
    n = p['planks']
    T = D.SKIN_T
    if mk in ('O1', 'O2', 'O3', 'I1', 'I2', 'TK'):
        L = p['length']
        out, planks, seams = station_panel([(0.0, 0.0, p['h0']), (L, 0.0, p['h1'])], n)
        sh = Shape(out, planks=planks, grain='x', guides=[line_guide(s[0], s[-1], 'seam') for s in seams])
        sh.notes = ['wall height %.2f aft end, %.2f forward end (deck underside less the bottom skin); the top edge follows the deck slope' % (p['h0'], p['h1'])]
        return sh
    if mk in ('TP', 'TR', 'TT', 'CA', 'CF'):
        w, h = p['length'], p['h0']
        sh = long_grain(Shape(rect(w, h)))
        return sh
    if mk in ('CO1', 'CO2', 'CI'):
        L = p['length']
        out, planks, seams = station_panel([(0.0, 0.0, p['h0']), (L, 0.0, p['h1'])], n)
        return Shape(out, planks=planks, grain='x', guides=[line_guide(s[0], s[-1], 'seam') for s in seams],
                     notes=['height above the deck top %.2f aft end, %.2f forward end' % (p['h0'], p['h1'])])
    if mk in ('BT', 'DK'):
        stn = _stations_plan(G.PLAN_STATIONS, G.inner_wall_y, G.outer_wall_y)
        out, planks, seams = station_panel(stn, n)
        y0 = min(s[1] for s in stn)
        sh = Shape(out, planks=planks, grain='x', guides=[line_guide(s[0], s[-1], 'seam') for s in seams]).map(lambda x, y: (x, y - y0))
        gd = station_lines(0.0, 0.0, max(s[2] for s in stn) - y0)
        if mk == 'DK':
            sh.guides += gd + _hatch_guides(0.0, y0, 1, 'sponson')
            sh.notes = ['dashed rectangles: hatch openings HM and HB of the port sponson; starboard is this piece turned over']
        else:
            sh.guides += gd + [poly_guide(rect_pts(0.0, G.YS - D.SKEG_W / 2 - y0, G.SKEG_X0, G.YS + D.SKEG_W / 2 - y0), 'opening', 'skeg box')]
            sh.notes = ['dashed: skeg box footprint, X 0 to %.1f; starboard is this piece turned over' % G.SKEG_X0]
        return sh
    if mk in ('RP', 'DC'):
        cw = lambda x: 2 * (G.HT + float(G.inner_off(x)))
        stn = [(x, -cw(x) / 2, cw(x) / 2) for x in (G.PLAN_STATIONS[0], G.PLAN_STATIONS[1], G.PLAN_STATIONS[-1])]
        out, planks, seams = station_panel(stn, n)
        y0 = -cw(0) / 2
        sh = Shape(out, planks=planks, grain='x', guides=[line_guide(s[0], s[-1], 'seam') for s in seams]).map(lambda x, y: (x, y - y0))
        sh.guides += station_lines(0.0, 0.0, cw(0))
        if mk == 'DC':
            sh.guides += _hatch_guides(0.0, y0, 1, 'center')
            sh.notes = ['dashed rectangles: hatch openings HC and HS']
        return sh
    if mk in ('AD', 'AB'):
        return aft_deck_shape(mk)
    if mk == 'CT':
        bps = [p['x0']] + [s for s in G.PLAN_STATIONS if p['x0'] < s < p['x1']] + [p['x1']]
        stn = _stations_plan(bps, G.inner_wall_y, G.outer_wall_y)
        out, planks, seams = station_panel(stn, n)
        y0 = min(s[1] for s in stn)
        return Shape(out, planks=planks, grain='x', guides=[line_guide(s[0], s[-1], 'seam') for s in seams]).map(lambda x, y: (x - bps[0], y - y0))
    if mk == 'SK':
        return skeg_plate_shape(n)
    if mk == 'SH':
        return shoe_shape()
    if mk == 'TE':
        return None
    return None


def aft_deck_shape(mk):
    """Aft deck top (AD) and bottom (AB) skins from the deck plan outline. Local x runs across the boat (port at the left), y runs forward."""
    plan = G.deck_plan()
    L, hw = D.AFT_DECK_L, D.AFT_DECK_W / 2
    if plan == 'rect':
        stn = [(-hw, -L, 0.0), (hw, -L, 0.0)]
    else:
        wc, c = D.BEAM / 2, -L + D.AFT_CHAMFER_L
        stn = [(-hw, c, 0.0), (-wc, -L, 0.0), (wc, -L, 0.0), (hw, c, 0.0)]
    n = max(1, math.ceil(L / D.STOCK_W))
    out, _, _ = station_panel(stn, n)
    planks, seams = level_split(out, 1, n)               # slabs across the length of the box, as narrow as the stock allows with the chamfered plan
    fn = lambda u, v: (hw - u, v + L)                     # port (+Y) at the left, bow at the top
    sh = Shape(out, planks=planks, grain='x', guides=[line_guide(s[0], s[-1], 'seam') for s in seams]).map(fn)
    sh.outline = _ccw(sh.outline)
    sh.planks = [_ccw(pk) for pk in sh.planks]
    sh.guides = [dict(g, text=g.get('text', '')) for g in sh.guides]
    if mk == 'AB':
        for sg in (1, -1):
            sh.points.append(fn(sg * G.YS, G.POSTX) + ('post %s' % ('port' if sg > 0 else 'stbd'),))
        sh.notes = ['crosses: nozzle post centres at X %.1f, Y +/- %.1f; the bushing hole size is not defined in the model (post %.1f dia)' % (G.POSTX, G.YS, D.NOZ_POST_D)]
    return sh.normalized()


def skeg_plate_shape(n):
    """Skeg side plate: right triangle in side view (x forward from the transom, z up), n planks, stern tube line marked."""
    out, _, _ = station_panel([(0.0, G.SHOE_BOT, 0.0), (G.SKEG_X0, 0.0, 0.0)], n)
    planks, seams = level_split(out, 1, n)               # level seams, so every plank is as narrow as the stock allows
    sh = Shape(out, planks=planks, grain='x', guides=[line_guide(s[0], s[-1], 'seam') for s in seams])
    sh.guides += tube_guides()
    sh.notes = ['stern tube centre line: through the CV joint (X %.1f, Z %.1f), rising %.1f deg forward, Z %.1f at the transom and the keel line at X %.1f; tube %.1f OD' % (D.CV_X, D.PROP_Z, D.MOTOR_AXIS_DEG, G.shaft_z(0.0), G.KEEL_X, D.TUBE_OD)]
    return sh.map(lambda x, y: (x, y - G.SHOE_BOT)).normalized()


def tube_guides():
    """Stern tube centre line and its two edges in the skeg side view (x forward, z up before normalizing)."""
    a = G.AXIS
    p0, p1 = (0.0, G.shaft_z(0.0)), (G.KEEL_X, 0.0)
    nx, ny = -math.sin(a), math.cos(a)
    r = D.TUBE_OD / 2
    out = [line_guide(p0, p1, 'axis', 'stern tube')]
    for sg in (1, -1):
        out.append(line_guide((p0[0] + sg * r * nx, p0[1] + sg * r * ny), (p1[0] + sg * r * nx, p1[1] + sg * r * ny), 'edge'))
    return out


def shoe_shape():
    """Skeg shoe: plan view of one layer, SHOE_AFT end at the left; pintle bushing hole at the nozzle post."""
    length = -G.SHOE_X1
    sh = Shape(rect(length, D.SKEG_W), grain='x')
    bx = G.POSTX - G.SHOE_X1                                    # post station measured from the aft end
    sh.cuts.append(circle_cut(bx, D.SKEG_W / 2, D.BUSHING_OD / 2))
    sh.notes = ['pintle bushing hole %.1f dia at %.1f from the aft end, on the centre line; layers are %.3f, shoe is %.2f thick; aft bottom edge radius R%.0f' % (
        D.BUSHING_OD, bx, D.SKIN_T, D.SHOE_T, G.SHOE_RE)]
    return sh


def skeg_core_shape(n):
    sh = skeg_plate_shape(n)
    # slot for the stern tube: two cut lines parallel to the tube centre line
    a = G.AXIS
    nx, ny = -math.sin(a), math.cos(a)
    r = D.TUBE_OD / 2
    dz = -G.SHOE_BOT
    p0, p1 = (0.0, G.shaft_z(0.0) + dz), (G.KEEL_X, dz)
    sh.guides = [g for g in sh.guides if g['style'] not in ('axis', 'edge')]
    sh.guides.append(line_guide(p0, p1, 'axis', 'tube centre'))
    for sg in (1, -1):
        sh.guides.append(line_guide((p0[0] + sg * r * nx, p0[1] + sg * r * ny), (p1[0] + sg * r * nx, p1[1] + sg * r * ny), 'slot'))
    sh.notes = ['slot %.1f wide along the tube centre line (cut lines), so the core separates into two pieces; core is %.2f thick, %d layers of %.3f' % (
        D.TUBE_OD, G.SKEG_INTERIOR, math.ceil(G.SKEG_INTERIOR / D.SKIN_T), D.SKIN_T)]
    return sh


# ---- frames, bulkheads, tunnel pieces (A-502) --------------------------------------------------------------------------------------------------
def frame_shape(f, side):
    """Sponson piece of frame f (schedules.frames row). side 'P' is drawn looking forward from the transom, outboard at the left; 'S' is its mirror."""
    w, h = f['w_in'], f['h']
    tri, sq = ('tri', D.BLOCK_LEG), ('sq', D.CHINE_LEG)
    notes = ['corner notches: %.3f triangles at the deck corners and the tunnel side bottom corner (blocking seats J3, J1); %.2f square at the outboard bottom corner (chine stringer J2)' % (D.BLOCK_LEG, D.CHINE_LEG)]
    cuts, guides = [], []
    if f['kind'] == 'solid_notch':
        wt = w - f['notch_w']
        out = notched_rect(wt, h, tl=tri, bl=sq)
        notes.append('trunk notch %.2f wide, full height, on the tunnel side; strip %.2f wide remains' % (f['notch_w'], wt))
    else:
        out = notched_rect(w, h, tl=tri, tr=tri, br=tri, bl=sq)
    if f['kind'] == 'ring':
        cuts.append(('poly', rect_pts(f['rib'], f['rib'], w - f['rib'], h - f['rib'])))
        notes.append('ring: members %.1f wide, opening %.1f x %.1f' % (f['rib'], f['open_w'], f['open_h']))
    if f['hole']:
        hd = f['hole']
        hx = (float(G.outer_wall_y(f['x'])) - D.SKIN_T) - hd['y']              # from the outboard face
        hr = hd['d'] / 2
        if hd['notch']:
            out = _notch_bottom(out, hx, hd['z'], hr)
            notes.append('shaft notch %.1f dia, centre %.1f from the outboard edge and %.2f above the bottom edge (opens through the bottom edge)' % (hd['d'], hx, hd['z']))
        else:
            cuts.append(circle_cut(hx, hd['z'], hr))
            notes.append('shaft hole %.1f dia, centre %.1f from the outboard edge and %.2f above the bottom edge' % (hd['d'], hx, hd['z']))
        guides.append(circle_guide((hx, hd['z']), hr, 'edge', ''))
    sh = Shape(out, cuts, guides, grain='y', notes=notes)
    if side == 'S':
        sh = sh.mirrored()
    return sh.normalized()


def _notch_bottom(outline, cx, cz, r):
    """Cut a round notch (centre cx, cz above the bottom edge y = 0, radius r) into the bottom edge of a counter-clockwise outline."""
    if cz >= r:
        return outline
    beta = math.asin(cz / r)
    dx = math.sqrt(max(r * r - cz * cz, 0.0))
    x1, x2 = cx - dx, cx + dx
    pts = []
    done = False
    for i, p in enumerate(outline):
        q = outline[(i + 1) % len(outline)]
        pts.append(p)
        if not done and abs(p[1]) < D.FIT_EPS and abs(q[1]) < D.FIT_EPS and p[0] < x1 and q[0] > x2:
            pts += arc((cx, cz), r, math.pi + beta, -beta, ARC_N // (2 * 2))
            done = True
    return _dedupe(pts)


def tunnel_shape(f):
    """Tunnel piece above the roof plate: ring or solid with the wire grommet hole."""
    w, h = f['tun_w'], f['tun_h']
    tri = ('tri', D.BLOCK_LEG)
    out = notched_rect(w, h, tl=tri, tr=tri, br=tri, bl=tri)
    cuts, notes = [], ['corner notches %.3f triangles (blocking seats, wall to roof plate and wall to deck)' % D.BLOCK_LEG]
    if f['tunnel_kind'] == 'ring':
        cuts.append(('poly', rect_pts(f['rib'], f['rib'], w - f['rib'], h - f['rib'])))
        notes.append('ring: members %.1f wide, opening %.1f x %.1f' % (f['rib'], w - 2 * f['rib'], h - 2 * f['rib']))
    else:
        g = f['grommet']
        cuts.append(circle_cut(w / 2 + g['y'], g['z'], g['d'] / 2))
        notes.append('wire grommet hole %.1f dia on the centre line, sitting on the roof plate (touches the bottom edge)' % g['d'])
    if f['clash']:
        notes.append('crosses ' + ', '.join(c.replace(' (tunnel frame)', '') for c in f['clash']) + ': notch size to the equipment is not defined in the model')
    return Shape(out, cuts, grain='x', notes=notes).normalized()


# ---- small flat parts -----------------------------------------------------------------------------------------------------------------------------
def rect_part(w, h, notes=None, cuts=None):
    return long_grain(Shape(rect(w, h), cuts, notes=notes))


def bracket_shape(L):
    return Shape(rect(L, D.FRAME_RIB), grain='x', notes=['deck bracket: frame extended outboard from the hull outer wall to the deck edge, %.2f long x %.2f deep' % (L, D.FRAME_RIB)])


def trunk_end_shape(h):
    return Shape(rect(G.blade_params()['trunk_w'], h), grain='y')


def deck_overhang_shapes(plan=None):
    """Deck overhang skin as three pieces: port side strip, starboard side strip, and the strip ahead of the bow tips."""
    if G.deck_plan(plan) != 'rect':
        return {}
    hw = D.AFT_DECK_W / 2
    wall = [(x, float(G.outer_wall_y(x))) for x in G.PLAN_STATIONS]
    poly = [(x, y) for x, y in wall] + [(wall[-1][0], hw), (wall[0][0], hw)]
    y0 = min(p[1] for p in poly)
    port = Shape(_ccw(poly), grain='x', guides=station_lines(0.0, 0.0, hw - y0)).map(lambda x, y: (x, y - y0)).normalized()
    stbd = port.mirrored()
    front = long_grain(Shape(rect(D.AFT_DECK_W, G.BUMPER_GAP)))
    cuts = [x for x in G.PLAN_STATIONS if 0 < x < D.LOA]                  # butt joints where the hull outline turns
    for sh, xs in ((port, cuts), (stbd, [D.LOA - x for x in reversed(cuts)])):
        edges = [0.0] + xs + [D.LOA]
        sh.planks = [_dedupe(clip_halfplane(clip_halfplane(sh.outline, 0, b, True), 0, a, False)) for a, b in zip(edges, edges[1:])]
        sh.guides += [line_guide((x, 0.0), (x, sh.size()[1]), 'seam') for x in xs]
    port.notes = ['strip between the hull outer wall and the deck edge (Y %.1f), X 0 to %.0f; frame stations dashed; butt joints dashed at the hull corners' % (hw, D.LOA)]
    stbd.notes = port.notes
    front.notes = ['strip ahead of the bow tips, X %.0f to %.0f, full deck width' % (D.LOA, G.BUMPER_X0)]
    return dict(P=port, S=stbd, F=front)


# ---- blades -----------------------------------------------------------------------------------------------------------------------------------------
def blade_shape():
    """Daggerboard blade, extended outline: sector about the hinge. Hinge centre, lift line attachment and the trunk end line are marked."""
    b = G.blade_params()
    pts = G.blade_outline(True)
    hx, hz = b['hinge_x'], b['hinge_z']
    lx, lz = G.line_attach(True)
    sh = Shape(pts, grain='x', points=[(hx, hz, 'hinge centre'), (lx, lz, 'lift line, %.0f from the hinge' % D.LINE_R)])
    t0, t1 = G.trunk_x()
    stop_x = t1 if b['dir'] == 'fwd' else t0
    sh.guides.append(line_guide((stop_x, hz + D.TRUNK_TIP_CLR), (stop_x, hz - b['R'] * math.sin(math.radians(b['sector_deg']))), 'station',
                                'trunk end X %.0f' % stop_x))
    sh.guides.append(line_guide((hx, hz), (hx + b['R'], hz), 'axis', 'keel line'))
    sh.notes = ['sector R%.0f, %.0f deg; hinge at X %.0f, Z %.0f; tip stops %.1f short of the trunk end; hole diameters are not defined in the model, centres only' % (
        b['R'], b['sector_deg'], hx, hz, D.TRUNK_TIP_CLR)]
    return sh.normalized()


# ---- mount, pads, rails, bars --------------------------------------------------------------------------------------------------------------------
def mount_layers():
    """Layers of one motor mount: list of dicts(j, x0, x1, len, width). Layer j (1 at the bottom) is SKIN_T thick, from the floor skin up;
    the top face slopes at MOTOR_AXIS_DEG, so a layer starts where the sloped top reaches its underside."""
    m = S.mount_dims()
    T = D.SKIN_T
    xa, xb = G.MOUNT[0][0], G.MOUNT[1][0]
    out = []
    for j in range(1, m['layers'] + 1):
        zb = (j - 1) * T
        zt = j * T
        x_start = xa if zb <= m['h_aft'] else xa + (zb - m['h_aft']) / G.TAN
        x_full = xa if zt <= m['h_aft'] else xa + (zt - m['h_aft']) / G.TAN
        out.append(dict(j=j, x0=x_start, x1=xb, len=xb - x_start, width=D.MOUNT_W, x_full=min(x_full, xb), slope=zt > m['h_aft']))
    return out


def mount_layer_shape(ly, m):
    sh = Shape(rect(ly['len'], D.MOUNT_W), grain='x')
    if ly['slope']:
        sh.guides.append(line_guide((ly['x_full'] - ly['x0'], 0.0), (ly['x_full'] - ly['x0'], D.MOUNT_W), 'slope', 'full thickness from here'))
    sh.notes = ['layer %d of %d, %.3f thick; the finished top face slopes %.0f deg (rises toward the bow); mount %.1f long x %.0f wide, %.1f high aft to %.1f forward' % (
        ly['j'], m['layers'], D.SKIN_T, m['angle'], m['l'], D.MOUNT_W, m['h_aft'], m['h_fwd'])]
    return sh


def hatch_shapes(h, plan_zd=None):
    """Lid, plug layers and rim ring of one hatch row (schedules.hatches). Local x along X, y across Y; the opening is at the origin before normalizing."""
    se = S.hatch_seal()
    L, W = h['L'], h['W']
    Rc = D.HATCH_CORNER_R
    F = D.FLANGE
    # lid: flange layer with an end tab at each end, screw hole at the pad centre
    R_l = Rc + F
    fx0, fx1, fy0, fy1 = -F, L + F, -F, W + F
    te = se['tab_end']
    tx0, tx1 = -te, L + te
    ty0, ty1 = W / 2 - D.LATCH_PAD / 2, W / 2 + D.LATCH_PAD / 2
    q = math.pi / 2
    lid_pts = (arc((fx0 + R_l, fy0 + R_l), R_l, 2 * q, q * (1 + 2)) + [(fx1 - R_l, fy0)] + arc((fx1 - R_l, fy0 + R_l), R_l, -q, 0.0)[1:] + [(fx1, ty0), (tx1, ty0), (tx1, ty1), (fx1, ty1)] +
               arc((fx1 - R_l, fy1 - R_l), R_l, 0.0, q) + arc((fx0 + R_l, fy1 - R_l), R_l, q, 2 * q) + [(fx0, ty1), (tx0, ty1), (tx0, ty0), (fx0, ty0)])
    lid = Shape(_ccw(_dedupe(lid_pts)), grain='x')
    for sx in (-se['pad_off'], L + se['pad_off']):
        lid.cuts.append(circle_cut(sx, W / 2, D.LATCH_SCREW_D / 2))
    lid.guides.append(poly_guide(rrect(0.0, 0.0, L, W, Rc), 'opening', 'opening %.1f x %.1f' % (L, W)))
    lid.notes = ['flange %.1f all round, corner R%.1f; end tabs %.1f wide reach %.3f from the opening edge; M3 clearance holes %.1f dia at %.3f from the opening edge' % (
        F, R_l, D.LATCH_PAD, te, D.LATCH_SCREW_D, se['pad_off']),
        'tab width is taken as the latch pad width (LATCH_PAD); the model gives the tab end only']
    # plug layer (both layers have the same outline, grain crossed)
    Rp = Rc - D.PLUG_CLR / 2
    pl_L, pl_W = h['plug_L'], h['plug_W']
    plug = Shape(rrect(0.0, 0.0, pl_L, pl_W, Rp), grain='x')
    plug.guides.append(poly_guide(rrect(D.GROOVE_D, D.GROOVE_D, pl_L - D.GROOVE_D, pl_W - D.GROOVE_D, max(Rp - D.GROOVE_D, 0.0)), 'groove',
                                  'O-ring groove %.1f wide x %.1f deep' % (D.GROOVE_W, D.GROOVE_D)))
    plug.notes = ['plug %.1f x %.1f, corner R%.1f; %d layers of %.3f, grain crossed between layers; O-ring groove line inset %.1f from the edge, centred on the joint between the layers; cord loop %.0f long' % (
        pl_L, pl_W, Rp, D.PLUG_LAYERS, D.SKIN_T, D.GROOVE_D, h['cord'])]
    # rim ring under the deck
    ry = h['rim_y']
    oL, oW = L + 2 * D.RIM_W, W + 2 * ry
    rim = Shape(rect(oL, oW), grain='x')
    rim.cuts.append(('poly', rrect(D.RIM_W, ry, D.RIM_W + L, ry + W, Rc)))
    rim.notes = ['rim ring %.3f thick, %.3f wide on the X sides and %.2f on the Y sides%s; opening %.1f x %.1f, corner R%.1f' % (
        D.RIM_T, D.RIM_W, ry, ' (trimmed to the wall)' if h['rim_touch'] else '', L, W, Rc)]
    return lid.normalized(), plug, rim


def latch_pad_shape():
    sh = Shape(rect(D.LATCH_PAD, D.LATCH_PAD), grain='x')
    sh.cuts.append(circle_cut(D.LATCH_PAD / 2, D.LATCH_PAD / 2, D.LATCH_SCREW_D / 2))
    sh.notes = ['M3 hole %.1f dia at the centre; M3 nut %.1f thick; nut flat size is not defined in the model' % (D.LATCH_SCREW_D, D.LATCH_NUT_T)]
    return sh


def bar_face_shape():
    return Shape(rect(G.bumper_front_width(), G.BUMPER_DEPTH), grain='x', notes=['ply face on the front of the push bar, %.1f thick' % D.BUMPER_FACE_T])
