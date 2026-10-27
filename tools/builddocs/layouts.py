"""Nesting layouts, 11 x 17 in landscape: a summary page, then one page per stock sheet or panel (to scale: rectangle, parts, marks, grain
arrows, kerf gaps) and pages of stock sticks with their cut lengths."""
import design as D
from .page import Doc, LINE, esc
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
        for w in __import__('tools.builddocs.page', fromlist=['wrap']).wrap(ln, D.TABLOID_IN[0] * D.INCH - 2 * m):
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


def sheet_pages(doc, tb, nest, key):
    st = tb.stock[key]
    bins = nest.bins.get(key, [])
    m = D.PAGE_MARGIN
    Wp = doc.size_mm[0]
    avail_w = Wp - 2 * m - 12
    avail_h = doc.size_mm[1] - 2 * m - 62
    s = min(avail_w / st.L, avail_h / st.W)
    for b in bins:
        pg = doc.page('%s %d of %d' % (esc(st.label), b.no, len(bins)), 'scale %.3f (about 1:%.1f), grain %s, kerf %.1f mm' % (
            s, 1 / s, 'along the length' if key == 'balsa' else 'any', D.KERF))
        x0, y0 = m + 6, m + 30
        pg.rect(x0, y0, st.L * s, st.W * s, 'tpl', 'style="fill:#fbf6e9"')
        for p in b.placed:
            _piece(pg, p, x0, y0, s, key)
        pg.dimh(x0, x0 + st.L * s, y0 - 5, '%.1f' % st.L, y0, y0)
        pg.dimv(y0, y0 + st.W * s, x0 - 4, '%.1f' % st.W, x0, x0)
        used = b.used_area() / (st.L * st.W)
        pg.text(x0, y0 + st.W * s + 6, '%d pieces, %.0f percent of the sheet used (bounding rectangles)' % (_count(b), used * 100), 'bold')
        _table(pg, b, x0, y0 + st.W * s + 12, Wp - m - x0)


def _count(b):
    return sum(len(p.poly) if p.poly else 1 for p in b.placed)


def _piece(pg, p, x0, y0, s, key):
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
    lab = p.mark
    if p.grain == 'x' or key != 'balsa':
        pass
    if w >= len(lab) * LAB_W + 1 and h >= 3.2:
        pg.text(X + w / 2, Y + h / 2 + 0.9, lab, 't', 'middle')
        if w >= len(lab) * LAB_W + 14 and h >= 7:
            ay = Y + h - 1.6
            pg.line(X + 2, ay, X + 9, ay, 'thin')
            pg.arrow(X + 9, ay, 1, 0)
    elif h >= len(lab) * LAB_W + 1:
        pg.text(X + w / 2 + 0.9, Y + h / 2, lab, 't', 'middle', -90)
    else:
        pg.text(X + w / 2, Y - 0.8, lab, 'ts', 'middle', -90)


def _table(pg, b, x, y, width):
    """Pieces on the sheet: mark, size, position of the lower left corner from the sheet corner (the cut list for the sheet)."""
    cols = max(1, int(width // 70))
    rows = []
    for p in sorted(b.placed, key=lambda p: (p.x, p.y)):
        if p.poly:
            for mk, inst, poly in p.poly:
                rows.append('%s (polygon pair, bounding box %.1f x %.1f at %.1f, %.1f)' % (mk, p.w, p.h, p.x, p.y))
        else:
            rows.append('%s  %.1f x %.1f  at %.1f, %.1f%s' % (p.mark, p.w, p.h, p.x, p.y, '  turned' if p.rot else ''))
    per = -(-len(rows) // cols)
    pg.text(x, y, 'pieces, lower left corner at (along the length, across)', 'ts')
    for i, r in enumerate(rows):
        pg.text(x + (i // per) * 70, y + 4 + (i % per) * 3.0, r, 'ts')


def stick_pages(doc, tb, nest, key):
    st = tb.stock[key]
    bins = nest.bins.get(key, [])
    if not bins or st.L is None:
        return
    m = D.PAGE_MARGIN
    Wp, Hp = doc.size_mm
    s = (Wp - 2 * m - 24) / st.L
    lanes = st.lanes
    pitch = 5.0 * lanes + 9
    per_page = max(1, int((Hp - 2 * m - 40) // pitch))
    npages = -(-len(bins) // per_page)
    for pi in range(npages):
        chunk = bins[pi * per_page:(pi + 1) * per_page]
        pg = doc.page('%s, sticks %d to %d of %d' % (esc(st.label), chunk[0].no, chunk[-1].no, len(bins)),
                      'scale %.3f (about 1:%.1f)%s, kerf %.1f mm' % (s, 1 / s, ', each stick rips into 2 lanes A and B' if lanes == 2 else '', D.KERF))
        y = m + 30
        for b in chunk:
            x0 = m + 12
            pg.text(m, y + 3, str(b.no), 'bold')
            for ln in range(lanes):
                pg.rect(x0, y + ln * 5.0, st.L * s, 5.0, 'tpl', 'style="fill:#fbf6e9"')
                if lanes == 2:
                    pg.text(x0 - 2, y + ln * 5.0 + 3.6, 'AB'[ln], 'ts', 'end')
            for p in b.placed:
                hh = 5.0 * (p.h if lanes == 2 else 1)
                yy = y + (p.y * 5.0 if lanes == 2 else 0)
                pg.rect(x0 + p.x * s, yy, p.w * s, hh, 'tpl', 'style="fill:#fff"')
                lab = '%s %.1f' % (p.mark, p.w)
                if p.w * s >= len(lab) * LAB_W:
                    pg.text(x0 + p.x * s + p.w * s / 2, yy + hh / 2 + 0.9, lab, 'ts', 'middle')
                else:
                    pg.text(x0 + p.x * s + p.w * s / 2, yy + hh + 3, p.mark, 'ts', 'middle', 0)
            used = sum(p.w * (p.h if lanes == 2 else 1) for p in b.placed) / (st.L * lanes)
            pg.text(x0 + st.L * s + 2, y + 3.5, '%.0f%%' % (used * 100), 'ts')
            y += pitch


def build(tb, nest):
    doc = _doc()
    chk = cutlist.check_rows(tb, nest)
    summary_page(doc, tb, nest, chk)
    for key, st in tb.stock.items():
        if st.kind == 'sheet':
            sheet_pages(doc, tb, nest, key)
        else:
            stick_pages(doc, tb, nest, key)
    return doc
