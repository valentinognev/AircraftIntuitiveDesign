import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication

from aid_gui.main_window import MainWindow


def test_analyze_submenu():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    analyze = [a for a in w.menuBar().actions() if a.text() == "Analyze"][0].menu()
    labels = [a.text() for a in analyze.actions() if not a.isSeparator()]
    assert labels == ["DATCOM", "Tornado", "AVL"]
