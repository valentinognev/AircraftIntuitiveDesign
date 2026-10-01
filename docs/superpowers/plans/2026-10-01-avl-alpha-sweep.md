# AVL angle-of-attack sweep Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** AVL Analyze solves every angle in `AERO.ALSCHD` and the force, moment, and derivative plots show those solved samples only.

**Architecture:** One AVL process runs one OPER case per scheduled angle (`a a <deg>`, `x`, `st`). Each `.st` is parsed with the existing `merge_avl_st` and stacked into parallel arrays. Qt and web plots draw those arrays. They do not extend a single `CLtot` with `CLa` or any other slope. Tornado, DATCOM, and flow5 plots stay as they are. MATLAB `AVL_IO.m` stays the single-case gold runner; Python gold compare reads the sweep sample whose solved alpha is 0.

**Tech Stack:** Python 3.11 (`aid`, pytest), PySide6 compare tabs, FastAPI `api/aid_web` (no route change), Vite React `web/`.

**Spec:** This file is the spec. Executors treat Global Constraints and the returned-dict schema as binding.

## Global Constraints

- Do not `git commit` or `git push`. Leave the worktree dirty. The parent asks the user before any commit.
- Implementers and reviewers use Grok non-fast only (`grok-4.7-high`). Fast modes, Composer, Claude, and `inherit` are forbidden.
- TDD: write the failing test, run it, then the minimum code, then run it again. A task is done only when its named pytest or `npm test` command passes.
- The angle list is `AERO.ALSCHD` in stored order. Do not sort it, unique it, or replace it with a linspace.
- Do not draw AVL coefficients at an angle AVL did not solve. No `C + C_alpha * (alpha - alpha0)` line for AVL. A one-angle schedule is one point, not a line across the DATCOM grid.
- Multiplying an AVL per-radian derivative by `pi/180` when it is plotted next to per-degree DATCOM is unit conversion. Do that. Do not spread that one number across unsolved angles.
- MATLAB `Matlab/fsroot/code/AVL_IO.m` is not modified. Gold `Results/matlab/*/avl.json` files are not modified.
- Tornado slope lines, DATCOM tables, and flow5 alpha tables stay.
- Control-derivative probes are out of scope. Do not change their call path.
- Empty `ALSCHD` raises `ValueError("AERO.ALSCHD is empty")`.
- After the feature lands, Task 7 bumps `UPDATES.md` to `1.32.0` and updates the AVL sentence in `README.md`. No other new markdown.

## Returned dict

`run_avl_full` returns one dict. Every sweep key is a `list[float]` of the same length as `alpha`, in case order. `alpha` is the `Alpha =` value parsed from that case, not a copy pasted from the schedule without checking.

Sweep totals: `CXtot`, `CYtot`, `CZtot`, `Cltot`, `Cmtot`, `Cntot`, `CLtot`, `CDtot`, `CDvis`, `CDind`, `CDff`, `CLff`, `CYff`, `e`.

Sweep derivatives (from `parse_st` of that same case): `CLa`, `CYa`, `Cla`, `Cma`, `Cna`, `CLb`, `CYb`, `Clb`, `Cmb`, `Cnb`, `CLp`, `CYp`, `Clp`, `Cmp`, `Cnp`, `CLq`, `CYq`, `Clq`, `Cmq`, `Cnq`, `CLr`, `CYr`, `Clr`, `Cmr`, `Cnr`, `NP`.

`surface` is the list from the first case only (deflections do not change with alpha).

`geometry.sb` is written once, for the case whose commanded angle is 0, or for case 0 when 0 is not in the schedule. It is not part of the returned dict and is not plotted.

## File map

- `Python/src/aid/avl_io.py` — run script, stack, `run_avl_full`.
- `Python/src/aid/compare.py` — gold scalars compared at solved alpha 0.
- `Python/src/aid/solver_overlay.py` — AVL series are solved samples.
- `Python/src/aid_gui/compare_tabs.py` — pass AVL value keys, not slope pairs.
- `Python/src/aid_gui/results_panel.py` — drop the `CL0 + CLa * alpha` AVL line.
- `web/src/coeffOverlay.ts` — same plotting rule.
- `web/src/aeroFigures.ts` — AVL specs are value keys; per-angle drag and rate derivatives are lines.
- `web/src/Results.tsx` — a one-point series draws a circle.
- `README.md`, `UPDATES.md` — architecture sentence and `1.32.0`.

---

### Task 1: Stack one parsed case per angle

**Files:**
- Modify: `Python/src/aid/avl_io.py` (`merge_avl_st` stays; add `stack_avl_cases` after it)
- Test: `Python/tests/test_avl_stack_cases.py`

**Interfaces:**
- Consumes: `merge_avl_st(path: Path) -> dict` (existing). Each file is one run case plus its stability derivatives.
- Produces: `stack_avl_cases(paths: list[Path]) -> dict` with `alpha: list[float]`, the sweep totals and sweep derivatives as `list[float]` of that length, and `surface` from the first file.

- [ ] **Step 1: Write the failing test**

```python
# Python/tests/test_avl_stack_cases.py
from pathlib import Path

from aid.avl_io import stack_avl_cases

_ST = """
 Run case:  wing

 Alpha =   {alpha:.5f}     pb/2V =   0.00000     p'b/2V =   0.00000
 Beta  =   0.00000     qc/2V =   0.00000
 Mach  =     0.000     rb/2V =   0.00000     r'b/2V =   0.00000

 CXtot =   {cx:.5f}     Cltot =   0.00000     Cl'tot =   0.00000
 CYtot =   0.00000     Cmtot =  {cm:.5f}     Cn'tot =   0.00000
 CZtot =  {cz:.5f}     Cntot =   0.00000

 CLtot =   {cl:.5f}
 CDtot =   {cd:.5f}
 CDvis =   0.00000     CDind =   {cdi:.5f}
 CLff  =   {cl:.5f}     CDff  =   0.01800    | Trefftz
 CYff  =   0.00000         e =   0.80000    | Plane

 Stability-axis derivatives...

  z' force CL   |  CLa =   {cla:.6f}   CLb =   0.000000
  y  force CY   |  CYa =   0.000000   CYb =  -0.400000
  x' mom.  Cl'  |  Cla =   0.000000   Clb =  -0.050000
  y  mom.  Cm   |  Cma =  -1.200000   Cmb =   0.000000
  z' mom.  Cn'  |  Cna =   0.000000   Cnb =   0.080000
  z' force CL   |  CLp =   0.010000   CLq =   8.000000   CLr =  -0.020000
  y  force CY   |  CYp =  -0.100000   CYq =  -0.200000   CYr =   0.300000
  x' mom.  Cl'  |  Clp =  -0.400000   Clq =  -0.010000   Clr =   0.040000
  y  mom.  Cm   |  Cmp =  -0.020000   Cmq = -15.000000   Cmr =   0.050000
  z' mom.  Cn'  |  Cnp =   0.030000   Cnq =   0.060000   Cnr =  -0.100000

 Neutral point  Xnp =   3.500000
"""


def _write(dirpath: Path, name: str, **kw) -> None:
    (dirpath / name).write_text(_ST.format(**kw))


def test_stack_avl_cases_keeps_each_solved_angle(tmp_path: Path):
    _write(tmp_path, "a0.st", alpha=-4, cx=0.01, cz=-0.2, cl=0.2, cd=0.01, cdi=0.008, cm=-0.02, cla=5.1)
    _write(tmp_path, "a1.st", alpha=0, cx=0.02, cz=-0.5, cl=0.5, cd=0.02, cdi=0.016, cm=-0.04, cla=5.2)
    got = stack_avl_cases([tmp_path / "a0.st", tmp_path / "a1.st"])
    assert got["alpha"] == [-4.0, 0.0]
    assert got["CLtot"] == [0.2, 0.5]
    assert got["CDtot"] == [0.01, 0.02]
    assert got["CZtot"] == [-0.2, -0.5]
    assert got["CXtot"] == [0.01, 0.02]
    assert got["CLa"] == [5.1, 5.2]
    assert got["NP"] == [3.5, 3.5]
    assert len(got["Cmtot"]) == 2
    assert got["surface"] == []


def test_stack_avl_cases_rejects_empty():
    try:
        stack_avl_cases([])
    except ValueError as exc:
        assert "empty" in str(exc)
    else:
        raise AssertionError("expected ValueError")
```

The fixture's derivative lines must be lines `parse_st` already matches (`CLa =`, `CLp =`, `Xnp =`). If a key comes back 0 because the fixture line does not match `find_value`, fix the fixture line, not the parser.

- [ ] **Step 2: Run test to verify it fails**

Run: `cd Python && python -m pytest tests/test_avl_stack_cases.py -v`

Expected: FAIL with `ImportError` or `AttributeError` for `stack_avl_cases`.

- [ ] **Step 3: Write minimal implementation**

Add after `merge_avl_st` in `Python/src/aid/avl_io.py`:

```python
_SWEEP_TOTALS = (
    "CXtot", "CYtot", "CZtot", "Cltot", "Cmtot", "Cntot",
    "CLtot", "CDtot", "CDvis", "CDind", "CDff", "CLff", "CYff", "e",
)
_SWEEP_DERIVS = (
    "CLa", "CYa", "Cla", "Cma", "Cna",
    "CLb", "CYb", "Clb", "Cmb", "Cnb",
    "CLp", "CYp", "Clp", "Cmp", "Cnp",
    "CLq", "CYq", "Clq", "Cmq", "Cnq",
    "CLr", "CYr", "Clr", "Cmr", "Cnr",
    "NP",
)


def stack_avl_cases(paths: list[Path]) -> dict:
    """One merged ``.st`` per angle, in path order. No interpolation."""
    if not paths:
        raise ValueError("AVL sweep is empty")
    cases = [merge_avl_st(path) for path in paths]
    out: dict = {
        "alpha": [float(case["alpha"]) for case in cases],
        "surface": list(cases[0].get("surface") or []),
    }
    for key in (*_SWEEP_TOTALS, *_SWEEP_DERIVS):
        out[key] = [float(case[key]) for case in cases]
    return out
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd Python && python -m pytest tests/test_avl_stack_cases.py -v`

Expected: PASS.

---

### Task 2: Write an OPER case per scheduled angle

**Files:**
- Modify: `Python/src/aid/avl_io.py` (`write_case`)
- Test: `Python/tests/test_avl_write_case_sweep.py`

**Interfaces:**
- Consumes: `state["AS"]` (airspeed, existing). Angles in degrees from the caller.
- Produces: `write_case(case_id: str, state: dict, run_dir: Path, alphas: list[float]) -> None`. The `.run` file commands AVL to solve each angle. No default-alpha-only script.

- [ ] **Step 1: Write the failing test**

```python
# Python/tests/test_avl_write_case_sweep.py
from pathlib import Path

from aid.avl_io import write_case


def test_write_case_commands_each_alpha(tmp_path: Path):
    write_case("geometry", {"AS": 100.0}, tmp_path, [-4.0, 0.0, 8.0])
    text = (tmp_path / "geometry.run").read_text()
    assert "a a -4.0000" in text
    assert "a a 0.0000" in text
    assert "a a 8.0000" in text
    assert text.count("\nx\n") == 3
    assert "geometry_0.st" in text
    assert "geometry_1.st" in text
    assert "geometry_2.st" in text
    # sb once, on the zero-angle case, before the next alpha command
    zero = text.index("a a 0.0000")
    sb = text.index("geometry.sb")
    eight = text.index("a a 8.0000")
    assert zero < sb < eight
    assert text.count("geometry.sb") == 1


def test_write_case_sb_on_first_when_zero_absent(tmp_path: Path):
    write_case("geometry", {"AS": 50.0}, tmp_path, [2.0, 4.0])
    text = (tmp_path / "geometry.run").read_text()
    assert text.index("geometry.sb") < text.index("a a 4.0000")
    assert text.count("geometry.sb") == 1


def test_write_case_rejects_empty_alphas(tmp_path: Path):
    try:
        write_case("geometry", {"AS": 1.0}, tmp_path, [])
    except ValueError as exc:
        assert "ALSCHD" in str(exc)
    else:
        raise AssertionError("expected ValueError")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd Python && python -m pytest tests/test_avl_write_case_sweep.py -v`

Expected: FAIL with `TypeError` (unexpected `alphas`) or missing `a a`.

- [ ] **Step 3: Write minimal implementation**

Replace `write_case` in `Python/src/aid/avl_io.py`:

```python
def write_case(case_id: str, state: dict, run_dir: Path, alphas: list[float]) -> None:
    """One AVL process, one solved angle per ``alphas`` entry (degrees)."""
    if not alphas:
        raise ValueError("AERO.ALSCHD is empty")
    run_dir = Path(run_dir)
    run_path = run_dir / f"{case_id}.run"
    as_val = float(state["AS"])
    sb_at = next((i for i, angle in enumerate(alphas) if float(angle) == 0.0), 0)

    with run_path.open("w", encoding="ascii") as fid:
        fid.write(f"LOAD {case_id}.avl\n")
        mass_path = run_dir / f"{case_id}.mass"
        if mass_path.is_file():
            fid.write(f"MASS {case_id}.mass\n")
            fid.write("MSET 1\n")
        fid.write("0\n")
        fid.write("PLOP\ng\n\n")
        fid.write("OPER\n")
        fid.write("c1\n")
        fid.write(f"v {as_val:6.4f}\n\n")
        for i, angle in enumerate(alphas):
            fid.write(f"a a {float(angle):.4f}\n")
            fid.write("x\n")
            fid.write("st\n")
            fid.write(f"{case_id}_{i}.st\n")
            if i == sb_at:
                fid.write("sb\n")
                fid.write(f"{case_id}.sb\n")
        fid.write("\n")
        fid.write("Quit\n")
```

The OPER command `a a <deg>` is AVL's one-line form: variable alpha, constraint alpha, value in degrees (same form as `D1 PM 0` in `avl_doc.txt`).

- [ ] **Step 4: Run test to verify it passes**

Run: `cd Python && python -m pytest tests/test_avl_write_case_sweep.py tests/test_avl_stack_cases.py -v`

Expected: PASS.

---

### Task 3: Run the sweep and keep the α = 0 gold sample

**Files:**
- Modify: `Python/src/aid/avl_io.py` (`run_avl_full`)
- Modify: `Python/src/aid/compare.py` (`_compare_avl`)
- Test: `Python/tests/test_avl_run_cessna.py`
- Test: `Python/tests/test_avl_gold_sample.py`

**Interfaces:**
- Consumes: `write_case(..., alphas)`, `stack_avl_cases`, `ac.AERO["ALSCHD"]`.
- Produces: `run_avl_full(ac, mesh, run_dir) -> dict` in the schema above. Timeout passed to `run_avl` is `120 * len(alphas)` seconds. Mesh retries delete `geometry_*.st` and `geometry.sb` and re-run the whole schedule. A missing `geometry_{i}.st` is failure, not a filled-in coefficient.
- Produces: `_compare_avl` compares a gold float to the sweep entry whose `alpha` is 0 within `1e-6` degrees. If that angle is absent, that key fails. It does not compare another angle.

- [ ] **Step 1: Write the failing tests**

Replace the body of `test_avl_cla_matches_matlab` in `Python/tests/test_avl_run_cessna.py` with:

```python
def test_avl_cla_matches_matlab(tmp_path):
    gold = json.loads((results_dir() / "matlab" / "Cessna 172" / "avl.json").read_text())
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    schedule = [float(a) for a in ac.AERO["ALSCHD"]]
    got = run_avl_full(ac, ("10", "10"), tmp_path)
    assert got["alpha"] == schedule or _solved_matches(got["alpha"], schedule)
    assert len(got["CLtot"]) == len(schedule)
    assert len(got["CDtot"]) == len(schedule)
    assert len(got["CZtot"]) == len(schedule)
    assert len(got["CXtot"]) == len(schedule)
    assert max(got["CLtot"]) - min(got["CLtot"]) > 1e-3
    assert max(got["CDtot"]) - min(got["CDtot"]) > 1e-6
    i0 = got["alpha"].index(0.0)
    assert abs(got["CLa"][i0] - gold["CLa"]) < 1e-6


def _solved_matches(solved, schedule) -> bool:
    if len(solved) != len(schedule):
        return False
    return all(abs(a - b) < 1e-2 for a, b in zip(solved, schedule))
```

Cessna `ALSCHD` contains 0. `got["alpha"].index(0.0)` is correct when AVL prints `0.00000`. If the parsed zero is `0.0` from `4f` rounding, `index` works. If a test fails because alpha is `1e-8`, compare with `abs(a) <= 1e-6` instead of `index`, and still require a unique zero sample.

Add `Python/tests/test_avl_gold_sample.py`:

```python
from aid.compare import _compare_avl


def test_gold_scalar_uses_zero_alpha_sample():
    python = {"alpha": [-4.0, 0.0, 4.0], "CLa": [5.0, 5.057308, 5.2], "CLtot": [0.1, 0.4, 0.8]}
    gold = {"CLa": 5.057308}
    assert _compare_avl(python, gold) is True


def test_gold_scalar_does_not_use_another_angle():
    python = {"alpha": [2.0, 4.0], "CLa": [5.057308, 5.2]}
    gold = {"CLa": 5.057308}
    assert _compare_avl(python, gold) is False
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd Python && python -m pytest tests/test_avl_gold_sample.py tests/test_avl_run_cessna.py -v`

Expected: `test_avl_gold_sample.py` fails because `_compare_avl` compares the whole list to a float. `test_avl_run_cessna.py` fails because `CLa` is still a float or the run is still one angle. The Cessna test needs `AVL/run/avl` on `PATH` via `aid.paths.avl_bin`; that is the existing requirement of this test.

- [ ] **Step 3: Write minimal implementation**

In `run_avl_full`, after `geo, state = tornado_io(...)`:

```python
import numpy as np

alphas = [float(a) for a in np.asarray(ac.AERO["ALSCHD"], dtype=float).reshape(-1)]
if not alphas:
    raise ValueError("AERO.ALSCHD is empty")
```

Inside the mesh loop, call `write_case("geometry", state, run_dir, alphas)`. Delete every `geometry_*.st` and `geometry.sb` before `run_avl`. Call `run_avl(run_dir, timeout=120 * len(alphas))`. Success is every `geometry_{i}.st` present for `i` in `range(len(alphas))`. Return `stack_avl_cases([run_dir / f"geometry_{i}.st" for i in range(len(alphas))])`. A partial set of files is the same failure as a missing `geometry.st` today: try the next spacing, then raise the last exception.

In `_compare_avl`, when `gold_val` is an `int` or `float` and `python[key]` is a `list` or `tuple`:

```python
alphas = python.get("alpha")
values = python[key]
if not isinstance(alphas, (list, tuple)) or len(alphas) != len(values):
    return False
sample = next((v for a, v in zip(alphas, values) if abs(float(a) - 0.0) <= 1e-6), None)
if sample is None or not _values_close(sample, gold_val, rtol=0.0, atol=_PARSER_ATOL):
    return False
continue
```

Leave the existing list-to-list and float-to-float branches unchanged.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd Python && python -m pytest tests/test_avl_gold_sample.py tests/test_avl_run_cessna.py tests/test_avl_stack_cases.py tests/test_avl_write_case_sweep.py -v`

Expected: PASS. `test_compare_primary` re-runs four full sweeps and is not this task's gate.

---

### Task 4: Plot solved AVL samples in the Qt overlay

**Files:**
- Modify: `Python/src/aid/solver_overlay.py`
- Modify: `Python/src/aid_gui/compare_tabs.py` (AVL key in each `overlay_vs_alpha` / `overlay_derivative` call)
- Modify: `Python/src/aid_gui/results_panel.py` (the AVL `CL0 + CLa * alpha` block around lines 72–86)
- Test: `Python/tests/test_solver_overlay.py`

**Interfaces:**
- Consumes: sweep dict from Task 3. `overlay_vs_alpha(..., avl: str | None = None)`. `overlay_derivative(..., avl: str | None = None)` already takes a string key.
- Produces: an AVL vs-alpha series whose `x` and `y` are the solved pairs. `kind` is `"line"` when `len(x) > 1` (`style` `"m.-"`) and `"marker"` when `len(x) == 1` (`style` `"m."`). Derivative series use `y * pi/180` at the solved alphas only. Tornado's slope line is unchanged.

- [ ] **Step 1: Write the failing test**

In `Python/tests/test_solver_overlay.py`, replace `test_overlay_groups_datcom_tornado_avl_on_cl` AVL expectations and add:

```python
def test_overlay_avl_plots_solved_samples_not_slope():
    st = _st()
    results = {
        "avl": {
            "alpha": [-4.0, 0.0, 4.0],
            "CLtot": [0.1, 0.4, 0.7],
            "CLa": [5.2, 5.2, 5.2],
            "CDtot": [0.01, 0.02, 0.04],
            "CZtot": [-0.1, -0.4, -0.69],
            "CXtot": [0.02, 0.02, 0.05],
        }
    }
    cl = overlay_vs_alpha(results, st, avl="CLtot")
    assert len(cl) == 1
    assert np.allclose(cl[0]["x"], [-4.0, 0.0, 4.0])
    assert np.allclose(cl[0]["y"], [0.1, 0.4, 0.7])
    assert cl[0]["kind"] == "line"
    # slope from CLa at 0 would be 0.4 at every nearby angle only if extrapolated;
    # the sample at -4 is 0.1, not 0.4 + 5.2 * radians(-4)
    assert abs(cl[0]["y"][0] - 0.1) < 1e-12

    cd = overlay_vs_alpha(results, st, avl="CDtot")
    assert np.allclose(cd[0]["y"], [0.01, 0.02, 0.04])
    cn = overlay_vs_alpha(results, st, avl="CZtot")
    assert np.allclose(cn[0]["y"], [-0.1, -0.4, -0.69])
    ca = overlay_vs_alpha(results, st, avl="CXtot")
    assert np.allclose(ca[0]["y"], [0.02, 0.02, 0.05])


def test_overlay_avl_one_angle_is_a_marker():
    st = _st()
    results = {"avl": {"alpha": [4.0], "CDtot": [0.03]}}
    series = overlay_vs_alpha(results, st, avl="CDtot")
    assert series[0]["kind"] == "marker"
    assert np.allclose(series[0]["x"], [4.0])
    assert np.allclose(series[0]["y"], [0.03])


def test_overlay_avl_derivative_stays_on_solved_alphas():
    st = _st()
    results = {"avl": {"alpha": [-4.0, 0.0, 4.0], "CLa": [5.0, 5.2, 5.1]}}
    series = overlay_derivative(results, st, avl="CLa")
    assert series[0]["kind"] == "line"
    assert np.allclose(series[0]["x"], [-4.0, 0.0, 4.0])
    assert np.allclose(series[0]["y"], np.array([5.0, 5.2, 5.1]) * np.pi / 180.0)
```

Update the existing CL test's `avl=` argument from `("CLtot", "CLa")` to `"CLtot"`, and give that fixture `alpha: [-4, 0, 4]` plus a `CLtot` list that is 0.51 at 4 degrees if the interpolation assertion stays. Update `avl=("CDtot", None)` and `avl=("CZtot", None)` call sites in this file to `"CDtot"` and `"CZtot"`. A scalar `CZtot` without an `alpha` list produces no AVL series (do not invent an x position).

- [ ] **Step 2: Run test to verify it fails**

Run: `cd Python && python -m pytest tests/test_solver_overlay.py -v`

Expected: FAIL because `avl` is still a `(value, slope)` pair and the new tests call it with a string.

- [ ] **Step 3: Write minimal implementation**

In `overlay_vs_alpha`, replace the AVL block with:

```python
ares = results.get("avl") or {}
if avl and avl in ares and "alpha" in ares:
    xs = np.asarray(ares["alpha"], dtype=float).reshape(-1)
    ys = np.asarray(ares[avl], dtype=float).reshape(-1)
    if xs.size == ys.size and xs.size > 0:
        kind = "line" if xs.size > 1 else "marker"
        series.append(
            {
                "label": "AVL",
                "x": xs,
                "y": ys,
                "style": "m.-" if kind == "line" else "m.",
                "kind": kind,
            }
        )
```

Delete `_vlm_line` use for AVL. Keep `_vlm_line` for Tornado. Delete `_avl_alpha_deg` if nothing else calls it.

In `overlay_derivative`, when `avl` is present and `ares[avl]` has the same length as `ares["alpha"]` (both arrays), append `kind: "line"` with `y = values * pi/180` and `x = alpha`. When both are a single number, append one marker at `ares["alpha"]` if that alpha exists; do not call `axhline` across `alpha_grid`. Tornado and flow5 hlines stay.

In `compare_tabs.py`, change each AVL tuple to the value key: `"CLtot"`, `"CDtot"`, `"CYtot"`, `"CZtot"`, `"CXtot"`, `"Cmtot"`, `"Cltot"`, `"Cntot"`. Derivative calls already pass `"CLa"`, `"Cma"`, `"CYb"`, `"Cnb"`, `"Clb"`. `_plot_force_extras` must not call `float()` on an array. Plot `CDind`, `CDvis`, and `e` only when `np.asarray(ares[key]).size == 1`. When they are sweep arrays, they are already on the CD line via `CDtot`; do not bar the first element.

In `results_panel.py`, delete the AVL block that plots `st["CL0"] + avl["CLa"] * alpha` and `st["Cm0"] + avl["Cma"] * alpha`. Plot `avl["alpha"]` against `avl["CLtot"]` and `avl["Cmtot"]` with `"m.-"` when those keys are present and the same length as `alpha`. Gold `avl.json` has `CLa` and no `CLtot`, so that panel draws no AVL line for a gold file.

In `Python/tests/test_gui_results_modes.py`, `test_cessna_stability_overlay_intercepts_match_matlab_formulas` asserts the magenta line equals `st["CL0"]`. Delete that magenta assertion. Do not add a fake `CLtot` onto the gold file to keep the old line.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd Python && python -m pytest tests/test_solver_overlay.py tests/test_gui_compare_tabs.py tests/test_gui_results_modes.py -v`

Expected: PASS. Update `test_gui_compare_tabs.py` fixtures in this same step if they still pass a slope pair or a scalar `CLtot` into a plot that now requires `alpha` and a list. Do not weaken an assertion to hide a slope line.

---

### Task 5: Plot solved AVL samples on the web charts

**Files:**
- Modify: `web/src/coeffOverlay.ts` (`seriesVsAlpha`, `seriesDerivative`)
- Modify: `web/src/aeroFigures.ts` (AVL specs and the extras/rate bars)
- Modify: `web/src/Results.tsx` (`LineFigureView`)
- Test: `web/src/coeffOverlay.test.ts`
- Test: `web/src/aeroFigures.test.ts`

**Interfaces:**
- Consumes: the same sweep dict the API already stores on `raws.avl` (`mapper_shaped_raw` listifies `alpha`, `CL`, `CD`, `Cm` from `CLtot` / `CDtot` / `Cmtot`).
- Produces: `seriesVsAlpha` `spec.avl` is a `string` key, not a `[value, slope]` pair. Samples are `pairedSamples(avl.alpha, avl[key], false)`. No `slopeLine` for AVL. `seriesDerivative` plots `value * pi/180` at `avl.alpha` when both arrays match in length. A series with one point is still returned; `LineFigureView` draws a `<circle>` of radius 3.5 when the polyline string has no space (one vertex).

- [ ] **Step 1: Write the failing test**

Replace `it("reconstructs AVL CL so y at 1 degree is 1.2")` in `web/src/coeffOverlay.test.ts` with:

```typescript
it("plots AVL CL at the solved angles and ignores CLa", () => {
  const series = seriesVsAlpha(
    {
      datcom: { alpha: [0, 1] },
      avl: { alpha: [-4, 0, 4], CLtot: [0.1, 0.4, 0.7], CLa: PER_RAD },
    },
    null,
    { avl: "CLtot" },
  );
  expect(series).toHaveLength(1);
  expect(series[0]).toMatchObject({
    solver: "avl",
    stroke: "magenta",
    kind: "line",
    x: [-4, 0, 4],
    y: [0.1, 0.4, 0.7],
  });
});
```

Replace the single-point AVL test so a scalar `CLtot` with scalar `alpha` is one point, and a missing `alpha` yields no series. Add:

```typescript
it("plots AVL CLa only at solved angles, in per degree", () => {
  const series = seriesDerivative(
    { avl: { alpha: [-4, 0, 4], CLa: [PER_RAD, PER_RAD, PER_RAD] } },
    null,
    { avl: "CLa" },
  );
  expect(series[0].x).toEqual([-4, 0, 4]);
  expect(series[0].y.every((value) => Math.abs(value - 1) < 1e-12)).toBe(true);
  expect(series[0].kind).toBe("line");
});
```

`PER_RAD` in that file is `180/pi`, so `PER_RAD * pi/180 === 1`.

In `web/src/aeroFigures.test.ts`, change the AVL CD expectation from a slope reconstruction to solved samples:

```typescript
avl: { alpha: [-4, 0, 4], CDtot: [0.01, 0.02, 0.04], CZtot: [-0.2, -0.5, -0.7], CXtot: [0.02, 0.03, 0.05], CYtot: [0, 0, 0] },
```

Assert the CD, CN, and CA series for solver `"avl"` have those `x` and `y` arrays. Delete any expectation that AVL CD is `{ x: [4], y: [0.3] }` from a lone total.

- [ ] **Step 2: Run test to verify it fails**

Run: `cd web && npm test -- src/coeffOverlay.test.ts src/aeroFigures.test.ts`

Expected: FAIL because `spec.avl` is still a pair and `seriesVsAlpha` still calls `slopeLine`.

- [ ] **Step 3: Write minimal implementation**

In `seriesVsAlpha`, type `avl?: string`. When `spec.avl` is set and `raws.avl` has that key and `alpha`:

```typescript
const samples = pairedSamples(avl.alpha, avl[spec.avl], false);
if (samples.x.length > 0) out.push(series("avl", samples.x, samples.y, "line"));
```

Remove the AVL `slopeLine` branch.

In `seriesDerivative`, for AVL (not Tornado, not flow5): if `alpha` and the derivative key are arrays of equal length, push `kind: "line"` with `y` equal to each value times `Math.PI / 180`. If both are one finite number, push one point at that alpha. Do not map the value onto `alphaGrid`.

In `aeroFigures.ts`, change `VsSpec.avl` from `[string, string | null]` to `string`. Change every `avl: ["CLtot", "CLa"]` style pair to `avl: "CLtot"` (and `"CDtot"`, `"CYtot"`, `"CZtot"`, `"CXtot"`, `"Cmtot"`, `"Cltot"`, `"Cntot"`). `derivLines` already passes `avl: "CLa"` and the other derivative names as strings; keep those names.

`forceExtras`: if `CDind`, `CDvis`, `e`, or `NP` is an array whose length is not 1, do not push a bar. Add line figures on the Forces tab for `CDind`, `CDvis`, and `e` via `alphaLines` with `avl` set to that key, so each solved angle is visible. Add an NP line on the Moments tab with `avl: "NP"`.

`rateBars`: when `raws.avl[group.avl]` is an array longer than 1, set that bar's `avl` to `null`. Add a Derivatives line figure per rate key (`Clp`, `Cmq`, `Cnr`, `CLp`, `CLq`, `CLr`) through `derivLines` so the per-angle AVL value is the line and Tornado remains the horizontal from its scalar.

In `LineFigureView`, when `svgPolyline` returns a string with no space and the series is not an hline, render:

```tsx
<circle cx={Number(pts.split(",")[0])} cy={Number(pts.split(",")[1])} r={3.5} fill={s.stroke} />
```

Keep the polyline for strings that contain a space.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd web && npm test -- src/coeffOverlay.test.ts src/aeroFigures.test.ts src/aeroChart.test.ts src/payload.test.ts && cd web && npx tsc --noEmit`

Expected: PASS. `mapper_shaped_raw` already turns a `CLtot` list into `raw["CL"]` and `raw["alpha"]`; no API change. If `aeroChart.test.ts` assumed an AVL hline across the DATCOM grid, update that fixture to solved alphas in this same step.

---

### Task 6: Docs

**Files:**
- Modify: `README.md` (the AVL row of the solver table, and the sentence that says Analyze runs one AVL case)
- Modify: `UPDATES.md` (new top entry `1.32.0`)

**Interfaces:**
- Consumes: the behavior from Tasks 3–5.
- Produces: a reader can tell AVL is solved at each `ALSCHD` angle and that the plots are those solutions.

- [ ] **Step 1: Update the docs**

`UPDATES.md` top entry:

```markdown
## 1.32.0 - AVL solved at each scheduled angle
- `run_avl_full` runs one AVL case per `AERO.ALSCHD` angle and returns totals and stability derivatives as arrays parallel to `alpha`
- Qt and web force, moment, and derivative charts plot those samples; AVL is not extended with `CLa` or any other slope
- MATLAB gold compare still checks the sweep sample at alpha 0
- Tests: `cd Python && python -m pytest tests/test_avl_stack_cases.py tests/test_avl_write_case_sweep.py tests/test_avl_gold_sample.py tests/test_avl_run_cessna.py tests/test_solver_overlay.py -q` and `cd web && npm test`
```

In `README.md`, state that AVL is one binary process with one OPER solution per `ALSCHD` angle, and that CL, CD, CY, CN, CA, and the moments on the plots are those solutions. Remove any sentence that says AVL is a single run case whose alpha slope is drawn across the axis.

- [ ] **Step 2: Check the entries**

Read the new `UPDATES.md` block and the AVL sentences in `README.md`. Confirm the version is `1.32.0`, the command lines match this plan, and no slope-extension wording remains.
