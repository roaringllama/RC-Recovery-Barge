"""Parts table: one source for vendor data and published weights.

Each Part: key, group, item, part_no, spec, qty, unit, price, cur, mass (g each, or None), basis, wsource, vendor, link, note.
price is the published unit price in the currency `cur` (None when not priced). mass is None when the vendor publishes none.
basis is 'Published', 'Calculated', 'Not published' or 'Stays ashore'.
Masses of items that design.py already carries (motor, jacket, ESC, battery, receiver, servo) are read from design.py, so there is
one number; model/weights.py reads every published mass from here.
Prices and links were re-checked on 2026-10-27 (see tools/order_sheet.py and model/order_parts.py for the dated order sheet, with stock status and substitutes); prices change, so check them again before ordering.
"""
import math
from collections import namedtuple
import design as D
from . import geometry as G

Part = namedtuple('Part', 'key group item part_no spec qty unit price cur mass basis wsource vendor link note')


def shaft_length():
    """Drive shaft length each, mm, derived in geometry (G.SHAFT_LEN)."""
    return G.SHAFT_LEN


def shaft_mass():
    """Steel drive shaft, g each, from the design diameter and length (cm3 times g/cm3)."""
    return math.pi * (D.SHAFT_D / 2) ** 2 * shaft_length() / 1000 * D.STEEL_RHO


def _p(key, group, item, part_no, spec, qty, unit, price, cur, mass, basis, wsource, vendor, link, note=''):
    return Part(key, group, item, part_no, spec, qty, unit, price, cur, mass, basis, wsource, vendor, link, note)


PARTS = [
    _p('rx', 'Radio', 'Transmitter and receiver', 'FS-i6X / FS-iA6B', 'FlySky FS-i6X 10ch AFHDS 2A with FS-iA6B receiver (Flysky i6X 6-Channel AFHDS 2A Air Radio System w/iA6B Receiver)', 1, 'set', 69.99, 'USD',
       D.RX['mass'], 'Published', 'Receiver 14.9 g; transmitter 392 g stays ashore (hiawathahobbies.com, flyingtech.co.uk).', 'Hiawatha Hobbies (US)',
       'https://hiawathahobbies.com/products/flysky-i6x-6-channel-afhds-2a-air-radio-system-wia6b-receiver',
       'SKU FSYI6XIA6B. Differential throttle is mixed in the transmitter. The receiver has 6 channels; the plan uses 4. Checked 2026-10-27.'),
    _p('servo_steer', 'Radio', 'Servo, nozzle steering', 'DS3225MG', 'DSSERVO DS3225 MG 25 kg waterproof digital servo, 180 deg, metal horn (one servo)', 1, 'each', 20.00, 'USD',
       D.STEER_SERVO['mass'], 'Published', '60 g each (aifitlab.com listing; DS3225 datasheet, bzbuas.com).', 'aifitlab (ships from China)',
       'https://aifitlab.com/products/dsservo-ds3225-mg-servo-motor', 'One servo drives both nozzles through a tie bar. Published spec: IP66, 25 kg-cm at 6.8 V. IP66 is not immersion rated.'),
    _p('servo_blade', 'Radio', 'Servo, daggerboard', 'DS3225MG', 'DSSERVO DS3225 MG, second servo; drives the spool and line of the reverse 25 deg blade', 1, 'each', 20.00, 'USD',
       D.STEER_SERVO['mass'], 'Published', 'Its mass is inside the 80 g blade mechanism item of the weight model, not counted twice there.', 'aifitlab (ships from China)',
       'https://aifitlab.com/products/dsservo-ds3225-mg-servo-motor', 'Bought as a second single servo (the v3 2-pack listing is not used). Sits in the bow cap, on a shelf above the stowed blade, with the spool over the line.'),
    _p('pushrod', 'Radio', 'Pushrods', 'DUB172', 'Du-Bro 2-56 x 12 in threaded rod', 2, 'each', 1.50, 'USD', None, 'Not published', '', 'Superstition Hobbies (US)',
       'https://superstitionhobbies.com/products/threaded-rods-2-56-x-12-36',
       'Nozzle linkage only; the blade servo uses a line, not a rod. Rod ends (Du-Bro 2-56 swivel ball links, 12 pack, 2135-R, $14.00) are on the order sheet. The pushrod route is not designed.'),
    _p('motor', 'Power', 'Brushless motor', 'ATO-RB-3670', 'ATO-RB-3670, 1200 kV, 36 x 70 mm, 5 mm shaft, 45 A max', 2, 'each', 142.87, 'USD',
       D.MOTOR_MASS, 'Published', '275 g each (ato.com). Cables not stated.', 'ATO', 'https://ato.com/1200kv-brushless-rc-boat-motor',
       'SKU ATO-BLDC-RB1200. Confirm kV against the 45 mm prop with a prop calculator and test runs; watch current and temperature.'),
    _p('jacket', 'Power', 'Motor water jacket', 'HRADCB36WC01 (DCB36WC01)', 'Hot Racing aluminum 36 mm water cooling jacket, 51 mm OD x 63 mm x 36 mm ID', 2 if D.JACKETS else 0, 'each', 38.88, 'USD',
       D.JACKET_MASS, 'Published', '90 g each in the model; the listing at amr-rc.com for the same SKU gives 3.2 oz (90.7 g), 51 mm OD x 63 mm long.', 'Tower Hobbies (US)',
       'https://www.towerhobbies.com/product/aluminum-36mm-water-cooling-jacket-traxxas-m41/HRADCB36WC01.html',
       'The identical part, no longer a comparable listing. Jackets are kept (JACKETS in design.py). A 51 mm OD jacket sets the minimum sponson interior width and raises the motor axis.'),
    _p('esc', 'Power', 'ESC, water cooled, reversing', 'HW30302200', 'Hobbywing SeaKing 60A V3.1, 2-3S, 6V/3A BEC', 2, 'each', 69.99, 'USD',
       D.ESC['mass'], 'Published', '93 g each, includes cooling pipe (gravesrc.com).', 'Graves RC (US)', 'https://gravesrc.com/hbw30302200-hobbywing-seaking-60a-v3-1-esc',
       'SKU HBW30302200; the page shows no stock text. Forward and reverse mode required for twin-screw steering. Disconnect the red BEC lead on one ESC.'),
    _p('battery', 'Power', 'LiPo battery', 'Ovonic 3S 5000', 'Ovonic 3S 11.1V 5000mAh 50C, XT60', 2, 'each', 36.16, 'EUR',
       D.BAT['mass'], 'Published', '343 g each (+/- 20 g); 155 x 42 x 24 mm (ampow.com).', 'ampow.com (Ovonic, ships from Germany)',
       'https://www.ampow.com/products/ovonic-11-1v-3s-5000mah-50c-lipo-battery-with-xt60-trx-plug',
       'One per sponson, one per ESC. SKU O-50C-5000-3S1P-XT60+TRX. The Ovonic US store lists the same pack at $87.99, out of stock.'),
    _p('xt60', 'Power', 'Connectors', 'XT60H', 'Amass XT60H, 5 pairs', 1, 'pack', 8.99, 'USD', 7.0, 'Published', '3.5 g per piece (getfpv.com); 2 pieces installed, one per ESC.', 'GetFPV (US)',
       'https://www.getfpv.com/amass-xt60h-power-connectors-male-female-5-sets-10-pcs.html', 'ESCs ship without connectors. SKU 11788.'),
    _p('charger', 'Power', 'Charger', 'M6AC', 'ToolkitRC M6AC 1-6S, 100W AC / 300W DC', 1, 'each', 71.99, 'USD', 0, 'Stays ashore', 'Not carried on the boat (350 g at pyrodrone.com).', 'Race Day Quads (US)',
       'https://racedayquads.com/products/toolkitrc-m6ac-300w-15a-1-6s-ac-charger-xt60', 'Skip if you already own a LiPo balance charger. Pyrodrone ($76.99) is sold out.'),
    _p('shaft', 'Drivetrain', 'Prop shaft and stern tube', 'ro1444 (Krick), 9779949', 'Romarin 4 mm shaft x 300 mm with 235 mm tube, M4 thread', 2, 'each', 11.50, 'EUR',
       shaft_mass(), 'Calculated', 'Shaft only: SHAFT_D x SHAFT_LEN of design.py in steel (STEEL_RHO). Tube wall thickness is not published, so the tube is excluded.',
       'Lindinger (Austria)',
       'https://lindinger.at/en/CARS-BOATS/ACCESSORIES/Boat-Accessories/Drive-Shafts/ROMARIN-Sterntube-235-shaft-M4x300mm/9779949',
       'Price includes Austrian VAT; US shipping is not stated on the page. The listing is a 300 mm shaft but the model shaft is SHAFT_LEN long (about 373 mm), so this part is too short as drawn.'),
    _p('ujoint', 'Drivetrain', 'Motor-to-shaft joint', 'universal joint 5 to 4 mm', 'Universal joint, 5 mm to 4 mm, 2-pack (single joint, 23 x 11 mm)', 1, 'pack', 16.94, 'USD', 22, 'Published',
       '22 g (eBay listing). The listing does not say per piece or per pair; read as the pair. Not used in the weight model, which carries the joints in an estimate item.',
       'eBay (dealbestshop)', 'https://www.ebay.de/itm/404668255092',
       'The model has a CV joint (outside diameter ASSUMED in design.py) that is not yet selected. No double joint with a 14 deg continuous rating was found; this single joint has no angle rating. Substitute on the order sheet.'),
    _p('mount', 'Drivetrain', 'Motor mount', '36 mm water-cooled bracket', '36 mm water-cooled aluminum motor mount bracket, 36 to 40 mm motors', 2, 'each', 25.72, 'USD', None, 'Not published', '',
       'eBay (immortallovesu2)', 'https://www.ebay.com/itm/152794760694',
       'Anodized aluminum; ships from China, shipping $3.89 extra. The model draws a laminated balsa mount; decide which is built, and check that a 51 mm jacket fits.'),
    _p('prop_l', 'Drivetrain', 'Kort propeller, port', 'RAB149-08', 'Raboesch 149 series, 4-blade, 45 mm, left-hand, M4', 1, 'each', 55.23, 'GBP', None, 'Not published', '',
       'Cornwall Model Boats (UK)', 'https://www.cornwallmodelboats.co.uk/acatalog/R149-M4.html', 'Left-hand turns anticlockwise viewed from astern.'),
    _p('prop_r', 'Drivetrain', 'Kort propeller, starboard', 'RAB149-07', 'Raboesch 149 series, 4-blade, 45 mm, right-hand, M4', 1, 'each', 55.24, 'GBP', None, 'Not published', '',
       'Cornwall Model Boats (UK)', 'https://www.cornwallmodelboats.co.uk/acatalog/45mm-M4-Threaded-4-Blade-R-H-Kort-Propeller-RAB149_07.html', 'Order as a matched pair with the port prop.'),
    _p('nozzle', 'Drivetrain', 'Steerable Kort nozzle', 'MBB-KNS', 'Model Boat Bits MBB-KNS, 45 mm prop size; 3D printed; 50 mm steering tube, 90 degree tiller arm', 2, 'each', 15.00, 'GBP',
       None, 'Not published', '', 'Model Boat Bits (UK)', 'https://www.modelboatbits.com/Kort-Nozzles?VariantID=37171&PPCT=1635849747',
       'The vendor publishes no nozzle length, outer diameter or weight; design.py carries NOZ_OD and NOZ_L as ASSUMED. The vendor 50 mm steering tube is too short and is not used: the post is cut from rod and tube stock (two lines below).'),
    _p('post_rod', 'Drivetrain', 'Nozzle post rod (cut stock)', 'K&S 9865', '3 mm brass rod, 300 mm, 3-piece pack, cut to the post length (check 18)', 1, 'pack', 9.99, 'USD', None, 'Not published', '',
       'K&S Precision Metals (US)', 'https://ksmetals.com/products/brrmet-3',
       'Source: ksmetals.com, in stock. One 300 mm length gives the two posts, each cut to the required length (derived, about 95 mm); the pack holds three rods.'),
    _p('post_tube', 'Drivetrain', 'Nozzle post tube (cut stock)', 'K&S 9822', '4 mm OD x 0.45 mm wall brass tube (3.1 mm bore), 300 mm, 3-piece pack, cut to the post length (check 18)', 1, 'pack', 9.99, 'USD', None,
       'Not published', '', 'K&S Precision Metals (US)', 'https://ksmetals.com/products/br45mm-4',
       'Source: ksmetals.com, in stock. One 300 mm length gives the two tubes. Bore is 0.122 in, so the 3 mm rod turns freely; check it.'),
    _p('pickup', 'Cooling', 'Cooling water pickup', 'WOB090M5', 'M5 threaded 90 degree brass water fitting, 2-pack', 1, 'pack', 6.04, 'USD', None, 'Not published', '', 'DY Motor Shop',
       'https://dymotorshop.com/index.php?main_page=index&cPath=9_23_43', 'One per sponson. Location is PENDING (COOL_PICKUP_X); the v3 prop-wash location no longer exists.'),
    _p('outlet', 'Cooling', 'Cooling water outlet', 'M6 90 deg brass fitting', 'M6 threaded 90 degree brass water fitting, 2-pack', 1, 'pack', 6.04, 'USD', None, 'Not published', '', 'DY Motor Shop',
       'https://dymotorshop.com/index.php?main_page=index&cPath=9_23_43', 'One overboard outlet per side, through the sponson side, so one pack of 2. Location is PENDING (COOL_OUTLET_X).'),
    _p('bellows', 'Sealing', 'Pushrod bellows set', 'Traxxas 5725 (was 10325)', 'Traxxas stuffing tube seal and pushrod seal set', 1, 'each', 2.99, 'USD', None, 'Not published', '', 'RC Street Shop (US)',
       'https://rcstreetshop.com/accessories/3970-seal-stuffing-tube-spartan.html',
       'Traxxas 10325 ($3.99, classicrcshop.com) is sold out, so 5725 is the substitute. No dimensions published. Size is PENDING (PUSHROD_BELLOWS_D). Only needed if the pushrod leaves the hull.'),
    _p('cord', 'Hatches', 'O-ring cord', '1.5 mm cord', 'O-ring cord, CORD_D in design.py, glued into loops', None, 'm', None, 'USD', None, 'Not published', '', 'Oringsandmore (eBay, US)',
       'https://www.ebay.com/itm/Metric-Silicone-O-ring-Cord-1-5mm-Price-for-3-ft-/163538644750',
       'Quantity is the hatch schedule total (A-503). Sold per 3 ft at $6.90; priced on the order sheet (tools/order_sheet.py). Silicone grease on the cord.'),
    _p('m3', 'Hatches', 'M3 thumb screws and M3 nuts', 'M3', 'M3 thumb screw with M3 nut, one set per latch', None, 'each', None, 'USD', None, 'Not published', '', 'Walmart (screws), eBay GM_IMPORTS (nuts)',
       'https://www.walmart.com/ip/M3-x-12mm-Knurled-Head-Thumb-Screw-Black-20pcs-for-Computer-PC-Case/194011182',
       'Quantity is the latch count of the hatch schedule (A-503). Screws $8.08 per 20, nylon insert nuts $11.50 per 100; priced on the order sheet. The nut lives in a ply pad, never threaded into balsa.'),
    _p('balsa', 'Hull', 'Balsa sheet, 1/8 in (3.175 mm)', '1/8 in sheet', 'Hull planking, frames, decks. Density is an open item (BALSA_RHO)', None, 'cm2', None, 'USD', None, 'Not published', '',
       'National Balsa (US)', 'https://www.nationalbalsa.com/products/18336',
       'Quantity is the net panel area of A-103; add cutting waste. 1/8 x 3 x 36 in sheets at $3.40; the sheet count (with frames, caps, lids and backing strips) is on the order sheet.'),
    _p('stock', 'Hull', 'Balsa square stock, 3/8 in (9.525 mm)', '3/8 in stick', 'Ripped on the diagonal for triangular blocking', None, 'm', None, 'USD', None, 'Not published', '',
       'National Balsa (US)', 'https://www.nationalbalsa.com/products/383836',
       'Quantity from the blocking table of A-501. 3/8 x 3/8 x 36 in sticks at $1.33; the stick count is on the order sheet.'),
    _p('chine', 'Hull', 'Balsa square stock, 3/4 in (19.05 mm)', '3/4 in stick', 'Chine stringers, sanded to the bilge radius', None, 'm', None, 'USD', None, 'Not published', '',
       'National Balsa (US)', 'https://www.nationalbalsa.com/collections/3-4-balsa-wood-sticks', 'Quantity from the blocking table of A-501. 3/4 x 3/4 x 36 in sticks at $4.54.'),
    _p('ply', 'Hull', 'Birch ply, 1/8 in (3.175 mm)', '1/8 in ply', 'Latch pads, servo pads, motor clamp caps, hatch rims', None, 'each', None, 'USD', None, 'Not published', '',
       'National Balsa (US)', 'https://www.nationalbalsa.com/products/181212bp', 'Counts from the hatch and support schedules (A-502, A-503). One 12 x 12 in sheet at $10.35 covers it.'),
    _p('glass', 'Hull', 'Glass cloth and epoxy', 'GLASS_OUT / GLASS_IN', 'Light cloth outside, seal coat inside; both sides of the daggerboards', None, 'm2', None, 'USD', None, 'Not published', '',
       'Fiberglass Supply (cloth), Hobby Etc (Z-Poxy)', 'https://fiberglasssupply.com/style-112-2-1-oz-x-38in-plain-weave-e-glass/',
       'Area from the weight model (A-601). Cloth: Style 112, 2.1 oz, 38 in, $7.02 per linear yard; epoxy: Z-Poxy Finishing Resin 4 oz, $14.99 (store.hobbyetc.com/parts/view/104890); both priced on the order '
       'sheet. Finish weights are ESTIMATES: weigh a test panel.'),
]

BY_KEY = {p.key: p for p in PARTS}


def get(key):
    return BY_KEY[key]


def mass(key):
    """Published (or calculated) mass of one unit, g. None when the vendor publishes none."""
    return BY_KEY[key].mass


def qty(key):
    return BY_KEY[key].qty


def total_mass(key):
    p = BY_KEY[key]
    return None if p.mass is None or p.qty is None else p.mass * p.qty
