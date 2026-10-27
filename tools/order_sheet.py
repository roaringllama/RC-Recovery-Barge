"""Write out/RC_Recovery_Barge_Parts_Order_v1.xlsx: the parts ordering spreadsheet.

Run:  python3 tools/order_sheet.py
Data: model/order_parts.py (vendor, part number, price, link, date checked, quantity arithmetic). Quantities of hull stock and hatch
hardware are computed from the model through model/schedules.py with the design.WASTE allowance.
Sheets: Order, Summary, Exchange rates (input cells), Sources. Prices are the listed unit price in the listed currency; Unit USD uses the
rate on the Exchange rates sheet, so change a rate there and every USD figure follows. Shipping, tax, VAT and duty are not included.
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

import design as D
from model import hydro, order_parts as OP

NAME = 'RC_Recovery_Barge_Parts_Order_v1.xlsx'
HEAD = PatternFill('solid', fgColor='DDDDDD')
INPUT = PatternFill('solid', fgColor='FFF2CC')
SUBFILL = PatternFill('solid', fgColor='FCE4D6')
BOLD = Font(bold=True)
LINK = Font(color='0563C1', underline='single')
DASHES = (chr(0x2014), chr(0x2013))
WRAP = Alignment(wrap_text=True, vertical='top')
THIN = Side(style='thin', color='BBBBBB')

ORDER_COLS = ['Group', 'Item', 'Qty', 'Unit', 'Vendor', 'Part no.', 'Unit price', 'Currency', 'Unit USD', 'Line USD', 'Weight each (g)', 'Line weight (g)',
              'Weight basis', 'Stock status', 'Date checked', 'Link', 'Substitute', 'Notes']
ORDER_W = [20, 46, 6, 12, 28, 22, 10, 9, 10, 11, 11, 11, 13, 30, 12, 50, 11, 90]
HR = 4                                   # header row of the Order sheet
FX_FIRST, FX_LAST = 5, 7                 # rate rows on the Exchange rates sheet


def clean(v):
    if isinstance(v, str):
        for d in DASHES:
            v = v.replace(d, '-')
    return v


def _header(ws, row, labels):
    for i, t in enumerate(labels, 1):
        c = ws.cell(row=row, column=i, value=t)
        c.font = BOLD
        c.fill = HEAD
        c.alignment = Alignment(wrap_text=True, vertical='top')


def _widths(ws, widths):
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w


def rate_of(cur):
    return dict(OP.RATES)[cur]


def totals(lines):
    """Python-side totals (the workbook computes the same with formulas). Returns a dict."""
    by = {g: 0.0 for g in OP.GROUPS}
    wt = 0.0
    n_nopub = n_calc = n_sub = 0
    grand = 0.0
    for ln in lines:
        usd = ln['price'] * rate_of(ln['cur']) * ln['qty']
        by[ln['group']] += usd
        grand += usd
        if ln['mass'] is not None:
            wt += ln['mass'] * ln['qty']
        if ln['basis'] == 'Not published':
            n_nopub += 1
        if ln['basis'] == 'Calculated':
            n_calc += 1
        if ln['sub']:
            n_sub += 1
    return dict(by_group=by, grand=grand, weight=wt, no_published=n_nopub, calculated=n_calc, substitutes=n_sub, n=len(lines))


def sheet_order(wb, lines):
    ws = wb.active
    ws.title = 'Order'
    ws['A1'] = 'RC Recovery Barge, parts order v1, design %s' % D.REV
    ws['A1'].font = Font(bold=True, size=14)
    ws['A2'] = ('Prices are the listed unit price on the date checked (%s), in the currency shown. Unit USD uses the Exchange rates sheet. Shipping, tax, VAT and duty '
                'are not included. Weight each is the published mass of one ordered unit that goes on the boat; blank means the vendor publishes none.' % OP.CHECKED)
    _header(ws, HR, ORDER_COLS)
    row = HR + 1
    first = row
    for ln in lines:
        note = ln['note']
        if ln['qty_note']:
            note = 'QTY: %s  %s' % (ln['qty_note'], note)
        if ln['sub']:
            note = 'SUBSTITUTE: %s  %s' % (ln['sub'], note)
        vals = [ln['group'], ln['item'], ln['qty'], ln['unit'], ln['vendor'], ln['part_no'], ln['price'], ln['cur'], None, None, ln['mass'], None, ln['basis'],
                ln['stock'], ln['checked'], ln['url'], 'Yes' if ln['sub'] else 'No', note]
        for i, v in enumerate(vals, 1):
            c = ws.cell(row=row, column=i, value=clean(v))
            c.alignment = WRAP
        ws.cell(row=row, column=9, value='=IF(G%d="","",G%d*VLOOKUP(H%d,\'Exchange rates\'!$A$%d:$B$%d,2,FALSE))' % (row, row, row, FX_FIRST, FX_LAST))
        ws.cell(row=row, column=10, value='=IF(OR(I%d="",C%d=""),"",I%d*C%d)' % (row, row, row, row))
        ws.cell(row=row, column=12, value='=IF(OR(K%d="",C%d=""),"",K%d*C%d)' % (row, row, row, row))
        for col in (9, 10, 11, 12):
            ws.cell(row=row, column=col).alignment = WRAP
        ws.cell(row=row, column=7).number_format = '#,##0.00'
        ws.cell(row=row, column=9).number_format = '$#,##0.00'
        ws.cell(row=row, column=10).number_format = '$#,##0.00'
        ws.cell(row=row, column=11).number_format = '#,##0.0'
        ws.cell(row=row, column=12).number_format = '#,##0.0'
        lk = ws.cell(row=row, column=16)
        lk.hyperlink = ln['url']
        lk.font = LINK
        if ln['sub']:
            ws.cell(row=row, column=17).fill = SUBFILL
        row += 1
    last = row - 1
    ws.cell(row=row, column=2, value='TOTAL').font = BOLD
    t = ws.cell(row=row, column=10, value='=SUM(J%d:J%d)' % (first, last))
    t.font = BOLD
    t.number_format = '$#,##0.00'
    t = ws.cell(row=row, column=12, value='=SUM(L%d:L%d)' % (first, last))
    t.font = BOLD
    t.number_format = '#,##0.0'
    _widths(ws, ORDER_W)
    ws.freeze_panes = ws.cell(row=HR + 1, column=3)
    ws.auto_filter.ref = 'A%d:R%d' % (HR, last)
    return first, last


def sheet_summary(wb, lines, first, last, tot):
    ws = wb.create_sheet('Summary')
    ws['A1'] = 'Summary, parts order v1'
    ws['A1'].font = Font(bold=True, size=14)
    ws['A2'] = 'All figures are formulas on the Order sheet. Shipping, tax, VAT and duty are not included.'
    _header(ws, 4, ['Group', 'Lines', 'Line USD', 'Line weight (g)'])
    r0 = 5
    rng = lambda col: 'Order!$%s$%d:$%s$%d' % (col, first, col, last)
    for i, g in enumerate(OP.GROUPS):
        r = r0 + i
        ws.cell(row=r, column=1, value=g)
        ws.cell(row=r, column=2, value='=COUNTIF(%s,A%d)' % (rng('A'), r))
        c = ws.cell(row=r, column=3, value='=SUMIF(%s,A%d,%s)' % (rng('A'), r, rng('J')))
        c.number_format = '$#,##0.00'
        c = ws.cell(row=r, column=4, value='=SUMIF(%s,A%d,%s)' % (rng('A'), r, rng('L')))
        c.number_format = '#,##0.0'
    rl = r0 + len(OP.GROUPS) - 1
    rt = rl + 1
    ws.cell(row=rt, column=1, value='Grand total').font = BOLD
    ws.cell(row=rt, column=2, value='=SUM(B%d:B%d)' % (r0, rl)).font = BOLD
    c = ws.cell(row=rt, column=3, value='=SUM(C%d:C%d)' % (r0, rl))
    c.font = BOLD
    c.number_format = '$#,##0.00'
    c = ws.cell(row=rt, column=4, value='=SUM(D%d:D%d)' % (r0, rl))
    c.font = BOLD
    c.number_format = '#,##0.0'
    k = rt + 2
    items = [
        ('Grand total (USD)', '=C%d' % rt, '$#,##0.00'),
        ('Total weight on the boat (g), published and calculated masses only', '=D%d' % rt, '#,##0.0'),
        ('Total weight on the boat (kg)', '=D%d/1000' % rt, '0.000'),
        ('Lines without a published weight (Not published or Calculated)', '=COUNTIF(%s,"Not published")+COUNTIF(%s,"Calculated")' % (rng('M'), rng('M')), '0'),
        ('   of which calculated by the model (shaft)', '=COUNTIF(%s,"Calculated")' % rng('M'), '0'),
        ('Lines marked substitute', '=COUNTIF(%s,"Yes")' % rng('Q'), '0'),
        ('Lines in the order', '=COUNTA(%s)' % rng('B'), '0'),
    ]
    for i, (a, f, nf) in enumerate(items):
        ws.cell(row=k + i, column=1, value=a)
        c = ws.cell(row=k + i, column=3, value=f)
        c.number_format = nf
        c.font = BOLD
    n = k + len(items) + 1
    ws.cell(row=n, column=1, value='Weight note').font = BOLD
    ws.cell(row=n + 1, column=1, value=(
        'The total counts the masses in the Order sheet: receiver, two servos (60 g each; the weight model carries the blade servo inside its 80 g mechanism item, so the '
        'model counts it once), motors, jackets (90.7 g listed against 90 g in design.py), ESCs, batteries, connectors, joints and the calculated steel shafts. '
        'Nozzles, props, mounts, hardware and all hull stock have no published weight, so the total is a floor, not the finished boat (the model total is in A-601). '
        'The charger and the transmitter stay ashore.'))
    ws.cell(row=n + 1, column=1).alignment = WRAP
    ws.merge_cells(start_row=n + 1, start_column=1, end_row=n + 1, end_column=4)
    ws.row_dimensions[n + 1].height = 90
    m = n + 3
    ws.cell(row=m, column=1, value='Resolve before ordering').font = BOLD
    todo = []
    for ln in lines:
        if ln['sub']:
            todo.append('Substitute: %s. %s' % (ln['item'], ln['sub']))
    todo.append('Shafts: the listed Romarin shaft is 300 mm; the model needs %.1f mm each. Pick a longer shaft or change the drive layout before ordering.' % __import__('model.geometry', fromlist=['x']).SHAFT_LEN)
    for ln in lines:
        s = ln['stock'].lower()
        if s.startswith('conflicting') or s.startswith('not shown') or s.startswith('not stated'):
            todo.append('Stock unclear: %s (%s). %s' % (ln['item'], ln['vendor'], ln['stock']))
    for i, t in enumerate(todo):
        c = ws.cell(row=m + 1 + i, column=1, value=clean(t))
        c.alignment = WRAP
        ws.merge_cells(start_row=m + 1 + i, start_column=1, end_row=m + 1 + i, end_column=4)
        ws.row_dimensions[m + 1 + i].height = max(30, 15 * (len(t) // 95 + 1))
    _widths(ws, [70, 8, 14, 16])
    return rt


def sheet_rates(wb):
    ws = wb.create_sheet('Exchange rates')
    ws['A1'] = 'Exchange rates (inputs)'
    ws['A1'].font = Font(bold=True, size=14)
    ws['A2'] = 'Change a yellow cell and every Unit USD on the Order sheet follows. Rates are USD per one unit of the currency.'
    _header(ws, 4, ['Currency', 'USD per unit', 'Source', 'Rate date', 'Date checked'])
    src = {
        'USD': 'base currency',
        'EUR': 'ECB euro reference rate, 1 EUR = %.4f USD (%s)' % (OP.EUR_USD, OP.FX_SOURCE),
        'GBP': 'cross rate from the ECB reference rates: %.4f USD / %.5f GBP per EUR = %.5f, entered rounded to 4 places (%s)' % (
            OP.EUR_USD, OP.EUR_GBP, OP.EUR_USD / OP.EUR_GBP, OP.FX_SOURCE),
    }
    for i, (cur, rate) in enumerate(OP.RATES):
        r = FX_FIRST + i
        ws.cell(row=r, column=1, value=cur)
        c = ws.cell(row=r, column=2, value=rate)
        c.number_format = '0.0000'
        if cur != 'USD':
            c.fill = INPUT
        ws.cell(row=r, column=3, value=src[cur]).alignment = WRAP
        ws.cell(row=r, column=4, value=OP.FX_DATE if cur != 'USD' else '')
        ws.cell(row=r, column=5, value=OP.CHECKED if cur != 'USD' else '')
    ws.cell(row=FX_LAST + 2, column=1, value=('The ECB publishes one reference rate per working day; the %s rate is the latest published on %s. Card, bank and marketplace '
                                              'conversion fees are not included. Lines in EUR: ampow.com battery, Lindinger shaft (incl. Austrian VAT). Lines in GBP: '
                                              'Cornwall Model Boats props, Model Boat Bits nozzles (VAT status not stated).' % (OP.FX_DATE, OP.CHECKED)))
    ws.cell(row=FX_LAST + 2, column=1).alignment = WRAP
    ws.merge_cells(start_row=FX_LAST + 2, start_column=1, end_row=FX_LAST + 2, end_column=5)
    ws.row_dimensions[FX_LAST + 2].height = 60
    _widths(ws, [12, 14, 80, 12, 14])


def sheet_sources(wb, lines):
    ws = wb.create_sheet('Sources')
    ws['A1'] = 'Sources, every URL read'
    ws['A1'].font = Font(bold=True, size=14)
    _header(ws, 3, ['URL', 'Vendor', 'Role', 'Used for or reason', 'Date checked'])
    used = {}
    for ln in lines:
        used.setdefault(ln['url'], []).append((ln['vendor'], ln['item']))
    rows = []
    for url, v in used.items():
        rows.append((url, v[0][0], 'Used', '; '.join(i for _, i in v), OP.CHECKED))
    seen = set(used)
    for url, vendor, why in OP.ALTERNATES:
        if url in seen:
            continue
        seen.add(url)
        rows.append((url, vendor, 'Read, not used', why, OP.CHECKED))
    rows.append((OP.FX_SOURCE, 'European Central Bank', 'Used', 'Exchange rates (reference date %s)' % OP.FX_DATE, OP.CHECKED))
    for i, rw in enumerate(rows, 4):
        for j, v in enumerate(rw, 1):
            c = ws.cell(row=i, column=j, value=clean(v))
            c.alignment = WRAP
        ws.cell(row=i, column=1).hyperlink = rw[0]
        ws.cell(row=i, column=1).font = LINK
    ws.freeze_panes = 'A4'
    _widths(ws, [80, 30, 14, 90, 13])


def main(out_dir=None, r=None):
    out_dir = out_dir or os.path.join(ROOT, 'out')
    os.makedirs(out_dir, exist_ok=True)
    r = r or hydro.design()
    lines = OP.lines(r)
    wb = Workbook()
    first, last = sheet_order(wb, lines)
    tot = totals(lines)
    sheet_summary(wb, lines, first, last, tot)
    sheet_rates(wb)
    sheet_sources(wb, lines)
    path = os.path.join(out_dir, NAME)
    wb.save(path)
    return path, tot


if __name__ == '__main__':
    p, t = main()
    print('wrote', p)
    print('grand total USD %.2f, weight %.1f g, lines %d, substitutes %d, not published %d, calculated %d' % (
        t['grand'], t['weight'], t['n'], t['substitutes'], t['no_published'], t['calculated']))
    for g, v in t['by_group'].items():
        print('  %-22s %9.2f' % (g, v))
