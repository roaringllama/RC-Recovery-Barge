"""Nesting of the cut pieces on the stock: 2D MaxRects for sheets (balsa keeps its grain along the 36 in length), a polygon-aware pairing for the
two G10 blades, and first-fit-decreasing for sticks (the 3/8 triangular sticks have two lanes: each stick rips into two lengths, a corner wedge
takes a whole stick). Every kerf is design.KERF. A piece longer than its stock raises StockError."""
import math
import design as D


class StockError(ValueError):
    pass


class Placed:
    """A piece on a stock sheet or stick. x runs along the stock length, y across it (sticks: lane)."""

    def __init__(self, mark, inst, x, y, w, h, rot=False, poly=None, grain='x'):
        self.mark, self.inst, self.x, self.y, self.w, self.h, self.rot, self.poly, self.grain = mark, inst, x, y, w, h, rot, poly, grain


class Bin:
    def __init__(self, no, stock):
        self.no, self.stock, self.placed = no, stock, []

    def used_area(self):
        return sum(p.w * p.h for p in self.placed)


# ---- MaxRects ---------------------------------------------------------------------------------------------------------------------------------
class _Rects:
    def __init__(self, W, H, kerf):
        self.W, self.H, self.k = W, H, kerf
        self.free = [(0.0, 0.0, W + kerf, H + kerf)]

    def find(self, w, h, rot):
        best = None
        for (fx, fy, fw, fh) in self.free:
            for r in ((False, True) if rot else (False,)):
                ww, hh = (h, w) if r else (w, h)
                ww, hh = ww + self.k, hh + self.k
                if ww <= fw + D.FIT_EPS and hh <= fh + D.FIT_EPS:
                    key = (min(fw - ww, fh - hh), max(fw - ww, fh - hh), fx, fy)       # best short side fit
                    if best is None or key < best[0]:
                        best = (key, fx, fy, ww, hh, r)
        return best

    def place(self, fx, fy, ww, hh):
        nf = []
        for (x, y, w, h) in self.free:
            if fx >= x + w or fx + ww <= x or fy >= y + h or fy + hh <= y:
                nf.append((x, y, w, h))
                continue
            if fx > x:
                nf.append((x, y, fx - x, h))
            if fx + ww < x + w:
                nf.append((fx + ww, y, x + w - fx - ww, h))
            if fy > y:
                nf.append((x, y, w, fy - y))
            if fy + hh < y + h:
                nf.append((x, fy + hh, w, y + h - fy - hh))
        self.free = [a for i, a in enumerate(nf) if not any(j != i and _inside(a, b) for j, b in enumerate(nf) if (b != a or j < i))]


def _inside(a, b):
    return a[0] >= b[0] - 1e-9 and a[1] >= b[1] - 1e-9 and a[0] + a[2] <= b[0] + b[2] + 1e-9 and a[1] + a[3] <= b[1] + b[3] + 1e-9


def nest_rects(items, stock, rotate, kerf=None):
    """items: list of dict(mark, inst, w, h[, poly]) with w along the stock length. Returns a list of Bin. Tries several orders and keeps the fewest bins."""
    kerf = D.KERF if kerf is None else kerf
    W, H = stock.L, stock.W
    for it in items:
        ok = (it['w'] <= W + D.FIT_EPS and it['h'] <= H + D.FIT_EPS) or (rotate and it['h'] <= W + D.FIT_EPS and it['w'] <= H + D.FIT_EPS)
        if not ok:
            raise StockError('piece %s (%.1f x %.1f mm) does not fit the %s stock (%.1f x %.1f mm)' % (it['mark'], it['w'], it['h'], stock.label, W, H))
    orders = [lambda i: (-i['w'] * i['h'], i['mark']), lambda i: (-max(i['w'], i['h']), -i['h'], i['mark']), lambda i: (-i['h'], -i['w'], i['mark']),
              lambda i: (-i['w'], -i['h'], i['mark'])]
    best = None
    for key in orders:
        bins = _pack(sorted(items, key=key), stock, rotate, kerf)
        score = (len(bins), -max((b.used_area() for b in bins[:-1]), default=0) if len(bins) > 1 else 0, -bins[-1].used_area() if bins else 0)
        if best is None or score < best[0]:
            best = (score, bins)
    return best[1] if best else []


def _pack(items, stock, rotate, kerf):
    bins, rects = [], []
    for it in items:
        done = False
        cand = []
        for bi, rc in enumerate(rects):
            f = rc.find(it['w'], it['h'], rotate)
            if f:
                cand.append((f[0], bi, f))
        if cand:
            cand.sort(key=lambda c: (c[1],))
            _, bi, f = cand[0]
            done = True
        else:
            rects.append(_Rects(stock.L, stock.W, kerf))
            bins.append(Bin(len(bins) + 1, stock))
            bi = len(rects) - 1
            f = rects[bi].find(it['w'], it['h'], rotate)
        _, fx, fy, ww, hh, r = f
        rects[bi].place(fx, fy, ww, hh)
        w, h = (it['h'], it['w']) if r else (it['w'], it['h'])
        bins[bi].placed.append(Placed(it['mark'], it['inst'], fx, fy, w, h, r, it.get('poly'), it.get('grain', 'x')))
    return bins


# ---- sticks -----------------------------------------------------------------------------------------------------------------------------------
def nest_sticks(items, stock, kerf=None, lanes=1):
    """First fit decreasing on sticks of stock.L. items: dict(mark, inst, w, wedge). With lanes=2 (the 3/8 triangular stock) a stick rips into two
    lengths; a wedge takes both lanes of its stick. Returns a list of Bin; Placed.y is the lane (0 or 1), h the lane count the piece uses."""
    kerf = D.KERF if kerf is None else kerf
    L = stock.L
    for it in items:
        if it['w'] > L + D.FIT_EPS:
            raise StockError('piece %s (%.1f mm) is longer than the %s stock (%.1f mm)' % (it['mark'], it['w'], stock.label, L))
    bins, used = [], []                                  # used[bin][lane] = length used
    wedges = sorted([i for i in items if i.get('wedge')], key=lambda i: (-i['w'], i['mark']))
    rest = sorted([i for i in items if not i.get('wedge')], key=lambda i: (-i['w'], i['mark']))
    for it in wedges:
        for bi, u in enumerate(used):
            if lanes == 1 or True:
                x = max(u)
                if x + it['w'] + kerf <= L + kerf + D.FIT_EPS:
                    bins[bi].placed.append(Placed(it['mark'], it['inst'], x, 0, it['w'], lanes))
                    used[bi] = [x + it['w'] + kerf] * lanes
                    break
        else:
            bins.append(Bin(len(bins) + 1, stock))
            used.append([it['w'] + kerf] * lanes)
            bins[-1].placed.append(Placed(it['mark'], it['inst'], 0.0, 0, it['w'], lanes))
    for it in rest:
        for bi, u in enumerate(used):
            lane = min(range(lanes), key=lambda k: u[k]) if False else None
            fits = [k for k in range(lanes) if u[k] + it['w'] + kerf <= L + kerf + D.FIT_EPS]
            if fits:
                k = max(fits, key=lambda k: u[k])        # tightest lane
                bins[bi].placed.append(Placed(it['mark'], it['inst'], u[k], k, it['w'], 1))
                u[k] += it['w'] + kerf
                break
        else:
            bins.append(Bin(len(bins) + 1, stock))
            used.append([0.0] * lanes)
            bins[-1].placed.append(Placed(it['mark'], it['inst'], 0.0, 0, it['w'], 1))
            used[-1][0] = it['w'] + kerf
    return bins


# ---- polygon pairing (G10 blades) -------------------------------------------------------------------------------------------------------------
def _ccw(p):
    s = sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(p, p[1:] + p[:1]))
    return p if s >= 0 else list(reversed(p))


def _offset_convex(poly, d):
    """Convex counter-clockwise polygon grown by d (each edge moved out by d)."""
    n = len(poly)
    lines = []
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        ex, ey = b[0] - a[0], b[1] - a[1]
        L = math.hypot(ex, ey)
        nx, ny = ey / L, -ex / L
        lines.append((nx, ny, nx * a[0] + ny * a[1] + d))
    out = []
    for i in range(n):
        n1, n2 = lines[i - 1], lines[i]
        det = n1[0] * n2[1] - n1[1] * n2[0]
        if abs(det) < 1e-9:
            continue
        out.append(((n1[2] * n2[1] - n2[2] * n1[1]) / det, (n1[0] * n2[2] - n2[0] * n1[2]) / det))
    return out


def _clip(subject, clip):
    """Sutherland-Hodgman: subject clipped to the convex counter-clockwise polygon clip."""
    out = subject
    for i in range(len(clip)):
        a, b = clip[i], clip[(i + 1) % len(clip)]
        inp, out = out, []
        if not inp:
            break
        side = lambda p: (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])
        for j in range(len(inp)):
            p, q = inp[j], inp[(j + 1) % len(inp)]
            sp, sq = side(p), side(q)
            if sp >= 0:
                out.append(p)
            if (sp >= 0) != (sq >= 0):
                t = sp / (sp - sq)
                out.append((p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1])))
    return out


def _area(p):
    return abs(sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(p, p[1:] + p[:1]))) / 2 if len(p) > 2 else 0.0


def pair_polygon(poly, kerf=None, step=6.0):
    """Two copies of a convex polygon, one turned 180 degrees, placed without overlap (kerf apart) so the union's bounding box is small.
    A coarse grid search over the offset, then a pattern search that shrinks the step. Returns (polyA, polyB, w, h), bounding box at the origin."""
    kerf = D.KERF if kerf is None else kerf
    a = _ccw([(float(x), float(y)) for x, y in poly])
    x0, y0 = min(p[0] for p in a), min(p[1] for p in a)
    a = [(x - x0, y - y0) for x, y in a]
    w = max(p[0] for p in a)
    h = max(p[1] for p in a)
    r = [(w - x, h - y) for x, y in a]                       # turned 180 degrees about the box centre
    big = _offset_convex(a, kerf)

    def box(dx, dy):
        return (max(w, w + dx) - min(0.0, dx)) * (max(h, h + dy) - min(0.0, dy))

    def free(dx, dy):
        return _area(_clip([(x + dx, y + dy) for x, y in r], big)) < D.FIT_EPS

    best = None
    n = int(w / step)
    m = int(h / step)
    for i in range(-n, n + 1):
        for j in range(-m, m + 1):
            dx, dy = i * step, j * step
            if (best is None or box(dx, dy) < best[0]) and free(dx, dy):
                best = (box(dx, dy), dx, dy)
    if best is None:
        return a, r, w, 2 * h + kerf
    _, dx, dy = best
    st = step / 2
    while st > 0.05:
        moved = True
        while moved:
            moved = False
            for ex, ey in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
                nx, ny = dx + ex * st, dy + ey * st
                if box(nx, ny) < box(dx, dy) - 1e-9 and free(nx, ny):
                    dx, dy, moved = nx, ny, True
        st /= 2
    ox, oy = min(0.0, dx), min(0.0, dy)
    return [(x - ox, y - oy) for x, y in a], [(x + dx - ox, y + dy - oy) for x, y in r], max(w, w + dx) - min(0.0, dx), max(h, h + dy) - min(0.0, dy)


# ---- the whole table -----------------------------------------------------------------------------------------------------------------------------
class Nest:
    """Result of nesting every stock item. bins[stock key] is a list of Bin; where[(mark, inst)] is (stock key, bin no)."""

    def __init__(self):
        self.bins, self.where, self.notes = {}, {}, {}

    def count(self, key):
        return len(self.bins.get(key, []))


def nest_all(tb):
    res = Nest()
    for key, st in tb.stock.items():
        parts = tb.parts_for(key)
        if not parts:
            continue
        if st.kind == 'sheet':
            items = []
            for p in parts:
                for i in range(1, p.qty + 1):
                    items.append(dict(mark=p.mark, inst=i, w=p.length, h=p.width, grain=p.grain))
            if key == 'g10':
                items = _pair_blades(tb, items)
            bins = nest_rects(items, st, st.rotate)
            for b in bins:
                _fix_polys(b, tb)
        else:
            if st.L is None:
                res.notes[key] = 'stock length is not defined in the model'
                bins = []
                for p in parts:
                    for i in range(1, p.qty + 1):
                        res.where[(p.mark, i)] = (key, 0)
                res.bins[key] = bins
                continue
            items = []
            for p in parts:
                for i in range(1, p.qty + 1):
                    items.append(dict(mark=p.mark, inst=i, w=p.length, wedge=p.wedge))
            bins = nest_sticks(items, st, lanes=st.lanes)
        res.bins[key] = bins
        for b in bins:
            for pl in b.placed:
                res.where[(pl.mark, pl.inst)] = (key, b.no)
                if pl.poly:
                    for mk, inst, _ in pl.poly:
                        res.where[(mk, inst)] = (key, b.no)
    return res


def _pair_blades(tb, items):
    """Replace the blade pieces by one composite item per pair (polygon pairing); an odd one stays a rectangle."""
    bl = [i for i in items if i['mark'].startswith('BL-')]
    rest = [i for i in items if not i['mark'].startswith('BL-')]
    while len(bl) >= 2:
        a, b = bl.pop(0), bl.pop(0)
        sh = tb.templates[a['mark']].shape
        A, B, w, h = pair_polygon(sh.outline)
        rest.append(dict(mark='%s+%s' % (a['mark'], b['mark']), inst=1, w=w, h=h, grain='x', poly=[(a['mark'], a['inst'], A), (b['mark'], b['inst'], B)]))
    return rest + bl


def _fix_polys(b, tb):
    """A rotated pair keeps its polygons in its own frame; move them to the sheet position."""
    for p in b.placed:
        if p.poly:
            p.poly = [(mk, inst, [((x if not p.rot else y) + p.x, (y if not p.rot else x) + p.y) for x, y in poly]) for mk, inst, poly in p.poly]
