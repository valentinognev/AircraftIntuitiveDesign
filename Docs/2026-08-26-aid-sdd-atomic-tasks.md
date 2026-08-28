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

ROOT = Path("/home/valentin/Projects/MDT/USAF_DATCOM/AircraftIntuitiveDesign")

def test_readme_and_updates_exist():
    readme = (ROOT / "README.md").read_text()
    updates = (ROOT / "UPDATES.md").read_text()
    assert "Aircraft Intuitive Design" in readme
    assert "UPDATES.md" in readme
    assert updates.startswith("# Updates")
    assert "0.1.0" in updates
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python3 -m pytest /home/valentin/Projects/MDT/USAF_DATCOM/AircraftIntuitiveDesign/Python/tests/test_project_docs.py -v
```

Expected FAIL: `FileNotFoundError: README.md`.

- [ ] **Step 3: Write minimal implementation**

Create `README.md` and `UPDATES.md` per project-docs rule. Also create minimal `Python/pyproject.toml`, `Python/src/aid/__init__.py`, and `Python/src/aid/paths.py`:

```python
from pathlib import Path

def repo_root() -> Path:
    p = Path(__file__).resolve()
    for cand in p.parents:
        if (cand / "Matlab" / "fsroot" / "code" / "AID.m").is_file():
            return cand
    raise FileNotFoundError("AircraftIntuitiveDesign root not found")

def matlab_code() -> Path:
    return repo_root() / "Matlab" / "fsroot" / "code"

def datcom_wrapper() -> Path:
    return matlab_code() / "DATCOM" / "datcom"

def avl_bin() -> Path:
    return matlab_code() / "AVL" / "run" / "avl"

def results_dir() -> Path:
    return repo_root() / "Results"
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd Python && pip install -e ".[dev]" && python -m pytest tests/test_project_docs.py -v
```

Expected PASS.

- [ ] **Step 5: Commit** (nested repo only; suggested message)

`docs: bootstrap README, UPDATES, aid.paths skeleton`

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

### Task 20: MATLAB gold primary aircraft (Navion, DA20, Learjet)

**Files:**
- Modify: `Matlab/fsroot/code/run_aid_batch.m` (full three-solver run)
- Test: `Python/tests/test_matlab_gold_primary.py`

**Interfaces:**
- Consumes: Tasks 17–19 combined runner
- Produces: `Results/matlab/{Navion,DA20-C1,Learjet 23}/status.json` all three `ok`

- [ ] **Step 1: Write the failing test**

```python
# Python/tests/test_matlab_gold_primary.py
import json
import pytest
from aid.paths import results_dir

PRIMARY = ["Navion", "DA20-C1", "Learjet 23"]

@pytest.mark.parametrize("name", PRIMARY)
def test_matlab_primary_three_ok(name):
    st = json.loads((results_dir() / "matlab" / name / "status.json").read_text())
    assert st["datcom"] == "ok"
    assert st["tornado"] == "ok"
    assert st["avl"] == "ok"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd Python && python -m pytest tests/test_matlab_gold_primary.py -v
```

Expected FAIL: missing status or solver not `ok`.

- [ ] **Step 3: Write minimal implementation**

Unify `run_aid_batch(name)` to run DATCOM+Tornado+AVL sequentially. MATLAB-batch each primary aircraft.

- [ ] **Step 4: Run test to verify it passes**

```bash
cd Python && python -m pytest tests/test_matlab_gold_primary.py -v
```

Expected PASS.

- [ ] **Step 5: Commit**

`feat: MATLAB gold dumps for primary comparison aircraft`

---

### Task 21: Batch all 23 models

**Files:**
- Create: `Matlab/fsroot/code/run_aid_batch_all.m`
- Create: `Results/matlab/_summary.json`
- Test: `Python/tests/test_matlab_batch_all.py`

**Interfaces:**
- Consumes: `run_aid_batch`
- Produces: 23 `status.json` files + summary

- [ ] **Step 1: Write the failing test**

```python
# Python/tests/test_matlab_batch_all.py
import json
from pathlib import Path
from aid.paths import results_dir, matlab_code

def test_all_23_models_attempted():
    summary = results_dir() / "matlab" / "_summary.json"
    assert summary.is_file()
    rows = json.loads(summary.read_text())
    assert len(rows) == 23
    mats = list((matlab_code() / "Models").glob("*.mat"))
    assert len(mats) == 23
    for row in rows:
        assert (results_dir() / "matlab" / row["name"] / "status.json").is_file()
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd Python && python -m pytest tests/test_matlab_batch_all.py -v
```

Expected FAIL: `_summary.json` missing.

- [ ] **Step 3: Write minimal implementation**

Implement `run_aid_batch_all.m` per old plan. Run full batch (may take hours). Record failures honestly in `status.json`.

- [ ] **Step 4: Run test to verify it passes**

```bash
cd Python && python -m pytest tests/test_matlab_batch_all.py -v
```

Expected PASS (23 rows exist; primary four must be three-way `ok`).

- [ ] **Step 5: Commit**

`feat: MATLAB batch gold Results/matlab for all models`

---

### Task 22: aid.paths models_dir extension

**Files:**
- Modify: `Python/src/aid/paths.py`
- Test: `Python/tests/test_paths.py`

**Interfaces:**
- Produces: `def models_dir() -> Path: ...` → `repo_root() / "Python" / "models"`

- [ ] **Step 1: Write the failing test**

```python
# Python/tests/test_paths.py
from aid.paths import avl_bin, datcom_wrapper, matlab_code, models_dir, repo_root, results_dir

def test_paths_resolve():
    assert (matlab_code() / "AID.m").is_file()
    assert datcom_wrapper().name == "datcom"
    assert avl_bin().name == "avl"
    assert repo_root().name == "AircraftIntuitiveDesign"
    assert results_dir().name == "Results"
    assert models_dir().name == "models"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd Python && python -m pytest tests/test_paths.py -v
```

Expected FAIL: `models_dir` missing or import error.

- [ ] **Step 3: Write minimal implementation**

Add `models_dir()` to `paths.py`. Ensure `pyproject.toml` has `dev = ["pytest"]` optional deps if not already present.

- [ ] **Step 4: Run test to verify it passes**

```bash
cd Python && python -m pytest tests/test_paths.py -v
```

Expected PASS.

- [ ] **Step 5: Commit**

`feat: add models_dir to aid.paths`

---

### Task 23: field_docs catalog

**Files:**
- Create: `Python/src/aid/field_docs.py`
- Test: `Python/tests/test_field_docs.py`

**Interfaces:**
- Produces: `DOCS: dict[str, str]` keyed by dotted paths (`WG.CHRDR`, `AERO.MACH`, …)

- [ ] **Step 1: Write the failing test**

```python
# Python/tests/test_field_docs.py
from aid.field_docs import DOCS

def test_cessna_wing_keys_documented():
    assert "WG.CHRDR" in DOCS
    assert "Root Chord" in DOCS["WG.CHRDR"]
    assert "WG.SSPN" in DOCS
    assert "AERO.ALSCHD" in DOCS
    assert "AERO.XCG" in DOCS
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd Python && python -m pytest tests/test_field_docs.py -v
```

Expected FAIL: `ModuleNotFoundError` or missing keys.

- [ ] **Step 3: Write minimal implementation**

Populate `DOCS` from spec §6.1–6.4 and `Initialize_GUI.m` labels. Include derived keys present on Cessna (`WG.S`, `WG.cbar`, `WG.AR`, …).

- [ ] **Step 4: Run test to verify it passes**

```bash
cd Python && python -m pytest tests/test_field_docs.py -v
```

Expected PASS.

- [ ] **Step 5: Commit**

`feat: JSONC field documentation catalog`

---

### Task 24: jsonc.loads_jsonc stripper

**Files:**
- Create: `Python/src/aid/jsonc.py`
- Test: `Python/tests/test_jsonc_loads.py`

**Interfaces:**
- Produces: `def loads_jsonc(text: str) -> dict`

- [ ] **Step 1: Write the failing test**

```python
# Python/tests/test_jsonc_loads.py
from aid.jsonc import loads_jsonc

SAMPLE = """{
  "WG": {
    "CHRDR": 2.0, // Root Chord ft
    "SSPN": 6.0 // Semi-Span ft
  },
  "unit": "ft" // length unit
}"""

def test_loads_jsonc_strips_comments():
    d = loads_jsonc(SAMPLE)
    assert d["WG"]["CHRDR"] == 2.0
    assert d["unit"] == "ft"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd Python && python -m pytest tests/test_jsonc_loads.py -v
```

Expected FAIL: `loads_jsonc` not implemented.

- [ ] **Step 3: Write minimal implementation**

```python
# Python/src/aid/jsonc.py
import json
import re

def loads_jsonc(text: str) -> dict:
  lines = []
  for line in text.splitlines():
    if "//" in line:
      in_str = False
      out = []
      i = 0
      while i < len(line):
        c = line[i]
        if c == '"' and (i == 0 or line[i-1] != "\\"):
          in_str = not in_str
          out.append(c)
        elif not in_str and line[i:i+2] == "//":
          break
        else:
          out.append(c)
        i += 1
      lines.append("".join(out))
    else:
      lines.append(line)
  return json.loads("\n".join(lines))
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd Python && python -m pytest tests/test_jsonc_loads.py -v
```

Expected PASS.

- [ ] **Step 5: Commit**

`feat: JSONC comment stripper loads_jsonc`

---

### Task 25: aircraft.load_mat

**Files:**
- Create: `Python/src/aid/aircraft.py`
- Test: `Python/tests/test_aircraft_load_mat.py`

**Interfaces:**
- Produces: `@dataclass class Aircraft` + `def load_mat(path: Path) -> Aircraft`

- [ ] **Step 1: Write the failing test**

```python
# Python/tests/test_aircraft_load_mat.py
from pathlib import Path
from aid.aircraft import load_mat
from aid.paths import matlab_code

MAT = matlab_code() / "Models" / "Cessna 172.mat"

def test_load_mat_cessna():
    ac = load_mat(MAT)
    assert ac.unit == "ft"
    assert abs(ac.WG["CHRDR"] - 2.0) < 1e-9
    assert list(ac.AERO["ALSCHD"]) == [-4, 0, 4, 8, 12]
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd Python && python -m pytest tests/test_aircraft_load_mat.py -v
```

Expected FAIL: `load_mat` missing.

- [ ] **Step 3: Write minimal implementation**

Use `scipy.io.loadmat(..., squeeze_me=True, struct_as_record=False)`; recursive convert `mat_struct` → dict, cells → list, field `i` → `"i"`.

- [ ] **Step 4: Run test to verify it passes**

```bash
cd Python && python -m pytest tests/test_aircraft_load_mat.py -v
```

Expected PASS.

- [ ] **Step 5: Commit**

`feat: load MATLAB .mat into Aircraft dataclass`

---

### Task 26: dumps_jsonc comments on every key

**Files:**
- Modify: `Python/src/aid/aircraft.py`, `Python/src/aid/jsonc.py`
- Test: `Python/tests/test_jsonc_comments_every_key.py`

**Interfaces:**
- Produces: `def dumps_jsonc(data: dict, docs: dict) -> str`, `def load_jsonc(path: Path) -> Aircraft`, `def save_jsonc(ac, path) -> None`

- [ ] **Step 1: Write the failing test**

```python
# Python/tests/test_jsonc_comments_every_key.py
from pathlib import Path
from aid.aircraft import load_mat, save_jsonc
from aid.paths import matlab_code

def test_every_key_line_has_comment(tmp_path):
    ac = load_mat(matlab_code() / "Models" / "Cessna 172.mat")
    out = tmp_path / "c.jsonc"
    save_jsonc(ac, out)
    text = out.read_text()
    for line in text.splitlines():
        s = line.strip()
        if not s or s in "{[]}," or s.startswith("//"):
            continue
        if ":" in s:
            assert "//" in s, line
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd Python && python -m pytest tests/test_jsonc_comments_every_key.py -v
```

Expected FAIL: keys without `//`.

- [ ] **Step 3: Write minimal implementation**

`dumps_jsonc` walks nested dicts; each emitted key line ends with `, // {DOCS[path]}`. `load_jsonc` uses `loads_jsonc`; `save_jsonc` writes file.

- [ ] **Step 4: Run test to verify it passes**

```bash
cd Python && python -m pytest tests/test_jsonc_comments_every_key.py -v
```

Expected PASS.

- [ ] **Step 5: Commit**

`feat: JSONC writer with comment on every key`

---

### Task 27: mat_to_jsonc convert 23 models

**Files:**
- Create: `Python/scripts/mat_to_jsonc.py`
- Create: `Python/models/*.jsonc` (23 files)
- Test: `Python/tests/test_mat_to_jsonc_all.py`

**Interfaces:**
- Consumes: decoded `.mat` files
- Produces: `Python/models/<Aircraft Name>.jsonc`

- [ ] **Step 1: Write the failing test**

```python
# Python/tests/test_mat_to_jsonc_all.py
from aid.paths import matlab_code, models_dir

def test_23_jsonc_models_exist():
    mats = list((matlab_code() / "Models").glob("*.mat"))
    jsonc = list(models_dir().glob("*.jsonc"))
    assert len(mats) == 23
    assert len(jsonc) == 23
    assert (models_dir() / "Cessna 172.jsonc").is_file()
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd Python && python -m pytest tests/test_mat_to_jsonc_all.py -v
```

Expected FAIL: count < 23.

- [ ] **Step 3: Write minimal implementation**

```python
# Python/scripts/mat_to_jsonc.py
from pathlib import Path
from aid.aircraft import load_mat, save_jsonc
from aid.paths import matlab_code, models_dir

def main():
    models_dir().mkdir(parents=True, exist_ok=True)
    for mat in sorted((matlab_code() / "Models").glob("*.mat")):
        ac = load_mat(mat)
        save_jsonc(ac, models_dir() / (mat.stem + ".jsonc"))

if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd Python && python scripts/mat_to_jsonc.py && python -m pytest tests/test_mat_to_jsonc_all.py -v
```

Expected PASS.

- [ ] **Step 5: Commit**

`feat: convert all 23 MATLAB models to JSONC`

---

### Task 28: atmosphere.py ISA port

**Files:**
- Create: `Python/src/aid/atmosphere.py`
- Test: `Python/tests/test_atmosphere.py`

**Interfaces:**
- Produces: `def atmosphere(h_ft: float) -> dict` keys `T,P,D,V,a`

- [ ] **Step 1: Write the failing test**

```python
# Python/tests/test_atmosphere.py
import math
from aid.atmosphere import atmosphere

def test_sea_level_isa():
    r = atmosphere(0.0)
    assert abs(r["T"] - 518.69) < 0.01
    assert abs(r["a"] - math.sqrt(1.4 * 1716 * r["T"])) < 0.1
    assert r["D"] > 0
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd Python && python -m pytest tests/test_atmosphere.py -v
```

Expected FAIL: module/function missing.

- [ ] **Step 3: Write minimal implementation**

Port `Atmosphere.m` piecewise `theta/delta/sigma` branches and sea-level constants (`T_0=518.69`, etc.) verbatim.

- [ ] **Step 4: Run test to verify it passes**

```bash
cd Python && python -m pytest tests/test_atmosphere.py -v
```

Expected PASS.

- [ ] **Step 5: Commit**

`feat: port Atmosphere.m to atmosphere.py`

---

### Task 29: geometry.py linear taper branch

**Files:**
- Create: `Python/src/aid/geometry.py`
- Test: `Python/tests/test_geometry_cessna_linear.py`

**Interfaces:**
- Produces: `def geometry(pt: dict, angl: bool, type: str = "") -> dict`

- [ ] **Step 1: Write the failing test**

```python
# Python/tests/test_geometry_cessna_linear.py
import numpy as np
from aid.aircraft import load_mat
from aid.geometry import geometry
from aid.paths import matlab_code

def test_cessna_wing_area_cbar_ar():
    ac = load_mat(matlab_code() / "Models" / "Cessna 172.mat")
    wg = dict(ac.WG)
    out = geometry(wg, angl=False)
    assert abs(float(np.asarray(out["S"]).reshape(-1)[-1]) - 24.0) < 1e-6
    assert abs(float(np.asarray(out["cbar"]).reshape(-1)[-1]) - 2.0) < 1e-6
    assert abs(float(np.asarray(out["AR"]).reshape(-1)[-1]) - 6.0) < 1e-4
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd Python && python -m pytest tests/test_geometry_cessna_linear.py -v
```

Expected FAIL: wrong `S` or missing function.

- [ ] **Step 3: Write minimal implementation**

Port `Geometry.m` `else` branch (single linear taper): `b=SSPN*2`, `cbar`, `TR`, `S`, `AR`, sweep/dihedral.

- [ ] **Step 4: Run test to verify it passes**

```bash
cd Python && python -m pytest tests/test_geometry_cessna_linear.py -v
```

Expected PASS.

- [ ] **Step 5: Commit**

`feat: geometry linear taper branch (Cessna)`

---

### Task 30: geometry.py break-span branch

**Files:**
- Modify: `Python/src/aid/geometry.py`
- Test: `Python/tests/test_geometry_break_span.py`

**Interfaces:**
- Consumes: planform with `CHRDBP` and `SSPNOP` nonzero
- Produces: segmented `S`, `cbar`, `TR` arrays

- [ ] **Step 1: Write the failing test**

```python
# Python/tests/test_geometry_break_span.py
from aid.geometry import geometry

def test_break_span_weighted_cbar():
    pt = {
        "CHRDR": 4.0, "CHRDBP": 3.0, "CHRDTP": 2.0,
        "SSPN": 10.0, "SSPNOP": 4.0,
        "SAVSI": 0.0, "SAVSO": 0.0, "CHSTAT": 0.25,
        "DHDADI": 0.0, "DHDADO": 0.0,
        "X": 0.0, "Y": 0.0, "Z": 0.0,
    }
    out = geometry(pt, angl=False)
    assert out["S"][-1] == out["S"][0] + out["S"][1]
    assert out["cbar"][-1] > 0
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd Python && python -m pytest tests/test_geometry_break_span.py -v
```

Expected FAIL: break branch not implemented.

- [ ] **Step 3: Write minimal implementation**

Port `Geometry.m` lines 5–67 (inboard/outboard sections, weighted `cbar`, equivalent taper).

- [ ] **Step 4: Run test to verify it passes**

```bash
cd Python && python -m pytest tests/test_geometry_break_span.py -v
```

Expected PASS.

- [ ] **Step 5: Commit**

`feat: geometry break-span branch`

---

### Task 31: drag.py CD0 port

**Files:**
- Create: `Python/src/aid/drag.py`
- Test: `Python/tests/test_drag_cessna.py`

**Interfaces:**
- Produces: `def drag(pt: dict, unit: str, atm: dict, wg_sref: float) -> dict`

- [ ] **Step 1: Write the failing test**

```python
# Python/tests/test_drag_cessna.py
from aid.aircraft import load_mat
from aid.atmosphere import atmosphere
from aid.drag import drag
from aid.paths import matlab_code

def test_drag_adds_cd0_field():
    ac = load_mat(matlab_code() / "Models" / "Cessna 172.mat")
    atm = atmosphere(float(ac.AERO["ALT"][0]))
    out = drag(dict(ac.WG), ac.unit, atm, float(ac.WG["S"]))
    assert "CD0" in out
    if "CD0" in ac.WG:
        assert abs(out["CD0"] - float(ac.WG["CD0"])) < 1e-3
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd Python && python -m pytest tests/test_drag_cessna.py -v
```

Expected FAIL: `drag` missing.

- [ ] **Step 3: Write minimal implementation**

Port `Drag.m` formulas for wing `CD0` using `TC`, `atm`, Reynolds from `atm["V"]`, etc.

- [ ] **Step 4: Run test to verify it passes**

```bash
cd Python && python -m pytest tests/test_drag_cessna.py -v
```

Expected PASS.

- [ ] **Step 5: Commit**

`feat: port Drag.m to drag.py`

---

### Task 32: datcom_io write FLTCON namelist

**Files:**
- Create: `Python/src/aid/datcom_io.py`
- Test: `Python/tests/test_datcom_fltcon.py`

**Interfaces:**
- Produces: `def write_fltcon(ac: Aircraft, lines: list) -> None`

- [ ] **Step 1: Write the failing test**

```python
# Python/tests/test_datcom_fltcon.py
from aid.aircraft import load_jsonc
from aid.datcom_io import write_fltcon
from aid.paths import models_dir

def test_fltcon_cessna_mach_alpha():
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    lines = []
    write_fltcon(ac, lines)
    text = "\n".join(lines)
    assert "$FLTCON" in text
    assert "MACH=0.030" in text or "MACH=0.03" in text
    assert "-4.0" in text and "12.0" in text
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd Python && python -m pytest tests/test_datcom_fltcon.py -v
```

Expected FAIL: `write_fltcon` missing.

- [ ] **Step 3: Write minimal implementation**

Translate `DATCOM_IO.m` `$FLTCON` block: `NALPHA`, `ALSCHD`, `NALT`, `ALT`, `NMACH`, `MACH`, `WT`, `LOOP`.

- [ ] **Step 4: Run test to verify it passes**

```bash
cd Python && python -m pytest tests/test_datcom_fltcon.py -v
```

Expected PASS.

- [ ] **Step 5: Commit**

`feat: DATCOM $FLTCON writer`

---

### Task 33: datcom_io write SYNTHS and OPTINS

**Files:**
- Modify: `Python/src/aid/datcom_io.py`
- Test: `Python/tests/test_datcom_synths.py`

**Interfaces:**
- Produces: `def write_optins(...)`, `def write_synths(...)`

- [ ] **Step 1: Write the failing test**

```python
# Python/tests/test_datcom_synths.py
from aid.aircraft import load_jsonc
from aid.datcom_io import write_synths, write_optins
from aid.paths import models_dir

def test_synths_xcg_and_wing_position():
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    lines = []
    write_optins(ac, lines)
    write_synths(ac, lines)
    text = "\n".join(lines)
    assert "$OPTINS" in text and "SREF=24" in text
    assert "$SYNTHS" in text and "XCG=2.94" in text
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd Python && python -m pytest tests/test_datcom_synths.py -v
```

Expected FAIL.

- [ ] **Step 3: Write minimal implementation**

Port `$OPTINS` (`SREF`, `CBARR`, `BLREF` from `AERO`/wing geometry) and `$SYNTHS` (`XCG`, `XW`, `ZW`, `ALIW`, tail positions).

- [ ] **Step 4: Run test to verify it passes**

```bash
cd Python && python -m pytest tests/test_datcom_synths.py -v
```

Expected PASS.

- [ ] **Step 5: Commit**

`feat: DATCOM $OPTINS and $SYNTHS writers`

---

### Task 34: datcom_io write BODY and NACA line

**Files:**
- Modify: `Python/src/aid/datcom_io.py`
- Test: `Python/tests/test_datcom_body.py`

**Interfaces:**
- Produces: `def write_body(ac, lines)`, `def naca_wing_line(ac) -> str`

- [ ] **Step 1: Write the failing test**

```python
# Python/tests/test_datcom_body.py
from aid.aircraft import load_jsonc
from aid.datcom_io import write_body, naca_wing_line
from aid.paths import models_dir

def test_body_and_naca_cessna():
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    lines = []
    write_body(ac, lines)
    naca = naca_wing_line(ac)
    assert "$BODY" in "\n".join(lines)
    assert "NACA-W-4-2412" in naca
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd Python && python -m pytest tests/test_datcom_body.py -v
```

Expected FAIL.

- [ ] **Step 3: Write minimal implementation**

Port `$BODY` from `BD` struct; NACA line `NACA-W-{digits}-{code}` from `WG.NACA{1}` length.

- [ ] **Step 4: Run test to verify it passes**

```bash
cd Python && python -m pytest tests/test_datcom_body.py -v
```

Expected PASS.

- [ ] **Step 5: Commit**

`feat: DATCOM $BODY and NACA-W writer`

---

### Task 35: datcom_io write WGPLNF wing

**Files:**
- Modify: `Python/src/aid/datcom_io.py`
- Test: `Python/tests/test_datcom_wgplnf.py`

**Interfaces:**
- Produces: `def write_wgplnf(pt, lines, label='')`

- [ ] **Step 1: Write the failing test**

```python
# Python/tests/test_datcom_wgplnf.py
from aid.aircraft import load_jsonc
from aid.datcom_io import write_wgplnf
from aid.paths import models_dir

def test_wgplnf_chrdr_sspn():
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    lines = []
    write_wgplnf(ac.WG, lines)
    text = "\n".join(lines)
    assert "$WGPLNF" in text
    assert "CHRDR=2" in text.replace(" ", "")
    assert "SSPN=6" in text.replace(" ", "")
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd Python && python -m pytest tests/test_datcom_wgplnf.py -v
```

Expected FAIL.

- [ ] **Step 3: Write minimal implementation**

Port wing `$WGPLNF`; if `SSPNOP!=0`, write span-from-tip `SSPN-SSPNOP`.

- [ ] **Step 4: Run test to verify it passes**

```bash
cd Python && python -m pytest tests/test_datcom_wgplnf.py -v
```

Expected PASS.

- [ ] **Step 5: Commit**

`feat: DATCOM $WGPLNF wing writer`

---

### Task 36: datcom_io write controls SYMFLP ASYFLP

**Files:**
- Modify: `Python/src/aid/datcom_io.py`
- Test: `Python/tests/test_datcom_controls.py`

**Interfaces:**
- Produces: `def write_symflp(...)`, `def write_asyflp(...)`

- [ ] **Step 1: Write the failing test**

```python
# Python/tests/test_datcom_controls.py
from aid.aircraft import load_jsonc
from aid.datcom_io import write_controls
from aid.paths import models_dir

def test_controls_section_present_or_empty():
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    lines = []
    write_controls(ac, lines)
    text = "\n".join(lines)
    # Cessna may have zero deflection; writer must not crash
    assert "PLOT" not in text  # controls only task
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd Python && python -m pytest tests/test_datcom_controls.py -v
```

Expected FAIL.

- [ ] **Step 3: Write minimal implementation**

Port `$SYMFLP` for `F` and `E`, `$ASYFLP` for `A` when deflections nonzero; skip when zero (batch never wing-only Yes).

- [ ] **Step 4: Run test to verify it passes**

```bash
cd Python && python -m pytest tests/test_datcom_controls.py -v
```

Expected PASS.

- [ ] **Step 5: Commit**

`feat: DATCOM flap/aileron/elevator writers`

---

### Task 37: datcom_io write_for005 orchestrator

**Files:**
- Modify: `Python/src/aid/datcom_io.py`
- Test: `Python/tests/test_datcom_writer_cessna.py`

**Interfaces:**
- Produces: `def write_for005(ac: Aircraft, path: Path, *, unit: str) -> None`

- [ ] **Step 1: Write the failing test**

```python
# Python/tests/test_datcom_writer_cessna.py
from pathlib import Path
from aid.aircraft import load_jsonc
from aid.datcom_io import write_for005
from aid.paths import models_dir

def test_full_for005_cessna(tmp_path):
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    p = tmp_path / "for005.dat"
    write_for005(ac, p, unit="ft")
    text = p.read_text()
    assert "CASEID" in text
    assert "$FLTCON" in text and "$WGPLNF" in text
    assert "NACA-W-4-2412" in text
    assert "PLOT" in text and "NEXT CASE" in text
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd Python && python -m pytest tests/test_datcom_writer_cessna.py -v
```

Expected FAIL.

- [ ] **Step 3: Write minimal implementation**

Assemble Tasks 32–36 + `DIM IN` when `unit=='in'`, HT/VT `$WGPLNF`, `CASEID`.

- [ ] **Step 4: Run test to verify it passes**

```bash
cd Python && python -m pytest tests/test_datcom_writer_cessna.py -v
```

Expected PASS.

- [ ] **Step 5: Commit**

`feat: assemble DATCOM for005 writer`

---

### Task 38: datcom_parse alpha cl cm

**Files:**
- Create: `Python/src/aid/datcom_parse.py`
- Test: `Python/tests/test_datcom_parse_gold.py`

**Interfaces:**
- Produces: `def parse_for006(text: str) -> dict`

- [ ] **Step 1: Write the failing test**

```python
# Python/tests/test_datcom_parse_gold.py
import json
from pathlib import Path
from aid.datcom_parse import parse_for006
from aid.paths import results_dir

def test_parse_matlab_gold_for006():
    p = results_dir() / "matlab" / "Cessna 172" / "datcom.out"
    gold = json.loads((results_dir() / "matlab" / "Cessna 172" / "datcom.json").read_text())
    got = parse_for006(p.read_text())
    import numpy as np
    assert np.allclose(got["alpha"], gold["alpha"], atol=1e-6)
    assert np.allclose(got["cl"], gold["cl"], atol=1e-6)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd Python && python -m pytest tests/test_datcom_parse_gold.py -v
```

Expected FAIL: parser missing or arrays differ.

- [ ] **Step 3: Write minimal implementation**

Parse Digital DATCOM stability tables; lowercase keys matching `datcomimport` (`alpha`, `cl`, `cd`, `cm`, derivatives).

- [ ] **Step 4: Run test to verify it passes**

```bash
cd Python && python -m pytest tests/test_datcom_parse_gold.py -v
```

Expected PASS.

- [ ] **Step 5: Commit**

`feat: parse DATCOM for006/datcom.out tables`

---

### Task 39: datcom_run subprocess

**Files:**
- Create: `Python/src/aid/datcom_run.py`
- Test: `Python/tests/test_datcom_run_cessna.py`

**Interfaces:**
- Produces: `def run_datcom(ac: Aircraft, workdir: Path) -> dict`

- [ ] **Step 1: Write the failing test**

```python
# Python/tests/test_datcom_run_cessna.py
import json
import numpy as np
from pathlib import Path
from aid.aircraft import load_jsonc
from aid.datcom_run import run_datcom
from aid.paths import models_dir, results_dir

def test_run_datcom_matches_matlab_gold(tmp_path):
    gold = json.loads((results_dir() / "matlab" / "Cessna 172" / "datcom.json").read_text())
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    got = run_datcom(ac, tmp_path / "work")
    assert np.allclose(got["cl"], gold["cl"], atol=1e-6)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd Python && python -m pytest tests/test_datcom_run_cessna.py -v
```

Expected FAIL.

- [ ] **Step 3: Write minimal implementation**

```python
def run_datcom(ac, workdir):
    workdir.mkdir(parents=True, exist_ok=True)
    write_for005(ac, workdir / "for005.dat", unit=ac.unit)
    subprocess.run([str(datcom_wrapper())], cwd=workdir, check=True, timeout=120)
    return parse_for006((workdir / "for006.dat").read_text())
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd Python && python -m pytest tests/test_datcom_run_cessna.py -v
```

Expected PASS.

- [ ] **Step 5: Commit**

`feat: DATCOM subprocess runner`

---

### Task 40: tornado_io geo and state

**Files:**
- Create: `Python/src/aid/tornado_io.py`
- Test: `Python/tests/test_tornado_io_cessna.py`

**Interfaces:**
- Produces: `def tornado_io(ac: Aircraft, mesh: tuple[str, str]) -> tuple[dict, dict]`

- [ ] **Step 1: Write the failing test**

```python
# Python/tests/test_tornado_io_cessna.py
from aid.aircraft import load_jsonc
from aid.tornado_io import tornado_io
from aid.paths import models_dir

def test_tornado_io_cessna_mesh_10_5():
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    geo, state = tornado_io(ac, ("10", "5"))
    assert geo["nwing"] >= 1
    assert float(geo["c"][0, 0]) == 2.0
    assert state["betha"] == 0.0
    assert state["AS"] > 0
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd Python && python -m pytest tests/test_tornado_io_cessna.py -v
```

Expected FAIL.

- [ ] **Step 3: Write minimal implementation**

Port `Tornado_IO.m`: `AS = MACH*a/3.28084`, `rho = D*515.379`, build `geo.c`, `geo.nwing`, component flags from `plot_cmp`.

- [ ] **Step 4: Run test to verify it passes**

```bash
cd Python && python -m pytest tests/test_tornado_io_cessna.py -v
```

Expected PASS.

- [ ] **Step 5: Commit**

`feat: port Tornado_IO geo/state builder`

---

### Task 41: tornado lattice_setup

**Files:**
- Create: `Python/src/aid/tornado/lattice.py`
- Create: `Python/src/aid/tornado/__init__.py`
- Test: `Python/tests/test_tornado_lattice.py`

**Interfaces:**
- Produces: `def lattice_setup(geo: dict, state: dict, mode: int) -> tuple[dict, dict]`

- [ ] **Step 1: Write the failing test**

```python
# Python/tests/test_tornado_lattice.py
from aid.aircraft import load_jsonc
from aid.tornado_io import tornado_io
from aid.tornado.lattice import lattice_setup
from aid.paths import models_dir

def test_lattice_nonzero_panels():
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    geo, state = tornado_io(ac, ("10", "5"))
    lattice, ref = lattice_setup(geo, state, 0)
    assert lattice["npan"] > 0
    assert "X" in lattice and "Y" in lattice
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd Python && python -m pytest tests/test_tornado_lattice.py -v
```

Expected FAIL.

- [ ] **Step 3: Write minimal implementation**

Port `fLattice_setup2.m` panel coordinates and reference lengths.

- [ ] **Step 4: Run test to verify it passes**

```bash
cd Python && python -m pytest tests/test_tornado_lattice.py -v
```

Expected PASS.

- [ ] **Step 5: Commit**

`feat: port fLattice_setup2 to lattice.py`

---

### Task 42: tornado setboundary5

**Files:**
- Create: `Python/src/aid/tornado/boundary.py`
- Test: `Python/tests/test_tornado_boundary.py`

**Interfaces:**
- Produces: `def set_boundary(lattice: dict, geo: dict, state: dict) -> dict`

- [ ] **Step 1: Write the failing test**

```python
# Python/tests/test_tornado_boundary.py
from aid.aircraft import load_jsonc
from aid.tornado_io import tornado_io
from aid.tornado.lattice import lattice_setup
from aid.tornado.boundary import set_boundary
from aid.paths import models_dir

def test_boundary_rhs_shape():
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    geo, state = tornado_io(ac, ("10", "5"))
    lattice, ref = lattice_setup(geo, state, 0)
    lat2 = set_boundary(lattice, geo, state)
    assert "rhs" in lat2 or "RHS" in lat2
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd Python && python -m pytest tests/test_tornado_boundary.py -v
```

Expected FAIL.

- [ ] **Step 3: Write minimal implementation**

Port `setboundary5.m` Kutta conditions and RHS assembly.

- [ ] **Step 4: Run test to verify it passes**

```bash
cd Python && python -m pytest tests/test_tornado_boundary.py -v
```

Expected PASS.

- [ ] **Step 5: Commit**

`feat: port setboundary5 to boundary.py`

---

### Task 43: tornado ISAtmosphere

**Files:**
- Create: `Python/src/aid/tornado/isa.py`
- Test: `Python/tests/test_tornado_isa.py`

**Interfaces:**
- Produces: `def isa_atmosphere(alt: float) -> dict`

- [ ] **Step 1: Write the failing test**

```python
# Python/tests/test_tornado_isa.py
from aid.tornado.isa import isa_atmosphere

def test_isa_rho_positive():
    r = isa_atmosphere(0.0)
    assert r["rho"] > 0
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd Python && python -m pytest tests/test_tornado_isa.py -v
```

Expected FAIL.

- [ ] **Step 3: Write minimal implementation**

Port `ISAtmosphere.m` if solver calls it; else thin wrapper on `aid.atmosphere` with Tornado unit conversions.

- [ ] **Step 4: Run test to verify it passes**

```bash
cd Python && python -m pytest tests/test_tornado_isa.py -v
```

Expected PASS.

- [ ] **Step 5: Commit**

`feat: Tornado ISA atmosphere helper`

---

### Task 44: tornado solver

**Files:**
- Create: `Python/src/aid/tornado/solver.py`
- Test: `Python/tests/test_tornado_solver_gamma.py`

**Interfaces:**
- Produces: `def solve(state: dict, geo: dict, lattice: dict) -> dict`

- [ ] **Step 1: Write the failing test**

```python
# Python/tests/test_tornado_solver_gamma.py
import numpy as np
from aid.aircraft import load_jsonc
from aid.tornado_io import tornado_io
from aid.tornado.lattice import lattice_setup
from aid.tornado.boundary import set_boundary
from aid.tornado.solver import solve
from aid.paths import models_dir

def test_solver_returns_gamma():
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    geo, state = tornado_io(ac, ("10", "5"))
    lattice, ref = lattice_setup(geo, state, 0)
    lattice = set_boundary(lattice, geo, state)
    res = solve(state, geo, lattice)
    g = np.asarray(res["gamma"]).reshape(-1)
    assert g.size > 0
    assert np.isfinite(g).all()
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd Python && python -m pytest tests/test_tornado_solver_gamma.py -v
```

Expected FAIL.

- [ ] **Step 3: Write minimal implementation**

Port `solver.m` + downwash (`fastdw`); `numpy.linalg.solve`; no waitbar; preserve `pgcorr`.

- [ ] **Step 4: Run test to verify it passes**

```bash
cd Python && python -m pytest tests/test_tornado_solver_gamma.py -v
```

Expected PASS.

- [ ] **Step 5: Commit**

`feat: port Tornado solver`

---

### Task 45: tornado coeff_create3

**Files:**
- Create: `Python/src/aid/tornado/coeff.py`
- Test: `Python/tests/test_tornado_cessna_coeff.py`

**Interfaces:**
- Produces: `def coeff_create(results, lattice, state, ref, geo) -> dict`

- [ ] **Step 1: Write the failing test**

```python
# Python/tests/test_tornado_cessna_coeff.py
import json
import numpy as np
from aid.aircraft import load_jsonc
from aid.tornado_io import tornado_io
from aid.tornado.lattice import lattice_setup
from aid.tornado.boundary import set_boundary
from aid.tornado.solver import solve
from aid.tornado.coeff import coeff_create
from aid.paths import models_dir, results_dir

def test_tornado_cl_matches_matlab_gold():
    gold = json.loads((results_dir() / "matlab" / "Cessna 172" / "tornado.json").read_text())
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    geo, state = tornado_io(ac, ("10", "5"))
    lattice, ref = lattice_setup(geo, state, 0)
    lattice = set_boundary(lattice, geo, state)
    raw = solve(state, geo, lattice)
    tres = coeff_create(raw, lattice, state, ref, geo)
    rtol, atol = 1e-4, 1e-5
    assert np.allclose(tres["CL"], gold["CL"], rtol=rtol, atol=atol)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd Python && python -m pytest tests/test_tornado_cessna_coeff.py -v
```

Expected FAIL.

- [ ] **Step 3: Write minimal implementation**

Port `coeff_create3.m` force/moment coefficients and derivatives.

- [ ] **Step 4: Run test to verify it passes**

```bash
cd Python && python -m pytest tests/test_tornado_cessna_coeff.py -v
```

Expected PASS.

- [ ] **Step 5: Commit**

`feat: port coeff_create3; Cessna Tornado parity`

---

### Task 46: avl_parse findValue

**Files:**
- Create: `Python/src/aid/avl_parse.py`
- Test: `Python/tests/test_avl_find_value.py`

**Interfaces:**
- Produces: `def find_value(lines: list[str], name: str, area: str = "") -> tuple[float, int]`

- [ ] **Step 1: Write the failing test**

```python
# Python/tests/test_avl_find_value.py
from aid.avl_parse import find_value

SAMPLE = [
    " Stability-axis derivatives...",
    " CLa =   4.5123  per rad",
    " Cma =  -0.8234  per rad",
]

def test_find_cla():
    v, ln = find_value(SAMPLE, "CLa")
    assert abs(v - 4.5123) < 1e-6
    assert ln == 1
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd Python && python -m pytest tests/test_avl_find_value.py -v
```

Expected FAIL.

- [ ] **Step 3: Write minimal implementation**

Port `findValue.m` string scan for `name = value`.

- [ ] **Step 4: Run test to verify it passes**

```bash
cd Python && python -m pytest tests/test_avl_find_value.py -v
```

Expected PASS.

- [ ] **Step 5: Commit**

`feat: port AVL findValue parser helper`

---

### Task 47: avl_parse parseST

**Files:**
- Modify: `Python/src/aid/avl_parse.py`
- Test: `Python/tests/test_avl_parse_st_gold.py`

**Interfaces:**
- Produces: `def parse_st(path: Path) -> dict`

- [ ] **Step 1: Write the failing test**

```python
# Python/tests/test_avl_parse_st_gold.py
import json
from aid.avl_parse import parse_st
from aid.paths import results_dir

def test_parse_st_matches_matlab_json():
    stfile = results_dir() / "matlab" / "Cessna 172" / "geometry.st"
    gold = json.loads((results_dir() / "matlab" / "Cessna 172" / "avl.json").read_text())
    got = parse_st(stfile)
    assert abs(got["CLa"] - gold["CLa"]) < 1e-6
    assert abs(got["Cma"] - gold["Cma"]) < 1e-6
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd Python && python -m pytest tests/test_avl_parse_st_gold.py -v
```

Expected FAIL.

- [ ] **Step 3: Write minimal implementation**

Port `parseST.m`; extract `CLa`, `Cma`, `CLb`, `Clb`, `Cnb`, `NP`, etc.

- [ ] **Step 4: Run test to verify it passes**

```bash
cd Python && python -m pytest tests/test_avl_parse_st_gold.py -v
```

Expected PASS.

- [ ] **Step 5: Commit**

`feat: port parseST to avl_parse.py`

---

### Task 48: avl_parse parseSB and parseRunCaseHeader

**Files:**
- Modify: `Python/src/aid/avl_parse.py`
- Test: `Python/tests/test_avl_parse_sb.py`

**Interfaces:**
- Produces: `def parse_sb(path: Path) -> dict`, `def parse_run_case_header(path: Path) -> dict`

- [ ] **Step 1: Write the failing test**

```python
# Python/tests/test_avl_parse_sb.py
from aid.avl_parse import parse_sb
from aid.paths import results_dir

def test_parse_sb_does_not_crash_on_gold():
    sb = results_dir() / "matlab" / "Cessna 172" / "geometry.sb"
    if sb.is_file():
        d = parse_sb(sb)
        assert isinstance(d, dict)
    else:
        import pytest
        pytest.skip("geometry.sb not in gold yet")
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd Python && python -m pytest tests/test_avl_parse_sb.py -v
```

Expected FAIL: functions missing.

- [ ] **Step 3: Write minimal implementation**

Port `parseSB.m` and `parseRunCaseHeader.m`.

- [ ] **Step 4: Run test to verify it passes**

```bash
cd Python && python -m pytest tests/test_avl_parse_sb.py -v
```

Expected PASS or skip.

- [ ] **Step 5: Commit**

`feat: port parseSB and parseRunCaseHeader`

---

### Task 49: avl_io write geometry files

**Files:**
- Create: `Python/src/aid/avl_io.py`
- Test: `Python/tests/test_avl_write_geometry.py`

**Interfaces:**
- Produces: `def write_avl_geometry(ac, geo, state, run_dir: Path, ni: int, nj: int) -> None`

- [ ] **Step 1: Write the failing test**

```python
# Python/tests/test_avl_write_geometry.py
from aid.aircraft import load_jsonc
from aid.tornado_io import tornado_io
from aid.avl_io import write_avl_geometry
from aid.paths import models_dir

def test_writes_geometry_avl(tmp_path):
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    geo, state = tornado_io(ac, ("10", "10"))
    write_avl_geometry(ac, geo, state, tmp_path, 10, 10)
    avl = tmp_path / "geometry.avl"
    assert avl.is_file()
    text = avl.read_text()
    assert "SURFACE" in text or "SECTION" in text
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd Python && python -m pytest tests/test_avl_write_geometry.py -v
```

Expected FAIL.

- [ ] **Step 3: Write minimal implementation**

Port `AVL_IO.m` `Write_Input`, `Write_Surface`, airfoil `AFILE` side files (`WG.1`, …).

- [ ] **Step 4: Run test to verify it passes**

```bash
cd Python && python -m pytest tests/test_avl_write_geometry.py -v
```

Expected PASS.

- [ ] **Step 5: Commit**

`feat: AVL geometry.avl writer`

---

### Task 50: avl_io Write_Case and run_avl

**Files:**
- Modify: `Python/src/aid/avl_io.py`
- Test: `Python/tests/test_avl_run_cessna.py`

**Interfaces:**
- Produces: `def write_case(...)`, `def run_avl(run_dir: Path) -> None`, `def run_avl_full(ac, mesh) -> dict`

- [ ] **Step 1: Write the failing test**

```python
# Python/tests/test_avl_run_cessna.py
import json
from pathlib import Path
from aid.aircraft import load_jsonc
from aid.avl_io import run_avl_full
from aid.paths import models_dir, results_dir

def test_avl_cla_matches_matlab(tmp_path):
    gold = json.loads((results_dir() / "matlab" / "Cessna 172" / "avl.json").read_text())
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    got = run_avl_full(ac, ("10", "10"), tmp_path)
    assert abs(got["CLa"] - gold["CLa"]) < 1e-6
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd Python && python -m pytest tests/test_avl_run_cessna.py -v
```

Expected FAIL.

- [ ] **Step 3: Write minimal implementation**

Port `Write_Case`: `LOAD geometry.avl`, `PLOP/g`, `OPER`, `c1`, `v <AS>`, `x`, `st geometry.st`, `sb geometry.sb`, `Quit`. Subprocess `avl_bin() < geometry.run`.

- [ ] **Step 4: Run test to verify it passes**

```bash
cd Python && python -m pytest tests/test_avl_run_cessna.py -v
```

Expected PASS.

- [ ] **Step 5: Commit**

`feat: AVL run case and Cessna parity`

---

### Task 51: compare harness

**Files:**
- Create: `Python/src/aid/compare.py`
- Test: `Python/tests/test_compare_primary.py`

**Interfaces:**
- Produces: `def compare_to_matlab(name: str) -> dict`, `def run_python(ac, work: Path) -> dict`

- [ ] **Step 1: Write the failing test**

```python
# Python/tests/test_compare_primary.py
import pytest
from aid.compare import compare_to_matlab

PRIMARY = ["Cessna 172", "Navion", "DA20-C1", "Learjet 23"]

@pytest.mark.parametrize("name", PRIMARY)
def test_primary_all_solvers(name):
    report = compare_to_matlab(name)
    assert report["datcom"]["pass"]
    assert report["tornado"]["pass"]
    assert report["avl"]["pass"]
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd Python && python -m pytest tests/test_compare_primary.py -v
```

Expected FAIL.

- [ ] **Step 3: Write minimal implementation**

Implement spec §13 tolerances; write `Results/compare/<name>.json`; `run_python` calls `run_datcom`, Tornado chain, `run_avl_full`.

- [ ] **Step 4: Run test to verify it passes**

```bash
cd Python && python -m pytest tests/test_compare_primary.py -v
```

Expected PASS on primary four.

- [ ] **Step 5: Commit**

`feat: MATLAB vs Python coefficient compare harness`

---

### Task 52: run_all script

**Files:**
- Create: `Python/scripts/run_all.py`
- Test: `Python/tests/test_run_all_summary.py`

**Interfaces:**
- Produces: CLI looping `Python/models/*.jsonc` → `Results/python/` + compare

- [ ] **Step 1: Write the failing test**

```python
# Python/tests/test_run_all_summary.py
import json
from aid.paths import models_dir, results_dir

def test_python_results_for_cessna_exist():
    d = results_dir() / "python" / "Cessna 172"
    assert (d / "status.json").is_file()
    st = json.loads((d / "status.json").read_text())
    assert st["datcom"] in ("ok", "failed")
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd Python && python -m pytest tests/test_run_all_summary.py -v
```

Expected FAIL.

- [ ] **Step 3: Write minimal implementation**

```python
# Python/scripts/run_all.py
for jsonc in sorted(models_dir().glob("*.jsonc")):
    name = jsonc.stem
    run_python(load_jsonc(jsonc), results_dir() / "python" / name)
    compare_to_matlab(name)
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd Python && python scripts/run_all.py --aircraft "Cessna 172" && python -m pytest tests/test_run_all_summary.py -v
```

Expected PASS.

- [ ] **Step 5: Commit**

`feat: run_all batch script for python Results`

---

### Task 53: aid_gui window title and size

**Files:**
- Create: `Python/src/aid_gui/__init__.py`
- Create: `Python/src/aid_gui/app.py`
- Create: `Python/src/aid_gui/main_window.py`
- Test: `Python/tests/test_gui_window.py`

**Interfaces:**
- Produces: `class MainWindow(QMainWindow)` title `Aircraft Intuitive Design Tool`, size 960×600

- [ ] **Step 1: Write the failing test**

```python
# Python/tests/test_gui_window.py
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication
from aid_gui.main_window import MainWindow

def test_window_title_and_size():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    assert w.windowTitle() == "Aircraft Intuitive Design Tool"
    assert w.size().width() == 960
    assert w.size().height() == 600
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd Python && python -m pytest tests/test_gui_window.py -v
```

Expected FAIL.

- [ ] **Step 3: Write minimal implementation**

```python
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Aircraft Intuitive Design Tool")
        self.resize(960, 600)
        self.aircraft = None
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd Python && python -m pytest tests/test_gui_window.py -v
```

Expected PASS.

- [ ] **Step 5: Commit**

`feat: PySide6 main window shell`

---

### Task 54: aid_gui File menu

**Files:**
- Create: `Python/src/aid_gui/menus.py`
- Modify: `Python/src/aid_gui/main_window.py`
- Test: `Python/tests/test_gui_file_menu.py`

**Interfaces:**
- Produces: menu actions `New`, `Load`, `Save`

- [ ] **Step 1: Write the failing test**

```python
# Python/tests/test_gui_file_menu.py
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication
from aid_gui.main_window import MainWindow

def test_file_menu_actions():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    file_menu = [a for a in w.menuBar().actions() if a.text() == "File"][0].menu()
    labels = [a.text() for a in file_menu.actions() if not a.isSeparator()]
    assert labels[:3] == ["New", "Load", "Save"]
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd Python && python -m pytest tests/test_gui_file_menu.py -v
```

Expected FAIL.

- [ ] **Step 3: Write minimal implementation**

`menus.py` builds File menu; slots stub (`aircraft = None` on New).

- [ ] **Step 4: Run test to verify it passes**

```bash
cd Python && python -m pytest tests/test_gui_file_menu.py -v
```

Expected PASS.

- [ ] **Step 5: Commit**

`feat: GUI File menu New Load Save`

---

### Task 55: aid_gui Analyze menu

**Files:**
- Modify: `Python/src/aid_gui/menus.py`
- Test: `Python/tests/test_gui_analyze_menu.py`

**Interfaces:**
- Produces: `Analyze` submenu `{DATCOM, Tornado, AVL}`

- [ ] **Step 1: Write the failing test**

```python
# Python/tests/test_gui_analyze_menu.py
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication
from aid_gui.main_window import MainWindow

def test_analyze_submenu():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    analyze = [a for a in w.menuBar().actions() if a.text() == "Analyze"][0].menu()
    labels = [a.text() for a in analyze.actions() if not a.isSeparator()]
    assert labels == ["DATCOM", "Tornado", "AVL"]
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd Python && python -m pytest tests/test_gui_analyze_menu.py -v
```

Expected FAIL.

- [ ] **Step 3: Write minimal implementation**

Wire Analyze submenu; connect to stub slots on `MainWindow`.

- [ ] **Step 4: Run test to verify it passes**

```bash
cd Python && python -m pytest tests/test_gui_analyze_menu.py -v
```

Expected PASS.

- [ ] **Step 5: Commit**

`feat: GUI Analyze menu DATCOM Tornado AVL`

---

### Task 56: aid_gui Help menu

**Files:**
- Modify: `Python/src/aid_gui/menus.py`
- Test: `Python/tests/test_gui_help_menu.py`

**Interfaces:**
- Produces: `Help` submenu `{Examples, Quick Start, User's Manual, control legend}`

- [ ] **Step 1: Write the failing test**

```python
# Python/tests/test_gui_help_menu.py
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication
from aid_gui.main_window import MainWindow

def test_help_submenu():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    help_m = [a for a in w.menuBar().actions() if a.text() == "Help"][0].menu()
    labels = [a.text() for a in help_m.actions() if not a.isSeparator()]
    assert "Examples" in labels and "User's Manual" in labels
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd Python && python -m pytest tests/test_gui_help_menu.py -v
```

Expected FAIL.

- [ ] **Step 3: Write minimal implementation**

Help → User's Manual opens `AID_Documentation.pdf` via `QDesktopServices` (path from `matlab_code()`).

- [ ] **Step 4: Run test to verify it passes**

```bash
cd Python && python -m pytest tests/test_gui_help_menu.py -v
```

Expected PASS.

- [ ] **Step 5: Commit**

`feat: GUI Help menu with manual action`

---

### Task 57: aid_gui Wing tab CHRDR field

**Files:**
- Create: `Python/src/aid_gui/tabs.py`
- Modify: `Python/src/aid_gui/main_window.py`
- Test: `Python/tests/test_gui_wing_chrdr.py`

**Interfaces:**
- Produces: Wing tab with labeled `Root Chord` bound to `WG.CHRDR`

- [ ] **Step 1: Write the failing test**

```python
# Python/tests/test_gui_wing_chrdr.py
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication
from aid_gui.main_window import MainWindow
from aid.aircraft import load_jsonc
from aid.paths import models_dir

def test_wing_chrdr_shows_2():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    w.load_aircraft(load_jsonc(models_dir() / "Cessna 172.jsonc"))
    assert abs(w.wing_chrdr_value() - 2.0) < 1e-9
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd Python && python -m pytest tests/test_gui_wing_chrdr.py -v
```

Expected FAIL.

- [ ] **Step 3: Write minimal implementation**

`tabs.py` Wing tab with `QLineEdit` for CHRDR label `Root Chord`; `load_aircraft` populates field.

- [ ] **Step 4: Run test to verify it passes**

```bash
cd Python && python -m pytest tests/test_gui_wing_chrdr.py -v
```

Expected PASS.

- [ ] **Step 5: Commit**

`feat: GUI Wing tab Root Chord field`

---

### Task 58: aid_gui remaining tabs and load JSONC

**Files:**
- Modify: `Python/src/aid_gui/tabs.py`, `main_window.py`
- Test: `Python/tests/test_gui_tabs_cessna.py`

**Interfaces:**
- Produces: tabs Wing/HT/VT/Control/Body/Aero/`+`; `load_jsonc`/`save_jsonc` via QFileDialog hooks

- [ ] **Step 1: Write the failing test**

```python
# Python/tests/test_gui_tabs_cessna.py
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication
from aid_gui.main_window import MainWindow
from aid.aircraft import load_jsonc
from aid.paths import models_dir

def test_aero_mach_and_sspn():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    w.load_aircraft(load_jsonc(models_dir() / "Cessna 172.jsonc"))
    assert abs(w.field_value("AERO.MACH") - 0.03) < 1e-9
    assert abs(w.field_value("WG.SSPN") - 6.0) < 1e-9
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd Python && python -m pytest tests/test_gui_tabs_cessna.py -v
```

Expected FAIL.

- [ ] **Step 3: Write minimal implementation**

Add remaining planform fields per spec §6.1 `RP` list; Aero tab `ALSCHD, ALT, MACH, WT, XCG`; `+` tab stub; File→Load sets aircraft from JSONC path.

- [ ] **Step 4: Run test to verify it passes**

```bash
cd Python && python -m pytest tests/test_gui_tabs_cessna.py -v
```

Expected PASS.

- [ ] **Step 5: Commit**

`feat: GUI geometry/aero tabs and JSONC load`

---

### Task 59: aid_gui 3D view placeholder

**Files:**
- Create: `Python/src/aid_gui/view3d.py`
- Modify: `Python/src/aid_gui/main_window.py`
- Test: `Python/tests/test_gui_view3d.py`

**Interfaces:**
- Produces: center matplotlib canvas updating on `load_aircraft`

- [ ] **Step 1: Write the failing test**

```python
# Python/tests/test_gui_view3d.py
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication
from aid_gui.main_window import MainWindow
from aid.aircraft import load_jsonc
from aid.paths import models_dir

def test_view3d_has_canvas():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    w.load_aircraft(load_jsonc(models_dir() / "Cessna 172.jsonc"))
    assert w.view3d is not None
    assert w.view3d.line_count() > 0
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd Python && python -m pytest tests/test_gui_view3d.py -v
```

Expected FAIL.

- [ ] **Step 3: Write minimal implementation**

Port minimal `Plot_Planform.m` wing outline to matplotlib `FigureCanvasQTAgg`; `line_count()` returns plotted segments.

- [ ] **Step 4: Run test to verify it passes**

```bash
cd Python && python -m pytest tests/test_gui_view3d.py -v
```

Expected PASS.

- [ ] **Step 5: Commit**

`feat: GUI 3D planform view placeholder`

---

### Task 60: aid_gui Analyze DATCOM wiring

**Files:**
- Modify: `Python/src/aid_gui/main_window.py`
- Create: `Python/src/aid_gui/results_panel.py`
- Test: `Python/tests/test_gui_analyze_datcom.py`

**Interfaces:**
- Produces: `MainWindow.run_datcom()` → `last_results["datcom"]`; missing binary shows `QMessageBox.critical` with path

- [ ] **Step 1: Write the failing test**

```python
# Python/tests/test_gui_analyze_datcom.py
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication
from aid_gui.main_window import MainWindow
from aid.aircraft import load_jsonc
from aid.paths import models_dir

def test_run_datcom_populates_cl():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    w.load_aircraft(load_jsonc(models_dir() / "Cessna 172.jsonc"))
    w.run_datcom()
    assert "cl" in w.last_results["datcom"]
    assert len(w.last_results["datcom"]["cl"]) >= 3
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd Python && python -m pytest tests/test_gui_analyze_datcom.py -v
```

Expected FAIL.

- [ ] **Step 3: Write minimal implementation**

Analyze→DATCOM calls `aid.datcom_run.run_datcom`; store results; `results_panel` plots `alpha` vs `cl`. Tornado/AVL slots call engine with meshes 10/5 and 10/10.

- [ ] **Step 4: Run test to verify it passes**

```bash
cd Python && python -m pytest tests/test_gui_analyze_datcom.py -v
```

Expected PASS.

- [ ] **Step 5: Commit**

`feat: wire GUI Analyze DATCOM and results plot`

---

### Task 61: aid_gui entry point and Settings stub

**Files:**
- Modify: `Python/pyproject.toml`, `Python/src/aid_gui/app.py`
- Test: `Python/tests/test_gui_entry.py`

**Interfaces:**
- Produces: `[project.scripts] aid = "aid_gui.app:main"`, Settings menu stub (no crash)

- [ ] **Step 1: Write the failing test**

```python
# Python/tests/test_gui_entry.py
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from importlib.metadata import entry_points
from aid_gui.app import main

def test_entry_point_registered():
    eps = {e.name: e.value for e in entry_points(group="console_scripts")}
    assert eps.get("aid") == "aid_gui.app:main"

def test_main_returns_zero():
    # do not exec event loop in CI; call with --help style if added
    assert callable(main)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd Python && python -m pytest tests/test_gui_entry.py -v
```

Expected FAIL.

- [ ] **Step 3: Write minimal implementation**

`app.main()` builds `QApplication`, shows `MainWindow`, runs loop. Settings menu items from spec §14 as disabled stubs.

- [ ] **Step 4: Run test to verify it passes**

```bash
cd Python && python -m pytest tests/test_gui_entry.py -v
```

Expected PASS.

- [ ] **Step 5: Commit**

`feat: aid console entry point and Settings stubs`

---

### Task 62: End-to-end verification and docs 1.0.0

**Files:**
- Modify: `README.md`, `UPDATES.md`
- Test: `Python/tests/test_e2e_primary.py`

**Interfaces:**
- Consumes: full stack Tasks 1–61
- Produces: `UPDATES.md` entry `1.0.0 - Python AID GUI and solver parity`

- [ ] **Step 1: Write the failing test**

```python
# Python/tests/test_e2e_primary.py
import subprocess
import pytest
from aid.paths import matlab_code

MATLAB = "/home/valentin/ProgramFiles/MB2025b/bin/matlab"

def test_matlab_batch_cessna_still_ok():
    r = subprocess.run(
        [MATLAB, "-batch", f"cd('{matlab_code()}'); run_aid_batch('Cessna 172')"],
        capture_output=True, text=True, timeout=600,
    )
    assert r.returncode == 0

def test_python_primary_compare_suite():
    r = subprocess.run(
        ["python", "-m", "pytest", "tests/test_compare_primary.py", "tests/test_gui_window.py", "-q"],
        cwd=matlab_code().parents[2] / "Python",
    )
    assert r.returncode == 0
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd Python && python -m pytest tests/test_e2e_primary.py -v
```

Expected FAIL until full stack complete.

- [ ] **Step 3: Write minimal implementation**

Update README with MATLAB batch + `pip install -e .` + `aid` launch commands. Bump `UPDATES.md` to `1.0.0`.

- [ ] **Step 4: Run test to verify it passes**

```bash
cd Python && python -m pytest tests/test_e2e_primary.py -v
```

Expected PASS.

- [ ] **Step 5: Commit**

`release: 1.0.0 Python AID GUI and solver parity`

---

## Task index (62 tasks)

| Range | Theme |
|-------|-------|
| 1–4 | Toolchain docs + DATCOM compile/wrapper/smoke |
| 5–6 | Model decode + Cessna .mat gold |
| 7–11 | AVL build + smoke |
| 12–16 | MATLAB Linux patches + batch helpers |
| 17–21 | MATLAB gold dumps (Cessna per-solver, primary, all 23) |
| 22–27 | Python package, JSONC, mat converter |
| 28–31 | Atmosphere, geometry, drag |
| 32–39 | DATCOM writer (by namelist) + parse + run |
| 40–45 | Tornado I/O + VLM (lattice, boundary, ISA, solver, coeff) |
| 46–52 | AVL parse/write/run + compare + run_all |
| 53–61 | PySide6 GUI (shell, menus, tabs, 3D, Analyze) |
| 62 | E2E + docs 1.0.0 |

## Self-review

- **Count:** 62 tasks (within 45–70).
- **Granularity:** Tornado split across Tasks 40–45; DATCOM writer split 32–37; GUI split 53–61; MATLAB gold split 17–21.
- **Independence:** Each task has its own test file and minimal surface area for Grok review between tasks.
- **No TBD:** Every task names exact paths, commands, and code stubs.
- **Concern:** Task 21 (all 23 models) is long-running; Task 45 (Tornado port) is the highest numerical risk — expect multiple review cycles. Task 22 (`models_dir`) must complete before Task 27 (`mat_to_jsonc`).
