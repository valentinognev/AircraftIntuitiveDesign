import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("PYVISTA_OFF_SCREEN", "true")
import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QTableWidget

from aid.aircraft import load_jsonc
from aid.axes import to_frd
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
    w.last_results["datcom"] = to_frd("datcom", parse_for006(_FOR006))
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
    w.last_results["datcom"] = to_frd("datcom", parse_for006(_FOR006))
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


def _table_text(table: QTableWidget) -> str:
    parts = []
    for r in range(table.rowCount()):
        for c in range(table.columnCount()):
            item = table.item(r, c)
            if item is not None and item.text():
                parts.append(item.text())
    for c in range(table.columnCount()):
        header = table.horizontalHeaderItem(c)
        if header is not None and header.text():
            parts.append(header.text())
    return " ".join(parts)


def _leftover_map(table: QTableWidget) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for r in range(table.rowCount()):
        if table.columnSpan(r, 0) > 1:
            continue
        qty = table.item(r, 0)
        if qty is None or not qty.text():
            continue
        vals = []
        for c in range(1, table.columnCount()):
            item = table.item(r, c)
            vals.append("" if item is None else item.text())
        out[qty.text()] = vals
    return out


def _group_headers(table: QTableWidget) -> list[str]:
    names = []
    for r in range(table.rowCount()):
        if table.columnSpan(r, 0) > 1:
            item = table.item(r, 0)
            if item is not None:
                names.append(item.text())
    return names


def _sections_have_data(tabs) -> bool:
    return tabs.leftover_table.rowCount() > 0 or tabs.section_defs_table.rowCount() > 0


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
    w.last_results["datcom"] = to_frd("datcom", parse_for006(_FOR006))
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
    w.last_results["datcom"] = to_frd("datcom", parse_for006(_FOR006))
    w.last_results["tornado"] = _tornado_sample()
    w.last_results["avl"] = _avl_sample()
    w.set_plot_mode("Aerodynamics")
    app.processEvents()
    empty = []
    for name in _TABS:
        if name == "Sections":
            if not _sections_have_data(w.compare_tabs):
                empty.append("Sections")
            continue
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
    leftover = _leftover_map(w.compare_tabs.leftover_table)
    assert "CDwing" in leftover
    assert "CYa" in leftover
    defs = _table_text(w.compare_tabs.section_defs_table)
    assert "Wing" in defs
    assert "alpha_ideal" in defs


def test_derivative_cyb_uses_full_alpha_range():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    w.show()
    w.load_aircraft(load_jsonc(models_dir() / "Cessna 172.jsonc"))
    w.last_results["datcom"] = to_frd("datcom", parse_for006(_FOR006))
    w.set_plot_mode("Aerodynamics")
    w.compare_tabs.setCurrentIndex(2)
    app.processEvents()
    ax_cyb = w.compare_tabs.figure("Derivatives").axes[2]
    x0, x1 = ax_cyb.get_xlim()
    assert x1 - x0 >= 14.0
    assert ax_cyb.yaxis.label.get_fontsize() >= 10
    assert ax_cyb.xaxis.get_ticklabels()[0].get_fontsize() >= 8


def test_spanwise_legend_names_tornado_surfaces():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    w.show()
    w.load_aircraft(load_jsonc(models_dir() / "Cessna 172.jsonc"))
    y = np.linspace(-5.0, 5.0, 5)
    w.last_results["tornado"] = {
        "spanwise": [
            {"y": y, "Cl": np.full(5, 0.3), "name": "Wing"},
            {"y": y * 0.4, "Cl": np.full(5, 0.04), "name": "HT"},
            {"y": y * 0.3, "Cl": np.zeros(5), "name": "VT"},
            {"y": y * 0.8, "Cl": np.full(5, 0.02), "name": "Wing 2"},
        ]
    }
    w.set_plot_mode("Aerodynamics")
    app.processEvents()
    ax = w.compare_tabs.figure("Spanwise").axes[0]
    lines = {ln.get_label(): ln for ln in ax.get_lines()}
    assert "Prandtl" in lines
    for name in ("Tornado Wing", "Tornado HT", "Tornado VT", "Tornado Wing 2"):
        assert name in lines
    tornado = [lines[n] for n in ("Tornado Wing", "Tornado HT", "Tornado VT", "Tornado Wing 2")]
    styles = [ln.get_linestyle() for ln in tornado]
    widths = [ln.get_linewidth() for ln in tornado]
    assert len(set(styles)) == 4
    assert len(set(widths)) == 4


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
        if name == "Sections":
            if not _sections_have_data(w.compare_tabs):
                empty.append("Sections")
            continue
        for i, ax in enumerate(w.compare_tabs.figure(name).axes):
            if not _axis_has_data(ax):
                empty.append(f"{name}[{i}] {ax.get_title() or ax.get_ylabel()}")
    assert empty == [], empty
    assert w.last_results["datcom"].get("high_lift")


def test_sections_leftover_splits_vectors_into_columns():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    w.show()
    w.load_aircraft(load_jsonc(models_dir() / "Cessna 172.jsonc"))
    w.last_results["tornado"] = _tornado_sample()
    w.set_plot_mode("Aerodynamics")
    app.processEvents()
    table = w.compare_tabs.leftover_table
    assert isinstance(table, QTableWidget)
    leftover = _leftover_map(table)
    assert leftover["CDwing"][0] == "0.02"
    assert leftover["CDwing"][1] == "0.005"
    assert leftover["CYwing"][0] == "0"
    assert leftover["CYwing"][1] == "0.01"


def test_sections_leftover_groups_by_solver():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    w.show()
    w.load_aircraft(load_jsonc(models_dir() / "Cessna 172.jsonc"))
    w.last_results["tornado"] = _tornado_sample()
    w.last_results["avl"] = _avl_sample()
    w.set_plot_mode("Aerodynamics")
    app.processEvents()
    table = w.compare_tabs.leftover_table
    assert _group_headers(table) == ["Tornado", "AVL"]
    leftover = _leftover_map(table)
    assert "CDwing" in leftover
    assert "CYa" in leftover
    assert all(not key.startswith("Tornado ") for key in leftover)


def test_sections_leftover_keeps_avl_rate_derivatives():
    """A short AVL sweep must still list its rate derivatives as leftovers.

    ``_leftover_groups`` only ever walks the Tornado and AVL result dicts, so a
    key in ``_SKIP_LEFTOVER`` that belongs to some *other* solver hides nothing --
    but the same key spelled the way AVL spells it hides exactly this. Whether
    these four belong in the table at all is a product question; hiding them is
    not an answer to it.
    """
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    w.show()
    w.load_aircraft(load_jsonc(models_dir() / "Cessna 172.jsonc"))
    avl = _avl_sample()
    avl.update({"CYp": -0.18, "CYr": 0.43, "Clr": 0.01, "Cnp": -0.06})
    w.last_results["avl"] = avl
    w.set_plot_mode("Aerodynamics")
    app.processEvents()
    leftover = _leftover_map(w.compare_tabs.leftover_table)
    for key in ("CYp", "CYr", "Clr", "Cnp"):
        assert key in leftover, key


def test_sections_leftover_zeroes_tiny_values():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    w.show()
    w.load_aircraft(load_jsonc(models_dir() / "Cessna 172.jsonc"))
    sample = _tornado_sample()
    sample["CX_P"] = 6.9042e-14
    w.last_results["tornado"] = sample
    w.set_plot_mode("Aerodynamics")
    app.processEvents()
    leftover = _leftover_map(w.compare_tabs.leftover_table)
    assert leftover["CX_P"][0] == "0"


def _luminance(color) -> float:
    def channel(v: int) -> float:
        x = v / 255.0
        return x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4

    return 0.2126 * channel(color.red()) + 0.7152 * channel(color.green()) + 0.0722 * channel(color.blue())


def _contrast_ratio(fg, bg) -> float:
    lighter = max(_luminance(fg), _luminance(bg))
    darker = min(_luminance(fg), _luminance(bg))
    return (lighter + 0.05) / (darker + 0.05)


def _assert_readable_headers(table: QTableWidget) -> None:
    for col in range(table.columnCount()):
        item = table.horizontalHeaderItem(col)
        assert item is not None
        assert item.foreground().style() != Qt.BrushStyle.NoBrush
        assert item.background().style() != Qt.BrushStyle.NoBrush
        assert _contrast_ratio(item.foreground().color(), item.background().color()) >= 4.5
        assert item.font().bold()
        assert item.font().pointSize() >= 10
    for row in range(table.rowCount()):
        if table.columnSpan(row, 0) <= 1:
            continue
        item = table.item(row, 0)
        assert item is not None
        assert item.foreground().style() != Qt.BrushStyle.NoBrush
        assert _contrast_ratio(item.foreground().color(), item.background().color()) >= 4.5
        assert item.font().bold()
        assert item.font().pointSize() >= 10


def test_sections_headers_are_readable():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    w.show()
    w.load_aircraft(load_jsonc(models_dir() / "Cessna 172.jsonc"))
    w.last_results["datcom"] = to_frd("datcom", parse_for006(_FOR006))
    w.last_results["tornado"] = _tornado_sample()
    w.last_results["avl"] = _avl_sample()
    w.set_plot_mode("Aerodynamics")
    app.processEvents()
    _assert_readable_headers(w.compare_tabs.leftover_table)
    _assert_readable_headers(w.compare_tabs.section_defs_table)


def test_sections_datcom_defs_is_qt_table():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    w.show()
    w.load_aircraft(load_jsonc(models_dir() / "Cessna 172.jsonc"))
    w.last_results["datcom"] = to_frd("datcom", parse_for006(_FOR006))
    w.set_plot_mode("Aerodynamics")
    w.compare_tabs.setCurrentIndex(list(_TABS).index("Sections"))
    app.processEvents()
    table = w.compare_tabs.section_defs_table
    assert isinstance(table, QTableWidget)
    text = _table_text(table)
    assert "Wing" in text
    assert "HT" in text
    assert "VT" in text
    assert "alpha_ideal" in text
    assert table.isVisible()
