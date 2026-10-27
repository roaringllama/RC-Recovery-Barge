"""A-104 Bow and stern views, every number from the model."""
import math
from .lib import *
from .tbl import para
import design as D
from model import geometry as G, hydro


def build(r=None):
    r = r or hydro.design()
    zd = r['deck']
    wl = lambda X: r['d0'] - r['k'] * X
    T = D.SKIN_T
    sh = Sheet('A-104', 'Bow and stern views',
               'End elevations: rounded bilges, skegs, shoes, nozzles, %s. Blade extended solid, retracted dashed; trunk and batteries hidden.' % ('bow cap' if G.blade_params()['housing'] == 'cap' else 'tower'), '1:2')
    s = 0.5
    R = D.BILGE_R
    ext, ret = G.blade_outline(True), G.blade_outline(False)
    bp = G.blade_params()
    hs = G.housing(zd)
    bY = G.blade_y()                                  # blade plane, port side (the sponson centerline for center variants)
    ty0, ty1 = G.trunk_y()
    bat = G.battery_boxes(D.DESIGN_BAT_X)[0]
    zmax = max(max(p[1] for p in ret), hs['top'](hs['x0']) if hs and hs['kind'] == 'cap' else zd(D.LOA) + D.TOWER_H, zd(G.tower_xc()) + D.TOWER_H if bp['housing'] == 'tower' else 0)
    oy = 137

    def view(cx, title, sub, look):
        """look=+1 bow view (looking aft, port on the right); -1 stern view (looking forward, port on the left)."""
        ys = lambda Y: cx + look * s * Y
        zs = lambda Z: oy - s * Z

        def box(Y0, Y1, Z0, Z1, c='cut', extra=''):
            a, b = sorted((ys(Y0), ys(Y1)))
            sh.rect(a, zs(Z1), b - a, (Z1 - Z0) * s, c, extra)

        def section(X, c_out, fill='#fff', skin=True):
            D_ = zd(X)
            for sg in (1, -1):
                yi = sg * float(G.inner_wall_y(X)); yo = sg * float(G.outer_wall_y(X))
                rr = min(R, abs(yo - yi))
                pts = [(yi, 0), (yo - sg * rr, 0)]
                for i in range(1, 13):
                    a = math.radians(90) * i / 12
                    pts.append((yo - sg * rr + sg * rr * math.sin(a), rr - rr * math.cos(a)))
                pts += [(yo, D_), (yi, D_)]
                sh.poly([(ys(y), zs(z)) for y, z in pts], c_out, 'style="fill:%s"' % fill)
                if skin:
                    sh.line(ys(yi + sg * T), zs(T), ys(yo - sg * rr), zs(T), 'thin')
                    sh.line(ys(yi + sg * T), zs(D_ - T), ys(yo - sg * T), zs(D_ - T), 'thin')
                    sh.line(ys(yi + sg * T), zs(T), ys(yi + sg * T), zs(D_ - T), 'thin')
                    sh.line(ys(yo - sg * T), zs(rr), ys(yo - sg * T), zs(D_ - T), 'thin')
            yin = G.HT + float(G.inner_off(X))
            return D_, yin

        sh.text(cx, 36, title, 'th', 'middle'); sh.text(cx, 40.5, sub, 'ts', 'middle')
        Xs = D.LOA if look > 0 else 0
        Xsec = G.BOW0 if look > 0 else 0
        # water
        sh.add(f'<rect x="{cx - s * 180:.1f}" y="{zs(wl(Xs)):.1f}" width="{s * 360:.1f}" height="{s * (wl(Xs) + 130):.1f}" class="water" opacity=".5"/>')
        # tower or bow cap above the deck (behind the hull in both views)
        if bp['housing'] == 'tower':
            tc = G.tower_xc()
            box(-D.TOWER_W / 2, D.TOWER_W / 2, zd(tc), zd(tc) + D.TOWER_H, 'gray')
        elif hs:
            # cap over each sponson: wide aft end (Xa) and the narrower bow end (Xb), flat top at hs['ztop']
            for Xc in ((hs['x0'], hs['x1']) if look > 0 else (hs['x1'], hs['x0'])):
                for sg in (1, -1):
                    box(sg * float(G.inner_wall_y(Xc)), sg * float(G.outer_wall_y(Xc)), zd(Xc), hs['ztop'], 'gray')
            ylab = (float(G.outer_wall_y(hs['x0'])) + float(G.outer_wall_y(hs['x1']))) / 2 if look > 0 else (float(G.inner_wall_y(hs['x0'])) + float(G.outer_wall_y(hs['x0']))) / 2
            sh.text(ys(ylab), zs(hs['ztop'] - 10), 'bow cap', 'ts', 'middle')
        # blade at Y = +/- YS: extended solid, retracted dashed (drawn before the skegs so a skeg hides what it covers)
        bt = G.blade_thickness()
        z_lo = min(p[1] for p in ext); z_hi = max(p[1] for p in ret)
        for sg in (1, -1):
            box(sg * bY - bt / 2, sg * bY + bt / 2, z_lo, bp['hinge_z'], 'blade')
        if look > 0:
            # bow: full max section behind, then the push pad across the whole face
            section(Xsec, 'thin', '#fff', False)
            box(-D.BEAM / 2, D.BEAM / 2, D.PUSH_PAD_INSET, zd(D.LOA) - D.PUSH_PAD_INSET, 'gray')
            sh.text(cx, zs(zd(D.LOA) * 3 / 4), 'push pad %.0f mm, full bow face' % D.PUSH_PAD_T, 'ts', 'middle')
            sh.text(cx - s * D.BEAM / 2 + 1, zs(zd(D.LOA) / 2), 'maximum section (thin) behind the pad', 'ts')
            c = 'hid'
        else:
            Dsec, yin = section(Xsec, 'thk')
            box(-yin, yin, D.ROOF_Z0, G.ROOF_Z1, 'cut'); box(-yin, yin, Dsec - T, Dsec, 'cut')
            # full width section behind, dashed outline
            for sg in (1, -1):
                sh.line(ys(sg * (G.HT + D.SPONSON_W)), zs(R), ys(sg * (G.HT + D.SPONSON_W)), zs(zd(D.AFT_TAPER_X)), 'hid')
                sh.line(ys(sg * G.HT), zs(0), ys(sg * G.HT), zs(zd(D.AFT_TAPER_X)), 'hid')
            c = 'obj'
        # blade trunk, batteries (hidden behind the bow face or the transom), blade pivot level
        for sg in (1, -1):
            if bp['side'] == 'tunnel':
                tdeck = zd(G.trunk_x()[1] if look > 0 else G.trunk_x()[0])
                box(sg * ty0, sg * ty1, T, tdeck - T, 'hid')
            box(sg * bat.y0, sg * bat.y1, bat.z0, bat.z1, 'hid')
        sh.line(ys(0), zs(zmax + 4), ys(0), zs(-D.SHOE_CLR - 130), 'ctr')
        for sg in (1, -1):
            yc = sg * G.YS
            fill_g = 'style="fill:#e4e4e4"' if look < 0 else ''
            box(yc - D.SKEG_W / 2, yc + D.SKEG_W / 2, G.SHOE_BOT, 0, c, fill_g)
            sh.circ(ys(yc), zs(D.PROP_Z), D.NOZ_OD / 2 * s, c, 'style="fill:#f6e3c2"' if look < 0 else '')
            sh.circ(ys(yc), zs(D.PROP_Z), D.PROP_D / 2 * s, c)
            sh.circ(ys(yc), zs(D.PROP_Z), 1.0, 'obj')
            if look < 0:
                dpost = zd(G.POSTX)
                box(yc - D.NOZ_POST_D / 2, yc + D.NOZ_POST_D / 2, G.NOZ_ZTOP, dpost, 'prop')
                box(yc - D.NOZ_POST_D / 2, yc + D.NOZ_POST_D / 2, G.SHOE_BOT, G.NOZ_ZBOT, 'prop')
        if look < 0:
            zda = zd(-D.AFT_DECK_L / 2)
            box(-D.AFT_DECK_W / 2, D.AFT_DECK_W / 2, zda - D.AFT_DECK_T, zda)
        # retracted blade, dashed, on top of everything
        for sg in (1, -1):
            box(sg * bY - bt / 2, sg * bY + bt / 2, bp['hinge_z'], z_hi, 'hid')
        sh.line(cx - s * 180, zs(wl(Xs)), cx + s * 180, zs(wl(Xs)), 'wl'); sh.text(cx - s * 180 + 1 if look > 0 else cx + s * 180 - 1, zs(wl(Xs)) - 1, 'WL at rest', 'ts', 'start' if look > 0 else 'end')
        # dims
        ytop = zs(zmax) - 7
        sh.dimh(ys(-D.BEAM / 2), ys(D.BEAM / 2), ytop, '%.0f beam' % D.BEAM, zs(zd(Xs)), zs(zd(Xs)))
        yb = zs(min(-D.SHOE_CLR - 138, z_lo - 12))
        # what is hidden inside, at the tunnel centerline above the deck
        notes_in = ['blade plane Y %.1f' % bY] + (['trunk Y %.1f to %.1f' % (ty0, ty1)] if bp['side'] == 'tunnel' else []) + \
                   ['battery Y %.1f to %.1f' % (bat.y0, bat.y1), '(%.0f outboard, dashed)' % D.BAT_Y_OFFSET]
        for i, t_ in enumerate(notes_in):
            sh.text(ys(0), zs(zd(Xs)) - 3 - 3.4 * (len(notes_in) - 1 - i), t_, 'ts', 'middle')
        if look > 0:
            sh.dimh(ys(-G.HT), ys(G.HT), yb, '%.1f tunnel' % D.TUNNEL_W, zs(0), zs(0))
            sh.dimh(ys(G.HT), ys(G.HT + D.SPONSON_W), yb, '%.2f' % D.SPONSON_W, zs(0), zs(0))
            sh.dimv(zs(zd(Xs)), zs(0), ys(D.BEAM / 2) + 10, '%.1f at the bow' % zd(Xs), None, None)
        else:
            w0 = float(G.sponson_width(0))
            sh.dimh(ys(-G.HT - float(G.inner_off(0))), ys(G.HT + float(G.inner_off(0))), yb, '%.1f tunnel at the transom' % (D.TUNNEL_W + 2 * float(G.inner_off(0))), zs(0), zs(0))
            sh.dimh(ys(G.HT + float(G.inner_off(0))), ys(G.HT + float(G.outer_off(0))), yb + 6, '%.1f' % w0, zs(0), zs(0))
            sh.dimv(zs(zd(Xs)), zs(0), ys(D.AFT_DECK_W / 2) - 20, '%.1f at the transom' % zd(Xs), None, None)
            sh.dimv(zs(0), zs(G.SHOE_BOT), ys(G.YS + D.NOZ_OD / 2) - 6, '%.1f skeg and shoe' % (-G.SHOE_BOT), ys(G.YS + D.SKEG_W / 2), ys(G.YS + D.SKEG_W / 2))
            sh.dimh(ys(G.YS - D.SKEG_W / 2), ys(G.YS + D.SKEG_W / 2), zs(G.SHOE_BOT) + 8, '%.0f skeg' % D.SKEG_W, zs(G.SHOE_BOT), zs(G.SHOE_BOT))
            sh.dimv(zs(wl(0)), zs(G.NOZ_ZTOP), ys(-G.YS - D.NOZ_OD / 2) + 6, '%.1f over nozzle' % r['over'], ys(-G.YS), ys(-G.YS))
        # blade depth below the keel, on the outboard side of the starboard sponson
        if bp['side'] == 'tunnel':
            sh.dimv(zs(0), zs(z_lo), ys(-bY + 10), '%.1f blade' % -z_lo, None, None)
        else:
            sh.dimv(zs(0), zs(z_lo), ys(-G.YS - D.NOZ_OD / 2) + (14 if look < 0 else -14) if look < 0 else ys(-G.YS - D.NOZ_OD / 2) - 14, '%.1f blade' % -z_lo, None, None)

    view(118, 'BOW VIEW', 'looking aft from ahead; bow face, blades extended solid and retracted dashed, skegs and nozzles hidden', +1)
    view(318, 'STERN VIEW', 'looking forward from astern; transom section, aft deck removed except its edge', -1)
    y = 233
    for t in ['%.3f mm (1/8 in) planked balsa over frames, glass both sides. Outer bilge sanded to R%.0f (PENDING, shown); inner tunnel corners stay square (blocking inside).' % (T, R),
              'Sponsons %.2f wide at the maximum section, %.1f at the transom with a straight taper to X %.0f (approved by the taper study); stern view shows the transom section, the full width as dashed lines.' % (D.SPONSON_W, D.AFT_W, D.AFT_TAPER_X),
              'Deck height: %.1f at the bow, %.1f at the transom; the deck is parallel to the waterline. Freeboard %.0f. Batteries at %.0f.' % (zd(D.LOA), zd(0), D.FREEBOARD, D.DESIGN_BAT_X),
              'Below the keel: skeg %.0f wide, shoe bottom %.1f below the keel, nozzle %.0f OD on a level axis at Z %.0f. Nozzle top %.1f under water at rest.' % (D.SKEG_W, -G.SHOE_BOT, D.NOZ_OD, D.PROP_Z, r['over']),
              ('Blade (%s): plane at Y %.1f in a %.0f wide trunk against the tunnel wall (Y %.1f to %.1f); extended %.1f below the keel (solid); retracted it rises to Z %.1f (dashed), through the deck into the bow cap, %.0f above the deck at the aft end and %.0f at the bow end. Batteries sit %.0f outboard (Y %.1f to %.1f) to clear the trunk.' % (
                  D.BLADE_VARIANT, bY, bp['trunk_w'], ty0, ty1, G.blade_depth(), max(p[1] for p in ret), hs['h0'], hs['h1'], D.BAT_Y_OFFSET, bat.y0, bat.y1)) if bp['housing'] == 'cap' else
              'Blade (%s): extended %.1f below the keel (solid); retracted it rises to Z %.1f (dashed), through the deck into the %.0f x %.0f x %.0f tower.' % (D.BLADE_VARIANT, G.blade_depth(), max(p[1] for p in ret), D.TOWER_L, D.TOWER_W, D.TOWER_H)]:
        y = para(sh, 14, y, t, 205, step=4.2, hang=0) + 0.4
    return sh
