"""Wrapping table for the schedule sheets: cell text is wrapped to the column width, row height follows the tallest cell."""
import textwrap

CW = {'t': 1.22, 'ts': 1.02, 'tb': 1.3}      # approximate glyph width (mm) of each text class


def wrap(text, width_mm, c='t'):
    n = max(4, int((width_mm - 2) / CW[c]))
    return textwrap.wrap(str(text), n) or ['']


def wtable(sh, x0, y0, cols, rows, title=None, c='t', step=3.1, pad=1.2, bold_first=False, fills=None):
    """cols: [(label, width)]; rows: list of tuples of strings. Returns the y below the table."""
    if title:
        sh.text(x0, y0 - 2.6, title, 'tb')
    x = x0
    hh = 4.4
    for n, w in cols:
        sh.rect(x, y0, w, hh, 'thin', 'style="fill:#ececec"')
        sh.text(x + 1, y0 + 3.1, n, 'tb')
        x += w
    y = y0 + hh
    for ri, r in enumerate(rows):
        cells = [wrap(v, w, c) for (n, w), v in zip(cols, r)]
        h = max(len(c_) for c_ in cells) * step + pad
        x = x0
        fill = fills[ri] if fills and fills[ri] else None
        for (n, w), lines in zip(cols, cells):
            sh.rect(x, y, w, h, 'thin', ('style="fill:%s"' % fill) if fill else '')
            for i, ln in enumerate(lines):
                sh.text(x + 1, y + 2.5 + i * step, ln, 'tb' if (bold_first and x == x0) else c)
            x += w
        y += h
    return y
