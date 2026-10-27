"""Page library for the builder documents: a small variant of sheets/lib.Sheet with its own page size, a plain header, and the scale-check footer.

Every page of the full size templates, the building board tiles and the planking guide carries a scale bar of design.SCALE_BAR mm and a square
check box of design.CHECK_BOX mm (text 'measure: 100 mm'), so a builder can see whether the printer scaled the page. Sizes come from design.py;
only presentation constants (type sizes, line gaps) are set here.
"""
import html
import design as D
from sheets import lib, render

FONT_T = 2.4                       # type size in mm (the sheets use the same)
LINE = 3.3                         # line pitch of a text block, mm
CHAR_W = 1.25                      # average character width at FONT_T, mm (wrapping only)
HEAD_H = 14.0                      # header band height, mm
GAP = 2.0                          # gap between the header, the drawing window and the footer, mm

STYLE = """
.tpl{stroke:#111;stroke-width:.35;fill:none;stroke-linejoin:round}
.cutl{stroke:#111;stroke-width:.35;fill:none}
.guide{stroke:#555;stroke-width:.2;fill:none;stroke-dasharray:3 1.2}
.seam{stroke:#555;stroke-width:.25;fill:none;stroke-dasharray:5 1.2 1 1.2}
.axis{stroke:#444;stroke-width:.2;fill:none;stroke-dasharray:6 1.2 1 1.2}
.edge{stroke:#777;stroke-width:.2;fill:none;stroke-dasharray:.8 .8}
.reg{stroke:#000;stroke-width:.25;fill:none}
.bar{stroke:#000;stroke-width:.3;fill:#fff}
.bold{font:bold 3px Arial,Helvetica,sans-serif;fill:#111}
.big{font:bold 4.2px Arial,Helvetica,sans-serif;fill:#111}
"""


def esc(s):
    return html.escape(str(s), quote=False)


def wrap(text, width_mm):
    """Greedy word wrap to a width in mm (character width is an average, so lines are slightly short on purpose)."""
    n = max(12, int(width_mm / CHAR_W))
    lines, cur = [], ''
    for w in text.split():
        if cur and len(cur) + 1 + len(w) > n:
            lines.append(cur)
            cur = w
        else:
            cur = (cur + ' ' + w).strip()
    if cur:
        lines.append(cur)
    return lines or ['']


class Page(lib.Sheet):
    """One page. size_mm is (width, height). doc is the document name shown in the header; n and m (page n of m) are set by Doc.finish()."""

    def __init__(self, size_mm, doc, title, sub=''):
        super().__init__('', title, sub, '', D.REV)
        self.Wp, self.Hp = size_mm
        self.doc = doc
        self.n = self.m = None
        self.clip_id = 0

    # ---- clipping ----
    def clip_begin(self, x, y, w, h):
        self.clip_id += 1
        cid = 'c%d' % self.clip_id
        self.add('<clipPath id="%s"><rect x="%.2f" y="%.2f" width="%.2f" height="%.2f"/></clipPath><g clip-path="url(#%s)">' % (cid, x, y, w, h, cid))

    def clip_end(self):
        self.add('</g>')

    def text(self, x, y, t, c='t', anchor='start', rot=0):
        super().text(x, y, esc(t), c, anchor, rot)

    # ---- page parts ----
    def window(self):
        """The drawing window (x, y, w, h) between the header and the footer."""
        m = D.PAGE_MARGIN
        top = m + HEAD_H + GAP
        foot = D.CHECK_BOX + 2 * GAP + GAP
        return m, top, self.Wp - 2 * m, self.Hp - m - foot - top - GAP

    def footer_top(self):
        return self.Hp - D.PAGE_MARGIN - (D.CHECK_BOX + 2 * GAP + GAP)

    def scale_footer(self, extra=None):
        """Scale bar and check box. extra(page, x, y, w, h) may draw in the rest of the footer (tile map, notes)."""
        m = D.PAGE_MARGIN
        y0 = self.footer_top() + GAP
        bx = m
        self.rect(bx, y0, D.CHECK_BOX, D.CHECK_BOX, 'reg')
        self.text(bx + D.CHECK_BOX / 2, y0 + D.CHECK_BOX / 2 - 1, 'measure: 100 mm', 'bold', 'middle')
        self.text(bx + D.CHECK_BOX / 2, y0 + D.CHECK_BOX / 2 + LINE, 'this box is %.0f x %.0f mm' % (D.CHECK_BOX, D.CHECK_BOX), 't', 'middle')
        sx = bx + D.CHECK_BOX + 3 * GAP
        sy = y0 + D.CHECK_BOX / 2
        L = D.SCALE_BAR
        n = 10
        for i in range(n):
            self.rect(sx + L * i / n, sy - 2, L / n, 4, 'bar', 'style="fill:%s"' % ('#000' if i % 2 == 0 else '#fff'))
        for i in range(n + 1):
            self.text(sx + L * i / n, sy + 7, '%d' % (i * 10), 't', 'middle')
        self.text(sx + L / 2, sy - 5, 'scale bar, %.0f mm: it should measure %.0f mm on the paper' % (L, L), 't', 'middle')
        self.text(sx + L / 2, sy + 12, 'printed at 100 percent, no page scaling', 'ts', 'middle')
        if extra:
            ex = sx + L + 3 * GAP
            if ex < self.Wp - m - 10:
                extra(self, ex, y0, self.Wp - m - ex, D.CHECK_BOX)

    def header(self):
        m = D.PAGE_MARGIN
        W = self.Wp
        out = ['<text x="%.2f" y="%.2f" class="bold">RC Recovery Barge</text>' % (m, m + 4),
               '<text x="%.2f" y="%.2f" class="bold" text-anchor="end">REV %s</text>' % (W - m, m + 4, esc(self.rev)),
               '<text x="%.2f" y="%.2f" class="big" text-anchor="middle">%s</text>' % (W / 2, m + 4, esc(self.title)),
               '<text x="%.2f" y="%.2f" class="t">%s</text>' % (m, m + 9.5, esc(self.doc)),
               '<text x="%.2f" y="%.2f" class="t" text-anchor="end">page %s of %s</text>' % (W - m, m + 9.5, self.n if self.n is not None else '?', self.m if self.m is not None else '?')]
        if self.sub:
            out.append('<text x="%.2f" y="%.2f" class="t" text-anchor="middle">%s</text>' % (W / 2, m + 9.5, esc(self.sub)))
        out.append('<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" stroke="#000" stroke-width=".3"/>' % (m, m + HEAD_H - 1, W - m, m + HEAD_H - 1))
        return '\n'.join(out)

    def frame(self):
        return self.header()

    def svg(self):
        return ('<svg xmlns="http://www.w3.org/2000/svg" width="%smm" height="%smm" viewBox="0 0 %s %s"><style>%s</style><rect width="%s" height="%s" fill="#fff"/>' % (
            self.Wp, self.Hp, self.Wp, self.Hp, STYLE, self.Wp, self.Hp) + self.frame() + '\n'.join(self.e) + '</svg>')


class Doc:
    """A document: pages of one size, numbered 'page n of m' and written as one PDF."""

    def __init__(self, name, size_in):
        self.name = name
        self.size_in = size_in
        self.size_mm = (size_in[0] * D.INCH, size_in[1] * D.INCH)
        self.pages = []

    def page(self, title, sub=''):
        p = Page(self.size_mm, self.name, title, sub)
        self.pages.append(p)
        return p

    def finish(self):
        for i, p in enumerate(self.pages, 1):
            p.n, p.m = i, len(self.pages)

    def write(self, pdf, pngdir=None, pngs=None, prefix='p'):
        self.finish()
        render.render(self.pages, pdf, pngdir, size_in=self.size_in, pngs=pngs, prefix=prefix)
        return len(self.pages)


HTML_CSS = """
body{font:9pt Arial,Helvetica,sans-serif;color:#111;margin:0}
h1{font-size:14pt;margin:0 0 2mm}
h2{font-size:11pt;margin:5mm 0 1mm}
p{margin:1mm 0}
table{border-collapse:collapse;width:100%;margin:1mm 0 3mm}
th,td{border:.25mm solid #777;padding:.6mm 1.2mm;text-align:left;vertical-align:top;font-size:7.5pt}
th{background:#e8e8e8}
td.n,th.n{text-align:right;white-space:nowrap}
tr.grp td{background:#f1f1f1;font-weight:bold}
tr{page-break-inside:avoid}
.small{font-size:7.5pt;color:#333}
.pb{page-break-before:always}
"""


def render_html(body, pdf, size_in, title, margin_mm=(16, 12, 14, 12)):
    """Body HTML to a PDF of size_in (inches) with a plain header (project, REV, title) and a footer 'page n of m'. Returns the page count."""
    import os
    import tempfile
    from playwright.sync_api import sync_playwright
    top, right, bottom, left = margin_mm
    head = ('<div style="font:8px Arial;width:100%%;padding:0 %dmm;display:flex;justify-content:space-between"><b>%s</b><span>%s</span><b>REV %s</b></div>'
            % (left, esc(D.PROJECT), esc(title), esc(D.REV)))
    foot = ('<div style="font:8px Arial;width:100%%;padding:0 %dmm;text-align:right">page <span class="pageNumber"></span> of <span class="totalPages"></span></div>' % left)
    doc = '<html><head><meta charset="utf-8"><style>%s</style></head><body>%s</body></html>' % (HTML_CSS, body)
    with tempfile.NamedTemporaryFile('w', suffix='.html', delete=False, encoding='utf-8') as f:
        f.write(doc)
        path = f.name
    try:
        with sync_playwright() as p:
            b = p.chromium.launch()
            pg = b.new_page()
            pg.goto('file://' + path)
            pg.pdf(path=pdf, width='%sin' % size_in[0], height='%sin' % size_in[1], print_background=True, display_header_footer=True,
                   header_template=head, footer_template=foot,
                   margin=dict(top='%smm' % top, right='%smm' % right, bottom='%smm' % bottom, left='%smm' % left))
            b.close()
    finally:
        os.unlink(path)
    return pdf_pages(pdf)


def pdf_pages(pdf):
    """Page count of a PDF written by Chromium (counts the page objects, no PDF library needed)."""
    import re
    with open(pdf, 'rb') as f:
        return len(re.findall(rb'/Type\s*/Page[^s]', f.read()))
