import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication

from aid_gui.main_window import MainWindow


def test_help_submenu():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    help_m = [a for a in w.menuBar().actions() if a.text() == "Help"][0].menu()
    labels = [a.text() for a in help_m.actions() if not a.isSeparator()]
    assert "Examples" in labels and "User's Manual" in labels
