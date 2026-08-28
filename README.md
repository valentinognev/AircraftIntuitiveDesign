# Aircraft Intuitive Design

Conceptual aircraft geometry editor and aerodynamic analysis tool. Enter a wing, tails, body, controls, and flight condition; get lift, drag, and moment coefficients from three independent solvers: USAF Digital DATCOM, Tornado (vortex lattice), and AVL 3.52.

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

AID also uses Joseph Moster’s AVL MATLAB I/O helpers (bundled under `Matlab/fsroot/code/AVL/`) and MathWorks Aerospace Toolbox `datcomimport` for MATLAB gold DATCOM dumps.

## Idea

AID is a conceptual-design workbench, not a CAD or CFD package. Geometry is stored in DATCOM-style planform fields (root/tip chord, semi-span, sweep, dihedral, NACA sections, apex position). Derived quantities — area, MAC, aspect ratio, CD0, lift-curve slope — are recomputed, not treated as independent inputs.

Analyze runs one of three methods and overlays coefficients vs angle of attack:

| Solver | Kind | How it runs |
|--------|------|-------------|
| **DATCOM** | Empirical / handbook (PDAS Digital DATCOM Fortran) | Shared Linux binary via a stdin wrapper |
| **Tornado** | Vortex-lattice method | MATLAB `.m` in `Tornado/`; rewritten in Python |
| **AVL 3.52** | Vortex-lattice (Drela/Youngren) | Shared binary; AID writes `.avl`/`.run` and parses `geometry.st` |

MATLAB remains the gold runner. Python `aid` is a headless engine; `aid_gui` is the only widget layer and calls `aid` for load, save, and Analyze.

## Architecture

Two stacks, one repo. DATCOM and AVL are compiled once and invoked as subprocesses from both languages. Tornado is a source port, so coefficient compare uses looser tolerances than the shared Fortran parsers.

```
Aircraft (WG/HT/VT/F/A/E/R/BD/AERO)
        │
        ├─ MATLAB AID.m  ── DATCOM_IO / Tornado_IO / AVL_IO ──► Results/matlab/
        │
        └─ Python aid    ── datcom_io / tornado_io / avl_io ──► Results/python/
                    │
                    └─ aid_gui (PySide6 + pyvistaqt 3D)  +  compare.py vs MATLAB gold
```

- `Matlab/fsroot/code` — AID GUI, geometry/aero/drag, Tornado VLM, AVL I/O, 23 `.mat` models, user manual PDF.
- DATCOM Fortran lives beside this repo at `../datcom/datcom.f` (namelist MAXNX=200 body stations, MAXNPTS=500 airfoil points; analysis uses the first 60 section points). AID writers clamp wing `$WGSCHR` to 60 and HT/VT/extra to 50 so Analyze cannot hang. Python `write_for005` wraps BODY arrays at 80 columns (`body_max=200`, no 18-station downsample), clamps MACH>0.6 to STMACH 0.6, omits DATCOM-illegal HT/VT (buried/negative SSPNE, SSPNE>SSPN, zero area) and inverted control spans (SPANFO<=SPANFI; no elevator namelist without HT). SPANFO past parent SSPN is still written, clamped to parent SSPN so DATCOM does not SIGSEGV (DA20 elevator). Uses a later numeric NACA when the first cell is `Data.`/a path (stored JSONC unchanged). Linux binary `DATCOM/datcom.bin` is gitignored; wrapper `DATCOM/datcom` feeds `for005.dat` on stdin and copies `datcom.out` → `for006.dat` even if the binary later SIGSEGVs (AID/`datcomimport` expect that name). AVL `run_avl_full` retries weighted-outboard / equal spanwise spacing if `geometry.st` is missing (GUI Analyze AVL with Inputs/Outputs uses the same retry, then previews the successful files).
- AVL 3.52 source: `Matlab/fsroot/code/AVL/AVL3.52rel09032025/`. Install executable to `AVL/run/avl` (gitignored).
- `Python/` — package `aid` (engine) + `aid_gui` (PySide6). Models: `Python/models/*.jsonc`.
- `Results/` — solver dumps, not versioned (`matlab/`, `python/`, `compare/`).
- Spec/plan: `Docs/2026-08-26-aid-linux-python-port-spec.md` (binding), atomic tasks, implementation plan.

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

Results cell: `{DATCOM, ASCDM, Tornado, AVL}`. Default batch meshes: Tornado 10×5, AVL 10×10.

GUI Analyze Tornado matches `AID.m` (handbook trim α, moments about 25% MAC, `CL0=CL-CL_a*α`). GUI Analyze DATCOM recomputes exposed span `SSPNE` from body radius at each planform LE/TE (`AID.m` spline interp) before writing `for005`. Batch gold (`run_aid_batch`) uses stored `.mat` SSPNE, mid-`ALSCHD`, and origin `ref_point`.

## Python package (`Python/`)

- `aid/` — `aircraft` (`.mat`/JSONC), `geometry`/`atmosphere`/`drag`, `stability` (CG % MAC, static margin, handbook CL/Cm), `viz` (Plot_Planform/Plot_Body loft meshes, including control-surface hinge deflection), DATCOM write/parse/run, Tornado lattice/boundary/solver/coeff, AVL write/parse/run, `compare` vs MATLAB gold. No widgets.
- `aid_gui/` — window **Aircraft Intuitive Design Tool** (960×600): File New/Load/Save; Analyze DATCOM/Tornado/AVL (Tornado/AVL always prompt Wing Mesh Parameters); Settings live (plot options, scale, units, calculations, Estimate CG, error check, scroll sensitivity); Help (Examples → `Python/models/*.jsonc`; Quick Start dialog; User's Manual PDF; disabled MATLAB control-legend labels); tabs Wing/HT/VT/Control/Body/Aero/`+` (Aero is MATLAB `AP`: α/alt/Mach/WT/XCG/ZCG/XI/YI + root/tip/tail NACA, `%MAC` slider). `+` adds MATLAB `addPart` extras — Body 2/3 (`NB` 1×2), Prop / Wing 2 / HT 2 / VT 2 (`NP` 1×4); Load recreates those tabs when slots are filled. Estimate CG stores 3×10 `cg_data`, click-part X/Z/weight dialog, recomputes WT/XCG/ZCG; Results radios Geometry / Stability / Aerodynamics plus CG/static-margin text; PyVista/VTK 3D aircraft view (initial camera MATLAB `view(3)` nose-on; right-click context menu Reset Plot / View Side-Top-Front / Background load-hide; key isolates the selected-tab component until Reset Plot; Body Adjust edits station X/ZU/ZL/R/P). Control-tab δ rotates flaps/ailerons/elevator/rudder; Aerodynamics 60/40 splitter with Prandtl lift overlay, Tornado red after Analyze, handbook drag vs speed, and comparison tabs Forces/Moments/Derivatives/Downwash/Controls/Spanwise/Sections overlaying DATCOM/Tornado/AVL, with leftover solver scalars on Sections). Batch/compare stays headless 10×5 / 10×10 (no mesh dialogs).
- Console entry: `aid` → `aid_gui.app:main`.
- Batch: `python scripts/run_all.py` [`--aircraft "Cessna 172"`] writes `Results/python/<name>/` and compare JSON.

DATCOM/AVL Python vs MATLAB should match at parser precision (shared Fortran). Tornado uses spec §13 tolerances (forces 1e-4 rel / 1e-5 abs, derivatives 1e-3 / 1e-4).

## Quick start

**Prerequisites:** Linux, MATLAB R2025b (Aerospace Toolbox / `datcomimport`) for gold runs, Python 3.11+, `gfortran`, `make`, `libx11-dev`. DATCOM source at `../datcom/datcom.f`. AVL built from `AVL3.52rel09032025/` (plotlib → eispack → `bin/Makefile.gfortranDP`; Linux X11 libs, not `/opt/X11`).

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

**Python tests (primary compare + full suite except all-23 MATLAB batch):**

```bash
cd Python && python -m pytest tests/ -q --ignore=tests/test_matlab_batch_all.py
```

## Reading order for agents
1. Read this `README.md` (mandatory if present).
2. Read `UPDATES.md` (mandatory) for the change history and current state before working.
3. Read `Docs/2026-08-26-aid-linux-python-port-spec.md` then `Docs/2026-08-26-aid-sdd-atomic-tasks.md`.
4. GUI MATLAB parity (mesh dialog, view(3), Aerodynamics overlay, Settings): `Docs/2026-08-27-aid-gui-matlab-parity-plan.md`.
