"""DXF and SVG of every template outline at 1:1 in millimetres: out/builddocs/dxf/<mark>.dxf (ezdxf) and out/builddocs/svg/<mark>.svg.
Layers: CUT (outline), HOLES (cut-outs), GUIDE (seams, stations, lines that are not cut), TEXT (mark, REV, notes). y runs up in the DXF, down in the SVG."""
import os
import design as D
from .page import esc

GUIDE_LAYER = {'seam': 'SEAM', 'axis': 'AXIS', 'edge': 'GUIDE', 'slot': 'HOLES'}
TEXT_H = 2.5


def dxf_write(t, path):
    import ezdxf
    sh = t.shape
    doc = ezdxf.new('R2010', setup=False)
    doc.units = ezdxf.units.MM
    for name, color in (('CUT', 7), ('HOLES', 1), ('GUIDE', 8), ('SEAM', 5), ('AXIS', 3), ('TEXT', 2)):
        doc.layers.add(name, color=color)
    msp = doc.modelspace()
    msp.add_lwpolyline(sh.outline, close=True, dxfattribs={'layer': 'CUT'})
    for c in sh.cuts:
        if c[0] == 'circle':
            msp.add_circle(c[1], c[2], dxfattribs={'layer': 'HOLES'})
        else:
            msp.add_lwpolyline(c[1], close=True, dxfattribs={'layer': 'HOLES'})
    for g in sh.guides:
        layer = GUIDE_LAYER.get(g.get('style'), 'GUIDE')
        if g['kind'] == 'line':
            msp.add_line(g['p'], g['q'], dxfattribs={'layer': layer})
        elif g['kind'] == 'circle':
            msp.add_circle(g['c'], g['r'], dxfattribs={'layer': layer})
        else:
            msp.add_lwpolyline(g['pts'], close=True, dxfattribs={'layer': layer})
    for x, y, txt in sh.points:
        msp.add_line((x - 2, y), (x + 2, y), dxfattribs={'layer': 'GUIDE'})
        msp.add_line((x, y - 2), (x, y + 2), dxfattribs={'layer': 'GUIDE'})
        msp.add_text(txt, height=TEXT_H, dxfattribs={'layer': 'TEXT', 'insert': (x + 2.5, y)})
    x0, y0, x1, y1 = sh.bbox()
    msp.add_text('%s  REV %s  %s, qty %d, thickness %.3g' % (t.mark, D.REV, t.name, t.qty, t.t), height=TEXT_H, dxfattribs={'layer': 'TEXT', 'insert': (x0, y0 - 2 * TEXT_H)})
    doc.saveas(path)


def svg_write(t, path):
    sh = t.shape
    x0, y0, x1, y1 = sh.bbox()
    pad = 6.0
    w, h = x1 - x0 + 2 * pad, y1 - y0 + 2 * pad + 2 * TEXT_H
    fx = lambda x: x - x0 + pad
    fy = lambda y: (y1 - y) + pad
    pts = lambda p: ' '.join('%.3f,%.3f' % (fx(a), fy(b)) for a, b in p)
    o = ['<svg xmlns="http://www.w3.org/2000/svg" width="%.3fmm" height="%.3fmm" viewBox="0 0 %.3f %.3f">' % (w, h, w, h),
         '<title>%s, REV %s, 1:1 millimetres</title>' % (esc(t.mark), esc(D.REV)),
         '<polygon points="%s" fill="none" stroke="#000" stroke-width="0.3"/>' % pts(sh.outline)]
    for c in sh.cuts:
        if c[0] == 'circle':
            o.append('<circle cx="%.3f" cy="%.3f" r="%.3f" fill="none" stroke="#c00" stroke-width="0.3"/>' % (fx(c[1][0]), fy(c[1][1]), c[2]))
        else:
            o.append('<polygon points="%s" fill="none" stroke="#c00" stroke-width="0.3"/>' % pts(c[1]))
    for g in sh.guides:
        st = 'fill="none" stroke="#777" stroke-width="0.2" stroke-dasharray="3 1.2"'
        if g['kind'] == 'line':
            o.append('<line x1="%.3f" y1="%.3f" x2="%.3f" y2="%.3f" %s/>' % (fx(g['p'][0]), fy(g['p'][1]), fx(g['q'][0]), fy(g['q'][1]), st))
        elif g['kind'] == 'circle':
            o.append('<circle cx="%.3f" cy="%.3f" r="%.3f" %s/>' % (fx(g['c'][0]), fy(g['c'][1]), g['r'], st))
        else:
            o.append('<polygon points="%s" %s/>' % (pts(g['pts']), st))
    for x, y, txt in sh.points:
        o.append('<path d="M%.3f %.3fh4M%.3f %.3fv4" stroke="#000" stroke-width="0.2" fill="none" transform="translate(-2 -2)"/>' % (fx(x), fy(y) + 2, fx(x) + 2, fy(y)))
    o.append('<text x="%.3f" y="%.3f" font-family="Arial" font-size="%.1f">%s  REV %s  %s</text>' % (pad, h - TEXT_H * 0.6, TEXT_H, esc(t.mark), esc(D.REV), esc(t.name)))
    o.append('</svg>')
    with open(path, 'w') as f:
        f.write('\n'.join(o))


def write_all(tb, out_dir):
    dx, sv = os.path.join(out_dir, 'dxf'), os.path.join(out_dir, 'svg')
    os.makedirs(dx, exist_ok=True)
    os.makedirs(sv, exist_ok=True)
    have_dxf = True
    try:
        import ezdxf  # noqa: F401
    except ImportError:
        have_dxf = False
    for mk, t in tb.templates.items():
        if have_dxf:
            dxf_write(t, os.path.join(dx, mk + '.dxf'))
        svg_write(t, os.path.join(sv, mk + '.svg'))
    return len(tb.templates) if have_dxf else -len(tb.templates)          # negative: SVG only, ezdxf is not installed
