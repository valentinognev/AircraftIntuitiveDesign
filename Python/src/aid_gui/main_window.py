from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMainWindow, QSplitter

from aid.aircraft import Aircraft
from aid_gui.menus import build_menus
from aid_gui.tabs import build_tabs, populate_from_aircraft
from aid_gui.view3d import View3D


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Aircraft Intuitive Design Tool")
        self.resize(960, 600)
        self.aircraft = None
        build_menus(self)
        build_tabs(self)
        tab_widget = self.centralWidget()
        self.view3d = View3D()
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(tab_widget)
        splitter.addWidget(self.view3d)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        self.setCentralWidget(splitter)

    def load_aircraft(self, ac: Aircraft) -> None:
        self.aircraft = ac
        populate_from_aircraft(self, ac)
        self.view3d.plot_aircraft(ac)

    def field_value(self, dotted: str) -> float:
        return float(self._field_edits[dotted].text())

    def wing_chrdr_value(self) -> float:
        return self.field_value("WG.CHRDR")

    def run_datcom(self) -> None:
        pass

    def run_tornado(self) -> None:
        pass

    def run_avl(self) -> None:
        pass
