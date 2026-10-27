"""Nesting layouts, 11 x 17 in landscape: a summary page, then pages that carry several stock pieces each. Every stock piece (a 3 x 36 in balsa
sheet is a thin strip, a stick is thinner) is drawn to one common scale, the largest at which the longest stock fits the printable width, with a
label above it (stock item, number, size, percent used, parts list). Pieces are stacked with design.NEST_GAP between them and share a page with
whatever fits beside or below them (shelf packing, first fit)."""
import design as D
from .page import Doc, LINE, HEAD_H, GAP, esc, wrap
from . import cutlist

LAB_W = 1.35            # character width used to decide where a label fits, mm per character


def _doc():
    return Doc('Nesting layouts', D.TABLOID_IN)


def summary_page(doc, tb, nest, chk):
    pg = doc.page('Stock and nesting summary', 'balsa sheet count against the order')
    m = D.PAGE_MARGIN
    y = m + 24
    pg.text(m, y, 'Stock item', 'bold')
    heads = [('order', 150), ('area + waste', 185), ('nested', 230), ('difference', 265), ('grain', 300)]
    for h, x in heads:
        pg.text(m + x, y, h, 'bold', 'end' if h != 'grain' else 'start')
    y += LINE * 1.5
    for c in chk:
        st = tb.stock[c['key']]
        o = c['order']
        a = c['summary']
        pg.text(m, y, '%s  (%s)' % (st.label, st.inch_label), 't')
        pg.text(m + 150, y, '-' if o is None else str(o), 't', 'end')
        pg.text(m + 185, y, '%.2f' % a['with_waste'] if 'with_waste' in a else '-', 't', 'end')
        pg.text(m + 230, y, str(c['nested']) if st.L is not None else 'n/a', 't', 'end')
        diff = '-' if o is None or st.L is None else '%+d' % (c['nested'] - o)
        pg.text(m + 265, y, diff, 't', 'end')
        pg.text(m + 270, y, 'grain along the length' if st.kind == 'sheet' and key_grain(st) else '', 't')
        y += LINE * 1.4
    y += LINE
    for ln in _summary_notes(tb, nest, chk):
        for w in wrap(ln, D.TABLOID_IN[0] * D.INCH - 2 * m):
            pg.text(m, y, w, 't')
            y += LINE
        y += LINE / 2


def key_grain(st):
    return st.key == 'balsa'


def _summary_notes(tb, nest, chk):
    c = next(x for x in chk if x['key'] == 'balsa')
    a = c['summary']
    return ['Balsa sheets: the nesting needs %d sheets of %.1f x %.1f mm (grain along the length, kerf %.1f mm, every plank a rectangle at its widest); the order '
            '(model/order_parts.py) carries %s. The order is an area estimate: net outline area %.0f cm2 plus the seam backing, with %.0f percent waste. The nesting also '
            'places the skeg core layers and the cut pieces as bounding rectangles, and a plank wider than half the sheet leaves its neighbour strip unusable '
            'for another plank.' % (c['nested'], tb.stock['balsa'].L, tb.stock['balsa'].W, D.KERF, c['order'], a['net'] / 100, D.WASTE * 100),
            'Sticks and sheets other than balsa agree with the order; where the nesting needs fewer stock pieces than the order lists, the order carries the spare '
            '(chine stringer, pushrod, rod packs).']


NEST_GAP = D.NEST_GAP   # clear space between stacked stock pieces; it holds the label of the piece below, mm
NEST_GAP_H = D.NEST_GAP  # clear space between stock pieces on one row, mm
STICK_LANE = 5.0        # drawn height of one stick lane, mm
STICK_GAP = 6.5         # least gap above a stick: its label line, mm
EDGE = 4.0              # room at the left and right of the strips inside the page margin, mm


def _label_fits(p, s):
    """True when a mark fits in or on a rectangular piece (inside, turned, or as a haloed label along it)."""
    w, h = p.w * s, p.h * s
    n = len(p.mark)
    tw, tw2 = n * LAB_W, n * LAB_W * 0.85
    return (w >= tw + 1 and h >= 3.4) or (h >= tw + 1 and w >= 3.4) or w >= tw2 + 0.6 or h >= tw2 + 0.6


def _tags(b, s):
    """One-letter tags for the pieces of a sheet whose mark does not fit on them, in order along the sheet: {Placed: letter}."""
    out = {}
    for p in sorted(b.placed, key=lambda p: (p.x, p.y)):
        if not p.poly and not _label_fits(p, s):
            out[p] = 'abcdefghijklmnopqrstuvwxyz'[len(out) % 26]
    return out


TIER = 2.6              # pitch of the rows of marks above and below a stick, mm


class Block:
    """One stock piece on a page: label zone above, then the drawing. w, h include the label zone (and, for a stick, the rows of marks below it)."""

    def __init__(self, key, st, b, count, s, avail_w):
        self.key, self.st, self.bin, self.count, self.s = key, st, b, count, s
        self.sheet = st.kind == 'sheet'
        self.body_w = st.L * s
        self.body_h = st.W * s if self.sheet else STICK_LANE * st.lanes
        self.w = self.body_w
        self.tags = _tags(b, s) if self.sheet else {}       # Placed -> one-letter tag
        self.lines = self._lines()
        self.marks, self.above, self.below = ([], 0, 0) if self.sheet else self._stick_marks()
        self.lh = max(NEST_GAP if self.sheet else STICK_GAP, len(self.lines) * LINE + 2.0 + self.above * TIER)
        self.h = self.lh + self.body_h + self.below * TIER + (1.5 if self.below else 0.0)

    def _stick_marks(self):
        """Pieces too short to carry 'mark length' inside get their mark alone, above the stick (first lane) or below it (last lane), in as few rows as
        fit. Returns ([(piece, side, row, centre x)], rows above, rows below)."""
        st, s = self.st, self.s
        out, ends = [], {'above': [], 'below': []}
        for p in sorted(self.bin.placed, key=lambda p: p.x):
            if p.w * s >= len('%s %.1f' % (p.mark, p.w)) * LAB_W:
                continue
            last = p.y + (p.h if st.lanes == 2 else 1) >= st.lanes
            side = 'below' if last else 'above'
            cx = (p.x + p.w / 2) * s
            half = len(p.mark) * 0.55 + 0.4
            rows = ends[side]
            for r, e in enumerate(rows):
                if cx - half >= e:
                    rows[r] = cx + half
                    break
            else:
                r = len(rows)
                rows.append(cx + half)
            out.append((p, side, r, cx))
        return out, len(ends['above']), len(ends['below'])

    def _lines(self):
        st, b = self.st, self.bin
        if self.sheet:
            used = b.used_area() / (st.L * st.W)
            head = '%s %d of %d   (%.1f x %.1f mm, %d pieces, %.0f percent used)' % (st.label, b.no, self.count, st.L, st.W, _count(b), used * 100)
            marks = []
            for p in sorted(b.placed, key=lambda p: (p.x, p.y)):
                marks += [mk for mk, _, _ in p.poly] if p.poly else [p.mark]
            out = [head] + wrap('parts: ' + ', '.join(marks), self.w)
            if self.tags:
                out += wrap('tags (pieces too small for their mark): ' + ', '.join('%s = %s' % (t, p.mark) for p, t in self.tags.items()), self.w)
            return out
        used = sum(p.w * (p.h if st.lanes == 2 else 1) for p in b.placed) / (st.L * st.lanes)
        return ['%s %d of %d   (%d pieces, %.0f percent used)' % (st.label, b.no, self.count, len(b.placed), used * 100)]


def scale_for(tb, doc):
    """Common drawing scale: the longest stock piece just fits the printable width."""
    m = D.PAGE_MARGIN
    longest = max(st.L for st in tb.stock.values() if st.L is not None)
    return (doc.size_mm[0] - 2 * m - 2 * EDGE) / longest


def content_box(doc):
    m = D.PAGE_MARGIN
    top = m + HEAD_H + GAP
    return m + EDGE, top, doc.size_mm[0] - 2 * m - 2 * EDGE, doc.size_mm[1] - m - top


def make_blocks(tb, nest, s):
    """Blocks in drawing order: balsa sheets, the other sheets (tallest first), then sticks."""
    sheets, big, sticks = [], [], []
    for key, st in tb.stock.items():
        bins = nest.bins.get(key, [])
        if st.L is None or not bins:
            continue
        bl = [Block(key, st, b, len(bins), s, 0) for b in bins]
        if st.kind == 'sheet':
            (sheets if key == 'balsa' else big).extend(bl)
        else:
            sticks.extend(bl)
    big.sort(key=lambda b: (-b.h, b.key, b.bin.no))
    return sheets + big + sticks


def place_blocks(blocks, avail_w, avail_h):
    """First-fit shelf packing. Returns pages, each a list of (block, x, y) relative to the content box."""
    pages = []
    for b in blocks:
        done = False
        for pg in pages:
            for sh in pg['shelves']:
                x = sh['x'] + (NEST_GAP_H if sh['x'] else 0.0)
                if b.h <= sh['h'] + 1e-6 and x + b.w <= avail_w + 1e-6:
                    pg['items'].append((b, x, sh['y']))
                    sh['x'] = x + b.w
                    done = True
                    break
            if done:
                break
            if pg['used'] + b.h <= avail_h + 1e-6:
                pg['shelves'].append(dict(y=pg['used'], h=b.h, x=b.w))
                pg['items'].append((b, 0.0, pg['used']))
                pg['used'] += b.h
                done = True
                break
        if not done:
            pages.append(dict(shelves=[dict(y=0.0, h=b.h, x=b.w)], items=[(b, 0.0, 0.0)], used=b.h))
    return pages


def _short(st):
    return st.label.split(',')[0]


def _range_title(items):
    """Title of a page: each stock item with the numbers of its pieces on the page."""
    by = {}
    for b, _, _ in items:
        by.setdefault(b.key, [b.st, b.count, []])[2].append(b.bin.no)
    parts = []
    for key, (st, n, nos) in by.items():
        nos = sorted(nos)
        parts.append('%s %s of %d' % (_short(st), '%d' % nos[0] if len(nos) == 1 else '%d to %d' % (nos[0], nos[-1]), n))
    t = '; '.join(parts)
    if len(t) <= 100:
        return t
    t = 'Other stock: ' + ', '.join(_short(by[k][0]) for k in by)
    return t if len(t) <= 110 else 'Other stock: sheets and sticks'


def stock_pages(doc, tb, nest):
    s = scale_for(tb, doc)
    cx, cy, cw, ch = content_box(doc)
    blocks = make_blocks(tb, nest, s)
    pages = place_blocks([b for b in blocks if b.key == 'balsa'], cw, ch) + place_blocks([b for b in blocks if b.key != 'balsa'], cw, ch)   # balsa sheets alone
    out = []
    titles = [_range_title(pg['items']) for pg in pages]
    for k, pg in enumerate(pages, 1):
        t = titles[k - 1]
        if titles.count(t) > 1:                                   # the same title on several pages: number them
            t += ' (%d of %d)' % (titles[:k].count(t), titles.count(t))
        page = doc.page(t, 'scale %.3f (about 1:%.2f), grain along the length of balsa sheets, kerf %.1f mm' % (s, 1 / s, D.KERF))
        boxes = []
        for b, x, y in pg['items']:
            _draw_block(page, b, cx + x, cy + y, boxes)
        out.append(page)
    return out


def _draw_block(pg, b, X, Y, boxes):
    st = b.st
    s = b.s
    y0 = Y + b.lh
    for i, (ln, cls) in enumerate(zip(b.lines, ['bold'] + ['t'] * 8)):
        pg.text(X, y0 - 1.8 - b.above * TIER - (len(b.lines) - 1 - i) * LINE, ln, cls)
    if b.sheet:
        pg.rect(X, y0, b.body_w, b.body_h, 'tpl', 'style="fill:#fbf6e9"')
        for p in b.bin.placed:
            _piece(pg, p, X, y0, s, b.key, boxes, (y0, y0 + b.body_h), b.tags.get(p))
        return
    lanes = st.lanes
    for ln in range(lanes):
        pg.rect(X, y0 + ln * STICK_LANE, b.body_w, STICK_LANE, 'tpl', 'style="fill:#fbf6e9"')
        if lanes == 2:
            pg.text(X - 1.2, y0 + ln * STICK_LANE + 3.6, 'AB'[ln], 'ts', 'end')
    for p in b.bin.placed:
        hh = STICK_LANE * (p.h if lanes == 2 else 1)
        yy = y0 + (p.y * STICK_LANE if lanes == 2 else 0)
        pg.rect(X + p.x * s, yy, p.w * s, hh, 'tpl', 'style="fill:#fff"')
        lab = '%s %.1f' % (p.mark, p.w)
        if p.w * s >= len(lab) * LAB_W:
            pg.text(X + p.x * s + p.w * s / 2, yy + hh / 2 + 0.9, lab, 'ts', 'middle')
    for p, side, r, cx in b.marks:
        y = (y0 - 1.0 - r * TIER) if side == 'above' else (y0 + b.body_h + 2.6 + r * TIER)
        pg.text(X + cx, y, p.mark, 'ts', 'middle')


def _count(b):
    return sum(len(p.poly) if p.poly else 1 for p in b.placed)


def _free(box, boxes):
    return not any(box[0] < o[2] and o[0] < box[2] and box[1] < o[3] and o[1] < box[3] for o in boxes)


def _halo(pg, x, y, t, anchor='middle', rot=0):
    tr = ' transform="rotate(%d %.2f %.2f)"' % (rot, x, y) if rot else ''
    pg.add('<text x="%.2f" y="%.2f" class="ts" text-anchor="%s"%s style="paint-order:stroke;stroke:#fff;stroke-width:.8px;stroke-linejoin:round">%s</text>' % (x, y, anchor, tr, esc(t)))


def _piece(pg, p, x0, y0, s, key, boxes, ylim, tag=None):
    X, Y, w, h = x0 + p.x * s, y0 + p.y * s, p.w * s, p.h * s
    if p.poly:
        for mk, inst, poly in p.poly:
            pg.poly([(x0 + x * s, y0 + y * s) for x, y in poly], 'tpl', 'style="fill:#e7efe9"')
            cx = sum(x for x, _ in poly) / len(poly)
            cy = sum(y for _, y in poly) / len(poly)
            pg.text(x0 + cx * s, y0 + cy * s, mk, 'bold', 'middle')
        pg.rect(X, Y, w, h, 'guide')
        return
    pg.rect(X, Y, w, h, 'tpl', 'style="fill:#fff"')
    if tag:                                                         # the mark is in the legend above the strip
        pg.text(X + w / 2, Y + h / 2 + 0.9, tag, 't', 'middle')
        return
    lab = p.mark
    tw, th = len(lab) * LAB_W, 2.4
    cx, cy = X + w / 2, Y + h / 2
    cands = []
    if w >= tw + 1 and h >= 3.4:
        cands.append(('t', cx, cy + 0.9, 0, (cx - tw / 2, cy - 1.5, cx + tw / 2, cy + 1.5)))
    if h >= tw + 1 and w >= 3.4:
        cands.append(('t', cx + 0.9, cy, -90, (cx - 1.5, cy - tw / 2, cx + 1.5, cy + tw / 2)))
    tw2 = len(lab) * LAB_W * 0.85
    if w >= tw2 + 0.6:
        cands.append(('h', cx, cy + 0.7, 0, (cx - tw2 / 2, cy - 1.3, cx + tw2 / 2, cy + 1.3)))
    if h >= tw2 + 0.6:
        cands.append(('h', cx + 0.7, cy, -90, (cx - 1.3, cy - tw2 / 2, cx + 1.3, cy + tw2 / 2)))
    for above in (True, False):                          # beside the piece, still inside the strip: just above or just below it, a haloed label
        yy = (Y - 0.6) if above else (Y + h + 2.4)
        if ylim[0] + 2.0 <= yy and yy + 0.6 <= ylim[1]:
            for dx in (0, 1, -1, 2, -2, 3, -3):
                d = dx * (tw2 * 0.6)
                cands.append(('h', cx + d, yy, 0, (cx + d - tw2 / 2, yy - 2.0, cx + d + tw2 / 2, yy + 0.5)))
    for dx in (0, 1, -1, 2, -2, 3, -3):                 # last resort: slide a haloed label along the piece, overhanging a neighbour if it must
        d = dx * (tw2 * 0.6)
        cands.append(('h', cx + d, cy + 0.7, 0, (cx + d - tw2 / 2, cy - 1.3, cx + d + tw2 / 2, cy + 1.3)))
    pick = next((c for c in cands if _free(c[4], boxes)), cands[0])
    kind, tx, ty, rot, box = pick
    boxes.append(box)
    if kind == 't':
        pg.text(tx, ty, lab, 't', 'middle', rot)
        if rot == 0 and w >= tw + 14 and h >= 7:
            ay = Y + h - 1.6
            pg.line(X + 2, ay, X + 9, ay, 'thin')
            pg.arrow(X + 9, ay, 1, 0)
    else:
        _halo(pg, tx, ty, lab, 'middle', rot)


def build(tb, nest):
    doc = _doc()
    chk = cutlist.check_rows(tb, nest)
    summary_page(doc, tb, nest, chk)
    stock_pages(doc, tb, nest)
    return doc
