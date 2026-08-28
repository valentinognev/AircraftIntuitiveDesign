# AID Python GUI MATLAB Parity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **Implementer model:** Composer 2.5 (`composer-2.5`). **Never** Composer 2.5 Fast. **Reviewer model:** Grok (`cursor-grok-4.6-high`). Implementer must not spawn reviewers or subagents.

**Goal:** Make the Python PySide6 GUI match MATLAB `AID.m` / `Initialize_GUI.m` for Analyze → Tornado/AVL mesh dialogs, initial 3D camera, Aerodynamics layout + wing lift overlay, and the full Settings menu.

**Architecture:** Keep widgets in `aid_gui` and numeric ports in `aid`. MATLAB sources of truth: `AID.m` Analyze Tornado/AVL (~1690–1872), plot-mode switch (~1474–1505), Aerodynamics lift overlay (~1172–1292); `Initialize_GUI.m` `setting()` (~1203–1694); `Lifting_Line.m`, `Plot_Planform.m` case `'lift'`, `Downwash.m`, `Body_Stability.m`. Batch/compare stays headless (no dialogs, meshes 10×5 / 10×10).

**Tech Stack:** Python 3.11+, PySide6, pyvista/pyvistaqt, numpy, pytest. Offscreen GUI tests: `QT_QPA_PLATFORM=offscreen`.

**Spec:** `Docs/2026-08-26-aid-linux-python-port-spec.md` (GUI §14, batch meshes §16) plus **Requirements** below. Conflicts: this slice’s Requirements win over spec §14 “Settings stubs” / “defer interpolated shading”.

## Requirements (this slice)

1. **Analyze → Tornado/AVL** always shows MATLAB `inputdlg` **Wing Mesh Parameters** before running. Fields: Spanwise Nodes, Chordwise Nodes; plus Twist Linearity if `WG.TWISTA` is nonzero; plus Airfoil Interpolation Linearity if the wing has **more than one airfoil station** (`aid.viz._as_airfoils` length > 1 — not `len(DATA)` of xy points). Defaults: Tornado `10/5` (twist `2`, foil `3`); AVL `10/10` (twist `1`, foil `1`). Cancel aborts. Tests pass `mesh=` and never call `QDialog.exec()`.
2. **Initial 3D view** matches MATLAB `view(ax,3)`: azimuth −37.5°, elevation 30° (camera in −X/−Y/+Z). Nose toward the viewer. Not PyVista isometric.
3. **Aerodynamics** shows 3D + drag plot. MATLAB axes: 3D `[0.41,0.55,0.5,0.45]`, drag `[0.41,0.15,0.5,0.3]` → stacked split ≈ **60% 3D / 40% plot**. Drag canvas must not collapse. Stability = full-height CL/Cm; Geometry = 3D only.
4. **Aerodynamics 3D** draws Prandtl lifting-line arrows + blue Cl + black dashed Cl_ideal (`Plot_Planform` `'lift'`). After Analyze Tornado, add red VLM spanwise curve (`AID.m` ~1263–1285). Geometry mode has no overlay.
5. **Settings** items are enabled and behave as MATLAB `setting()`. Defaults: Interpolated Shading **on**, Multhopp **on**, ft-lb-kts **on**, Error Check **on**; all other listed checks **off**. Inputs/Outputs off until the user checks it, then extra Analyze dialogs run.
6. **Out of scope:** Help Examples/Quick Start/control legend; context-menu Reset/View/Background; ASCDM; FlightGear; Neutral Point `questdlg` (batch already skips it; GUI NP iterate stays later); DATCOM hidden Plot Results / Read Coefficients menus.

## Global Constraints

- OS: Linux. Work directory: `/home/valentin/Projects/MDT/USAF_DATCOM/AircraftIntuitiveDesign`.
- Package split: `Python/src/aid` (no widgets), `Python/src/aid_gui` (PySide6). Tests live in `Python/tests/`.
- Primary aircraft: **Cessna 172** (`Python/models/Cessna 172.jsonc`). `unit='ft'`, `WG.CHRDR=2`, `WG.SSPN=6`, `WG.TWISTA=0`, `WG.S=24`.
- Batch/compare meshes unchanged: Tornado `("10","5")` mode 0, AVL `("10","10")`, `check_io=false`. Do not add dialogs to `aid.compare` or `scripts/run_all.py`.
- TDD: failing test first, then minimal code. Every task has pytest.
- Implementer: **Composer 2.5** (`composer-2.5`). Never Composer 2.5 Fast. Never Kimi 3.
- Reviewer: **Grok** (`cursor-grok-4.6-high`).
- Do **not** `git commit` or `git push` unless the user explicitly asks. Record the suggested message in the task report.
- After each meaningful slice, bump `UPDATES.md` (project-docs). Only `README.md` and `UPDATES.md` among markdown files may be edited besides files this plan names.
- Offscreen: `os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")` at top of every GUI test file. Never `QDialog.exec()` / `QMessageBox.exec()` in tests; construct dialogs and call `accept()`/`reject()`, or pass `mesh=` / inject values.
- Do not change DATCOM/AVL theory or MATLAB gold runners.

## File structure (locked)

```
Python/src/aid/mesh_params.py              # CREATE — prompts/defaults (no Qt)
Python/src/aid/lifting_line.py             # CREATE — Lifting_Line.m
Python/src/aid/downwash.py                 # CREATE — Downwash.m
Python/src/aid/body_stability.py           # CREATE — Body_Stability.m
Python/src/aid/scale_geom.py               # CREATE — scale length fields
Python/src/aid/tornado/spanwise.py         # CREATE — AID.m spanwise Cl from VLM
Python/src/aid/viz.py                      # MODIFY — lift_overlay + public stations
Python/src/aid/tornado_io.py               # MODIFY — mesh type tuple[str, ...]
Python/src/aid/stability.py                # MODIFY — trim_mode, dwash override, angl
Python/src/aid_gui/settings.py             # CREATE — SettingsState + MATLAB defaults
Python/src/aid_gui/mesh_dialog.py          # CREATE — Wing Mesh Parameters QDialog
Python/src/aid_gui/menus.py                # MODIFY — enable Settings, wire callbacks
Python/src/aid_gui/main_window.py          # MODIFY — dialogs, camera, splitter, overlays
Python/src/aid_gui/view3d.py               # MODIFY — view(3), plot options, lift actors
Python/src/aid_gui/tabs.py                 # MODIFY — field writeback, scroll UserData
Python/src/aid_gui/results_panel.py        # MODIFY — min height for drag plot
Python/tests/test_mesh_params.py           # CREATE
Python/tests/test_lifting_line.py          # CREATE
Python/tests/test_lift_overlay.py          # CREATE
Python/tests/test_tornado_spanwise.py      # CREATE
Python/tests/test_gui_settings_defaults.py # CREATE
Python/tests/test_gui_mesh_dialog.py       # CREATE
Python/tests/test_gui_field_sync.py        # CREATE
Python/tests/test_gui_view_orientation.py  # CREATE
Python/tests/test_gui_aero_layout.py       # CREATE
Python/tests/test_gui_lift_overlay.py      # CREATE
Python/tests/test_gui_plot_options.py      # CREATE
Python/tests/test_scale_geom.py            # CREATE
Python/tests/test_gui_units_scale.py       # CREATE
Python/tests/test_gui_check_io.py          # CREATE
Python/tests/test_body_stability.py        # CREATE
Python/tests/test_downwash.py              # CREATE
Python/tests/test_gui_calculations.py      # CREATE
Python/tests/test_gui_estimate_cg.py       # CREATE
Python/tests/test_gui_error_scroll.py      # CREATE
```

Existing tests that call `w.run_tornado()` without `mesh=` must be updated in Task 8 to `w.run_tornado(mesh=("10","5"))`.

---

### Task 1: Mesh prompt fields (no Qt)

**Files:**
- Create: `Python/src/aid/mesh_params.py`
- Modify: `Python/src/aid/tornado_io.py` — annotation `mesh: tuple[str, ...]`
- Test: `Python/tests/test_mesh_params.py`

**Interfaces:**
- Consumes: `Aircraft.WG["TWISTA"]`, `aid.viz._as_airfoils`
- Produces: `mesh_fields(ac, solver: str) -> tuple[list[str], list[str]]` where `solver` is `"tornado"` or `"avl"`. Returns `(prompts, defaults)` matching `AID.m` 1696–1705 and 1851–1860.

- [ ] **Step 1: Write the failing test**

```python
# Python/tests/test_mesh_params.py
from copy import deepcopy
from aid.aircraft import load_jsonc
from aid.mesh_params import mesh_fields
from aid.paths import models_dir

def test_cessna_tornado_two_fields():
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    prompts, defaults = mesh_fields(ac, "tornado")
    assert prompts == ["Spanwise Nodes", "Chordwise Nodes"]
    assert defaults == ["10", "5"]

def test_cessna_avl_chord_ten():
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    prompts, defaults = mesh_fields(ac, "avl")
    assert prompts == ["Spanwise Nodes", "Chordwise Nodes"]
    assert defaults == ["10", "10"]

def test_twist_adds_third_field():
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    ac.WG = deepcopy(ac.WG)
    ac.WG["TWISTA"] = 5.0
    prompts, defaults = mesh_fields(ac, "tornado")
    assert prompts[-1] == "Twist Linearity"
    assert defaults == ["10", "5", "2"]
    _, avl_def = mesh_fields(ac, "avl")
    assert avl_def[-1] == "1"

def test_two_airfoils_adds_interpolation_field():
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    ac.WG = deepcopy(ac.WG)
    foil = ac.WG["DATA"]
    ac.WG["DATA"] = [foil, foil]
    ac.WG["TWISTA"] = 0
    prompts, defaults = mesh_fields(ac, "tornado")
    assert prompts[-1] == "Airfoil Interpolation Linearity"
    assert defaults[-1] == "3"
    _, avl_def = mesh_fields(ac, "avl")
    assert avl_def[-1] == "1"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /home/valentin/Projects/MDT/USAF_DATCOM/AircraftIntuitiveDesign/Python && python -m pytest tests/test_mesh_params.py -v
```

Expected FAIL: `ModuleNotFoundError: aid.mesh_params`.

- [ ] **Step 3: Write minimal implementation**

```python
# Python/src/aid/mesh_params.py
from aid.viz import _as_airfoils

def mesh_fields(ac, solver: str) -> tuple[list[str], list[str]]:
    prompts = ["Spanwise Nodes", "Chordwise Nodes"]
    if solver == "tornado":
        defaults = ["10", "5"]
        twist_def, foil_def = "2", "3"
    elif solver == "avl":
        defaults = ["10", "10"]
        twist_def, foil_def = "1", "1"
    else:
        raise ValueError(solver)
    if ac.WG.get("TWISTA"):
        prompts.append("Twist Linearity")
        defaults.append(twist_def)
    if len(_as_airfoils(ac.WG.get("DATA"))) > 1:
        prompts.append("Airfoil Interpolation Linearity")
        defaults.append(foil_def)
    return prompts, defaults
```

Export `_as_airfoils` from `viz.py` (already defined). Widen `tornado_io(ac, mesh: tuple[str, ...])`.

- [ ] **Step 4: Run test to verify it passes**

```bash
cd /home/valentin/Projects/MDT/USAF_DATCOM/AircraftIntuitiveDesign/Python && python -m pytest tests/test_mesh_params.py -v
```

Expected: PASS.

- [ ] **Step 5: Record commit message (do not commit unless asked)**

`feat: MATLAB Wing Mesh Parameters field list for Tornado/AVL`

---

### Task 2: Prandtl lifting line

**Files:**
- Create: `Python/src/aid/lifting_line.py`
- Test: `Python/tests/test_lifting_line.py`

**Interfaces:**
- Consumes: `Aircraft`, `aid.atmosphere.atmosphere`, `aid.stability.aircraft_stability` (for trim `alpha`)
- Produces: `lifting_line(ac, y, c, twist) -> dict` with keys `y`, `dy`, `Cl`, `Cl_ideal`, `scale`, `e`, `K`, `CL` (port `Lifting_Line.m`). `y`/`c`/`twist` are 1-D arrays along the **right** semi-span as `Plot_Planform` builds them. Output `y` is full span (negative to positive) like MATLAB.

Port `Matlab/fsroot/code/Lifting_Line.m` line-for-line: `v_inf = MACH * a` (ft/s), `alpha = st["alpha"] * pi/180`, `alpha_0 = (alpha0L - i - twist)*pi/180`. Use `WG.S[-1]`, `WG.b`, `WG.AR[-1]`, `max(BD.R)`.

- [ ] **Step 1: Write the failing test**

```python
# Python/tests/test_lifting_line.py
import numpy as np
from aid.aircraft import load_jsonc
from aid.lifting_line import lifting_line
from aid.paths import models_dir
from aid.viz import planform_stations

def test_cessna_lifting_line_elliptic_peak():
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    y, c, _dx, _dz, theta = planform_stations(ac.WG, 25, angle=True, kind="wing")
    out = lifting_line(ac, y, c, theta)
    assert out["y"][0] < 0 < out["y"][-1]
    assert abs(out["y"][0] + out["y"][-1]) < 1e-6
    i_root = int(np.argmin(np.abs(out["y"])))
    assert out["Cl_ideal"][i_root] > out["Cl_ideal"][0]
    assert out["scale"] == pytest_approx_max(out["Cl_ideal"])
    assert 0.8 < float(out["e"]) <= 1.0
    assert out["Cl"].shape == out["y"].shape

def pytest_approx_max(arr):
    import numpy as np
    m = float(np.max(np.abs(arr)))
    assert abs(m - float(np.max(np.abs(arr)))) < 1e-12
    return m
```

Fix the scale assert to:

```python
    assert out["scale"] == np.max(np.abs(out["Cl_ideal"]))
```

Delete `pytest_approx_max`. `planform_stations` is added in this task as a thin public wrapper around `viz._stations` (same signature as `_stations`). If wrapping in Task 2 is cleaner than Task 3, put `planform_stations = _stations` export in `viz.py` here.

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /home/valentin/Projects/MDT/USAF_DATCOM/AircraftIntuitiveDesign/Python && python -m pytest tests/test_lifting_line.py -v
```

Expected FAIL: missing `aid.lifting_line`.

- [ ] **Step 3: Write minimal implementation**

Port `Lifting_Line.m`. Use `np.linalg.solve(R, L)` for `A_ij`. Handle the `CHRDBP and SSPNOP` unique-y branch. Mirror gamma to full span exactly as MATLAB `y=[y1;-flipud(y1(1:end-1))]`.

- [ ] **Step 4: Run test to verify it passes**

```bash
cd /home/valentin/Projects/MDT/USAF_DATCOM/AircraftIntuitiveDesign/Python && python -m pytest tests/test_lifting_line.py -v
```

Expected: PASS.

- [ ] **Step 5: Record commit message (do not commit unless asked)**

`feat: port Prandtl lifting line from Lifting_Line.m`

---

### Task 3: Lift overlay polylines

**Files:**
- Modify: `Python/src/aid/viz.py`
- Test: `Python/tests/test_lift_overlay.py`

**Interfaces:**
- Consumes: `planform_stations`, `lifting_line`
- Produces: `lift_overlay(ac, nj: int, *, angle: bool = True) -> dict` with `X`, `Y`, `Z0`, `Cl`, `Cl_ideal` (already scaled: `Cl/scale*CHRDR` as `Plot_Planform.m` 497–498). `X = WG.X + xmac + cbar[-1]/4` (scalar broadcast). `Z0 = WG.Z`. `Y` is full-span from lifting_line.

- [ ] **Step 1: Write the failing test**

```python
# Python/tests/test_lift_overlay.py
import numpy as np
from aid.aircraft import load_jsonc
from aid.paths import models_dir
from aid.viz import lift_overlay

def test_cessna_lift_overlay_at_quarter_mac():
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    ov = lift_overlay(ac, 25, angle=True)
    x_expect = float(ac.WG["X"]) + float(np.asarray(ac.WG["xmac"]).reshape(-1)[-1]) + float(np.asarray(ac.WG["cbar"]).reshape(-1)[-1]) / 4
    assert np.allclose(ov["X"], x_expect)
    assert ov["Y"][0] < 0 < ov["Y"][-1]
    assert np.allclose(ov["Z0"], float(ac.WG["Z"]))
    assert np.max(np.abs(ov["Cl"])) == float(ac.WG["CHRDR"])  # scale to CHRDR
    assert ov["Cl_ideal"].shape == ov["Y"].shape
```

MATLAB: `Cl = Cl/scale*CHRDR` so `max(abs(Cl_ideal_scaled)) == CHRDR` because `scale = max(abs(Cl_ideal))`. Actual Cl (non-ideal) max may differ slightly — assert `max(abs(ov["Cl_ideal"])) == pytest.approx(ac.WG["CHRDR"])`.

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /home/valentin/Projects/MDT/USAF_DATCOM/AircraftIntuitiveDesign/Python && python -m pytest tests/test_lift_overlay.py -v
```

Expected FAIL: `lift_overlay` missing.

- [ ] **Step 3: Write minimal implementation** in `viz.py`.

- [ ] **Step 4: Run test to verify it passes**

```bash
cd /home/valentin/Projects/MDT/USAF_DATCOM/AircraftIntuitiveDesign/Python && python -m pytest tests/test_lift_overlay.py tests/test_lifting_line.py -v
```

Expected: PASS.

- [ ] **Step 5: Record commit message (do not commit unless asked)**

`feat: Plot_Planform lift overlay coordinates`

---

### Task 4: Tornado spanwise Cl

**Files:**
- Create: `Python/src/aid/tornado/spanwise.py`
- Test: `Python/tests/test_tornado_spanwise.py`

**Interfaces:**
- Consumes: `coeff_create` output plus `lattice`, `geo`, `state`; `Aircraft` for `WG.S`, `stability` `Q`
- Produces: `tornado_spanwise(coeffs, lattice, geo, state, ac) -> list[dict]` one dict per wing: `y`, `dy`, `Cl` matching `AID.m` 1769–1785. `L = ForcePerMeter / 4.44822 / 3.28084**2` (N/m → lb/ft), `Cl = L / (WG.S[-1] * Q)`.

Python `coeff_create` does **not** yet expose `ForcePerMeter`/`ystation`. Implement span-load assembly from panel forces `coeffs["F"]` and lattice collocation Y, grouped by `geo.ny` / symmetry, **or** port the `ForcePerMeter` block from `coeff_create3.m` 340–391 into `spanwise.py` (do not bloat `coeff.py` unless the port is a verbatim extract). Prefer a dedicated function that uses lattice `COLLOC`[:,1], panel `F`, and `geo["ny"]`/`geo["symetric"]`.

- [ ] **Step 1: Write the failing test**

```python
# Python/tests/test_tornado_spanwise.py
import math
import numpy as np
from aid.aircraft import load_jsonc
from aid.paths import models_dir
from aid.stability import aircraft_stability
from aid.tornado.boundary import set_boundary
from aid.tornado.coeff import coeff_create
from aid.tornado.lattice import lattice_setup
from aid.tornado.spanwise import tornado_spanwise
from aid.tornado.solver import solve
from aid.tornado_io import tornado_io

def test_cessna_tornado_spanwise_covers_span():
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    st = aircraft_stability(ac)
    geo, state = tornado_io(ac, ("10", "5"))
    state = dict(state)
    state["alpha"] = float(st["alpha"]) * math.pi / 180.0
    lattice, ref = lattice_setup(geo, state, 0)
    lattice = set_boundary(lattice, geo, state)
    raw = solve(state, geo, lattice)
    coeffs = coeff_create(raw, lattice, state, ref, geo)
    sw = tornado_spanwise(coeffs, lattice, geo, state, ac)
    assert len(sw) >= 1
    y = np.asarray(sw[0]["y"], dtype=float)
    cl = np.asarray(sw[0]["Cl"], dtype=float)
    assert y.size == cl.size
    assert y.min() < 0 < y.max()
    assert np.isfinite(cl).all()
    assert cl.max() > 0
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /home/valentin/Projects/MDT/USAF_DATCOM/AircraftIntuitiveDesign/Python && python -m pytest tests/test_tornado_spanwise.py -v
```

Expected FAIL: missing module.

- [ ] **Step 3: Write minimal implementation.** Match MATLAB unit conversion and `ystation ~= 0` mask.

- [ ] **Step 4: Run test to verify it passes**

```bash
cd /home/valentin/Projects/MDT/USAF_DATCOM/AircraftIntuitiveDesign/Python && python -m pytest tests/test_tornado_spanwise.py -v
```

Expected: PASS.

- [ ] **Step 5: Record commit message (do not commit unless asked)**

`feat: Tornado spanwise Cl for Aerodynamics overlay`

---

### Task 5: Settings menu enabled with MATLAB defaults

**Files:**
- Create: `Python/src/aid_gui/settings.py`
- Modify: `Python/src/aid_gui/menus.py` — stop `setEnabled(False)` on Settings items; attach `SettingsState`
- Modify: `Python/src/aid_gui/main_window.py` — `self.settings = SettingsState()` before `build_menus`
- Test: `Python/tests/test_gui_settings_defaults.py`

**Interfaces:**
- Consumes: MATLAB `Initialize_GUI.m` 134–176
- Produces: `class SettingsState` on the window with checkable `QAction`s and data:
  - `estimate_cg` off; `transparent` off, userdata alpha `0.3`; `show_axes` off; `plot_res` `[100,101,51]`; `shading` **on**; `project_dims` off; `ac_color` `(1,1,1)`; `trim_mode` userdata `[0, 30]`; `slipstream` off, userdata `[0.5, 0.9]`; `multhopp` **on**; `units_in` off; `units_kts` **on**; `check_io` off; `error_check` **on**, userdata `[999, 89, 0]`; `scroll` userdata `0.1`.
  - `window.settings.action(path: tuple[str,...]) -> QAction` e.g. `("Plot Options", "Transparent")`.

Callbacks may be no-ops until later tasks **except** checkable toggles must actually check/uncheck (MATLAB generic `setting` toggle).

- [ ] **Step 1: Write the failing test**

```python
# Python/tests/test_gui_settings_defaults.py
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication
from aid_gui.main_window import MainWindow

def _act(w, *labels):
    obj = w.menuBar()
    for lab in labels[:-1]:
        obj = [a for a in obj.actions() if a.text() == lab][0].menu()
    return [a for a in obj.actions() if a.text() == labels[-1]][0]

def test_settings_enabled_matlab_defaults():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    scale = _act(w, "Settings", "Scale A/C Size")
    assert scale.isEnabled()
    assert not _act(w, "Settings", "Estimate CG").isChecked()
    assert _act(w, "Settings", "Plot Options", "Interpolated Shading").isChecked()
    assert _act(w, "Settings", "Plot Options", "Interpolated Shading").isEnabled()
    assert not _act(w, "Settings", "Plot Options", "Transparent").isChecked()
    assert _act(w, "Settings", "Calculations", "Multhopp's Method").isChecked()
    assert not _act(w, "Settings", "Calculations", "Trim Mode").isChecked()
    assert _act(w, "Settings", "Units", "ft-lb-kts").isChecked()
    assert not _act(w, "Settings", "Units", "in-oz-ft/s").isChecked()
    assert _act(w, "Settings", "Error Check").isChecked()
    assert not _act(w, "Settings", "Inputs/Outputs").isChecked()
    trans = _act(w, "Settings", "Plot Options", "Transparent")
    trans.trigger()
    assert trans.isChecked()
```

MATLAB menu label is **Scale A/C Size** (`Initialize_GUI.m` 134). Python currently says `"Scale"`. Change the label to `Scale A/C Size` in this task.

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /home/valentin/Projects/MDT/USAF_DATCOM/AircraftIntuitiveDesign/Python && python -m pytest tests/test_gui_settings_defaults.py -v
```

Expected FAIL: actions disabled and/or wrong label.

- [ ] **Step 3: Write `SettingsState`, wire `build_menus(window)` to create checkable enabled actions with those defaults. Keep Help stubs unchanged.**

- [ ] **Step 4: Run test to verify it passes**

```bash
cd /home/valentin/Projects/MDT/USAF_DATCOM/AircraftIntuitiveDesign/Python && python -m pytest tests/test_gui_settings_defaults.py tests/test_gui_analyze_menu.py -v
```

Expected: PASS.

- [ ] **Step 5: Record commit message (do not commit unless asked)**

`feat: enable Settings menu with MATLAB check defaults`

---

### Task 6: Mesh dialog widget

**Files:**
- Create: `Python/src/aid_gui/mesh_dialog.py`
- Test: `Python/tests/test_gui_mesh_dialog.py`

**Interfaces:**
- Consumes: `mesh_fields(ac, solver)`
- Produces: `class MeshDialog(QDialog)` title `"Wing Mesh Parameters"`, `QFormLayout` of `QLineEdit`s, `values() -> tuple[str, ...] | None` (`None` if rejected). Do not call `exec()` inside the constructor.

- [ ] **Step 1: Write the failing test**

```python
# Python/tests/test_gui_mesh_dialog.py
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication, QDialog
from aid.aircraft import load_jsonc
from aid.paths import models_dir
from aid_gui.mesh_dialog import MeshDialog

def test_mesh_dialog_defaults_and_accept():
    app = QApplication.instance() or QApplication([])
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    dlg = MeshDialog(ac, "tornado")
    assert dlg.windowTitle() == "Wing Mesh Parameters"
    assert dlg.values() is None  # not yet accepted
    dlg.accept()
    assert dlg.result() == QDialog.DialogCode.Accepted
    assert dlg.values() == ("10", "5")

def test_mesh_dialog_reject_is_none():
    app = QApplication.instance() or QApplication([])
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    dlg = MeshDialog(ac, "avl")
    dlg.reject()
    assert dlg.values() is None
```

After `accept()`, `values()` must return the line-edit texts even without `exec()`. Store `_accepted` on `accept`/`reject`.

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /home/valentin/Projects/MDT/USAF_DATCOM/AircraftIntuitiveDesign/Python && python -m pytest tests/test_gui_mesh_dialog.py -v
```

Expected FAIL: missing `MeshDialog`.

- [ ] **Step 3: Implement dialog (OK/Cancel buttons).**

- [ ] **Step 4: Run test to verify it passes**

```bash
cd /home/valentin/Projects/MDT/USAF_DATCOM/AircraftIntuitiveDesign/Python && python -m pytest tests/test_gui_mesh_dialog.py -v
```

Expected: PASS.

- [ ] **Step 5: Record commit message (do not commit unless asked)**

`feat: Wing Mesh Parameters dialog widget`

---

### Task 7: Sync tab fields into Aircraft

**Files:**
- Modify: `Python/src/aid_gui/tabs.py` — add `sync_fields_to_aircraft(window) -> None`
- Modify: `Python/src/aid_gui/main_window.py` — call it at the start of `run_datcom` / `run_tornado` / `run_avl` (and later Scale)
- Test: `Python/tests/test_gui_field_sync.py`

**Interfaces:**
- Consumes: `window._field_edits`, `window.aircraft`
- Produces: mutating `Aircraft` dicts from QLineEdit text. Parse numbers with `ast.literal_eval` for lists (NACA/DATA stay as Python literals). Skip empty edits.

MATLAB reads GUI strings on every `AID` update. Without this, Settings Scale and edited CHRDR never reach solvers.

- [ ] **Step 1: Write the failing test**

```python
# Python/tests/test_gui_field_sync.py
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication
from aid.aircraft import load_jsonc
from aid.paths import models_dir
from aid_gui.main_window import MainWindow
from aid_gui.tabs import sync_fields_to_aircraft

def test_sync_writes_chrdr():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    w.load_aircraft(load_jsonc(models_dir() / "Cessna 172.jsonc"))
    w._field_edits["WG.CHRDR"].setText("2.5")
    sync_fields_to_aircraft(w)
    assert w.aircraft.WG["CHRDR"] == 2.5
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /home/valentin/Projects/MDT/USAF_DATCOM/AircraftIntuitiveDesign/Python && python -m pytest tests/test_gui_field_sync.py -v
```

Expected FAIL: `sync_fields_to_aircraft` missing.

- [ ] **Step 3: Implement. Call it from the three Analyze handlers before solver work.**

- [ ] **Step 4: Run test to verify it passes**

```bash
cd /home/valentin/Projects/MDT/USAF_DATCOM/AircraftIntuitiveDesign/Python && python -m pytest tests/test_gui_field_sync.py -v
```

Expected: PASS.

- [ ] **Step 5: Record commit message (do not commit unless asked)**

`feat: write GUI tab fields back into Aircraft`

---

### Task 8: Analyze Tornado/AVL use mesh dialog

**Files:**
- Modify: `Python/src/aid_gui/main_window.py` — `run_tornado(self, mesh=None)`, `run_avl(self, mesh=None)`. If `mesh is None`, construct `MeshDialog`, and if an event loop is running **and** `QT_QPA_PLATFORM != "offscreen"`, call `exec()`; otherwise (tests) treat missing mesh as the MATLAB defaults from `mesh_fields` **only when** a keyword is omitted in offscreen tests… **No.** Tests must pass `mesh=("10","5")`. Interactive GUI uses `exec()`. Offscreen + `mesh is None` must **not** hang: if `QT_QPA_PLATFORM=="offscreen"`, use `mesh_fields` defaults without exec (so a forgotten test still matches batch, but existing tests must be updated to pass mesh explicitly).
- Modify: `Python/tests/test_gui_results_modes.py` — `w.run_tornado(mesh=("10","5"))` at both call sites.

**Interfaces:**
- Consumes: `MeshDialog`, `mesh_fields`, existing `tornado_io` / `run_avl_full`
- Produces: GUI Analyze uses dialog values; cancel (`values() is None` after reject) returns without writing `last_results`.

- [ ] **Step 1: Write the failing test** (in `test_gui_mesh_dialog.py` or new `test_gui_analyze_mesh.py`)

```python
# add to Python/tests/test_gui_mesh_dialog.py
from aid_gui.main_window import MainWindow

def test_run_tornado_cancel_skips(monkeypatch):
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    w.load_aircraft(load_jsonc(models_dir() / "Cessna 172.jsonc"))
    class Fake:
        def exec(self):
            return 0
        def values(self):
            return None
    monkeypatch.setattr("aid_gui.main_window.MeshDialog", lambda *a, **k: Fake())
    w.run_tornado()
    assert "tornado" not in w.last_results

def test_run_tornado_mesh_kwarg_skips_dialog(monkeypatch):
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    w.load_aircraft(load_jsonc(models_dir() / "Cessna 172.jsonc"))
    called = []
    monkeypatch.setattr("aid_gui.main_window.MeshDialog", lambda *a, **k: called.append(1))
    w.run_tornado(mesh=("10", "5"))
    assert called == []
    assert "tornado" in w.last_results
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /home/valentin/Projects/MDT/USAF_DATCOM/AircraftIntuitiveDesign/Python && python -m pytest tests/test_gui_mesh_dialog.py -v
```

Expected FAIL: `run_tornado()` ignores cancel / always runs.

- [ ] **Step 3: Implement. Update `test_gui_results_modes.py` both `run_tornado()` calls. Interactive path: `dlg = MeshDialog(self.aircraft, "tornado"); if dlg.exec() != Accepted: return; mesh = dlg.values()`.**

- [ ] **Step 4: Run tests**

```bash
cd /home/valentin/Projects/MDT/USAF_DATCOM/AircraftIntuitiveDesign/Python && python -m pytest tests/test_gui_mesh_dialog.py tests/test_gui_results_modes.py tests/test_gui_analyze_datcom.py -v
```

Expected: PASS.

- [ ] **Step 5: Record commit message (do not commit unless asked)**

`feat: Analyze Tornado/AVL prompt for wing mesh`

---

### Task 9: MATLAB view(3) camera

**Files:**
- Modify: `Python/src/aid_gui/view3d.py` — replace `view_isometric()` with MATLAB `view(3)` vector
- Test: `Python/tests/test_gui_view_orientation.py`

**Interfaces:**
- Consumes: MATLAB `view(ax,3)` → az=−37.5°, el=30°. Camera direction from origin:
  `dx=cos(el)*sin(az)`, `dy=-cos(el)*cos(az)`, `dz=sin(el)` ≈ `(-0.527, -0.687, 0.5)`.
- Produces: `View3D.apply_matlab_view()` called at end of `plot_aircraft`. Expose `camera_xyz() -> tuple[float,float,float]` (plotter camera position).

- [ ] **Step 1: Write the failing test**

```python
# Python/tests/test_gui_view_orientation.py
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("PYVISTA_OFF_SCREEN", "true")
from PySide6.QtWidgets import QApplication
from aid.aircraft import load_jsonc
from aid.paths import models_dir
from aid_gui.main_window import MainWindow

def test_camera_is_nose_on_matlab_view3():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    w.load_aircraft(load_jsonc(models_dir() / "Cessna 172.jsonc"))
    pos = w.view3d.camera_xyz()
    foc = w.view3d.camera_focus()
    assert pos[0] < foc[0]  # camera toward -X relative to focus → nose toward viewer
    assert pos[1] < foc[1]
    assert pos[2] > foc[2]
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /home/valentin/Projects/MDT/USAF_DATCOM/AircraftIntuitiveDesign/Python && python -m pytest tests/test_gui_view_orientation.py -v
```

Expected FAIL: isometric camera has `pos[0] > foc[0]` (tail-on).

- [ ] **Step 3: After `reset_camera()`, `view_vector((dx,dy,dz), viewup=(0,0,1))`. Do not call `view_isometric()`.**

- [ ] **Step 4: Run tests**

```bash
cd /home/valentin/Projects/MDT/USAF_DATCOM/AircraftIntuitiveDesign/Python && python -m pytest tests/test_gui_view_orientation.py tests/test_gui_view3d.py -v
```

Expected: PASS.

- [ ] **Step 5: Record commit message (do not commit unless asked)**

`fix: 3D camera matches MATLAB view(3) nose-on`

---

### Task 10: Aerodynamics drag-plot height

**Files:**
- Modify: `Python/src/aid_gui/main_window.py` — `set_plot_mode("Aerodynamics")` stretch/sizes
- Modify: `Python/src/aid_gui/results_panel.py` — `setMinimumHeight(160)` on the canvas
- Modify: `Python/tests/test_gui_results_modes.py` or create `Python/tests/test_gui_aero_layout.py`

**Interfaces:**
- Consumes: MATLAB Aerodynamics axes heights 0.45 vs 0.3 → **60/40** of the right vertical splitter
- Produces: after `show()` + `resize(960,600)` + `set_plot_mode("Aerodynamics")` + `processEvents()`, `results_panel.height() / view3d.height()` in `0.45..0.90` (plot not a strip). Geometry still hides the panel. Stability still hides 3D.

- [ ] **Step 1: Write the failing test**

```python
# Python/tests/test_gui_aero_layout.py
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication
from aid.aircraft import load_jsonc
from aid.paths import models_dir
from aid_gui.main_window import MainWindow

def test_aerodynamics_plot_not_collapsed():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    w.show()
    w.resize(960, 600)
    w.load_aircraft(load_jsonc(models_dir() / "Cessna 172.jsonc"))
    w.set_plot_mode("Aerodynamics")
    app.processEvents()
    assert not w.results_panel.isHidden()
    assert not w.view3d.isHidden()
    assert w.results_panel.height() >= 160
    ratio = w.results_panel.height() / max(w.view3d.height(), 1)
    assert 0.4 <= ratio <= 1.2
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /home/valentin/Projects/MDT/USAF_DATCOM/AircraftIntuitiveDesign/Python && python -m pytest tests/test_gui_aero_layout.py -v
```

Expected FAIL: `results_panel.height() < 160` (stretch factor 0).

- [ ] **Step 3: For Aerodynamics, `setStretchFactor(0, 3)` and `setStretchFactor(1, 2)` and `setSizes([360, 240])` on `_right_splitter`. Keep Stability stretch 0/1 with 3D hidden. Geometry hides results_panel.**

- [ ] **Step 4: Run tests**

```bash
cd /home/valentin/Projects/MDT/USAF_DATCOM/AircraftIntuitiveDesign/Python && python -m pytest tests/test_gui_aero_layout.py tests/test_gui_results_modes.py -v
```

Expected: PASS.

- [ ] **Step 5: Record commit message (do not commit unless asked)**

`fix: Aerodynamics drag plot uses MATLAB 60/40 split`

---

### Task 11: Draw lifting-line overlay in Aerodynamics

**Files:**
- Modify: `Python/src/aid_gui/view3d.py` — `plot_lift_overlay(ov, tornado_sw=None)`
- Modify: `Python/src/aid_gui/main_window.py` — on Aerodynamics refresh, call overlay; Geometry/Stability clear it
- Test: `Python/tests/test_gui_lift_overlay.py`

**Interfaces:**
- Consumes: `lift_overlay(ac, nj)` with `nj = max(8, round(plot_res[1]/4))` (MATLAB `round(res(2)/4)`, default res wing 101 → 25)
- Produces: PyVista lines: blue Cl, black dashed Cl_ideal, arrows as lines from `(X,Y,Z0)` to `(X,Y,Z0+Cl)` color `(0.5, 0.6, 1)`. `View3D.overlay_count() -> int` ≥ 2 in Aerodynamics, `0` in Geometry.

- [ ] **Step 1: Write the failing test**

```python
# Python/tests/test_gui_lift_overlay.py
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("PYVISTA_OFF_SCREEN", "true")
from PySide6.QtWidgets import QApplication
from aid.aircraft import load_jsonc
from aid.paths import models_dir
from aid_gui.main_window import MainWindow

def test_aerodynamics_adds_lift_overlay():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    w.load_aircraft(load_jsonc(models_dir() / "Cessna 172.jsonc"))
    assert w.view3d.overlay_count() == 0
    w.set_plot_mode("Aerodynamics")
    app.processEvents()
    assert w.view3d.overlay_count() >= 2
    w.set_plot_mode("Geometry")
    app.processEvents()
    assert w.view3d.overlay_count() == 0
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /home/valentin/Projects/MDT/USAF_DATCOM/AircraftIntuitiveDesign/Python && python -m pytest tests/test_gui_lift_overlay.py -v
```

Expected FAIL: `overlay_count` 0 or missing.

- [ ] **Step 3: Implement. Store overlay actor names; `plot_aircraft` clears them.**

- [ ] **Step 4: Run tests**

```bash
cd /home/valentin/Projects/MDT/USAF_DATCOM/AircraftIntuitiveDesign/Python && python -m pytest tests/test_gui_lift_overlay.py tests/test_gui_view3d.py tests/test_gui_view_orientation.py -v
```

Expected: PASS.

- [ ] **Step 5: Record commit message (do not commit unless asked)**

`feat: Aerodynamics 3D Prandtl lift distribution overlay`

---

### Task 12: Tornado red spanwise overlay

**Files:**
- Modify: `Python/src/aid_gui/main_window.py` — after Tornado, stash `spanwise` on `last_results["tornado"]`
- Modify: `Python/src/aid_gui/view3d.py` — red line scaled like `AID.m` 1269–1272: `Cl * max(WG_spanwise.Cl)/max(Cl) / scale * CHRDR`
- Test: extend `Python/tests/test_gui_lift_overlay.py`

**Interfaces:**
- Consumes: Task 4 `tornado_spanwise`, Task 3 overlay for Prandtl `Cl` max/scale
- Produces: `overlay_count()` increases by 1 after `run_tornado(mesh=("10","5"))` while in Aerodynamics.

- [ ] **Step 1: Write the failing test**

```python
def test_tornado_adds_red_spanwise(monkeypatch):
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    w.load_aircraft(load_jsonc(models_dir() / "Cessna 172.jsonc"))
    w.set_plot_mode("Aerodynamics")
    app.processEvents()
    n0 = w.view3d.overlay_count()
    w.run_tornado(mesh=("10", "5"))
    w.set_plot_mode("Aerodynamics")
    app.processEvents()
    assert w.view3d.overlay_count() > n0
    assert "spanwise" in w.last_results["tornado"]
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /home/valentin/Projects/MDT/USAF_DATCOM/AircraftIntuitiveDesign/Python && python -m pytest tests/test_gui_lift_overlay.py::test_tornado_adds_red_spanwise -v
```

Expected FAIL: no extra overlay / no `spanwise` key.

- [ ] **Step 3: Implement scaling exactly as MATLAB. Skip HT overlay (commented out in AID.m).**

- [ ] **Step 4: Run tests**

```bash
cd /home/valentin/Projects/MDT/USAF_DATCOM/AircraftIntuitiveDesign/Python && python -m pytest tests/test_gui_lift_overlay.py tests/test_gui_results_modes.py -v
```

Expected: PASS.

- [ ] **Step 5: Record commit message (do not commit unless asked)**

`feat: Tornado VLM spanwise curve on Aerodynamics 3D`

---

### Task 13: Plot Options — Transparent, Axes, Shading, Color

**Files:**
- Modify: `Python/src/aid_gui/view3d.py`, `Python/src/aid_gui/settings.py`, `Python/src/aid_gui/menus.py`
- Test: `Python/tests/test_gui_plot_options.py`

**Interfaces:**
- **Transparent:** checked → mesh opacity `0.3` (userdata); unchecked → `1.0` (`setting` `'alpha'`).
- **Show Axes:** checked → add x/y/z lines and labels like MATLAB 1314–1326 (length from `BD.X[-1]/2`); switch camera to orthographic. Unchecked → remove lines, perspective, `apply_matlab_view` kept.
- **Interpolated Shading:** on → current smooth shading; off → `show_edges=True`, `smooth_shading=False` (MATLAB faceted/wireframe).
- **Aircraft Color:** `QColorDialog.getColor` is modal — in tests call `window.settings.set_ac_color((1,0,0))` which reapplies meshes. Default white.

- [ ] **Step 1: Write the failing test**

```python
# Python/tests/test_gui_plot_options.py
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("PYVISTA_OFF_SCREEN", "true")
from PySide6.QtWidgets import QApplication
from aid.aircraft import load_jsonc
from aid.paths import models_dir
from aid_gui.main_window import MainWindow

def _act(w, *labels):
    obj = w.menuBar()
    for lab in labels[:-1]:
        obj = [a for a in obj.actions() if a.text() == lab][0].menu()
    return [a for a in obj.actions() if a.text() == labels[-1]][0]

def test_transparent_sets_opacity():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    w.load_aircraft(load_jsonc(models_dir() / "Cessna 172.jsonc"))
    assert w.view3d.mesh_opacity() == 1.0
    _act(w, "Settings", "Plot Options", "Transparent").trigger()
    assert abs(w.view3d.mesh_opacity() - 0.3) < 1e-6
    _act(w, "Settings", "Plot Options", "Transparent").trigger()
    assert w.view3d.mesh_opacity() == 1.0

def test_show_axes_adds_actors():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    w.load_aircraft(load_jsonc(models_dir() / "Cessna 172.jsonc"))
    n0 = w.view3d.axis_actor_count()
    _act(w, "Settings", "Plot Options", "Show Axes").trigger()
    assert w.view3d.axis_actor_count() > n0
    assert w.view3d.is_parallel_projection() is True
    _act(w, "Settings", "Plot Options", "Show Axes").trigger()
    assert w.view3d.is_parallel_projection() is False

def test_shading_off_is_faceted():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    w.load_aircraft(load_jsonc(models_dir() / "Cessna 172.jsonc"))
    assert w.view3d.smooth_shading() is True
    _act(w, "Settings", "Plot Options", "Interpolated Shading").trigger()
    assert w.view3d.smooth_shading() is False

def test_set_ac_color_red():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    w.load_aircraft(load_jsonc(models_dir() / "Cessna 172.jsonc"))
    w.settings.set_ac_color((1.0, 0.0, 0.0))
    assert w.view3d.mesh_color()[:3] == (1.0, 0.0, 0.0)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /home/valentin/Projects/MDT/USAF_DATCOM/AircraftIntuitiveDesign/Python && python -m pytest tests/test_gui_plot_options.py -v
```

Expected FAIL: missing opacity/axis APIs.

- [ ] **Step 3: Implement. Color menu may open `QColorDialog` when triggered interactively; `set_ac_color` is the testable path. Store RGB on the action userdata.**

- [ ] **Step 4: Run tests**

```bash
cd /home/valentin/Projects/MDT/USAF_DATCOM/AircraftIntuitiveDesign/Python && python -m pytest tests/test_gui_plot_options.py tests/test_gui_view3d.py tests/test_gui_settings_defaults.py -v
```

Expected: PASS.

- [ ] **Step 5: Record commit message (do not commit unless asked)**

`feat: Plot Options transparent, axes, shading, color`

---

### Task 14: Plot Resolution and Project Dimensions

**Files:**
- Modify: `Python/src/aid_gui/view3d.py` — pass `res` and `angle` into `aircraft_surfaces`
- Modify: `Python/src/aid/viz.py` — `aircraft_surfaces(ac, angle=True, res=(100,101,51))` body/wing/tail
- Modify: `Python/src/aid_gui/settings.py` — Plot Resolution dialog fields Body/Wing/Tail; Project Dimensions check inverts `angl` (`AID.m`: `angl = ~Project Dimensions`)
- Test: extend `test_gui_plot_options.py`

**Interfaces:**
- Consumes: `opt(4) UserData [100,101,51]`; `opt(6)` Project Dimensions
- Produces: `window.settings.plot_res -> tuple[int,int,int]`; `window.settings.angle -> bool` (`True` when Project Dimensions is **unchecked**). Changing either rebuilds 3D. Tests set `settings.plot_res = (20,21,11)` without `exec()`.

MATLAB Plot Resolution dialog loops until Cancel — Python: one dialog, Cancel keeps previous. Tests: `settings.set_plot_res((20,21,11))`.

- [ ] **Step 1: Write the failing test**

```python
def test_project_dimensions_disables_angle():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    w.load_aircraft(load_jsonc(models_dir() / "Cessna 172.jsonc"))
    assert w.settings.angle is True
    _act(w, "Settings", "Plot Options", "Project Dimensions").trigger()
    assert w.settings.angle is False

def test_set_plot_res_changes_surface_count_path():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    w.load_aircraft(ac)
    n0 = w.view3d.mesh_count()
    w.settings.set_plot_res((20, 21, 11))
    w.view3d.plot_aircraft(ac, res=(20, 21, 11), angle=True)
    assert w.view3d.mesh_count() == n0  # same parts, coarser loft
    assert w.settings.plot_res == (20, 21, 11)
```

`aircraft_surfaces` currently uses `_RES_BODY=100`, `_RES_WING=101`, `_RES_TAIL=51`. After this task those defaults come from `res`. Mesh count stays the same number of surfaces; assert `plot_res` stored and `plot_aircraft` accepts `res=`.

Better test: `from aid.viz import aircraft_surfaces` and compare first wing grid shape vs res.

```python
def test_viz_res_changes_grid():
    from aid.viz import aircraft_surfaces
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    s_hi = aircraft_surfaces(ac, angle=True, res=(100, 101, 51))
    s_lo = aircraft_surfaces(ac, angle=True, res=(20, 21, 11))
    assert s_hi[0].x.shape[1] > s_lo[0].x.shape[1]
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /home/valentin/Projects/MDT/USAF_DATCOM/AircraftIntuitiveDesign/Python && python -m pytest tests/test_gui_plot_options.py tests/test_viz_cessna_surfaces.py -v
```

Expected FAIL: `aircraft_surfaces` has no `res=` (or ignores it).

- [ ] **Step 3: Thread `res` through `aircraft_surfaces` / `_planform_surfaces` / `_body_surfaces`. Wire Project Dimensions toggle to `angle`.**

- [ ] **Step 4: Run tests**

```bash
cd /home/valentin/Projects/MDT/USAF_DATCOM/AircraftIntuitiveDesign/Python && python -m pytest tests/test_gui_plot_options.py tests/test_gui_view3d.py tests/test_viz_cessna_surfaces.py tests/test_gui_lift_overlay.py -v
```

Expected: PASS.

- [ ] **Step 5: Record commit message (do not commit unless asked)**

`feat: plot resolution and Project Dimensions (angl)`

---

### Task 15: Scale A/C Size

**Files:**
- Create: `Python/src/aid/scale_geom.py`
- Modify: `Python/src/aid_gui/settings.py` / `main_window.py` — Scale dialog; tests call `scale_aircraft(ac, factor)` then `populate_from_aircraft`
- Test: `Python/tests/test_scale_geom.py`

**Interfaces:**
- Consumes: MATLAB scale block 1618–1671. Length planform keys `CHRDR,CHRDBP,CHRDTP,SSPN,SSPNOP,X,Y,Z` (not angles). Body `X,ZU,ZL,R`. AERO `WT,XCG` and fields 4–8 in MATLAB (`WT,XCG,...` — scale `AERO_In(4:8)`: WT, XCG, and the next three length-like aero fields present in the GUI). Python aero tab currently has ALSCHD, ALT, MACH, WT, XCG — scale **WT and XCG only** among those (MATLAB also scales unnamed 6–8 if they are length; do not scale MACH/ALSCHD/ALT).
- Produces: `scale_aircraft(ac: Aircraft, factor: float) -> Aircraft` (mutates and returns). Factor `1` is no-op.

- [ ] **Step 1: Write the failing test**

```python
# Python/tests/test_scale_geom.py
from aid.aircraft import load_jsonc
from aid.paths import models_dir
from aid.scale_geom import scale_aircraft

def test_scale_two_doubles_lengths_not_angles():
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    savsi0 = ac.WG["SAVSI"]
    chrdr0 = ac.WG["CHRDR"]
    xcg0 = ac.AERO["XCG"]
    scale_aircraft(ac, 2.0)
    assert ac.WG["CHRDR"] == chrdr0 * 2
    assert ac.WG["SSPN"] == 12
    assert ac.WG["SAVSI"] == savsi0
    assert ac.AERO["XCG"] == xcg0 * 2
    assert ac.AERO["MACH"] == 0.03 or ac.AERO["MACH"][0] == 0.03
```

Use `float(np.asarray(ac.AERO["MACH"]).reshape(-1)[0]) == 0.03`.

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /home/valentin/Projects/MDT/USAF_DATCOM/AircraftIntuitiveDesign/Python && python -m pytest tests/test_scale_geom.py -v
```

Expected FAIL: missing `scale_aircraft`.

- [ ] **Step 3: Implement. GUI: `Scale A/C Size` opens a one-field dialog (tests call `window.apply_scale(2.0)`). Then `populate_from_aircraft` + `plot_aircraft`.**

- [ ] **Step 4: Run tests**

```bash
cd /home/valentin/Projects/MDT/USAF_DATCOM/AircraftIntuitiveDesign/Python && python -m pytest tests/test_scale_geom.py tests/test_gui_field_sync.py tests/test_gui_tabs_cessna.py -v
```

Expected: PASS.

- [ ] **Step 5: Record commit message (do not commit unless asked)**

`feat: Settings Scale A/C Size`

---

### Task 16: Units in-oz-ft/s vs ft-lb-kts

**Files:**
- Modify: `Python/src/aid_gui/settings.py`, `main_window.py`, `aid/scale_geom.py` if useful
- Test: `Python/tests/test_gui_units_scale.py`

**Interfaces:**
- Consumes: MATLAB `'units'` 1365–1403. Checking `in-oz-ft/s` unchecks `ft-lb-kts` and vice versa. `questdlg` “Scale dimensions to maintain size?”: Yes → scale lengths by 12 or 1/12 and keep displayed length; No → `unit` flips, lengths numerically unchanged, WT converted `/12` or `*12`.
- Produces: `window.apply_units(to_in: bool, *, scale_size: bool)`. Tests never show `QMessageBox`. Drag plot xlabel already uses `unit != "in"` → knots (`drag_vs_speed`).

- [ ] **Step 1: Write the failing test**

```python
# Python/tests/test_gui_units_scale.py
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication
from aid.aircraft import load_jsonc
from aid.paths import models_dir
from aid_gui.main_window import MainWindow

def test_units_no_scale_converts_weight_only():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    w.load_aircraft(ac)
    chrdr = ac.WG["CHRDR"]
    wt = float(ac.AERO["WT"])
    w.apply_units(to_in=True, scale_size=False)
    assert w.aircraft.unit == "in"
    assert w.aircraft.WG["CHRDR"] == chrdr
    assert w.aircraft.AERO["WT"] == wt / 12

def test_units_scale_size_multiplies_lengths():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    w.load_aircraft(ac)
    w.apply_units(to_in=True, scale_size=True)
    assert w.aircraft.unit == "in"
    assert w.aircraft.WG["CHRDR"] == 24
```

MATLAB Yes when switching **to inches** uses `scale=12` (ft→in). WT `/scale` so weight in oz-ish. Match that.

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /home/valentin/Projects/MDT/USAF_DATCOM/AircraftIntuitiveDesign/Python && python -m pytest tests/test_gui_units_scale.py -v
```

Expected FAIL: `apply_units` missing.

- [ ] **Step 3: Implement. Mutual exclusion of the two Units actions. Interactive path may `QMessageBox` the Yes/No prompt; tests use `apply_units`.**

- [ ] **Step 4: Run tests**

```bash
cd /home/valentin/Projects/MDT/USAF_DATCOM/AircraftIntuitiveDesign/Python && python -m pytest tests/test_gui_units_scale.py tests/test_scale_geom.py tests/test_gui_settings_defaults.py -v
```

Expected: PASS.

- [ ] **Step 5: Record commit message (do not commit unless asked)**

`feat: Settings Units ft-lb-kts / in-oz-ft/s`

---

### Task 17: Inputs/Outputs extra Analyze dialogs

**Files:**
- Create: small dialog helpers in `Python/src/aid_gui/io_dialogs.py` or reuse form dialogs
- Modify: `Python/src/aid_gui/main_window.py` `run_tornado` / `run_avl` / `run_datcom`
- Test: `Python/tests/test_gui_check_io.py`

**Interfaces:**
- Consumes: `AID.m` `check_io` 1714–1739 (Tornado state `inputdlg` + wake `questdlg`); 1574–1598 DATCOM `type` files (Python: if check_io, `QMessageBox.information` with first 20 lines of `for005.dat` / DATCOM out — tests inject `check_io` and a callback). AVL `AVL_IO.m` 23–33 dumps `.avl`/`.run` text.
- Produces: `window.settings.check_io` bool. When True, after building Tornado `state`, apply `apply_tornado_state(state, values: dict)` from a non-exec test helper. Wake: `"Fixed Wake"` → `lattice_setup(..., mode=1)` else `mode=0`. Default mode 0.

Do **not** dump files to Notepad. Show a read-only `QDialog` with text (tests: `format_io_preview(path) -> str`).

- [ ] **Step 1: Write the failing test**

```python
# Python/tests/test_gui_check_io.py
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication
from aid.aircraft import load_jsonc
from aid.paths import models_dir
from aid_gui.main_window import MainWindow

def test_check_io_fixed_wake_mode(monkeypatch):
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    w.load_aircraft(load_jsonc(models_dir() / "Cessna 172.jsonc"))
    w.settings.check_io = True
    modes = []
    real_setup = __import__("aid.tornado.lattice", fromlist=["lattice_setup"]).lattice_setup
    def wrap(geo, state, mode):
        modes.append(mode)
        return real_setup(geo, state, mode)
    monkeypatch.setattr("aid_gui.main_window.lattice_setup", wrap)
    monkeypatch.setattr(w, "_tornado_io_extras", lambda state: {"mode": 1, "state": state})
    w.run_tornado(mesh=("10", "5"))
    assert 1 in modes
```

Simpler API: `run_tornado(mesh=("10","5"), *, vlm_mode=None, state_overrides=None)`. When `settings.check_io` and kwargs omitted, interactive dialogs run. Tests pass `vlm_mode=1`.

```python
def test_check_io_vlm_mode_kwarg():
    ...
    w.settings.check_io = True
    w.run_tornado(mesh=("10", "5"), vlm_mode=1)
    assert w.last_results["tornado"].get("vlm_mode") == 1
```

Store `vlm_mode` on results. Implementer threads `mode` into `lattice_setup`.

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /home/valentin/Projects/MDT/USAF_DATCOM/AircraftIntuitiveDesign/Python && python -m pytest tests/test_gui_check_io.py -v
```

Expected FAIL: always mode 0.

- [ ] **Step 3: Implement. When `check_io` is False, ignore extras (MATLAB).**

- [ ] **Step 4: Run tests**

```bash
cd /home/valentin/Projects/MDT/USAF_DATCOM/AircraftIntuitiveDesign/Python && python -m pytest tests/test_gui_check_io.py tests/test_gui_mesh_dialog.py tests/test_gui_results_modes.py -v
```

Expected: PASS.

- [ ] **Step 5: Record commit message (do not commit unless asked)**

`feat: Settings Inputs/Outputs extra solver dialogs`

---

### Task 18: Body_Stability and Downwash ports

**Files:**
- Create: `Python/src/aid/body_stability.py`
- Create: `Python/src/aid/downwash.py`
- Test: `Python/tests/test_body_stability.py`, `Python/tests/test_downwash.py`

**Interfaces:**
- Consumes: `Body_Stability.m`, `Downwash.m`
- Produces:
  - `body_stability(ac, method: str) -> dict` with `Cma`, `Cm0` written onto a copy of `BD`. `method` is `"Multhopp"` or `"Gilruth_White"`.
  - `downwash(ac) -> dict` with `HT.dwash`, `HT.eta`, `Z_eta`, `Z_w`.

Cessna JSONC already has `HT.dwash`, `HT.eta`, `BD.Cma`. Tests: Gilruth_White `Cma > 0`; Multhopp finite; downwash `0 < eta <= 1` and `dwash > 0` for Cessna.

- [ ] **Step 1: Write the failing tests**

```python
# Python/tests/test_body_stability.py
from aid.aircraft import load_jsonc
from aid.body_stability import body_stability
from aid.paths import models_dir

def test_cessna_multhopp_finite():
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    out = body_stability(ac, "Multhopp")
    assert out["Cma"] == out["Cma"]  # not NaN
    assert abs(out["Cma"]) > 0

def test_gilruth_positive_cma():
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    out = body_stability(ac, "Gilruth_White")
    assert out["Cma"] > 0
```

```python
# Python/tests/test_downwash.py
from aid.aircraft import load_jsonc
from aid.downwash import downwash
from aid.paths import models_dir

def test_cessna_downwash_eta():
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    out = downwash(ac)
    assert 0 < out["eta"] <= 1
    assert out["dwash"] > 0
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /home/valentin/Projects/MDT/USAF_DATCOM/AircraftIntuitiveDesign/Python && python -m pytest tests/test_body_stability.py tests/test_downwash.py -v
```

Expected FAIL: missing modules.

- [ ] **Step 3: Port MATLAB. Multhopp early-out to Gilruth when fwd/aft empty (`Body_Stability.m` 28).**

- [ ] **Step 4: Run tests**

```bash
cd /home/valentin/Projects/MDT/USAF_DATCOM/AircraftIntuitiveDesign/Python && python -m pytest tests/test_body_stability.py tests/test_downwash.py -v
```

Expected: PASS.

- [ ] **Step 5: Record commit message (do not commit unless asked)**

`feat: port Body_Stability and Downwash`

---

### Task 19: Calculations menu — Trim, Slipstream, Multhopp

**Files:**
- Modify: `Python/src/aid/stability.py` — optional `trim_mode: int`, `dwash`/`eta` overrides, `body_method`
- Modify: `Python/src/aid_gui/main_window.py` — `aircraft_stability` uses settings; refresh results bar
- Modify: `Python/src/aid_gui/settings.py`
- Test: `Python/tests/test_gui_calculations.py`

**Interfaces:**
- **Multhopp** checked (default): `body_stability(..., "Multhopp")` then use `BD.Cma` in handbook. Unchecked: Gilruth_White.
- **Estimate Slipstream** checked: `downwash(ac)` overwrites `HT.dwash`/`HT.eta`. Unchecked: userdata `[0.5, 0.9]` as MATLAB `dw` when slipstream off (`AID.m` 58–59, 908).
- **Trim Mode** checked: userdata `[1, delta_max]` elevator or `[2, delta]` incidence. Port `Longitudinal_Static_Stability.m` trim==1 (solve elevator `E.DELTA`). trim==2: linear solve for the two equations `CL = CL0+CLa*aoa`, `0 = Cm0+Cma*aoa` with the third constraint as MATLAB (`i_wg` held if `WG.i` nonempty). Tests use `window.apply_calculations()` without questdlg; `set_trim(1, 30)`.

Existing Cessna “13% stable” must **remain** with defaults (Multhopp on, slipstream off with 0.5/0.9 — wait: MATLAB default slipstream is **off**, so it uses userdata `[0.5, 0.9]` not `Downwash`. JSONC already stores computed `HT.dwash`/`eta`. When slipstream stays off, **do not overwrite** JSONC dwash unless the user opened the slipstream dialog. Match MATLAB: `if ~downwash, HT.dwash=dw(1); HT.eta=dw(2)`. That **does** overwrite with 0.5/0.9 on every MATLAB update when slipstream is off. Python currently uses JSONC values. For MATLAB parity, when slipstream is off apply userdata `[0.5, 0.9]`. That **will change** Cessna static margin vs current Python. **Ruling for implementers:** match MATLAB: slipstream off → `HT.dwash=0.5`, `HT.eta=0.9` during stability/update. Update `test_gui_results_modes.py` CG/stable strings if they change; recompute from `aircraft_stability` after the override. Do not freeze the old 13% if MATLAB would not.

Verify Cessna JSONC `HT.dwash` / `eta` vs 0.5/0.9 before changing tests. If handbook summary changes, update assertions to the new MATLAB-consistent values and note them in UPDATES.

- [ ] **Step 1: Write the failing test**

```python
# Python/tests/test_gui_calculations.py
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication
from aid.aircraft import load_jsonc
from aid.paths import models_dir
from aid.stability import aircraft_stability
from aid_gui.main_window import MainWindow

def test_slipstream_off_uses_userdata():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    w.load_aircraft(ac)
    st = w.stability_for_display()
    # MATLAB: dwash=0.5, eta=0.9 when Estimate Slipstream is off
    assert abs(w.aircraft.HT["dwash"] - 0.5) < 1e-9 or abs(st["CLa"] - aircraft_stability(ac)["CLa"]) > 0
```

Replace with a crisp assert after implementing `stability_for_display()`:

```python
def test_multhopp_toggle_changes_cma():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    w.load_aircraft(load_jsonc(models_dir() / "Cessna 172.jsonc"))
    w.settings.multhopp = True
    c1 = w.stability_for_display()["Cma"]
    w.settings.multhopp = False
    c2 = w.stability_for_display()["Cma"]
    assert c1 != c2
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /home/valentin/Projects/MDT/USAF_DATCOM/AircraftIntuitiveDesign/Python && python -m pytest tests/test_gui_calculations.py -v
```

Expected FAIL: missing `stability_for_display` / toggle has no effect.

- [ ] **Step 3: Implement. Trim==1: port elevator solve; write `E.DELTA` and refresh Control tab. Tests: `w.settings.set_trim(1, 30); w.apply_trim()` then `E.DELTA` is finite.**

- [ ] **Step 4: Run tests** including `test_gui_results_modes.py` — update numeric strings if MATLAB override requires it.

```bash
cd /home/valentin/Projects/MDT/USAF_DATCOM/AircraftIntuitiveDesign/Python && python -m pytest tests/test_gui_calculations.py tests/test_gui_results_modes.py tests/test_stability_cessna.py -v
```

Expected: PASS.

- [ ] **Step 5: Record commit message (do not commit unless asked)**

`feat: Calculations Trim, Slipstream, Multhopp`

---

### Task 20: Estimate CG

**Files:**
- Modify: `Python/src/aid_gui/settings.py`, `tabs.py`, `view3d.py`
- Test: `Python/tests/test_gui_estimate_cg.py`

**Interfaces:**
- Consumes: MATLAB `'weights'` 1547–1581. Checked: disable AERO WT and XCG edits; tint planforms missing `XCG` red (`FaceColor` red). Unchecked: re-enable edits, restore `ac_color`.
- Produces: `window.settings.estimate_cg` bool. `view3d.missing_cg_highlights() -> int`.

Cessna parts typically lack per-part `XCG` → all four highlight when checked.

- [ ] **Step 1: Write the failing test**

```python
# Python/tests/test_gui_estimate_cg.py
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("PYVISTA_OFF_SCREEN", "true")
from PySide6.QtWidgets import QApplication
from aid.aircraft import load_jsonc
from aid.paths import models_dir
from aid_gui.main_window import MainWindow

def _act(w, *labels):
    obj = w.menuBar()
    for lab in labels[:-1]:
        obj = [a for a in obj.actions() if a.text() == lab][0].menu()
    return [a for a in obj.actions() if a.text() == labels[-1]][0]

def test_estimate_cg_disables_aero_and_tints():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    w.load_aircraft(load_jsonc(models_dir() / "Cessna 172.jsonc"))
    assert w._field_edits["AERO.XCG"].isEnabled()
    _act(w, "Settings", "Estimate CG").trigger()
    assert not w._field_edits["AERO.XCG"].isEnabled()
    assert not w._field_edits["AERO.WT"].isEnabled()
    assert w.view3d.missing_cg_highlights() >= 1
    _act(w, "Settings", "Estimate CG").trigger()
    assert w._field_edits["AERO.XCG"].isEnabled()
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /home/valentin/Projects/MDT/USAF_DATCOM/AircraftIntuitiveDesign/Python && python -m pytest tests/test_gui_estimate_cg.py -v
```

Expected FAIL: fields stay enabled.

- [ ] **Step 3: Implement highlight via mesh color `(1,0,0)` on components without `XCG`. Do not build the full 3×10 weight table UI in this task; MATLAB also only toggles highlight + disable on the menu check. Component weight click-entry (`Initialize_GUI.m` ~2537+) is **out of this task** unless already reachable from Estimate CG — it is a separate click-on-part flow. Menu parity is the toggle above.

- [ ] **Step 4: Run tests**

```bash
cd /home/valentin/Projects/MDT/USAF_DATCOM/AircraftIntuitiveDesign/Python && python -m pytest tests/test_gui_estimate_cg.py tests/test_gui_plot_options.py -v
```

Expected: PASS.

- [ ] **Step 5: Record commit message (do not commit unless asked)**

`feat: Settings Estimate CG lock and highlight`

---

### Task 21: Error Check and Scroll Sensitivity

**Files:**
- Modify: `Python/src/aid_gui/tabs.py` — wheel event on `QLineEdit`, clamp using error limits
- Modify: `Python/src/aid_gui/settings.py`
- Test: `Python/tests/test_gui_error_scroll.py`

**Interfaces:**
- **Error Check** on (default): userdata `[max_length, max_angle, minimums]` default `[999, 89, 0]`. Length fields cannot exceed 999; angles 89. Tests: `clamp_field("WG.CHRDR", 5000) == 999` when enabled; when disabled, 5000 stays.
- **Scroll Sensitivity:** MATLAB sets per-field `UserData` increment (`setting` `'scroll'`). Default delta `0.1` or `10^(floor(log10(L))-2)` when the dialog runs. Tests: `window.settings.scroll_delta = 0.5` then `QTest.mouseWheel` or call `nudge_field(edit, +1)` → CHRDR 2.0 → 2.5. Angle fields nudge by 1 deg; CHSTAT by 0.01 (`Initialize_GUI.m` 1500–1511).

- [ ] **Step 1: Write the failing test**

```python
# Python/tests/test_gui_error_scroll.py
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication
from aid.aircraft import load_jsonc
from aid.paths import models_dir
from aid_gui.main_window import MainWindow
from aid_gui.tabs import clamp_value, nudge_field

def test_error_check_clamps_length():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    w.load_aircraft(load_jsonc(models_dir() / "Cessna 172.jsonc"))
    w.settings.error_check = True
    w.settings.error_limits = (999.0, 89.0, 0.0)
    assert clamp_value(w, "WG.CHRDR", 5000) == 999.0
    w.settings.error_check = False
    assert clamp_value(w, "WG.CHRDR", 5000) == 5000.0

def test_nudge_length_uses_scroll_delta():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    w.load_aircraft(load_jsonc(models_dir() / "Cessna 172.jsonc"))
    w.settings.scroll_delta = 0.5
    edit = w._field_edits["WG.CHRDR"]
    nudge_field(w, edit, +1)
    assert float(edit.text()) == 2.5
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /home/valentin/Projects/MDT/USAF_DATCOM/AircraftIntuitiveDesign/Python && python -m pytest tests/test_gui_error_scroll.py -v
```

Expected FAIL: missing helpers.

- [ ] **Step 3: Implement `wheelEvent` on a small `AidLineEdit(QLineEdit)` used in `_register_field`. Clamp on editingFinished when error_check is on.**

- [ ] **Step 4: Run tests**

```bash
cd /home/valentin/Projects/MDT/USAF_DATCOM/AircraftIntuitiveDesign/Python && python -m pytest tests/test_gui_error_scroll.py tests/test_gui_tabs_cessna.py tests/test_gui_field_sync.py -v
```

Expected: PASS.

- [ ] **Step 5: Record commit message (do not commit unless asked)**

`feat: Settings Error Check and Scroll Sensitivity`

---

### Task 22: README / UPDATES slice note

**Files:**
- Modify: `README.md` — reading order lists this plan; mention mesh dialog, view(3), Aerodynamics overlay, Settings live
- Modify: `UPDATES.md` — new top version **1.3.0** (feature: GUI MATLAB parity)
- Test: `Python/tests/test_project_docs.py` if it asserts a version — extend if needed

**Interfaces:**
- Consumes: project-docs rule
- Produces: agents know Settings are no longer stubs

- [ ] **Step 1: Write/adjust test**

```python
# add to Python/tests/test_project_docs.py if the file exists; else assert in a tiny test
from pathlib import Path
ROOT = Path("/home/valentin/Projects/MDT/USAF_DATCOM/AircraftIntuitiveDesign")

def test_updates_has_1_3_0_and_plan_named():
    text = (ROOT / "UPDATES.md").read_text()
    assert "## 1.3.0" in text
    readme = (ROOT / "README.md").read_text()
    assert "2026-08-27-aid-gui-matlab-parity-plan.md" in readme
```

If `test_project_docs.py` does not exist, create `Python/tests/test_gui_parity_docs.py` with that test.

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /home/valentin/Projects/MDT/USAF_DATCOM/AircraftIntuitiveDesign/Python && python -m pytest tests/test_gui_parity_docs.py -v
```

Expected FAIL: version/plan missing.

- [ ] **Step 3: Update docs. README Architecture: Settings are live, not stubs. Analyze Tornado/AVL mesh dialog. Batch still 10×5 / 10×10.**

- [ ] **Step 4: Run tests**

```bash
cd /home/valentin/Projects/MDT/USAF_DATCOM/AircraftIntuitiveDesign/Python && python -m pytest tests/test_gui_parity_docs.py tests/test_gui_settings_defaults.py -v
```

Expected: PASS.

- [ ] **Step 5: Record commit message (do not commit unless asked)**

`docs: GUI MATLAB parity 1.3.0`

---

## Execution

Each task: Composer 2.5 implementer (TDD, no subagents) → Grok `cursor-grok-4.6-high` task reviewer on the task diff. Do not parallelize implementers (file conflicts on `main_window.py` / `view3d.py` / `menus.py`).

Suggested order is the task numbers (1→22). Do not skip engine tasks 1–4; GUI overlays depend on them.

## Self-review

- Spec coverage: mesh dialog, camera, aero layout, lift overlay, every Settings item in the Requirements table has a task. Out-of-scope items are listed and have no tasks.
- No TBD in task bodies. Task 19 documents the MATLAB dwash overwrite and requires updating Cessna summary tests.
- Types: `mesh: tuple[str, ...]`, `SettingsState`, `lift_overlay` dict keys, `run_tornado(mesh=None, vlm_mode=None)` stay consistent across tasks 1, 6, 8, 17.
