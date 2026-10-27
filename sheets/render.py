"""Render sheets to PDF and PNG with Playwright/Chromium (preinstalled; do not run playwright install)."""
import os, tempfile
from playwright.sync_api import sync_playwright
from . import lib


def render(sheets, pdf=None, pngdir=None):
    html = ('<html><head><style>@page{size:17in 11in;margin:0}body{margin:0}'
            '.pg{width:431.8mm;height:279.4mm;page-break-after:always;overflow:hidden}' + lib.CSS + '</style></head><body>')
    for sh in sheets:
        html += '<div class="pg">' + sh.svg() + '</div>'
    html += '</body></html>'
    with tempfile.NamedTemporaryFile('w', suffix='.html', delete=False) as f:
        f.write(html)
        path = f.name
    try:
        with sync_playwright() as p:
            b = p.chromium.launch()
            pg = b.new_page(viewport={'width': 1632, 'height': 1056})
            pg.goto('file://' + path)
            pg.wait_for_timeout(400)
            if pdf:
                pg.pdf(path=pdf, width='17in', height='11in', print_background=True, prefer_css_page_size=True)
            if pngdir:
                for i, e in enumerate(pg.query_selector_all('.pg')):
                    e.screenshot(path=os.path.join(pngdir, 'p%d.png' % (i + 1)))
            b.close()
    finally:
        os.unlink(path)
