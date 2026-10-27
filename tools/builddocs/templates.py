"""Full size templates (1:1, letter portrait). Every flat part gets a thin outline, its mark, a grain arrow and its key dimensions. A part that does
not fit the drawing window is tiled: a grid of pages with registration crosses, design.TILE_OVERLAP mm of overlap, and labels like
'SK-P1 sheet 2 of 3 (row 1, col 2)'. Small parts share a page."""
import math
import design as D
from . import draw
from .page import Doc, LINE, GAP

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


def text_for(tb, t, shape):
    lines = ['qty %d; %s; thickness %.3g; %.1f x %.1f; grain along the %s side' % (
        t.qty, tb.stock[t.stock].label, t.t, shape.size()[0], shape.size()[1], 'horizontal' if shape.grain == 'x' else 'vertical')]
    for p in tb.parts:
        if (p.template or p.mark) == t.mark and (p.a1 is not None and (abs(p.a1 - 90) > D.FIT_EPS or abs(p.a2 - 90) > D.FIT_EPS)):
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


def items(tb, ww, wh):
    out = []
    for mk, t in tb.templates.items():
        sh = t.shape
        rot = choose_rotation(sh, ww, wh)
        shp = sh.rotated90() if rot else sh
        w, h = shp.size()
        lines = text_for(tb, t, shp)
        tx = draw.block_height(max(w, 70), lines)
        if w + draw.PAD_L + draw.PAD_R <= ww and draw.PAD_T + h + tx + GAP * 3 <= wh:
            cols, rows = 1, 1                                  # fits one page with its dimensions and notes
        else:
            cols, rows = tile_grid(w + TILE_PAD_L + TILE_PAD, h + TILE_PAD_T + TILE_PAD + tx, ww, wh, D.TILE_OVERLAP)
        out.append(dict(mark=mk, t=t, shape=shp, rot=rot, lines=lines, w=w, h=h, tx=tx, cols=cols, rows=rows))
    return out


def page_count(tb, doc=None):
    doc = doc or Doc('Full size templates', D.LETTER_IN)
    ww, wh = window_size(doc)[2:]
    its = items(tb, ww, wh)
    tiled = sum(i['cols'] * i['rows'] for i in its if i['cols'] * i['rows'] > 1 or i['w'] > ww or i['h'] > wh)
    singles = [i for i in its if i['cols'] * i['rows'] == 1]
    return tiled + len(pack(singles, ww, wh)), its


def pack(singles, ww, wh):
    """Shelf packing of small parts onto pages. Returns a list of pages, each a list of (item, x, y_top) positions in window coordinates."""
    pages, cur, x, y, rowh = [], [], 0.0, 0.0, 0.0
    for it in singles:
        bw = max(it['w'] + draw.PAD_L + draw.PAD_R, 70 + draw.PAD_L)
        bh = draw.PAD_T + it['h'] + it['tx'] + GAP * 3
        if x + bw > ww and cur:
            x, y, rowh = 0.0, y + rowh, 0.0
        if y + bh > wh and cur:
            pages.append(cur)
            cur, x, y, rowh = [], 0.0, 0.0, 0.0
        cur.append((it, x, y))
        x += bw
        rowh = max(rowh, bh)
    if cur:
        pages.append(cur)
    return pages


def build(tb):
    """Returns the Doc of template pages."""
    doc = Doc('Full size templates, print at 100 percent', D.LETTER_IN)
    ww, wh = window_size(doc)[2:]
    its = items(tb, ww, wh)
    tiled = [i for i in its if i['cols'] * i['rows'] > 1]
    singles = [i for i in its if i['cols'] * i['rows'] == 1]
    for pk in pack(singles, ww, wh):
        marks = [it['mark'] for it, _, _ in pk]
        pg = doc.page(', '.join(marks) if len(', '.join(marks)) < 60 else '%s to %s' % (marks[0], marks[-1]), 'full size')
        pg.marks = marks
        wx, wy, _, _ = pg.window()
        for it, x, y in pk:
            fr = draw.Frame(wx + x + draw.PAD_L, wy + y + draw.PAD_T + it['h'])
            draw.draw_shape(pg, it['shape'], fr, it['mark'], it['t'].name, it['lines'])
        pg.scale_footer()
    for it in tiled:
        tile_pages(doc, it, ww, wh)
    return doc


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
            pg = doc.page(title, it['t'].name)
            pg.marks = [it['mark']]
            wx, wy, _, _ = pg.window()
            # tile window in world coordinates: left edge at c*sx, top edge at toth - r*sy (world y up, origin at the pad's lower left, text block below)
            wl = c * sx
            wtop = toth - r * sy
            # part box lower left in world: (TILE_PAD, it['tx'] + TILE_PAD)
            px, py = TILE_PAD_L, it['tx'] + TILE_PAD
            pg.clip_begin(wx, wy, ww, wh)
            fr = draw.Frame(wx + (px - wl), wy + (wtop - py))
            draw.draw_shape(pg, it['shape'], fr, it['mark'], it['t'].name, it['lines'])
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
