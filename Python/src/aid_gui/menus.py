from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMainWindow


def build_menus(window: QMainWindow) -> None:
    _build_file_menu(window)


def _build_file_menu(window: QMainWindow) -> None:
    file_menu = window.menuBar().addMenu("File")

    new_action = QAction("New", window)
    new_action.triggered.connect(lambda: _on_new(window))
    file_menu.addAction(new_action)

    load_action = QAction("Load", window)
    load_action.triggered.connect(lambda: _on_load(window))
    file_menu.addAction(load_action)

    save_action = QAction("Save", window)
    save_action.triggered.connect(lambda: _on_save(window))
    file_menu.addAction(save_action)


def _on_new(window: QMainWindow) -> None:
    window.aircraft = None


def _on_load(window: QMainWindow) -> None:
    pass


def _on_save(window: QMainWindow) -> None:
    pass
