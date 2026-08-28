from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

_MODES = ("Geometry", "Stability", "Aerodynamics")


class ResultsBar(QWidget):
    modeChanged = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(4, 0, 4, 4)
        outer.addWidget(QLabel("Results:"))
        row = QHBoxLayout()
        plot_box = QGroupBox("Plot")
        plot_col = QVBoxLayout(plot_box)
        self._group = QButtonGroup(self)
        self._radios: dict[str, QRadioButton] = {}
        for i, name in enumerate(_MODES):
            radio = QRadioButton(name)
            radio.setChecked(name == "Geometry")
            self._group.addButton(radio, i)
            self._radios[name] = radio
            plot_col.addWidget(radio)
        self._group.buttonClicked.connect(self._on_button)
        row.addWidget(plot_box)
        stab_box = QGroupBox("Stability")
        stab_col = QVBoxLayout(stab_box)
        self._summary = QLabel()
        self._summary.setWordWrap(True)
        stab_col.addWidget(self._summary)
        row.addWidget(stab_box, 1)
        outer.addLayout(row)

    def _on_button(self, btn: QRadioButton) -> None:
        self.modeChanged.emit(btn.text())

    def plot_mode(self) -> str:
        for name, radio in self._radios.items():
            if radio.isChecked():
                return name
        return "Geometry"

    def set_mode(self, mode: str) -> None:
        radio = self._radios[mode]
        if radio.isChecked():
            return
        radio.blockSignals(True)
        radio.setChecked(True)
        radio.blockSignals(False)

    def summary_text(self) -> str:
        return self._summary.text()

    def set_summary(self, lines: list[str]) -> None:
        self._summary.setText("\n".join(lines))
