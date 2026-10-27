"""Hydrostatic solve (method of wb9.solve): HYDRO_STRIPS strips, fsolve on stern draft and trim with fixed skeg buoyancy.

The waterline in hull coordinates is Z = d0 - k X. The deck is parallel to it (FREEBOARD above) at the design
battery position. Other battery positions are solved on that same built deck (pass fixed_deck).
The bilge radius is not modeled (displacement is slightly overstated, drawn only).
"""
import math
import numpy as np
from scipy.optimize import fsolve
import design as D
from . import geometry as G
from . import weights as W


def _integ(d0, k, n=None):
    n = n or D.HYDRO_STRIPS
    dx = D.LOA / n
    Xs = (np.arange(n) + 1 / 2) * dx
    h = np.maximum(0, d0 - k * Xs)
    a = 2 * (G.outer_off(Xs) - G.inner_off(Xs)) * dx
    V = G.SKEG_VOL * 1000 + (a * h).sum()
    M = G.SKEG_VOL * 1000 * G.SKEG_BUOY_X + (a * h * Xs).sum()
    return V / 1000, M / 1000          # cm3 (= g of fresh water) and its moment


def solve(bat_x=None, fixed_deck=None, rho=None):
    """Returns dict: W, G (LCG), d0 (stern draft), bow, k, trim (deg), over (water over nozzle top at the stern draft),
    deck (function), deck_params (d0, k), items, area, disp, lcb, deck_off_level (deg, vs the built deck)."""
    bat_x = D.DESIGN_BAT_X if bat_x is None else bat_x
    d0, k = D.D0_GUESS, D.K_GUESS
    if fixed_deck is not None:
        d0, k = fixed_deck['deck_params']
    passes = 1 if fixed_deck is not None else D.HYDRO_ITER
    for _ in range(passes):
        deck = fixed_deck['deck'] if fixed_deck is not None else G.deck_fn(d0, k)
        items, area = W.build_items(deck, bat_x, rho)
        Wt, Gx = W.totals(items)
        f = lambda p: [_integ(*p)[0] - Wt, _integ(*p)[1] / _integ(*p)[0] - Gx]
        prev = d0
        d0, k = fsolve(f, [d0, k], xtol=D.HYDRO_TOL)
        if fixed_deck is None and abs(d0 - prev) < D.HYDRO_TOL:
            break
    d0, k = float(d0), float(k)
    if fixed_deck is None:
        deck = G.deck_fn(d0, k)          # the built deck, parallel to the converged waterline
    V, M = _integ(d0, k)
    built = fixed_deck['deck_params'][1] if fixed_deck is not None else k
    return dict(W=Wt, G=Gx, d0=d0, k=k, bow=d0 - k * D.LOA, over=d0 - G.NOZ_ZTOP,
                trim=math.degrees(math.atan(k)), deck=deck, deck_params=(fixed_deck['deck_params'] if fixed_deck is not None else (d0, k)),
                items=items, area=area, disp=V, lcb=M / V, bat_x=bat_x, rho=D.BALSA_RHO if rho is None else rho,
                deck_off_level=math.degrees(math.atan(built)) - math.degrees(math.atan(k)) if fixed_deck is not None else 0)


def design():
    return solve(D.DESIGN_BAT_X)


def at(bat_x, base=None):
    """Solve at another battery position on the deck built for the design position."""
    return solve(bat_x, fixed_deck=base or design())


def at_density(rho, base=None, bat_x=None):
    """Same built deck and battery position as `base` (default the design solve), balsa at `rho` g/cm3."""
    base = base or design()
    return solve(base['bat_x'] if bat_x is None else bat_x, fixed_deck=base, rho=rho)


def density_cases(base=None):
    """The two reported densities: BALSA_RHO (design) and BALSA_RHO_HI, both on the deck built at the design density.
    Returns [(rho, result)]; the first is the base itself."""
    base = base or design()
    return [(D.BALSA_RHO, base), (D.BALSA_RHO_HI, at_density(D.BALSA_RHO_HI, base))]
