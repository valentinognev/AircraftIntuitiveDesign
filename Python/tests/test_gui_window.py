import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication

from aid_gui.main_window import MainWindow


def test_window_title_and_size():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    assert w.windowTitle() == "Aircraft Intuitive Design Tool"
    assert w.size().width() == 960
    assert w.size().height() == 600
