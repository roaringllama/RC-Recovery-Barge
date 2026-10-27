"""A-004 Daggerboard variants: port sponson side elevations (hang R120, reverse 15 and 25 deg) and the blade sweep table."""
from .lib import *
from .tbl import table, para
import design as D
from model import geometry as G, hydro, variants

# layout positions (mm on the sheet); the content area is x 12 to 420, y 30 to 238
X_MIN, X_MAX, Y_MIN, Y_MAX = 12, 420, 30, 238
RH = 3.6
SCALES = (3, 4, 5, 6, 7, 8)                 # tried in this order: 1:3 first
OX = 28                                     # sheet X of the bow tip
ROW_HEAD, ROW_DIM, ROW_GAP = 5, 5, 1.5
TABLE_HEAD = 6
NOTE_GAP = 6                                # gap between the drawings and the text column
COLS = [('Variant', 52), ('Area mm2', 22), ('Ctr from bow', 26), ('Depth', 18), ('Tip over deck', 28), ('Trunk X', 28),
        ('Trunk len', 22), ('Blade sys g', 26), ('Total g', 20), ('LCG', 18), ('Stern', 18), ('Bow', 16), ('Over noz.', 20), ('Margin', 20), ('Fails', 40)]


def _row_data(label):
    """Solve one sweep variant at the design battery position. Returns everything a row needs, computed inside its context."""
    base, over = next((b, o) for l, b, o in D.BLADE_SWEEP if l == label)
    with variants.use(base, over, name=label):
        r = hydro.design()
        zd = r['deck']
        hs = G.housing(zd)
        ext, ret = G.blade_outline(True), G.blade_outline(False)
        zmax = max(zd(0), zd(D.LOA), max(p[1] for p in ret), hs['top'](hs['x1']) if hs else 0)
        zmin = min(-G.blade_depth(), G.SHOE_BOT)
        res = variants.metrics(r, __import__('model.checks', fromlist=['x']).run_all(r))
        return dict(label=label, base=base, over=over, r=r, zmax=zmax, zmin=zmin, m=res)


def _fits(den, rows):
    s = 1 / den
    h = sum(ROW_HEAD + (d['zmax'] - d['zmin']) * s + ROW_DIM + ROW_GAP for d in rows)
    h += TABLE_HEAD + RH * (len(D.BLADE_SWEEP) + 1)
    w = OX + s * (D.LOA + D.AFT_DECK_L) + NOTE_GAP
    return Y_MIN + h <= Y_MAX and w <= X_MAX - 160, h   # leave 160 mm for the text column


def _draw_row(sh, d, s, y_top, notes):
    label, base, over = d['label'], d['base'], d['over']
    with variants.use(base, over, name=label):
        r = d['r']
        zd = r['deck']
        wl = lambda X: r['d0'] - r['k'] * X
        T = D.SKIN_T
        b = G.blade_params()
        hs = G.housing(zd)
        oy = y_top + ROW_HEAD + d['zmax'] * s
        xs = lambda X: OX + s * (D.LOA - X)
        zs = lambda Z: oy - s * Z
        P = lambda pts: [(xs(x), zs(z)) for x, z in pts]
        zb = zs(d['zmin'])
        sh.text(X_MIN + 2, y_top + 2.6, '%s: hinge X %.0f Z %.0f, R%.0f, %.0f deg sector, points %s' % (
            label.upper(), b['hinge_x'], b['hinge_z'], b['R'], b['sector_deg'], 'forward' if b['dir'] == 'fwd' else 'aft'), 'tb')
        # water, then hull lines
        sh.add(f'<polygon points="{xs(D.LOA + 10):.2f},{zs(wl(D.LOA + 10)):.2f} {xs(-90):.2f},{zs(wl(-90)):.2f} {xs(-90):.2f},{zb:.2f} {xs(D.LOA + 10):.2f},{zb:.2f}" class="water" opacity=".55"/>')
        sh.pline(P([(D.LOA, zd(D.LOA)), (D.LOA, 0), (0, 0), (0, zd(0))]), 'thin')
        sh.line(xs(D.LOA), zs(0), xs(0), zs(0), 'thk')                           # keel
        sh.line(xs(D.LOA), zs(zd(D.LOA)), xs(0), zs(zd(0)), 'thk')               # deck line
        sh.line(xs(D.LOA + 10), zs(wl(D.LOA + 10)), xs(-90), zs(wl(-90)), 'wl')  # waterline
        lx = 150 # label X, clear of the blades and the bow items
        sh.text(xs(lx), zs(0) + 2.6, 'keel', 'ts', 'middle')
        sh.text(xs(lx), zs(zd(lx)) - 1.2, 'deck %.1f at the bow, %.1f at the stern' % (zd(D.LOA), zd(0)), 'ts', 'middle')
        sh.text(xs(-90) - 1, zs(wl(-90)) - 0.8, 'WL', 'ts', 'end')
        # skeg, shoe, nozzle
        sh.poly(P(G.SKEG), 'gray'); sh.poly(P(G.SHOE), 'gray')
        sh.rect(xs(G.NOZ_XF), zs(G.NOZ_ZTOP), D.NOZ_L * s, D.NOZ_OD * s, 'prop')
        sh.text(xs(G.NOZ_XA) + 1, zs(D.PROP_Z) + 0.8, 'nozzle', 'ts')
        sh.text(xs(G.SHOE_X1) + 1, zs(G.SHOE_BOT) + 2.4, 'skeg, shoe', 'ts')
        # trunk, tower or cap (dashed)
        tx0, tx1 = G.trunk_x()
        sh.poly(P([(tx0, 0), (tx1, 0), (tx1, zd(tx1) - T), (tx0, zd(tx0) - T)]), 'hid')
        if hs:
            sh.poly(P([(hs['x0'], zd(hs['x0'])), (hs['x1'], zd(hs['x1'])), (hs['x1'], hs['top'](hs['x1'])), (hs['x0'], hs['top'](hs['x0']))]), 'hid')
            sh.text(xs(hs['x0']) + 1.5, zs(hs['top'](hs['x0'])) + 2.4, hs['kind'] if hs['kind'] == 'tower' else 'bow cap', 'ts')
        if b['housing'] == 'cap':
            bx = G.blade_servo_box(zd)
            sh.rect(xs(bx.x1), zs(bx.z1), (bx.x1 - bx.x0) * s, (bx.z1 - bx.z0) * s, 'hid')
            sh.text(xs(bx.x0) + 1.5, zs(bx.z1) + 2.4, 'servo in cap', 'ts')
        # blade: extended solid, retracted dashed
        sh.poly(P(G.blade_outline(True)), 'blade')
        sh.poly(P(G.blade_outline(False)), 'hid')
        sh.circ(xs(b['hinge_x']), zs(b['hinge_z']), 1.0, 'obj', 'style="fill:#fff"')
        sh.text(xs(b['hinge_x']) + (-2 if b['dir'] == 'aft' else 2), zs(b['hinge_z']) + 3.4, 'hinge', 'ts', 'end' if b['dir'] == 'aft' else 'start')
        cx, cz = G.blade_centroid(True)
        sh.circ(xs(cx), zs(cz), 0.9, 'obj', 'style="fill:#111"')
        m = d['m']
        yd = zb + 4
        sh.dimh(xs(D.LOA), xs(cx), yd, '', zs(0), zs(cz))
        sh.text(xs(cx) + 2.6, yd + 0.8, '%.1f from bow' % m['area_center_from_bow'], 't')
        nx = OX + s * (D.LOA + D.AFT_DECK_L) + NOTE_GAP
        sh.text(nx, y_top + 2.6, 'Area %.0f mm2 (one blade), area center %.1f from the bow, depth %.1f, stowed tip %.1f above deck, over nozzle %.1f, margin %.1f after %.0f trough' % (
            m['area_mm2'], m['area_center_from_bow'], m['depth_below_keel'], m['stowed_tip_above_deck'], m['over_nozzle'], m['margin_after_trough'], D.TROUGH), 't')
        ny = y_top + 8
        for t in notes:
            ny = para(sh, nx, ny, t, int((X_MAX - nx) / 1.25), step=4.0) + 0.8


def build(sweep_rows=None):
    data = [_row_data(l) for l in D.SHEET_ROWS]
    tried = []
    for den in SCALES:
        ok, h = _fits(den, data)
        tried.append(den)
        if ok:
            break
    note = '1:%d' % den if den == SCALES[0] else '1:%d (1:%s do not fit)' % (den, ', 1:'.join(str(t) for t in tried[:-1]))
    sh = Sheet('A-004', 'Daggerboard variants', 'Port sponson, side elevations, bow at the left. Extended solid, stowed dashed. Batteries at %.0f.' % D.DESIGN_BAT_X, note)
    s = 1 / den
    y = Y_MIN
    rev = D.BLADE_VARIANTS['reverse']
    notes = [['Solid: blade extended. Dashed: blade stowed (extended blade rotated up about the hinge by the sector angle), trunk, tower, servo box.',
              'Dot: area center of the extended blade, dimensioned from the bow tip. WL: waterline at rest.'],
             ['Pivot midships, blade points forward. The servo drives it forward against a stop; gravity does not deploy it.',
              'Trunk from the hinge to X %.0f, %.0f wide, against the tunnel wall. Servo and spool in a box on the deck at the hinge.' % (rev['trunk_x1'], rev['trunk_w'])],
             ['Bow cap: X range where the stowed blade is above the deck underside, full sponson width, %.0f above the blade.' % D.CAP_CLR,
              'Trunk mass is %.0f g for every variant. Selected for the design: %s (APPROVED); the other variants are PENDING.' % (D.TRUNK_MASS, D.BLADE_VARIANT)]]
    for d, nt in zip(data, notes):
        h = ROW_HEAD + (d['zmax'] - d['zmin']) * s + ROW_DIM + ROW_GAP
        _draw_row(sh, d, s, y, nt)
        y += h
    # sweep table at the design battery position
    sweep_rows = sweep_rows or variants.sweep()[0]
    sel = [x for x in sweep_rows if x['battery_x'] == D.DESIGN_BAT_X]
    f = lambda v, p=1: ('%.*f' % (p, v))
    trs = [[x['variant'], f(x['area_mm2'], 0), f(x['area_center_from_bow']), f(x['depth_below_keel']), f(x['stowed_tip_above_deck']),
            '%.0f to %.0f' % (x['trunk_x0'], x['trunk_x1']), f(x['trunk_len'], 0), f(x['blade_system_g']), f(x['total_g'], 0), f(x['lcg_mm']),
            f(x['stern_draft']), f(x['bow_draft']), f(x['over_nozzle']), f(x['margin_after_trough']), x['failed_checks']] for x in sel]
    table(sh, X_MIN, y + TABLE_HEAD, COLS, trs, 'BLADE SWEEP, batteries at %.0f (design). Rows at the alternate position %.0f are in out/blade_sweep.csv. Check 6 is a warning only.' % (D.DESIGN_BAT_X, D.ALT_BAT_X[0]), rh=RH)
    return sh
