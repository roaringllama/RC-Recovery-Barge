"""Stock cut list: one table per stock item (PDF, letter portrait) and one CSV. Columns: mark, qty, length, width or height, thickness, end angle 1,
end angle 2 (90 where square), grain, stock piece numbers from the nesting, note. Totals per stock item are checked against model/order_parts.py."""
import csv
import math
import design as D
from model import order_parts as OP
from . import page

COLS = ['mark', 'qty', 'length mm', 'width or height mm', 'thickness mm', 'end angle 1 deg', 'end angle 2 deg', 'grain', 'stock piece', 'note']


def order_counts():
    """Pieces of each stock item on the order, from model/order_parts.py: {stock key: (count, order text)}."""
    hq = OP.hull_quantities()
    out = {'balsa': hq['balsa'], 'tri': hq['stock'], 'chine': hq['chine'], 'cord': hq['cord'], 'g10': hq['g10']}
    for ln in OP.lines():
        if ln['pkey'] == 'ply' and ln['group'] == 'Hull materials':
            out['ply'] = (ln['qty'], ln['qty_note'] or ln['item'])
        if ln['pkey'] == 'post_rod':
            out['rod3'] = (ln['qty'] * D.ROD_PACK, 'pack of %d' % D.ROD_PACK)
        if ln['pkey'] == 'post_tube':
            out['tube4'] = (ln['qty'] * D.ROD_PACK, 'pack of %d' % D.ROD_PACK)
        if ln['pkey'] == 'pushrod':
            out['rod256'] = (ln['qty'], ln['qty_note'])
    return out


def piece_label(nest, key, mark, inst):
    w = nest.where.get((mark, inst))
    if not w or not w[1]:
        return '-'
    st = nest.bins[key]
    b = st[w[1] - 1]
    for pl in b.placed:
        if pl.mark == mark and pl.inst == inst and key == 'tri' and pl.h == 1:
            return '%d%s' % (b.no, 'AB'[int(pl.y)])
    return str(w[1])


def compress(labels):
    """'3, 3, 4' becomes '3 x2, 4'."""
    out, seen = [], {}
    for lb in labels:
        seen[lb] = seen.get(lb, 0) + 1
    for lb, n in seen.items():
        out.append(lb if n == 1 else '%s x%d' % (lb, n))
    return ', '.join(out)


def grain_text(stock_key, part):
    if stock_key in ('g10', 'rod3', 'tube4', 'bar4', 'bush', 'cord', 'rod256', 'ply15'):
        return 'n/a'
    return 'length'


def rows(tb, nest):
    """{stock key: [row dict]} with rows in table order (by group, then mark)."""
    out = {}
    for key in tb.stock:
        ps = tb.parts_for(key)
        if not ps:
            continue
        rs = []
        order = []
        for p in ps:
            if p.group not in order:
                order.append(p.group)
        ps = sorted(ps, key=lambda p: order.index(p.group))          # stable: parts of one group stay together, in creation order
        for p in ps:
            labels = [piece_label(nest, key, p.mark, i) for i in range(1, p.qty + 1)]
            st = tb.stock[key]
            wd = p.width if p.width is not None else st.section
            rs.append(dict(stock=key, group=p.group, mark=p.mark, qty=p.qty, length=p.length, width=wd, t=p.t,
                           a1=p.a1 if p.a1 is not None else 90.0, a2=p.a2 if p.a2 is not None else 90.0, grain=grain_text(key, p),
                           pieces=compress(labels), note=p.note, joint=p.joint))
        out[key] = rs
    return out


def area_summary(tb, nest, key, rs):
    """Per stock totals: the same arithmetic as order_parts (net quantity x (1 + WASTE) / stock) next to the nesting."""
    st = tb.stock[key]
    w = 1 + D.WASTE
    nested = nest.count(key)
    if st.kind == 'sheet':
        rect = sum(r['qty'] * r['length'] * r['width'] for r in rs)
        net = 0.0
        for p in tb.parts_for(key):
            net += p.qty * p.length * p.width
        # net outline area where the template has one
        net_poly = 0.0
        for mk, t in tb.templates.items():
            if t.stock == key:
                net_poly += t.qty * t.shape.area()
        sheet = st.L * st.W
        return dict(unit='sheets', rect=rect, net=net_poly, with_waste=rect * w / sheet, by_net=net_poly * w / sheet, nested=nested)
    if st.L is None:
        return dict(unit='pieces', length=sum(r['qty'] * r['length'] for r in rs), nested=nested)
    total = sum(r['qty'] * r['length'] for r in rs)
    wedge = sum(r['qty'] * r['length'] for r in rs if r['joint'] and r['joint'] == 'J4')
    lanes = st.lanes
    eff = (total - wedge) / lanes + wedge                 # a rip makes two lanes; a wedge takes a whole stick
    return dict(unit='sticks', length=total, wedge=wedge, with_waste=eff * w / st.L, nested=nested)


def check_rows(tb, nest):
    """Cut list versus order: one dict per stock item. 'derived' is the order_parts arithmetic applied to the cut list pieces."""
    oc = order_counts()
    rs = rows(tb, nest)
    out = []
    for key, st in tb.stock.items():
        if key not in rs:
            continue
        a = area_summary(tb, nest, key, rs[key])
        derived = math.ceil(a['with_waste'] - 1e-9) if 'with_waste' in a else None
        o = oc.get(key)
        out.append(dict(key=key, label=st.label, order=o[0] if o else None, order_note=o[1] if o else 'not on the order list',
                        derived=derived, nested=a['nested'], summary=a))
    return out


def csv_write(tb, nest, path):
    rs = rows(tb, nest)
    with open(path, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['rev', 'stock'] + COLS)
        for key, lst in rs.items():
            for r in lst:
                w.writerow([D.REV, tb.stock[key].label, r['mark'], r['qty'], '%.2f' % r['length'], '%.2f' % r['width'], '%.3f' % r['t'], '%.2f' % r['a1'], '%.2f' % r['a2'],
                            r['grain'], r['pieces'], r['note']])
    return path


def pdf_write(tb, nest, path):
    from .page import esc
    rs = rows(tb, nest)
    chk = {c['key']: c for c in check_rows(tb, nest)}
    body = ['<h1>Stock cut list</h1><p class="small">%s. The length is along the grain (balsa) or the stick. End angles are 90 where square; a mitered end is the cut angle from square, '
            'measured as 90 minus half the corner turn. Kerf %.1f mm in the nesting. Stock piece numbers refer to the nesting layouts (Balsa sheet 7, stick 3, lane A or B).</p>' % (
                esc(D.PROJECT), D.KERF)]
    first = True
    for key, lst in rs.items():
        st = tb.stock[key]
        c = chk[key]
        a = c['summary']
        body.append('<h2%s>%s  [%s]</h2>' % ('' if first else ' class="pb"', esc(st.label), esc(st.inch_label)))
        first = False
        if a['unit'] == 'sheets':
            tot = ('Total cut area %.0f cm2 (bounding rectangles; %.0f cm2 net outlines). With %.0f percent waste: %.2f sheets of %.1f x %.1f mm (outlines: %.2f). '
                   % (a['rect'] / 100, a['net'] / 100, D.WASTE * 100, a['with_waste'], st.L, st.W, a['by_net']))
        elif a['unit'] == 'sticks':
            tot = 'Total length %.0f mm. With %.0f percent waste: %.2f sticks of %.1f mm. ' % (a['length'], D.WASTE * 100, a['with_waste'], st.L)
        else:
            tot = 'Total length %.0f mm; the stock length is not defined in the model. ' % a['length']
        tot += 'Nested: %d stock piece%s. On the order: %s.' % (c['nested'], '' if c['nested'] == 1 else 's', ('%s' % c['order'] if c['order'] is not None else 'not on the order list'))
        if st.note:
            tot += ' ' + st.note + '.'
        body.append('<p class="small">%s</p>' % esc(tot))
        body.append('<table><tr>%s</tr>' % ''.join('<th%s>%s</th>' % (' class="n"' if i in (1, 2, 3, 4, 5, 6) else '', esc(h)) for i, h in enumerate(COLS)))
        grp = None
        for r in lst:
            if r['group'] != grp:
                grp = r['group']
                body.append('<tr class="grp"><td colspan="%d">%s</td></tr>' % (len(COLS), esc(grp)))
            body.append('<tr><td><b>%s</b></td><td class="n">%d</td><td class="n">%.2f</td><td class="n">%.2f</td><td class="n">%.3f</td><td class="n">%.2f</td><td class="n">%.2f</td><td>%s</td><td>%s</td><td>%s</td></tr>' % (
                esc(r['mark']), r['qty'], r['length'], r['width'], r['t'], r['a1'], r['a2'], esc(r['grain']), esc(r['pieces']), esc(r['note'])))
        body.append('</table>')
    return page.render_html('\n'.join(body), path, D.LETTER_IN, 'Stock cut list')
