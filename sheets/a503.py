"""A-503 Hatches: deck plan from the model's hatch dicts, plug lid section for the 1/8 in deck, latch detail, schedule, daily use."""
import math
from .lib import *
from .wtbl import wtable
from .tbl import para
import design as D
from model import geometry as G, hydro, schedules as S

BF = 'style="fill:#f1e3c8"'
PLY = 'style="fill:#c9a66b"'
K = 4.0                                    # section scale 4:1


def build(r=None):
    r = r or hydro.design()
    zd = r['deck']
    T = D.SKIN_T
    hs = S.hatches(zd)
    ht = S.hatch_totals(hs)
    se = S.hatch_seal()
    sh = Sheet('A-503', 'Hatches and latching',
               'Plug lids with a radial O-ring cord for the 1/8 in (%.3f) deck, rim ring under the deck, thumb screw latches for daily opening' % T, '1:4 and 4:1')
    # ---- deck plan 1:3
    s = 1 / 4
    ox = 22
    xs = lambda X: ox + s * (D.LOA - X)
    oy = 68
    ys = lambda Y: oy - s * Y
    P = lambda pts: [(xs(x), ys(y)) for x, y in pts]
    sh.text(14, 33, 'DECK PLAN, 1:4 (bow at left). Lids at flange size, openings dashed, latch screws dotted.', 'tb')
    for sg in (1, -1):
        sh.poly(P([(x, sg * y) for x, y in S.OUTER] + [(x, sg * y) for x, y in reversed(S.INNER)]), 'obj', 'style="fill:#fff"')
    sh.rect(xs(D.LOA), ys(G.HT), D.LOA * s, 2 * G.HT * s, 'thin')
    sh.rect(xs(0), ys(D.AFT_DECK_W / 2), D.AFT_DECK_L * s * -1 + 0, D.AFT_DECK_W * s, 'thin') if False else None
    sh.rect(xs(0) + 0, ys(D.AFT_DECK_W / 2), D.AFT_DECK_L * s, D.AFT_DECK_W * s, 'thin')
    sh.text(xs(0) + D.AFT_DECK_L * s / 2, ys(0) + 1, 'aft deck', 'ts', 'middle')
    for h in G.hatch_rects(flange=True):
        sh.rect(xs(h['x1']), ys(h['y1']), (h['x1'] - h['x0']) * s, (h['y1'] - h['y0']) * s, 'obj', 'style="fill:#f4f4f4"')
    se_ = S.hatch_seal()
    for h in G.hatch_rects():
        sh.rect(xs(h['x1']), ys(h['y1']), (h['x1'] - h['x0']) * s, (h['y1'] - h['y0']) * s, 'hid')
        sh.text(xs((h['x0'] + h['x1']) / 2), ys(h['yc']) + 0.8, h['name'], 'tb', 'middle')
        for X_ in (h['x0'] - se_['pad_off'], h['x1'] + se_['pad_off']):
            sh.circ(xs(X_), ys(h['yc']), D.LATCH_SCREW_D * s / 2 + 0.5, 'obj', 'style="fill:#555"')
    for sg in (1, -1):
        sh.circ(xs(G.POSTX), ys(sg * G.YS), D.NOZ_POST_D * s / 2 + 0.6, 'obj')
    sh.text(xs(G.POSTX), ys(-G.YS) + 7, 'post bushings', 'ts', 'middle')
    for q in hs:
        a, b = q['x0'], q['x1']
        sh.dimh(xs(b), xs(a), ys(-(G.YS + 42)) + 3 + 3.4 * list(D.HATCHES).index(q['name']), '%s %.0f to %.0f' % (q['name'], a, b), ys(-G.YS - 40), ys(-G.YS - 40)) if q['zone'] == 'sponson' and False else None
    # ---- hatch schedule
    cols = [('ID', 8), ('ACCESS', 36), ('QTY', 8), ('OPENING X x Y', 26), ('FLANGE LID', 26), ('PLUG', 24), ('CORD mm', 16), ('LATCH X (pads)', 34),
            ('RIM SIDE', 17), ('CONTENTS AND FIT', 52), ('PADS MEET', 30)]
    acc = {'HM': 'motor and jacket, per sponson', 'HB': 'battery, per sponson', 'HC': 'ESCs and receiver, center', 'HS': 'steering servo, center'}
    rows = []
    for q in hs:
        fit = '%s %.1f x %.1f: %s' % (q['contents'], q['c_l'], q['c_w'], 'fits' if q['fits'] else 'DOES NOT FIT') if q['contents'] else ''
        rows.append((q['name'], acc.get(q['name'], q['zone']), str(q['qty']), '%.1f x %.1f' % (q['L'], q['W']), '%.1f x %.1f' % (q['flange_L'], q['flange_W']),
                     '%.1f x %.1f' % (q['plug_L'], q['plug_W']), '%.0f' % q['cord'], '%.1f and %.1f' % tuple(q['pads']),
                     '%.2f%s' % (q['rim_y'], ' (to wall)' if q['rim_touch'] else ''), fit, ', '.join(q['meets']) or 'clear'))
    y = wtable(sh, 14, 112, cols, rows, 'HATCH SCHEDULE (X along the hull from the transom, Y across; opening Y centered on the sponson or the centerline)', step=2.9, pad=0.8)
    y += 2
    sh.text(14, y + 3.4, 'Lids %d, latches %d (%d per lid), cord %.0f mm in all, rim blocking %.0f mm. Cord loop = rounded rectangle at the compressed cord centerline (corner R%.1f) plus %.0f lap. Pads that meet a frame, bulkhead or deck beam (column PADS MEET) need the pad moved or the frame notched.' % (
        ht['lids'], ht['latches'], D.LATCH_PER_LID, ht['cord'], ht['rim_blocking'], D.HATCH_CORNER_R, D.CORD_LAP), 'ts')
    # ---- plug lid section 4:1
    X0, Y0 = 22, 182
    t = T * K
    sh.text(14, Y0 - 24, 'DETAIL 1  Plug lid section 4:1 (cut through a long edge, opening edge at center)', 'tb')
    dw = 34                                                     # drawn deck width each side
    clr = D.PLUG_CLR / 2 * K
    xe = X0 + dw                                                # opening edge
    # deck (left) and rim ring under it
    sh.rect(X0, Y0, dw, t, 'cut')
    sh.rect(X0 + dw - D.RIM_W * K, Y0 + t, D.RIM_W * K, D.RIM_T * K, 'cut', PLY)
    # plug: two laminated layers, edge at opening edge + clearance
    px = xe + clr
    pd = D.PLUG_LAYERS * T * K
    sh.rect(px, Y0, dw, pd, 'cut', BF)
    sh.line(px, Y0 + t, px + dw, Y0 + t, 'thin')
    # flange layer on top of the deck, extends past the opening by FLANGE
    fl_x0 = xe - D.FLANGE * K
    sh.rect(fl_x0, Y0 - t, (px + dw) - fl_x0, t, 'cut', 'style="fill:#e8d9b8"')
    # cord in the groove (center at the compressed position)
    gz = Y0 + pd / 2
    gd, gw = D.GROOVE_D * K, D.GROOVE_W * K
    sh.rect(px, gz - gw / 2, gd, gw, 'obj', 'style="fill:#fff"')
    sh.circ(xe + se['inset'] * K, gz, D.CORD_D * K / 2, 'obj', 'style="fill:#222"')
    sh.dimv(Y0, Y0 + t, X0 + 3, '%.3f' % T, X0, X0) if False else None
    sh.dimv(Y0 - t, Y0, fl_x0 - 5, 'flange %.3f' % T, fl_x0, fl_x0)
    sh.dimv(Y0, Y0 + pd, px + dw + 6, 'plug %.3f' % (pd / K), px + dw, px + dw)
    sh.dimh(fl_x0, xe, Y0 - t - 5, '%.1f' % D.FLANGE, Y0 - t, Y0 - t)
    sh.dimh(xe, px, Y0 + pd + 22, '%.2f' % (D.PLUG_CLR / 2), Y0 + pd, Y0 + pd) if False else None
    sh.dimh(X0 + dw - D.RIM_W * K, xe, Y0 + t + D.RIM_T * K + 5, 'rim %.3f' % D.RIM_W, Y0 + t + D.RIM_T * K, Y0 + t + D.RIM_T * K)
    sh.text(X0, Y0 + pd + 13, 'deck %.3f; rim ring %.3f (ply) under the deck makes the opening wall %.3f deep' % (T, D.RIM_T, se['seat']), 'ts')
    sh.text(X0, Y0 + pd + 17, 'plug = %d layers of %.3f laminated, crossed grain, %.3f deep; clearance %.2f each side' % (D.PLUG_LAYERS, T, pd / K, D.PLUG_CLR / 2), 'ts')
    sh.text(X0, Y0 + pd + 21, 'cord %.1f in a %.1f wide x %.1f deep groove; squeeze %.2f (%s), radial seal' % (D.CORD_D, D.GROOVE_W, D.GROOVE_D, se['squeeze'], format(se['squeeze_pct'], '.0%')), 'ts')
    sh.text(X0, Y0 + pd + 25, 'flange layer (lid top) overhangs the opening %.1f all round and sits on the deck; lid proud %.3f' % (D.FLANGE, se['lid_proud']), 'ts')
    sh.text(X0, Y0 + pd + 29, 'water above the deck pushes the lid into the opening; the latch only resists lift', 'ts')
    sh.text(X0, Y0 + pd + 33, 'the bench-test lid is held %.0f mm under water for %.0f min' % (D.HATCH_TEST_DEPTH, D.HATCH_TEST_MIN), 'ts')
    # ---- latch detail 4:1
    X1, Y1 = 150, 182
    sh.text(X1 - 4, Y1 - 24, 'DETAIL 2  End latch, section along the lid end 4:1', 'tb')
    L1 = 70
    sh.rect(X1, Y1, L1, t, 'cut')                                  # deck
    padx0 = X1 + 4
    ring_w = D.RIM_W * K
    pad_w = D.LATCH_PAD * K
    sh.rect(padx0, Y1 + t, ring_w, D.RIM_T * K, 'cut', PLY)           # rim ring end
    sh.rect(padx0 + ring_w, Y1 + t, pad_w, T * K, 'cut', PLY)         # latch pad beside the rim, glued to both faces
    nut_x = padx0 + ring_w + pad_w / 2
    sh.rect(nut_x - D.LATCH_SCREW_D * K, Y1 + t + (T - D.LATCH_NUT_T) * K / 2, 2 * D.LATCH_SCREW_D * K, D.LATCH_NUT_T * K, 'obj', 'style="fill:#bbb"')
    tab_end = padx0 + ring_w + pad_w
    sh.rect(padx0 - 4, Y1 - t, tab_end - padx0 + 4 - 2, t, 'cut', 'style="fill:#e8d9b8"')   # lid flange layer with its end tab
    sh.line(nut_x, Y1 - t - 10, nut_x, Y1 + 2 * t + 3, 'obj')
    sh.rect(nut_x - 5, Y1 - t - 14, 10, 4, 'cut', 'style="fill:#bbb"')
    sh.dimh(padx0, tab_end, Y1 + 2 * t + 10, '%.3f to the end of the pad' % se['tab_end'], Y1 + t + 3, Y1 + t + 3)
    sh.text(X1 - 4, Y1 + 2 * t + 17, 'M3 thumb screw (%.0f) through the lid tab and the deck into an M3 nut' % D.LATCH_SCREW_D, 'ts')
    sh.text(X1 - 4, Y1 + 2 * t + 21, 'captured in the ply pad (%.1f square x %.3f, nut %.1f thick)' % (D.LATCH_PAD, T, D.LATCH_NUT_T), 'ts')
    sh.text(X1 - 4, Y1 + 2 * t + 25, 'pad bears on the deck underside and on the rim end: two faces', 'ts')
    sh.text(X1 - 4, Y1 + 2 * t + 29, 'screw center %.3f from the opening edge; %.0f lanyard to the deck' % (se['pad_off'], D.LANYARD_D), 'ts')
    sh.text(X1 - 4, Y1 + 2 * t + 33, 'turn-button option: brass strip on the same pad, quarter turn over the tab', 'ts')
    # ---- daily use, right column
    X = 262
    notes = ['DAILY USE',
             '1  Unscrew the %d thumb screws, lift the lid by its end tab.' % D.LATCH_PER_LID,
             '2  Wipe the cord and the opening edge; silicone grease the cord if dry.',
             '3  Seat the plug, thumb screws finger tight, no tools.',
             '4  The metal nut in the ply pad takes the wear. Never thread into balsa.',
             '5  The lid is tied to the deck by a %.0f mm lanyard.' % D.LANYARD_D,
             '6  Replace the cord yearly or when it takes a set.',
             '7  Test: hold the lid %.0f mm under water for %.0f min, dry, check.' % (D.HATCH_TEST_DEPTH, D.HATCH_TEST_MIN),
             'If the test leaks: add a flat EPDM gasket under the flange (Model Boat Mayhem 12941).']
    yy = 40
    for i, n_ in enumerate(notes):
        sh.text(X, yy, n_, 'tb' if i == 0 else 't')
        yy += 4.2
    X = 262
    yy = 168
    sh.text(X, yy, 'SEAL NUMBERS (from design.py, all ASSUMED)', 'tb')
    yy += 4.2
    nums = ['plug depth %.3f, seat depth %.3f (deck + rim), lid total %.3f' % (se['plug_depth'], se['seat'], se['lid_total']),
            'cord %.1f, groove %.1f x %.1f, clearance %.2f each side, squeeze %.2f' % (D.CORD_D, D.GROOVE_W, D.GROOVE_D, D.PLUG_CLR / 2, se['squeeze']),
            'opening corner R%.1f; cord splice lap %.0f; flange %.1f; rim %.3f x %.3f' % (D.HATCH_CORNER_R, D.CORD_LAP, D.FLANGE, D.RIM_W, D.RIM_T),
            'seams are never at a hatch edge; the rim is trimmed to the wall where the sponson is narrow']
    for t_ in nums:
        yy = para(sh, X, yy, t_, 80, 't', 3.8, 2)
    return sh
