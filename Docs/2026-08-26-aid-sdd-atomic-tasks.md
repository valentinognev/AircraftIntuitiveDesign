# AID Atomic SDD Tasks

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Linux MATLAB AID gold results then Python PySide6 twin matching DATCOM/Tornado/AVL coefficients.

**Architecture:** Shared DATCOM/AVL binaries; Tornado ported; MATLAB AVL I/O ported; `aid` engine + `aid_gui`; JSONC models with // comments on every key.

**Tech Stack:** MATLAB R2025b at /home/valentin/ProgramFiles/MB2025b/bin/matlab, gfortran, AVL 3.52, Python 3.11+, PySide6, numpy, scipy, pytest.

**Spec:** /home/valentin/Projects/MDT/USAF_DATCOM/AircraftIntuitiveDesign/Docs/2026-08-26-aid-linux-python-port-spec.md

## Global Constraints

- OS: Linux. MATLAB: `/home/valentin/ProgramFiles/MB2025b/bin/matlab` (R2025b / 25.2, glnxa64). Aerospace Toolbox required; `exist('datcomimport')==2`.
- DATCOM Fortran source: `/home/valentin/Projects/MDT/USAF_DATCOM/datcom/datcom.f`. PDAS binary reads input **filename from stdin**, writes **`datcom.out`** (not `for006.dat`). Wrapper feeds `for005.dat` on stdin and copies `datcom.out` → `for006.dat`.
- AVL source: `Matlab/fsroot/code/AVL/AVL3.52rel09032025/`. Build plotlib → eispack → `bin/Makefile.gfortranDP`. Install executable to `Matlab/fsroot/code/AVL/run/avl`. Do **not** invent a new `.avl` writer; port `Tornado_IO.m`, `AVL_IO.m`, `parseST.m`, `parseSB.m`, `parseRunCaseHeader.m`, `findValue.m`.
- Python aircraft: `Python/models/<Aircraft Name>.jsonc` with `//` line comments on **every key**. MATLAB Phase 1 keeps `.mat`.
- Package split: `Python/src/aid` (no widgets), `Python/src/aid_gui` (PySide6). Comparison harness calls `aid` only.
- Results layout: `Results/matlab/<aircraft>/`, `Results/python/<aircraft>/`, `Results/compare/<aircraft>.json`.
- Compare Python vs MATLAB with spec §13 tolerances. Shared Fortran binaries must match at parser precision.
- Attempt all 23 models; record `status: skipped|failed|ok` per solver; never fabricate results.
- Primary pass aircraft: **Cessna 172**, **Navion**, **DA20-C1**, **Learjet 23**.
- Non-goals: ASCDM, FlightGear/Simulink sim, neural-network import, CAD/CFD export, changing DATCOM/AVL theory.
- Implement with **subagent-driven development**. Each task: Composer 2.5 implementer, then Grok reviewer.
- Implementer model: **Composer 2.5** (`composer-2.5`). Never Composer 2.5 Fast. Never Kimi 3.
- Reviewer model: **Grok** (`cursor-grok-4.6-high`).
- Work directory: `/home/valentin/Projects/MDT/USAF_DATCOM/AircraftIntuitiveDesign`
- Parent git repo is `/home/valentin/Projects/MDT` (this project is currently untracked). If a nested git repo exists at `AircraftIntuitiveDesign`, commit **there** only. NEVER `git add`/`commit`/`push` in `/home/valentin/Projects/MDT`.
- Do not git push. Nested-repo commits are allowed for SDD review diffs.
- Do not commit unless the user explicitly asks. Update root `README.md` / `UPDATES.md` after meaningful slices.
- Every task has its own unit test (pytest preferred; MATLAB `-batch` one-liner or bash assert allowed only for Fortran/MATLAB binary tasks).
- TDD: failing test first, then minimal implementation.
- Batch mesh: Tornado 10/5 mode 0; AVL 10/10; no `questdlg` / `inputdlg` blocking in batch (`owg` not Yes, NP estimate No, `check_io=false`).
- Cessna 172 gold (decoded `Cessna 172.mat`): `unit='ft'`, `WG.CHRDR=2`, `WG.SSPN=6`, `WG.S=24`, `AERO.ALSCHD=[-4,0,4,8,12]`, `AERO.MACH=0.03`, `AERO.XCG=2.94`, NACA 2412.

---

### Task 1: README and UPDATES bootstrap

**Files:**
- Create: `README.md`
- Create: `UPDATES.md`
- Test: `Python/tests/test_project_docs.py`

**Interfaces:**
- Consumes: spec §1–4
- Produces: project docs readable by future agents

- [ ] **Step 1: Write the failing test**

```python
# Python/tests/test_project_docs.py
from pathlib import Path
from aid.paths import repo_root

def test_readme_and_updates_exist():
    root = repo_root()
    readme = (root / "README.md").read_text()
    updates = (root / "UPDATES.md").read_text()
    assert "Aircraft Intuitive Design" in readme
    assert "UPDATES.md" in readme
    assert updates.startswith("# Updates")
    assert "0.1.0" in updates
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /home/valentin/Projects/MDT/USAF_DATCOM/AircraftIntuitiveDesign/Python && python -m pytest tests/test_project_docs.py -v
```

Expected FAIL: `ModuleNotFoundError: aid` or `FileNotFoundError: README.md`.

- [ ] **Step 3: Write minimal implementation**

Create `README.md` and `UPDATES.md` per project-docs rule (Idea, Architecture, Reading order; Updates `0.1.0 - Project bootstrap`). Add minimal `Python/pyproject.toml` + `Python/src/aid/paths.py` with `repo_root()` only so the test can import.

- [ ] **Step 4: Run test to verify it passes**

```bash
cd Python && pip install -e ".[dev]" && python -m pytest tests/test_project_docs.py -v
```

Expected PASS.

- [ ] **Step 5: Commit** (nested repo only; suggested message)

`docs: add README, UPDATES, and project-docs smoke test`

---

### Task 2: Compile DATCOM Fortran binary

**Files:**
- Create: `Matlab/fsroot/code/DATCOM/datcom.bin`
- Test: `Python/tests/test_datcom_binary.py`

**Interfaces:**
- Consumes: `/home/valentin/Projects/MDT/USAF_DATCOM/datcom/datcom.f`
- Produces: executable `Matlab/fsroot/code/DATCOM/datcom.bin`

- [ ] **Step 1: Write the failing test**

```python
# Python/tests/test_datcom_binary.py
from aid.paths import matlab_code

def test_datcom_bin_executable():
    p = matlab_code() / "DATCOM" / "datcom.bin"
    assert p.is_file() and p.stat().st_mode & 0o111
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd Python && python -m pytest tests/test_datcom_binary.py -v
```

Expected FAIL: `AssertionError` — `datcom.bin` missing.

- [ ] **Step 3: Write minimal implementation**

```bash
command -v gfortran || sudo apt-get update && sudo apt-get install -y gfortran
cd /home/valentin/Projects/MDT/USAF_DATCOM/datcom
gfortran -O2 -std=legacy -fallow-argument-mismatch -fbackslash \
  datcom.f -o /home/valentin/Projects/MDT/USAF_DATCOM/AircraftIntuitiveDesign/Matlab/fsroot/code/DATCOM/datcom.bin
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd Python && python -m pytest tests/test_datcom_binary.py -v
```

Expected PASS.

- [ ] **Step 5: Commit**

`build: compile PDAS datcom.f to datcom.bin`

---

### Task 3: DATCOM stdin wrapper script

**Files:**
- Create: `Matlab/fsroot/code/DATCOM/datcom`
- Test: `Python/tests/test_datcom_wrapper.py`

**Interfaces:**
- Consumes: `datcom.bin`, `for005.dat` in cwd
- Produces: shell script `Matlab/fsroot/code/DATCOM/datcom` → writes `for006.dat` and `datcom.out`

- [ ] **Step 1: Write the failing test**

```python
# Python/tests/test_datcom_wrapper.py
from aid.paths import datcom_wrapper

def test_datcom_wrapper_is_executable_script():
    p = datcom_wrapper()
    assert p.is_file()
    text = p.read_text()
    assert "for005.dat" in text
    assert "datcom.out" in text
    assert p.stat().st_mode & 0o111
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd Python && python -m pytest tests/test_datcom_wrapper.py -v
```

Expected FAIL: wrapper file missing.

- [ ] **Step 3: Write minimal implementation**

```bash
cat > /home/valentin/Projects/MDT/USAF_DATCOM/AircraftIntuitiveDesign/Matlab/fsroot/code/DATCOM/datcom <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
BIN="$DIR/datcom.bin"
if [[ ! -f for005.dat ]]; then
  echo "DATCOM wrapper: for005.dat not found in $(pwd)" >&2
  exit 2
fi
printf 'for005.dat\n' | "$BIN"
if [[ -f datcom.out ]]; then
  cp -f datcom.out for006.dat
else
  echo "DATCOM wrapper: datcom.out was not produced" >&2
  exit 3
fi
EOF
chmod +x /home/valentin/Projects/MDT/USAF_DATCOM/AircraftIntuitiveDesign/Matlab/fsroot/code/DATCOM/datcom
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd Python && python -m pytest tests/test_datcom_wrapper.py -v
```

Expected PASS.

- [ ] **Step 5: Commit**

`build: add DATCOM stdin wrapper copying datcom.out to for006.dat`

---

### Task 4: DATCOM wrapper smoke run

**Files:**
- Create: `Matlab/fsroot/code/DATCOM/for005.dat` (minimal smoke case)
- Test: `Python/tests/test_datcom_wrapper_smoke.py`

**Interfaces:**
- Consumes: Task 3 wrapper + minimal namelist
- Produces: non-empty `for006.dat` after `./datcom`

- [ ] **Step 1: Write the failing test**

```python
# Python/tests/test_datcom_wrapper_smoke.py
import subprocess
from pathlib import Path
from aid.paths import matlab_code

SMOKE = """CASEID WRAPPER SMOKE
 $FLTCON NALPHA=3.0,ALSCHD=-2.0,0.0,2.0,
  NALT=1.0,ALT=0.0,
  NMACH=1.0,MACH=0.200,
  WT=1000.00,LOOP=2.0$
 $OPTINS SREF=100.00,CBARR=5.00,BLREF=20.00$
 $SYNTHS XCG=5.00,ZCG=0.00,XW=2.00,ZW=0.00,ALIW=0.00,
  XH=15.00,ZH=1.00,ALIH=0.00,XV=15.00,YV=0.00,ZV=0.00,VERTUP=.TRUE.$
 $BODY NX=3.0,ITYPE=1.0,
  X=0.00,5.00,20.00,
  ZU=0.50,1.00,0.20,
  ZL=-0.50,-1.00,-0.20,
  R=0.50,1.00,0.20,
  S=0.79,3.14,0.13$
NACA-W-4-2412
 $WGPLNF CHRDR=5.00,CHRDBP=5.00,CHRDTP=5.00,SSPN=10.00,
  SSPNOP=0.00,SAVSI=0.00,SAVSO=0.00,CHSTAT=0.25,
  DHDADI=0.00,DHDADO=0.00,TWISTA=0.00,TYPE=1.0$
PLOT
NEXT CASE
"""

def test_datcom_wrapper_produces_for006():
    d = matlab_code() / "DATCOM"
    (d / "for005.dat").write_text(SMOKE)
    r = subprocess.run(["./datcom"], cwd=d, capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stderr
    out = (d / "for006.dat").read_text()
    assert "CASEID" in out
    assert len(out) > 200
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd Python && python -m pytest tests/test_datcom_wrapper_smoke.py -v
```

Expected FAIL: `returncode != 0` or empty `for006.dat`.

- [ ] **Step 3: Write minimal implementation**

Run wrapper; if DATCOM rejects namelist, adjust smoke `for005.dat` until `datcom.out` contains coefficient tables. No code change beyond the input file.

- [ ] **Step 4: Run test to verify it passes**

```bash
cd Python && python -m pytest tests/test_datcom_wrapper_smoke.py -v
```

Expected PASS.

- [ ] **Step 5: Commit**

`test: DATCOM wrapper smoke for005 produces for006.dat`

---

### Task 5: Decode model %20 filenames

**Files:**
- Modify: `Matlab/fsroot/code/Models/*.mat` (rename only)
- Test: `Python/tests/test_model_filenames.py`

**Interfaces:**
- Consumes: URL-encoded names (`Cessna%20172.mat`)
- Produces: decoded names (`Cessna 172.mat`), 23 files total

- [ ] **Step 1: Write the failing test**

```python
# Python/tests/test_model_filenames.py
from pathlib import Path
from aid.paths import matlab_code

def test_models_decoded_and_count_23():
    d = matlab_code() / "Models"
    mats = list(d.glob("*.mat"))
    assert len(mats) == 23
    assert (d / "Cessna 172.mat").is_file()
    assert not any("%20" in p.name for p in mats)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd Python && python -m pytest tests/test_model_filenames.py -v
```

Expected FAIL: `Cessna 172.mat` missing or `%20` still present.

- [ ] **Step 3: Write minimal implementation**

```python
from pathlib import Path
from urllib.parse import unquote
p = Path("/home/valentin/Projects/MDT/USAF_DATCOM/AircraftIntuitiveDesign/Matlab/fsroot/code/Models")
for f in list(p.glob("*.mat")):
    new = p / unquote(f.name)
    if new != f:
        f.rename(new)
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd Python && python -m pytest tests/test_model_filenames.py -v
```

Expected PASS.

- [ ] **Step 5: Commit**

`chore: decode URL-encoded AID model .mat filenames`

---

### Task 6: Verify Cessna 172.mat loads in MATLAB

**Files:**
- Test: `Python/tests/test_cessna_mat_gold.py`

**Interfaces:**
- Consumes: `Matlab/fsroot/code/Models/Cessna 172.mat`
- Produces: pytest asserting gold scalars

- [ ] **Step 1: Write the failing test**

```python
# Python/tests/test_cessna_mat_gold.py
import subprocess, json
from aid.paths import matlab_code

MATLAB = "/home/valentin/ProgramFiles/MB2025b/bin/matlab"
MAT = matlab_code() / "Models" / "Cessna 172.mat"

def test_cessna_matlab_load_gold():
    cmd = (
        f"S=load('{MAT}'); "
        "fprintf('%s\\n',jsonencode(struct("
        "'CHRDR',S.WG.CHRDR,'SSPN',S.WG.SSPN,'S',S.WG.S,"
        "'unit',S.unit,'ALSCHD',S.AERO.ALSCHD,'MACH',S.AERO.MACH(1),'XCG',S.AERO.XCG)));"
    )
    r = subprocess.run([MATLAB, "-batch", cmd], capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stderr
    line = [ln for ln in r.stdout.splitlines() if ln.startswith("{")][-1]
    d = json.loads(line)
    assert d["CHRDR"] == 2
    assert d["SSPN"] == 6
    assert d["S"] == 24
    assert d["unit"] == "ft"
    assert d["ALSCHD"] == [-4, 0, 4, 8, 12]
    assert abs(d["MACH"] - 0.03) < 1e-9
    assert abs(d["XCG"] - 2.94) < 1e-9
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd Python && python -m pytest tests/test_cessna_mat_gold.py -v
```

Expected FAIL: file not found if Task 5 incomplete, or wrong values.

- [ ] **Step 3: Write minimal implementation**

Ensure Task 5 rename done; no code changes if `.mat` already correct.

- [ ] **Step 4: Run test to verify it passes**

```bash
cd Python && python -m pytest tests/test_cessna_mat_gold.py -v
```

Expected PASS.

- [ ] **Step 5: Commit**

`test: MATLAB gold scalar check for Cessna 172.mat`

---

### Task 7: AVL Makefile Linux X11 path

**Files:**
- Modify: `Matlab/fsroot/code/AVL/AVL3.52rel09032025/bin/Makefile.gfortranDP`
- Modify: `Matlab/fsroot/code/AVL/AVL3.52rel09032025/plotlib/config.make` (if `/opt/X11` present)
- Test: `Python/tests/test_avl_makefile_linux.py`

**Interfaces:**
- Consumes: macOS `PLTLIB = -L/opt/X11/lib -lX11`
- Produces: Linux `PLTLIB` using `/usr/lib/x86_64-linux-gnu` or `pkg-config --libs x11`

- [ ] **Step 1: Write the failing test**

```python
# Python/tests/test_avl_makefile_linux.py
from aid.paths import matlab_code

def test_avl_makefile_uses_linux_x11():
    mf = (matlab_code() / "AVL/AVL3.52rel09032025/bin/Makefile.gfortranDP").read_text()
    assert "/opt/X11" not in mf
    assert "-lX11" in mf
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd Python && python -m pytest tests/test_avl_makefile_linux.py -v
```

Expected FAIL: `/opt/X11` still in makefile.

- [ ] **Step 3: Write minimal implementation**

Replace `PLTLIB = -L/opt/X11/lib -lX11` with `PLTLIB = -L/usr/lib/x86_64-linux-gnu -lX11` (or `pkg-config --libs x11` output). Mirror fix in plotlib config if needed.

- [ ] **Step 4: Run test to verify it passes**

```bash
cd Python && python -m pytest tests/test_avl_makefile_linux.py -v
```

Expected PASS.

- [ ] **Step 5: Commit**

`build: point AVL Makefile.gfortranDP at Linux libX11`

---

### Task 8: Build AVL plotlib

**Files:**
- Create: `Matlab/fsroot/code/AVL/AVL3.52rel09032025/plotlib/libPlt_gDP.a` (or `libPlt.a`)
- Test: `Python/tests/test_avl_plotlib.py`

**Interfaces:**
- Consumes: plotlib sources
- Produces: static plot library archive

- [ ] **Step 1: Write the failing test**

```python
# Python/tests/test_avl_plotlib.py
from aid.paths import matlab_code

def test_avl_plotlib_built():
    d = matlab_code() / "AVL/AVL3.52rel09032025/plotlib"
    assert (d / "libPlt_gDP.a").is_file() or (d / "libPlt.a").is_file()
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd Python && python -m pytest tests/test_avl_plotlib.py -v
```

Expected FAIL: archive missing.

- [ ] **Step 3: Write minimal implementation**

```bash
cd Matlab/fsroot/code/AVL/AVL3.52rel09032025/plotlib
make clean || true
make gfortranDP
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd Python && python -m pytest tests/test_avl_plotlib.py -v
```

Expected PASS.

- [ ] **Step 5: Commit**

`build: compile AVL plotlib for gfortranDP`

---

### Task 9: Build AVL eispack

**Files:**
- Create: `Matlab/fsroot/code/AVL/AVL3.52rel09032025/eispack/libeispack.a` (or equivalent)
- Test: `Python/tests/test_avl_eispack.py`

**Interfaces:**
- Consumes: eispack Fortran sources
- Produces: `libeispack.a`

- [ ] **Step 1: Write the failing test**

```python
# Python/tests/test_avl_eispack.py
from aid.paths import matlab_code

def test_avl_eispack_built():
    d = matlab_code() / "AVL/AVL3.52rel09032025/eispack"
    libs = list(d.glob("*.a"))
    assert libs, "no eispack archive"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd Python && python -m pytest tests/test_avl_eispack.py -v
```

Expected FAIL: no `.a` file.

- [ ] **Step 3: Write minimal implementation**

```bash
cd Matlab/fsroot/code/AVL/AVL3.52rel09032025/eispack
make -f Makefile.gfortran
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd Python && python -m pytest tests/test_avl_eispack.py -v
```

Expected PASS.

- [ ] **Step 5: Commit**

`build: compile AVL eispack`

---

### Task 10: Build and install AVL executable

**Files:**
- Create: `Matlab/fsroot/code/AVL/AVL3.52rel09032025/bin/avl`
- Create: `Matlab/fsroot/code/AVL/run/avl`
- Test: `Python/tests/test_avl_binary.py`

**Interfaces:**
- Consumes: Tasks 7–9 build artifacts
- Produces: `Matlab/fsroot/code/AVL/run/avl` executable

- [ ] **Step 1: Write the failing test**

```python
# Python/tests/test_avl_binary.py
from aid.paths import avl_bin

def test_avl_installed():
    p = avl_bin()
    assert p.is_file() and p.stat().st_mode & 0o111
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd Python && python -m pytest tests/test_avl_binary.py -v
```

Expected FAIL: `avl` missing.

- [ ] **Step 3: Write minimal implementation**

```bash
cd Matlab/fsroot/code/AVL/AVL3.52rel09032025/bin
make -f Makefile.gfortranDP avl
cp -f avl ../../run/avl && chmod +x ../../run/avl
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd Python && python -m pytest tests/test_avl_binary.py -v
```

Expected PASS.

- [ ] **Step 5: Commit**

`build: install AVL 3.52 binary to AVL/run/avl`

---

### Task 11: AVL batch quit smoke

**Files:**
- Test: `Python/tests/test_avl_smoke.py`

**Interfaces:**
- Consumes: `avl_bin()`, stdin `PLOP\ng\n\nQuit\n`
- Produces: process exits without hang

- [ ] **Step 1: Write the failing test**

```python
# Python/tests/test_avl_smoke.py
import subprocess
from aid.paths import avl_bin

def test_avl_quits_with_plop_g():
    r = subprocess.run(
        [str(avl_bin())],
        input="PLOP\ng\n\nQuit\n",
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert r.returncode == 0
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd Python && python -m pytest tests/test_avl_smoke.py -v
```

Expected FAIL: timeout or nonzero exit if binary missing/broken.

- [ ] **Step 3: Write minimal implementation**

Ensure Task 10 binary works; fix X11/PLOP if needed per `avl_doc`.

- [ ] **Step 4: Run test to verify it passes**

```bash
cd Python && python -m pytest tests/test_avl_smoke.py -v
```

Expected PASS.

- [ ] **Step 5: Commit**

`test: AVL PLOP/g batch quit smoke`

---

### Task 12: Patch AID.m DATCOM Linux binary

**Files:**
- Modify: `Matlab/fsroot/code/AID.m`
- Test: `Python/tests/test_aid_datcom_patch.py`

**Interfaces:**
- Consumes: `./datcom` wrapper (Task 3)
- Produces: non-Windows branch calls `system('./datcom')` not `./datcom.osx`

- [ ] **Step 1: Write the failing test**

```python
# Python/tests/test_aid_datcom_patch.py
from aid.paths import matlab_code

def test_aid_uses_linux_datcom_wrapper():
    text = (matlab_code() / "AID.m").read_text()
    assert "system('./datcom')" in text or 'system("./datcom")' in text
    assert "./datcom.osx" not in text.split("else")[ -1]  # crude: linux branch
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd Python && python -m pytest tests/test_aid_datcom_patch.py -v
```

Expected FAIL: still `./datcom.osx`.

- [ ] **Step 3: Write minimal implementation**

In `AID.m` non-Windows DATCOM branch (~1594), replace `system('./datcom.osx');` with `system('./datcom');`. Keep `datcomimport('for006.dat',true)`.

- [ ] **Step 4: Run test to verify it passes**

```bash
cd Python && python -m pytest tests/test_aid_datcom_patch.py -v
```

Expected PASS.

- [ ] **Step 5: Commit**

`fix: call Linux DATCOM wrapper from AID.m`

---

### Task 13: Patch AVL_IO.m Linux binary

**Files:**
- Modify: `Matlab/fsroot/code/AVL_IO.m`
- Test: `Python/tests/test_avl_io_patch.py`

**Interfaces:**
- Consumes: `AVL/run/avl`
- Produces: else-branch `system(['./avl',' < ',CaseID,'.run']);`

- [ ] **Step 1: Write the failing test**

```python
# Python/tests/test_avl_io_patch.py
from aid.paths import matlab_code

def test_avl_io_calls_avl352():
    t = (matlab_code() / "AVL_IO.m").read_text()
    assert "./avl'" in t or "'./avl'" in t
    assert "avl3.35" not in t
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd Python && python -m pytest tests/test_avl_io_patch.py -v
```

Expected FAIL: still `avl3.35`.

- [ ] **Step 3: Write minimal implementation**

Replace `system(['./avl3.35',' < ',CaseID,'.run']);` and remove macOS `DYLD_LIBRARY_PATH` setenv in else-branch.

- [ ] **Step 4: Run test to verify it passes**

```bash
cd Python && python -m pytest tests/test_avl_io_patch.py -v
```

Expected PASS.

- [ ] **Step 5: Commit**

`fix: AVL_IO invokes ./avl on Linux`

---

### Task 14: DATCOM_IO batch dialog defaults

**Files:**
- Modify: `Matlab/fsroot/code/DATCOM_IO.m`
- Test: `Python/tests/test_datcom_io_batch.py`

**Interfaces:**
- Consumes: `choice=='batch'`
- Produces: no `questdlg` when `choice` is `'batch'` (wing-only and CG prompts skipped)

- [ ] **Step 1: Write the failing test**

```python
# Python/tests/test_datcom_io_batch.py
from aid.paths import matlab_code

def test_datcom_io_batch_skips_questdlg():
    t = (matlab_code() / "DATCOM_IO.m").read_text()
    assert "strcmp(choice,'batch')" in t or "strcmp(choice, 'batch')" in t
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd Python && python -m pytest tests/test_datcom_io_batch.py -v
```

Expected FAIL: no explicit batch guard.

- [ ] **Step 3: Write minimal implementation**

Audit `Write_DATCOM` `questdlg` sites; ensure `choice=='batch'` never opens dialogs (default `owg` to non-Yes string; skip CG dialog). Add explicit `strcmp(choice,'batch')` early-outs where needed.

- [ ] **Step 4: Run test to verify it passes**

```bash
cd Python && python -m pytest tests/test_datcom_io_batch.py -v
```

Expected PASS.

- [ ] **Step 5: Commit**

`fix: DATCOM_IO skips questdlg for batch choice`

---

### Task 15: AID.m Tornado NP batch default

**Files:**
- Modify: `Matlab/fsroot/code/AID.m`
- Test: `Python/tests/test_aid_tornado_batch_np.py`

**Interfaces:**
- Consumes: `choice=='batch'`
- Produces: NP estimate defaults to `'No'` without `questdlg`

- [ ] **Step 1: Write the failing test**

```python
# Python/tests/test_aid_tornado_batch_np.py
from aid.paths import matlab_code

def test_aid_batch_np_default_no():
    t = (matlab_code() / "AID.m").read_text()
    assert "strcmp(choice,'batch')" in t
    assert "Estimate Neutral Point" in t
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd Python && python -m pytest tests/test_aid_tornado_batch_np.py -v
```

Expected FAIL: no batch guard around NP `questdlg`.

- [ ] **Step 3: Write minimal implementation**

```matlab
if ~strcmp(choice,'batch')
    np = questdlg('Estimate Neutral Point?','Iterate to Find NP');
else
    np = 'No';
end
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd Python && python -m pytest tests/test_aid_tornado_batch_np.py -v
```

Expected PASS.

- [ ] **Step 5: Commit**

`fix: skip Tornado NP questdlg in batch mode`

---

### Task 16: run_aid_batch JSON helpers

**Files:**
- Create: `Matlab/fsroot/code/run_aid_batch.m` (helpers only: `write_json`, `strip_datcom`, `strip_tornado`, `onoff`)
- Test: `Python/tests/test_run_aid_batch_helpers.py`

**Interfaces:**
- Consumes: MATLAB R2025b `jsonencode`
- Produces: local functions callable from future batch runner

- [ ] **Step 1: Write the failing test**

```python
# Python/tests/test_run_aid_batch_helpers.py
import subprocess
from aid.paths import matlab_code

MATLAB = "/home/valentin/ProgramFiles/MB2025b/bin/matlab"

def test_run_aid_batch_file_exists():
    p = matlab_code() / "run_aid_batch.m"
    assert p.is_file()
    t = p.read_text()
    assert "function write_json" in t
    assert "function strip_datcom" in t
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd Python && python -m pytest tests/test_run_aid_batch_helpers.py -v
```

Expected FAIL: file or helper functions missing.

- [ ] **Step 3: Write minimal implementation**

Create `run_aid_batch.m` containing only helper subfunctions from old plan Task 5 (`write_json`, `strip_datcom`, `strip_tornado`, `onoff`). Main function body can be `error('not implemented')` for now.

- [ ] **Step 4: Run test to verify it passes**

```bash
cd Python && python -m pytest tests/test_run_aid_batch_helpers.py -v
```

Expected PASS.

- [ ] **Step 5: Commit**

`feat: run_aid_batch JSON strip helpers`

---

### Task 17: MATLAB gold Cessna DATCOM only

**Files:**
- Modify: `Matlab/fsroot/code/run_aid_batch.m` (add `run_datcom_gold`)
- Create: `Results/matlab/Cessna 172/datcom.json` (runtime)
- Test: `Python/tests/test_matlab_gold_cessna_datcom.py`

**Interfaces:**
- Consumes: `Cessna 172.mat`, `DATCOM_IO`, wrapper, `datcomimport`
- Produces: `Results/matlab/Cessna 172/{datcom.json,for005.dat,datcom.out,status.json}` with `datcom: ok`

- [ ] **Step 1: Write the failing test**

```python
# Python/tests/test_matlab_gold_cessna_datcom.py
import json
from pathlib import Path
from aid.paths import results_dir

def test_cessna_matlab_datcom_gold():
    d = results_dir() / "matlab" / "Cessna 172"
    st = json.loads((d / "status.json").read_text())
    assert st["datcom"] == "ok"
    coef = json.loads((d / "datcom.json").read_text())
    assert "cl" in coef and "alpha" in coef
    assert len(coef["alpha"]) >= 3
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd Python && python -m pytest tests/test_matlab_gold_cessna_datcom.py -v
```

Expected FAIL: `status.json` missing or `datcom != ok`.

- [ ] **Step 3: Write minimal implementation**

Extend `run_aid_batch.m` with DATCOM-only path for one model (`run_datcom_gold(model_name)`): load `.mat`, hidden figure stubs for `cmp`/`opt`, `DATCOM_IO(...,'batch',...)`, `./datcom`, `datcomimport`, write JSON. Run:

```bash
/home/valentin/ProgramFiles/MB2025b/bin/matlab -batch "cd('/home/valentin/Projects/MDT/USAF_DATCOM/AircraftIntuitiveDesign/Matlab/fsroot/code'); run_aid_batch('Cessna 172','datcom')"
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd Python && python -m pytest tests/test_matlab_gold_cessna_datcom.py -v
```

Expected PASS.

- [ ] **Step 5: Commit**

`feat: MATLAB gold DATCOM dump for Cessna 172`

---

### Task 18: MATLAB gold Cessna Tornado only

**Files:**
- Modify: `Matlab/fsroot/code/run_aid_batch.m`
- Create: `Results/matlab/Cessna 172/tornado.json`
- Test: `Python/tests/test_matlab_gold_cessna_tornado.py`

**Interfaces:**
- Consumes: mesh `{'10','5'}`, `Tornado_IO`, `fLattice_setup2(geo,state,0)`, `solver`, `coeff_create3`
- Produces: `tornado.json` with `CL`, `CD`, `Cm`

- [ ] **Step 1: Write the failing test**

```python
# Python/tests/test_matlab_gold_cessna_tornado.py
import json
from aid.paths import results_dir

def test_cessna_matlab_tornado_gold():
    d = results_dir() / "matlab" / "Cessna 172"
    st = json.loads((d / "status.json").read_text())
    assert st["tornado"] == "ok"
    t = json.loads((d / "tornado.json").read_text())
    assert "CL" in t and "CD" in t and "Cm" in t
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd Python && python -m pytest tests/test_matlab_gold_cessna_tornado.py -v
```

Expected FAIL: `tornado` not `ok`.

- [ ] **Step 3: Write minimal implementation**

Add Tornado-only branch to `run_aid_batch.m`. Set `set(0,'DefaultFigureVisible','off')` at top. Mesh `{'10','5'}`. Patch `solver.m` minimally only if waitbar breaks headless (treat invalid waitbar as continue). Run MATLAB batch for Cessna Tornado.

- [ ] **Step 4: Run test to verify it passes**

```bash
cd Python && python -m pytest tests/test_matlab_gold_cessna_tornado.py -v
```

Expected PASS.

- [ ] **Step 5: Commit**

`feat: MATLAB gold Tornado dump for Cessna 172`

---

### Task 19: MATLAB gold Cessna AVL only

**Files:**
- Modify: `Matlab/fsroot/code/run_aid_batch.m`
- Create: `Results/matlab/Cessna 172/{avl.json,geometry.st,geometry.avl}`
- Test: `Python/tests/test_matlab_gold_cessna_avl.py`

**Interfaces:**
- Consumes: mesh `{'10','10'}`, `AVL_IO(...,false)`, `parseST`
- Produces: `avl.json` with `CLa`, `Cma`

- [ ] **Step 1: Write the failing test**

```python
# Python/tests/test_matlab_gold_cessna_avl.py
import json
from aid.paths import results_dir

def test_cessna_matlab_avl_gold():
    d = results_dir() / "matlab" / "Cessna 172"
    st = json.loads((d / "status.json").read_text())
    assert st["avl"] == "ok"
    a = json.loads((d / "avl.json").read_text())
    assert "CLa" in a
    assert (d / "geometry.st").is_file()
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd Python && python -m pytest tests/test_matlab_gold_cessna_avl.py -v
```

Expected FAIL: `avl` not `ok`.

- [ ] **Step 3: Write minimal implementation**

Add AVL-only branch: `AVL_IO` with `check_io=false`, copy `geometry.st`/`.avl`, `parseST` → JSON.

- [ ] **Step 4: Run test to verify it passes**

```bash
cd Python && python -m pytest tests/test_matlab_gold_cessna_avl.py -v
```

Expected PASS.

- [ ] **Step 5: Commit**

`feat: MATLAB gold AVL dump for Cessna 172`

---

<!-- TASKS_BATCH_4 -->
