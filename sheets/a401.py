"""A-401 Sealing and penetration schedule, RC channel plan, trim table."""
from .lib import *
from .wtbl import wtable
from .tbl import para
import design as D
from model import geometry as G, hydro, schedules as S


def build(r=None, alts=None):
    r = r or hydro.design()
    alts = alts or [hydro.at(x, r) for x in D.ALT_BAT_X]
    sh = Sheet('A-401', 'Sealing, RC channels and trim',
               'Penetration and sealing schedule, RC channel plan, trim at the design and alternate battery positions', 'NTS')
    rows = S.sealing(r['deck'])
    cols = [('REF', 10), ('PENETRATION', 62), ('WHERE', 84), ('SEAL METHOD', 140), ('CHECK', 112)]
    y = wtable(sh, 14, 38, cols, rows, 'SEALING AND PENETRATION SCHEDULE (the hull is sealed, no bilge pump; every row is tested before the first run)')
    y += 12
    ch = S.channels()
    cols = [('CH', 16), ('FUNCTION', 40), ('DEVICE', 56), ('NOTE', 100)]
    y1 = wtable(sh, 14, y, cols, ch, 'RC CHANNEL PLAN (FlySky FS-i6X and FS-iA6B; confirm against the radio setup)')
    # trim table (right), from the hydro results at each battery position
    trows = []
    for b, rr in [(D.DESIGN_BAT_X, r)] + list(zip(D.ALT_BAT_X, alts)):
        trows.append(('%.0f%s' % (b, ' (design)' if b == D.DESIGN_BAT_X else ' (alternate)'), '%.0f' % rr['W'], '%.1f' % rr['G'], '%.1f' % rr['d0'], '%.1f' % rr['bow'],
                      '%.2f' % -rr['trim'], '%.1f' % rr['over'], '%.1f' % (rr['over'] - D.TROUGH), '%.2f' % rr['deck_off_level']))
    X0 = 234
    cols = [('BATTERY X', 24), ('g', 12), ('LCG', 14), ('STERN', 14), ('BOW', 14), ('BOW DOWN', 20), ('OVER NOZ.', 20), ('MARGIN', 18), ('OFF LEVEL', 22)]
    yt = wtable(sh, X0, y, cols, trows, 'TRIM AT REST (draft in mm below the keel; deck built level at X %.0f)' % D.DESIGN_BAT_X)
    yt += 3
    for t in ['Bow down and deck off level in deg. Margin is the water over the nozzle top less the %.0f mm trough (check 6).' % D.TROUGH,
              'Skeg buoyancy %.0f cm3 is included, with %.1f cm3 of root fillets; the four bilge rounds are subtracted from the hull sections (A-601). Not in the weight: %s.' % (
                  G.SKEG_VOL, G.SKEG_VOL_FILLET, ', '.join(n for _, n, _, _ in __import__('model.weights', fromlist=['x']).UNWEIGHED).lower())]:
        yt = para(sh, X0, yt, t, 96, 'ts', 3.3, 2)
    # sealed compartments of one sponson (the frames are A-502)
    yt += 6
    comp = S.compartments(r['deck'])
    crows = [('%s' % n, 'X %.1f to %.1f' % (c['x0'], c['x1']), c['closes'], ', '.join(c['frames']) or 'none', ', '.join(c['inside']) or 'empty')
             for n, c in zip(('Stern', 'Motor', 'Battery', 'Forward', 'Bow'), comp)]
    cols = [('COMPARTMENT', 22), ('X', 28), ('CLOSED BY', 42), ('FRAMES INSIDE', 34), ('CONTENTS', 60)]
    yt = wtable(sh, X0, yt + 2, cols, crows, 'SEALED COMPARTMENTS, EACH SPONSON (all sealed; wires only through BH1 and BH2, S8)', 'ts')
    sh.text(X0, yt + 3.6, 'Stern X 0 to %.0f and bow X %.0f to %.0f are sealed by the solid frames F%s; F1 is solid inside the stern compartment. Frames: A-502.' % (
        D.FRAME_X[D.SEAL_FRAMES[0] - 1], D.FRAME_X[D.SEAL_FRAMES[1] - 1], D.LOA, ' and F'.join(str(i) for i in D.SEAL_FRAMES)), 'ts')
    yt += 6
    yl = y1 + 6
    sh.text(14, yl, 'COOLING AND POWER NOTES', 'tb')
    yl += 3.6
    notes = ['Cooling loop per side: sponson pickup, ESC, motor jacket, side outlet. Jackets are kept (JACKETS %s). Pickup and outlet positions are PENDING; the v3 prop-wash pickup no longer exists with the nozzles aft of the transom.' % D.JACKETS,
             'One BEC feeds the receiver and both servos: pull the red lead of the second ESC receiver cable. Confirm the combined servo peak against the 6 V / 3 A BEC.',
             'Steering travel %.0f deg each side is ASSUMED (v8 sheets said 45). Slow-speed running of sensorless motors is a bench test (Model Boat Mayhem 42581); see the slow-speed study.' % D.STEER_TRAVEL_DEG]
    for t in notes:
        yl = para(sh, 14, yl, t, 190, 'ts', 3.3, 2) + 0.8
    y_right = yt
    # the right column runs past the diagram's notes; the diagram follows the left column and the notes at X 244 clear the right column
    yt = max(yl, y_right - 14)
    # ---- power, signal and cooling block diagram
    yb = yt + 11
    sh.text(14, yb - 3, 'POWER, SIGNAL AND COOLING (blocks, not to scale)', 'tb')
    bh = 12

    def box(x, y, w, label, cls='gray'):
        sh.rect(x, y, w, bh, cls)
        n = label.count('\n')
        for i, ln in enumerate(label.split('\n')):
            sh.text(x + w / 2, y + bh / 2 + 0.9 + (i - n / 2) * 3, ln, 't', 'middle')
    rows = (('port', yb + 3), ('starboard', yb + 43))
    for nm, y in rows:
        box(14, y, 36, '%s battery\n3S 5000' % nm, 'elec')
        box(70, y, 40, '%s ESC\nSeaKing 60A' % nm, 'elec')
        box(130, y, 46, 'motor ATO 3670\n%s' % ('with jacket' if D.JACKETS else 'no jacket'), 'prop')
        box(196, y, 40, 'shaft, CV joint\nnozzle and prop', 'prop')
        for a_, b_ in ((50, 70), (110, 130), (176, 196)):
            sh.line(a_, y + bh / 2, b_, y + bh / 2, 'thk')
        if nm != 'port':
            continue                                                        # the starboard row repeats the port notes (and would sit on the title block)
        sh.text(244, y + 4, 'water: pickup (X %s) > ESC > jacket > outlet (X %s)' % (
            'PENDING' if D.COOL_PICKUP_X is None else '%.0f' % D.COOL_PICKUP_X, 'PENDING' if D.COOL_OUTLET_X is None else '%.0f' % D.COOL_OUTLET_X), 'ts')
        sh.text(244, y + 8, 'XT60 battery to ESC, 3 phase to the motor, shaft through the stern tube', 'ts')
    ym = yb + 23
    box(70, ym, 40, 'receiver\nFS-iA6B', 'elec')
    sh.line(90, yb + 3 + bh, 90, ym, 'dim')
    sh.line(90, ym + bh, 90, yb + 43, 'dim')
    sh.text(92, ym - 1.4, 'CH2 and BEC power', 'ts')
    sh.text(92, ym + bh + 3.6, 'CH3', 'ts')
    box(130, ym, 46, 'steering servo\nDS3225MG', 'blade')
    sh.line(110, ym + 4, 130, ym + 4, 'dim')
    sh.text(111, ym + 2.6, 'CH1', 'ts')
    box(196, ym, 40, 'blade servo\nDS3225MG', 'blade')
    sh.pline([(110, ym + 9), (116, ym + 9), (116, ym + bh + 3), (216, ym + bh + 3), (216, ym + bh)], 'dim')
    sh.text(150, ym + bh + 6.2, 'CH4 daggerboard, line and spool', 'ts')
    sh.text(244, ym + 4, 'steering: pushrod and tie bar to both nozzle posts', 'ts')
    sh.text(244, ym + 8, 'blade: servo in the bow cap, line to the blade', 'ts')
    # ---- slow-speed study (text only, computed from design.py)
    xs_ = 332
    ys_ = y_right + 4
    sh.text(xs_, ys_, 'SLOW-SPEED STUDY (text only)', 'tb')
    ys_ += 4.4
    ss = S.slow_speed()
    ys_ = para(sh, xs_, ys_, 'Motor ATO 3670, %.0f kV (published). No-load rpm = kV x pack volts. Sensorless floor assumed at %.0f%% of no-load rpm (ASSUMED).' % (D.MOTOR_KV, D.FLOOR_FRACTION * 100), 88, 'ts', 3.3, 2)
    for q in ss:
        ys_ = para(sh, xs_, ys_ + 0.6, '%s %.1f V: no-load %s rpm, floor %s rpm%s.' % (
            q['cells'], q['volts'], format(round(q['noload']), ','), format(round(q['floor']), ','), ' (design pack)' if q['cells'] == D.PACK_V[0][0] else ' (study case)'), 88, 'ts', 3.3, 2)
    ys_ = para(sh, xs_, ys_ + 0.6, 'Prop pitch is not published, so the boat speed at the floor rpm cannot be computed. Bench test required: run each prop at its floor and measure.', 88, 'ts', 3.3, 2)
    ys_ = para(sh, xs_, ys_ + 0.6, 'Radio: set dual rate and expo on the FS-i6X throttle channels (CH2, CH3) for fine control at low throttle; values are set at the bench.', 88, 'ts', 3.3, 2)
    return sh
