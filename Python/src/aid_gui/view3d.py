import math

import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from aid.aircraft import Aircraft


class View3D(FigureCanvasQTAgg):
    def __init__(self) -> None:
        self._figure = Figure()
        super().__init__(self._figure)
        self._ax = self._figure.add_subplot(111, projection="3d")
        self._line_count = 0

    def line_count(self) -> int:
        return self._line_count

    def plot_aircraft(self, ac: Aircraft) -> None:
        self._ax.clear()
        self._line_count = 0
        self._plot_wing_outline(ac.WG)
        self._set_equal_aspect()
        self.draw()

    def _set_equal_aspect(self) -> None:
        xr = float(np.ptp(self._ax.get_xlim3d())) or 1.0
        yr = float(np.ptp(self._ax.get_ylim3d())) or 1.0
        zr = float(np.ptp(self._ax.get_zlim3d())) or 1.0
        self._ax.set_box_aspect((xr, yr, zr))

    def _plot_polyline(self, xs: np.ndarray, ys: np.ndarray, zs: np.ndarray) -> None:
        self._ax.plot(xs, ys, zs, color="C0")
        if len(xs) >= 2:
            self._line_count += len(xs) - 1

    def _plot_wing_outline(self, pt: dict, nj: int = 20) -> None:
        y, x_le, x_te, z = _wing_planform_edges(pt, nj)
        self._plot_polyline(x_le, y, z)
        self._plot_polyline(x_te, y, z)
        self._plot_polyline(x_le, -y, z)
        self._plot_polyline(x_te, -y, z)
        self._plot_polyline([x_le[0], x_te[0]], [y[0], y[0]], [z[0], z[0]])
        self._plot_polyline([x_le[0], x_te[0]], [-y[0], -y[0]], [z[0], z[0]])
        self._plot_polyline([x_le[-1], x_te[-1]], [y[-1], y[-1]], [z[-1], z[-1]])
        self._plot_polyline([x_le[-1], x_te[-1]], [-y[-1], -y[-1]], [z[-1], z[-1]])


def _wing_planform_edges(pt: dict, nj: int) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    xt = 0.25
    y0 = float(pt.get("Y", 0))
    z0 = float(pt.get("Z", 0))
    x0 = float(pt.get("X", 0))
    chrdr = float(pt.get("CHRDR", 0))
    chrdtp = float(pt.get("CHRDTP", chrdr))
    chrdbp = float(pt.get("CHRDBP", 0))
    sspn = float(pt.get("SSPN", 0))
    sspnop = float(pt.get("SSPNOP", 0))
    savsi = float(pt.get("SAVSI", 0))
    savso = float(pt.get("SAVSO", 0))
    chstat = float(pt.get("CHSTAT", 0))
    dhdadi = float(pt.get("DHDADI", 0))
    dhdado = float(pt.get("DHDADO", 0))

    if chrdbp and sspnop:
        y_break = sspnop
        n1 = max(2, round(nj * abs(y_break) / sspn))
        y1 = y0 + np.linspace(0, y_break, n1)
        c1 = chrdr + (y1 - y0) / (y1[-1] - y0) * (chrdbp - chrdr)
        dx1 = x0 + (y1 - y0) * math.tan(math.radians(savsi))
        dx1 += chstat * (chrdr - chrdbp) * (y1 - y0) / (y1[-1] - y0)
        dz1 = z0 + (y1 - y0) * math.tan(math.radians(dhdadi))

        y_out = sspn
        n2 = max(2, nj - n1 + 1)
        y2 = y0 + np.linspace(y_break, y_out, n2)
        c2 = chrdbp + (y2 - y2[0]) / (y2[-1] - y2[0]) * (chrdtp - chrdbp)
        dx2 = dx1[-1] + (y2 - y2[0]) * math.tan(math.radians(savso))
        dx2 += chstat * (chrdbp - chrdtp) * (y2 - y2[0]) / (y2[-1] - y2[0])
        dz2 = dz1[-1] + (y2 - y2[0]) * math.tan(math.radians(dhdado))

        y = np.concatenate([y1, y2[1:]])
        c = np.concatenate([c1, c2[1:]])
        dx = np.concatenate([dx1, dx2[1:]])
        z = np.concatenate([dz1, dz2[1:]])
    else:
        y_out = sspn
        y = y0 + np.linspace(0, y_out, nj)
        c = chrdr + (y - y0) / (y[-1] - y0) * (chrdtp - chrdr)
        dx = x0 + (y - y0) * math.tan(math.radians(savsi))
        dx += chstat * (chrdr - chrdtp) * (y - y0) / (y[-1] - y0)
        z = z0 + (y - y0) * math.tan(math.radians(dhdadi))

    dx_qc = dx + xt * c
    x_le = dx_qc - xt * c
    x_te = dx_qc + (1 - xt) * c
    return y, x_le, x_te, z
