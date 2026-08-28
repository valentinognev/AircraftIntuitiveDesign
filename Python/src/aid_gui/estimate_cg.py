"""Estimate CG: 3×10 table, component dialog, mass-weighted AERO.WT/XCG/ZCG."""

from __future__ import annotations

import numpy as np
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from aid.aircraft import Aircraft

CG_NCOLS = 10
CG_TITLES = (
    "Wing",
    "Horizontal Tail",
    "Vertical Tail",
    "Body",
    "Wing 2",
    "Horizontal Tail 2",
    "Vertical Tail 2",
    "Propeller",
    "Body 2",
    "Body 3",
)

_SURFACE_COL = {
    "wing": 0,
    "wingtip": 0,
    "WG": 0,
    "WGtip": 0,
    "F": 0,
    "A": 0,
    "ht": 1,
    "httip": 1,
    "HT": 1,
    "HTtip": 1,
    "E": 1,
    "vt": 2,
    "vttip": 2,
    "VT": 2,
    "VTtip": 2,
    "R": 2,
    "BD": 3,
    "wing 2": 4,
    "wing 2tip": 4,
    "NP{1}": 4,
    "NP{1}tip": 4,
    "ht 2": 5,
    "ht 2tip": 5,
    "NP{2}": 5,
    "NP{2}tip": 5,
    "vt 2": 6,
    "vt 2tip": 6,
    "NP{3}": 6,
    "NP{3}tip": 6,
    "prop": 7,
    "NP{4}": 7,
    "NB{1}": 8,
    "NB{2}": 9,
}


def empty_cg_data() -> list[list[float]]:
    return [[0.0] * CG_NCOLS for _ in range(3)]


def _is_3x10(data) -> bool:
    return (
        isinstance(data, list)
        and len(data) == 3
        and all(isinstance(row, list) and len(row) == 10 for row in data)
    )


def ensure_cg_data(ac: Aircraft) -> list[list[float]]:
    if not _is_3x10(ac.cg_data):
        ac.cg_data = empty_cg_data()
    return ac.cg_data


def _last(val) -> float:
    return float(np.asarray(val, dtype=float).reshape(-1)[-1])


def _first(val) -> float:
    arr = np.asarray(val, dtype=float).reshape(-1)
    return float(arr[0]) if arr.size else 0.0


def column_for_surface(name: str) -> int | None:
    if name in _SURFACE_COL:
        return _SURFACE_COL[name]
    if name.endswith("tip"):
        return _SURFACE_COL.get(name[:-3])
    return None


def part_for_column(ac: Aircraft, col: int) -> dict | None:
    if col == 0:
        return ac.WG
    if col == 1:
        return ac.HT
    if col == 2:
        return ac.VT
    if col == 3:
        return ac.BD
    if 4 <= col <= 7:
        idx = col - 4
        if idx < len(ac.NP):
            pt = ac.NP[idx]
            return pt if isinstance(pt, dict) else None
        return None
    if 8 <= col <= 9:
        idx = col - 8
        if idx < len(ac.NB):
            pt = ac.NB[idx]
            return pt if isinstance(pt, dict) else None
        return None
    return None


def _apex(ac: Aircraft) -> tuple[list[float], list[float]]:
    x0 = [0.0] * CG_NCOLS
    z0 = [0.0] * CG_NCOLS
    x0[0] = float(ac.WG.get("X") or 0)
    x0[1] = float(ac.HT.get("X") or 0)
    x0[2] = float(ac.VT.get("X") or 0)
    x0[3] = _first(ac.BD.get("X", 0))
    z0[0] = float(ac.WG.get("Z") or 0)
    z0[1] = float(ac.HT.get("Z") or 0)
    z0[2] = float(ac.VT.get("Z") or 0)
    z0[3] = 0.0
    for n in range(4):
        pt = ac.NP[n] if n < len(ac.NP) else None
        if isinstance(pt, dict):
            x0[4 + n] = float(pt.get("X") or 0)
            z0[4 + n] = float(pt.get("Z") or 0)
    for n in range(2):
        pt = ac.NB[n] if n < len(ac.NB) else None
        if isinstance(pt, dict):
            x0[8 + n] = _first(pt.get("X0", 0))
            z0[8 + n] = _first(pt.get("Z0", 0))
    return x0, z0


def _weight_enabled(ac: Aircraft) -> list[bool]:
    flags = list(ac.plot_cmp) + [1] * 8
    ok = [True] * CG_NCOLS
    for i in range(4):
        ok[i] = bool(flags[i])
    for n in range(4):
        pt = ac.NP[n] if n < len(ac.NP) else None
        ok[4 + n] = bool(pt) and bool(flags[4 + n])
    for n in range(2):
        pt = ac.NB[n] if n < len(ac.NB) else None
        ok[8 + n] = bool(pt) and bool(flags[8 + n])
    return ok


def recompute_aero_cg(ac: Aircraft) -> bool:
    """Mass-weighted WT/XCG/ZCG from 3×10 cg_data (AID.m ~818). False if Σw=0."""
    if not _is_3x10(ac.cg_data):
        return False
    x = [float(v) for v in ac.cg_data[0]]
    z = [float(v) for v in ac.cg_data[1]]
    w = [float(v) for v in ac.cg_data[2]]
    x0, z0 = _apex(ac)
    enabled = _weight_enabled(ac)
    for i in range(CG_NCOLS):
        if not enabled[i]:
            w[i] = 0.0
        x[i] = x[i] + x0[i]
        z[i] = z[i] + z0[i]
    if ac.unit == "in":
        w = [wi / 16.0 for wi in w]
    sw = sum(w)
    if sw == 0:
        return False
    ac.AERO["WT"] = sw
    ac.AERO["XCG"] = sum(xi * wi for xi, wi in zip(x, w)) / sw
    ac.AERO["ZCG"] = sum(zi * wi for zi, wi in zip(z, w)) / sw
    return True


def apply_component(ac: Aircraft, col: int, x: float, z: float, wt: float) -> None:
    data = ensure_cg_data(ac)
    data[0][col] = float(x)
    data[1][col] = float(z)
    data[2][col] = float(wt)
    part = part_for_column(ac, col)
    if isinstance(part, dict):
        part["XCG"] = float(x)
        part["ZCG"] = float(z)
        part["WT"] = float(wt)


def default_component_values(ac: Aircraft, col: int) -> tuple[float, float, float]:
    data = ac.cg_data
    if _is_3x10(data) and float(data[0][col]) != 0.0:
        return float(data[0][col]), float(data[1][col]), float(data[2][col])
    if col == 0:
        return _last(ac.WG.get("xmac", 0)) + _last(ac.WG.get("cbar", 0)) / 3.0, 0.0, 0.0
    if col == 1:
        return _last(ac.HT.get("xmac", 0)) + _last(ac.HT.get("cbar", 0)) / 2.0, 0.0, 0.0
    if col == 2:
        return (
            _last(ac.VT.get("xmac", 0)) + _last(ac.VT.get("cbar", 0)) / 2.0,
            _last(ac.VT.get("ymac", 0)) / 2.0,
            0.0,
        )
    if col == 3:
        x_st = np.asarray(ac.BD.get("X", [0.0]), dtype=float).reshape(-1)
        zu = np.asarray(ac.BD.get("ZU", [0.0]), dtype=float).reshape(-1)
        zl = np.asarray(ac.BD.get("ZL", [0.0]), dtype=float).reshape(-1)
        n = min(x_st.size, zu.size, zl.size)
        zmean = float(np.mean((zu[:n] + zl[:n]) / 2.0)) if n else 0.0
        return (float(x_st[-1] - x_st[0]) / 2.0 if n else 0.0), zmean, 0.0
    if 4 <= col <= 7:
        pt = part_for_column(ac, col)
        if not isinstance(pt, dict):
            return 0.0, 0.0, 0.0
        if col == 7:
            return 0.0, 0.0, 0.0
        frac = 3.0 if col == 4 else 2.0
        zdef = _last(pt.get("ymac", 0)) / 2.0 if col == 6 else 0.0
        return _last(pt.get("xmac", 0)) + _last(pt.get("cbar", 0)) / frac, zdef, 0.0
    pt = part_for_column(ac, col)
    if not isinstance(pt, dict):
        return 0.0, 0.0, 0.0
    x_st = np.asarray(pt.get("X", [0.0]), dtype=float).reshape(-1)
    zu = np.asarray(pt.get("ZU", [0.0]), dtype=float).reshape(-1)
    zl = np.asarray(pt.get("ZL", [0.0]), dtype=float).reshape(-1)
    n = min(x_st.size, zu.size, zl.size)
    zmean = float(np.mean((zu[:n] + zl[:n]) / 2.0)) if n else 0.0
    return (float(x_st[-1] - x_st[0]) / 2.0 if n else 0.0), zmean, 0.0


def weight_unit(ac: Aircraft) -> str:
    x_end = _last(ac.BD.get("X", 0))
    if ac.unit == "in" and x_end < 120:
        return "oz"
    return "lb"


class ComponentCgDialog(QDialog):
    def __init__(
        self,
        part: str,
        defaults: tuple[float, float, float] = (0.0, 0.0, 0.0),
        unit: str = "ft",
        wt_unit: str = "lb",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"{part} Weight")
        self._accepted = False
        self._edits: list[QLineEdit] = []
        form = QFormLayout()
        prompts = (
            f"Component X-CG Location, {unit}",
            f"Component Z-CG Location, {unit}",
            f"Component Weight, {wt_unit}",
        )
        for prompt, value in zip(prompts, defaults, strict=True):
            edit = QLineEdit(str(value))
            form.addRow(prompt, edit)
            self._edits.append(edit)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def accept(self) -> None:
        self._accepted = True
        super().accept()

    def reject(self) -> None:
        self._accepted = False
        super().reject()

    def values(self) -> tuple[float, float, float] | None:
        if not self._accepted:
            return None
        try:
            return tuple(float(edit.text()) for edit in self._edits)
        except ValueError:
            return None
