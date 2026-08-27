from PySide6.QtWidgets import QFormLayout, QLineEdit, QTabWidget, QWidget

from aid.aircraft import Aircraft


def build_tabs(window) -> None:
    tab_widget = QTabWidget()
    wing_tab = QWidget()
    layout = QFormLayout(wing_tab)
    window._wing_chrdr_edit = QLineEdit()
    layout.addRow("Root Chord", window._wing_chrdr_edit)
    tab_widget.addTab(wing_tab, "Wing")
    window.setCentralWidget(tab_widget)


def populate_from_aircraft(window, ac: Aircraft) -> None:
    window._wing_chrdr_edit.setText(str(ac.WG["CHRDR"]))
