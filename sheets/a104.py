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
    sbx = G.blade_servo_box(zd)
    zmax = max(max(p[1] for p in ret), hs['top'](hs['x0']) if hs and hs['kind'] == 'cap' else zd(D.LOA) + D.TOWER_H, zd(G.tower_xc()) + D.TOWER_H if bp['housing'] == 'tower' else 0)
    oy = 137

    def view(cx, title, sub, look):
        """look=+1 bow view (looking aft, port on the right); -1 stern view (looking forward, port on the left)."""
        ys = lambda Y: cx + look * s * Y
        zs = lambda Z: oy - s * Z

        def box(Y0, Y1, Z0, Z1, c='cut', extra=''):
            a, b = sorted((ys(Y0), ys(Y1)))
            sh.rect(a, zs(Z1), b - a, (Z1 - Z0) * s, c, extra)

        def section(X, c_out, fill='#fff', skin=True, skeg=True):
            """Sponson sections at station X, both sponsons: both bilge corners rounded, the skeg box and its root fillets where X is over the skeg."""
            D_ = zd(X)
            for sg in (1, -1):
                pts = G.sponson_section(X, D_) if skeg else G.hull_section(X, D_)
                sh.poly([(ys(sg * y), zs(z)) for y, z in pts], c_out, 'style="fill:%s"' % fill)
                if skin:
                    sh.poly([(ys(sg * y), zs(z)) for y, z in G.hull_section(X, D_, T)], 'thin', 'style="fill:none"')
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
            # bow: full max section behind (thin), the planked tip faces (20 wide, nothing projects below the bar), then the push bar at deck level on its arms
            section(Xsec, 'thin', '#fff', False)
            for sg in (1, -1):
                sh.poly([(ys(sg * y), zs(z)) for y, z in G.hull_section(D.LOA, zd(D.LOA))], 'obj', 'style="fill:#fff"')
            bz0, bz1 = G.bumper_z0(zd), G.bumper_z1(zd)
            bw = G.bumper_front_width()
            for sg in (1, -1):
                box(sg * (G.BUMPER_ARM_Y - D.BUMPER_ARM_W / 2), sg * (G.BUMPER_ARM_Y + D.BUMPER_ARM_W / 2), zd(D.LOA), zd(D.LOA) + D.BUMPER_ARM_T, 'gray')
            box(-bw / 2, bw / 2, bz0, bz1, 'gray')
            sh.text(cx, zs((bz0 + bz1) / 2) + 0.8, 'push bar %.0f wide x %.0f deep x %.0f (deck plan %s)' % (bw, bz1 - bz0, D.BUMPER_T, G.deck_plan()), 'ts', 'middle')
            sh.text(cx - s * D.BEAM / 2 + 1, zs(zd(D.LOA) / 4), 'maximum section (thin) behind the tips', 'ts')
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
            if look > 0:
                re_ = min(D.SKEG_EDGE_R, G.skeg_depth(0))
                sk = [(-G.SKEG_S, 0.0), (-G.SKEG_S, G.SHOE_BOT + re_)] + [(-G.SKEG_S + re_ - re_ * math.cos(math.pi / 2 * i / 12), G.SHOE_BOT + re_ - re_ * math.sin(math.pi / 2 * i / 12)) for i in range(13)]
                sk += [(-y_, z_) for y_, z_ in reversed(sk)]
                sh.poly([(ys(yc + y_), zs(z_)) for y_, z_ in sk], c)                       # hidden behind the bow face: skeg and shoe, bottom corners rounded
            sh.circ(ys(yc), zs(D.PROP_Z), D.NOZ_OD / 2 * s, c, 'style="fill:#f6e3c2"' if look < 0 else '')
            sh.circ(ys(yc), zs(D.PROP_Z), D.PROP_D / 2 * s, c)
            sh.circ(ys(yc), zs(D.PROP_Z), 1.0, 'obj')
            if look < 0:
                dpost = zd(G.POSTX)
                box(yc - D.NOZ_POST_D / 2, yc + D.NOZ_POST_D / 2, G.NOZ_ZTOP, dpost, 'prop')
                box(yc - D.NOZ_POST_D / 2, yc + D.NOZ_POST_D / 2, G.SHOE_BOT, G.NOZ_ZBOT, 'prop')
        if look < 0:
            ab = G.aft_box()
            zde = zd(-D.AFT_DECK_L)
            he = ab['end_len'] / 2
            if G.deck_plan() == 'taper':
                box(-D.AFT_DECK_W / 2, D.AFT_DECK_W / 2, zde - D.AFT_DECK_DEPTH, zde, 'hid')                 # the full width part, forward of the chamfers
            box(-he, he, zde - D.AFT_DECK_DEPTH, zde)                                                         # aft edge of the closed box
            box(-he, he, zde - D.AFT_DECK_T - ab['h'], zde - D.AFT_DECK_T, 'thin', 'style="fill:#f1e3c8"')   # end beam between the skins
            sh.text(ys(0), zs(zde - D.AFT_DECK_DEPTH) + 3.2, 'aft deck box edge, %.0f wide x %.1f deep (end beam %.2f x %.2f between the skins)' % (2 * he, D.AFT_DECK_DEPTH, ab['w'], ab['h']), 'ts', 'middle')
        if bp['housing'] == 'cap' and sbx:
            for sg in (1, -1):
                box(sg * sbx.y0, sg * sbx.y1, sbx.z0, sbx.z1, 'hid')
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
    y = 229
    for t in ['%.3f mm (1/8 in) planked balsa over frames, glass both sides. Both bottom corners of each sponson, outer and tunnel side, are sanded to R%.0f (PENDING); where a section is narrower than 2 x R the radius is half the width (the stern section is %.1f wide, R%.1f). Skeg root fillets R%.0f and skeg and shoe edge rounds R%.0f (ASSUMED).' % (T, R, float(G.sponson_width(0)), float(G.bilge_r(0)), D.SKEG_ROOT_R, D.SKEG_EDGE_R),
              'Sponsons %.2f wide at the maximum section, %.1f at the transom with a straight taper to X %.0f (approved by the taper study); stern view shows the transom section, the full width as dashed lines.' % (D.SPONSON_W, D.AFT_W, D.AFT_TAPER_X),
              'Deck height: %.1f at the bow, %.1f at the transom; the deck is parallel to the waterline. Freeboard %.0f. Batteries at %.0f.' % (zd(D.LOA), zd(0), D.FREEBOARD, D.DESIGN_BAT_X),
              'Bow: planked tip, nothing submerged projects forward; push bar Z %.1f to %.1f at deck level (%.0f above the waterline), on two ply arms to the bow caps. Stern: aft deck is a closed box %.1f deep (%s plan).' % (
                  G.bumper_z0(zd), G.bumper_z1(zd), D.BUMPER_WL_CLR, D.AFT_DECK_DEPTH, G.deck_plan()),
              'Below the keel: skeg %.0f wide, shoe bottom %.1f below the keel, nozzle %.0f OD with a %.0f prop on a level axis at Z %.0f. Nozzle top %.1f under water at rest.' % (D.SKEG_W, -G.SHOE_BOT, D.NOZ_OD, D.PROP_D, D.PROP_Z, r['over']),
              ('Blade (%s): plane at Y %.1f in a %.0f wide trunk against the tunnel wall (Y %.1f to %.1f); extended %.1f below the keel (solid); retracted it rises to Z %.1f (dashed), through the deck into the bow cap, %.1f above the deck at the aft end and %.1f at the bow end. The blade servo (hidden, dashed) sits in the cap outboard of the blade plane, Y %.1f to %.1f. Batteries sit %.0f outboard (Y %.1f to %.1f) to clear the trunk.' % (
                  D.BLADE_VARIANT, bY, bp['trunk_w'], ty0, ty1, G.blade_depth(), max(p[1] for p in ret), hs['h0'], hs['h1'], sbx.y0, sbx.y1, D.BAT_Y_OFFSET, bat.y0, bat.y1)) if bp['housing'] == 'cap' else
              'Blade (%s): extended %.1f below the keel (solid); retracted it rises to Z %.1f (dashed), through the deck into the %.0f x %.0f x %.0f tower.' % (D.BLADE_VARIANT, G.blade_depth(), max(p[1] for p in ret), D.TOWER_L, D.TOWER_W, D.TOWER_H)]:
        y = para(sh, 14, y, t, 205, step=4.2, hang=0) + 0.4
    return sh
