"""A-301 Drivetrain cutaway: port sponson centerline section, every number from the model."""
import math
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
    sh = Sheet('A-301', 'Drivetrain cutaway',
               'Port sponson centerline section: motor, CV joint, level prop, skeg and shoe. Bow left. Blade extended solid, retracted dashed (inset).', '1:2')
    s = 0.45; ox = 14; oy = 100
    XW = 430
    xs = lambda X: ox + s * (XW - X)
    zs = lambda Z: oy - s * Z
    P = lambda pts: [(xs(x), zs(z)) for x, z in pts]
    XA = -100
    sh.text(14, 34, 'PORT DRIVETRAIN, SECTION ON THE SPONSON CENTERLINE (Y = %.1f), X %d TO %d. Starboard is the mirror.' % (G.YS, XW, XA), 'th')
    sh.add(f'<polygon points="{xs(XW):.1f},{zs(wl(XW)):.1f} {xs(XA):.1f},{zs(wl(XA)):.1f} {xs(XA):.1f},{zs(-120):.1f} {xs(XW):.1f},{zs(-120):.1f}" class="water" opacity=".5"/>')
    # hull: floor (open over the skeg), deck, transom, aft deck, roof line, bulkhead
    sh.poly(P([(XW, 0), (G.SKEG_X0, 0), (G.SKEG_X0, T), (XW, T)]), 'cut')
    sh.poly(P([(XW, zd(XW)), (0, zd(0)), (0, zd(0) - T), (XW, zd(XW) - T)]), 'cut')
    sh.poly(P([(0, G.SHOE_BOT), (-T, G.SHOE_BOT), (-T, zd(0)), (0, zd(0))]), 'cut')
    sh.poly(P([(0, zd(0)), (XA, zd(XA)), (XA, zd(XA) - D.AFT_DECK_T), (0, zd(0) - D.AFT_DECK_T)]), 'cut')
    sh.line(xs(XW), zs(G.ROOF_Z1), xs(0), zs(G.ROOF_Z1), 'thin'); sh.text(xs(110), zs(G.ROOF_Z1) - 1, 'tunnel roof line beyond', 'ts', 'middle')
    sh.line(xs(D.BH1_X), zs(T), xs(D.BH1_X), zs(zd(D.BH1_X) - T), 'hid'); sh.text(xs(D.BH1_X) - 1.2, zs(8), 'BH1 X %.0f' % D.BH1_X, 'ts', rot=-90)
    tx0 = G.trunk_x()[0]
    if tx0 <= XW:
        sh.line(xs(tx0), zs(T), xs(tx0), zs(zd(tx0) - T), 'hid'); sh.text(xs(tx0) - 1.2, zs(8), 'blade trunk aft wall X %.0f' % tx0, 'ts', rot=-90)
    # skeg side plate, shoe
    ang = math.radians(G.SKEG_BOT_DEG)
    sh.poly(P([(G.SKEG_X0, 0), (0, 0), (0, G.SHOE_BOT), (G.SKEG_X0 - T / math.sin(ang), 0)]), 'gray')
    sh.poly(P(G.SKEG), 'thin')
    sh.poly(P([(G.SKEG_X0 - T / math.sin(ang) - T, 0), (0, 0), (0, G.SHOE_BOT + T)]), 'obj', 'style="fill:#fff"')
    sh.poly(P(G.SHOE), 'cut')
    sh.poly(P([(0, G.SHOE_BOT), (-T, G.SHOE_BOT), (-T, G.SHOE_TOP), (0, G.SHOE_TOP)]), 'cut')
    # motor, mount, shaft, CV, stern tube, seal
    sh.poly(P(G.MOT), 'prop'); sh.circ(xs(G.F[0]), zs(G.F[1]), 0.8, 'obj')
    sh.poly(P(G.MOUNT), 'gray')
    sh.line(xs(G.F[0]), zs(G.F[1]), xs(D.CV_X), zs(D.PROP_Z), 'obj')
    for d_ in (D.TUBE_OD / 2, -D.TUBE_OD / 2):
        sh.line(xs(G.F[0] - 6), zs(G.shaft_z(G.F[0] - 6) + d_), xs(D.CV_X + 10), zs(G.shaft_z(D.CV_X + 10) + d_), 'hid')
    sh.circ(xs(D.CV_X), zs(D.PROP_Z), D.CV_OD_ASSUMED / 2 * s, 'prop'); sh.circ(xs(D.CV_X), zs(D.PROP_Z), 0.8, 'obj', 'style="fill:#111"')
    sh.line(xs(D.CV_X), zs(D.PROP_Z), xs(G.NOZ_XF), zs(D.PROP_Z), 'obj')
    for d_ in (D.TUBE_OD / 2, -D.TUBE_OD / 2):
        sh.line(xs(D.CV_X - 8), zs(D.PROP_Z + d_), xs(G.NOZ_XF + 2), zs(D.PROP_Z + d_), 'obj')
    sh.rect(xs(D.SEAL_L / 2), zs(D.PROP_Z + D.SEAL_OD / 2), D.SEAL_L * s, D.SEAL_OD * s, 'gray')
    sh.line(xs(G.MOT_X0 + 30), zs(G.shaft_z(G.MOT_X0 + 30)), xs(D.CV_X - 5), zs(G.shaft_z(D.CV_X - 5)), 'ctr')
    sh.line(xs(D.CV_X + 5), zs(D.PROP_Z), xs(G.SHOE_X1), zs(D.PROP_Z), 'ctr')
    # nozzle, prop disc, post, bottom pintle
    sh.rect(xs(G.NOZ_XF), zs(G.NOZ_ZTOP), D.NOZ_L * s, D.NOZ_OD * s, 'prop')
    sh.rect(xs(G.POSTX + D.PROP_T / 2), zs(D.PROP_Z + D.PROP_D / 2), D.PROP_T * s, D.PROP_D * s, 'thin')
    sh.rect(xs(G.POSTX) - D.NOZ_POST_D * s / 2, zs(zd(G.POSTX) + 8), D.NOZ_POST_D * s, (zd(G.POSTX) + 8 - G.NOZ_ZTOP) * s, 'prop')
    sh.rect(xs(G.POSTX + 6), zs(zd(G.POSTX)), 12 * s, D.AFT_DECK_T * s, 'gray')
    sh.rect(xs(G.POSTX) - D.PINTLE_D * s / 2, zs(G.NOZ_ZBOT), D.PINTLE_D * s, G.PINTLE_L * s, 'prop')
    sh.rect(xs(G.POSTX) - D.BUSHING_OD * s / 2, zs(G.SHOE_TOP), D.BUSHING_OD * s, D.SHOE_T * s, 'obj', 'style="fill:#c9a24a"')
    sh.rect(xs(G.POSTX) - D.TIE_BAR * s / 2, zs(G.ZR) - D.TIE_BAR * s / 2, D.TIE_BAR * s, D.TIE_BAR * s, 'obj', 'style="fill:#c9a24a"')
    sh.dimv(zs(G.NOZ_ZTOP), zs(zd(G.POSTX) - T), xs(G.POSTX) + 14, '%.1f post required' % G.post_required_length(zd), xs(G.POSTX), xs(G.POSTX))
    sh.line(xs(XW), zs(wl(XW)), xs(XA), zs(wl(XA)), 'wl')
    # dims
    yb = zs(G.SHOE_BOT) + 10
    sh.dimh(xs(G.MOT_X1), xs(G.MOT_X0), zs(G.MOT_TOP) - 8, '%.1f motor %s' % (G.MOT_X1 - G.MOT_X0, 'jacket' if D.JACKETS else 'can'), zs(G.MOT_TOP), zs(G.MOT_TOP))
    sh.dimh(xs(G.F[0]), xs(D.CV_X), yb, '%.1f: %.0f deg shaft, motor to CV' % (G.F[0] - D.CV_X, D.MOTOR_AXIS_DEG), zs(G.F[1]), zs(D.PROP_Z))
    sh.dimh(xs(D.CV_X), xs(G.POSTX), yb, '%.0f CV to prop' % (D.CV_X - G.POSTX), zs(D.PROP_Z), zs(D.PROP_Z))
    sh.dimh(xs(G.SKEG_X0), xs(0), yb + 8, '%.1f skeg' % G.SKEG_X0, zs(0), zs(0))
    sh.dimh(xs(0), xs(G.SHOE_X1), yb + 8, '%.0f shoe' % (-G.SHOE_X1), zs(G.SHOE_BOT), zs(G.SHOE_BOT))
    sh.dimv(zs(0), zs(G.SHOE_BOT), xs(G.SKEG_X0) + 14, '%.1f' % (-G.SHOE_BOT), xs(0), xs(0))
    sh.dimv(zs(G.F[1]), zs(0), xs(G.MOT_X0) + 8, '%.1f' % G.F[1], xs(G.MOT_X0), xs(G.MOT_X0))
    sh.dimv(zs(0), zs(D.PROP_Z), xs(D.CV_X) - 8, '%.0f' % (-D.PROP_Z), xs(D.CV_X), xs(D.CV_X))
    sh.dimv(zs(wl(G.POSTX)), zs(G.NOZ_ZTOP), xs(G.SHOE_X1) - 22, '%.1f over nozzle' % r['over'], xs(G.POSTX), xs(G.POSTX))
    sh.dimv(zs(G.NOZ_ZBOT), zs(G.SHOE_TOP), xs(G.SHOE_X1) - 6, '%.0f' % D.SHOE_CLR, xs(G.SHOE_X1), xs(G.SHOE_X1))
    sh.dimv(zs(zd(0)), zs(0), xs(0) + 22, '%.1f' % zd(0), xs(0), xs(0))
    sh.text(xs(250), zs(G.shaft_z(250)) + 9, '%.0f deg' % D.MOTOR_AXIS_DEG, 'ts', 'middle')
    # tags
    tags = [(1, G.MOT[1][0] - 10, G.MOT_TOP, 'Motor %.0f x %.0f%s, axis %.0f deg, on a %.0f deg laminated mount' % (D.MOTOR_D, D.MOTOR_L, ' in %.0f jacket' % D.JACKET_D if D.JACKETS else '', D.MOTOR_AXIS_DEG, D.MOTOR_AXIS_DEG)),
            (2, 150, G.shaft_z(150), 'Angled shaft inside the hull and skeg, no seal'),
            (3, D.CV_X, D.PROP_Z - D.CV_OD_ASSUMED / 2, 'CV joint at X %.0f, Z %.0f, working angle %.0f deg (OD %.0f assumed)' % (D.CV_X, D.PROP_Z, D.MOTOR_AXIS_DEG, D.CV_OD_ASSUMED)),
            (4, 8, D.PROP_Z, 'Level stern tube; the only seal is at the transom'),
            (5, -40, D.PROP_Z, 'Kort nozzle %.0f x %.0f (assumed), prop level' % (D.NOZ_OD, D.NOZ_L)),
            (6, 100, G.skeg_bot(100), 'Skeg: planked box, %.0f wide, bottom edge %.1f deg, open to the hull' % (D.SKEG_W, G.SKEG_BOT_DEG)),
            (7, -50, G.SHOE_BOT, 'Shoe: %.2f thick, %.0f under the nozzle, %.0f long' % (D.SHOE_T, D.SHOE_CLR, -G.SHOE_X1)),
            (8, G.POSTX, G.SHOE_TOP + 4, 'Bottom pintle: %.0f mm pin, %.0f below the nozzle, %.0f deep in a %.0f OD brass bushing (wall %.1f) in the shoe (fabricated, ASSUMED)' % (D.PINTLE_D, G.PINTLE_L, D.PINTLE_ENGAGE, D.BUSHING_OD, G.BUSHING_WALL)),
            (9, G.POSTX, zd(G.POSTX), 'Top post %.0f mm in the aft deck bushing (rod and tube cut to length)' % D.NOZ_POST_D)]
    for n, X, Z, _ in tags:
        dz = -14 if n in (3, 6, 7, 8) else 14
        if n in (2, 4, 5):
            dz = 16
        sh.tag(xs(X), zs(Z + dz), n); sh.leader(xs(X), zs(Z + dz) + (2.3 if dz > 0 else -2.3), xs(X), zs(Z))
    X0 = 262; y = 40
    sh.text(X0, y, 'KEY', 'tb'); y += 5
    for n, _, _, t in tags:
        y = para(sh, X0, y, '%d  %s' % (n, t), 78, step=4.2, hang=4) + 0.2
    y += 3
    sh.text(X0, y, 'TRIM AT REST (%s g, skeg buoyancy %.0f cm3 included)' % (format(round(r['W']), ','), G.SKEG_VOL), 'tb'); y += 5
    for b, rr in trim_rows:
        sh.text(X0, y, 'Batteries at %.0f: stern %.1f, bow %.1f, over nozzle top %.1f, in a %.0f trough %.1f' % (b, rr['d0'], rr['bow'], rr['over'], D.TROUGH, rr['over'] - D.TROUGH), 't'); y += 4.2
    y += 3
    sh.text(X0, y, 'NOTES', 'tb'); y += 5
    notes = ['Prop axis Z %.0f, nozzle top %.0f below the keel. Shoe bottom %.1f below the keel.' % (D.PROP_Z, -G.NOZ_ZTOP, -G.SHOE_BOT),
             'Skeg interior %.2f after two %.3f skins; CV joint OD not published (assumed %.0f), confirm before planking.' % (G.SKEG_INTERIOR, T, D.CV_OD_ASSUMED),
             'Motor top %.1f; deck underside %.1f at X %.0f; clearance %.1f.' % (G.MOT_TOP, zd(G.MOT_XMAX) - T, G.MOT_XMAX, zd(G.MOT_XMAX) - T - G.MOT_TOP),
             'Weights are estimates; see A-601 for the total and the checks report.',
             'Nozzle: Model Boat Bits MBB-KNS, 90 deg tiller; no bottom pivot listed. The vendor 50 mm steering tube is not used: the post is %.0f mm rod in %.0f mm bore tube, both cut to %.1f (nozzle top to the aft deck underside) from %.0f mm stock (check 18).' % (D.NOZ_POST_D, D.NOZ_POST_D, G.post_required_length(zd), D.NOZ_POST_STOCK_L),
             'Drive shaft %.1f mm each: %.0f CV to prop plane + %.1f CV to the motor aft face along the axis + %.0f stub + %.0f at the prop end (derived).' % (G.SHAFT_LEN, D.CV_X - G.POSTX, G.SHAFT_MOTOR_SEG - D.SHAFT_STUB, D.SHAFT_STUB, D.SHAFT_MARGIN),
             'Tie bar %.0f x %.0f brass at X %.0f, Z %.1f, between the posts (section square on the post); pushrod and horns on A-101.' % (D.TIE_BAR, D.TIE_BAR, G.POSTX, G.ZR)]
    for t in notes:
        y = para(sh, X0, y, t, 78, step=4.2, hang=0) + 0.2
    # ---- inset: blade, bow end of the same sponson section
    bp = G.blade_params()
    ext, ret = G.blade_outline(True), G.blade_outline(False)
    hs = G.housing(zd)
    bb = G.blade_box() if bp['housing'] == 'cap' else None
    t0, t1 = G.trunk_x()
    xl = min(min(p[0] for p in ext + ret), t0) - 20
    xr = D.LOA + 10
    ztops = [max(p[1] for p in ret), zd(D.LOA) + D.TOWER_H if bp['housing'] == 'tower' else 0]
    if hs and hs['kind'] == 'cap':
        ztops.append(hs['ztop'])
    if bb:
        ztops.append(zd(bb.x0) + bb.z1)
    ztop = max(ztops) + 8
    zbot = -G.blade_depth() - 8
    avail = 72
    den = math.ceil((ztop - zbot) / avail)               # whole-number scale 1:den that fits the free area
    si = 1 / den
    iox = 14; ioy = 166 + si * ztop
    xi = lambda X: iox + si * (xr - X); zi = lambda Z: ioy - si * Z
    Pi = lambda pts: [(xi(x), zi(z)) for x, z in pts]
    ttl = 'BLADE (%s), BOW END, SAME SECTION, 1:%d. Trunk X %.0f to %.0f; %s.' % (
        D.BLADE_VARIANT, den, t0, t1, ('bow cap X %.0f to %.0f' % (hs['x0'], hs['x1'])) if hs and hs['kind'] == 'cap' else 'tower %.0f x %.0f x %.0f centered on the trunk' % (D.TOWER_L, D.TOWER_W, D.TOWER_H))
    sh.text(14, 162, ttl, 'tb')
    sh.add(f'<polygon points="{xi(xr):.1f},{zi(wl(xr)):.1f} {xi(xl):.1f},{zi(wl(xl)):.1f} {xi(xl):.1f},{zi(zbot):.1f} {xi(xr):.1f},{zi(zbot):.1f}" class="water" opacity=".5"/>')
    sh.poly(Pi([(xr, 0), (xl, 0), (xl, T), (xr, T)]), 'cut')
    sh.poly(Pi([(xr, zd(xr)), (xl, zd(xl)), (xl, zd(xl) - T), (xr, zd(xr) - T)]), 'cut')
    sh.rect(xi(D.LOA), zi(zd(D.LOA) - D.PUSH_PAD_INSET), D.PUSH_PAD_T * si, (zd(D.LOA) - 2 * D.PUSH_PAD_INSET) * si, 'cut')
    sh.rect(xi(t1), zi(zd(t1) - T), (t1 - t0) * si, (zd(t1) - 2 * T) * si, 'hid')
    if hs and hs['kind'] == 'cap':
        sh.poly(Pi([(hs['x0'], zd(hs['x0'])), (hs['x1'], zd(hs['x1'])), (hs['x1'], hs['top'](hs['x1'])), (hs['x0'], hs['top'](hs['x0']))]), 'gray')
        sh.text(xi(hs['xc']), zi(hs['ztop']) + 4.5, 'bow cap', 'ts', 'middle')
        sh.dimv(zi(zd(hs['x0'])), zi(hs['ztop']), xi(hs['x0']) + 6, '%.0f high' % hs['h0'], xi(hs['x0']), xi(hs['x0']), 2.6)
    elif hs:
        u0, u1 = G.tower_x()
        sh.rect(xi(u1), zi(zd(u1) + D.TOWER_H), (u1 - u0) * si, D.TOWER_H * si, 'gray')
        sh.text(xi(u0) - 2, zi(zd(u0) + D.TOWER_H / 2), 'tower', 'ts', 'end')
    if bb:
        sh.poly(Pi([(bb.x0, zd(bb.x0)), (bb.x1, zd(bb.x1)), (bb.x1, zd(bb.x1) + bb.z1), (bb.x0, zd(bb.x0) + bb.z1)]), 'elec')
        sh.text(xi((bb.x0 + bb.x1) / 2), zi(zd(bb.x0) + bb.z1 / 2), 'servo box', 'ts', 'middle')
    sh.poly(Pi(ext), 'blade'); sh.poly(Pi(ret), 'hid')
    sh.circ(xi(bp['hinge_x']), zi(bp['hinge_z']), 0.7, 'obj', 'style="fill:#fff"')
    sh.line(xi(xr), zi(wl(xr)), xi(xl), zi(wl(xl)), 'wl')
    sh.text(xi(bp['hinge_x']) + 2, zi(bp['hinge_z']) + 3.5, 'hinge X %.0f, Z %.0f' % (bp['hinge_x'], bp['hinge_z']), 'ts', 'start' if bp['dir'] == 'fwd' else 'end')
    cxe = G.blade_centroid(True)
    sh.text(xi(cxe[0]), zi(cxe[1]), 'extended', 'ts', 'middle')
    cxr = G.blade_centroid(False)
    sh.text(xi(cxr[0]), zi(cxr[1]), 'retracted', 'ts', 'middle')
    sh.dimv(zi(0), zi(-G.blade_depth()), xi(xl) + 6, '%.1f below keel' % G.blade_depth(), xi(bp['hinge_x']), xi(bp['hinge_x']))
    # notes beside the inset
    nx = iox + si * (xr - xl) + 24
    ny = 170
    sh.text(nx, ny, 'BLADE NOTES', 'tb'); ny += 5
    if bp['side'] == 'tunnel':
        bt0, bt1 = G.trunk_y()
        blade_notes = ['Hinge X %.0f, Z %.0f; R%.0f; %.0f deg sector; the blade points forward. Extended it hangs %.1f below the keel (solid); stowed it is rotated up %.0f deg about the hinge, tip at Z %.1f (dashed).' % (
                           bp['hinge_x'], bp['hinge_z'], bp['R'], bp['sector_deg'], G.blade_depth(), bp['sector_deg'], max(p[1] for p in ret)),
                       'The blade plane is Y %.1f on the tunnel side of each sponson, in a %.0f wide trunk (Y %.1f to %.1f) from X %.0f to %.0f. This section is on the sponson centerline, so the blade is projected onto it.' % (
                           G.blade_y(), bp['trunk_w'], bt0, bt1, t0, t1)]
    else:
        blade_notes = ['Hinge X %.0f, Z %.0f; R%.0f; %.0f deg sector. Extended %.1f below the keel (solid); stowed in the trunk and tower (dashed).' % (bp['hinge_x'], bp['hinge_z'], bp['R'], bp['sector_deg'], G.blade_depth())]
    if hs and hs['kind'] == 'cap':
        blade_notes.append('Bow cap X %.0f to %.0f over the stowed blade: flat top Z %.1f, %.0f clear of the stowed tip, %.0f above the deck at the aft end and %.0f at the bow end; full sponson width.' % (
            hs['x0'], hs['x1'], hs['ztop'], D.CAP_CLR, hs['h0'], hs['h1']))
    if bb:
        blade_notes.append('Blade servo and spool in the deck box at the hinge, X %.0f to %.0f, %.0f high. The servo drives the blade forward against a stop; gravity does not deploy it.' % (bb.x0, bb.x1, bb.z1))
    for t in blade_notes:
        ny = para(sh, nx, ny, t, 80, step=4.2, hang=0) + 0.6
    return sh
