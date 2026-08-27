import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication

from aid_gui.main_window import MainWindow


def test_file_menu_actions():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    file_menu = [a for a in w.menuBar().actions() if a.text() == "File"][0].menu()
    labels = [a.text() for a in file_menu.actions() if not a.isSeparator()]
    assert labels[:3] == ["New", "Load", "Save"]
