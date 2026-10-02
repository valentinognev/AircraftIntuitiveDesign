"""Fuselage station edit, symmetry, and smooth.

Port of ``Point``, ``Symmetry``, and ``Smooth`` in
``Matlab/fsroot/code/Profile_Sketcher.m``. Plotting and the 30-step camera
animation are not included.
"""

from __future__ import annotations

import numpy as np


def _as_float(values) -> np.ndarray:
    return np.asarray(values, dtype=float).reshape(-1).copy()


def _interp_linear_extrap(x_new: np.ndarray, x_old: np.ndarray, y_old: np.ndarray) -> np.ndarray:
    """MATLAB ``interp1(..., 'linear', 'extrap')`` for a strictly increasing ``x_old``."""
    y = np.interp(x_new, x_old, y_old)
    if x_old.size < 2:
        return np.full(x_new.shape, float(y_old[0]), dtype=float)
    left = x_new < x_old[0]
    right = x_new > x_old[-1]
    if np.any(left):
        slope = (y_old[1] - y_old[0]) / (x_old[1] - x_old[0])
        y = y.copy()
        y[left] = y_old[0] + slope * (x_new[left] - x_old[0])
    if np.any(right):
        slope = (y_old[-1] - y_old[-2]) / (x_old[-1] - x_old[-2])
        y = np.array(y, dtype=float, copy=True)
        y[right] = y_old[-1] + slope * (x_new[right] - x_old[-1])
    return y


def add_or_remove_point(bd: dict, x: float, y: float, *, view: str, thresh: float, manual: bool) -> dict:
    """Port Profile_Sketcher.m Point() for a single click.

    view is 'side' or 'top'. manual True allows deletion when the click is
    within thresh of an existing station. Side: y is Z. Top: y is the
    half-breadth and the opposite side is mirrored (ZL=-ZU or ZU=-ZL) as in
    lines 1109 and 1125. Returns the same dict, updated. NX follows the
    array length.
    """
    x = float(x)
    y = float(y)
    xs = _as_float(bd["X"])
    zu = _as_float(bd["ZU"])
    zl = _as_float(bd["ZL"])
    radius = _as_float(bd["R"]) if "R" in bd else np.zeros(xs.shape, dtype=float)
    orig_x = xs.copy()
    orig_zu = zu.copy()
    orig_zl = zl.copy()
    orig_r = radius.copy()

    x_check = np.flatnonzero(np.abs(xs - x) < thresh)
    if x_check.size > 1:
        # Profile_Sketcher.m lines 1086-1088 both measure distance to ZU.
        dist = (zu[x_check] - y) ** 2 + (xs[x_check] - x) ** 2
        index = int(x_check[int(np.argmin(dist))])
    else:
        index = int(np.argmin(np.abs(xs - x)))
    close_x = abs(float(xs[index] - x))

    upper = abs(float(zu[index] - y)) < abs(float(zl[index] - y))
    if upper:
        close_y = abs(float(zu[index] - y))
        if close_x < thresh and close_y < thresh and manual:
            xs = np.delete(xs, index)
            zu = np.delete(zu, index)
            zl = np.delete(zl, index)
            radius = np.delete(radius, index)
        else:
            at = index if x < float(xs[index]) else index + 1
            xs = np.insert(xs, at, x)
            zu = np.insert(zu, at, y)
            zl = _interp_linear_extrap(xs, orig_x, orig_zl)
            radius = _interp_linear_extrap(xs, orig_x, orig_r)
            if view == "top":
                radius[at] = abs(y)
        if view == "top":
            zl = -zu
    else:
        close_y = abs(float(zl[index] - y))
        if close_x < thresh and close_y < thresh and manual:
            xs = np.delete(xs, index)
            zu = np.delete(zu, index)
            zl = np.delete(zl, index)
            radius = np.delete(radius, index)
        else:
            at = index if x < float(xs[index]) else index + 1
            xs = np.insert(xs, at, x)
            zl = np.insert(zl, at, y)
            zu = _interp_linear_extrap(xs, orig_x, orig_zu)
            radius = _interp_linear_extrap(xs, orig_x, orig_r)
            if view == "top":
                radius[at] = abs(y)
        if view == "top":
            zu = -zl

    bd["X"] = xs
    bd["ZU"] = zu
    bd["ZL"] = zl
    bd["R"] = radius
    bd["NX"] = int(xs.size)
    return bd


def mirror_surface(bd: dict, *, source: str, center: float) -> dict:
    """source 'upper' copies ZU onto ZL about center (ZL = 2*center - ZU).

    source 'lower' copies ZL onto ZU. Profile_Sketcher.m Symmetry().
    """
    center = float(center)
    zu = _as_float(bd["ZU"])
    zl = _as_float(bd["ZL"])
    if source == "upper":
        zl = 2.0 * center - zu
    elif source == "lower":
        zu = 2.0 * center - zl
    else:
        raise ValueError(f"source must be 'upper' or 'lower', got {source!r}")
    bd["ZU"] = zu
    bd["ZL"] = zl
    bd["NX"] = int(_as_float(bd["X"]).size)
    return bd


def _fit_window(x: np.ndarray, z: np.ndarray, start: int, stop: int) -> None:
    stop = min(stop, x.size)
    start = max(start, 0)
    if stop - start < 3:
        return
    coeff = np.polyfit(x[start:stop], z[start:stop], 2)
    z[start:stop] = np.polyval(coeff, x[start:stop])


def smooth_profile(bd: dict, *, flatten: bool) -> dict:
    """Port Smooth() without questdlg.

    flatten True sets ZU and ZL to their means. flatten False runs the local
    quadratic polyfit on windows of 4 or 5 points where the slope jump exceeds
    0.01 (upper) or 0.1 (lower), then swaps any station with ZU<ZL.
    """
    xs = _as_float(bd["X"])
    zu = _as_float(bd["ZU"])
    zl = _as_float(bd["ZL"])
    nx = int(xs.size)
    if flatten:
        zu[:] = float(np.mean(zu)) if zu.size else 0.0
        zl[:] = float(np.mean(zl)) if zl.size else 0.0
    elif nx >= 2:
        dx = xs[1:] - xs[:-1]
        m_upper = (zu[1:] - zu[:-1]) / dx
        m_lower = (zl[1:] - zl[:-1]) / dx
        for i in range(1, nx - 1):
            if i == 1:
                start, stop = i - 1, i + 3
            elif i == nx - 2:
                start, stop = i - 2, i + 2
            else:
                start, stop = i - 2, i + 3
            if abs(float(m_upper[i] - m_upper[i - 1])) > 0.01:
                _fit_window(xs, zu, start, stop)
            if abs(float(m_lower[i] - m_lower[i - 1])) > 0.1:
                _fit_window(xs, zl, start, stop)
            flipped = np.flatnonzero(zu < zl)
            if flipped.size:
                held = zu[flipped].copy()
                zu[flipped] = zl[flipped]
                zl[flipped] = held
    bd["X"] = xs
    bd["ZU"] = zu
    bd["ZL"] = zl
    bd["NX"] = nx
    return bd
