"""Part mark text rules, with no dependencies, so the schedules, the sheets, the CAD export and the builder documents all spell a mark the same way.
Full table: model/partmarks.py. A mark ending -P or -S is a port or starboard piece; a plank is the panel mark, a dot and the plank number (O1.2)."""

# A-103 row id -> mark text shown in the schedule's mark column
PANEL_DISPLAY = {'SK': 'SK-P1 SK-P2 SK-S1 SK-S2', 'BP': 'BB-C BB-F', 'DO': 'DO-P DO-S DO-F', 'TE': 'TE-A TE-F', 'AD': 'AD-T', 'AB': 'AD-B'}
PANEL_MARK = {'AD': 'AD-T', 'AB': 'AD-B'}              # the one mark a panel row's template carries


def a103_mark(mark):
    return PANEL_DISPLAY.get(mark, mark)


def frame_marks(num):
    """Sponson piece port, sponson piece starboard, tunnel piece of frame F<num>."""
    return 'F%d-P' % num, 'F%d-S' % num, 'F%d-T' % num


def frame_cell(num):
    return ' '.join(frame_marks(num))


def bracket_mark(x, side):
    return 'BR-x%03d-%s' % (round(x), side)


def rib_mark(x):
    return 'CR-x%03d' % round(x)


def beam_mark(x):
    return 'DB-%03d' % round(x)
