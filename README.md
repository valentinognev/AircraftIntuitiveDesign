# Aircraft Intuitive Design

Conceptual aircraft geometry editor and aerodynamic analysis tool. Enter a wing, tails, body, controls, and flight condition; get lift, drag, and moment coefficients from four independent solvers: USAF Digital DATCOM, Tornado (vortex lattice), AVL 3.52, and flow5 (vortex-lattice panel).

The original application is a MATLAB GUI (`AID.m`). This repository also ships a Python twin: the same aircraft data, the same DATCOM/AVL binaries, a port of Tornado’s VLM, and a PySide6 desktop GUI. MATLAB `.mat` dumps are the oracle; Python is required to match those coefficients.

GitHub: [github.com/valentinognev/AircraftIntuitiveDesign](https://github.com/valentinognev/AircraftIntuitiveDesign)

## Credits

This repository is a Linux MATLAB + Python port of the original AID application and the solvers it wraps. Credit the upstream projects:

| Project | Authors / source | Link |
|---------|------------------|------|
| **Aircraft Intuitive Design (AID)** | Zachary T. Lietzau, Embry-Riddle Aeronautical University (2017) | [MATLAB File Exchange](https://www.mathworks.com/matlabcentral/fileexchange/66770-aircraft-intuitive-design-aid) |
| **USAF Digital DATCOM** | USAF Stability and Control DATCOM (AFFDL-TR-79-3032); Fortran via Public Domain Aeronautical Software (PDAS) | [PDAS Digital Datcom](https://www.pdas.com/datcom.html) |
| **Tornado** | Tomas Melin, KTH Royal Institute of Technology (GNU GPL vortex-lattice code) | [tornado.redhammer.se](https://tornado.redhammer.se/) |
| **AVL** (Athena Vortex Lattice) 3.52 | Mark Drela and Harold Youngren, MIT | [web.mit.edu/drela/Public/web/avl](https://web.mit.edu/drela/Public/web/avl/) |
| **flow5** | André Deperrois (GNU GPL v3 vortex-lattice / panel code) | Vendored under `FLOW5/` in this repo |

AID also uses Joseph Moster’s AVL MATLAB I/O helpers (bundled under `Matlab/fsroot/code/AVL/`) and MathWorks Aerospace Toolbox `datcomimport` for MATLAB gold DATCOM dumps. flow5 has no MATLAB gold runner; coefficients come only from the native helper subprocess.

## Idea

AID is a conceptual-design workbench, not a CAD or CFD package. Geometry is stored in DATCOM-style planform fields (root/tip chord, semi-span, sweep, dihedral, NACA sections, apex position). Derived quantities — area, MAC, aspect ratio, CD0, lift-curve slope — are recomputed, not treated as independent inputs.

Analyze runs one of four methods and overlays coefficients vs angle of attack. AVL is one binary process: one unconstrained reference solve, then one OPER solution per `AERO.ALSCHD` angle. CL, CD, CY, CN, CA, and the moments on the plots are those scheduled solutions.

| Solver | Kind | How it runs |
|--------|------|-------------|
| **DATCOM** | Empirical / handbook (PDAS Digital DATCOM Fortran) | Shared Linux binary via a stdin wrapper |
| **Tornado** | Vortex-lattice method | MATLAB `.m` in `Tornado/`; rewritten in Python |
| **AVL 3.52** | Vortex-lattice (Drela/Youngren) | One binary process: unconstrained reference `x` (no `a a`), then one OPER solution per `AERO.ALSCHD` angle |
| **flow5** | Vortex-lattice panel (Deperrois GPL-3) | Vendored `FLOW5/` native helper `flow5_run` subprocess; Python writes a JSON deck only |

MATLAB remains the gold runner. Python `aid` is a headless engine. `aid_gui` (PySide6) stays installable. The CADAC workbench sibling is `api/` + `web/` (`./start-web.sh`: FastAPI :8002, Vite :5175); it wraps the same `aid` for load, Analyze, and handshake.

## Architecture

Two solver stacks, one repo, three UIs (MATLAB, PySide, web). DATCOM, AVL, and flow5 are compiled once and invoked as subprocesses from both languages (flow5 is Python-only today). Tornado is a source port, so coefficient compare uses looser tolerances than the shared Fortran parsers. flow5 is GPL-3: the PySide GUI never links `flow5-lib`; only `FLOW5/run/flow5_run` runs as a subprocess (same pattern as AVL). Web Analyze uses the same `aid` runners (no second solver).

```
Aircraft (WG/HT/VT/F/A/E/R/BD/AERO)
        │
        ├─ MATLAB AID.m  ── DATCOM_IO / Tornado_IO / AVL_IO ──► Results/matlab/
        │
        └─ Python aid    ── datcom_io / tornado_io / avl_io / flow5_io ──► Results/python/
                    │
                    ├─ aid_gui (PySide6 + pyvistaqt 3D)  +  compare.py vs MATLAB gold
                    └─ api/ aid-web FastAPI :8002 + web/ Vite React :5175
```

Vendored flow5 source lives under `FLOW5/` (`XFoil-lib/`, `flow5-lib/`, superbuild `CMakeLists.txt`). Build the helper with `cmake -S FLOW5 -B FLOW5/build` then `cmake --build FLOW5/build` (installs executable to `FLOW5/run/flow5_run`, gitignored). System packages (Ubuntu): `libocct-foundation-dev`, `libocct-modeling-algorithms-dev`, `libocct-modeling-data-dev`, `libocct-ocaf-dev`, `libocct-data-exchange-dev`, `libopenblas-dev`. `write_flow5_deck` maps AID JSONC → deck JSON (T1 VLM2, inviscid, thin surfaces, no fuselage). `run_flow5` invokes the native helper from Analyze → flow5; Cessna 172 e2e matches native within atol=1e-6 (`test_e2e_flow5_cessna.py`).

- `Matlab/fsroot/code` — AID GUI, geometry/aero/drag, Tornado VLM, AVL I/O, 23 `.mat` models, user manual PDF.
- DATCOM Fortran lives beside this repo at `../datcom/datcom.f` (namelist MAXNX=200 body stations, MAXNPTS=500 airfoil points; analysis uses the first 60 section points). AID writers clamp wing `$WGSCHR` to 60 and HT/VT/extra to 50 so Analyze cannot hang. Python `write_for005` wraps BODY arrays at 80 columns (`body_max=200`, no 18-station downsample), clamps MACH>0.6 to STMACH 0.6, omits DATCOM-illegal HT/VT (buried/negative SSPNE, SSPNE>SSPN, zero area) and inverted control spans (SPANFO<=SPANFI; no elevator namelist without HT). SPANFO past parent SSPN is still written, clamped to parent SSPN so DATCOM does not SIGSEGV (DA20 elevator). Uses a later numeric NACA when the first cell is `Data.`/a path (stored JSONC unchanged). Linux binary `DATCOM/datcom.bin` is gitignored; wrapper `DATCOM/datcom` feeds `for005.dat` on stdin and copies `datcom.out` → `for006.dat` even if the binary later SIGSEGVs (AID/`datcomimport` expect that name). AVL `run_avl_full` retries weighted-outboard / equal spanwise spacing if `geometry.st` is missing (GUI Analyze AVL with Inputs/Outputs uses the same retry, then previews the successful files).
- AVL 3.52 source: `Matlab/fsroot/code/AVL/AVL3.52rel09032025/`. Install executable to `AVL/run/avl` (gitignored).
- `FLOW5/` — vendored flow5 back-end (`XFoil-lib`, `flow5-lib`, CMake superbuild). Helper `FLOW5/run/flow5_run` (gitignored). Python `flow5_io.write_flow5_deck` + `run_flow5`; no MATLAB gold.
- `Python/` — package `aid` (engine) + `aid_gui` (PySide6). `aid.handbook_pass.apply_handbook` runs the MATLAB handbook sequence (geometry, section slopes, aero, CD0, lateral, trim, longitudinal dynamic). Models: `Python/models/*.jsonc`.
- `api/` — FastAPI `aid-web`: `GET /models`, `GET /models/{name}`, `POST /models/validate`, `POST /analyze` (`solver` `datcom`|`tornado`|`avl`|`flow5`; omitted solver is datcom). Optional `mesh` (Tornado default `("10","5")`, AVL/flow5 `("10","10")`). Analyze returns `raw` with mapper lists `{alpha, CL, CD, Cm, MACH}` plus handshake `payload` (`source: "aid"`, `solver` set, tables `cl`/`cd`/`cm`). `POST /stability` body `{aircraft}` returns `aid.stability.aircraft_stability` (CG / static margin). Engine fail (`FileNotFoundError` / `CalledProcessError` / `TimeoutExpired` / `ValueError` / `OSError` / `KeyError`) → HTTP 400 `{ok: false, error}`. Unknown solver → HTTP 400. `POST /control-derivatives` returns flap, aileron, elevator, and rudder slopes per degree from handbook, DATCOM, Tornado, AVL, and flow5.
- `web/` — Vite React 18 + Tailwind 3 (`darkMode: ["selector", ".dark"]`) + Zustand on :5175. Proxy `/models` `/analyze` `/stability` → `http://127.0.0.1:8002`. Start: New / Load examples (`GET /models`) / Open file (FileReader JSONC) / Recent (localStorage last-5 names, key `aid-recent`). Theme `aid-theme` + `html.dark`. Non-empty `?cadacSession=` on first load `openNew()` (starter GET is plan 5). Tabs Wing/HT/VT/Control/Body/Aero/Geometry/`+` from PySide `PLANFORM_RP` / Control / Body / Aero keys. Control: Flaps/Ailerons/Elevator/Rudder Inboard|Outboard grids (`F,A,E,R` `CONTROL_BLOCKS`). `+` ExtraTab adds Body 2/3 (`NB` 1×2) and Prop / Wing 2 / HT 2 / VT 2 (`NP` 1×4); Load shows those tabs when slots are filled. Number fields commit on blur (`null` if blank). Save is client download. Analyze header (`DATCOM`/`Tornado`/`AVL`/`flow5`) `POST /analyze`; stores `lastPayload`. If `?cadacSession=` is set, after success `fetch` POSTs the handshake `payload` (`source: "aid"`) to `http://127.0.0.1:8001/handshake/sessions/${id}/complete` (`Content-Type` JSON); `!ok` or thrown fetch sets `handshakeError` and keeps plots. Geometry tab (and a right pane on form tabs) is R3F `AircraftCanvas`, lofting WG/HT/VT/NP airfoils and the body the same way as the PySide view (`aid.viz`). Aero tab right pane is `Results`: with analysis raw, tabs Forces, Moments, Derivatives, Downwash, Controls, Spanwise, and Sections plot those Qt coefficient categories (Tornado spanwise and the Prandtl curve included); without raw, SVG CL/CD/Cm vs α overlays from the handshake payload (tables `cl`/`cd`/`cm` only; DATCOM default, Tornado red, flow5 yellow, AVL magenta). CG/static-margin text still comes from `POST /stability` (`aid.stability.aircraft_stability`).
- `Results/` — solver dumps, not versioned (`matlab/`, `python/`, `compare/`).
- Spec/plan: `Docs/2026-08-26-aid-linux-python-port-spec.md` (binding). Handbook extras port: `Docs/2026-10-02-matlab-feature-port-plan.md`.

**Not in scope:** ASCDM, FlightGear/Simulink 6-DOF, neural-network 3-view import, CAD/CFD export, changing DATCOM methods or AVL theory.

## Aircraft data

MATLAB save variables (and JSONC top-level keys):

`WG, HT, VT, F, A, E, R, BD, NP, NB, AERO, plot_cmp, unit` (`cg_data` optional)

| Group | Meaning |
|-------|---------|
| `WG` / `HT` / `VT` | Wing, horizontal tail, vertical tail planforms (DATCOM WGPLNF-style: `CHRDR`, `CHRDTP`, `SSPN`, sweep, dihedral, `NACA`, apex `X,Y,Z`, incidence `i`) |
| `F` / `A` / `E` / `R` | Flap, aileron, elevator, rudder (`$SYMFLP` / `$ASYFLP`; rudder is Tornado/AVL only here) |
| `BD` | Body (`NX`, stations `X`, `ZU`/`ZL`, `R`, `S`, `ITYPE`) |
| `NP` / `NB` | Extra planforms (1×4 cell) and extra bodies (1×2 cell) |
| `AERO` | Flight: `ALSCHD`, `ALT`, `MACH`, `WT`, `XCG`, reference lengths, component positions (`XW`…`ZV`) |
| `unit` | `'ft'` or `'in'` (`DIM IN` only for inches) |
| `plot_cmp` | Component flags `[wing, HT, VT, body]`; DATCOM writes HT/VT/body only when set (wing always) |

JSONC is JSON plus `//` comments on every key. MATLAB field `i` (incidence) is the JSON key `"i"`. Converter: `Python/scripts/mat_to_jsonc.py`. Python GUI Open/Save is JSONC only.

**Bundled models (23):** ASW-20 Sailplane, B-1 Lancer, Beechcraft T-34C, Boeing 727, Boeing 737Max, Boeing 747-400, Box, Cessna 172, DA20-C1, Enterprise, ERAU DBF Plane, F-16, HK36, Learjet 23, Navion, Orbiter, Rocket Prop, Ski Plane, Sphere, SR-71, T-38, XB-70 Valkyrie, X-Wing.

Primary compare aircraft: **Cessna 172**, **Navion**, **DA20-C1**, **Learjet 23**. Status is `ok|failed|skipped`; numbers are not invented. Not all 23×3 succeed. Live Python DATCOM is finite for 19/23 (honest NaN/Inf remain: SR-71, Enterprise, XB-70, X-Wing). Tornado 22/23 (Sphere body-only). AVL 22/23 (T-34C retries weighted-outboard spacing; Sphere has no lifting surface). F-16 DATCOM runs when MACH is clamped to 0.6 at write time; Box DATCOM uses a numeric NACA card; Orbiter DATCOM omits a buried HT; Sphere DATCOM omits HT/VT via `plot_cmp`.

## MATLAB map (`Matlab/fsroot/code`)

| Path | Role |
|------|------|
| `AID.m` | Controller: load/save, plot, Analyze DATCOM/Tornado/AVL |
| `Initialize_GUI.m` | Figure, menus, tabs, option handles |
| `DATCOM_IO.m` | Digital DATCOM namelist `for005.dat` |
| `Tornado_IO.m` | Tornado `geo`/`state` from AID globals |
| `AVL_IO.m` | Write `.avl`/`.run`, invoke AVL |
| `Tornado/*.m` | VLM: lattice, boundary, solver, coefficients |
| `Geometry.m`, `Aero.m`, `Drag.m`, `Atmosphere.m` | Derived planform / aero / CD0 / ISA |
| `run_aid_batch.m` | Headless gold run (no GUI dialogs) |
| `Models/*.mat` | 23 aircraft (decoded names with spaces) |
| `AID_Documentation.pdf` | User manual (Help → User's Manual) |

Results cell: `{DATCOM, ASCDM, Tornado, AVL}` (MATLAB); Python GUI also stores `flow5` after Analyze. Default batch meshes: Tornado 10×5, AVL 10×10, flow5 10×10.

GUI Analyze Tornado matches `AID.m` (handbook trim α, moments about 25% MAC, `CL0=CL-CL_a*α`). GUI Analyze DATCOM recomputes exposed span `SSPNE` from body radius at each planform LE/TE (`AID.m` spline interp) before writing `for005`. Batch gold (`run_aid_batch`) uses stored `.mat` SSPNE, mid-`ALSCHD`, and origin `ref_point`.

## Python package (`Python/`)

- `aid/` — `aircraft` (`.mat`/JSONC), `geometry`/`atmosphere`/`drag` (`aircraft_cd0`), `handbook_pass` / `section_aero` / `aero` / `trim` / `lateral` / `longitudinal_dynamic`, `naca456` + `naca_ordinates`/`panel_method`, `stability` (CG % MAC, static margin, handbook CL/Cm; CD0 from `aircraft_cd0`), `viz` (Plot_Planform/Plot_Body loft meshes, including control-surface hinge deflection), DATCOM write/parse/run, Tornado lattice/boundary/solver/coeff plus opt-in `static_margin` / `viscous` / `pablo`, AVL write/parse/run, flow5 deck writer (`flow5_io`, `flow5_sections`, `flow5_foils`, `flow5_units`), `compare` vs MATLAB gold. No widgets.
- `aid_gui/` — window **Aircraft Intuitive Design Tool** (960×600): File New/Load/Save/Recent (last 5 JSONC, QSettings); Analyze DATCOM/Tornado/AVL/flow5 (Tornado/AVL/flow5 prompt Wing Mesh Parameters); Settings live (plot options, scale, units, calculations including Viscous Strip off by default, Estimate CG, error check, scroll sensitivity); Help (Examples → `Python/models/*.jsonc`; Quick Start dialog; User's Manual PDF; disabled MATLAB control-legend labels); tabs Wing/HT/VT/Control/Body/Aero/`+` laid out like MATLAB `Initialize_GUI.m` (right-aligned label, edit, unit; gray section breaks; visibility checkbox). Wing/HT/VT: 16 planform rows. Control: Flaps/Ailerons/Elevator/Rudder Inboard|Outboard grids. Body: Adjust (station table), Sketch (`ProfileSketchDialog` side/top), Circular Cross-Section. Aero: MATLAB `AP` (α/alt/Mach/WT/XCG/ZCG/XI/YI + root/tip/tail NACA, `%MAC` slider). `+` adds MATLAB `addPart` extras — Body 2/3 (`NB` 1×2), Prop / Wing 2 / HT 2 / VT 2 (`NP` 1×4); Load recreates those tabs when slots are filled. Estimate CG stores 3×10 `cg_data`, click-part X/Z/weight dialog, recomputes WT/XCG/ZCG; Results radios Geometry / Stability / Aerodynamics plus CG/static-margin text; PyVista/VTK 3D aircraft view (initial camera MATLAB `view(3)` nose-on; right-click context menu Reset Plot / View Side-Top-Front / Background load-hide; key isolates the selected-tab component until Reset Plot; Body Adjust edits station X/ZU/ZL/R/P; Tornado Cp `paint_cp` / `clear_cp`). Control-tab δ rotates flaps/ailerons/elevator/rudder; Aerodynamics 60/40 splitter with Prandtl lift overlay, Tornado red after Analyze, handbook drag vs speed, and comparison tabs Forces/Moments/Derivatives/Downwash/Controls/Spanwise (Tornado per surface: Wing/HT/VT/Wing 2…, distinct linestyle and width)/Sections (DATCOM Wing/HT/VT defs plus leftover solver scalars in a grouped scrollable table; vector quantities as columns). Stability and comparison overlays include flow5 (yellow) when Analyze → flow5 has run. Batch/compare stays headless 10×5 / 10×10 (no mesh dialogs). Tornado finish may ask Estimate Neutral Point (skipped offscreen); Yes stores `results["N0"]` without replacing CL/CD.
- Console entry: `aid` → `aid_gui.app:main`.
- Batch: `python scripts/run_all.py` [`--aircraft "Cessna 172"`] writes `Results/python/<name>/` and compare JSON.

DATCOM/AVL Python vs MATLAB should match at parser precision (shared Fortran). Tornado uses spec §13 tolerances (forces 1e-4 rel / 1e-5 abs, derivatives 1e-3 / 1e-4).

## Quick start

**Prerequisites:** Linux, MATLAB R2025b (Aerospace Toolbox / `datcomimport`) for gold runs, Python 3.11+, `gfortran`, `make`, `libx11-dev`, CMake ≥ 3.16, g++ C++20. DATCOM source at `../datcom/datcom.f`. AVL built from `AVL3.52rel09032025/` (plotlib → eispack → `bin/Makefile.gfortranDP`; Linux X11 libs, not `/opt/X11`). flow5 helper: OCCT + OpenBLAS dev packages (see Architecture) then `cmake -S FLOW5 -B FLOW5/build && cmake --build FLOW5/build`.

**MATLAB batch (headless gold run, one aircraft):**

```bash
/home/valentin/ProgramFiles/MB2025b/bin/matlab -batch "cd('Matlab/fsroot/code'); run_aid_batch('Cessna 172')"
```

Run from the repo root; adjust the MATLAB path and `cd(...)` if your checkout differs. Optional second argument: `'datcom'` | `'tornado'` | `'avl'` | `'all'`. All 23: `run_aid_batch_all`.

**Python install and GUI:**

```bash
./start.sh
```

Uses the Anaconda `pigeon` env (`$HOME/anaconda/envs/pigeon`), installs the package if needed, and launches the PySide6 GUI (`aid`). Override the env path with `PIGEON_ENV`. Manual equivalent:

```bash
cd Python
pip install -e ".[dev]"
aid
```

Headless/offscreen: `QT_QPA_PLATFORM=offscreen aid`. Without the console entry point: `python -m aid_gui.app`.

**AID web (API :8002 + Vite :5175):**

```bash
./start-web.sh
```

Kills any previous web instance, then starts FastAPI at `http://127.0.0.1:8002` and Vite at `http://127.0.0.1:5175`. Prefers `api/.venv`. PIDs in `.run/`. Re-run `./start-web.sh` to restart. Stop only: `./kill-web.sh`. Desktop PySide GUI remains `./start.sh`.

Once:

```bash
(cd api && python -m venv .venv && .venv/bin/pip install -e .)
(cd web && npm install)
```

Manual Vite-only: `cd web && npm run dev` (still :5175; API must already be on :8002).

**Python tests (primary compare + full suite except all-23 MATLAB batch):**

```bash
cd Python && python -m pytest tests/ -q --ignore=tests/test_matlab_batch_all.py
```

**AID web tests:**

```bash
cd api && python -m pytest tests/ -q
cd web && npm test
```

## Reading order for agents
1. Read this `README.md` (mandatory if present).
2. Read `UPDATES.md` (mandatory) for the change history and current state before working.
3. Read `Docs/2026-08-26-aid-linux-python-port-spec.md` then `Docs/2026-08-26-aid-sdd-atomic-tasks.md`.
4. GUI MATLAB parity (mesh dialog, view(3), Aerodynamics overlay, Settings): `Docs/2026-08-27-aid-gui-matlab-parity-plan.md`.
