"""The Aero tab carries the sideslip angle, and the overlays say who flew it.

Two separate claims, and the second is the reason this file exists:

1. ``AERO.BETA`` (degrees) reaches every engine from the window, and a blank field
   means symmetric flight (0.0) rather than "leave it alone" -- ``save_jsonc`` omits
   default-valued AERO keys, so a model with no ``BETA`` line must still read 0.0.

2. Only Tornado and flow5's *force* channels respond to sideslip. DATCOM and AVL
   have no sideslip capability in their interfaces, and flow5's twelve stability
   derivatives are computed by ``computeStabilityDerivatives``, which builds its
   axes from ``windDirection(alpha, 0.0)``. So at beta != 0 the overlays must say
   "(beta=0)" on DATCOM, on AVL *and* on flow5's derivative series, or the panel
   claims agreement across solvers that flew different conditions.
"""

import inspect
import math
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np
import pytest
from PySide6.QtWidgets import QApplication

from aid.aircraft import aero_beta, load_jsonc
from aid.paths import models_dir
from aid.solver_overlay import overlay_derivative, overlay_vs_alpha
from aid.tornado_io import tornado_io
from aid_gui import main_window as main_window_mod
from aid_gui.main_window import MainWindow


class _ReachedState(Exception):
    """Stops a Tornado run once the flight state has been captured."""


def _window(beta: float | None = None):
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    w.load_aircraft(load_jsonc(models_dir() / "Cessna 172.jsonc"))
    if beta is not None:
        w._beta_widgets["BETA"].setText(str(beta))
        main_window_mod.sync_fields_to_aircraft(w)
    return w


def _st() -> dict:
    return {
        "alpha": 4.0,
        "CL0": 0.25,
        "CLa": 0.08,
        "CL": 0.57,
        "Cm0": 0.05,
        "Cma": -0.01,
        "Cm_CL": -0.12,
    }


def _results() -> dict:
    return {
        "datcom": {
            "alpha": np.array([-4.0, 0.0, 4.0]),
            "cl": np.array([-0.2, 0.13, 0.52]),
            "cla": np.array([0.085, 0.092, 0.100]),
            "cyb": np.array([-0.012, -0.012, -0.011]),
        },
        "tornado": {
            "alpha": float(np.deg2rad(4.0)),
            "CL": 0.50,
            "CL_a": 5.0,
            "CY_b": 0.15,
        },
        "avl": {
            "alpha": [-4.0, 0.0, 4.0],
            "CLtot": [0.10, 0.30, 0.51],
            "CYb": [-0.013, -0.013, -0.012],
        },
        "flow5": {
            "alpha": np.array([-4.0, 0.0, 4.0]),
            "CL": np.array([-0.1, 0.2, 0.5]),
            "CYb": 0.014,
        },
    }


def test_aero_tab_has_a_beta_field():
    w = _window()
    assert "BETA" in w._beta_widgets
    assert w._field_edits["AERO.BETA"] is w._beta_widgets["BETA"]


def test_beta_field_shows_the_model_default():
    w = _window()
    assert w._beta_widgets["BETA"].text() in ("0", "0.0")


def test_editing_beta_syncs_to_the_aircraft():
    w = _window()
    w._beta_widgets["BETA"].setText("5")
    main_window_mod.sync_fields_to_aircraft(w)
    assert w.aircraft.AERO["BETA"] == 5.0
    assert aero_beta(w.aircraft) == 5.0


def test_blank_beta_commits_zero_not_the_previous_value():
    w = _window(beta=5.0)
    assert w.aircraft.AERO["BETA"] == 5.0
    w._beta_widgets["BETA"].setText("")
    main_window_mod.sync_fields_to_aircraft(w)
    assert w.aircraft.AERO["BETA"] == 0.0


def test_populate_shows_the_model_value_again():
    w = _window(beta=5.0)
    main_window_mod.populate_from_aircraft(w, w.aircraft)
    assert w._beta_widgets["BETA"].text() in ("5", "5.0")


def test_run_tornado_hands_tornado_the_sideslip_in_radians(monkeypatch):
    w = _window()
    w._beta_widgets["BETA"].setText("5")
    seen: dict = {}
    real_io = tornado_io

    def spy(ac, mesh, *args, **kwargs):
        geo, state = real_io(ac, mesh, *args, **kwargs)
        seen["betha"] = state["betha"]
        raise _ReachedState

    monkeypatch.setattr(main_window_mod, "tornado_io", spy)
    with pytest.raises(_ReachedState):
        w.run_tornado(("10", "5"))
    assert seen["betha"] == pytest.approx(math.radians(5.0))


def test_run_flow5_forwards_beta(monkeypatch):
    w = _window()
    w._beta_widgets["BETA"].setText("5")
    seen: dict = {}
    fake = {"alpha": [-4.0, 0.0], "CL": [0.1, 0.2], "CD": [0.01, 0.02], "Cm": [0.0, -0.1]}
    monkeypatch.setattr(
        "aid_gui.main_window.run_flow5",
        lambda ac, mesh, **k: (seen.update(k), fake)[1],
    )
    w.run_flow5(("10", "10"))
    assert seen["beta"] == 5.0
    assert w.aircraft.AERO["BETA"] == 5.0


def test_datcom_and_avl_take_no_beta_argument():
    for name in ("run_datcom", "run_avl"):
        params = inspect.signature(getattr(MainWindow, name)).parameters
        assert "beta" not in params, name


def test_datcom_and_avl_labels_carry_beta_zero():
    series = overlay_vs_alpha(
        _results(),
        _st(),
        datcom="cl",
        tornado=("CL", "CL_a"),
        avl="CLtot",
        beta=5.0,
    )
    labels = {s["label"] for s in series}
    assert "DATCOM (beta=0)" in labels and "AVL (beta=0)" in labels
    assert "Tornado" in labels


def test_labels_are_untouched_at_beta_zero():
    series = overlay_vs_alpha(
        _results(),
        _st(),
        datcom="cl",
        tornado=("CL", "CL_a"),
        avl="CLtot",
        beta=0.0,
    )
    assert {s["label"] for s in series} == {"DATCOM", "Tornado", "AVL"}


def test_flow5_force_series_keeps_the_plain_label():
    series = overlay_vs_alpha(_results(), _st(), flow5="CL", beta=5.0)
    labels = [s["label"] for s in series]
    assert labels == ["flow5"]


def test_flow5_derivative_series_claims_beta_zero():
    series = overlay_derivative(_results(), _st(), flow5="CYb", beta=5.0)
    assert [s["label"] for s in series] == ["flow5 (beta=0)"]
    assert series[0]["kind"] == "hline"


def test_derivative_labels_split_solvers_by_who_flew_beta():
    series = overlay_derivative(
        _results(),
        _st(),
        datcom="cyb",
        tornado="CY_b",
        avl="CYb",
        flow5="CYb",
        beta=5.0,
    )
    labels = [s["label"] for s in series]
    assert "DATCOM (beta=0)" in labels
    assert "AVL (beta=0)" in labels
    assert "flow5 (beta=0)" in labels
    assert "Tornado" in labels, "Tornado's betha follows the field, so it needs no suffix"
    assert not any(label.endswith("(beta=0)") for label in labels if label == "Tornado")


def test_derivative_labels_are_untouched_at_beta_zero():
    series = overlay_derivative(
        _results(),
        _st(),
        datcom="cyb",
        tornado="CY_b",
        avl="CYb",
        flow5="CYb",
        beta=0.0,
    )
    assert [s["label"] for s in series] == [
        "DATCOM",
        "Tornado",
        "AVL",
        "flow5",
    ]


def _legend_labels(ax) -> list[str]:
    _handles, labels = ax.get_legend_handles_labels()
    return list(labels)


def _plotted(beta: float | None):
    """A window whose Aerodynamics panel has been drawn, so the labels are real."""
    w = _window(beta)
    w.last_results = _results()
    w.set_plot_mode("Aerodynamics")
    return w


def test_compare_tabs_force_panel_marks_the_solvers_that_ignored_beta():
    w = _plotted(beta=5.0)
    labels = _legend_labels(w.compare_tabs.figure("Forces").axes[0])
    assert "DATCOM (beta=0)" in labels
    assert "AVL (beta=0)" in labels
    assert "Tornado" in labels
    assert "flow5" in labels


def test_compare_tabs_derivative_panel_marks_flow5_too():
    w = _plotted(beta=5.0)
    labels = _legend_labels(w.compare_tabs.figure("Derivatives").axes[2])
    assert "DATCOM (beta=0)" in labels
    assert "flow5 (beta=0)" in labels
    assert "Tornado" in labels


def test_compare_tabs_defaults_to_no_suffix():
    w = _plotted(beta=None)
    labels = _legend_labels(w.compare_tabs.figure("Derivatives").axes[2])
    assert "flow5" in labels
    assert not any("(beta=0)" in label for label in labels)