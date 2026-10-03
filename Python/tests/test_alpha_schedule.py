import ast
import math
import os
from itertools import pairwise

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np
import pytest
from PySide6.QtWidgets import QApplication

from aid.aircraft import Aircraft, load_jsonc
from aid.alpha_schedule import ALPHA_POINTS, alpha_schedule, apply_alpha_default
from aid.paths import models_dir
from aid_gui.main_window import MainWindow
from aid_gui.tabs import sync_fields_to_aircraft

# A deliberately sparse schedule, set explicitly so the tests do not depend on
# what a shipped model happens to store. The default schedule is that envelope
# on a 1-degree step.
SPARSE_TEXT = "-4, 0, 4, 8, 12"
CESSNA_EXPANDED = [-4.0 + i for i in range(17)]


def _craft(alschd) -> Aircraft:
    return Aircraft(
        WG={},
        HT={},
        VT={},
        F={},
        A={},
        E={},
        R={},
        BD={},
        NP=[],
        NB=[],
        AERO={"ALSCHD": alschd},
        plot_cmp=[],
        unit="ft",
    )


def _step(sched: list[float]) -> float:
    return round(sched[1] - sched[0], 9)


@pytest.mark.parametrize(
    ("span", "expected_step", "expected_count"),
    [(4, 0.2, 21), (16, 1.0, 17), (20, 2.0, 11), (28, 2.0, 15), (40, 2.0, 21)],
)
def test_span_fills_to_target_on_round_step(span, expected_step, expected_count):
    sched = alpha_schedule(_craft([-4.0, -4.0 + span]))
    assert len(sched) == expected_count
    assert _step(sched) == expected_step
    assert {round(b - a, 9) for a, b in pairwise(sched)} == {expected_step}
    assert abs(len(sched) - ALPHA_POINTS) <= 6


@pytest.mark.parametrize("span", [16, 28, 5.3, 20.7])
def test_endpoints_preserved(span):
    sched = alpha_schedule(_craft([-span, span]))
    assert sched[0] == pytest.approx(-span)
    assert sched[-1] == pytest.approx(span)
    assert all(b > a for a, b in pairwise(sched))


def test_tie_between_ladder_steps_prefers_finer_step():
    sched = alpha_schedule(_craft([-4, 36]))
    assert _step(sched) == 2.0
    assert len(sched) == 21


@pytest.mark.parametrize(
    ("alschd", "expected"),
    [(0, [0.0]), ([3.5], [3.5]), ((-2.0,), [-2.0]), ([2.0, 2.0], [2.0]),
     (np.array(3.0), [3.0])],
)
def test_degenerate_input_kept(alschd, expected):
    assert alpha_schedule(_craft(alschd)) == expected


@pytest.mark.parametrize("alschd", [None, [], np.array([])])
def test_empty_input_yields_empty_schedule(alschd):
    assert alpha_schedule(_craft(alschd)) == []


@pytest.mark.parametrize(
    "given",
    [
        [-4.0, -1.3, 0.0, 2.7, 5.5, 7.1, 9.9, 11.3, 13.0, 15.7,
         17.2, 19.9, 21.4, 23.8, 26.0],
        [-4.0, -1.3, 0.0, 2.7, 5.5, 7.1, 9.9, 11.3, 13.0, 15.7,
         17.2, 19.9, 21.4, 23.8, 26.0, 28.4, 30.1],
    ],
    ids=["at-target", "above-target"],
)
def test_dense_input_returned_verbatim(given):
    assert alpha_schedule(_craft(given)) == given


def test_target_override_thresholds_on_count():
    given = [0.0, 5.0, 10.0, 15.0, 20.0]
    assert alpha_schedule(_craft(given), target=5) == given
    assert len(alpha_schedule(_craft(given), target=15)) == 11


def test_apply_alpha_default_writes_schedule_and_returns_aircraft():
    ac = _craft([-4, 0, 4, 8, 12, 16])
    out = apply_alpha_default(ac)
    assert out is ac
    assert ac.AERO["ALSCHD"] == [-4.0, -2.0, 0.0, 2.0, 4.0, 6.0, 8.0,
                                  10.0, 12.0, 14.0, 16.0]
    assert ac.AERO["ALSCHD"] == alpha_schedule(ac)


def test_non_finite_entries_ignored():
    sched = alpha_schedule(_craft([0.0, math.nan, 4.0]))
    assert all(math.isfinite(a) for a in sched)
    assert sched[0] == 0.0
    assert sched[-1] == pytest.approx(4.0)


def test_column_shaped_array_matches_flat_list():
    flat = alpha_schedule(_craft([-4.0, 0.0, 4.0, 8.0, 12.0, 16.0]))
    column = alpha_schedule(_craft(np.array([[-4.0], [0.0], [4.0], [8.0], [12.0], [16.0]])))
    assert column == flat


def test_apply_alpha_default_is_idempotent():
    ac = _craft([-4, 0, 4, 8, 12, 16])
    apply_alpha_default(ac)
    first = list(ac.AERO["ALSCHD"])
    apply_alpha_default(ac)
    assert ac.AERO["ALSCHD"] == first


def test_apply_alpha_default_stores_plain_floats_from_numpy_input():
    ac = _craft(np.array([-4.0, 0.0, 4.0, 8.0, 12.0, 16.0]))
    apply_alpha_default(ac)
    assert all(type(a) is float for a in ac.AERO["ALSCHD"])


def test_absent_key_is_not_introduced():
    ac = _craft([-4, 0, 4])
    ac.AERO.pop("ALSCHD")
    out = apply_alpha_default(ac)
    assert out is ac
    assert "ALSCHD" not in ac.AERO


class _SolverReached(Exception):
    """Stops a GUI entry point at its first solver call."""


def _cessna_window() -> MainWindow:
    """Cessna geometry with the sparse ALSCHD typed into the Aero field."""
    QApplication.instance() or QApplication([])
    w = MainWindow()
    w.load_aircraft(load_jsonc(models_dir() / "Cessna 172.jsonc"))
    w._field_edits["AERO.ALSCHD"].setText(SPARSE_TEXT)
    return w


def _drive(monkeypatch, method, solver, kwargs) -> tuple[MainWindow, list]:
    """Run one GUI entry point up to its first solver call; return the window
    and the schedules the solver was handed."""
    seen: list = []

    def stop(ac, *args, **kw):
        seen.append(list(ac.AERO["ALSCHD"]))
        raise _SolverReached

    monkeypatch.setattr(solver, stop)
    w = _cessna_window()
    with pytest.raises(_SolverReached):
        getattr(w, method)(**kwargs)
    return w, seen


@pytest.mark.parametrize(
    ("method", "solver", "kwargs"),
    [
        ("run_datcom", "aid_gui.main_window.write_for005", {}),
        ("run_tornado", "aid_gui.main_window.tornado_io", {"mesh": ("6", "3")}),
        ("run_avl", "aid_gui.main_window.run_avl_full", {"mesh": ("6", "3")}),
        ("run_flow5", "aid_gui.main_window.run_flow5", {"mesh": ("6", "3")}),
        ("run_control_derivatives", "aid_gui.main_window.control_report", {}),
    ],
    ids=["datcom", "tornado", "avl", "flow5", "control_derivatives"],
)
def test_analyze_entry_points_expand_alschd_before_the_solver(
    monkeypatch, method, solver, kwargs
):
    """Every GUI Analyze entry point hands the expanded schedule to its solver."""
    w, seen = _drive(monkeypatch, method, solver, kwargs)
    assert seen == [CESSNA_EXPANDED]
    assert w.aircraft.AERO["ALSCHD"] == CESSNA_EXPANDED


def test_aero_field_shows_the_expanded_schedule(monkeypatch):
    """The Aero field must mirror the model, or the next field sync reverts it."""
    w, _ = _drive(
        monkeypatch, "run_flow5", "aid_gui.main_window.run_flow5", {"mesh": ("6", "3")}
    )
    text = w._field_edits["AERO.ALSCHD"].text()
    assert ast.literal_eval(text) == CESSNA_EXPANDED
    sync_fields_to_aircraft(w)
    assert w.aircraft.AERO["ALSCHD"] == CESSNA_EXPANDED


def test_analyze_entry_point_does_not_introduce_alschd(monkeypatch):
    """A blanked ALSCHD field stays absent; an Analyze run must not invent one."""

    def stop(ac, mesh, **kw):
        raise _SolverReached

    monkeypatch.setattr("aid_gui.main_window.run_flow5", stop)
    w = _cessna_window()
    w._field_edits["AERO.ALSCHD"].setText("")
    w.aircraft.AERO.pop("ALSCHD")
    with pytest.raises(_SolverReached):
        w.run_flow5(mesh=("6", "3"))
    assert "ALSCHD" not in w.aircraft.AERO


# (low, high) of every shipped model as it was before the resample. The resample
# refines the schedule but must not move the envelope it sweeps.
SHIPPED_ALSCHD_RANGES = {
    "ASW-20 Sailplane.jsonc": (-9.0, 10.0),
    "B-1 Lancer.jsonc": (-4.0, 16.0),
    "Beechcraft T-34C.jsonc": (-16.0, 24.0),
    "Boeing 727.jsonc": (-4.0, 16.0),
    "Boeing 737Max.jsonc": (-4.0, 16.0),
    "Boeing 747-400.jsonc": (-4.0, 16.0),
    "Box.jsonc": (-4.0, 16.0),
    "Cessna 172.jsonc": (-4.0, 12.0),
    "DA20-C1.jsonc": (-4.0, 16.0),
    "ERAU DBF Plane.jsonc": (-2.0, 16.0),
    "Enterprise.jsonc": (-4.0, 16.0),
    "F-16.jsonc": (-4.0, 16.0),
    "HK36.jsonc": (2.0, 8.0),
    "Learjet 23.jsonc": (-4.0, 16.0),
    "Navion.jsonc": (-4.0, 24.0),
    "Orbiter.jsonc": (-4.0, 16.0),
    "Rocket Prop.jsonc": (-4.0, 16.0),
    "SR-71.jsonc": (-4.0, 16.0),
    "Ski Plane.jsonc": (-4.0, 16.0),
    "Sphere.jsonc": (-4.0, 16.0),
    "X-Wing.jsonc": (-4.0, 16.0),
    "XB-70 Valkyrie.jsonc": (-4.0, 16.0),
}
# Scalar ALSCHD, no schedule to expand; deliberately left alone.
SCALAR_ALSCHD_MODEL = "T-38.jsonc"
MIN_SHIPPED_POINTS = 11
SHIPPED_NAMES = sorted(SHIPPED_ALSCHD_RANGES)


def _shipped_alschd(name: str) -> list[float]:
    stored = load_jsonc(models_dir() / name).AERO["ALSCHD"]
    return [float(a) for a in stored]


def test_range_table_covers_every_shipped_model():
    shipped = {p.name for p in models_dir().glob("*.jsonc")}
    assert shipped == set(SHIPPED_ALSCHD_RANGES) | {SCALAR_ALSCHD_MODEL}


@pytest.mark.parametrize("name", SHIPPED_NAMES)
def test_shipped_alschd_is_fine_enough(name):
    """A shipped model must already carry a plot-grade schedule on disk."""
    assert len(_shipped_alschd(name)) >= MIN_SHIPPED_POINTS


@pytest.mark.parametrize(("name", "expected"), SHIPPED_ALSCHD_RANGES.items())
def test_shipped_alschd_range_did_not_move(name, expected):
    sched = _shipped_alschd(name)
    assert (min(sched), max(sched)) == pytest.approx(expected)


@pytest.mark.parametrize("name", SHIPPED_NAMES)
def test_shipped_alschd_equals_the_runtime_default(name):
    """The files are already the default schedule, so a run changes nothing."""
    ac = load_jsonc(models_dir() / name)
    assert [float(a) for a in ac.AERO["ALSCHD"]] == alpha_schedule(ac)


def test_scalar_alschd_model_left_alone():
    assert load_jsonc(models_dir() / SCALAR_ALSCHD_MODEL).AERO["ALSCHD"] == 0
