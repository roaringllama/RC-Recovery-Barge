"""Interference and fit checks. Each check takes the design hydro result and returns (name, pass_bool, message).

Checks 1 to 10 are the required set. 9b and 11 to 23 are additions. Check 6 is a warning, not a failure.
Nothing here alters a design value; failures are reported only.
"""
import math
from collections import namedtuple
import design as D
from . import geometry as G
from . import hydro
from . import schedules as S

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
    m0 = G.nozzle_margins(0)
    ymax = G.YS + D.NOZ_OD / 2
    hw = G.aft_half_y(xa)
    avail = r['deck'](G.POSTX) - D.AFT_DECK_T - G.NOZ_ZTOP
    post = 'post %.1f required between nozzle top and aft deck top skin underside (through the bottom skin and the beam bushing; cut from %.0f mm stock, check 18)' % (avail, D.NOZ_POST_STOCK_L)
    return ('10 Nozzle fits under the aft deck', m0['inside'] and avail > 0,
            'deck plan %s: nozzle aft face %.1f aft of the transom vs deck %.1f (%.1f spare); outer edge Y %.1f vs deck half width %.1f at that station; %s' % (
                G.deck_plan(), -xa, D.AFT_DECK_L, D.AFT_DECK_L + xa, ymax, hw, post))


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
    """Bumper: a nozzle turned about its post, swept from 0 to BUMPER_TURN_DEG, keeps its whole plan footprint inside the outline of the chosen deck plan
    (DECK_PLAN) by at least BUMPER_MARGIN_MIN: the distance to the aft edge, to the side and chamfer edges, and (tapered deck) to the step where the
    aft deck, wider than the hull at the transom, ends against the hull outline."""
    rows = G.nozzle_margin_rows()
    end = rows[-1]
    aft = min(x['m_aft'] for x in rows)
    out = min(x['m_side'] for x in rows)
    steps = [x for x in rows if x['m_step'] is not None]
    stp = min(x['m_step'] for x in steps) if steps else None
    chs = [x for x in rows if x['m_chamfer'] is not None]
    chm = min(x['m_chamfer'] for x in chs) if chs else None
    wa = min(rows, key=lambda x: x['m_aft'])
    wo = min(rows, key=lambda x: x['m_side'])
    fwd = max(x['fwd'] for x in rows)
    ok = aft >= D.BUMPER_MARGIN_MIN and out >= D.BUMPER_MARGIN_MIN and all(v is None or v >= D.BUMPER_MARGIN_MIN for v in (stp, chm))
    extra = ''
    if chm is not None:
        extra += '; chamfer margin %.1f at %.1f deg (edges chamfered in to Y %.1f over the last %.0f)' % (chm, min(chs, key=lambda x: x['m_chamfer'])['deg'], D.BEAM / 2, D.AFT_CHAMFER_L)
    if stp is not None:
        extra += '; forward step margin %.1f at %.1f deg (where the %.1f wide aft deck meets the hull outline at the transom)' % (stp, min(steps, key=lambda x: x['m_step'])['deg'], D.AFT_DECK_W)
    step_txt = extra
    return ('17 Bumper: turned nozzle stays inside the deck outline', ok,
            'deck plan %s: nozzle turned %.0f deg: aft-most %.1f behind the transom (margin %.1f to the deck edge %.1f), outboard-most Y %.1f (margin %.1f to the deck outline); '
            'swept 0 to %.0f deg: aft margin %.1f at %.1f deg, outboard margin %.1f at %.1f deg%s; need >= %.0f. '
            'Forward-most point reaches X %.1f (positive is ahead of the transom plane)' % (
                G.deck_plan(), end['deg'], end['aft'], end['m_aft'], D.AFT_DECK_L, end['out'], end['m_side'],
                D.BUMPER_TURN_DEG, aft, wa['deg'], out, wo['deg'], step_txt, D.BUMPER_MARGIN_MIN, fwd))


def c18(r):
    need = G.post_required_length(r['deck'])
    return ('18 Nozzle post length', need <= D.NOZ_POST_STOCK_L,
            'post length required %.1f (aft deck underside %.1f less nozzle top %.1f at X %.0f); 3 mm rod and 3 mm bore tube are cut to it from %.0f mm stock, %s %.1f (each stock length gives %d posts)' % (
                need, r['deck'](G.POSTX) - D.AFT_DECK_T, G.NOZ_ZTOP, G.POSTX, D.NOZ_POST_STOCK_L,
                'spare' if need <= D.NOZ_POST_STOCK_L else 'stock too short by', abs(D.NOZ_POST_STOCK_L - need), int(D.NOZ_POST_STOCK_L // need)))


def c19(r):
    """The blade tip, extended or stowed, stops at least TRUNK_TIP_CLR short of the trunk end it points toward."""
    b = G.blade_params()
    x0, x1 = G.blade_xrange()
    t0, t1 = G.trunk_x()
    gap = G.tip_to_trunk_end()
    end = t1 if b['dir'] == 'fwd' else t0
    tip = x1 if b['dir'] == 'fwd' else x0
    return ('19 Blade tip clears the trunk end', gap >= D.TRUNK_TIP_CLR,
            'variant %s: blade tip (extended and stowed) at X %.1f, trunk end at X %.1f, clearance %.1f; need >= %.0f' % (D.BLADE_VARIANT, tip, end, gap, D.TRUNK_TIP_CLR))


def c20(r):
    """The blade servo fits inside the bow cap footprint, outboard of the blade plane (the blade is a plane at its Y), inside the servo bay, and
    the lift line runs straight up through the open part of the trunk."""
    zd = r['deck']
    h = G.housing(zd)
    sb = G.blade_servo_box(zd)
    if sb is None or h is None or h['kind'] != 'cap':
        return ('20 Blade servo fits in the bow cap', True, 'variant %s has no bow cap servo' % D.BLADE_VARIANT)
    bay0, bay1 = D.BLADE_SERVO_BAY
    lo = max(float(G.inner_wall_y(x)) for x in (sb.x0, sb.x1)) + D.SKIN_T
    hi = min(float(G.outer_wall_y(x)) for x in (sb.x0, sb.x1)) - D.SKIN_T
    plane = G.blade_y() + G.blade_thickness() / 2                     # outboard face of the blade plane
    over = [p[0] for p in G.stowed_above(zd)]
    tx0, tx1 = G.trunk_x()
    ox0, ox1 = max(min(over), tx0), min(max(over), tx1)
    lx = G.line_x()
    edge = max(G.blade_top_at(x, False) for x in (sb.x0, sb.x1))
    top_clr = h['ztop'] - sb.z1
    spool = G.spool_pos(zd)
    probs = []
    if not (bay0 <= sb.x0 and sb.x1 <= bay1):
        probs.append('servo X %.0f to %.0f is outside the bay X %.0f to %.0f' % (sb.x0, sb.x1, bay0, bay1))
    if not (h['x0'] <= sb.x0 and sb.x1 <= h['x1']):
        probs.append('servo X %.0f to %.0f is outside the cap X %.1f to %.1f' % (sb.x0, sb.x1, h['x0'], h['x1']))
    if not (lo <= sb.y0 and sb.y1 <= hi):
        probs.append('servo Y %.1f to %.1f is outside the cap interior Y %.1f to %.1f' % (sb.y0, sb.y1, lo, hi))
    if sb.y0 < plane:
        probs.append('servo reaches %.1f into the blade plane (Y %.1f)' % (plane - sb.y0, G.blade_y()))
    if top_clr < D.CAP_CLR:
        probs.append('servo top is %.1f under the cap top, need >= %.0f' % (top_clr, D.CAP_CLR))
    if not (ox0 <= lx <= ox1):
        probs.append('line X %.1f is outside the open part of the trunk X %.1f to %.1f' % (lx, ox0, ox1))
    return ('20 Blade servo fits in the bow cap', not probs,
            ('; '.join(probs) if probs else 'servo inside the cap and the bay') +
            '; servo X %.0f to %.0f, Y %.1f to %.1f (cap interior Y %.1f to %.1f), Z %.1f to %.1f; '
            'outboard of the blade plane (face Y %.1f) by %.1f; cap top Z %.1f (%s governs), %.1f above the servo top; '
            'line X %.1f, spool Z %.1f, %.0f from the hinge, open trunk X %.1f to %.1f' % (
                sb.x0, sb.x1, sb.y0, sb.y1, lo, hi, sb.z0, sb.z1, plane, sb.y0 - plane, h['ztop'], h['governs'], top_clr,
                lx, spool[1], D.LINE_R, ox0, ox1))


def c21(r):
    """Solid frames and cap ribs against what is in their way: a solid tunnel piece against the roof equipment, a solid sponson piece against the
    motor, the battery slide and the mount, and the cap rib of a frame inside the bow cap against the blade servo and the lift line."""
    zd = r['deck']
    half = D.FRAME_T / 2
    hits, ok_rows = [], []
    h = G.housing(zd)
    sb = G.blade_servo_box(zd)
    tx0, tx1 = G.trunk_x()
    bat0, bat1 = G.battery_xrange(D.BAT_SLIDE[0])[0], G.battery_xrange(D.BAT_SLIDE[1])[1]
    for f in S.frames(zd):
        x = f['x']
        if f['tunnel_solid']:
            for nm, bx in (('ESC', G.esc_boxes()[0]), ('receiver', G.rx_box()), ('steering servo', G.steer_servo_box())):
                ov = min(x + half, bx.x1) - max(x - half, bx.x0)
                if ov > 0:
                    hits.append('%s tunnel piece (solid, X %.1f to %.1f) crosses the %s (X %.1f to %.1f) by %.1f in X; grommet hole %.0f at Y 0 on the roof plate%s' % (
                        f['mark'], x - half, x + half, nm, bx.x0, bx.x1, ov, D.WIRE_HOLE_D,
                        ', hatch ' + ', '.join(f['cut']) + ' lies over it' if f['cut'] else ''))
            ok_rows.append(f['mark'] + ' tunnel piece')
        if f['solid']:
            for nm, a, b in (('motor', G.MOT_XMIN, G.MOT_XMAX), ('battery slide', bat0, bat1), ('motor mount', G.MOUNT[0][0], G.MOUNT[1][0])):
                if a < x + half and b > x - half:
                    hits.append('%s sponson piece (solid) crosses the %s (X %.1f to %.1f)' % (f['mark'], nm, a, b))
            if tx0 <= x <= tx1 and f['kind'] != 'solid_notch' and f['kind'] != 'bulkhead':
                hits.append('%s sponson piece (solid) crosses the blade trunk (X %.0f to %.0f) with no notch' % (f['mark'], tx0, tx1))
            ok_rows.append(f['mark'] + ' sponson piece')
        if h and h['kind'] == 'cap' and sb and h['x0'] < x < h['x1']:
            if sb.x0 < x + half and sb.x1 > x - half:
                hits.append('%s cap rib (X %.1f, inside the bow cap) crosses the blade servo (X %.0f to %.0f)%s' % (
                    f['mark'], x, sb.x0, sb.x1, ' and the lift line at X %.0f' % G.line_x() if abs(x - G.line_x()) <= half else ''))
    return ('21 Solid frames and cap ribs clear the equipment', not hits,
            ('; '.join(hits) if hits else 'no conflicts') + '; %d solid pieces and the cap ribs tested' % len(ok_rows))


def c22(r):
    """Aft deck cantilever: AFT_LOAD at the aft edge, shared by the two longitudinal beams (rectangular section, balsa along the grain)."""
    k = G.aft_cantilever()
    box = G.aft_box()
    fits = box['h'] <= box['gap'] + D.FIT_EPS
    ok = k['margin'] >= D.AFT_MARGIN_MIN and fits
    return ('22 Aft deck cantilever (hand load at the aft edge)', ok,
            'deck plan %s: %.0f g (%.2f N) at the aft edge, %.1f from the transom, %.2f N per beam (2 beams %.2f x %.2f); moment %.0f N mm, '
            'Z %.1f mm3, stress %.2f vs %.1f MPa: margin %.2f, need >= %.1f; tip deflection %.2f mm (E %.0f MPa). '
            'Beam %.2f high %s the %.2f between the skins (box %.1f). One beam alone: margin %.2f; post hole (%.0f) and skins not credited' % (
                G.deck_plan(), D.AFT_LOAD, k['P'], k['L'], k['per'], box['w'], box['h'], k['M'], k['Z'], k['sigma'], D.BALSA_SIGMA, k['margin'], D.AFT_MARGIN_MIN,
                k['defl'], D.E_BALSA, box['h'], 'fits in' if fits else 'does NOT fit in', box['gap'], D.AFT_DECK_DEPTH, k['margin_one'], D.NOZ_POST_D))


def c23(r):
    """Push bar: bottom edge clear of the water at the design position and at every battery position (deck fixed, waterline moves with trim), the bar front
    face ahead of everything submerged (hull tip, blade tips)."""
    z0 = G.bumper_z0(r['deck'])
    z1 = G.bumper_z1(r['deck'])
    rows = []
    for b in _bat_positions():
        rr = r if b == r['bat_x'] else hydro.at(b, r)
        wl = rr['d0'] - rr['k'] * D.LOA
        rows.append((b, z0 - wl))
    low = min(c for _, c in rows)
    sub = max(D.LOA, G.blade_xrange()[1])
    ahead = G.BUMPER_X1 - sub
    ok = low > D.BUMPER_WL_CLR_MIN and ahead > 0 and abs(z1 - r['deck'](D.LOA)) == 0
    return ('23 Push bar clear of the water, ahead of the hull', ok,
            'deck plan %s: bar X %.1f to %.1f (%.1f ahead of the bow tip, %.1f ahead of the forward-most submerged point at X %.1f), Z %.1f to %.1f (%.1f deep), thick %.0f, width %.0f; '
            'bottom edge above the waterline: %s; need > %.0f. Top flush with the deck (Z %.1f); bar bottom %.1f above the keel line, bow draft %.1f' % (
                G.deck_plan(), G.BUMPER_X0, G.BUMPER_X1, D.BUMPER_PROJ, ahead, sub, z0, z1, z1 - z0, D.BUMPER_T, 2 * max(p[1] for p in G.bumper_plan()),
                ', '.join('%.1f at batteries %.0f' % (c, b) for b, c in rows), D.BUMPER_WL_CLR_MIN, z1, z0, r['bow']))


ALL = (c1, c2, c3, c4, c5, c6, c7, c8, c9, c9b, c10, c11, c12, c13, c14, c15, c16, c17, c18, c19, c20, c21, c22, c23)


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
