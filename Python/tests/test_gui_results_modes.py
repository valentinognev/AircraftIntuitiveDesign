import json
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import numpy as np
import pytest
from matplotlib.colors import to_rgb
from PySide6.QtWidgets import QApplication

from aid.aircraft import load_jsonc
from aid.paths import models_dir, results_dir
from aid.stability import aircraft_stability
from aid_gui.main_window import MainWindow


def test_results_bar_shows_cessna_margin():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    w.load_aircraft(load_jsonc(models_dir() / "Cessna 172.jsonc"))
    text = w.results_bar.summary_text()
    assert "CG at 37% MAC" in text
    assert "13% stable" in text
    assert w.plot_mode() == "Geometry"


def test_plot_mode_stability_hides_3d():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    w.show()
    app.processEvents()
    w.load_aircraft(load_jsonc(models_dir() / "Cessna 172.jsonc"))
    w.set_plot_mode("Stability")
    app.processEvents()
    assert w.plot_mode() == "Stability"
    assert w.view3d.isHidden()
    assert not w.results_panel.isHidden()
    w.set_plot_mode("Aerodynamics")
    app.processEvents()
    assert not w.view3d.isHidden()
    w.set_plot_mode("Geometry")
    app.processEvents()
    assert not w.view3d.isHidden()


def test_stability_ylim_fits_coefficients():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    w.show()
    app.processEvents()
    w.load_aircraft(load_jsonc(models_dir() / "Cessna 172.jsonc"))
    w.set_plot_mode("Stability")
    app.processEvents()
    ax_cl, ax_cm = w.results_panel.figure.axes[:2]
    cl_lo, cl_hi = ax_cl.get_ylim()
    cm_lo, cm_hi = ax_cm.get_ylim()
    assert cl_lo == -0.5
    assert 2 <= cl_hi < 10
    assert -1 <= cm_lo <= -0.15
    assert 0.15 <= cm_hi <= 1


def test_aero_drag_ylim_is_weight_over_three():
    from aid.stability import aircraft_stability

    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    w.show()
    app.processEvents()
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    w.load_aircraft(ac)
    w.set_plot_mode("Aerodynamics")
    app.processEvents()
    ax = w.results_panel.figure.axes[0]
    lo, hi = ax.get_ylim()
    st = aircraft_stability(ac)
    assert lo == 0
    assert hi == pytest.approx(st["WT"] / 3)
    x0, x1 = ax.get_xlim()
    assert x1 > x0


def _line_y_at(ax, color, xq=0.0):
    target = to_rgb(color)
    for line in ax.lines:
        if not np.allclose(to_rgb(line.get_color()), target, atol=0.05):
            continue
        x = np.asarray(line.get_xdata(), dtype=float)
        y = np.asarray(line.get_ydata(), dtype=float)
        if x.size < 2:
            continue
        order = np.argsort(x)
        return float(np.interp(xq, x[order], y[order]))
    raise AssertionError(f"no {color!r} line on axes")


def _cyan_line_y_at_zero(ax):
    return _line_y_at(ax, "c")


def test_cessna_gui_tornado_matches_aid_quarter_mac_trim():
    """AID.m Analyze Tornado: handbook trim alpha, moments about 25% MAC."""
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    w.load_aircraft(load_jsonc(models_dir() / "Cessna 172.jsonc"))
    w.run_tornado(mesh=("10", "5"))
    t = w.last_results["tornado"]
    assert t["CL"] == pytest.approx(0.168, abs=0.03)
    assert abs(t["Cm_a"]) < 3.0
    assert "CL0" in t and t["CL0"] == pytest.approx(0.169, abs=0.03)


def test_tornado_plot_intercept_uses_run_alpha_not_handbook():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    w.load_aircraft(ac)
    w.last_results["tornado"] = {
        "CL": 0.502,
        "CL_a": 5.148,
        "Cm": -0.822,
        "Cm_a": -1.819,
        "alpha": float(np.deg2rad(4.0)),
    }
    w.set_plot_mode("Stability")
    app.processEvents()
    y0 = _cyan_line_y_at_zero(w.results_panel.figure.axes[0])
    expected = 0.502 - 5.148 * np.deg2rad(4.0)
    assert y0 == pytest.approx(expected, abs=0.02)


def test_cessna_stability_overlay_intercepts_match_matlab_formulas():
    """Injected batch-gold DATCOM/AVL; Tornado uses AID.m intercepts."""
    app = QApplication.instance() or QApplication([])
    gold = results_dir() / "matlab" / "Cessna 172"
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    st = aircraft_stability(ac)
    w = MainWindow()
    w.load_aircraft(ac)
    w.run_tornado(mesh=("10", "5"))
    w.last_results["datcom"] = json.loads((gold / "datcom.json").read_text())
    w.last_results["avl"] = json.loads((gold / "avl.json").read_text())
    w.set_plot_mode("Stability")
    app.processEvents()
    ax_cl = w.results_panel.figure.axes[0]
    assert _line_y_at(ax_cl, "b") == pytest.approx(st["CL0"], abs=0.01)
    assert _line_y_at(ax_cl, "g") == pytest.approx(0.131, abs=0.01)
    assert _line_y_at(ax_cl, "c") == pytest.approx(0.169, abs=0.03)
    ax_cm = w.results_panel.figure.axes[1]
    assert _line_y_at(ax_cm, "g", 0.0) == pytest.approx(0.0472, abs=1e-4)
    assert _line_y_at(ax_cm, "g", 10.0) == pytest.approx(-0.1115, abs=1e-3)
    assert _line_y_at(ax_cm, "g", 12.0) == pytest.approx(-0.1558, abs=1e-4)
    assert _line_y_at(ax_cm, "b", 12.0) == pytest.approx(-0.1237, abs=0.01)
    assert w.results_panel.figure.axes[1].get_legend() is not None
