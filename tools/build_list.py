"""Write out/RC_Recovery_Cat_Build_List_v6.xlsx from the model: parts, channel plan, cooling plan, references.

Run:  python3 tools/build_list.py    (build.py calls main())
Prices and links come from model/parts.py; quantities of material rows come from the schedules; exchange rates are inputs (cells C3, C4).
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

import design as D
from model import hydro, parts as P, references as REF, schedules as S

FX = {'EUR': 1.15, 'GBP': 1.33}          # USD per unit of currency: placeholders for the owner to update (inputs, not design values)
NAME = 'RC_Recovery_Cat_Build_List_%s.xlsx' % 'v6'
HEAD = PatternFill('solid', fgColor='DDDDDD')
BOLD = Font(bold=True)
DASHES = (chr(0x2014), chr(0x2013))


def clean(v):
    if isinstance(v, str):
        for d in DASHES:
            v = v.replace(d, ', ')
    return v


def material_qty(r):
    zd = r['deck']
    pl = S.panels(zd)
    rows = S.blocking(zd, pl)
    hs = S.hatches(zd)
    ht = S.hatch_totals(hs)
    sc = S.stick_counts(rows, ht['rim_blocking'])
    area = S.hull_area_total(pl)
    waste = 1 + D.WASTE
    return {
        'cord': ht['cord'] * waste / 1000,
        'm3': ht['latches'],
        'balsa': area * waste / 100,
        'stock': (sc['tri_len'] + sc['wedge_len'] + sc['back_len']) / 1000,
        'chine': sc['chine_len'] / 1000,
        'ply': ht['latches'],
        'glass': area * 2 / 1000 ** 2,
    }


def _header(ws, row, labels):
    for i, t in enumerate(labels, 1):
        c = ws.cell(row=row, column=i, value=t)
        c.font = BOLD
        c.fill = HEAD
        c.alignment = Alignment(wrap_text=True, vertical='top')


def sheet_parts(wb, r):
    ws = wb.active
    ws.title = 'Build List'
    ws['A1'] = 'RC Recovery Barge, 32 in sailboat recovery catamaran, build list %s' % D.REV
    ws['A1'].font = Font(bold=True, size=14)
    ws['B3'] = 'USD per EUR'
    ws['C3'] = FX['EUR']
    ws['B4'] = 'USD per GBP'
    ws['C4'] = FX['GBP']
    ws['E3'] = 'Exchange rates are placeholders: update C3 and C4. Prices are published prices when checked, in the currency shown.'
    labels = ['Group', 'Item', 'Part no.', 'Specification', 'Qty', 'Unit', 'Price', 'Cur', 'Unit USD', 'Line USD', 'Mass each g', 'Line mass g', 'Mass basis', 'Mass source',
              'Vendor', 'Link', 'Note']
    hr = 6
    _header(ws, hr, labels)
    mq = material_qty(r)
    row = hr + 1
    for p in P.PARTS:
        q = p.qty if p.qty is not None else mq.get(p.key)
        if q is not None and p.qty is None:
            q = round(q, 2)
        vals = [p.group, p.item, p.part_no, p.spec, q, p.unit, p.price, p.cur, None, None, p.mass, None, p.basis, p.wsource, p.vendor, p.link, p.note]
        for i, v in enumerate(vals, 1):
            ws.cell(row=row, column=i, value=clean(v))
        ws.cell(row=row, column=9, value='=IF(G%d="","",G%d*IF(H%d="EUR",$C$3,IF(H%d="GBP",$C$4,1)))' % ((row,) * 4))
        ws.cell(row=row, column=10, value='=IF(OR(I%d="",E%d=""),"",I%d*E%d)' % ((row,) * 4))
        ws.cell(row=row, column=12, value='=IF(OR(K%d="",E%d=""),"",K%d*E%d)' % ((row,) * 4))
        if p.link:
            ws.cell(row=row, column=16).hyperlink = p.link
            ws.cell(row=row, column=16).font = Font(color='0563C1', underline='single')
        row += 1
    last = row - 1
    ws.cell(row=row, column=2, value='TOTAL').font = BOLD
    ws.cell(row=row, column=10, value='=SUM(J%d:J%d)' % (hr + 1, last)).font = BOLD
    ws.cell(row=row, column=12, value='=SUM(L%d:L%d)' % (hr + 1, last)).font = BOLD
    ws.cell(row=row + 1, column=2, value='Weight total counts published or calculated masses only. Rows with a blank mass are not in it (see the weight model, A-601).')
    ws.cell(row=row + 2, column=2, value='Material quantities come from the schedules: balsa area and sticks from A-103 and A-501, cord and latches from A-503, with %.0f%% waste.' % (D.WASTE * 100))
    widths = [11, 34, 22, 48, 8, 7, 9, 6, 10, 10, 11, 11, 13, 40, 24, 40, 60]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    for rr in ws.iter_rows(min_row=hr + 1, max_row=last):
        for c in rr:
            c.alignment = Alignment(wrap_text=True, vertical='top')
    ws.freeze_panes = ws.cell(row=hr + 1, column=3)


def sheet_channels(wb):
    ws = wb.create_sheet('Channels and Wiring')
    _header(ws, 1, ['Channel', 'Function', 'Device', 'Note'])
    for i, rw in enumerate(S.channels(), 2):
        for j, v in enumerate(rw, 1):
            ws.cell(row=i, column=j, value=clean(v)).alignment = Alignment(wrap_text=True, vertical='top')
    n = len(S.channels()) + 3
    ws.cell(row=n, column=1, value='Wiring').font = BOLD
    wires = [
        ('Battery to ESC', 'one 3S pack per ESC, XT60, one per sponson'),
        ('ESC to motor', 'three phase leads; swap two to reverse a motor'),
        ('ESC to receiver', 'CH2 port throttle, CH3 starboard throttle; one red BEC lead only'),
        ('Servos', 'CH1 steering servo, CH4 blade servo, from the receiver or a BEC'),
    ]
    for i, (a, b) in enumerate(wires, n + 1):
        ws.cell(row=i, column=1, value=a)
        ws.cell(row=i, column=2, value=b)
    for i, w in enumerate([14, 36, 40, 80], 1):
        ws.column_dimensions[get_column_letter(i)].width = w


def sheet_cooling(wb):
    ws = wb.create_sheet('Cooling Plan')
    _header(ws, 1, ['Step', 'Component', 'Where', 'Note'])
    pk = 'PENDING' if D.COOL_PICKUP_X is None else 'X %.0f' % D.COOL_PICKUP_X
    ol = 'PENDING' if D.COOL_OUTLET_X is None else 'X %.0f' % D.COOL_OUTLET_X
    rows = [
        (1, 'Pickup nipple, M5', 'sponson bottom, %s' % pk, 'One per sponson. Face it into the flow; keep it clear of the skeg and shoe.'),
        (2, 'Silicone tube', 'inside the sponson', 'To the ESC cooling pipe.'),
        (3, 'ESC cooling pipe (SeaKing)', 'tunnel roof', 'Cooling pipe is part of the ESC.'),
    ]
    if D.JACKETS:
        rows.append((4, 'Motor water jacket, %.0f x %.0f mm' % (D.JACKET_D, D.JACKET_L), 'on the motor', 'Jackets are kept. Series path: ESC then jacket.'))
    rows.append((len(rows) + 1, 'Outlet nipple, M6', 'sponson side, %s' % ol, 'One overboard outlet per side. Keep it above the waterline at rest.'))
    for i, rw in enumerate(rows, 2):
        for j, v in enumerate(rw, 1):
            ws.cell(row=i, column=j, value=clean(v)).alignment = Alignment(wrap_text=True, vertical='top')
    ws.cell(row=len(rows) + 3, column=1, value='Pickup and outlet positions are PENDING in design.py (COOL_PICKUP_X, COOL_OUTLET_X). No flow rate is published for the pump-less scoop; test it.')
    for i, w in enumerate([6, 40, 30, 80], 1):
        ws.column_dimensions[get_column_letter(i)].width = w


def sheet_refs(wb):
    ws = wb.create_sheet('References')
    _header(ws, 1, ['Key', 'Source', 'Supports', 'URL', 'Note'])
    for i, (k, s, w, u, n) in enumerate(REF.REFERENCES, 2):
        for j, v in enumerate((k, s, w, u or 'no URL recorded', n), 1):
            ws.cell(row=i, column=j, value=clean(v)).alignment = Alignment(wrap_text=True, vertical='top')
        if u:
            ws.cell(row=i, column=4).hyperlink = u
    ws.cell(row=len(REF.REFERENCES) + 3, column=1, value='Limits')
    ws.cell(row=len(REF.REFERENCES) + 3, column=2, value=REF.LIMITS)
    for i, w in enumerate([18, 44, 44, 60, 80], 1):
        ws.column_dimensions[get_column_letter(i)].width = w


def main(out_dir=None, r=None):
    out_dir = out_dir or os.path.join(ROOT, 'out')
    os.makedirs(out_dir, exist_ok=True)
    r = r or hydro.design()
    wb = Workbook()
    sheet_parts(wb, r)
    sheet_channels(wb)
    sheet_cooling(wb)
    sheet_refs(wb)
    path = os.path.join(out_dir, NAME)
    wb.save(path)
    return path


if __name__ == '__main__':
    print('wrote', main())
