"""A-000 Cover, drawing index, design basis, references and open items (two pages). The open items are parsed from design.py."""
import re
from .lib import *
from .wtbl import wtable, wrap
from .tbl import para
import design as D
from model import hydro, references as REF, schedules as S

SELF = ('A-000', 'Cover, index, basis, open items', 'none')
CONTENTS = 'Cover, drawing index, design basis, references, open items from design.py'
TAGNOTE = {'APPROVED': 'the owner has decided it', 'PENDING': 'the owner has not decided it', 'ASSUMED': 'no published source; this design proposes it',
           'ESTIMATE': 'a weight guessed; weigh the real part'}


def _clean(text):
    t = text.replace('section tag: ESTIMATE', 'weight list in this section is estimated')
    t = re.sub(r'\s*[,;]?\s*\b(PENDING|ASSUMED|ESTIMATE)\b', '', t)
    t = re.sub(r'\(\s*\)', '', t)
    t = re.sub(r'(\w)\(', r'\1 (', t)
    t = re.sub(r'\(([^()]*)$', r'(\1)', t)
    t = re.sub(r'\s+', ' ', t).strip(' ,;')
    return t or 'no further note'


def basis_rows(r):
    return [
        ('Overall length', '%.0f mm' % D.LOA, 'APPROVED'),
        ('Overall beam', '%.0f mm' % D.BEAM, 'APPROVED'),
        ('Tunnel width', '%.1f mm' % D.TUNNEL_W, 'APPROVED'),
        ('Sponson width', '%.2f mm, tip %.0f, transom %.1f' % (D.SPONSON_W, D.TIP_W, D.AFT_W), 'APPROVED'),
        ('Skin', '%.3f mm balsa (1/8 in) over frames' % D.SKIN_T, 'APPROVED'),
        ('Freeboard', '%.0f mm, deck parallel to the waterline' % D.FREEBOARD, 'APPROVED'),
        ('Weight and LCG', '%.0f g, %.0f mm from the transom' % (r['W'], r['G']), 'calculated'),
        ('Drafts and trim', 'stern %.1f, bow %.1f, %.2f deg bow down' % (r['d0'], r['bow'], -r['trim']), 'calculated'),
        ('Battery position', 'X %.0f, slide %.0f to %.0f, service X %.0f' % ((D.DESIGN_BAT_X,) + tuple(D.BAT_SLIDE) + (D.BAT_SERVICE_X,)), 'APPROVED'),
        ('Motors', 'ATO 3670, %.0f x %.0f mm, jackets %s' % (D.MOTOR_D, D.MOTOR_L, 'fitted' if D.JACKETS else 'deleted'), 'APPROVED'),
        ('Drive', 'shaft %.0f mm, axis %.0f deg, prop %.0f mm in a Kort nozzle' % (D.SHAFT_D, D.MOTOR_AXIS_DEG, D.PROP_D), 'APPROVED'),
        ('Steering and blade', 'one steering servo, one blade servo, variant %s' % D.BLADE_VARIANT, 'APPROVED'),
        ('Hatch seal', 'plug lids, %.1f mm cord in a %.1f x %.1f groove' % (D.CORD_D, D.GROOVE_W, D.GROOVE_D), 'ASSUMED'),
    ]


def open_rows():
    order = {t: i for i, t in enumerate(S.TAGS)}
    items = sorted(S.open_items(), key=lambda i: (order[i['tag']], i['line']))
    return [(i['tag'], i['name'], S._fmt_value(i['value']) if isinstance(i['value'], (bool, int, float, str)) else '', _clean(i['text'])) for i in items]


def build_cover(index, r):
    sh = Sheet('A-000', 'Cover, index and design basis', 'Drawing index, design basis and references. Sheet 1 of 2.', 'none')
    sh.text(14, 40, 'RC RECOVERY BARGE', 'th')
    sh.text(14, 45, '32 in (%.0f mm) sailboat recovery catamaran, twin-screw balsa hull with a daggerboard, Kort nozzles and sealed plug hatches' % D.LOA, 't')
    sh.text(14, 49.5, 'Revision %s, %s. Every number on every sheet is computed from design.py; nothing is typed twice.' % (D.REV, D.REV_DATE), 't')
    y = 54
    sh.text(14, y, 'STATUS TAGS', 'tb')
    for i, (k, v) in enumerate(TAGNOTE.items()):
        sh.text(14, y + 4 + i * 3.6, '%s: %s' % (k, v), 't')
    y = 76
    y = wtable(sh, 14, y + 3, [('No.', 14), ('Sheet', 72), ('Scale', 20), ('Contents', 90)], index, 'DRAWING INDEX', 't')
    y = wtable(sh, 14, y + 8, [('Key', 28), ('Source', 70), ('Supports', 98)],
               [(k, s, w) for k, s, w, u, n in REF.REFERENCES], 'REFERENCES (links in the build list workbook)', 'ts')
    sh.text(14, y + 4, 'Limits:', 'tb')
    para(sh, 14, y + 8, REF.LIMITS, 150, 'ts', 3.4, 0)
    wtable(sh, 222, 43 + 5, [('Design basis', 54), ('Value', 100), ('Tag', 22)], [(a, b, c) for a, b, c in basis_rows(r)], None, 't', 3.2, 1.4, True)
    return sh


def build_open():
    sh = Sheet('A-000', 'Open items', 'Parsed from design.py: every PENDING, ASSUMED and ESTIMATE tag. Sheet 2 of 2.', 'none')
    rows = open_rows()
    cols = [('Tag', 16), ('Name', 40), ('Value', 20), ('Note from design.py', 119)]
    step, pad = 3.1, 1.2
    hs = [max(len(wrap(v, w, 'ts')) for (n, w), v in zip(cols, rw)) * step + pad for rw in rows]
    half = sum(hs) / 2
    acc, cut = 0, len(rows)
    for i, h in enumerate(hs):
        if acc + h / 2 > half:
            cut = i
            break
        acc += h
    counts = {t: sum(1 for x in rows if x[0] == t) for t in S.TAGS}
    sh.text(14, 31, 'OPEN ITEMS: %s' % ', '.join('%d %s' % (counts[t], t) for t in S.TAGS), 'tb')
    fills = {'PENDING': '#fde7c8', 'ASSUMED': None, 'ESTIMATE': '#e6eefb'}
    for x0, part in ((12, rows[:cut]), (217, rows[cut:])):
        wtable(sh, x0, 36, cols, part, None, 'ts', step, pad, True, [fills[x[0]] for x in part])
    return sh


def build(r=None, index=None):
    r = r or hydro.design()
    index = index or []
    return [build_cover(index, r), build_open()]
