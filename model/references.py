"""References as data: (key, source, what it supports, url, note). URLs are as they appeared in the earlier sheets and workbooks.

The rfcafe page appeared in the old workbooks by site name only (no URL was recorded), so its url is None.
"""
REFERENCES = [
    ('MBM-12941', 'Model Boat Mayhem, thread 12941', 'Hatch gaskets and fasteners',
     'https://www.modelboatmayhem.co.uk/forum/index.php/topic,12941.0.html',
     'EPDM gasket; silicone tubing in a channel; magnets; bolts into captive nuts; nylon thumb turns with nuts glued under the deck.'),
    ('MBM-69271', 'Model Boat Mayhem, thread 69271', 'O-ring cord in a groove on the hatch edge',
     'https://www.modelboatmayhem.co.uk/forum/index.php/topic,69271.0.html',
     'O-ring cord in a groove on the hatch edge; silicone foam or neoprene tape; Vaseline on the lip; machine screws in blind holes.'),
    ('MBM-42581', 'Model Boat Mayhem, thread 42581 (tug motors)', 'Slow-speed running of sensorless motors, big props',
     'https://www.modelboatmayhem.co.uk/forum/index.php/topic,42581.0.html',
     'Low kV multirotor outrunners suggested for big props; sensorless motors run roughly at very low rpm; belt reduction as an option.'),
    ('MBM-49746', 'Model Boat Mayhem, thread 49746 (submarine servos)', 'Waterproof linkage, servos kept dry',
     'https://www.modelboatmayhem.co.uk/forum/index.php/topic,49746.0.html',
     'Keep servos inside the dry hull and use waterproof linkages; an O-ring is one way to seal a pushrod.'),
    ('KALOPA-H002', 'Kalopa, Hull 002', 'Balsa hull practice: seams, backing pieces, stations',
     'https://kalopa.com/blog/2016-09-24-hull-002',
     'Backing piece behind butt joints; staggered seams; fibreglass inside and out; stations as bulkheads.'),
    ('BDN-228144', 'boatdesign.net, Bulkhead Connection thread', 'Bulkhead to hull joints, fillets, transitions',
     'https://www.boatdesign.net/posts/228144',
     'Small bulkhead gaps for easier fillets; about 45 deg transitions ease layup.'),
    ('OVERLANDER-4250', 'Overlander 4250/06 800KV Tornado Thumper V3 page', 'Motor size comparison (motor now ATO 3670)',
     'https://overlander.co.uk/4250-06-800kv-tornado-thumper-v3-brushless-outrunner-rc-motor.html',
     '42.6 x 50 mm, 5 mm shaft, 210 g, 62 A max, 3 to 7S, GBP 47.99 when checked.'),
    ('MBB-KORT', 'Model Boat Bits, Kort nozzle page (MBB-KNS)', 'Steerable Kort nozzle, published sizes',
     'https://www.modelboatbits.com/Kort-Nozzles',
     'Five sizes (40 to 60 mm prop size) at one price; the vendor publishes no nozzle length, outside diameter or weight.'),
    ('TRAXXAS-10325', 'Traxxas 10325 stuffing tube seal and pushrod bellows set (classicrcshop.com)', 'Rubber bellows on the steering pushrod exit',
     'https://classicrcshop.com/products/traxxas-stuffing-tube-seal-and-pushrod-set-10325',
     'USD 3.99, sold out when checked, no dimensions published.'),
    ('RFCAFE-BALSA', 'rfcafe.com, balsa weight sheet', 'Balsa density (8 to 10 lb/ft3 for hobby-shop stock)',
     None,
     'Cited by site name in the v3 to v5 workbooks; no URL was recorded. Weigh the actual sheets.'),
]

LIMITS = ('No published standard gives corner blocking size, bulkhead spacing, pushrod seal size, skeg proportions, hatch rim size or clamp pitch '
          'for a 32 in balsa catamaran. The values marked ASSUMED in design.py are this design\'s proposals and need a build test.')

KEYS = [r[0] for r in REFERENCES]


def get(key):
    return next(r for r in REFERENCES if r[0] == key)
