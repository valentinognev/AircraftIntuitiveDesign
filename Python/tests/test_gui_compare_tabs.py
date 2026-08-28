import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("PYVISTA_OFF_SCREEN", "true")
import numpy as np
from PySide6.QtWidgets import QApplication

from aid.aircraft import load_jsonc
from aid.datcom_parse import parse_for006
from aid.paths import models_dir
from aid_gui.main_window import MainWindow
from tests.test_datcom_parse_tables import _FOR006

_TABS = (
    "Forces",
    "Moments",
    "Derivatives",
    "Downwash",
    "Controls",
    "Spanwise",
    "Sections",
)


def test_aerodynamics_shows_compare_tabs():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    w.show()
    w.load_aircraft(load_jsonc(models_dir() / "Cessna 172.jsonc"))
    w.set_plot_mode("Aerodynamics")
    app.processEvents()
    assert not w.compare_tabs.isHidden()
    names = [w.compare_tabs.tabText(i) for i in range(w.compare_tabs.count())]
    assert names == list(_TABS)
    w.set_plot_mode("Stability")
    app.processEvents()
    assert w.compare_tabs.isHidden()
    w.set_plot_mode("Geometry")
    app.processEvents()
    assert w.compare_tabs.isHidden()


def test_forces_tab_plots_datcom_when_analyzed():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    w.show()
    w.load_aircraft(load_jsonc(models_dir() / "Cessna 172.jsonc"))
    w.last_results["datcom"] = parse_for006(_FOR006)
    w.set_plot_mode("Aerodynamics")
    app.processEvents()
    fig = w.compare_tabs.figure("Forces")
    ax_cl = fig.axes[0]
    labels = [ln.get_label() for ln in ax_cl.get_lines()]
    assert "DATCOM" in labels


def test_forces_axes_fill_tab_canvas():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    w.show()
    w.resize(960, 700)
    w.load_aircraft(load_jsonc(models_dir() / "Cessna 172.jsonc"))
    w.last_results["datcom"] = parse_for006(_FOR006)
    w.set_plot_mode("Aerodynamics")
    w.compare_tabs.setCurrentIndex(0)
    app.processEvents()
    canvas = w.compare_tabs.currentWidget()
    canvas.resize(720, 360)
    app.processEvents()
    boxes = [ax.get_position() for ax in w.compare_tabs.figure("Forces").axes]
    xmin = min(b.x0 for b in boxes)
    xmax = max(b.x1 for b in boxes)
    ymin = min(b.y0 for b in boxes)
    ymax = max(b.y1 for b in boxes)
    assert xmax - xmin > 0.86
    assert ymax - ymin > 0.80
    assert xmin < 0.10
    assert xmax > 0.95


def _axis_has_data(ax) -> bool:
    if ax.lines or ax.patches or ax.tables or ax.collections:
        return True
    return False


def _tornado_sample() -> dict:
    return {
        "alpha": float(np.deg2rad(4.0)),
        "CL": 0.50,
        "CL_a": 5.0,
        "CD": 0.03,
        "CD_a": 0.1,
        "CY": 0.0,
        "CY_a": 0.0,
        "CZ": -0.50,
        "CZ_a": -5.0,
        "CX": 0.02,
        "CX_a": 0.1,
        "CC": 0.001,
        "Cm": -0.05,
        "Cm_a": -1.0,
        "Cl": 0.0,
        "Cl_a": 0.0,
        "Cn": 0.0,
        "Cn_a": 0.0,
        "CY_b": -0.4,
        "Cn_b": 0.08,
        "Cl_b": -0.05,
        "Cl_P": -0.4,
        "Cm_Q": -8.0,
        "Cn_R": -0.1,
        "CL_P": 0.0,
        "CL_Q": 4.0,
        "CL_R": 0.0,
        "CLwing": np.array([0.45, 0.08]),
        "CDwing": np.array([0.02, 0.005]),
        "CYwing": np.array([0.0, 0.01]),
        "CL_d": np.array([0.01, -0.02, 0.0]),
        "Cm_d": np.array([0.0, -0.03, 0.0]),
        "CD_d": np.array([0.001, 0.0, 0.0]),
        "spanwise": [{"y": np.linspace(0.0, 6.0, 5), "Cl": np.linspace(0.3, 0.1, 5)}],
    }


def _avl_sample() -> dict:
    return {
        "alpha": 4.0,
        "CLtot": 0.51,
        "CDtot": 0.025,
        "CYtot": 0.0,
        "CZtot": -0.51,
        "CXtot": 0.01,
        "Cltot": 0.0,
        "Cmtot": -0.05,
        "Cntot": 0.0,
        "CLa": 5.2,
        "Cma": -1.2,
        "CYa": -0.01,
        "CYb": -0.4,
        "Cnb": 0.08,
        "Clb": -0.05,
        "Cla": 0.0,
        "Cna": 0.01,
        "Clp": -0.5,
        "Cmq": -9.0,
        "Cnr": -0.12,
        "CLp": 0.0,
        "CLq": 4.1,
        "CLr": 0.0,
        "CDind": 0.02,
        "CDvis": 0.005,
        "CDff": 0.018,
        "e": 0.8,
        "NP": 3.5,
        "surface": [{"name": "elevator", "angle": 0.0}, {"name": "flap", "angle": 0.0}],
    }


def test_controls_plots_datcom_high_lift():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    w.show()
    w.load_aircraft(load_jsonc(models_dir() / "Cessna 172.jsonc"))
    w.last_results["datcom"] = parse_for006(_FOR006)
    w.set_plot_mode("Aerodynamics")
    app.processEvents()
    fig = w.compare_tabs.figure("Controls")
    assert fig.axes[0].patches
    assert fig.axes[1].lines
    _, labs = fig.axes[0].get_legend_handles_labels()
    assert any("DATCOM" in str(lab) for lab in labs)
    assert fig.axes[2].patches


def test_all_solver_outputs_appear_on_compare_tabs():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    w.show()
    w.load_aircraft(load_jsonc(models_dir() / "Cessna 172.jsonc"))
    w.last_results["datcom"] = parse_for006(_FOR006)
    w.last_results["tornado"] = _tornado_sample()
    w.last_results["avl"] = _avl_sample()
    w.set_plot_mode("Aerodynamics")
    app.processEvents()
    empty = []
    for name in _TABS:
        for i, ax in enumerate(w.compare_tabs.figure(name).axes):
            if not _axis_has_data(ax):
                empty.append(f"{name}[{i}] {ax.get_title() or ax.get_ylabel()}")
    assert empty == [], empty
    forces = w.compare_tabs.figure("Forces")
    assert any("Tornado" in ln.get_label() for ln in forces.axes[2].get_lines())
    assert any("Tornado" in ln.get_label() for ln in forces.axes[3].get_lines())
    moments = w.compare_tabs.figure("Moments")
    assert any("Tornado" in ln.get_label() for ln in moments.axes[1].get_lines())
    assert any("Tornado" in ln.get_label() for ln in moments.axes[2].get_lines())
    controls = w.compare_tabs.figure("Controls")
    clabels = [ln.get_label() for ln in controls.axes[0].get_lines()] + [
        p.get_label() for p in controls.axes[0].patches
    ]
    assert any("CL_d" in str(lab) or "Tornado" in str(lab) for lab in clabels)
    assert any("Cm_d" in str(lab) for lab in clabels)
    section_text = " ".join(
        cell.get_text().get_text()
        for ax in w.compare_tabs.figure("Sections").axes
        for table in ax.tables
        for cell in table.get_celld().values()
    )
    assert "CDwing" in section_text
    assert "CYa" in section_text


def test_derivative_cyb_uses_full_alpha_range():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    w.show()
    w.load_aircraft(load_jsonc(models_dir() / "Cessna 172.jsonc"))
    w.last_results["datcom"] = parse_for006(_FOR006)
    w.set_plot_mode("Aerodynamics")
    w.compare_tabs.setCurrentIndex(2)
    app.processEvents()
    ax_cyb = w.compare_tabs.figure("Derivatives").axes[2]
    x0, x1 = ax_cyb.get_xlim()
    assert x1 - x0 >= 14.0
    assert ax_cyb.yaxis.label.get_fontsize() >= 10
    assert ax_cyb.xaxis.get_ticklabels()[0].get_fontsize() >= 8


def test_cessna_all_solvers_fill_compare_axes():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    w.load_aircraft(load_jsonc(models_dir() / "Cessna 172.jsonc"))
    w.run_datcom()
    w.run_tornado(mesh=("10", "5"))
    w.run_avl(mesh=("10", "10"))
    w.set_plot_mode("Aerodynamics")
    app.processEvents()
    empty = []
    for name in _TABS:
        for i, ax in enumerate(w.compare_tabs.figure(name).axes):
            if not _axis_has_data(ax):
                empty.append(f"{name}[{i}] {ax.get_title() or ax.get_ylabel()}")
    assert empty == [], empty
    assert w.last_results["datcom"].get("high_lift")
