import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("PYVISTA_OFF_SCREEN", "true")
from PySide6.QtWidgets import QApplication
from aid.aircraft import load_jsonc
from aid.paths import models_dir
from aid_gui.main_window import MainWindow

def test_camera_is_nose_on_matlab_view3():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    w.load_aircraft(load_jsonc(models_dir() / "Cessna 172.jsonc"))
    pos = w.view3d.camera_xyz()
    foc = w.view3d.camera_focus()
    assert pos[0] < foc[0]  # camera toward -X relative to focus → nose toward viewer
    assert pos[1] < foc[1]
    assert pos[2] > foc[2]
