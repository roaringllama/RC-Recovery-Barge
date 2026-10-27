"""A-00R: rendered views of the model as the first pages of the set. The stills come from tools/render_stills.py (out/cad/still_<view>_<REV>.png)."""
import base64, glob, os
from .lib import Sheet, W, H
import design as D

VIEWS = (('bowclose', 'Bow, close'), ('bow', 'Bow three-quarter'), ('stern', 'Stern three-quarter'), ('profile', 'Profile at the waterline'), ('under', 'Underside'))
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'out', 'cad')


def _still(view):
    p = os.path.join(OUT, 'still_%s_%s.png' % (view, D.REV))
    if not os.path.exists(p):
        cands = sorted(glob.glob(os.path.join(OUT, 'still_%s_*.png' % view)), key=os.path.getmtime)
        p = cands[-1] if cands else None
    return p


def build():
    sheets = []
    pages = [(v, t, _still(v)) for v, t in VIEWS]
    pages = [q for q in pages if q[2]]
    for i, (view, title, path) in enumerate(pages, 1):
        sh = Sheet('A-00R.%d' % i, 'Rendering, %s' % title.lower(), 'Model render, blades down, water at the waterline for batteries at X %.0f. %s.' % (D.DESIGN_BAT_X, os.path.basename(path)), 'NTS', rev=D.REV)
        # drawing area inside the frame, above the title block
        x0, y0, x1, y1 = 8.0, 25.0, W - 8.0, H - 8.0 - 30.0
        b64 = base64.b64encode(open(path, 'rb').read()).decode()
        from PIL import Image
        iw, ih = Image.open(path).size
        aw, ah = x1 - x0, y1 - y0
        s = min(aw / iw, ah / ih)
        w, h = iw * s, ih * s
        x = x0 + (aw - w) / 2; y = y0 + (ah - h) / 2
        sh.add('<image href="data:image/png;base64,%s" x="%.2f" y="%.2f" width="%.2f" height="%.2f" preserveAspectRatio="xMidYMid meet"/>' % (b64, x, y, w, h))
        sheets.append(sh)
    return sheets
