"""Interference and fit checks. Each check takes the design hydro result and returns (name, pass_bool, message).

Checks 1 to 10 are the required set. 9b and 11 to 18 are additions. Check 6 is a warning, not a failure.
Nothing here alters a design value; failures are reported only.
"""
import math
from collections import namedtuple
import design as D
from . import geometry as G
from . import hydro

WARN_ONLY = ('6',)


def _under(r, X):
    """Deck underside Z at station X."""
    return r['deck'](X) - D.SKIN_T


def _bat_positions():
    """Battery center X positions to test: both ends of the slide, the design position and the alternates, each once."""
    return sorted({*D.BAT_SLIDE, D.DESIGN_BAT_X, *D.ALT_BAT_X})


def _deck_gap(r, x0, x1, ztop):
    """Smallest deck underside clearance above a flat top at Z=ztop over X x0..x1 (the deck is straight, so the ends decide)."""
    lo = min(_under(r, x0), _under(r, x1))
    return lo - ztop


def c1(r):
    xs = [G.MOT_XMIN + (G.MOT_XMAX - G.MOT_XMIN) * i / D.BLADE_ARC_PTS for i in range(D.BLADE_ARC_PTS + 1)]
    worst = min(xs, key=lambda x: G.sponson_width(x) - 2 * D.SKIN_T - G.BODY_D)
    inner = G.sponson_width(worst) - 2 * D.SKIN_T
    ok = inner >= G.BODY_D
    return ('1 Motor width inside the sponson', ok,
            'body %.1f (%s) vs interior %.1f at X %.1f (motor spans X %.1f to %.1f); margin %.1f' % (
                G.BODY_D, 'jacket' if D.JACKETS else 'motor can', inner, worst, G.MOT_XMIN, G.MOT_XMAX, inner - G.BODY_D))


def c2(r):
    tx0, _ = G.trunk_x()
    bx0 = G.battery_xrange(D.BAT_SLIDE[0])[0]
    gaps = [('trunk aft wall (X %.0f)' % tx0, tx0 - G.MOT_XMAX), ('BH1 (X %.0f)' % D.BH1_X, D.BH1_X - G.MOT_XMAX),
            ('battery at slide %.0f' % D.BAT_SLIDE[0], bx0 - G.MOT_XMAX)]
    ok = all(g >= D.MOTOR_TRUNK_CLR_MIN for _, g in gaps)
    return ('2 Motor front face clears what is forward', ok,
            'front face X %.1f; ' % G.MOT_XMAX + '; '.join('%s: %.1f' % (n, g) for n, g in gaps) + '; need >= %.0f' % D.MOTOR_TRUNK_CLR_MIN)


def c3(r):
    mot = min(_under(r, p[0]) - p[1] for p in G.MOT)
    parts = [('motor', mot)]
    for name, box in (('ESC', G.esc_boxes()[0]), ('steering servo', G.steer_servo_box()), ('receiver', G.rx_box())):
        parts.append((name, _deck_gap(r, box.x0, box.x1, box.z1)))
    bat = min(_deck_gap(r, *G.battery_xrange(b), G.battery_boxes(b)[0].z1) for b in _bat_positions())
    parts.append(('battery', bat))
    ok = all(g >= D.DECK_CLR_MIN for _, g in parts)
    return ('3 Deck underside clears equipment', ok,
            '; '.join('%s: %.1f' % (n, g) for n, g in parts) + '; need >= %.0f' % D.DECK_CLR_MIN)


def c4(r):
    rows = []
    for b in _bat_positions():
        aft = G.battery_xrange(b)[0]
        rows.append((b, aft - G.KEEL_X))
    ok = all(g > D.TUBE_OD for _, g in rows)
    return ('4 Battery clears the shaft entry', ok,
            'shaft enters the floor at X %.1f; battery aft end is ' % G.KEEL_X + ', '.join('%.1f ahead at slide %.0f' % (g, b) for b, g in rows) +
            '; min %.1f vs tube OD %.0f' % (min(g for _, g in rows), D.TUBE_OD))


def c5(r):
    hits = []
    margin = None
    for h in G.hatch_rects(flange=True):
        stations = [('BH1', D.BH1_X), ('BH2', G.BOW0)] if h['zone'] == 'sponson' else []
        stations += [('beam', x) for x in D.DECK_BEAMS]
        for n, x in stations:
            gap = min(abs(x - h['x0']), abs(x - h['x1']))
            inside = h['x0'] < x < h['x1']
            if inside:
                hits.append('%s %.0f crosses %s' % (h['name'], x, n))
            margin = gap if margin is None else min(margin, gap)
    return ('5 Hatches clear bulkheads and deck beams', not hits,
            ('; '.join(hits) if hits else 'no crossings, flange %.0f included (bulkheads in the sponsons only); nearest structure %.1f from a flange edge' % (D.FLANGE, margin)))


def c6(r):
    m = r['over'] - D.TROUGH
    hi = hydro.at_density(D.BALSA_RHO_HI, r)
    return ('6 Water over the nozzle top', m >= D.TROUGH_MARGIN_MIN,
            'batteries at %.0f: at rest %.1f over the nozzle top, minus %.0f trough = %.1f; want >= %.0f (warning only). Balsa %.3f g/cm3: %.1f g, %.1f over, %.1f after the trough' % (
                r['bat_x'], r['over'], D.TROUGH, m, D.TROUGH_MARGIN_MIN, D.BALSA_RHO_HI, hi['W'], hi['over'], hi['over'] - D.TROUGH))


def c7(r):
    return ('7 Skeg interior fits the CV joint', G.SKEG_INTERIOR >= D.CV_OD_ASSUMED,
            'interior %.2f (skeg %.1f less two %.3f skins) vs assumed CV OD %.1f; margin %.2f' % (
                G.SKEG_INTERIOR, D.SKEG_W, D.SKIN_T, D.CV_OD_ASSUMED, G.SKEG_INTERIOR - D.CV_OD_ASSUMED))


def c8(r):
    return ('8 Bow draft', r['bow'] >= D.BOW_DRAFT_MIN,
            'bow draft %.1f vs minimum %.0f' % (r['bow'], D.BOW_DRAFT_MIN))


def _stowed_overshoot(r):
    """Largest distance (mm) by which the stowed blade leaves trunk plus tower or cap in the XZ elevation, and the point."""
    tx0, tx1 = G.trunk_x()
    h = G.housing(r['deck'])
    worst, where = 0, None
    for X, Z in G.blade_outline(extended=False):
        top = r['deck'](X)
        if Z <= top:                       # at or below the deck top: must be in the trunk
            miss = max(tx0 - X, X - tx1, 0)
        elif h is None:
            miss = Z - top
        else:                               # above the deck: must be in the tower or cap
            miss = max(h['x0'] - X, X - h['x1'], Z - h['top'](X), 0)
        if miss > worst:
            worst, where = miss, (X, Z)
    return worst, where


def c9(r):
    miss, where = _stowed_overshoot(r)
    ztop = max(p[1] for p in G.blade_outline(extended=False))
    h = G.housing(r['deck'])
    tx0, tx1 = G.trunk_x()
    xs = [p[0] for p in G.blade_outline(False)]
    msg = 'variant %s; stowed blade X %.0f to %.0f, top Z %.1f; trunk X %.0f to %.0f; ' % (D.BLADE_VARIANT, min(xs), max(xs), ztop, tx0, tx1)
    if h is None:
        msg += 'no tower or cap needed'
    else:
        msg += '%s X %.0f to %.0f, %s above the deck' % (h['kind'], h['x0'], h['x1'], ('%.1f' % h['h0']) if h['h0'] == h['h1'] else '%.1f at the aft end to %.1f at the bow end' % (h['h0'], h['h1']))
    if where:
        msg += '; sticks out %.1f at X %.1f, Z %.1f' % (miss, where[0], where[1])
    return ('9 Stowed blade inside trunk or tower or cap (elevation)', miss == 0, msg)


def c9b(r):
    h = G.housing(r['deck'])
    out = [p for p in G.blade_outline(extended=False) if p[1] > r['deck'](p[0])]
    if not out:
        return ('9b Stowed blade above the deck is under the tower or cap (plan)', True, 'stowed blade stays below the deck, no tower needed')
    by = G.blade_y()
    edge = by + G.blade_thickness() / 2
    if h['kind'] == 'cap':
        xm = max(p[0] for p in out)
        lo, hi = float(G.inner_wall_y(xm)), float(G.outer_wall_y(xm))
        return ('9b Stowed blade above the deck is under the tower or cap (plan)', lo <= by - G.blade_thickness() / 2 and edge <= hi,
                'blade plane at Y +/-%.1f; cap covers the sponson, Y %.1f to %.1f at X %.0f' % (by, lo, hi, xm))
    cover = D.TOWER_W / 2
    return ('9b Stowed blade above the deck is under the tower or cap (plan)', edge <= cover,
            'blade plane at Y +/-%.1f (edge %.1f); tower covers Y +/-%.1f; short by %.1f' % (by, edge, cover, max(edge - cover, 0)))


def c10(r):
    xa = G.NOZ_XA
    plan_x = -xa <= D.AFT_DECK_L
    ymax = G.YS + D.NOZ_OD / 2
    plan_y = ymax <= D.AFT_DECK_W / 2
    avail = r['deck'](G.POSTX) - D.AFT_DECK_T - G.NOZ_ZTOP
    post = 'post %.1f required between nozzle top and aft deck underside (cut from %.0f mm stock, check 18)' % (avail, D.NOZ_POST_STOCK_L)
    return ('10 Nozzle fits under the aft deck', plan_x and plan_y and avail > 0,
            'nozzle aft face %.1f aft of the transom vs deck %.1f (%.1f spare); outer edge Y %.1f vs deck half width %.1f; %s' % (
                -xa, D.AFT_DECK_L, D.AFT_DECK_L + xa, ymax, D.AFT_DECK_W / 2, post))


def c11(r):
    boxes = [('ESC port', G.esc_boxes()[0]), ('ESC stbd', G.esc_boxes()[1]), ('receiver', G.rx_box()), ('steering servo', G.steer_servo_box())]
    hits = []
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            (na, a), (nb, b) = boxes[i], boxes[j]
            ox = min(a.x1, b.x1) - max(a.x0, b.x0)
            oy = min(a.y1, b.y1) - max(a.y0, b.y0)
            if ox > 0 and oy > 0:
                hits.append('%s / %s overlap %.1f in X and %.1f in Y' % (na, nb, ox, oy))
    wide = max(max(abs(b.y0), abs(b.y1)) for _, b in boxes)
    ok = not hits and wide <= G.HT
    return ('11 Roof equipment does not overlap and fits the roof', ok,
            ('; '.join(hits) if hits else 'no overlaps') + '; widest edge Y %.1f vs roof half width %.1f' % (wide, G.HT))


def c12(r):
    beam = 2 * (G.HT + D.SPONSON_W)
    return ('12 Beam equals tunnel plus two sponsons', round(beam - D.BEAM, 1) == 0, '%.2f computed vs %.2f design' % (beam, D.BEAM))


def c13(r):
    tx0, tx1 = G.trunk_x()
    ty0, ty1 = G.trunk_y()
    hits = []
    for b in _bat_positions():
        bx = G.battery_boxes(b)[0]
        ox = min(bx.x1, tx1) - max(bx.x0, tx0)
        oy = min(bx.y1, ty1) - max(bx.y0, ty0)
        if ox > 0 and oy > 0:
            hits.append('battery at %.0f overlaps the trunk by %.1f in X and %.1f in Y' % (b, ox, oy))
    bx = G.battery_boxes(D.DESIGN_BAT_X)[0]
    # the offset battery must still sit inside the sponson (outer wall inside face) over the whole slide
    xa, xb = G.battery_xrange(D.BAT_SLIDE[0])[0], G.battery_xrange(D.BAT_SLIDE[1])[1]
    wall = min(float(G.outer_wall_y(xa)), float(G.outer_wall_y(xb))) - D.SKIN_T
    inside = bx.y1 <= wall
    if not inside:
        hits.append('battery outer edge Y %.1f is outside the sponson interior (Y %.1f)' % (bx.y1, wall))
    gap = bx.y0 - ty1
    return ('13 Blade trunk clears the batteries (plan)', not hits,
            ('; '.join(hits) if hits else 'no overlap at any slide position') + '; trunk X %.0f to %.0f, Y %.1f to %.1f; battery (offset %.1f outboard) Y %.1f to %.1f, %.2f clear of the trunk in Y; battery outer edge %.1f inside the sponson wall at Y %.1f' % (
                tx0, tx1, ty0, ty1, D.BAT_Y_OFFSET, bx.y0, bx.y1, gap, wall - bx.y1, wall))


def c14(r):
    x0, x1 = G.blade_xrange()
    return ('14 Blade stays inside the hull length', x0 >= 0 and x1 <= D.LOA,
            'blade extended and stowed span X %.1f to %.1f vs hull 0 to %.0f' % (x0, x1, D.LOA))


def c15(r):
    """The hatch flange is tested only against the part of the trunk that is open through the deck (where the stowed blade
    is above the deck underside); the closed part of the trunk may lie under a hatch."""
    tx0, tx1 = G.trunk_x()
    ty0, ty1 = G.trunk_y()
    above = G.stowed_above(r['deck'])
    if not above:
        return ('15 Hatches clear the blade trunk (plan)', True, 'the stowed blade stays below the deck underside: the trunk is closed over its whole length; trunk X %.0f to %.0f, Y %.1f to %.1f' % (tx0, tx1, ty0, ty1))
    ox0, ox1 = max(min(p[0] for p in above), tx0), min(max(p[0] for p in above), tx1)
    hits = []
    near = None
    for h in G.hatch_rects(flange=True):
        if h['yc'] < 0:
            continue                                     # the trunk and hatches are mirrored; test the port side
        ox = min(h['x1'], ox1) - max(h['x0'], ox0)
        oy = min(h['y1'], ty1) - max(h['y0'], ty0)
        if ox > 0 and oy > 0:
            hits.append('%s with flange overlaps the open trunk by %.1f in X and %.1f in Y' % (h['name'], ox, oy))
        elif oy > 0:
            gap = max(h['x0'] - ox1, ox0 - h['x1'])
            near = gap if near is None else min(near, gap)
    return ('15 Hatches clear the blade trunk (plan)', not hits,
            ('; '.join(hits) if hits else 'no hatch flange touches the open part of the trunk (%.1f clear in X)' % near if near is not None else 'no hatch flange touches the open part of the trunk') +
            '; trunk X %.0f to %.0f, Y %.1f to %.1f, open through the deck X %.1f to %.1f (stowed blade above the deck underside); the closed part may lie under a hatch' % (tx0, tx1, ty0, ty1, ox0, ox1))


Fit = namedtuple('Fit', 'inside ovx ovy outx outy')


def _fit(fp, op):
    """Plan fit of a footprint in an opening: (inside, overlap_x, overlap_y, out_x, out_y), all in mm."""
    ovx = max(0, min(fp['x1'], op['x1']) - max(fp['x0'], op['x0']))
    ovy = max(0, min(fp['y1'], op['y1']) - max(fp['y0'], op['y0']))
    outx = max(0, op['x0'] - fp['x0']) + max(0, fp['x1'] - op['x1'])
    outy = max(0, op['y0'] - fp['y0']) + max(0, fp['y1'] - op['y1'])
    return Fit(outx == 0 and outy == 0, ovx, ovy, outx, outy)


def c16(r):
    """Every piece of equipment lifts straight out through its hatch: its plan footprint lies inside the opening.
    The battery is tested at the service position (BAT_SERVICE_X), where it is slid before lift-out, not at every slide position."""
    rows, ok_all = [], True
    for fp in G.lift_items([D.BAT_SERVICE_X]):
        op = G.hatch_open(fp['hatch'], (fp['y0'] + fp['y1']) / 2)
        res = _fit(fp, op)
        ok, ovx, ovy, outx, outy = res
        ok_all = ok_all and ok
        if ok:
            rows.append('%s, %s: inside (spare X %.1f, Y %.1f)' % (fp['name'], fp['hatch'], min(fp['x0'] - op['x0'], op['x1'] - fp['x1']), min(fp['y0'] - op['y0'], op['y1'] - fp['y1'])))
        else:
            rows.append('%s, %s: NOT inside, overlap %.1f of %.1f mm in X (%.1f outside), %.1f of %.1f in Y (%.1f outside)' % (
                fp['name'], fp['hatch'], ovx, fp['x1'] - fp['x0'], outx, ovy, fp['y1'] - fp['y0'], outy))
    hb = G.hatch_open('HB', G.BAT_YC)
    lo, hi = hb['x0'] + D.BAT['l'] / 2, hb['x1'] - D.BAT['l'] / 2
    rows.append('HB (X %.0f to %.0f) takes the %.0f long battery only with its center at X %s' % (hb['x0'], hb['x1'], D.BAT['l'], ('%.1f to %.1f' % (lo, hi)) if lo <= hi else 'none (HB is shorter than the battery)'))
    rows.append('battery service position X %.0f; on the slide (%.0f to %.0f) it must be moved %.0f forward from %.0f and %.0f aft from %.0f before lift-out' % (
        D.BAT_SERVICE_X, D.BAT_SLIDE[0], D.BAT_SLIDE[1], D.BAT_SERVICE_X - D.BAT_SLIDE[0], D.BAT_SLIDE[0], D.BAT_SLIDE[1] - D.BAT_SERVICE_X, D.BAT_SLIDE[1]))
    return ('16 Equipment lifts out through its hatch', ok_all, '; '.join(rows))


def c17(r):
    """Bumper: a nozzle turned about its post, swept from 0 to BUMPER_TURN_DEG, keeps its aft-most and outboard-most points inside the aft deck outline."""
    rows = G.nozzle_sweep()
    end = rows[-1]
    aft = min(D.AFT_DECK_L - x['aft'] for x in rows)
    out = min(D.AFT_DECK_W / 2 - x['out'] for x in rows)
    wa = min(rows, key=lambda x: D.AFT_DECK_L - x['aft'])
    wo = min(rows, key=lambda x: D.AFT_DECK_W / 2 - x['out'])
    fwd = max(x['fwd'] for x in rows)
    ok = aft >= D.BUMPER_MARGIN_MIN and out >= D.BUMPER_MARGIN_MIN
    return ('17 Bumper: turned nozzle stays inside the aft deck', ok,
            'nozzle turned %.0f deg: aft-most %.1f behind the transom (margin %.1f to the deck edge %.1f), outboard-most Y %.1f (margin %.1f to the deck edge %.1f); '
            'swept 0 to %.0f deg: aft margin %.1f at %.1f deg, outboard margin %.1f at %.1f deg; need >= %.0f. '
            'Forward-most point reaches X %.1f (positive is ahead of the transom plane; not part of this check)' % (
                end['deg'], end['aft'], D.AFT_DECK_L - end['aft'], D.AFT_DECK_L, end['out'], D.AFT_DECK_W / 2 - end['out'], D.AFT_DECK_W / 2,
                D.BUMPER_TURN_DEG, aft, wa['deg'], out, wo['deg'], D.BUMPER_MARGIN_MIN, fwd))


def c18(r):
    need = G.post_required_length(r['deck'])
    return ('18 Nozzle post length', need <= D.NOZ_POST_STOCK_L,
            'post length required %.1f (aft deck underside %.1f less nozzle top %.1f at X %.0f); 3 mm rod and 3 mm bore tube are cut to it from %.0f mm stock, %s %.1f (each stock length gives %d posts)' % (
                need, r['deck'](G.POSTX) - D.AFT_DECK_T, G.NOZ_ZTOP, G.POSTX, D.NOZ_POST_STOCK_L,
                'spare' if need <= D.NOZ_POST_STOCK_L else 'stock too short by', abs(D.NOZ_POST_STOCK_L - need), int(D.NOZ_POST_STOCK_L // need)))


ALL = (c1, c2, c3, c4, c5, c6, c7, c8, c9, c9b, c10, c11, c12, c13, c14, c15, c16, c17, c18)


def run_all(r=None):
    r = r or hydro.design()
    return [(n, bool(ok), m) for n, ok, m in (f(r) for f in ALL)]


def level(name, ok):
    if ok:
        return 'PASS'
    return 'WARN' if name.split()[0] in WARN_ONLY else 'FAIL'


def report(results):
    lines = ['CHECKS REPORT, variant %s, jackets %s, batteries at %.0f' % (D.BLADE_VARIANT, D.JACKETS, D.DESIGN_BAT_X), '']
    for n, ok, m in results:
        lines.append('[%s] %s: %s' % (level(n, ok), n, m))
    f = sum(level(n, ok) == 'FAIL' for n, ok, _ in results)
    w = sum(level(n, ok) == 'WARN' for n, ok, _ in results)
    lines += ['', '%d checks, %d failed, %d warnings' % (len(results), f, w)]
    return '\n'.join(lines)
