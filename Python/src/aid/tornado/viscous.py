"""Port of Tornado fViscCorr, fStripforce, and spanload7 (fViscCorr2.m).

Viscous strip correction is opt-in: nothing here is called by the default
Tornado coefficient path.
"""

from __future__ import annotations

import numpy as np

from aid.tornado.isa import isa_atmosphere
from aid.tornado.pablo import pablo

__all__ = ["viscous_correction"]

_MAX_ALPHA_ITERS = 40


def viscous_correction(geo: dict, state: dict, lattice: dict, results: dict, ref: dict) -> dict:
    """Strip viscous correction. Port of fViscCorr().

    Returns Striplift, Stripdrag, Stripalpha, upperbl, lowerbl,
    totalliftcoeff, and totalvdragcoeff.
    """
    cl_alpha = 2.0 * np.pi
    atm = isa_atmosphere(float(state["ALT"]))
    re = atm["rho"] * float(state["AS"]) * float(ref["C_mac"]) / atm["mu"]
    p_dyn = (float(state["rho"]) * float(state["AS"]) ** 2) / 2.0

    ny = np.atleast_2d(np.asarray(geo["ny"], dtype=float))
    sym = np.asarray(geo["symetric"], dtype=float).reshape(-1)
    n_wing, n_part = ny.shape
    spp = np.zeros((n_wing, n_part), dtype=float)
    for i in range(n_part):
        spp[:, i] = ny[:, i] * (sym + 1.0)

    lc, lb, sf = _local_chord3(geo, lattice)
    ls = lc * lb
    f0 = _stripforce(geo, results, lattice, state)

    nelem = np.asarray(geo["nelem"], dtype=int).reshape(-1)
    foil = geo.get("foil")

    strip_lift: list[float] = []
    strip_drag: list[float] = []
    strip_alpha: list[float] = []
    upper_bl: list[np.ndarray] = []
    lower_bl: list[np.ndarray] = []

    m = 0
    xa = np.linspace(0.0, 1.0, 101)
    for i in range(n_wing):
        n_elem = int(nelem[i]) if i < nelem.size else 0
        for j in range(n_elem):
            inner, outer = _foil_pair(foil, i, j)
            p_inner = _profilegen(inner)
            p_outer = _profilegen(outer)
            for _k in range(int(spp[i, j])):
                frac = float(sf[m])
                yu = p_inner[:, 1] * (1.0 - frac) + p_outer[:, 1] * frac
                yl = p_inner[:, 2] * (1.0 - frac) + p_outer[:, 2] * frac
                yl = np.array(yl, dtype=float, copy=True)
                yl[-1] = yu[-1]
                n_yu = yu.size
                n_yl = yl.size
                z_file = np.vstack(
                    [
                        np.array([[n_yu, n_yl]], dtype=float),
                        np.column_stack((xa[:n_yu], yu)),
                        np.column_stack((xa[:n_yl], yl)),
                    ]
                )
                alpha = 0.0
                delta_alpha = 10.0
                cd = 0.0
                cl = 0.0
                strip = None
                n_iter = 0
                while abs(delta_alpha) > 0.0001 and n_iter < _MAX_ALPHA_ITERS:
                    n_iter += 1
                    strip = pablo(z_file, alpha, re)
                    cl = float(strip["cl"])
                    area = p_dyn * ls[m]
                    cl_inv = f0[m] / area if area != 0.0 else 0.0
                    delta_cl = cl - cl_inv
                    delta_alpha = -delta_cl / cl_alpha
                    alpha = alpha + delta_alpha
                    cd = float(strip["cd"])
                area = p_dyn * ls[m]
                strip_lift.append(cl * area)
                strip_drag.append(cd * area)
                strip_alpha.append(alpha)
                upper_bl.append(np.asarray(strip["upperbl"], dtype=float))
                lower_bl.append(np.asarray(strip["lowerbl"], dtype=float))
                m += 1

    lifts = np.asarray(strip_lift, dtype=float)
    drags = np.asarray(strip_drag, dtype=float)
    s_ref = float(ref["S_ref"])
    denom = s_ref * p_dyn
    return {
        "Striplift": lifts,
        "Stripdrag": drags,
        "Stripalpha": np.asarray(strip_alpha, dtype=float),
        "upperbl": np.vstack(upper_bl) if upper_bl else np.zeros((0, 6)),
        "lowerbl": np.vstack(lower_bl) if lower_bl else np.zeros((0, 6)),
        "totalliftcoeff": float(np.sum(lifts) / denom) if denom != 0.0 else 0.0,
        "totalvdragcoeff": float(np.sum(drags) / denom) if denom != 0.0 else 0.0,
    }


def _foil_pair(foil, wing: int, part: int):
    if foil is None:
        return None, None
    try:
        pair = foil[wing][part]
    except (IndexError, TypeError, KeyError):
        return None, None
    if isinstance(pair, (list, tuple)) and len(pair) >= 2:
        return pair[0], pair[1]
    return pair, pair


def _profilegen(foil) -> np.ndarray:
    """NACA 4-digit section, stored coordinates, or a 12% ellipse.

    The MATLAB case-2 directory loader is not ported.
    """
    if _is_missing_foil(foil):
        return _ellipse12()
    naca = _as_naca(foil)
    if naca is not None:
        return _naca4_profile(naca)
    if isinstance(foil, str):
        return _ellipse12()
    arr = np.asarray(foil, dtype=float)
    if arr.ndim == 2 and arr.shape[0] >= 4 and arr.shape[1] >= 2:
        return _coords_to_profile(arr)
    return _ellipse12()


def _is_missing_foil(foil) -> bool:
    if foil is None:
        return True
    if isinstance(foil, str) and not foil.strip():
        return True
    if isinstance(foil, np.ndarray) and foil.size == 0:
        return True
    return False


def _as_naca(foil):
    if isinstance(foil, (bool, np.bool_)):
        return None
    if isinstance(foil, (int, np.integer)):
        return int(foil)
    if isinstance(foil, (float, np.floating)):
        val = float(foil)
        if val.is_integer():
            return int(val)
        return None
    if isinstance(foil, str) and foil.strip().isdigit():
        return int(foil.strip())
    return None


def _ellipse12() -> np.ndarray:
    """12% ellipse of chord 1, sampled on the MATLAB 0:0.01:1 grid."""
    xa = np.linspace(0.0, 1.0, 101)
    y = 0.06 * np.sqrt(np.maximum(0.0, 1.0 - ((xa - 0.5) / 0.5) ** 2))
    return np.column_stack((xa, y, -y))


def _naca4_profile(foil_val: int) -> np.ndarray:
    """Port of profilegen case 1 (NACA 4-digit)."""
    m_code = int(foil_val) // 1000
    lemma = int(foil_val) - m_code * 1000
    p_code = lemma // 100
    t = (int(foil_val) - m_code * 1000 - p_code * 100) / 100.0
    p = p_code / 10.0
    m = m_code / 100.0
    xa = np.linspace(0.0, 1.0, 101)
    camber = np.zeros_like(xa)
    for i, x in enumerate(xa):
        if p > 0.0 and x < p:
            camber[i] = (m / (p**2)) * x * (2.0 * p - x)
        else:
            denom = (1.0 - p) ** 2
            camber[i] = 0.0 if denom == 0.0 else (m / denom) * ((1.0 - 2.0 * p) + 2.0 * p * x - x**2)
    angle = np.arctan(np.diff(camber) / np.diff(xa))
    angle = np.concatenate([angle, angle[-1:]])
    yt = t * 5.0 * (
        0.2969 * np.sqrt(np.maximum(xa, 0.0))
        - 0.1260 * xa
        - 0.3516 * xa**2
        + 0.2843 * xa**3
        - 0.1015 * xa**4
    )
    xu = xa - yt * np.sin(angle)
    yu = camber + yt * np.cos(angle)
    xl = xa + yt * np.sin(angle)
    yl = camber - yt * np.cos(angle)
    return np.column_stack((xa, _interp_sorted(xa, xu, yu), _interp_sorted(xa, xl, yl)))


def _coords_to_profile(data: np.ndarray) -> np.ndarray:
    xa = np.linspace(0.0, 1.0, 101)
    data = np.asarray(data, dtype=float)
    if data.shape[1] >= 3:
        xu, yu = data[:, 0], data[:, 1]
        xl, yl = data[:, 0], data[:, 2]
    else:
        x = data[:, 0]
        ile = int(np.argmin(x))
        closed = abs(float(x[0] - x[-1])) <= 1e-6 and ile not in (0, x.size - 1)
        # geo["foil"] arrays are a closed loop: lower TE→LE, then upper LE→TE.
        if closed:
            lower = data[: ile + 1][::-1]
            upper = data[ile:]
        elif x.size % 2 == 0:
            n = x.size // 2
            lower = data[:n]
            upper = data[n:]
        else:
            lower = data[: ile + 1][::-1]
            upper = data[ile:]
        xu, yu = upper[:, 0], upper[:, 1]
        xl, yl = lower[:, 0], lower[:, 1]
    return np.column_stack((xa, _interp_sorted(xa, xu, yu), _interp_sorted(xa, xl, yl)))


def _interp_sorted(xq: np.ndarray, x: np.ndarray, y: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=float).ravel()
    y = np.asarray(y, dtype=float).ravel()
    n = min(x.size, y.size)
    x, y = x[:n], y[:n]
    order = np.argsort(x)
    x, y = x[order], y[order]
    uniq, idx = np.unique(x, return_index=True)
    y = y[idx]
    if uniq.size == 1:
        return np.full(np.asarray(xq).shape, y[0], dtype=float)
    return np.interp(xq, uniq, y)


def _local_chord3(geo: dict, lattice: dict):
    """Local chord, strip width, and span fraction. Port of fLocal_chord3()."""
    ny = np.atleast_2d(np.asarray(geo["ny"], dtype=float))
    sym = np.asarray(geo["symetric"], dtype=float).reshape(-1)
    nx = np.atleast_2d(np.asarray(geo["nx"], dtype=float))
    fnx = np.atleast_2d(np.asarray(geo["fnx"], dtype=float))
    bgeo = np.atleast_2d(np.asarray(geo["b"], dtype=float))
    indx1, indx2 = bgeo.shape
    spp = np.column_stack([ny[:, i] * (sym + 1.0) for i in range(ny.shape[1])])

    xyz = np.asarray(lattice["XYZ"], dtype=float)
    panel_chords = (
        np.linalg.norm(xyz[:, 0, :] - xyz[:, 3, :], axis=1)
        + np.linalg.norm(xyz[:, 1, :] - xyz[:, 2, :], axis=1)
    ) / 2.0

    lc_parts: list[np.ndarray] = []
    for i in range(indx1):
        for j in range(indx2):
            lemma: list[float] = []
            chordwise = int(nx[i, j] + fnx[i, j])
            for _k in range(int(ny[i, j])):
                if ny[i, j] != 0 and chordwise > 0:
                    lemma.append(float(np.sum(panel_chords[:chordwise])))
                    panel_chords = panel_chords[chordwise:]
            lemma_arr = np.asarray(lemma, dtype=float)
            if sym[i] == 1:
                lc_parts.append(lemma_arr)
                lc_parts.append(lemma_arr)
                skip = chordwise * int(ny[i, j])
                panel_chords = panel_chords[skip:]
            elif lemma_arr.size:
                lc_parts.append(lemma_arr)
    lc = np.concatenate([part for part in lc_parts if part.size]) if lc_parts else np.zeros(0)

    span_vec = xyz[:, 0, :] - xyz[:, 1, :]
    panel_span = np.sqrt(span_vec[:, 1] ** 2 + span_vec[:, 2] ** 2)
    knx = nx + fnx
    lb_list: list[float] = []
    for i in range(indx1):
        for j in range(indx2):
            step = int(knx[i, j])
            for _k in range(int(spp[i, j])):
                lb_list.append(float(panel_span[0]) if panel_span.size else 0.0)
                if step > 0:
                    panel_span = panel_span[step:]
    lb = np.asarray(lb_list, dtype=float)

    colloc = np.asarray(lattice["COLLOC"], dtype=float)
    panel_mid = np.sqrt(np.sum(colloc[:, 1:3] ** 2, axis=1))
    panel_min = np.linalg.norm(xyz[:, 0, :], axis=1)
    panel_max = np.linalg.norm(xyz[:, 1, :], axis=1)
    sf_parts: list[np.ndarray] = []
    for i in range(indx1):
        for j in range(indx2):
            step = int(knx[i, j])
            mids: list[float] = []
            maxes: list[float] = []
            for _k in range(int(spp[i, j])):
                mids.append(float(panel_mid[0]) if panel_mid.size else 0.0)
                if panel_min.size and panel_max.size:
                    maxes.append(float(max(panel_min[0], panel_max[0])))
                else:
                    maxes.append(0.0)
                if step > 0:
                    panel_mid = panel_mid[step:]
                    panel_min = panel_min[step:]
                    panel_max = panel_max[step:]
            mid_arr = np.asarray(mids, dtype=float)
            max_arr = np.asarray(maxes, dtype=float)
            if mid_arr.size == 0:
                continue
            denom = float(np.max(max_arr)) if max_arr.size else 0.0
            sf_parts.append(mid_arr / denom if denom != 0.0 else np.zeros_like(mid_arr))
    sf = np.concatenate(sf_parts) if sf_parts else np.zeros(0)
    return lc, lb, sf


def _stripforce(geo: dict, results: dict, lattice: dict, state: dict) -> np.ndarray:
    """Lift force on each strip. Port of fStripforce()."""
    il = _spanload7(results, geo, lattice, state)
    nx = np.atleast_2d(np.asarray(geo["nx"], dtype=float))
    fnx = np.atleast_2d(np.asarray(geo["fnx"], dtype=float))
    ny = np.atleast_2d(np.asarray(geo["ny"], dtype=float))
    sym = np.asarray(geo["symetric"], dtype=float).reshape(-1)
    cnx = nx + fnx
    n_wing_rows, n_part = nx.shape
    nwing = int(geo["nwing"])
    cny = np.zeros((nwing, n_part), dtype=float)
    for i in range(nwing):
        cny[i, :] = ny[i, :] * (sym[i] + 1.0)

    forces: list[float] = []
    for i in range(n_wing_rows):
        for j in range(n_part):
            step = int(cnx[i, j])
            index1 = 0
            index2 = step
            n_strips = int(cny[i, j]) if i < nwing else 0
            for _k in range(n_strips):
                forces.append(float(np.sum(il[index1:index2])))
                index1 += step
                index2 += step
    return np.asarray(forces, dtype=float)


def _spanload7(results: dict, geo: dict, lattice: dict, state: dict) -> np.ndarray:
    """Panel lift in wind axes. Port of spanload7() in fViscCorr2.m.

    Solver output stores F as (npanel, nderiv, 3). After coeff_create the
    steady slice is (npanel, 3). Both layouts are accepted; derivatives
    other than the steady solution are ignored, matching results.F(:,1,:).
    """
    forces = np.asarray(results["F"], dtype=float)
    if forces.ndim == 3:
        forces = forces[:, 0, :]
    alpha = float(state["alpha"])
    betha = float(state["betha"])
    b2w = np.array(
        [
            [
                np.cos(betha) * np.cos(alpha),
                -np.sin(betha),
                np.cos(betha) * np.sin(alpha),
            ],
            [
                np.cos(alpha) * np.sin(betha),
                np.cos(betha),
                np.sin(betha) * np.sin(alpha),
            ],
            [-np.sin(alpha), 0.0, np.cos(alpha)],
        ],
        dtype=float,
    )
    # starty/startz offsets are built in the MATLAB function and not used
    # for the lift returned to fViscCorr.
    _ = geo
    _ = lattice
    lift = np.empty(forces.shape[0], dtype=float)
    for i in range(forces.shape[0]):
        wind = b2w @ forces[i, :3]
        lift[i] = wind[2]
    return lift
