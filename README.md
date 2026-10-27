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
| `model/variants.py` | Blade variant override: `use(key_or_dict, overrides)` context for any blade parameters, and the sweep |
| `sheets/` | SVG sheet library (`lib.py`, `tbl.py`, `render.py`) and the twelve sheets `a000.py` (cover), `a101.py`, `a103.py`, `a104.py`, `a301.py`, `a401.py`, `a501.py`, `a502.py`, `a503.py`, `a601.py`, `a004.py` (and `wtbl.py`, the schedule table helper) |
| `model/parts.py`, `model/references.py`, `model/schedules.py` | Parts table (vendor data, published prices and masses), references, and the computed schedules (panels, sealing, joints, frames, hatches) |
| `tools/build_list.py` | Writes the build list workbook |
| `build.py` | Runs everything |
| `tests/` | pytest suite |
| `out/` | Build products (git-ignored) |
| `pdf/` | Issued PDFs and the build list workbook, kept for reference (git-ignored) |
| `LICENSE` | MIT license |

## Running

Requires Python 3 with numpy, scipy, Pillow, Playwright (Chromium already installed) and pytest.

    python3 build.py      # prints the checks report, then renders the sheets
    python3 -m pytest     # model tests

`build.py` prints the checks report and continues even when checks fail. It writes to `out/`:

- `RC_Recovery_Cat_Drawings_<REV>.pdf` (REV is `design.REV`, now v9.1) and `p1.png` to `p12.png` (A-000, A-101, A-103, A-104, A-301, A-401, A-501, A-502, A-503, A-601, A-004; the cover is two pages). Every sheet title block carries `design.REV`.
- `RC_Recovery_Cat_Build_List_v6.xlsx`, the build list workbook (parts with live formulas, channel plan, cooling plan, references)
- `blade_sweep.csv`, the blade variant sweep at the design battery position (475) and the first alternate (520)
- `checks.txt`, the checks report
- `weights.csv`, the weight and balance items

The combined PDF keeps the name `RC_Recovery_Cat_Drawings_<REV>.pdf`. Issued PDFs are kept in `pdf/`, which git ignores.

The battery design position is 475 (APPROVED); the deck is built parallel to the waterline there. 520 and 590 stay in the trim table as alternate positions on that deck. A-601 also shows a balsa density sensitivity (`BALSA_RHO` and `BALSA_RHO_HI`, 10 lb/ft3): total weight and water over the nozzle top at both.

Checks 15 to 18 (v9.1): 15 hatch flanges against the part of the blade trunk that is open through the deck; 16 every item lifts out through its hatch (plan footprint inside the opening; the battery is tested at its service position `BAT_SERVICE_X`, 505, where it is slid before lift-out, and the report gives the slide range it must be moved from); 17 a nozzle turned about its post, swept 0 to 90 deg, stays inside the aft deck outline by at least 5 mm; 18 the nozzle post length required (about 95 mm), cut from 3 mm rod and 3 mm bore tube stock (300 mm). A failing check is reported, never tuned away.

The steering linkage (pushrod at Z = ZR, tie bar between the posts, nozzle horns, transom hole and bellows, bottom pintle and bushing) is modeled from the ASSUMED constants in `design.py`; the drive shaft length is derived in `model/geometry.py` from the joint, the prop, the motor face, a stub and a margin.

Items with no published weight (nozzles, props, bought motor mounts, water fittings, ball links, bellows) are listed under the total and are not in it, so the total is a floor.

## Blade variants

`design.BLADE_VARIANTS` is a dict of parameter dicts and `design.BLADE_VARIANT` selects the key (`reverse25` by default, APPROVED by the owner on 2026-10-26). A blade is a function of hinge X, hinge Z, radius, sector angle, direction (`aft` or `fwd`) and swing (`up`). The variants are:

- `trail`: R400, 15 deg, hinge X 785, points aft
- `hang`: R120, 90 deg, hinge X 800, points aft
- `reverse`: R380, 15 deg, hinge X 420, points forward, trunk 12 wide against the tunnel wall from the hinge to X 800, bow cap over where the stowed blade is above the deck underside, servo and spool in a deck box at the hinge. The servo drives it forward against a stop; gravity does not deploy it.
- `reverse25`: the same with a 25 deg sector (the design default). The blade plane is on the tunnel side of each sponson, so the batteries sit `BAT_Y_OFFSET` (5 mm, PENDING) outboard of the sponson centerline to clear the trunk.

To run any other blade without editing a file:

    from model import variants, hydro, checks
    with variants.use('reverse', dict(sector_deg=20.0), name='reverse 20 deg'):
        r = hydro.design()
        print(checks.report(checks.run_all(r)))

`design.BLADE_SWEEP` lists the sweep rows; `build.py` runs them and writes `out/blade_sweep.csv`.

## License

MIT for everything in the repository (see `LICENSE`). Vendor data, prices and forum references are cited, not licensed. No trademarks are included.
