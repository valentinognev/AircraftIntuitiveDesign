# Handbook, Airfoil, and Tornado Extra Port

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan. Wave 1 tasks run as **parallel** subagents (the user asked for that). Wave 2 is one agent after every Wave 1 task has passed its tests. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Port the MATLAB handbook and Tornado extras that Python does not run yet, including a Python naca456, without changing default DATCOM, Tornado, or AVL coefficients.

**Architecture:** Each Wave 1 task owns new modules or one existing file and exposes a pure function. Nothing in Wave 1 edits `main_window.py`, `stability.py`, `menus.py`, `settings.py`, `UPDATES.md`, or `README.md`. Wave 2 calls those functions in the same order as `AID.m` (about lines 863–966) and after Tornado `coeff_create`. Viscous strip and neutral-point iteration stay off unless the user turns them on, so gold compares stay inviscid.

**Tech Stack:** Python 3.11+, NumPy, SciPy (`CubicSpline` / `interp1d` where MATLAB uses `spline`), PySide6, PyVista. Oracle binary: `/home/valentin/Projects/FlightSimulation/USAF_DATCOM/naca456/naca456` (Fortran source beside it). MATLAB sources under `Matlab/fsroot/code/`.

**Spec:** The Requirements section below. It is the spec; there is no second document.

## Global Constraints

- Do not `git commit` or `git push` unless the user explicitly asks in that session. Skip every commit step.
- Wave 1 must not edit `Python/src/aid/stability.py`, `Python/src/aid_gui/main_window.py`, `Python/src/aid_gui/menus.py`, `Python/src/aid_gui/settings.py`, `UPDATES.md`, or `README.md`.
- Do not change default Tornado, DATCOM, or AVL numbers. Viscous correction and neutral-point iteration are opt-in.
- Copy MATLAB numeric tables verbatim. Do not refit them.
- MATLAB 1-based `swp(row, end)` is Python `pt["swp"][row - 1, -1]` after `geometry()` (`geometry.py` builds a 4×n matrix: row 0 LE, row 1 c/4, row 2 c/2, row 3 TE).
- `Aero.m` propeller block (`isfield(PT,'Propeller')`) is a MATLAB TODO. Do not port it.
- `Panel_Method.m` figures and `msgbox` are not ported. Headless only.
- Profile-sketcher camera animation (30 `view` steps) is not ported.
- Tests from the repo: `cd Python && python -m pytest <path> -q`.
- Subagents and reviewers use Grok non-fast `grok-4.7-high` only.
- Keep the existing rudder-area fix in `handbook_controls.py`. `test_rudder_tau_uses_rudder_area_not_elevator_area` must stay green. Do not restore MATLAB `Controls.m` line 25 (`R.tau` interpolated on elevator area).

## Requirements

| ID | MATLAB | Python result |
|----|--------|----------------|
| R1 | `/home/valentin/Projects/FlightSimulation/USAF_DATCOM/naca456/*.f90` | `aid.naca456.ordinates` matches the Fortran binary's `naca.gnu` |
| R2 | `NACA_Panel_Maker.m` 4- and 5-digit, `Panel_Method.m`, `Coefficients.m`, `Panel_Points.m`, `Lift_Curve_Slope.m` | Cosine-spaced ordinates and 2D vortex panel `a0`, `alpha0`, `Cm_ac` |
| R3 | `Aero.m` through the `x_ac` assignment (line 494) and `a *= pi/180` (line 497) | `aid.aero.aero` |
| R4 | `Drag.m` plus `AID.m` CD0 sum and `* 1.25` | `aid.drag.aircraft_cd0` |
| R5 | `Longitudinal_Static_Stability.m` `trim == 2` | `aid.trim.trim_incidence` |
| R6 | `Controls.m` live assignments (`tau`, `Kb`, `x_ac`, `l`) | `stamp_control_geometry` writes those fields; probe rows stay as they are |
| R7 | `Lat_Dir_Corrections.m`, `Lateral_Static_Stability.m`, `Lateral_Dynamic_Stability.m` | `aid.lateral` |
| R8 | `Longitudinal_Dynamic_Stability.m` | `aid.longitudinal_dynamic.longitudinal_dynamic` |
| R9 | `Tornado/fFindstaticmargin.m` | `aid.tornado.static_margin.find_static_margin` |
| R10 | `AID.m` Cp `fill3` after Tornado | `AircraftView.paint_cp` |
| R11 | `Profile_Sketcher.m` station edit, symmetry, smooth | Pure edits plus a side/top dialog |
| R12 | `Tornado/fViscCorr2.m`, `Tornado/fPablo.m` | `aid.tornado.viscous.viscous_correction` |
| R13 | Wire R1–R12 into the GUI handbook pass and Tornado analyze | Wave 2 only |

## Parallel dispatch

Wave 1 agents share no files. Dispatch all twelve together. Review each when it returns. Start Wave 2 only after all twelve test commands pass.

| Task | Owns | Must not touch |
|------|------|----------------|
| 1 naca456 | `Python/src/aid/naca456/`, `Python/tests/test_naca456_ordinates.py` | `naca_ordinates.py`, `panel_method.py` |
| 2 Panel + 4/5-digit | `Python/src/aid/naca_ordinates.py`, `Python/src/aid/panel_method.py`, `Python/src/aid/panel_points.py`, `Python/tests/test_naca_ordinates.py`, `Python/tests/test_panel_method.py` | `aid/naca456/` |
| 3 Aero | `Python/src/aid/aero.py`, `Python/tests/test_aero.py` | |
| 4 Drag buildup | `Python/src/aid/drag.py`, `Python/tests/test_aircraft_cd0.py` | `stability.py` |
| 5 Incidence trim | `Python/src/aid/trim.py`, `Python/tests/test_trim_incidence.py` | `stability.py` |
| 6 Control stamps | `Python/src/aid/handbook_controls.py`, `Python/tests/test_control_stamp.py` | Do not change probe formulas that existing tests lock |
| 7 Lateral handbook | `Python/src/aid/lateral.py`, `Python/tests/test_lateral.py` | |
| 8 Longitudinal dynamic | `Python/src/aid/longitudinal_dynamic.py`, `Python/tests/test_longitudinal_dynamic.py` | |
| 9 Tornado neutral point | `Python/src/aid/tornado/static_margin.py`, `Python/tests/test_tornado_static_margin.py` | `coeff.py`, `solver.py`, `lattice.py` |
| 10 Cp paint | `Python/src/aid_gui/view3d.py`, `Python/tests/test_gui_cp_paint.py` | `profile_sketcher.py`, `profile_sketch.py` |
| 11 Fuselage sketch | `Python/src/aid/profile_edit.py`, `Python/src/aid_gui/profile_sketch_dialog.py`, `Python/tests/test_profile_edit.py` | `view3d.py`. Leave the station-table dialog in `profile_sketcher.py` in place |
| 12 Viscous strip | `Python/src/aid/tornado/pablo.py`, `Python/src/aid/tornado/viscous.py`, `Python/tests/test_pablo.py`, `Python/tests/test_tornado_viscous.py` | `coeff.py` |

---

### Task 1: naca456 ordinates

**Files:**
- Create: `Python/src/aid/naca456/__init__.py`
- Create: `Python/src/aid/naca456/ordinates.py` (and sibling modules split by Fortran file: `splprocs.f90` → spline, `nacax.f90` → thickness, `epspsi.f90` / `avd.f90` → camber and combination)
- Test: `Python/tests/test_naca456_ordinates.py`

**Interfaces:**
- Consumes: nothing from this repo
- Produces:

```python
@dataclass(frozen=True)
class NacaSpec:
    name: str
    profile: str   # Fortran legal: '4', '4M', '6', '6A'
    camber: str    # '0', '2', '3', '3R', '6', '6A'
    toc: float
    cl: float = 0.0
    dencode: int = 3
    a: float = 1.0
    cmax: float = 0.0
    xmaxc: float = 0.0
    chord: float = 1.0

def ordinates(spec: NacaSpec) -> np.ndarray:
    """(N, 2) x,y in naca.gnu order. First half upper, second half lower, same split as floor(N/2) in NACA_Panel_Maker.m."""
```

`ordinates` must not call the binary. The test may.

- [ ] **Step 1: Write the failing test**

```python
import os
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import pytest

from aid.naca456 import NacaSpec, ordinates

BINARY = Path("/home/valentin/Projects/FlightSimulation/USAF_DATCOM/naca456/naca456")

def _gnu(spec: NacaSpec) -> np.ndarray:
    namelist = (
        "&NACA\n"
        f"NAME='{spec.name}',\n"
        f"PROFILE='{spec.profile}',\n"
        f"CAMBER='{spec.camber}',\n"
        f"TOC={spec.toc:.4f},\n"
        f"CL={spec.cl:.4f},\n"
        f"A={spec.a:.4f},\n"
        f"CMAX={spec.cmax:.4f},\n"
        f"XMAXC={spec.xmaxc:.4f},\n"
        f"CHORD={spec.chord:.4f},\n"
        f"DENCODE={spec.dencode},\n"
        "/\n"
    )
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "naca.in"
        path.write_text(namelist)
        subprocess.run([str(BINARY), str(path)], cwd=tmp, check=True, capture_output=True)
        return np.loadtxt(Path(tmp) / "naca.gnu")

@pytest.mark.skipif(not BINARY.is_file() or not os.access(BINARY, os.X_OK), reason="naca456 binary missing")
@pytest.mark.parametrize("spec", [
    NacaSpec(name="NACA 2412", profile="4", camber="2", toc=0.12, cmax=0.02, xmaxc=0.4),
    NacaSpec(name="NACA 64-210", profile="6", camber="6", toc=0.10, cl=0.2, a=0.4),
])
def test_ordinates_match_fortran_gnu(spec):
    got = ordinates(spec)
    ref = _gnu(spec)
    assert got.shape == ref.shape
    assert np.allclose(got, ref, atol=1e-4)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd Python && python -m pytest tests/test_naca456_ordinates.py -q`
Expected: FAIL with import error for `aid.naca456`

- [ ] **Step 3: Write minimal implementation**

Translate the Fortran that fills `naca.gnu` (`ReadDataAndMakeAirfoils` and the included `splprocs.f90`, `epspsi.f90`, `nacax.f90`, `avd.f90`). Public surface is only `NacaSpec` and `ordinates`. Drop the welcome banner and the `.dbg` / `.out` printers. `dencode=3` must emit the same point count as the binary.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd Python && python -m pytest tests/test_naca456_ordinates.py -q`
Expected: PASS (or skip only if the binary is not executable)

- [ ] **Step 5: Commit**

Skip unless the user asked to commit.

---

### Task 2: 4/5-digit ordinates and 2D panel

**Files:**
- Create: `Python/src/aid/naca_ordinates.py`
- Create: `Python/src/aid/panel_method.py`
- Create: `Python/src/aid/panel_points.py`
- Test: `Python/tests/test_naca_ordinates.py`
- Test: `Python/tests/test_panel_method.py`

**Interfaces:**
- Consumes: nothing from Task 1. Six-series is Wave 2.
- Produces:

```python
def naca4_ordinates(code: str, n_pts: int) -> np.ndarray:
    """Cosine spacing, shape (n_pts, 2). Closed loop: lower TE→LE then upper LE→TE, matching NACA_Panel_Maker.m lines 149-158. code length 4."""

def naca5_ordinates(code: str, n_pts: int) -> np.ndarray:
    """Same layout. code length 5. Families 210, 220, 230, 240, 250 only."""

def panel_method(data: np.ndarray, alpha_deg: np.ndarray) -> dict:
    """data is (M, 2) airfoil nodes, M-1 panels. alpha_deg length >= 2.
    Returns {'a0': float per rad, 'alpha0': float deg, 'Cm_ac': float, 'Cl': np.ndarray}.
    Port Panel_Method.m + Coefficients.m with plot_option forced off."""

def read_airfoil_file(path: Path) -> np.ndarray:
    """Port Panel_Points.m file read: two columns x,y. No GUI."""
```

- [ ] **Step 1: Write the failing test**

```python
import math
from pathlib import Path

import numpy as np
import pytest

from aid.naca_ordinates import naca4_ordinates, naca5_ordinates
from aid.panel_method import panel_method
from aid.panel_points import read_airfoil_file

def test_naca2412_thickness_and_closure():
    xy = naca4_ordinates("2412", 51)
    assert xy.shape == (51, 2)
    assert abs(xy[0, 0] - 1.0) < 1e-6
    assert abs(xy[-1, 0] - 1.0) < 1e-6
    # Camber rotates a 12% section; thickness stays within 0.02 of 0.12.
    assert float(xy[:, 1].max() - xy[:, 1].min()) == pytest.approx(0.12, abs=0.02)

def test_naca23012_has_positive_camber():
    xy = naca5_ordinates("23012", 41)
    assert xy.shape == (41, 2)
    assert float(xy[:, 1].max()) > 0.02

def test_symmetric_0012_panel_alpha0_near_zero():
    xy = naca4_ordinates("0012", 81)
    out = panel_method(xy, np.linspace(-4.0, 8.0, 7))
    assert abs(out["alpha0"]) < 0.5
    assert 5.5 < out["a0"] < 7.0  # per rad, near 2*pi
    assert abs(out["Cm_ac"]) < 0.02

def test_read_airfoil_file_two_columns(tmp_path: Path):
    p = tmp_path / "foil.dat"
    p.write_text("1.0 0.0\n0.0 0.0\n1.0 0.0\n")
    xy = read_airfoil_file(p)
    assert xy.shape == (3, 2)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd Python && python -m pytest tests/test_naca_ordinates.py tests/test_panel_method.py -q`
Expected: FAIL with import error

- [ ] **Step 3: Write minimal implementation**

Port `NACA_Panel_Maker.m` lines 13–80 and 149–158 for digit length 4 and 5 only. `n=1000` dense stations, then cosine `x = 0.5 - cos(angle)/2` with `angle = linspace(0, pi, floor(n_pts/2)+1)`, then the flip layout on lines 156–158. Raise `ValueError` for any other length.

Port `Coefficients.m` and the solve loop in `Panel_Method.m` (source + vortex, `A @ gamma = B`). `a0` is the slope of Cl versus alpha in radians. `alpha0` is the zero-lift intercept in degrees. `Cm_ac` is the moment about the quarter chord, averaged the way `Panel_Method.m` does for a multi-alpha call. No figures.

`read_airfoil_file` loads whitespace-separated `x y` and returns float64 `(N, 2)`.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd Python && python -m pytest tests/test_naca_ordinates.py tests/test_panel_method.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

Skip unless the user asked to commit.

---

### Task 3: 3D lift slope, twist, aerodynamic center

**Files:**
- Create: `Python/src/aid/aero.py`
- Test: `Python/tests/test_aero.py`

**Interfaces:**
- Consumes: a planform dict that already has `geometry()` fields plus `a0`, `alpha0`, `Cm_ac`. Does not call the panel method.
- Produces:

```python
def aero(pt: dict, mach: float, angl: bool) -> dict:
    """Mutates pt. Sets a (scalar, after the MATLAB pi/180 scale), alpha0L (scalar degrees),
    Cm (scalar), x_ac (MATLAB line 494). Copies Aero.m lines 1-497 except the Propeller block.
    swp row k in MATLAB is pt['swp'][k-1, -1]."""
```

- [ ] **Step 1: Write the failing test**

```python
import math

import numpy as np

from aid.aero import aero

def test_unswept_ar6_helmbold_then_pi_over_180():
    # Aero.m: a = 2*pi*AR/(2+sqrt(AR^2+4)) at M=0, then a *= pi/180.
    # a0 >= 1 is left as per rad, so k = a0/(2*pi) = 1.
    ar = 6.0
    raw = 2 * math.pi * ar / (2 + math.sqrt(ar**2 + 4))
    pt = {
        "a0": [2 * math.pi],
        "alpha0": [0.0],
        "Cm_ac": [0.0],
        "AR": [ar],
        "TR": [1.0],
        "swp": np.zeros((4, 1)),
        "TC": 0.12,
        "TWISTA": 0.0,
        "CHRDR": 1.0,
        "xmac": 0.25,
        "cbar": [1.0],
        "SSPNOP": 0.0,
        "DHDADI": 0.0,
        "DHDADO": 0.0,
        "SSPN": 3.0,
    }
    out = aero(pt, mach=0.0, angl=False)
    assert abs(float(np.asarray(out["a"]).reshape(-1)[-1]) - raw * math.pi / 180) < 1e-9
    assert abs(float(np.asarray(out["alpha0L"]).reshape(-1)[-1])) < 1e-8

def test_zero_twist_keeps_alpha0():
    pt = {
        "a0": [2 * math.pi, 2 * math.pi],
        "alpha0": [-2.0, -1.0],
        "Cm_ac": [-0.04, -0.04],
        "AR": [8.0],
        "TR": [0.5],
        "swp": np.zeros((4, 1)),
        "TC": 0.12,
        "TWISTA": 0.0,
        "CHRDR": 5.0,
        "xmac": 0.4,
        "cbar": [4.0],
        "SSPNOP": 0.0,
        "DHDADI": 0.0,
        "DHDADO": 0.0,
        "SSPN": 10.0,
    }
    out = aero(pt, mach=0.2, angl=False)
    # mean of the two section alpha0 values when twist correction is zero
    assert abs(float(out["alpha0L"]) - (-1.5)) < 1e-6
    assert "x_ac" in out
```

If `TWISTA == 0` still multiplies by a Mach factor that is not 1, assert the factor from the DATCOM table instead of `-1.5`, and document the factor in the test name. The Helmbold assertion must stay exact.

- [ ] **Step 2: Run test to verify it fails**

Run: `cd Python && python -m pytest tests/test_aero.py -q`
Expected: FAIL with import error

- [ ] **Step 3: Write minimal implementation**

Port `Aero.m` lines 1–497. Include the DATCOM twist tables for `alpha0L` and `Cm`, and the aerodynamic-center table ending at line 494. Use SciPy spline interpolation where MATLAB calls `interp1(...,'spline')`, and linear where it calls `'linear'`. Convert `a0 < 1` with `* 180/pi` before `k = a0/(2*pi)`, matching lines 5–8. Finish with `pt["a"] = pt["a"] * math.pi / 180`. Do not port lines 499–598.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd Python && python -m pytest tests/test_aero.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

Skip unless the user asked to commit.

---

### Task 4: Parasite drag buildup

**Files:**
- Modify: `Python/src/aid/drag.py`
- Test: `Python/tests/test_aircraft_cd0.py`

**Interfaces:**
- Consumes: existing `drag(pt, unit, atm, wg_sref)`
- Produces:

```python
def aircraft_cd0(ac: Aircraft) -> float:
    """AID.m lines 882-902. Sum Drag() over wing, HT, VT, body, NP, NB when plot_cmp (and extra slots) are on.
    Twin if NP.Y or NB.Y0 is truthy. Return 1.25 * sum. Writes each part['CD0']."""
```

`plot_cmp` indexes: 0 wing, 1 HT, 2 VT, 3 body. Extra planforms use slots 0–3 when that dict is non-empty. Extra bodies use slots 0–1. Match `AID.m`: wing/HT/VT/body follow `plot_cmp`; NP/NB are included when the dict is non-empty (the MATLAB GUI also checks a checkbox; treat a non-empty dict as checked).

- [ ] **Step 1: Write the failing test**

```python
import numpy as np

from aid.aircraft import Aircraft, load_mat
from aid.atmosphere import atmosphere
from aid.drag import aircraft_cd0, drag
from aid.paths import matlab_code

def test_cessna_cd0_is_interference_times_component_sum():
    ac = load_mat(matlab_code() / "Models" / "Cessna 172.mat")
    total = aircraft_cd0(ac)
    atm = atmosphere(float(np.asarray(ac.AERO["ALT"]).reshape(-1)[0]))
    sref = float(np.asarray(ac.WG["S"]).reshape(-1)[-1])
    parts = [drag(dict(ac.WG), ac.unit, atm, sref)["CD0"]]
    if ac.plot_cmp[1]:
        parts.append(drag(dict(ac.HT), ac.unit, atm, sref)["CD0"])
    if ac.plot_cmp[2]:
        parts.append(drag(dict(ac.VT), ac.unit, atm, sref)["CD0"])
    if ac.plot_cmp[3]:
        parts.append(drag(dict(ac.BD), ac.unit, atm, sref)["CD0"])
    assert abs(total - 1.25 * sum(parts)) < 1e-9

def test_wing_off_drops_wing_cd0():
    ac = load_mat(matlab_code() / "Models" / "Cessna 172.mat")
    ac.plot_cmp[0] = 0
    on = aircraft_cd0(ac)
    ac.plot_cmp[0] = 1
    both = aircraft_cd0(ac)
    assert both > on
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd Python && python -m pytest tests/test_aircraft_cd0.py -q`
Expected: FAIL with `aircraft_cd0` missing

- [ ] **Step 3: Write minimal implementation**

Add `aircraft_cd0` to `drag.py`. Build `atm` with `atmosphere(ALT)` and set `atm["Re"]`, `atm["Q"]` the way `AID.m` lines 877–880 do before `Drag`. Call existing `drag` per included component. Do not edit `stability.py` (it still sums stored `CD0` until Wave 2).

- [ ] **Step 4: Run test to verify it passes**

Run: `cd Python && python -m pytest tests/test_aircraft_cd0.py tests/test_drag_cessna.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

Skip unless the user asked to commit.

---

### Task 5: Incidence trim

**Files:**
- Create: `Python/src/aid/trim.py`
- Test: `Python/tests/test_trim_incidence.py`

**Interfaces:**
- Consumes: planform fields `a`, `alpha0L`, `i`, `Cm`, `x_ac`, `cbar`, `S`, HT `eta`, `dwash`, `l`, flap/elevator `DELTA`, `tau`, `l`
- Produces:

```python
def trim_incidence(ac: Aircraft, *, htail: bool, body: bool, fix: str) -> dict:
    """fix is 'both', 'wing', or 'ht' (Longitudinal_Static_Stability.m trim == 2).
    'both': solve i_wg and i_ht with aoa fixed at ALSCHD[0].
    'wing': i_ht fixed at HT['i'], solve i_wg and aoa.
    'ht': i_wg fixed at WG['i'], solve i_ht and aoa.
    Returns {'i_wg': float, 'i_ht': float, 'alpha': float, 'error': int}.
    Non-finite or abs(incidence) > 60 sets that incidence to 0 and error to 1 (wing) or 2 (ht). Non-finite alpha sets alpha to 0 and error to 3.
    Does not write back onto ac."""
```

Linear system, no SymPy. Let `aw` be wing `a` after the same `_per_deg` rule as `stability.py` (if `a > 1`, multiply by `pi/180`). `TLT = ht_a * eta * S_ht / S_w`. `CLa` and `Cma` use the same expressions as `aircraft_stability` (wing + tail term if `htail`, body `Cma` if `body`).

Lift, with scalar flap/elevator delta only:

```
CL0 = aw*(i_w - a0L) + flap + TLT*(i_h - dwash*(i_w - a0L)) + elev
flap = aw*F.DELTA*F.tau    if DELTA is a length-1 number else 0
elev = TLT*E.DELTA*E.tau   if DELTA is a length-1 number else 0
AC.CL == CL0 + CLa*aoa
```

Moment:

```
Cm0_wg = WG.Cm + aw*(i_w - a0L)*(x_cg - x_ac) - aw*F.DELTA*F.tau*F.l/cbar
Cm0_ht = -(HT.l)/cbar * (TLT*(i_h - dwash*(i_w - a0L)) + elev)
0 == Cm0_wg + Cm0_ht + (BD.Cm0 if body else 0) + Cma*aoa
```

`x_cg = (XCG - WG.X - xmac) / cbar`. `AC.CL = WT / (q * S)` with `q` from `atmosphere` the same way `aircraft_stability` does.

- [ ] **Step 1: Write the failing test**

`x_cg = 0.25` and `x_ac = 0.25`, so the wing moment arm is 0 and `Cma = -TLT * l / cbar = -0.04`. Return `CL` from `trim_incidence` so the residual can be checked. Also keep the 60-degree guard test.

```python
from aid.aircraft import Aircraft
from aid.trim import trim_incidence

def _craft() -> Aircraft:
    return Aircraft(
        WG={"a": 0.1, "alpha0L": 0.0, "i": 0.0, "Cm": 0.0, "x_ac": 0.25,
            "cbar": [1.0], "S": [10.0], "X": 0.0, "xmac": 0.0, "Z": 0.0},
        HT={"a": 0.1, "S": [2.0], "eta": 1.0, "dwash": 0.0, "l": 2.0, "i": 0.0,
            "cbar": [1.0], "x_ac": 0.25, "X": 0.0, "xmac": 0.0},
        VT={},
        F={"DELTA": 0.0, "tau": 0.0, "l": 0.0},
        A={},
        E={"DELTA": 0.0, "tau": 0.0},
        R={},
        BD={"Cm0": 0.0, "Cma": 0.0},
        NP=[], NB=[],
        AERO={"ALSCHD": [2.0], "ALT": [0.0], "MACH": [0.1], "WT": 500.0, "XCG": 0.25, "ZCG": 0.0},
        plot_cmp=[1, 1, 1, 0], unit="ft",
    )

def test_both_free_lift_and_moment_residuals_are_zero():
    ac = _craft()
    out = trim_incidence(ac, htail=True, body=False, fix="both")
    assert out["error"] == 0
    assert abs(out["alpha"] - 2.0) < 1e-9
    aw, tlt = 0.1, 0.02
    cl0 = aw * out["i_wg"] + tlt * out["i_ht"]
    cla = 0.1 + tlt
    assert abs(out["CL"] - (cl0 + cla * out["alpha"])) < 1e-8
    cm0_ht = -2.0 * (tlt * out["i_ht"])
    cma = -tlt * 2.0
    assert abs(cm0_ht + cma * out["alpha"]) < 1e-8

def test_huge_weight_trips_the_sixty_degree_guard():
    ac = _craft()
    ac.WG["a"] = 1e-6
    ac.HT["a"] = 1e-6
    ac.AERO["WT"] = 1e9
    out = trim_incidence(ac, htail=True, body=False, fix="both")
    assert out["error"] != 0
    assert out["i_wg"] == 0.0 or out["i_ht"] == 0.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd Python && python -m pytest tests/test_trim_incidence.py -q`
Expected: FAIL with import error

- [ ] **Step 3: Write minimal implementation**

Solve the 2×2 or 3×3 linear system with `numpy.linalg.solve`. Return the dict described above, including `CL`. Apply the 60-degree and non-finite guards from `Longitudinal_Static_Stability.m` lines 95–97.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd Python && python -m pytest tests/test_trim_incidence.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

Skip unless the user asked to commit.

---

### Task 6: Stamp control geometry

**Files:**
- Modify: `Python/src/aid/handbook_controls.py`
- Test: `Python/tests/test_control_stamp.py`

**Interfaces:**
- Consumes: existing `_tau`, `_aileron_kb`, `_control_area`, `_per_deg`
- Produces:

```python
def stamp_control_geometry(ac: Aircraft) -> None:
    """Write the Controls.m fields the trim equations read.
    F['tau'], F['x_ac'], F['l'] with l = x_ac_flap - x_cg and
    x_ac_flap = cbar - 0.5*(CHRDFI+CHRDFO).
    E['tau'] from elevator area / HT.S.
    R['tau'] from rudder area / VT.S (keep the existing fix; do not use elevator area).
    A['Kb'] from _aileron_kb.
    x_cg is (AERO.XCG - WG.X - xmac) / cbar when those keys exist, else WG['x_cg'] if present, else 0.25.
    Skip a surface whose span is illegal; leave its fields unchanged."""
```

Do not change `handbook_controls` probe values. Existing `tests/test_handbook_controls.py` must still pass.

- [ ] **Step 1: Write the failing test**

```python
from aid.aircraft import Aircraft
from aid.handbook_controls import stamp_control_geometry

def test_flap_tau_and_lever_are_written():
    ac = Aircraft(
        WG={"a": 0.1, "S": [20.0], "cbar": [2.0], "b": 10.0, "SSPN": 5.0, "TR": 1.0,
            "X": 1.0, "xmac": 0.5},
        HT={"a": 0.08, "S": [4.0], "eta": 0.9, "l": 8.0},
        VT={"a": 0.05, "S": [2.0], "k": 1.0, "swash": 1.0, "h": 1.0, "l": 8.0},
        F={"SPANFI": 0.0, "SPANFO": 2.0, "CHRDFI": 0.4, "CHRDFO": 0.4},
        A={"SPANFI": 3.0, "SPANFO": 4.5, "CHRDFI": 0.3, "CHRDFO": 0.25},
        E={"SPANFI": 0.0, "SPANFO": 1.0, "CHRDFI": 0.4, "CHRDFO": 0.4},
        R={"SPANFI": 0.0, "SPANFO": 1.0, "CHRDFI": 0.4, "CHRDFO": 0.4},
        BD={}, NP=[], NB=[],
        AERO={"XCG": 2.0}, plot_cmp=[1, 1, 1, 1], unit="ft",
    )
    stamp_control_geometry(ac)
    # area = 0.5*(0.4+0.4)*(2-0) = 0.8; ratio = 0.8/20 = 0.04 → tau table clamps toward 0.1 bin
    assert ac.F["tau"] > 0.0
    assert abs(ac.F["x_ac"] - (2.0 - 0.4)) < 1e-12
    # x_cg = (2.0 - 1.0 - 0.5) / 2.0 = 0.25
    assert abs(ac.F["l"] - (ac.F["x_ac"] - 0.25)) < 1e-12
    assert "Kb" in ac.A
    assert ac.E["tau"] > 0.0
    assert ac.R["tau"] > 0.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd Python && python -m pytest tests/test_control_stamp.py -q`
Expected: FAIL with `stamp_control_geometry` missing

- [ ] **Step 3: Write minimal implementation**

Add the function next to `handbook_controls`. Use the same `_tau` and `_aileron_kb` helpers. Do not write `AC.Clda`. Aileron yaw stays omitted (`Cn` on the aileron probe stays `None`).

- [ ] **Step 4: Run test to verify it passes**

Run: `cd Python && python -m pytest tests/test_control_stamp.py tests/test_handbook_controls.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

Skip unless the user asked to commit.

---

### Task 7: Lateral-directional handbook

**Files:**
- Create: `Python/src/aid/lateral.py`
- Test: `Python/tests/test_lateral.py`

**Interfaces:**
- Consumes: geometry fields, `BD`, `AERO.MACH`, wing `CL` via `AC` equivalent argument
- Produces:

```python
def lat_dir_corrections(ac: Aircraft, mach: float) -> dict:
    """Port Lat_Dir_Corrections.m. Writes VT['AReff'] and BD['Cnb'].
    Returns {'Clb_wing': float} which is ClB_sweep+ClB_AR+ClB_twist+ClB_dihedral (line 448)."""

def lateral_static(ac: Aircraft, angl: bool, cl: float) -> dict:
    """Port Lateral_Static_Stability.m. Writes VT['a'], VT['k'], VT['swash'], VT['h'], VT['l'].
    Returns {'CYb': float, 'Cnb': float, 'Clb': float, 'Clda': 0.1, 'Cnda': 0.1}."""

def lateral_dynamic(ac: Aircraft, cl: float, cyb: float) -> dict:
    """Port Lateral_Dynamic_Stability.m.
    Returns CYp, CYr, Clp, Clr, Cnp, Cnr."""
```

`lateral_static` must call the same `k`, `Avb_Av`, `Kh` tables that are in `Lateral_Static_Stability.m` lines 37–80, not the `Lat_Dir_Corrections` effective-AR tables. Those stay inside `lat_dir_corrections`. `Clb` adds `Clb_wing` to the fuselage and VT terms on lines 106–107.

- [ ] **Step 1: Write the failing test**

```python
import math

from aid.aircraft import Aircraft
from aid.lateral import lateral_dynamic, lateral_static

def _lat() -> Aircraft:
    return Aircraft(
        WG={"a": 0.1, "S": [20.0], "cbar": [2.0], "b": 10.0, "AR": [5.0], "TR": [1.0],
            "swp": __import__("numpy").zeros((4, 1)), "gamma": 0.0, "SSPN": 5.0,
            "Z": 1.0, "X": 4.0, "CHRDR": 2.0, "x_ac": 0.25, "xmac": 0.5, "CL": 0.4},
        HT={"a": 0.08, "a0": [6.0], "S": [4.0], "Z": 1.0, "DHDADI": 0.0, "DHDADO": 0.0,
            "SSPNOP": 0.0, "SSPN": 2.0},
        VT={"AR": [1.5], "TR": [0.6], "S": [2.0], "b": 2.0, "Z": 0.5, "X": 10.0,
            "cbar": [1.0], "xmac": 0.3, "ymac": 0.4},
        F={}, A={}, E={}, R={},
        BD={"X": [0.0, 5.0, 12.0], "ZU": [0.2, 0.8, 0.3], "ZL": [-0.2, -0.6, -0.2],
            "R": [0.2, 0.7, 0.25], "S": [0.1, 1.5, 0.2], "NX": 3, "dk": 1.0, "d_eq": 1.0,
            "Cnb": 0.0},
        NP=[], NB=[],
        AERO={"MACH": [0.2], "ZCG": 0.0, "XCG": 4.5},
        plot_cmp=[1, 1, 1, 1], unit="ft",
    )

def test_static_placeholders_are_point_one():
    out = lateral_static(_lat(), angl=True, cl=0.4)
    assert out["Clda"] == 0.1
    assert out["Cnda"] == 0.1
    assert "CYb" in out and "Clb" in out and "Cnb" in out

def test_dynamic_matches_closed_form():
    ac = _lat()
    ac.VT["a"] = 0.05
    ac.VT["swash"] = 1.0
    ac.VT["S"] = [2.0]
    ac.VT["l"] = 4.0
    ac.VT["h"] = 1.0
    ac.VT["hp"] = 1.0
    ac.WG["a"] = 0.1
    ac.WG["TR"] = [1.0]
    ac.WG["AR"] = [5.0]
    ac.WG["swp"] = __import__("numpy").zeros((4, 1))
    ac.WG["b"] = 10.0
    ac.WG["S"] = [20.0]
    out = lateral_dynamic(ac, cl=0.4, cyb=-0.01)
    # Clp = -a/12 * (1+3*TR)/(1+TR) = -0.1/12 * 4/2
    assert abs(out["Clp"] - (-0.1 / 12 * 2)) < 1e-12
    # Cnr = -2*a*swash*Sv/Sw*(l/b)^2
    expect = -2 * 0.05 * 1.0 * 2.0 / 20.0 * (4.0 / 10.0) ** 2
    assert abs(out["Cnr"] - expect) < 1e-12
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd Python && python -m pytest tests/test_lateral.py -q`
Expected: FAIL with import error

- [ ] **Step 3: Write minimal implementation**

Port the three MATLAB files. Copy every lookup table in `Lat_Dir_Corrections.m` verbatim (the file is about 550 lines). `lateral_dynamic` is `Lateral_Dynamic_Stability.m` in full (16 lines). V-tail projection at the top of `Lateral_Static_Stability.m` stays: if the body component flag is off and the HT has dihedral, VT geometry is replaced by the projected HT before the derivatives. Pass that flag as `body_on: bool` added to `lateral_static` if `plot_cmp[3]` is the MATLAB `plt(4)` check (`~plt(4)` means body checkbox off). Use `ac.plot_cmp[3]` inside the function so the signature stays `(ac, angl, cl)`.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd Python && python -m pytest tests/test_lateral.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

Skip unless the user asked to commit.

---

### Task 8: Longitudinal dynamic stability

**Files:**
- Create: `Python/src/aid/longitudinal_dynamic.py`
- Test: `Python/tests/test_longitudinal_dynamic.py`

**Interfaces:**
- Consumes: a dict of handbook scalars, not the GUI
- Produces:

```python
def longitudinal_dynamic(state: dict) -> dict:
    """Port Longitudinal_Dynamic_Stability.m including the prop=1 branch
    (CXu = -CDu - 3*CD) and the 4x4 A, 4x1 B, short-period and phugoid eigenvalues.
    Returns keys: A (4,4), B (4,1), short_period (2,), phugoid (2,),
    Xu, Xa, Zu, Za, Mu, Ma, Mq, Madot, CDu, CDa, CLu, CLadot, CLq, CD, CL.
    state keys: WT, YI, MACH, ALT, Q, a_sound, S, cbar, CD0, K, CL, CLa, Cma,
    CLde, Cmde, ht_a, eta, ht_V, dwash, ht_l.
    CDu = 0, CXadot = 0, CXq = 0, CXt = 0, CXde = 0, CZt = 0, Cmu = 0. g = 32.17."""
```

- [ ] **Step 1: Write the failing test**

```python
import math

import numpy as np

from aid.longitudinal_dynamic import longitudinal_dynamic

def test_cxu_uses_three_cd_for_prop():
    cd0, k, cl = 0.02, 0.05, 0.5
    cd = cd0 + k * cl**2
    cda = 2 * k * cl * 0.08
    out = longitudinal_dynamic({
        "WT": 3217.0, "YI": 1000.0, "MACH": 0.2, "ALT": 0.0,
        "Q": 50.0, "a_sound": 1000.0, "S": 20.0, "cbar": 2.0,
        "CD0": cd0, "K": k, "CL": cl, "CLa": 0.08, "Cma": -0.01,
        "CLde": 0.01, "Cmde": -0.02, "ht_a": 0.07, "eta": 0.9,
        "ht_V": 0.5, "dwash": 0.4, "ht_l": 8.0,
    })
    # CXu = -0 - 3*CD; Xu = CXu * Q * S / (m * U); m = WT/32.17; U = M*a
    cxu = -3 * cd
    m = 3217.0 / 32.17
    u = 0.2 * 1000.0
    expect = cxu * 50.0 * 20.0 / (m * u)
    assert abs(out["Xu"] - expect) < 1e-9
    assert out["A"].shape == (4, 4)
    assert out["B"].shape == (4, 1)
    assert out["short_period"].shape == (2,)
    assert out["phugoid"].shape == (2,)
    assert np.all(np.isfinite(out["short_period"]))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd Python && python -m pytest tests/test_longitudinal_dynamic.py -q`
Expected: FAIL with import error

- [ ] **Step 3: Write minimal implementation**

Translate `Longitudinal_Dynamic_Stability.m` line for line. `CD = CD0 + K*CL^2`. `CDa = 2*K*CL*CLa`. Eigenvalues via `numpy.linalg.eigvals` on `Ashort` and `Aphu` as written on lines 113–120. No plots.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd Python && python -m pytest tests/test_longitudinal_dynamic.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

Skip unless the user asked to commit.

---

### Task 9: Tornado neutral-point iteration

**Files:**
- Create: `Python/src/aid/tornado/static_margin.py`
- Test: `Python/tests/test_tornado_static_margin.py`

**Interfaces:**
- Consumes: injectable runners, defaulting to `lattice_setup`, `solve`, `coeff_create`
- Produces:

```python
class StaticMarginError(RuntimeError):
    pass

def find_static_margin(geo: dict, state: dict, *, max_iter: int = 10, tol: float = 1e-5,
                       run=None) -> dict:
    """Port fFindstaticmargin.m. Mutates geo['ref_point'][0] during the iteration
    and leaves it at the converged aerodynamic center.
    run(geo, state) -> results dict with CL_a and Cm_a.
    Default run builds a lattice, solves, and calls coeff_create.
    Returns {'ac': np.ndarray shape (3,), 'h': np.ndarray shape (3,)}.
    h = (ac - CG) / C_mac from the last lattice ref.
    Raises StaticMarginError after max_iter without abs(Cm_a/CL_a) < tol.
    solvertype/mode passed to lattice_setup is 1, matching the MATLAB call."""
```

Newton step from the MATLAB file:

```
var = Cm_a / CL_a
step starts at 0.5
DvarDstep = (var1 - var0) / step
step = -var1 / DvarDstep
ref_point[0] += step
```

The first baseline uses `var0 = CL_a/Cm_a` (line 19) and later iterations use `var = Cm_a/CL_a` (line 35). Keep that inconsistency; it is the MATLAB code.

- [ ] **Step 1: Write the failing test**

```python
import numpy as np
import pytest

from aid.tornado.static_margin import StaticMarginError, find_static_margin

def test_newton_stops_when_cm_over_cl_is_tiny():
    geo = {"ref_point": np.array([1.0, 0.0, 0.0], dtype=float), "CG": np.array([0.5, 0.0, 0.0])}
    state = {}
    calls = {"n": 0}

    def run(g, s):
        calls["n"] += 1
        x = float(g["ref_point"][0])
        # Cm_a/CL_a = 0.2*(x-1.5) so the root is x=1.5. CL_a stays 1.
        return {"CL_a": 1.0, "Cm_a": 0.2 * (x - 1.5), "C_mac": 2.0}

    out = find_static_margin(geo, state, run=run)
    assert abs(out["ac"][0] - 1.5) < 1e-4
    assert abs(out["h"][0] - (1.5 - 0.5) / 2.0) < 1e-4
    assert calls["n"] < 10

def test_ten_misses_raise():
    geo = {"ref_point": np.array([0.0, 0.0, 0.0], dtype=float), "CG": np.zeros(3)}

    def run(g, s):
        return {"CL_a": 1.0, "Cm_a": 1.0, "C_mac": 1.0}

    with pytest.raises(StaticMarginError):
        find_static_margin(geo, state={}, run=run)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd Python && python -m pytest tests/test_tornado_static_margin.py -q`
Expected: FAIL with import error

- [ ] **Step 3: Write minimal implementation**

Implement the loop from `fFindstaticmargin.m`. The default `run` calls `lattice_setup(geo, state, 1)`, `solve`, `coeff_create`. The unit tests pass `run`, so they must not build a lattice. Store `C_mac` from `run()`'s return if present, else from the lattice `ref` the default runner sees. For the injected runner, read `results["C_mac"]`.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd Python && python -m pytest tests/test_tornado_static_margin.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

Skip unless the user asked to commit.

---

### Task 10: Tornado Cp on the 3D view

**Files:**
- Modify: `Python/src/aid_gui/view3d.py`
- Test: `Python/tests/test_gui_cp_paint.py`

**Interfaces:**
- Consumes: PyVista plotter already on `AircraftView`
- Produces:

```python
def paint_cp(self, xyz: np.ndarray, cp: np.ndarray) -> None:
    """xyz (npan, 4, 3) corner points, cp (npan,). Adds mesh name 'tornado_cp'
    with cell scalars, clim (min(cp), max(cp)), scalar bar title 'Cp'.
    Replaces a previous tornado_cp mesh. Does not clear the aircraft mesh."""

def clear_cp(self) -> None:
    """Remove tornado_cp if present."""
```

MATLAB reference is `AID.m` lines 1789–1796: `fill3` of `lattice.XYZ` colored by `results.cp`, colorbar label `Cp`.

- [ ] **Step 1: Write the failing test**

```python
import os

import numpy as np
import pytest

pytestmark = pytest.mark.skipif(os.environ.get("QT_QPA_PLATFORM") != "offscreen" and not os.environ.get("DISPLAY"), reason="no display")

def test_paint_cp_adds_named_mesh(qtbot):
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from aid_gui.view3d import AircraftView
    view = AircraftView()
    qtbot.addWidget(view)
    xyz = np.array([[[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0]]], dtype=float)
    cp = np.array([-0.5])
    view.paint_cp(xyz, cp)
    names = [a.name for a in view._plotter.actors.values()] if hasattr(view._plotter, "actors") else []
    assert view.cp_painted() is True
    view.clear_cp()
    assert view.cp_painted() is False
```

Add `def cp_painted(self) -> bool` that is true when the `tornado_cp` actor exists. If `qtbot` is not installed, construct `QApplication` the way `tests/test_gui_context_isolate.py` does and follow that file's offscreen pattern instead of `qtbot`.

- [ ] **Step 2: Run test to verify it fails**

Run: `cd Python && QT_QPA_PLATFORM=offscreen python -m pytest tests/test_gui_cp_paint.py -q`
Expected: FAIL with `paint_cp` missing

- [ ] **Step 3: Write minimal implementation**

Build one quad per panel from `xyz` and color by `cp`. Name the actor `tornado_cp`. Set the scalar bar title to `Cp`. `clear_cp` removes only that actor. Do not call this from `run_tornado` (Wave 2 does).

- [ ] **Step 4: Run test to verify it passes**

Run: `cd Python && QT_QPA_PLATFORM=offscreen python -m pytest tests/test_gui_cp_paint.py tests/test_gui_context_isolate.py -q`
Expected: PASS. Context-menu tests must still pass.

- [ ] **Step 5: Commit**

Skip unless the user asked to commit.

---

### Task 11: Interactive fuselage sketch

**Files:**
- Create: `Python/src/aid/profile_edit.py`
- Create: `Python/src/aid_gui/profile_sketch_dialog.py`
- Test: `Python/tests/test_profile_edit.py`

**Interfaces:**
- Consumes: a body dict with `X`, `ZU`, `ZL`, `R`, `NX`
- Produces:

```python
def add_or_remove_point(bd: dict, x: float, y: float, *, view: str, thresh: float, manual: bool) -> dict:
    """Port Profile_Sketcher.m Point() for a single click.
    view is 'side' or 'top'. manual True allows deletion when the click is within thresh of an existing station.
    Side: y is Z. Top: y is the half-breadth and the opposite side is mirrored (ZL=-ZU or ZU=-ZL) as in lines 1109 and 1125.
    Returns the same dict, updated. NX follows the array length."""

def mirror_surface(bd: dict, *, source: str, center: float) -> dict:
    """source 'upper' copies ZU onto ZL about center (ZL = 2*center - ZU).
    source 'lower' copies ZL onto ZU. Profile_Sketcher.m Symmetry()."""

def smooth_profile(bd: dict, *, flatten: bool) -> dict:
    """Port Smooth() without questdlg. flatten True sets ZU and ZL to their means.
    flatten False runs the local quadratic polyfit on windows of 4 or 5 points where the slope jump exceeds 0.01 (upper) or 0.1 (lower), then swaps any station with ZU<ZL."""
```

The dialog `ProfileSketchDialog(bd)` shows side and top polylines of the stations, a Side/Top toggle, Smooth, Mirror upper, Mirror lower, and Apply. Apply writes `X`, `ZU`, `ZL`, `R`, `NX` back onto the dict. Dragging a station calls `add_or_remove_point` only for insert/delete; moving an existing station within `thresh` updates that station's `X` and `ZU` or `ZL` (side) or `R` (top) instead of inserting. Use `thresh = 0.05 * (X[-1]-X[0])` when the MATLAB `thresh` global is unavailable.

Do not edit `view3d.py` or `profile_sketcher.py`. The table dialog stays. Wave 2 adds a menu entry.

- [ ] **Step 1: Write the failing test**

```python
import numpy as np

from aid.profile_edit import add_or_remove_point, mirror_surface, smooth_profile

def _bd():
    return {"NX": 3, "X": np.array([0.0, 1.0, 2.0]), "ZU": np.array([0.0, 0.5, 0.0]),
            "ZL": np.array([0.0, -0.4, 0.0]), "R": np.array([0.0, 0.4, 0.0])}

def test_side_insert_grows_nx():
    bd = add_or_remove_point(_bd(), 0.5, 0.2, view="side", thresh=0.01, manual=False)
    assert len(bd["X"]) == 4
    assert bd["NX"] == 4

def test_manual_click_on_station_deletes():
    bd = add_or_remove_point(_bd(), 1.0, 0.5, view="side", thresh=0.2, manual=True)
    assert len(bd["X"]) == 2

def test_mirror_upper_onto_lower():
    bd = mirror_surface(_bd(), source="upper", center=0.0)
    assert np.allclose(bd["ZL"], -bd["ZU"])

def test_flatten_sets_means():
    bd = smooth_profile(_bd(), flatten=True)
    assert np.allclose(bd["ZU"], np.mean([0.0, 0.5, 0.0]))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd Python && python -m pytest tests/test_profile_edit.py -q`
Expected: FAIL with import error

- [ ] **Step 3: Write minimal implementation**

Port `Point`, `Symmetry`, and `Smooth` into `profile_edit.py` with the signatures above. The dialog is a `QDialog` that edits a copy and copies arrays back on Apply. Offscreen open/apply test goes in `tests/test_profile_edit.py` as `test_dialog_apply_copies_stations`, following `tests/test_gui_context_isolate.py` for the `QApplication`. Skip that one test if Qt cannot start; the four pure tests must not skip.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd Python && QT_QPA_PLATFORM=offscreen python -m pytest tests/test_profile_edit.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

Skip unless the user asked to commit.

---

### Task 12: Tornado viscous strip correction

**Files:**
- Create: `Python/src/aid/tornado/pablo.py`
- Create: `Python/src/aid/tornado/viscous.py`
- Test: `Python/tests/test_pablo.py`
- Test: `Python/tests/test_tornado_viscous.py`

**Interfaces:**
- Consumes: Tornado `geo`, `state`, `lattice`, `results`, `ref` dicts already produced by the Python solver. Does not modify `coeff.py`.
- Produces:

```python
def pablo(z: np.ndarray, alpha_rad: float, reynolds: float) -> dict:
    """Port fPablo.m. z is (N, 2) airfoil coordinates.
    Returns cl, cd, cm, upperbl, lowerbl."""

def viscous_correction(geo: dict, state: dict, lattice: dict, results: dict, ref: dict) -> dict:
    """Port fViscCorr in fViscCorr2.m, including fStripforce and spanload7 in that file.
    Returns Striplift, Stripdrag, Stripalpha, upperbl, lowerbl, totalliftcoeff, totalvdragcoeff."""
```

- [ ] **Step 1: Write the failing test**

```python
import math

import numpy as np

from aid.naca_ordinates import naca4_ordinates
from aid.tornado.pablo import pablo

def test_symmetric_section_at_zero_alpha_has_small_cl_and_positive_cd():
    z = naca4_ordinates("0012", 81)
    out = pablo(z, alpha_rad=0.0, reynolds=1.0e6)
    assert abs(out["cl"]) < 0.05
    assert out["cd"] > 0.0
    assert math.isfinite(out["cm"])
```

`test_tornado_viscous.py` builds a one-strip fake `geo`/`lattice`/`results` only if `viscous_correction` can run without a full aircraft. If the MATLAB function requires `results.F`, `lattice.N`, `lattice.XYZ`, `geo.nx`, `geo.ny`, `geo.b`, `state.alpha`, `state.betha`, `state.AS`, `state.rho`, `ref.S_ref`, and `ref.C_mac`, construct the smallest arrays that reach `totalliftcoeff` and assert that key is finite. Use `pablo` as the section solver inside `viscous_correction` the way `fViscCorr` calls `fPablo`.

Task 12's viscous test may import `naca4_ordinates` from Task 2. Those tasks are parallel, so **do not import `aid.naca_ordinates` from `test_tornado_viscous.py`**. Build a unit-circle-free NACA-like ellipse inline in the viscous test, or call `pablo` with a 20-point ellipse `x = 0.5*(1-cos)`, `y = ±0.06*sin`. The `test_pablo.py` file also must not import `naca_ordinates`. Duplicate the ellipse helper in `test_pablo.py`.

- [ ] **Step 2: Run test to verify it fails**

Run: `cd Python && python -m pytest tests/test_pablo.py tests/test_tornado_viscous.py -q`
Expected: FAIL with import error

- [ ] **Step 3: Write minimal implementation**

Port `fPablo.m` (Thwaites, Michel, Head, the linear-strength vortex `vortex`, `library`, `solvebl`, `sy`) into `pablo.py`. Port `fViscCorr`, `fStripforce`, and `spanload7` from `fViscCorr2.m` into `viscous.py`. Skip the `profilegen` early-return file loader (the `case 2` block that `cd`s to an airfoil directory and returns). Section coordinates come from `geo` airfoil fields the lattice already stores; if a strip has no airfoil, use a 12% ellipse of chord 1.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd Python && python -m pytest tests/test_pablo.py tests/test_tornado_viscous.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

Skip unless the user asked to commit.

---

### Task 13: Wire the handbook pass and Tornado extras

**Files:**
- Create: `Python/src/aid/handbook_pass.py`
- Modify: `Python/src/aid/stability.py` (CD0 block only, about lines 253–268)
- Modify: `Python/src/aid_gui/main_window.py` (`apply_calculations`, Tornado finish)
- Modify: `Python/src/aid_gui/menus.py` and `Python/src/aid_gui/settings.py` (two new checkable actions)
- Modify: `Python/src/aid_gui/profile_sketcher.py` only to add a button that opens `ProfileSketchDialog` if there is no other place on the Body tab; prefer a button on the existing body tab in `tabs.py` if that file is the body-tab owner. Touch only the Body tab widget that already opens the table dialog.
- Test: `Python/tests/test_handbook_pass.py`
- Modify: `UPDATES.md` (new top entry `1.33.0`)

**Interfaces:**
- Consumes: every Wave 1 signature exactly as written above
- Produces:

```python
def apply_handbook(ac: Aircraft, *, angl: bool, slipstream: bool, slipstream_data: tuple[float, float],
                   multhopp: bool, trim_mode: int, trim_fix: str) -> dict:
    """Order, matching AID.m:
    1. geometry() on WG, HT, VT, and non-empty NP.
    2. section_slopes() on WG (indexes 0 and 1 if two NACA codes), HT index 0, VT index 0.
    3. aero() on WG and HT at MACH[0].
    4. stamp_control_geometry().
    5. aircraft_cd0() assigned to the returned 'CD0' (do not leave the stored-field sum).
    6. lateral_static + lat_dir_corrections + lateral_dynamic.
    7. aircraft_stability(..., trim_mode=1 if trim_mode==1 else 0).
    8. If trim_mode==2, trim_incidence(..., fix=trim_fix), write i_wg/i_ht/alpha onto the aircraft, then recompute the lift terms via a second aircraft_stability call with trim_mode 0.
    9. longitudinal_dynamic on the stability scalars plus CLde/Cmde from stamp/handbook.
    Returns the stability dict plus 'lateral' and 'dynamic'."""

def section_slopes(pt: dict, index: int) -> None:
    """Lift_Curve_Slope.m without dialogs.
    NACA length 4 → naca4_ordinates(120). Length 5 → naca5_ordinates(120).
    Length >= 6 → NacaSpec the way NACA_Panel_Maker.m lines 114-124 writes the namelist
    (PROFILE = first two characters, or first two plus 'A' when 'A' is in the code;
    CAMBER = '6A' if 'A' in the code else the first character;
    TOC = last two digits/100; CL = the digit before those / 10; dencode=3),
    then cosine-resample to 120 points with the same x = 0.5-cos spacing.
    If ordinates() raises or returns an empty array, leave pt unchanged (MATLAB returns empty DATA).
    Then panel_method on alphas -4,-2,0,2,4,6,8 degrees and store a0, alpha0, Cm_ac at `index`,
    and TC = max(y)-min(y). A path ending in a known airfoil suffix goes through read_airfoil_file."""
```

`section_slopes` lives in `Python/src/aid/section_aero.py` (created here, because it imports both Task 1 and Task 2).

Settings additions, default **off**, so existing sessions match today's Tornado:

- Calculations → "Viscous Strip" → `settings.viscous_strip: bool`
- After Tornado succeeds, if `settings.estimate_neutral_point` is not a persistent toggle: ask with `QMessageBox.question` "Estimate Neutral Point?" only when `QT_QPA_PLATFORM != "offscreen"`. Offscreen and tests never ask and never call `find_static_margin`. Yes calls `find_static_margin` and stores `results["N0"]`.
- If Viscous Strip is checked, call `viscous_correction` after `coeff_create` and store the dict on `results["viscous"]`. Do not replace `results["CL"]` / `CD` used by the gold compare.

Tornado finish also calls `view3d.paint_cp(lattice XYZ, results cp)` when those arrays exist. `plot_aircraft` calls `clear_cp` so a geometry edit removes the old colormap.

`stability.py` CD0 block (the stored-field sum) becomes `from aid.drag import aircraft_cd0` and `cd0 = aircraft_cd0(ac)` when the components are present. Keep the 1.25 factor inside `aircraft_cd0` only, not twice.

Body tab: a "Sketch" button opens `ProfileSketchDialog`. The existing Adjust table stays.

`trim_fix` comes from which incidence box the user is editing. If neither is being edited, pass `'ht'` when `ALSCHD` has more than one value (MATLAB default `HT.i = []`) and `'both'` when `ALSCHD` is a scalar. Document that in `apply_handbook`'s docstring. The GUI passes `'both'` unless a specific incidence field is the edit source; `MainWindow.apply_calculations` passes `'both'`.

- [ ] **Step 1: Write the failing test**

```python
import numpy as np

from aid.aircraft import load_mat
from aid.handbook_pass import apply_handbook
from aid.paths import matlab_code

def test_cessna_handbook_pass_has_dynamic_and_lateral_keys():
    ac = load_mat(matlab_code() / "Models" / "Cessna 172.mat")
    out = apply_handbook(
        ac, angl=True, slipstream=False, slipstream_data=(0.5, 0.9),
        multhopp=True, trim_mode=0, trim_fix="both",
    )
    assert np.isfinite(out["CLa"])
    assert np.isfinite(out["CD0"])
    assert "CYb" in out["lateral"]
    assert out["dynamic"]["A"].shape == (4, 4)
    assert np.isfinite(out["dynamic"]["Xu"])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd Python && python -m pytest tests/test_handbook_pass.py -q`
Expected: FAIL with import error

- [ ] **Step 3: Write minimal implementation**

Create `section_aero.py` and `handbook_pass.py`. Change the CD0 block in `stability.py`. Add the two Tornado hooks and the Sketch button. Update `UPDATES.md` with `1.33.0 - handbook airfoil lateral dynamic tornado extras` and one line per R1–R13. Do not change README architecture unless the handbook pass becomes a new package boundary; a sentence under the Python package bullet is enough if you mention `handbook_pass`.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd Python && QT_QPA_PLATFORM=offscreen python -m pytest tests/test_handbook_pass.py tests/test_stability_cessna.py tests/test_drag_cessna.py tests/test_handbook_controls.py -q`
Expected: PASS

Then the Wave 1 files still pass:

Run: `cd Python && QT_QPA_PLATFORM=offscreen python -m pytest tests/test_naca456_ordinates.py tests/test_naca_ordinates.py tests/test_panel_method.py tests/test_aero.py tests/test_aircraft_cd0.py tests/test_trim_incidence.py tests/test_control_stamp.py tests/test_lateral.py tests/test_longitudinal_dynamic.py tests/test_tornado_static_margin.py tests/test_gui_cp_paint.py tests/test_profile_edit.py tests/test_pablo.py tests/test_tornado_viscous.py tests/test_handbook_pass.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

Skip unless the user asked to commit.

---

## Self-review

- R1 Task 1. R2 Task 2 plus `section_slopes` in Task 13. R3 Task 3. R4 Task 4 and the CD0 swap in Task 13. R5 Task 5 and the `trim_mode==2` call in Task 13. R6 Task 6. R7 Task 7. R8 Task 8. R9 Task 9, dialog in Task 13. R10 Task 10, call site in Task 13. R11 Task 11, Sketch button in Task 13. R12 Task 12, opt-in in Task 13. R13 Task 13.
- Wave 1 file sets are disjoint. Task 12 tests do not import Task 2.
- `stamp_control_geometry` does not change probe rows locked by `test_handbook_controls.py`.
- Default Tornado path does not call viscous correction or neutral-point iteration.
- Propeller block, ASCDM, FlightGear, and profile-sketcher camera animation stay out.
