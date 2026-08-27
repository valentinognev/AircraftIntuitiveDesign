from PySide6.QtWidgets import QApplication

from aid_gui.main_window import MainWindow


def main() -> int:
    app = QApplication([])
    window = MainWindow()
    window.show()
    return app.exec()
