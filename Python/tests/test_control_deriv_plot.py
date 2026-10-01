import copy
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("PYVISTA_OFF_SCREEN", "true")
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from PySide6.QtWidgets import QApplication

from aid.aircraft import load_jsonc
from aid.control_report import control_report
from aid.paths import models_dir
from aid_gui.main_window import MainWindow


def test_controls_tab_plots_probe_curve_at_zero_stored_deflection():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    w.show()
    w.load_aircraft(load_jsonc(models_dir() / "Cessna 172.jsonc"))
    stored = copy.deepcopy(w.aircraft.F["DELTA"])
    w.last_results["control_derivatives"] = control_report(w.aircraft, "handbook", [0.0, 5.0])
    w.set_plot_mode("Aerodynamics")
    controls = next(i for i in range(w.compare_tabs.count()) if w.compare_tabs.tabText(i) == "Controls")
    w.compare_tabs.setCurrentIndex(controls)
    app.processEvents()
    xs = []
    labels = []
    page = w.compare_tabs.widget(controls)
    canvas = page.findChild(FigureCanvas) or page
    fig = canvas.figure
    for ax in fig.axes:
        for line in ax.get_lines():
            labels.append(line.get_label())
            xs.append(list(line.get_xdata()))
    assert any("handbook" in lab and "flap" in lab for lab in labels)
    assert any(x == [0.0, 5.0] for x in xs)
    assert w.aircraft.F["DELTA"] == stored
