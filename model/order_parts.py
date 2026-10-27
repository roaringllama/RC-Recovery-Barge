"""Parts ordering data, v1: one row per purchased line, with the vendor listing found on the check date.

Reusable data: tools/order_sheet.py writes it to a workbook, but nothing here needs openpyxl.

Each line is a dict (see _l): group, item, qty, unit, vendor, part_no, price, cur, mass, basis, stock, url, sub, note, pkey.
  qty     a number, or a string key into hull_quantities() / consumable_quantities() when the model sets the amount
  price   the listed unit price in `cur` (per `unit`), as shown on the page on CHECKED; no price is ever estimated
  mass    published mass in g of one ordered unit that goes on the boat (None when the vendor publishes none)
  basis   'Published', 'Calculated', 'Not published' or 'Stays ashore'
  sub     None, or the reason the line is a substitute for the part named in model/parts.py or the brief
  pkey    key of the matching row in model/parts.py (None for lines that have no row there)
Quantities come from the model (design.py through model/schedules.py) with design.WASTE (10 percent) allowance; the arithmetic is
returned as note text so the spreadsheet can show it.
"""
import math

import design as D
from . import geometry as G0
from . import parts as P0

CHECKED = '2026-10-27'                 # date the listings were read
FX_DATE = '2026-10-26'                 # ECB reference rate date (the ECB publishes one rate per working day)
FX_SOURCE = 'https://www.ecb.europa.eu/stats/shared/pdf/eurofxref.pdf'
EUR_USD = 1.1188                       # USD per EUR, ECB reference rate of FX_DATE
EUR_GBP = 0.8382                       # GBP per EUR, ECB reference rate of FX_DATE
GBP_USD = round(EUR_USD / EUR_GBP, 4)  # USD per GBP, cross rate (1.33477 unrounded)
RATES = [('USD', 1.0), ('EUR', EUR_USD), ('GBP', GBP_USD)]   # USD per one unit of the currency

GROUPS = ['Radio and servos', 'Power', 'Drivetrain', 'Steering and sealing', 'Cooling', 'Blades', 'Hatches', 'Hull materials', 'Consumables']


def _l(group, item, qty, unit, vendor, part_no, price, cur, mass, basis, stock, url, sub=None, note='', pkey=None):
    return dict(group=group, item=item, qty=qty, unit=unit, vendor=vendor, part_no=part_no, price=price, cur=cur, mass=mass, basis=basis,
                stock=stock, url=url, sub=sub, note=note, pkey=pkey, checked=CHECKED)


# ---- quantities that come from the model ------------------------------------------------------------------------------
def hull_quantities(r=None):
    """Hull stock and hatch hardware from the schedules. Returns {key: (qty, arithmetic text)}."""
    from model import hydro, schedules as S, geometry as G
    r = r or hydro.design()
    zd = r['deck']
    pl = S.panels(zd)
    rows = S.blocking(zd, pl)
    hs = S.hatches(zd)
    ht = S.hatch_totals(hs)
    sc = S.stick_counts(rows, ht['rim_blocking'])       # stick_counts already carries the (1 + WASTE) factor
    w = 1 + D.WASTE
    sheet = D.STOCK_W * D.STICK_L                        # one 1/8 x 3 x 36 in sheet, mm2
    hull = S.hull_area_total(pl)
    trunk_cap = sum(p['qty'] * p['area'] for p in pl if p['where'] in ('trunk', 'cap'))
    frames = 0.0
    for f in S.frames(zd):
        sp = f['w_in'] * f['h'] - f['open_w'] * f['open_h']
        tu = f['tun_w'] * f['tun_h'] if f['tunnel_solid'] else f['tun_w'] * f['tun_h'] - (f['tun_w'] - 2 * f['rib']) * (f['tun_h'] - 2 * f['rib'])
        frames += 2 * sp + tu                            # two sponson pieces and one tunnel piece per frame
    lids = sum(h['qty'] * h['flange_L'] * h['flange_W'] for h in hs)
    plugs = sum(h['qty'] * h['plug_L'] * h['plug_W'] * D.PLUG_LAYERS for h in hs)
    md = S.mount_dims()
    mounts = 2 * md['l'] * md['w'] * md['layers']
    rails = 2 * 2 * D.RAIL_W * D.BAT['l']
    net = hull + trunk_cap + frames + lids + plugs + mounts + rails
    strips = math.ceil(sc['back_len'] / D.STICK_L)
    per_sheet = math.floor(D.STOCK_W / D.BACK_W)
    n_sheets = math.ceil(net * w / sheet + strips / per_sheet)
    out = {}
    out['balsa'] = (n_sheets,
                    'Net sheet area %.0f cm2 = skin %.0f (A-103, %.2f m2) + trunks and bow caps %.0f + frames %.0f + hatch lids %.0f + plugs (%d layers) %.0f '
                    '+ motor mounts %.0f + battery rails %.0f. x %.2f waste = %.0f cm2 / sheet %.0f cm2 (%.1f x %.1f in) = %.2f sheets. Seam backing: %.1f m '
                    '(A-501 J5, waste included) = %d strips of %.2f mm, %d strips per %.1f mm sheet = %.2f sheets. Total %.2f, rounded up to %d. '
                    'Area estimate; real nesting needs a cutting plan.' % (
                        net / 100, hull / 100, hull / 1e6, trunk_cap / 100, frames / 100, lids / 100, D.PLUG_LAYERS, plugs / 100, mounts / 100, rails / 100,
                        w, net * w / 100, sheet / 100, D.STICK_L / 25.4, D.STOCK_W / 25.4, net * w / sheet,
                        sc['back_len'] / 1000, strips, D.BACK_W, per_sheet, D.STOCK_W, strips / per_sheet,
                        net * w / sheet + strips / per_sheet, n_sheets))
    tri = sc['tri_len'] + sc['wedge_len']
    out['stock'] = (math.ceil(tri / D.STICK_L),
                    'Triangular blocking %.1f m (A-501: raw %.1f m + rim blocking %.1f m, /2 because each 3/8 stick rips into two, x %.2f waste = %.1f m) '
                    '+ corner wedges %.1f m (x %.2f waste) = %.1f m / %.1f mm stick = %.2f, rounded up to %d.' % (
                        sc['tri_len'] / 1000, (sc['tri_len'] * 2 / w - ht['rim_blocking']) / 1000, ht['rim_blocking'] / 1000, w, sc['tri_len'] / 1000,
                        sc['wedge_len'] / 1000, w, tri / 1000, D.STICK_L, tri / D.STICK_L, math.ceil(tri / D.STICK_L)))
    ch = sc['chine_len'] / D.STICK_L
    out['chine'] = (math.ceil(ch) + 1,
                    'Chine stringers %.2f m (A-501 J2, x %.2f waste included) / %.1f mm stick = %.2f sticks, rounded up to %d, plus 1 spare because the '
                    'margin over 2 sticks is only %.0f percent.' % (sc['chine_len'] / 1000, w, D.STICK_L, ch, math.ceil(ch), (math.ceil(ch) - ch) / ch * 100))
    cord_m = ht['cord'] * w / 1000
    out['cord'] = (math.ceil(cord_m / 0.9144),
                   'Hatch cord loops %.3f m (A-503, %d lids, includes splice laps) x %.2f waste = %.3f m / 0.9144 m per 3 ft unit = %.2f, rounded up to %d.' % (
                       ht['cord'] / 1000, ht['lids'], w, cord_m, cord_m / 0.9144, math.ceil(cord_m / 0.9144)))
    out['latches'] = (ht['latches'], '%d lids x %d latches per lid (A-503) = %d.' % (ht['lids'], D.LATCH_PER_LID, ht['latches']))
    bl = G.blade_params()
    ba = G.blade_area()
    chord = 2 * bl['R'] * math.sin(math.radians(bl['sector_deg'] / 2))
    need_len = bl['R'] + 10
    out['g10'] = (1,
                  'Two blades, each a R%.0f x %.0f deg sector = %.0f mm2 (G.blade_area). A sector is %.0f mm long and %.0f mm across the arc; one flipped '
                  'against the other nests in about %.0f x %.0f mm. A 300 x 300 mm (12 x 12 in) sheet is shorter than the %.0f mm blade, so the smallest '
                  'ePlastics 12 in wide length that fits is 24 in (610 mm).' % (bl['R'], bl['sector_deg'], ba, bl['R'], chord, need_len, chord + 10, bl['R']))
    # glass cloth and epoxy
    m2 = hull * 2 / 1e6                                  # outside and inside, same area (build_list convention)
    cloth_m2 = m2 * w
    run_m = cloth_m2 / (38 * 0.0254)
    out['cloth'] = (math.ceil(run_m / 0.9144),
                    'Hull skin %.3f m2 x 2 faces (outside cloth, inside seal coat cloth) = %.3f m2 x %.2f waste = %.3f m2; 38 in (0.965 m) wide cloth: '
                    '%.3f m = %.2f yd of length, rounded up to %d yd. Blades are G10, no glass.' % (hull / 1e6, m2, w, cloth_m2, run_m, run_m / 0.9144, math.ceil(run_m / 0.9144)))
    cloth_g = cloth_m2 / w * 71.2                        # 2.1 oz/yd2 = 71.2 g/m2
    epoxy_g = (hull / 1e6 * (D.GLASS_OUT + D.GLASS_IN) - cloth_g) * w
    kit_g = 118 * 1.1                                    # 4 oz kit = 118 ml, mixed density about 1.1 g/ml (ASSUMED)
    ek = math.ceil(epoxy_g / kit_g)
    if (ek - epoxy_g / kit_g) / (epoxy_g / kit_g) < 0.05:
        ek += 1                                          # estimate of an ESTIMATE: keep a spare kit when the margin is under 5 percent
    out['epoxy'] = (ek,
                    'Finish mass %.0f g (%.3f m2 x (%.0f outside + %.0f inside) g/m2, design.py ESTIMATES) less cloth %.0f g (2.1 oz/yd2 = 71.2 g/m2) '
                    '= %.0f g epoxy x %.2f waste = %.0f g. One 4 oz kit is 118 ml, about %.0f g mixed (density 1.1 g/ml ASSUMED) = %.2f kits, rounded up to %d.' % (
                        hull / 1e6 * (D.GLASS_OUT + D.GLASS_IN), hull / 1e6, D.GLASS_OUT, D.GLASS_IN, cloth_g, epoxy_g / w, w, epoxy_g, kit_g,
                        epoxy_g / kit_g, math.ceil(epoxy_g / kit_g)) + (' Plus one spare kit because the margin is under 5 percent.' if ek > math.ceil(epoxy_g / kit_g) else ''))
    return out


def lines(r=None):
    """All order lines with quantities resolved. Returns a list of dicts; each gets 'qty_note' (arithmetic or the source of the count)."""
    hq = hull_quantities(r)
    out = []
    for ln in LINES:
        ln = dict(ln)
        q = ln['qty']
        if isinstance(q, str):
            ln['qty'], ln['qty_note'] = hq[q]
            ln.pop('qty_why', None)
        else:
            ln['qty_note'] = ln.pop('qty_why', '')
        out.append(ln)
    return out


# ---- the lines --------------------------------------------------------------------------------------------------------
R, P, DR, ST, CO, BL, HA, HU, CS = GROUPS

LINES = [
    # ---- radio and servos
    dict(_l(R, 'Flysky i6X 6-Channel AFHDS 2A Air Radio System w/iA6B Receiver (FS-i6X transmitter and FS-iA6B receiver)', 1, 'set', 'Hiawatha Hobbies (US)',
            'FSYI6XIA6B', 69.99, 'USD', 14.9, 'Published', 'Add to Cart shown; no stock count',
            'https://hiawathahobbies.com/products/flysky-i6x-6-channel-afhds-2a-air-radio-system-wia6b-receiver', None,
            'Weight each is the receiver only (14.9 g). The transmitter is 392 g (13.83 oz on the vendor page) and stays ashore. Same set at Island Hobby Nut, $69.99 '
            '(SKU FSY-I6X+IA6B). Price shown on the page as $6999, read as $69.99 from the page metadata.', 'rx'), qty_why='One transmitter and one receiver.'),
    dict(_l(R, 'DSSERVO DS3225 MG Servo Motor, steering (180 deg, metal horn)', 1, 'each', 'aifitlab (ships from China)', 'DS3225MG', 20.00, 'USD', 60.0, 'Published',
            'Add to cart shown; no stock count', 'https://aifitlab.com/products/dsservo-ds3225-mg-servo-motor', None,
            'Weight 60 g from the vendor page. IP66 per DS3225 sheets, not immersion rated. US shipping is by the cheapest carrier from China; an eBay 2-pack '
            'from a Texas seller (rcexpress, 2 for $29.95, ebay.de/itm/334698838029) was active in an earlier snapshot and is a possible alternate.', 'servo_steer'),
         qty_why='One steering servo on the tunnel roof (design.py STEER_SERVO).'),
    dict(_l(R, 'DSSERVO DS3225 MG Servo Motor, blade (180 deg, metal horn)', 1, 'each', 'aifitlab (ships from China)', 'DS3225MG', 20.00, 'USD', 60.0, 'Published',
            'Add to cart shown; no stock count', 'https://aifitlab.com/products/dsservo-ds3225-mg-servo-motor', None,
            'One blade servo drives both blades (BLADE_SERVO_QTY 1). The weight model carries this servo inside the 80 g blade mechanism item, so the total here '
            'counts 60 g that the model counts once inside the 80 g.', 'servo_blade'), qty_why='BLADE_SERVO_QTY = 1 in design.py.'),
    dict(_l(R, 'Du-Bro DUB172 2-56 x 12 in Threaded Steel Rod (sold individually)', 2, 'each', 'Superstition Hobbies (US)', 'DUB172', 1.50, 'USD', None, 'Not published',
            'In stock', 'https://superstitionhobbies.com/products/threaded-rods-2-56-x-12-36', None,
            'Nozzle linkage, 2 rods as in parts.py. Motion RC lists the same part but its page would not load. Rod ends are the next line.', 'pushrod'),
         qty_why='parts.py pushrod qty 2.'),
    dict(_l(R, '2-56 x 1/2 in Swivel Ball Links Colored, 12 Pack (DU-BRO)', 1, 'pack of 12', 'Du-Bro (dubro.com, US)', '2135-R (red)', 14.00, 'USD', None, 'Not published',
            'In stock', 'https://www.dubro.com/products/2-56-x-1-2-swivel-ball-link-colored-12pkg', None,
            'Sale price, regular $18.00. The design needs 4 ends (servo horn, tie bar, two spare); a 12 pack is the smallest unit. Motion RC quotes 2 g per assembly for '
            'DUB860, a different SKU, so no weight is recorded here. Kwik-Link clevises (rcdude.com DB109, $2.15) are the alternate.', None),
         qty_why='4 pushrod ends plus spares; pack of 12.'),
    # ---- power
    dict(_l(P, '1200KV Brushless RC Boat Motor (ATO-RB-3670, 36 x 70 mm, 5 mm shaft)', 2, 'each', 'ATO (ato.com)', 'ATO-RB-3670 (SKU ATO-BLDC-RB1200)', 142.87, 'USD', 275.0,
            'Published', 'Not stated; quantity selector and 8 to 12 day delivery estimate shown', 'https://ato.com/1200kv-brushless-rc-boat-motor', None,
            '275 g, 45 A max, 36 V max (vendor page). One per sponson.', 'motor'), qty_why='Two motors.'),
    dict(_l(P, 'Hot Racing Aluminum 36mm Water Cooling Jacket: Traxxas M41 (51 mm OD x 63 mm, 36 mm ID)', 2, 'each', 'Tower Hobbies (US)', 'HRADCB36WC01 (DCB36WC01)', 38.88, 'USD', 90.7,
            'Published', 'In Stock', 'https://www.towerhobbies.com/product/aluminum-36mm-water-cooling-jacket-traxxas-m41/HRADCB36WC01.html', None,
            'Exact part of the model (JACKET_D 51, JACKET_L 63). Weight 3.2 oz = 90.7 g and the 51 x 63 mm size are from the AMR RC page for the same SKU '
            '(amr-rc.com, 17144); the model uses 90 g. Also at RC Express at $38.88. The v3 eBay jacket at $11.66 could not be re-checked.', 'jacket'),
         qty_why='JACKETS is True: one per motor.'),
    dict(_l(P, 'HobbyWing Seaking 60A V3.1 ESC (water cooled, 2-3S)', 2, 'each', 'Graves RC (US)', 'HBW30302200 (Hobbywing 30302200)', 69.99, 'USD', 93.0, 'Published',
            'Not shown on the page (no Add to Cart text either); confirm with the vendor', 'https://gravesrc.com/hbw30302200-hobbywing-seaking-60a-v3-1-esc', None,
            '93 g with cooling pipe. White Rose Hobbies has it at $59.99 but sold out; rcjaz.com $84.10 not available; rcgarage.com AUD 169.95 sold out. The official Hobbywing '
            'North America store now lists only the SeaKing 60A V4 ($49.99); V4 was not checked against forward and reverse and BEC needs, so V3.1 is kept.', 'esc'),
         qty_why='Two ESCs.'),
    dict(_l(P, 'OVONIC 11.1V 3S 5000mAh 50C Lipo Battery for Slash/E-Revo/UDR/X-Maxx (XT60 plug)', 2, 'each', 'ampow.com (Ovonic, ships from Germany)', 'O-50C-5000-3S1P-XT60+TRX', 36.16, 'EUR',
            343.0, 'Published', 'In Stock', 'https://www.ampow.com/products/ovonic-11-1v-3s-5000mah-50c-lipo-battery-with-xt60-trx-plug', None,
            '343 g (+/- 20 g), 155 x 42 x 24 mm: matches BAT in design.py. Sale price shown in EUR, regular EUR 57.73; discount code not applied. The page ships from a Germany '
            'warehouse; check duty and delivery to the US. The Ovonic US store (us.ovonicshop.com) lists this pack at $87.99, out of stock. The 138 x 42 x 28 mm 359 g variant '
            'is a different size and was not used.', 'battery'), qty_why='One pack per sponson.'),
    dict(_l(P, 'Amass XT60H Power Connectors (Male + Female - 5 Sets, 10 Pcs)', 1, 'pack of 5 sets', 'GetFPV (US)', '11788', 8.99, 'USD', 7.0, 'Published', 'In Stock',
            'https://www.getfpv.com/amass-xt60h-power-connectors-male-female-5-sets-10-pcs.html', None,
            '3.5 g per piece on the vendor page. Weight each is 2 pieces installed (one per ESC), 7.0 g. ESCs ship without connectors.', 'xt60'),
         qty_why='One pack covers 2 ESC leads with spares.'),
    dict(_l(P, 'ToolkitRC M6AC 300W 15A 1-6S AC Charger - XT60', 1, 'each', 'Race Day Quads (US)', 'M6AC', 71.99, 'USD', 0.0, 'Stays ashore',
            'Not shown on the page', 'https://racedayquads.com/products/toolkitrc-m6ac-300w-15a-1-6s-ac-charger-xt60', None,
            'Optional; skip if you already own a LiPo balance charger. Not carried on the boat (350 g published at Pyrodrone, where it is sold out at $76.99).', 'charger'),
         qty_why='One charger.'),
    # ---- drivetrain
    dict(_l(DR, 'ROMARIN Stern tube/235 + shaft M4x300 mm', 2, 'each', 'Modellbau Lindinger (Austria)', '9779949 (Krick ro1444)', 11.50, 'EUR', P0.shaft_mass(), 'Calculated',
            'In stock, ships within one business day', 'https://lindinger.at/en/CARS-BOATS/ACCESSORIES/Boat-Accessories/Drive-Shafts/ROMARIN-Sterntube-235-shaft-M4x300mm/9779949', None,
            'Price includes Austrian VAT; the page does not mention shipping to the US, so confirm before ordering. No weight published; the mass here is the 4 mm steel '
            'shaft only, calculated in parts.py (tube excluded). LENGTH PROBLEM: the listed shaft is 300 mm but the model needs %.1f mm each (geometry SHAFT_LEN), so this part is too short as the model '
            'draws it; no longer Romarin 4 mm shaft was found. Harbor Models (US) sells a 4 mm shaft with stuffing tube, HAR2004, 11 in shaft, $29.95, and a 4 mm shaft only, '
            'HAR2022A, 11 in, $10.00, also too short.' % G0.SHAFT_LEN, 'shaft'), qty_why='One shaft and tube per drive line, two lines.'),
    dict(_l(DR, '2pcs 5mm to 4mm Motor Shaft Coupling Universal Joint Connector for BL RC Boat', 1, 'pack of 2', 'eBay: dealbestshop (ships from Shenzhen)', 'item 404668255092',
            16.94, 'USD', 22.0, 'Published', '5 available (eBay page)', 'https://www.ebay.de/itm/404668255092',
            'Substitute: no double CV joint with a published 14 deg continuous rating was found at 5 mm to 4 mm. This is a single alloy universal joint, 23 mm long, 11 mm OD '
            '(CV_OD_ASSUMED is 14), no angle rating published. Nearest alternates: Aeronaut cardan coupling 22 x 4.0/5.0 mm (Lindinger 9798698, EUR 6.10, special order) and '
            'Robbe RO-NAVY universal joint 9 x 23 mm bore 4/5 (Lindinger 9748228, EUR 3.99); neither lists an angle either. Test at 14 deg on the bench.',
            '22 g listed for the listing; read as the pair (eBay does not say). Free shipping, delivery estimate 2 to 12 Nov.', 'ujoint'),
         qty_why='Two joints, one per drive line (one 2-pack).'),
    dict(_l(DR, '3660 Water Cooled Brushless Suitable for 36-40 Motor Mount RC Boat #204', 2, 'each', 'eBay: immortallovesu2 (ships from China)', 'item 152794760694', 25.72, 'USD', None,
            'Not published', '2 available (eBay page)', 'https://www.ebay.com/itm/152794760694',
            'Substitute: the v3 listing (Joyfeel RC, glass fiber stands, $16.64) could not be re-checked; this is a silver anodized aluminum water-cooled mount for 36 to 40 mm '
            'motors. Shipping $3.89 extra. Optional: the model draws a laminated balsa mount, and a 51 mm jacket may not fit a bracket made for the bare 36 mm can.',
            'Check fit with the jacket before buying.', 'mount'), qty_why='One per motor.'),
    dict(_l(DR, 'Raboesch 45mm M4 Threaded 4 Blade L/H Brass Kort Propeller (series 149)', 1, 'each', 'Cornwall Model Boats (UK)', 'RAB149-08', 55.23, 'GBP', None, 'Not published',
            'Not shown on the series page', 'https://www.cornwallmodelboats.co.uk/acatalog/R149-M4.html', None,
            'Price from the series page; the right-hand part shows 55.24 on its own page. VAT status not stated. Left-hand turns anticlockwise from astern. Other sources: Krick '
            'rb149-08 on eBay Germany, EUR 59.99 incl. VAT; Tecnimodel lists the right-hand 149 for 45 mm nozzles (PBRA214907, 1 in stock).', 'prop_l'), qty_why='One left-hand prop.'),
    dict(_l(DR, 'Raboesch 45mm M4 Threaded 4 Blade R/H Kort Propeller (series 149)', 1, 'each', 'Cornwall Model Boats (UK)', 'RAB149-07', 55.24, 'GBP', None, 'Not published',
            'In stock', 'https://www.cornwallmodelboats.co.uk/acatalog/45mm-M4-Threaded-4-Blade-R-H-Kort-Propeller-RAB149_07.html', None,
            'RRP 57.24, saving 2.00. A-type blades, 46.1 mm pitch. VAT status not stated. Order as a matched pair with the port prop.', 'prop_r'), qty_why='One right-hand prop.'),
    dict(_l(DR, 'Kort Nozzles (steerable), TO SUIT 45mm PROPELLER', 2, 'each', 'Model Boat Bits (UK)', 'MBB-KNS (45 mm)', 15.00, 'GBP', None, 'Not published',
            'Not stated; Add To Basket shown', 'https://www.modelboatbits.com/Kort-Nozzles?VariantID=37171&PPCT=1635849747', None,
            'Solid 3D printed, 3 mm post fitted, 50 mm steering tube (too short for the design, which uses the cut stock below), 90 deg tiller arm, Allen key. No weight, length or '
            'OD published. VAT status not stated.', 'nozzle'), qty_why='One per drive line.'),
    # ---- steering and sealing
    dict(_l(ST, 'Round Brass Rod: 3mm OD x 300mm Long (3 Pieces), K&S 9865', 1, 'pack of 3', 'K&S Precision Metals (ksmetals.com, US)', '9865', 9.99, 'USD', None, 'Not published',
            'In stock', 'https://ksmetals.com/products/brrmet-3', None,
            'Nozzle post rod, cut from the 300 mm stock (NOZ_POST_STOCK_L); about 95 mm each, so one rod makes both posts and the pack has spares. Hobbylinc lists the pack at '
            '$5.19 (stock not stated).', 'post_rod'), qty_why='One pack; one 300 mm rod gives both posts.'),
    dict(_l(ST, 'Round Brass Tube: 4mm OD x 0.45mm Wall x 300mm Long (3 Pieces), K&S 9822', 1, 'pack of 3', 'K&S Precision Metals (ksmetals.com, US)', '9822', 9.99, 'USD', None,
            'Not published', 'In stock', 'https://ksmetals.com/products/br45mm-4', None,
            'Bore is 0.122 in (3.1 mm), so the 3 mm rod turns freely. There is no 3 mm bore tube at 3 mm OD; this 4 mm OD tube is the nearest K&S size. Hobbylinc lists it at $7.99 '
            '(stock not stated).', 'post_tube'), qty_why='One pack; one tube gives both sleeves.'),
    dict(_l(ST, 'Traxxas Hull Seals, Stuffing Tube & Push Rod (TRA5725)', 1, 'each', 'RC Street Shop (US)', '5725 (replaces 10325)', 2.99, 'USD', None, 'Not published', 'In stock',
            'https://rcstreetshop.com/accessories/3970-seal-stuffing-tube-spartan.html',
            'Substitute for Traxxas 10325 (classicrcshop.com, $3.99, sold out). 5725 is the current Traxxas stuffing tube and pushrod seal. No dimensions published for either; '
            'PUSHROD_BELLOWS_D is still PENDING. Needed only if the pushrod leaves the hull.', '', 'bellows'), qty_why='One set.'),
    # ---- cooling
    dict(_l(CO, 'M5 Threaded 90 Degree Brass Water Fittings x 2 units (water pickup)', 1, 'pack of 2', 'DY Motor Shop', 'WOB090M5', 6.04, 'USD', None, 'Not published', 'Not shown',
            'https://dymotorshop.com/index.php?main_page=index&cPath=9_23_43', None,
            'One pickup per sponson, so one pack of 2. Position is PENDING (COOL_PICKUP_X). Link is the category page, which lists the part.', 'pickup'), qty_why='Two pickups.'),
    dict(_l(CO, 'M6 Threaded 90 Degree Brass Water Fittings x 2 units (water outlet)', 1, 'pack of 2', 'DY Motor Shop', 'model number not shown', 6.04, 'USD', None, 'Not published',
            'Not shown', 'https://dymotorshop.com/index.php?main_page=index&cPath=9_23_43', None,
            'One outlet per sponson, so one pack of 2. Position is PENDING (COOL_OUTLET_X). Silicone cooling tube is not on this list: not in the brief.', 'outlet'),
         qty_why='Two outlets.'),
    # ---- blades
    dict(_l(BL, 'G10/FR4 natural sheet, 0.060 x 12 x 24 in (1.5 mm)', 'g10', 'each', 'ePlastics (US)', 'G10NAT-060X12X24', 25.55, 'USD', None, 'Not published',
            'Not shown on the page', 'https://www.eplastics.com/fiberglass/sheets/g10-fr4-epoxy',
            'Substitute: 0.060 in (1.52 mm) replaces 1.5 mm, and 12 x 24 in replaces the 300 x 300 mm in the brief, because the R375 blade is longer than 305 mm (see the '
            'arithmetic). The 12 x 12 in sheet, G10NAT-060X12X12, is $12.79. Price is the quantity 1 to 4 tier; sheets are nominal, may run 0.75 in under size. '
            'Mass would be about 540 g at 1.9 g/cm3 (computed, vendor publishes none).', '', None), qty_why=''),
    # ---- hatches
    dict(_l(HA, 'Metric Silicone O-ring Cord 1.5mm Price for 3 ft', 'cord', '3 ft length', 'Oringsandmore (eBay, ships from Virginia)', 'item 163538644750', 6.90, 'USD', None,
            'Not published', '999 available (eBay page)', 'https://www.ebay.com/itm/Metric-Silicone-O-ring-Cord-1-5mm-Price-for-3-ft-/163538644750', None,
            'Shipping $6.55 extra. The photo caption says 2 ft while the title says 3 ft; check on arrival. Use silicone grease on the cord. Splice with CA glue.', 'cord'),
         qty_why=''),
    dict(_l(HA, 'M3 x 12mm Knurled Head Thumb Screw Black 20pcs', 1, 'pack of 20', 'Walmart (Tasharina Corp)', 'M3x12 thumb screw, 20 pcs', 8.08, 'USD', None, 'Not published',
            'Add to cart shown; no stock count', 'https://www.walmart.com/ip/M3-x-12mm-Knurled-Head-Thumb-Screw-Black-20pcs-for-Computer-PC-Case/194011182', None,
            'Black zinc plated metal, 20 screws; the design needs 12 (qty basis below). Not stainless: rinse and dry after use.', 'm3'), qty_why='12 latches; pack of 20.'),
    dict(_l(HA, '100Pcs M3 X 0.5mm 304 Stainless Steel Self-Lock Nylon Inserted Hex Nuts', 1, 'pack of 100', 'eBay: GM_IMPORTS (ships from New York)', 'item 255539291387', 11.50, 'USD',
            None, 'Not published', '4 available (eBay page)', 'https://www.ebay.com/itm/255539291387', None,
            'Nylon insert nuts, glued into the ply pad. Plain M3 nuts were not found in a small pack from a US seller. Aspen Fasteners lists boxes of 2,500 or more. '
            'Need 12.', 'm3'), qty_why='12 nuts; pack of 100.'),
    # ---- hull materials
    dict(_l(HU, '1/8 x 3 x 36 Balsa Wood Sheet', 'balsa', 'sheet', 'National Balsa (US)', '18336', 3.40, 'USD', None, 'Not published',
            'Conflicting: product page shows both "Sold out" and "Add to cart"; collection page lists it in stock', 'https://www.nationalbalsa.com/products/18336', None,
            'Sale price, regular $4.76. Nationwide shipping $19.95 and a $50 minimum order per the site. Midwest 1/8 x 3 x 36 in packs of 10 at Hobbylinc (mid6304, $39.49) are '
            'the alternate.', 'balsa'), qty_why=''),
    dict(_l(HU, '3/8 x 3/8 x 36 Balsa Wood Stick', 'stock', 'stick', 'National Balsa (US)', '383836', 1.33, 'USD', None, 'Not published',
            'Conflicting: "Sold out" label and "Add to cart" both shown; collection page lists it in stock', 'https://www.nationalbalsa.com/products/383836', None,
            'Sale price, regular $1.86. Ripped on the diagonal for triangular blocking.', 'stock'), qty_why=''),
    dict(_l(HU, '3/4 x 3/4 x 36 Balsa Wood Stick', 'chine', 'stick', 'National Balsa (US)', '3/4 x 3/4 x 36 (handle not shown)', 4.54, 'USD', None, 'Not published', 'In stock (collection page)',
            'https://www.nationalbalsa.com/collections/3-4-balsa-wood-sticks', None,
            'Sale price, regular $5.72. Chine stringers. Balsa USA has it at $3.87 (SKU 854) but every grade is sold out.', 'chine'), qty_why=''),
    dict(_l(HU, '1/8 x 12 x 12 Aircraft Plywood (birch, 6 ply)', 1, 'sheet', 'National Balsa (US)', '181212bp', 10.35, 'USD', None, 'Not published',
            'Conflicting: "Sold out" label and "Add to cart" both shown', 'https://www.nationalbalsa.com/products/181212bp', None,
            'Sale price, regular $14.49. Latch pads (12 x %.1f mm squares), servo pads, motor clamp caps and hatch rims come to well under one 12 x 12 in sheet '
            '(92,900 mm2).' % D.LATCH_PAD, 'ply'), qty_why='One sheet covers the pads and caps; area shown in notes.'),
    # ---- consumables
    dict(_l(CS, 'Style 112, 2.1 oz. X 38in. Plain Weave E-Glass', 'cloth', 'linear yard', 'Fiberglass Supply (US)', 'Style 112', 7.02, 'USD', None, 'Not published', 'In stock (page metadata)',
            'https://fiberglasssupply.com/style-112-2-1-oz-x-38in-plain-weave-e-glass/', None,
            'The page shows 7.02 without a unit; the site says all cloth is sold by the linear yard, so this is read as per linear yard. Hobbico 2 oz cloth (Hobbylinc) is discontinued.',
            'glass'), qty_why=''),
    dict(_l(CS, 'Pacer Technology Zap Z-Poxy Finishing Resin 4oz', 'epoxy', 'kit', 'Hobby Etc (US)', 'PAAPT41', 14.99, 'USD', None, 'Not published', 'Add to Cart shown; no stock count',
            'https://store.hobbyetc.com/parts/view/104890', None,
            'Sale price, regular $16.94. 4 oz kit = one 2 oz bottle of resin and one of hardener; shipping weight 178.6 g. Thin laminating resin for glass over balsa.', 'glass'), qty_why=''),
    dict(_l(CS, '5 Minute 2 Part Epoxy Z-Poxy 8oz', 1, 'kit', 'Hobby Etc (US)', 'PAAPT38', 19.99, 'USD', None, 'Not published', 'Add to Cart shown; no stock count',
            'https://store.hobbyetc.com/parts/view/21228', None,
            'Joints, motor mounts and ply pads. Sale price, regular $21.12. Quantity is a judgment, not computed from the model.', None), qty_why='One kit; not computed from the model.'),
    dict(_l(CS, 'ZAP Zap-A-Gap Medium CA+ Glue Gap Filling Formula PT-02 1oz', 1, 'bottle', 'Buddy RC (US)', 'ZAP-PT02', 9.59, 'USD', None, 'Not published', 'Add to cart shown; no stock count',
            'https://www.buddyrc.com/products/pt-02-1-oz-zap-a-gap-ca', None,
            'Sale price. Hobby Etc has it at $8.99 but not in stock. Cord splices and tack gluing. Quantity is a judgment.', None), qty_why='One bottle; not computed from the model.'),
    dict(_l(CS, '3M Wet or Dry Sandpaper, Assorted Sheets, 220, 320, 400 Grits, 9 in. x 11 in., 5 Pack', 1, 'pack of 5', 'Walmart (Coral Port, fulfilled by Walmart)',
            '3M assorted 220/320/400', 10.78, 'USD', None, 'Not published', 'Add to cart shown; no stock count', 'https://www.walmart.com/ip/21129775', None,
            'Finishing grits only. A coarse grit (80 to 120) for planking was not sourced: the 3M 120 grit sheets found are sold in 50-sheet inner packs without a price. '
            'Quantity is a judgment.', None), qty_why='One pack; not computed from the model.'),
    dict(_l(CS, 'Traxxas 1657 Silicone Grease, Waterproof RC Lubricant', 1, 'tube', 'Superstition Hobbies (US)', '1657', 4.00, 'USD', None, 'Not published', 'In stock',
            'https://superstitionhobbies.com/products/traxxas-1647-silicone-grease-lube', None,
            'Hatch cord and pushrod seal. The page address says 1647 and the SKU says 1657; the size is not listed. Quantity is a judgment.', None),
         qty_why='One tube; not computed from the model.'),
]

# Listings read and not used, for the Sources sheet: (url, vendor, why not used)
ALTERNATES = [
    ('https://www.whiterosehobbies.com/products/hobbywing-30302200-seaking-60a-v3-1-brushless-marine-esc', 'White Rose Hobbies', 'SeaKing 60A V3.1 at $59.99, sold out'),
    ('https://www.rcjaz.com/hobbywing-seaking-60a-v31-30302200-p-9014.html', 'RCJAZ', 'SeaKing 60A V3.1 at $84.10, not available'),
    ('https://www.rcgarage.com/products/hobbywing-seaking-60a-v3-1-sensorless-brushless-marine-esc-hw30302200', 'RC Garage', 'SeaKing 60A V3.1 at AUD 169.95, sold out'),
    ('https://www.hobbywingdirect.com/products/seaking-60a-v3-esc', 'Hobbywing North America', 'Store now lists the SeaKing 60A V4 at $49.99 and no V3.1'),
    ('https://upgraderc.be/products/flysky-fs-i6x-10ch-2-4ghz-afhds-2a-transmitter-w-ia6b-ia10b-receiver', 'Upgrade RC', 'FS-i6X with iA6B, EUR 79.99, sold out'),
    ('https://islandhobbynut.com/products/flysky-i6x-6-channel-afhds-2a-air-radio-system-w-ia6b-receiver', 'Island Hobby Nut', 'Same radio set, $69.99; alternate to Hiawatha Hobbies'),
    ('https://usa.banggood.com/Flysky-i6X-FS-i6X-2_4GHz-10CH-AFHDS-2A-RC-Transmitter-With-X6B-or-IA6B-or-A8S-Receiver-for-FPV-RC-Drone-p-1090406.html', 'Banggood USA', 'Stock 0, no shipping to the US'),
    ('https://www.walmart.com/ip/403571177', 'Walmart', 'FS-i6X with iA6B, $62.99, out of stock'),
    ('https://www.ebay.com/itm/146372493939', 'eBay: WeShipNow', 'FS-i6X with iA6B, $98.99, listing ended'),
    ('https://www.ebay.de/itm/334698838029', 'eBay: rcexpress', 'DS3225MG 2-pack $29.95 from Texas; page snapshot of uncertain age, "last item"; alternate'),
    ('https://www.ebay.com/itm/393594037921', 'eBay: Qjtamia', 'DS3225MG 2-pack $37.04, out of stock'),
    ('https://www.ebay.com/itm/254985471612', 'eBay: rcmodelpart369', 'DS3225MG $20.99 plus $5.69 shipping from Shenzhen; alternate'),
    ('https://usa-m.banggood.com/DSSERVO-DS3225MG-25KG-Waterproof-me%3Cx%3Etal-Gear-Digital-Servo-For-1-or-8-1-or-10-1-or-12-RC-Cars-p-1542156.html', 'Banggood USA', 'DS3225MG $18.99, stock not shown'),
    ('https://vxb.com/products/dual-pack-270-degree-beefy-torque-digital-servo-fo', 'VXB', 'DS3225 2-pack, inconsistent $88.88 / $150 price, MG not confirmed'),
    ('https://www.motionrc.com/collections/pushrods/products/du-bro-2-56-305mm-12-threaded-rod-dub172', 'Motion RC', 'DUB172 page would not load'),
    ('https://motionrc.com/products/du-bro-2-56-swivel-ball-link-12-pack-dub860', 'Motion RC', 'DUB860 ball links, price garbled ($2089), weight 2 g each'),
    ('https://rcdude.com/dubro-kwik-link-clevis-2-56.html', 'RC Dude Hobbies', 'Kwik-Link clevis 2-56 DB109, $2.15, in stock; alternate to the ball links'),
    ('https://www.amainhobbies.com/flysky-i6x-6channel-afhds-2a-air-radio-system-w-ia6b-receiver-fsy-i6xia6b/p1674181', 'AMain Hobbies', 'Same radio set; page showed no price to the reader'),
    ('https://amr-rc.com/aluminum-36mm-water-cooling-jacket-m41.html', 'AMR RC (Canada)', 'Source of the jacket weight and size (3.2 oz, 51 x 63 mm); CAD 56.59'),
    ('https://www.rcexpress.com/hot-racing-traxxas-dcb-m41-catamaran-aluminum-water-cooling-jacket-dcb36wc01/', 'RC Express', 'Same jacket at $38.88, in stock; alternate to Tower Hobbies'),
    ('https://vxb.com/products/beefy-aluminum-water-cooling-jacket-for-36mm-rc-bo', 'VXB', '36 mm jacket 50 mm long, 31 g, $49.99; shorter than the design'),
    ('https://www.ebay.com/itm/164006076772', 'eBay: cinedx', '36 mm jacket sleeve, $14.17 plus $9.30 shipping, 45 or 60 mm long, OD not listed'),
    ('https://pyrodrone.com/products/toolkitrc-m6ac-1-6s-ac-100w-dc-300w-15a-battery-charger-xt60', 'Pyrodrone', 'M6AC at $76.99, sold out; source of the 350 g weight'),
    ('https://ampow.com/ovonic-50c-5000mah-3s1p-xt60-lipo-battery.html', 'Ampow', 'Ovonic 138 x 42 x 28 mm variant, EUR 34.36, out of stock'),
    ('https://us.ovonicshop.com/products/ovonic-11-1v-3s-5000mah-50c-lipo-battery-with-xt60-trx-plug', 'Ovonic US store', 'Same pack as the chosen one, $87.99, out of stock'),
    ('https://us.ovonicshop.com/products/ovonic-50c-11-1v-5000mah-3s1p-xt60-lipo-battery', 'Ovonic US store', '138 x 42 x 28 mm variant, $32.99, out of stock'),
    ('https://www.ovonicshop.com/products/ovonic-11-1v-3s-5000mah-50c-lipo-battery-with-xt60-trx-plug', 'Ovonic shop (AU)', 'AUD 45.99, Australia warehouse'),
    ('https://rcdrone.top/ar/products/ovonic-5000mah-3s-lipo-battery-2', 'rcdrone.top', 'Ovonic 3S 5000, $52.90, sold out'),
    ('https://www.harbormodels.com/shaftstuffbox.html', 'Harbor Models (US)', 'HAR2004 4 mm shaft and stuffing tube, 11 in shaft, $29.95, in stock; shorter than needed'),
    ('https://www.harbormodels.com/prsh.html', 'Harbor Models (US)', 'HAR2022A 4 mm shaft only, 11 in, $10.00'),
    ('https://lindinger.at/en/CARS-BOATS/ACCESSORIES/Boat-Accessories/Coupling-and-Accessories/AERONAUT-Cardan-coupling-22-4.0-5.0mm/9798698', 'Modellbau Lindinger', 'Aeronaut cardan coupling 22 x 4.0/5.0, EUR 6.10, special order; alternate joint'),
    ('https://www.lindinger.at/en/CARS-BOATS/ACCESSORIES/Boat-Accessories/Coupling-and-Accessories/', 'Modellbau Lindinger', 'Coupling category: Robbe RO-NAVY 9 x 23 mm bore 4/5, EUR 3.99; alternate joint'),
    ('https://www.ebay.com/itm/134316279559', 'eBay: Promise Hobby', 'B36 water cool motor mount, $23.99 plus $6.00 shipping from Shanghai; alternate mount'),
    ('https://www.tecnimodel.com/en/m4-thread/11531-4-blade-brass-propeller-for-o45mm-m4-nozzles-range-149-type-a-raboesch-clockwise.html', 'Tecnimodel (France)', 'Raboesch 149 right-hand 45 mm, 1 in stock, price not shown; alternate'),
    ('https://www.ebay.de/p/1177785848', 'eBay: RC Multistore Modellbau', 'Krick rb149-08 left-hand 45 mm, EUR 59.99; alternate'),
    ('https://cornwallmodelboats.co.uk/acatalog/R147-M4.html', 'Cornwall Model Boats', 'Series 147 open-water 45 mm props (RAB147-15/16, GBP 25.75); not nozzle-specific'),
    ('https://www.hobbylinc.com/k-s-round-brass-rod-3mm-x-300mm-3-hobby-and-craft-metal-rod-9865', 'Hobbylinc', 'K&S 9865 at $5.19, stock not stated; alternate'),
    ('https://www.hobbylinc.com/k-s-round-brass-tube-45mm-x-4mm-x-300mm-3-hobby-and-craft-metal-tubing-9822', 'Hobbylinc', 'K&S 9822 at $7.99, stock not stated; alternate'),
    ('https://classicrcshop.com/products/traxxas-stuffing-tube-seal-and-pushrod-set-10325.oembed', 'Classic RC Shop', 'Traxxas 10325 at $3.99, out of stock'),
    ('https://classicrcshop.com/products/stuffing-tube-and-push-rod-hull-seals', 'Classic RC Shop', 'Traxxas 5725 at $2.99, 1 in stock; alternate'),
    ('https://www.hobbylinc.com/htm/mid/mid6304.htm', 'Hobbylinc', 'Midwest 1/8 x 3 x 36 balsa, 10 sheets $39.49; alternate to National Balsa'),
    ('https://balsausa.com/products/3-4-x-3-4-x-36-balsa-stick', 'Balsa USA', '3/4 x 3/4 x 36 stick $3.87, every grade sold out'),
    ('https://www.hobbylinc.com/htm/hca/hcahcar5010.htm', 'Hobbylinc', 'Hobbico 2 oz cloth, discontinued'),
    ('https://store.hobbyetc.com/parts/view/21203', 'Hobby Etc', 'Zap-A-Gap 1 oz $8.99, not in stock'),
    ('https://www.aspenfasteners.com/m3-0-5-din-934-iso-4032-metric-hex-finished-nuts-a2-stainless-steel/', 'Aspen Fasteners', 'M3 nuts sold in boxes of 2,500 or more'),
    ('https://www.ebay.de/itm/376144774054', 'eBay: HKDZ-Tech01', 'M3 thumb screws; no shipping to the US'),
    ('https://www.ebay.com/itm/156770033591', 'eBay: toolmaster88', 'M3 x 12 brass thumb screws 10 pcs $13.60, last one; alternate'),
    ('https://callapg.com/15-mm-059-silicone-o-ring-cord-70-du', 'Apple Rubber / APG', '1.5 mm silicone cord by the foot, price shown only after login'),
    ('https://www.ebay.com/itm/332727062603', 'eBay: Huapingshu', 'Silicone cord 1.5 mm, $6.12 each (1, 2, 5 or 10 m), ships from Shenzhen; alternate'),
    ('https://www.eplastics.com/fiberglass/sheets/g10-fr4-epoxy', 'ePlastics', 'Used for the G10 line'),
]
