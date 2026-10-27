"""Building board layout: the side view of the boat on the keel datum, every line from the model. Frame stations (marks and X), the deck slope, blade hinge
centre, nozzle post centres, CV joint and the motor axis, skeg and shoe outline, the waterline at the design battery position, datum marks at the
transom (X 0) and the bow (X LOA). Drawn at design.BOARD_SCALE on 11 x 17 in sheets (as many sheets as the length needs, with a match line), and
full size on tiled letter pages with registration crosses. Positions only."""
import math
import design as D
from model import geometry as G, schedules as S
from .page import Doc, LINE, esc
from . import templates as T

PAD_X = 12.0           # board mm beyond the first and last feature
PAD_Z = 16.0
OVERLAP = 20.0         # board mm shared by neighbouring 1:2 sheets


def items(r):
    """Primitives in board coordinates (X forward from the transom, Z up from the keel datum): dict(kind, ...)."""
    zd = r['deck']
    out = []
    L = lambda p, q, cls, text='', at=0.5, dx=0.0, dy=0.0, anchor='start': out.append(dict(kind='line', p=p, q=q, cls=cls, text=text, at=at, dx=dx, dy=dy, anchor=anchor))
    P = lambda pts, cls, text='', fill=None: out.append(dict(kind='poly', pts=pts, cls=cls, text=text, fill=fill))
    X = lambda c, cls='thin': out.append(dict(kind='cross', c=c, cls=cls))
    TX = lambda c, text, cls='t', anchor='start', rot=0, dx=0.0, dy=0.0: out.append(dict(kind='text', c=c, text=text, cls=cls, anchor=anchor, rot=rot, dx=dx, dy=dy))
    C = lambda c, rad, cls='thin': out.append(dict(kind='circle', c=c, r=rad, cls=cls))
    x_lo = min(-D.AFT_DECK_L, G.SHOE_X1, G.POSTX - D.NOZ_L) - PAD_X
    x_hi = G.BUMPER_X0 + D.BUMPER_T + PAD_X
    hz = G.housing(zd)
    z_lo = min(G.SHOE_BOT, D.PROP_Z - D.NOZ_OD / 2) - PAD_Z
    z_hi = max(hz['ztop'] if hz else zd(D.LOA), G.bumper_z1(zd), zd(D.LOA)) + PAD_Z * 2
    # keel datum
    L((x_lo, 0.0), (x_hi, 0.0), 'axis', 'keel datum, Z 0', 0.02, 0, -1.2)
    # hull profile: transom, bottom, bow, deck
    xs = [D.LOA * i / 20 for i in range(21)]
    deck = [(x, zd(x)) for x in xs]
    P([(0.0, 0.0), (D.LOA, 0.0), (D.LOA, zd(D.LOA))] + list(reversed(deck)), 'tpl')
    slope = math.degrees(math.atan2(zd(D.LOA) - zd(0.0), D.LOA))
    TX((D.LOA * 0.62, zd(D.LOA * 0.62)), 'deck top: Z %.2f at X 0 to Z %.2f at X %.0f, %.3f deg' % (zd(0.0), zd(D.LOA), D.LOA, slope), 't', 'middle', 0, 0, -12.0)
    out.append(dict(kind='polyline', pts=deck, cls='thk'))
    # skeg and shoe
    P([(0.0, 0.0), (0.0, G.SHOE_BOT), (G.SKEG_X0, 0.0)], 'guide', 'skeg outline (side view), X 0 to %.1f, depth %.2f at the transom' % (G.SKEG_X0, -G.SHOE_BOT))
    P([(G.SHOE_X1, G.SHOE_BOT), (0.0, G.SHOE_BOT), (0.0, G.SHOE_BOT + D.SHOE_T), (G.SHOE_X1, G.SHOE_BOT + D.SHOE_T)], 'guide', 'shoe, X %.0f to 0' % G.SHOE_X1)
    # frame stations
    for f in S.frames(zd):
        x = f['x']
        L((x, z_lo + PAD_Z / 2), (x, zd(x) + PAD_Z / 2), 'guide')
        TX((x, zd(x) + PAD_Z / 2), 'F%d' % f['num'], 'bold', 'middle', 0, 0, -1.0)
        TX((x, z_lo + PAD_Z / 2), 'X %.1f' % x, 'ts', 'middle', 0, 0, -1.0)
    # datum marks
    for x, nm in ((0.0, 'X 0, transom datum'), (D.LOA, 'X %.0f, bow datum' % D.LOA)):
        L((x, z_lo), (x, z_hi - PAD_Z), 'thk')
        TX((x, z_hi - PAD_Z), nm, 'bold', 'middle', 0, 0, -1.5)
    # hatches along the deck (positions), blade trunk
    for i, h in enumerate(sorted(S.hatches(zd), key=lambda h: h['x0'])):
        if h['x0'] < 0:
            continue
        zz = zd((h['x0'] + h['x1']) / 2) + 5 + 7 * (i % 2) * 2
        L((h['x0'], zz), (h['x1'], zz), 'thk', 'hatch %s, X %.0f to %.0f' % (h['name'], h['x0'], h['x1']), 0.5, 0, -1.2, 'middle')
    t0, t1 = G.trunk_x()
    L((t0, -4.0), (t1, -4.0), 'thk', 'blade trunk, X %.0f to %.0f' % (t0, t1), 0.5, 0, 4.0, 'middle')
    # bow cap profile
    if hz and hz['kind'] == 'cap':
        P([(hz['x0'], zd(hz['x0'])), (hz['x0'], hz['ztop']), (hz['x1'], hz['ztop']), (hz['x1'], zd(hz['x1']))], 'guide', 'bow cap, X %.1f to %.1f, top Z %.1f' % (hz['x0'], hz['x1'], hz['ztop']))
    # push bar
    P([(G.BUMPER_X0, G.bumper_z0(zd)), (G.BUMPER_X0 + D.BUMPER_T, G.bumper_z0(zd)), (G.BUMPER_X0 + D.BUMPER_T, G.bumper_z1(zd)), (G.BUMPER_X0, G.bumper_z1(zd))], 'tpl',
      'push bar, X %.0f to %.0f' % (G.BUMPER_X0, G.BUMPER_X0 + D.BUMPER_T))
    # aft deck box
    ab = G.aft_box()
    P([(-D.AFT_DECK_L, zd(0.0) - D.AFT_DECK_DEPTH), (0.0, zd(0.0) - D.AFT_DECK_DEPTH), (0.0, zd(0.0)), (-D.AFT_DECK_L, zd(0.0))], 'tpl', 'aft deck box, X %.1f to 0' % -D.AFT_DECK_L)
    # nozzle and post centre
    nz0, nz1 = -(D.NOZ_X0 + D.NOZ_L), -D.NOZ_X0
    P([(nz0, D.PROP_Z - D.NOZ_OD / 2), (nz1, D.PROP_Z - D.NOZ_OD / 2), (nz1, D.PROP_Z + D.NOZ_OD / 2), (nz0, D.PROP_Z + D.NOZ_OD / 2)], 'guide', 'nozzle, X %.0f to %.0f' % (nz0, nz1))
    L((G.POSTX, D.PROP_Z - D.NOZ_OD / 2 - 6), (G.POSTX, zd(0.0)), 'axis', 'nozzle post centre, X %.1f' % G.POSTX, 0.2, -2.0, 0.0, 'end')
    X((G.POSTX, D.PROP_Z), 'thin')
    # CV joint and motor axis
    xa = G.POSTX - D.NOZ_OD / 2
    xb = G.MOT_X0 + D.MOTOR_L * math.cos(G.AXIS)
    L((xa, G.shaft_z(xa)), (xb, G.shaft_z(xb)), 'axis', 'shaft and motor axis, %.1f deg to the keel datum' % D.MOTOR_AXIS_DEG, 0.6, 0.0, 6.0, 'start')
    X((D.CV_X, D.PROP_Z), 'thin')
    C((D.CV_X, D.PROP_Z), 3.0)
    TX((D.CV_X, D.PROP_Z), 'CV joint, X %.0f, Z %.0f' % (D.CV_X, D.PROP_Z), 't', 'start', 0, 5.0, 5.0)
    # blade hinge centre
    b = G.blade_params()
    X((b['hinge_x'], b['hinge_z']), 'thin')
    C((b['hinge_x'], b['hinge_z']), 3.0)
    TX((b['hinge_x'], b['hinge_z']), 'blade hinge centre, X %.0f, Z %.0f' % (b['hinge_x'], b['hinge_z']), 't', 'start', 0, 5.0, 5.0)
    # waterline at the design battery position (trim from the hydrostatics)
    wl = lambda x: r['d0'] - r['k'] * x
    L((x_lo, wl(x_lo)), (x_hi, wl(x_hi)), 'wl', 'waterline, batteries at X %.0f: Z %.2f at X 0, %.2f at X %.0f' % (D.DESIGN_BAT_X, wl(0.0), wl(D.LOA), D.LOA), 0.97, 0.0, -1.2, 'end')
    return out, (x_lo, x_hi, z_lo, z_hi)


CLS = {'tpl': 'tpl', 'thk': 'tpl', 'thin': 'thin', 'guide': 'guide', 'axis': 'axis', 'wl': 'wl', 'bold': 'bold', 't': 't', 'ts': 'ts'}


def paint(pg, its, tf, sc, clip=None):
    """Draw primitives. tf(x, z) -> page (x, y). Text offsets dx, dy are page mm."""
    for it in its:
        k = it['kind']
        if k == 'line':
            a, b = tf(*it['p']), tf(*it['q'])
            pg.line(a[0], a[1], b[0], b[1], CLS.get(it['cls'], it['cls']))
            if it['text']:
                px = a[0] + (b[0] - a[0]) * it['at'] + it['dx']
                py = a[1] + (b[1] - a[1]) * it['at'] + it['dy']
                pg.text(px, py, it['text'], 'ts', it['anchor'])
        elif k == 'polyline':
            pg.pline([tf(*p) for p in it['pts']], CLS.get(it['cls'], 'tpl'))
        elif k == 'poly':
            pts = [tf(*p) for p in it['pts']]
            pg.poly(pts, CLS.get(it['cls'], 'tpl'), 'style="fill:none"')
            if it['text']:
                pg.text(min(p[0] for p in pts) + 1.0, min(p[1] for p in pts) - 1.2, it['text'], 'ts')
        elif k == 'cross':
            c = tf(*it['c'])
            pg.line(c[0] - 3, c[1], c[0] + 3, c[1], 'thin')
            pg.line(c[0], c[1] - 3, c[0], c[1] + 3, 'thin')
        elif k == 'circle':
            c = tf(*it['c'])
            pg.circ(c[0], c[1], it['r'] * sc, 'thin')
        elif k == 'text':
            c = tf(*it['c'])
            pg.text(c[0] + it['dx'], c[1] + it['dy'], it['text'], CLS.get(it['cls'], 't'), it['anchor'], it['rot'])


def half_scale_doc(r):
    """The 11 x 17 in sheets at design.BOARD_SCALE. A page whose width cannot take the whole board takes a part, with a match line."""
    its, (x_lo, x_hi, z_lo, z_hi) = items(r)
    sc = D.BOARD_SCALE
    doc = Doc('Building board layout', D.TABLOID_IN)
    m = D.PAGE_MARGIN
    W, H = doc.size_mm
    cap = (W - 2 * m) / sc                                  # board mm one sheet shows
    total = x_hi - x_lo
    n = 1 if total <= cap else math.ceil((total - OVERLAP) / (cap - OVERLAP))
    span = (total + (n - 1) * OVERLAP) / n
    top = m + 16
    for i in range(n):
        xa = x_lo + i * (span - OVERLAP)
        xb = xa + span
        pg = doc.page('Building board, sheet %d of %d' % (i + 1, n), 'scale 1:%.0f, X %.0f to %.0f%s' % (1 / sc, xa, xb, '' if n == 1 else ', overlap with the next sheet %.0f mm' % OVERLAP))
        x0 = m + (W - 2 * m - span * sc) / 2
        zt = top + 8
        tf = lambda x, z, x0=x0, xa=xa: (x0 + (x - xa) * sc, zt + (z_hi - z) * sc)
        pg.clip_begin(x0, top, span * sc, (z_hi - z_lo) * sc + 12)
        paint(pg, its, tf, sc)
        pg.clip_end()
        pg.rect(x0, top, span * sc, (z_hi - z_lo) * sc + 12, 'edge')
        if n > 1:
            for xm, nm in (((xa + span - OVERLAP) if i < n - 1 else None, 'continues on sheet %d' % (i + 2)), ((xa if i else None), 'continued from sheet %d' % i)):
                if xm is not None:
                    pg.line(x0 + (xm - xa) * sc, top, x0 + (xm - xa) * sc, top + (z_hi - z_lo) * sc + 12, 'seam')
                    pg.text(x0 + (xm - xa) * sc + 1, top + 4, 'match line X %.0f, %s' % (xm, nm), 'ts')
        # a 1:2 scale bar
        bx, by = x0, zt + (z_hi - z_lo) * sc + 16
        L = D.SCALE_BAR * sc
        pg.line(bx, by, bx + L, by, 'tpl')
        for t in range(int(D.SCALE_BAR // 10) + 1):
            pg.line(bx + t * 10 * sc, by - 1.5, bx + t * 10 * sc, by + 1.5, 'tpl')
        pg.text(bx, by + 6, 'board scale bar: %.0f board mm (%.0f mm on this sheet at 1:%.0f)' % (D.SCALE_BAR, L, 1 / sc), 'ts')
    return doc


def full_size_doc(r):
    """Full size tiled letter pages of the same drawing."""
    its, (x_lo, x_hi, z_lo, z_hi) = items(r)
    doc = Doc('Building board layout, full size, print at 100 percent', D.LETTER_IN)
    ww, wh = T.window_size(doc)[2:]
    w, h = x_hi - x_lo, z_hi - z_lo
    pad_l, pad_t, pad_r, pad_b = T.TILE_PAD_L, T.TILE_PAD, T.TILE_PAD, T.TILE_PAD
    totw, toth = w + pad_l + pad_r, h + pad_t + pad_b
    cols, rows = T.tile_grid(totw, toth, ww, wh, D.TILE_OVERLAP)
    sx, sy = ww - D.TILE_OVERLAP, wh - D.TILE_OVERLAP
    n = cols * rows
    for r_ in range(rows):
        for c in range(cols):
            k = r_ * cols + c + 1
            pg = doc.page('Building board sheet %d of %d (row %d, col %d)' % (k, n, r_ + 1, c + 1), 'full size, X %.0f to %.0f' % (x_lo + c * sx - pad_l, x_lo + c * sx - pad_l + ww))
            wx, wy, _, _ = pg.window()
            wl = c * sx
            wtop = toth - r_ * sy
            # world (page-independent): u = x - x_lo + pad_l, v = z - z_lo + pad_b  (v up)
            tf = lambda x, z, wx=wx, wy=wy, wl=wl, wtop=wtop: (wx + (x - x_lo + pad_l - wl), wy + (wtop - (z - z_lo + pad_b)))
            pg.clip_begin(wx, wy, ww, wh)
            paint(pg, its, tf, 1.0)
            pg.clip_end()
            T.overlap_marks(pg, wx, wy, ww, wh, r_, c, rows, cols, k)
            T.registration(pg, wx, wy, ww, wh, r_, c)
            it = dict(cols=cols, rows=rows)
            pg.scale_footer(lambda p, x, y, w_, h_, it=it, r_=r_, c=c: T.tile_map(p, x, y, w_, h_, it, r_, c))
    return doc
