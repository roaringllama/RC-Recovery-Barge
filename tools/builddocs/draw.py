"""Draw one Shape (a flat part) on a Page at a given scale: outline, cut-outs, guides, grain arrow, mark and dimensions. Used by the full size
templates (scale 1), the tiled pages and the building board; the DXF and SVG exporters read the same Shape."""
import math
from .page import LINE, esc, wrap

PAD_L = 11.0           # room left of the part for the height dimension, mm
PAD_T = 15.0           # room above the part for the width dimension and the mark, mm
PAD_R = 4.0
GRAIN_MIN = 18.0       # shortest part (along the grain) that carries an arrow inside it, mm
ARROW = 28.0           # grain arrow length when it fits, mm


class Frame:
    """Where a part sits on the page: lower left corner of its bounding box at page (ox, oy_bottom); y runs up in the part, down on the page."""

    def __init__(self, ox, oy_bottom, scale=1.0):
        self.ox, self.oy, self.sc = ox, oy_bottom, scale

    def p(self, x, y):
        return self.ox + x * self.sc, self.oy - y * self.sc


def info_lines(width_mm, lines):
    out = []
    for ln in lines:
        out += wrap(ln, width_mm)
    return out


def block_height(width_mm, lines):
    return len(info_lines(width_mm, lines)) * LINE


def draw_shape(pg, shape, fr, mark, name, text_lines, dims=True, show_mark=True, text_w=None, vdim=True):
    """Draw the shape. name '' leaves the name out of the header (the packed templates put it in the text block); text_w is the wrap width of the text block
    (default: the part width, at least 70 mm); vdim False leaves out the height dimension (the size is also in the text block). Returns the page y below the part's text block."""
    sc = fr.sc
    P = fr.p
    n0 = len(pg.e)
    x0, y0, x1, y1 = shape.bbox()
    # shape coordinates are normalised so the bbox starts at 0, 0; be safe for others
    ox, oy = fr.ox - x0 * sc, fr.oy + y0 * sc
    fr2 = Frame(ox, oy, sc)
    P = fr2.p
    w, h = (x1 - x0), (y1 - y0)
    # planks: faint fill alternate to show the stock pieces, outline on top
    if shape.planks and len(shape.planks) > 1:
        for k, pk in enumerate(shape.planks):
            if k % 2:
                pg.poly([P(*q) for q in pk], 'guide', 'style="fill:#efefef;stroke:none"')
    pg.poly([P(*q) for q in shape.outline], 'tpl')
    for c in shape.cuts:
        if c[0] == 'circle':
            cx, cy = P(*c[1])
            pg.circ(cx, cy, c[2] * sc, 'cutl')
            pg.line(cx - 1.5, cy, cx + 1.5, cy, 'thin')
            pg.line(cx, cy - 1.5, cx, cy + 1.5, 'thin')
            if dims:
                txt = 'dia %.1f at %.1f, %.1f' % (2 * c[2], c[1][0] - x0, c[1][1] - y0)
                edge = P(x1, y0)[0]
                if cx + c[2] * sc + 1.2 + len(txt) * 1.3 <= edge:
                    pg.text(cx + c[2] * sc + 1.2, cy - 0.8, txt, 't')
                elif cx + c[2] * sc + 3.8 <= edge:                      # a hole near the right edge: the label runs up the page beside it
                    pg.text(cx + c[2] * sc + 3.0, cy, txt, 't', 'middle', -90)
                else:
                    pg.text(cx - c[2] * sc - 1.2, cy - 0.8, txt, 't', 'end')
        else:
            pg.poly([P(*q) for q in c[1]], 'cutl')
            if dims:
                xs = [q[0] for q in c[1]]
                ys = [q[1] for q in c[1]]
                qx, qy = P(min(xs), max(ys))
                pg.text(qx, qy - 0.8, '%.1f x %.1f' % (max(xs) - min(xs), max(ys) - min(ys)), 'ts')
    for g in shape.guides:
        st = g.get('style', 'guide')
        cls = {'seam': 'seam', 'axis': 'axis', 'edge': 'edge', 'slot': 'cutl', 'station': 'guide', 'opening': 'guide', 'groove': 'guide', 'slope': 'axis'}.get(st, 'guide')
        if g['kind'] == 'line':
            a, b = P(*g['p']), P(*g['q'])
            pg.line(a[0], a[1], b[0], b[1], cls)
            if g.get('text'):
                pg.text(a[0] + (b[0] - a[0]) * 0.12 + 0.8, a[1] + (b[1] - a[1]) * 0.12 - 0.8, g['text'], 'ts')
        elif g['kind'] == 'circle':
            c = P(*g['c'])
            pg.circ(c[0], c[1], g['r'] * sc, cls)
            if g.get('text'):
                pg.text(c[0] + g['r'] * sc + 1, c[1], g['text'], 'ts')
        else:
            pts = [P(*q) for q in g['pts']]
            pg.poly(pts, cls)
            if g.get('text'):
                pg.text(min(q[0] for q in pts) + 1, min(q[1] for q in pts) + 3, g['text'], 'ts')
    for px, py, txt in shape.points:
        a = P(px, py)
        pg.line(a[0] - 2, a[1], a[0] + 2, a[1], 'thin')
        pg.line(a[0], a[1] - 2, a[0], a[1] + 2, 'thin')
        pg.text(a[0] + 2.5, a[1] - 1, txt, 'ts')
    # grain arrow
    along = w if shape.grain == 'x' else h
    across = h if shape.grain == 'x' else w
    L = min(ARROW, along * 0.6 * sc)
    if along * sc >= GRAIN_MIN and across * sc >= 5:
        lx, ly = label_point(shape)
        cx, cy = P(lx, ly)
        _grain(pg, cx, cy, L, shape.grain, _text_boxes(pg.e[n0:]))
    else:
        # outside, to the right of the part
        a = P(x1, y0 + h / 2)
        _grain(pg, a[0] + 8, a[1], 10, shape.grain, _text_boxes(pg.e[n0:]))
    top = P(x0, y1)[1]
    left = P(x0, y1)[0]
    right = P(x1, y1)[0]
    bottom = P(x0, y0)[1]
    if dims:
        pg.dimh(left, right, top - 5, '%.1f' % w, top, top, tdy=-0.9)
        if vdim:
            pg.dimv(top, bottom, left - 5, '%.1f' % h, left, left, tdx=-0.9)
    if show_mark:
        pg.text(left, top - 9.5, mark, 'big')
        if name:
            pg.text(left + 3 + 2.6 * len(mark), top - 9.5, name, 't')
    bw = text_w or max(right - left, 70)
    y = bottom + 7
    ext = extent(pg.e[n0:])                      # the text block starts below everything drawn so far (a notch or hole that runs past the bottom edge)
    if ext:
        y = max(y, ext[3] + 4.5)
    for ln in info_lines(bw, text_lines):
        pg.text(left, y, ln, 't')
        y += LINE
    return y


def _inside(poly, x, y):
    n, c = len(poly), False
    for i in range(n):
        (ax, ay), (bx, by) = poly[i], poly[(i + 1) % n]
        if (ay > y) != (by > y) and x < ax + (y - ay) * (bx - ax) / (by - ay):
            c = not c
    return c


def label_point(shape):
    """A point well inside the largest plank (or the outline): the area centroid, else the best of a grid of candidates."""
    poly = max(shape.planks, key=lambda p: _area(p)) if shape.planks else shape.outline
    a = _area(poly)
    cx = cy = 0.0
    for i in range(len(poly)):
        (x0, y0), (x1, y1) = poly[i], poly[(i + 1) % len(poly)]
        k = x0 * y1 - x1 * y0
        cx += (x0 + x1) * k
        cy += (y0 + y1) * k
    s = sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1] for i in range(len(poly)))
    cx, cy = cx / (3 * s), cy / (3 * s)
    holes = [c for c in shape.cuts if c[0] == 'circle']
    ok = lambda x, y: _inside(poly, x, y) and not any((x - c[1][0]) ** 2 + (y - c[1][1]) ** 2 < (c[2] + 3) ** 2 for c in holes)
    if ok(cx, cy):
        return cx, cy
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    best = None
    for i in range(1, 12):
        for j in range(1, 12):
            x, y = min(xs) + (max(xs) - min(xs)) * i / 12, min(ys) + (max(ys) - min(ys)) * j / 12
            if ok(x, y):
                d = (x - cx) ** 2 + (y - cy) ** 2
                if best is None or d < best[0]:
                    best = (d, x, y)
    return (best[1], best[2]) if best else (cx, cy)


def _area(poly):
    return abs(sum(p[0] * q[1] - q[0] * p[1] for p, q in zip(poly, poly[1:] + poly[:1]))) / 2


def _text_boxes(elements):
    return [extent([e]) for e in elements if e.startswith('<text')]


def _hit(box, boxes):
    return any(box[0] < o[2] and o[0] < box[2] and box[1] < o[3] and o[1] < box[3] for o in boxes)


def _grain(pg, cx, cy, L, grain, boxes=()):
    """The grain arrow with its word beside it: above (right of, for a vertical arrow) when that is clear of the text already drawn, else the other side."""
    dx, dy = (L / 2, 0) if grain == 'x' else (0, L / 2)
    pg.line(cx - dx, cy - dy, cx + dx, cy + dy, 'thin')
    pg.arrow(cx + dx, cy + dy, dx, dy)
    pg.arrow(cx - dx, cy - dy, -dx, -dy)
    w = 5 * TEXT_W['ts']
    if grain == 'x':
        spots = [(cx, y) for y in (cy - 1.3, cy + 3.3)] + [(cx + d, y) for d in (-9.0, 9.0) for y in (cy - 1.3, cy + 3.3)]
        pick = next((q for q in spots if not _hit((q[0] - w / 2, q[1] - TEXT_H['ts'], q[0] + w / 2, q[1] + 0.6), boxes)), spots[0])
        pg.text(pick[0], pick[1], 'grain', 'ts', 'middle')
    else:
        spots = [(x, y) for y in (cy, cy + 6.0, cy - 6.0) for x in (cx + 1.3, cx - 0.9)]
        pick = next((q for q in spots if not _hit(((q[0] - 0.8 * TEXT_H['ts']) if q[0] > cx else (q[0] - TEXT_H['ts']), q[1] - w, (q[0] - 0.8 * TEXT_H['ts'] if q[0] > cx else q[0] - TEXT_H['ts']) + 1.3 * TEXT_H['ts'], q[1]), boxes)), spots[0])
        pg.text(pick[0], pick[1], 'grain', 'ts', 'start', -90)


# ---- measuring a drawing ----------------------------------------------------------------------------------------------------------------------
TEXT_W = {'t': 1.3, 'ts': 1.1, 'bold': 1.8, 'big': 2.6}      # generous average character width per text class, mm
TEXT_H = {'t': 2.4, 'ts': 2.0, 'bold': 3.0, 'big': 4.2}      # type size, mm
_NUM = r'(-?[\d.]+)'


def extent(elements):
    """Bounding box (x0, y0, x1, y1) of the SVG element strings a Page collected: lines, rects, polygons, circles and text (width estimated from the
    character count, so it errs large). None for an empty list."""
    import re
    xs, ys = [], []

    def pt(x, y):
        xs.append(x)
        ys.append(y)
    for e in elements:
        if e.startswith('<line'):
            a = [float(v) for v in re.findall(r'(?:x1|y1|x2|y2)="' + _NUM + '"', e)]
            pt(a[0], a[1])
            pt(a[2], a[3])
        elif e.startswith('<rect'):
            m = re.search(r'x="' + _NUM + r'" y="' + _NUM + r'" width="' + _NUM + r'" height="' + _NUM + '"', e)
            x, y, w, h = (float(v) for v in m.groups())
            pt(x, y)
            pt(x + w, y + h)
        elif e.startswith('<polygon'):
            for a, b in re.findall(_NUM + ',' + _NUM, re.search(r'points="([^"]*)"', e).group(1)):
                pt(float(a), float(b))
        elif e.startswith('<circle'):
            m = re.search(r'cx="' + _NUM + r'" cy="' + _NUM + r'" r="' + _NUM + '"', e)
            cx, cy, r = (float(v) for v in m.groups())
            pt(cx - r, cy - r)
            pt(cx + r, cy + r)
        elif e.startswith('<text'):
            m = re.search(r'x="' + _NUM + r'" y="' + _NUM + r'" class="(\w+)" text-anchor="(\w+)"(?: transform="rotate\(' + _NUM + r' [^"]*\)")?[^>]*>([^<]*)<', e)
            x, y, c, anc, rot, t = m.groups()
            x, y = float(x), float(y)
            n = len(t.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>'))
            w, h = n * TEXT_W.get(c, 1.3), TEXT_H.get(c, 2.4)
            lo, hi = {'start': (0, w), 'middle': (-w / 2, w / 2), 'end': (-w, 0)}[anc]
            if rot and abs(float(rot)) > 1:
                if float(rot) < 0:                  # turned -90: the text runs up the page from its anchor
                    lo, hi = -hi, -lo
                pt(x - h, y + lo)
                pt(x + 0.3 * h, y + hi)
            else:
                pt(x + lo, y - h)
                pt(x + hi, y + 0.3 * h)
    return (min(xs), min(ys), max(xs), max(ys)) if xs else None
