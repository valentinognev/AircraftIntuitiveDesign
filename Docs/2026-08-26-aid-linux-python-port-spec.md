# Aircraft Intuitive Design — Linux MATLAB + Python GUI Port

**Date:** 2026-08-26  
**Status:** locked (approved in session: approach 1, full GUI, AVL 3.52 source, JSONC models)  
**This file is the binding spec.** The implementation plan argues from it.

## 1. Goal

Make the existing MATLAB Aircraft Intuitive Design (AID) tool run on Linux with Digital DATCOM, Tornado, and AVL 3.52 against all bundled aircraft models, dump coefficient results as an oracle, then port AID to a Python desktop GUI that uses the same solvers and the same aircraft data (JSONC), and matches the MATLAB coefficients.

## 2. Non-goals

- Porting ASCDM (MATLAB menu is gated on a missing `ASCDM` folder).
- Porting FlightGear / Simulink 6-DOF (`AID.m` `action=='sim'`).
- Neural-network 3-view import, CAD/CFD export (listed as TO DO in `AID.m`).
- Changing DATCOM empirical methods or AVL vortex-lattice theory.
- Auto-committing or pushing (user must request git commits).

## 3. Platform and tools

| Item | Value |
|------|--------|
| OS | Linux |
| MATLAB | `/home/valentin/ProgramFiles/MB2025b/bin/matlab` (R2025b / 25.2, glnxa64) |
| Aerospace Toolbox | present; `exist('datcomimport')==2` |
| DATCOM source | `/home/valentin/Projects/MDT/USAF_DATCOM/datcom/datcom.f` (PDAS Digital DATCOM) |
| DATCOM compiler | `gfortran datcom.f -o datcom` (install `gfortran` if missing) |
| AVL source | `Matlab/fsroot/code/AVL/AVL3.52rel09032025/` |
| AVL build | plotlib → eispack → `bin/Makefile.gfortranDP` |
| Python | 3.11+; package under `Python/` |
| GUI toolkit | PySide6 |
| Implementer subagent | Composer 2.5 (**not** Composer 2.5 Fast) |
| Reviewer subagent | Grok (`cursor-grok-4.6-high`) |

## 4. Architecture (approved)

Two phases, same repo.

**Phase 1 — MATLAB on Linux.** Decode `%20` model names, compile DATCOM and AVL 3.52, point AID at Linux binaries, batch-run all 23 models, write `Results/matlab/<aircraft>/`.

**Phase 2 — Python twin.** Package split:

- `aid/` — geometry, atmosphere, DATCOM/Tornado/AVL I/O, coefficient assembly (no widgets).
- `aid_gui/` — PySide6 window that mirrors AID menus/tabs/3D view and **only** calls `aid`.

The comparison harness uses the same `aid` calls as the GUI.

DATCOM and AVL remain compiled binaries invoked as subprocesses. Tornado’s VLM is rewritten in Python from `Matlab/fsroot/code/Tornado/*.m`. MATLAB AVL conversion/parse helpers are ported, not replaced with a new file format.

## 5. MATLAB application map

Root of the MATLAB app (unpacked MATLAB App Designer / compiler package):

`Matlab/fsroot/code/`

| File / dir | Role |
|------------|------|
| `AID.m` | Main controller: load/save, plot update, Analyze DATCOM/Tornado/AVL |
| `Initialize_GUI.m` | Figure, menus, tabs, option handles `opt`, component checkboxes `cmp` |
| `DATCOM_IO.m` | Read/write Digital DATCOM namelist (`for005.dat`) |
| `Tornado_IO.m` | Build Tornado `geo`/`state` from AID globals |
| `AVL_IO.m` | Write `.avl`/`.run`, invoke AVL, return run folder |
| `Tornado/*.m` | VLM: `fLattice_setup2`, `solver`, `coeff_create3`, `setboundary5`, … |
| `AVL/parseST.m` etc. | Parse AVL `geometry.st` / `.sb` |
| `AVL/runAVL.m` | Batch `.run` template (Joseph Moster); `AVL_IO.Write_Case` already uses it |
| `Geometry.m`, `Aero.m`, `Drag.m`, `Atmosphere.m` | Derived planform / aero / CD0 / ISA |
| `Models/*.mat` | 23 aircraft save files |
| `AID_Documentation.pdf` | User manual (Help → User's Manual) |

**Analyze wiring in `AID.m` (`action=='save'`):**

- `choice=='DATCOM'`: `cd DATCOM`, `DATCOM_IO('for005.dat','case',…)`, `system('./datcom.osx')` on non-Windows, `datcomimport('for006.dat',true)` → `Results{1}`. Success = `isfield(Results{1},'cl')`.
- `choice=='Tornado'`: mesh dialog default `{'10','5'}`, `Tornado_IO` → `fLattice_setup2(geo,state,0)` → `solver` → `coeff_create3` → `Results{3}`.
- `choice=='AVL'`: mesh default `{'10','10'}`, same `Tornado_IO` geo, `AVL_IO` → `parseST(.../geometry.st)` → `Results{4}`.

**Results cell:** `{DATCOM, ASCDM, Tornado, AVL}`.

**Plot comparison** (`AID.m` ~1370): DATCOM `Results{1}.alpha`, `.cl`, `.cm` vs Tornado/AVL overlays.

## 6. Aircraft `.mat` schema

`save` in `AID.m` writes:

`WG, HT, VT, F, A, E, R, BD, NP, NB, AERO, plot_cmp, unit, cg_data`

Cessna 172 (loaded 2026-08-26) has no `cg_data`. `NP` is 1×4 cell (extra planforms); `NB` is 1×2 cell (extra bodies). `plot_cmp` is `[1 1 1 1]` (wing, HT, VT, body). `unit` is `'ft'`.

### 6.1 Planform fields (WG / HT / VT) — DATCOM names + GUI labels

From `Initialize_GUI.m` `RP` / `PR`:

| Field | GUI label | Units (ft mode) | Notes |
|-------|-----------|-----------------|-------|
| `CHRDR` | Root Chord | ft | DATCOM WGPLNF |
| `CHRDBP` | Break Chord | ft | 0 or unused if `SSPNOP==0` |
| `CHRDTP` | Tip Chord | ft | |
| `SSPN` | Semi-Span | ft | |
| `SSPNOP` | Break Span | ft | AID stores span from root; DATCOM write converts to span from tip (`SSPN-SSPNOP`) |
| `SAVSI` | Inboard Sweep | deg | |
| `SAVSO` | Outboard Sweep | deg | |
| `CHSTAT` | Sweep Reference | LE–TE fraction | 0 = LE, 1 = TE typical |
| `DHDADI` | Inboard Dihedral | deg | |
| `DHDADO` | Outboard Dihedral | deg | |
| `TC` | Thickness | chord fraction | |
| `TWISTA` | Washout | deg | |
| `i` | Incidence | deg | DATCOM `ALIW`/`ALIH` via SYNTHS |
| `X`,`Y`,`Z` | Position | ft | Apex location |
| `NACA` | airfoil id | string cell | e.g. `{'2412'}` |
| `DATA` | airfoil xy | cell of N×2 | from `NACA_Panel_Maker` |

Derived by `Geometry.m` / `Aero.m` / `Drag.m` (must recompute in Python, not treated as independent inputs): `b, cbar, TR, S, AR, gamma, Xtip, Xbrk, Zbrk, Ztip, Ybrk, Ytip, swp, ymac, xmac, SSPNE, a0, alpha0, alpha0L, Cm_ac, Cm, CD0, a, x_ac, CL0, e, K, CM0, Cm0`, plus HT/VT volume `V, l, dwash, eta, swash, AReff, hp, lp, h, k`.

### 6.2 Controls

| Struct | Fields | Meaning |
|--------|--------|---------|
| `F` (flap) | `FTYPE, PHETE, PHETEP, TC, CB, SPANFI, SPANFO, CHRDFI, CHRDFO, DELTA` | DATCOM `$SYMFLP` |
| `A` (aileron) | `STYPE, SPANFI, SPANFO, CHRDFI, CHRDFO, DELTAL, DELTAR, Kb` | DATCOM `$ASYFLP` |
| `E` (elevator) | same as flap | second `$SYMFLP` |
| `R` (rudder) | `SPANFI, SPANFO, CHRDFI, CHRDFO, DELTA` | Tornado/AVL only in this app |

### 6.3 Body `BD`

`NX, X, ZU, ZL, R, S, N, P, ITYPE` plus derived `CD0, CMa, Cma, CM0, Cm0, CNB, Cnb, dk`.

### 6.4 Flight `AERO`

`ALSCHD, ALT, MACH, WT, XCG, ZCG, XI, YI, XW, YW, ZW, ALIW, XH, YH, ZH, ALIH, XV, YV, ZV, NALPHA, NALT, NMACH, LOOP, SREF, CBARR, BLREF`.

Cessna 172 gold values (ft, loaded from `Cessna%20172.mat`):

- `ALSCHD = [-4, 0, 4, 8, 12]`, `ALT = 0`, `MACH = 0.03`, `WT = 5`, `XCG = 2.94`
- Wing `CHRDR=2, CHRDTP=2, SSPN=6, DHDADI=3, X=2.2, Z=1.15, NACA 2412`, `S=24`

## 7. Model files (23)

Directory: `Matlab/fsroot/code/Models/`

On disk they are URL-encoded (`Cessna%20172.mat`). MATLAB `uigetfile` and `Help → Examples` expect spaces (`Cessna 172.mat`). **Phase 1 must rename** (`%20` → space, `%` decode).

Aircraft list after decode:

1. ASW-20 Sailplane  
2. B-1 Lancer  
3. Beechcraft T-34C  
4. Boeing 727  
5. Boeing 737Max  
6. Boeing 747-400  
7. Box  
8. Cessna 172  
9. DA20-C1  
10. Enterprise  
11. ERAU DBF Plane  
12. F-16  
13. HK36  
14. Learjet 23  
15. Navion  
16. Orbiter  
17. Rocket Prop  
18. Ski Plane  
19. Sphere  
20. SR-71  
21. T-38  
22. XB-70 Valkyrie  
23. X-Wing  

Primary comparison aircraft (must pass): **Cessna 172**, **Navion**, **DA20-C1**, **Learjet 23**.  
All 23 must be attempted; exotic shapes (Sphere, Box, X-Wing, Enterprise, Orbiter, SR-71) may fail DATCOM — record `status: skipped|failed|ok` per solver, do not fake numbers.

## 8. DATCOM Linux behavior (critical)

PDAS `datcom.f` (lines 6886–6904):

- Prints `Enter the input file name:`
- Reads filename from **stdin**
- Opens that file as unit 5
- Writes **`datcom.out`** (unit 6), **not** `for006.dat`
- Also writes `for013.dat`, `for014.dat`

Windows/macOS binaries used by AID (`DATCOM/datcom.exe`, `datcom.osx`) consume `for005.dat` and produce `for006.dat`.

**Required adapter:** a wrapper `DATCOM/datcom` (shell) that:

1. Takes no interactive prompt when invoked from MATLAB/Python.
2. Feeds `for005.dat` on stdin to the Fortran binary (or argv if we add a tiny wrapper).
3. Copies `datcom.out` → `for006.dat` so `datcomimport` and the Python parser see the AID-expected name.

MATLAB `AID.m` non-Windows branch must call `./datcom` (the wrapper), not `./datcom.osx`.

Batch/non-GUI DATCOM runs must **not** show `questdlg` for wing-only flap case. Headless runner passes a flag equivalent to answering “no” (`owg` not `'Yes'`).

## 9. AVL 3.52

Source: `Matlab/fsroot/code/AVL/AVL3.52rel09032025/`

Build order (README):

1. `plotlib` — `make gfortranDP` (or equivalent) → `libPlt_gDP.a`
2. `eispack` — `make -f Makefile.gfortran`
3. `bin` — `make -f Makefile.gfortranDP avl`

Linux fix: `Makefile.gfortranDP` has `PLTLIB = -L/opt/X11/lib -lX11` (macOS). On Linux use `-L/usr/lib/x86_64-linux-gnu -lX11` (or `pkg-config --libs x11`). Need `gfortran`, `make`, `libx11-dev`. Batch runs use `PLOP / g` to disable graphics (`AVL_IO.Write_Case`).

Install the executable to `Matlab/fsroot/code/AVL/run/avl` (replace/supplement `avl3.35` / `avl.exe`).

`AVL_IO.m` else-branch currently: `system(['./avl3.35',' < ',CaseID,'.run']);`  
Patch to `./avl`.

**Do not invent a new `.avl` writer.** Port:

- `Tornado_IO.m` `Write_Geometry` (geo/state)
- `AVL_IO.m` `Write_Input`, `Write_Surface`, `Write_Case`
- `AVL/parseST.m`, `parseSB.m`, `parseRunCaseHeader.m`, `findValue.m`

`runAVL.m` is the historical template; `Write_Case` is the one AID actually executes.

Default batch mesh: spanwise 10, chordwise 10 (AID AVL dialog defaults).

## 10. Tornado

MATLAB files to port (order):

1. `Tornado_IO.m` — `geo`/`state` from AID aircraft  
2. `Tornado/fLattice_setup2.m`  
3. `Tornado/setboundary5.m`  
4. `Tornado/solver.m` — drop MATLAB waitbar (`h`); empty-results path if cancelled becomes unused  
5. `Tornado/coeff_create3.m`  
6. `Tornado/ISAtmosphere.m`  
7. `Tornado/fFindstaticmargin.m` — optional; batch default **skip** NP dialog (`questdlg` No)  
8. Supporting: `fViscCorr2.m`, `fmultLattice.m`, `fPablo.m`, `fSonicCP.m`, `config.m` only if called

Default batch mesh: spanwise 10, chordwise 5, mode 0 (freestream-following wake).

## 11. Python aircraft format (JSONC)

Path: `Python/models/<Aircraft Name>.jsonc`

- JSON with `//` line comments **on every key** (and array-bearing objects).
- Top-level keys match the `.mat` variables: `WG, HT, VT, F, A, E, R, BD, NP, NB, AERO, plot_cmp, unit` (`cg_data` optional).
- Numeric arrays as JSON arrays. Airfoil `DATA` as nested lists.
- MATLAB struct field `i` (incidence) is serialized as `"i"` (legal JSON key).
- Converter: `Python/scripts/mat_to_jsonc.py` reads decoded `.mat`, writes JSONC using the field-comment catalog in this spec (GUI label + DATCOM namelist + units).
- GUI Open/Save uses JSONC only. MATLAB Phase 1 continues to use `.mat`.

Loader: strip `//` comments (not inside strings), then `json.loads`. Do not require `json5` if a 40-line stripper suffices; `json5` is allowed.

## 12. Results layout

```
Results/
  matlab/<aircraft>/{datcom.json,tornado.json,avl.json,for005.dat,datcom.out,geometry.avl,geometry.st,status.json}
  python/<aircraft>/{datcom.json,tornado.json,avl.json,status.json}
  compare/<aircraft>.json
```

JSON coefficient dumps must include at least:

- DATCOM: `alpha`, `cl`, `cd`, `cm`, `cla`, `cma` (names as `datcomimport` returns, lowercase).
- Tornado: `CL`, `CD`, `Cm`, `CL_a`, `Cm_a`, `CY`, `Cl`, `Cn` and spanwise if present.
- AVL: `parseST` fields `CLa, Cma, CLb, Clb, Cnb, NP, …`.

## 13. Comparison tolerances

Compare Python vs MATLAB on the same model, same mesh, same Mach/alpha.

| Quantity | Relative | Absolute floor |
|----------|----------|----------------|
| Forces `CL, CD, CY` | 1e-4 | 1e-5 |
| Moments `Cl, Cm, Cn` | 1e-4 | 1e-5 |
| Derivatives `/rad` (`CLa`, …) | 1e-3 | 1e-4 |
| DATCOM table vs alpha | max abs error 1e-3 on `cl`,`cm` | |

Fortran DATCOM/AVL binaries are shared → DATCOM/AVL Python vs MATLAB should match at parser precision (near machine-eps on parsed text), not 1e-3. If parsers disagree, fix the parser. Tornado is a port → use the table above.

## 14. Python GUI (full port)

PySide6 window **Aircraft Intuitive Design Tool**, default 960×600.

**Menus (from `Initialize_GUI.m`):** New, Load, Save, Analyze {DATCOM, Tornado, AVL}, Settings {Scale, Estimate CG, Plot Options, Calculations, Units, Inputs/Outputs, Error Check, Scroll Sensitivity}, Help {Examples, Quick Start, User's Manual, control legend}.

**Tabs:** Wing, HT, VT, Control, Body, Aero, `+` (add part).

**Center:** 3D aircraft view (perspective, equal aspect). Port `Plot_Planform.m` / `Plot_Body.m` behavior enough to show the loaded model and update on field edits.

**Out of first GUI milestone (defer, do not block solver tests):** background image tracing, profile sketcher double-click, isolate-part hotkeys, report overlay expressions, interpolated shading quality match. Ship stubs that do not crash.

Help → User's Manual opens `Matlab/fsroot/code/AID_Documentation.pdf`.

## 15. Error handling

- Missing binary: dialog/log with the path that was tried; do not hang on stdin.
- DATCOM input rejected: keep `datcom.out`, surface first error line, `status.failed`.
- AVL no `geometry.st`: fail the run, do not parse empty.
- JSONC unknown key: keep it (forward compatible); missing required planform key: refuse Analyze.
- Units: `unit` is `ft` or `in`; DATCOM `DIM IN` only when inches (`DATCOM_IO.m`).

## 16. Headless MATLAB runner

Do not rely on clicking the GUI for gold results. Add `Matlab/fsroot/code/run_aid_batch.m` that:

1. Adds `code/`, `code/Tornado`, `code/AVL` to path.
2. Loads each `.mat` with spaces in the name.
3. Reconstructs the globals `Geometry`/`Aero` would fill by calling `Geometry`, `Aero`, `Atmosphere` as AID’s update path does (or loads already-derived fields from the `.mat` — Cessna already has derived fields).
4. Writes DATCOM input via `DATCOM_IO` with `choice` not triggering dialogs (use `'batch'` and patch `questdlg` branches to default No).
5. Runs DATCOM wrapper, `datcomimport`.
6. Builds Tornado mesh `{10,5}`, runs solver, saves `Results{3}` via `jsonencode` of selected fields.
7. Builds AVL mesh `{10,10}`, runs `AVL_IO` with `check_io=false`, `parseST`.
8. Writes `Results/matlab/<name>/`.

`questdlg` / `inputdlg` / `warndlg` must not block. Patch those call sites in a **copy** used by batch (`choice=='batch'`) rather than deleting GUI dialogs.

## 17. Execution process

- Implement with **subagent-driven development**.
- Each task: Composer 2.5 implementer, then Grok reviewer.
- No Composer 2.5 Fast. No Kimi 3.
- Do not commit unless the user asks.
- Update root `README.md` / `UPDATES.md` after meaningful slices (project-docs rule).
