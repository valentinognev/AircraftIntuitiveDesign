import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("PYVISTA_OFF_SCREEN", "true")
os.environ.setdefault("VTK_DEFAULT_RENDER_WINDOW_OFFSCREEN", "1")

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from PySide6.QtWidgets import QApplication, QWidget

from aid.aircraft import load_jsonc
from aid.paths import models_dir
from aid.viz import aircraft_surfaces
from aid_gui.main_window import MainWindow


def test_view3d_has_canvas():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    w.load_aircraft(ac)
    assert w.view3d is not None
    assert isinstance(w.view3d, QWidget)
    assert not isinstance(w.view3d, FigureCanvasQTAgg)
    n = len(aircraft_surfaces(ac))
    assert w.view3d.mesh_count() == n
    assert w.view3d.line_count() == n
    assert n > 0
