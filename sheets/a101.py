"""A-101 General arrangement: centerline profile and plan, every number from the model."""
import math, textwrap
from .lib import *
from .tbl import para
import design as D
from model import geometry as G, hydro


def build(r=None, alts=None):
    r = r or hydro.design()
    alts = alts or [hydro.at(x, r) for x in D.ALT_BAT_X]
    trim_rows = [(D.DESIGN_BAT_X, r)] + list(zip(D.ALT_BAT_X, alts))     # design position first, then the alternates on the same deck
    zd = r['deck']
    wl = lambda X: r['d0'] - r['k'] * X
    T = D.SKIN_T
    sh = Sheet('A-101', 'General arrangement',
               'Centerline profile and plan. Blade extended solid, retracted dashed. Variant: %s.' % D.BLADE_VARIANT, '1:3')
    s = 1 / 3
    ox = 36
    xs = lambda X: ox + s * (D.LOA - X)
    oy = 92
    zs = lambda Z: oy - s * Z
    P = lambda pts: [(xs(x), zs(z)) for x, z in pts]
    # water
    sh.add(f'<polygon points="{xs(D.LOA+12):.1f},{zs(wl(D.LOA)):.1f} {xs(-110):.1f},{zs(wl(-110)):.1f} {xs(-110):.1f},{zs(-120):.1f} {xs(D.LOA+12):.1f},{zs(-120):.1f}" class="water" opacity=".55"/>')
    # hull outline, roof, deck, push pad, aft deck
    sh.poly(P([(D.LOA, 0), (0, 0), (0, zd(0)), (D.LOA, zd(D.LOA))]), 'thin', 'style="fill:none"')
    sh.rect(xs(D.LOA), zs(G.ROOF_Z1), D.LOA * s, T * s, 'cut')
    sh.poly(P([(D.LOA, zd(D.LOA)), (0, zd(0)), (0, zd(0) - T), (D.LOA, zd(D.LOA) - T)]), 'cut')
    for h in G.hatch_rects():
        if h['yc'] >= 0:
            for X in (h['x0'], h['x1']):
                sh.line(xs(X), zs(zd(X)) - 1.6, xs(X), zs(zd(X) - T) + 1.6, 'thin')
    # push bar on the bow caps (balsa core, ply face on the front), mount arm on the deck top (behind the section plane), aft deck box (section through the beam at Y = YS)
    bz0, bz1 = G.bumper_z0(zd), G.bumper_z1(zd)
    am = G.bumper_arms(zd)
    sh.rect(xs(am['x1']), zs(am['z1']), am['L'] * s, am['t'] * s, 'gray')
    sh.rect(xs(G.BUMPER_X1), zs(bz1), D.BUMPER_T * s, (bz1 - bz0) * s, 'cut')
    sh.rect(xs(G.BUMPER_X1), zs(bz1), D.BUMPER_FACE_T * s, (bz1 - bz0) * s, 'thk')
    sh.dimv(zs(wl(D.LOA)), zs(bz0), xs(G.BUMPER_X1) - 4, '%.0f' % D.BUMPER_WL_CLR, xs(G.BUMPER_X1), xs(G.BUMPER_X1))
    Ld = D.AFT_DECK_L
    sh.poly(P([(0, zd(0)), (-Ld, zd(-Ld)), (-Ld, zd(-Ld) - D.AFT_DECK_T), (0, zd(0) - D.AFT_DECK_T)]), 'cut')
    sh.poly(P([(0, zd(0) - D.AFT_DECK_DEPTH + G.AFT_SKIN_LOW_T), (-Ld, zd(-Ld) - D.AFT_DECK_DEPTH + G.AFT_SKIN_LOW_T), (-Ld, zd(-Ld) - D.AFT_DECK_DEPTH), (0, zd(0) - D.AFT_DECK_DEPTH)]), 'cut')
    sh.poly(P([(0, zd(0) - D.AFT_DECK_T), (-Ld, zd(-Ld) - D.AFT_DECK_T), (-Ld, zd(-Ld) - D.AFT_DECK_DEPTH + G.AFT_SKIN_LOW_T), (0, zd(0) - D.AFT_DECK_DEPTH + G.AFT_SKIN_LOW_T)]), 'cut', 'style="fill:#f1e3c8"')
    # skeg and shoe (near side)
    sh.poly(P(G.SKEG), 'gray'); sh.poly(P(G.SHOE), 'gray')
    # stern tube level, shaft angled, CV joint
    for dz in (D.TUBE_OD / 2, -D.TUBE_OD / 2):
        sh.line(xs(D.CV_X), zs(D.PROP_Z + dz), xs(G.NOZ_XF), zs(D.PROP_Z + dz), 'hid')
    sh.line(xs(D.CV_X), zs(D.PROP_Z), xs(G.SHOE_X1), zs(D.PROP_Z), 'ctr')
    sh.line(xs(D.CV_X), zs(D.PROP_Z), xs(G.MOT_X0), zs(G.F[1]), 'obj')
    sh.circ(xs(D.CV_X), zs(D.PROP_Z), D.CV_OD_ASSUMED / 2 * s, 'prop')
    # motor and mount
    sh.poly(P(G.MOUNT), 'gray'); sh.poly(P(G.MOT), 'prop')
    # battery at design position (solid), slide extent dashed
    b0 = G.battery_boxes(D.DESIGN_BAT_X)[0]
    sh.rect(xs(b0[1]), zs(b0[5]), (b0[1] - b0[0]) * s, (b0[5] - b0[4]) * s, 'elec')
    lo, hi = G.battery_xrange(D.BAT_SLIDE[0])[0], G.battery_xrange(D.BAT_SLIDE[1])[1]
    sh.rect(xs(hi), zs(b0[5]), (hi - lo) * s, (b0[5] - b0[4]) * s, 'hid')
    sh.rect(xs(hi), zs(D.SKIN_T + D.BAT['rail']), (hi - lo) * s, D.BAT['rail'] * s, 'hid')
    # roof equipment (center compartment, hidden)
    for bx in (G.esc_boxes()[0], G.rx_box(), G.steer_servo_box()):
        sh.rect(xs(bx[1]), zs(bx[5]), (bx[1] - bx[0]) * s, (bx[5] - bx[4]) * s, 'hid')
    # nozzle, post
    sh.rect(xs(G.NOZ_XF), zs(G.NOZ_ZTOP), D.NOZ_L * s, D.NOZ_OD * s, 'prop')
    sh.rect(xs(G.POSTX) - D.NOZ_POST_D * s / 2, zs(zd(G.POSTX) - D.AFT_DECK_T), D.NOZ_POST_D * s, (zd(G.POSTX) - D.AFT_DECK_T - G.NOZ_ZTOP) * s, 'prop')
    sh.line(xs(G.POSTX), zs(zd(G.POSTX) + 6), xs(G.POSTX), zs(G.NOZ_ZBOT - 6), 'ctr')
    # steering linkage: pushrod from the servo output to the tie bar at ZR, horn boss, transom bellows
    sh.rect(xs(0), zs(G.ZR + D.BELLOWS_OD / 2), D.BELLOWS_L * s, D.BELLOWS_OD * s, 'gray')
    sh.line(xs(G.ROD_X0), zs(G.ZR), xs(G.ROD_X1), zs(G.ZR), 'thk')
    sh.circ(xs(G.ROD_X0), zs(G.ZR), 0.7, 'obj', 'style="fill:#111"')
    sh.rect(xs(G.POSTX) - D.TIE_BAR * s / 2, zs(G.ZR) - D.TIE_BAR * s / 2, D.TIE_BAR * s, D.TIE_BAR * s, 'obj', 'style="fill:#c9a24a"')
    sh.circ(xs(G.ROD_X1), zs(G.ZR), 0.6, 'obj', 'style="fill:#fff"')
    # trunk, tower, blade
    tx0, tx1 = G.trunk_x(); bp = G.blade_params(); hs = G.housing(zd)
    ux0, ux1 = (hs['x0'], hs['x1']) if hs else (tx0, tx1)
    sh.rect(xs(tx1), zs(zd(tx1) - T), (tx1 - tx0) * s, (zd(tx1) - 2 * T) * s, 'hid')
    if hs and hs['kind'] == 'tower':
        sh.rect(xs(ux1), zs(zd(ux1) + D.TOWER_H), (ux1 - ux0) * s, D.TOWER_H * s, 'gray')
    elif hs:
        sh.poly(P([(ux0, zd(ux0)), (ux1, zd(ux1)), (ux1, hs['top'](ux1)), (ux0, hs['top'](ux0))]), 'gray')
    bb = G.blade_servo_box(zd) if bp['housing'] == 'cap' else None
    if bb:
        spx, spz = G.spool_pos(zd)
        ae, as_ = G.line_attach(True), G.line_attach(False)
        sh.rect(xs(bb.x1), zs(bb.z1), (bb.x1 - bb.x0) * s, (bb.z1 - bb.z0) * s, 'elec')
        sh.line(xs(ae[0]), zs(ae[1]), xs(spx), zs(spz), 'thk')                    # lift line, blade extended: straight up from the upper edge
        sh.line(xs(as_[0]), zs(as_[1]), xs(spx), zs(spz), 'hid')                  # lift line, blade stowed
        sh.circ(xs(spx), zs(spz), 1.2, 'obj', 'style="fill:#fff"')
        sh.circ(xs(ae[0]), zs(ae[1]), 0.6, 'obj', 'style="fill:#111"')
        sh.text(xs(bb.x0) + 1.5, zs(bb.z0) + 3.4, 'servo', 'ts', 'start')
    sh.poly(P(G.blade_outline(True)), 'blade')
    sh.poly(P(G.blade_outline(False)), 'hid')
    sh.circ(xs(bp['hinge_x']), zs(bp['hinge_z']), 0.8, 'obj', 'style="fill:#fff"')
    sh.line(xs(D.LOA + 12), zs(wl(D.LOA)), xs(-110), zs(wl(-110)), 'wl')

    def tg(n, X, Z, dx=0, dz=10):
        sh.tag(xs(X) + dx, zs(Z + dz), n); sh.leader(xs(X) + dx, zs(Z + dz) + (2.3 if dz > 0 else -2.3), xs(X), zs(Z))
    tg(1, (G.BUMPER_X0 + G.BUMPER_X1) / 2, bz0, 0, -22)
    tg(2, 560, zd(560), 0, 14)
    tg(3, D.ESC['x0'] + D.ESC['l'] / 2, G.esc_boxes()[0][5], 0, 22)
    tg(4, D.DESIGN_BAT_X, b0[4], 0, -34)
    tg(5, G.MOT_CG[0], G.MOT_TOP, -9, 22)
    tg(6, D.CV_X, D.PROP_Z, 0, -30)
    tg(7, 110, G.shaft_z(110), 0, -40)
    tg(8, G.SKEG_X0 * 0.6, G.skeg_bot(G.SKEG_X0 * 0.6), 0, -30)
    tg(9, G.POSTX, G.NOZ_ZBOT, 0, -18)
    tg(10, G.POSTX, zd(G.POSTX) - T, 8, 16)
    tg(11, D.STEER_SERVO['x0'] + D.STEER_SERVO['l'] / 2, G.steer_servo_box()[5], 6, 26)
    tg(12, D.RX['x0'] + D.RX['l'] / 2, G.rx_box()[5], 6, 30)
    tg(13, -D.AFT_DECK_L + 8, zd(-D.AFT_DECK_L), 0, 20)
    tg(14, hs['x0'], hs['top'](hs['x0']), 7, 7)
    tg(15, 640, G.ROOF_Z1, 0, -26)
    tg(17, (G.ROD_X0 + G.ROD_X1) / 2, G.ZR, 0, 20)
    tg(18, G.POSTX, G.ZR, 9, -16)
    if bb:
        tg(16, (bb.x0 + bb.x1) / 2, bb.z1, 0, 14)
    # dims
    yb = zs(-125)
    sh.dimh(xs(0), xs(G.SHOE_X1), yb, '%.0f shoe' % (-G.SHOE_X1), zs(G.SHOE_BOT), zs(G.SHOE_BOT))
    sh.dimv(zs(zd(0)), zs(0), xs(90), '%.1f' % zd(0), xs(0), xs(0))
    sh.dimv(zs(zd(D.LOA)), zs(0), xs(D.LOA) - 14, '%.1f' % zd(D.LOA), xs(D.LOA), xs(D.LOA))
    sh.dimv(zs(0), zs(G.SHOE_BOT), xs(G.SKEG_X0) + 6, '%.1f' % (-G.SHOE_BOT), xs(0), xs(0))
    sh.dimv(zs(wl(G.POSTX)), zs(G.NOZ_ZTOP), xs(G.POSTX) + 18, '%.1f' % r['over'], xs(G.POSTX), xs(G.POSTX))
    sh.text(xs(620), zs(-100), 'WL at rest, batteries at %.0f: stern draft %.1f, bow draft %.1f; deck parallel to WL (%.2f deg to keel)' % (
        D.DESIGN_BAT_X, r['d0'], r['bow'], -r['trim']), 'ts')
    sh.text(xs(200), zs(G.shaft_z(200)) + 9, 'shaft %.0f deg' % D.MOTOR_AXIS_DEG, 'ts', 'middle')
    sh.text(xs(bp['hinge_x']) - 2, zs(bp['hinge_z']) + 4, 'hinge', 'ts', 'end')
    sh.text(xs(G.blade_centroid(True)[0]) - 2, zs(G.blade_centroid(True)[1]) + 1, 'blade extended', 'ts', 'end')
    sh.text(xs(G.blade_centroid(False)[0]) - 2, zs(G.blade_centroid(False)[1]), 'retracted', 'ts', 'end')
    # ---- plan
    oy2 = 190
    ys = lambda Y: oy2 - s * Y
    Pp = lambda pts: [(xs(x), ys(y)) for x, y in pts]
    for sg in (1, -1):
        outer = [(x, sg * float(G.outer_wall_y(x))) for x in G.PLAN_STATIONS]
        inner = [(x, sg * float(G.inner_wall_y(x))) for x in reversed(G.PLAN_STATIONS)]
        sh.poly(Pp(outer + inner), 'obj', 'style="fill:#fff"')
        yc = sg * G.YS
        yb_ = sg * G.blade_y()
        bx = G.battery_boxes(D.DESIGN_BAT_X)[0 if sg > 0 else 1]
        sh.rect(xs(hi), ys(sg * G.BAT_YC) - D.BAT['w'] / 2 * s, (hi - lo) * s, D.BAT['w'] * s, 'hid')
        sh.rect(xs(bx[1]), ys(bx[3]), (bx[1] - bx[0]) * s, (bx[3] - bx[2]) * s, 'elec')
        sh.rect(xs(G.MOT_XMAX), ys(yc + G.BODY_D / 2), (G.MOT_XMAX - G.MOT_XMIN) * s, G.BODY_D * s, 'prop')
        sh.line(xs(D.CV_X), ys(yc), xs(G.SHOE_X1), ys(yc), 'ctr')
        sh.rect(xs(G.SKEG_X0), ys(yc) - D.SKEG_W / 2 * s, (G.SKEG_X0 - G.SHOE_X1) * s, D.SKEG_W * s, 'hid')
        sh.rect(xs(G.NOZ_XF), ys(yc) - D.NOZ_OD / 2 * s, D.NOZ_L * s, D.NOZ_OD * s, 'prop')
        sh.circ(xs(G.POSTX), ys(yc), D.NOZ_POST_D * s / 2 + 0.3, 'obj')
        for X in G.BH:
            sh.line(xs(X), ys(float(G.inner_wall_y(X)) * sg), xs(X), ys(float(G.outer_wall_y(X)) * sg), 'thin')
        sh.rect(xs(tx1), ys(yb_ + bp['trunk_w'] / 2), (tx1 - tx0) * s, bp['trunk_w'] * s, 'hid')
        wb = max(G.blade_thickness() * s, 1.2)
        xe = [p[0] for p in G.blade_outline(True)]; xr = [p[0] for p in G.blade_outline(False)]
        sh.rect(xs(max(xe)), ys(yb_) - wb / 2, (max(xe) - min(xe)) * s, wb, 'blade')
        sh.rect(xs(max(xr)), ys(yb_) - wb / 2 - 0.3, (max(xr) - min(xr)) * s, wb + 0.6, 'hid')
    # steering linkage in plan: bellows at the transom, pushrod, tie bar, horns (point to port)
    sh.rect(xs(0), ys(G.ROD_Y + D.BELLOWS_OD / 2), D.BELLOWS_L * s, D.BELLOWS_OD * s, 'gray')
    sh.line(xs(G.ROD_X0), ys(G.ROD_Y), xs(G.ROD_X1), ys(G.ROD_Y), 'thk')
    sh.circ(xs(G.ROD_X0), ys(G.ROD_Y), 0.7, 'obj', 'style="fill:#111"')
    sh.rect(xs(G.POSTX) - D.TIE_BAR * s / 2, ys(G.TIE_Y1), D.TIE_BAR * s, G.TIE_L * s, 'obj', 'style="fill:#c9a24a"')
    for sg in (1, -1):
        sh.line(xs(G.POSTX), ys(sg * G.YS), xs(G.POSTX), ys(sg * G.YS + G.TIE_Y1 - G.YS), 'thk')
    for bxe in G.esc_boxes() + [G.rx_box(), G.steer_servo_box()]:
        sh.rect(xs(bxe[1]), ys(bxe[3]), (bxe[1] - bxe[0]) * s, (bxe[3] - bxe[2]) * s, 'elec')
    for X in D.DECK_BEAMS:
        sh.line(xs(X), ys(D.BEAM / 2), xs(X), ys(-D.BEAM / 2), 'hid')
    for h in G.hatch_rects():
        sh.rect(xs(h['x1']), ys(h['y1']), (h['x1'] - h['x0']) * s, (h['y1'] - h['y0']) * s, 'thin')
    seen = set()
    for h in G.hatch_rects():
        if h['name'] not in seen:
            seen.add(h['name']); sh.text(xs(h['x0']) - 1, ys(h['y1']) - 0.9, h['name'], 'tb', 'end')
    if hs and hs['kind'] == 'tower':
        sh.rect(xs(ux1), ys(D.TOWER_W / 2), (ux1 - ux0) * s, D.TOWER_W * s, 'hid')
        sh.text(xs(ux0) + 1.5, ys(D.TOWER_W / 2) - 0.9, 'tower', 'ts')
    elif hs:
        for sg in (1, -1):
            sh.poly(Pp([(ux0, sg * float(G.inner_wall_y(ux0))), (ux1, sg * float(G.inner_wall_y(ux1))), (ux1, sg * float(G.outer_wall_y(ux1))), (ux0, sg * float(G.outer_wall_y(ux0)))]), 'hid')
        sh.text(xs((ux0 + ux1) / 2), ys(float(G.outer_wall_y(ux0)) + 8), 'bow cap', 'ts', 'middle')
    if bb:
        sh.rect(xs(bb.x1), ys(bb.y1), (bb.x1 - bb.x0) * s, (bb.y1 - bb.y0) * s, 'elec')
        sh.text(xs((bb.x0 + bb.x1) / 2), ys((bb.y0 + bb.y1) / 2) + 0.8, 'servo', 'ts', 'middle')
        sh.circ(xs(G.line_x()), ys(G.blade_y()), 0.9, 'obj', 'style="fill:#fff"')
    # deck outline of the chosen plan (the deck itself is removed in this view), aft deck beams, push bar and its mount arms
    sh.poly(Pp(G.deck_outline()), 'thin', 'style="fill:none"')
    ab = G.aft_box()
    for sg in (1, -1):
        x0_, x1_, y0_, y1_ = ab['long']
        sh.rect(xs(x1_), ys(sg * y1_ if sg > 0 else -y0_), (x1_ - x0_) * s, (y1_ - y0_) * s, 'hid')
    for key in ('transom', 'end'):
        x0_, x1_, y0_, y1_ = ab[key]
        sh.rect(xs(x1_), ys(y1_), (x1_ - x0_) * s, (y1_ - y0_) * s, 'hid')
    for sg in (1, -1):
        sh.rect(xs(G.BUMPER_X0), ys(sg * G.BUMPER_ARM_Y + D.BUMPER_ARM_W / 2), am['L'] * s, D.BUMPER_ARM_W * s, 'gray')
    sh.poly(Pp(G.bumper_plan()), 'cut')
    for b in G.deck_brackets():
        for sg in (1, -1):
            sh.rect(xs(b['x'] + D.FRAME_T / 2), ys(b['y1'] if sg > 0 else -b['y0']), D.FRAME_T * s, b['L'] * s, 'gray')
    sh.text(xs(-D.AFT_DECK_L / 2), ys(-D.AFT_DECK_W / 2) - 2, 'deck plan: %s' % G.deck_plan(), 'tb', 'middle')
    sh.dimh(xs(G.BUMPER_X1), xs(-D.AFT_DECK_L), ys(-D.AFT_DECK_W / 2) + 4, '%.1f overall = %.0f hull + %.0f bar projection + %.1f aft deck' % (D.LOA + D.BUMPER_PROJ + D.AFT_DECK_L, D.LOA, D.BUMPER_PROJ, D.AFT_DECK_L), ys(-D.AFT_DECK_W / 2) + 1, ys(-D.AFT_DECK_W / 2) + 1)
    sh.dimv(ys(D.BEAM / 2), ys(-D.BEAM / 2), 27, '%.0f' % D.BEAM, xs(D.LOA), xs(D.LOA))
    sh.dimv(ys(D.AFT_DECK_W / 2), ys(-D.AFT_DECK_W / 2), xs(-D.AFT_DECK_L) + 6, '%.0f' % D.AFT_DECK_W, xs(-D.AFT_DECK_L), xs(-D.AFT_DECK_L))
    sh.dimv(ys(G.HT + D.SPONSON_W), ys(G.HT), xs(410), '%.2f' % D.SPONSON_W, xs(410), xs(410))
    sh.dimv(ys(G.HT), ys(-G.HT), xs(410), '%.1f' % D.TUNNEL_W, xs(410), xs(410))
    sh.text(36, 29.5, 'PROFILE, SECTION ON THE SPONSON CENTERLINE (Y = %.1f), LOOKING PORT' % G.YS, 'tb')
    sh.text(110, 145.3, 'PLAN, DECK REMOVED', 'tb')
    # key
    X0 = 352
    keys = ['1  Push bar, X %.0f to %.0f, Z %.1f to %.1f (%.0f above the waterline), on two ply arms to the bow caps' % (G.BUMPER_X0, G.BUMPER_X1, bz0, bz1, D.BUMPER_WL_CLR),
            '2  Deck parallel to the waterline, %.0f freeboard' % D.FREEBOARD,
            '3  ESC (2) on the tunnel roof, X %.0f to %.0f' % (D.ESC['x0'], D.ESC['x0'] + D.ESC['l']),
            '4  Battery on slide, center X %.0f to %.0f, design %.0f, %.0f outboard (Y %.1f), hatch HB' % (D.BAT_SLIDE[0], D.BAT_SLIDE[1], D.DESIGN_BAT_X, D.BAT_Y_OFFSET, G.BAT_YC),
            '5  Motor ATO 3670%s, axis %.0f deg up forward, hatch HM' % (' in 51 mm jacket' if D.JACKETS else '', D.MOTOR_AXIS_DEG),
            '6  CV joint at X %.0f, Z %.0f' % (D.CV_X, D.PROP_Z),
            '7  Shaft %.0f deg down going aft, inside the skeg, no seal' % D.MOTOR_AXIS_DEG,
            '8  Skeg %.0f wide, bottom edge %.1f deg, open to the hull' % (D.SKEG_W, G.SKEG_BOT_DEG),
            '9  Kort nozzle %.0f x %.0f (assumed), top %.0f below the keel' % (D.NOZ_OD, D.NOZ_L, -G.NOZ_ZTOP),
            '10 Steering post %.0f mm in the aft deck bushing, %.1f long, cut from %.0f mm rod and tube stock (check 18)' % (D.NOZ_POST_D, G.post_required_length(zd), D.NOZ_POST_STOCK_L),
            '11 Steering servo DS3225 on its side on the roof, %.0f high, %.0f x %.1f footprint, hatch HS' % (D.STEER_SERVO['h'], D.STEER_SERVO['l'], D.STEER_SERVO['w']),
            '12 Receiver on the tunnel roof, X %.0f to %.0f, hatch HC' % (D.RX['x0'], D.RX['x0'] + D.RX['l']),
            '13 Aft deck box over nozzles, %.1f x %.0f, %.1f deep (A-502)' % (D.AFT_DECK_L, D.AFT_DECK_W, D.AFT_DECK_DEPTH),
            ('14 Blade tower %.0f x %.0f x %.0f over the trunk' % (D.TOWER_L, D.TOWER_W, D.TOWER_H)) if hs and hs['kind'] == 'tower' else '14 Bow cap, X %.0f to %.0f, top Z %.1f, %.1f above the deck at the aft end' % (ux0, ux1, hs['ztop'], hs['h0']),
            '15 Tunnel roof plate, Z %.1f to %.1f' % (D.ROOF_Z0, G.ROOF_Z1),
            ('16 Blade servo DS3225 on its side in the bow cap, X %.0f to %.0f, Y %.1f to %.1f, on a shelf at Z %.1f; spool at X %.0f; lift line from the blade upper edge %.0f from the hinge' % (
                bb.x0, bb.x1, bb.y0, bb.y1, bb.z0, G.line_x(), D.LINE_R)) if bb else '',
            '17 Pushrod, 2-56 rod %.2f dia, Z %.1f, Y %.1f, %.0f between link centers; transom hole %.0f with a %.0f x %.0f bellows' % (D.ROD_D, G.ZR, G.ROD_Y, G.ROD_L, D.ROD_HOLE_D, D.BELLOWS_OD, D.BELLOWS_L),
            '18 Tie bar %.0f x %.0f brass, %.1f long, X %.0f, Z %.1f; two %.0f arm horns point to port' % (D.TIE_BAR, D.TIE_BAR, G.TIE_L, G.POSTX, G.ZR, D.NOZ_HORN_ARM),
            'WL Waterline at rest (blue dashed)']
    sh.text(X0, 36, 'KEY', 'tb')
    y = 41
    for k_ in [k for k in keys if k]:
        y = para(sh, X0, y, k_, 58, step=4.2) + 0.2
    y += 3
    sh.text(X0, y, 'TRIM AT REST (A-601 %s, %s g)' % (D.REV, format(round(r['W']), ',')), 'tb'); y += 4.6
    for b, rr in trim_rows:
        sh.text(X0, y, 'Bat %.0f: stern %.1f, bow %.1f, over nozzle %.1f' % (b, rr['d0'], rr['bow'], rr['over']), 't'); y += 4.4
    sh.text(X0, y, 'Hull hangs %.1f below the keel; over nozzle less %.0f trough: %.1f' % (-G.SHOE_BOT, D.TROUGH, r['over'] - D.TROUGH), 't'); y += 4.4
    sh.text(X0, y, 'Excludes nozzles, props, mounts, fittings (A-601)', 't'); y += 5
    sh.text(X0, y, 'GENERAL', 'tb'); y += 4.6
    gen = ['All hull panels %.3f mm (1/8 in) balsa, glassed.' % T,
           'Sponsons %.2f wide, %.1f at the transom, tapering to X %.0f; tunnel %.1f wide.' % (D.SPONSON_W, D.AFT_W, D.AFT_TAPER_X, D.TUNNEL_W),
           'Blade (%s): R%.0f, %.0f deg sector, hinge X %.0f. Tip stops %.1f short of the trunk end (X %.0f).' % (
               D.BLADE_VARIANT, bp['R'], bp['sector_deg'], bp['hinge_x'], G.tip_to_trunk_end(), tx1),
           ('Blade plane at Y %.1f in a %.0f wide trunk, X %.0f to %.0f. Batteries %.0f outboard.' % (G.blade_y(), bp['trunk_w'], tx0, tx1, D.BAT_Y_OFFSET)) if bp['side'] == 'tunnel' else 'Blade and trunk on the sponson centerline.',
           ]
    for t in gen:
        y = para(sh, X0, y, t, 58, step=4.2) + 0.2
    yn = 251
    for t in ['Hidden items dashed. Plan: deck removed. Deck top %.1f at the transom, %.1f at the bow. Pending items are tagged in design.py.' % (zd(0), zd(D.LOA)),
              'Steering: servo output at Z %.1f (roof top + %.0f), pushrod X %.1f to %.1f at Y %.1f through the center transom, tie bar between the posts at X %.0f; nozzle horns and tie bar are ASSUMED (design.py).' % (G.ZR, D.STEER_SERVO['h'] / 2, G.ROD_X0, G.ROD_X1, G.ROD_Y, G.POSTX)]:
        yn = para(sh, 80, yn, t, 140, step=4.2, hang=0)
    sh.line(36, 246, 36 + 100 * s, 246, 'obj'); sh.line(36, 244.5, 36, 247.5, 'obj'); sh.line(36 + 100 * s, 244.5, 36 + 100 * s, 247.5, 'obj')
    sh.text(36 + 100 * s + 2, 247, '100 mm', 't')
    return sh
