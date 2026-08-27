from PySide6.QtWidgets import QMainWindow

from aid_gui.menus import build_menus


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Aircraft Intuitive Design Tool")
        self.resize(960, 600)
        self.aircraft = None
        build_menus(self)
