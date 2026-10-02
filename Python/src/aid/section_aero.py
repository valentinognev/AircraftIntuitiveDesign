"""Section lift slope from Lift_Curve_Slope.m (no dialogs)."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from aid.naca456 import NacaSpec, ordinates
from aid.naca_ordinates import naca4_ordinates, naca5_ordinates
from aid.panel_method import panel_method
from aid.panel_points import read_airfoil_file

_ALPHAS_DEG = np.array([-4.0, -2.0, 0.0, 2.0, 4.0, 6.0, 8.0], dtype=float)
_AIRFOIL_SUFFIXES = (".txt", ".dat", ".shp")


def section_slopes(pt: dict, index: int) -> None:
    """Lift_Curve_Slope.m without dialogs.

    NACA length 4 → naca4_ordinates(code, 120). Length 5 → naca5_ordinates(code, 120).
    Length >= 6 → NacaSpec the way NACA_Panel_Maker.m lines 114-124 writes the namelist
    (PROFILE = first two characters, or first two plus 'A' when 'A' is in the code;
    CAMBER = '6A' if 'A' in the code else the first character;
    TOC = last two digits/100; CL = the digit before those / 10; dencode=3),
    then cosine-resample to 120 points with the same x = 0.5-cos spacing.
    If ordinates() raises or returns an empty array, leave pt unchanged (MATLAB returns empty DATA).
    Then panel_method on alphas -4,-2,0,2,4,6,8 degrees and store a0, alpha0, Cm_ac at `index`,
    and TC = max(y)-min(y). A path ending in a known airfoil suffix goes through read_airfoil_file.
    """
    code = _naca_at(pt, index)
    if not code:
        return
    data = _section_ordinates(code)
    if data is None or data.size == 0:
        return
    out = panel_method(data, _ALPHAS_DEG)
    _assign_indexed(pt, "a0", index, out["a0"])
    _assign_indexed(pt, "alpha0", index, out["alpha0"])
    _assign_indexed(pt, "Cm_ac", index, out["Cm_ac"])
    y = data[:, 1]
    pt["TC"] = float(np.max(y) - np.min(y))


def _naca_at(pt: dict, index: int) -> str | None:
    naca = pt.get("NACA")
    if isinstance(naca, str):
        text = naca.strip()
        return text if index == 0 and text else None
    if isinstance(naca, (list, tuple)):
        if index < 0 or index >= len(naca) or naca[index] is None:
            return None
        text = str(naca[index]).strip()
        return text or None
    if naca is None or index != 0:
        return None
    text = str(naca).strip()
    return text or None


def _section_ordinates(code: str) -> np.ndarray | None:
    lower = code.lower()
    if lower.endswith(_AIRFOIL_SUFFIXES):
        try:
            data = read_airfoil_file(Path(code))
        except (OSError, ValueError):
            return None
        data = np.asarray(data, dtype=float)
        if data.size == 0:
            return None
        return data
    n = len(code)
    try:
        if n == 4:
            data = naca4_ordinates(code, 120)
        elif n == 5:
            data = naca5_ordinates(code, 120)
        elif n >= 6:
            data = ordinates(_naca_spec(code))
            data = np.asarray(data, dtype=float)
            if data.size == 0:
                return None
            data = _cosine_resample(data, 120)
        else:
            return None
    except (ValueError, OSError, IndexError):
        return None
    data = np.asarray(data, dtype=float)
    if data.size == 0:
        return None
    return data


def _naca_spec(code: str) -> NacaSpec:
    """NACA_Panel_Maker.m namelist. Profile is the Fortran family, never '6'."""
    profile = code[:2] + ("A" if "A" in code else "")
    camber = "6A" if "A" in code else code[0]
    toc = float(code[-2:]) / 100.0
    cl = float(code[-3]) / 10.0
    return NacaSpec(
        name=code,
        profile=profile,
        camber=camber,
        toc=toc,
        cl=cl,
        dencode=3,
    )


def _cosine_resample(data: np.ndarray, n_pts: int) -> np.ndarray:
    """NACA_Panel_Maker.m lines 149-158. n_pts is the MATLAB pts argument."""
    le = data.shape[0] // 2
    x_upper = data[:le, 0]
    y_upper = data[:le, 1]
    x_lower = data[le:, 0][::-1]
    y_lower = data[le:, 1][::-1]
    angle = np.linspace(0.0, np.pi, n_pts // 2 + 1)
    x_new = 0.5 - np.cos(angle) / 2.0
    y_upper_i = _interp_linear_extrap(x_upper, y_upper, x_new)
    y_lower_i = _interp_linear_extrap(x_lower, y_lower, x_new)
    x_out = np.concatenate([x_new[::-1], x_new[1:]])
    y_out = np.concatenate([y_lower_i[::-1], y_upper_i[1:]])
    return np.column_stack([x_out, y_out])


def _interp_linear_extrap(xp: np.ndarray, fp: np.ndarray, xq: np.ndarray) -> np.ndarray:
    xp = np.asarray(xp, dtype=np.float64)
    fp = np.asarray(fp, dtype=np.float64)
    order = np.argsort(xp, kind="mergesort")
    xp = xp[order]
    fp = fp[order]
    uniq = np.empty(xp.shape[0], dtype=bool)
    uniq[0] = True
    uniq[1:] = np.diff(xp) > 0.0
    xp = xp[uniq]
    fp = fp[uniq]
    y = np.interp(xq, xp, fp)
    if xp.shape[0] >= 2:
        left = fp[0] + (xq - xp[0]) * (fp[1] - fp[0]) / (xp[1] - xp[0])
        right = fp[-1] + (xq - xp[-1]) * (fp[-1] - fp[-2]) / (xp[-1] - xp[-2])
        y = np.where(xq < xp[0], left, y)
        y = np.where(xq > xp[-1], right, y)
    return y


def _assign_indexed(pt: dict, key: str, index: int, value: float) -> None:
    current = pt.get(key)
    if index == 0 and not isinstance(current, (list, tuple, np.ndarray)):
        pt[key] = float(value)
        return
    if isinstance(current, np.ndarray):
        values = [float(v) for v in np.asarray(current, dtype=float).reshape(-1)]
    elif isinstance(current, (list, tuple)):
        values = [float(v) for v in current]
    elif current is None:
        values = []
    else:
        values = [float(current)]
    while len(values) <= index:
        values.append(0.0)
    values[index] = float(value)
    pt[key] = values
