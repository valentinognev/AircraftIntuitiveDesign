import inspect
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np
from PySide6.QtWidgets import QApplication

from aid_gui.compare_tabs import CompareTabs
from aid_gui.results_panel import ResultsPanel


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


def _flow5_results() -> dict:
    return {
        "flow5": {
            "alpha": np.array([0.0, 4.0]),
            "CL": np.array([0.2, 0.5]),
            "CD": np.array([0.01, 0.02]),
            "Cm": np.array([0.0, -0.1]),
            "CLa": 5.0,
            "Cma": -1.0,
            # Lateral half: per-point Cl/Cn plus the twelve single-point
            # stability scalars, all already Forward-Right-Down except the two
            # moment channels, which Task 2.3's flow5 map mirrors.
            "Cl": np.array([0.001, -0.02]),
            "Cn": np.array([-0.002, 0.03]),
            "CYb": -0.4107,
            "Cnb": 0.1685,
            "Clb": -0.053,
        }
    }


def _labels(fig, index: int) -> list[str]:
    return [line.get_label() for line in fig.axes[index].get_lines()]


def test_compare_tabs_moments_panels_carry_flow5():
    # _plot_moments gains Cltot -> flow5 "Cl" and Cntot -> flow5 "Cn"; axes are
    # Cm, Cl, Cn in declaration order.
    app = QApplication.instance() or QApplication([])
    tabs = CompareTabs()
    tabs.plot(_st(), _flow5_results())
    fig = tabs.figure("Moments")
    for index in (1, 2):
        assert "flow5" in _labels(fig, index), index


def test_compare_tabs_beta_derivative_panels_carry_flow5():
    # _plot_derivatives gains CYb, Cnb and Clb; axes are CLa, Cm_a, CYb, Cnb, Clb.
    # flow5's scalars are per radian, and overlay_derivative already rescales every
    # solver's derivative to per degree, so no panel-side unit work is needed.
    app = QApplication.instance() or QApplication([])
    tabs = CompareTabs()
    tabs.plot(_st(), _flow5_results())
    fig = tabs.figure("Derivatives")
    for index in (2, 3, 4):
        assert "flow5" in _labels(fig, index), index


def test_compare_tabs_plot_flow5():
    app = QApplication.instance() or QApplication([])
    tabs = CompareTabs()
    tabs.plot(_st(), _flow5_results())


def test_compare_tabs_source_passes_flow5():
    for method in ("_plot_forces", "_plot_moments", "_plot_derivatives"):
        src = inspect.getsource(getattr(CompareTabs, method))
        assert "flow5" in src, f"{method} must pass flow5= to overlay helpers"


def test_compare_tabs_forces_cl_has_flow5_series():
    app = QApplication.instance() or QApplication([])
    tabs = CompareTabs()
    tabs.plot(_st(), _flow5_results())
    fig = tabs.figure("Forces")
    ax = fig.axes[0]
    labels = [line.get_label() for line in ax.get_lines()]
    assert "flow5" in labels


def test_style_color_supports_yellow():
    from aid_gui.compare_tabs import _STYLE_COLOR

    assert _STYLE_COLOR.get("y") == "y"


def test_results_panel_plot_stability_flow5():
    app = QApplication.instance() or QApplication([])
    panel = ResultsPanel()
    panel.plot_stability(_st(), _flow5_results())
    ax_cl = panel._figure.axes[0]
    ax_cm = panel._figure.axes[1]
    cl_labels = [line.get_label() for line in ax_cl.get_lines()]
    cm_labels = [line.get_label() for line in ax_cm.get_lines()]
    assert "flow5" in cl_labels
    assert "flow5" in cm_labels
