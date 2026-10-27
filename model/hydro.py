"""Hydrostatic solve (method of wb9.solve): HYDRO_STRIPS strips, fsolve on stern draft and trim with fixed skeg buoyancy.

The waterline in hull coordinates is Z = d0 - k X. The deck is parallel to it (FREEBOARD above) at the design
battery position. Other battery positions are solved on that same built deck (pass fixed_deck).
The rounds are modeled (rounds=True, the default): the four bilge corners (two per sponson) are subtracted from the section of every
strip, R^2 (1 - pi/4) each when the corner is under water (a smaller part when the draft there is less than R), and the skeg root fillets
are added to the skeg buoyancy. rounds=False gives the square-section hull, used to report what the rounds change.
"""
import math
import numpy as np
from scipy.optimize import fsolve
import design as D
from . import geometry as G
from . import weights as W


CORNERS = 2 * 2                    # bottom corners of the hull: outer and tunnel side of each of the two sponsons


def _integ(d0, k, n=None, rounds=True):
    n = n or D.HYDRO_STRIPS
    dx = D.LOA / n
    Xs = (np.arange(n) + 1 / 2) * dx
    h = np.maximum(0, d0 - k * Xs)
    a = 2 * (G.outer_off(Xs) - G.inner_off(Xs)) * dx
    vol = (a * h).sum()
    mom = (a * h * Xs).sum()
    skeg, skeg_x = (G.SKEG_VOL, G.SKEG_BUOY_X) if rounds else (G.SKEG_VOL_BASE, G.SKEG_BUOY_X_BASE)
    if rounds:
        cut = CORNERS * G.round_area(G.bilge_r(Xs), h) * dx          # mm3 removed from each strip by the four bilge rounds
        vol, mom = vol - cut.sum(), mom - (cut * Xs).sum()
    V = skeg * 1000 + vol
    M = skeg * 1000 * skeg_x + mom
    return V / 1000, M / 1000          # cm3 (= g of fresh water) and its moment


def round_volumes(d0, k, n=None):
    """Volumes (cm3) the rounds change at a waterline: dict(bilge=-removed from the strips, fillet=+added to the skeg)."""
    n = n or D.HYDRO_STRIPS
    dx = D.LOA / n
    Xs = (np.arange(n) + 1 / 2) * dx
    h = np.maximum(0, d0 - k * Xs)
    return dict(bilge=-(CORNERS * G.round_area(G.bilge_r(Xs), h) * dx).sum() / 1000, fillet=G.SKEG_VOL_FILLET)


def solve(bat_x=None, fixed_deck=None, rho=None, rounds=True):
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
        f = lambda p: [_integ(*p, rounds=rounds)[0] - Wt, _integ(*p, rounds=rounds)[1] / _integ(*p, rounds=rounds)[0] - Gx]
        prev = d0
        d0, k = fsolve(f, [d0, k], xtol=D.HYDRO_TOL)
        if fixed_deck is None and abs(d0 - prev) < D.HYDRO_TOL:
            break
    d0, k = float(d0), float(k)
    if fixed_deck is None:
        deck = G.deck_fn(d0, k)          # the built deck, parallel to the converged waterline
    V, M = _integ(d0, k, rounds=rounds)
    built = fixed_deck['deck_params'][1] if fixed_deck is not None else k
    return dict(W=Wt, G=Gx, d0=d0, k=k, bow=d0 - k * D.LOA, over=d0 - G.NOZ_ZTOP,
                trim=math.degrees(math.atan(k)), deck=deck, deck_params=(fixed_deck['deck_params'] if fixed_deck is not None else (d0, k)),
                items=items, area=area, disp=V, lcb=M / V, bat_x=bat_x, rho=D.BALSA_RHO if rho is None else rho, rounds=rounds,
                round_vol=round_volumes(d0, k) if rounds else dict(bilge=0.0, fillet=0.0),
                deck_off_level=math.degrees(math.atan(built)) - math.degrees(math.atan(k)) if fixed_deck is not None else 0)


def design(rounds=True):
    return solve(D.DESIGN_BAT_X, rounds=rounds)


def round_effect(r=None):
    """What the rounds change at the design position: the design solve (rounds in) against the same boat with square sections.
    Returns dict(with, without, d0, bow, over, bilge, fillet) with the changes as with minus without (mm, cm3)."""
    r = r or design()
    sq = design(rounds=False)
    return dict(with_=r, without=sq, d0=r['d0'] - sq['d0'], bow=r['bow'] - sq['bow'], over=r['over'] - sq['over'],
                bilge=r['round_vol']['bilge'], fillet=r['round_vol']['fillet'], skeg_edges=-G.SKEG_EDGE_VOL)


def at(bat_x, base=None):
    """Solve at another battery position on the deck built for the design position."""
    base = base or design()
    return solve(bat_x, fixed_deck=base, rounds=base.get('rounds', True))


def at_density(rho, base=None, bat_x=None):
    """Same built deck and battery position as `base` (default the design solve), balsa at `rho` g/cm3."""
    base = base or design()
    return solve(base['bat_x'] if bat_x is None else bat_x, fixed_deck=base, rho=rho, rounds=base.get('rounds', True))


def density_cases(base=None):
    """The two reported densities: BALSA_RHO (design) and BALSA_RHO_HI, both on the deck built at the design density.
    Returns [(rho, result)]; the first is the base itself."""
    base = base or design()
    return [(D.BALSA_RHO, base), (D.BALSA_RHO_HI, at_density(D.BALSA_RHO_HI, base))]
