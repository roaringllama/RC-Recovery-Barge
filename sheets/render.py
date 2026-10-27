"""Render sheets to PDF and PNG with Playwright/Chromium (preinstalled; do not run playwright install).

The page size defaults to the 17 x 11 in drawing sheet; the builder documents pass their own size (letter portrait or landscape, 11 x 17 landscape).
"""
import os, tempfile
from playwright.sync_api import sync_playwright
from . import lib

MM_IN = 25.4
PX_IN = 96


def render(sheets, pdf=None, pngdir=None, size_in=None, pngs=None, prefix='p'):
    """sheets: objects with .svg(). size_in: (width, height) in inches, default 17 x 11. pngs: None for every page, or a list of 1-based page numbers."""
    wi, hi = size_in or (lib.W / MM_IN, lib.H / MM_IN)
    wi, hi = round(wi, 4), round(hi, 4)
    html = ('<html><head><style>@page{size:%sin %sin;margin:0}body{margin:0}'
            '.pg{width:%.2fmm;height:%.2fmm;page-break-after:always;overflow:hidden}' % (wi, hi, wi * MM_IN, hi * MM_IN) + lib.CSS + '</style></head><body>')
    for sh in sheets:
        html += '<div class="pg">' + sh.svg() + '</div>'
    html += '</body></html>'
    with tempfile.NamedTemporaryFile('w', suffix='.html', delete=False) as f:
        f.write(html)
        path = f.name
    try:
        with sync_playwright() as p:
            b = p.chromium.launch()
            pg = b.new_page(viewport={'width': int(wi * PX_IN), 'height': int(hi * PX_IN)})
            pg.goto('file://' + path)
            pg.wait_for_timeout(400)
            if pdf:
                pg.pdf(path=pdf, width='%sin' % wi, height='%sin' % hi, print_background=True, prefer_css_page_size=True)
            if pngdir:
                for i, e in enumerate(pg.query_selector_all('.pg')):
                    if pngs is None or (i + 1) in pngs:
                        e.screenshot(path=os.path.join(pngdir, '%s%d.png' % (prefix, i + 1)))
            b.close()
    finally:
        os.unlink(path)
