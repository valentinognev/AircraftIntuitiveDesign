# Updates

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
