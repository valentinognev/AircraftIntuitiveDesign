"""Prandtl lifting line with Glauert Fourier method.

Port of ``Matlab/fsroot/code/Lifting_Line.m``.
"""

from __future__ import annotations

import math

import numpy as np

from aid.aircraft import Aircraft
from aid.atmosphere import atmosphere
from aid.stability import aircraft_stability


def _last(val) -> float:
    return float(np.asarray(val, dtype=float).reshape(-1)[-1])


def _interp1(x: np.ndarray, xp: np.ndarray, fp: np.ndarray) -> np.ndarray:
    """MATLAB ``interp1``-compatible 1-D linear interpolation."""
    xp = np.asarray(xp, dtype=float).reshape(-1)
    fp = np.asarray(fp, dtype=float).reshape(-1)
    if xp.size > 1 and xp[0] > xp[-1]:
        order = np.argsort(xp)
        xp = xp[order]
        fp = fp[order]
    return np.interp(x, xp, fp)


def lifting_line(ac: Aircraft, y: np.ndarray, c: np.ndarray, twist: np.ndarray) -> dict:
    """Spanwise lift distribution for a planform semi-span input (right wing)."""
    pt = ac.WG
    wg = ac.WG
    bd = ac.BD
    aero = ac.AERO

    y = np.asarray(y, dtype=float).reshape(-1)
    c = np.asarray(c, dtype=float).reshape(-1)
    twist = np.asarray(twist, dtype=float).reshape(-1)

    y0 = float(y[-1])
    n_pts = y.size

    st = aircraft_stability(ac)
    alpha = st["alpha"] * math.pi / 180.0
    alpha0l = float(np.asarray(pt.get("alpha0L", 0), dtype=float).reshape(-1)[0])
    inc = float(pt.get("i", 0) or 0)
    alpha_0 = (alpha0l - inc - twist) * math.pi / 180.0

    mach = float(np.asarray(aero["MACH"]).reshape(-1)[0])
    alt = float(np.asarray(aero["ALT"]).reshape(-1)[0])
    v_inf = mach * atmosphere(alt)["a"]

    n = np.arange(1, 2 * n_pts, 2)
    theta = np.arange(1, n_pts + 1) / n_pts * math.pi / 2.0
    y1 = -np.cos(theta) * y0

    chrdbp = float(pt.get("CHRDBP", 0) or 0)
    sspnop = float(pt.get("SSPNOP", 0) or 0)
    if chrdbp and sspnop:
        _, index = np.unique(y, return_index=True)
        y = -y[index]
        theta = theta[index]
        y1 = y1[index]
        n_pts = n_pts - 1
        n = n[index]
        alpha_0 = _interp1(y1, y, alpha_0[index])
        c = _interp1(y1, y, c[index])
    else:
        y = -y
        alpha_0 = _interp1(y1, y, alpha_0)
        c = _interp1(y1, y, c)

    y2 = float(y[-1])
    dy = np.zeros(y1.size)
    y2_arr = np.empty(y1.size + 1)
    y2_arr[0] = y2
    for i in range(y1.size):
        dy[i] = y1[i] - y2_arr[i]
        y2_arr[i + 1] = y1[i] + dy[i]
    dy = 2 * dy

    sin_theta = np.sin(theta)
    sin_theta_n = np.sin(theta[:, None] * n[None, :])
    l_vec = math.pi * c / (4 * y0) * (alpha - alpha_0) * sin_theta
    r_mat = sin_theta_n * (math.pi * c[:, None] * n[None, :] / (4 * y0) + sin_theta[:, None])
    a_ij = np.linalg.solve(r_mat, l_vec)

    gamma = 4 * v_inf * y0 * sin_theta_n @ a_ij

    delta = float(np.sum(n[1:] * (a_ij[1:] / a_ij[0]) ** 2))
    e0 = 1 / (1 + delta) - 0.01
    b_span = float(wg.get("b", 0) or 0)
    r_max = float(np.max(np.asarray(bd.get("R", [0]), dtype=float)))
    e = e0 * (1 - (r_max / b_span) ** 2)
    ar = _last(wg["AR"])
    k = 1 / (math.pi * e * ar)
    cl = a_ij[0] * ar * math.pi

    y_full = np.concatenate([y1, -np.flip(y1[:-1])])
    dy_full = np.concatenate([dy, np.flip(dy[:-1])])
    gamma_full = np.concatenate([gamma, np.flip(gamma[:-1])])
    gamma_ideal = 4 * v_inf * y0 * a_ij[0] * sin_theta
    gamma_ideal_full = np.concatenate([gamma_ideal, np.flip(gamma_ideal[:-1])])

    s_ref = _last(wg["S"])
    cl_dist = 2 * gamma_full / (v_inf * s_ref)
    cl_ideal = 2 * gamma_ideal_full / (v_inf * s_ref)
    scale = float(np.max(np.abs(cl_ideal)))

    return {
        "y": y_full,
        "dy": dy_full,
        "Cl": cl_dist,
        "Cl_ideal": cl_ideal,
        "scale": scale,
        "e": e,
        "K": k,
        "CL": float(cl),
    }
