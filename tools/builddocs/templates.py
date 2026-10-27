"""Full size templates (1:1, letter portrait). Every flat part gets a thin outline, its mark, a grain arrow and its key dimensions.

Identical parts are drawn once ('qty 4'), and a port and starboard pair that are mirror images are drawn once ('cut 1 as drawn, 1 mirrored'): the
drawing is a group of marks (see groups()). A drawing that fits the window (with its dimensions and text) shares a page with others, packed with
design.TEMPLATE_GAP mm between drawings (MaxRects on the measured extent of each drawing, text included). A drawing that does not fit is tiled: a
grid of pages with registration crosses, design.TILE_OVERLAP mm of overlap, and labels like 'SK-P1 sheet 2 of 3 (row 1, col 2)'. The first pages are
an index of marks to pages. Every page carries the 100 mm scale bar and the 50 mm check box."""
import math
import random
import re
import design as D
from . import draw
from .nest import _Rects
from .page import Doc, Page, LINE, GAP, wrap

CROSS = 5.0            # registration cross arm and inset from the window corner, mm
TILE_PAD = 8.0         # blank margin right and below a tiled part, mm
TILE_PAD_L = 16.0      # left margin (height dimension clear of the registration crosses)
TILE_PAD_T = 24.0      # top margin (mark, width dimension, clear of the crosses)


def window_size(doc):
    pg = doc.page('x')
    doc.pages.pop()
    return pg.window()


def tile_grid(w, h, ww, wh, ov):
    """Columns and rows of windows ww x wh with overlap ov that cover w x h."""
    cols = 1 if w <= ww else math.ceil((w - ww) / (ww - ov)) + 1
    rows = 1 if h <= wh else math.ceil((h - wh) / (wh - ov)) + 1
    return cols, rows


TRIALS = 150           # shuffled orders tried by the packer after the four fixed ones
INDEX_COLS = 3         # columns of the index of marks
INDEX_HEAD = 26.0      # room for the heading text of an index page, mm
TW_CHOICES = (45.0, 60.0, 75.0, 100.0, 140.0)   # text block wrap widths tried for a packed drawing, mm


# ---- groups of identical or mirrored parts -------------------------------------------------------------------------------------------------------
SAME_TOL = 0.02        # mm: two points closer than this are the same point when parts are compared


def _match(a, b):
    """True when the point lists a and b hold the same points, in any order, within SAME_TOL."""
    if len(a) != len(b):
        return False
    left = list(b)
    for p in a:
        k = next((i for i, q in enumerate(left) if abs(p[0] - q[0]) <= SAME_TOL and abs(p[1] - q[1]) <= SAME_TOL), None)
        if k is None:
            return False
        left.pop(k)
    return True


def _items_match(a, b, eq):
    if len(a) != len(b):
        return False
    left = list(b)
    for x in a:
        k = next((i for i, y in enumerate(left) if eq(x, y)), None)
        if k is None:
            return False
        left.pop(k)
    return True


def _guide_pts(g):
    return [g[k] for k in ('p', 'q', 'c') if k in g] + list(g.get('pts', []))


def _same_shape(a, b):
    """True when shape b is shape a drawn again (position does not matter): outline, cut-outs, guides, points, plank areas, grain and notes."""
    if a.grain != b.grain or a.notes != b.notes:
        return False
    a, b = a.normalized(), b.normalized()
    if not _match(a.outline, b.outline):
        return False

    def cut_eq(c, d):
        if c[0] != d[0]:
            return False
        return (_match([c[1]], [d[1]]) and abs(c[2] - d[2]) <= SAME_TOL) if c[0] == 'circle' else _match(c[1], d[1])

    def guide_eq(g, h):
        return (g['kind'], g.get('style', ''), g.get('text', '')) == (h['kind'], h.get('style', ''), h.get('text', '')) and abs(g.get('r', 0.0) - h.get('r', 0.0)) <= SAME_TOL \
            and _match(_guide_pts(g), _guide_pts(h))
    return (_items_match(a.cuts, b.cuts, cut_eq) and _items_match(a.guides, b.guides, guide_eq)
            and _items_match(a.points, b.points, lambda p, q: p[2] == q[2] and _match([p[:2]], [q[:2]]))
            and _items_match(a.planks, b.planks, lambda p, q: abs(draw._area(p) - draw._area(q)) <= 0.5))


def _relation(rep, t):
    """'same' when t's shape is rep's drawn again, 'mirror' when it is rep's mirror image, None when they differ (or differ in stock or thickness)."""
    if rep.stock != t.stock or abs(rep.t - t.t) > 1e-9:
        return None
    a, b = rep.shape, t.shape
    if abs(a.size()[0] - b.size()[0]) > 0.05 or abs(a.size()[1] - b.size()[1]) > 0.05:
        return None
    if _same_shape(a, b):
        return 'same'
    if _same_shape(a, b.mirrored()):
        return 'mirror'
    return None


def groups(tb):
    """Templates that share one drawing. Each group: marks (in table order), rep (first template), members [(mark, mirrored, qty)], qty, n_as, n_mir.
    A member is mirrored only when its shape is a mirror image that is not also the same drawing (a symmetric part is simply 'same')."""
    out = []
    for mk, t in tb.templates.items():
        for g in out:
            rel = _relation(g['rep'], t)
            if rel:
                g['members'].append((mk, rel == 'mirror', t.qty))
                break
        else:
            out.append(dict(rep=t, members=[(mk, False, t.qty)]))
    for g in out:
        g['marks'] = [m for m, _, _ in g['members']]
        g['qty'] = sum(q for _, _, q in g['members'])
        g['n_mir'] = sum(q for _, mi, q in g['members'] if mi)
        g['n_as'] = g['qty'] - g['n_mir']
    return out


def group_name(g):
    """One name for the group: the common name once port, starboard, station and layer numbers are taken off, else the distinct names joined."""
    names = []
    for m in g['marks']:
        t = g['tpls'][m]
        n = re.sub(r',?\s*\b(port|starboard)\b', '', t.name)
        n = re.sub(r'\s+at X \d+', '', n)
        n = re.sub(r'\s+(layer|plate|part)?\s*\d+\s*$', '', n) if len(g['marks']) > 1 else n
        if n not in names:
            names.append(n)
    return '; '.join(names)


def qty_text(g):
    if g['n_mir']:
        return 'cut %d as drawn, %d mirrored' % (g['n_as'], g['n_mir'])
    return 'qty %d' % g['qty']


def text_for(tb, g, shape):
    t = g['rep']
    lines = ['%s; %s; thickness %.3g; %.1f x %.1f; grain along the %s side' % (
        qty_text(g), tb.stock[t.stock].label, t.t, shape.size()[0], shape.size()[1], 'horizontal' if shape.grain == 'x' else 'vertical')]
    if len(g['marks']) > 1:
        if g['n_mir']:
            lines.append('as drawn: %s; mirrored: %s' % (', '.join(m for m, mi, _ in g['members'] if not mi), ', '.join(m for m, mi, _ in g['members'] if mi)))
        else:
            lines.append('marks: ' + ', '.join('%s (%d)' % (m, q) if q > 1 else m for m, _, q in g['members']))
    for p in tb.parts:
        if (p.template or p.mark) in g['marks'] and (p.a1 is not None and (abs(p.a1 - 90) > D.FIT_EPS or abs(p.a2 - 90) > D.FIT_EPS)):
            lines.append('end angles %.2f and %.2f deg (90 is square)' % (p.a1, p.a2))
            break
    lines += shape.notes
    return lines


def choose_rotation(shape, ww, wh):
    """0 or 90 degrees, whichever needs fewer pages (0 on a tie)."""
    w, h = shape.size()
    px, py = TILE_PAD_L + TILE_PAD, TILE_PAD_T + TILE_PAD

    def pages(a, b):
        if a + draw.PAD_L + draw.PAD_R <= ww and draw.PAD_T + b + draw.PAD_T <= wh:
            return 1
        c, r = tile_grid(a + px, b + py, ww, wh, D.TILE_OVERLAP)
        return c * r
    return 90 if pages(h, w) < pages(w, h) else 0


def measure(shape, mark, lines, tw, vdim=True):
    """Extent (x0, y0, x1, y1) of the drawing of a shape at 1:1 with its dimensions, mark and text block wrapped at tw, the part's lower left at 0, 0."""
    pg = Page((400.0, 400.0), 'x', 'x')
    draw.draw_shape(pg, shape, draw.Frame(0.0, 0.0), mark, '', lines, text_w=tw, vdim=vdim)
    return draw.extent(pg.e)


def variants(shape, mark, name, lines_fn, ww, wh):
    """Every way to draw a shape on a shared page: text wrap widths, with the height dimension left out only when the part is so wide that the
    dimension would not fit. Each variant: dict(tw, lines, bb, bw, bh, vdim) with bb the extent of the drawing (lower left of the part at 0, 0)."""
    w = shape.size()[0]
    ls = ([name] if name else []) + lines_fn(shape)
    out = []
    for vd in (True, False):
        for tw in sorted({max(w, TW_CHOICES[0])} | set(TW_CHOICES)):
            bb = measure(shape, mark, ls, tw, vd)
            bw, bh = bb[2] - bb[0], bb[3] - bb[1]
            if bw <= ww + 1e-6 and bh <= wh + 1e-6 and not any(abs(v['bw'] - bw) < 0.5 and abs(v['bh'] - bh) < 0.5 for v in out):
                out.append(dict(tw=tw, lines=ls, bb=bb, bw=bw, bh=bh, vdim=vd))
        if out:
            break
    return out


def items(tb, ww, wh):
    out = []
    tpl = tb.templates
    for g in groups(tb):
        g['tpls'] = tpl
        t = g['rep']
        mk = t.mark
        name = group_name(g)
        sh = t.shape
        lines_fn = lambda s_, g=g: text_for(tb, g, s_)
        v0 = variants(sh, mk, name, lines_fn, ww, wh)
        sh90 = sh.rotated90()
        v90 = variants(sh90, mk, name, lines_fn, ww, wh)
        if v0 or v90:
            rot = 0 if v0 else 90
            shp = sh90 if rot else sh
            w, h = shp.size()
            pk = min(v0 or v90, key=lambda v: (v['bw'] * v['bh'], v['bh']))
            out.append(dict(mark=mk, marks=g['marks'], g=g, t=t, name=name, shape=shp, rot=rot, lines=lines_fn(shp), w=w, h=h, tx=0.0, cols=1, rows=1, pk=pk, base=pk,
                            v0=v0, v90=v90, shape0=sh, shape90=sh90))
            continue
        rot = choose_rotation(sh, ww, wh)
        shp = sh90 if rot else sh
        w, h = shp.size()
        lines = lines_fn(shp)
        tx = draw.block_height(max(w, 70), lines)
        cols, rows = tile_grid(w + TILE_PAD_L + TILE_PAD, h + TILE_PAD_T + TILE_PAD + tx, ww, wh, D.TILE_OVERLAP)
        out.append(dict(mark=mk, marks=g['marks'], g=g, t=t, name=name, shape=shp, rot=rot, lines=lines, w=w, h=h, tx=tx, cols=cols, rows=rows, pk=None))
    return out


def index_pages_needed(n_marks, wh):
    rows = int((wh - INDEX_HEAD) // LINE)
    return max(1, -(-n_marks // (rows * INDEX_COLS)))


def page_count(tb, doc=None):
    """(number of pages including the index, items)."""
    doc = doc or Doc('Full size templates', D.LETTER_IN)
    ww, wh = window_size(doc)[2:]
    its = items(tb, ww, wh)
    tiled = sum(i['cols'] * i['rows'] for i in its if i['cols'] * i['rows'] > 1)
    singles = [i for i in its if i['cols'] * i['rows'] == 1]
    return index_pages_needed(len(tb.templates), wh) + tiled + len(pack(singles, ww, wh)), its


def pack(singles, ww, wh, gap=None, rotate=None):
    """MaxRects packing of the shared-page drawings onto pages, gap mm apart (first fit over the pages, best fit within a page; several orders tried,
    fewest pages kept). rotate: turn a drawing 90 degrees when that saves space (None tries without, then with, and keeps the fewer pages; a drawing
    that only fits turned is always turned). Each item's 'pk' and 'shape' are set to the variant used. Returns pages, each a list of (item, x, y)
    with x, y the top left of the drawing's extent in window coordinates."""
    gap = D.TEMPLATE_GAP if gap is None else gap
    if rotate is None:
        b = pack(singles, ww, wh, gap, True)
        a = pack(singles, ww, wh, gap, False)
        return a if len(a) <= len(b) else pack(singles, ww, wh, gap, True)
    area = lambda i: i['base']['bw'] * i['base']['bh']
    orders = [lambda i: (-i['base']['bh'], -i['base']['bw'], i['mark']), lambda i: (-area(i), i['mark']),
              lambda i: (-max(i['base']['bw'], i['base']['bh']), i['mark']), lambda i: (-i['base']['bw'], -i['base']['bh'], i['mark'])]
    seq = [sorted(singles, key=key) for key in orders]
    rng = random.Random(7)                                    # then shuffles of the area order: a fixed seed, so the result is the same every run
    base = sorted(singles, key=orders[1])
    for _ in range(TRIALS):
        t = list(base)
        for k in range(len(t) - 1):
            if rng.random() < 0.15:
                t[k], t[k + 1] = t[k + 1], t[k]
        seq.append(t)
    best = None
    for order in seq:
        pages, rects, chosen = [], [], {}
        for it in order:
            vs = [(0, v) for v in it['v0']] + ([(90, v) for v in it['v90']] if rotate or not it['v0'] else [])
            hit = None
            for pi, rc in enumerate(rects):
                for rot, v in vs:
                    f = rc.find(v['bw'], v['bh'], False)
                    if f and (hit is None or f[0] < hit[0]):
                        hit = (f[0], pi, f, rot, v)
                if hit:
                    break
            if not hit:
                rects.append(_Rects(ww, wh, gap))
                pages.append([])
                pi = len(rects) - 1
                for rot, v in vs:
                    f = rects[pi].find(v['bw'], v['bh'], False)
                    if f and (hit is None or f[0] < hit[0]):
                        hit = (f[0], pi, f, rot, v)
            _, pi, f, rot, v = hit
            _, fx, fy, w2, h2, _ = f
            rects[pi].place(fx, fy, w2, h2)
            pages[pi].append((it, fx, fy))
            chosen[id(it)] = (rot, v)
        score = (len(pages), -sum(chosen[id(it)][1]['bw'] * chosen[id(it)][1]['bh'] for it, _, _ in pages[-1])) if pages else (0, 0)
        if best is None or score < best[0]:
            best = (score, pages, chosen)
    _, pages, chosen = best
    for pg in pages:
        for it, _, _ in pg:
            rot, v = chosen[id(it)]
            it['pk'], it['rot'] = v, rot
            it['shape'] = it['shape90'] if rot else it['shape0']
    return pages


def page_label(its_marks):
    t = ', '.join(its_marks)
    return t if len(t) < 60 else '%s to %s' % (its_marks[0], its_marks[-1])


def build(tb):
    """Returns the Doc of template pages: the index, the packed pages, then the tiled parts."""
    doc = Doc('Full size templates, print at 100 percent', D.LETTER_IN)
    ww, wh = window_size(doc)[2:]
    its = items(tb, ww, wh)
    tiled = [i for i in its if i['cols'] * i['rows'] > 1]
    singles = [i for i in its if i['cols'] * i['rows'] == 1]
    n_idx = index_pages_needed(len(tb.templates), wh)
    idx = []
    for k in range(n_idx):
        pg = doc.page('Index of marks to pages', 'part %d of %d' % (k + 1, n_idx))
        pg.marks = []
        idx.append(pg)
    for pk in pack(singles, ww, wh):
        pk.sort(key=lambda e: (e[2], e[1]))
        marks = [m for it, _, _ in pk for m in it['marks']]
        pg = doc.page(page_label([it['mark'] for it, _, _ in pk]), 'full size')
        pg.marks = marks
        wx, wy, _, _ = pg.window()
        for it, x, y in pk:
            b = it['pk']['bb']
            fr = draw.Frame(wx + x - b[0], wy + y - b[1])
            draw.draw_shape(pg, it['shape'], fr, it['mark'], '', it['pk']['lines'], text_w=it['pk']['tw'], vdim=it['pk']['vdim'])
        pg.scale_footer()
    for it in tiled:
        tile_pages(doc, it, ww, wh)
    pages_of = {}
    for i, pg in enumerate(doc.pages, 1):
        for mk in pg.marks:
            pages_of.setdefault(mk, [])
            if i not in pages_of[mk]:
                pages_of[mk].append(i)
    index_fill(idx, list(tb.templates), pages_of, ww, wh)
    return doc


def page_ranges(nums):
    """[3, 21, 22, 23] to '3, 21-23'."""
    out, i = [], 0
    nums = sorted(nums)
    while i < len(nums):
        j = i
        while j + 1 < len(nums) and nums[j + 1] == nums[j] + 1:
            j += 1
        out.append(str(nums[i]) if i == j else '%d-%d' % (nums[i], nums[j]))
        i = j + 1
    return ', '.join(out)


def index_fill(idx, marks, pages_of, ww, wh):
    """The index of marks to pages: mark, then the page numbers of its drawing, three columns, in table order."""
    rows = int((wh - INDEX_HEAD) // LINE)
    per = rows * INDEX_COLS
    cw = ww / INDEX_COLS
    for k, pg in enumerate(idx):
        wx, wy, _, _ = pg.window()
        y = wy + 3
        for ln in wrap('Each template mark and the page (page n of m, top right) that carries its drawing. A part that appears on a page with several others is found by its '
                       'mark in the title or beside its outline. Identical parts share one drawing marked qty N; a port and starboard pair shares one drawing marked '
                       'cut 1 as drawn, 1 mirrored. A part may be turned 90 degrees to share a page; its grain arrow gives the grain. Parts larger than a page run over consecutive pages (tiles, with registration crosses).', ww):
            pg.text(wx, y, ln, 't')
            y += LINE
        pg.text(wx, wy + INDEX_HEAD - 2, 'mark', 'bold')
        for c in range(1, INDEX_COLS):
            pg.text(wx + c * cw, wy + INDEX_HEAD - 2, 'mark', 'bold')
        for c in range(INDEX_COLS):
            pg.text(wx + (c + 1) * cw - 6, wy + INDEX_HEAD - 2, 'page', 'bold', 'end')
        chunk = marks[k * per:(k + 1) * per]
        for n, mk in enumerate(chunk):
            c, r = divmod(n, rows)
            x = wx + c * cw
            yy = wy + INDEX_HEAD + 1.5 + r * LINE
            pg.text(x, yy, mk, 't')
            pg.text(x + cw - 6, yy, page_ranges(pages_of.get(mk, [])) or '-', 't', 'end')
        pg.scale_footer()


def tile_pages(doc, it, ww, wh):
    """All pages of one tiled part. World frame: x right, y up from the lower left of the part box; the pad and text block extend it."""
    ov = D.TILE_OVERLAP
    cols, rows = it['cols'], it['rows']
    sx, sy = ww - ov, wh - ov
    n = cols * rows
    toth = TILE_PAD_T + TILE_PAD + it['h'] + it['tx']
    for r in range(rows):
        for c in range(cols):
            k = r * cols + c + 1
            title = '%s sheet %d of %d (row %d, col %d)' % (it['mark'], k, n, r + 1, c + 1)
            pg = doc.page(title, it['name'])
            pg.marks = it['marks']
            wx, wy, _, _ = pg.window()
            # tile window in world coordinates: left edge at c*sx, top edge at toth - r*sy (world y up, origin at the pad's lower left, text block below)
            wl = c * sx
            wtop = toth - r * sy
            # part box lower left in world: (TILE_PAD, it['tx'] + TILE_PAD)
            px, py = TILE_PAD_L, it['tx'] + TILE_PAD
            pg.clip_begin(wx, wy, ww, wh)
            fr = draw.Frame(wx + (px - wl), wy + (wtop - py))
            draw.draw_shape(pg, it['shape'], fr, it['mark'], it['name'], it['lines'])
            pg.clip_end()
            overlap_marks(pg, wx, wy, ww, wh, r, c, rows, cols, k)
            registration(pg, wx, wy, ww, wh, r, c)
            pg.scale_footer(lambda p, x, y, w, h, it=it, r=r, c=c: tile_map(p, x, y, w, h, it, r, c))


def registration(pg, wx, wy, ww, wh, r, c):
    """Crosses CROSS mm inside the window corners. Adjacent tiles share cross positions in the overlap, labelled by lattice position."""
    for dr, y in ((0, wy + CROSS), (1, wy + wh - CROSS)):
        for dc, x in ((0, wx + CROSS), (1, wx + ww - CROSS)):
            pg.line(x - CROSS, y, x + CROSS, y, 'reg')
            pg.line(x, y - CROSS, x, y + CROSS, 'reg')
            pg.circ(x, y, 1.2, 'reg')
            lab = '%s%d' % (chr(ord('A') + c + dc), r + dr + 1)
            pg.text(x + (1.5 if not dc else -1.5), y + (-2 if not dr else 4.5), lab, 'bold', 'start' if not dc else 'end')


def tile_map(pg, x, y, w, h, it, r, c):
    cols, rows = it['cols'], it['rows']
    cell = min(w / cols, h / rows, 14.0)
    pg.text(x, y + 3, 'tile %d of %d' % (r * cols + c + 1, cols * rows), 't')
    for rr in range(rows):
        for cc in range(cols):
            on = (rr == r and cc == c)
            pg.rect(x + cc * cell, y + 6 + rr * cell, cell, cell, 'reg', 'style="fill:%s"' % ('#bbb' if on else '#fff'))
            pg.text(x + cc * cell + cell / 2, y + 6 + rr * cell + cell / 2 + 1, str(rr * cols + cc + 1), 'ts', 'middle')


def overlap_marks(pg, wx, wy, ww, wh, r, c, rows, cols, k):
    """Dashed lines where the neighbouring sheets overlap this one, labelled with their sheet numbers."""
    ov = D.TILE_OVERLAP
    if c > 0:
        pg.line(wx + ov, wy, wx + ov, wy + wh, 'edge')
        pg.text(wx + 1, wy + wh / 2, 'overlaps sheet %d' % (k - 1), 'ts', 'start', -90)
    if c < cols - 1:
        pg.line(wx + ww - ov, wy, wx + ww - ov, wy + wh, 'edge')
        pg.text(wx + ww - 1, wy + wh / 2, 'overlaps sheet %d' % (k + 1), 'ts', 'end', -90)
    if r > 0:
        pg.line(wx, wy + ov, wx + ww, wy + ov, 'edge')
        pg.text(wx + ww / 2, wy + 3, 'overlaps sheet %d' % (k - cols), 'ts', 'middle')
    if r < rows - 1:
        pg.line(wx, wy + wh - ov, wx + ww, wy + wh - ov, 'edge')
        pg.text(wx + ww / 2, wy + wh - 1.5, 'overlaps sheet %d' % (k + cols), 'ts', 'middle')
