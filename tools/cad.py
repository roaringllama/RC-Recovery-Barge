"""CadQuery model of the boat, built from the one model (design.py, model/geometry.py, model/hydro.py), at the design battery position.

Axes: X from the transom forward, Z up from the keel, Y to port (the same as the sheets). Units mm.
Every dimension comes from the model; the few render-only values (propeller blade count, fillet radii) are in the CAD block of design.py.

    python3 -m tools.cad            # writes out/cad/*.step, *.stl, *.glb, manifest.json, render_info.json

Part groups (name prefix before the double underscore of every part): hull, deck, caps, skegs_shoes, nozzles_props, blades, blades_stowed,
bumper, electronics, water.
"""
import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import cadquery as cq
import design as D
from model import geometry as G, hydro

OUT_DIR = os.path.join(ROOT, 'out', 'cad')
SEP = '__'
GROUPS = ('hull', 'deck', 'caps', 'skegs_shoes', 'nozzles_props', 'blades', 'blades_stowed', 'bumper', 'electronics', 'water')

# material tag -> (rgb, alpha); the viewer re-materials by tag, these are the glTF fallbacks
MATERIALS = {
    'balsa_clearcoat': ((0.80, 0.62, 0.38), 1.0),
    'dark_matte': ((0.10, 0.10, 0.11), 1.0),
    'brass': ((0.78, 0.60, 0.22), 1.0),
    'ply': ((0.62, 0.45, 0.26), 1.0),
    'g10_green': ((0.07, 0.25, 0.14), 1.0),
    'battery_grey': ((0.25, 0.26, 0.28), 1.0),
    'esc_blue': ((0.10, 0.30, 0.75), 1.0),
    'servo_black': ((0.06, 0.06, 0.07), 1.0),
    'rx_red': ((0.70, 0.12, 0.10), 1.0),
    'motor_metal': ((0.55, 0.57, 0.60), 1.0),
    'steel': ((0.65, 0.66, 0.68), 1.0),
    'water': ((0.15, 0.45, 0.75), 0.45),
}


class Part:
    def __init__(self, group, name, shape, material):
        self.group, self.name, self.shape, self.material = group, name, shape, material

    @property
    def full(self):
        return self.group + SEP + self.name


# ---- helpers -------------------------------------------------------------------------------------------------------------------------
def _solid(wp):
    return wp.val() if hasattr(wp, 'val') else wp


def _prism(pts, z0, z1):
    return cq.Workplane('XY').workplane(offset=z0).polyline(pts).close().extrude(z1 - z0)


def _wedge(f_lo, f_hi, x0, x1, half_y):
    """Volume between two surfaces Z = f_lo(X) and Z = f_hi(X) for X in [x0, x1], across Y in [-half_y, half_y]."""
    pts = [(x0, f_lo(x0)), (x1, f_lo(x1)), (x1, f_hi(x1)), (x0, f_hi(x0))]
    return cq.Workplane('XZ').polyline(pts).close().extrude(half_y, both=True)


def _box(b, name=None):
    """cq solid from a model Box(x0 x1 y0 y1 z0 z1)."""
    return cq.Workplane('XY').box(b.x1 - b.x0, b.y1 - b.y0, b.z1 - b.z0, centered=False).translate((b.x0, b.y0, b.z0))


def _cyl(radius, length, p, d):
    return cq.Workplane('XY').add(cq.Solid.makeCylinder(radius, length, cq.Vector(*p), cq.Vector(*d)))


def _dedupe(pts):
    out = []
    for p in pts:
        if not out or math.hypot(p[0] - out[-1][0], p[1] - out[-1][1]) > D.CAD_EPS:
            out.append(p)
    if math.hypot(out[0][0] - out[-1][0], out[0][1] - out[-1][1]) <= D.CAD_EPS:
        out.pop()
    return out


def _mirror(wp):
    return wp.mirror('XZ')


# ---- hull ----------------------------------------------------------------------------------------------------------------------------
def plan_pts():
    """Port sponson plan outline [(X, Y)] from the wall offsets at the stations where the outline changes direction."""
    st = G.PLAN_STATIONS
    inner = [(X, float(G.inner_wall_y(X))) for X in st]
    outer = [(X, float(G.outer_wall_y(X))) for X in reversed(st)]
    return inner + outer


def _section_wire(X, ztop, t=0.0):
    """Closed section wire of the port sponson at station X: deck at ztop, both bilge rounds, offset inward by t."""
    yi, yo = float(G.inner_wall_y(X)) + t, float(G.outer_wall_y(X)) - t
    half = (yo - yi) / 2
    flat = max(half - max(float(G.bilge_r(X)) - t, 0.0), D.CAD_EPS)
    Rb = half - flat
    c = Rb * math.cos(math.pi / 2 / 2)                  # arc midpoint offset (45 deg)
    wp = (cq.Workplane('YZ', origin=(X, 0, 0)).moveTo(yi, ztop).lineTo(yi, t + Rb)
          .threePointArc((yi + Rb - c, t + Rb - c), (yi + Rb, t))
          .lineTo(yo - Rb, t)
          .threePointArc((yo - Rb + c, t + Rb - c), (yo, t + Rb))
          .lineTo(yo, ztop).close())
    return wp.val() if isinstance(wp.val(), cq.Wire) else wp.wires().val()


def _stations(x0, x1):
    """Loft stations: ends, the plan break points, and where a bilge round stops fitting (section width = 2 R)."""
    xs = {x0, x1}
    xs.update(X for X in G.PLAN_STATIONS if x0 < X < x1)
    rr = 2 * D.BILGE_R
    if D.AFT_W < rr < D.SPONSON_W:
        xs.add((rr - D.AFT_W) / (D.SPONSON_W - D.AFT_W) * D.AFT_TAPER_X)
        xs.add(G.BOW0 + (D.SPONSON_W - rr) / (D.SPONSON_W - D.TIP_W) * (D.LOA - G.BOW0))
    return sorted(x for x in xs if x0 <= x <= x1)


def _loft(x0, x1, ztop_fn, t=0.0):
    wires = [_section_wire(X, ztop_fn(X), t) for X in _stations(x0, x1)]
    return cq.Workplane('XY').add(cq.Solid.makeLoft(wires, True))


def sponson_outer(zd):
    """Port sponson outer solid: keel Z 0 to the deck, bilge rounds on both bottom corners (lofted through the sections)."""
    s = _loft(0.0, D.LOA, zd)
    try:                                                 # round the vertical edges of the bow tip face
        s = s.edges(cq.selectors.BoxSelector((D.LOA - 1, -1000, G.ROOF_Z1), (D.LOA + 1, 1000, 1000))).edges('|Z').fillet(D.CAD_TIP_R)
    except Exception as e:                               # fillet did not close on the lofted tip: keep the sharp tip and say so
        print('NOTE bow tip edge fillet skipped (%s)' % str(e)[:60])
    return s


def sponson_cavity(zd):
    """Inside of the hull skin (offset SKIN_T), open at the top."""
    return _loft(D.SKIN_T, D.LOA - D.SKIN_T, lambda X: zd(X) + D.SKIN_T, D.SKIN_T)


def hull_solid(zd):
    """Both sponsons as solids (the keel Z 0 to the deck). This is the volume the model's sponson estimate is compared with."""
    p = sponson_outer(zd)
    return p.union(_mirror(p))


def tunnel_pts():
    """Plan outline of the tunnel between the inner walls."""
    st = G.PLAN_STATIONS
    left = [(X, float(G.inner_wall_y(X))) for X in st]
    right = [(X, -float(G.inner_wall_y(X))) for X in reversed(st)]
    return left + right


def skeg_parts(zd):
    """Skeg side plate, shoe and the lofted root fillets for the port skeg; returns a solid."""
    up = D.BILGE_R                                       # the plate runs up this far into the hull so it meets the curved bottom at its sides
    plate_pts = [(G.SKEG_X0, up), (G.SKEG_X0, 0), (0, G.SHOE_BOT), (0, up)]
    plate = cq.Workplane('XZ').polyline(plate_pts).close().extrude(G.SKEG_S, both=True)
    try:
        plate = plate.edges(cq.selectors.BoxSelector((0, -1000, G.SHOE_BOT - 1), (G.SKEG_X0, 1000, 1))).edges('not(|Y)').fillet(D.SKEG_EDGE_R)
    except Exception as e:
        print('NOTE skeg bottom edge round skipped (%s)' % str(e)[:60])
    shoe = cq.Workplane('XZ').polyline(_dedupe(G.SHOE)).close().extrude(G.SKEG_S, both=True)
    try:
        shoe = shoe.faces('<Z').edges().fillet(D.SKEG_EDGE_R / 2)
    except Exception:
        pass
    body = plate.union(shoe)
    # root fillets from the model's fillet section, lofted along X
    x_full = G.SKEG_X0 * (1 - D.SKEG_ROOT_R / (-G.SHOE_BOT))      # skeg depth equals the root radius here
    n = D.CAD_SKEG_FILLET_STATIONS
    xs = [x_full * i / (n - 1) for i in range(n)] + [x_full + (G.SKEG_X0 - x_full) / 2]
    for sgn in (1, -1):
        wires = []
        for X in xs:
            fl = G.skeg_fillet(X)
            if not fl:
                continue
            pts = fl['pts'][:-1]
            pts = pts[::D.CAD_FILLET_SUBSAMPLE]
            wp = cq.Workplane('YZ', origin=(X, 0, 0)).polyline([(sgn * u, z) for u, z in pts]).close()
            wires.append(wp.val() if isinstance(wp.val(), cq.Wire) else wp.wires().val())
        try:
            body = body.union(cq.Workplane('XY').add(cq.Solid.makeLoft(wires, True)))
        except Exception as e:
            print('NOTE skeg root fillet loft skipped (%s)' % str(e)[:60])
    return body


# ---- the parts -----------------------------------------------------------------------------------------------------------------------
def build(r=None):
    """All parts of the boat at the design battery position. Returns (list of Part, info dict)."""
    r = r or hydro.design()
    zd = r['deck']
    T = D.SKIN_T
    parts = []
    add = lambda g, n, s, m: parts.append(Part(g, n, s if isinstance(s, cq.Workplane) else cq.Workplane('XY').add(s), m))
    BIG = max(zd(0), zd(D.LOA)) + D.TOWER_H + D.BEAM
    HALF = D.BEAM

    # sponsons: shell, deck skin
    outer = sponson_outer(zd)
    cav = sponson_cavity(zd)
    deck_wedge = _wedge(lambda X: zd(X) - T, lambda X: zd(X) + BIG, 0.0, D.LOA, HALF)
    shell = outer.cut(cav)
    if D.CAD_TRUNK_SLOT_FLOOR:
        y0, y1 = G.trunk_y()
        tx0, tx1 = G.trunk_x()
        yin = float(G.inner_wall_y(tx0)) + T
        slot = cq.Workplane('XY').box(tx1 - tx0, y1 - y0 - 2 * T, 2 * T, centered=False).translate((tx0, yin, -T / 2))
        shell = shell.cut(slot)
    deck_skin = outer.intersect(deck_wedge)
    shell = shell.cut(deck_wedge)
    for sg, side in ((1, 'port'), (-1, 'stbd')):
        add('hull', 'sponson_' + side, shell if sg > 0 else _mirror(shell), 'balsa_clearcoat')
        add('deck', 'sponson_deck_' + side, deck_skin if sg > 0 else _mirror(deck_skin), 'balsa_clearcoat')

    tp = tunnel_pts()
    roof = _prism(tp, D.ROOF_Z0, G.ROOF_Z1)
    add('hull', 'tunnel_roof', roof, 'balsa_clearcoat')
    cdeck = _prism(tp, 0.0, BIG).intersect(_wedge(lambda X: zd(X) - T, lambda X: zd(X), 0.0, D.LOA, HALF))
    add('deck', 'center_deck', cdeck, 'balsa_clearcoat')
    # deck plan: aft deck as a closed box (top skin, bottom skin, two long beams, transom beam, end beam), then for the rectangular plan the overhang skin and the brackets
    slab = lambda pts, f_lo, f_hi, x0, x1: _prism(pts, 0.0, BIG).intersect(_wedge(f_lo, f_hi, x0, x1, HALF))
    L = D.AFT_DECK_L
    adp = G.aft_deck_outline()
    f_top = lambda X: zd(X) - D.AFT_DECK_T
    f_bot = lambda X: zd(X) - D.AFT_DECK_DEPTH
    add('deck', 'aft_deck_top', slab(adp, f_top, zd, -L, 0.0), 'balsa_clearcoat')
    add('deck', 'aft_deck_bottom', slab(adp, f_bot, lambda X: zd(X) - D.AFT_DECK_DEPTH + G.AFT_SKIN_LOW_T, -L, 0.0), 'balsa_clearcoat')
    ab = G.aft_box()
    g_lo, g_hi = (lambda X: zd(X) - D.AFT_DECK_DEPTH + G.AFT_SKIN_LOW_T), f_top
    rect = lambda x0, x1, y0, y1: [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    inside = _prism(adp, 0.0, BIG)
    lb = slab(rect(*ab['long'][:2], *ab['long'][2:]), g_lo, g_hi, ab['long'][0], ab['long'][1])
    add('deck', 'aft_beam_port', lb, 'balsa_clearcoat')
    add('deck', 'aft_beam_stbd', _mirror(lb), 'balsa_clearcoat')
    for nm, key in (('aft_beam_transom', 'transom'), ('aft_beam_end', 'end')):
        x0, x1, y0, y1 = ab[key]
        add('deck', nm, slab(rect(x0, x1, y0, y1), g_lo, g_hi, x0, x1).intersect(inside), 'balsa_clearcoat')
    if G.deck_plan() == 'rect':
        hw, F = D.AFT_DECK_W / 2, G.BUMPER_X0
        ov = slab(rect(0.0, F, -hw, hw), f_top, zd, 0.0, F).cut(deck_skin).cut(_mirror(deck_skin)).cut(cdeck)
        add('deck', 'deck_overhang', ov, 'balsa_clearcoat')
        for i, b in enumerate(G.deck_brackets(), 1):
            t2 = D.FRAME_T / 2
            br = slab(rect(b['x'] - t2, b['x'] + t2, b['y0'], b['y1']), lambda X: zd(X) - D.AFT_DECK_T - D.FRAME_RIB, f_top, b['x'] - t2, b['x'] + t2)
            add('deck', 'bracket_x%03d_port' % b['x'], br, 'balsa_clearcoat')
            add('deck', 'bracket_x%03d_stbd' % b['x'], _mirror(br), 'balsa_clearcoat')

    # push bar on the bow caps: balsa core and ply face, two ply mount arms on the deck top
    bz0, bz1 = G.bumper_z0(zd), G.bumper_z1(zd)
    bar = _prism(G.bumper_plan(), bz0, bz1)
    face = bar.intersect(cq.Workplane('XY').box(D.BUMPER_FACE_T, 4 * D.BEAM, bz1 - bz0, centered=False).translate((G.BUMPER_X1 - D.BUMPER_FACE_T, -2 * D.BEAM, bz0)))
    add('bumper', 'bar_core', bar.cut(face), 'balsa_clearcoat')
    add('bumper', 'bar_face', face, 'ply')
    am = G.bumper_arms(zd)
    arm = cq.Workplane('XY').box(am['L'], am['w'], am['t'], centered=False).translate((am['x0'], am['y'] - am['w'] / 2, am['z0']))
    add('bumper', 'arm_port', arm, 'ply')
    add('bumper', 'arm_stbd', _mirror(arm), 'ply')

    # bow caps
    hz = G.housing(zd)
    info = dict(cap=None)
    if hz and hz['kind'] == 'cap':
        zlo = min(zd(hz['x0']), zd(hz['x1']))             # the cap sits on the deck, so start at the lowest deck height in its X range
        cap_box = cq.Workplane('XY').box(hz['x1'] - hz['x0'], D.BEAM, hz['ztop'] - zlo, centered=False).translate((hz['x0'], -D.BEAM / 2, zlo))
        cap = _prism(plan_pts(), zlo, hz['ztop']).intersect(cap_box).cut(outer)
        try:
            cap = cap.edges().fillet(D.CAD_CAP_R)
        except Exception:
            try:
                cap = cap.edges('not(|Z)').fillet(D.CAD_CAP_R)
            except Exception as e:
                print('NOTE cap fillet skipped (%s)' % str(e)[:60])
        add('caps', 'cap_port', cap, 'balsa_clearcoat')
        add('caps', 'cap_stbd', _mirror(cap), 'balsa_clearcoat')
        info['cap'] = (hz['x0'], hz['x1'], hz['ztop'])

    # skegs and shoes
    sk = skeg_parts(zd)
    for sg, side in ((1, 'port'), (-1, 'stbd')):
        s = sk.translate((0, G.YS, 0))
        add('skegs_shoes', 'skeg_' + side, s if sg > 0 else _mirror(s), 'balsa_clearcoat')

    # nozzles, props, posts
    ax = (1, 0, 0)
    bore = D.NOZ_OD - D.NOZ_BORE_LESS
    for sg, side in ((1, 'port'), (-1, 'stbd')):
        yc = sg * G.YS
        ring = _cyl(D.NOZ_OD / 2, D.NOZ_L, (G.NOZ_XA, yc, D.PROP_Z), ax).cut(_cyl(bore / 2, D.NOZ_L, (G.NOZ_XA, yc, D.PROP_Z), ax))
        add('nozzles_props', 'nozzle_' + side, ring, 'dark_matte')
        post = _cyl(D.NOZ_POST_D / 2, zd(G.POSTX) - D.AFT_DECK_T - G.NOZ_ZTOP, (G.POSTX, yc, G.NOZ_ZTOP), (0, 0, 1))
        add('nozzles_props', 'post_' + side, post, 'steel')
        hub = _cyl(D.CAD_PROP_HUB_D / 2, D.CAD_PROP_CHORD, (G.POSTX - D.CAD_PROP_CHORD / 2, yc, D.PROP_Z), ax)
        rad = D.PROP_D / 2 - D.CAD_PROP_HUB_D / 2
        for i in range(D.CAD_PROP_BLADES):
            bl = (cq.Workplane('XY').box(D.CAD_PROP_CHORD, rad, D.CAD_PROP_BLADE_T, centered=(True, False, True))
                  .rotate((0, 0, 0), (0, 1, 0), D.CAD_PROP_PITCH_DEG)
                  .translate((0, D.CAD_PROP_HUB_D / 2, 0))
                  .rotate((0, 0, 0), (1, 0, 0), 360.0 / D.CAD_PROP_BLADES * i)
                  .translate((G.POSTX, yc, D.PROP_Z)))
            hub = hub.union(bl)
        add('nozzles_props', 'prop_' + side, hub, 'brass')
        # drive line: shaft from the prop plane to the CV joint, then up the motor axis
        add('electronics', 'shaft_aft_' + side, _cyl(D.SHAFT_D / 2, G.SHAFT_PROP_SEG, (D.CV_X, yc, D.PROP_Z), (-1, 0, 0)), 'steel')
        a = G.AXIS
        add('electronics', 'shaft_fwd_' + side, _cyl(D.SHAFT_D / 2, G.SHAFT_MOTOR_SEG, (D.CV_X, yc, D.PROP_Z), (math.cos(a), 0, math.sin(a))), 'steel')
        # motor and water jacket
        mp = (G.F[0], yc, G.F[1])
        mdir = (math.cos(a), 0, math.sin(a))
        add('electronics', 'motor_' + side, _cyl(D.MOTOR_D / 2, D.MOTOR_L, mp, mdir), 'motor_metal')
        if D.JACKETS:
            add('electronics', 'jacket_' + side, _cyl(D.JACKET_D / 2, D.JACKET_L, mp, mdir), 'esc_blue')

    # blades, extended and stowed, in the blade plane (port and starboard)
    bm = D.BLADE_MATERIALS[D.BLADE_MATERIAL]
    for ext, grp in ((True, 'blades'), (False, 'blades_stowed')):
        pts = G.blade_outline(ext)
        for sg, side in ((1, 'port'), (-1, 'stbd')):
            yb = sg * G.blade_y()
            b = cq.Workplane('XZ').polyline(pts).close().extrude(bm['t'] / 2, both=True).translate((0, yb, 0))
            add(grp, 'blade_' + side, b, 'g10_green')

    # electronics
    add('electronics', 'steer_servo', _box(G.steer_servo_box()), 'servo_black')
    for i, e in enumerate(G.esc_boxes()):
        add('electronics', 'esc_%d' % (i + 1), _box(e), 'esc_blue')
    add('electronics', 'receiver', _box(G.rx_box()), 'rx_red')
    for i, bb in enumerate(G.battery_boxes(r['bat_x'])):
        add('electronics', 'battery_' + ('port' if i == 0 else 'stbd'), _box(bb), 'battery_grey')
    sb = G.blade_servo_box(zd)
    if sb is not None:
        add('electronics', 'blade_servo', _box(sb), 'servo_black')

    # water plane at the waterline Z = d0 - k X, render only
    wl = lambda X: r['d0'] - r['k'] * X
    span = D.CAD_WATER_SPAN
    wx0, wx1 = -D.LOA * (span - 1), D.LOA * span
    water = _wedge(lambda X: wl(X) - D.CAD_WATER_T, wl, wx0, wx1, D.BEAM * span)
    add('water', 'water', water, 'water')
    return parts, dict(r=r, zd=zd, cap=info['cap'])


# ---- export --------------------------------------------------------------------------------------------------------------------------
def _compound(shapes):
    return cq.Compound.makeCompound([s for s in shapes])


def _vals(wp):
    return [o for o in wp.vals() if isinstance(o, (cq.Solid, cq.Compound, cq.Shape))]


def _shape(wp):
    v = _vals(wp)
    return v[0] if len(v) == 1 else _compound(v)


def assembly(parts):
    a = cq.Assembly(name='RC_Recovery_Barge_%s' % D.REV)
    for p in parts:
        rgb, alpha = MATERIALS[p.material]
        a.add(_shape(p.shape), name=p.full, color=cq.Color(rgb[0], rgb[1], rgb[2], alpha))
    return a


def hull_volume_check(zd):
    """(built hull solid volume cm3, model estimate cm3): plan area times mean deck height for each sponson."""
    hs = hull_solid(zd)
    vol = _shape(hs).Volume() / 1000
    n = D.HYDRO_STRIPS
    dx = D.LOA / n
    Xs = [(i + 1 / 2) * dx for i in range(n)]
    est = 2 * sum(float(G.sponson_width(X)) * zd(X) * dx for X in Xs) / 1000
    return vol, est


def export_all(out_dir=OUT_DIR, log=print):
    os.makedirs(out_dir, exist_ok=True)
    r = hydro.design()
    parts, info = build(r)
    rev = D.REV
    files = {}
    asm = assembly(parts)
    step = os.path.join(out_dir, 'RC_Recovery_Barge_%s.step' % rev)
    asm.save(step, 'STEP')
    files['step'] = step
    glb = os.path.join(out_dir, 'RC_Recovery_Barge_%s.glb' % rev)
    asm.save(glb, 'GLTF', tolerance=D.CAD_STL_TOL * 2, angularTolerance=D.CAD_STL_ANG)
    files['glb'] = glb

    manifest = dict(rev=rev, units='mm for the bounding boxes, cm3 for the volumes', groups={})
    for g in GROUPS:
        ps = [p for p in parts if p.group == g]
        if not ps:
            continue
        comp = _compound([_shape(p.shape) for p in ps])
        stl = os.path.join(out_dir, '%s_%s.stl' % (g, rev))
        cq.exporters.export(cq.Workplane('XY').add(comp), stl, tolerance=D.CAD_STL_TOL, angularTolerance=D.CAD_STL_ANG)
        files['stl_' + g] = stl
        bb = comp.BoundingBox()
        manifest['groups'][g] = dict(
            parts=[p.full for p in ps], materials=sorted({p.material for p in ps}),
            volume_cm3=round(sum(_shape(p.shape).Volume() for p in ps) / 1000, 3),
            bbox_mm=dict(x=[round(bb.xmin, 2), round(bb.xmax, 2)], y=[round(bb.ymin, 2), round(bb.ymax, 2)], z=[round(bb.zmin, 2), round(bb.zmax, 2)]),
            stl=os.path.basename(stl))
    manifest['part_materials'] = {p.full: p.material for p in parts}
    mp = os.path.join(out_dir, 'manifest.json')
    with open(mp, 'w') as f:
        json.dump(manifest, f, indent=2)
    files['manifest'] = mp

    info_json = dict(rev=rev, weight_g=round(r['W'], 1), lcg_mm=round(r['G'], 1), stern_draft_mm=round(r['d0'], 1), bow_draft_mm=round(r['bow'], 1),
                     trim_deg=round(r['trim'], 2), over_nozzle_mm=round(r['over'], 1), nozzle_margin_mm=round(r['over'] - D.TROUGH, 1),
                     trough_mm=D.TROUGH, battery_x_mm=D.DESIGN_BAT_X, blade=D.BLADE_VARIANT, glb=os.path.basename(glb))
    ip = os.path.join(out_dir, 'render_info.json')
    with open(ip, 'w') as f:
        json.dump(info_json, f, indent=2)
    files['render_info'] = ip
    log('CAD wrote %d files to %s' % (len(files), out_dir))
    return files, manifest


if __name__ == '__main__':
    export_all()
