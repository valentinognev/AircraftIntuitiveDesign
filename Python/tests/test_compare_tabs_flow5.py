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
        }
    }


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
