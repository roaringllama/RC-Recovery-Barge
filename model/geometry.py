"""Derived geometry only: functions of design.py. No literals except 0, 1, 2, 1000 (unit conversion) and pi.

Axes: X from the transom forward, Z up from the keel, Y to port from the centerline.
"""
import math
from collections import namedtuple
import numpy as np
import design as D

Box = namedtuple('Box', 'x0 x1 y0 y1 z0 z1')
_THIRD = 1 / (1 + 2)            # centroid factor of a triangle


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
SHOE = [(0, SHOE_TOP), (SHOE_X1, SHOE_TOP), (SHOE_X1, SHOE_BOT), (0, SHOE_BOT)]
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


# buoyant volume of both skegs and shoes (cm3), and its centroid X
SKEG_VOL_TRI = 2 * SKEG_TRI_AREA * D.SKEG_W / 1000
SKEG_VOL_SHOE = 2 * SHOE_AREA * D.SHOE_T / 1000
SKEG_VOL = SKEG_VOL_TRI + SKEG_VOL_SHOE
SKEG_BUOY_X = (SKEG_VOL_TRI * SKEG_X0 * _THIRD + SKEG_VOL_SHOE * SHOE_X1 / 2) / SKEG_VOL
SKEG_INTERIOR = D.SKEG_W - 2 * D.SKIN_T              # inside width after two skins

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


def housing(zd, variant=None):
    """What covers the stowed blade above the deck. Returns dict(kind, x0, x1, xc, top(X) -> Z, h0, h1) or None.
    tower: fixed footprint centered over the trunk. cap: X range where the stowed blade is above the deck underside,
    full sponson width, flat top CAP_CLR above the stowed blade. h0, h1: height above the deck top at x0 and x1."""
    b = blade_params(variant)
    if b['housing'] == 'tower':
        x0, x1 = tower_x(variant)
        top = lambda X: zd(X) + D.TOWER_H
        return dict(kind='tower', x0=x0, x1=x1, xc=(x0 + x1) / 2, top=top, h0=D.TOWER_H, h1=D.TOWER_H)
    pts = stowed_above(zd, variant)
    if not pts:
        return None
    x0, x1 = min(p[0] for p in pts), max(p[0] for p in pts)
    ztop = max(p[1] for p in pts) + D.CAP_CLR
    return dict(kind='cap', x0=x0, x1=x1, xc=(x0 + x1) / 2, top=lambda X: ztop, ztop=ztop, h0=ztop - zd(x0), h1=ztop - zd(x1))


def stowed_tip_height(zd, variant=None):
    """Highest the stowed blade stands above the deck top (negative: below the deck top)."""
    return max(p[1] - zd(p[0]) for p in blade_outline(False, variant))


def blade_box(variant=None):
    """Blade servo and spool box on the deck at the hinge (cap variants): Box with Z from 0 (set on the deck by the caller)."""
    b = blade_params(variant)
    bb = D.BLADE_BOX
    return Box(b['hinge_x'], b['hinge_x'] + bb['l'], -bb['w'] / 2, bb['w'] / 2, 0, bb['h'])


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
