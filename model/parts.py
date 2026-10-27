"""Parts table: one source for vendor data and published weights.

Each Part: key, group, item, part_no, spec, qty, unit, price, cur, mass (g each, or None), basis, wsource, vendor, link, note.
price is the published unit price in the currency `cur` (None when not priced). mass is None when the vendor publishes none.
basis is 'Published', 'Calculated', 'Not published' or 'Stays ashore'.
Masses of items that design.py already carries (motor, jacket, ESC, battery, receiver, servo) are read from design.py, so there is
one number; model/weights.py reads every published mass from here.
Prices and links are as found when the v3 workbook was built; check them before ordering.
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
    _p('rx', 'Radio', 'Transmitter and receiver', 'FS-i6X / FS-iA6B', 'FlySky FS-i6X 10ch AFHDS 2A with FS-iA6B receiver', 1, 'each', 53.49, 'GBP',
       D.RX['mass'], 'Published', 'Receiver 14.9 g (flyingtech.co.uk). Transmitter stays ashore.', 'eBay UK (mohaal72)',
       'https://www.ebay.de/itm/406062211243', 'Differential throttle is mixed in the transmitter. The receiver has 6 channels; the plan uses 4.'),
    _p('servo_steer', 'Radio', 'Servo, nozzle steering', 'DS3225MG', 'DS3225MG 25 kg waterproof digital servo, sold as a 2-pack (this line is the pack)', 1, 'pack', 29.95, 'USD',
       D.STEER_SERVO['mass'], 'Published', '60 g each (DS3225 datasheet, bzbuas.com).', 'eBay US (rcexpress, Frisco TX)',
       'https://www.ebay.de/itm/334698838029', 'One servo drives both nozzles through a tie bar. Published spec: IP66, 25 kg-cm at 6.8 V. IP66 is not immersion rated.'),
    _p('servo_blade', 'Radio', 'Servo, daggerboard (second servo of the pack)', 'DS3225MG', 'Second servo of the 2-pack above; drives the spool and line of the reverse 25 deg blade', 1, 'each', 0.0, 'USD',
       D.STEER_SERVO['mass'], 'Published', 'Its mass is inside the 80 g blade mechanism item of the weight model, not counted twice there.', 'eBay US (rcexpress, Frisco TX)',
       'https://www.ebay.de/itm/334698838029', 'Included in the pack price above. Sits in the deck box at the hinge, above the deck.'),
    _p('pushrod', 'Radio', 'Pushrods', 'DUB172', 'Du-Bro 2-56 x 12 in threaded rod', 2, 'each', 0.89, 'USD', None, 'Not published', '', 'Motion RC',
       'https://www.motionrc.com/collections/pushrods/products/du-bro-2-56-305mm-12-threaded-rod-dub172',
       'Nozzle linkage only; the blade servo uses a line, not a rod. Clevises not included. The pushrod route is not designed.'),
    _p('motor', 'Power', 'Brushless motor', 'ATO-RB-3670', 'ATO-RB-3670, 1200 kV, 36 x 70 mm, 5 mm shaft, 45 A max', 2, 'each', 142.87, 'USD',
       D.MOTOR_MASS, 'Published', '275 g each (ato.com). Cables not stated.', 'ATO', 'https://www.ato.com/1200kv-brushless-rc-boat-motor',
       'Confirm kV against the 45 mm prop with a prop calculator and test runs; watch current and temperature.'),
    _p('jacket', 'Power', 'Motor water jacket', 'DCB36WC01 (comparable)', 'Aluminum jacket, 36 mm motor, 51 mm OD x 63 mm', 2 if D.JACKETS else 0, 'each', 11.66, 'USD',
       D.JACKET_MASS, 'Published', '90 g each, from a comparable 36 mm jacket (vxb.com DCB36WC01: 51 mm OD x 63 mm long). Not the identical listing.', 'eBay (Joyfeel RC)',
       'https://www.ebay.de/itm/127513048479', 'Jackets are kept (JACKETS in design.py). A 51 mm OD jacket sets the minimum sponson interior width and raises the motor axis.'),
    _p('esc', 'Power', 'ESC, water cooled, reversing', 'HW30302200', 'Hobbywing SeaKing 60A V3.1, 2-3S, 6V/3A BEC', 2, 'each', 86.55, 'USD',
       D.ESC['mass'], 'Published', '93 g each, includes cooling pipe (bigboyswithcooltoys.ca).', 'eBay US (Fast Rc Parts, NH)', 'https://www.ebay.de/itm/154168050910',
       'Forward and reverse mode required for twin-screw steering. Disconnect the red BEC lead on one ESC.'),
    _p('battery', 'Power', 'LiPo battery', 'Ovonic 3S 5000', 'Ovonic 3S 11.1V 5000mAh 50C, XT60', 2, 'each', 52.90, 'USD',
       D.BAT['mass'], 'Published', '343 g each; 155 x 42 x 24 mm (rcdrone.top).', 'rcdrone.top', 'https://rcdrone.top/ar/products/ovonic-5000mah-3s-lipo-battery-2',
       'One per sponson, one per ESC.'),
    _p('xt60', 'Power', 'Connectors', 'XT60H', 'Amass XT60H, 5 pairs', 1, 'pack', 9.04, 'USD', None, 'Not published', '', 'rcdrone.top',
       'https://rcdrone.top/products/10-x-amass-xt60-xt60h-plug-connector', 'ESCs ship without connectors.'),
    _p('charger', 'Power', 'Charger', 'M6AC', 'ToolkitRC M6AC 1-6S, 100W AC / 300W DC', 1, 'each', 76.99, 'USD', 0, 'Stays ashore', 'Not carried on the boat.', 'Pyrodrone',
       'https://pyrodrone.com/collections/all/products/toolkitrc-m6ac-1-6s-ac-100w-dc-300w-15a-battery-charger-xt60', 'Skip if you already own a LiPo balance charger.'),
    _p('shaft', 'Drivetrain', 'Prop shaft and stern tube', 'ro1444 (Krick), 9779949', 'Romarin 4 mm shaft x 300 mm with 235 mm tube, M4 thread', 2, 'each', 9.50, 'EUR',
       shaft_mass(), 'Calculated', 'Shaft only: SHAFT_D x SHAFT_LEN of design.py in steel (STEEL_RHO). Tube wall thickness is not published, so the tube is excluded.',
       'Lindinger (Austria)',
       'https://lindinger.at/en/CARS-BOATS/ACCESSORIES/Boat-Accessories/Drive-Shafts/ROMARIN-Sterntube-235-shaft-M4x300mm/9779949',
       'The listing is 300 mm shaft and 235 mm tube; the model shaft is SHAFT_LEN long. Confirm the length before ordering.'),
    _p('ujoint', 'Drivetrain', 'Motor-to-shaft joint', 'universal joint 5 to 4 mm', 'Universal joint, 5 mm to 4 mm, 2-pack', 1, 'pack', 12.37, 'USD', 22, 'Published',
       '22 g (eBay listing). The listing does not say per piece or per pair; read as the pair. Not used in the weight model, which carries the joints in an estimate item.',
       'eBay (dealbestshop)', 'https://www.ebay.de/itm/404668255092',
       'The model has a CV joint (outside diameter ASSUMED in design.py) that is not yet selected; this is the v3 choice and its fit is open.'),
    _p('mount', 'Drivetrain', 'Motor mount', '36 mm water-cooled bracket', '36 mm water-cooled motor mount bracket, glass fiber', 2, 'each', 16.64, 'USD', None, 'Not published', '',
       'eBay (Joyfeel RC)', 'https://www.ebay.de/itm/123564984800',
       'Anodized aluminum clamps on fiberglass stands. The model draws a laminated balsa mount; decide which is built.'),
    _p('prop_l', 'Drivetrain', 'Kort propeller, port', 'RAB149-08', 'Raboesch 149 series, 4-blade, 45 mm, left-hand, M4', 1, 'each', 55.23, 'GBP', None, 'Not published', '',
       'Cornwall Model Boats (UK)', 'https://www.cornwallmodelboats.co.uk/acatalog/R149-M4.html', 'Left-hand turns anticlockwise viewed from astern.'),
    _p('prop_r', 'Drivetrain', 'Kort propeller, starboard', 'RAB149-07', 'Raboesch 149 series, 4-blade, 45 mm, right-hand, M4', 1, 'each', 55.23, 'GBP', None, 'Not published', '',
       'Cornwall Model Boats (UK)', 'https://www.cornwallmodelboats.co.uk/acatalog/R149-M4.html', 'Order as a matched pair with the port prop.'),
    _p('nozzle', 'Drivetrain', 'Steerable Kort nozzle', 'MBB-KNS', 'Model Boat Bits MBB-KNS, 45 mm prop size; 3D printed; 50 mm steering tube, 90 degree tiller arm', 2, 'each', 15.00, 'GBP',
       None, 'Not published', '', 'Model Boat Bits (UK)', 'https://www.modelboatbits.com/Kort-Nozzles',
       'The vendor publishes no nozzle length, outer diameter or weight; design.py carries NOZ_OD and NOZ_L as ASSUMED. The vendor 50 mm steering tube is too short and is not used: the post is cut from rod and tube stock (two lines below).'),
    _p('post_rod', 'Drivetrain', 'Nozzle post rod (cut stock)', '3 mm rod', '3 mm brass or stainless rod, 300 mm, cut to the post length (check 18)', 1, 'each', None, 'USD', None, 'Not published', '', 'to be sourced', None,
       'Source: price and weight not yet found. One 300 mm length gives the two posts, each cut to the required length (derived, about 95 mm).'),
    _p('post_tube', 'Drivetrain', 'Nozzle post tube (cut stock)', '3 mm bore tube', '3 mm bore tube, 300 mm, cut to the post length (check 18)', 1, 'each', None, 'USD', None, 'Not published', '', 'to be sourced', None,
       'Source: price and weight not yet found. One 300 mm length gives the two tubes. Check that the rod turns freely in the bore.'),
    _p('pickup', 'Cooling', 'Cooling water pickup', 'M5 nipple', 'M5 water pickup nipple, 2-pack', 1, 'pack', 6.72, 'USD', None, 'Not published', '', 'eBay (winasum)',
       'https://www.ebay.de/itm/183764614186', 'One per sponson. Location is PENDING (COOL_PICKUP_X); the v3 prop-wash location no longer exists.'),
    _p('outlet', 'Cooling', 'Cooling water outlet', 'M6 nipple', 'M6 water outlet nipple', 2, 'each', 4.38, 'USD', None, 'Not published', '', 'eBay (winasum)',
       'https://www.ebay.de/itm/172976215531', 'One overboard outlet per side, through the sponson side. Location is PENDING (COOL_OUTLET_X).'),
    _p('bellows', 'Sealing', 'Pushrod bellows set', 'Traxxas 10325', 'Traxxas 10325 stuffing tube seal and pushrod set', 1, 'each', 3.99, 'USD', None, 'Not published', '', 'classicrcshop.com',
       'https://classicrcshop.com/products/traxxas-stuffing-tube-seal-and-pushrod-set-10325',
       'Sold out when checked, no dimensions published. Size is PENDING (PUSHROD_BELLOWS_D). Only needed if the pushrod leaves the hull.'),
    _p('cord', 'Hatches', 'O-ring cord', '1.5 mm cord', 'O-ring cord, CORD_D in design.py, glued into loops', None, 'm', None, 'USD', None, 'Not published', '', 'to be sourced', None,
       'Quantity is the hatch schedule total (A-503). Silicone grease on the cord.'),
    _p('m3', 'Hatches', 'M3 thumb screws and M3 nuts', 'M3', 'M3 thumb screw with M3 nut, one set per latch', None, 'each', None, 'USD', None, 'Not published', '', 'to be sourced', None,
       'Quantity is the latch count of the hatch schedule (A-503). The nut lives in a ply pad, never threaded into balsa.'),
    _p('balsa', 'Hull', 'Balsa sheet, 1/8 in (3.175 mm)', '1/8 in sheet', 'Hull planking, frames, decks. Density is an open item (BALSA_RHO)', None, 'cm2', None, 'USD', None, 'Not published', '', 'to be sourced', None,
       'Quantity is the net panel area of A-103; add cutting waste. Confirm sheet widths with the supplier.'),
    _p('stock', 'Hull', 'Balsa square stock, 3/8 in (9.525 mm)', '3/8 in stick', 'Ripped on the diagonal for triangular blocking', None, 'm', None, 'USD', None, 'Not published', '', 'to be sourced', None,
       'Quantity from the blocking table of A-501.'),
    _p('chine', 'Hull', 'Balsa square stock, 3/4 in (19.05 mm)', '3/4 in stick', 'Chine stringers, sanded to the bilge radius', None, 'm', None, 'USD', None, 'Not published', '', 'to be sourced', None,
       'Quantity from the blocking table of A-501.'),
    _p('ply', 'Hull', 'Birch ply, 1/8 in (3.175 mm)', '1/8 in ply', 'Latch pads, servo pads, motor clamp caps, hatch rims', None, 'each', None, 'USD', None, 'Not published', '', 'to be sourced', None,
       'Counts from the hatch and support schedules (A-502, A-503).'),
    _p('glass', 'Hull', 'Glass cloth and epoxy', 'GLASS_OUT / GLASS_IN', 'Light cloth outside, seal coat inside; both sides of the daggerboards', None, 'm2', None, 'USD', None, 'Not published', '', 'to be sourced', None,
       'Area from the weight model (A-601). Finish weights are ESTIMATES: weigh a test panel.'),
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
