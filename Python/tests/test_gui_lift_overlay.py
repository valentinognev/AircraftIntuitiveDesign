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
