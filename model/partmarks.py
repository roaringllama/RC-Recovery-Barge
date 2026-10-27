"""Part mark scheme: one mark for every physical part, from the one model. No literals except 0, 1, 2, 1000 (a test enforces this).

`build()` returns a Table: cut `parts` (what is sawn from stock, planks and blocking pieces included), `templates` (the marks that get a full size
template), `assemblies` (groups of marks), `bought` (purchased items that carry a mark), and the CAD name map. The cut list, nesting, templates, DXF and SVG
all read this table; tools/cad.py and the A-103 and A-502 schedules take their marks from it.

Mark rules: a mark ending -P or -S is a port or starboard piece (a mirror pair); a mark without a side is identical on both sides or single (qty says how many).
A plank of a panel is the panel mark, a dot and the plank number (O1.2). Blocking is J<joint>-<where>. Frames are F<n>-P and F<n>-S (sponson pieces) and F<n>-T (the
tunnel piece above the roof plate). The solid frames at the bulkhead stations are the bulkheads: BH1 is the assembly F5-P + F5-S, BH2 is F8-P + F8-S.
"""
import math
from collections import OrderedDict
import design as D
from . import geometry as G, hydro, schedules as S, partshapes as SH

RIGHT = SH.RIGHT
BOTH = S.BOTH

from .marknames import PANEL_MARK, PANEL_DISPLAY, a103_mark, frame_marks, bracket_mark, rib_mark, beam_mark  # noqa: E402,F401


# ---- stock -----------------------------------------------------------------------------------------------------------------------------------------------
class Stock:
    def __init__(self, key, label, kind, L, W, t, inch_label, rotate=False, lanes=1, order=None, note='', section=None):
        self.key, self.label, self.kind, self.L, self.W, self.t = key, label, kind, L, W, t
        self.inch_label, self.rotate, self.lanes, self.order, self.note, self.section = inch_label, rotate, lanes, order, note, section


def stocks():
    """Stock items by key. L is the long side (the grain direction of balsa sheet and the stick length), W the width (None for sticks)."""
    bm = D.BLADE_MATERIALS[D.BLADE_MATERIAL]
    ply = tuple(v * D.INCH for v in D.PLY_SHEET_IN)
    g10 = tuple(v * D.INCH for v in D.G10_SHEET_IN)
    out = OrderedDict()
    add = lambda *a, **k: out.__setitem__(a[0], Stock(*a, **k))
    add('balsa', '1/8 x 3 x 36 in balsa sheet', 'sheet', D.STICK_L, D.STOCK_W, D.SKIN_T, '1/8 x 3 x 36 in', order='balsa',
        note='grain runs along the 36 in length; planks, frames, lids, plugs, mounts, rails and backing strips are cut from it')
    add('tri', '3/8 x 3/8 x 36 in balsa stick, ripped to two triangular lengths', 'stick', D.STICK_L, None, D.BLOCK_LEG, '3/8 x 3/8 x 36 in', lanes=2, order='stock',
        section=D.BLOCK_LEG, note='each stick rips on the diagonal into two triangular lengths (two lanes); a corner wedge takes a whole stick length')
    add('chine', '3/4 x 3/4 x 36 in balsa stick', 'stick', D.STICK_L, None, D.CHINE_LEG, '3/4 x 3/4 x 36 in', order='chine', section=D.CHINE_LEG, note='chine stringers')
    add('strip', '3/4 x 1/4 x 36 in balsa strip', 'stick', D.STICK_L, None, D.DECK_BEAM_T, '3/4 x 1/4 x 36 in', order=None, section=D.DECK_BEAM_W,
        note='deck beams and aft deck beams (%.2f x %.2f); NOT on the order list' % (D.DECK_BEAM_W, D.DECK_BEAM_T))
    add('ply', '1/8 x 12 x 12 in birch ply', 'sheet', max(ply), min(ply), D.SKIN_T, '1/8 x 12 x 12 in', rotate=True, order='ply', note='pads, rims, clamp caps, servo pads, bar arms')
    add('ply15', '1.5 mm ply or hardwood (push bar face)', 'sheet', max(ply), min(ply), D.BUMPER_FACE_T, '1.5 mm', rotate=True, order=None,
        note='NOT on the order list; sheet size is not defined in the model, a %.0f x %.0f mm piece is assumed' % (max(ply), min(ply)))
    add('g10', '1.5 mm G10 sheet, 12 x 24 in', 'sheet', max(g10), min(g10), bm['t'], '0.060 x 12 x 24 in', rotate=True, order='g10', note='daggerboard blades')
    add('rod3', '3 mm brass rod, 300 mm', 'stick', D.NOZ_POST_STOCK_L, None, D.NOZ_POST_D, '3 mm x 300 mm (pack of %d)' % D.ROD_PACK, order='post_rod',
        section=D.NOZ_POST_D, note='nozzle posts and pintle pins')
    add('tube4', '4 mm OD brass tube, 300 mm', 'stick', D.NOZ_POST_STOCK_L, None, D.NOZ_POST_D, '4 mm x 0.45 x 300 mm (pack of %d)' % D.ROD_PACK, order='post_tube',
        section=D.NOZ_POST_D, note='nozzle post sleeves')
    add('bar4', '4 x 4 brass bar', 'stick', None, None, D.TIE_BAR, '4 x 4 mm', order=None, section=D.TIE_BAR, note='tie bar; NOT on the order list; stock length is not defined in the model')
    add('cord', '1.5 mm silicone O-ring cord, 3 ft', 'stick', D.CORD_STOCK_IN * D.INCH, None, D.CORD_D, '1.5 mm x 3 ft', order='cord', section=D.CORD_D, note='hatch cord loops')
    add('rod256', '2-56 threaded rod, 12 in', 'stick', D.ROD256_STOCK_IN * D.INCH, None, D.ROD_D, '2-56 x 12 in', order='pushrod', section=D.ROD_D, note='steering pushrod')
    add('bush', 'brass tube for the pintle bushings', 'stick', None, None, D.BUSHING_OD, '%.0f mm OD' % D.BUSHING_OD, order=None, section=D.BUSHING_OD,
        note='NOT on the order list; no tube size is defined in the model beyond the OD')
    return out


# ---- the table ---------------------------------------------------------------------------------------------------------------------------------------
class Part:
    """One cut piece (a row of the cut list). dims are (length along the grain, width across it) for sheet pieces, the stick length for sticks."""

    def __init__(self, mark, name, qty, stock, t, length, width=None, grain='x', a1=None, a2=None, note='', group='', template=None, joint=None, wedge=False):
        self.mark, self.name, self.qty, self.stock, self.t = mark, name, qty, stock, t
        self.length, self.width, self.grain, self.a1, self.a2 = length, width, grain, a1, a2
        self.note, self.group, self.template, self.joint, self.wedge = note, group, template, joint, wedge

    def area(self):
        return self.length * self.width


class Template:
    def __init__(self, mark, name, shape, qty, stock, t, group, note=''):
        self.mark, self.name, self.shape, self.qty, self.stock, self.t, self.group, self.note = mark, name, shape, qty, stock, t, group, note


class Table:
    def __init__(self):
        self.parts = []
        self.templates = OrderedDict()
        self.assemblies = OrderedDict()
        self.bought = OrderedDict()
        self.cad = {}
        self.stock = stocks()
        self.index = OrderedDict()                       # every mark -> dict(kind, name, qty, stock)

    def mark(self, mark, kind, name, qty, stock=None):
        if mark in self.index:
            raise ValueError('duplicate part mark %s' % mark)
        self.index[mark] = dict(mark=mark, kind=kind, name=name, qty=qty, stock=stock)

    def add_template(self, mark, name, shape, qty, stock, t, group, note=''):
        self.templates[mark] = Template(mark, name, shape, qty, stock, t, group, note)
        self.mark(mark, 'part', name, qty, stock)

    def add_stick(self, mark, name, qty, stock, length, group, a1=None, a2=None, note='', joint=None, wedge=False, t=None):
        a1 = RIGHT if a1 is None else a1
        a2 = RIGHT if a2 is None else a2
        st = self.stock[stock]
        self.parts.append(Part(mark, name, qty, stock, t if t is not None else st.t, length, st.section, 'x', a1, a2, note, group, None, joint, wedge))
        self.mark(mark, 'part', name, qty, stock)

    def add_sheet(self, mark, name, shape, qty, stock, t, group, a1=None, a2=None, note='', template=None, register=True):
        """Register a flat part: a template (unless register is False) and its cut pieces (planks when the shape is planked)."""
        st = self.stock[stock]
        if stock == 'balsa' and not shape.planks:
            auto_planks(shape, st)
        pcs = shape.planks if shape.planks else [shape.outline]
        n = len(pcs)
        if register:
            self.add_template(mark, name, shape, qty, stock, t, group, note)
        if st.kind == 'sheet' and stock != 'balsa':
            fit_sheet(mark, shape, st)
        for k, pc in enumerate(pcs, 1):
            xs = [p[0] for p in pc]
            ys = [p[1] for p in pc]
            dx, dy = max(xs) - min(xs), max(ys) - min(ys)
            ln, wd = (dx, dy) if shape.grain == 'x' else (dy, dx)
            pm = mark if n == 1 else '%s.%d' % (mark, k)
            self.parts.append(Part(pm, name if n == 1 else '%s, plank %d of %d' % (name, k, n), qty, stock, t, ln, wd, shape.grain, a1, a2, note, group, template or mark))
            if n > 1:
                self.mark(pm, 'plank', '%s, plank %d of %d' % (name, k, n), qty, stock)

    def parts_for(self, stock):
        return [p for p in self.parts if p.stock == stock]


def fit_sheet(mark, shape, st):
    """Check a ply or G10 part fits the sheet in at least one orientation (balsa is planked instead)."""
    a, b = shape.size()
    long_, short_ = max(a, b), min(a, b)
    if long_ > max(st.L, st.W) + D.FIT_EPS or short_ > min(st.L, st.W) + D.FIT_EPS:
        raise ValueError('part %s (%.1f x %.1f) does not fit the %s stock' % (mark, a, b, st.label))


def auto_planks(shape, st):
    """Split a balsa part wider than the stock into equal planks (butt joints). Grain runs along x or y; try both and keep the option with the fewest
    planks whose seams stay clear of the holes. Raises when a piece is longer than the stock (planks run along the stock length)."""
    best = None
    for grain in (shape.grain, 'y' if shape.grain == 'x' else 'x'):
        ax_along, ax_across = (0, 1) if grain == 'x' else (1, 0)
        x0, y0, x1, y1 = shape.bbox()
        ext = (x1 - x0, y1 - y0)
        along, across = ext[ax_along], ext[ax_across]
        if along > st.L + D.FIT_EPS:
            continue
        n = max(1, math.ceil(across / st.W - D.FIT_EPS))
        lo = (x0, y0)[ax_across]
        seams = [lo + across * i / n for i in range(1, n)]
        clear = all(abs(s - c[1][ax_across]) > c[2] + D.SKIN_T for s in seams for c in shape.cuts if c[0] == 'circle')
        key = (n, 0 if clear else 1, 0 if grain == shape.grain else 1)
        if best is None or key < best[0]:
            best = (key, grain, ax_across, n)
    if best is None:
        raise ValueError('a balsa part of %.1f x %.1f is longer than the %.1f stock in both directions' % (shape.size() + (st.L,)))
    _, grain, ax, n = best
    shape.grain = grain
    if n > 1:
        planks, seams = SH.split_polygon(shape.outline, ax, n)
        shape.planks = planks
        for s in seams:
            p, q = ((s, min(pp[1] for pp in shape.outline)), (s, max(pp[1] for pp in shape.outline))) if ax == 0 else \
                   ((min(pp[0] for pp in shape.outline), s), (max(pp[0] for pp in shape.outline), s))
            shape.guides.append(SH.line_guide(p, q, 'seam'))


RING = ('O1', 'O2', 'O3', 'TP', 'I2', 'I1', 'TR')


def ring_ends():
    """Wall mark -> (start vertex, end vertex) in the turn list of schedules.turns(): the walls run round the sponson outline in RING order."""
    n = len(RING)
    return {m: (i, (i + 1) % n) for i, m in enumerate(RING)}


def seam_backing(tb, p, T):
    """Backing strips for the plank seams of a panel (A-501 J5): one strip per seam, the seam length of the panel."""
    if p['planks'] <= 1 or p['where'] in ('trunk', 'cap'):
        return
    pm = PANEL_MARK.get(p['mark'], p['mark'])
    nseam = p['qty'] * (p['planks'] - 1)
    name = 'Seam backing strip for %s' % pm
    tb.parts.append(Part('BK-%s' % pm, name, nseam, 'balsa', T, p['seam'] / (p['planks'] - 1), D.BACK_W, 'x', None, None,
                         'centered on the plank seam, %.2f wide' % D.BACK_W, 'Seam backing', None, 'J5'))
    tb.mark('BK-%s' % pm, 'part', name, nseam, 'balsa')


def _ang(turn):
    return RIGHT - turn / 2


def build(r=None):
    """The whole mark table at the design battery position."""
    r = r or hydro.design()
    zd = r['deck']
    T = D.SKIN_T
    tb = Table()
    pl = S.panels(zd)
    fr = S.frames(zd)
    hs = S.hatches(zd)
    tn = [t for _, _, t in S.turns()]
    wf = lambda x: float(G.sponson_width(x))
    hz = G.housing(zd)

    # ---- hull skin (A-103) ----
    ends = ring_ends()
    skin_names = {}
    for p in pl:
        mk = p['mark']
        if mk in ('BP', 'DO', 'SK', 'SH', 'TE', 'TK') or p['where'] == 'cap' and mk in ('CT',):
            pass
        if mk in ('BP', 'DO', 'SK', 'SH', 'TE'):
            if mk == 'SK':
                seam_backing(tb, p, T)
            continue
        pm = PANEL_MARK.get(mk, mk)
        if mk == 'CT':
            p = dict(p, x0=hz['x0'], x1=hz['x1'])
        sh = SH.panel_shape(p, zd)
        a1, a2 = (_ang(tn[ends[mk][0]]), _ang(tn[ends[mk][1]])) if mk in ends else (None, None)
        group = {'wall': 'Hull skin', 'plate': 'Hull skin', 'triangle': 'Skegs'}.get(p['kind'], 'Hull skin')
        if p['where'] == 'trunk':
            group = 'Blade trunk'
        if p['where'] == 'cap':
            group = 'Bow cap'
        if p['where'] == 'aft':
            group = 'Aft deck box'
        tb.add_sheet(pm, p['name'], sh, p['qty'], 'balsa', p['t'], group, a1, a2,
                     note='mitered ends: bevel through the thickness' if mk in ends else '')
        seam_backing(tb, p, T)
    # deck overhang, three pieces
    for side, shape in SH.deck_overhang_shapes().items():
        tb.add_sheet('DO-' + side, {'P': 'Deck overhang strip, port', 'S': 'Deck overhang strip, starboard', 'F': 'Deck overhang strip ahead of the bow tips'}[side],
                     shape, 1, 'balsa', T, 'Deck overhang')
    # push bar, arms
    core_t = D.BUMPER_T - D.BUMPER_FACE_T
    layers = math.ceil(core_t / T)
    bw = 2 * max(abs(p[1]) for p in G.bumper_plan())
    core = SH.long_grain(SH.Shape(SH.rect(bw, G.BUMPER_DEPTH), notes=['core %.2f thick: %d layers of %.3f; ends chamfered %.0f deg in plan on the taper deck plan only' % (core_t, layers, T, D.BUMPER_CHAMFER_DEG)]))
    tb.add_sheet('BB-C', 'Push bar core', core, layers, 'balsa', T, 'Push bar', note='%d layers' % layers)
    tb.add_sheet('BB-F', 'Push bar face', SH.bar_face_shape(), 1, 'ply15', D.BUMPER_FACE_T, 'Push bar')
    arm = G.bumper_arms(zd)
    for sd, nm in (('P', 'port'), ('S', 'starboard')):
        tb.add_sheet('BA-' + sd, 'Push bar arm, %s' % nm, SH.long_grain(SH.Shape(SH.rect(arm['L'], arm['w']), notes=['ply arm lying on the deck top, from the cap forward plate (X %.1f) to the bar aft face (X %.1f)' % (arm['x0'], arm['x1'])])),
                     1, 'ply', arm['t'], 'Push bar')

    # ---- skegs ----
    sk_row = next(p for p in pl if p['mark'] == 'SK')
    n_pl = sk_row['planks']
    for sd in ('P', 'S'):
        for k in (1, 2):
            sh = SH.skeg_plate_shape(n_pl)
            if sd == 'S':
                sh = sh.mirrored()
            tb.add_sheet('SK-%s%d' % (sd, k), 'Skeg side plate %d, %s' % (k, 'port' if sd == 'P' else 'starboard'), sh, 1, 'balsa', T, 'Skeg')
    sc_layers = math.ceil(G.SKEG_INTERIOR / T)
    tb.add_sheet('SC', 'Skeg core layer', SH.skeg_core_shape(n_pl), BOTH * sc_layers, 'balsa', T, 'Skeg', note='%d layers per skeg, finished thickness %.2f' % (sc_layers, G.SKEG_INTERIOR))
    sh_layers = math.ceil(D.SHOE_T / T)
    tb.add_sheet('SH', 'Skeg shoe layer', SH.shoe_shape(), BOTH * sh_layers, 'balsa', T, 'Skeg', note='%d layers per shoe' % sh_layers)
    for sd in ('P', 'S'):
        tb.add_stick('PB-' + sd, 'Pintle bushing, %s' % ('port' if sd == 'P' else 'starboard'), 1, 'bush', D.SHOE_T, 'Steering', note='%.0f OD brass, length = shoe thickness' % D.BUSHING_OD)

    # ---- trunk, bow cap ----
    te = next(p for p in pl if p['mark'] == 'TE')
    for nm, key, h in (('TE-A', 'aft', te['h0']), ('TE-F', 'forward', te['h1'])):
        tb.add_sheet(nm, 'Trunk end plate, %s end' % key, SH.trunk_end_shape(h), te['qty'] // BOTH, 'balsa', T, 'Blade trunk')
    if hz and hz['kind'] == 'cap':
        for f in fr:
            if hz['x0'] < f['x'] < hz['x1']:
                w, h = f['w_out'] - 2 * T, hz['ztop'] - zd(f['x'])
                tb.add_sheet(rib_mark(f['x']), 'Bow cap rib at F%d' % f['num'], SH.long_grain(SH.Shape(SH.rect(w, h), notes=['rib at X %.0f, %.1f wide (sponson less two walls) x %.1f high' % (f['x'], w, h)])),
                             BOTH, 'balsa', T, 'Bow cap')

    # ---- frames, bulkheads, tunnel pieces, deck brackets ----
    for f in fr:
        mp, ms, mt = frame_marks(f['num'])
        role = ' (bulkhead BH%d)' % (1 + [x['num'] for x in fr if x['bulkhead']].index(f['num'])) if f['bulkhead'] else ''
        tb.add_sheet(mp, 'Frame F%d sponson piece, port%s' % (f['num'], role), SH.frame_shape(f, 'P'), 1, 'balsa', f['t'], 'Frames', note=f['kind'])
        tb.add_sheet(ms, 'Frame F%d sponson piece, starboard%s' % (f['num'], role), SH.frame_shape(f, 'S'), 1, 'balsa', f['t'], 'Frames', note=f['kind'])
        tb.add_sheet(mt, 'Frame F%d tunnel piece' % f['num'], SH.tunnel_shape(f), 1, 'balsa', f['t'], 'Frames', note=f['tunnel_kind'])
    for b in G.deck_brackets():
        for sd, nm in (('P', 'port'), ('S', 'starboard')):
            tb.add_sheet(bracket_mark(b['x'], sd), 'Deck bracket at X %.0f, %s' % (b['x'], nm), SH.bracket_shape(b['L']), 1, 'balsa', D.FRAME_T, 'Deck brackets')

    # ---- aft deck box beams, deck beams ----
    ab = G.aft_box()
    sec = 'section %.2f x %.2f' % (ab['w'], ab['h'])
    post_x = G.POSTX - (-D.AFT_DECK_L + ab['w'])
    tb.add_stick('AD-BP', 'Aft deck long beam, port', 1, 'strip', ab['long_len'], 'Aft deck box', note='%s; post bushing hole at %.1f from the aft end (size not defined in the model)' % (sec, post_x))
    tb.add_stick('AD-BS', 'Aft deck long beam, starboard', 1, 'strip', ab['long_len'], 'Aft deck box', note='%s; post bushing hole at %.1f from the aft end (size not defined in the model)' % (sec, post_x))
    tb.add_stick('AD-BT', 'Aft deck transom beam', 1, 'strip', ab['transom_len'], 'Aft deck box', note=sec)
    tb.add_stick('AD-BE', 'Aft deck end beam', 1, 'strip', ab['end_len'], 'Aft deck box', note=sec)
    sup, rail_l = S.supports(zd)
    for q in sup:
        if q['mark'] != 'DB':
            continue
        x = q['x']
        al = S.aft_taper_deg() if x < D.AFT_TAPER_X else (S.bow_taper_deg() if x > G.BOW0 else 0.0)
        tb.add_stick(beam_mark(x), 'Deck beam at X %.0f' % x, 1, 'strip', q['w'], 'Deck beams', a1=RIGHT - al, a2=RIGHT - al,
                     note='section %.2f x %.2f, ends cut to the hull wall (%.2f deg off square)' % (D.DECK_BEAM_W, D.DECK_BEAM_T, al))

    # ---- supports ----
    m = S.mount_dims()
    for sd, nm in (('P', 'port'), ('S', 'starboard')):
        for ly in SH.mount_layers():
            tb.add_sheet('MM-%s%d' % (sd, ly['j']), 'Motor mount %s, layer %d' % (nm, ly['j']), SH.mount_layer_shape(ly, m), 1, 'balsa', T, 'Motor mounts')
    tb.add_sheet('MC', 'Motor clamp cap', SH.long_grain(SH.Shape(SH.rect(m['l'], D.MOUNT_W), notes=['ply clamp cap over the motor']))
                 , BOTH, 'ply', T, 'Motor mounts')
    tb.add_sheet('RL', 'Battery rail', SH.long_grain(SH.Shape(SH.rect(rail_l, D.RAIL_W), notes=['rail %.2f wide x %.1f high; slide X %.0f to %.0f plus the battery length' % (D.RAIL_W, D.BAT['rail'], D.BAT_SLIDE[0], D.BAT_SLIDE[1])])),
                 BOTH * BOTH, 'balsa', D.BAT['rail'], 'Battery rails', note='rail height %.1f, less than the %.3f sheet' % (D.BAT['rail'], T))
    sv = D.STEER_SERVO
    pad = D.PAD_MARGIN
    tb.add_sheet('SV', 'Steering servo pad', SH.long_grain(SH.Shape(SH.rect(sv['l'] + 2 * pad, sv['w'] + 2 * pad), notes=['servo footprint %.1f x %.1f plus %.0f each side' % (sv['l'], sv['w'], pad)])), 1, 'ply', T, 'Servo pads')
    bsv = D.BLADE_SERVO
    if G.blade_servo_box(zd) is not None:
        tb.add_sheet('BV', 'Blade servo shelf', SH.long_grain(SH.Shape(SH.rect(bsv['l'] + 2 * pad, bsv['w'] + 2 * pad), notes=['servo footprint %.1f x %.1f plus %.0f each side' % (bsv['l'], bsv['w'], pad)])), 1, 'ply', T, 'Servo pads')

    # ---- hatches ----
    for h in hs:
        nm = h['name']
        lid, plug, rim = SH.hatch_shapes(h)
        tb.add_sheet('LD-' + nm, 'Hatch %s lid' % nm, lid, h['qty'], 'balsa', T, 'Hatches')
        for k in range(D.PLUG_LAYERS):
            pk = SH.Shape(list(plug.outline), list(plug.cuts), list(plug.guides), grain='x' if k % 2 == 0 else 'y', notes=list(plug.notes))
            pk.notes.append('layer %d of %d, grain %s' % (k + 1, D.PLUG_LAYERS, 'along the length' if k % 2 == 0 else 'across (crossed with layer 1)'))
            tb.add_sheet('PG-%s-%d' % (nm, k + 1), 'Hatch %s plug, layer %d' % (nm, k + 1), pk, h['qty'], 'balsa', T, 'Hatches')
        tb.add_sheet('RR-' + nm, 'Hatch %s rim ring' % nm, rim, h['qty'], 'ply', D.RIM_T, 'Hatches')
        tb.add_stick('CD-' + nm, 'Hatch %s O-ring cord loop' % nm, h['qty'], 'cord', h['cord'], 'Hatches', note='includes the %.0f splice lap' % D.CORD_LAP, t=D.CORD_D)
    ht = S.hatch_totals(hs)
    tb.add_sheet('LP', 'Latch pad', SH.latch_pad_shape(), ht['latches'], 'ply', T, 'Hatches')

    # ---- blades ----
    bm = D.BLADE_MATERIALS[D.BLADE_MATERIAL]
    for sd, nm in (('P', 'port'), ('S', 'starboard')):
        tb.add_sheet('BL-' + sd, 'Daggerboard blade, %s' % nm, SH.blade_shape(), 1, 'g10', bm['t'], 'Blades')

    # ---- steering metal ----
    post_l = G.post_required_length(zd)
    for sd, nm in (('P', 'port'), ('S', 'starboard')):
        tb.add_stick('NP-' + sd, 'Nozzle post, %s' % nm, 1, 'rod3', post_l, 'Steering', note='%.1f mm rod, length required under the aft deck top skin' % D.NOZ_POST_D)
        tb.add_stick('NT-' + sd, 'Nozzle post sleeve, %s' % nm, 1, 'tube4', post_l, 'Steering', note='same length as the post')
        tb.add_stick('PT-' + sd, 'Pintle pin, %s' % nm, 1, 'rod3', G.PINTLE_L, 'Steering', note='%.1f mm pin below the nozzle; the depth into the nozzle is not defined in the model' % D.PINTLE_D)
    tb.add_stick('TB', 'Tie bar', 1, 'bar4', G.TIE_L, 'Steering', note='between the two post centres')
    tb.add_stick('PRD', 'Steering pushrod', 1, 'rod256', G.ROD_L, 'Steering', note='between link centres; the order list carries a spare')

    # ---- blocking ----
    block_pieces(tb, zd, fr, hs, tn)

    # ---- assemblies, bought parts, CAD names ----
    assemblies(tb, fr, hz)
    bought(tb)
    cad_names(tb)
    return tb


def block_pieces(tb, zd, fr, hs, tn):
    """Blocking and stringers as cut sticks, grouped by joint (J1 to J7, M1, H1) with the miter angles of the corners they meet."""
    T = D.SKIN_T
    wf = lambda x: float(G.sponson_width(x))
    seg = S._seg
    L = {'O1': seg(S.OUTER[0], S.OUTER[1]), 'O2': seg(S.OUTER[1], S.OUTER[2]), 'O3': seg(S.OUTER[2], S.OUTER[-1]), 'TP': wf(D.LOA),
         'I2': seg(S.INNER[1], S.INNER[2]), 'I1': seg(S.INNER[0], S.INNER[1]), 'TR': wf(0)}
    V = ring_ends()
    ang = lambda k: (_ang(tn[V[k][0]]), _ang(tn[V[k][1]]))
    nm = {'O1': 'outer wall, aft taper', 'O2': 'outer wall, straight', 'O3': 'outer wall, bow', 'I1': 'inner wall, aft taper', 'I2': 'inner wall, straight',
          'TR': 'transom', 'TP': 'tip face'}

    def add(mark, name, qty, stock, length, a, joint, note='', wedge=False):
        tb.add_stick(mark, name, qty, stock, length, 'Blocking ' + joint, a[0], a[1], note, joint, wedge)

    for k in ('I1', 'I2', 'TR', 'TP'):
        add('J1-' + k, 'Blocking, wall to bottom, %s' % nm[k], BOTH, 'tri', L[k], ang(k), 'J1')
    for k in ('I1', 'I2'):
        add('J1R-' + k, 'Blocking, wall to roof plate, %s' % nm[k], BOTH, 'tri', L[k], ang(k), 'J1')
    for k in ('O1', 'O2', 'O3'):
        add('J2-' + k, 'Chine stringer, %s' % nm[k], BOTH, 'chine', L[k], ang(k), 'J2', 'outer corner radius equal to the bilge radius')
    for k in ('O1', 'O2', 'O3', 'I1', 'I2', 'TR', 'TP'):
        add('J3-' + k, 'Blocking, wall to deck, %s' % nm[k], BOTH, 'tri', L[k], ang(k), 'J3')
    cw0 = 2 * (G.HT + float(G.inner_off(0)))
    add('J3-TTR', 'Blocking, tunnel-top transom TT to roof plate', 1, 'tri', cw0, (RIGHT, RIGHT), 'J3')
    add('J3-TTD', 'Blocking, tunnel-top transom TT to deck', 1, 'tri', cw0, (RIGHT, RIGHT), 'J3')
    for i, (name, p, turn) in enumerate(S.turns(), 1):
        add('J4-%d' % i, 'Corner wedge, %s' % name, BOTH, 'tri', zd(p[0]) - 2 * T, (RIGHT, RIGHT), 'J4',
            'wedge for a %.2f deg turn, included angle %.2f, legs %.3f, wall height at X %.1f; takes a whole stick length' % (turn, 2 * RIGHT - turn, D.BLOCK_LEG, p[0]), wedge=True)
    add('J6-SK', 'Blocking, skeg box to bottom', BOTH * BOTH, 'tri', G.SKEG_X0, (RIGHT, RIGHT), 'J6', 'both sides of each skeg box')
    half = RIGHT / 2
    for f in fr:
        n = f['num']
        add('J7-F%d-W' % n, 'Gusset, frame F%d sponson piece, bottom and deck edges' % n, BOTH * BOTH * BOTH, 'tri', f['w_in'], (half, half), 'J7', 'both faces, mitered at the frame corners')
        add('J7-F%d-H' % n, 'Gusset, frame F%d sponson piece, wall edges' % n, BOTH * BOTH * BOTH, 'tri', f['h'], (half, half), 'J7', 'both faces, mitered at the frame corners')
        add('J7-F%d-TW' % n, 'Gusset, frame F%d tunnel piece, roof and deck edges' % n, BOTH * BOTH, 'tri', f['tun_w'], (half, half), 'J7', 'both faces')
        add('J7-F%d-TH' % n, 'Gusset, frame F%d tunnel piece, wall edges' % n, BOTH * BOTH, 'tri', f['tun_h'], (half, half), 'J7', 'both faces')
    m = S.mount_dims()
    add('M1-MM', 'Blocking, motor mount base to floor', BOTH * BOTH, 'tri', m['l'], (RIGHT, RIGHT), 'M1', 'both long edges of each mount')
    for h in hs:
        ry = h['rim_y']
        oW, oL = h['W'] + 2 * ry, h['L'] + 2 * D.RIM_W
        a = RIGHT if h['rim_touch'] else half
        add('H1-%s-W' % h['name'], 'Blocking, hatch %s rim ends' % h['name'], BOTH * h['qty'], 'tri', oW, (a, a), 'H1')
        if not h['rim_touch']:
            add('H1-%s-L' % h['name'], 'Blocking, hatch %s rim sides' % h['name'], BOTH * h['qty'], 'tri', oL, (half, half), 'H1')


# ---- assemblies, bought items, CAD names -------------------------------------------------------------------------------------------------------------
def assemblies(tb, fr, hz):
    A = tb.assemblies
    bh = [f for f in fr if f['bulkhead']]
    for k, f in enumerate(bh, 1):
        A['BH%d' % k] = ('Bulkhead %d (solid frame F%d at X %.1f)' % (k, f['num'], f['x']), [frame_marks(f['num'])[0], frame_marks(f['num'])[1]])
    skin = ['O1', 'O2', 'O3', 'I1', 'I2', 'TP', 'TR', 'BT']
    A['HS-P'] = ('Hull shell, port sponson (walls, bottom)', skin)
    A['HS-S'] = ('Hull shell, starboard sponson (walls, bottom)', skin)
    A['SKG-P'] = ('Skeg and shoe, port', ['SK-P1', 'SK-P2', 'SC', 'SH', 'PB-P'])
    A['SKG-S'] = ('Skeg and shoe, starboard', ['SK-S1', 'SK-S2', 'SC', 'SH', 'PB-S'])
    if hz and hz['kind'] == 'cap':
        cap = ['CT', 'CO1', 'CO2', 'CI', 'CA', 'CF'] + [rib_mark(f['x']) for f in fr if hz['x0'] < f['x'] < hz['x1']]
        A['CAP-P'] = ('Bow cap, port', cap)
        A['CAP-S'] = ('Bow cap, starboard', cap)
    A['BB'] = ('Push bar', ['BB-C', 'BB-F'])
    A['MM-P'] = ('Motor mount, port', ['MM-P%d' % ly['j'] for ly in SH.mount_layers()])
    A['MM-S'] = ('Motor mount, starboard', ['MM-S%d' % ly['j'] for ly in SH.mount_layers()])
    A['AD'] = ('Aft deck box', ['AD-T', 'AD-B', 'AD-BP', 'AD-BS', 'AD-BT', 'AD-BE'])
    for k, v in A.items():
        tb.mark(k, 'assembly', v[0], 1)


BOUGHT = [('MOT-P', 'Motor, port'), ('MOT-S', 'Motor, starboard'), ('JK-P', 'Water jacket, port'), ('JK-S', 'Water jacket, starboard'),
          ('ESC-P', 'ESC, port'), ('ESC-S', 'ESC, starboard'), ('RX', 'Receiver'), ('SSV', 'Steering servo'), ('BSV', 'Blade servo'),
          ('BAT-P', 'Battery, port'), ('BAT-S', 'Battery, starboard'), ('NZ-P', 'Nozzle, port'), ('NZ-S', 'Nozzle, starboard'),
          ('PR-P', 'Propeller, port'), ('PR-S', 'Propeller, starboard'), ('DS-P', 'Drive shaft and joint, port'), ('DS-S', 'Drive shaft and joint, starboard')]


def bought(tb):
    for mk, nm in BOUGHT:
        tb.bought[mk] = nm
        tb.mark(mk, 'bought', nm, 1)


def cad_names(tb):
    """CAD part name -> mark (tools/cad.py names a part <group>__<mark>_<name>)."""
    c = tb.cad
    c.update({'sponson_port': 'HS-P', 'sponson_stbd': 'HS-S', 'tunnel_roof': 'RP', 'sponson_deck_port': 'DK', 'sponson_deck_stbd': 'DK', 'center_deck': 'DC',
              'aft_deck_top': 'AD-T', 'aft_deck_bottom': 'AD-B', 'aft_beam_port': 'AD-BP', 'aft_beam_stbd': 'AD-BS', 'aft_beam_transom': 'AD-BT', 'aft_beam_end': 'AD-BE',
              'deck_overhang': 'DO', 'bar_core': 'BB-C', 'bar_face': 'BB-F', 'arm_port': 'BA-P', 'arm_stbd': 'BA-S', 'cap_port': 'CAP-P', 'cap_stbd': 'CAP-S',
              'skeg_port': 'SKG-P', 'skeg_stbd': 'SKG-S', 'nozzle_port': 'NZ-P', 'nozzle_stbd': 'NZ-S', 'post_port': 'NP-P', 'post_stbd': 'NP-S',
              'prop_port': 'PR-P', 'prop_stbd': 'PR-S', 'shaft_aft_port': 'DS-P', 'shaft_aft_stbd': 'DS-S', 'shaft_fwd_port': 'DS-P', 'shaft_fwd_stbd': 'DS-S',
              'motor_port': 'MOT-P', 'motor_stbd': 'MOT-S', 'jacket_port': 'JK-P', 'jacket_stbd': 'JK-S', 'steer_servo': 'SSV', 'esc_1': 'ESC-P', 'esc_2': 'ESC-S',
              'receiver': 'RX', 'battery_port': 'BAT-P', 'battery_stbd': 'BAT-S', 'blade_servo': 'BSV', 'blade_port': 'BL-P', 'blade_stbd': 'BL-S', 'water': 'WL'})
    for b in G.deck_brackets():
        c['bracket_x%03d_port' % round(b['x'])] = bracket_mark(b['x'], 'P')
        c['bracket_x%03d_stbd' % round(b['x'])] = bracket_mark(b['x'], 'S')


_CACHE = {}


def table():
    """The mark table at the design battery position, built once per process."""
    if 'tb' not in _CACHE:
        _CACHE['tb'] = build()
    return _CACHE['tb']


def cad_name(name):
    """CAD part name carrying its mark: <mark>_<name>. Raises KeyError when the CAD part has no mark."""
    tb = table()
    if name not in tb.cad:
        raise KeyError('CAD part %s has no mark' % name)
    return '%s_%s' % (tb.cad[name], name)
