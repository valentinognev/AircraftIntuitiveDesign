from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMainWindow


def build_menus(window: QMainWindow) -> None:
    _build_file_menu(window)
    _build_analyze_menu(window)


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


def _build_analyze_menu(window: QMainWindow) -> None:
    analyze_menu = window.menuBar().addMenu("Analyze")

    datcom_action = QAction("DATCOM", window)
    datcom_action.triggered.connect(window.run_datcom)
    analyze_menu.addAction(datcom_action)

    tornado_action = QAction("Tornado", window)
    tornado_action.triggered.connect(window.run_tornado)
    analyze_menu.addAction(tornado_action)

    avl_action = QAction("AVL", window)
    avl_action.triggered.connect(window.run_avl)
    analyze_menu.addAction(avl_action)
