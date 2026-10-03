# Alpha schedule default of 15 points

## Problem

Pressing **Analyze** produces coarse coefficient-vs-alpha curves. The cause is
`AERO.ALSCHD`, the alpha schedule every solver reads:

- `Python/src/aid/datcom_io.py:87` (`$FLTCON NALPHA=...,ALSCHD=...`)
- `Python/src/aid/avl_io.py:382` (one AVL solve per alpha)
- `Python/src/aid/tornado_io.py:376`
- `Python/src/aid/flow5_io.py:79`

The 23 shipped models hold only 5–6 points each (most are `[-4, 0, 4, 8, 12, 16]`),
so the plots have 5–6 markers. There is no hardcoded default anywhere — `ALSCHD`
is pure data.

## Goal

Default the analysis alpha sweep to **~15 points** on a **round increment**, so
curves are smooth without making AVL (one solve per alpha) slow. `ALPHA_POINTS`
is a single constant so it can be raised later.

## Global Constraints

- Target is **15**, not 50 (perf: AVL solves once per alpha, `avl_io.py:392`).
- Increment must come from a round ladder — never a computed fractional step.
- Both endpoints of the existing range are always preserved.
- A degenerate range (`span == 0`) is returned unchanged.
- An input already at or above the target point count is left alone.
- Resampling preserves each model's **existing** min/max range; it never widens
  or narrows the envelope.
- No behaviour change outside `ALSCHD`.

## Task 1 — `aid/alpha_schedule.py`

New module `Python/src/aid/alpha_schedule.py`:

```python
ALPHA_POINTS = 15
_STEP_LADDER = (0.05, 0.1, 0.2, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0)

def alpha_schedule(ac, target: int = ALPHA_POINTS) -> list[float]: ...
def apply_alpha_default(ac, target: int = ALPHA_POINTS): ...
```

- `alpha_schedule` reads `ac.AERO["ALSCHD"]`, tolerating scalar, list, tuple,
  numpy array and `None`-ish shapes.
- `lo`/`hi` = min/max of the finite values.
- `span == 0` → `[lo]`.
- Already `>= target` points → returned unchanged (verbatim, not re-rounded).
- Otherwise, for each ladder step `s`: `n = floor(span / s + 1e-9) + 1`.
  Choose the `n` closest to `target`; tie → the **finer** (smaller) step.
- Build `[lo + i * s for i in range(n)]`, then append `hi` if the last value is
  short of `hi` by more than `1e-9`.
- `apply_alpha_default` writes the result back into `ac.AERO["ALSCHD"]` and
  returns the aircraft, so every downstream reader (solvers, `stability.py:221`,
  `tornado/control_deriv.py:103`, `trim.py:106`, plots) sees one schedule.

Tests in `Python/tests/test_alpha_schedule.py`, written first:

- round step chosen; count within ±6 of 15 for spans 4, 16, 20, 28, 40
- endpoints preserved for both round and non-round spans
- degenerate / scalar / single-element input unchanged
- input already at or above target left verbatim
- `apply_alpha_default` mutates `ac.AERO["ALSCHD"]` and is idempotent
- numpy array input does not leak a numpy scalar into the stored list

## Task 2 — call sites

`apply_alpha_default` is called at the Analyze entry points, not at each solver
read site, so the Aero tab shows the expanded list instead of hiding it.

- `Python/src/aid_gui/main_window.py`: `run_datcom`, `run_tornado`, `run_avl`,
  `run_flow5`, `run_control_derivatives`
- `api/aid_web/analyze.py`: `analyze_datcom`, `analyze_tornado`, `analyze_avl`,
  `analyze_flow5`, `control_derivatives`

Tests:

- `Python/tests/test_alpha_schedule.py` gains GUI-entry-point coverage asserting
  each entry point expands `ALSCHD` (follow the existing monkeypatch style in
  `Python/tests/test_gui_analyze_flow5.py`).
- `api/tests/` gains the equivalent coverage for the web entry points, following
  the existing style in `api/tests/test_analyze_spanwise.py`.

## Task 3 — resample the shipped models

Apply the same `alpha_schedule` to all 23 files in `Python/models/*.jsonc`,
preserving each model's current `lo`/`hi`. `T-38.jsonc` has scalar `"ALSCHD": 0`
and is a no-op.

Numeric lists are written one number per line (`aid/jsonc.py:69`), so this adds
roughly one line per point per file.

Tests: every shipped `.jsonc` except `T-38.jsonc` yields `>= 11` points, and the
range of every resampled file equals the pre-change range.

## Task 4 — docs

New top entry in `UPDATES.md` (feature → bump the sub-version). `README.md` only
if the alpha default counts as architecture; it does not.

## Verification

Run from `.worktrees/alpha-default-50`:

```
cd Python && PYTHONPATH=src python -m pytest tests/ -q
cd api    && PYTHONPATH=../Python/src python -m pytest tests/ -q
```

Known pre-existing failure in a worktree: `tests/test_paths.py::test_paths_resolve`
asserts `repo_root().name == "AircraftIntuitiveDesign"`, which a worktree
directory cannot satisfy. Not caused by this change.