# Updates

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
