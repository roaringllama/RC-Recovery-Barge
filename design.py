# License: MIT (see LICENSE). Copyright (c) 2026 roaringllama.
"""THE MODEL. Every design decision lives here as a named constant.

Axes: X from the transom forward, Z up from the keel, Y to port from the centerline.
Units: mm, g, degrees unless the name says otherwise.

Status tags in the comments:
  APPROVED  the owner has decided it
  PENDING   the owner has not decided it
  ASSUMED   no published source
  ESTIMATE  weight guessed

Nothing numeric may appear in any other file except layout positions on sheets.
When something does not fit, record it in the checks report; do not alter a value to make it pass.
"""

# ---- document ----------------------------------------------------------------------------------
REV = 'v9.2'                    # sheet revision label, used on every sheet and in the output file name, APPROVED (owner review 2026-10-27: blade R375, servo in the bow cap, rounded underwater edges, solid frames, studies)
REV_DATE = '2026-10-27'         # sheet date, APPROVED
PROJECT = 'RC Recovery Barge, 32 in sailboat recovery catamaran'   # title block text, APPROVED

# ---- hull --------------------------------------------------------------------------------------
LOA = 813.0                     # overall hull length, transom to bow tip, APPROVED
BEAM = 254.0                    # overall beam, APPROVED (checked against tunnel + 2 sponsons)
TUNNEL_W = 114.3                # tunnel width between sponsons, APPROVED
SPONSON_W = 69.85               # full sponson width, APPROVED
TIP_W = 20.0                    # sponson width at the bow tip, APPROVED
BOW_TAPER_DEG = 25.0            # bow taper angle of the outer wall; start X derived from the geometry, APPROVED
AFT_W = 25.4                    # sponson width at the transom, APPROVED by the taper study
AFT_TAPER_X = 305.0             # straight taper reaches full sponson width here, symmetric about the sponson centerline, APPROVED
SKIN_T = 3.175                  # planked balsa over frames (1/8 in), APPROVED
BILGE_R = 15.0                  # bilge sanded radius on BOTH bottom corners of each sponson (outer and tunnel side); where a section is narrower than 2 R the radius is half the width; in the hydrostatics and the sections, PENDING
SKEG_ROOT_R = 8.0               # fillet radius where the skeg box meets the hull bottom, both sides; limited by the local skeg depth; its volume is added to the skeg buoyancy, ASSUMED
SKEG_EDGE_R = 6.0               # round on the skeg bottom edge and the shoe outer (bottom) edges, drawn; its volume is reported but not subtracted in the hydrostatics, ASSUMED
FREEBOARD = 60.0                # deck height above the waterline, deck parallel to the waterline, APPROVED
DESIGN_BAT_X = 475.0            # battery center X at the design position; the deck is built parallel to the waterline at this position, APPROVED (owner, 2026-10-26)
BAT_SLIDE = (475.0, 590.0)      # battery center X travel on the slide, APPROVED
BAT_SERVICE_X = 504.0           # battery center X for lift-out: slide the battery here, then lift it through hatch HB (check 16), APPROVED (owner, 2026-10-27)
ALT_BAT_X = (520.0, 590.0)      # alternate battery positions on the same deck (trim table, sweep), APPROVED (kept as alternates to the design position 475)
AFT_DECK_L = 101.6              # aft deck over the nozzles, length aft of the transom, APPROVED
AFT_DECK_W = 285.0              # aft deck width (was 270; widened so a nozzle swept 0 to 90 deg keeps the 5 mm bumper margin, check 17), APPROVED (owner, 2026-10-27)
AFT_DECK_T = 3.175              # aft deck thickness, APPROVED
PUSH_PAD_T = 10.0               # bow push pad thickness, full bow face (BEAM wide), APPROVED
PUSH_PAD_INSET = 5.0            # pad stops this far above the keel and below the deck, ASSUMED
ROOF_Z0 = 45.7                  # tunnel roof plate bottom; plate thickness = SKIN_T, APPROVED
BALSA_RHO = 0.144               # g/cm3 (9 lb/ft3), ASSUMED
BALSA_RHO_HI = 0.160            # g/cm3 (10 lb/ft3), density sensitivity case, reported next to BALSA_RHO on A-601, ASSUMED
GLASS_OUT = 250.0               # g/m2 glass and epoxy, outside, ESTIMATE
GLASS_IN = 200.0                # g/m2 glass and seal coat, inside, ESTIMATE
LB_FT3_PER_G_CM3 = 62.428     # unit factor, lb/ft3 per g/cm3 (for labels)
STEEL_RHO = 7.85                # g/cm3, shaft steel, ASSUMED (handbook value)

# ---- drivetrain --------------------------------------------------------------------------------
MOTOR_D = 36.0                  # ATO 3670 can diameter, APPROVED
MOTOR_L = 70.0                  # ATO 3670 can length, APPROVED
JACKET_D = 51.0                 # water jacket outside diameter, APPROVED
JACKET_L = 63.0                 # water jacket length, APPROVED
JACKETS = True                  # fit water jackets (owner may delete), PENDING
MOTOR_AXIS_DEG = 14.0           # motor axis rises going forward; shaft runs this far down going aft, APPROVED
MOTOR_FLOOR_CLR = 1.5           # bottom line of the body, extended to the aft face axis X, sits this far above the floor skin, ASSUMED (the real aft corner is higher)
MOUNT_INSET = 3.0               # laminated motor mount stops this far in from the jacket ends, ASSUMED
CV_X = 25.0                     # CV joint X, APPROVED
PROP_Z = -40.0                  # CV joint, stern tube and prop axis height, APPROVED
NOZ_OD = 60.0                   # Kort nozzle outside diameter (vendor publishes none), ASSUMED
NOZ_L = 60.0                    # Kort nozzle length (vendor publishes none), ASSUMED
NOZ_X0 = 10.0                   # gap from the transom to the nozzle forward face, APPROVED
NOZ_POST_D = 3.0                # steering post diameter, published (Model Boat Bits MBB-KNS)
NOZ_POST_STOCK_L = 300.0        # 3 mm rod and 3 mm bore tube are bought in 300 mm lengths and cut to the post length; NOZ_POST_L is not typed, it is the length required, derived in geometry (about 95, check 18), APPROVED as cut stock (owner, 2026-10-27)
SKEG_W = 22.0                   # skeg and shoe width, APPROVED
SKEG_FWD_OF_KEEL = 20.0         # skeg starts this far forward of where the shaft crosses the keel, APPROVED
SHOE_CLR = 8.0                  # shoe top below nozzle bottom, APPROVED
SHOE_T = 6.35                   # shoe thickness, APPROVED
SHOE_AFT_OVERHANG = 10.0        # shoe ends this far aft of the nozzle aft face, APPROVED
CV_OD_ASSUMED = 14.0            # CV joint outside diameter (not published), ASSUMED
SHAFT_D = 4.0                   # drive shaft diameter, steel, APPROVED
SHAFT_STUB = 10.0               # motor-side stub: the shaft reaches this far into the motor coupler beyond the motor aft face (measured along the axis), ASSUMED
SHAFT_MARGIN = 5.0              # shaft extends this far past the prop plane for the prop nut, ASSUMED
# shaft length each = joint to prop + joint to motor aft face (along the axis) + SHAFT_STUB + SHAFT_MARGIN, derived in geometry
TUBE_OD = 7.0                   # stern tube outside diameter, APPROVED
SEAL_L = 8.0                    # transom seal (stuffing tube) length, drawn only, ASSUMED
SEAL_OD = 11.0                  # transom seal outside diameter, drawn only, ASSUMED
PROP_D = 45.0                   # propeller diameter inside the nozzle, drawn only, APPROVED (owner, 2026-10-27)
PROP_D_ALT = 50.0               # study case: larger propeller, A-601 shows the water over the nozzle top with it, drawn only, APPROVED as a study case (owner, 2026-10-27)
NOZ_OD_ALT = 65.0               # study case: nozzle outside diameter that takes PROP_D_ALT, same axis height PROP_Z, ASSUMED
PROP_T = 4.0                    # propeller hub plane thickness as drawn, ASSUMED
# seal at the transom only (APPROVED); no seal inside the hull.

# ---- blades (PENDING: select with BLADE_VARIANT) -----------------------------------------------
# Every blade is a sector of radius R and angle sector_deg about a hinge (hinge_x, hinge_z), swung from the keel line.
#   dir:     'aft' or 'fwd', which way the blade points along the keel when extended
#   swing:   'up', the retracted blade is the extended one rotated up about the hinge by the sector angle
#   side:    'center' (blade and trunk on the sponson centerline) or 'tunnel' (trunk against the tunnel side wall)
#   housing: 'tower' (fixed footprint over the trunk) or 'cap' (bow cap over where the stowed blade clears the deck underside)
#   trunk_x0, trunk_x1, trunk_w: trunk X range and inside width across Y
TRUNK_W = 55.0                  # trunk inside width across Y, ESTIMATE
BLADE_VARIANTS = {
    'trail':   dict(R=400.0, sector_deg=15.0, hinge_x=785.0, hinge_z=6.0, trunk_x0=395.0, trunk_x1=617.0, trunk_w=TRUNK_W,
                    dir='aft', swing='up', side='center', housing='tower'),   # PENDING (owner calls it a design flaw)
    'hang':    dict(R=120.0, sector_deg=90.0, hinge_x=800.0, hinge_z=6.0, trunk_x0=680.0, trunk_x1=800.0, trunk_w=TRUNK_W,
                    dir='aft', swing='up', side='center', housing='tower'),   # PENDING (mechanism not approved)
    'reverse': dict(R=380.0, sector_deg=15.0, hinge_x=420.0, hinge_z=6.0, trunk_x0=420.0, trunk_x1=800.0, trunk_w=12.0,
                    dir='fwd', swing='up', side='tunnel', housing='cap'),     # PENDING (pivot midships, blade points forward; servo drives forward against a stop, gravity does not deploy it)
    'reverse25': dict(R=375.0, sector_deg=25.0, hinge_x=420.0, hinge_z=6.0, trunk_x0=420.0, trunk_x1=800.0, trunk_w=12.0,
                      dir='fwd', swing='up', side='tunnel', housing='cap'),   # APPROVED (owner chose the reverse 25 deg daggerboard on 2026-10-26; R375, was 380, APPROVED owner 2026-10-27 so the stowed tip stops TRUNK_TIP_CLR short of the trunk end): hinge X 420, Z 6, points forward, trunk 12 wide on the tunnel side from the hinge to X 800, bow cap over the stowed tip and the blade servo (CAP_CLR)
}
BLADE_VARIANT = 'reverse25'     # default selection, APPROVED (owner chose it on 2026-10-26)
BLADE_ARC_PTS = 48              # arc resolution for outlines and checks, ASSUMED (numerical setting)
CAP_CLR = 5.0                   # bow cap top clears the stowed blade by this much, PENDING
TRUNK_TIP_CLR = 5.0             # the blade tip (extended or stowed) stops at least this far short of the trunk end it points toward (check 19), APPROVED (owner, 2026-10-27)
LINE_R = 250.0                  # blade lift line attaches on the blade upper edge this far from the hinge (X 670 for reverse25, between cap ribs F7 and F8) and runs straight up through the open trunk to the spool, APPROVED (owner, 2026-10-27)
BLADE_SERVO = dict(l=40.0, w=40.5, h=20.0)   # blade servo DS3225 (40 x 20 x 40.5) on its side inside the bow cap, outboard of the blade plane: footprint l along X, w along Y, h tall; output shaft STEER_OUT_X from its aft end, at mid-height; mass is BLADE_MECH_MASS, APPROVED (owner, 2026-10-27)
BLADE_SERVO_BAY = (655.0, 705.0)  # X range in the bow cap reserved for the blade servo and spool, between cap ribs F7 (620) and F8 (706), APPROVED (owner, 2026-10-27)
# sweep: (label, base variant key, overrides). Overrides replace entries of the base dict.
BLADE_SWEEP = [
    ('trail R400 15 deg hinge 785', 'trail', {}),
    ('hang R120', 'hang', {}),
    ('hang R140', 'hang', dict(R=140.0, trunk_x0=660.0)),
    ('hang R163', 'hang', dict(R=163.0, trunk_x0=637.0)),
    ('reverse 15 deg R380', 'reverse', {}),
    ('reverse 20 deg R380', 'reverse', dict(sector_deg=20.0)),
    ('reverse 25 deg R375', 'reverse25', {}),
    ('reverse 15 deg R380 hinge 450', 'reverse', dict(hinge_x=450.0, trunk_x0=450.0)),
]
SWEEP_BAT_X = (DESIGN_BAT_X, ALT_BAT_X[0])   # battery positions swept: the design position (475) and the first alternate (520)
SHEET_ROWS = ('hang R120', 'reverse 15 deg R380', 'reverse 25 deg R375')   # A-004 rows (labels from BLADE_SWEEP); A-004 is a study sheet, not in the issued set
TOWER_L = 94.0                  # tower footprint along X, centered over the trunk, APPROVED (orientation as in v8b)
TOWER_W = 127.0                 # tower footprint across Y, centered on the centerline, APPROVED (orientation as in v8b)
TOWER_H = 44.0                  # tower height above the deck, APPROVED

# ---- electronics (positions APPROVED from v7 unless noted) -------------------------------------
STEER_SERVO = dict(l=40.0, w=40.5, h=20.0, x0=20.0, mass=60.0)         # DS3225 lying on its side on the tunnel roof, centered, X 20 to 60: height 20, footprint 40 x 40.5, APPROVED; output shaft at mid-height, pointing to port
ESC = dict(l=60.5, w=38.5, h=25.6, x0=270.0, y=20.8, mass=93.0)                 # SeaKing 60A, two, on the tunnel roof at Y +/- y
RX = dict(l=47.0, w=26.0, h=15.0, x0=338.0, mass=14.9)                          # FS-iA6B on the roof, X0 is the aft edge, centered; X 338 to 385, clear of the F5 tunnel piece at 388.4, forward of the ESCs (X 270 to 330.5) and inside hatch HC (X 265 to 400), APPROVED (owner, 2026-10-27)
BAT = dict(l=155.0, w=42.0, h=24.0, mass=343.0, rail=2.5)                       # one per sponson on 2.5 mm rails
BAT_Y_OFFSET = 5.0              # each battery (and its rails) sits this far outboard of the sponson centerline (center Y 97.075 instead of 92.075) so the 12 mm tunnel-side blade trunk clears it, PENDING (owner may prefer the trunk on the outboard wall instead)
MOTOR_MASS = 275.0              # ATO 3670 each, published
JACKET_MASS = 90.0              # each, APPROVED
# bought items with no published weight are listed in model/weights.py

# ---- structure (ESTIMATE): name, mass g, X mm --------------------------------------------------
STRUCTURE = [
    ('Structure', 'Frames (8 per sponson, 1/8 in) and tunnel frames', 70.0, 400.0),
    ('Structure', 'Chine and corner blocking, stringers', 70.0, 400.0),
    ('Structure', 'Hatch lids and plugs, latch pads', 55.0, 420.0),
    ('Structure', 'Motor mounts (2), battery rails', 30.0, 400.0),
]
OTHER_ESTIMATES = [
    ('Estimate', 'CV joints (2), stern tubes, seals', 60.0, 40.0),
    ('Estimate', 'Steering pushrod, tie bar, horns, bushings, pintles', 45.0, -30.0),
    ('Estimate', 'Wire, connectors, glue', 60.0, 350.0),
]
TRUNK_MASS = 28.0               # both trunks, ESTIMATE
TOWER_MASS = 30.0               # tower shell, ESTIMATE
BLADE_MECH_MASS = 80.0          # blade servo, spool and line, now carried in the bow cap at the servo center X, ESTIMATE
BLADE_MATERIALS = {               # daggerboard sheet options: thickness mm, density g/cm3, glass both sides (True adds GLASS_OUT per side)
    'balsa_1_8':  dict(t=3.175, rho=0.144, glass=True,  note='1/8 in balsa, glassed; floats, needs a spring or weight to stay down'),
    'g10_1_5':    dict(t=1.5,   rho=1.9,   glass=False, note='1.5 mm G10 fiberglass sheet; sinks, stiff, no glassing needed'),
    'g10_2':      dict(t=2.0,   rho=1.9,   glass=False, note='2 mm G10 fiberglass sheet; sinks, stiffer, heavier'),
    'pc_2':       dict(t=2.0,   rho=1.2,   glass=False, note='2 mm polycarbonate; barely sinks'),
    'alu_1_5':    dict(t=1.5,   rho=2.7,   glass=False, note='1.5 mm aluminum; sinks hard, heaviest'),
}                                 # densities are handbook values, ASSUMED; owner asked for a denser blade so gravity deploys and holds it (2026-10-27)
BLADE_MATERIAL = 'g10_1_5'        # PENDING: owner to choose; G10 1.5 mm proposed. The trunk width TRUNK_W stays as is.
BLADE_SERVO_QTY = 1               # one blade servo (port cap) drives both blades through a cross line between the caps behind the push pad, APPROVED (owner, 2026-10-27); cross line route PENDING

# ---- steering linkage (ASSUMED unless noted; geometry derives the points) ------------------------
# One servo on its side on the tunnel roof; its horn turns in a vertical plane, so the pushrod runs fore and aft at height ZR
# (ZR = servo output height = roof top + STEER_SERVO h / 2 = roof top + 10, derived in geometry) from the servo horn aft through the
# center transom to a tie bar at X = POSTX. The tie bar joins the tips of two nozzle horns that point to port; pushing it turns both nozzles.
ROD_D = 2.18                    # pushrod: 2-56 threaded rod, nominal thread diameter 0.086 in, ASSUMED
TIE_BAR = 4.0                   # tie bar: 4 x 4 brass square, between the two nozzle posts at X = POSTX and Z = ZR, ASSUMED
NOZ_HORN_ARM = 20.0             # nozzle horn arm, post center to tie bar center, ASSUMED
STEER_OUT_X = 10.0              # servo output shaft this far forward of the servo aft end, ASSUMED (standard servo)
STEER_ROD_OFF = 5.0             # pushrod plane this far outboard of the servo side face (horn standoff), ASSUMED
ROD_HOLE_D = 8.0                # transom hole for the pushrod bellows tube, at the center transom at Z = ZR, ASSUMED
BELLOWS_OD = 12.0               # rubber bellows boot outside diameter, ASSUMED (no dimensions published)
BELLOWS_L = 20.0                # bellows boot length, outside the transom, ASSUMED
PINTLE_D = 3.0                  # bottom pintle: 3 mm pin on the nozzle bottom, fabricated, ASSUMED
PINTLE_ENGAGE = 5.0             # pin depth inside the shoe bushing, ASSUMED
BUSHING_OD = 5.0                # brass bushing in the shoe (pintle bearing), length = SHOE_T, fabricated, ASSUMED

# ---- hatches (APPROVED layout; HB, HC reshaped 2026-10-27) --------------------------------------
# zone 'sponson': one per sponson, centered on the sponson centerline plus yoff (outboard on the port side); zone 'center': one, on the centerline.
HATCHES = {
    'HM': dict(x0=300.0, x1=380.0, w=53.0, zone='sponson'),                      # over the motor and jacket, APPROVED
    'HB': dict(x0=425.0, x1=582.0, w=48.0, zone='sponson', yoff=BAT_Y_OFFSET),   # over the battery: opening 48 wide centered on the shifted battery Y; x1 585 to 582 so the flange clears the open trunk, APPROVED (owner, 2026-10-27)
    'HC': dict(x0=265.0, x1=400.0, w=94.0, zone='center'),                       # over the ESCs and the receiver (extended from 345 to 400), APPROVED (owner, 2026-10-27)
    'HS': dict(x0=10.0, x1=70.0, w=60.0, zone='center'),                         # over the steering servo, APPROVED
}
FLANGE = 6.0                    # hatch flange width around the opening, APPROVED
BH1_X = 390.0                   # bulkhead 1 in each sponson, APPROVED (BH2 is at the bow taper start, derived)
DECK_BEAMS = (150.0, 200.0, 660.0)   # deck beams across the full deck, APPROVED

# ---- check thresholds --------------------------------------------------------------------------
DECK_CLR_MIN = 5.0              # deck underside above the top of anything below it, APPROVED
MOTOR_TRUNK_CLR_MIN = 10.0      # motor front face to blade trunk aft wall, APPROVED
TROUGH = 25.0                   # trough depth around the nozzle top, APPROVED
TROUGH_MARGIN_MIN = 10.0        # water over nozzle top minus the trough, warn if less, APPROVED
BOW_DRAFT_MIN = 20.0            # bow draft, APPROVED
BUMPER_MARGIN_MIN = 5.0         # a nozzle turned about its post stays inside the aft deck outline by at least this, APPROVED
BUMPER_TURN_DEG = 90.0          # nozzle turn about its post tested for the bumper check (swept from 0), APPROVED

# ---- slow-speed study (A-401, text only; the motor and cells are the design, the floor fraction is an assumption) -------------------
MOTOR_KV = 1200.0               # ATO 3670 kV, published
PACK_V = (('3S', 11.1), ('2S', 7.4))   # nominal pack voltage by cell count (3.7 V per cell), published nominal; 3S is the design battery, 2S is a study case
FLOOR_FRACTION = 0.08           # lowest steady rpm of a sensorless ESC as a fraction of the no-load rpm, ASSUMED (bench test required)

# ---- numerical settings (not design decisions) -------------------------------------------------
HYDRO_STRIPS = 3000             # hydrostatic strips
HULL_STRIPS = 2000              # hull skin mass strips
FILLET_STRIPS = 400             # strips along the skeg for the skeg root fillet volume
HYDRO_ITER = 20                 # most deck/weight/waterline fixed-point passes
HYDRO_TOL = 1e-9                # stop when the stern draft changes less than this (mm)
D0_GUESS = 35.0                 # first guess, stern draft
K_GUESS = 0.03                  # first guess, waterline slope


# ---- schedules: frames, planking, blocking, hatch seal, latches (added with sheets A-000, A-103, A-401 to A-503) ----------
FRAME_X = (60.0, 150.0, 200.0, 305.0, 390.0, 520.0, 620.0, 706.0, 760.0)   # frame stations X in each sponson and the tunnel (transom and tip closures are extra), ASSUMED
FRAME_T = SKIN_T                # frame thickness (1/8 in), ASSUMED
FRAME_KIND = {1: 'solid', 2: 'solid', 3: 'solid_shaft', 9: 'solid_notch'}   # sponson piece of frame n where it is not a ring (key is the frame number): solid panel; solid with the shaft hole; solid with the trunk notch. A bulkhead (BH1, BH2) is solid wherever it falls. APPROVED (owner, 2026-10-27)
TUNNEL_KIND = {5: 'solid_grommet'}   # tunnel piece of frame n where it is not a ring: solid with one wire grommet hole at the roof plate level. APPROVED (owner, 2026-10-27)
SEAL_FRAMES = (2, 9)            # solid frames that close a sealed compartment besides BH1 and BH2: F2 closes the stern compartment X 0 to 150 (F1 is a solid frame inside it), F9 closes the bow compartment X 760 to the tip, APPROVED (owner, 2026-10-27)
SHAFT_HOLE_CLR = 2.0            # clearance added to the stern tube OD for the shaft hole in the solid frame (F3), APPROVED (owner, 2026-10-27)
WIRE_HOLE_D = 10.0              # wire grommet hole in the solid tunnel piece of F5, sitting on the roof plate, ASSUMED
FRAME_RIB = 12.7                # ring member width of a frame (bottom, wall, deck members), ASSUMED
STOCK_W = 76.2                  # balsa sheet stock width (3 in), planks run along the long side of a panel, ASSUMED
BLOCK_LEG = 9.525               # triangular blocking leg (3/8 in stock ripped on the diagonal, 45 deg, bears on both faces), ASSUMED
CHINE_LEG = 19.05               # chine stringer square section (3/4 in), outer corner sanded to the bilge radius less the skin, ASSUMED
BACK_W = 19.05                  # plank seam backing strip width (thickness = SKIN_T), centered on the seam, ASSUMED
STICK_L = 914.4                 # stock stick length (36 in), ASSUMED
WASTE = 0.10                    # waste allowance on stick lengths, ASSUMED
DECK_BEAM_W = 19.05             # deck beam width along X, ASSUMED
DECK_BEAM_T = 6.35              # deck beam depth under the deck, ASSUMED
RAIL_W = 6.35                   # battery rail width (rail height is BAT['rail']), two rails under each battery, ASSUMED
MOUNT_W = 40.0                  # laminated motor mount width across Y, ASSUMED
PAD_MARGIN = 5.0                # servo pad extends this far past the servo footprint on each side, ASSUMED
PLUG_LAYERS = 2                 # hatch plug is this many laminated SKIN_T layers (plug depth = deck plus rim), ASSUMED
PLUG_CLR = 1.0                  # total radial clearance between plug and opening (half each side), ASSUMED
CORD_D = 1.5                    # O-ring cord diameter, ASSUMED
GROOVE_D = 0.8                  # cord groove depth into the plug edge, ASSUMED
GROOVE_W = 1.6                  # cord groove width along the plug thickness, ASSUMED
HATCH_CORNER_R = 5.0            # opening corner radius so the cord can follow it, ASSUMED
CORD_LAP = 10.0                 # cord overlap at the glued splice, ASSUMED
RIM_W = 9.525                   # rim ring width under the deck around each opening (trimmed to the wall where the sponson is narrower), ASSUMED
RIM_T = SKIN_T                  # rim ring thickness, ASSUMED
LATCH_PER_LID = 2               # thumb screw latches per lid, ASSUMED
LATCH_SCREW_D = 3.0             # thumb screw diameter (M3), ASSUMED
LATCH_PAD = 12.7                # square ply pad under the deck holding the M3 nut, ASSUMED
LATCH_NUT_T = 2.4               # M3 nut thickness, ASSUMED
LANYARD_D = 1.0                 # lid lanyard diameter, ASSUMED
HATCH_TEST_DEPTH = 50.0         # bench test: lid held under this much water, ASSUMED
HATCH_TEST_MIN = 10.0           # bench test duration in minutes, ASSUMED
STEER_TRAVEL_DEG = 35.0         # nozzle steering travel each side of center (forum report; v8 sheets said 45), ASSUMED
PUSHROD_BELLOWS_D = None        # pushrod bellows size is not published and the pushrod route is not designed, PENDING
COOL_PICKUP_X = None            # M5 water pickup X on the sponson bottom, not decided (v3 used the prop wash, which no longer exists), PENDING
COOL_OUTLET_X = None            # M6 water outlet X through the sponson side, not decided, PENDING
