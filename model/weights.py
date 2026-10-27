"""Weight and balance: item list (group, name, mass g, X mm) built from design.py and geometry.

Hull skin masses come from areas, glass from areas. Returns items, total, LCG.
"""
import math
import numpy as np
import design as D
from . import geometry as G
from . import parts as P

# Bought items with no published weight: NOT in the total. (group, name, mass, X)
UNWEIGHED = [
    ('Not weighed', 'Kort nozzles (2)', None, None),
    ('Not weighed', 'Propellers (2)', None, None),
    ('Not weighed', 'Motor mounts, bought (2)', None, None),
    ('Not weighed', 'Water fittings', None, None),
    ('Not weighed', 'Ball links', None, None),
    ('Not weighed', 'Bellows', None, None),
]


def _k(rho=None):
    """Balsa g per mm3 for a density in g/cm3 (default D.BALSA_RHO)."""
    return (D.BALSA_RHO if rho is None else rho) / 1000


def hull_items(zd, rho=None):
    """Balsa skin items by area. Returns (items, area mm2) where area is every skinned surface."""
    _K = _k(rho)
    n = D.HULL_STRIPS
    dx = D.LOA / n
    Xs = (np.arange(n) + 1 / 2) * dx
    T = D.SKIN_T
    inw, outw = G.inner_off, G.outer_off
    it = []
    area = 0.0

    def add(name, vol, mom, a):
        nonlocal area
        it.append(('Hull skin', name, vol * _K, mom / vol if vol else 0))
        area += a

    wsp = outw(Xs) - inw(Xs)
    h = zd(Xs) - 2 * T
    dsO = np.hypot(dx, outw(Xs + dx / 2) - outw(Xs - dx / 2))     # wall length per strip
    dsI = np.hypot(dx, inw(Xs + dx / 2) - inw(Xs - dx / 2))
    v = 2 * wsp * dx * T
    add('Sponson bottoms (2)', v.sum(), (v * Xs).sum(), 2 * (wsp * dx).sum())
    v = 2 * h * dsO * T
    add('Outer walls (2)', v.sum(), (v * Xs).sum(), 2 * (h * dsO).sum())
    v = 2 * h * dsI * T
    add('Inner walls (2)', v.sum(), (v * Xs).sum(), 2 * (h * dsI).sum())
    tw = 2 * (G.HT + inw(Xs))
    v = tw * dx * T
    add('Tunnel roof plate', v.sum(), (v * Xs).sum(), (tw * dx).sum())
    dw = 2 * (G.HT + outw(Xs))
    v = dw * dx * D.SKIN_T
    add('Deck (full width)', v.sum(), (v * Xs).sum(), (dw * dx).sum())
    v = D.AFT_DECK_L * D.AFT_DECK_W * D.AFT_DECK_T
    add('Aft deck over nozzles', v, v * (-D.AFT_DECK_L / 2), D.AFT_DECK_L * D.AFT_DECK_W)
    ph = zd(D.LOA) - 2 * D.PUSH_PAD_INSET
    v = D.BEAM * ph * D.PUSH_PAD_T
    add('Bow push pad', v, v * (D.LOA - D.PUSH_PAD_T / 2), D.BEAM * ph)
    wa = float(outw(0) - inw(0))
    ta = 2 * (G.HT + float(inw(0)))
    v = (2 * wa * (zd(0) - 2 * T) + ta * (zd(0) - T - G.ROOF_Z1)) * T
    add('Transom closures', v, 0.0, 2 * wa * zd(0) + ta * (zd(0) - G.ROOF_Z1))
    plates = 2 * 2 * G.SKEG_TRI_AREA * T                 # two skegs, two plates each
    shoes = 2 * G.SHOE_AREA * D.SHOE_T
    v = plates + shoes
    add('Skegs and shoes (2)', v, plates * G.SKEG_X0 / (1 + 2) + shoes * G.SHOE_X1 / 2,
        2 * (2 * G.SKEG_TRI_AREA + G.SHOE_AREA))
    return it, area


def blade_items(zd, rho=None):
    """Daggerboards, trunks, tower or bow cap, blade mechanism for the selected variant, at the stowed position.
    Tower variants carry trunk, tower and mechanism at the tower center. Cap variants carry the cap at the cap center
    and the servo and spool in the deck box at the hinge."""
    _K = _k(rho)
    cx, _ = G.blade_centroid(extended=False)
    A = G.blade_area()
    sq_m = A / 1000 / 1000
    per = A * D.SKIN_T * _K + 2 * sq_m * D.GLASS_OUT      # skin plus glass both sides
    b = G.blade_params()
    tx0, tx1 = G.trunk_x()
    h = G.housing(zd)
    it = [('Blades', 'Daggerboards (2): R%.0f %.0f deg sector, %.3f mm, glass both sides' % (b['R'], b['sector_deg'], D.SKIN_T), 2 * per, cx),
          ('Blades', 'Trunks (2), X %.0f to %.0f' % (tx0, tx1), D.TRUNK_MASS, (tx0 + tx1) / 2)]
    if h is None:
        pass                                              # stowed blade stays below the deck underside: no housing
    elif h['kind'] == 'tower':
        it.append(('Blades', 'Tower shell %.0f x %.0f x %.0f' % (D.TOWER_L, D.TOWER_W, D.TOWER_H), D.TOWER_MASS, h['xc']))
    else:
        it.append(('Blades', 'Bow cap (2), X %.0f to %.0f, %.0f to %.0f above the deck' % (h['x0'], h['x1'], h['h0'], h['h1']), D.TOWER_MASS, h['xc']))
    if b['housing'] == 'cap':
        bx = G.blade_box()
        it.append(('Blades', 'Blade servo DS3225, spool, line, deck box X %.0f to %.0f' % (bx.x0, bx.x1), D.BLADE_MECH_MASS, (bx.x0 + bx.x1) / 2))
    else:
        it.append(('Blades', 'Blade servo DS3225, spool, line', D.BLADE_MECH_MASS, G.tower_xc()))
    return it


def published_items(bat_x):
    """Published and calculated masses, read from model/parts.py (one source)."""
    s = D.STEER_SERVO
    esc_x = D.ESC['x0'] + D.ESC['l'] / 2
    rx_x = D.RX['x0'] + D.RX['l'] / 2
    shaft_x = G.SHAFT_CG_X
    it = [('Published', 'Receiver FS-iA6B', P.mass('rx'), rx_x),
          ('Published', 'Steering servo DS3225 (center, on its side)', P.mass('servo_steer'), s['x0'] + s['l'] / 2),
          ('Published', 'Motors ATO 3670 (2)', P.qty('motor') * P.mass('motor'), G.MOT_CG[0])]
    if D.JACKETS:
        it.append(('Published', 'Water jackets (2)', P.qty('jacket') * P.mass('jacket'), G.MOT_CG[0]))
    it += [('Published', 'ESC SeaKing 60A (2)', P.qty('esc') * P.mass('esc'), esc_x),
           ('Published', 'LiPo 3S 5000 (2)', P.qty('battery') * P.mass('battery'), bat_x),
           ('Published', 'Shafts %.0f mm steel (2), %.0f mm each' % (D.SHAFT_D, P.shaft_length()), P.qty('shaft') * P.mass('shaft'), shaft_x)]
    return it


def build_items(zd, bat_x=None, rho=None):
    """Full item list for a deck function, a battery position and a balsa density (default D.BALSA_RHO). Returns (items, hull area mm2)."""
    bat_x = D.DESIGN_BAT_X if bat_x is None else bat_x
    hi, area = hull_items(zd, rho)
    hx = sum(m * x for _, _, m, x in hi) / sum(m for _, _, m, x in hi)
    it = list(hi)
    sq_m = area / 1000 / 1000
    it.append(('Finish', 'Glass and epoxy outside, %.2f m2 at %.0f g/m2' % (sq_m, D.GLASS_OUT), sq_m * D.GLASS_OUT, hx))
    it.append(('Finish', 'Glass and seal coat inside, same area at %.0f g/m2' % D.GLASS_IN, sq_m * D.GLASS_IN, hx))
    it += list(D.STRUCTURE)
    it += blade_items(zd, rho)
    it += published_items(bat_x)
    it += list(D.OTHER_ESTIMATES)
    return it, area


def totals(items):
    W = sum(m for _, _, m, _ in items)
    return W, sum(m * x for _, _, m, x in items) / W


def by_group(items):
    out = {}
    for grp, _, m, _ in items:
        out[grp] = out.get(grp, 0) + m
    return out
