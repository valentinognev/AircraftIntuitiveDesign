# Forward-Right-Down sign convention, and flow5 lateral coverage — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Put all four solvers' coefficients into one Forward-Right-Down frame, and stop flow5 from being structurally absent from the lateral coefficient panels.

**Architecture:** One new module `aid/axes.py` holds the per-solver sign map and is applied at the solver boundary (`run_datcom`, `coeff_create`, `run_flow5`, `stack_avl_cases`), never in the plots and never in the bare parsers. `compare.py` applies the inverse map to the Python side so MATLAB-gold parity against `Results/matlab/*.json` stays a real check. Separately, the vendored flow5 helper is extended to emit the channels it already computes but never reads, plus its `StabDerivatives`.

**Tech Stack:** Python 3.11+ / numpy / pytest; PySide6; Vite + React 18 + Tailwind 3 + Vitest; C++20 + nlohmann/json (flow5 helper, CMake superbuild).

**Spec:** `docs/superpowers/plans/2026-10-03-frd-sign-convention-design.md` — read it before Task 1.1; it carries the per-solver evidence for every sign in the map.

## Global Constraints

- Sign normalization happens in the **parsers**, not in the plots. `compare.py` applies the inverse map to the Python side before diffing raw MATLAB gold.
- Parser entry points stay raw: `parse_for006`, `parse_st`, `parse_sb`, `parse_run_case_header` are compared key-for-key against gold. Only the `*_run` / `coeff_create` wrappers normalize.
- `CY` and `CC` are **not** flipped by anything. `CC` is already the wind-axis side-force coefficient (`coeff.py:104`).
- `xcp` is **not** flipped. DATCOM prints `XCP = CM/CN` (`datcom.f` `INTERM`, line 1010 of that subroutine); flipping `cn` alone would desynchronise it from its own numerator.
- The raw solver vectors `F`, `M`, `FORCE`, `MOMENTS` are **not** flipped. They are solver internals, already excluded from the Sections table (`compare_tabs.py:522-534`), and `FORCE` is needed to rebuild `cp`. This is the one documented place the pre-normalization frame survives, and the API `raw` payload carries it.
- No coefficient changes magnitude. Sign only.
- `AERO.BETA` is Python-only; `AID.m`'s save list is unchanged, the same treatment `cg_data` and `results` already get.
- `handbook_controls.py` and `stability.py` are **not** touched — the handbook already reports F-R-D (`Lateral_Static_Stability.m:100` gives `Cnβ > 0`, `Clβ < 0`, `CYβ < 0`). `avl_controls.py` and `datcom_controls.py` get a documenting comment only, never a `to_frd` call, because their `Cl`/`Cn` come from sources that are already F-R-D.
- **Non-goals, do not "fix" these in passing.** The `wind1` freestream expression in `tornado/solver.py:149-153` (a transcription of `Matlab/fsroot/code/Tornado/solver.m:131`, missing its `sin(betha)` y-component) stays as it is. DATCOM and AVL do not gain a sideslip capability — their interfaces have none. No DATCOM method, AVL theory, Tornado physics or flow5 solver behaviour changes.
- flow5 keeps its OLS `CLa`/`Cma` keys so `test_e2e_flow5_cessna.py` does not move. `StabDerivatives::Cma` is asserted to agree with the OLS slope inside a tolerance rather than replacing it.
- Tornado's `Cl_a`/`Cn_a`/`Cl_P`/`Cn_P`/`Cl_Q`/`Cn_Q`/`Cl_R`/`Cn_R` and `CX_d`/`CZ_d`/`Cl_d`/`Cn_d` **are** in the map; its `CY_a`/`CY_b`/`CY_P`/`CY_R` and `CY_d` are **not**. Tornado's rate derivatives already agree with AVL numerically, and flipping them would break that.
- DATCOM's `ND`/`NDM` sentinel (`99999`, `datcom_parse.py:7`) must survive `to_frd`/`from_frd` as the same magnitude. `_mask_nd` (`solver_overlay.py:181`) keys on `abs(y) >= 99998`, so a negated sentinel must still mask.
- **Every `git commit` step in this plan waits for explicit user approval.** The repo's agent-permissions rule forbids committing unprompted. Each task ends at a green test run with its changes staged-or-uncommitted as the user prefers.

## Review Focus

1. **A `.mat` model or an old `.jsonc` with no `AERO["BETA"]`.** `load_jsonc` / `load_mat` must yield `0.0`, never `KeyError`. Every shipped model predates this key.
2. **DATCOM's `ND` sentinel after normalization.** `ca` and `cn` are flipped; an `ND` in those columns must come back as `±99999` of the same magnitude and must still be masked out of the plots, not drawn as `-99999`.
3. **flow5's `computeStability` returning NaN or zero.** `FLOW5/run/flow5_run.cpp:226` warns the locked thin-surface VLM2 triple is fragile. A silent `0.0` for `Cnb` would read as a perfectly stable aircraft; the helper must fail loudly or omit the key, never emit a zero.
4. **`FLOW5/run/flow5_run` absent.** The binary is gitignored (`test_flow5_gitignore.py` enforces that). Any new test that shells out to it must `pytest.skip` when it is missing, matching `test_e2e_flow5_cessna.py`.
5. **`AERO` present but `BETA` absent vs `AERO` itself absent.** `Box` and `Sphere` have degenerate geometry; `AERO["BETA"]` must resolve to `0.0` in both the "key missing" and "container missing" cases without a separate special case.

---

## File Structure

| file | responsibility |
|---|---|
| `Python/src/aid/axes.py` | **new.** The only place in the repo that encodes a solver sign. `to_frd` / `from_frd`. |
| `Python/src/aid/datcom_run.py` | wraps `parse_for006` with `to_frd("datcom", ...)` |
| `Python/src/aid/tornado/coeff.py` | returns `to_frd("tornado", out)` |
| `Python/src/aid/flow5_io.py` | wraps with `to_frd("flow5", ...)`; gains `beta` (Tasks 2.3, 3.1) |
| `Python/src/aid/avl_io.py` | `stack_avl_cases` wraps with `to_frd("avl", ...)` (identity, documented) |
| `Python/src/aid/tornado/control_deriv.py` | wraps with `to_frd("tornado", ...)` |
| `Python/src/aid/compare.py` | `_compare_coeffs` applies `from_frd` first |
| `Python/src/aid/aircraft.py` | `AERO["BETA"]` default `0.0` |
| `Python/src/aid/field_docs.py` | the `BETA` JSONC comment string |
| `Python/src/aid/tornado_io.py` | `state["betha"] = radians(AERO["BETA"])` |
| `Python/src/aid_gui/tabs.py` | Aero tab `Beta (deg)` field |
| `Python/src/aid_gui/compare_tabs.py` | `(beta=0)` label on DATCOM/AVL series |
| `web/src/Editor.tsx` | Aero tab beta field |
| `web/src/aeroFigures.ts` | `(beta=0)` label on DATCOM/AVL series |
| `api/aid_web/analyze.py` | accepts `beta` on `/analyze` and `/stability` |
| `FLOW5/flow5-lib/objects3d/analysis3d/planepolar.cpp` | `getVariable` cases 57/58 for `Cx`/`Cz` |
| `FLOW5/run/flow5_run.cpp` | derivatives on, per-point channels, `beta_deg` |

---

### Task 1.1: `aid/axes.py` and its unit tests

**Files:**
- Create: `Python/src/aid/axes.py`
- Test: `Python/tests/test_axes.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `to_frd(solver: str, data: Mapping[str, Any]) -> dict[str, Any]` and `from_frd(solver: str, data: Mapping[str, Any]) -> dict[str, Any]`. Both shallow-copy and return a new dict. `to_frd` multiplies each key present in `_SIGN_MAP[solver]` by its sign; `from_frd` uses the negated sign. An unknown `solver` raises `KeyError`.

- [ ] **Step 1: Write the failing test**

`Python/tests/test_axes.py`:

```python
import numpy as np
import pytest

from aid.axes import from_frd, to_frd


def test_datcom_flips_axial_and_normal_only():
    raw = {"alpha": [0.0, 2.0], "cd": [0.02, 0.03], "cl": [0.1, 0.2],
           "cm": [0.01, 0.0], "cn": [0.1, 0.2], "ca": [0.02, 0.01],
           "xcp": [0.1, 0.0], "cla": [0.09, 0.09], "cyb": [-0.01, -0.01],
           "cnb": [0.001, 0.001], "clb": [-0.002, -0.002]}
    got = to_frd("datcom", raw)
    assert got["ca"] == [-0.02, -0.01]
    assert got["cn"] == [-0.1, -0.2]
    for key in ("cd", "cl", "cm", "xcp", "cla", "cyb", "cnb", "clb", "alpha"):
        assert got[key] == raw[key]
    assert raw["ca"] == [0.02, 0.01], "to_frd must not mutate its input"


def test_tornado_flips_axial_normal_roll_yaw_and_their_derivatives():
    raw = {"CX": -0.04, "CY": 0.0, "CZ": 0.54, "Cl": 0.003, "Cm": -0.95, "Cn": -0.027,
           "CX_a": -0.2, "CZ_a": 4.2, "Cl_a": 0.01, "Cn_a": -0.07,
           "CY_a": 0.0, "CY_b": -0.3, "CY_R": 0.4, "CC": -0.0,
           "Cl_b": 0.05, "Cn_b": -0.25,
           "Cl_P": -0.49, "Cl_Q": 0.0, "Cl_R": 0.04,
           "Cn_P": 0.07, "Cn_Q": 0.0, "Cn_R": -0.29,
           "CX_d": [-1.0], "CZ_d": [-2.0], "Cl_d": [0.5], "Cn_d": [0.6],
           "CY_d": [0.1]}
    got = to_frd("tornado", raw)
    for key in ("CX", "CZ", "Cl", "Cn", "CX_a", "CZ_a", "Cl_a", "Cn_a",
                "Cl_b", "Cn_b", "Cl_P", "Cl_Q", "Cl_R", "Cn_P", "Cn_Q", "Cn_R",
                "CX_d", "CZ_d", "Cl_d", "Cn_d"):
        assert got[key] == pytest.approx(-raw[key]), key
    for key in ("CY", "Cm", "CY_a", "CY_b", "CY_R", "CC", "CY_d"):
        assert got[key] == pytest.approx(raw[key]), key
    assert got["Cl_d"] == [-0.5] and got["Cn_d"] == [-0.6]
    assert got["CY_d"] == [0.1]


def test_avl_and_flow5_are_identity():
    raw = {"CXtot": 0.03, "CZtot": -0.6, "CYtot": 0.0, "Cltot": 0.0,
           "Cmtot": -0.2, "Cntot": 0.0, "CYb": -0.3, "Cnb": 0.17, "Clb": -0.03}
    for solver in ("avl", "flow5"):
        assert to_frd(solver, raw) == raw


def test_round_trip_is_identity_for_every_solver():
    raw = {"CX": -0.04, "CZ": 0.54, "Cl": 0.003, "Cn": -0.027,
           "cn": 0.1, "ca": 0.02, "CXtot": 0.03}
    for solver in ("avl", "datcom", "tornado", "flow5"):
        assert from_frd(solver, to_frd(solver, raw)) == raw


def test_unknown_solver_raises():
    with pytest.raises(KeyError):
        to_frd("handbook", {"CL": 1.0})
    with pytest.raises(KeyError):
        from_frd("vlm2", {"CL": 1.0})


def test_missing_key_is_absent_not_zero():
    got = to_frd("tornado", {"CL": 0.5})
    assert got == {"CL": 0.5}
    assert "CZ" not in got


def test_structured_values_pass_through_by_identity():
    surface = [{"name": "aileron", "angle": 0.0}]
    high_lift = [{"config": "flap 10", "delta": 10.0, "dcl": [0.3]}]
    cp = np.zeros((4, 3))
    raw = {"surface": surface, "high_lift": high_lift, "cp": cp, "CZ": 0.5}
    got = to_frd("tornado", raw)
    assert got["surface"] is surface
    assert got["high_lift"] is high_lift
    assert got["cp"] is cp
    assert got["CZ"] == -0.5


def test_nd_sentinel_keeps_its_magnitude():
    raw = {"ca": [0.02, 99999.0], "cn": [99999.0, 0.1], "cd": [0.02, 99999.0]}
    got = to_frd("datcom", raw)
    assert got["ca"] == [-0.02, -99999.0]
    assert got["cn"] == [-99999.0, -0.1]
    assert got["cd"] == [0.02, 99999.0]
    masked = np.abs(np.asarray(got["ca"], dtype=float)) >= 99998
    assert list(masked) == [False, True], "a negated ND must still mask"


def test_numpy_arrays_stay_arrays():
    raw = {"CZ": np.array([0.5, 0.6])}
    got = to_frd("tornado", raw)
    assert isinstance(got["CZ"], np.ndarray)
    assert got["CZ"].tolist() == [-0.5, -0.6]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd Python && python -m pytest tests/test_axes.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'aid.axes'`

- [ ] **Step 3: Implement `Python/src/aid/axes.py`**

Module docstring states the convention and cites the evidence per solver (the measured table from the spec). Then:

```python
from __future__ import annotations

from typing import Any, Mapping

__all__ = ["to_frd", "from_frd"]

_SIGN_MAP: dict[str, dict[str, int]] = {
    "avl": {},
    "datcom": {"ca": -1, "cn": -1},
    "tornado": {
        "CX": -1, "CZ": -1, "Cl": -1, "Cn": -1,
        "CX_a": -1, "CZ_a": -1, "Cl_a": -1, "Cn_a": -1,
        "Cl_b": -1, "Cn_b": -1,
        "Cl_P": -1, "Cl_Q": -1, "Cl_R": -1,
        "Cn_P": -1, "Cn_Q": -1, "Cn_R": -1,
        "CX_d": -1, "CZ_d": -1, "Cl_d": -1, "Cn_d": -1,
    },
    "flow5": {},
}
```

`_convert(solver, data, negate: bool)` resolves `_SIGN_MAP[solver]` (letting the `KeyError` from an unknown solver escape), shallow-copies `data`, and for each `(key, sign)` present in `data` applies `sign * value` for a scalar or a list of numbers, and `sign * value` for a numpy array, leaving any other value type untouched. `to_frd` calls it with `negate=False`; `from_frd` with `negate=True`.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd Python && python -m pytest tests/test_axes.py -q`
Expected: PASS, 9 passed

- [ ] **Step 5: Verify no existing test moved**

Run: `cd Python && python -m pytest tests/ -q --ignore=tests/test_matlab_batch_all.py`
Expected: PASS, no new failures

- [ ] **Step 6: Commit** (needs user approval)

```bash
git add Python/src/aid/axes.py Python/tests/test_axes.py
git commit -m "feat: add aid/axes.py, the single home for solver sign conventions"
```

---

### Task 1.2: Apply the map at the solver boundary

**Files:**
- Modify: `Python/src/aid/datcom_run.py:25`
- Modify: `Python/src/aid/tornado/coeff.py:226` (the `return out`)
- Modify: `Python/src/aid/flow5_io.py:110-111`
- Modify: `Python/src/aid/avl_io.py:312-323` (`stack_avl_cases`)
- Modify: `Python/src/aid/tornado/control_deriv.py:146-148`
- Test: `Python/tests/test_axes_wiring.py`

**Interfaces:**
- Consumes: `to_frd` from Task 1.1.
- Produces: `run_datcom`, `coeff_create`, `run_flow5`, `stack_avl_cases` and `tornado.control_deriv` all return Forward-Right-Down dictionaries. No signature changes.

- [ ] **Step 1: Write the failing test**

`Python/tests/test_axes_wiring.py`, following the gold-fixture style of `tests/test_datcom_run_cessna.py`:

```python
import json

import numpy as np
import pytest

from aid.aircraft import load_jsonc
from aid.avl_io import run_avl_full
from aid.datcom_parse import parse_for006
from aid.datcom_run import run_datcom
from aid.paths import results_dir
from aid.axes import from_frd

GOLD = results_dir() / "matlab" / "Cessna 172"


def _cessna():
    return load_jsonc(pathlib_Path("models/Cessna 172.jsonc"))


def test_run_datcom_flips_ca_and_cn(tmp_path):
    ac = _cessna()
    gold = json.loads((GOLD / "datcom.json").read_text())
    ac.AERO["ALSCHD"] = list(gold["alpha"])
    got = run_datcom(ac, tmp_path / "w")
    assert np.allclose(got["ca"], -np.asarray(gold["ca"]), atol=1e-6)
    assert np.allclose(got["cn"], -np.asarray(gold["cn"]), atol=1e-6)
    assert np.allclose(got["cl"], gold["cl"], atol=1e-6)
    assert np.allclose(got["cd"], gold["cd"], atol=1e-6)
    assert np.allclose(got["xcp"], gold["xcp"], atol=1e-6)


def test_run_datcom_is_the_inverse_of_the_bare_parser(tmp_path):
    ac = _cessna()
    got = run_datcom(ac, tmp_path / "w")
    raw = parse_for006((tmp_path / "w" / "for006.dat").read_text())
    for key in ("alpha", "cd", "cl", "cm", "cn", "ca", "xcp", "cla", "cma", "cyb", "cnb", "clb"):
        assert np.allclose(from_frd("datcom", got)[key], raw[key], atol=1e-9), key


def test_tornado_coeff_create_flips_cz_and_cn():
    from aid.tornado.boundary import set_boundary
    from aid.tornado.coeff import coeff_create
    from aid.tornado.lattice import lattice_setup
    from aid.tornado.solver import solve
    from aid.tornado_io import tornado_io

    ac = _cessna()
    geo, state = tornado_io(ac, ("10", "5"))
    lattice, ref = lattice_setup(geo, state, 0)
    lattice = set_boundary(lattice, geo, state)
    raw = solve(state, geo, lattice)
    got = coeff_create(raw, lattice, state, ref, geo)
    assert got["CZ"] < 0.0, "lift must be negative z in Forward-Right-Down"
    assert got["CX"] < 0.0, "drag must be negative x in Forward-Right-Down"
    assert got["CL"] > 0.0 and got["CD"] > 0.0, "wind-axis signs are untouched"
    assert got["CZ"] == pytest.approx(-raw["FORCE"][0][2] / (0.5 * state["rho"] * state["AS"] ** 2 * ref["S_ref"]))


def test_avl_stack_cases_is_identity(tmp_path):
    ac = _cessna()
    got = run_avl_full(ac, ("10", "10"), tmp_path)
    for key in ("CXtot", "CZtot", "CYtot", "Cltot", "Cmtot", "Cntot"):
        assert got[key] == from_frd("avl", got)[key]
    assert all(v <= 1e-9 for v in got["CZtot"]), "AVL is already Forward-Right-Down"
```

Use `Path(__file__).resolve().parents[1] / "models" / "Cessna 172.jsonc"` for the model path, matching how `tests/conftest.py` resolves fixtures.

- [ ] **Step 2: Run test to verify it fails**

Run: `cd Python && python -m pytest tests/test_axes_wiring.py -q`
Expected: FAIL — `test_run_datcom_flips_ca_and_cn` sees `ca` equal to the gold, not negated.

- [ ] **Step 3: Wire each call site**

- `datcom_run.py:25` becomes `return to_frd("datcom", parse_for006(out.read_text()))`.
- `tornado/coeff.py` returns `to_frd("tornado", out)` in place of `return out`.
- `flow5_io.py:110` becomes `return to_frd("flow5", run_flow5_native(write_flow5_deck(ac, mesh), timeout=timeout))`.
- `avl_io.py` `stack_avl_cases` returns `to_frd("avl", out)`; add a one-line comment that AVL is natively F-R-D so the map is empty.
- `tornado/control_deriv.py:146-148` wraps its returned dict with `to_frd("tornado", ...)`.
- `avl_controls.py` and `datcom_controls.py` get **no** `to_frd` call — add only a short comment at `avl_controls.py:149` and `datcom_controls.py:107-109` recording that their `CY`/`Cl`/`Cn` already arrive in F-R-D (AVL `.sb` tags; DATCOM's lowercase parser keys), so a future reader does not wrap them by reflex.
- Add `from aid.axes import to_frd` to each file that needs it.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd Python && python -m pytest tests/test_axes_wiring.py -q`
Expected: PASS

- [ ] **Step 5: Verify the control-derivative probe too**

Run: `cd Python && python -m pytest tests/test_control_deriv_schema.py tests/test_tornado_control_deriv.py tests/test_avl_controls.py tests/test_datcom_controls.py -q`
Expected: PASS. If `test_tornado_control_deriv.py` pins raw `Cl`/`Cn`, update it to the F-R-D value — that is the intended behaviour change, not a regression.

- [ ] **Step 6: Run the full Python suite**

Run: `cd Python && python -m pytest tests/ -q --ignore=tests/test_matlab_batch_all.py`
Expected: PASS except for the known worktree-only `tests/test_paths.py::test_paths_resolve` failure if run from `.worktrees/`.

- [ ] **Step 7: Commit** (needs user approval)

```bash
git add Python/src/aid/datcom_run.py Python/src/aid/tornado/coeff.py \
        Python/src/aid/flow5_io.py Python/src/aid/avl_io.py \
        Python/src/aid/tornado/control_deriv.py Python/tests/test_axes_wiring.py
git commit -m "fix: return every solver's coefficients in Forward-Right-Down"
```

---

### Task 1.3: Keep MATLAB-gold parity honest

**Files:**
- Modify: `Python/src/aid/compare.py:240-248` (`_compare_coeffs`)
- Test: `Python/tests/test_compare_sign_roundtrip.py`

**Interfaces:**
- Consumes: `from_frd` from Task 1.1; the F-R-D runner output from Task 1.2.
- Produces: unchanged `_compare_coeffs` signature. `Results/python/<name>/*.json` stays F-R-D; only the in-memory comparison happens in raw space.

- [ ] **Step 1: Write the failing test**

`Python/tests/test_compare_sign_roundtrip.py`:

```python
import json

import numpy as np
import pytest

from aid.compare import _compare_avl, _compare_coeffs, _compare_datcom, _compare_tornado
from aid.datcom_parse import parse_for006


def test_compare_datcom_accepts_normalized_python():
    gold = json.loads((RESULTS / "matlab" / "Cessna 172" / "datcom.json").read_text())
    normalized = {k: (np.asarray(v) * -1 if k in ("ca", "cn") else v)
                  for k, v in gold.items()}
    assert _compare_coeffs("datcom", normalized, gold) is True


def test_compare_datcom_rejects_a_double_flip():
    gold = json.loads((RESULTS / "matlab" / "Cessna 172" / "datcom.json").read_text())
    assert _compare_coeffs("datcom", gold, gold) is False


def test_compare_tornado_and_avl_still_pass_against_gold():
    for solver in ("tornado", "avl"):
        gold = json.loads((RESULTS / "matlab" / "Cessna 172" / f"{solver}.json").read_text())
        python_result = _to_raw_space(solver, gold)
        assert _compare_coeffs(solver, python_result, gold) is True


def test_unknown_solver_still_raises():
    with pytest.raises(ValueError):
        _compare_coeffs("vlm2", {}, {})
```

where `_to_raw_space(solver, gold)` applies the solver's inverse map with `from_frd`, and `RESULTS` is `results_dir() / "matlab"`. Keep the existing tolerance behaviour: the helpers under test are the private comparators, so mirror what `compare.py` already imports.

- [ ] **Step 2: Run test to verify it fails**

Run: `cd Python && python -m pytest tests/test_compare_sign_roundtrip.py -q`
Expected: FAIL — `test_compare_datcom_accepts_normalized_python` fails because `_compare_coeffs` compares raw keys without inverting.

- [ ] **Step 3: Apply the inverse in `_compare_coeffs`**

Add `python = from_frd(solver, python)` as the first statement of `_compare_coeffs`, after the `None` guard. Do not touch `_compare_datcom`, `_compare_tornado` or `_compare_avl` — they receive raw values from here on.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd Python && python -m pytest tests/test_compare_sign_roundtrip.py -q`
Expected: PASS

- [ ] **Step 5: Verify the four primary compare aircraft still pass**

Run: `cd Python && python scripts/run_all.py --aircraft "Cessna 172" --aircraft Navion`
Expected: `datcom`, `tornado`, `avl` all `pass: true` in `Results/compare/*.json`. If DATCOM `Navion` fails, that is the pre-existing SIGSEGV recorded in `UPDATES.md`, not this change.

- [ ] **Step 6: Run the full Python suite**

Run: `cd Python && python -m pytest tests/ -q --ignore=tests/test_matlab_batch_all.py`
Expected: PASS

- [ ] **Step 7: Commit** (needs user approval)

```bash
git add Python/src/aid/compare.py Python/tests/test_compare_sign_roundtrip.py
git commit -m "fix: compare MATLAB gold in raw space so parity survives normalization"
```

---

### Task 1.4: Prove the four solvers now agree on sign

**Files:**
- Test: `Python/tests/test_frd_sign_agreement.py`
- Modify (only if a test fails for a modelling reason, not a sign reason): none. This task is a test-only deliverable; if a sign assertion fails, the sign map in `aid/axes.py` is wrong — fix it there and say so in the commit body.

**Interfaces:**
- Consumes: F-R-D output from all four runner entry points.
- Produces: the regression guard for the whole of Deliverable 1.

- [ ] **Step 1: Write the test**

`Python/tests/test_frd_sign_agreement.py`. One fixture runs Cessna 172 through DATCOM, AVL and Tornado once and yields the three result dicts; the rest are sign and order-of-magnitude assertions on that fixture.

```python
import numpy as np
import pytest

from aid.aircraft import load_jsonc
from aid.avl_io import run_avl_full
from aid.datcom_run import run_datcom
from aid.tornado.boundary import set_boundary
from aid.tornado.coeff import coeff_create
from aid.tornado.lattice import lattice_setup
from aid.tornado.solver import solve
from aid.tornado_io import tornado_io


@pytest.fixture(scope="module")
def three_solvers(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("frd")
    ac = load_jsonc(MODELS / "Cessna 172.jsonc")
    datcom = run_datcom(ac, tmp / "datcom")
    avl = run_avl_full(ac, ("10", "10"), tmp / "avl")
    geo, state = tornado_io(ac, ("10", "5"))
    lattice, ref = lattice_setup(geo, state, 0)
    lattice = set_boundary(lattice, geo, state)
    tornado = coeff_create(solve(state, geo, lattice), lattice, state, ref, geo)
    return datcom, avl, tornado


def _mid(avl):
    i = len(avl["alpha"]) // 2
    return {k: v[i] for k, v in avl.items() if isinstance(v, list) and len(v) == len(avl["alpha"])}


def test_axial_force_agrees_in_sign(three_solvers):
    datcom, avl, tornado = three_solvers
    a = _mid(avl)
    signs = {np.sign(datcom["ca"][len(datcom["alpha"]) // 2]),
             np.sign(a["CXtot"]),
             np.sign(tornado["CX"])}
    assert len(signs) == 1, f"axial force signs disagree: {signs}"


def test_normal_force_agrees_in_sign(three_solvers):
    datcom, avl, tornado = three_solvers
    a = _mid(avl)
    signs = {np.sign(datcom["cn"][len(datcom["alpha"]) // 2]),
             np.sign(a["CZtot"]),
             np.sign(tornado["CZ"])}
    assert len(signs) == 1, f"normal force signs disagree: {signs}"


def test_beta_derivatives_agree_in_sign(three_solvers):
    datcom, avl, tornado = three_solvers
    a = _mid(avl)
    for label, d, v, t in (
        ("yaw", datcom["cnb"][0] * 180 / np.pi, a["Cnb"], tornado["Cn_b"]),
        ("roll", datcom["clb"][0] * 180 / np.pi, a["Clb"], tornado["Cl_b"]),
        ("side", datcom["cyb"][0] * 180 / np.pi, a["CYb"], tornado["CY_b"]),
    ):
        signs = {np.sign(d), np.sign(v), np.sign(t)}
        assert len(signs) == 1, f"{label} beta-derivative signs disagree: {signs}"


def test_damping_derivatives_still_agree(three_solvers):
    _, avl, tornado = three_solvers
    a = _mid(avl)
    assert np.sign(a["Clp"]) == np.sign(tornado["Cl_P"]) < 0
    assert np.sign(a["Cnr"]) == np.sign(tornado["Cn_R"]) < 0
    assert np.sign(a["Cmq"]) == np.sign(tornado["Cm_Q"]) < 0


def test_frd_physical_signs_hold(three_solvers):
    _, avl, tornado = three_solvers
    a = _mid(avl)
    assert a["Cnb"] > 0.0, "weathercock stability: Cn_beta must be positive"
    assert a["Clb"] < 0.0, "dihedral effect: Cl_beta must be negative"
    assert a["CYb"] < 0.0, "side force opposes sideslip"
    assert a["Clp"] < 0.0 and a["Cnr"] < 0.0 and a["Cmq"] < 0.0
    assert tornado["Cn_b"] > 0.0 and tornado["Cl_b"] < 0.0 and tornado["CY_b"] < 0.0


def test_lateral_derivatives_are_the_same_order_as_avl(three_solvers):
    _, avl, tornado = three_solvers
    a = _mid(avl)
    for label, v, t in (("Cnb", a["Cnb"], tornado["Cn_b"]),
                        ("Clb", a["Clb"], tornado["Cl_b"]),
                        ("CYb", a["CYb"], tornado["CY_b"])):
        ratio = abs(t / v)
        assert 0.2 < ratio < 5.0, f"{label}: Tornado {t} vs AVL {v}"
```

`MODELS` is `Path(__file__).resolve().parents[1] / "models"`. If the DATCOM binary or the Cessna gold is unavailable, `pytest.skip` at the top of the fixture rather than failing.

- [ ] **Step 2: Run test to verify it passes**

Run: `cd Python && python -m pytest tests/test_frd_sign_agreement.py -q`
Expected: PASS — this task's tests are written against already-normalized code, so the RED step is "run it against `git stash`ed Tasks 1.2/1.3 and watch it go green", which the reviewer should confirm.

If any assertion fails, the map is wrong. Fix `aid/axes.py`, re-run, and record which key moved.

- [ ] **Step 3: Confirm the test actually has teeth**

Run: `cd Python && python -m pytest tests/test_frd_sign_agreement.py -q -k beta_derivatives` with `to_frd("tornado", ...)` temporarily removed from `coeff.py`.
Expected: FAIL on `test_beta_derivatives_agree_in_sign`. Restore the change.

- [ ] **Step 4: Run the full Python suite**

Run: `cd Python && python -m pytest tests/ -q --ignore=tests/test_matlab_batch_all.py`
Expected: PASS

- [ ] **Step 5: Commit** (needs user approval)

```bash
git add Python/tests/test_frd_sign_agreement.py
git commit -m "test: pin cross-solver sign agreement in Forward-Right-Down"
```

---

### Task 2.0: Spike — can flow5 give us beta and derivatives?

**Files:**
- Create: `/tmp/opencode/flow5_spike/` (scratch, outside the repo)
- Modify: `docs/superpowers/plans/2026-10-03-frd-sign-convention-design.md` — fill in the three Spike answers

**Interfaces:**
- Consumes: `FLOW5/run/flow5_run.cpp`, `FLOW5/flow5-lib/`.
- Produces: a written go/no-go for each of the spec's three spikes. No production code. Nothing else in this plan may start until spike 1 and spike 2 are answered.

- [ ] **Step 1: Answer spike 1 — is beta drivable?**

Read `PlaneTask::setOppList` and `PlanePolar::setType` in `FLOW5/flow5-lib/`, looking for a beta list or a per-opp beta setter. Then write a scratch C++-free probe: build a deck JSON by hand with `"beta_deg": 5.0` added under `polar`, run `FLOW5/run/flow5_run --deck`, and see whether the helper rejects the key, ignores it, or changes the output. Record which.

Expected finding, given `flow5_run.cpp:254` hard-codes `setType(xfl::T1POLAR)`: the key is ignored and every point comes back at beta = 0. **RESOLVED — half right.** The key IS ignored (byte-identical output), but beta IS drivable via `PlanePolar::setBetaSpec` (`polar3d.h:213`), not via the opp list; see the `### Spikes` section of the design doc.

- [ ] **Step 2: Answer spike 2 — are the derivatives finite?**

Write a scratch copy of `flow5_run.cpp` with `setComputeDerivatives(true)` and a `for` loop printing every `StabDerivatives` field for the Cessna deck at alpha = 0. Compile it alone against the installed `libflow5-lib` (do not touch `FLOW5/run/flow5_run.cpp` yet). Record whether each field is finite, and the sign of `Clb`, `Cnb`, `CYb`.

Expected finding: finite, with `Cnb > 0`, `Clb < 0`, `CYb < 0` (the same physical signs AVL gives), which also answers spike 3.

- [ ] **Step 3: Answer spike 3 — are `Clb`/`Cnb` already standard?**

Read `computeStabilityDerivatives` in `FLOW5/flow5-lib/analysis3d/panelanalysis.cpp` and check whether it fills `SD.Clb`/`SD.Cnb` from `AeroForces::Cli()`/`Cni()` (standard) or from the raw algebraic `Mi.x`/`Mi.z` (needs a flip).

- [ ] **Step 4: Write the answers into the design doc**

Replace the three bullet questions in the spec's `### Spikes` section with the findings and a `GO` / `NO-GO` per spike. If spike 1 is `NO-GO`, state that Deliverable 3's flow5 half is deferred and Deliverable 2 ships derivatives-only.

- [ ] **Step 5: No commit** — the design doc edit goes in with Task 2.1's commit.

---

### Task 2.1: flow5 per-point force and moment channels

**Files:**
- Modify: `FLOW5/flow5-lib/objects3d/analysis3d/planepolar.cpp` — `getVariable` gains `case 57` / `case 58`; `s_VariableNames` (line 509) gains two entries
- Modify: `FLOW5/run/flow5_run.cpp` — `polar_to_json` (line 349) and `skeleton_output` (line 299)
- Test: `Python/tests/test_flow5_force_channels.py`

**Interfaces:**
- Consumes: spike 2/3 answers (only to confirm signs; the channels themselves do not depend on them).
- Produces: `run_flow5` returns, in addition to today's keys, `beta`, `CY`, `Cl`, `Cn`, `Cx`, `Cz`, `CDvis`, `CDind` — all arrays of length `len(alpha)`. `Cx`/`Cz` are pre-normalization (aft-positive / up-positive); Task 2.3 puts them in the sign map.

- [ ] **Step 1: Write the failing test**

`Python/tests/test_flow5_force_channels.py`:

```python
import numpy as np
import pytest

from aid.aircraft import load_jsonc
from aid.flow5_io import run_flow5

pytestmark = pytest.mark.skipif(
    not FLOW5_BIN.is_file(), reason="flow5 helper not built"
)


@pytest.fixture(scope="module")
def cessna(tmp_path_factory):
    ac = load_jsonc(MODELS / "Cessna 172.jsonc")
    return run_flow5(ac, ("10", "10"))


def test_flow5_emits_the_new_channels(cessna):
    for key in ("beta", "CY", "Cl", "Cn", "Cx", "Cz", "CDvis", "CDind"):
        assert key in cessna, key
        assert len(cessna[key]) == len(cessna["alpha"]), key


def test_flow5_existing_channels_are_unchanged(cessna):
    assert cessna["CL"][0] == pytest.approx(-0.2352703035574828, abs=1e-6)
    assert cessna["CD"][0] == pytest.approx(0.0024455127232803743, abs=1e-9)
    assert cessna["Cm"][0] == pytest.approx(0.06768149276937234, abs=1e-9)


def test_flow5_lateral_channels_are_zero_at_beta_zero(cessna):
    # atol=1e-5, NOT 1e-9: these are panel-method round-off residuals, not zeros.
    # Measured max|v| over the 17 Cessna alphas at beta = 0:
    #   CY 6.750e-07, Cl 6.662e-08, Cn 3.767e-07  -- all fail atol=1e-9.
    assert np.allclose(cessna["beta"], 0.0)
    for key in ("CY", "Cl", "Cn"):
        assert np.allclose(cessna[key], 0.0, atol=1e-5), key


def test_flow5_cx_is_aft_positive_and_cz_is_up_positive(cessna):
    # Pre-normalization frame: x aft, z up. Settled by Task 2.0 spike 4 -- do NOT
    # assert a bare sign at one alpha. Raw Cx = CD*cos(a) - CL*sin(a), so it is
    # aft-positive only while CD*cos(a) > CL*sin(a) and goes NEGATIVE at high alpha
    # (measured: positive at just 2 of the 17 sweep alphas, alpha = -1 and 0;
    # -0.1828 at alpha = +12). A single-point sign test would pass by luck.
    a = np.deg2rad(np.asarray(cessna["alpha"]))
    assert np.allclose(np.asarray(cessna["Cx"]), np.asarray(cessna["CD"]) * np.cos(a)
                       - np.asarray(cessna["CL"]) * np.sin(a), atol=1e-12)
    # Aft-positive, checked where the identity is unambiguous: alpha = 0, where
    # Cx reduces to CD exactly (measured Cx = +0.0012434 vs CD = +0.0012434).
    i = int(np.argmin(np.abs(np.asarray(cessna["alpha"]))))
    assert cessna["Cx"][i] > 0.0, "at alpha = 0 the axial component reduces to CD, so it is aft-positive"
    # Up-positive: Cz is +1.1948 at alpha = +12 with CL = +1.2067.
    j = int(np.argmax(cessna["CL"]))
    assert cessna["Cz"][j] > 0.0
    # And note Cz == CL only at alpha = 0 -- do not assert it across the sweep.
    # Measured: Cz - CL is 4.8e-13 at alpha = 0 but 1.2e-2 at alpha = +12.


def test_flow5_cd_splits_into_viscous_and_induced(cessna):
    total = np.asarray(cessna["CDvis"]) + np.asarray(cessna["CDind"])
    assert np.allclose(total, cessna["CD"], atol=1e-9)
```

`FLOW5_BIN` is `flow5_bin()` from `aid.paths`; `MODELS` is `Path(__file__).resolve().parents[1] / "models"`. `OLS_CMA` is `-1.576986273169212`.

- [ ] **Step 2: Run test to verify it fails**

Run: `cd Python && python -m pytest tests/test_flow5_force_channels.py -q`
Expected: FAIL — `test_flow5_emits_the_new_channels` reports `beta` missing.

- [ ] **Step 3: Add the two `getVariable` cases**

In `planepolar.cpp`, after `case 56` on line **651** and before `default:` (verified: `case 56: return m_CoG_z.at(index) * Units::mtoUnit();`):

```cpp
        case 57: return m_AF.at(index).Cx();
        case 58: return m_AF.at(index).Cz();
```

In `s_VariableNames` (line 509), append `"Cx", "Cz"` to the initialiser list so `listVariable` stays index-aligned.

- [ ] **Step 4: Emit the channels from the helper**

In `polar_to_json` (`flow5_run.cpp:349`), add `beta` from variable 2, `CDvis` from 6, `CDind` from 7, `CY` from 8, `Cl` from 12, `Cn` from 13, `Cx` from 57, `Cz` from 58, each built in the same `out["key"].push_back(...)` loop as `alpha`/`CL`/`CD`/`Cm`. Add the same eight keys to `skeleton_output` (line 299) with a `0.0` seed so the failure path keeps the schema.

- [ ] **Step 5: Rebuild the helper**

Run: `cmake --build FLOW5/build -j`
Expected: `flow5_run` relinks; `planepolar.cpp` and `flow5_run.cpp` are the only recompiled objects.

- [ ] **Step 6: Run test to verify it passes**

Run: `cd Python && python -m pytest tests/test_flow5_force_channels.py -q`
Expected: PASS, 5 passed

- [ ] **Step 7: Verify the pre-existing flow5 e2e still passes**

Run: `cd Python && python -m pytest tests/test_e2e_flow5_cessna.py tests/test_flow5_run_wrapper.py -q`
Expected: PASS

- [ ] **Step 8: Commit** (needs user approval)

```bash
git add FLOW5/flow5-lib/objects3d/analysis3d/planepolar.cpp FLOW5/run/flow5_run.cpp \
        Python/tests/test_flow5_force_channels.py \
        docs/superpowers/plans/2026-10-03-frd-sign-convention-design.md
git commit -m "feat: emit flow5's lateral, axial and drag-split channels"
```

---

### Task 2.2: flow5 stability derivatives

**Files:**
- Modify: `FLOW5/run/flow5_run.cpp` — line 284 `setComputeDerivatives(false)` -> `true`; dump `StabDerivatives` after `pPlaneTask->run()`
- Test: `Python/tests/test_flow5_derivatives.py`

**Interfaces:**
- Consumes: Task 2.1's rebuilt helper.
- Produces: `run_flow5` additionally returns scalars `CXa`, `CZa`, `CYb`, `CYp`, `CYr`, `Clb`, `Clp`, `Clr`, `Cnb`, `Cnp`, `Cnr`, `XNP`. `CLa` and `Cma` keep their OLS values.

- [ ] **Step 1: Write the failing test**

`Python/tests/test_flow5_derivatives.py`:

```python
import numpy as np
import pytest

from aid.aircraft import load_jsonc
from aid.avl_io import run_avl_full
from aid.flow5_io import run_flow5

pytestmark = pytest.mark.skipif(not FLOW5_BIN.is_file(), reason="flow5 helper not built")

DERIVS = ("CXa", "CZa", "CYb", "CYp", "CYr", "Clb", "Clp", "Clr", "Cnb", "Cnp", "Cnr", "XNP")


@pytest.fixture(scope="module")
def pair(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("f5d")
    ac = load_jsonc(MODELS / "Cessna 172.jsonc")
    return run_flow5(ac, ("10", "10")), run_avl_full(ac, ("10", "10"), tmp / "avl")


def test_flow5_emits_finite_derivatives(pair):
    flow5, _ = pair
    for key in DERIVS:
        assert key in flow5, key
        value = float(flow5[key])
        assert np.isfinite(value), f"{key} is not finite: {value}"


def test_flow5_beta_derivatives_hold_the_physical_signs(pair):
    flow5, avl = pair
    a = {k: v[len(avl["alpha"]) // 2] for k, v in avl.items() if isinstance(v, list)}
    assert flow5["Cnb"] > 0.0 and np.sign(flow5["Cnb"]) == np.sign(a["Cnb"])
    assert flow5["Clb"] < 0.0 and np.sign(flow5["Clb"]) == np.sign(a["Clb"])
    assert flow5["CYb"] < 0.0 and np.sign(flow5["CYb"]) == np.sign(a["CYb"])


def test_flow5_damping_derivatives_are_negative(pair):
    flow5, _ = pair
    assert flow5["Clp"] < 0.0, "roll damping must be negative"
    assert flow5["Cnr"] < 0.0, "yaw damping must be negative"
    # CZa < 0 is CORRECT and is the F-R-D expectation: flow5's raw CZa is
    # -5.2562 at alpha = 0, and CZa = -CLa - CD exactly (Task 2.0 spike 2,
    # residual flat within 9.0e-5 over 14 central-difference points), matching the gold's
    # Longitudinal_Dynamic_Stability.m:35. CZa is an ALPHA derivative, not a
    # q-derivative -- the original assertion message here was simply wrong.
    assert flow5["CZa"] < 0.0, "CZa = -CLa - CD is negative; CZa takes no sign-map entry"


def test_flow5_lateral_derivatives_are_the_same_order_as_avl(pair):
    flow5, avl = pair
    a = {k: v[len(avl["alpha"]) // 2] for k, v in avl.items() if isinstance(v, list)}
    for key in ("Cnb", "Clb", "CYb"):
        assert 0.1 < abs(flow5[key] / a[key]) < 10.0, key


def test_flow5_cma_agrees_with_the_ols_slope(pair):
    flow5, _ = pair
    assert flow5["Cma"] == pytest.approx(OLS_CMA, rel=0.25)


def test_flow5_ols_channels_are_unchanged(pair):
    flow5, _ = pair
    assert flow5["CLa"] == pytest.approx(5.1769701450904195, rel=1e-6)
    assert flow5["Cma"] == pytest.approx(-1.576986273169212, rel=1e-6)
```

`OLS_CMA` is `-1.576986273169212`. Fix the `test_flow5_damping_derivatives_are_negative` assertion on `Cmq`: use `assert flow5["CZa"] < 0.0` instead, since `Cmq` is not part of this task's deliverable.

- [ ] **Step 2: Run test to verify it fails**

Run: `cd Python && python -m pytest tests/test_flow5_derivatives.py -q`
Expected: FAIL — `CXa` missing.

- [ ] **Step 3: Enable derivatives and dump them**

In `flow5_run.cpp` line 284, change to `pPlaneTask->setComputeDerivatives(true);`. After `pPlaneTask->run()` succeeds, iterate `pPlaneTask->planeOppList()`. **`PlaneTask::storePOpp` only retains opps when `m_bKeepOpps` is set** (`planetask.cpp:2267-2271`), so you must also call `pPlaneTask->setKeepOpps(true)` (`Task3D`, `api/task3d.h:111`) before `run()`, or the list is empty and you will silently emit nothing. Verified end-to-end in Task 2.0. and copy the reference-point entry's `m_SD` fields into the JSON as the scalars listed in Interfaces. **If any field is not finite, return a non-zero exit and an error string rather than writing `0.0`** — a silent zero reads as a perfectly stable aircraft (Review Focus item 3).

- [ ] **Step 4: Rebuild**

Run: `cmake --build FLOW5/build -j`
Expected: `flow5_run` relinks.

- [ ] **Step 5: Run test to verify it passes**

Run: `cd Python && python -m pytest tests/test_flow5_derivatives.py -q`
Expected: PASS. If `test_flow5_cma_agrees_with_the_ols_slope` fails, widen the tolerance to 50% and say so — the OLS slope and the flow5 derivative are computed differently and are not expected to match tightly.

- [ ] **Step 6: Verify the earlier flow5 tests**

Run: `cd Python && python -m pytest tests/test_e2e_flow5_cessna.py tests/test_flow5_force_channels.py tests/test_flow5_run_wrapper.py -q`
Expected: PASS

- [ ] **Step 7: Commit** (needs user approval)

```bash
git add FLOW5/run/flow5_run.cpp Python/tests/test_flow5_derivatives.py
git commit -m "feat: compute and emit flow5 stability derivatives"
```

---

### Task 2.3: flow5 signs, beta plumbing, and the overlay

**Files:**
- Modify: `Python/src/aid/axes.py` — flow5 map becomes `{"Cx": -1, "Cz": -1, "Cl": -1, "Cn": -1}`.
  **Supersedes this plan's original text** (`{"Cx": -1, "Cz": -1, "CXa": -1, "CZa": -1}`), which Task 2.0's measurement refuted in both directions: `CXa`/`CZa` take **no** entry (they already measure F-R-D), and `Cl`/`Cn` were missing. Evidence and per-channel settling numbers: the `### Spikes` section of `2026-10-03-frd-sign-convention-design.md` and `.superpowers/sdd/2026-10-03-frd-sign-convention-plan/task-2.0-report.md`.
- Modify: `Python/src/aid/flow5_io.py` — `write_flow5_deck(ac, mesh, beta=0.0)`, `run_flow5(ac, mesh, beta=0.0)`
- Modify: `Python/src/aid/flow5_controls.py` — wrap with `to_frd("flow5", ...)`
- Modify: `Python/src/aid_gui/compare_tabs.py` — add `flow5=` entries to the Moments and Derivatives specs
- Test: `Python/tests/test_flow5_beta_deck.py`, `Python/tests/test_flow5_overlay_signs.py`

**Interfaces:**
- Consumes: Task 2.1's channels, Task 2.2's derivatives, spike 3's sign answer.
- Produces: `write_flow5_deck(ac, mesh, beta: float | None = None) -> dict` and `run_flow5(ac, mesh, beta: float | None = None, timeout: int = 180) -> dict`, both backwards compatible — `None` resolves to `0.0` in this task and becomes `ac.AERO["BETA"]` in Task 3.1, which is the only change to these defaults later. `run_flow5` output is F-R-D.

- [ ] **Step 1: Write the failing tests**

`Python/tests/test_flow5_beta_deck.py`:

```python
from aid.aircraft import load_jsonc
from aid.flow5_io import write_flow5_deck


def test_deck_defaults_beta_to_zero():
    ac = load_jsonc(MODELS / "Cessna 172.jsonc")
    assert write_flow5_deck(ac, ("10", "10"))["polar"]["beta_deg"] == 0.0


def test_deck_carries_beta_through():
    ac = load_jsonc(MODELS / "Cessna 172.jsonc")
    deck = write_flow5_deck(ac, ("10", "10"), beta=5.0)
    assert deck["polar"]["beta_deg"] == 5.0


def test_deck_alpha_list_is_untouched_by_beta():
    ac = load_jsonc(MODELS / "Cessna 172.jsonc")
    a = write_flow5_deck(ac, ("10", "10"))["polar"]["alpha_deg"]
    b = write_flow5_deck(ac, ("10", "10"), beta=5.0)["polar"]["alpha_deg"]
    assert a == b
```

`Python/tests/test_flow5_overlay_signs.py`:

```python
def test_flow5_cx_flips_into_forward_right_down(cessna_flow5):
    # After to_frd the flow5 map flips both Cx and Cz, so at alpha = 0 (where raw
    # Cx reduces to CD = +0.0012434) Cx must read NEGATIVE, i.e. forward-positive.
    i = int(np.argmin(np.abs(np.asarray(cessna_flow5["alpha"]))))
    assert cessna_flow5["Cx"][i] < 0.0, "raw Cx is aft-positive, so F-R-D must be forward-positive"
    j = int(np.argmax(cessna_flow5["CL"]))
    assert cessna_flow5["Cz"][j] < 0.0, "raw Cz is up-positive, so F-R-D must be down-negative"
    # NOTE: do not assert Cx < 0 at argmax(CL) (alpha = +12). Measured raw Cx
    # there is -0.1828 -- already negative because CL*sin(a) dominates CD*cos(a) --
    # so after the flip it reads +0.1828 and an `assert Cx < 0` FAILS.


def test_flow5_cz_flips_into_forward_right_down(cessna_flow5):
    i = int(np.argmax(cessna_flow5["CL"]))
    assert cessna_flow5["CL"][i] > 0.0
    assert cessna_flow5["Cz"][i] < 0.0


def test_flow5_cy_cl_cn_are_not_flipped(cessna_flow5):
    for key in ("CY", "Cl", "Cn"):
        assert key in cessna_flow5


def test_flow5_lateral_derivatives_survive_normalization(cessna_flow5):
    assert cessna_flow5["Cnb"] > 0.0
    assert cessna_flow5["Clb"] < 0.0
    assert cessna_flow5["CYb"] < 0.0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd Python && python -m pytest tests/test_flow5_beta_deck.py tests/test_flow5_overlay_signs.py -q`
Expected: FAIL — `beta_deg` absent from the deck, and `Cx`/`Cz` still in the raw frame.

- [ ] **Step 3: Implement**

- `axes.py`: fill in the flow5 entry with the four keys spike 3 justifies. If spike 3 shows `Clb`/`Cnb` raw, add them too and say so in the commit body.
- `flow5_io.py`: add `beta: float | None = None` to both signatures; resolve `None` to `0.0` with `beta = 0.0 if beta is None else float(beta)`; put `"beta_deg": beta` in the `polar` dict; pass `beta` from `run_flow5` into `write_flow5_deck`. `run_flow5_native` stays as-is.
- `flow5_controls.py`: wrap its returned dict with `to_frd("flow5", ...)`.
- `compare_tabs.py`: `_plot_moments` gains `flow5` for `Cltot`/`Cntot` and `_plot_derivatives` gains it for `CYb`/`Cnb`/`Clb`. The `flow5` element of each spec tuple is currently `None`; fill it in the same style as the existing `CL`/`CD`/`Cm` entries, and add `"Cltot"`, `"Cntot"`, `"CZa"`, `"CYb"`, `"Cnb"`, `"Clb"` to the flow5 half of `_SKIP_LEFTOVER` handling if the Sections table needs them.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd Python && python -m pytest tests/test_flow5_beta_deck.py tests/test_flow5_overlay_signs.py -q`
Expected: PASS

- [ ] **Step 5: Verify nothing regressed**

Run: `cd Python && python -m pytest tests/ -q --ignore=tests/test_matlab_batch_all.py`
Expected: PASS

- [ ] **Step 6: Commit** (needs user approval)

```bash
git add Python/src/aid/axes.py Python/src/aid/flow5_io.py Python/src/aid/flow5_controls.py \
        Python/src/aid_gui/compare_tabs.py \
        Python/tests/test_flow5_beta_deck.py Python/tests/test_flow5_overlay_signs.py
git commit -m "feat: put flow5 in Forward-Right-Down and let its deck carry a sideslip"
```

---

### Task 3.1: `AERO["BETA"]` in the schema and the engines

**Files:**
- Modify: `Python/src/aid/aircraft.py` — the `AERO` default block and `_aircraft_from_dict` normalisation
- Modify: `Python/src/aid/field_docs.py` — the `BETA` field comment
- Modify: `Python/src/aid/tornado_io.py` — `state["betha"]`
- Modify: `Python/src/aid/flow5_io.py` — resolve `beta=None` from `AERO["BETA"]`
- Test: `Python/tests/test_aero_beta.py`

**Interfaces:**
- Consumes: `write_flow5_deck`'s `beta` keyword from Task 2.3.
- Produces: `ac.AERO["BETA"]` always present as a float in degrees. `tornado_io(ac, mesh)` sets `state["betha"] = math.radians(beta)`. `write_flow5_deck` / `run_flow5` resolve `beta=None` to `ac.AERO["BETA"]` instead of `0.0`.

- [ ] **Step 1: Write the failing test**

`Python/tests/test_aero_beta.py`:

```python
import json
from pathlib import Path

import numpy as np
import pytest

from aid.aircraft import load_jsonc, save_jsonc
from aid.jsonc import loads_jsonc
from aid.aircraft import _aircraft_from_dict
from aid.tornado_io import tornado_io

MODELS = Path(__file__).resolve().parents[1] / "models"


def test_beta_defaults_to_zero():
    ac = load_jsonc(MODELS / "Cessna 172.jsonc")
    assert ac.AERO["BETA"] == 0.0


def test_every_shipped_model_resolves_beta():
    for path in sorted(MODELS.glob("*.jsonc")):
        assert isinstance(load_jsonc(path).AERO["BETA"], float), path.name


def test_beta_survives_a_jsonc_round_trip(tmp_path):
    ac = load_jsonc(MODELS / "Cessna 172.jsonc")
    ac.AERO["BETA"] = 5.0
    out = tmp_path / "m.jsonc"
    save_jsonc(ac, out)
    assert load_jsonc(out).AERO["BETA"] == 5.0
    assert "// " in out.read_text(), "every JSONC key needs a comment"
    assert '"BETA"' in out.read_text()


def test_missing_beta_key_is_not_an_error():
    raw = json.loads((MODELS / "Cessna 172.jsonc").read_text())
    raw["AERO"].pop("BETA", None)
    assert _aircraft_from_dict(raw).AERO["BETA"] == 0.0


def test_missing_aero_container_is_not_an_error():
    raw = json.loads((MODELS / "Cessna 172.jsonc").read_text())
    raw.pop("AERO")
    assert _aircraft_from_dict(raw).AERO["BETA"] == 0.0


def test_tornado_state_uses_beta():
    ac = load_jsonc(MODELS / "Cessna 172.jsonc")
    ac.AERO["BETA"] = 5.0
    _, state = tornado_io(ac, ("10", "5"))
    assert state["betha"] == pytest.approx(np.deg2rad(5.0))


def test_tornado_beta_defaults_to_zero():
    ac = load_jsonc(MODELS / "Cessna 172.jsonc")
    _, state = tornado_io(ac, ("10", "5"))
    assert state["betha"] == pytest.approx(0.0)
```

`json.loads` is used rather than `loads_jsonc` because the shipped file has `//` comments that plain `json` rejects — read it with `loads_jsonc((MODELS / "Cessna 172.jsonc").read_text())` and drop `BETA` from the resulting dict instead.

- [ ] **Step 2: Run test to verify it fails**

Run: `cd Python && python -m pytest tests/test_aero_beta.py -q`
Expected: FAIL — `KeyError: 'BETA'`

- [ ] **Step 3: Implement**

In `aircraft.py`, add `"BETA": 0.0` to the `AERO` defaults and to whatever normalisation pass already fills absent `AERO` keys, so both the "key missing" and "container missing" cases land on `0.0`. Add the field comment `// sideslip angle in degrees (0 = symmetric flight)` to `aid/field_docs.py`'s `DOCS` so `save_jsonc` emits it. In `tornado_io.py`, set `state["betha"] = math.radians(float(ac.AERO.get("BETA", 0.0) or 0.0))`. In `flow5_io.py`, change the `beta` default resolution from `0.0` to `ac.AERO["BETA"]` in both `write_flow5_deck` and `run_flow5`.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd Python && python -m pytest tests/test_aero_beta.py -q`
Expected: PASS, 7 passed

- [ ] **Step 5: Verify the JSONC comment rule and the shipped models**

Run: `cd Python && python -m pytest tests/test_jsonc_comments_every_key.py tests/test_mat_to_jsonc_all.py tests/test_model_filenames.py -q`
Expected: PASS

- [ ] **Step 6: Commit** (needs user approval)

```bash
git add Python/src/aid/aircraft.py Python/src/aid/field_docs.py \
        Python/src/aid/tornado_io.py Python/src/aid/flow5_io.py \
        Python/tests/test_aero_beta.py
git commit -m "feat: add AERO.BETA, the sideslip angle every solver reads"
```

---

### Task 3.2: Beta field in the PySide GUI

**Files:**
- Modify: the Aero tab builder in `Python/src/aid_gui/tabs.py`
- Modify: `Python/src/aid_gui/main_window.py` — `sync_fields_to_aircraft`, `populate_from_aircraft`, `run_tornado`, `run_flow5`
- Modify: `Python/src/aid_gui/compare_tabs.py` — the `(beta=0)` series label
- Test: `Python/tests/test_gui_aero_beta.py`

**Interfaces:**
- Consumes: `ac.AERO["BETA"]` from Task 3.1.
- Produces: a `Beta (deg)` row on the Aero tab, and `overlay_vs_alpha`/`overlay_derivative` accept an optional `beta` argument that appends `" (beta=0)"` to the DATCOM and AVL series labels when `beta` is non-zero.

- [ ] **Step 1: Write the failing test**

`Python/tests/test_gui_aero_beta.py`, following the monkeypatch style of `tests/test_gui_analyze_flow5.py`:

```python
def test_aero_tab_has_a_beta_field(window):
    assert "BETA" in window._beta_widgets


def test_beta_field_shows_the_model_default(window):
    assert window._beta_widgets["BETA"].text() in ("0", "0.0")


def test_editing_beta_syncs_to_the_aircraft(window):
    window._beta_widgets["BETA"].setText("5")
    window.sync_fields_to_aircraft()
    assert window.aircraft.AERO["BETA"] == 5.0


def test_blank_beta_commits_null_and_reads_as_zero(window):
    window._beta_widgets["BETA"].setText("")
    window.sync_fields_to_aircraft()
    assert window.aircraft.AERO["BETA"] == 0.0


def test_run_tornado_forwards_beta(window, monkeypatch):
    seen = {}
    monkeypatch.setattr(main_window, "run_tornado", lambda *a, **k: seen.update(k))
    window._beta_widgets["BETA"].setText("5")
    window.run_tornado()
    assert seen["beta"] == 5.0


def test_datcom_and_avl_labels_carry_beta_zero():
    series = overlay_vs_alpha(RESULTS, ST, datcom="cl", tornado=("CL", "CL_a"),
                              avl="CLtot", beta=5.0)
    labels = {s["label"] for s in series}
    assert "DATCOM (beta=0)" in labels and "AVL (beta=0)" in labels
    assert "Tornado" in labels


def test_labels_are_untouched_at_beta_zero():
    series = overlay_vs_alpha(RESULTS, ST, datcom="cl", tornado=("CL", "CL_a"),
                              avl="CLtot", beta=0.0)
    assert {s["label"] for s in series} == {"DATCOM", "Tornado", "AVL"}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd Python && python -m pytest tests/test_gui_aero_beta.py -q`
Expected: FAIL — `window._beta_widgets` does not exist, and `overlay_vs_alpha` has no `beta` parameter.

- [ ] **Step 3: Implement**

- Add the `Beta (deg)` row to the Aero tab with the same right-aligned label / edit / unit layout as the neighbouring `ALT` and `Mach` rows, storing the editor in `self._beta_widgets["BETA"]`.
- Register it in `sync_fields_to_aircraft` (`None` when blank) and `populate_from_aircraft`.
- `run_tornado` passes `beta=self.aircraft.AERO["BETA"]` down to the `tornado_io` call; `run_flow5` passes it to `run_flow5`. `run_datcom` and `run_avl` are unchanged and must not gain a beta argument.
- In `solver_overlay.py`, give both `overlay_vs_alpha` and `overlay_derivative` a `beta: float = 0.0` keyword. When `beta != 0`, suffix the DATCOM and AVL labels with `" (beta=0)"`; leave Tornado and flow5 alone, since those two actually fly at `beta`.
- Update `_plot_forces`, `_plot_moments` and `_plot_derivatives` in `compare_tabs.py` to pass `beta=self.beta` through.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd Python && python -m pytest tests/test_gui_aero_beta.py tests/test_solver_overlay.py tests/test_gui_compare_tabs.py -q`
Expected: PASS

- [ ] **Step 5: Verify the GUI suite**

Run: `cd Python && QT_QPA_PLATFORM=offscreen python -m pytest tests/ -q --ignore=tests/test_matlab_batch_all.py`
Expected: PASS

- [ ] **Step 6: Commit** (needs user approval)

```bash
git add Python/src/aid_gui/tabs.py Python/src/aid_gui/main_window.py \
        Python/src/aid_gui/compare_tabs.py Python/src/aid/solver_overlay.py \
        Python/tests/test_gui_aero_beta.py
git commit -m "feat: Aero tab Beta field, and honest labels when only some solvers have beta"
```

---

### Task 3.3: Beta in the API and the web app

**Files:**
- Modify: `api/aid_web/analyze.py`
- Modify: `web/src/Editor.tsx`
- Modify: `web/src/aeroFigures.ts`
- Modify: `web/src/aeroChart.ts` if the request body is assembled there
- Test: `api/tests/test_analyze_beta.py`, `web/src/aeroFigures.test.ts`

**Interfaces:**
- Consumes: `ac.AERO["BETA"]` from Task 3.1; the `beta` keyword from Task 2.3.
- Produces: `POST /analyze` and `POST /stability` accept an optional `beta` (degrees). `seriesVsAlpha`/`seriesDerivative` in `coeffOverlay.ts` gain an optional `beta` and apply the same label rule as Python.

- [ ] **Step 1: Write the failing tests**

`api/tests/test_analyze_beta.py`:

```python
def test_analyze_defaults_beta_to_zero(client, cessna):
    r = client.post("/analyze", json={"aircraft": cessna, "solver": "tornado"})
    assert r.status_code == 200


def test_analyze_accepts_beta(client, cessna, monkeypatch):
    seen = {}
    monkeypatch.setattr(analyze, "analyze_tornado", lambda *a, **k: seen.update(k))
    client.post("/analyze", json={"aircraft": cessna, "solver": "tornado", "beta": 5.0})
    assert seen["beta"] == 5.0


def test_stability_accepts_beta(client, cessna):
    assert client.post("/stability", json={"aircraft": cessna, "beta": 5.0}).status_code == 200


def test_unknown_solver_still_400s(client, cessna):
    assert client.post("/analyze", json={"aircraft": cessna, "solver": "vlm2"}).status_code == 400
```

In `web/src/aeroFigures.test.ts`, following the existing `flow5` fixtures at line 217:

```ts
it("labels datcom and avl with beta=0 when the flight has a sideslip", () => {
  const raws = { datcom: { alpha: [0, 2], cl: [0.1, 0.2] }, avl: { alpha: [0, 2], CLtot: [0.1, 0.2] } };
  const series = seriesVsAlpha(raws, null, { datcom: "cl", avl: "CLtot" }, 5);
  expect(series.map((s) => s.label ?? s.solver)).toContain("datcom (beta=0)");
  expect(series.map((s) => s.label ?? s.solver)).toContain("avl (beta=0)");
});

it("leaves labels alone at beta zero", () => {
  const raws = { datcom: { alpha: [0, 2], cl: [0.1, 0.2] } };
  const series = seriesVsAlpha(raws, null, { datcom: "cl" }, 0);
  expect(series[0].label ?? series[0].solver).toBe("datcom");
});
```

Match the real field name — `coeffOverlay.ts` returns `{ solver, ... }`, so assert on whatever carries the display name rather than inventing `label`.

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd api && python -m pytest tests/test_analyze_beta.py -q` and `cd web && npm test -- aeroFigures`
Expected: FAIL — the API rejects the extra field and `seriesVsAlpha` takes no beta.

- [ ] **Step 3: Implement**

- `api/aid_web/analyze.py`: read `beta` from the request body with a `0.0` default, push it into the aircraft's `AERO["BETA"]` before dispatching, so every engine path sees one value. Do not add a per-solver argument.
- `web/src/Editor.tsx`: add a `Beta (deg)` number input to the Aero tab, committed on blur, `null` when blank, defaulting to `0`.
- `web/src/aeroChart.ts` (or wherever the Analyze body is built): include `beta` in the POST.
- `web/src/coeffOverlay.ts`: give `seriesVsAlpha` and `seriesDerivative` an optional `beta = 0`; when non-zero, suffix the `datcom` and `avl` display names with ` (beta=0)`.
- `web/src/aeroFigures.ts`: thread `beta` from the figure spec through to those calls.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd api && python -m pytest tests/ -q` and `cd web && npm test`
Expected: PASS

- [ ] **Step 5: Verify the full Python suite once more**

Run: `cd Python && python -m pytest tests/ -q --ignore=tests/test_matlab_batch_all.py`
Expected: PASS

- [ ] **Step 6: Commit** (needs user approval)

```bash
git add api/aid_web/analyze.py api/tests/test_analyze_beta.py \
        web/src/Editor.tsx web/src/coeffOverlay.ts web/src/aeroFigures.ts web/src/aeroChart.ts \
        web/src/aeroFigures.test.ts
git commit -m "feat: sideslip reaches the API and the web Aero tab"
```

---

### Task 3.4: Docs

**Files:**
- Modify: `UPDATES.md` — new top entry, sub-version bump (features, no architecture break)
- Modify: `README.md` — only if the sign convention or `AERO.BETA` counts as architecture. It does: `README.md` documents the `AERO` group and the solver table, so add one line naming Forward-Right-Down as the reported convention and one line on `AERO.BETA`.

**Interfaces:**
- Consumes: everything above.
- Produces: the two mandatory project docs, current.

- [ ] **Step 1: Update `UPDATES.md`**

New top entry, `1.<subver>.<n>`, one line per task group: the F-R-D unification, the flow5 lateral channels and derivatives, `AERO.BETA`, and the `(beta=0)` labelling. Mention the two spikes and their answers if they constrained the outcome.

- [ ] **Step 2: Update `README.md`**

In the Aircraft data table's `AERO` row, name `BETA`. In the Architecture section, add one sentence: all four solvers report coefficients in Forward-Right-Down; `aid/axes.py` is the only place a sign is written down.

- [ ] **Step 3: Verify the docs test passes**

Run: `cd Python && python -m pytest tests/test_project_docs.py -q`
Expected: PASS

- [ ] **Step 4: Commit** (needs user approval)

```bash
git add UPDATES.md README.md
git commit -m "docs: record the Forward-Right-Down convention and AERO.BETA"
```

---

## Execution Plan

11 tasks, dispatched as **8 waves**. Within a wave the tasks touch disjoint files and share no process, so they are safe to run concurrently. Wave membership is chosen so that every task's `Interfaces` block is satisfied by an earlier wave.

| wave | tasks | notes |
|---|---|---|
| 0 | — | Create the worktree. Sequential: nothing else runs first. |
| 1 | **1.1**, **2.0** | 1.1 is new-file Python; 2.0 is read-only plus `/tmp` scratch. Fully disjoint. 2.0's answer gates 2.1. |
| 2 | **1.2**, **2.1** | 1.2 touches Python solver runners; 2.1 touches two C++ files and rebuilds. 1.2's tests never invoke `flow5_run`, so the relink cannot race them. |
| 3 | **1.3**, **2.2** | 1.3 touches `compare.py` only; 2.2 touches `flow5_run.cpp` and rebuilds. 1.3's tests are DATCOM/Tornado/AVL parity and never invoke `flow5_run`. |
| 4 | **1.4**, **2.3** | 1.4 is test-only; 2.3 touches `axes.py`, `flow5_io.py`, `compare_tabs.py`. **1.4 must not start until 1.3 lands, because it asserts the final sign state.** If 1.4 lands in wave 4 alongside 2.3, it may see 2.3's `axes.py` edit — which is the correct final state, so this is safe. |
| 5 | — | **Deliverable 1 + 2 gate.** Full Python suite green, all four flow5 test files green, `run_all.py` parity green for Cessna 172 / Navion / DA20-C1 / Learjet 23. |
| 6 | **3.1** | Schema first; 3.2 and 3.3 both read `AERO["BETA"]`. |
| 7 | **3.2**, **3.3** | PySide and web are disjoint trees (`Python/src/aid_gui` vs `web/src` + `api/`). |
| 8 | **3.4**, then whole-branch review | Docs last, so they describe what shipped. |

**Reviewers.** One reviewer subagent per task, dispatched after that task's tests go green and before the next wave starts. Plus one whole-branch reviewer at the end of wave 8. Model for every implementer and every reviewer: **space-bunny-free** (approved by the user for this plan). No fast variants, per the repo's agent-permissions rule.

**Reviewer brief** (same for all of them): the spec is `docs/superpowers/plans/2026-10-03-frd-sign-convention-design.md`; the task's own steps define done; the five Review Focus items above are what to probe beyond the task's tests. A reviewer must run the task's test command and quote the output — a green self-review is not evidence.

## Verification

From the worktree root:

```
cd Python && python -m pytest tests/ -q --ignore=tests/test_matlab_batch_all.py
cd api    && python -m pytest tests/ -q
cd web    && npm test
python Python/scripts/run_all.py --aircraft "Cessna 172"
```

Manual check, B-1 Lancer, after wave 5: Analyze DATCOM, Tornado, AVL and flow5, then open Forces and Moments. `C_A` must show DATCOM and Tornado on one side of zero and AVL on the same side, not mirrored. `C_N` likewise. `C_n` and `C_l` in Moments must have AVL and DATCOM on the same side. Derivatives must show `C_{nβ} > 0` and `C_{ℓβ} < 0` for all solvers that contribute, with flow5 present and yellow.

Known pre-existing failure in a worktree: `tests/test_paths.py::test_paths_resolve` asserts `repo_root().name == "AircraftIntuitiveDesign"`, which a worktree directory cannot satisfy. Not caused by this plan.