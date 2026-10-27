"""Builder documents: part marks, cut list against the order, nesting, templates and tiling, planking guide, building board, DXF and SVG."""
import math
import os
import re

import pytest

import design as D
from model import geometry as G, hydro, partmarks as M, partshapes as SH, marknames as MN, schedules as S
from tools.builddocs import board, cutlist, export, layouts, make, nest, planking, templates


@pytest.fixture(scope='module')
def r():
    return hydro.design()


@pytest.fixture(scope='module')
def tb(r):
    return M.build(r)


@pytest.fixture(scope='module')
def nst(tb):
    return nest.nest_all(tb)


# ---- marks ---------------------------------------------------------------------------------------------------------------------
def test_marks_are_unique_and_cover_the_scheme(tb):
    for m in ('O1', 'O2', 'O3', 'I1', 'I2', 'TP', 'TR', 'BT', 'DK', 'RP', 'TT', 'AD-T', 'AD-B', 'AD-BP', 'AD-BS', 'AD-BT', 'AD-BE', 'DO-P', 'BR-x060-P', 'F1-P', 'F9-S', 'F5-T',
              'F8-T', 'BH1', 'BH2', 'DB-150', 'DB-200', 'DB-660', 'RL', 'MM-P1', 'MM-S6', 'SV', 'SK-P1', 'SK-S2', 'SC', 'SH', 'BL-P', 'BL-S', 'BB-C', 'BB-F', 'BA-P', 'BA-S',
              'LD-HM', 'RR-HM', 'LP', 'J1-I2', 'J4-1', 'NP-P', 'PB-P', 'CA', 'CF', 'CT', 'CR-x620'):
        assert m in tb.index, m
    assert len(tb.index) == len(set(tb.index))          # Table.mark raises on a duplicate; this pins the count
    assert all(k in tb.index for k in tb.assemblies)
    assert set(tb.templates) <= set(tb.index)


def test_every_cad_part_carries_a_mark():
    cq = pytest.importorskip('cadquery')
    from tools import cad
    r = hydro.design()
    parts, _ = cad.build(r)
    for p in parts:
        assert re.match(r'^[a-z_]+__[A-Z][A-Za-z0-9-]*_', p.full), p.full
    assert M.cad_name('sponson_port') == 'HS-P_sponson_port'
    with pytest.raises(KeyError):
        M.cad_name('no_such_part')


def test_schedules_use_the_marks(r):
    assert MN.a103_mark('SK') == 'SK-P1 SK-P2 SK-S1 SK-S2'
    assert MN.a103_mark('O1') == 'O1'
    rows = S.deck_frame_rows(r['deck'])
    assert rows[0][0] == 'AD-BP AD-BS' and rows[1][0] == 'AD-BT' and rows[2][0] == 'AD-BE'
    from sheets import a103, a502
    a103.build(r)
    a502.build(r)


# ---- cut list against the order --------------------------------------------------------------------------------------------
def test_stock_totals_agree_with_order_parts(tb, nst, capsys):
    chk = {c['key']: c for c in cutlist.check_rows(tb, nst)}
    lines = []
    for k, c in chk.items():
        lines.append('%-7s order %-5s cut list %-5s nested %s' % (k, c['order'], c['derived'], c['nested']))
    print('\n'.join(lines))
    # sticks and sheets other than balsa: the order's arithmetic applied to the cut list gives the ordered count (chine and rods carry a spare)
    assert chk['tri']['derived'] == chk['tri']['order']
    assert chk['cord']['derived'] == chk['cord']['order']
    assert chk['g10']['derived'] == chk['g10']['order'] == chk['g10']['nested']
    assert chk['ply']['derived'] == chk['ply']['order']
    assert chk['chine']['order'] == chk['chine']['derived'] + 1
    assert chk['rod3']['order'] >= chk['rod3']['nested'] and chk['tube4']['order'] >= chk['tube4']['nested']
    assert chk['rod256']['order'] >= chk['rod256']['nested']
    # nesting never beats the area bound, and never needs fewer sticks than the order's arithmetic
    for k in ('tri', 'chine', 'cord'):
        assert chk[k]['nested'] >= chk[k]['derived'] - 1
    # blocking pieces carry the A-501 totals exactly
    zd = hydro.design()['deck']
    rows = S.blocking(zd)
    hs = S.hatches(zd)
    ht = S.hatch_totals(hs)
    sc = S.stick_counts(rows, ht['rim_blocking'])
    w = 1 + D.WASTE
    tri = sum(p.qty * p.length for p in tb.parts if p.stock == 'tri' and not p.wedge) / 2 * w
    wedge = sum(p.qty * p.length for p in tb.parts if p.stock == 'tri' and p.wedge) * w
    assert math.isclose(tri, sc['tri_len'], rel_tol=1e-9) and math.isclose(wedge, sc['wedge_len'], rel_tol=1e-9)
    assert math.isclose(sum(p.qty * p.length for p in tb.parts if p.stock == 'chine') * w, sc['chine_len'], rel_tol=1e-9)


def test_balsa_area_against_the_order(tb, nst):
    c = next(x for x in cutlist.check_rows(tb, nst) if x['key'] == 'balsa')
    a = c['summary']
    sheet = tb.stock['balsa'].L * tb.stock['balsa'].W
    back = sum(p.qty * p.length * p.width for p in tb.parts if p.mark.startswith('BK-'))
    by_outline = a['by_net'] + back * (1 + D.WASTE) / sheet           # outlines plus seam backing, with the order's waste factor
    print('balsa: order %s, outlines + backing %.2f, bounding rectangles %.2f, nested %d' % (c['order'], by_outline, a['with_waste'], c['nested']))
    assert abs(by_outline - c['order']) <= 3.0              # the cut list adds parts the order's area sum leaves out (skeg cores, aft deck, push bar, overhang)
    assert c['nested'] >= by_outline                        # nesting cannot beat the area bound
    assert c['nested'] >= c['derived'] - 1


def test_cut_rows_have_all_columns_and_angles(tb, nst):
    rs = cutlist.rows(tb, nst)
    assert 'balsa' in rs and 'tri' in rs
    for key, lst in rs.items():
        for r_ in lst:
            assert r_['length'] > 0 and r_['width'] > 0 and r_['t'] > 0, r_['mark']
            assert 0 < r_['a1'] <= 90 + 1e-9 and 0 < r_['a2'] <= 90 + 1e-9, r_['mark']
    j4 = [r_ for r_ in rs['tri'] if r_['mark'].startswith('J4-')]
    assert len(j4) == len(S.turns()) and all(abs(r_['a1'] - 90) < 1e-9 for r_ in j4)
    # miter angle of a wall end is 90 less half the corner turn
    o1 = next(r_ for r_ in rs['balsa'] if r_['mark'] == 'O1.1')
    turns = [t for _, _, t in S.turns()]
    assert math.isclose(o1['a1'], 90 - turns[0] / 2) and math.isclose(o1['a2'], 90 - turns[1] / 2)


def test_cut_list_files(tb, nst, tmp_path):
    cutlist.csv_write(tb, nst, str(tmp_path / 'c.csv'))
    head = open(str(tmp_path / 'c.csv')).read().splitlines()[0]
    assert 'end angle 1 deg' in head and 'stock piece' in head and 'rev' in head
    n = cutlist.pdf_write(tb, nst, str(tmp_path / 'c.pdf'))
    assert n >= 2


# ---- nesting -------------------------------------------------------------------------------------------------------------------
def test_part_longer_than_stock_raises(tb):
    st = tb.stock['balsa']
    with pytest.raises(nest.StockError):
        nest.nest_rects([dict(mark='X', inst=1, w=st.L + 1.0, h=10.0)], st, False)
    with pytest.raises(nest.StockError):
        nest.nest_sticks([dict(mark='X', inst=1, w=tb.stock['chine'].L + 1.0)], tb.stock['chine'])


def test_nesting_is_consistent(tb, nst):
    for key, bins in nst.bins.items():
        st = tb.stock[key]
        for b in bins:
            if st.kind == 'sheet':
                for p in b.placed:
                    assert p.x >= -1e-6 and p.y >= -1e-6 and p.x + p.w <= st.L + 1e-6 and p.y + p.h <= st.W + 1e-6, (key, p.mark)
                rects = [(p.x, p.y, p.w, p.h) for p in b.placed]
                for i, a in enumerate(rects):
                    for c in rects[i + 1:]:
                        gap = D.KERF - 1e-6
                        assert a[0] + a[2] + gap <= c[0] or c[0] + c[2] + gap <= a[0] or a[1] + a[3] + gap <= c[1] or c[1] + c[3] + gap <= a[1], (key, b.no)
            else:
                for lane in range(st.lanes):
                    ends = sorted((p.x, p.x + p.w) for p in b.placed if p.y == lane or (st.lanes == 2 and p.h == 2))
                    for (a0, a1), (c0, c1) in zip(ends, ends[1:]):
                        assert a1 + D.KERF - 1e-6 <= c0
                    assert not ends or ends[-1][1] <= st.L + 1e-6
    # every piece of every part is placed
    for p in tb.parts:
        if tb.stock[p.stock].L is not None:
            for i in range(1, p.qty + 1):
                assert (p.mark, i) in nst.where, (p.mark, i)
    # balsa grain stays along the stock length: no balsa piece is turned
    assert not any(p.rot for b in nst.bins['balsa'] for p in b.placed)


def test_g10_blades_pair_inside_the_sheet(tb, nst):
    st = tb.stock['g10']
    assert nst.count('g10') == 1
    b = nst.bins['g10'][0]
    assert any(p.poly for p in b.placed)
    assert b.placed[0].w <= max(st.L, st.W) and b.placed[0].h <= min(st.L, st.W) or b.placed[0].rot


def test_layout_pages(tb, nst):
    doc = layouts.build(tb, nst)
    n_sheets = sum(nst.count(k) for k, st in tb.stock.items() if st.kind == 'sheet')
    assert len(doc.pages) >= 1 + n_sheets


# ---- templates and tiling ----------------------------------------------------------------------------------------------------
def test_sample_template_bounding_boxes(tb, r):
    zd = r['deck']
    f5 = next(f for f in S.frames(zd) if f['num'] == 5)
    w, h = tb.templates['F5-P'].shape.size()
    assert math.isclose(w, f5['w_in'], abs_tol=1e-6) and math.isclose(h, f5['h'], abs_tol=1e-6)
    w, h = tb.templates['F5-T'].shape.size()
    assert math.isclose(w, f5['tun_w'], abs_tol=1e-6) and math.isclose(h, f5['tun_h'], abs_tol=1e-6)
    ext = G.blade_outline(True)
    w, h = tb.templates['BL-P'].shape.size()
    assert math.isclose(w, max(p[0] for p in ext) - min(p[0] for p in ext), abs_tol=1e-6)
    assert math.isclose(h, max(p[1] for p in ext) - min(p[1] for p in ext), abs_tol=1e-6)
    w, h = tb.templates['SK-P1'].shape.size()
    assert math.isclose(w, G.SKEG_X0, abs_tol=1e-6) and math.isclose(h, -G.SHOE_BOT, abs_tol=1e-6)
    # the F3 shaft opening, the F5 grommet and the F9 trunk notch are in the shapes
    assert any('shaft' in n for n in tb.templates['F3-P'].shape.notes)
    assert tb.templates['F5-T'].shape.cuts and tb.templates['F5-T'].shape.cuts[0][0] == 'circle'
    assert any('trunk notch' in n for n in tb.templates['F9-P'].shape.notes)
    # six mount layers, the top slopes
    assert len([m for m in tb.templates if m.startswith('MM-P')]) == S.mount_dims()['layers']


def test_template_pages_equal_the_tiled_count(tb):
    doc = templates.build(tb)
    n, its = templates.page_count(tb)
    assert len(doc.pages) == n
    ww, wh = templates.window_size(doc)[2:]
    # a part larger than the window is tiled: sheets = columns x rows with the design overlap
    sk = next(i for i in its if i['mark'] == 'SK-P1')
    assert (sk['cols'], sk['rows']) == templates.tile_grid(sk['w'] + templates.TILE_PAD_L + templates.TILE_PAD, sk['h'] + templates.TILE_PAD_T + templates.TILE_PAD + sk['tx'], ww, wh, D.TILE_OVERLAP)
    assert sk['cols'] * sk['rows'] > 1
    titles = [p.title for p in doc.pages]
    assert 'SK-P1 sheet 2 of %d (row 1, col 2)' % (sk['cols'] * sk['rows']) in titles
    # tiles of one part cover the part: windows advance by (window - overlap)
    for it in its:
        cols, rows = it['cols'], it['rows']
        if cols * rows == 1:
            continue
        totw = it['w'] + templates.TILE_PAD_L + templates.TILE_PAD
        assert cols * ww - (cols - 1) * D.TILE_OVERLAP >= totw - 1e-6
        assert rows * wh - (rows - 1) * D.TILE_OVERLAP >= it['h'] + templates.TILE_PAD_T + templates.TILE_PAD + it['tx'] - 1e-6


def test_every_template_page_has_scale_bar_and_check_box(tb):
    doc = templates.build(tb)
    doc.finish()
    for pg in doc.pages:
        svg = pg.svg()
        assert svg.count('measure: 100 mm') == 1
        assert 'REV %s' % D.REV in svg and 'page %d of %d' % (pg.n, pg.m) in svg
        assert 'scale bar, %.0f mm' % D.SCALE_BAR in svg
        # the check box is CHECK_BOX mm square, the bar is SCALE_BAR mm long in ten segments
        assert re.search(r'<rect x="[\d.]+" y="[\d.]+" width="%.2f" height="%.2f" class="reg"' % (D.CHECK_BOX, D.CHECK_BOX), svg)
        segs = re.findall(r'<rect [^>]*width="(%.2f)" height="4.00" class="bar"' % (D.SCALE_BAR / 10), svg)
        assert len(segs) == 10
    # page size is letter, portrait
    assert math.isclose(doc.pages[0].Wp, D.LETTER_IN[0] * D.INCH) and math.isclose(doc.pages[0].Hp, D.LETTER_IN[1] * D.INCH)


def test_registration_crosses_are_shared_by_neighbouring_tiles(tb):
    # the cross CROSS mm inside the right edge of tile c sits at the same part position as the cross inside the left edge of tile c + 1
    ww, _ = templates.window_size(templates.Doc('x', D.LETTER_IN))[2:]
    step = ww - D.TILE_OVERLAP
    right_cross = (ww - templates.CROSS)
    left_cross_next = step + templates.CROSS
    assert math.isclose(right_cross, left_cross_next)


def test_taper_plan_builds(monkeypatch, r):
    monkeypatch.setattr(D, 'DECK_PLAN', 'taper')
    t2 = M.build(r)
    assert 'DO-P' not in t2.templates and 'AD-T' in t2.templates
    n = nest.nest_all(t2)
    assert n.count('balsa') > 0
    assert templates.page_count(t2)[0] > 0


# ---- planking guide and board ------------------------------------------------------------------------------------------------
def test_planking_tables(tb, nst, r):
    zd = r['deck']
    for mk in planking.HULL + planking.CENTER:
        n = len(planking.planks_of(tb, mk))
        for k in range(n):
            for num, X in planking.stations(zd):
                w = planking.width_at(tb, mk, k, X)
                if w is not None:
                    assert w <= D.STOCK_W + 1e-6, (mk, k, X, w)
    # width of an O2 plank at F5 equals half the wall height there (equal split)
    p = next(p for p in S.panels(zd) if p['mark'] == 'O2')
    f5x = next(x for n_, x in planking.stations(zd) if n_ == 5)
    w0 = planking.width_at(tb, 'O2', 0, f5x)
    h = p['h0'] + (p['h1'] - p['h0']) * (f5x - D.AFT_TAPER_X) / (G.BOW0 - D.AFT_TAPER_X)
    assert math.isclose(w0, h / p['planks'], rel_tol=1e-3)
    doc = planking.build(tb, nst, zd)
    assert len(doc.pages) >= 4
    svg = ''.join(p_.svg() for p_ in doc.pages)
    assert 'REV %s' % D.REV in svg and svg.count('measure: 100 mm') == len(doc.pages)


def test_building_board(r):
    its, (x_lo, x_hi, z_lo, z_hi) = board.items(r)
    text = ' '.join(i.get('text', '') for i in its)
    for s in ('keel datum', 'X 0, transom datum', 'X %.0f, bow datum' % D.LOA, 'waterline', 'blade hinge centre', 'nozzle post centre', 'CV joint', 'motor axis', 'skeg outline', 'deck top'):
        assert s in text, s
    assert x_lo < -D.AFT_DECK_L and x_hi > D.LOA
    for f in S.frames(r['deck']):
        assert 'F%d' % f['num'] in text and 'X %.1f' % f['x'] in text
    half = board.half_scale_doc(r)
    full = board.full_size_doc(r)
    assert len(half.pages) >= 1 and len(full.pages) >= 2
    assert math.isclose(half.pages[0].Wp, D.TABLOID_IN[0] * D.INCH)
    assert all(p.svg().count('measure: 100 mm') == 1 for p in full.pages)


# ---- DXF and SVG -------------------------------------------------------------------------------------------------------------
def test_dxf_and_svg_export(tb, tmp_path):
    ezdxf = pytest.importorskip('ezdxf')
    n = export.write_all(tb, str(tmp_path))
    assert n == len(tb.templates)
    for mk in ('F5-P', 'BL-P', 'SK-P1'):
        doc = ezdxf.readfile(str(tmp_path / 'dxf' / (mk + '.dxf')))
        assert doc.units == ezdxf.units.MM
        pl = [e for e in doc.modelspace() if e.dxftype() == 'LWPOLYLINE' and e.dxf.layer == 'CUT'][0]
        pts = [(p[0], p[1]) for p in pl.get_points()]
        w = max(p[0] for p in pts) - min(p[0] for p in pts)
        assert math.isclose(w, tb.templates[mk].shape.size()[0], abs_tol=1e-6)
        svg = open(str(tmp_path / 'svg' / (mk + '.svg'))).read()
        assert 'REV %s' % D.REV in svg and 'mm"' in svg


def test_make_writes_everything(tmp_path):
    res = make.main(str(tmp_path), log=None)
    for name, (path, pages) in res['files'].items():
        assert os.path.exists(path), name
    assert res['balsa']['nested'] >= 1 and res['balsa']['order'] == 23
    assert res['templates'] == len(M.table().templates)
    assert os.path.exists(str(tmp_path / 'part_marks.csv'))
