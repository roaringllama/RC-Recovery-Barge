"""A-601 Weights, balance, trim table and the checks report, every number from the model."""
import textwrap
from .lib import *
from .tbl import table, para
import design as D
from model import geometry as G, hydro, weights as W, checks as C

_COL = {'PASS': '#1d7a3c', 'WARN': '#b36200', 'FAIL': '#b00020'}


def build(r=None, alts=None, results=None):
    r = r or hydro.design()
    alts = alts or [hydro.at(x, r) for x in D.ALT_BAT_X]
    trim_rows = [(D.DESIGN_BAT_X, r)] + list(zip(D.ALT_BAT_X, alts))     # design position first, then the alternates on the same deck
    results = results or C.run_all(r)
    sh = Sheet('A-601', 'Weights, balance and checks',
               'Bottom-up weight and balance, waterline at the design battery position, trim table, interference and fit checks', 'NTS')
    items = r['items']
    mom = sum(i[2] * i[3] for i in items)
    rows = [(n, '%.1f' % m, '%.0f' % x, format(round(m * x), ',')) for grp, n, m, x in items]
    rows.append(('TOTAL (LCG from the transom, mm)', '%.0f' % r['W'], '%.1f' % r['G'], format(round(mom), ',')))
    rh = 3.7
    yend = table(sh, 14, 40, [('ITEM (X from the transom, mm; batteries at X %.0f)' % D.DESIGN_BAT_X, 112), ('g', 16), ('X', 14), ('g x mm', 22)], rows,
                 'WEIGHT AND BALANCE, %s (blade variant: %s)' % (D.REV, D.BLADE_VARIANT), rh=rh)
    y = yend + 5
    grp = W.by_group(items)
    y = para(sh, 14, y, 'By group: ' + '; '.join('%s %.0f g' % (k, v) for k, v in grp.items()), 130, hang=0)
    y = para(sh, 14, y, 'Basis: balsa %.3f g/cm3 (UNVERIFIED), %.3f mm skin; glass %.0f g/m2 outside and %.0f g/m2 inside over %.2f m2 (ESTIMATES, weigh a test panel).' % (
        D.BALSA_RHO, D.SKIN_T, D.GLASS_OUT, D.GLASS_IN, r['area'] / 1e6), 130, hang=0)
    y = para(sh, 14, y, 'Hydrostatics: displacement %.1f g vs weight %.1f g; LCB %.1f vs LCG %.1f. Bilge radius R%.0f is not in the displacement.' % (r['disp'], r['W'], r['lcb'], r['G'], D.BILGE_R), 130, hang=0)
    y += 2
    sh.text(14, y, 'NOT IN THE TOTAL (no published weight, so the total is a floor):', 'tb'); y += 4.2
    y = para(sh, 14, y, ', '.join(n for _, n, _, _ in W.UNWEIGHED) + '.', 130, hang=0)
    y += 2
    sh.text(14, y, 'DECISIONS AND PENDING ITEMS (design.py):', 'tb'); y += 4.2
    for t in ['Batteries at X %.0f (APPROVED); slide %.0f to %.0f; %s are alternate positions on the same deck.' % (D.DESIGN_BAT_X, D.BAT_SLIDE[0], D.BAT_SLIDE[1], ' and '.join('%.0f' % x for x in D.ALT_BAT_X)),
              'Hatches HB (X %.0f to %.0f, %.0f wide) and HC (X %.0f to %.0f); receiver X %.0f to %.0f on the roof, forward of the ESCs and inside HC. Battery service position X %.0f.' % (
                  D.HATCHES['HB']['x0'], D.HATCHES['HB']['x1'], D.HATCHES['HB']['w'], D.HATCHES['HC']['x0'], D.HATCHES['HC']['x1'], D.RX['x0'], D.RX['x0'] + D.RX['l'], D.BAT_SERVICE_X),
              'Water jackets %s (owner may delete); outer bilge radius R%.0f.' % ('fitted' if D.JACKETS else 'deleted', D.BILGE_R),
              'Batteries %.1f outboard on their rails (BAT_Y_OFFSET); owner may prefer the trunk on the outboard wall instead.' % D.BAT_Y_OFFSET,
              'Blade variant %s is approved; nozzle post cut to %.1f from %.0f mm stock (check 18).' % (D.BLADE_VARIANT, G.post_required_length(r['deck']), D.NOZ_POST_STOCK_L)]:
        sh.text(14, y, t, 't'); y += 3.8
    y += 6
    drows = []
    for rho, rr in hydro.density_cases(r):
        drows.append(('%.3f g/cm3 (%.0f lb/ft3)' % (rho, rho * D.LB_FT3_PER_G_CM3), '%.1f' % rr['W'], '%.1f' % rr['G'], '%.1f' % rr['d0'], '%.1f' % rr['over'], '%.1f' % (rr['over'] - D.TROUGH)))
    y = table(sh, 14, y + 4, [('BALSA DENSITY', 40), ('TOTAL g', 20), ('LCG', 16), ('STERN DRAFT', 26), ('OVER NOZZLE', 26), ('MARGIN, %.0f TROUGH' % D.TROUGH, 34)], drows,
              'DENSITY SENSITIVITY (batteries at %.0f, same built deck; balsa is the largest unverified input)' % D.DESIGN_BAT_X, rh=4.2)
    # ---- right column
    X0 = 190
    trows = []
    for b, rr in trim_rows:
        trows.append(('%.0f%s' % (b, ' (design)' if b == D.DESIGN_BAT_X else ''), '%.1f' % rr['d0'], '%.1f' % rr['bow'], '%.2f' % -rr['trim'],
                      '%.1f' % rr['over'], '%.1f' % (rr['over'] - D.TROUGH), '%.2f' % rr['deck_off_level'], '%.0f' % rr['W']))
    yt = table(sh, X0, 40, [('BATTERY X', 26), ('STERN DRAFT', 26), ('BOW DRAFT', 24), ('BOW DOWN, DEG', 28), ('OVER NOZZLE', 26), ('MARGIN, %.0f TROUGH' % D.TROUGH, 40), ('DECK OFF LEVEL, DEG', 38), ('g', 14)], trows,
               'TRIM AT REST (deck built level at the design battery position; sponson %.1f at the transom, full width from X %.0f)' % (D.AFT_W, D.AFT_TAPER_X), rh=4.2)
    y = yt + 3
    y = para(sh, X0, y, 'Drafts in mm below the keel at the transom and at the bow tip. Water over the nozzle top is the stern draft less the nozzle top at Z %.0f.' % G.NOZ_ZTOP, 128, hang=0)
    y += 5
    sh.text(X0, y, 'CHECKS REPORT (interference and fit; no design value was changed to pass a check)', 'tb'); y += 3
    cols = [('#', 9), ('CHECK', 52), ('RESULT', 14), ('NUMBERS', 150)]
    x = X0
    for n, w in cols:
        sh.rect(x, y, w, 4.2, 'thin', 'style="fill:#ececec"'); sh.text(x + 1, y + 3, n, 'tb'); x += w
    y += 4.2
    for name, ok, msg in results:
        num, _, title = name.partition(' ')
        lv = C.level(name, ok)
        lines = textwrap.wrap(msg, 124)
        tl = textwrap.wrap(title, 30)
        n = max(len(lines), len(tl))
        h = 3.2 * n + 1.4
        x = X0
        for (cn, w), v in zip(cols, (num, None, None, None)):
            sh.rect(x, y, w, h, 'thin')
            x += w
        sh.text(X0 + 1, y + 3.1, num, 'tb')
        for i, ln in enumerate(tl):
            sh.text(X0 + 10, y + 3.1 + 3.2 * i, ln, 't')
        sh.add(f'<text x="{X0 + 62:.2f}" y="{y + 3.1:.2f}" class="tb" style="fill:{_COL[lv]}">{lv}</text>')
        for i, ln in enumerate(lines):
            sh.text(X0 + 77, y + 3.1 + 3.2 * i, ln, 't')
        y += h
    return sh
