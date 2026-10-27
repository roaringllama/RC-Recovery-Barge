# Changelog

## 2026-10-27, v9.2: owner review

All design changes below are tagged in `design.py` (APPROVED, owner 2026-10-27 unless noted). `REV` is v9.2.

- Blade R375 for `reverse25` (was 380): the tip stops `TRUNK_TIP_CLR` (5) short of the trunk end (new check 19, passes at 5.0). The other variants keep R380 and fail check 19 in the sweep.
- Blade servo and spool moved into the bow cap. `BLADE_BOX` is removed. `LINE_R` 200 from the hinge puts the line at X 620, straight up the open trunk to a spool on the servo (`BLADE_SERVO` DS3225, 40 x 20 x 40.5 on its side, 20 high, bay X 600 to 650, outboard of the blade plane, on a shelf above the stowed blade). Cap top = max(stowed blade top, servo top) + `CAP_CLR`: Z 169.5, 79.6 above the deck at the aft end and 79.1 at the bow end; the stowed blade governs (stowed top 164.5, servo top 133.3). New check 20 (servo fits the cap and the bay, clear of the blade plane) passes. The line only lifts: the blade deploys by gravity.
- Rounded underwater edges. `BILGE_R` 15 (still PENDING) on both bottom corners of each sponson; `SKEG_ROOT_R` 8 (ASSUMED) fillets where the skeg meets the hull bottom; `SKEG_EDGE_R` 6 (ASSUMED) on the skeg bottom edge and the shoe outer edges. A-104 sections show the rounds; the stern view shows the skeg blended in. Hydrostatics subtract the four corner rounds (R^2 (1 - pi/4) each when under water) from the waterplane strip (154.9 cm3 at the waterline) and add the fillet volume (2.5 cm3) to the skeg buoyancy; the edge rounds (9.7 cm3) are reported, not subtracted. Draft change from the rounds: stern +1.97 (26.60 to 28.57), bow +1.41 (28.99 to 30.40). No item weight changed; the total differs by about 6 g from the square-section solve because the deck skin follows the deeper draft.
- Frames: F1 and F2 solid; F3 solid with a shaft hole (tube OD + 2 at shaft height and sponson centerline Y); F9 solid with a trunk notch; the F5 tunnel piece solid with one `WIRE_HOLE_D` 10 grommet hole (ASSUMED) at the roof plate level; F4, F6 and F7 keep their openings. A-502 rings and schedule, A-103 stations and A-401's compartment list updated (stern X 0 to 150 and bow X 760 to 813 sealed by F2 and F9).
- A-004 removed from `build.py` and the A-000 index. `sheets/a004.py` is kept (patched to the servo box) as a study sheet that is not in the set. The set is now 11 sheets (`p1.png` to `p11.png`).
- `PROP_D` 45 (APPROVED). `NOZ_OD` and `NOZ_L` stay 60 (ASSUMED). New `PROP_D_ALT` 50 and `NOZ_OD_ALT` 65 (ASSUMED) and `model/study.py`. A-601 trim table has one extra row, 475 with the 50 mm prop and 65 mm nozzle at the same axis height: nozzle top Z -7.5, stern draft 28.0, water over the nozzle top 35.5, margin 10.5 after the 25 trough (design: 38.6 and 13.6).
- Slow-speed study block on A-401 (text only): `MOTOR_KV` 1200 (published), `PACK_V` 3S 11.1 V and 2S 7.4 V, no-load 13,320 and 8,880 rpm, `FLOOR_FRACTION` 0.08 (ASSUMED) gives floor rpm 1,066 and 710. Prop pitch is not published, so speed at the floor cannot be computed and a bench test is required; dual rate and expo on the FS-i6X throttle channels.

Results at 475: 3047.7 g, LCG 384.7, stern draft 28.6, bow draft 30.4 (0.13 deg bow down), water over the nozzle top 38.6, 13.6 after the 25 trough. At 520: 25.4 and 33.3, margin 10.4; at 590: 20.4 and 37.7, margin 5.4 (warning).

Check 21 (new) FAILS and is reported, not tuned: the F5 tunnel piece (solid, X 388.4 to 391.6) crosses the receiver (X 345 to 392) by 3.2 in X and hatch HC lies over its grommet hole; the F7 cap rib at X 620 crosses the blade servo (X 610 to 650) and the lift line. Also noted: the F3 shaft hole center is only 0.46 above the frame bottom edge so it opens as a notch; the 8 mm root fillet barely fits on the curved bottom beside the 22 mm skeg; one blade servo (qty 1, 80 g) drives one blade, so the starboard blade drive is unresolved.

Other changes: `model/geometry.py` (`bilge_r`, `round_area`, skeg fillet, `sponson_section`, `hull_section`, servo box, line and spool, tip clearance), `model/hydro.py` (`rounds`, `round_effect`), `model/schedules.py` (frame kinds, compartments, slow-speed), A-101, A-103, A-104, A-301, A-401, A-501, A-502 and A-601 redrawn for the above. Tests: 51.

## 2026-10-27, schedules merged; hatch, receiver, post and aft deck decisions; logo removed; MIT license

Merge of the `schedules` branch into master. Conflicts in `design.py` (master block kept, schedules block appended), `model/weights.py` (published masses from `model/parts.py` and the derived `G.SHAFT_LEN` and `G.SHAFT_CG_X`), `build.py`, `CHANGELOG.md` and `tests/test_model.py` resolved. `parts.shaft_length()` returns `G.SHAFT_LEN`. The schedule sheets read `ALT_BAT_X` directly (A-401 takes the same `alts` list as A-101, A-301 and A-601, and labels 475 design, 520 and 590 alternate). `REV` stays v9.1.

Owner decisions applied in `design.py` (all APPROVED, owner, 2026-10-27):

- `BAT_SERVICE_X` 505 (new): the battery lift-out service position. Check 16 tests the battery through HB at 505 only, not at every slide position, and reports the slide range it must be moved from (30 forward from 475, 85 aft from 590). HB is now X 425 to 582 (was 585), 48 wide, so the 6 mm flange (to X 588) clears the open part of the trunk (starts at 588.5) by 0.5 mm; check 15 passes.
- HC is X 265 to 400 (was 345). The receiver is X 345 to 392 on the roof, forward of the ESCs (X 270 to 330.5) and inside HC with 8.0 spare in X; check 16 passes for the receiver.
- `NOZ_POST_TUBE_L` (vendor 50 mm tube) is gone. `NOZ_POST_STOCK_L` 300: the post is 3 mm rod in 3 mm bore tube, both cut to the required length (derived, 95.1) from 300 mm stock. Check 18 compares the required length to the stock and passes (204.9 spare, three posts per stock length). `model/parts.py` gets two lines (3 mm brass or stainless rod, 300 mm; 3 mm bore tube, 300 mm), price and mass None, to be sourced.
- `AFT_DECK_W` 285 (was 270). Check 17 (nozzle swept 0 to 90 deg) passes: outboard margin 8.0 at 45 deg, aft margin 19.2 at 45 deg (need 5).

Check 16 still fails by 0.5 mm: the 155 mm battery at the service position 505 spans X 427.5 to 582.5 and the HB opening is X 425 to 582 (157 long). The battery fits only with its center at X 502.5 to 504.5. Reported, not tuned.

Results at 475: 3043.1 g, LCG 379.6, stern draft 28.2, bow draft 27.6, 38.2 over the nozzle top (13.2 after the trough). Before these decisions: 3041.7 g, LCG 379.8 (the aft deck is wider and the post is cut stock, so the total and the LCG move slightly).

Other changes:

- The Cdaeris logo is removed everywhere: `assets/logo.png` deleted, the sheet frame header left side now reads `RC Recovery Barge` (th class), and the build list workbook has its title in A1 with no image.
- Project name is now `RC Recovery Barge, 32 in sailboat recovery catamaran` (README, `design.PROJECT`, sheet title blocks, the cover, the workbook title). The combined PDF keeps the name `RC_Recovery_Cat_Drawings_<REV>.pdf`. README notes that PDFs are in `pdf/`, ignored by git (`.gitignore` now ignores everything in `pdf/`).
- MIT license: `LICENSE` (copyright roaringllama) in the repo root, a License section in `README.md`, a one-line license comment at the top of `design.py`.
- Tests: 44 (known check state is now only check 16; new tests for the service position, receiver in HC, post stock, parts lines, HB flange clearance, bumper margins).

## 2026-10-27, schedules restored as model sheets; parts table; build list v6

- New sheets, all computed from design.py: A-000 (cover, index, design basis, references, open items parsed from the PENDING, ASSUMED and ESTIMATE tags), A-103 (panel and planking schedule), A-401 (sealing and penetration schedule, RC channel plan, trim at the design and alternate battery positions), A-501 (joints J1 to J7 at 2:1 and blocking lengths), A-502 (frames, bulkheads, deck beams, rails, motor mount, servo pad, bow cap framing), A-503 (hatch plan, plug lid section, latch detail, hatch schedule with cord lengths, daily use).
- New model files: `model/schedules.py` (literal-free), `model/parts.py` (parts table: vendor, part number, published price and currency, published mass, link), `model/references.py` (references as data). `weights.py` takes published masses from the parts table; the weight total is unchanged (3045.5 g, LCG 391.2).
- `tools/build_list.py` writes `out/RC_Recovery_Cat_Build_List_v6.xlsx` (build list with live formulas and FX inputs, channel plan, cooling plan, references). `build.py` calls it.
- design.py: new ASSUMED values for frames, blocking, hatches and latches (FRAME_X, FRAME_T, FRAME_RIB, STOCK_W, BLOCK_LEG, CHINE_LEG, BACK_W, STICK_L, WASTE, DECK_BEAM_W, DECK_BEAM_T, RAIL_W, MOUNT_W, PAD_MARGIN, PLUG_LAYERS, PLUG_CLR, CORD_D, GROOVE_D, GROOVE_W, HATCH_CORNER_R, CORD_LAP, RIM_W, RIM_T, LATCH_PER_LID, LATCH_SCREW_D, LATCH_PAD, LATCH_NUT_T, LANYARD_D, HATCH_TEST_DEPTH, HATCH_TEST_MIN, STEER_TRAVEL_DEG) and PENDING None values (PUSHROD_BELLOWS_D, COOL_PICKUP_X, COOL_OUTLET_X). No existing value changed.
- Tests: every sheet builds, the open-items parser finds all three tags, parts masses match design.py, the workbook writes without dashes, and `schedules.py` joins the no-literals test.

## 2026-10-27, v9.1: battery position 475, hatches HB and HC, steering linkage, bumper, lift-out and post checks

Design values changed (owner items 1 to 3 only; everything else is new modeling or new checks, no value was changed to pass a check):

- `DESIGN_BAT_X` 475, APPROVED (owner, 2026-10-26). The deck is now built parallel to the waterline at 475. New `ALT_BAT_X` (520, 590) keeps 520 and 590 as alternate positions on that deck (trim tables, sweep; `SWEEP_BAT_X` is now 475 and 520). The slide is still 475 to 590.
- Hatch HB: X 425 to 585 (was 430 to 630), opening 48 wide (was 44.4), centered on the shifted battery Y (new hatch key `yoff`, set to `BAT_Y_OFFSET`). PENDING.
- Hatch HC: X 265 to 345 (was 315 to 395), same width 94, over the ESCs (X 270 to 330.5). PENDING.
- Receiver stays at X 335 to 382. It is mostly outside HC. The move to X 300 to 347 between the ESCs does not fit: the ESCs leave a 3.1 mm gap and the receiver would overlap each by 30.5 in X and 11.4 in Y (check 11). Reported by check 16; PENDING.
- `REV` is now `v9.1`; it is on every sheet and in the PDF file name.

New in the model:

- Steering linkage constants (all ASSUMED): 2-56 pushrod, 4 x 4 brass tie bar, 20 mm nozzle horns, servo output offset and pushrod standoff, transom hole 8 with a 12 x 20 bellows, bottom pintle 3 mm pin 5 mm into a 5 OD brass bushing in the shoe. `geometry.ZR` (servo output height, roof top + 10) places the pushrod, tie bar and horns; tie bar X is `POSTX`; the pushrod runs from the servo horn (X 30) to the tie bar (70 between link centers) through the center transom at Y 25.25.
- `NOZ_POST_TUBE_L` 50 (published vendor tube) replaces `NOZ_POST_L` None. The length required is derived: aft deck underside minus nozzle top (95.0).
- `SHAFT_LEN` is no longer typed. It is derived in geometry: joint to prop plane (65) + margin, plus joint to motor aft face along the 14 deg axis (293.3) + stub: 373.3 (was 390). design.py keeps only `SHAFT_STUB` 10 and `SHAFT_MARGIN` 5 (ASSUMED). The shaft mass center now uses both segments (was the midpoint of the motor segment only).
- Density sensitivity: `BALSA_RHO_HI` 0.160 g/cm3 (10 lb/ft3), ASSUMED. `weights` and `hydro` take a density; `hydro.at_density` and `hydro.density_cases` solve it on the deck built for 0.144. Total 3041.7 g to 3085.4 g, water over the nozzle top 38.1 to 38.6.
- Thresholds `BUMPER_MARGIN_MIN` 5 and `BUMPER_TURN_DEG` 90.

Checks (no threshold weakened):

- 15: the hatch flange is tested only against the part of the trunk that is open through the deck (where the stowed blade is above the deck underside); the closed part may lie under a hatch. Result: still FAIL, the HB flange (to X 591) reaches 2.5 mm into the open part (X 588.5 to 791.8) and 8.4 in Y.
- 16 (new): every item lifts out through its hatch (motor and jacket through HM, battery through HB at every slide position, ESCs and receiver through HC, steering servo through HS). FAIL: the battery (155 long) is longer than HB allows except with its center at X 502.5 to 507.5 (it sticks out 27.5 at 475, 12.5 at 520, 82.5 at 590); the receiver overlaps HC by 10.0 of 47.0 in X (37.0 outside).
- 17 (new): bumper. A nozzle turned 90 deg is 31.6 inside the aft edge and 12.9 inside the side edge, but swept from 0 to 90 deg the outboard corner at 45 deg is 0.5 from the deck side edge (need 5). FAIL. The forward corner also reaches X +2.4 at 45 deg (into the transom plane); reported, not part of the check.
- 18 (new): post length required 95.0 against the 50 mm vendor tube. FAIL (45.0 short).
- 6 stays a warning and now evaluates at the design position 475: 38.1 over the nozzle top, 13.1 after the 25 mm trough (PASS); at 520 it is 9.9 (WARN). Its message also gives the 10 lb/ft3 case.
- Checks 3, 4 and 13 test each battery position once.

Sheets: A-101 draws the pushrod, tie bar, horns, bellows and transom hole in profile and plan (keys 17 and 18); A-301 shows the pintle, bushing, tie bar section, vendor tube end and required post length; A-601 shows the density sensitivity table, the three trim rows (475, 520, 590) and checks 15 to 18. Notes moved on A-101 to keep the title block clear. The sheets take the alternate positions as a list (`build(r, alts)`).

Results at 475: 3041.7 g, LCG 379.8, stern draft 28.1, bow draft 27.6, 38.1 over the nozzle top (13.1 after the trough). At 520 on the same deck: LCG 389.9, stern draft 24.9, bow draft 30.5, 34.9 over (9.9 after the trough).

Tests extended (38): v9.1 constants, hatches, linkage geometry, post, shaft, density, checks 6 and 15 to 18, REV on every sheet.

## 2026-10-27, reverse 25 deg daggerboard adopted; servo on its side; receiver and battery offsets

- `reverse25` blade variant added and made the default (`BLADE_VARIANT`), APPROVED (owner chose it on 2026-10-26): hinge X 420, Z 6, R380, 25 deg sector, points forward; trunk 12 wide on the tunnel side from the hinge to X 800; bow cap over the stowed tip with `CAP_CLR` 5. The cap is X 592 to 791 and 82 mm above the deck at its aft end (81 at the bow end); the blade hangs 154.6 below the keel. The sweep row `reverse 25 deg R380` now uses it.
- Steering servo DS3225 lies on its side on the tunnel roof, X 20 to 60, centered: height 20, footprint 40 x 40.5 (was standing, 40 x 20 x 40.5). APPROVED.
- Receiver moved 5 mm forward, X 335 to 382 (was 330), so it clears the ESCs (it overlapped them by 0.5 in X). APPROVED (trivial fix).
- Batteries (and rails) shifted 5 mm outboard: new constant `BAT_Y_OFFSET`, battery center Y 97.075 (was 92.075), so the 12 mm tunnel-side trunk (Y 60.3 to 75.5) clears the battery (Y 76.1 to 118.1, 0.58 clear). PENDING: the owner may prefer the trunk on the outboard wall instead.
- Checks: 13 now also requires the offset battery to stay inside the sponson interior and reports the Y gap to the trunk; new check 15 (hatches with flange clear the blade trunk in plan). Check 15 FAILS for the tunnel-side trunk: hatch HB (Y 69.9 to 114.3, X 430 to 630, with flange 63.9 to 120.3 and X 424 to 636) overlaps the trunk (Y 60.3 to 75.5) by 11.6 in Y. Not fixed; no value was changed. Checks 3, 9 and 9b needed no change (the servo box, cap and thresholds are as before). Check 3 now passes with the servo on its side (servo clearance 12.7 under the deck).
- Results at the design battery position (520): weight 3045.5 g, LCG 391.2, stern draft 24.6, bow draft 30.9, water over the nozzle top 34.6 (9.6 after the 25 mm trough, check 6 warning). At 475 on the same deck: 37.8 over the nozzle top.
- Sheets: A-101 draws the bow cap and the blade servo box (profile and plan) and the batteries at their new Y; A-104 draws the blade plane at its actual Y on the tunnel side, the trunk, the bow cap in both views and the batteries at the new Y (dashed, hidden); A-301 inset shows the blade extended (solid) and stowed (dashed) with the cap, trunk and servo box, at a whole-number scale; A-601 lists the bow cap (not a tower) and the new pending items. A-101 profile no longer carries the 813 hull dimension (the plan carries it) because the extended blade crosses it.
- `hang` is unchanged except LCG 398.35 to 398.37 from the receiver move; its checks 9 and 9b still fail and check 3 and 11 now pass.
- Tests extended for the new constants (default variant, servo, receiver, battery offset, cap).

## 2026-10-27, reverse daggerboard variant and blade sweep

- Third blade variant `reverse` (all values PENDING): pivot midships at hinge X 420, Z 6, R380, 15 deg sector, blade points forward.
  - Extended: sector below the keel between forward along the keel and forward 15 deg down; upper edge tip at X 800, Z 6. Stowed: rotated up about the hinge by the sector angle.
  - Trunk 12 wide on the tunnel side of each sponson, X 420 to 800. Bow cap (30 g, `TOWER_MASS`) over the X range where the stowed blade is above the deck underside, full sponson width, `CAP_CLR` 5 above the stowed blade. Servo and spool (80 g, `BLADE_MECH_MASS`) in a deck box at the hinge, X 420 to 470. Servo drives the blade forward against a stop; gravity does not deploy it.
- Blade geometry is now a function of hinge X, hinge Z, radius, sector, direction and swing. `design.BLADES` is renamed `BLADE_VARIANTS` (same values for `trail` and `hang`, plus `trunk_w`, `dir`, `swing`, `side`, `housing` keys); `BLADE_VARIANT` selects the key.
- New `model/variants.py`: `use(key_or_dict, overrides)` context so weights, hydro and checks run for any blade without editing files; `sweep()` runs `design.BLADE_SWEEP`.
- Checks 13 (blade trunk clears the batteries in plan) and 14 (blade stays inside the hull length) added; checks 9 and 9b now cover a bow cap. Existing results for `hang` are unchanged.
- Blade sweep of eight variants at the design battery position (520) and at 475 on the deck built for the design position: `out/blade_sweep.csv`, also printed by `build.py`.
- New sheet A-004 Daggerboard variants (rev v9): side elevations of hang R120, reverse 15 deg and reverse 25 deg with the sweep table. Drawn at 1:6 because 1:3, 1:4 and 1:5 do not fit with the table.
- A-101 draws the trunk and cap or tower for any variant.

## 2026-10-27

- v9 model established from study sheets.
  - One model: every design decision is a named constant in `design.py`, tagged APPROVED, PENDING, ASSUMED or ESTIMATE.
  - `model/` derives geometry, weights and balance, the hydrostatic solve, and the interference and fit checks from it.
  - Four sheets (A-101, A-104, A-301, A-601) are drawn from the model by `build.py`; each shows the blade extended (solid) and retracted (dashed).
  - Changes from the v9 study scripts, all consequences of the encoded decisions:
    - Blade default is the `hang` variant (R120, 90 deg, hinge X 800) instead of the trailing R400 blade.
    - Roof plate is `SKIN_T` thick on `ROOF_Z0` 45.7 (top 48.875), not the v8 6.35 plate.
    - Bow push pad sits inside LOA (X 803 to 813) and is `BEAM` wide by deck height less 2 x 5.
    - Skeg buoyancy moment uses the true centroid of the skeg plates and the shoe.
    - Other battery positions are solved on the deck built for the design position, so the deck is slightly off level there.
    - Steering servo, ESC and receiver positions are taken from v7 as given; the checks report whether they fit.
