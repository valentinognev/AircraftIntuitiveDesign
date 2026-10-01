# Control-surface derivative coefficients

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Report flap, aileron, elevator, and rudder derivatives per degree at any probe deflection, including when the stored surface angle is zero, for the handbook model and for DATCOM, Tornado, AVL, and flow5.

**Architecture:** A frozen record in `aid.control_deriv` is the only type solvers return. Each solver lives in its own module and is called with a deepcopy of the aircraft, so the stored `F`/`A`/`E`/`R` angles stay put. The probe angle is an argument, not the stored deflection. Expensive solvers are not hooked into ordinary Analyze; a separate call fills the Controls plot and `POST /control-derivatives`.

**Tech Stack:** Python 3.11 (`aid`, pytest), PySide6 Controls tab, FastAPI `api/aid_web`, Vite React `web/`, flow5 helper `FLOW5/run/flow5_run.cpp`.

**Spec:** This file is the spec. Executors treat the Global Constraints and the record schema as binding.

## Global Constraints

- Do not `git commit` or `git push`. Leave the worktree dirty. The parent asks the user before any commit.
- Implementers and reviewers use Grok non-fast only (`grok-4.7-high`). Fast modes, Composer, Claude, and `inherit` are forbidden.
- TDD: write the failing test, run it, then the minimum code, then run it again. A task is done only when its named pytest or `npm test` command passes.
- Do not change stored control angles on the caller's `Aircraft`. Every solver deep-copies first.
- Do not change ordinary Analyze results. `run_datcom`, `tornado_io` (default), `run_avl_full`, `run_flow5`, and `POST /analyze` keep their current coefficients. Gold MATLAB compare stays on those paths.
- Derivatives are per degree. Missing physics is JSON `null`, never a filled-in number.
- Positive aileron probe: right trailing edge down, left trailing edge up (`DELTAR = +δ`, `DELTAL = -δ`). Positive flap, elevator, and rudder probes write that surface's `DELTA`.
- Finite-difference step is `h_deg = 1.0`. Slope at probe `δ` is `(C(δ+h) - C(δ-h)) / (2h)`.
- Default probe list, when the caller omits it: `[0.0, 5.0]`.
- A surface with illegal span (`SPANFO <= SPANFI`, or missing chords) is `available: false`. The other surfaces are still returned.
- File ownership in the dispatch table is exclusive during a wave. A task that needs a new schema field stops and reports it; it does not edit `control_deriv.py`.
- After the feature lands, Task 10 bumps `UPDATES.md` to `1.30.0`. No other new markdown.

## Record schema

```python
SURFACES = ("flap", "aileron", "elevator", "rudder")
COEFFS = ("CL", "CD", "Cm", "CY", "Cl", "Cn")

# One dict per surface per probe angle:
{
    "surface": "flap",          # one of SURFACES
    "delta_deg": 5.0,           # probe, not the stored angle
    "available": True,
    "reason": "",               # empty when available
    "CL": 0.01,                 # per degree, or None
    "CD": None,
    "Cm": -0.002,
    "CY": None,
    "Cl": None,
    "Cn": None,
}
```

A solver returns `list[dict]` with one row per `(surface, delta_deg)` in `SURFACES` order, and within a surface in the order of `deltas_deg`. Four surfaces times two default probes is eight rows.

## What each model can fill

| Model | Flap | Aileron | Elevator | Rudder | How, at a stored angle of 0 |
|---|---|---|---|---|---|
| Handbook | `CL`, `Cm` | `Cl` | `CL`, `Cm` | `CY`, `Cl`, `Cn` | Linear theory. The same slope is repeated at every probe. |
| DATCOM | `CL`, `CD`, `Cm` | `Cl`, `Cn`, `CY` | `CL`, `CD`, `Cm` | unavailable | Two `for005` cases at `δ±h`. Rudder reason: `datcom has no rudder namelist`. |
| Tornado | all six | all six | all six | all six | Force the surface onto the lattice even when stored `DELTA` is 0, then central-difference one column per surface. |
| AVL | all six that `.sb` contains | same | same | same | Emit `CONTROL` cards even at stored angle 0. Set the run-case angle to the probe. Read `geometry.sb`. Convert per radian to per degree. |
| flow5 | `CL`, `CD`, `Cm` | `Cl`, `Cn` | `CL`, `CD`, `Cm` | `CY`, `Cl`, `Cn` | Deck hinge at `δ±h`. Aileron uses opposite left/right angles. |

Handbook `CD` is `null`. DATCOM rudder coefficients are `null`. flow5 leaves the unlisted coefficients `null`.

## File map

| File | Responsibility | Task |
|---|---|---|
| `Python/src/aid/control_deriv.py` | Schema, central difference, deepcopy probe helper | 1 |
| `Python/src/aid/handbook_controls.py` | Port of `Controls.m` | 2 |
| `Python/src/aid/tornado/control_deriv.py` | Tornado surface derivatives | 3 |
| `Python/src/aid/avl_controls.py` | AVL control geometry, case angle, `.sb` map | 4 |
| `Python/src/aid/datcom_controls.py` | DATCOM probe cases | 5 |
| `Python/src/aid/flow5_controls.py` | flow5 decks at `δ±h` | 6 |
| `FLOW5/run/flow5_run.cpp` | Optional section TE flap; old decks unchanged | 6 |
| `Python/src/aid/control_report.py` | Dispatch one solver name | 7 |
| `api/aid_web/app.py`, `api/aid_web/analyze.py` | `POST /control-derivatives` | 7 |
| `Python/src/aid_gui/compare_tabs.py`, `menus.py`, `main_window.py` | Controls plot | 8 |
| `web/src/Results.tsx`, `web/src/controlDeriv.ts` | Web chart | 9 |
| `UPDATES.md`, `README.md` | `1.30.0` and the new endpoint | 10 |

---

### Task 1: Shared record and probe copy

**Files:**
- Create: `Python/src/aid/control_deriv.py`
- Test: `Python/tests/test_control_deriv_schema.py`

**Interfaces:**
- Consumes: `aid.aircraft.Aircraft`
- Produces:
  - `SURFACES`, `COEFFS`, `DEFAULT_DELTAS_DEG = (0.0, 5.0)`, `H_DEG = 1.0`
  - `blank_row(surface: str, delta_deg: float, *, available: bool, reason: str = "") -> dict`
  - `central_difference(plus: dict, minus: dict, h_deg: float = H_DEG) -> dict` with keys `COEFFS`, values per degree
  - `with_probe(ac: Aircraft, surface: str, delta_deg: float) -> Aircraft` deepcopy. Does not mutate `ac`.
  - `iter_rows(deltas_deg: tuple[float, ...] | list[float] | None) -> list[tuple[str, float]]`

- [ ] **Step 1: Write the failing test**

```python
from copy import deepcopy

from aid.aircraft import Aircraft
from aid.control_deriv import (
    COEFFS,
    DEFAULT_DELTAS_DEG,
    H_DEG,
    blank_row,
    central_difference,
    iter_rows,
    with_probe,
)


def _ac() -> Aircraft:
    z = {"SPANFI": 1.0, "SPANFO": 4.0, "CHRDFI": 1.0, "CHRDFO": 0.6, "DELTA": 0.0}
    a = {"SPANFI": 6.0, "SPANFO": 8.0, "CHRDFI": 0.5, "CHRDFO": 0.4, "DELTAL": 0.0, "DELTAR": 0.0}
    return Aircraft(
        WG={}, HT={}, VT={}, F=dict(z), A=dict(a), E=dict(z), R=dict(z),
        BD={}, NP=[], NB=[], AERO={}, plot_cmp=[1, 1, 1, 1], unit="ft",
    )


def test_default_probes_include_zero_and_a_nonzero_point():
    assert DEFAULT_DELTAS_DEG == (0.0, 5.0)
    assert H_DEG == 1.0
    pairs = iter_rows(None)
    assert pairs[0] == ("flap", 0.0)
    assert ("aileron", 5.0) in pairs
    assert [p[0] for p in pairs].count("rudder") == 2


def test_central_difference_is_per_degree():
    plus = {"CL": 0.12, "CD": 0.02, "Cm": -0.04, "CY": 0.0, "Cl": 0.01, "Cn": -0.01}
    minus = {"CL": 0.08, "CD": 0.02, "Cm": -0.02, "CY": 0.0, "Cl": -0.01, "Cn": 0.01}
    slope = central_difference(plus, minus, 1.0)
    assert slope["CL"] == (0.12 - 0.08) / 2.0
    assert slope["CD"] == 0.0
    assert set(slope) == set(COEFFS)


def test_blank_row_uses_null_coefficients():
    row = blank_row("rudder", 5.0, available=False, reason="datcom has no rudder namelist")
    assert row["available"] is False
    assert row["CL"] is None and row["Cn"] is None


def test_with_probe_does_not_mutate_stored_zero():
    ac = _ac()
    probed = with_probe(ac, "aileron", 5.0)
    assert ac.A["DELTAL"] == 0.0 and ac.A["DELTAR"] == 0.0
    assert ac.F["DELTA"] == 0.0
    assert probed.A["DELTAR"] == 5.0 and probed.A["DELTAL"] == -5.0
    assert probed.F["DELTA"] == 0.0
    flap = with_probe(ac, "flap", 5.0)
    assert flap.F["DELTA"] == 5.0 and ac.F["DELTA"] == 0.0
    assert deepcopy(ac.E)["DELTA"] == 0.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd Python && python -m pytest tests/test_control_deriv_schema.py -q`

Expected: FAIL with `ModuleNotFoundError` or `ImportError` for `aid.control_deriv`.

- [ ] **Step 3: Write minimal implementation**

`with_probe` rules:

- `flap` sets `F["DELTA"]`
- `elevator` sets `E["DELTA"]`
- `rudder` sets `R["DELTA"]`
- `aileron` sets `DELTAR = delta_deg` and `DELTAL = -delta_deg`
- lists already stored in `DELTA` are replaced by the scalar probe on the copy only
- `central_difference` skips a coefficient when either side is `None`
- `iter_rows(None)` uses `DEFAULT_DELTAS_DEG`

- [ ] **Step 4: Run test to verify it passes**

Run: `cd Python && python -m pytest tests/test_control_deriv_schema.py -q`

Expected: PASS

---

### Task 2: Handbook derivatives

**Files:**
- Create: `Python/src/aid/handbook_controls.py`
- Test: `Python/tests/test_handbook_controls.py`
- Read only: `Matlab/fsroot/code/Controls.m`, `Python/src/aid/stability.py` (`_per_deg`)

**Interfaces:**
- Consumes: `blank_row`, `iter_rows`, `SURFACES` from `aid.control_deriv`
- Produces: `handbook_controls(ac: Aircraft, deltas_deg=None) -> list[dict]`

Port `Controls.m` numeric formulas. Do not call MATLAB.

- Flap area `F.S = 0.5 * (CHRDFI + CHRDFO) * (SPANFO - SPANFI)`. Same for elevator and rudder.
- `tau` from Perkins and Hage Figure 5-33: `S_ratio = [0, 0.1, …, 0.7]`, `tau = [0, 0.25, 0.4, 0.5, 0.58, 0.65, 0.71, 0.76]`, linear interpolation of area over parent area. Clamp the ratio to `[0, 0.7]`.
- Parent areas: flap and aileron use `WG["S"]` last element; elevator uses `HT["S"]`; rudder uses `VT["S"]`.
- Rudder `tau` uses rudder area over VT area. `Controls.m` line 25 uses `E.S` there; that is a bug. The Python port uses `R.S`.
- `CLdf = a_w * tau_f`, `Cmdf = -a_w * tau_f * F.l / cbar` with `F.l = (cbar - 0.5 * (CHRDFI + CHRDFO)) - x_cg` and `x_cg` the wing aerodynamic-center fraction already on the aircraft if present, else `0.25`. `cbar` is the last `WG["cbar"]`.
- Elevator: `CLde = a_h * eta * S_h / S_w * tau_e`, `Cmde = -HT.l / cbar * CLde`. `eta` from `HT["eta"]` or `0.9`. `HT.l` from `HT["l"]` when present, else the distance `HT["X"] + HT xmac - XCG` is out of scope: if `HT["l"]` is missing, elevator `available` is false and `reason` is `HT.l missing`.
- Rudder: `CYdr = k * a_v * swash * S_v / S_w * tau_r`, `Cldr = CYdr * h / b`, `Cndr = -CYdr * l / b`. `k`, `a`, `swash`, `h`, `l` come from `VT`. `b` is `WG["b"]`. Missing `VT["l"]` or `VT["a"]` makes the rudder unavailable with `reason` naming the missing key.
- Aileron: compute `A.tau` with the flap table and `A.S / WG.S`. Compute `A.Kb` exactly as `Controls.m` lines 30–42 (DATCOM Figure 6.1.4.1-15). `Cl` per the unfinished comment, closed with that `Kb`: `Clda = a_w * A.tau * A.Kb`. `Cn` stays `null` (the `Cnda` line in `Controls.m` is a comment, and `Lateral_Static_Stability.m` hard-codes `0.1`; do not copy `0.1`).
- Lift slopes `WG["a"]`, `HT["a"]`, `VT["a"]` convert with the same rule as `stability._per_deg` before multiplying, so the reported slope is per degree. If `a > 1`, treat it as per radian and multiply the product by `pi/180`.
- The slope does not depend on `delta_deg`. Copy it onto every probe row.
- `CD` is `null` on every handbook row.

- [ ] **Step 1: Write the failing test**

```python
import math

from aid.aircraft import Aircraft
from aid.handbook_controls import handbook_controls


def _plane() -> Aircraft:
    return Aircraft(
        WG={"a": 0.1, "S": [10.0, 20.0], "cbar": [1.0, 2.0], "b": 10.0, "SSPN": 5.0, "TR": 0.6, "x_cg": 0.25},
        HT={"a": 0.08, "S": [4.0], "eta": 0.9, "l": 8.0},
        VT={"a": 0.05, "S": [2.0], "k": 1.0, "swash": 1.0, "h": 1.5, "l": 8.0},
        F={"SPANFI": 1.0, "SPANFO": 3.0, "CHRDFI": 0.4, "CHRDFO": 0.4, "DELTA": 0.0},
        A={"SPANFI": 3.0, "SPANFO": 4.5, "CHRDFI": 0.3, "CHRDFO": 0.25, "DELTAL": 0.0, "DELTAR": 0.0},
        E={"SPANFI": 0.2, "SPANFO": 1.5, "CHRDFI": 0.3, "CHRDFO": 0.2, "DELTA": 0.0},
        R={"SPANFI": 0.2, "SPANFO": 1.2, "CHRDFI": 0.35, "CHRDFO": 0.2, "DELTA": 0.0},
        BD={}, NP=[], NB=[], AERO={"XCG": 1.0}, plot_cmp=[1, 1, 1, 1], unit="ft",
    )


def test_zero_stored_deflection_still_returns_nonzero_probe():
    rows = handbook_controls(_plane(), [0.0, 5.0])
    flap = [r for r in rows if r["surface"] == "flap"]
    assert [r["delta_deg"] for r in flap] == [0.0, 5.0]
    assert flap[0]["CL"] == flap[1]["CL"]
    assert flap[0]["CL"] is not None and flap[0]["CL"] != 0.0
    assert flap[0]["CD"] is None


def test_rudder_tau_uses_rudder_area_not_elevator_area():
    ac = _plane()
    ac.E["SPANFO"] = 0.21  # elevator area near zero, rudder area is not
    rows = handbook_controls(ac, [5.0])
    rudder = next(r for r in rows if r["surface"] == "rudder")
    assert rudder["available"] is True
    assert rudder["CY"] is not None and rudder["Cn"] == -rudder["CY"] * 8.0 / 10.0


def test_aileron_cl_is_not_the_placeholder():
    rows = handbook_controls(_plane(), [5.0])
    ail = next(r for r in rows if r["surface"] == "aileron")
    assert ail["Cl"] not in (None, 0.1, 0.1 * math.pi / 180.0)
    assert ail["Cn"] is None


def test_stored_angles_stay_zero():
    ac = _plane()
    handbook_controls(ac, [5.0])
    assert ac.F["DELTA"] == 0.0 and ac.A["DELTAR"] == 0.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd Python && python -m pytest tests/test_handbook_controls.py -q`

Expected: FAIL importing `handbook_controls`.

- [ ] **Step 3: Write minimal implementation**

Match the formulas in the task text. Per-radian inputs (`a > 1`) go through `pi/180` after the `Controls.m` product.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd Python && python -m pytest tests/test_handbook_controls.py tests/test_control_deriv_schema.py -q`

Expected: PASS

---

### Task 3: Tornado derivatives at a probe

**Files:**
- Create: `Python/src/aid/tornado/control_deriv.py`
- Modify: `Python/src/aid/tornado_io.py` — add keyword only
- Test: `Python/tests/test_tornado_control_deriv.py`
- Read only: `Python/src/aid/tornado/boundary.py`, `lattice.py`, `solver.py`, `coeff.py`

**Interfaces:**
- Consumes: `with_probe`, `central_difference`, `blank_row`, `iter_rows`, `H_DEG`
- Produces: `tornado_controls(ac: Aircraft, deltas_deg=None, mesh: tuple[str, str] = ("4", "2")) -> list[dict]`

`tornado_io` today drops a control when its stored deflection is zero (`_has_deflection`). Add `force_controls: bool = False`. When `True`, flap, aileron, elevator, and rudder are passed into `write_geometry` whenever their span is legal, even if `DELTA`/`DELTAL`/`DELTAR` are 0. Default `False` keeps the gold path.

Derivative column: one per surface, not one per flapped strip. Deflect every strip of that surface together by `H_DEG` degrees inside a copied `geo["flap_vector"]`. Solve `C(δ+h)` and `C(δ-h)` with the existing `lattice_setup` → `set_boundary` → `solve` → `coeff_create` chain. Map `CL`, `CD`, `Cm`, `CY` (from `CC`), `Cl`, `Cn`.

Aileron geometry is antisymmetric (`fsym = 0` on the aileron strips). Flap and elevator stay symmetric. Rudder stays on the vertical tail.

Do not add these columns to the ordinary `solve()` result used by Analyze.

- [ ] **Step 1: Write the failing test**

```python
from aid.aircraft import load_jsonc
from aid.paths import models_dir
from aid.tornado.control_deriv import tornado_controls
from aid.tornado_io import tornado_io


def test_force_controls_off_matches_zero_deflection_lattice():
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    geo_default, _ = tornado_io(ac, ("4", "2"))
    # Cessna stored flap/aileron deflections are zero, so the default lattice has no flap panels.
    import numpy as np
    assert float(np.sum(np.asarray(geo_default["flapped"]))) == 0.0


def test_zero_stored_angle_probe_at_five_degrees_is_finite():
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    rows = tornado_controls(ac, [5.0], mesh=("4", "2"))
    flap = next(r for r in rows if r["surface"] == "flap")
    assert flap["available"] is True
    assert flap["delta_deg"] == 5.0
    assert flap["CL"] is not None and abs(flap["CL"]) < 1.0
    rudder = next(r for r in rows if r["surface"] == "rudder")
    assert rudder["available"] is True and rudder["Cn"] is not None
    assert ac.F["DELTA"] == 0 or float(ac.F["DELTA"][0] if isinstance(ac.F["DELTA"], list) else ac.F["DELTA"]) == 0.0
```

Check the Cessna JSON before writing the assertion on `ac.F["DELTA"]`. Assert the value that was loaded, unchanged, rather than assuming the container type. The behavioral assertion is: `tornado_controls` returns and the loaded `DELTA` object compares equal to a copy taken before the call.

- [ ] **Step 2: Run test to verify it fails**

Run: `cd Python && python -m pytest tests/test_tornado_control_deriv.py -q`

Expected: FAIL importing `tornado_controls`.

- [ ] **Step 3: Write minimal implementation**

`force_controls=True` only from `tornado_controls`. Build the baseline geo at the probe (so the linearization sits at `δ`, with the step `±h` applied on top). Use mesh `("4", "2")` in tests so a Cessna case stays small. Alpha for the state is the first `ALSCHD` entry.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd Python && python -m pytest tests/test_tornado_control_deriv.py tests/test_tornado_io_cessna.py -q`

Expected: PASS. `test_tornado_io_cessna.py` guards the default `force_controls=False` path.

---

### Task 4: AVL derivatives at a probe

**Files:**
- Create: `Python/src/aid/avl_controls.py`
- Test: `Python/tests/test_avl_controls.py`
- Read only: `Python/src/aid/avl_io.py`, `Python/src/aid/avl_parse.py` (`parse_sb`)

**Interfaces:**
- Consumes: `blank_row`, `iter_rows`, `with_probe`
- Produces:
  - `write_avl_control_geometry(ac, run_dir, mesh) -> None` writes `geometry.avl` with `CONTROL` cards for every legal surface even when stored deflection is 0
  - `write_avl_control_case(run_dir, delta_by_name: dict[str, float]) -> None`
  - `rows_from_sb(sb_text: str, delta_deg: float, names: tuple[str, ...] = SURFACES) -> list[dict]`
  - `avl_controls(ac, deltas_deg=None, mesh=("10", "10"), run_dir=None) -> list[dict]`

Do not change `write_avl_geometry` or `run_avl_full`. Those stay the Analyze path.

Control names written to AVL, in this order: `flap`, `aileron`, `elevator`, `rudder`. Aileron gain is `-1` on the right-hand section, matching the existing `aileron ... -1` line in `avl_io.py`. The run file sets each control to the probe degrees (`D1` style commands after `OPER`, one name per defined control). One AVL process per probe angle, because AVL's control derivatives are the slope at the set angle.

`parse_sb` already returns `surface[].CX/CY/CZ/Cl/Cm/Cn` per radian. Map:

- `CL` from `CZ` with a sign flip only if the fixture's `CZd` is the AVL normal-force derivative and the existing `CLtot` mapping in `merge_avl_st` treats `CLtot` as lift. Prefer the stability-axis `CLd` line when the `.sb` or `.st` body contains `CLdN =`. If only body-axis `CZd` exists, set `CL` from `-CZd` when alpha is near 0 (the fixture test uses alpha 0). Document the choice in the function docstring in one sentence.
- `CD` from `CX` at alpha 0
- `Cm` from `Cm`
- `CY` from `CY`
- `Cl` from `Cl`
- `Cn` from `Cn`
- multiply each by `pi/180` to get per degree

A missing control name in the `.sb` becomes `available: false`, `reason` `avl surface missing`.

- [ ] **Step 1: Write the failing test**

```python
from aid.avl_controls import rows_from_sb

_SB = """
 Geometry-axis derivatives...
 CXd1 = 0.01
 CYd1 = 0.0
 CZd1 = -1.8
 Cld1 = 0.0
 Cmd1 = -0.4
 Cnd1 = 0.0
 CXd2 = 0.0
 CYd2 = 0.0
 CZd2 = 0.0
 Cld2 = 0.5
 Cmd2 = 0.0
 Cnd2 = -0.1
"""


def test_sb_fixture_maps_flap_and_aileron_per_degree():
    # Header parser needs surface names; rows_from_sb accepts an explicit order
    # when the fixture has no run-case header.
    rows = rows_from_sb(_SB, 5.0, names=("flap", "aileron", "elevator", "rudder"))
    flap = next(r for r in rows if r["surface"] == "flap")
    assert flap["delta_deg"] == 5.0
    assert flap["available"] is True
    ail = next(r for r in rows if r["surface"] == "aileron")
    assert ail["Cl"] is not None and abs(ail["Cl"]) < abs(0.5)  # per degree is smaller than per radian
    rudder = next(r for r in rows if r["surface"] == "rudder")
    assert rudder["available"] is False
```

Add a second test that `write_avl_control_geometry` on Cessna 172 with all stored deflections zero still contains the four tokens `flap`, `aileron`, `elevator`, and `rudder` in `geometry.avl`. Use `tmp_path` and mesh `("4", "2")`. Do not invoke the AVL binary in the unit test.

- [ ] **Step 2: Run test to verify it fails**

Run: `cd Python && python -m pytest tests/test_avl_controls.py -q`

Expected: FAIL importing `avl_controls`.

- [ ] **Step 3: Write minimal implementation**

Geometry writer may call the same section loop facts as `avl_io._write_surface`, but from `avl_controls.py`. Copy the needed private helpers only if importing them does not change `avl_io.py`. If a one-line public wrapper in `avl_io.py` is required, that edit belongs to this task and must default to today's behavior when the wrapper is not used.

`avl_controls` runs the binary only when `run_dir` is None and `AVL/run/avl` exists. The unit tests do not call `avl_controls` against the binary.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd Python && python -m pytest tests/test_avl_controls.py tests/test_avl_merge_run_case.py -q`

Expected: PASS

---

### Task 5: DATCOM derivatives at a probe

**Files:**
- Create: `Python/src/aid/datcom_controls.py`
- Test: `Python/tests/test_datcom_controls.py`
- Read only: `Python/src/aid/datcom_io.py` (`write_for005`), `Python/src/aid/datcom_run.py`, `Python/src/aid/datcom_parse.py`

**Interfaces:**
- Consumes: `with_probe`, `central_difference`, `blank_row`, `iter_rows`, `H_DEG`
- Produces: `datcom_controls(ac, deltas_deg=None, *, run=None) -> list[dict]`

`run`, when passed, is `run(ac) -> dict` and replaces `run_datcom`. Tests pass a fake. Production calls `run_datcom`.

For each probe and each of flap, aileron, elevator:

- deepcopy via `with_probe` at `δ+h` and `δ-h`
- read totals at the first alpha: `CL`, `CD`, `Cm`, and lateral `Cl`/`Cn`/`CY` when the parsed dict has `cl`, `cn`, `cy` (lowercase, the static table). If a lateral key is absent, that coefficient stays `null`.
- central-difference

Rudder rows: `available: false`, `reason` exactly `datcom has no rudder namelist`.

Do not add a rudder namelist to `write_for005`.

One surface per paired run. Leave the other surfaces at their stored angles (usually 0) so the difference isolates one control.

- [ ] **Step 1: Write the failing test**

```python
from aid.aircraft import Aircraft
from aid.datcom_controls import datcom_controls


def _ac() -> Aircraft:
    z = {"SPANFI": 1.0, "SPANFO": 3.0, "CHRDFI": 0.4, "CHRDFO": 0.3, "DELTA": 0.0,
         "FTYPE": 1.0, "PHETE": 0.0, "PHETEP": 0.0, "TC": 0.12, "CB": 0.5}
    a = {"SPANFI": 3.0, "SPANFO": 4.0, "CHRDFI": 0.3, "CHRDFO": 0.2, "DELTAL": 0.0, "DELTAR": 0.0, "STYPE": 1.0}
    return Aircraft(
        WG={"SSPN": 5.0}, HT={"SSPN": 2.0}, VT={"SSPN": 2.0},
        F=dict(z), A=dict(a), E=dict(z), R=dict(z),
        BD={}, NP=[], NB=[], AERO={"ALSCHD": [0.0]}, plot_cmp=[1, 1, 1, 1], unit="ft",
    )


def test_datcom_differences_a_fake_run_and_skips_rudder():
    seen = []

    def fake_run(ac):
        seen.append(("flap", float(ac.F["DELTA"]), "ail", float(ac.A["DELTAR"])))
        cl = 0.1 + 0.02 * float(ac.F["DELTA"])
        return {"alpha": [0.0], "CL": [cl], "CD": [0.02], "Cm": [-0.01 * float(ac.F["DELTA"])]}

    ac = _ac()
    rows = datcom_controls(ac, [5.0], run=fake_run)
    flap = next(r for r in rows if r["surface"] == "flap")
    assert abs(flap["CL"] - 0.02) < 1e-9
    assert flap["Cm"] is not None
    rudder = next(r for r in rows if r["surface"] == "rudder")
    assert rudder["available"] is False
    assert rudder["reason"] == "datcom has no rudder namelist"
    assert ac.F["DELTA"] == 0.0
    assert any(abs(delta - 6.0) < 1e-9 for _, delta, _, _ in seen)
    assert any(abs(delta - 4.0) < 1e-9 for _, delta, _, _ in seen)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd Python && python -m pytest tests/test_datcom_controls.py -q`

Expected: FAIL importing `datcom_controls`.

- [ ] **Step 3: Write minimal implementation**

Call `fake_run` / `run_datcom` on the copies only. Index the alpha row 0.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd Python && python -m pytest tests/test_datcom_controls.py -q`

Expected: PASS. Do not run a live DATCOM binary in this task.

---

### Task 6: flow5 derivatives at a probe

**Files:**
- Create: `Python/src/aid/flow5_controls.py`
- Modify: `FLOW5/run/flow5_run.cpp` (`configure_wing` only)
- Test: `Python/tests/test_flow5_controls.py`
- Read only: `Python/src/aid/flow5_io.py`, `Python/src/aid/flow5_sections.py`

**Interfaces:**
- Consumes: `with_probe`, `central_difference`, `blank_row`, `iter_rows`, `H_DEG`, `write_flow5_deck`
- Produces: `flow5_controls(ac, deltas_deg=None, mesh=("4", "2"), *, run=None) -> list[dict]`

`write_flow5_deck` stays unchanged so Analyze decks have no flap keys.

`flow5_controls` builds a deck, then adds optional keys on the sections that bound the surface:

```json
"te_flap_x": 0.7,
"te_flap_deg": 6.0,
"te_flap_antisym": false
```

`te_flap_x` is the hinge as a fraction of local chord: `1 - CHRDFI / local_chord`, clamped to `(0.05, 0.95)`. Sections whose span station lies inside `[SPANFI, SPANFO]` get the keys. Insert extra sections at `SPANFI` and `SPANFO` when those stations are not already in the deck, so a partial-span aileron does not flap the whole wing.

`te_flap_antisym: true` only for the aileron. The helper applies `+te_flap_deg` on the starboard surface and `-te_flap_deg` on the port surface. Flap, elevator, and rudder use `false` (same sign both sides; the vertical tail is a single fin).

In `configure_wing`, when `te_flap_x` is absent, behavior is identical to today. When it is present, set that section foil's trailing-edge flap with `Foil::setTEFlapData(true, x, 0.0, angle_deg)` before `makePlane`. For `te_flap_antisym`, the port surface angle is the negative. Rebuild the flow5 helper after the C++ edit (`cmake --build FLOW5/build`).

`run`, when passed, is `run(deck: dict) -> dict` with `CL`, `CD`, `Cm` lists and optional `Cl`, `Cn`, `CY` lists. Tests use the fake. Production uses `run_flow5_native`. Central-difference the first alpha sample.

Coefficients to fill: flap and elevator `CL`, `CD`, `Cm`; aileron `Cl`, `Cn`; rudder `CY`, `Cl`, `Cn`. Anything the deck run does not return stays `null`.

- [ ] **Step 1: Write the failing test**

```python
from aid.aircraft import Aircraft
from aid.flow5_controls import flow5_controls


def _ac() -> Aircraft:
    wing = {
        "CHRDR": 2.0, "CHRDTP": 1.0, "SSPN": 5.0, "SSPNOP": 0.0,
        "SAVSI": 0.0, "SAVSO": 0.0, "CHSTAT": 0.25, "DHDADI": 0.0, "DHDADO": 0.0,
        "TWISTA": 0.0, "SSPNE": 5.0, "X": 0.0, "Y": 0.0, "Z": 0.0, "i": 0.0,
        "NACA": ["0012"], "S": [20.0],
    }
    tail = dict(wing)
    tail["SSPN"] = 2.0
    z = {"SPANFI": 0.5, "SPANFO": 2.0, "CHRDFI": 0.4, "CHRDFO": 0.4, "DELTA": 0.0}
    a = {"SPANFI": 3.0, "SPANFO": 4.5, "CHRDFI": 0.3, "CHRDFO": 0.25, "DELTAL": 0.0, "DELTAR": 0.0}
    return Aircraft(
        WG=wing, HT=dict(tail), VT=dict(tail), F=dict(z), A=dict(a), E=dict(z), R=dict(z),
        BD={}, NP=[], NB=[], AERO={"ALSCHD": [0.0], "SREF": 20.0, "CBARR": 1.5, "BLREF": 10.0,
                                    "XCG": 0.4, "ZCG": 0.0, "WT": 1000.0, "MACH": [0.1], "ALT": [0.0]},
        plot_cmp=[1, 1, 1, 1], unit="ft",
    )


def test_flow5_probe_difference_and_antisym_aileron():
    decks = []

    def fake_run(deck):
        decks.append(deck)
        wing = next(w for w in deck["wings"] if w["name"] == "Wing")
        flaps = [s for s in wing["sections"] if "te_flap_deg" in s]
        angle = flaps[0]["te_flap_deg"] if flaps else 0.0
        antisym = bool(flaps and flaps[0].get("te_flap_antisym"))
        return {
            "alpha": [0.0],
            "CL": [0.2 + (0.0 if antisym else 0.01 * angle)],
            "CD": [0.02],
            "Cm": [0.0],
            "Cl": [0.002 * angle if antisym else 0.0],
            "Cn": [0.0],
            "CY": [0.0],
        }

    ac = _ac()
    rows = flow5_controls(ac, [5.0], mesh=("4", "2"), run=fake_run)
    flap = next(r for r in rows if r["surface"] == "flap")
    assert abs(flap["CL"] - 0.01) < 1e-9
    ail = next(r for r in rows if r["surface"] == "aileron")
    assert any(s.get("te_flap_antisym") is True for d in decks for w in d["wings"] for s in w["sections"])
    assert ail["Cl"] is not None
    assert ac.F["DELTA"] == 0.0
```

The wing dict above must satisfy `planform_sections`. If `geometry()` raises on a missing key, add that key to the fixture with a zero of the right shape. Do not weaken `geometry()`.

- [ ] **Step 2: Run test to verify it fails**

Run: `cd Python && python -m pytest tests/test_flow5_controls.py -q`

Expected: FAIL importing `flow5_controls`.

- [ ] **Step 3: Write minimal implementation**

C++ change is limited to reading the three optional keys. A deck without them still solves. After the C++ edit, rebuild `FLOW5/run/flow5_run`.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd Python && python -m pytest tests/test_flow5_controls.py tests/test_flow5_run_cli.py -q`

Expected: PASS. `test_flow5_run_cli.py` still sees a flap-free skeleton deck. Skip the native rebuild assertion only when `FLOW5/run/flow5_run` is absent; say so in the test output. Do not skip `test_flow5_controls.py`.

---

### Task 7: Dispatcher and HTTP endpoint

**Files:**
- Create: `Python/src/aid/control_report.py`
- Modify: `api/aid_web/app.py`, `api/aid_web/analyze.py` (add a function; do not change `analyze()`)
- Test: `api/tests/test_control_derivatives.py`
- Depends on: Tasks 2–6

**Interfaces:**
- Consumes: `handbook_controls`, `datcom_controls`, `tornado_controls`, `avl_controls`, `flow5_controls`, `DEFAULT_DELTAS_DEG`
- Produces: `control_report(ac, solver: str, deltas_deg=None, mesh=None) -> dict`

```python
{
    "solver": "handbook",
    "deltas_deg": [0.0, 5.0],
    "rows": [ ... schema rows ... ],
}
```

`solver` is one of `handbook`, `datcom`, `tornado`, `avl`, `flow5`. Unknown solver raises `ValueError`.

`POST /control-derivatives` body: `{"aircraft": <json>, "solver": "handbook", "deltas_deg": [0, 5]}`. `deltas_deg` may be omitted. Response is the `control_report` dict. Unknown solver is HTTP 400 `{"ok": false, "error": "..."}`, same style as `POST /analyze`. This route does not add fields to the Analyze handshake payload.

- [ ] **Step 1: Write the failing test**

```python
from fastapi.testclient import TestClient

from aid_web.app import app


def test_control_derivatives_handbook_zero_and_five(cessna_aircraft_json):
    client = TestClient(app)
    r = client.post(
        "/control-derivatives",
        json={"aircraft": cessna_aircraft_json, "solver": "handbook", "deltas_deg": [0, 5]},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["solver"] == "handbook"
    assert body["deltas_deg"] == [0.0, 5.0]
    assert len(body["rows"]) == 8
    assert {row["surface"] for row in body["rows"]} == {"flap", "aileron", "elevator", "rudder"}


def test_unknown_solver_is_400(cessna_aircraft_json):
    client = TestClient(app)
    r = client.post(
        "/control-derivatives",
        json={"aircraft": cessna_aircraft_json, "solver": "panel"},
    )
    assert r.status_code == 400
```

Reuse the Cessna loader already used by `api/tests/test_analyze_solvers.py` (`_cessna()` or equivalent). Do not call DATCOM, AVL, Tornado, or flow5 in this test: the request uses `solver: "handbook"` only. Add a unit test of `control_report` that monkeypatches the four heavy functions and checks the dispatcher passes `deltas_deg` through.

- [ ] **Step 2: Run test to verify it fails**

Run: `cd api && python -m pytest tests/test_control_derivatives.py -q`

Expected: FAIL with 404 on `/control-derivatives`.

- [ ] **Step 3: Write minimal implementation**

Wire the five functions. Default mesh from `DEFAULT_MESH` in `analyze.py` for tornado, avl, and flow5.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd api && python -m pytest tests/test_control_derivatives.py tests/test_analyze_solvers.py -q`

Expected: PASS. Analyze responses are unchanged.

---

### Task 8: PySide Controls plot

**Files:**
- Modify: `Python/src/aid_gui/compare_tabs.py` (`_plot_controls`)
- Modify: `Python/src/aid_gui/menus.py`, `Python/src/aid_gui/main_window.py`
- Test: `Python/tests/test_control_deriv_plot.py`
- Depends on: Task 7

**Interfaces:**
- Consumes: `control_report`
- Produces: Analyze menu action `Control derivatives` that runs `control_report` for the solver last used by Analyze, or `handbook` if none has run. Stores `window.last_results["control_derivatives"]`. `_plot_controls` draws `CL`, `Cm`, `Cl`, `Cn`, `CY` against `delta_deg` for that payload. Existing DATCOM high-lift bars stay.

The menu action asks for nothing beyond the default probes `[0, 5]` in this task. A stored deflection of zero is valid input.

- [ ] **Step 1: Write the failing test**

Follow `tests/test_gui_compare_tabs.py`: offscreen `QT_QPA_PLATFORM`, `MainWindow`, load `Python/models/Cessna 172.jsonc`.

```python
def test_controls_tab_plots_probe_curve_at_zero_stored_deflection():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    w.show()
    w.load_aircraft(load_jsonc(models_dir() / "Cessna 172.jsonc"))
    stored = copy.deepcopy(w.aircraft.F["DELTA"])
    w.last_results["control_derivatives"] = control_report(w.aircraft, "handbook", [0.0, 5.0])
    w.set_plot_mode("Aerodynamics")
    controls = next(i for i in range(w.compare_tabs.count()) if w.compare_tabs.tabText(i) == "Controls")
    w.compare_tabs.setCurrentIndex(controls)
    app.processEvents()
    xs = []
    labels = []
    fig = w.compare_tabs.widget(controls).findChild(FigureCanvas).figure
    for ax in fig.axes:
        for line in ax.get_lines():
            labels.append(line.get_label())
            xs.append(list(line.get_xdata()))
    assert any("handbook" in lab and "flap" in lab for lab in labels)
    assert any(x == [0.0, 5.0] for x in xs)
    assert w.aircraft.F["DELTA"] == stored
```

Imports match `tests/test_gui_compare_tabs.py` (`QApplication`, `MainWindow`, `load_jsonc`, `models_dir`) plus `copy` and `control_report`. `FigureCanvas` is `matplotlib.backends.backend_qtagg.FigureCanvasQTAgg`. If the Controls tab index is not 4, select it by `tabText` equal to `Controls`.

- [ ] **Step 2: Run test to verify it fails**

Run: `cd Python && python -m pytest tests/test_control_deriv_plot.py -q`

Expected: FAIL because the series is absent.

- [ ] **Step 3: Write minimal implementation**

Add the series in `_plot_controls` without removing the high-lift bars. Menu action calls `control_report` and refreshes the Controls tab.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd Python && python -m pytest tests/test_control_deriv_plot.py tests/test_gui_compare_tabs.py -q`

Expected: PASS

- [ ] **Step 5: Browser is not this task**

PySide only. Web is Task 9.

---

### Task 9: Web control-derivative chart

**Files:**
- Create: `web/src/controlDeriv.ts`
- Modify: `web/src/Results.tsx`
- Test: `web/src/controlDeriv.test.ts`
- Depends on: Task 7

**Interfaces:**
- Consumes: `POST /control-derivatives` JSON `{solver, deltas_deg, rows}`
- Produces: `chartRows(payload)` grouping finite coefficients by `surface` and coefficient name, skipping `null` and `available: false`

The Aero results pane gets one chart, `dC/dδ` versus probe angle, for the handbook payload fetched with `deltas_deg: [0, 5]` after a successful Analyze of any solver. Use the same axes style as the existing CL chart (ticks and grid). Do not send this payload to the CADAC handshake.

- [ ] **Step 1: Write the failing test**

```typescript
import { chartRows } from "./controlDeriv";

test("zero and five degree probes survive null coefficients", () => {
  const rows = chartRows({
    solver: "handbook",
    deltas_deg: [0, 5],
    rows: [
      { surface: "flap", delta_deg: 0, available: true, reason: "", CL: 0.02, CD: null, Cm: -0.01, CY: null, Cl: null, Cn: null },
      { surface: "flap", delta_deg: 5, available: true, reason: "", CL: 0.02, CD: null, Cm: -0.01, CY: null, Cl: null, Cn: null },
      { surface: "rudder", delta_deg: 0, available: false, reason: "datcom has no rudder namelist", CL: null, CD: null, Cm: null, CY: null, Cl: null, Cn: null },
    ],
  });
  const flapCL = rows.find((s) => s.id === "handbook-flap-CL");
  expect(flapCL?.xs).toEqual([0, 5]);
  expect(flapCL?.ys).toEqual([0.02, 0.02]);
  expect(rows.some((s) => s.id.includes("rudder"))).toBe(false);
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd web && npm test -- src/controlDeriv.test.ts`

Expected: FAIL importing `chartRows`.

- [ ] **Step 3: Write minimal implementation**

`Results.tsx` fetches `/control-derivatives` with the current aircraft and `solver: "handbook"` when results are shown. Plot `chartRows`. If the fetch fails, leave the existing CL/CD/Cm charts up and show the error string already used for handshake failures, or the same pattern.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd web && npm test`

Expected: PASS, including existing `payload.test.ts`.

- [ ] **Step 5: Verify in the browser**

With `./start-web.sh` already up, open the app, load Cessna 172, run Analyze on DATCOM or whichever solver is available, and confirm the new chart has a flap line through probe angles 0 and 5. If the API binary stack is down, say which click could not be completed.

---

### Task 10: Docs

**Files:**
- Modify: `UPDATES.md`, `README.md`
- Depends on: Tasks 1–9

- [ ] **Step 1: Write the failing test**

No new test module. The check is the docs themselves plus the full unit set.

- [ ] **Step 2: Update the docs**

New top `UPDATES.md` entry `1.30.0 - control derivatives at a probe angle`:

- Handbook, DATCOM, Tornado, AVL, and flow5 return flap, aileron, elevator, and rudder slopes per degree at caller-chosen probes, including when the stored deflection is 0
- DATCOM has no rudder row (`datcom has no rudder namelist`)
- `POST /control-derivatives`; PySide Controls tab and the web results chart plot the probes
- Ordinary Analyze coefficients are unchanged

`README.md` Architecture: one sentence on `POST /control-derivatives` and the five sources. Name `UPDATES.md` if that line is not already there.

- [ ] **Step 3: Run the unit set**

Run:

```bash
cd Python && python -m pytest tests/test_control_deriv_schema.py tests/test_handbook_controls.py tests/test_tornado_control_deriv.py tests/test_avl_controls.py tests/test_datcom_controls.py tests/test_flow5_controls.py tests/test_control_deriv_plot.py -q
cd api && python -m pytest tests/test_control_derivatives.py -q
cd web && npm test
```

Expected: PASS

---

## Dispatch

Parent session coordinates. It does not write production code. One fresh implementer per task, then one fresh reviewer per task. Model for every implementer and every reviewer: `grok-4.7-high`.

| Wave | Tasks | Parallel | Then |
|---|---|---|---|
| 0 | 1 | no | reviewer of Task 1 |
| 1 | 2, 3, 4, 5, 6 | yes, five implementers | five reviewers, one per task, in parallel |
| 2 | 7 | no | reviewer of Task 7 |
| 3 | 8, 9 | yes | two reviewers |
| 4 | 10 | no | reviewer of Task 10 |
| 5 | whole branch | no | one reviewer over the union of the diffs |

Reviewer prompt, every task:

- Spec compliance against this plan's task text and Global Constraints
- Stored control angles unchanged
- Ordinary Analyze / `POST /analyze` untouched
- Per-degree units, `null` instead of invented numbers
- File ownership: no edits outside the task's file list
- The named test command was run and passed
- No commit was made

Whole-branch reviewer: the five solvers agree on the record schema, the Controls plot and the web chart both read it, and a stored deflection of zero still produces the 5° probe row.

## Self-review

- Spec coverage: zero stored angle and a nonzero probe are in Tasks 1–6 and both plots. All five models are Tasks 2–6. DATCOM rudder gap is explicit. Analyze gold path is excluded.
- Placeholder scan: no TBD steps. AVL body-axis versus stability-axis lift is decided in Task 4 (`-CZd` at alpha 0, docstring required).
- Type consistency: every solver returns the Task 1 row. `control_report` wraps that list. `chartRows` reads `surface`, `delta_deg`, `available`, and `COEFFS`.
