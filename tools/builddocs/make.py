"""Builder documents: one entry point. Writes everything to out/builddocs/ from the one model (design.py through model/partmarks.py):

  cut_list.csv, Cut_List_<REV>.pdf            stock cut list, one table per stock item
  Nesting_Layouts_<REV>.pdf                   11 x 17 in, one page per stock sheet, sticks on shared pages
  Templates_Full_Size_<REV>.pdf               letter portrait, 1:1, tiled where a part is larger than a page
  Planking_Guide_<REV>.pdf                    letter portrait, sections at the frame stations and the plank tables
  Building_Board_1to2_<REV>.pdf               11 x 17 in at 1:2
  Building_Board_Full_Size_<REV>.pdf          letter portrait tiles at 1:1
  part_marks.csv                              every mark, its kind, quantity, stock and template pages
  dxf/<mark>.dxf, svg/<mark>.svg              every template outline, 1:1 mm

Run from build.py, or:  python3 -m tools.builddocs.make
"""
import csv
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import design as D
from model import hydro, partmarks
from . import nest, cutlist, layouts, templates, planking, board, export, page

OUT = os.path.join(ROOT, 'out', 'builddocs')


def main(out=None, r=None, log=print):
    """Write all builder documents. Returns a dict: files (name -> (path, pages)), balsa nested/ordered, template counts, nesting errors."""
    out = out or OUT
    os.makedirs(out, exist_ok=True)
    r = r or hydro.design()
    zd = r['deck']
    tb = partmarks.build(r)
    res = dict(files={}, marks=len(tb.index), templates=len(tb.templates), parts=len(tb.parts))
    nst = nest.nest_all(tb)                                  # raises StockError when a part is longer than its stock
    chk = cutlist.check_rows(tb, nst)
    res['stock'] = {c['key']: dict(order=c['order'], nested=c['nested'], derived=c['derived']) for c in chk}
    res['balsa'] = res['stock']['balsa']
    rev = D.REV
    p = lambda n: os.path.join(out, n)
    cutlist.csv_write(tb, nst, p('cut_list.csv'))
    res['files']['cut_list.csv'] = (p('cut_list.csv'), None)
    n = cutlist.pdf_write(tb, nst, p('Cut_List_%s.pdf' % rev))
    res['files']['Cut_List_%s.pdf' % rev] = (p('Cut_List_%s.pdf' % rev), n)
    d = layouts.build(tb, nst)
    res['files']['Nesting_Layouts_%s.pdf' % rev] = (p('Nesting_Layouts_%s.pdf' % rev), d.write(p('Nesting_Layouts_%s.pdf' % rev)))
    d = templates.build(tb)
    nn = d.write(p('Templates_Full_Size_%s.pdf' % rev))
    res['files']['Templates_Full_Size_%s.pdf' % rev] = (p('Templates_Full_Size_%s.pdf' % rev), nn)
    pages = {}
    for i, pg in enumerate(d.pages, 1):
        for mk in getattr(pg, 'marks', []):
            pages.setdefault(mk, []).append(i)
    d = planking.build(tb, nst, zd)
    res['files']['Planking_Guide_%s.pdf' % rev] = (p('Planking_Guide_%s.pdf' % rev), d.write(p('Planking_Guide_%s.pdf' % rev)))
    d = board.half_scale_doc(r)
    res['files']['Building_Board_1to2_%s.pdf' % rev] = (p('Building_Board_1to2_%s.pdf' % rev), d.write(p('Building_Board_1to2_%s.pdf' % rev)))
    d = board.full_size_doc(r)
    res['files']['Building_Board_Full_Size_%s.pdf' % rev] = (p('Building_Board_Full_Size_%s.pdf' % rev), d.write(p('Building_Board_Full_Size_%s.pdf' % rev)))
    with open(p('part_marks.csv'), 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['rev', 'mark', 'kind', 'name', 'qty', 'stock', 'template pages'])
        for mk, e in tb.index.items():
            tp = pages.get(mk) or pages.get(mk.split('.')[0], [])
            w.writerow([rev, mk, e['kind'], e['name'], e['qty'], tb.stock[e['stock']].label if e['stock'] else '', ' '.join(str(x) for x in tp)])
    res['files']['part_marks.csv'] = (p('part_marks.csv'), None)
    res['dxf'] = export.write_all(tb, out)
    if res['dxf'] < 0 and log:
        log('builder documents: DXF skipped, ezdxf is not installed (pip install ezdxf); SVG written')
    res['files']['dxf and svg'] = (os.path.join(out, 'dxf'), abs(res['dxf']))
    if log:
        for k, (path, n) in res['files'].items():
            log('builder documents: %s%s' % (path, '' if n is None else ' (%s %s)' % (n, 'pages' if k.endswith('.pdf') else 'files')))
        b = res['balsa']
        log('builder documents: balsa sheets from the nesting %d, ordered %s; %d marks, %d templates, %d cut rows' % (b['nested'], b['order'], res['marks'], res['templates'], res['parts']))
    return res


if __name__ == '__main__':
    main()
