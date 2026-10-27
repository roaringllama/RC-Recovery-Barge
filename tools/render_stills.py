"""Render the four preset stills of the viewer with Playwright (Chromium).

Serves the repository root with python http.server on a free port, opens tools/viewer/index.html with blades down and water on,
and writes out/cad/still_<preset>_<REV>.png at STILL_W x STILL_H.

    python3 -m tools.render_stills
"""
import functools
import http.server
import os
import socket
import sys
import threading

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import design as D

OUT_DIR = os.path.join(ROOT, 'out', 'cad')
PRESETS = ('bow', 'stern', 'profile', 'under', 'bowclose')
from sheets.lib import W as _SW, H as _SH
# same aspect as the drawing area of a sheet (inside the frame, above the title block), so the render fills an A-00R page
STILL_W = 1920
STILL_H = int(round(STILL_W * (_SH - 8.0 - 30.0 - 25.0) / (_SW - 16.0)))
LOAD_MS = 120000
SETTLE_MS = 1500


class _Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def _serve():
    s = socket.socket()
    s.bind(('127.0.0.1', 0))
    port = s.getsockname()[1]
    s.close()
    handler = functools.partial(_Quiet, directory=ROOT)
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', port), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, port


def render(out_dir=OUT_DIR, extra='', suffix='', log=print):
    from playwright.sync_api import sync_playwright
    srv, port = _serve()
    paths = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(args=['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
            page = browser.new_page(viewport={'width': STILL_W, 'height': STILL_H})
            logs = []
            page.on('console', lambda m: logs.append(m.text))
            page.on('pageerror', lambda e: logs.append('PAGEERROR ' + str(e)))
            url = 'http://127.0.0.1:%d/tools/viewer/index.html?blades=down&water=1&ui=0&zoom=0.78&rev=%s%s' % (port, D.REV, extra)
            page.goto(url, wait_until='commit', timeout=LOAD_MS)
            page.wait_for_function('window.__viewer && (window.__viewer.ready || window.__viewer.error)', timeout=LOAD_MS)
            err = page.evaluate('window.__viewer.error || null')
            if err:
                raise RuntimeError('viewer: %s %s' % (err, logs[-3:]))
            for pr in PRESETS:
                page.evaluate('p => { const v = window.__viewer; v.state.blades = true; v.state.water = true; v.state.deck = true; v.applyState(); v.setView(p, false); }', pr)
                page.wait_for_timeout(SETTLE_MS)
                path = os.path.join(out_dir, 'still_%s_%s%s.png' % (pr, D.REV, suffix))
                page.screenshot(path=path, timeout=LOAD_MS)
                paths.append(path)
            browser.close()
    finally:
        srv.shutdown()
    log('STILLS wrote %d images to %s' % (len(paths), out_dir))
    return paths


if __name__ == '__main__':
    render()
