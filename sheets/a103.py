"""A-103 Panel and planking schedule: plan, wall elevation, frame stations and the panel table, every number from the model."""
import math
from .lib import *
from .wtbl import wtable
from .tbl import para
import design as D
from model import geometry as G, hydro, schedules as S


def build(r=None):
    r = r or hydro.design()
    zd = r['deck']
    T = D.SKIN_T
    pl = S.panels(zd)
    sh = Sheet('A-103', 'Panel and planking schedule',
               'Hull is %.3f mm (1/8 in) balsa planked over frames. Port sponson plan, outer wall elevation, stations, every panel length, angle and thickness.' % T, '1:3')
    s = 1 / 3
    ox = 22
    xs = lambda X: ox + s * (D.LOA - X)
    oy = 74
    ys = lambda Y: oy - s * (Y - G.HT)
    P = lambda pts: [(xs(x), ys(y)) for x, y in pts]
    sh.text(14, 33, 'PORT SPONSON PLAN (bow at left). Starboard is the mirror. Skin %.3f; frames F1 to F%d dashed (solid frames heavy).' % (T, len(D.FRAME_X)), 'tb')
    sh.poly(P(S.POLY), 'obj', 'style="fill:#fff"')
    sh.pline(P([(x, y - T) for x, y in S.OUTER]), 'thin')
    sh.pline(P([(x, y + T) for x, y in S.INNER]), 'thin')
    fk = {f['x']: f['kind'] for f in S.frames(zd)}
    for i, fx in enumerate(D.FRAME_X, 1):
        a, b = float(G.inner_wall_y(fx)), float(G.outer_wall_y(fx))
        sh.line(xs(fx), ys(a) + 1, xs(fx), ys(b) - 1, 'thk' if fk[fx] != 'ring' else 'hid')
        sh.text(xs(fx), ys(b) - 2.0 - (i % 2) * 2.6, 'F%d' % i, 'ts', 'middle')
    sh.rect(xs(G.SKEG_X0), ys(G.YS + D.SKEG_W / 2), G.SKEG_X0 * s, D.SKEG_W * s, 'hid')
    sh.text(xs(G.SKEG_X0 / 2), ys(G.HT) + 6.8, 'dashed: skeg box below, %.2f wide, X %.1f to %.1f' % (D.SKEG_W, G.SKEG_X0, G.SHOE_X1), 'ts', 'middle')
    # station dimensions along the inner wall
    yd = ys(G.HT) + 11
    pts = [D.LOA, G.BOW0, D.AFT_TAPER_X, 0.0]
    for a, b in zip(pts, pts[1:]):
        sh.dimh(xs(a), xs(b), yd, '%.2f' % (a - b), ys(G.HT) + 1, ys(G.HT) + 1)
    # segment lengths and turn angles
    for (mark, a, b) in (('O1', S.OUTER[0], S.OUTER[1]), ('O2', S.OUTER[1], S.OUTER[2]), ('O3', S.OUTER[2], S.OUTER[3])):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        sh.text(xs((a[0] + b[0]) / 2), ys((a[1] + b[1]) / 2) - 8.4, '%s %.2f' % (mark, L), 'tb', 'middle')
    for (mark, a, b) in (('I1', S.INNER[0], S.INNER[1]), ('I2', S.INNER[1], S.INNER[2])):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        sh.text(xs((a[0] + b[0]) / 2), ys((a[1] + b[1]) / 2) + 4.6, '%s %.2f' % (mark, L), 'tb', 'middle')
    tn = S.turns()
    sh.text(xs(G.BOW0), ys(G.HT + D.SPONSON_W) - 4.6, '%.2f deg' % tn[2][2], 'ts', 'middle')
    sh.text(xs(D.AFT_TAPER_X), ys(G.HT + D.SPONSON_W) - 4.6, '%.2f deg' % tn[1][2], 'ts', 'middle')
    sh.dimv(ys(G.HT + float(G.outer_off(D.LOA))), ys(G.HT), xs(D.LOA) - 5, '%.2f tip' % D.TIP_W, xs(D.LOA), xs(D.LOA))
    sh.dimv(ys(G.HT + float(G.outer_off(0))), ys(G.HT + float(G.inner_off(0))), xs(0) + 5, '%.2f' % D.AFT_W, xs(0), xs(0))
    sh.dimv(ys(G.HT + D.SPONSON_W), ys(G.HT), xs(D.AFT_TAPER_X) - 4, '%.2f' % D.SPONSON_W, xs(D.AFT_TAPER_X), xs(D.AFT_TAPER_X))
    # ---- outer wall elevation, unrolled along X
    oy2 = 122
    zs = lambda Z: oy2 - s * Z
    sh.text(14, 89, 'OUTER WALL ELEVATION (bow at left, projected on X). Top edge follows the deck underside; wall height = deck height at X less 2 x %.3f.' % T, 'tb')
    sh.line(xs(0) + 4, zs(0), xs(D.LOA) - 4, zs(0), 'thin')
    sh.poly([(xs(D.LOA), zs(T)), (xs(0), zs(T)), (xs(0), zs(zd(0) - T)), (xs(D.LOA), zs(zd(D.LOA) - T))], 'obj', 'style="fill:#fff"')
    sh.line(xs(0), zs(0), xs(0), zs(T), 'thin')
    for x in [0.0] + list(D.FRAME_X) + [D.LOA]:
        sh.line(xs(x), zs(T), xs(x), zs(zd(x) - T), 'hid')
    sh.pline([(xs(D.LOA), zs((zd(D.LOA) + 0) / 2)), (xs(0), zs(zd(0) / 2))], 'hid')
    sh.text(xs(D.LOA / 2), zs(zd(D.LOA / 2) / 2) - 1, 'plank seam %d of %d (O planks %.2f to %.2f wide)' % (1, 2, next(p for p in pl if p['mark'] == 'O1')['plank_w0'], next(p for p in pl if p['mark'] == 'O3')['plank_w1']), 'ts', 'middle')
    for x in (0.0, D.AFT_TAPER_X, G.BOW0, D.LOA):
        h = zd(x) - 2 * T
        off = -6 if x > 0 else 6
        sh.dimv(zs(zd(x) - T), zs(T), xs(x) + (off if x == 0 else -off), '%.2f' % h, xs(x), xs(x))
    sh.text(xs(D.LOA / 2), zs(0) + 7, 'deck rises %.2f deg toward the bow relative to the keel line (deck parallel to the waterline); wall tops are planed to it' % abs(math.degrees(math.atan(r['k']))), 't', 'middle')
    # ---- stations table (right)
    X0 = 300
    st = S.stations(zd)
    rows = [('%.1f' % q['x'], q['label'], '%.2f' % q['w_out'], '%.2f' % q['w_in'], '%.2f' % q['deck'], '%.2f' % q['wall'], '%.2f' % q['tun_w'], '%.2f' % q['tun_h']) for q in st]
    cols = [('X', 9), ('FRAME', 35), ('SPONSON', 14), ('INSIDE', 12), ('DECK Z', 12), ('WALL H', 12), ('TUN W', 11), ('TUN H', 11)]
    y = wtable(sh, X0, 38, cols, rows, 'STATIONS: transom, frames F1 to F%d, tip' % len(D.FRAME_X), step=3.0, pad=0.8)
    y += 5
    notes = ['Sponson = outside width. Inside = less 2 skins. Wall H = deck Z less 2 x %.3f (the wall stands on the bottom and carries the deck).' % T,
             'TUN W = tunnel width, the distance between the two inner wall faces; TUN H = deck underside above the roof plate top (Z %.2f). FRAME gives the kind of each sponson piece (A-502): ring, solid, solid with the shaft hole, solid with the trunk notch, or bulkhead.' % G.ROOF_Z1,
             'Turn angles: aft taper %.2f deg per wall, bow %.2f deg, tip outer %.2f deg, tip inner %.2f deg, transom corners %.2f deg. Joints in A-501.' % (S.aft_taper_deg(), S.bow_taper_deg(), tn[3][2], tn[4][2], tn[0][2]),
             'Planks run along the long side of each panel; sheet stock %.1f wide (STOCK_W, ASSUMED); seams are backed (J5) and kept off hatch edges.' % D.STOCK_W]
    notes.append('Hull skin by this schedule %.0f cm2 (%.4f m2); the weight model (A-601) strips give %.0f cm2. Hatch openings are not deducted.' % (S.hull_area_total(pl) / 100, S.hull_area_total(pl) / 1e6, r['area'] / 100))
    for t in notes:
        y = para(sh, X0, y, t, 96, 'ts', 3.3, 2)
        y += 0.8
    # ---- panel table
    rows, fills = [], []
    for p in pl:
        sk = p['kind'] == 'triangle'
        dims = '%.2f' % p['length']
        w0 = '%.2f' % p['h0'] if not sk else '%.2f (at transom)' % p['h0']
        w1 = '%.2f' % p['h1'] if not sk else '0 (at the point)'
        pk = '%d x %.1f to %.1f' % (p['planks'], p['plank_w0'], p['plank_w1']) if p['planks'] > 1 else '1 piece'
        rows.append((p['mark'], p['name'], str(p['qty']), dims, w0, w1, '%.3f' % p['t'], '%.1f' % (p['area'] / 100), pk, p['note']))
        fills.append('#f4f0e6' if p['where'] in ('trunk', 'cap') else None)
    cols = [('MARK', 11), ('PANEL', 40), ('QTY', 8), ('LENGTH', 17), ('H OR W AFT', 24), ('H OR W FWD', 24), ('THICK', 13), ('AREA CM2', 17), ('PLANKS', 32), ('ANGLE AND NOTE', 222)]
    y0 = 137
    y = wtable(sh, 14, y0, cols, rows, None, step=2.9, pad=0.7, fills=fills)
    sh.text(14, y + 3.8, 'PANEL SCHEDULE. Lengths are along the outer face; heights and widths at the two ends (trapezoids). Shaded rows are the trunk and the bow cap (carried as lumps in A-601). QTY counts both sponsons. Thickness: skin %.3f, aft deck skins %.3f, shoe %.2f, push bar %.0f. Deck plan: %s (AD and AB are the two skins of the aft deck box; beams and brackets are on A-502).' % (T, D.AFT_DECK_T, D.SHOE_T, D.BUMPER_T, G.deck_plan()), 't')
    return sh
