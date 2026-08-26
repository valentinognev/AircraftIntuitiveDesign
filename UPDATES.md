# Updates

## 0.3.9 - geometry.py break-span branch
- `Python/src/aid/geometry.py`: break-span branch from `Geometry.m` lines 5–67 — segmented `S`/`AR`/`cbar`/`TR`, equivalent taper via quadratic (`b_quad` not span), weighted sweep/dihedral, tip/break locations
- `Python/tests/test_geometry_break_span.py`: weighted `cbar` and total `S` asserts for kinked planform

## 0.3.8 - geometry.py linear taper branch
- `Python/src/aid/geometry.py`: `geometry(pt, angl, type)` — single linear taper from `Geometry.m` else branch; sweep/MAC block; break-span raises (Task 30)
- `Python/tests/test_geometry_cessna_linear.py`: Cessna 172 gold `S=24`, `cbar=2`, `AR=6`

## 0.3.7 - atmosphere.py ISA port
- `Python/src/aid/atmosphere.py`: `atmosphere(h_ft)` — piecewise theta/delta/sigma from `Atmosphere.m`, keys `T,P,D,V,a`
- `Python/tests/test_atmosphere.py`: sea-level ISA asserts `T≈518.69`, speed of sound, `D>0`

## 0.3.6 - mat_to_jsonc all 23 models
- `Python/scripts/mat_to_jsonc.py`: batch `.mat` → `Python/models/*.jsonc` via `load_mat`/`save_jsonc`
- `Python/models/*.jsonc`: 23 aircraft JSONC source models (incl. `Cessna 172.jsonc`)
- `Python/tests/test_mat_to_jsonc_all.py`: asserts 23 `.mat` ↔ 23 `.jsonc`
- `Python/src/aid/jsonc.py`: serialize NaN/Inf as JSON `null` for valid comment-stripped parse
- `Python/src/aid/aircraft.py`: default missing `unit` to `"ft"` (matches `run_aid_batch.m`)
- `Python/src/aid/field_docs.py`: TYPE, e0, CL, XCG/ZCG/WT, spanwise.*, BD X0/Y0/Z0/d_eq

## 0.3.5 - dumps_jsonc comments on every key
- `Python/src/aid/jsonc.py`: `dumps_jsonc(data, docs)` — pretty-print with `//` on every dict key via dotted DOCS lookup (NP→WG, NB→BD fallbacks)
- `Python/src/aid/aircraft.py`: `save_jsonc(ac, path)`, `load_jsonc(path)` — write/read JSONC round-trip via `asdict` + `field_docs.DOCS`
- `Python/src/aid/field_docs.py`: top-level section keys (WG, HT, …) and control derived fields (F.S, F.tau, F.l, F.x_ac, E.S, E.tau, R.S, R.tau)
- `Python/tests/test_jsonc_comments_every_key.py`: Cessna save asserts every `:` line has `//`

## 0.3.4 - load_mat preserves 2-D airfoil DATA
- `Python/src/aid/aircraft.py`: non-column 2-D arrays → nested lists (N×2 `DATA`); column vectors still flatten (ALSCHD)
- `Python/tests/test_aircraft_load_mat.py`: asserts `WG.DATA` is 101×2 nested list

## 0.3.3 - aircraft.load_mat from MATLAB .mat
- `Python/src/aid/aircraft.py`: `@dataclass Aircraft` + `load_mat(path)` — scipy loadmat, recursive mat_struct→dict, NP/NB empty doubles→None, field `i` preserved
- `Python/tests/test_aircraft_load_mat.py`: Cessna gold asserts `unit`, `WG.CHRDR`, `AERO.ALSCHD`

## 0.3.2 - JSONC comment stripper loads_jsonc
- `Python/src/aid/jsonc.py`: `loads_jsonc(text)` — line-oriented `//` stripper respecting quoted strings, then `json.loads`
- `Python/tests/test_jsonc_loads.py`: asserts WG/unit fields parse from JSONC sample with inline comments

## 0.3.1 - JSONC field documentation catalog
- `Python/src/aid/field_docs.py`: `DOCS` dict (248 dotted paths) from spec §6.1–6.4 and `Initialize_GUI.m` labels; WG/HT/VT derived keys (`S`, `cbar`, `AR`, …)
- `Python/tests/test_field_docs.py`: asserts Cessna wing/aero keys including `"Root Chord"` in `DOCS["WG.CHRDR"]`

## 0.3.0 - aid.paths models_dir
- `Python/src/aid/paths.py`: `models_dir()` → `repo_root() / "Python" / "models"`
- `Python/tests/test_paths.py`: `test_paths_resolve` asserts path helpers including `models_dir().name == "models"`

## 0.2.0 - MATLAB gold Results/matlab for all 23 models
- `run_aid_batch_all.m`: batch driver over `Models/*.mat`; per-model `try/catch`; skip when `status.json` already has all three solver fields; writes `Results/matlab/_summary.json`
- `Python/tests/test_matlab_batch_all.py`: asserts 23 summary rows and per-model `status.json`
- Gold batch: 23/23 attempted; primary four honest (Cessna/DA20/Learjet three-way `ok`; Navion datcom `failed`, tornado+avl `ok`)

## 0.1.24 - Primary gold test expects Navion DATCOM failed
- `Python/tests/test_matlab_gold_primary.py`: per-aircraft `EXPECTED` map; Navion `datcom: failed` (Linux binary exit 139), tornado/avl `ok`; DA20-C1 and Learjet 23 all three `ok`

## 0.1.23 - Honest primary gold status and usable coefficients
- `run_aid_batch.m`: `gold_datcom_ok`/`gold_tornado_ok` reject ND (`99999`) and empty/NaN; record `datcom: binary exit N` on crash; delete stale JSON on failure
- `DATCOM/datcom`: restored `set -e` (no `|| true` on segfault)
- `DATCOM_IO.m`: skip batch elevator `SYMFLP` when `E.SPANFI<0.01`; body write uses local `body` struct (no global `BD` mutation); `write_namelist_array` capped at 12+6
- `fLattice_setup2.m`: sanitize NaN/`<=0` `geo.T` before chord extrapolation (fixes Navion/DA20 Tornado NaN lattice)
- `AVL_IO.m`: cosine spacing only when `geo.nelem(k)>=4` (not all multi-section); retains tip NaN/degenerate-section fixes
- Navion DATCOM: `failed` (binary exit 139 segfault); DA20-C1 and Learjet 23 all three `ok` with finite coefficients

## 0.1.22 - MATLAB gold primary aircraft (Navion, DA20, Learjet)
- `run_aid_batch.m`: default `solver='all'` runs DATCOM+Tornado+AVL sequentially; per-solver dispatch preserved
- `DATCOM/datcom`: copy `datcom.out` even when `datcom.bin` segfaults (Navion)
- `DATCOM_IO.m`: `$BODY` arrays chunked 12+6 (max 18 stations; decimate longer bodies); `write_namelist_array` helper
- `AVL_IO.m`: scalar `WG.S(end)` refs; NaN tip chord fallback; cosine spacing for multi-section wings; skip degenerate tip sections; empty `.st` guard
- `Python/tests/test_matlab_gold_primary.py`: asserts Navion, DA20-C1, Learjet 23 all three `ok` in `status.json`
- Gold runs: `run_aid_batch('Navion')` etc. → `Results/matlab/<model>/` (gitignored)

## 0.1.21 - MATLAB gold AVL dump for Cessna 172
- `Matlab/fsroot/code/run_aid_batch.m`: `run_avl_gold` — mesh `{'10','10'}`, `Tornado_IO`/`AVL_IO(...,false)`/`parseST`, merges `status.json` (preserves `datcom`/`tornado: ok`); deletes stale `geometry.st`/`.sb` before run
- `Matlab/fsroot/code/AVL_IO.m`: IYsym/IZsym/Zsym line uses `%d %d %.1f` (AVL 3.52 rejects `0.0 0.0 0.0`)
- `Python/tests/test_matlab_gold_cessna_avl.py`: asserts `avl: ok`, `CLa` in `avl.json`, `geometry.st` present
- Gold run: `run_aid_batch('Cessna 172','avl')` → `Results/matlab/Cessna 172/avl.json` (gitignored)

## 0.1.20 - MATLAB gold Tornado dump for Cessna 172
- `Matlab/fsroot/code/run_aid_batch.m`: `run_tornado_gold` — mesh `{'10','5'}`, `Tornado_IO`/`fLattice_setup2(geo,state,0)`/`solver`/`coeff_create3`, merges `status.json` (preserves `datcom: ok`)
- `Matlab/fsroot/code/Tornado/fLattice_setup2.m`, `coeff_create3.m`: R2025b `size()` loop-index fixes (`numel` / `size(...,1)`)
- `Python/tests/test_matlab_gold_cessna_tornado.py`: asserts `tornado: ok` and `CL`/`CD`/`Cm` in `tornado.json`
- Gold run: `run_aid_batch('Cessna 172','tornado')` → `Results/matlab/Cessna 172/tornado.json` (gitignored)

## 0.1.19 - DATCOM_IO batch DATCOM-safe SYNTHS
- `Matlab/fsroot/code/DATCOM_IO.m`: `$SYNTHS` branch matches `'batch'` as well as `'DATCOM'` (no YW/YH)
- `Matlab/fsroot/code/run_aid_batch.m`: `run_datcom_gold` calls `DATCOM_IO(...,'batch',...)` per plan
- `Python/tests/test_datcom_io_batch.py`: asserts batch uses DATCOM-safe SYNTHS condition

## 0.1.18 - MATLAB gold DATCOM dump for Cessna 172
- `Matlab/fsroot/code/run_aid_batch.m`: `run_datcom_gold` — load `.mat`, hidden `cmp`/`opt` stubs, `DATCOM_IO`/`./datcom`/`datcomimport`, JSON to `Results/matlab/<model>/`
- `Python/tests/test_matlab_gold_cessna_datcom.py`: asserts `status.json` `datcom: ok` and coefficient fields in `datcom.json`
- Gold run: `run_aid_batch('Cessna 172','datcom')` → `Results/matlab/Cessna 172/` (gitignored)

## 0.1.17 - run_aid_batch JSON strip helpers
- `Matlab/fsroot/code/run_aid_batch.m`: stub main (`error('not implemented')`); local helpers `onoff`, `write_json`, `strip_datcom`, `strip_tornado`
- `Python/tests/test_run_aid_batch_helpers.py`: asserts file exists and helper function declarations present

## 0.1.16 - AID.m Tornado NP batch default
- `Matlab/fsroot/code/AID.m`: NP `questdlg` skipped when `choice=='batch'`; default `np='No'`
- `Python/tests/test_aid_tornado_batch_np.py`: asserts batch guard around NP estimate dialog

## 0.1.15 - DATCOM_IO batch dialog defaults
- `Matlab/fsroot/code/DATCOM_IO.m`: `Write_DATCOM` skips `questdlg` when `choice=='batch'`; default `owg`, `cg_calc=0`
- `Python/tests/test_datcom_io_batch.py`: asserts explicit `strcmp(choice,'batch')` guard in DATCOM_IO.m

## 0.1.14 - AVL_IO.m Linux binary
- `Matlab/fsroot/code/AVL_IO.m`: else-branch calls `./avl` (Task 10 binary); removed macOS `DYLD_LIBRARY_PATH` setenv
- `Python/tests/test_avl_io_patch.py`: asserts `./avl` invocation, no `avl3.35` in file

## 0.1.13 - AID.m Linux DATCOM wrapper
- `Matlab/fsroot/code/AID.m`: non-Windows DATCOM branch calls `system('./datcom')` instead of `./datcom.osx`
- `Python/tests/test_aid_datcom_patch.py`: asserts Linux branch uses wrapper, not macOS binary

## 0.1.12 - AVL batch quit smoke
- `Python/tests/test_avl_smoke.py`: runs `avl` with stdin `PLOP\ng\n\nQuit\n`; asserts exit 0 within 30s (Task 10 binary; no X11 fix needed)

## 0.1.11 - AVL 3.52 binary install
- `Python/tests/test_avl_binary.py`: asserts `AVL/run/avl` exists and is executable
- Built `AVL3.52rel09032025/bin/avl` via `make -f Makefile.gfortranDP avl`, copied to `AVL/run/avl` (binary gitignored; reproduce locally)

## 0.1.10 - AVL eispack gfortran build
- `Python/tests/test_avl_eispack.py`: asserts `eispack/libeispack.a` (or `*.a`) exists after local build
- Built `eispack/libeispack.a` via `make -f Makefile.gfortran` (archive gitignored; reproduce locally)

## 0.1.9 - plotlib gfortranDP Linux X11 paths
- `plotlib/config.make.gfortranDP`: `LINKLIB`/`INCDIR` aligned with Task 7 Linux X11 (`/usr/lib/x86_64-linux-gnu`, `/usr/include`)
- `Python/tests/test_avl_makefile_linux.py`: asserts gfortranDP plotlib template has no macOS X11 paths

## 0.1.8 - AVL plotlib gfortranDP build
- `Python/tests/test_avl_plotlib.py`: asserts `plotlib/libPlt_gDP.a` (or `libPlt.a`) exists after local build
- Built `plotlib/libPlt_gDP.a` via `make gfortranDP` (archive gitignored; reproduce locally)

## 0.1.7 - AVL Makefile Linux X11 path
- `bin/Makefile.gfortranDP`: `PLTLIB` uses `-L/usr/lib/x86_64-linux-gnu -lX11` instead of macOS `/opt/X11`
- `plotlib/config.make`: `LINKLIB`/`INCDIR` pointed at Linux X11 lib and headers
- `Python/tests/test_avl_makefile_linux.py`: asserts no `/opt/X11` in gfortranDP makefile

## 0.1.6 - MATLAB gold scalar check for Cessna 172.mat
- `Python/tests/test_cessna_mat_gold.py`: loads `Models/Cessna 172.mat` via MATLAB `-batch`, asserts WG/AERO gold scalars

## 0.1.5 - Decode URL-encoded model .mat filenames
- Renamed 12 `Models/*.mat` files (`%20` → space) via `urllib.parse.unquote`
- `Python/tests/test_model_filenames.py`: asserts 23 models, no `%20` in names

## 0.1.4 - DATCOM smoke BODY fix and coefficient asserts
- `test_datcom_wrapper_smoke.py`: circular `$BODY` uses X+R only; tapered wing with SSPNE; assert coefficient table header in for006.dat

## 0.1.3 - DATCOM wrapper smoke test
- `Python/tests/test_datcom_wrapper_smoke.py`: runs `./datcom` with minimal namelist; asserts `for006.dat` contains CASEID and is >200 bytes

## 0.1.2 - DATCOM stdin wrapper script
- `Matlab/fsroot/code/DATCOM/datcom`: bash wrapper pipes `for005.dat` to `datcom.bin`, copies `datcom.out` → `for006.dat`
- `.gitignore`: stop ignoring wrapper; still ignore `datcom.bin`
- `Python/tests/test_datcom_wrapper.py`: asserts wrapper exists, references inputs/outputs, is executable

## 0.1.1 - DATCOM binary compile test
- `Python/tests/test_datcom_binary.py`: asserts `Matlab/fsroot/code/DATCOM/datcom.bin` exists and is executable (build locally from `../datcom/datcom.f` via gfortran)

## 0.1.0 - README, UPDATES, aid.paths bootstrap
- README.md and UPDATES.md per project-docs rule (idea, architecture, reading order)
- Python package skeleton: `pyproject.toml`, `src/aid/paths.py` (repo root discovery via `AID.m`)

## 0.0.1 - Project git repository
- Nested git repo at AircraftIntuitiveDesign (not the parent MDT repo)
- `.gitignore`: executables, objects, PDFs, Results, images, solver runtime output; keep source and aircraft inputs
