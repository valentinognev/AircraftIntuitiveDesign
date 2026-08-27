from PySide6.QtWidgets import QMainWindow

from aid.aircraft import Aircraft
from aid_gui.menus import build_menus
from aid_gui.tabs import build_tabs, populate_from_aircraft


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Aircraft Intuitive Design Tool")
        self.resize(960, 600)
        self.aircraft = None
        build_menus(self)
        build_tabs(self)

    def load_aircraft(self, ac: Aircraft) -> None:
        self.aircraft = ac
        populate_from_aircraft(self, ac)

    def wing_chrdr_value(self) -> float:
        return float(self._wing_chrdr_edit.text())

    def run_datcom(self) -> None:
        pass

    def run_tornado(self) -> None:
        pass

    def run_avl(self) -> None:
        pass
