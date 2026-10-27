# RC Recovery Barge, 32 in sailboat recovery catamaran, single-source design model

A 32 in (813 mm) tunnel catamaran that recovers RC sailboats. This repository holds one design model and everything drawn or calculated from it.

## The one-model rule

Every design decision is a named constant in `design.py`, with a one-line comment and a status tag:

- APPROVED: the owner has decided it
- PENDING: the owner has not decided it
- ASSUMED: no published source
- ESTIMATE: weight guessed

Nothing numeric appears anywhere else, except layout positions on the sheets. `model/geometry.py` and the other model files contain no literals beyond 0, 1, 2 and the unit factor 1000 (a test enforces this). To change the design, edit `design.py` and run `build.py`. When something does not fit, the checks report says so; do not change a value just to make a check pass.

Axes: X from the transom forward, Z up from the keel, Y to port from the centerline. Units are mm and g.

## Layout

| Path | What it is |
| --- | --- |
| `design.py` | The model: all design constants |
| `model/geometry.py` | Derived geometry (sponson width by station, deck height, drivetrain points, skeg, shoe, nozzle, blade outlines, hatches) |
| `model/weights.py` | Weight and balance item list (group, name, mass g, X mm), total and LCG |
| `model/hydro.py` | Hydrostatic solve: 3000 strips, stern draft and trim, skeg buoyancy fixed, deck parallel to the waterline |
| `model/checks.py` | Interference and fit checks, each returns (name, pass, message) |
| `model/study.py` | Prop and nozzle study: `alternate()` runs the whole model again with `PROP_D_ALT` and `NOZ_OD_ALT` |
| `model/variants.py` | Blade variant override: `use(key_or_dict, overrides)` context for any blade parameters, and the sweep |
| `sheets/` | SVG sheet library (`lib.py`, `tbl.py`, `render.py`) and the eleven sheets of the set `a000.py` (cover, two pages), `a101.py`, `a103.py`, `a104.py`, `a301.py`, `a401.py`, `a501.py`, `a502.py`, `a503.py`, `a601.py` (and `wtbl.py`, the schedule table helper). `a004.py` (blade sweep study) is a study sheet that is not in the set: `build.py` does not build it and A-000 does not list it; the file is kept |
| `model/parts.py`, `model/references.py`, `model/schedules.py` | Parts table (vendor data, published prices and masses), references, and the computed schedules (panels, sealing, joints, frames, hatches) |
| `tools/build_list.py` | Writes the build list workbook |
| `tools/cad.py` | CadQuery model of the boat from the one model (hull shell, deck, caps, skegs and shoes, nozzles, props, blades, electronics, water plane); exports STEP, STL, glTF and the manifest |
| `tools/viewer/index.html` | Self-contained three.js viewer for the glTF (materials by part group, blades, deck and water toggles, four view presets) |
| `tools/render_stills.py` | Playwright renders the four viewer presets to PNG |
| `build.py` | Runs everything |
| `tests/` | pytest suite |
| `out/` | Build products (git-ignored) |
| `pdf/` | Issued PDFs and the build list workbook, kept for reference (git-ignored) |
| `LICENSE` | MIT license |

## Running

Requires Python 3 with numpy, scipy, Pillow, Playwright (Chromium already installed), pytest, for the CAD step CadQuery 2.8 (`pip install cadquery`), and for the DXF files ezdxf (`pip install ezdxf`). trimesh (`pip install trimesh`) is only a fallback for converting STL to glTF if CadQuery's own glTF export is not available; the current export does not need it.

    python3 build.py      # prints the checks report, then renders the sheets
    python3 -m pytest     # model tests

`build.py` prints the checks report and continues even when checks fail. It writes to `out/`:

- `RC_Recovery_Cat_Drawings_<REV>.pdf` (REV is `design.REV`, now v9.3) and `p1.png` to `p11.png` (A-000 twice, A-101, A-103, A-104, A-301, A-401, A-501, A-502, A-503, A-601). Every sheet title block carries `design.REV`.
- `RC_Recovery_Cat_Build_List_v6.xlsx`, the build list workbook (parts with live formulas, channel plan, cooling plan, references)
- `blade_sweep.csv`, the blade variant sweep at the design battery position (475) and the first alternate (520)
- `checks.txt`, the checks report
- `weights.csv`, the weight and balance items

## Builder documents

`build.py` writes the builder documents to `out/builddocs/` after the sheets (`tools/builddocs/make.py`; alone: `python3 -m tools.builddocs.make`). Everything is stamped `design.REV` and comes from the one model: `model/partmarks.py` (the part mark scheme, also used for the CAD part names and the mark column of A-103 and A-502), `model/partshapes.py` (flat outlines) and `model/schedules.py`. The documents give marks, dimensions, angles, quantities and layouts only, no assembly instructions. DXF export needs `ezdxf` (`pip install ezdxf`); without it the DXF files are skipped with a message and the SVG files are still written.

| File | Content |
|---|---|
| `Cut_List_<REV>.pdf`, `cut_list.csv` | Stock cut list, one table per stock item: mark, qty, length, width or height, thickness, both end angles (90 where square), grain, stock piece number, note. Totals with 10 percent waste are checked against `order_parts` by a test |
| `Nesting_Layouts_<REV>.pdf` | 11 x 17 in landscape, one page per stock sheet, to scale, marks, grain arrows, 1 mm kerf; summary page with the sheet count against the order. A part longer than its stock raises an error |
| `Templates_Full_Size_<REV>.pdf` | Letter portrait at 1:1 for every flat part. Parts larger than a page are tiled with registration crosses and 10 mm overlap, labeled like `SK-P1 sheet 2 of 3 (row 1, col 2)`. Every page has a 100 mm scale bar, a 50 mm check box and a header with project, REV, part mark and page n of m |
| `Planking_Guide_<REV>.pdf` | Sections at every frame station at 1:2, plank width table per station, plank length and stock sheet. Grain along the hull |
| `Building_Board_1to2_<REV>.pdf`, `Building_Board_Full_Size_<REV>.pdf` | Board layout (keel datum, frame stations, deck slope, hinge, post centers, CV joint and motor axis, skegs, waterline at the design battery position, datum marks at X 0 and X 813): two 11 x 17 in sheets at 1:2 (the board is longer than one sheet at that scale), and a 1:1 tiled letter version |
| `dxf/<mark>.dxf`, `svg/<mark>.svg` | Every template outline, 1:1 mm |
| `part_marks.csv` | Every mark with kind, quantity, stock and template pages |

The nesting reports the balsa sheet count against the order in `order_parts` (the order is 23 sheets). The nesting needs more sheets than the order because the planks are split into equal widths that cannot share a sheet width, and part rectangles are not area-perfect; this is reported, not hidden.

## CAD model, STEP, glTF and viewer

`build.py` ends with an optional CAD step (skipped with a message if CadQuery is missing); it can also be run alone:

    python3 -m tools.cad              # out/cad/ model files
    python3 -m tools.render_stills    # out/cad/still_<preset>_<REV>.png at 1600 x 1000

`tools/cad.py` builds the boat from `design.py` and `model/geometry.py` at the design battery position (475) and the hydrostatic waterline, and writes to `out/cad/` (git-ignored):

- `RC_Recovery_Barge_<REV>.step`: the whole assembly with named, colored parts (`<group>__<part>`)
- `RC_Recovery_Barge_<REV>.glb`: the same assembly as glTF binary, per-part names kept
- `<group>_<REV>.stl`: one STL per group: hull, deck, caps, skegs_shoes, nozzles_props, blades, blades_stowed, bumper, electronics, water
- `manifest.json`: each group with its parts, volume (cm3), bounding box (mm) and material tag
- `render_info.json`: REV, weight, stern and bow draft, water over the nozzle top and the margin after the trough (read by the viewer)
- `still_bow|stern|profile|under_<REV>.png`: the four viewer presets, blades down, water on

The hull is a shell (outer skin lofted through sections with the bilge rounds, minus the inside offset by `SKIN_T`) with the deck skin as a separate part, so the deck can be removed to show the electronics; the solid sponson used for the volume test is `tools.cad.hull_solid`. Render-only values (nozzle bore, propeller blade drawing, cap and tip fillets) are in the CAD block at the end of `design.py`. Not modeled: frames, hatches, trunk walls (only a slot in the floor), pushrod and tie bar.

To open the viewer, serve the repository root and open the page (it loads `../../out/cad/RC_Recovery_Barge_<REV>.glb`; `?model=` takes another path, `?preset=bow|stern|profile|under`, `?blades=up`, `?deck=0` and `?water=0` set the start state):

    python3 -m http.server 8000
    # then open http://localhost:8000/tools/viewer/index.html

cdnjs hosts only the core three.js build (0.160.0), not GLTFLoader or OrbitControls, so the page includes a small glTF reader and orbit controls of its own and loads nothing else from the network.

The combined PDF keeps the name `RC_Recovery_Cat_Drawings_<REV>.pdf`. Issued PDFs are kept in `pdf/`, which git ignores.

The battery design position is 475 (APPROVED); the deck is built parallel to the waterline there. 520 and 590 stay in the trim table as alternate positions on that deck. A-601 also shows a balsa density sensitivity (`BALSA_RHO` and `BALSA_RHO_HI`, 10 lb/ft3): total weight and water over the nozzle top at both.

Checks 15 to 18 (v9.1): 15 hatch flanges against the part of the blade trunk that is open through the deck; 16 every item lifts out through its hatch (plan footprint inside the opening; the battery is tested at its service position `BAT_SERVICE_X`, 505, where it is slid before lift-out, and the report gives the slide range it must be moved from); 17 a nozzle turned about its post, swept 0 to 90 deg, stays inside the aft deck outline by at least 5 mm; 18 the nozzle post length required (about 95 mm), cut from 3 mm rod and 3 mm bore tube stock (300 mm). A failing check is reported, never tuned away.

Checks 22 and 23 (v9.3): 22 aft deck cantilever (1000 g at the aft edge on two 19.05 x 6.35 balsa beams, margin and deflection reported, fails under margin 2); 23 the raised push bar (BUMPER_*, bottom `BUMPER_WL_CLR` above the waterline, deck level at the top) is out of the water at every battery position and ahead of everything submerged. `DECK_PLAN` in `design.py` selects `rect` (default, PENDING) or `taper`; build.py prints both plans and A-601 tabulates them.

Checks 19 to 21 (v9.2): 19 the blade tip, extended or stowed, stays `TRUNK_TIP_CLR` (5) short of the trunk end; 20 the blade servo (DS3225 on its side, 40 x 20 x 40.5) fits in the bow cap and the servo bay X 600 to 650, outboard of the blade plane, with the lift line (`LINE_R` 200 from the hinge) straight up the open trunk to the spool; 21 the solid frames and the cap ribs clear the equipment. Check 21 currently fails and is reported (the F5 tunnel piece against the receiver and hatch HC, the F7 cap rib against the servo and the line).

Rounded underwater edges (v9.2): `BILGE_R` 15 (PENDING) on both bottom corners of each sponson, `SKEG_ROOT_R` 8 and `SKEG_EDGE_R` 6 (ASSUMED). The hydrostatics subtract the four corner rounds from the waterplane strip and add the root fillet volume to the skeg buoyancy; the edge rounds are drawn and their volume is reported, not subtracted. A-601 shows the draft change. Frames are solid at F1, F2, F3 (shaft hole), F9 (trunk notch) and the F5 tunnel piece (grommet hole); F4, F6 and F7 keep their openings (`FRAME_KIND`, `TUNNEL_KIND`). The slow-speed study on A-401 is text only and computed from `MOTOR_KV`, `PACK_V` and `FLOOR_FRACTION`.

The steering linkage (pushrod at Z = ZR, tie bar between the posts, nozzle horns, transom hole and bellows, bottom pintle and bushing) is modeled from the ASSUMED constants in `design.py`; the drive shaft length is derived in `model/geometry.py` from the joint, the prop, the motor face, a stub and a margin.

Items with no published weight (nozzles, props, bought motor mounts, water fittings, ball links, bellows) are listed under the total and are not in it, so the total is a floor.

## Blade variants

`design.BLADE_VARIANTS` is a dict of parameter dicts and `design.BLADE_VARIANT` selects the key (`reverse25` by default, APPROVED by the owner on 2026-10-26). A blade is a function of hinge X, hinge Z, radius, sector angle, direction (`aft` or `fwd`) and swing (`up`). The variants are:

- `trail`: R400, 15 deg, hinge X 785, points aft
- `hang`: R120, 90 deg, hinge X 800, points aft
- `reverse`: R380, 15 deg, hinge X 420, points forward, trunk 12 wide against the tunnel wall from the hinge to X 800, bow cap over where the stowed blade is above the deck underside, servo and spool in the bow cap with the line lifting the blade to stow; gravity deploys it.
- `reverse25`: R375 with a 25 deg sector (the design default; the tip stops 5 mm short of the trunk end). The blade plane is on the tunnel side of each sponson, so the batteries sit `BAT_Y_OFFSET` (5 mm, PENDING) outboard of the sponson centerline to clear the trunk.

To run any other blade without editing a file:

    from model import variants, hydro, checks
    with variants.use('reverse', dict(sector_deg=20.0), name='reverse 20 deg'):
        r = hydro.design()
        print(checks.report(checks.run_all(r)))

`design.BLADE_SWEEP` lists the sweep rows; `build.py` runs them and writes `out/blade_sweep.csv`.

## License

MIT for everything in the repository (see `LICENSE`). Vendor data, prices and forum references are cited, not licensed. No trademarks are included.
