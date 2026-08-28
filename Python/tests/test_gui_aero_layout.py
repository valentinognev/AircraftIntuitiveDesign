import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication

from aid.aircraft import load_jsonc
from aid.paths import models_dir
from aid_gui.main_window import MainWindow


def test_aerodynamics_plot_not_collapsed():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    w.show()
    w.resize(960, 600)
    w.load_aircraft(load_jsonc(models_dir() / "Cessna 172.jsonc"))
    w.set_plot_mode("Aerodynamics")
    app.processEvents()
    assert not w.results_panel.isHidden()
    assert not w.view3d.isHidden()
    assert w.results_panel.height() >= 160
    ratio = w.results_panel.height() / max(w.view3d.height(), 1)
    assert 0.4 <= ratio <= 1.2
