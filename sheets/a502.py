"""A-502 Frames, bulkheads, deck beams, battery rails, motor mount, servo pads and bow cap framing, with a schedule."""
import math
from .lib import *
from .wtbl import wtable
from .tbl import para
import design as D
from model import geometry as G, hydro, schedules as S

BF = 'style="fill:#f1e3c8"'


def _short(f):
    n = []
    if f['bulkhead']:
        n.append('bulkhead BH')
    for x in D.DECK_BEAMS:
        if abs(x - f['x']) <= D.FRAME_T:
            n.append('deck beam DB')
    if f['cut']:
        n.append('top member cut by ' + ', '.join(f['cut']))
    if f['clash']:
        n.append('crosses ' + ', '.join(c.replace(' (tunnel frame)', '') for c in f['clash']) + ': notch')
    if f['trunk_w'] is not None:
        n.append('beside trunk %.1f wide' % f['trunk_w'])
    return '; '.join(n)


def build(r=None):
    r = r or hydro.design()
    zd = r['deck']
    T = D.SKIN_T
    fr = S.frames(zd)
    sup, rail_l = S.supports(zd)
    hs = S.hatches(zd)
    ht = S.hatch_totals(hs)
    sh = Sheet('A-502', 'Frames, bulkheads and supports',
               'Frames and bulkheads, deck beams, battery rails, motor mount, servo pads, bow cap framing. 1/8 in (%.3f) parts unless noted.' % T, '1:3, 1:1, 1:2')
    # ---- plan 1:3, port sponson and half the tunnel, deck removed
    s = 1 / 3
    ox = 22
    xs = lambda X: ox + s * (D.LOA - X)
    oy = 92
    ys = lambda Y: oy - s * Y
    P = lambda pts: [(xs(x), ys(y)) for x, y in pts]
    sh.text(14, 33, 'PLAN, PORT SPONSON AND HALF THE TUNNEL, DECK REMOVED (bow at left). Frames F, bulkheads BH, deck beams DB.', 'tb')
    sh.pline(P(S.OUTER), 'obj')
    sh.pline(P(S.INNER), 'obj')
    sh.line(xs(D.LOA), ys(0), xs(0), ys(0), 'ctr')
    sh.line(xs(D.LOA), ys(float(G.outer_wall_y(D.LOA))), xs(D.LOA), ys(0), 'thin')
    sh.line(xs(0), ys(float(G.outer_wall_y(0))), xs(0), ys(0), 'thin')
    for f in fr:
        a, b = float(G.inner_wall_y(f['x'])), float(G.outer_wall_y(f['x']))
        sh.rect(xs(f['x'] + D.FRAME_T / 2), ys(b), D.FRAME_T * s, (b - a) * s, 'cut')
        sh.line(xs(f['x']), ys(a), xs(f['x']), ys(0), 'hid')
        sh.text(xs(f['x']), ys(b) - 1.6 - (int(f['mark'][1:]) % 2) * 2.6, f['mark'], 'ts', 'middle')
    for x in D.DECK_BEAMS:
        b = float(G.outer_wall_y(x))
        sh.rect(xs(x + D.DECK_BEAM_W / 2), ys(b), D.DECK_BEAM_W * s, b * s, 'gray')
        sh.text(xs(x), ys(0) + 4.2, 'DB %.0f' % x, 'ts', 'middle')
    for i, x in enumerate(G.BH, 1):
        sh.text(xs(x), ys(float(G.outer_wall_y(x))) - 7.8, 'BH%d X %.1f' % (i, x), 'tb', 'middle')
    # hatches, trunk, motor mount, rails, battery, cap
    for h in G.hatch_rects():
        if h['yc'] >= 0:
            y0c = max(h['y0'], 0.0)
            sh.rect(xs(h['x1']), ys(h['y1']), (h['x1'] - h['x0']) * s, (h['y1'] - y0c) * s, 'hid')
            sh.text(xs((h['x0'] + h['x1']) / 2), ys(h['yc'] + (0 if h['yc'] else 20)) + 0.8, h['name'], 'ts', 'middle')
    ty = G.trunk_y()
    tx0, tx1 = G.trunk_x()
    sh.rect(xs(tx1), ys(ty[1]), (tx1 - tx0) * s, (ty[1] - ty[0]) * s, 'blade')
    sh.text(xs((tx0 + tx1) / 2), ys(ty[0]) + 3.2, 'blade trunk', 'ts', 'middle')
    m = S.mount_dims()
    xa, xb = G.MOUNT[0][0], G.MOUNT[1][0]
    sh.rect(xs(xb), ys(G.YS + D.MOUNT_W / 2), (xb - xa) * s, D.MOUNT_W * s, 'gray')
    sh.text(xs((xa + xb) / 2), ys(G.YS) - 3.6, 'MM', 'ts', 'middle')
    for dy in (-1, 1):
        yc = G.BAT_YC + dy * (D.BAT['w'] / 2 - D.RAIL_W / 2)
        sh.rect(xs(D.BAT_SLIDE[1] + D.BAT['l'] / 2), ys(yc + D.RAIL_W / 2), rail_l * s, D.RAIL_W * s, 'cut')
    sh.text(xs((D.BAT_SLIDE[0] + D.BAT_SLIDE[1]) / 2), ys(30), 'RL rails %.0f long, battery slide X %.0f to %.0f' % (rail_l, D.BAT_SLIDE[0], D.BAT_SLIDE[1]), 'ts', 'middle')
    hz = G.housing(zd)
    if hz and hz['kind'] == 'cap':
        sh.rect(xs(hz['x1']), ys(float(G.outer_wall_y(hz['x0']))), (hz['x1'] - hz['x0']) * s, (float(G.outer_wall_y(hz['x0'])) - float(G.inner_wall_y(hz['x0']))) * s, 'hid')
        sh.text(xs((hz['x0'] + hz['x1']) / 2), ys(float(G.inner_wall_y(hz['x0']))) + 3.6, 'bow cap X %.0f to %.0f' % (hz['x0'], hz['x1']), 'ts', 'middle')
    sv = G.steer_servo_box()
    sp = D.PAD_MARGIN
    sh.rect(xs(sv.x1 + sp), ys(sv.y1 + sp), (sv.x1 - sv.x0 + 2 * sp) * s, (sv.y1 - sv.y0 + 2 * sp) * s, 'thin')
    sh.text(xs((sv.x0 + sv.x1) / 2), ys(0) - 1, 'SV', 'ts', 'middle')
    # ---- ring frames at 1:3 (sponson pieces), then one tunnel frame
    s3 = 1 / 3
    sh.text(14, 106, 'SPONSON FRAMES F1 to F%d, 1:3 (ring of %.1f members; dashed = battery envelope at the frame)' % (len(fr), D.FRAME_RIB), 'tb')
    fx = 16
    base = 142
    for f in fr:
        w, h = f['w_in'] * s3, f['h'] * s3
        sh.rect(fx, base - h, w, h, 'cut')
        if f['open_w'] > 0 and not f['bulkhead']:
            sh.rect(fx + D.FRAME_RIB * s3, base - h + D.FRAME_RIB * s3, f['open_w'] * s3, f['open_h'] * s3, 'obj', 'style="fill:#fff"')
        if f['clash'] and 'battery slide' in f['clash']:
            bz0 = T + D.BAT['rail']
            by = (G.BAT_YC - float(G.inner_wall_y(f['x'])) - T) - D.BAT['w'] / 2
            sh.rect(fx + by * s3, base - (T + D.BAT['rail'] + D.BAT['h']) * s3, D.BAT['w'] * s3, D.BAT['h'] * s3, 'hid')
        sh.text(fx + w / 2, base + 3.6, f['mark'], 'tb', 'middle')
        sh.text(fx + w / 2, base + 6.8, 'X %.0f' % f['x'], 'ts', 'middle')
        sh.text(fx + w / 2, base + 10, '%.1f x %.1f' % (f['w_in'], f['h']), 'ts', 'middle')
        if f['bulkhead']:
            sh.text(fx + w / 2, base + 13.2, 'BH solid', 'ts', 'middle')
        fx += 23
    tf = fr[len(fr) // 2]
    sh.text(fx + 2, 96, 'TUNNEL FRAME (at %s), 1:3' % tf['mark'], 'tb') if False else None
    sh.rect(fx + 3, base - tf['tun_h'] * s3, tf['tun_w'] * s3, tf['tun_h'] * s3, 'cut')
    sh.rect(fx + 3 + D.FRAME_RIB * s3, base - tf['tun_h'] * s3 + D.FRAME_RIB * s3, (tf['tun_w'] - 2 * D.FRAME_RIB) * s3, (tf['tun_h'] - 2 * D.FRAME_RIB) * s3, 'obj', 'style="fill:#fff"')
    sh.text(fx + 3 + tf['tun_w'] * s3 / 2, base + 3.6, 'tunnel piece of %s' % tf['mark'], 'tb', 'middle')
    sh.text(fx + 3 + tf['tun_w'] * s3 / 2, base + 6.8, '%.1f x %.1f above the roof plate' % (tf['tun_w'], tf['tun_h']), 'ts', 'middle')
    # ---- supports table (right of the frames)
    X = 268
    srows = []
    for q in sup:
        if q['mark'].startswith('BH'):
            srows.append((q['mark'], q['part'], str(q['qty']), '%.2f x %.2f x %.3f, X %.1f' % (q['w'], q['h'], q['t'], q['x'])))
    srows.append(('DB', 'Deck beam, full width (3)', '3', ', '.join('X %.0f: %.1f long' % (x, 2 * (G.HT + float(G.outer_off(x)))) for x in D.DECK_BEAMS) + '; %.2f wide x %.2f deep' % (D.DECK_BEAM_W, D.DECK_BEAM_T)))
    srows.append(('RL', 'Battery rail', '4', '%.0f x %.2f x %.1f' % (rail_l, D.RAIL_W, D.BAT['rail'])))
    srows.append(('MM', 'Motor mount, laminated', '2', '%.1f x %.0f, %.1f aft to %.1f fwd high, %d layers of %.3f, top at %.0f deg' % (m['l'], m['w'], m['h_aft'], m['h_fwd'], m['layers'], T, m['angle'])))
    srows.append(('MC', 'Motor clamp cap, ply', '2', '%.1f x %.0f x %.3f' % (m['l'], m['w'], T)))
    sv_ = D.STEER_SERVO
    srows.append(('SV', 'Steering servo pad, ply', '1', '%.1f x %.1f x %.3f' % (sv_['l'] + 2 * D.PAD_MARGIN, sv_['w'] + 2 * D.PAD_MARGIN, T)))
    bb = D.BLADE_BOX
    srows.append(('BV', 'Blade servo box doubler, ply, under the deck', '1 each sponson', '%.1f x %.1f x %.3f' % (bb['l'] + 2 * D.PAD_MARGIN, bb['w'] + 2 * D.PAD_MARGIN, T)))
    srows.append(('LP', 'Latch pad, ply, M3 nut captured', str(ht['latches']), '%.1f x %.1f x %.3f (A-503)' % (D.LATCH_PAD, D.LATCH_PAD, T)))
    srows.append(('RR', 'Hatch rim ring', str(ht['lids']), '%.3f thick, %.3f wide (A-503)' % (D.RIM_T, D.RIM_W)))
    capr = [f['mark'] for f in fr if hz and hz['kind'] == 'cap' and hz['x0'] < f['x'] < hz['x1']]
    if capr:
        srows.append(('CR', 'Bow cap ribs (frames inside the cap), per sponson', str(len(capr)), ', '.join('%s X %.0f %.1f high' % (f['mark'], f['x'], hz['ztop'] - zd(f['x'])) for f in fr if f['mark'] in capr)))
    cols = [('MARK', 11), ('PART', 54), ('QTY', 11), ('SIZE (mm)', 76)]
    ys0 = wtable(sh, X, 108, cols, srows, 'SUPPORT SCHEDULE', step=2.7, pad=0.6)
    # ---- frame schedule
    cols = [('MARK', 10), ('X', 11), ('SPONSON OUT', 21), ('INSIDE', 15), ('HEIGHT', 15), ('OPENING', 25), ('TUNNEL W', 18), ('TUNNEL H', 18), ('NOTES', 127)]
    rows = []
    for f in fr:
        ot = '%.1f x %.1f' % (f['open_w'], f['open_h']) if (f['open_w'] > 0 and not f['bulkhead']) else ('solid' if f['bulkhead'] else 'none')
        rows.append((f['mark'], '%.0f' % f['x'], '%.2f' % f['w_out'], '%.2f' % f['w_in'], '%.2f' % f['h'], ot, '%.2f' % f['tun_w'], '%.2f' % f['tun_h'], _short(f)))
    yf = wtable(sh, 160, 162, cols, rows, 'FRAME SCHEDULE (1/8 in, grain vertical; transom TR and tip TP are closures, A-103)', step=2.7, pad=0.6)
    # ---- details, left column
    sh.text(14, 162, 'MOTOR MOUNT MM, side view 1:1 (port; bow right)', 'tb')
    mx, my = 20, 184
    k = 1.0
    sx = lambda x: mx + (x - xa) * k
    sz = lambda z: my - z * k
    sh.rect(mx - 6, sz(0), (xb - xa) + 12, T, 'cut')
    sh.poly([(sx(p[0]), sz(p[1])) for p in G.MOUNT], 'gray')
    tan_ = (G.MOUNT[2][1] - G.MOUNT[3][1]) / (xb - xa)
    for i in range(1, m['layers']):
        z = T + i * T
        if z < G.MOUNT[2][1]:
            xz = max(xa, xa + (z - G.MOUNT[3][1]) / tan_)
            sh.line(sx(xz), sz(z), sx(xb), sz(z), 'thin')
    sh.line(sx(G.MOUNT[3][0]), sz(G.MOUNT[3][1]), sx(G.MOUNT[2][0]), sz(G.MOUNT[2][1]), 'thk')
    sh.text(mx, my + 7.5, '%.1f long x %.0f wide, %d layers of %.3f, top face at %.0f deg' % (m['l'], m['w'], m['layers'], T, m['angle']), 'ts')
    sh.text(mx, my + 11.5, 'ply clamp cap over the motor; blocking %.3f both long edges to the floor' % D.BLOCK_LEG, 'ts')
    # battery bay section 1:1
    sh.text(14, 201.5, 'BATTERY BAY SECTION at X %.0f, 1:1 (port sponson)' % D.DESIGN_BAT_X, 'tb')
    X0b = 20
    yi0 = float(G.inner_wall_y(D.DESIGN_BAT_X)) + T
    yo1 = float(G.outer_wall_y(D.DESIGN_BAT_X)) - T
    by_ = lambda Y: X0b + (Y - yi0)
    zb = 233
    sh.rect(by_(yi0) - T, zb, (yo1 - yi0) + 2 * T, T, 'cut')
    sh.rect(by_(yi0) - T, zb - 28, T, 28, 'cut')
    sh.rect(by_(yo1), zb - 28, T, 28, 'cut')
    for dy in (-1, 1):
        yc = G.BAT_YC + dy * (D.BAT['w'] / 2 - D.RAIL_W / 2)
        sh.rect(by_(yc - D.RAIL_W / 2), zb - D.BAT['rail'], D.RAIL_W, D.BAT['rail'], 'cut', BF)
    sh.rect(by_(G.BAT_YC - D.BAT['w'] / 2), zb - D.BAT['rail'] - D.BAT['h'], D.BAT['w'], D.BAT['h'], 'elec')
    sh.rect(by_(ty[0]), zb - 28, ty[1] - ty[0], 28, 'blade', 'style="opacity:.6"')
    sh.text(X0b, zb + 5, 'battery %.0f x %.0f on rails %.2f x %.1f; trunk Y %.1f to %.1f; gap to trunk %.2f, to wall %.2f' % (D.BAT['w'], D.BAT['h'], D.RAIL_W, D.BAT['rail'], ty[0], ty[1], G.BAT_YC - D.BAT['w'] / 2 - ty[1], yo1 - (G.BAT_YC + D.BAT['w'] / 2)), 'ts')
    # ---- bow cap framing, right column below the frame table
    if hz and hz['kind'] == 'cap':
        s4 = 1 / 4
        xa_, xb_ = hz['x0'] - 30, D.LOA
        cx0 = 170
        cxs = lambda X: cx0 + s4 * (xb_ - X)
        z0_, z1_ = zd(xa_) - 8, hz['ztop'] + 6
        czs = lambda Z: 236 - s4 * (Z - z0_)
        sh.text(160, yf + 5, 'BOW CAP FRAMING, profile 1:4. End plates CA and CF, ribs at the frames inside the cap, top plate CT; blade stowed dashed.', 'tb')
        sh.poly([(cxs(xb_), czs(zd(xb_))), (cxs(xa_), czs(zd(xa_))), (cxs(xa_), czs(zd(xa_) - T)), (cxs(xb_), czs(zd(xb_) - T))], 'cut')
        for X_ in (hz['x0'], hz['x1']):
            sh.line(cxs(X_), czs(zd(X_)), cxs(X_), czs(hz['ztop']), 'thk')
        sh.line(cxs(hz['x0']), czs(hz['ztop']), cxs(hz['x1']), czs(hz['ztop']), 'thk')
        for f in fr:
            if hz['x0'] < f['x'] < hz['x1']:
                sh.line(cxs(f['x']), czs(zd(f['x'])), cxs(f['x']), czs(hz['ztop']), 'thin')
                sh.text(cxs(f['x']), czs(hz['ztop']) - 4.8, f['mark'], 'ts', 'middle')
        sh.pline([(cxs(x), czs(z)) for x, z in G.blade_outline(False) if xa_ <= x <= xb_ and z >= z0_], 'hid')
        sh.text(cxs(hz['x0']) + 1, czs(hz['ztop']) - 1.2, 'CA X %.0f' % hz['x0'], 'ts')
        sh.text(cxs(hz['x1']) - 14, czs(hz['ztop']) - 1.2, 'CF X %.0f' % hz['x1'], 'ts')
        sh.text(cxs(hz['x0']) + 8, czs(hz['ztop']) + 8, 'cap top Z %.1f: %.1f above the deck at CA, %.1f at CF' % (hz['ztop'], hz['h0'], hz['h1']), 'ts')
        sh.text(cxs(hz['x0']) + 8, czs(hz['ztop']) + 12, 'ribs and end plates %.3f thick; each rib meets the deck and the top plate (two faces, blocked %.3f)' % (D.FRAME_T, D.BLOCK_LEG), 'ts')
    return sh
