"""A-501 Joint details at 2:1 for the 1/8 in skin, with the blocking length table computed from the geometry."""
import math
from .lib import *
from .wtbl import wtable
from .tbl import para
import design as D
from model import geometry as G, hydro, schedules as S

BF = 'style="fill:#f1e3c8"'        # blocking fill
K = 2.0                            # drawing scale 2:1


def _section(sh, x, y, w, h, extra=''):
    sh.rect(x, y, w, h, 'cut', extra)


def _tri(sh, p, q, r_, label=None):
    sh.poly([p, q, r_], 'cut', BF)


def build(r=None):
    r = r or hydro.design()
    zd = r['deck']
    T = D.SKIN_T
    t, b = T * K, D.BLOCK_LEG * K
    sh = Sheet('A-501', 'Joint details and blocking',
               'Every joint has blocking bearing on two or more faces; corner turns mitered and wedge-filled, no gaps. 1/8 in (%.3f) skin, 2:1.' % T, '2:1')
    H = 36
    # ---- J1 wall to bottom
    X0, Y0 = 20, 90
    sh.text(X0, 36, 'J1  Wall to bottom, 90 deg', 'tb')
    sh.text(X0, 40, 'triangular blocking, bears on the wall face and the bottom face', 'ts')
    _section(sh, X0, Y0, 62, t)
    _section(sh, X0, Y0 - H, t, H)
    _tri(sh, (X0 + t, Y0), (X0 + t + b, Y0), (X0 + t, Y0 - b))
    sh.dimh(X0 + t, X0 + t + b, Y0 + t + 7, '%.3f' % D.BLOCK_LEG, Y0 + t, Y0 + t)
    sh.dimv(Y0 - b, Y0, X0 + t + b + 7, '%.3f' % D.BLOCK_LEG, X0 + t, X0 + t)
    sh.dimv(Y0 - H, Y0 + t, X0 - 6, 'wall %.3f thick' % T, X0, X0) if False else None
    sh.dimh(X0, X0 + t, Y0 - H - 4, '%.3f' % T, Y0 - H, Y0 - H)
    sh.dimv(Y0, Y0 + t, X0 + 56, '%.3f' % T, X0 + 62, X0 + 62)
    sh.leader(X0 + t + 2.6, Y0 - 2.6, X0 + 34, Y0 - 22)
    sh.text(X0 + 34, Y0 - 23, 'face 1: wall', 'ts')
    sh.leader(X0 + t + 7, Y0 - 0.6, X0 + 34, Y0 - 14)
    sh.text(X0 + 34, Y0 - 15, 'face 2: bottom', 'ts')
    sh.text(X0 + 36, Y0 + t + 14, 'hypotenuse %.2f faces the room' % (D.BLOCK_LEG * math.sqrt(2)), 'ts')
    # ---- J2 chine (bilge radius)
    X1, Y1 = 118, 90
    R = D.BILGE_R * K
    r_in = (D.BILGE_R - T) * K
    L = D.CHINE_LEG * K
    xo, yb = X1 + 62, Y1 + t                 # outer vertex (outer wall face x = xo, outer bottom face y = yb)
    sh.text(X1 - 6, 36, 'J2  Chine, outer wall to bottom', 'tb')
    sh.text(X1 - 6, 40, 'stringer sanded to the bilge radius; planks bend over it', 'ts')
    sh.add('<path d="M%.2f,%.2f L%.2f,%.2f A%.2f,%.2f 0 0 1 %.2f,%.2f L%.2f,%.2f L%.2f,%.2f L%.2f,%.2f A%.2f,%.2f 0 0 0 %.2f,%.2f L%.2f,%.2f Z" class="cut"/>' % (
        xo, Y1 - H, xo, yb - R, R, R, xo - R, yb, X1, yb, X1, yb - t, xo - R, yb - t, r_in, r_in, xo - t, yb - R, xo - t, Y1 - H))
    vx, vy = xo - t, yb - t                  # virtual inner vertex
    rr = r_in
    sh.add('<path d="M%.2f,%.2f L%.2f,%.2f L%.2f,%.2f A%.2f,%.2f 0 0 1 %.2f,%.2f L%.2f,%.2f Z" class="cut" %s/>' % (
        vx - L, vy - L, vx, vy - L, vx, vy - rr, rr, rr, vx - rr, vy, vx - L, vy, BF))
    sh.dimh(vx - L, vx, vy - L - 4, '%.2f' % D.CHINE_LEG, vy - L, vy - L)
    sh.text(X1 - 6, yb + 7, 'outer radius R%.1f, inner (skin) radius R%.2f' % (D.BILGE_R, D.BILGE_R - T), 'ts')
    sh.text(X1 - 6, yb + 11, 'flat bearing on each skin face %.2f plus the arc' % (D.CHINE_LEG + T - D.BILGE_R), 'ts')
    sh.text(X1 - 6, yb + 15, 'faces: wall skin, bottom skin, arc (3 faces); the tunnel-side corner is also R%.0f (J1 blocking)' % D.BILGE_R, 'ts')
    sh.leader(xo - R + 3, yb - 1, X1 + 10, yb + 5) if False else None
    # ---- J3 wall to deck
    X2, Yd = 218, 52
    sh.text(X2 - 6, 36, 'J3  Wall to deck, 90 deg', 'tb')
    sh.text(X2 - 6, 40, 'wall top planed to the deck slope (%.2f deg); triangular blocking' % abs(math.degrees(math.atan(r['k']))), 'ts')
    _section(sh, X2, Yd + 0, 62, t)
    _section(sh, X2, Yd + t, t, H)
    _tri(sh, (X2 + t, Yd + t), (X2 + t + b, Yd + t), (X2 + t, Yd + t + b))
    sh.dimh(X2 + t, X2 + t + b, Yd - 4, '%.3f' % D.BLOCK_LEG, Yd, Yd) if False else None
    sh.dimv(Yd + t, Yd + t + b, X2 + t + b + 7, '%.3f' % D.BLOCK_LEG, X2 + t, X2 + t)
    sh.dimh(X2 + t, X2 + t + b, Yd + t + b + 6, '%.3f' % D.BLOCK_LEG, Yd + t + b, Yd + t + b)
    sh.dimv(Yd, Yd + t, X2 + 56, '%.3f' % T, X2 + 62, X2 + 62)
    sh.text(X2 + 14, Yd - 1.5, 'deck %.3f' % T, 'ts')
    sh.text(X2 + 12, Yd + t + b + 12, 'wall %.3f; wall height = deck Z less 2 x %.3f' % (T, T), 'ts')
    sh.text(X2 + 12, Yd + t + b + 16, 'faces: deck underside, wall inside', 'ts')
    # ---- J4 corner turns
    sh.text(20, 116, 'J4  Corner turns in plan: both panel ends mitered at half the turn so the outer faces meet closed; wedge blocking cut to the included angle bears on both inside faces, full wall height', 'tb')
    seen, corners = set(), []
    for name, p, deg in S.turns():
        key = round(deg, 2)
        if key not in seen:
            seen.add(key)
            corners.append((deg, [n for n, pp, d in S.turns() if round(d, 2) == key], p))
    corners.sort(key=lambda c: c[0])
    cx = 20
    for deg, names, p in corners:
        a = math.radians(deg)
        hm = math.radians(deg / 2)
        L1, L2 = 22, 22
        qx, qy = cx + L1, 150                # inner corner point
        d = (math.cos(a), -math.sin(a))
        o = (qx + t * math.tan(hm), qy + t)
        sh.poly([(qx - L1, qy), (qx, qy), o, (qx - L1, qy + t)], 'cut')
        sh.poly([(qx, qy), (qx + L2 * d[0], qy + L2 * d[1]), (o[0] + L2 * d[0], o[1] + L2 * d[1]), o], 'cut')
        sh.line(qx, qy, o[0], o[1], 'thin')
        leg = D.BLOCK_LEG * K
        sh.poly([(qx, qy), (qx - leg, qy), (qx + leg * d[0], qy + leg * d[1])], 'cut', BF)
        sh.text(cx - 2, 164, '%.2f deg turn' % deg, 'tb')
        sh.text(cx - 2, 168, 'miter %.2f each end' % (deg / 2), 'ts')
        sh.text(cx - 2, 172, 'wedge: legs %.3f, included %.2f' % (D.BLOCK_LEG, 180 - deg), 'ts')
        sh.text(cx - 2, 176, '; '.join(sorted({n.split(',')[0] for n in names}))[:34], 'ts')
        sh.text(cx - 2, 180, 'wall height %.2f at X %.1f' % (zd(p[0]) - 2 * T, p[0]), 'ts')
        cx += 52
    # ---- J5 plank seam
    X5, Y5 = 20, 206
    sh.text(X5, 192, 'J5  Plank seam, butt joint with backing strip', 'tb')
    sh.text(X5, 196, 'seam never at a hatch edge; strip %.2f wide, %.3f thick' % (D.BACK_W, T), 'ts')
    pw = 36
    _section(sh, X5, Y5, pw, t)
    _section(sh, X5 + pw, Y5, pw, t)
    bw = D.BACK_W * K
    sh.rect(X5 + pw - bw / 2, Y5 + t, bw, t, 'cut', BF)
    sh.dimh(X5 + pw - bw / 2, X5 + pw + bw / 2, Y5 + 2 * t + 6, '%.2f' % D.BACK_W, Y5 + 2 * t, Y5 + 2 * t)
    sh.text(X5, Y5 - 3, 'plank %.3f' % T, 'ts')
    sh.text(X5, Y5 + 2 * t + 13, 'backing %.2f past the seam each side; edges trued flat and square, epoxy' % (D.BACK_W / 2), 'ts')
    # ---- J6 skeg box to bottom
    X6, Y6 = 142, 200
    sh.text(X6 - 10, 190, 'J6  Skeg box to bottom (section across the sponson)', 'tb')
    sh.text(X6 - 10, 194, 'plates, slotted core and stern tube; blocking both sides', 'ts')
    wi = G.SKEG_INTERIOR * K
    _section(sh, X6 - 36, Y6, 36 + 2 * t + wi + 36, t)
    px = X6
    sh.rect(px, Y6 + t, t, 26, 'cut')
    sh.rect(px + t + wi, Y6 + t, t, 26, 'cut')
    sh.rect(px + t, Y6 + t, wi, 26, 'cut', 'style="fill:#ddd"')
    sh.circ(px + t + wi / 2, Y6 + t + 13, D.TUBE_OD * K / 2, 'thin', 'style="fill:#fff"')
    _tri(sh, (px, Y6 + t), (px - b, Y6 + t), (px, Y6 + t + b))
    _tri(sh, (px + 2 * t + wi, Y6 + t), (px + 2 * t + wi + b, Y6 + t), (px + 2 * t + wi, Y6 + t + b))
    sh.dimh(px, px + 2 * t + wi, Y6 + t + 26 + 6, '%.2f' % D.SKEG_W, Y6 + t + 26, Y6 + t + 26)
    sh.text(px + t + wi / 2, Y6 + t + 13 + 1, '%.1f' % D.TUBE_OD, 'ts', 'middle')
    sh.text(X6 - 36, Y6 + t + 38, 'plates %.3f, core %.2f wide slotted for the %.1f tube, epoxy filled' % (T, G.SKEG_INTERIOR, D.TUBE_OD), 'ts')
    sh.text(X6 - 36, Y6 + t + 42, 'blocking %.3f x %.3f on both outer faces; glass over the box' % (D.BLOCK_LEG, D.BLOCK_LEG), 'ts')
    # ---- J7 frame to skin
    X7, Y7 = 240, 204
    sh.text(X7 - 6, 190, 'J7  Frame to skin (plan section through a wall)', 'tb')
    sh.text(X7 - 6, 194, 'gusset on each face of every frame, full edge length', 'ts')
    ft = D.FRAME_T * K
    _section(sh, X7, Y7, 64, t)
    _section(sh, X7 + 32 - ft / 2, Y7 + t, ft, 24)
    _tri(sh, (X7 + 32 - ft / 2, Y7 + t), (X7 + 32 - ft / 2 - b, Y7 + t), (X7 + 32 - ft / 2, Y7 + t + b))
    _tri(sh, (X7 + 32 + ft / 2, Y7 + t), (X7 + 32 + ft / 2 + b, Y7 + t), (X7 + 32 + ft / 2, Y7 + t + b))
    sh.dimh(X7 + 32 - ft / 2, X7 + 32 + ft / 2, Y7 + t + 24 + 6, '%.3f' % D.FRAME_T, Y7 + t + 24, Y7 + t + 24)
    sh.text(X7 - 6, Y7 - 3, 'skin %.3f (wall plank, frame edge beveled to it)' % T, 'ts')
    sh.text(X7 - 6, Y7 + t + 38, 'gusset legs %.3f; faces: frame face, skin' % D.BLOCK_LEG, 'ts')
    # ---- blocking table (right)
    pl = S.panels(zd)
    rows = S.blocking(zd, pl)
    hs = S.hatches(zd)
    ht = S.hatch_totals(hs)
    cols = [('ID', 7), ('JOINT AND WHERE', 56), ('KIND', 10), ('PER SP.', 14), ('CENTER', 13), ('HULL', 14)]
    trows = [(q['id'], '%s: %s' % (q['joint'], q['where']), q['kind'], '%.0f' % q['per'], '%.0f' % q['center'], '%.0f' % q['total']) for q in rows]
    trows.append(('H1', 'hatch rim to deck: outer edge of the rim rings', 'tri', '', '', '%.0f' % ht['rim_blocking']))
    X = 304
    y = wtable(sh, X, 44, cols, trows, 'BLOCKING LENGTHS, mm (computed from the geometry)', step=2.7, pad=0.6)
    sc = S.stick_counts(rows, ht['rim_blocking'])
    tt = S.blocking_totals(rows)
    y += 2
    for t_ in ['Triangular blocking (BLOCK_LEG %.3f): %.1f m net, %.1f m of ripped stock with %.0f%% waste, %d x %.0f mm square sticks (two pieces per stick).' % (
                   D.BLOCK_LEG, (tt['tri'] + ht['rim_blocking']) / 1000, sc['tri_len'] / 1000, D.WASTE * 100, sc['tri_n'], D.STICK_L),
               'Chine stringer (%.2f square): %.2f m, %d sticks.  Wedges J4 (%.3f legs): %.2f m, %d sticks.  Backing strip %.2f x %.3f: %.2f m, %d sticks.' % (
                   D.CHINE_LEG, sc['chine_len'] / 1000, sc['chine_n'], D.BLOCK_LEG, sc['wedge_len'] / 1000, sc['wedge_n'], D.BACK_W, T, sc['back_len'] / 1000, sc['back_n']),
               'Sizes are ASSUMED (no published standard). Battery rails (%.1f high) are glued with an epoxy fillet, not blocked: too low for %.3f blocking.' % (D.BAT['rail'], D.BLOCK_LEG)]:
        y = para(sh, X, y, t_, 84, 'ts', 3.2, 2) + 0.8
    return sh
