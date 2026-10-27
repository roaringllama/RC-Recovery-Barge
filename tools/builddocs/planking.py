"""Planking guide (letter portrait PDF): the sponson section at every frame station at 1:2, with the developed girth split into planks of at most
design.STOCK_W, then tables of plank number against plank width at each station, plank length and stock sheet. Grain runs along the hull.
Section outlines come from geometry.sponson_section, the function behind A-104 and tools/cad.py; plank widths from the same part shapes as the
templates. No instructions: marks, widths and positions only."""
import math
import design as D
from model import geometry as G, schedules as S
from .page import Doc, LINE, esc

SC = D.SECTION_SCALE
WALLS = {'O1': (0, D.AFT_TAPER_X), 'O2': (D.AFT_TAPER_X, G.BOW0), 'O3': (G.BOW0, D.LOA), 'I1': (0, D.AFT_TAPER_X), 'I2': (D.AFT_TAPER_X, D.LOA)}
SIDE = {'O1': 'outer', 'O2': 'outer', 'O3': 'outer', 'I1': 'inner', 'I2': 'inner'}


def extent(poly, x):
    """(lowest y, highest y) of a polygon on the vertical line at x, or None when x is outside it."""
    ys = []
    n = len(poly)
    for i in range(n):
        (ax, ay), (bx, by) = poly[i], poly[(i + 1) % n]
        if min(ax, bx) - D.FIT_EPS <= x <= max(ax, bx) + D.FIT_EPS:
            if abs(bx - ax) < D.FIT_EPS:
                ys += [ay, by]
            else:
                ys.append(ay + (by - ay) * (x - ax) / (bx - ax))
    return (min(ys), max(ys)) if ys else None


def planks_of(tb, mark):
    t = tb.templates[mark]
    sh = t.shape
    return sh.planks if sh.planks else [sh.outline]


def width_at(tb, mark, k, X):
    """Width of plank k (0 = lowest or aftmost slab) of panel `mark` at plan station X, or None when the panel does not reach X."""
    pk = planks_of(tb, mark)[k]
    sh = tb.templates[mark].shape
    if mark in WALLS:
        xa, xb = WALLS[mark]
        if not (xa - D.FIT_EPS <= X <= xb + D.FIT_EPS):
            return None
        L = sh.size()[0]
        u = (X - xa) / (xb - xa) * L
    elif mark == 'TK':
        xa, xb = G.trunk_x()
        if not (xa - D.FIT_EPS <= X <= xb + D.FIT_EPS):
            return None
        u = X - xa
    else:
        u = X
    e = extent(pk, u)
    return None if e is None else e[1] - e[0]


def piece_sheets(tb, nest, mark, inst):
    """Stock sheet number of the cut piece(s) of this panel: {plank mark: sheet} for instance inst."""
    out = {}
    for p in tb.parts:
        if (p.template or p.mark) == mark:
            w = nest.where.get((p.mark, min(inst, p.qty)))
            out[p.mark] = w[1] if w else None
    return out


def stations(zd):
    return [(f['num'], f['x']) for f in S.frames(zd)]


# ---- section drawing -------------------------------------------------------------------------------------------------------------------------
def draw_section(pg, tb, X, zd, cx, y_floor, label):
    """Both sponsons and the tunnel at station X, looking forward (port on the left), 1:2. y_floor is the page y of Z = 0. Returns the lowest page y used."""
    D_ = zd(X)
    ys = lambda Y: cx - SC * Y
    zs = lambda Z: y_floor - SC * Z
    low = y_floor
    T = D.SKIN_T
    for sg in (1, -1):
        pts = G.sponson_section(X, D_)
        pg.poly([(ys(sg * y), zs(z)) for y, z in pts], 'tpl', 'style="fill:#fbf6e9"')
        low = max(low, max(zs(z) for _, z in pts))
        pg.poly([(ys(sg * y), zs(z)) for y, z in G.hull_section(X, D_, T)], 'guide', 'style="fill:none"')
        side = 'port' if sg > 0 else 'starboard'
        yi, yo = float(G.inner_wall_y(X)), float(G.outer_wall_y(X))
        for wall, y, anchor in (('inner', yi, -1), ('outer', yo, 1)):
            marks = [m for m, (xa, xb) in WALLS.items() if SIDE[m] == wall and xa - D.FIT_EPS <= X <= xb + D.FIT_EPS]
            m = marks[-1] if X > WALLS[marks[0]][0] + D.FIT_EPS or len(marks) == 1 else marks[0]
            if X >= D.LOA - D.FIT_EPS:
                m = marks[-1]
            n = len(planks_of(tb, m))
            z = T
            for k in range(n):
                w = width_at(tb, m, k, X)
                if w is None:
                    break
                z0, z1 = z, z + w
                if k:
                    pg.line(ys(sg * y) - 1.6 * anchor * -1 if False else ys(sg * y) - 1.6, zs(z0), ys(sg * y) + 1.6, zs(z0), 'thk')
                tx = ys(sg * y) + (3.0 if (anchor * sg) < 0 else -3.0)
                pg.text(tx, zs((z0 + z1) / 2) + 0.9, '%s.%d' % (m, k + 1), 'ts', 'start' if (anchor * sg) < 0 else 'end')
                z = z1
        yc = (yi + yo) / 2
        pg.text(ys(sg * yc), low + 4.5 if False else zs(0) + 4.5, 'BT', 'ts', 'middle')
        pg.text(ys(sg * yc), zs(D_) - 1.5, 'DK', 'ts', 'middle')
    # tunnel roof plate and centre deck, between the inner walls
    yin = G.HT + float(G.inner_off(X))
    for z0, z1, nm in ((D.ROOF_Z0, G.ROOF_Z1, 'RP'), (D_ - T, D_, 'DC')):
        pg.rect(ys(yin), zs(z1), 2 * yin * SC, (z1 - z0) * SC, 'tpl', 'style="fill:#ddd"')
        pg.text(cx, zs(z1) - 1.0 if nm == 'DC' else zs(z1) + 4.5 + (z1 - z0) * SC, nm, 'ts', 'middle')
    pg.line(cx, zs(0) + 2, cx, zs(D_) - 5, 'axis')
    return low


def section_pages(doc, tb, nest, zd):
    sts = stations(zd)
    blocks = []
    for num, X in sts:
        skeg = G.skeg_fillet(X) or G.skeg_depth(X) > 0
        depth = (G.skeg_depth(X) if skeg else 0.0)
        blocks.append((num, X, zd(X), depth))
    # greedy page packing
    pages, cur, used = [], [], 0.0
    pg0 = doc.page('probe')
    doc.pages.pop()
    wx, wy, ww, wh = pg0.window()
    for b in blocks:
        h = (b[2] + b[3]) * SC + 32
        if used + h > wh and cur:
            pages.append(cur)
            cur, used = [], 0.0
        cur.append((b, h))
        used += h
    pages.append(cur)
    for grp in pages:
        pg = doc.page('Sections at the frame stations', 'sponson sections, 1:2, looking forward')
        wx, wy, ww, wh = pg.window()
        y = wy
        for (num, X, dz, depth), h in grp:
            cx = wx + ww / 2
            pg.text(wx, y + 5, 'F%d at X %.1f' % (num, X), 'big')
            pg.text(wx + 60, y + 5, 'deck top Z %.2f; sponson width %.2f; hull walls %.1f apart at the inner faces, bilge radius %.1f' % (
                dz, G.sponson_width(X), 2 * (G.HT + float(G.inner_off(X))), G.bilge_r(X)), 't')
            low = draw_section(pg, tb, X, zd, cx, y + 14 + dz * SC, 'F%d' % num)
            girth = _girth(X, dz)
            pg.text(wx, y + h - 3, 'developed girth of one sponson skin (inner deck edge, inner wall, floor with both bilge rounds, outer wall, outer deck edge): %.1f mm; '
                    'plank widths in the tables' % girth, 'ts')
            y += h
        pg.scale_footer()
    return len(pages)


def _girth(X, D_):
    pts = G.sponson_section(X, D_)
    return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:]))


# ---- tables -------------------------------------------------------------------------------------------------------------------------------------
HULL = ['O1', 'O2', 'O3', 'I1', 'I2', 'TP', 'TR', 'BT', 'DK', 'TK']
CENTER = ['RP', 'DC']


def table_page(doc, tb, nest, zd, title, marks, inst):
    pg = doc.page(title, 'plank width at each frame station, mm; length along the grain; stock sheet from the nesting')
    sts = stations(zd)
    wx, wy, ww, wh = pg.window()
    cw = 12.5
    x_mark, x_st0 = wx, wx + 26
    x_len = x_st0 + cw * len(sts)
    x_max, x_sheet = x_len + 14, x_len + 28
    y = wy + 4
    pg.text(x_mark, y, 'plank', 'bold')
    for i, (num, X) in enumerate(sts):
        pg.text(x_st0 + cw * i + cw - 1, y - 3.5, 'F%d' % num, 'bold', 'end')
        pg.text(x_st0 + cw * i + cw - 1, y, '%.0f' % X, 'ts', 'end')
    pg.text(x_len + 12, y, 'length', 'bold', 'end')
    pg.text(x_max + 12, y, 'max w', 'bold', 'end')
    pg.text(x_sheet, y, 'stock sheet', 'bold')
    pg.line(wx, y + 1.5, wx + ww, y + 1.5, 'thin')
    y += LINE + 1
    for mk in marks:
        if mk not in tb.templates:
            continue
        n = len(planks_of(tb, mk))
        sheets = piece_sheets(tb, nest, mk, inst)
        for k in range(n):
            pm = mk if n == 1 else '%s.%d' % (mk, k + 1)
            pg.text(x_mark, y, pm, 'bold')
            mx = 0.0
            for i, (num, X) in enumerate(sts):
                w = width_at(tb, mk, k, X)
                if w is not None:
                    mx = max(mx, w)
                    pg.text(x_st0 + cw * i + cw - 1, y, '%.1f' % w, 't', 'end')
                else:
                    pg.text(x_st0 + cw * i + cw - 1, y, '-', 'ts', 'end')
            pk = planks_of(tb, mk)[k]
            xs = [p[0] for p in pk]
            ys_ = [p[1] for p in pk]
            L = (max(xs) - min(xs)) if tb.templates[mk].shape.grain == 'x' else (max(ys_) - min(ys_))
            W = (max(ys_) - min(ys_)) if tb.templates[mk].shape.grain == 'x' else (max(xs) - min(xs))
            pg.text(x_len + 12, y, '%.1f' % L, 't', 'end')
            pg.text(x_max + 12, y, '%.1f' % W, 't', 'end')
            sh = sheets.get(pm)
            pg.text(x_sheet, y, 'sheet %s' % sh if sh else '-', 't')
            y += LINE
        y += LINE / 3
    y += 3
    for ln in ['Plank 1 is the lowest (walls) or the aftmost slab; widths are measured across the grain at the station, so a tapering plank shows a different width at each station. '
               'Every plank is at most %.1f mm wide (the stock width); grain runs along the hull. Instance %d of a pair is %s.' % (D.STOCK_W, inst, 'the port piece' if inst == 1 else 'the starboard piece')]:
        from .page import wrap
        for w in wrap(ln, ww):
            pg.text(wx, y, w, 't')
            y += LINE
    pg.scale_footer()


def build(tb, nest, zd):
    doc = Doc('Planking guide', D.LETTER_IN)
    section_pages(doc, tb, nest, zd)
    table_page(doc, tb, nest, zd, 'Planking table, port sponson', HULL, 1)
    table_page(doc, tb, nest, zd, 'Planking table, starboard sponson', HULL, 2)
    table_page(doc, tb, nest, zd, 'Planking table, tunnel plates', CENTER, 1)
    return doc
