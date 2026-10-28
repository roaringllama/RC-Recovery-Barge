"""A-701 Line launcher module, concept. Every design number comes from design.py (LAUNCHER_*) or the model. The numbers typed here are layout
positions and drawing details with no design meaning (LAY and the panel coordinates)."""
import math
from .lib import *
from .wtbl import wtable, wrap
import design as D
from model import geometry as G, hydro, variants

BIRCH = 'style="fill:#e8d9b8"'
BRASS = 'style="fill:#c9a24a"'
FOAM = 'style="fill:#dbeafe"'
FLOATC = 'style="fill:#f97316"'
LINEC = 'style="stroke:#1d4ed8;stroke-width:.45;fill:none"'
LATEXC = 'style="stroke:#a0522d;stroke-width:1;fill:none;stroke-linecap:round"'
LINEB = 'style="stroke:#1d4ed8;stroke-width:.4;fill:none"'
ORANGE = '#f97316'

# drawing details (layout only): cap thickness, pin and sear sizes, ring radii
LAY = dict(cap_t=6.0, pin_d=3.0, pin_up=13.0, guide_back=12.0, guide_down=10.0, bail_r=21.0, roller_r=1.6, ring_r=2.0,
           sear_gap=1.5, sear_h=8.5, sear_l=18.0, head_k=2.5, head_h=3.0)


def _unit(dx, dy):
    n = math.hypot(dx, dy)
    return dx / n, dy / n


def adim(sh, p1, p2, off, label, tdy=1.0):
    """Dimension parallel to p1-p2 (page points), offset by `off` mm to the left of the direction p1 to p2; the text sits on the offset side."""
    ux, uy = _unit(p2[0] - p1[0], p2[1] - p1[1])
    nx, ny = uy, -ux
    a = (p1[0] + nx * off, p1[1] + ny * off)
    b = (p2[0] + nx * off, p2[1] + ny * off)
    g = 1.0 if off > 0 else -1.0
    sh.line(p1[0] + nx * g, p1[1] + ny * g, a[0] + nx * g * 1.2, a[1] + ny * g * 1.2, 'dim')
    sh.line(p2[0] + nx * g, p2[1] + ny * g, b[0] + nx * g * 1.2, b[1] + ny * g * 1.2, 'dim')
    sh.line(a[0], a[1], b[0], b[1], 'dim')
    sh.arrow(a[0], a[1], -ux, -uy)
    sh.arrow(b[0], b[1], ux, uy)
    ang = math.degrees(math.atan2(uy, ux))
    if ang > 90 or ang <= -90:
        ang += 180
    sh.text((a[0] + b[0]) / 2 + nx * tdy * g, (a[1] + b[1]) / 2 + ny * tdy * g, label, 't', 'middle', ang)


def arc(sh, cx, cy, r, a0, a1, cls='dim'):
    """Arc about (cx, cy) from page angle a0 to a1 in degrees (y down, clockwise positive)."""
    p0 = (cx + r * math.cos(math.radians(a0)), cy + r * math.sin(math.radians(a0)))
    p1 = (cx + r * math.cos(math.radians(a1)), cy + r * math.sin(math.radians(a1)))
    sw = 1 if a1 > a0 else 0
    sh.add(f'<path d="M {p0[0]:.2f} {p0[1]:.2f} A {r:.2f} {r:.2f} 0 0 {sw} {p1[0]:.2f} {p1[1]:.2f}" class="{cls}"/>')
    return p0, p1


def vacuum_range(r, L):
    """Vacuum range (m) from the muzzle at LAUNCHER_V0 and LAUNCHER_ELEV, and the muzzle height above the waterline (m), from the hydro result."""
    xm, zm = L['muzzle']
    h = (zm - (r['d0'] - r['k'] * xm)) / 1000
    v, th, g = D.LAUNCHER_V0, math.radians(D.LAUNCHER_ELEV), D.GRAVITY
    return v * math.cos(th) / g * (v * math.sin(th) + math.sqrt((v * math.sin(th)) ** 2 + 2 * g * h)), h


def note(sh, x, y, head, text, width, step=3.1):
    """Wrapped note: a bold lead word, then the text; returns the next free y."""
    lines = wrap(head + ' ' + text, width - 8, 'ts')
    first = lines[0]
    sh.add(f'<text x="{x:.2f}" y="{y:.2f}" class="ts"><tspan style="font-weight:bold;fill:#111">{head}</tspan>{first[len(head):]}</text>')
    for ln in lines[1:]:
        y += step
        sh.text(x, y, ln, 'ts')
    return y + step + 1.2


def build(r=None, lrows=None):
    r = r or hydro.design()
    lrows = lrows or variants.launcher_rows(r)
    zd = r['deck']
    L = G.launcher(zd)
    sh = Sheet('A-701', 'Line launcher module, concept', 'Concept for review. All values ESTIMATE or PROPOSED, see design.py.', '1:2, 2:1, sequence NTS')
    s = 0.5
    th = L['e']
    bore, tlen, wall = D.LAUNCHER_TUBE
    od = L['od']
    fd, fl = D.LAUNCHER_MUZZLE_FUNNEL
    pd, plen = D.LAUNCHER_PISTON
    p0 = L['p0']
    pl_l, pl_w, pl_t = D.LAUNCHER_PLATE
    ddia, dlen, dmass = D.LAUNCHER_DART
    fdia, flen = D.LAUNCHER_FLOAT
    ldia, llen, lmass = D.LAUNCHER_LINE
    xmax = max(p[0] for p in L['funnel'])                      # far forward point of the module, X
    x0p, x1p = L['plate'][0], L['plate'][1]
    rs, ts_ = L['reel_servo'], L['trig_servo']
    t_bail, t_sear = D.LAUNCHER_TRIG_TRAVEL
    vac, h_mz = vacuum_range(r, L)
    apex = (D.LAUNCHER_V0 * math.sin(th)) ** 2 / (2 * D.GRAVITY)           # m above the muzzle
    fit = lrows[1]
    nof = lrows[0]

    # ================= 1. SIDE SECTION, 1:2, bow at left =================
    ox, dy0 = 21.0, 178.0                                      # page x of X = xmax, page y of the deck top
    xs = lambda X: ox + s * (xmax - X)
    zs = lambda Z: dy0 - s * (Z - L['deck'])
    P = lambda sn, n=0.0: tuple(f(v) for f, v in zip((xs, zs), L['at'](sn, n)))
    sh.text(58, 31, 'SIDE SECTION THROUGH THE TUBE AXIS, 1:2', 'tb')
    # deck, deck beam, plate
    sh.rect(xs(x1p + 30), dy0, (x1p + 30 - (x0p - 14)) * s, D.SKIN_T * s, 'cut')
    bw, bt = D.DECK_BEAM_W, D.DECK_BEAM_T
    sh.rect(xs(L['beam'] + bw / 2), dy0 + D.SKIN_T * s, bw * s, bt * s, 'cut', 'style="fill:#f1e3c8"')
    sh.rect(xs(x1p), zs(L['z_top']), (x1p - x0p) * s, pl_t * s, 'cut', BIRCH)
    # thumbscrew (beside the plane): head on the plate, shank through plate, deck and beam into the captive nut
    scx = xs(L['beam'])
    sh.rect(scx - LAY['head_k'], zs(L['z_top']) - LAY['head_h'], 2 * LAY['head_k'], LAY['head_h'], 'obj', 'style="fill:#bbb"')
    sh.line(scx, zs(L['z_top']), scx, dy0 + (D.SKIN_T + bt) * s, 'obj')
    sh.rect(scx - D.LAUNCHER_SCREW_D * s, dy0 + (D.SKIN_T + bt) * s, 2 * D.LAUNCHER_SCREW_D * s, 1.0, 'obj', 'style="fill:#888"')
    # servos beside the plane
    sh.rect(xs(rs.x1), zs(rs.z1), (rs.x1 - rs.x0) * s, (rs.z1 - rs.z0) * s, 'elec')
    sh.rect(xs(ts_.x1), zs(ts_.z1), (ts_.x1 - ts_.x0) * s, (ts_.z1 - ts_.z0) * s, 'elec')
    # stay from the plate fore edge to the tube underside
    (bx_, bz_), (ax_, az_) = L['brace']
    sh.line(xs(bx_), zs(bz_), xs(ax_), zs(az_), 'thk')
    # reel body, spool, bail and roller (beneath the tube, parallel to it)
    sh.poly([(xs(x), zs(z)) for x, z in L['reel']], 'gray')
    rl, rh = D.LAUNCHER_REEL_BODY
    sd, sl = D.LAUNCHER_SPOOL
    s0 = D.LAUNCHER_REEL_S0
    n_mid = -(od / 2 + D.LAUNCHER_REEL_GAP) - rh / 2
    sh.poly([P(s0, n_mid + sd / 2), P(s0 + sl, n_mid + sd / 2), P(s0 + sl, n_mid - sd / 2), P(s0, n_mid - sd / 2)], 'prop')
    rr_ = (s0 - LAY['roller_r'] * 3, n_mid)
    sh.pline([P(s0 + sl / 2, n_mid + LAY['bail_r']), P(s0 - LAY['roller_r'] * 3, n_mid + LAY['bail_r']), P(*rr_)], 'thk')            # bail, closed
    sh.pline([P(s0 + sl / 2, n_mid + LAY['bail_r']), P(s0 - LAY['roller_r'] * 3 - 3, n_mid + LAY['bail_r'] + 10), P(s0 - LAY['roller_r'] * 3 - 3, n_mid + 10)], 'hid')   # bail, open
    sh.circ(*P(*rr_), LAY['roller_r'], 'obj', 'style="fill:#fff"')
    # tube walls (the upper wall is open over the slot), breech cap, funnel
    sh.poly([P(0, -od / 2), P(tlen, -od / 2), P(tlen, -bore / 2), P(0, -bore / 2)], 'cut')
    slot0, slot1 = p0, p0 + D.LAUNCHER_STROKE
    for a_, b_ in ((0, slot0), (slot1, tlen)):
        sh.poly([P(a_, od / 2), P(b_, od / 2), P(b_, bore / 2), P(a_, bore / 2)], 'cut')
    sh.poly([P(slot0, od / 2), P(slot1, od / 2), P(slot1, bore / 2), P(slot0, bore / 2)], 'hid')
    sh.poly([P(-LAY['cap_t'], od / 2), P(0, od / 2), P(0, -od / 2), P(-LAY['cap_t'], -od / 2)], 'cut')
    sh.poly([P(tlen, od / 2), P(tlen + fl, fd / 2), P(tlen + fl, fd / 2 - wall), P(tlen, bore / 2)], 'cut')
    sh.poly([P(tlen, -od / 2), P(tlen + fl, -fd / 2), P(tlen + fl, -fd / 2 + wall), P(tlen, -bore / 2)], 'cut')
    sh.line(*P(-LAY['cap_t'] - 8, 0), *P(tlen + fl + 6, 0), 'ctr')
    # piston, cross pin through the slot, latex loop to the muzzle anchor
    sh.poly([P(p0, pd / 2), P(p0 + plen, pd / 2), P(p0 + plen, -pd / 2), P(p0, -pd / 2)], 'gray')
    pin_s = p0 + plen / 2
    n_pin = od / 2 + LAY['pin_up']
    sh.line(*P(pin_s, pd / 2), *P(pin_s, n_pin), 'thk')
    sh.line(*P(tlen, od / 2), *P(tlen, n_pin), 'thk')
    sh.add('<polyline points="%s" %s/>' % (' '.join('%.2f,%.2f' % P(a_, n_pin) for a_ in (pin_s, tlen)), LATEXC))
    # sear: a block ahead of the pin, tail toward the muzzle (lifted clear by the last part of the trigger travel)
    n_s0 = od / 2 + LAY['sear_gap']
    k0 = pin_s + LAY['pin_d']
    sh.poly([P(k0, n_s0), P(k0 + 3, n_s0), P(k0 + 3, n_s0 + 4), P(k0 + LAY['sear_l'], n_s0 + 4), P(k0 + LAY['sear_l'], n_s0 + LAY['sear_h']), P(k0, n_s0 + LAY['sear_h'])],
            'obj', 'style="fill:#999"')
    sear_tail = P(k0 + LAY['sear_l'] - 4, n_s0 + LAY['sear_h'] / 2)
    sh.circ(*sear_tail, 0.8, 'obj', 'style="fill:#fff"')
    # float, dart (foam and brass nose), seated in front of the piston
    nose = L['s_nose'] - D.LAUNCHER_NOSE_L
    s_f0 = p0 + plen
    sh.poly([P(s_f0, fdia / 2), P(s_f0 + flen, fdia / 2), P(s_f0 + flen, -fdia / 2), P(s_f0, -fdia / 2)], 'obj', FLOATC)
    sh.poly([P(L['s_dart'], ddia / 2), P(nose, ddia / 2), P(nose, -ddia / 2), P(L['s_dart'], -ddia / 2)], 'obj', FOAM)
    sh.poly([P(nose, ddia / 2), P(L['s_nose'], ddia / 2), P(L['s_nose'], -ddia / 2), P(nose, -ddia / 2)], 'obj', BRASS)
    # line: spool, bail roller, line guide, breech cap hole, along the tube to the float and the dart tail eye
    guide = (-LAY['guide_back'], -LAY['guide_down'])
    gx, gy = P(*guide)
    ptl = [P(s0 + sl / 2, n_mid + sd / 2), P(*rr_), P(*guide), P(-LAY['cap_t'], 0), P(L['s_dart'], 0)]
    sh.add('<polyline points="%s" %s/>' % (' '.join('%.2f,%.2f' % q for q in ptl), LINEC))
    sh.circ(gx, gy, LAY['ring_r'], 'obj', 'style="fill:#fff"')
    # trigger lever on the micro servo: first part of the travel opens the bail, the last part lifts the sear
    hxp, hzp = xs(ts_.x0 + D.LAUNCHER_SERVO_TRIG['l'] / 2), zs(ts_.z1)
    arm = D.LAUNCHER_TRIG_ARM * s
    sh.circ(hxp, hzp, 0.9, 'obj', 'style="fill:#fff"')
    ends = {}
    for ang, cls in ((0, 'thk'), (t_bail, 'hid'), (t_bail + t_sear, 'hid')):
        a = math.radians(ang)
        ends[ang] = (hxp - arm * math.cos(a), hzp - arm * math.sin(a))      # zero points forward (page left), then swings up
        sh.line(hxp, hzp, *ends[ang], cls)
    arc(sh, hxp, hzp, arm * 1.3, 180, 180 + t_bail, 'dim')
    arc(sh, hxp, hzp, arm * 1.7, 180 + t_bail, 180 + t_bail + t_sear, 'dim')
    sh.line(*ends[0], *P(*rr_), 'hid')                                       # rod to the bail roller
    sh.line(*ends[t_bail + t_sear], *sear_tail, 'hid')                       # rod to the sear tail (runs beside the tube)

    # ---- dimensions
    ztop = max(p[1] for p in L['funnel'])
    sh.dimv(zs(ztop), dy0, 16.0, '%.0f overall height above the deck' % L['height'], xs(max(p[0] for p in L['funnel'] if p[1] == ztop)), 18.0)
    adim(sh, P(0, 0), P(tlen, 0), -24, 'tube %.0f' % tlen)
    adim(sh, P(p0, 0), P(slot1, 0), -15, 'stroke %.0f' % D.LAUNCHER_STROKE)
    ap = P(tlen * 0.78, 0)                                                   # elevation: horizontal reference through a point on the axis, clear of the reel
    sh.line(ap[0], ap[1], ap[0] - 26, ap[1], 'ctr')
    arc(sh, ap[0], ap[1], 22, 180, 180 + D.LAUNCHER_ELEV, 'dim')
    sh.text(ap[0] - 26, ap[1] - 3.2, '%.0f deg' % D.LAUNCHER_ELEV, 't', 'start')
    sh.dimh(xs(x1p), xs(x0p), dy0 + 9, 'plate %.0f fore-aft x %.0f ply (%.0f across, see the plan)' % (pl_w, pl_t, pl_l), dy0 + pl_t * s, dy0 + pl_t * s, 1.8)
    bxx = xs(L['xb'])
    sh.dimv(zs(L['zb']), zs(L['z_top']), xs(x0p) + 3.6, '%.0f' % D.LAUNCHER_BREECH_Z, bxx, xs(x0p))
    yb = dy0 + 5.0                                                          # axis position from the aft edge, arrows outside the short span
    sh.line(bxx, dy0 + 1.0, bxx, yb + 1.2, 'dim')
    sh.line(xs(x0p), dy0 + 1.0, xs(x0p), yb + 1.2, 'dim')
    sh.line(bxx - 4.5, yb, xs(x0p) + 4.5, yb, 'dim')
    sh.arrow(bxx, yb, 1, 0)
    sh.arrow(xs(x0p), yb, -1, 0)
    sh.text(xs(x0p) + 6.0, yb + 0.9, '%.0f' % D.LAUNCHER_BREECH_INSET, 't')

    # ---- tags and key (the lower-left of the section is free, the key sits there)
    def tg(n, pt, tx, ty):
        sh.leader(pt[0], pt[1], tx, ty)
        sh.tag(tx, ty, n)
    tg(1, (xs(x1p) + 0.5, dy0 - 0.3), 80.0, 171.0)
    tg(2, (scx - 3, dy0 + 6.5), 121.0, 183.0)
    tg(3, P(200, -od / 2), 52.0, 88.0)
    tg(4, P(tlen + fl * 0.55, -fd / 4), 24.0, 52.0)
    tg(5, P(-LAY['cap_t'] / 2, od / 2), 156.0, 146.0)
    tg(6, P(p0 + plen / 2, -pd / 2), 152.0, 157.0)
    tg(7, P(pin_s, od / 2 + LAY['pin_up']), 156.0, 131.5)
    tg(8, P(110, n_pin), 126.0, 99.0)
    tg(9, P(k0 + LAY['sear_l'] / 2, n_s0 + LAY['sear_h']), 138.0, 127.0)
    tg(10, P(L['s_dart'] + 22, 0), 99.0, 118.0)
    tg(11, P(s_f0 + flen / 2, -fdia / 2), 135.0, 146.0)
    tg(12, P(s0 + rl * 0.6, n_mid - rh / 2 + 2), 94.0, 150.0)
    tg(13, (gx, gy), 133.0, 156.0)
    tg(14, (xs(ts_.x1) - 0.5, zs(ts_.z0 + 8)), 132.0, 172.0)
    tg(15, (xs(rs.x0 + 12), zs(rs.z1)), 100.0, 160.0)
    tg(16, ((xs(bx_) + xs(ax_)) / 2, (zs(bz_) + zs(az_)) / 2), 92.0, 131.0)
    key = ['1  plate, birch ply, on the deck', '2  thumbscrew (2) to a nut in a deck beam', '3  tube %.0f bore, %.0f long, %.1f wall' % (bore, tlen, wall),
           '4  muzzle funnel %.0f to %.0f over %.0f' % (fd, bore, fl), '5  breech cap, line hole on the axis', '6  piston, cocked',
           '7  cross pin in the slot (slot = stroke)', '8  latex loop, anchored at the muzzle', '9  sear, ahead of the pin',
           '10 dart, seated in front of the piston', '11 tail float, fixed on the line', '12 spinning reel, spool and bail', '13 line guide',
           '14 trigger servo (micro) with its lever:', '     0 to %.0f deg opens the bail,' % t_bail, '     %.0f to %.0f deg lifts the sear' % (t_bail, t_bail + t_sear),
           '15 reel servo, continuous rotation', '16 forward stay, plate to tube']
    ky = 117.0
    for i, k in enumerate(key):
        sh.text(24, ky + i * 3.3, k, 'ts')
    yk = ky + len(key) * 3.3 + 0.5
    sh.add(f'<line x1="24" y1="{yk:.2f}" x2="32" y2="{yk:.2f}" {LINEC}/>')
    sh.text(34, yk + 0.8, 'line (spool to dart eye)', 'ts')
    sh.text(24, yk + 4.2, 'Servos and reel lie beside the plane.', 'ts')

    # ================= 2. PLAN VIEW, 1:2, same scale =================
    px0, pyc = 154.0, 68.0
    xp = lambda X: px0 + s * (xmax - X)
    yp = lambda Y: pyc - s * Y
    sh.text(153, 31, 'PLAN VIEW, 1:2 (bow at left)', 'tb')
    cx0, cx1 = L['cap_x']
    clip = x0p - 7.0
    capy = L['cap_inner'] + 9.0                                               # the caps are drawn only this far out in Y
    for sg in (1, -1):                                                        # bow caps, phantom, cut short aft of the plate
        sh.rect(xp(cx1), yp(sg * capy) if sg > 0 else yp(sg * L['cap_inner']), (cx1 - clip) * s, (capy - L['cap_inner']) * s, 'hid')
    sh.text(xp(cx1) + 1.5, yp(L['cap_inner'] + 3.2), 'bow cap, phantom, X %.1f to %.1f' % (cx0, cx1), 'ts')
    sh.rect(xp(x1p), yp(pl_l / 2), pl_w * s, pl_l * s, 'obj', BIRCH)
    rxs = [p[0] for p in L['reel']]
    sh.rect(xp(max(rxs)), yp(sd / 2), (max(rxs) - min(rxs)) * s, sd * s, 'hid')
    sh.text(xp((max(rxs) + min(rxs)) / 2), yp(-sd / 2) + 2.6, 'reel, below the tube', 'ts', 'middle')
    sh.rect(xp(rs.x1), yp(rs.y1), (rs.x1 - rs.x0) * s, (rs.y1 - rs.y0) * s, 'elec')
    sh.text(xp((rs.x0 + rs.x1) / 2), yp((rs.y0 + rs.y1) / 2) + 0.8, 'reel servo', 'ts', 'middle')
    sh.rect(xp(ts_.x1), yp(ts_.y1), (ts_.x1 - ts_.x0) * s, (ts_.y1 - ts_.y0) * s, 'elec')
    sh.text(xp((ts_.x0 + ts_.x1) / 2), yp(ts_.y1) - 1.2, 'trigger servo', 'ts', 'middle')
    # tube and funnel footprint
    txs = [p[0] for p in L['tube']]
    sh.rect(xp(max(txs)), yp(od / 2), (max(txs) - min(txs)) * s, od * s, 'obj', 'style="fill:none"')
    mx_, mz_ = L['muzzle']
    ex_, ez_ = L['mouth']
    sh.add(f'<ellipse cx="{xp(mx_):.2f}" cy="{yp(0):.2f}" rx="{od / 2 * math.sin(th) * s:.2f}" ry="{od / 2 * s:.2f}" class="obj"/>')
    sh.add(f'<ellipse cx="{xp(ex_):.2f}" cy="{yp(0):.2f}" rx="{fd / 2 * math.sin(th) * s:.2f}" ry="{fd / 2 * s:.2f}" class="obj"/>')
    sh.line(xp(mx_), yp(od / 2), xp(ex_), yp(fd / 2), 'obj')
    sh.line(xp(mx_), yp(-od / 2), xp(ex_), yp(-fd / 2), 'obj')
    sh.line(xp(xmax + 6), yp(0), xp(x0p - 12), yp(0), 'ctr')
    for X_, Y_ in L['screws']:
        sh.circ(xp(X_), yp(Y_), D.LAUNCHER_SCREW_D * 1.25 * s, 'obj', 'style="fill:#bbb"')
        sh.circ(xp(X_), yp(Y_), D.LAUNCHER_SCREW_D * 0.5 * s, 'obj', 'style="fill:#555"')
    cxy = (xp(L['cable'][0]), yp(L['cable'][1]))
    sh.circ(cxy[0], cxy[1], D.LAUNCHER_CABLE_D / 2 * s, 'obj', 'style="fill:#fff"')
    sh.line(cxy[0], cxy[1], cxy[0] + 8, cxy[1], 'thin')
    sh.arrow(cxy[0] + 8, cxy[1], 1, 0)
    sh.text(cxy[0] + 9.0, cxy[1] + 0.8, 'cable exit', 'ts')
    # plan dimensions
    xd = xp(x0p - 2 * D.LAUNCHER_CABLE_D)
    sh.dimv(yp(L['screws'][0][1]), yp(L['screws'][1][1]), xp(x0p) + 3.6, '%.0f' % L['screw_spacing'], xp(L['screws'][0][0]), xp(L['screws'][1][0]))
    sh.dimv(yp(pl_l / 2), yp(-pl_l / 2), xp(x0p) + 9.2, '%.0f' % pl_l, xp(x0p), xp(x0p))
    sh.dimh(xp(x1p), xp(x0p), yp(-capy) + 4.0, '%.0f' % pl_w, yp(-pl_l / 2), yp(-pl_l / 2))
    sh.text(153, yp(-capy) + 10.0, 'Tunnel gap between the bow caps %.1f; the plate leaves %.2f each side (LAUNCHER_CAP_CLR %.0f).' % (2 * L['cap_inner'], L['gap'], D.LAUNCHER_CAP_CLR), 'ts')
    sh.text(153, yp(-capy) + 13.2, 'M%.0f thumbscrews %.0f apart on the deck beam (X %.0f to %.0f, below the deck); muzzle X %.0f, funnel mouth X %.0f.' % (
        D.LAUNCHER_SCREW_D, L['screw_spacing'], L['beam'] - bw / 2, L['beam'] + bw / 2, mx_, xmax), 'ts')

    # ================= 3. DART DETAIL, 2:1 =================
    k2 = 2.0
    xn, yc = 172.0, 160.0
    sh.text(164, 130.2, 'DART DETAIL, 2:1', 'tb')
    nl = D.LAUNCHER_NOSE_L
    tail = xn + dlen * k2
    top_, bot_ = yc - ddia * k2 / 2, yc + ddia * k2 / 2
    sh.rect(xn + nl * k2, top_, (dlen - nl) * k2, ddia * k2, 'obj', FOAM)
    sh.rect(xn, top_, nl * k2, ddia * k2, 'obj', BRASS)
    sh.rect(tail, yc - fdia * k2 / 2, flen * k2, fdia * k2, 'obj', FLOATC)
    sh.add(f'<line x1="{tail - 6:.2f}" y1="{yc:.2f}" x2="{tail + flen * k2 + 3:.2f}" y2="{yc:.2f}" {LINEB.replace(".4", ".8")}/>')
    sh.circ(tail - 2.5, yc, 2.2, 'obj', 'style="fill:#fff"')
    sh.dimh(xn, tail, top_ - 5, '%.0f' % dlen, top_, top_)
    sh.dimv(top_, bot_, xn - 5, '%.0f dia' % ddia, xn, xn)
    sh.dimh(xn, xn + nl * k2, bot_ + 5, '%.0f' % nl, bot_, bot_)
    sh.dimh(tail, tail + flen * k2, bot_ + 5, '%.0f' % flen, bot_, bot_)
    sh.text(xn, bot_ + 10.0, 'brass nose weight', 'ts')
    sh.text(xn + 75, yc + 1, 'closed-cell foam cylinder', 't', 'middle')
    sh.text(tail + flen * k2, bot_ + 10.0, 'bright tail float', 'tb', 'end')
    sh.text(tail - 4, yc + 5.2, 'line eye', 'ts', 'end')
    sh.text(tail + flen * k2, top_ - 10.0, 'tail float = the toggle: it stops the line', 'ts', 'end')
    sh.text(tail + flen * k2, top_ - 7.0, 'pulling through the rigging', 'ts', 'end')
    sh.text(164, 193.6, 'Brass nose %.1f g (%.0f dia x %.0f at %.1f g/cm3, computed) plus foam and eye: %.0f g in all (LAUNCHER_DART).' % (
            L['nose_mass'], ddia, nl, D.LAUNCHER_BRASS_RHO, dmass), 'ts')

    # ================= 4. SHOT SEQUENCE, schematic, four panels =================
    sh.text(14, 198.4, 'SHOT SEQUENCE (schematic, not to scale; heights are in proportion to LAUNCHER_TARGET)', 'tb')
    pw, ph, gap = 62.0, 52.0, 3.5
    wl = 40.0
    kk = 22.0 / (D.LAUNCHER_TARGET[1] / 1000)                                  # units per m: the mast drawn 22 high
    mast_h = D.LAUNCHER_TARGET[1] / 1000 * kk
    ya0, ya1, ymast = 3.0, 25.0, 12.5                                           # yacht hull aft end, bow, mast
    bo = 34.0                                                                   # barge bow
    deck_u = (L['deck'] - (r['d0'] - r['k'] * x0p)) / 1000 * kk
    plate_u0 = bo + 2.0
    caps = ['(a) AIM', '(b) FIRE', '(c) DRAPE', '(d) REEL IN']
    caption = ['Steer the barge at the yacht, %.0f to %.0f m away. The tube is fixed, so aiming is steering.' % (D.LAUNCHER_AIM_DIST[0] / 1000, D.LAUNCHER_AIM_DIST[1] / 1000),
               'Trigger: the first %.0f deg opens the bail, the last %.0f deg lifts the sear. %.0f deg arc, apex %.2f m above the muzzle, dart lands beyond the yacht.' % (t_bail, t_sear, D.LAUNCHER_ELEV, apex),
               'The line lies through the gap between the mast and the jib luff, the dart afloat beyond.',
               'Reel in: the line comes taut on the mast or forestay fitting, the tail float jams as a toggle, the barge tows.']

    for i in range(4):
        x0 = 14.0 + i * (pw + gap)
        y0 = 201.0
        U = lambda u, v, x0=x0, y0=y0: (x0 + u, y0 + v)
        sh.rect(x0, y0, pw, ph, 'thin', 'style="fill:#fff"')
        sh.rect(x0, y0 + wl, pw, ph - wl, 'water')
        sh.line(x0, y0 + wl, x0 + pw, y0 + wl, 'wl')
        sh.text(x0 + 1.5, y0 + 4.0, caps[i], 'tb')
        # yacht, bow toward the barge
        fx0, fz0 = ymast, wl - mast_h                                           # masthead
        bowp = (ya1, wl - 2.5)
        sh.poly([U(ya0, wl - 2.5), U(ya1, wl - 2.5), U(ya1 - 3, wl + 1.5), U(ya0 + 3, wl + 1.5)], 'obj', 'style="fill:#fff"')
        head = (fx0 + (bowp[0] - fx0) * 0.22, fz0 + (bowp[1] - fz0) * 0.22)
        tack = (fx0 + (bowp[0] - fx0) * 0.97, fz0 + (bowp[1] - fz0) * 0.97)
        clew = (head[0] + 0.8, wl - 4.5)
        sh.poly([U(*head), U(*tack), U(*clew)], 'thin', 'style="fill:#f4f4f4"')
        sh.line(*U(fx0, fz0), *U(*bowp), 'obj')
        # barge, bow to the left, launcher near the bow
        sh.poly([U(bo, wl - deck_u), U(bo + 22, wl - deck_u), U(bo + 22, wl + 2), U(bo + 3, wl + 2)], 'obj', 'style="fill:#e4e4e4"')
        bx = bo + 11.0
        by = wl - deck_u - D.LAUNCHER_BREECH_Z / 1000 * kk
        tl_u = tlen / 1000 * kk
        mzu = (bx - tl_u * math.cos(th), by - tl_u * math.sin(th))
        sh.line(*U(bx, wl - deck_u), *U(bx, by), 'thk')
        sh.line(*U(bx, by), *U(*mzu), 'thk')
        sh.circ(*U(*mzu), 0.9, 'obj', 'style="fill:#fff"')
        sh.line(*U(bx - 5, wl - deck_u), *U(bx + 5, wl - deck_u), 'thk')
        mz = mzu
        # ballistic path from the muzzle, heights from the model, the horizontal stretched to the panel
        h0 = h_mz
        vy = D.LAUNCHER_V0 * math.sin(th)
        T = (vy + math.sqrt(vy ** 2 + 2 * D.GRAVITY * h0)) / D.GRAVITY
        land_u = ya0 - 0.5

        def path(frac=1.0, n=24):
            pts = []
            for j in range(n + 1):
                f = frac * j / n
                tau = f * T
                z = h0 + vy * tau - D.GRAVITY * tau ** 2 / 2
                pts.append((mz[0] + (land_u - mz[0]) * f, wl - z * kk))
            return pts
        if i == 0:
            sh.text(*U(ya0 + 8, wl + 5.2), 'yacht', 'ts', 'middle')
            sh.text(*U(bo + 11, wl + 5.2), 'barge', 'ts', 'middle')
            sh.line(*U(bo - 1, wl - 6), *U(bo - 7, wl - 6), 'thk')
            sh.arrow(*U(bo - 7, wl - 6), -1, 0)
            sh.text(*U(bo - 4, wl - 7.6), 'heading', 'ts', 'middle')
            yy = wl + 8.5
            sh.line(*U(ya1, wl + 1), *U(ya1, yy + 1.5), 'dim')
            sh.line(*U(bo, wl + 1), *U(bo, yy + 1.5), 'dim')
            sh.line(*U(ya1, yy), *U(bo, yy), 'dim')
            sh.arrow(*U(ya1, yy), 1, 0)
            sh.arrow(*U(bo, yy), -1, 0)
            sh.text(*U((ya1 + bo) / 2, yy + 3.2), '%.0f to %.0f m' % (D.LAUNCHER_AIM_DIST[0] / 1000, D.LAUNCHER_AIM_DIST[1] / 1000), 't', 'middle')
        if i == 1:
            pts = path()
            sh.add('<polyline points="%s" style="stroke:#555;stroke-width:.3;fill:none;stroke-dasharray:1.6 1"/>' % ' '.join('%.2f,%.2f' % U(*q) for q in pts))
            sh.add('<polyline points="%s" %s/>' % (' '.join('%.2f,%.2f' % U(*q) for q in pts[:-1]), LINEB))
            top = min(pts, key=lambda q: q[1])
            sh.line(*U(top[0], top[1]), *U(top[0], mz[1]), 'dim')
            sh.arrow(*U(top[0], top[1]), 0, 1)
            sh.text(*U(top[0] + 1.6, top[1] + 6.5), 'apex', 'ts')
            sh.text(*U(top[0] + 1.6, top[1] + 9.5), '%.2f m' % apex, 'ts')
            dx_, dy_ = pts[-1]
            sh.circ(*U(dx_, dy_ - 0.8), 1.1, 'obj', FLOATC)
            sh.text(*U(mz[0] - 3, mz[1] - 4.5), '%.0f deg' % D.LAUNCHER_ELEV, 'ts', 'end')
        if i in (2, 3):
            if i == 2:
                lp = [mz, (bo - 5, wl - 21), (ymast + 7.5, wl - mast_h - 2.2), (ymast + 2.2, wl - mast_h + 3.5), (ymast + 2.4, wl - 9.0), (ya0 + 1.5, wl - 1.0)]
                sh.add('<polyline points="%s" %s/>' % (' '.join('%.2f,%.2f' % U(*q) for q in lp), LINEB))
                sh.circ(*U(lp[-1][0] - 0.6, lp[-1][1] + 0.6), 1.0, 'obj', FLOATC)
                sh.poly([U(lp[-1][0] - 2.8, lp[-1][1] + 1.0), U(lp[-1][0] - 1.4, lp[-1][1] + 0.0), U(lp[-1][0] - 1.4, lp[-1][1] + 1.9)], 'obj', BRASS)
            else:
                J = (ymast + 1.7, wl - mast_h + 4.4)
                sh.add('<polyline points="%s" %s/>' % (' '.join('%.2f,%.2f' % U(*q) for q in (mz, J)), LINEB))
                sh.add('<polyline points="%s" style="stroke:#1d4ed8;stroke-width:.3;fill:none;stroke-dasharray:1 .8"/>' % ' '.join('%.2f,%.2f' % U(*q) for q in (J, (ya0 + 4, wl - 5.5))))
                sh.circ(*U(*J), 1.5, 'obj', FLOATC)
                sh.poly([U(ya0 + 2.3, wl - 4.6), U(ya0 + 4.4, wl - 5.9), U(ya0 + 4.6, wl - 4.5)], 'obj', BRASS)
                sh.text(*U(J[0] + 3.5, J[1] - 5.8), 'float jams', 'ts', 'start')
                sh.leader(*U(J[0] + 3.4, J[1] - 5.0), *U(J[0] + 0.9, J[1] - 0.7))
                yy = wl + 6.0
                sh.line(*U(bo + 4, yy), *U(bo + 21, yy), 'thk')
                sh.arrow(*U(bo + 21, yy), 1, 0)
                sh.text(*U(bo + 12, yy + 3.2), 'tow', 'ts', 'middle')
        # mast on top
        sh.line(*U(fx0, wl - 2.5), *U(fx0, fz0), 'thk')
        for j, t in enumerate(textwrap_lines(caption[i], pw - 1.5)):
            sh.text(x0 + 0.8, y0 + ph + 3.6 + j * 3.1, t, 'ts')

    # ================= 5. CYCLE table, 6. NOTES, trim rows =================
    X0, WR = 318.0, 102.0
    cyc = [('1 aim', 'steering servo (existing)', 'steer the barge at the yacht, %.0f to %.0f m away' % (D.LAUNCHER_AIM_DIST[0] / 1000, D.LAUNCHER_AIM_DIST[1] / 1000)),
           ('2 fire', 'trigger servo, micro', 'one sweep: %.0f deg opens the reel bail, then %.0f deg lifts the sear; the latex drives the piston and the dart out' % (t_bail, t_sear)),
           ('3 reel in', 'reel servo, continuous', 'dart returns tail-first through the funnel, pushes the piston back %.0f, the sear clicks' % D.LAUNCHER_STROKE),
           ('4 slack', 'reel servo', 'the reel backs off one turn so the line has slack'),
           ('5 ready', 'none', 'cocked, bail closed, dart seated in front of the piston')]
    y = wtable(sh, X0, 38, [('STEP', 17), ('SERVO', 33), ('ACTION', WR - 50)], cyc, 'CYCLE (two launcher servos only, %s and %s)' % ('trigger', 'reel'), 'ts', 3.1, 1.2)
    y += 5
    sh.text(X0, y, 'NOTES (physics and assumptions, each names its constant)', 'tb')
    y += 4.2
    mboat = fit['W'] / 1000
    imp = dmass / 1000 * D.LAUNCHER_V0
    ke = 0.5 * dmass / 1000 * D.LAUNCHER_V0 ** 2
    y = note(sh, X0, y, 'Range.', 'LAUNCHER_RANGE %.2f m is the design range, a fixed shot. In vacuum the dart would fly %.2f m from the muzzle (%.2f m above the water); drag and the trailing line cut it to the design value (ESTIMATE, bench test).' % (D.LAUNCHER_RANGE / 1000, vac, h_mz), WR)
    y = note(sh, X0, y, 'Speed.', 'LAUNCHER_V0 %.1f m/s at LAUNCHER_ELEV %.0f deg gives an apex %.2f m above the muzzle, %.2f m above the water, against a mast %.2f m above its deck (LAUNCHER_TARGET).' % (
        D.LAUNCHER_V0, D.LAUNCHER_ELEV, apex, apex + h_mz, D.LAUNCHER_TARGET[1] / 1000), WR)
    y = note(sh, X0, y, 'Energy.', 'LAUNCHER_E_FLIGHT %.2f J in the dart (1/2 x %.0f g x %.1f m/s = %.2f J); LAUNCHER_E_STORED %.1f J in the latex, so %.0f percent reaches the dart.' % (
        D.LAUNCHER_E_FLIGHT, dmass, D.LAUNCHER_V0, ke, D.LAUNCHER_E_STORED, 100 * D.LAUNCHER_E_FLIGHT / D.LAUNCHER_E_STORED), WR)
    y = note(sh, X0, y, 'Cocking.', 'LAUNCHER_COCK_F %.0f N peak over the %.0f stroke (LAUNCHER_STROKE), pulled in slowly through the line by the reel servo.' % (D.LAUNCHER_COCK_F, D.LAUNCHER_STROKE), WR)
    y = note(sh, X0, y, 'Recoil.', 'Dart mass x LAUNCHER_V0 = %.0f g x %.1f m/s = %.3f N s against the boat mass %.2f kg (model, launcher fitted): %.0f mm/s, negligible.' % (
        dmass, D.LAUNCHER_V0, imp, mboat, imp / mboat * 1000), WR)
    y = note(sh, X0, y, 'Line.', 'LAUNCHER_LINE: %.1f mm braided polyethylene floating line, %.0f m, %.0f g. It floats, so it lies on the water clear of the nozzles.' % (ldia, llen / 1000, lmass), WR)
    y = note(sh, X0, y, 'Why %.0f deg fixed.' % D.LAUNCHER_ELEV, 'The apex is near masthead height, so the descending leg falls through the foretriangle. A flat shot crosses at deck level into the boom and rails. Anything inside LAUNCHER_RANGE is draped, so there is no elevation servo.', WR)
    y = note(sh, X0, y, 'Fixed spool.', 'LAUNCHER_REEL (%s) has no spool inertia at launch: the line peels off the spool end once the trigger opens the bail.' % D.LAUNCHER_REEL.split(',')[0], WR)
    y = note(sh, X0, y, 'Cocking by the reel.', 'Reeling in pulls the dart back tail-first into the funnel and the piston to the sear. This removes a third servo; LAUNCHER_COCK_F passes through the line slowly.', WR)
    y = note(sh, X0, y, 'Mount.', 'LAUNCHER_MOUNT. LAUNCHER_MASS %.0f g at LAUNCHER_LCG_X %.0f; LAUNCHER_FITTED is %s, so the model carries no launcher until it is set.' % (D.LAUNCHER_MASS, D.LAUNCHER_LCG_X, D.LAUNCHER_FITTED), WR)
    y = note(sh, X0, y, 'Fit.', 'LAUNCHER_PLATE %.0f x %.0f sits between the bow caps (X %.0f to %.0f, %.1f apart), %.2f clear each side. The funnel mouth reaches X %.0f, %.0f past the bow tip and %.0f past the push bar face, %.0f above the deck.' % (
        pl_l, pl_w, L['cap_x'][0], L['cap_x'][1], 2 * L['cap_inner'], L['gap'], xmax, xmax - D.LOA, xmax - G.BUMPER_X1, L['height']), WR)
    trows = [('weight g', '%.1f' % nof['W'], '%.1f' % fit['W']), ('LCG from the transom', '%.1f' % nof['G'], '%.1f' % fit['G']),
             ('stern draft d0', '%.2f' % nof['d0'], '%.2f' % fit['d0']), ('bow draft', '%.2f' % nof['bow'], '%.2f' % fit['bow']),
             ('trim, deg bow down', '%.3f' % -nof['trim'], '%.3f' % -fit['trim']), ('water over nozzle top', '%.1f' % nof['over'], '%.1f' % fit['over']),
             ('margin after the %.0f trough' % D.TROUGH, '%.1f' % nof['margin'], '%.1f' % fit['margin']), ('checks failed', ', '.join(nof['failed']) or 'none', ', '.join(fit['failed']) or 'none')]
    wtable(sh, X0, y + 4.5, [('TRIM, BATTERIES AT %.0f' % D.DESIGN_BAT_X, 46), ('NOT FITTED', 28), ('FITTED', 28)], trows,
           'TRIM, LAUNCHER NOT FITTED AND FITTED (each on its own deck, from the model)', 'ts', 3.1, 1.2)
    return sh


def textwrap_lines(text, width_mm):
    return wrap(text, width_mm, 'ts')
