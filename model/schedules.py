"""Schedules derived from the model: panels, frames, blocking, hatches, sealing, channels, open items.

Everything numeric comes from design.py, geometry.py and the hydro result. No literals except 0, 1, 2, 1000 (a test enforces this).
`zd` is the deck function Z(X) of a hydro result.
"""
import ast
import io
import math
import re
import tokenize
import design as D
from . import geometry as G

BOTH = 2                                   # port and starboard
TAGS = ('PENDING', 'ASSUMED', 'ESTIMATE')


def _seg(a, b):
    return math.hypot(b[0] - a[0], b[1] - a[1])


def _planks(cross, length):
    """Planks run along the long side. Returns the count across the short side."""
    n = cross / D.STOCK_W
    return max(1, round(n) if math.isclose(n, round(n)) else math.ceil(n))


# ---- plan outline of the port sponson ------------------------------------------------------------
OUTER = [(x, G.HT + float(G.outer_off(x))) for x in G.PLAN_STATIONS]                       # transom to tip, outer wall
INNER = [(x, G.HT + float(G.inner_off(x))) for x in (G.PLAN_STATIONS[0], G.PLAN_STATIONS[1], G.PLAN_STATIONS[-1])]   # transom to tip, inner wall
POLY = OUTER + list(reversed(INNER))
VERTEX_NAMES = ['transom, outer', 'aft taper end, outer', 'bow taper start, outer', 'tip, outer', 'tip, inner', 'aft taper end, inner', 'transom, inner']


def turns():
    """Exterior turn angle (deg) at each vertex of the sponson outline. Returns [(name, (x, y), turn_deg)]."""
    out = []
    n = len(POLY)
    for i, p in enumerate(POLY):
        a, b = POLY[i - 1], POLY[(i + 1) % n]
        h1 = math.atan2(p[1] - a[1], p[0] - a[0])
        h2 = math.atan2(b[1] - p[1], b[0] - p[0])
        d = (h2 - h1 + math.pi) % (2 * math.pi) - math.pi
        out.append((VERTEX_NAMES[i], p, abs(math.degrees(d))))
    return out


def aft_taper_deg():
    """Angle of the aft taper of each wall to the centerline."""
    return math.degrees(math.atan((D.SPONSON_W - D.AFT_W) / 2 / D.AFT_TAPER_X))


def bow_taper_deg():
    return math.degrees(math.atan((D.SPONSON_W - D.TIP_W) / (D.LOA - G.BOW0)))


def _trap(fn, xs):
    """Area under a piecewise linear fn over the breakpoints xs."""
    return sum((fn(a) + fn(b)) / 2 * (b - a) for a, b in zip(xs, xs[1:]))


def _P(mark, name, qty, where, kind, length, h0, h1, area, cross, note='', t=None, angle=''):
    n = _planks(cross, length)
    return dict(mark=mark, name=name, qty=qty, where=where, kind=kind, length=length, h0=h0, h1=h1, t=D.SKIN_T if t is None else t,
                area=area, planks=n, plank_w0=h0 / n, plank_w1=h1 / n, note=note, angle=angle,
                seam=(n - 1) * length)


def panels(zd):
    """Panel schedule rows. qty counts both sponsons where the panel is one per sponson."""
    T = D.SKIN_T
    hw = lambda x: zd(x) - 2 * T
    out = []
    tr = {n: t for n, p, t in turns()}
    walls = [('O1', 'Outer wall, aft taper', OUTER[0], OUTER[1], '%.2f deg to the centerline' % aft_taper_deg()),
             ('O2', 'Outer wall, straight', OUTER[1], OUTER[2], 'parallel to the centerline'),
             ('O3', 'Outer wall, bow', OUTER[2], OUTER[-1], '%.2f deg to the centerline' % bow_taper_deg()),
             ('I1', 'Inner wall, aft taper', INNER[0], INNER[1], '%.2f deg to the centerline' % aft_taper_deg()),
             ('I2', 'Inner wall, straight', INNER[1], INNER[2], 'parallel to the centerline')]
    for mark, name, a, b, note in walls:
        L = _seg(a, b)
        out.append(_P(mark, name, BOTH, 'sponson', 'wall', L, hw(a[0]), hw(b[0]), L * (hw(a[0]) + hw(b[0])) / 2, max(hw(a[0]), hw(b[0])),
                      'trapezoid; ' + note))
    wf = lambda x: float(G.sponson_width(x))
    xs = list(G.PLAN_STATIONS)
    abot = _trap(wf, xs)
    out.append(_P('TP', 'Tip face', BOTH, 'sponson', 'wall', wf(D.LOA), hw(D.LOA), hw(D.LOA), wf(D.LOA) * hw(D.LOA), hw(D.LOA), 'rectangle, ends mitered with O3 and I2'))
    out.append(_P('TR', 'Sponson transom', BOTH, 'sponson', 'wall', wf(0), hw(0), hw(0), wf(0) * hw(0), hw(0), 'rectangle, ends mitered with O1 and I1'))
    out.append(_P('BT', 'Sponson bottom', BOTH, 'sponson', 'plate', D.LOA, wf(0), wf(D.LOA), abot, D.SPONSON_W, 'outline of the sponson, widths %.2f at the transom, %.2f full, %.2f at the tip' % (wf(0), D.SPONSON_W, wf(D.LOA))))
    out.append(_P('DK', 'Sponson deck', BOTH, 'sponson', 'plate', D.LOA, wf(0), wf(D.LOA), abot, D.SPONSON_W, 'same outline as BT; hatch openings not deducted'))
    cw = lambda x: 2 * (G.HT + float(G.inner_off(x)))
    xi = [G.PLAN_STATIONS[0], G.PLAN_STATIONS[1], G.PLAN_STATIONS[-1]]
    acen = _trap(cw, xi)
    out.append(_P('RP', 'Tunnel roof plate', 1, 'center', 'plate', D.LOA, cw(0), cw(D.LOA), acen, cw(0), 'between the inner walls, Z %.1f to %.1f' % (D.ROOF_Z0, G.ROOF_Z1)))
    out.append(_P('DC', 'Center deck', 1, 'center', 'plate', D.LOA, cw(0), cw(D.LOA), acen, cw(0), 'between the inner walls; hatch openings not deducted'))
    ht = zd(0) - T - G.ROOF_Z1
    out.append(_P('TT', 'Tunnel-top transom', 1, 'center', 'wall', cw(0), ht, ht, cw(0) * ht, ht, 'closes the center cavity aft'))
    out.append(_P('AD', 'Aft deck', 1, 'aft', 'plate', D.AFT_DECK_W, D.AFT_DECK_L, D.AFT_DECK_L, D.AFT_DECK_L * D.AFT_DECK_W, D.AFT_DECK_L, 'over the nozzles; post bushings', t=D.AFT_DECK_T))
    ph = zd(D.LOA) - 2 * D.PUSH_PAD_INSET
    out.append(_P('BP', 'Bow push pad', 1, 'bow', 'plate', D.BEAM, ph, ph, D.BEAM * ph, ph, 'full bow face, glassed', t=D.PUSH_PAD_T))
    sk = G.SKEG_X0
    drop = -G.SHOE_BOT
    out.append(_P('SK', 'Skeg side plate', 2 * BOTH, 'skeg', 'triangle', sk, drop, 0.0, G.SKEG_TRI_AREA, drop, 'right triangle, legs %.2f along the bottom and %.2f at the transom, edge %.2f at %.2f deg' % (sk, drop, math.hypot(sk, drop), G.SKEG_BOT_DEG)))
    out.append(_P('SH', 'Skeg shoe', BOTH, 'skeg', 'plate', -G.SHOE_X1, D.SKEG_W, D.SKEG_W, G.SHOE_AREA, D.SKEG_W, 'under the nozzle, Z %.2f to %.2f' % (G.SHOE_TOP, G.SHOE_BOT), t=D.SHOE_T))
    # trunk
    tx0, tx1 = G.trunk_x()
    tw = G.blade_params()['trunk_w']
    L = tx1 - tx0
    out.append(_P('TK', 'Trunk wall', BOTH, 'trunk', 'wall', L, hw(tx0), hw(tx1), L * (hw(tx0) + hw(tx1)) / 2, max(hw(tx0), hw(tx1)), 'blade trunk, open through the deck and the bottom; inner wall is I2'))
    out.append(_P('TE', 'Trunk end plates', 2 * BOTH, 'trunk', 'wall', tw, hw(tx0), hw(tx1), tw * (hw(tx0) + hw(tx1)) / 2, max(hw(tx0), hw(tx1)), 'one at each end of each trunk, height %.2f aft and %.2f forward' % (hw(tx0), hw(tx1))))
    # housing
    h = G.housing(zd)
    if h and h['kind'] == 'cap':
        x0, x1, ztop = h['x0'], h['x1'], h['ztop']
        bps = [x0] + [s for s in G.PLAN_STATIONS if x0 < s < x1] + [x1]
        out.append(_P('CT', 'Bow cap top plate', BOTH, 'cap', 'plate', x1 - x0, wf(x0), wf(x1), _trap(wf, bps), D.SPONSON_W, 'flat at Z %.1f, %.1f above the stowed blade' % (ztop, D.CAP_CLR)))
        for i, (a, b) in enumerate(zip(bps, bps[1:]), 1):
            Lc = math.hypot(b - a, float(G.outer_off(b) - G.outer_off(a)))
            ha, hb = ztop - zd(a), ztop - zd(b)
            out.append(_P('CO%d' % i, 'Bow cap outer wall, part %d' % i, BOTH, 'cap', 'wall', Lc, ha, hb, Lc * (ha + hb) / 2, max(ha, hb), 'X %.1f to %.1f, heights are above the deck top' % (a, b)))
        Li = math.hypot(x1 - x0, float(G.inner_off(x1) - G.inner_off(x0)))
        ha, hb = ztop - zd(x0), ztop - zd(x1)
        out.append(_P('CI', 'Bow cap inner wall', BOTH, 'cap', 'wall', Li, ha, hb, Li * (ha + hb) / 2, max(ha, hb), 'X %.1f to %.1f, parallel to the centerline' % (x0, x1)))
        out.append(_P('CA', 'Bow cap aft end plate', BOTH, 'cap', 'wall', wf(x0), ztop - zd(x0), ztop - zd(x0), wf(x0) * (ztop - zd(x0)), ztop - zd(x0), 'at X %.1f' % x0))
        out.append(_P('CF', 'Bow cap forward end plate', BOTH, 'cap', 'wall', wf(x1), ztop - zd(x1), ztop - zd(x1), wf(x1) * (ztop - zd(x1)), ztop - zd(x1), 'at X %.1f' % x1))
    elif h:
        out.append(_P('TW', 'Tower shell', 1, 'cap', 'plate', D.TOWER_W, D.TOWER_L, D.TOWER_H, D.TOWER_L * D.TOWER_W, D.TOWER_L, 'footprint %.0f x %.0f, %.0f high' % (D.TOWER_L, D.TOWER_W, D.TOWER_H)))
    return out


def hull_area_total(pl):
    """Skin area counted by the weight model: every panel except the trunk and the bow cap or tower (carried as lumps)."""
    return sum(p['qty'] * p['area'] for p in pl if p['where'] not in ('trunk', 'cap'))


def wall_heights(zd):
    """Wall height (between bottom and deck skins) at the transom, each frame and the tip."""
    return [(x, zd(x) - 2 * D.SKIN_T) for x in [0.0] + list(D.FRAME_X) + [D.LOA]]


# ---- frames -------------------------------------------------------------------------------------------
def _near(x, xs):
    return next((s for s in xs if abs(s - x) <= D.FRAME_T), None)


def frames(zd):
    """Frame schedule. Each frame is a ring of FRAME_RIB members in the sponson plus a tunnel frame above the roof plate."""
    T = D.SKIN_T
    tx0, tx1 = G.trunk_x()
    ty = G.trunk_y()
    bat0, bat1 = G.battery_xrange(D.BAT_SLIDE[0])[0], G.battery_xrange(D.BAT_SLIDE[1])[1]
    out = []
    for i, x in enumerate(D.FRAME_X, 1):
        wo = float(G.sponson_width(x))
        wi = wo - 2 * T
        h = zd(x) - 2 * T
        tw = 2 * (G.HT + float(G.inner_off(x)))
        th = zd(x) - T - G.ROOF_Z1
        notes = []
        bh = _near(x, G.BH)
        if bh is not None:
            notes.append('bulkhead BH at X %.1f (solid, sealed)' % bh)
        db = _near(x, D.DECK_BEAMS)
        if db is not None:
            notes.append('deck beam at X %.0f is this frame top member' % db)
        cut = []
        for name, hh in D.HATCHES.items():
            if hh['x0'] <= x <= hh['x1']:
                cut.append(name)
        if cut:
            notes.append('top member cut by hatch ' + ', '.join(cut))
        clash = []
        if G.MOT_XMIN <= x <= G.MOT_XMAX:
            clash.append('motor')
        if bat0 <= x <= bat1:
            clash.append('battery slide')
        for nm, bx in (('ESC', G.esc_boxes()[0]), ('receiver', G.rx_box()), ('steering servo', G.steer_servo_box())):
            if bx.x0 <= x <= bx.x1:
                clash.append(nm + ' (tunnel frame)')
        if clash:
            notes.append('crosses ' + ', '.join(clash) + ': notch to the equipment')
        wt = None
        if tx0 <= x <= tx1:
            wt = float(G.outer_wall_y(x)) - T - ty[1]
            notes.append('trunk strip: sponson frame is %.2f wide beside the trunk' % wt)
        out.append(dict(mark='F%d' % i, x=x, w_out=wo, w_in=wi, h=h, tun_w=tw, tun_h=th, rib=D.FRAME_RIB, open_w=wi - 2 * D.FRAME_RIB,
                        open_h=h - 2 * D.FRAME_RIB, t=D.FRAME_T, trunk_w=wt, notes=notes, bulkhead=bh is not None, clash=clash, cut=cut))
    return out


def stations(zd):
    rows = []
    for x in [0.0] + list(D.FRAME_X) + [D.LOA]:
        wo = float(G.sponson_width(x))
        rows.append(dict(x=x, w_out=wo, w_in=wo - 2 * D.SKIN_T, deck=zd(x), wall=zd(x) - 2 * D.SKIN_T, tun_w=2 * (G.HT + float(G.inner_off(x))),
                         tun_h=zd(x) - D.SKIN_T - G.ROOF_Z1))
    return rows


# ---- supports ---------------------------------------------------------------------------------------
def supports(zd):
    """Bulkheads, deck beams, rails, motor mount, servo pads. Rows: mark, part, qty, size text."""
    T = D.SKIN_T
    out = []
    for i, x in enumerate(G.BH, 1):
        wi = float(G.sponson_width(x)) - 2 * T
        out.append(dict(mark='BH%dS' % i, part='Bulkhead, sponson piece', qty=BOTH, x=x, w=wi, h=zd(x) - 2 * T, t=D.FRAME_T))
    for x in D.DECK_BEAMS:
        out.append(dict(mark='DB', part='Deck beam, full deck width', qty=1, x=x, w=2 * (G.HT + float(G.outer_off(x))), h=D.DECK_BEAM_T, t=D.DECK_BEAM_W))
    bl = D.BAT['l']
    rail_l = (D.BAT_SLIDE[1] - D.BAT_SLIDE[0]) + bl
    return out, rail_l


def mount_dims():
    xa, xb = G.MOUNT[0][0], G.MOUNT[1][0]
    h_aft = G.MOUNT[-1][1] - G.MOUNT[0][1]
    h_fwd = G.MOUNT[2][1] - G.MOUNT[1][1]
    return dict(l=xb - xa, w=D.MOUNT_W, h_aft=h_aft, h_fwd=h_fwd, layers=math.ceil(max(h_aft, h_fwd) / D.SKIN_T), angle=D.MOTOR_AXIS_DEG)


# ---- blocking ---------------------------------------------------------------------------------------
def blocking(zd, pl=None):
    """Blocking length table. Rows: id, joint, where, kind, per sponson, center, total (mm). kind: tri, chine, wedge, back."""
    pl = pl or panels(zd)
    T = D.SKIN_T
    outer = sum(_seg(a, b) for a, b in zip(OUTER, OUTER[1:]))
    inner = sum(_seg(a, b) for a, b in zip(INNER, INNER[1:]))
    rows = []

    def add(i, joint, where, kind, per, center=0.0):
        rows.append(dict(id=i, joint=joint, where=where, kind=kind, per=per, center=center, total=BOTH * per + center))
    add('J1', 'wall to bottom', 'inner wall (I1, I2)', 'tri', inner)
    add('J1', 'wall to bottom', 'transom TR', 'tri', float(G.sponson_width(0)))
    add('J1', 'wall to bottom', 'tip face TP', 'tri', float(G.sponson_width(D.LOA)))
    add('J1', 'wall to roof plate', 'inner wall at the roof plate', 'tri', inner)
    add('J2', 'chine, outer wall to bottom', 'outer wall (O1, O2, O3), chine stringer', 'chine', outer)
    add('J3', 'wall to deck', 'outer wall', 'tri', outer)
    add('J3', 'wall to deck', 'inner wall', 'tri', inner)
    add('J3', 'wall to deck', 'transom and tip face', 'tri', float(G.sponson_width(0)) + float(G.sponson_width(D.LOA)))
    add('J3', 'tunnel transom TT to roof and deck', 'TT', 'tri', 0.0, 2 * 2 * (G.HT + float(G.inner_off(0))))
    for name, p, turn in turns():
        add('J4', 'corner turn %.2f deg' % turn, name + ' (wall height at X %.1f)' % p[0], 'wedge', zd(p[0]) - 2 * T)
    seam = sum(p['qty'] * p['seam'] for p in pl if p['where'] not in ('trunk', 'cap'))
    add('J5', 'plank seams, backing strip', 'all panels with more than one plank', 'back', 0.0, seam)
    add('J6', 'skeg box to bottom', 'both sides of each skeg plate pair', 'tri', 2 * G.SKEG_X0)
    fr = frames(zd)
    per = sum(2 * 2 * (f['w_in'] + f['h']) for f in fr)
    cen = sum(2 * 2 * (f['tun_w'] + f['tun_h']) for f in fr)
    add('J7', 'frame to skin, gusset each face', 'all frame edges (%d frames)' % len(fr), 'tri', per, cen)
    m = mount_dims()
    add('M1', 'motor mount base to floor', 'both sides of each mount', 'tri', 2 * m['l'])
    return rows


def blocking_totals(rows):
    tot = {}
    for r in rows:
        tot[r['kind']] = tot.get(r['kind'], 0.0) + r['total']
    return tot


def stick_counts(rows, extra_tri=0.0):
    """Stock counts. Triangular blocking is ripped from square stock, two pieces per stick length."""
    t = blocking_totals(rows)
    tri = (t.get('tri', 0.0) + extra_tri) * (1 + D.WASTE) / 2
    chine = t.get('chine', 0.0) * (1 + D.WASTE)
    back = t.get('back', 0.0) * (1 + D.WASTE)
    wedge = t.get('wedge', 0.0) * (1 + D.WASTE)
    n = lambda L: math.ceil(L / D.STICK_L)
    return dict(tri_len=tri, chine_len=chine, back_len=back, wedge_len=wedge, tri_n=n(tri), chine_n=n(chine), back_n=n(back), wedge_n=n(wedge))


# ---- hatches --------------------------------------------------------------------------------------
def _contents(name):
    if name == 'HM':
        return 'motor and jacket', G.MOT_XMAX - G.MOT_XMIN, G.BODY_D
    if name == 'HB':
        return 'battery', D.BAT['l'], D.BAT['w']
    if name == 'HC':
        return 'ESC', D.ESC['l'], D.ESC['w']
    if name == 'HS':
        return 'steering servo', D.STEER_SERVO['l'], D.STEER_SERVO['w']
    return None, None, None


def hatch_seal():
    """Derived seal numbers shared by every hatch."""
    inset = (D.PLUG_CLR / 2 + D.GROOVE_D) / 2          # cord center inset from the opening wall when compressed
    squeeze = D.CORD_D - (D.PLUG_CLR / 2 + D.GROOVE_D)
    plug_depth = D.PLUG_LAYERS * D.SKIN_T
    seat = D.SKIN_T + D.RIM_T
    return dict(inset=inset, squeeze=squeeze, squeeze_pct=squeeze / D.CORD_D, plug_depth=plug_depth, seat=seat,
                lid_total=plug_depth + D.SKIN_T, lid_proud=D.SKIN_T + (plug_depth - seat),
                pad_off=D.RIM_W + D.LATCH_PAD / 2, tab_end=D.RIM_W + D.LATCH_PAD)


def cord_length(L, W):
    """Cord loop length for an L x W opening: rounded rectangle at the compressed cord centerline plus the splice lap."""
    s = hatch_seal()
    a, b = L - 2 * s['inset'], W - 2 * s['inset']
    r = D.HATCH_CORNER_R - s['inset']
    return 2 * (a + b) - 2 * 2 * 2 * r + 2 * math.pi * r + D.CORD_LAP


def hatches(zd):
    """One row per hatch type. Lengths along X, widths along Y."""
    T = D.SKIN_T
    s = hatch_seal()
    out = []
    frame_x = list(D.FRAME_X)
    for name, h in D.HATCHES.items():
        L, W = h['x1'] - h['x0'], h['w']
        qty = BOTH if h['zone'] == 'sponson' else 1
        xs = (h['x0'], h['x1'])
        if h['zone'] == 'sponson':
            avail = min(float(G.sponson_width(x)) for x in xs) - 2 * T
        else:
            avail = min(2 * (G.HT + float(G.inner_off(x))) for x in xs)
        rim_y = min(D.RIM_W, (avail - W) / 2)
        touch = (avail - W) / 2 <= D.RIM_W
        outer_L, outer_W = L + 2 * D.RIM_W, W + 2 * rim_y
        blk = 2 * outer_W + (0.0 if touch else 2 * outer_L)
        what, cl, cw_ = _contents(name)
        pad = [h['x0'] - s['pad_off'], h['x1'] + s['pad_off']]
        meet = []
        for px in pad:
            lo, hi = px - D.LATCH_PAD / 2, px + D.LATCH_PAD / 2
            for fx in frame_x + [b for b in G.BH] + list(D.DECK_BEAMS):
                half = D.DECK_BEAM_W / 2 if fx in D.DECK_BEAMS else D.FRAME_T / 2
                if lo < fx + half and hi > fx - half:
                    meet.append('%.0f' % fx)
            if lo < 0:
                meet.append('off the hull (X<0)')
        out.append(dict(name=name, zone=h['zone'], qty=qty, x0=h['x0'], x1=h['x1'], L=L, W=W, flange_L=L + 2 * D.FLANGE, flange_W=W + 2 * D.FLANGE,
                        plug_L=L - D.PLUG_CLR, plug_W=W - D.PLUG_CLR, cord=cord_length(L, W), latches=D.LATCH_PER_LID, rim_y=rim_y, rim_touch=touch,
                        avail=avail, rim_blocking=blk, contents=what, c_l=cl, c_w=cw_,
                        fits=(what is None) or (cl <= L and cw_ <= W), pads=pad, meets=sorted(set(meet), key=lambda v: (len(v), v)),
                        zc=(zd(h['x0']) + zd(h['x1'])) / 2))
    return out


def hatch_totals(hs):
    return dict(cord=sum(h['qty'] * h['cord'] for h in hs), latches=sum(h['qty'] * h['latches'] for h in hs),
                lids=sum(h['qty'] for h in hs), rim_blocking=sum(h['qty'] * h['rim_blocking'] for h in hs))


# ---- sealing, channels, trim ------------------------------------------------------------------------------
def sealing():
    """Penetration and sealing schedule rows: (ref, penetration, where, method, check)."""
    hs = D.HATCHES
    n_h = sum(BOTH if h['zone'] == 'sponson' else 1 for h in hs.values())
    names = ', '.join(hs)
    tx0, tx1 = G.trunk_x()
    bb = G.blade_box()
    rows = [
        ('S1', 'Hatches %s (%d lids)' % (names, n_h), 'deck, see A-503', 'plug lid, %.1f mm O-ring cord in a groove, rim ring under the deck, %d thumb screws per lid' % (D.CORD_D, D.LATCH_PER_LID),
         'bench test: lid under %.0f mm of water for %.0f min; fill test before every run' % (D.HATCH_TEST_DEPTH, D.HATCH_TEST_MIN)),
        ('S2', 'Stern tubes (2), %.1f mm OD' % D.TUBE_OD, 'transom, Z %.0f; enters the hull through the floor at X %.1f' % (D.PROP_Z, G.KEEL_X),
         'transom stuffing seal %.0f long x %.0f OD, tube epoxied into the skeg core and the floor slot; no seal inside the hull' % (D.SEAL_L, D.SEAL_OD), 'dye test at the floor slot; check for drip after each run'),
        ('S3', 'Steering posts (2), %.1f mm' % D.NOZ_POST_D, 'aft deck, X %.1f' % G.POSTX, 'bushings in the aft deck, outside the hull; no hull seal', 'check free turning over the full travel (%.0f deg each side)' % D.STEER_TRAVEL_DEG),
        ('S4', 'Steering pushrod', 'route not designed; servo at X %.0f to %.0f' % (D.STEER_SERVO['x0'], D.STEER_SERVO['x0'] + D.STEER_SERVO['l']),
         'rubber bellows if the rod leaves the hull (size %s)' % ('PENDING' if D.PUSHROD_BELLOWS_D is None else '%.1f' % D.PUSHROD_BELLOWS_D), 'cycle full travel, then fill-test'),
        ('S5', 'Blade trunks (2), X %.0f to %.0f' % (tx0, tx1), 'open to the water at the bottom and through the deck into the bow cap',
         'wet well: walls epoxy-filleted to the bottom, the inner wall and the deck edge; the bow cap closes the top above the deck', 'dye test of the trunk walls'),
        ('S6', 'Blade servo wire (2)', 'deck box X %.0f to %.0f, above the deck' % (bb.x0, bb.x1), 'potted gland through the deck; the servo is IP66, not immersion rated, so it stays above the deck under the cap', 'fill-test the hull with the cap in place'),
        ('S7', 'Skeg box to bottom (2)', 'bottom, X 0 to %.1f' % G.SKEG_X0, 'triangular blocking both sides, epoxy fillet, glass over', 'dye test'),
        ('S8', 'Wires through BH1 and BH2', 'bulkheads at X %.1f and %.1f' % G.BH, 'epoxy-potted feedthrough, one per sponson per bulkhead', 'fill-test each compartment'),
        ('S9', 'Water jacket plumbing (2 pickups, 2 outlets)', 'pickup X %s, outlet X %s' % ('PENDING' if D.COOL_PICKUP_X is None else '%.0f' % D.COOL_PICKUP_X, 'PENDING' if D.COOL_OUTLET_X is None else '%.0f' % D.COOL_OUTLET_X),
         'M5 pickup and M6 outlet nipples through the skin, epoxied; sealed loop inside', 'inspect fittings; check the pickup is below the waterline'),
        ('S10', 'Transom closures, tip face, bow pad', 'X 0 and X %.0f' % D.LOA, 'epoxy fillet all round, glass over', 'fill-test'),
    ]
    return rows


def channels():
    """RC channel plan: (channel, function, device, note)."""
    return [
        ('CH1', 'Steering (both nozzles)', 'one DS3225MG on the tunnel roof', 'pushrod and tie bar; travel about %.0f deg each side (ASSUMED)' % D.STEER_TRAVEL_DEG),
        ('CH2', 'Port throttle', 'port ESC, forward and reverse', 'mixed with CH1 in the transmitter for differential thrust'),
        ('CH3', 'Starboard throttle', 'starboard ESC, forward and reverse', 'mixed with CH1 in the transmitter for differential thrust'),
        ('CH4', 'Daggerboard', 'DS3225MG blade servo in the deck box', 'spool and line drive the blade forward against a stop; set end points for extended and stowed'),
        ('CH5, CH6', 'Spare', 'FS-iA6B has six channels', 'unused'),
        ('Power', 'Receiver supply', 'one ESC BEC only', 'pull the red lead of the second ESC receiver cable'),
        ('Power', 'Servo load', 'two DS3225MG on one 6 V / 3 A BEC', 'peak current of both servos is not published: confirm, or add a BEC (open)'),
        ('Power', 'Batteries', 'one 3S pack per ESC', 'one per sponson, sliding %.0f to %.0f' % D.BAT_SLIDE),
    ]


# ---- open items from design.py --------------------------------------------------------------------
def open_items(path=None):
    """Parse design.py for PENDING, ASSUMED and ESTIMATE tags. Returns [{name, value, tag, text, line}] in file order.

    A tag in a trailing comment belongs to that assignment (or to that key of a dict assigned over several lines). A section header
    `# ---- name (ESTIMATE): ...` gives its tag to the assignments below it that carry no tag of their own.
    """
    path = path or D.__file__
    src = open(path).read()
    tree = ast.parse(src)
    lines = src.splitlines()
    comments = {}
    for tok in tokenize.generate_tokens(io.StringIO(src).readline):
        if tok.type == tokenize.COMMENT:
            comments[tok.start[0]] = tok.string.lstrip('# ').strip()
    sect = {}
    cur = None
    for i, ln in enumerate(lines, 1):
        m = re.match(r'# ---- .*\((ESTIMATE)\)', ln)
        if m:
            cur = m.group(1)
        elif ln.startswith('# ----'):
            cur = None
        sect[i] = cur
    out = []
    for node in tree.body:
        if not isinstance(node, ast.Assign) or not isinstance(node.targets[0], ast.Name):
            continue
        name = node.targets[0].id
        val = getattr(D, name, None)
        found = []
        if isinstance(node.value, ast.Dict) and node.end_lineno > node.lineno:
            for k, v in zip(node.value.keys, node.value.values):
                key = k.value if isinstance(k, ast.Constant) else '?'
                for ln in range(v.lineno, v.end_lineno + 1):
                    if ln in comments:
                        found.append(('%s[%s]' % (name, key), comments[ln], ln))
        for ln in range(node.lineno, node.end_lineno + 1):
            if ln in comments and not (isinstance(node.value, ast.Dict) and node.end_lineno > node.lineno):
                found.append((name, comments[ln], ln))
        if not found and sect.get(node.lineno):
            found.append((name, 'section tag: ' + sect[node.lineno], node.lineno))
        for nm, text, ln in found:
            tags = [t for t in TAGS if re.search(r'\b%s\b' % t, text)]
            if sect.get(node.lineno) and not tags and nm == name and text.startswith('section tag'):
                tags = [sect[node.lineno]]
            if not tags:
                continue
            # the tag that closes the decision: the last one named
            tag = max(tags, key=lambda t: text.rfind(t))
            out.append(dict(name=nm, value=val if nm == name else None, tag=tag, text=text, line=ln))
    return out


def _fmt_value(v):
    if v is None:
        return 'None'
    if isinstance(v, float):
        return '%g' % v
    return repr(v)
