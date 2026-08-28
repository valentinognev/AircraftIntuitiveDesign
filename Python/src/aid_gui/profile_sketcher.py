"""Body-station editor (MATLAB Profile_Sketcher idea: X, ZU, ZL, R, P)."""

from __future__ import annotations

import numpy as np
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

COLS = ("X", "ZU", "ZL", "R", "P")


def _station_count(bd: dict) -> int:
    x = bd.get("X", [])
    n = len(np.asarray(x, dtype=float).reshape(-1))
    nx = bd.get("NX")
    if nx is not None:
        try:
            n = max(n, int(nx))
        except (TypeError, ValueError):
            pass
    return max(n, 1)


def _col_values(bd: dict, key: str, n: int) -> list[float]:
    raw = bd.get(key, [0.0] * n)
    vals = [float(v) for v in np.asarray(raw, dtype=float).reshape(-1)]
    if len(vals) < n:
        vals.extend([0.0] * (n - len(vals)))
    return vals[:n]


class ProfileSketcherDialog(QDialog):
    def __init__(self, bd: dict, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Fuselage Design")
        n = _station_count(bd)
        self._table = QTableWidget(n, len(COLS), self)
        self._table.setHorizontalHeaderLabels(list(COLS))
        for col, key in enumerate(COLS):
            for row, val in enumerate(_col_values(bd, key, n)):
                self._table.setItem(row, col, QTableWidgetItem(str(val)))

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Apply | QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        apply_btn = buttons.button(QDialogButtonBox.StandardButton.Apply)
        if apply_btn is not None:
            apply_btn.clicked.connect(self.accept)

        layout = QVBoxLayout(self)
        layout.addWidget(self._table)
        layout.addWidget(buttons)

    def set_station_value(self, row: int, col_name: str, value: float) -> None:
        col = COLS.index(col_name)
        item = self._table.item(row, col)
        text = str(value)
        if item is None:
            self._table.setItem(row, col, QTableWidgetItem(text))
        else:
            item.setText(text)

    def body_arrays(self) -> dict:
        n = self._table.rowCount()
        out: dict = {"NX": n}
        for col, key in enumerate(COLS):
            vals: list[float] = []
            for row in range(n):
                item = self._table.item(row, col)
                text = item.text() if item is not None else "0"
                try:
                    vals.append(float(text))
                except ValueError:
                    vals.append(0.0)
            out[key] = vals
        return out

    def apply_to(self, bd: dict) -> None:
        bd.update(self.body_arrays())
