"""Blade variant override: run the whole model (weights, hydro, checks) for any blade parameter dict without editing files.

    with variants.use('reverse', dict(sector_deg=20.0), name='reverse 20 deg'):
        r = hydro.design()

use() temporarily installs the merged parameter dict in D.BLADE_VARIANTS under `name`, selects it as D.BLADE_VARIANT,
and restores both on exit. Nothing in design.py is changed on disk.
"""
import csv
from contextlib import contextmanager
import design as D
from . import geometry as G, hydro, checks, weights

COLS = ['variant', 'battery_x', 'area_mm2', 'area_center_from_bow', 'depth_below_keel', 'stowed_tip_above_deck',
        'trunk_x0', 'trunk_x1', 'trunk_len', 'blade_system_g', 'total_g', 'lcg_mm', 'stern_draft', 'bow_draft',
        'over_nozzle', 'margin_after_trough', 'failed_checks']


def merged(base, overrides=None):
    """Parameter dict: base (a key of D.BLADE_VARIANTS or a dict) with `overrides` replacing entries."""
    p = dict(D.BLADE_VARIANTS[base] if not isinstance(base, dict) else base)
    p.update(overrides or {})
    return p


@contextmanager
def use(base, overrides=None, name=None):
    """Model context for a blade variant: a key or dict, plus overrides."""
    params = merged(base, overrides)
    name = name or (base if not isinstance(base, dict) else 'custom')
    saved_sel, had, old = D.BLADE_VARIANT, name in D.BLADE_VARIANTS, D.BLADE_VARIANTS.get(name)
    D.BLADE_VARIANTS[name] = params
    D.BLADE_VARIANT = name
    try:
        yield params
    finally:
        D.BLADE_VARIANT = saved_sel
        if had:
            D.BLADE_VARIANTS[name] = old
        else:
            del D.BLADE_VARIANTS[name]


@contextmanager
def deck_plan(plan):
    """Model context for one deck plan ('rect' or 'taper'): installs D.DECK_PLAN and restores it on exit. Nothing in design.py is changed on disk."""
    G.deck_plan(plan)
    saved = D.DECK_PLAN
    D.DECK_PLAN = plan
    try:
        yield plan
    finally:
        D.DECK_PLAN = saved


def plan_rows():
    """One row per deck plan (D.DECK_PLANS) at the design battery position: weight, LCG, drafts, trim, water over the nozzle, aft deck beam margin,
    deck skin area, the failed checks, and the hydro result and results themselves."""
    rows = []
    for p in D.DECK_PLANS:
        with deck_plan(p):
            r = hydro.design()
            res = checks.run_all(r)
            k = G.aft_cantilever()
            rows.append(dict(plan=p, W=r['W'], G=r['G'], d0=r['d0'], bow=r['bow'], trim=r['trim'], over=r['over'], margin=r['over'] - D.TROUGH,
                             beam_margin=k['margin'], deflection=k['defl'], bar_width=G.bumper_front_width(), deck_area=G.hull_deck_area() + G.overhang_area() + G.aft_deck_area(),
                             failed=[n.split()[0] for n, ok, _ in res if not ok], r=r, results=res))
    return rows


@contextmanager
def launcher(fitted=True):
    """Model context with the line launcher fitted (or not): installs D.LAUNCHER_FITTED and restores it on exit. Nothing in design.py is changed on disk."""
    saved = D.LAUNCHER_FITTED
    D.LAUNCHER_FITTED = fitted
    try:
        yield fitted
    finally:
        D.LAUNCHER_FITTED = saved


def launcher_rows(r=None):
    """Trim with the line launcher not fitted, then fitted: weight, LCG, stern draft, bow draft, trim, water over the nozzle top, margin after the trough,
    the failed checks. Each case is solved on its own deck at the design battery position (the deck is built parallel to the waterline), like plan_rows.
    `r` is the design result of the current setting and is reused for the case that matches D.LAUNCHER_FITTED."""
    rows, now = [], D.LAUNCHER_FITTED
    for fitted in (False, True):
        with launcher(fitted):
            rr = r if (r is not None and fitted == now and r.get('bat_x') == D.DESIGN_BAT_X) else hydro.design()
            res = checks.run_all(rr)
            rows.append(dict(fitted=fitted, W=rr['W'], G=rr['G'], d0=rr['d0'], bow=rr['bow'], trim=rr['trim'], over=rr['over'], margin=rr['over'] - D.TROUGH,
                             failed=[n.split()[0] for n, ok, _ in res if not ok], r=rr, results=res))
    return rows


def failed(results):
    """Names (numbers) of failed checks; a warning-only failure is marked (warn)."""
    out = []
    for n, ok, _ in results:
        if not ok:
            num = n.split()[0]
            out.append(num + ('(warn)' if checks.level(n, ok) == 'WARN' else ''))
    return out


def metrics(r, results):
    """One row of numbers for the selected variant at the hydro result r."""
    tx0, tx1 = G.trunk_x()
    blade_g = sum(m for grp, _, m, _ in r['items'] if grp == 'Blades')
    return dict(area_mm2=G.blade_area(), area_center_from_bow=G.blade_center_from_bow(), depth_below_keel=G.blade_depth(),
                stowed_tip_above_deck=G.stowed_tip_height(r['deck']), trunk_x0=tx0, trunk_x1=tx1, trunk_len=tx1 - tx0,
                blade_system_g=blade_g, total_g=r['W'], lcg_mm=r['G'], stern_draft=r['d0'], bow_draft=r['bow'],
                over_nozzle=r['over'], margin_after_trough=r['over'] - D.TROUGH, battery_x=r['bat_x'],
                failed_checks=','.join(failed(results)) or 'none')


def sweep():
    """Rows for every D.BLADE_SWEEP entry at every D.SWEEP_BAT_X. Each variant is solved at the design battery position;
    the other positions are solved on that variant's deck. Returns (rows, runs) where runs keeps (label, bat_x, r, results)."""
    rows, runs = [], []
    for label, base, over in D.BLADE_SWEEP:
        with use(base, over, name=label):
            r0 = hydro.design()
            for bx in D.SWEEP_BAT_X:
                r = r0 if bx == D.DESIGN_BAT_X else hydro.at(bx, r0)
                res = checks.run_all(r)
                row = dict(variant=label, **metrics(r, res))
                rows.append(row)
                runs.append((label, bx, r, res))
    return rows, runs


def write_csv(rows, path):
    with open(path, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(COLS)
        for r in rows:
            w.writerow([r[c] if isinstance(r[c], str) else ('%.1f' % r[c]) for c in COLS])


def table_text(rows):
    cells = [COLS] + [[r[c] if isinstance(r[c], str) else ('%.1f' % r[c]) for c in COLS] for r in rows]
    wd = [max(len(row[i]) for row in cells) for i in range(len(COLS))]
    return '\n'.join('  '.join(c.ljust(w) for c, w in zip(row, wd)).rstrip() for row in cells)
