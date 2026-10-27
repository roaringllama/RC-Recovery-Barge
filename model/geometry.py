"""Derived geometry only: functions of design.py. No literals except 0, 1, 2, 1000 (unit conversion) and pi.

Axes: X from the transom forward, Z up from the keel, Y to port from the centerline.
"""
import math
from collections import namedtuple
import numpy as np
import design as D

Box = namedtuple('Box', 'x0 x1 y0 y1 z0 z1')
_THIRD = 1 / (1 + 2)            # centroid factor of a triangle
_SIX = 2 * (1 + 2)              # section modulus divisor of a rectangle, b h^2 / 6
_TWELVE = 2 * 2 * (1 + 2)       # second moment divisor of a rectangle, b h^3 / 12


def _ret(a):
    a = np.asarray(a, dtype=float)
    return a if a.ndim else float(a)


# ---- hull plan ---------------------------------------------------------------------------------
HT = D.TUNNEL_W / 2                                  # tunnel half width
YS = HT + D.SPONSON_W / 2                            # sponson centerline Y
ROOF_Z1 = D.ROOF_Z0 + D.SKIN_T                       # tunnel roof plate top
BOW_RUN = (D.SPONSON_W - D.TIP_W) / math.tan(math.radians(D.BOW_TAPER_DEG))
BOW0 = D.LOA - BOW_RUN                               # where the bow taper starts (BH2)
BH = (D.BH1_X, BOW0)                                 # bulkhead X stations
PLAN_STATIONS = (0, D.AFT_TAPER_X, BOW0, D.LOA)      # where the sponson outline changes direction


def _straight(X):
    """Sponson width with the aft taper only (symmetric about the sponson centerline)."""
    X = np.asarray(X, dtype=float)
    return D.AFT_W + (D.SPONSON_W - D.AFT_W) * np.clip(X / D.AFT_TAPER_X, 0, 1)


def inner_off(X):
    """Inner wall offset from the tunnel face (Y = HT)."""
    return _ret(D.SPONSON_W / 2 - _straight(X) / 2)


def outer_off(X):
    """Outer wall offset from the tunnel face."""
    X = np.asarray(X, dtype=float)
    bow = D.SPONSON_W + (D.TIP_W - D.SPONSON_W) * (X - BOW0) / (D.LOA - BOW0)
    return _ret(np.where(X > BOW0, bow, D.SPONSON_W / 2 + _straight(X) / 2))


def sponson_width(X):
    return _ret(outer_off(X) - inner_off(X))


def inner_wall_y(X):
    return HT + inner_off(X)


def outer_wall_y(X):
    return HT + outer_off(X)


def deck_fn(d0, k):
    """Deck height Z at station X: parallel to the waterline d0 - k X, FREEBOARD above it."""
    return lambda X: d0 - k * X + D.FREEBOARD


# ---- rounds: bilge on both bottom corners of each sponson ---------------------------------------------
def bilge_r(X):
    """Bilge radius at station X on each bottom corner: BILGE_R, or half the sponson width where the section is narrower than two radii."""
    return _ret(np.minimum(D.BILGE_R, np.asarray(sponson_width(X), dtype=float) / 2))


def round_area(R, h):
    """Section area (mm2) a rounded corner of radius R removes from a square corner, up to a water height h above the corner line.
    The corner is fully under water when h >= R, where it is R^2 (1 - pi/4); below that only the part below h counts."""
    R = np.asarray(R, dtype=float)
    h = np.clip(np.asarray(h, dtype=float), 0, R)
    Rs = np.where(R > 0, R, 1)
    u = Rs - h                                           # height of the cut below the arc center line
    F = lambda v: (v * np.sqrt(np.maximum(Rs ** 2 - v ** 2, 0)) + Rs ** 2 * np.arcsin(np.clip(v / Rs, -1, 1))) / 2
    full = Rs ** 2 * math.pi / (2 * 2)
    return _ret(np.where(R > 0, Rs * h - (full - F(u)), 0))


def _hull_z(u, f, Rb):
    """Hull bottom height at distance u from the sponson centerline: flat out to f, then the bilge arc of radius Rb."""
    return 0.0 if u <= f else Rb - math.sqrt(max(Rb ** 2 - (u - f) ** 2, 0))


# ---- drivetrain --------------------------------------------------------------------------------
AXIS = math.radians(D.MOTOR_AXIS_DEG)
TAN = math.tan(AXIS)
BODY_D = D.JACKET_D if D.JACKETS else D.MOTOR_D      # what the motor occupies
BODY_L = D.JACKET_L if D.JACKETS else D.MOTOR_L


def shaft_z(X):
    """Shaft centerline height: level at PROP_Z aft of the CV joint, rising at the motor angle forward of it."""
    return D.PROP_Z + (X - D.CV_X) * TAN


KEEL_X = D.CV_X - D.PROP_Z / TAN                     # shaft crosses the floor (Z 0) here
MOT_AFT_Z = D.SKIN_T + BODY_D / 2 / math.cos(AXIS) + D.MOTOR_FLOOR_CLR   # axis height at the aft face
MOT_X0 = D.CV_X + (MOT_AFT_Z - D.PROP_Z) / TAN       # aft face X on the shaft line
U = (math.cos(AXIS), math.sin(AXIS))                 # motor axis direction
NRM = (-U[1], U[0])                                  # normal, up


def _add(p, v, s):
    return (p[0] + v[0] * s, p[1] + v[1] * s)


F = (MOT_X0, shaft_z(MOT_X0))                        # aft face center
MOT = [_add(F, NRM, BODY_D / 2),
       _add(_add(F, NRM, BODY_D / 2), U, BODY_L),
       _add(_add(F, NRM, -BODY_D / 2), U, BODY_L),
       _add(F, NRM, -BODY_D / 2)]                    # top aft, top fwd, bottom fwd, bottom aft
MOT_TOP = max(p[1] for p in MOT)
MOT_LOW = min(p[1] for p in MOT)
MOT_XMIN = min(p[0] for p in MOT)
MOT_XMAX = max(p[0] for p in MOT)
MOT_X1 = MOT_X0 + BODY_L * U[0]                      # front face center X
MOT_CG = _add(F, U, BODY_L / 2)
_ta, _tf, _bf, _ba = MOT


def _under(x):
    return _ba[1] + TAN * (x - _ba[0])


_xa, _xb = _ba[0] + D.MOUNT_INSET, _bf[0] - D.MOUNT_INSET
MOUNT = [(_xa, D.SKIN_T), (_xb, D.SKIN_T), (_xb, _under(_xb)), (_xa, _under(_xa))]

NOZ_ZTOP = D.PROP_Z + D.NOZ_OD / 2
NOZ_ZBOT = D.PROP_Z - D.NOZ_OD / 2
NOZ_XF = -D.NOZ_X0                                   # forward face
NOZ_XA = -(D.NOZ_X0 + D.NOZ_L)                       # aft face
POSTX = -(D.NOZ_X0 + D.NOZ_L / 2)                    # steering post at the nozzle mid-length

# drive shaft: joint to prop, plus joint to motor aft face along the axis, plus the stub and the prop-end margin
SHAFT_PROP_SEG = (D.CV_X - POSTX) + D.SHAFT_MARGIN                   # CV joint to past the prop plane
SHAFT_MOTOR_SEG = (MOT_X0 - D.CV_X) / math.cos(AXIS) + D.SHAFT_STUB  # CV joint to the motor aft face along the axis, plus the stub
SHAFT_LEN = SHAFT_PROP_SEG + SHAFT_MOTOR_SEG                         # each drive line
SHAFT_CG_X = (SHAFT_MOTOR_SEG * (D.CV_X + SHAFT_MOTOR_SEG / 2 * math.cos(AXIS)) + SHAFT_PROP_SEG * (D.CV_X - SHAFT_PROP_SEG / 2)) / SHAFT_LEN

SHOE_TOP = NOZ_ZBOT - D.SHOE_CLR
SHOE_BOT = SHOE_TOP - D.SHOE_T
SHOE_X1 = -(D.NOZ_X0 + D.NOZ_L + D.SHOE_AFT_OVERHANG)
SKEG_X0 = KEEL_X + D.SKEG_FWD_OF_KEEL
SKEG = [(SKEG_X0, 0), (0, 0), (0, SHOE_BOT)]         # side plate outline, straight bottom edge
SHOE_RE = min(D.SKEG_EDGE_R, D.SHOE_T)               # round on the shoe aft-bottom edge (the shoe is only SHOE_T thick)
SHOE = [(0, SHOE_TOP), (SHOE_X1, SHOE_TOP), (SHOE_X1, SHOE_BOT + SHOE_RE)] + [
    (SHOE_X1 + SHOE_RE - SHOE_RE * math.cos(math.pi / 2 * i / D.BLADE_ARC_PTS), SHOE_BOT + SHOE_RE - SHOE_RE * math.sin(math.pi / 2 * i / D.BLADE_ARC_PTS))
    for i in range(D.BLADE_ARC_PTS + 1)] + [(0, SHOE_BOT)]
SKEG_BOT_DEG = math.degrees(math.atan(-SHOE_BOT / SKEG_X0))
SKEG_TRI_AREA = SKEG_X0 * (-SHOE_BOT) / 2            # one side plate, mm2
SHOE_AREA = (-SHOE_X1) * D.SKEG_W                    # plan area of one shoe, mm2


def skeg_bot(X):
    """Skeg bottom edge Z at station X."""
    if X < 0:
        return SHOE_BOT
    if X > SKEG_X0:
        return 0
    return SHOE_BOT * (1 - X / SKEG_X0)


# nozzle post, bottom pintle
PINTLE_TIP_Z = SHOE_TOP - D.PINTLE_ENGAGE            # pin tip inside the shoe bushing
PINTLE_L = NOZ_ZBOT - PINTLE_TIP_Z                   # pin length below the nozzle bottom
BUSHING_WALL = (D.BUSHING_OD - D.PINTLE_D) / 2       # brass bushing wall around the pin


def post_required_length(zd):
    """Steering post length needed: aft deck underside minus nozzle top, at the post station."""
    return zd(POSTX) - D.AFT_DECK_T - NOZ_ZTOP


# steering linkage (roof-level pushrod to a tie bar between the posts); ZR is the servo output height on its side
ZR = ROOF_Z1 + D.STEER_SERVO['h'] / 2                # servo output, pushrod, tie bar and horns height
ROD_Y = D.STEER_SERVO['w'] / 2 + D.STEER_ROD_OFF     # pushrod lateral position (port), outboard of the servo side face
ROD_X0 = D.STEER_SERVO['x0'] + D.STEER_OUT_X         # servo horn (output shaft) X
ROD_X1 = POSTX                                       # tie bar X
ROD_L = ROD_X0 - ROD_X1                              # between link centers
TIE_Y0 = -YS + D.NOZ_HORN_ARM                        # horns point to port: starboard tip
TIE_Y1 = YS + D.NOZ_HORN_ARM                         # port tip
TIE_L = TIE_Y1 - TIE_Y0                              # tie bar length, equal to the post spacing


def nozzle_corners(deg):
    """Plan corners (X, Y) of the port nozzle rotated by `deg` about its post (the nozzle is a cylinder: NOZ_L along X by NOZ_OD across Y)."""
    a, b = D.NOZ_L / 2, D.NOZ_OD / 2
    c, s_ = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return [(POSTX + c * x - s_ * y, YS + s_ * x + c * y) for x, y in ((a, b), (a, -b), (-a, -b), (-a, b))]


def nozzle_sweep(turn=None, n=D.BLADE_ARC_PTS):
    """Rotation 0 to `turn` degrees in n steps. Returns list of dict(deg, aft, fwd, out): aft-most reach behind the transom (positive),
    forward-most X (positive is ahead of the transom plane), outboard-most Y."""
    turn = D.BUMPER_TURN_DEG if turn is None else turn
    rows = []
    for i in range(n + 1):
        d = turn * i / n
        pts = nozzle_corners(d)
        rows.append(dict(deg=d, aft=-min(p[0] for p in pts), fwd=max(p[0] for p in pts), out=max(p[1] for p in pts)))
    return rows


SKEG_S = D.SKEG_W / 2                                # skeg half width


def skeg_depth(X):
    """Depth of the skeg below the keel line at station X (zero forward of the skeg)."""
    return -skeg_bot(X)


def skeg_fillet(X):
    """Skeg root fillet on one side of one skeg at station X, in (u, z) with u the distance from the sponson centerline and z up from the keel.
    The fillet circle of radius r = min(SKEG_ROOT_R, skeg depth) is tangent to the skeg face (u = SKEG_W/2) and to the hull bottom: the flat keel
    line, or the bilge arc where the flat is too narrow (the skeg is 22 wide in a sponson that is 25 to 55 wide over its length).
    Returns dict(r, zc, pts, area) where pts is the closed section of the fillet material, or None where there is no skeg."""
    d = skeg_depth(X)
    if X < 0 or X >= SKEG_X0 or d <= 0 or D.SKEG_ROOT_R <= 0:
        return None
    r = min(D.SKEG_ROOT_R, d)
    w = float(sponson_width(X))
    Rb = float(bilge_r(X))
    f = w / 2 - Rb                                    # flat half width before the bilge arc
    uc = SKEG_S + r
    if uc <= f:
        zc = -r
        t2 = (uc, 0.0)
    else:
        zc = Rb - math.sqrt((Rb + r) ** 2 - (uc - f) ** 2)
        dx, dz = uc - f, zc - Rb
        n = math.hypot(dx, dz)
        t2 = (f + Rb * dx / n, Rb + Rb * dz / n)
    a2 = math.atan2(t2[1] - zc, t2[0] - uc)
    arc = [(uc + r * math.cos(math.pi + (a2 - math.pi) * i / D.BLADE_ARC_PTS), zc + r * math.sin(math.pi + (a2 - math.pi) * i / D.BLADE_ARC_PTS)) for i in range(D.BLADE_ARC_PTS + 1)]
    back = [(t2[0] + (SKEG_S - t2[0]) * i / D.BLADE_ARC_PTS, _hull_z(t2[0] + (SKEG_S - t2[0]) * i / D.BLADE_ARC_PTS, f, Rb)) for i in range(D.BLADE_ARC_PTS + 1)]
    pts = [(SKEG_S, _hull_z(SKEG_S, f, Rb))] + arc + back
    a = abs(sum(p[0] * q[1] - q[0] * p[1] for p, q in zip(pts, pts[1:] + pts[:1]))) / 2
    return dict(r=r, zc=zc, t2=t2, arc=arc, pts=pts, area=a)


def _fillet_integral():
    """Volume (cm3) of all four skeg root fillets (two skegs, two sides) and its centroid X."""
    n = D.FILLET_STRIPS
    dx = SKEG_X0 / n
    vol, mom = 0.0, 0.0
    for i in range(n):
        X = (i + 1 / 2) * dx
        f_ = skeg_fillet(X)
        if f_:
            vol += f_['area'] * dx
            mom += f_['area'] * dx * X
    vol *= 2 * 2
    mom *= 2 * 2
    return vol / 1000, (mom / vol if vol else 0.0)


# buoyant volume of both skegs and shoes (cm3), and its centroid X
SKEG_VOL_TRI = 2 * SKEG_TRI_AREA * D.SKEG_W / 1000
SKEG_VOL_SHOE = 2 * SHOE_AREA * D.SHOE_T / 1000
SKEG_VOL_BASE = SKEG_VOL_TRI + SKEG_VOL_SHOE
SKEG_BUOY_X_BASE = (SKEG_VOL_TRI * SKEG_X0 * _THIRD + SKEG_VOL_SHOE * SHOE_X1 / 2) / SKEG_VOL_BASE
SKEG_VOL_FILLET, SKEG_FILLET_X = _fillet_integral()  # the root fillets add buoyancy (both sides of both skegs)
SKEG_VOL = SKEG_VOL_BASE + SKEG_VOL_FILLET
SKEG_BUOY_X = (SKEG_VOL_BASE * SKEG_BUOY_X_BASE + SKEG_VOL_FILLET * SKEG_FILLET_X) / SKEG_VOL
SKEG_INTERIOR = D.SKEG_W - 2 * D.SKIN_T              # inside width after two skins
# skeg bottom edge (slope) and shoe outer bottom edges (two sides and the aft end), both skegs: length and the volume the R SKEG_EDGE_R rounds would remove
_SKEG_EDGE_L = 2 * math.hypot(SKEG_X0, -SHOE_BOT) + 2 * (-SHOE_X1) + D.SKEG_W
SKEG_EDGE_VOL = 2 * _SKEG_EDGE_L * D.SKEG_EDGE_R ** 2 * (1 - math.pi / (2 * 2)) / 1000   # reported only, not subtracted in the hydrostatics


def sponson_section(X, D_):
    """Closed outline [(y, z)] of the port sponson section at station X, with the deck at height D_: both bilge rounds, and where the
    skeg is under the section its box with the bottom edge rounds and the root fillets. Mirror y for starboard."""
    yi, yo = float(inner_wall_y(X)), float(outer_wall_y(X))
    w = yo - yi
    yc = (yi + yo) / 2
    Rb = float(bilge_r(X))
    f = w / 2 - Rb
    n = D.BLADE_ARC_PTS
    half = []                                          # right half of the bottom, from the sponson centerline outward: (u, z)
    fl = skeg_fillet(X)
    if fl:
        zb = -skeg_depth(X)
        re = min(D.SKEG_EDGE_R, skeg_depth(X), SKEG_S)
        half.append((0.0, zb))
        half += [(SKEG_S - re + re * math.sin(math.pi / 2 * i / n), zb + re - re * math.cos(math.pi / 2 * i / n)) for i in range(n + 1)]
        half += [(u_, z_) for u_, z_ in fl['arc']]
        t2u = fl['t2'][0]
    else:
        half.append((0.0, 0.0))
        t2u = 0.0
    if t2u < f:
        half.append((f, 0.0))
    half += [(f + Rb * math.sin(math.pi / 2 * i / n), Rb - Rb * math.cos(math.pi / 2 * i / n)) for i in range(n + 1) if f + Rb * math.sin(math.pi / 2 * i / n) > t2u]
    left = [(-u_, z_) for u_, z_ in reversed(half[1:])]
    bottom = left + half
    return [(yi, D_)] + [(yc + u_, z_) for u_, z_ in bottom] + [(yo, D_)]


def hull_section(X, D_, t=0.0):
    """Outline [(y, z)] of the port sponson hull section at station X without the skeg, offset inward by t (t = SKIN_T gives the inside of the skin):
    both bilge corners rounded (radius less t, not below zero), floor at z = t, deck at D_ - t."""
    yi, yo = float(inner_wall_y(X)) + t, float(outer_wall_y(X)) - t
    Rb = max(float(bilge_r(X)) - t, 0.0)
    n = D.BLADE_ARC_PTS
    pts = [(yi, D_ - t)]
    pts += [(yi + Rb - Rb * math.cos(math.pi / 2 * i / n), t + Rb - Rb * math.sin(math.pi / 2 * i / n)) for i in range(n + 1)]
    pts += [(yo - Rb + Rb * math.sin(math.pi / 2 * i / n), t + Rb - Rb * math.cos(math.pi / 2 * i / n)) for i in range(n + 1)]
    pts += [(yo, D_ - t)]
    return pts


# ---- blades ------------------------------------------------------------------------------------
# A blade is a function of (hinge X, hinge Z, radius, sector, direction, swing). `variant` is a key of
# D.BLADE_VARIANTS, a parameter dict, or None for the selected D.BLADE_VARIANT.


def blade_params(variant=None):
    v = D.BLADE_VARIANT if variant is None else variant
    return v if isinstance(v, dict) else D.BLADE_VARIANTS[v]


def _dir(b):
    """+1 when the extended blade points forward along the keel, -1 when it points aft."""
    return 1 if b['dir'] == 'fwd' else -1


def blade_outline(extended=True, variant=None, n=D.BLADE_ARC_PTS):
    """Sector polygon in the XZ plane. Angle t runs from the keel line (forward or aft per `dir`) toward down.
    Extended: t in [0, sector]. Retracted: rotated about the hinge by the sector angle, up for swing 'up'."""
    b = blade_params(variant)
    a = math.radians(b['sector_deg'])
    up = b['swing'] == 'up'
    t0, t1 = (0, a) if extended else ((-a, 0) if up else (a, 2 * a))
    pts = [(b['hinge_x'], b['hinge_z'])]
    for i in range(n + 1):
        t = t0 + (t1 - t0) * i / n
        pts.append((b['hinge_x'] + _dir(b) * b['R'] * math.cos(t), b['hinge_z'] - b['R'] * math.sin(t)))
    return pts


def blade_area(variant=None):
    b = blade_params(variant)
    return b['R'] ** 2 * math.radians(b['sector_deg']) / 2


def blade_centroid(extended=True, variant=None):
    """Area centroid (X, Z) of one blade: 2 R sin(a) / (3 a) from the apex along the bisector, a = half angle."""
    b = blade_params(variant)
    half = math.radians(b['sector_deg']) / 2
    d = 2 * b['R'] * math.sin(half) / (1 + 2) / half
    ang = half if extended else (-half if b['swing'] == 'up' else half + 2 * half)   # bisector angle below the keel line
    return b['hinge_x'] + _dir(b) * d * math.cos(ang), b['hinge_z'] - d * math.sin(ang)


def blade_center_from_bow(variant=None):
    """Distance from the bow tip to the area center of the extended blade, along X."""
    return D.LOA - blade_centroid(True, variant)[0]


def blade_depth(variant=None):
    """Depth of the extended blade tip below the keel."""
    return -min(p[1] for p in blade_outline(True, variant))


def blade_thickness():
    return D.SKIN_T


def blade_xrange(variant=None):
    """X extent of the extended and stowed blade outlines together."""
    xs = [p[0] for e in (True, False) for p in blade_outline(e, variant)]
    return min(xs), max(xs)


def trunk_x(variant=None):
    b = blade_params(variant)
    return b['trunk_x0'], b['trunk_x1']


def trunk_y(variant=None):
    """Outer Y extent (y0, y1) of the trunk on the port side. A tunnel-side trunk uses the sponson inner wall as its inner wall."""
    b = blade_params(variant)
    if b['side'] == 'tunnel':
        y0 = float(inner_wall_y(b['trunk_x0'])) + D.SKIN_T
        return y0, y0 + b['trunk_w'] + D.SKIN_T
    return YS - b['trunk_w'] / 2 - D.SKIN_T, YS + b['trunk_w'] / 2 + D.SKIN_T


def blade_y(variant=None):
    """Y of the blade plane (port side): the sponson centerline, or the middle of a tunnel-side trunk."""
    b = blade_params(variant)
    if b['side'] == 'tunnel':
        return float(inner_wall_y(b['trunk_x0'])) + D.SKIN_T + b['trunk_w'] / 2
    return YS


def stowed_above(zd, variant=None):
    """Part of the stowed blade polygon above the deck underside: list of points (vertices above it plus edge crossings)."""
    pts = blade_outline(False, variant)
    f = lambda p: p[1] - (zd(p[0]) - D.SKIN_T)
    out = []
    for i, p in enumerate(pts):
        q = pts[(i + 1) % len(pts)]
        if f(p) > 0:
            out.append(p)
        if f(p) * f(q) < 0:
            t = f(p) / (f(p) - f(q))
            out.append((p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1])))
    return out


def blade_top_at(X, extended=False, variant=None):
    """Highest Z of the blade outline at station X (the upper edge of the blade seen in profile), or None outside it."""
    pts = blade_outline(extended, variant)
    zs = []
    for i, p in enumerate(pts):
        q = pts[(i + 1) % len(pts)]
        if (p[0] - X) * (q[0] - X) <= 0 and p[0] != q[0]:
            zs.append(p[1] + (q[1] - p[1]) * (X - p[0]) / (q[0] - p[0]))
        elif p[0] == q[0] == X:
            zs += [p[1], q[1]]
    return max(zs) if zs else None


def line_x(variant=None):
    """X of the blade lift line: LINE_R from the hinge along the keel line (forward or aft per `dir`)."""
    b = blade_params(variant)
    return b['hinge_x'] + _dir(b) * D.LINE_R


def line_attach(extended=True, variant=None):
    """Where the lift line meets the blade upper edge, LINE_R from the hinge: (X, Z). Extended the upper edge lies along the keel line;
    stowed it is rotated up with the blade."""
    b = blade_params(variant)
    a = math.radians(b['sector_deg'])
    t = 0 if extended else (-a if b['swing'] == 'up' else a)
    return b['hinge_x'] + _dir(b) * D.LINE_R * math.cos(t), b['hinge_z'] - D.LINE_R * math.sin(t)


def blade_servo_box(zd, variant=None):
    """Blade servo in the bow cap (cap variants), port side, as a Box; None for a tower variant.
    X: the output shaft (the spool) is at the line X and STEER_OUT_X from the servo aft end. Y: outboard of the trunk outer wall, so
    outboard of the blade plane. Z: its base sits above the stowed blade upper edge and the deck top over its footprint (a shelf in the cap)."""
    b = blade_params(variant)
    if b['housing'] != 'cap':
        return None
    sv = D.BLADE_SERVO
    x0 = line_x(variant) - D.STEER_OUT_X
    x1 = x0 + sv['l']
    xs_ = [x0 + (x1 - x0) * i / D.BLADE_ARC_PTS for i in range(D.BLADE_ARC_PTS + 1)]
    z0 = max([zd(x) for x in xs_] + [z for z in (blade_top_at(x, False, variant) for x in xs_) if z is not None])
    y0 = trunk_y(variant)[1]
    return Box(x0, x1, y0, y0 + sv['w'], z0, z0 + sv['h'])


def spool_pos(zd, variant=None):
    """Spool center (X, Z) on the blade servo output shaft, at servo mid-height; Y is the blade plane."""
    sb = blade_servo_box(zd, variant)
    if sb is None:
        return None
    return line_x(variant), (sb.z0 + sb.z1) / 2


def housing(zd, variant=None):
    """What covers the stowed blade above the deck. Returns dict(kind, x0, x1, xc, top(X) -> Z, h0, h1) or None.
    tower: fixed footprint centered over the trunk. cap: X range where the stowed blade is above the deck underside,
    full sponson width, flat top CAP_CLR above the higher of the stowed blade and the blade servo.
    h0, h1: height above the deck top at x0 and x1."""
    b = blade_params(variant)
    if b['housing'] == 'tower':
        x0, x1 = tower_x(variant)
        top = lambda X: zd(X) + D.TOWER_H
        return dict(kind='tower', x0=x0, x1=x1, xc=(x0 + x1) / 2, top=top, h0=D.TOWER_H, h1=D.TOWER_H)
    pts = stowed_above(zd, variant)
    if not pts:
        return None
    x0, x1 = min(p[0] for p in pts), max(p[0] for p in pts)
    z_blade = max(p[1] for p in pts)
    sb = blade_servo_box(zd, variant)
    z_servo = sb.z1 if sb else z_blade
    ztop = max(z_blade, z_servo) + D.CAP_CLR
    return dict(kind='cap', x0=x0, x1=x1, xc=(x0 + x1) / 2, top=lambda X: ztop, ztop=ztop, h0=ztop - zd(x0), h1=ztop - zd(x1),
                z_blade=z_blade, z_servo=z_servo, governs='servo' if z_servo > z_blade else 'stowed blade')


def tip_to_trunk_end(variant=None):
    """Clearance from the blade tip (extended or stowed, whichever reaches further) to the trunk end it points toward."""
    b = blade_params(variant)
    x0, x1 = blade_xrange(variant)
    t0, t1 = trunk_x(variant)
    return (t1 - x1) if _dir(b) > 0 else (x0 - t0)


def stowed_tip_height(zd, variant=None):
    """Highest the stowed blade stands above the deck top (negative: below the deck top)."""
    return max(p[1] - zd(p[0]) for p in blade_outline(False, variant))


def tower_x(variant=None):
    x0, x1 = trunk_x(variant)
    c = (x0 + x1) / 2
    return c - D.TOWER_L / 2, c + D.TOWER_L / 2


def tower_xc(variant=None):
    x0, x1 = trunk_x(variant)
    return (x0 + x1) / 2


# ---- hatches, bulkheads --------------------------------------------------------------------------


def hatch_rects(flange=False):
    """One dict per hatch opening instance: name, x0, x1, y0, y1, zone (flange widens each side by FLANGE)."""
    f = D.FLANGE if flange else 0
    out = []
    for name, h in D.HATCHES.items():
        yo = YS + h.get('yoff', 0)
        ycs = (yo, -yo) if h['zone'] == 'sponson' else (0,)
        for yc in ycs:
            out.append(dict(name=name, zone=h['zone'], yc=yc, x0=h['x0'] - f, x1=h['x1'] + f,
                            y0=yc - h['w'] / 2 - f, y1=yc + h['w'] / 2 + f))
    return out


# ---- electronics boxes ---------------------------------------------------------------------------
def steer_servo_box():
    s = D.STEER_SERVO
    return Box(s['x0'], s['x0'] + s['l'], -s['w'] / 2, s['w'] / 2, ROOF_Z1, ROOF_Z1 + s['h'])


def esc_boxes():
    e = D.ESC
    return [Box(e['x0'], e['x0'] + e['l'], sg * e['y'] - e['w'] / 2, sg * e['y'] + e['w'] / 2, ROOF_Z1, ROOF_Z1 + e['h']) for sg in (1, -1)]


def rx_box():
    r = D.RX
    return Box(r['x0'], r['x0'] + r['l'], -r['w'] / 2, r['w'] / 2, ROOF_Z1, ROOF_Z1 + r['h'])


BAT_YC = YS + D.BAT_Y_OFFSET                         # battery (and rail) center Y on the port side; starboard is the mirror


def battery_boxes(bat_x):
    """Port battery first, starboard second; each is shifted outboard by BAT_Y_OFFSET."""
    b = D.BAT
    z0 = D.SKIN_T + b['rail']
    return [Box(bat_x - b['l'] / 2, bat_x + b['l'] / 2, sg * BAT_YC - b['w'] / 2, sg * BAT_YC + b['w'] / 2, z0, z0 + b['h']) for sg in (1, -1)]


def battery_xrange(bat_x):
    return bat_x - D.BAT['l'] / 2, bat_x + D.BAT['l'] / 2


def hatch_open(name, yc):
    """Opening (no flange) of hatch `name` whose center is nearest to Y = yc."""
    return min((h for h in hatch_rects() if h['name'] == name), key=lambda h: abs(h['yc'] - yc))


def lift_items(bat_xs):
    """Everything that must be lifted out through a hatch: list of dict(name, hatch, x0, x1, y0, y1) plan footprints (port side
    and center items; starboard is the mirror). Batteries are listed once per slide position in bat_xs."""
    out = [dict(name='motor and jacket' if D.JACKETS else 'motor', hatch='HM', x0=MOT_XMIN, x1=MOT_XMAX, y0=YS - BODY_D / 2, y1=YS + BODY_D / 2)]
    for bx in bat_xs:
        b = battery_boxes(bx)[0]
        out.append(dict(name='battery at %.0f' % bx, hatch='HB', x0=b.x0, x1=b.x1, y0=b.y0, y1=b.y1, bat_x=bx))
    for i, b in enumerate(esc_boxes()):
        out.append(dict(name='ESC %s' % ('port' if i == 0 else 'stbd'), hatch='HC', x0=b.x0, x1=b.x1, y0=b.y0, y1=b.y1))
    r = rx_box()
    out.append(dict(name='receiver', hatch='HC', x0=r.x0, x1=r.x1, y0=r.y0, y1=r.y1))
    s_ = steer_servo_box()
    out.append(dict(name='steering servo', hatch='HS', x0=s_.x0, x1=s_.x1, y0=s_.y0, y1=s_.y1))
    return out


# ---- deck plan, push bar, framed aft deck (v9.3) ---------------------------------------------------
# Everything here reads design.DECK_PLAN when it is called (not at import), so one run can compare both plans.
BUMPER_X1 = D.LOA + D.BUMPER_PROJ                    # push bar front face
BUMPER_X0 = BUMPER_X1 - D.BUMPER_T                   # push bar aft face
BUMPER_GAP = BUMPER_X0 - D.LOA                       # between the bow tip and the bar aft face (bridged by the mount arms)
BUMPER_DEPTH = D.FREEBOARD - D.BUMPER_WL_CLR         # bar depth: deck top at the bow less (waterline at the bow + BUMPER_WL_CLR)
BUMPER_ARM_Y = HT + D.TIP_W / 2                      # mount arm centerline Y: the middle of the sponson at the bow tip (port; starboard is the mirror)
AFT_SKIN_LOW_T = D.SKIN_T                            # bottom skin of the aft deck box
AFT_BEAM_GAP = D.AFT_DECK_DEPTH - D.AFT_DECK_T - AFT_SKIN_LOW_T   # room between the two skins for the beams


def deck_plan(plan=None):
    p = D.DECK_PLAN if plan is None else plan
    if p not in D.DECK_PLANS:
        raise ValueError('DECK_PLAN must be one of %s, not %r' % (D.DECK_PLANS, p))
    return p


def bumper_z0(zd):
    """Bar bottom edge Z: the waterline at the bow tip plus BUMPER_WL_CLR (the deck is parallel to the waterline, FREEBOARD above it)."""
    return zd(D.LOA) - D.FREEBOARD + D.BUMPER_WL_CLR


def bumper_z1(zd):
    """Bar top edge Z: flush with the deck top at the bow tip."""
    return zd(D.LOA)


def deck_front_x(plan=None):
    """Forward end of the deck skin: the bar aft face for the rectangle, the bow tip for the tapered deck."""
    return BUMPER_X0 if deck_plan(plan) == 'rect' else D.LOA


def aft_deck_outline(plan=None):
    """Plan polygon [(X, Y)] of the aft deck (X from -AFT_DECK_L to 0), both sides, the aft edge as the closing segment."""
    L, hw = D.AFT_DECK_L, D.AFT_DECK_W / 2
    if deck_plan(plan) == 'rect':
        return [(-L, -hw), (0, -hw), (0, hw), (-L, hw)]
    wc, c = D.BEAM / 2, -L + D.AFT_CHAMFER_L
    return [(-L, -wc), (c, -hw), (0, -hw), (0, hw), (c, hw), (-L, wc)]


def aft_half_y(X, plan=None):
    """Aft deck half width at station X (X from -AFT_DECK_L to 0)."""
    hw = D.AFT_DECK_W / 2
    if deck_plan(plan) == 'rect':
        return hw
    wc, c = D.BEAM / 2, -D.AFT_DECK_L + D.AFT_CHAMFER_L
    return hw if X >= c else wc + (hw - wc) * (X + D.AFT_DECK_L) / D.AFT_CHAMFER_L


def deck_outline(plan=None):
    """Plan polygon [(X, Y)] of the whole deck skin. rect: one rectangle from the aft end to the bar aft face. taper: the aft deck, then the hull
    outline (wall offsets at the stations where the outline changes direction). The last segment is the aft edge."""
    if deck_plan(plan) == 'rect':
        L, hw, F = D.AFT_DECK_L, D.AFT_DECK_W / 2, BUMPER_X0
        return [(-L, -hw), (F, -hw), (F, hw), (-L, hw)]
    ad = aft_deck_outline('taper')
    port = [p for p in ad if p[1] > 0]                              # (0, hw), (c, hw), (-L, wc): forward to aft
    port = list(reversed(port))                                     # aft to forward: (-L, wc), (c, hw), (0, hw)
    port += [(x, float(outer_wall_y(x))) for x in PLAN_STATIONS]
    return port + [(x, -y) for x, y in reversed(port)]


def deck_edges(plan=None):
    """Segments of the deck outline as (p, q, kind): 'aft' for the aft edge, 'step' for the edge where the wider aft deck meets the hull outline at the
    transom, 'chamfer' for the sloped aft deck edges (tapered deck only), 'side' for every other segment."""
    pts = deck_outline(plan)
    n = len(pts)
    kind = lambda i, p, q: ('aft' if i == n - 1 else 'step' if p[0] == 0 and q[0] == 0 else
                            'chamfer' if p[0] != q[0] and p[1] != q[1] and max(p[0], q[0]) <= 0 else 'side')
    return [(pts[i], pts[(i + 1) % n], kind(i, pts[i], pts[(i + 1) % n])) for i in range(n)]


def poly_area(pts):
    return abs(sum(p[0] * q[1] - q[0] * p[1] for p, q in zip(pts, pts[1:] + pts[:1]))) / 2


def aft_deck_area(plan=None):
    return poly_area(aft_deck_outline(plan))


def hull_deck_area():
    """Plan area of the deck over the hull outline (both sponsons and the tunnel), X 0 to LOA: the outline is piecewise straight between the plan stations."""
    w = lambda x: 2 * (HT + float(outer_off(x)))
    return sum((w(a) + w(b)) / 2 * (b - a) for a, b in zip(PLAN_STATIONS, PLAN_STATIONS[1:]))


def overhang_area(plan=None):
    """Plan area of the deck skin outside the hull outline between the transom and the deck front (rect only; zero for the tapered deck)."""
    if deck_plan(plan) != 'rect':
        return 0.0
    return D.AFT_DECK_W * BUMPER_X0 - hull_deck_area()


def deck_brackets(plan=None):
    """Frames extended outboard as deck brackets under the overhang (rect only): one dict per frame and side (port values), with the
    frame X, the hull outer wall Y it starts at, the deck edge Y, and the length between them. Frames whose wall reaches the deck edge are left out."""
    if deck_plan(plan) != 'rect':
        return []
    hw = D.AFT_DECK_W / 2
    out = []
    for x in D.FRAME_X:
        y0 = float(outer_wall_y(x))
        if hw > y0:
            out.append(dict(x=x, y0=y0, y1=hw, L=hw - y0))
    return out


def bumper_plan(plan=None):
    """Plan polygon [(X, Y)] of the push bar. rect: BUMPER_T by AFT_DECK_W. taper: the aft face is the deck width at the bow tip and the two
    ends are chamfered back to the deck at BUMPER_CHAMFER_DEG through the bar thickness."""
    if deck_plan(plan) == 'rect':
        hw = D.AFT_DECK_W / 2
        return [(BUMPER_X0, -hw), (BUMPER_X1, -hw), (BUMPER_X1, hw), (BUMPER_X0, hw)]
    hw = float(outer_wall_y(D.LOA))
    c = D.BUMPER_T / math.tan(math.radians(D.BUMPER_CHAMFER_DEG))
    return [(BUMPER_X0, -hw), (BUMPER_X1, -(hw - c)), (BUMPER_X1, hw - c), (BUMPER_X0, hw)]


def bumper_front_width(plan=None):
    pts = bumper_plan(plan)
    return max(p[1] for p in pts if p[0] == BUMPER_X1) * 2


def bumper_arm_x0(zd):
    """Forward end plate of the bow cap, where the mount arms start (the bow tip when the variant has no cap)."""
    h = housing(zd)
    return h['x1'] if h and h['kind'] == 'cap' else D.LOA


def bumper_arms(zd):
    """Mount arms (one per cap, port values; starboard mirrors): ply strips lying on the deck top from the cap forward plate to the bar aft face."""
    x0 = bumper_arm_x0(zd)
    z0 = zd(x0)
    return dict(x0=x0, x1=BUMPER_X0, y=BUMPER_ARM_Y, w=D.BUMPER_ARM_W, t=D.BUMPER_ARM_T, L=BUMPER_X0 - x0, z0=z0, z1=z0 + D.BUMPER_ARM_T)


def aft_box(plan=None):
    """Aft deck framed box in plan, between the skins. Returns dict of rectangles (x0, x1, y0, y1) and the section numbers:
    long (the two longitudinal beams, port values, from the transom beam to the end beam, at the sponson centerlines), transom (beam at the
    transom, full width), end (beam at the aft edge, width of the outline there). Z: bottom skin below, top skin above, gap between."""
    L, w, hw = D.AFT_DECK_L, D.AFT_BEAM['w'], aft_half_y(0, plan)
    he = aft_half_y(-L + w / 2, plan)
    return dict(
        long=(-L + w, -w, YS - w / 2, YS + w / 2),
        transom=(-w, 0.0, -hw, hw),
        end=(-L, -L + w, -he, he),
        long_len=L - 2 * w, transom_len=2 * hw, end_len=2 * he, w=w, h=D.AFT_BEAM['h'], gap=AFT_BEAM_GAP)


def aft_cantilever():
    """Aft deck as a cantilever from the transom: AFT_LOAD at the aft edge shared by the two longitudinal beams, each a rectangle
    AFT_BEAM w wide and h high (the skins are ignored). Returns dict(P N, per N, L, M N mm, I mm4, Z mm3, sigma MPa, margin, margin_one, defl mm)."""
    P = D.AFT_LOAD / 1000 * D.GRAVITY
    per = P / 2
    L = D.AFT_DECK_L
    b, h = D.AFT_BEAM['w'], D.AFT_BEAM['h']
    M = per * L
    Z = b * h ** 2 / _SIX
    I = b * h * h * h / _TWELVE
    sigma = M / Z
    return dict(P=P, per=per, L=L, M=M, I=I, Z=Z, sigma=sigma, margin=D.BALSA_SIGMA / sigma, margin_one=D.BALSA_SIGMA / (sigma * 2),
                defl=per * L * L * L / ((1 + 2) * D.E_BALSA * I))


def _seg_dist(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L2 = dx * dx + dy * dy
    t = 0 if L2 == 0 else max(0, min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L2))
    return math.hypot(p[0] - (a[0] + t * dx), p[1] - (a[1] + t * dy))


def _inside(p, pts):
    """Even-odd point in polygon."""
    c = False
    for i, a in enumerate(pts):
        b = pts[(i + 1) % len(pts)]
        if (a[1] > p[1]) != (b[1] > p[1]) and p[0] < a[0] + (p[1] - a[1]) / (b[1] - a[1]) * (b[0] - a[0]):
            c = not c
    return c


def nozzle_margins(deg, plan=None):
    """Plan footprint of the port nozzle turned `deg` about its post against the deck outline. Returns dict(m_aft, m_side, m_step, m_chamfer, inside): the smallest
    distance (mm) from the footprint to the aft edge, to the side edges, to the chamfers, and to the step edge where a wider aft deck meets the hull
    (None when the plan has none). A point outside the outline counts as negative, in the class of the edge it is nearest to."""
    n = D.BLADE_ARC_PTS
    cs = nozzle_corners(deg)
    pts = []
    for i, a in enumerate(cs):
        b = cs[(i + 1) % len(cs)]
        pts += [(a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n) for k in range(n)]
    outline, edges = deck_outline(plan), deck_edges(plan)
    kinds = sorted({k for _, _, k in edges})
    best = {k: None for k in kinds}
    inside = True
    for p in pts:
        ins = _inside(p, outline)
        inside = inside and ins
        d = {k: min(_seg_dist(p, a, b) for a, b, kk in edges if kk == k) for k in kinds}
        near = min(d, key=d.get)
        for k in kinds:
            v = d[k] * (1 if ins or k != near else -1)             # only the nearest edge sees the penetration
            best[k] = v if best[k] is None else min(best[k], v)
    return dict(m_aft=best['aft'], m_side=best['side'], m_step=best.get('step'), m_chamfer=best.get('chamfer'), inside=inside)


def nozzle_margin_rows(turn=None, plan=None):
    """nozzle_sweep rows with the margins to the deck outline added."""
    return [dict(row, **nozzle_margins(row['deg'], plan)) for row in nozzle_sweep(turn)]
