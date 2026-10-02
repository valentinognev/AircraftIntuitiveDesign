"""Interactive fuselage sketch: side and top station polylines.

Edits a copy of the body dict. Apply writes ``X``, ``ZU``, ``ZL``, ``R``,
``NX``, and ``S = pi * ZU**2`` back. The station-table dialog in
``profile_sketcher.py`` is unchanged.
"""

from __future__ import annotations

import numpy as np
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QPainter, QPen, QPolygonF
from PySide6.QtWidgets import (
    QButtonGroup,
    QDialog,
    QHBoxLayout,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from aid.profile_edit import add_or_remove_point, mirror_surface, smooth_profile

_MARGIN = 12.0


def _copy_stations(bd: dict) -> dict:
    xs = np.asarray(bd["X"], dtype=float).reshape(-1).copy()
    return {
        "NX": int(xs.size),
        "X": xs,
        "ZU": np.asarray(bd["ZU"], dtype=float).reshape(-1).copy(),
        "ZL": np.asarray(bd["ZL"], dtype=float).reshape(-1).copy(),
        "R": np.asarray(bd["R"], dtype=float).reshape(-1).copy(),
    }


class _SketchCanvas(QWidget):
    def __init__(self, dialog: ProfileSketchDialog) -> None:
        super().__init__(dialog)
        self._dialog = dialog
        self.setMinimumSize(360, 280)
        self._press: dict | None = None

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("white"))
        height = self.height()
        mid = height // 2
        painter.setPen(QPen(QColor("#bbbbbb"), 1))
        painter.drawLine(0, mid, self.width(), mid)
        self._draw_view(painter, "side", 0, mid)
        self._draw_view(painter, "top", mid, height - mid)
        painter.end()

    def _draw_view(self, painter: QPainter, view: str, top: int, height: int) -> None:
        work = self._dialog.work
        color = QColor("#1a5fb4") if self._dialog.view == view else QColor("#555555")
        painter.setPen(QPen(color, 2))
        if view == "side":
            curves = (work["ZU"], work["ZL"])
        else:
            curves = (work["R"], -work["R"])
        for values in curves:
            points = [
                QPointF(*self._dialog.data_to_pixel(view, float(x), float(z), top, height))
                for x, z in zip(work["X"], values, strict=True)
            ]
            if len(points) >= 2:
                painter.drawPolyline(QPolygonF(points))
            elif len(points) == 1:
                painter.drawPoint(points[0])

    def mousePressEvent(self, event) -> None:
        if event.button() != Qt.MouseButton.LeftButton:
            return
        px = float(event.position().x())
        py = float(event.position().y())
        view, x, y = self._dialog.pixel_to_data(px, py)
        self._dialog.set_view(view)
        self._press = {
            "view": view,
            "x": x,
            "y": y,
            "px": px,
            "py": py,
            "hit": self._dialog.station_at(view, x, y),
            "moved": False,
        }

    def mouseMoveEvent(self, event) -> None:
        if self._press is None or not (event.buttons() & Qt.MouseButton.LeftButton):
            return
        px = float(event.position().x())
        py = float(event.position().y())
        if abs(px - self._press["px"]) + abs(py - self._press["py"]) > 4.0:
            self._press["moved"] = True
        if self._press["moved"] and self._press["hit"] is not None:
            x, y = self._dialog.data_from_pixel(self._press["view"], px, py)
            self._dialog.move_station(self._press["hit"], self._press["view"], x, y)
            self.update()

    def mouseReleaseEvent(self, event) -> None:
        if self._press is None:
            return
        press = self._press
        self._press = None
        if press["moved"] and press["hit"] is not None:
            self.update()
            return
        if press["hit"] is not None:
            self._dialog.remove_station(press["hit"][0])
        else:
            if press["moved"]:
                x, y = self._dialog.data_from_pixel(
                    press["view"], float(event.position().x()), float(event.position().y())
                )
            else:
                x, y = press["x"], press["y"]
            add_or_remove_point(
                self._dialog.work,
                x,
                y,
                view=press["view"],
                thresh=self._dialog.thresh(),
                manual=False,
            )
            self._dialog.sync_nx()
        self.update()


class ProfileSketchDialog(QDialog):
    def __init__(self, bd: dict, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Fuselage Sketch")
        self._target = bd
        self._work = _copy_stations(bd)
        self._view = "side"

        self._side = QRadioButton("Side")
        self._top = QRadioButton("Top")
        self._side.setChecked(True)
        group = QButtonGroup(self)
        group.addButton(self._side)
        group.addButton(self._top)
        self._side.toggled.connect(lambda checked: checked and self.set_view("side"))
        self._top.toggled.connect(lambda checked: checked and self.set_view("top"))

        smooth = QPushButton("Smooth")
        mirror_upper = QPushButton("Mirror upper")
        mirror_lower = QPushButton("Mirror lower")
        apply_btn = QPushButton("Apply")
        smooth.clicked.connect(self._on_smooth)
        mirror_upper.clicked.connect(self._on_mirror_upper)
        mirror_lower.clicked.connect(self._on_mirror_lower)
        apply_btn.clicked.connect(self._on_apply)

        row = QHBoxLayout()
        for widget in (self._side, self._top, smooth, mirror_upper, mirror_lower, apply_btn):
            row.addWidget(widget)
        self._canvas = _SketchCanvas(self)
        layout = QVBoxLayout(self)
        layout.addLayout(row)
        layout.addWidget(self._canvas, 1)

    @property
    def work(self) -> dict:
        return self._work

    @property
    def view(self) -> str:
        return self._view

    def set_view(self, view: str) -> None:
        self._view = view
        button = self._side if view == "side" else self._top
        if not button.isChecked():
            button.setChecked(True)
        self._canvas.update()

    def thresh(self) -> float:
        xs = self._work["X"]
        if xs.size < 2:
            return 0.05
        return 0.05 * float(xs[-1] - xs[0])

    def sync_nx(self) -> None:
        self._work["NX"] = int(np.asarray(self._work["X"]).reshape(-1).size)

    def _limits(self, view: str) -> tuple[float, float, float, float]:
        xs = np.asarray(self._work["X"], dtype=float).reshape(-1)
        if view == "side":
            ys = np.concatenate([np.asarray(self._work["ZU"], dtype=float), np.asarray(self._work["ZL"], dtype=float)])
        else:
            radius = np.asarray(self._work["R"], dtype=float)
            ys = np.concatenate([radius, -radius])
        x0 = float(np.min(xs)) if xs.size else 0.0
        x1 = float(np.max(xs)) if xs.size else 1.0
        y0 = float(np.min(ys)) if ys.size else -1.0
        y1 = float(np.max(ys)) if ys.size else 1.0
        if x1 <= x0:
            x1 = x0 + 1.0
        if y1 <= y0:
            y1 = y0 + 1.0
        return x0 - 0.05 * (x1 - x0), x1 + 0.05 * (x1 - x0), y0 - 0.08 * (y1 - y0), y1 + 0.08 * (y1 - y0)

    def _region(self, view: str) -> tuple[int, int]:
        height = max(self._canvas.height(), 1)
        if view == "side":
            return 0, height // 2
        return height // 2, height - height // 2

    def data_to_pixel(
        self,
        view: str,
        x: float,
        y: float,
        top: int | None = None,
        height: int | None = None,
    ) -> tuple[float, float]:
        if top is None or height is None:
            top, height = self._region(view)
        x0, x1, y0, y1 = self._limits(view)
        width = max(float(self._canvas.width()) - 2.0 * _MARGIN, 1.0)
        plot_h = max(float(height) - 2.0 * _MARGIN, 1.0)
        px = _MARGIN + (x - x0) / (x1 - x0) * width
        py = float(top) + _MARGIN + (y1 - y) / (y1 - y0) * plot_h
        return px, py

    def data_from_pixel(self, view: str, px: float, py: float) -> tuple[float, float]:
        top, height = self._region(view)
        x0, x1, y0, y1 = self._limits(view)
        width = max(float(self._canvas.width()) - 2.0 * _MARGIN, 1.0)
        plot_h = max(float(height) - 2.0 * _MARGIN, 1.0)
        x = x0 + (px - _MARGIN) / width * (x1 - x0)
        y = y1 - (py - float(top) - _MARGIN) / plot_h * (y1 - y0)
        return x, y

    def pixel_to_data(self, px: float, py: float) -> tuple[str, float, float]:
        view = "side" if py < self._canvas.height() / 2.0 else "top"
        x, y = self.data_from_pixel(view, px, py)
        return view, x, y

    def station_at(self, view: str, x: float, y: float) -> tuple[int, str] | None:
        thresh = self.thresh()
        xs = np.asarray(self._work["X"], dtype=float).reshape(-1)
        if view == "side":
            series = (("upper", self._work["ZU"]), ("lower", self._work["ZL"]))
        else:
            radius = np.asarray(self._work["R"], dtype=float)
            series = (("upper", radius), ("lower", -radius))
        best: tuple[int, str] | None = None
        best_d: float | None = None
        for name, values in series:
            for index, (xi, yi) in enumerate(zip(xs, np.asarray(values, dtype=float), strict=True)):
                dx = abs(float(xi) - x)
                dy = abs(float(yi) - y)
                if dx < thresh and dy < thresh:
                    dist = dx * dx + dy * dy
                    if best_d is None or dist < best_d:
                        best_d = dist
                        best = (index, name)
        return best

    def remove_station(self, index: int) -> None:
        """Drop a station the canvas already hit. Does not re-test y against ZU/ZL."""
        for key in ("X", "ZU", "ZL", "R"):
            self._work[key] = np.delete(np.asarray(self._work[key], dtype=float), index)
        self.sync_nx()

    def move_station(self, hit: tuple[int, str], view: str, x: float, y: float) -> None:
        """Move one station. Insert and delete stay on ``add_or_remove_point``."""
        index, surface = hit
        self._work["X"][index] = float(x)
        if view == "top":
            self._work["R"][index] = abs(float(y))
        elif surface == "upper":
            self._work["ZU"][index] = float(y)
        else:
            self._work["ZL"][index] = float(y)

    def _on_smooth(self) -> None:
        smooth_profile(self._work, flatten=False)
        self.sync_nx()
        self._canvas.update()

    def _on_mirror_upper(self) -> None:
        mirror_surface(self._work, source="upper", center=0.0)
        self._canvas.update()

    def _on_mirror_lower(self) -> None:
        mirror_surface(self._work, source="lower", center=0.0)
        self._canvas.update()

    def _on_apply(self) -> None:
        for key in ("X", "ZU", "ZL", "R"):
            self._target[key] = np.array(self._work[key], dtype=float, copy=True)
        self._target["NX"] = int(len(self._target["X"]))
        zu = np.asarray(self._target["ZU"], dtype=float)
        self._target["S"] = np.pi * zu**2
