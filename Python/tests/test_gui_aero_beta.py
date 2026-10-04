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
import warnings

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np
import pytest
from PySide6.QtWidgets import QApplication

from aid.aircraft import aero_beta, load_jsonc
from aid.paths import models_dir
from aid.solver_overlay import (
    BETA_CAPABLE_CONTROL_SOLVERS,
    FLOW5_BETA_FLAT,
    Flow5BetaFlatGap,
    control_probe_label,
    flow5_emitted_stab_derivatives,
    overlay_derivative,
    overlay_vs_alpha,
)
from aid.tornado_io import tornado_io
from aid_gui import main_window as main_window_mod
from aid_gui.main_window import MainWindow
from aid import solver_overlay as solver_overlay_mod
from aid_gui.results_panel import ResultsPanel


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
            "cma": np.array([-0.78, -0.80, -0.83]),
            "cyb": np.array([-0.012, -0.012, -0.011]),
        },
        "tornado": {
            "alpha": float(np.deg2rad(4.0)),
            "CL": 0.50,
            "CL_a": 5.0,
            "Cm_a": -0.80,
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
            "CLa": 5.5,
            "Cma": -1.58,
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
    # Exact parameter lists, not just "beta" not in params: a **kwargs would let a
    # beta reach these two invisibly, and the whole point is that they cannot.
    expected = {"run_datcom": ["self"], "run_avl": ["self", "mesh"]}
    for name, names in expected.items():
        params = inspect.signature(getattr(MainWindow, name)).parameters
        assert list(params) == names, name
        assert all(
            p.kind is not inspect.Parameter.VAR_KEYWORD for p in params.values()
        ), name


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


def test_overlay_vs_alpha_skips_flow5_without_an_alpha_key():
    """A result set with no alpha vector is skipped, exactly like DATCOM and AVL.

    The per-point channel exists but there is nothing to plot it against, and
    reading fres["alpha"] unguarded raises KeyError.
    """
    res = {"flow5": {"CL": np.array([0.1, 0.2])}}
    assert overlay_vs_alpha(res, _st(), flow5="CL", beta=5.0) == []


def test_every_stab_derivative_flow5_emits_is_marked_beta_flat():
    """The set cannot drift from the C++: this compares against the parsed source."""
    emitted = flow5_emitted_stab_derivatives()
    assert len(emitted) == 12, "flow5_run.cpp's derivative literals were not found"
    assert emitted == FLOW5_BETA_FLAT


def test_a_stab_derivative_missing_from_the_set_is_loud(monkeypatch):
    """A 13th derivative must not plot as if it flew the flight condition."""
    monkeypatch.setattr(
        solver_overlay_mod,
        "flow5_emitted_stab_derivatives",
        lambda: frozenset(FLOW5_BETA_FLAT | {"Cmq"}),
    )
    with pytest.warns(Flow5BetaFlatGap, match="Cmq"):
        series = overlay_derivative({"flow5": {"Cmq": -1.5}}, _st(), flow5="Cmq", beta=5.0)
    assert [s["label"] for s in series] == ["flow5"]


def test_an_unknown_non_derivative_channel_stays_silent(monkeypatch):
    monkeypatch.setattr(
        solver_overlay_mod,
        "flow5_emitted_stab_derivatives",
        lambda: frozenset(FLOW5_BETA_FLAT),
    )
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        for key in ("CLa", "Cma", "CLq", "Cm_d"):
            series = overlay_derivative({"flow5": {key: 1.0}}, _st(), flow5=key, beta=5.0)
            assert [s["label"] for s in series] == ["flow5"], key


@pytest.mark.parametrize("key", sorted(FLOW5_BETA_FLAT))
def test_flow5_stab_derivatives_claim_beta_zero(key):
    res = {"flow5": {key: 0.5, "CLa": 5.0}}
    series = overlay_derivative(res, _st(), flow5=key, beta=5.0)
    assert [s["label"] for s in series] == [f"flow5 (beta=0)"]
    assert series[0]["kind"] == "hline", key


@pytest.mark.parametrize("key", ["CLa", "Cma"])
def test_flow5_polar_slopes_stay_unmarked(key):
    """R30: CLa/Cma are OLS slopes over the polar, so they move with beta.

    Measured on Cessna 172: CLa = 5.5402333786223235 at beta 0, 5.500374829746751
    at +5, 5.500374817599451 at -5. Marking these "(beta=0)" is a false claim.
    """
    res = {"flow5": {key: 5.5}}
    series = overlay_derivative(res, _st(), flow5=key, beta=5.0)
    assert [s["label"] for s in series] == ["flow5"]
    assert series[0]["kind"] == "hline", key


def test_flow5_beta_flat_set_is_the_twelve_stab_derivatives():
    assert FLOW5_BETA_FLAT == frozenset(
        {
            "CXa", "CZa", "CYb", "CYp", "CYr",
            "Clb", "Clp", "Clr", "Cnb", "Cnp", "Cnr",
            "XNP",
        }
    )
    # Everything the Forces panel hands overlay_vs_alpha as a flow5 key, plus the
    # two OLS slopes and the per-point arrays, is a polar channel and is absent.
    assert not FLOW5_BETA_FLAT & {
        "CL", "CD", "Cm", "Cl", "Cn", "CY",   # per-point polar forces/moments
        "Cx", "Cz",                          # the other two per-point polar arrays
        "beta",                              # the polar's own beta vector
        "CLa", "Cma",                        # OLS slopes, which do move with beta
    }


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


def _line_labels(ax) -> list[str]:
    return [line.get_label() for line in ax.get_lines()]


def _bar_labels(ax) -> list[str]:
    return [patch.get_label() for patch in ax.patches]


def _rich_results() -> dict:
    """Enough solver output to light up every panel that prints a solver name."""
    res = _results()
    res["datcom"].update(
        {
            "xcp": [4.1, 4.2, 4.3],
            "epslon": [1.0, 1.1, 1.2],
            "Cl_P": -0.05,
            "Cm_Q": -3.1,
            "Cn_R": -0.11,
            "CL_P": -0.02,
            "CL_Q": -4.0,
            "CL_R": 0.08,
            "high_lift": [
                {
                    "delta": 10.0,
                    "config": "F 10",
                    "dcl": 0.31,
                    "dcm": -0.02,
                    "cha": 0.11,
                    "chd": 0.22,
                    "dcl_max": 1.51,
                    "dcdi_alpha": [-4.0, 0.0, 4.0],
                    "dcdi": [0.02, 0.03, 0.05],
                }
            ],
        }
    )
    res["tornado"].update(
        {
            "CLwing": [0.4, 0.1, 0.05],
            "CDwing": [0.01, 0.005],
            "CYwing": [0.0, 0.01],
            "CC": [0.02],
            "Cl_P": -0.05,
            "Cm_Q": -3.2,
            "Cn_R": -0.10,
            "CL_P": -0.02,
            "CL_Q": -3.9,
            "CL_R": 0.09,
        }
    )
    res["avl"].update(
        {
            "CDind": 0.02,
            "CDvis": 0.01,
            "e": 0.78,
            "NP": 1.1,
            "Clp": -0.05,
            "Cmq": -3.0,
            "Cnr": -0.10,
            "CLp": -0.02,
            "CLq": -3.8,
            "CLr": 0.07,
            "CYa": 0.012,
            "surface": [{"name": "F", "angle": 10.0}],
        }
    )
    res["control_derivatives"] = {
        "solver": "avl",
        "rows": [
            {"available": True, "surface": "F", "delta_deg": d, "CY": 0.01 * d}
            for d in (-5.0, 0.0, 10.0)
        ],
    }
    return res


def _plotted(beta: float | None, results: dict | None = None):
    """A window whose Aerodynamics panel has been drawn, so the labels are real."""
    w = _window(beta)
    w.last_results = _rich_results() if results is None else results
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


def test_compare_tabs_polar_slope_panels_do_not_mark_flow5():
    """R30, end to end: C_La and C_m_alpha plot flow5's OLS slopes, not a StabDerivative."""
    w = _plotted(beta=5.0)
    fig = w.compare_tabs.figure("Derivatives")
    # Only the first panel carries a legend; read the line labels, which cover
    # axhline's hline series too.
    for ax, marked in ((fig.axes[0], False), (fig.axes[1], False), (fig.axes[2], True)):
        labels = _line_labels(ax)
        assert ("flow5 (beta=0)" in labels) is marked, ax.get_ylabel()
        assert "DATCOM (beta=0)" in labels, ax.get_ylabel()
        assert "Tornado" in labels, ax.get_ylabel()


def test_moments_xcp_series_is_marked():
    """The X_CP sub-axes has no legend, so read the line label, not the legend."""
    w = _plotted(beta=5.0)
    assert _line_labels(w.compare_tabs.figure("Moments").axes[3]) == ["DATCOM (beta=0)"]


def test_moments_xcp_series_is_unmarked_at_beta_zero():
    w = _plotted(beta=None)
    assert _line_labels(w.compare_tabs.figure("Moments").axes[3]) == ["DATCOM"]


def test_force_extras_avl_bars_are_marked_next_to_tornado():
    """The Forces tab prints AVL in _plot_force_extras as well as in the overlays."""
    w = _plotted(beta=5.0)
    labels = _legend_labels(w.compare_tabs.figure("Forces").axes[5])
    assert "AVL (beta=0)" in labels
    assert "Tornado" in labels


def test_rate_bar_avl_bars_are_marked():
    w = _plotted(beta=5.0)
    labels = _legend_labels(w.compare_tabs.figure("Derivatives").axes[5])
    assert "AVL (beta=0)" in labels
    assert "Tornado" in labels


def test_downwash_datcom_line_is_marked():
    w = _plotted(beta=5.0)
    assert "DATCOM (beta=0)" in _legend_labels(w.compare_tabs.figure("Downwash").axes[0])


def test_controls_datcom_bars_are_marked():
    w = _plotted(beta=5.0)
    fig = w.compare_tabs.figure("Controls")
    labels = _legend_labels(fig.axes[0]) + _legend_labels(fig.axes[1])
    assert r"DATCOM $\Delta C_L$ (beta=0)" in labels
    assert r"DATCOM $\Delta C_m$ (beta=0)" in labels
    assert any(lab.startswith("DATCOM ΔCDi δ=10.0 (beta=0)") for lab in labels)


def test_sections_leftover_group_headers_are_marked():
    w = _plotted(beta=5.0)
    headers = [
        w.compare_tabs.leftover_table.item(row, 0).text()
        for row in range(w.compare_tabs.leftover_table.rowCount())
    ]
    assert "DATCOM high-lift (beta=0)" in headers
    assert "AVL (beta=0)" in headers
    assert "Tornado" in headers


def test_control_probe_curves_follow_the_solver_not_the_panel():
    # avl has no sideslip capability, tornado and flow5 probe at the model's beta.
    assert control_probe_label("avl", "F", "CY", 5.0) == "avl F CY (beta=0)"
    assert control_probe_label("handbook", "F", "CY", 5.0) == "handbook F CY (beta=0)"
    assert control_probe_label("tornado", "F", "CY", 5.0) == "tornado F CY"
    assert control_probe_label("flow5", "F", "CY", 5.0) == "flow5 F CY"
    assert BETA_CAPABLE_CONTROL_SOLVERS == frozenset({"tornado", "flow5"})
    for solver in ("avl", "handbook", "tornado", "flow5"):
        assert control_probe_label(solver, "F", "CY", 0.0) == f"{solver} F CY"


def test_compare_tabs_defaults_to_no_suffix():
    w = _plotted(beta=None)
    labels = _legend_labels(w.compare_tabs.figure("Derivatives").axes[2])
    assert "flow5" in labels
    assert not any("(beta=0)" in label for label in labels)


# --- the CL / C_m results panel (aid_gui.results_panel) ------------------------
# The panel users see first. Every series on it is vs-alpha, so the split is the
# vs-alpha one: DATCOM and AVL cannot fly a sideslip at all, while flow5's CL and
# Cm come straight off its polar and did move with beta.


def _panel_results() -> dict:
    """One vs-alpha series per solver, on both the CL and the C_m sub-axes."""
    return {
        "datcom": {
            "alpha": [-4.0, 0.0, 4.0],
            "cl": [-0.2, 0.13, 0.52],
            "cm": [0.05, 0.02, -0.06],
        },
        "avl": {
            "alpha": [-4.0, 0.0, 4.0],
            "CLtot": [0.10, 0.30, 0.51],
            "Cmtot": [0.04, 0.01, -0.07],
        },
        "flow5": {
            "alpha": np.array([-4.0, 0.0, 4.0]),
            "CL": np.array([-0.1, 0.2, 0.5]),
            "Cm": np.array([0.03, 0.0, -0.08]),
        },
        "tornado": {
            "alpha": float(np.deg2rad(4.0)),
            "CL": 0.50,
            "CL_a": 5.0,
            "Cm": -0.80,
            "Cm_a": -0.80,
        },
    }


def _panel(beta: float):
    app = QApplication.instance() or QApplication([])
    del app
    panel = ResultsPanel()
    panel.plot_stability(_st(), _panel_results(), beta=beta)
    return panel


def test_results_panel_marks_datcom_and_avl_at_beta():
    panel = _panel(5.0)
    for ax in panel.figure.axes[:2]:
        labels = _legend_labels(ax)
        assert "DATCOM (beta=0)" in labels, ax.get_ylabel()
        assert "AVL (beta=0)" in labels, ax.get_ylabel()


def test_results_panel_leaves_flow5_and_tornado_unmarked_at_beta():
    """flow5's polar forces and Tornado's betha both follow the field."""
    panel = _panel(5.0)
    for ax in panel.figure.axes[:2]:
        labels = _legend_labels(ax)
        assert "flow5" in labels, ax.get_ylabel()
        assert "Tornado" in labels, ax.get_ylabel()
        assert not any(
            lab.startswith(("flow5 (", "Tornado (")) for lab in labels
        ), labels


def test_results_panel_labels_are_byte_identical_at_beta_zero():
    panel = _panel(0.0)
    for ax in panel.figure.axes[:2]:
        assert _legend_labels(ax) == [
            "Cruise",
            "Approximated",
            "DATCOM",
            "Tornado",
            "AVL",
            "flow5",
        ], ax.get_ylabel()


def test_results_panel_defaults_to_no_suffix():
    app = QApplication.instance() or QApplication([])
    del app
    panel = ResultsPanel()
    panel.plot_stability(_st(), _panel_results())
    assert "DATCOM" in _legend_labels(panel.figure.axes[0])


def test_stability_panel_follows_the_model_beta():
    """The panel must be handed the model's sideslip, not default to zero."""
    w = _window(beta=5.0)
    w.last_results = _panel_results()
    w.set_plot_mode("Stability")
    ax_cl, ax_cm = w.results_panel.figure.axes[:2]
    for ax in (ax_cl, ax_cm):
        labels = _legend_labels(ax)
        assert "DATCOM (beta=0)" in labels, ax.get_ylabel()
        assert "AVL (beta=0)" in labels, ax.get_ylabel()
        assert "flow5" in labels, ax.get_ylabel()


def test_stability_panel_is_unmarked_without_a_sideslip():
    w = _window(beta=None)
    w.last_results = _panel_results()
    w.set_plot_mode("Stability")
    for ax in w.results_panel.figure.axes[:2]:
        assert "DATCOM" in _legend_labels(ax), ax.get_ylabel()