"""Tornado spanwise lift distribution — port of spanload6 + AID.m lift overlay."""

from __future__ import annotations

import numpy as np

from aid.aircraft import Aircraft
from aid.stability import aircraft_stability

__all__ = ["tornado_spanwise"]

_N_M_TO_LBFT = 1.0 / (4.44822 * 3.28084**2)


def _last(val) -> float:
    return float(np.asarray(val, dtype=float).reshape(-1)[-1])


def _spanload(coeffs: dict, lattice: dict, geo: dict) -> tuple[np.ndarray, np.ndarray]:
    """Port of spanload6() in coeff_create3.m — ForcePerMeter and ystation per wing."""
    f = np.asarray(coeffs["F"], dtype=float)
    normals = np.asarray(lattice["N"], dtype=float)
    xyz = np.asarray(lattice["XYZ"], dtype=float)

    force_magn = -np.einsum("ij,ij->i", f, normals)

    a1 = xyz[:, 0, :] - xyz[:, 1, :]
    p_span = np.sqrt(a1[:, 1] ** 2 + a1[:, 2] ** 2)
    p_mid = (xyz[:, 0, :] + xyz[:, 1, :]) / 2.0

    nx = np.asarray(geo["nx"], dtype=float)
    fnx = np.asarray(geo["fnx"], dtype=float)
    ny = np.asarray(geo["ny"], dtype=float)
    sym = np.asarray(geo["symetric"], dtype=float)
    b = np.asarray(geo["b"], dtype=float)
    starty = np.asarray(geo["starty"], dtype=float)
    startz = np.asarray(geo["startz"], dtype=float)

    knx = nx + fnx
    noofpanels = np.sum(knx * ny, axis=1) * (sym + 1)

    corry_parts = []
    corrz_parts = []
    for i in range(b.shape[0]):
        n_pan = int(noofpanels[i])
        corry_parts.append(np.full(n_pan, starty[i, 0]))
        corrz_parts.append(np.full(n_pan, startz[i, 0]))
    corry = np.concatenate(corry_parts)
    corrz = np.concatenate(corrz_parts)

    p_mid_r = np.sqrt((p_mid[:, 1] - corry) ** 2 + (p_mid[:, 2] - corrz) ** 2)

    fpm = force_magn / p_span

    p_blocks: list[np.ndarray] = []
    p2_blocks: list[np.ndarray] = []
    for i in range(b.shape[0]):
        for j in range(b.shape[1]):
            n_y = int(ny[i, j])
            if n_y == 0:
                continue
            a = np.full(n_y, knx[i, j])
            c = np.ones(n_y)
            if sym[i]:
                a = np.concatenate([a, a])
                c = np.concatenate([c, -c])
            p_blocks.append(a)
            p2_blocks.append(c)
    p = np.concatenate(p_blocks)
    p2 = np.concatenate(p2_blocks)

    sf_list: list[float] = []
    r_list: list[float] = []
    fpm_work = fpm
    p_mid_r_work = p_mid_r
    for n_panels in p.astype(int):
        sf_list.append(float(np.sum(fpm_work[:n_panels])))
        fpm_work = fpm_work[n_panels:]
        r_list.append(float(np.sum(p_mid_r_work[:n_panels]) / n_panels))
        p_mid_r_work = p_mid_r_work[n_panels:]

    sf = np.asarray(sf_list, dtype=float)
    ystation = np.asarray(r_list, dtype=float) * p2

    kny = np.sum(ny, axis=1).astype(int) * (sym + 1).astype(int)
    nwing = int(geo["nwing"])
    ys = np.zeros((int(np.max(kny)), nwing), dtype=float)
    fpm_out = np.zeros((int(np.max(kny)), nwing), dtype=float)

    y_work = ystation
    sf_work = sf
    for i in range(nwing):
        n = int(kny[i])
        sf2 = sf_work[:n]
        ystat, order = np.sort(y_work[:n]), np.argsort(y_work[:n])
        ys[:n, i] = ystat
        fpm_out[:n, i] = sf2[order]
        y_work = y_work[n:]
        sf_work = sf_work[n:]

    return ys, fpm_out


def _spanwise_dy(y1: np.ndarray, semi_span: float) -> np.ndarray:
    """Strip widths from AID.m ~1777–1782."""
    y0 = np.empty(y1.size + 1, dtype=float)
    y0[0] = -abs(semi_span)
    dy = np.zeros(y1.size, dtype=float)
    for i in range(y1.size):
        dy[i] = y1[i] - y0[i]
        y0[i + 1] = y1[i] + dy[i]
    return 2.0 * dy


def tornado_spanwise(
    coeffs: dict,
    lattice: dict,
    geo: dict,
    state: dict,
    ac: Aircraft,
) -> list[dict]:
    """Spanwise y, dy, Cl per wing — matches AID.m 1769–1785."""
    st = aircraft_stability(ac)
    q = float(st["Q"])
    s_ref = _last(ac.WG["S"])

    ys, fpm = _spanload(coeffs, lattice, geo)

    b = np.asarray(geo["b"], dtype=float)
    nwing = int(geo["nwing"])
    out: list[dict] = []
    for k in range(nwing):
        y_col = ys[:, k]
        fpm_col = fpm[:, k]
        mask = y_col != 0
        y1 = y_col[mask]
        l_lbft = fpm_col[mask] * _N_M_TO_LBFT
        cl = l_lbft / (s_ref * q)
        semi = float(np.sum(b[k, :]))
        out.append({"y": y1, "dy": _spanwise_dy(y1, semi), "Cl": cl})
    return out
