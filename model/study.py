"""Prop and nozzle study: the whole model run again with the alternate prop and nozzle at the same axis height.

    with study.alternate():
        r = hydro.design()

The nozzle outside diameter sets values that geometry.py computes once (nozzle top, shoe, skeg), so the context swaps design.NOZ_OD and
design.PROP_D and reloads the model modules in place; on exit it restores both and reloads again. Nothing in design.py changes on disk.
"""
import importlib
import sys
from contextlib import contextmanager
import design as D
from . import geometry, parts, weights, hydro, checks, schedules

_ORDER = (geometry, parts, weights, hydro, schedules, checks)       # dependency order: geometry first


def _reload():
    for m in _ORDER:
        importlib.reload(sys.modules[m.__name__])


@contextmanager
def alternate():
    """Model context with PROP_D_ALT and NOZ_OD_ALT in place of PROP_D and NOZ_OD (PROP_Z, the axis height, is unchanged)."""
    saved = (D.PROP_D, D.NOZ_OD)
    D.PROP_D, D.NOZ_OD = D.PROP_D_ALT, D.NOZ_OD_ALT
    _reload()
    try:
        yield
    finally:
        D.PROP_D, D.NOZ_OD = saved
        _reload()


def row(label, prop, noz, r, results):
    """One study row from a hydro result r and its checks."""
    g = sys.modules['model.geometry']
    return dict(label=label, prop=prop, noz=noz, axis=D.PROP_Z, top=g.NOZ_ZTOP, W=r['W'], d0=r['d0'], over=r['over'], margin=r['over'] - D.TROUGH,
                radial=(noz - prop) / 2, bow=r['bow'], trim=r['trim'], off=r['deck_off_level'], failed=[n.split()[0] for n, ok, _ in results if not ok])


def rows(r=None, results=None):
    """[design row, alternate row]: the design prop and nozzle from r, then the alternate solved afresh (own deck, own checks)."""
    r = r or hydro.design()
    results = results or checks.run_all(r)
    out = [row('design', D.PROP_D, D.NOZ_OD, r, results)]
    with alternate():
        ra = sys.modules['model.hydro'].design()
        res = sys.modules['model.checks'].run_all(ra)
        out.append(row('alternate', D.PROP_D, D.NOZ_OD, ra, res))
    return out
