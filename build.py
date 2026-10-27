"""Build everything from the one model (design.py): checks report, weights.csv, and the sheets as PDF and PNG.

Run:  python3 build.py
Failed checks are printed and marked; the build continues.
"""
import csv
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

import design as D
from model import hydro, checks, weights, variants
from tools import build_list
from sheets import a000, a101, a103, a104, a301, a401, a501, a502, a503, a601, a004, render

OUT = os.path.join(ROOT, 'out')


def main():
    os.makedirs(OUT, exist_ok=True)
    r = hydro.design()
    alts = [hydro.at(x, r) for x in D.ALT_BAT_X]

    results = checks.run_all(r)
    text = checks.report(results)
    print(text)
    print()
    print('WEIGHT %.1f g, LCG %.1f mm from the transom (batteries at %.0f, blade variant %s)' % (r['W'], r['G'], D.DESIGN_BAT_X, D.BLADE_VARIANT))
    print('TRIM stern draft %.1f, bow draft %.1f, trim %.2f deg bow down, water over nozzle top %.1f (%.1f left after a %.0f mm trough)' % (
        r['d0'], r['bow'], -r['trim'], r['over'], r['over'] - D.TROUGH, D.TROUGH))
    for bx, rr in [(D.DESIGN_BAT_X, r)] + list(zip(D.ALT_BAT_X, alts)):
        print('TRIM batteries at %.0f: %.1f g, LCG %.1f, stern draft %.1f, bow draft %.1f, over nozzle top %.1f, %.1f after the trough' % (bx, rr['W'], rr['G'], rr['d0'], rr['bow'], rr['over'], rr['over'] - D.TROUGH))
    for rho, rr in hydro.density_cases(r):
        print('DENSITY balsa %.3f g/cm3: %.1f g, LCG %.1f, stern draft %.1f, over nozzle top %.1f, %.1f after the trough' % (rho, rr['W'], rr['G'], rr['d0'], rr['over'], rr['over'] - D.TROUGH))
    print('NOT IN THE TOTAL (no published weight): ' + ', '.join(n for _, n, _, _ in weights.UNWEIGHED))
    with open(os.path.join(OUT, 'checks.txt'), 'w') as f:
        f.write(text + '\n')

    with open(os.path.join(OUT, 'weights.csv'), 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['group', 'name', 'mass_g', 'x_mm', 'moment_g_mm'])
        for grp, name, m, x in r['items']:
            w.writerow([grp, name, '%.2f' % m, '%.1f' % x, '%.0f' % (m * x)])
        w.writerow(['TOTAL', 'weight and LCG', '%.2f' % r['W'], '%.1f' % r['G'], '%.0f' % sum(m * x for _, _, m, x in r['items'])])
        for grp, name, m, x in weights.UNWEIGHED:
            w.writerow([grp, name, '', '', 'not in the total'])

    sweep_rows, _ = variants.sweep()
    variants.write_csv(sweep_rows, os.path.join(OUT, 'blade_sweep.csv'))
    print()
    print('BLADE SWEEP (out/blade_sweep.csv), batteries at %s' % ' and '.join('%.0f' % x for x in D.SWEEP_BAT_X))
    print(variants.table_text(sweep_rows))

    body = [a101.build(r, alts), a103.build(r), a104.build(r), a301.build(r, alts), a401.build(r, alts), a501.build(r),
            a502.build(r), a503.build(r), a601.build(r, alts, results), a004.build(sweep_rows)]
    index = [a000.SELF + (a000.CONTENTS,)] + [(sh.no, sh.title, sh.scale, sh.sub) for sh in body]
    sheets = a000.build(r, index) + body
    pdf = os.path.join(OUT, 'RC_Recovery_Cat_Drawings_%s.pdf' % D.REV)
    render.render(sheets, pdf, OUT)
    print('wrote %s' % build_list.main(OUT, r))
    print('wrote %s and %s' % (pdf, os.path.join(OUT, 'p1.png to p%d.png' % len(sheets))))


if __name__ == '__main__':
    main()
