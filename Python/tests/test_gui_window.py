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


def test_window_fits_screen_after_show():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    w.show()
    app.processEvents()
    avail = app.primaryScreen().availableGeometry()
    assert w.size().height() <= min(600, avail.height())
    assert w.size().width() <= min(960, avail.width())
    assert w.size().height() <= avail.height()
    assert w.size().width() <= avail.width()
