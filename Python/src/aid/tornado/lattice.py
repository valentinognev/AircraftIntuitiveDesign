"""Port of Tornado fLattice_setup2.m (geosetup15, wakesetup2, setrudder3, geometry19)."""

from __future__ import annotations

import math

import numpy as np
from scipy.interpolate import PchipInterpolator

__all__ = ["lattice_setup", "flap_indices"]


def flap_indices(geo: dict) -> tuple[np.ndarray, np.ndarray]:
    """Return (division, wing) indices in MATLAB ``find(geo.flapped')`` order."""
    flapped_t = np.asarray(geo["flapped"], dtype=float).T
    linear = np.flatnonzero(flapped_t.ravel(order="F"))
    n_div = flapped_t.shape[0]
    i_idx = linear % n_div
    k_idx = linear // n_div
    return i_idx, k_idx


def _config(key: str):
    if key in ("S_ref", "b_ref", "C_mac", "mac_pos", "infinity"):
        return None
    if key == "near":
        return 1e-7
    if key == "verbose":
        return 1
    if key == "delta":
        return 0.0001
    return 0


def _trot3(hinge: np.ndarray, p: np.ndarray, alpha: float) -> np.ndarray:
    a, b, c = float(hinge[0]), float(hinge[1]), float(hinge[2])
    rho = math.sqrt(a * a + b * b)
    r = math.sqrt(a * a + b * b + c * c)
    if r == 0:
        cost, sint = 0.0, 1.0
    else:
        cost, sint = c / r, rho / r
    if rho == 0:
        cosf, sinf = 0.0, 1.0
    else:
        cosf, sinf = a / rho, b / rho
    cosa, sina = math.cos(alpha), math.sin(alpha)
    rzf = np.array([[cosf, -sinf, 0.0], [sinf, cosf, 0.0], [0.0, 0.0, 1.0]])
    ryt = np.array([[cost, 0.0, sint], [0.0, 1.0, 0.0], [-sint, 0.0, cost]])
    rza = np.array([[cosa, -sina, 0.0], [sina, cosa, 0.0], [0.0, 0.0, 1.0]])
    rymt = np.array([[cost, 0.0, -sint], [0.0, 1.0, 0.0], [sint, 0.0, cost]])
    rzmf = np.array([[cosf, sinf, 0.0], [-sinf, cosf, 0.0], [0.0, 0.0, 1.0]])
    p_mat = rzf @ ryt @ rza @ rymt @ rzmf
    return p_mat @ np.asarray(p, dtype=float).reshape(3)


def _slope2(foil) -> tuple[np.ndarray, np.ndarray]:
    if isinstance(foil, np.ndarray) and foil.ndim >= 2:
        data = np.asarray(foil, dtype=float)
        nx = int(math.ceil(data.shape[0] / 2))
        if data.shape[0] % 2:
            data = np.insert(data, nx, data[nx - 1], axis=0)
        x = np.flip(data[:nx, 0])
        zu = data[-nx:, 1]
        zl = np.flip(data[:nx, 1])
        c = 0.5 * (zl + zu)
        xa_pts: list[float] = []
        angle_pts: list[float] = []
        for i in range(nx - 1):
            dx = float(x[i + 1] - x[i])
            if dx == 0.0:
                continue
            ang = math.atan((c[i + 1] - c[i]) / dx)
            if not math.isfinite(ang):
                ang = 0.0
            xa_pts.append(0.5 * (x[i] + x[i + 1]))
            angle_pts.append(ang)
        if len(xa_pts) < 2:
            return np.array([0.0, 1.0]), np.array([0.0, 0.0])
        return np.asarray(xa_pts, dtype=float), np.asarray(angle_pts, dtype=float)

    foil_str = str(foil).strip()
    try:
        foil_num = float(foil_str)
        foil_val = int(foil_num) if foil_num == int(foil_num) else foil_num
    except ValueError:
        foil_val = None

    if foil_val is not None and str(foil_val).replace(".", "", 1).isdigit():
        m = foil_val // 1000
        lemma = foil_val - m * 1000
        p = lemma // 100
        p = p / 10.0
        m = m / 100.0
        xa = np.arange(0.0, 1.01, 0.01)
        a = np.empty_like(xa)
        for i, x in enumerate(xa):
            if x < p:
                a[i] = (2 * m / (p * p)) * (p - x)
            else:
                a[i] = 2 * m / ((1 - p) ** 2) * (p - x)
        return xa, np.arctan(a)

    xa = np.arange(0.0, 1.01, 0.01)
    return xa, np.zeros_like(xa)


def _drawhinge(wx, wy, wz, fc) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    if fc is None or (isinstance(fc, float) and fc == 0) or (
        isinstance(fc, (list, np.ndarray)) and len(fc) == 0
    ):
        return np.array([]), np.array([]), np.array([])
    wx, wy, wz = np.asarray(wx), np.asarray(wy), np.asarray(wz)
    fc = float(fc)
    r1, r2 = [], []
    for i in (0, 1):
        a = np.array([wx[i], wy[i], wz[i]], dtype=float)
        b = np.array([wx[3 - i], wy[3 - i], wz[3 - i]], dtype=float)
        c = b - a
        l = np.linalg.norm(c)
        c_hat = c / l if l else c
        d = (1 - fc) * l * c_hat
        r = a + d
        r1.append(r)
        r2.append(r)
    r1 = np.asarray(r1)
    return r1[:, 0], r1[:, 1], r1[:, 2]


def _tmesh2(wx, wy, wz, nx: int, ny: int, meshtype: int) -> np.ndarray:
    a1 = np.array([wx[0], wy[0], wz[0]], dtype=float)
    b1 = np.array([wx[1], wy[1], wz[1]], dtype=float)
    b2 = np.array([wx[2], wy[2], wz[2]], dtype=float)
    a2 = np.array([wx[3], wy[3], wz[3]], dtype=float)

    percent_cy = np.arange(ny + 1, dtype=float) / ny
    percent_cx = np.arange(nx + 1, dtype=float) / nx

    mt = int(meshtype)
    if mt == 2:
        percent_cy = np.cos(np.pi / 2 * (1 - percent_cy))
    elif mt == 3:
        percent_cx = (np.cos(np.pi * (1 - percent_cx)) + 1) / 2
        percent_cy = np.cos(np.pi / 2 * (1 - percent_cy))
    elif mt == 4:
        percent_cx = (np.cos(np.pi * (1 - percent_cx)) + 1) / 2
        percent_cy = (np.cos(np.pi * (1 - percent_cy)) + 1) / 2
    elif mt == 5:
        percent_cy = (np.cos(np.pi * (1 - percent_cy)) + 1) / 2
    elif mt == 6:
        percent_cx = (np.cos(np.pi * (1 - percent_cx)) + 1) / 2
    elif mt == 7:
        percent_cx = 2.2 * percent_cx**3 - 3.3 * percent_cx**2 + 2.1 * percent_cx
        percent_cy = 2.2 * percent_cy**3 - 3.3 * percent_cy**2 + 2.1 * percent_cy

    a_grid = np.zeros((ny + 1, nx + 1, 3), dtype=float)
    for i in range(ny + 1):
        perc_y = percent_cy[i]
        c1 = b1 - a1
        l1 = np.linalg.norm(c1)
        c1_hat = c1 / l1 if l1 else c1
        d1 = perc_y * l1 * c1_hat
        m = a1 + d1
        c2 = b2 - a2
        d2 = perc_y * c2
        n = a2 + d2
        for j in range(nx + 1):
            perc_x = percent_cx[j]
            c3 = n - m
            d3 = perc_x * c3
            a_grid[i, j, :] = m + d3

    panel = np.zeros((ny * nx, 5, 3), dtype=float)
    t = 0
    for i in range(ny):
        for j in range(nx):
            panel[t, 0] = a_grid[i, j]
            panel[t, 1] = a_grid[i + 1, j]
            panel[t, 2] = a_grid[i + 1, j + 1]
            panel[t, 3] = a_grid[i, j + 1]
            panel[t, 4] = a_grid[i, j]
            t += 1
    return panel


def _normals4(colloc: np.ndarray, vortex: np.ndarray, c_slope: np.ndarray) -> np.ndarray:
    step = colloc.shape[0]
    _, e, _ = vortex.shape
    a = e // 2
    b = a + 1
    normals = []
    for t in range(step):
        alpha = float(c_slope[t])
        ra = vortex[t, a - 1, :]
        rb = vortex[t, b - 1, :]
        rc = colloc[t, :]
        r0 = rb - ra
        r0[0] = 0.0
        r1 = rc - ra
        r2 = rc - rb
        n = np.cross(r1, r2)
        nl = math.sqrt(float(np.sum(n**2)))
        r_vec = n / nl if nl else n
        r2_rot = _trot3(r0, r_vec, -alpha)
        normals.append(r2_rot)
    return np.asarray(normals, dtype=float)


def _pchip_interp(x_src: np.ndarray, y_src: np.ndarray, xq: float) -> float:
    x = np.asarray(x_src, dtype=float).ravel()
    y = np.asarray(y_src, dtype=float).ravel()
    n = min(x.size, y.size)
    x, y = x[:n], y[:n]
    ok = np.isfinite(x) & np.isfinite(y)
    x, y = x[ok], y[ok]
    if y.size == 0:
        return 0.0
    x, idx = np.unique(x, return_index=True)
    y = y[idx]
    if x.size < 2:
        return float(y[0])
    interp = PchipInterpolator(x, y, extrapolate=True)
    val = float(interp(xq))
    return val if math.isfinite(val) else 0.0


def _geometry19(
    fnx: int,
    ny: int,
    nx: int,
    fsym: float,
    fc: float,
    flapped: float,
    tw,
    foil,
    t: float,
    sw: float,
    c: float,
    dihed: float,
    b: float,
    sym: float,
    sx: float,
    sy: float,
    sz: float,
    meshtype: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    fnx = int(fnx)
    ny = int(ny)
    nx = int(nx)
    flapped = int(flapped)
    sym = int(sym)
    meshtype = int(meshtype)

    tw_arr = np.asarray(tw, dtype=float).reshape(-1)
    tw_in = float(tw_arr[0]) if tw_arr.size else 0.0
    tw_out = float(tw_arr[1]) if tw_arr.size > 1 else tw_in

    ox, oy, oz = sx, sy, sz
    neqns = (nx + fnx) * ny

    dx = c * (1 - fc) / nx if nx else 0.0
    fdx = c * fc / fnx if flapped == 1 and fnx else 0.0
    a1 = np.ones(nx) * dx
    a2 = np.ones(fnx) * fdx if fnx else np.array([])
    dr = np.concatenate([a1, a2]) if fnx else a1

    lem = np.array([0.25 * c, 0.25 * t * c, -0.75 * t * c, -0.75 * c])
    tw_lem = np.array([tw_in, tw_out, tw_out, tw_in])
    dx_arr = (1 - np.cos(tw_lem)) * np.cos(sw) * lem
    dy_arr = -np.sin(tw_lem) * np.sin(dihed) * np.cos(sw) * lem
    dz_arr = np.sin(tw_lem) * np.cos(dihed) * lem

    wingx = np.array([0, 0.25 * c + b * math.tan(sw) - 0.25 * t * c,
                      0.25 * c + b * math.tan(sw) + 0.75 * t * c, c]) + ox + dx_arr
    wingy = np.array([0, b * math.cos(dihed), b * math.cos(dihed), 0]) + oy + dy_arr
    wingz = np.array([0, b * math.sin(dihed), b * math.sin(dihed), 0]) + oz + dz_arr

    foil_pair = foil
    if isinstance(foil, (list, tuple)):
        foil_in, foil_out = foil[0], foil[1]
    else:
        foil_in = foil_out = foil

    if flapped == 1:
        flapx, flapy, flapz = _drawhinge(wingx, wingy, wingz, fc)
        tempx = wingx[2:4].copy()
        tempy = wingy[2:4].copy()
        tempz = wingz[2:4].copy()
        wingx[2:4] = np.flip(flapx[:2])
        wingy[2:4] = np.flip(flapy[:2])
        wingz[2:4] = np.flip(flapz[:2])
        flapx_full = np.array([flapx[0], flapx[1], tempx[0], tempx[1]])
        flapy_full = np.array([flapy[0], flapy[1], tempy[0], tempy[1]])
        flapz_full = np.array([flapz[0], flapz[1], tempz[0], tempz[1]])
        p = _tmesh2(wingx, wingy, wingz, nx, ny, meshtype)
        q = _tmesh2(flapx_full, flapy_full, flapz_full, fnx, ny, meshtype)
        chunks = []
        for i in range(ny):
            c1 = list(range(nx * i, nx * (i + 1)))
            c2 = list(range(fnx * i, fnx * (i + 1)))
            chunks.extend([p[j] for j in c1])
            chunks.extend([q[j] for j in c2])
        r = np.asarray(chunks, dtype=float)
        px, py, pz = r[:, :, 0], r[:, :, 1], r[:, :, 2]
    else:
        p = _tmesh2(wingx, wingy, wingz, nx, ny, meshtype)
        px, py, pz = p[:, :, 0], p[:, :, 1], p[:, :, 2]

    nx_total = nx + fnx
    x_1_s, lemma_1_s_tot = _slope2(foil_in)
    x_2_s, lemma_2_s_tot = _slope2(foil_out)

    neqns = nx_total * ny
    n_panels_total = neqns * (1 + sym)
    hp = np.zeros((n_panels_total, 2, 3))
    tep1 = np.zeros((n_panels_total, 2, 3))
    c1_list: list[np.ndarray] = []
    v1 = np.zeros((n_panels_total, 2, 3))
    lemma_1_s = np.zeros(neqns)
    lemma_2_s = np.zeros(neqns)
    s_slopes = np.zeros(neqns)

    t_idx = 0
    for j in range(ny):
        for i in range(nx_total):
            t_idx += 1
            idx = t_idx - 1
            px_row = px[idx]
            py_row = py[idx]
            pz_row = pz[idx]

            if i == (nx_total - fnx - 1):
                for s in range(nx_total - fnx):
                    src = idx - s
                    hp[src] = np.array([[px_row[3], py_row[3], pz_row[3]],
                                        [px_row[2], py_row[2], pz_row[2]]])
                    if sym == 1:
                        dst = src + neqns
                        hp[dst] = np.array([[px_row[2], -py_row[2], pz_row[2]],
                                            [px_row[3], -py_row[3], pz_row[3]]])

            if i == (nx_total - 1):
                for s in range(nx_total):
                    src = idx - s
                    tep1[src] = np.array([[px_row[3], py_row[3], pz_row[3]],
                                          [px_row[2], py_row[2], pz_row[2]]])
                    if sym == 1:
                        dst = src + neqns
                        tep1[dst] = np.array([[px_row[2], -py_row[2], pz_row[2]],
                                              [px_row[3], -py_row[3], pz_row[3]]])
                    for u in range(fnx):
                        h_src = idx - u
                        hp[h_src] = np.array([[px_row[3], py_row[3], pz_row[3]],
                                              [px_row[2], py_row[2], pz_row[2]]])
                        if sym == 1:
                            h_dst = h_src + neqns
                            hp[h_dst] = np.array([[px_row[2], -py_row[2], pz_row[2]],
                                                  [px_row[3], -py_row[3], pz_row[3]]])

            mx = np.sum(px_row[:4]) / 4
            my = np.sum(py_row[:4]) / 4
            mz = np.sum(pz_row[:4]) / 4
            bkx = (px_row[2] + px_row[3]) / 2
            c_row = np.array([(mx + bkx) / 2, (py_row[2] + py_row[3] + 2 * my) / 4,
                              (pz_row[2] + pz_row[3] + 2 * mz) / 4])
            c1_list.append(c_row)

            ax = ((px_row[0] + px_row[3]) / 2 + px_row[0]) * 0.5
            ay = (3 * py_row[0] + py_row[3]) / 4
            az = (3 * pz_row[0] + pz_row[3]) / 4
            bx = ((px_row[1] + px_row[2]) / 2 + px_row[1]) * 0.5
            by = (3 * py_row[1] + py_row[2]) / 4
            bz = (3 * pz_row[1] + pz_row[2]) / 4

            v1[idx, 0] = [ax, ay, az]
            v1[idx, 1] = [bx, by, bz]

            if dr.size:
                a3 = (float(np.sum(dr[: i + 1])) - 0.25 * dr[i]) / c
            else:
                a3 = 0.0
            lemma_1_s[idx] = _pchip_interp(x_1_s, lemma_1_s_tot, a3)
            lemma_2_s[idx] = _pchip_interp(x_2_s, lemma_2_s_tot, a3)
            s_slopes[idx] = (lemma_1_s[idx] * (ny - j) + lemma_2_s[idx] * j) / ny

    c1 = np.asarray(c1_list, dtype=float)
    if sym == 1:
        c2 = c1.copy()
        c2[:, 1] = -c2[:, 1]
        c_out = np.vstack([c1, c2])
        v_sym = np.zeros((neqns, 2, 3))
        v_sym[:, 0] = v1[:neqns, 1]
        v_sym[:, 0, 1] = -v_sym[:neqns, 0, 1]
        v_sym[:, 1] = v1[:neqns, 0]
        v_sym[:, 1, 1] = -v_sym[:neqns, 1, 1]
        v_full = np.vstack([v1[:neqns], v_sym])
        s_full = np.concatenate([s_slopes[:neqns], s_slopes[:neqns]])
    else:
        c_out = c1
        v_full = v1[:neqns]
        s_full = s_slopes[:neqns]

    n_panels = c_out.shape[0]
    vor = np.zeros((n_panels, 6, 3), dtype=float)
    for k in range(n_panels):
        vor[k, 0] = tep1[k, 0]
        vor[k, 1] = hp[k, 0]
        vor[k, 2:4] = v_full[k]
        vor[k, 4] = hp[k, 1]
        vor[k, 5] = tep1[k, 1]

    n_out = _normals4(c_out, vor, s_full)
    v_out = vor

    if sym == 1:
        px2 = np.column_stack([px[:, 1], px[:, 0], px[:, 3], px[:, 2], px[:, 1]])
        py2 = np.column_stack([py[:, 1], py[:, 0], py[:, 3], py[:, 2], py[:, 1]])
        pz2 = np.column_stack([pz[:, 1], pz[:, 0], pz[:, 3], pz[:, 2], pz[:, 1]])
        px = np.vstack([px, px2])
        py = np.vstack([py, -py2])
        pz = np.vstack([pz, pz2])

    p_out = np.stack([px, py, pz], axis=2)
    return c_out, v_out, n_out, p_out


def _fcmac(
    c: np.ndarray,
    b: np.ndarray,
    sw: np.ndarray,
    sx: np.ndarray,
    sy: np.ndarray,
    sz: np.ndarray,
    dihed: np.ndarray,
    sym: float,
) -> tuple[float, np.ndarray]:
    c = np.asarray(c, dtype=float).reshape(-1)
    b = np.asarray(b, dtype=float).reshape(-1)
    sw = np.asarray(sw, dtype=float).reshape(-1)
    sx = np.asarray(sx, dtype=float).reshape(-1)
    sy = np.asarray(sy, dtype=float).reshape(-1)
    sz = np.asarray(sz, dtype=float).reshape(-1)
    dihed = np.asarray(dihed, dtype=float).reshape(-1)
    noofpan = c.size
    if noofpan < 2:
        return float(c[0]) if noofpan else 0.0, np.zeros(3)

    taper = c[1:] / c[:-1]
    cb, ct = c[:-1], c[1:]
    b_mac = b * (2 * ct + cb) / (3 * (ct + cb))
    cmac_parts = cb - (cb - ct) / b * b_mac
    cmac_parts = np.nan_to_num(cmac_parts, nan=0.0)

    start = np.zeros((noofpan - 1, 3))
    for i in range(noofpan - 1):
        start[i, 0] = 0.25 * cb[i] + b_mac[i] * math.tan(sw[i]) - 0.25 * cmac_parts[i] + sx[i]
        start[i, 1] = math.cos(dihed[i]) * b_mac[i] + sy[i]
        start[i, 2] = math.sin(dihed[i]) * b_mac[i] + sz[i]

    if sym:
        start[:, 1] = 0.0

    a = (1 + taper) * cb * b / 2
    c_mac = float(np.sum(cmac_parts * a) / np.sum(a))
    mac_start = np.array([
        np.sum(start[:, 0] * a) / np.sum(a),
        np.sum(start[:, 1] * a) / np.sum(a),
        np.sum(start[:, 2] * a) / np.sum(a),
    ])
    return c_mac, mac_start


def _geosetup15(geo: dict) -> tuple[dict, dict]:
    geo = dict(geo)
    meshtype = geo.get("meshtype")
    if meshtype is None:
        meshtype = np.ones_like(geo["T"])
    else:
        meshtype = np.asarray(meshtype)

    lattice = {
        "COLLOC": np.empty((0, 3)),
        "VORTEX": np.empty((0, 0, 3)),
        "N": np.empty((0, 3)),
        "XYZ": np.empty((0, 5, 3)),
    }

    loopsperwing = np.asarray(geo["nelem"], dtype=int)
    noofwings = loopsperwing.size
    noofloops = loopsperwing

    chords = np.zeros((noofwings, int(np.max(noofloops)) + 1))
    sx = np.zeros_like(chords)
    sy = np.zeros_like(chords)
    sz = np.zeros_like(chords)

    for s in range(noofwings):
        chords[s, 0] = geo["c"][s, 0]
        sx[s, 0] = geo["startx"][s, 0]
        sy[s, 0] = geo["starty"][s, 0]
        sz[s, 0] = geo["startz"][s, 0]

    for s in range(noofwings):
        for t in range(noofloops[s]):
            t_val = float(geo["T"][s, t])
            if math.isnan(t_val) or t_val <= 0:
                geo["T"][s, t] = 1.0
                t_val = 1.0
            chords[s, t + 1] = chords[s, t] * t_val
            sx[s, t + 1] = (
                0.25 * chords[s, t]
                + geo["b"][s, t] * math.tan(geo["SW"][s, t])
                - 0.25 * chords[s, t + 1]
                + sx[s, t]
            )
            sy[s, t + 1] = geo["b"][s, t] * math.cos(geo["dihed"][s, t]) + sy[s, t]
            sz[s, t + 1] = geo["b"][s, t] * math.sin(geo["dihed"][s, t]) + sz[s, t]

    s_area = np.zeros((noofwings, int(np.max(noofloops))))
    cmgc = np.zeros_like(s_area)

    for s in range(noofwings):
        for t in range(noofloops[s]):
            foil = geo["foil"][s][t]
            tw = geo["TW"][s, t, :]
            c, v, n2, p = _geometry19(
                int(geo["fnx"][s, t]),
                int(geo["ny"][s, t]),
                int(geo["nx"][s, t]),
                float(geo["fsym"][s, t]),
                float(geo["fc"][s, t]),
                float(geo["flapped"][s, t]),
                tw,
                foil,
                float(geo["T"][s, t]),
                float(geo["SW"][s, t]),
                float(chords[s, t]),
                float(geo["dihed"][s, t]),
                float(geo["b"][s, t]),
                float(geo["symetric"][s]),
                float(sx[s, t]),
                float(sy[s, t]),
                float(sz[s, t]),
                float(meshtype[s, t]),
            )
            lattice["COLLOC"] = np.vstack([lattice["COLLOC"], c]) if lattice["COLLOC"].size else c
            lattice["VORTEX"] = np.vstack([lattice["VORTEX"], v]) if lattice["VORTEX"].size else v
            lattice["N"] = np.vstack([lattice["N"], n2]) if lattice["N"].size else n2
            lattice["XYZ"] = np.vstack([lattice["XYZ"], p]) if lattice["XYZ"].size else p

            s_area[s, t] = geo["b"][s, t] * chords[s, t] * (1 + geo["T"][s, t]) / 2
            cmgc[s, t] = s_area[s, t] / geo["b"][s, t]
            if geo["symetric"][s] == 1:
                s_area[s, t] *= 2

    ref: dict = {}
    ref_b = _config("b_ref")
    if ref_b is None:
        b_sum = np.sum(geo["b"], axis=1)
        ref["b_ref"] = float(b_sum[0] * (geo["symetric"][0] + 1))
    else:
        ref["b_ref"] = ref_b

    ref_s = _config("S_ref")
    if ref_s is None:
        ref["S_ref"] = float(np.sum(s_area, axis=1)[0])
    else:
        ref["S_ref"] = ref_s

    c_m = np.sum(cmgc * s_area, axis=1)
    ref["C_mgc"] = float(c_m[0] / ref["S_ref"])

    ref_cmac = _config("C_mac")
    if ref_cmac is None:
        ref["C_mac"], _ = _fcmac(
            chords[0, : noofloops[0] + 1],
            geo["b"][0, : noofloops[0]],
            geo["SW"][0, : noofloops[0]],
            sx[0, : noofloops[0]],
            sy[0, : noofloops[0]],
            sz[0, : noofloops[0]],
            geo["dihed"][0, : noofloops[0]],
            geo["symetric"][0],
        )
    else:
        ref["C_mac"] = ref_cmac

    ref_mac = _config("mac_pos")
    if ref_mac is None:
        _, ref["mac_pos"] = _fcmac(
            chords[0, : noofloops[0] + 1],
            geo["b"][0, : noofloops[0]],
            geo["SW"][0, : noofloops[0]],
            sx[0, : noofloops[0]],
            sy[0, : noofloops[0]],
            sz[0, : noofloops[0]],
            geo["dihed"][0, : noofloops[0]],
            geo["symetric"][0],
        )
    else:
        ref["mac_pos"] = ref_mac

    return lattice, ref


def _wakesetup2(lattice: dict, state: dict, ref: dict) -> dict:
    infdist = _config("infinity")
    if infdist is None:
        infdist = 6 * ref["b_ref"]

    v2 = lattice["VORTEX"]
    a, b, _ = v2.shape
    infx = infdist * math.cos(state["alpha"]) * math.cos(state["betha"])
    infy = -infdist * math.sin(state["betha"])
    infz = infdist * math.sin(state["alpha"]) * math.cos(state["betha"])

    dx = np.zeros((a, 2))
    dy = np.zeros((a, 2))
    dz = np.zeros((a, 2))
    cols = [0, b - 1]
    for t in range(a):
        for si, s in enumerate(cols):
            x = infx + v2[t, s, 0]
            y = infy + v2[t, s, 1]
            z = infz + v2[t, s, 2]
            psi = state["P"] / state["AS"] * x
            theta = state["Q"] / state["AS"] * x
            fi = state["R"] / state["AS"] * x
            dx[t, si] = -x * (2 - math.cos(theta) - math.cos(fi))
            dy[t, si] = math.sin(psi) * z - math.sin(fi) * x + (1 - math.cos(psi)) * y
            dz[t, si] = math.sin(theta) * x - math.sin(psi) * y + (1 - math.cos(psi)) * z

    inf1 = np.zeros((a, 1, 3))
    inf2 = np.zeros((a, 1, 3))
    for i in range(a):
        inf1[i, 0] = v2[i, 0] + [infx + dx[i, 0], infy + dy[i, 0], infz + dz[i, 0]]
        inf2[i, 0] = v2[i, b - 1] + [infx + dx[i, 1], infy + dy[i, 1], infz + dz[i, 1]]

    lattice = dict(lattice)
    lattice["VORTEX"] = np.concatenate([inf1, v2, inf2], axis=1)
    return lattice


def _setrudder3(rudder: int, deflection: float, lattice: dict, geo: dict) -> dict:
    i_idx, k_idx = flap_indices(geo)
    if rudder > len(i_idx):
        raise ValueError(f"Invalid rudder index {rudder}")
    wing = int(k_idx[rudder - 1])
    division = int(i_idx[rudder - 1])

    lattice = dict(lattice)
    vortex = lattice["VORTEX"]
    q2 = vortex.shape[1]
    temp_v1 = temp_v2 = None
    if q2 == 8:
        temp_v1 = vortex[:, 0:1, :].copy()
        temp_v2 = vortex[:, 7:8, :].copy()
        vortex = vortex[:, 1:7, :].copy()

    fsym = float(geo["fsym"][wing, division])
    mp = 3
    t_start = 1
    r_count = 0
    nr = (geo["nx"] + geo["fnx"]) * geo["ny"]
    nr = nr * (1 + geo["symetric"][:, np.newaxis])
    for i in range(nr.shape[0]):
        for j in range(nr.shape[1]):
            if geo["flapped"][i, j] == 1:
                r_count += 1
            if r_count < rudder:
                t_start += int(nr[i, j])

    nx = int(geo["nx"][wing, division])
    ny = int(geo["ny"][wing, division])
    fnx = int(geo["fnx"][wing, division])
    xyz = lattice["XYZ"]
    colloc = lattice["COLLOC"]
    n_arr = lattice["N"]

    a1 = xyz[t_start + nx - 1, 0].copy()
    b1 = xyz[t_start + nx - 1, 1].copy()
    a2 = np.array([xyz[t_start + nx - 1, 1, 0], -xyz[t_start + nx - 1, 1, 1], xyz[t_start + nx - 1, 1, 2]])
    b2 = np.array([xyz[t_start + nx - 1, 0, 0], -xyz[t_start + nx - 1, 0, 1], xyz[t_start + nx - 1, 0, 2]])

    h = b1 - a1
    h1_hat = h / np.linalg.norm(h)
    h2 = b2 - a2
    h2_hat = h2 / np.linalg.norm(h2)
    s_span = nx + fnx

    for i in range((nx + fnx) * ny * (1 + int(geo["symetric"][wing]))):
        rad2 = t_start + i
        if rad2 < t_start + (nx + fnx) * ny:
            a, b, h_hat, def_val = a1, b1, h1_hat, deflection
        else:
            h_hat = h2_hat
            a, b = a2, b2
            def_val = -deflection if fsym == 0 else deflection
        for col in (0, 1, 5):
            p1 = vortex[rad2 - 1, col, :].copy()
            if col <= mp - 1:
                r_vec = p1 - a
                p2 = _trot3(h_hat, r_vec, def_val)
                vortex[rad2 - 1, col] = p2 + a
            else:
                r_vec = p1 - b
                p2 = _trot3(h_hat, r_vec, def_val)
                vortex[rad2 - 1, col] = p2 + b

    sym_factor = 1 + int(geo["symetric"][wing])
    for i in range(s_span, s_span * ny * sym_factor + 1, s_span):
        for j in range(fnx):
            ii = i - fnx
            rad1 = t_start + ii + j - 1
            if rad1 < t_start + (nx + fnx) * ny - 1:
                a, b, h_hat, def_val = a1, b1, h1_hat, deflection
            else:
                h_hat = h2_hat
                a, b = a2, b2
                def_val = -deflection if fsym == 0 else deflection
            for k in range(4):
                col = k + mp - 1
                if col in (0, 1, 5):
                    continue
                p1 = vortex[rad1, col, :].copy()
                if col <= mp - 1:
                    p2 = _trot3(h_hat, p1 - a, def_val) + a
                else:
                    p2 = _trot3(h_hat, p1 - b, def_val) + b
                vortex[rad1, col] = p2
            p1 = colloc[rad1].copy()
            c_mid = (a + b) / 2
            colloc[rad1] = _trot3(h_hat, p1 - c_mid, def_val) + c_mid
            p1 = n_arr[rad1].copy()
            n_arr[rad1] = _trot3(h_hat, p1, def_val)
            for k in range(5):
                col = k
                p1 = xyz[rad1, col].copy()
                if col <= 0:
                    xyz[rad1, col] = _trot3(h_hat, p1 - a, def_val) + a
                elif col <= 2:
                    xyz[rad1, col] = _trot3(h_hat, p1 - b, def_val) + b
                else:
                    xyz[rad1, col] = _trot3(h_hat, p1 - a, def_val) + a

    if q2 == 8:
        vortex = np.concatenate([temp_v1, vortex, temp_v2], axis=1)

    lattice["VORTEX"] = vortex
    lattice["COLLOC"] = colloc
    lattice["N"] = n_arr
    lattice["XYZ"] = xyz
    return lattice


def lattice_setup(geo: dict, state: dict, mode: int = 0) -> tuple[dict, dict]:
    lattice, ref = _geosetup15(geo)

    dim2 = lattice["VORTEX"].shape[1] if lattice["VORTEX"].ndim >= 2 else 0
    if dim2 == 8:
        lattice["VORTEX"] = lattice["VORTEX"][:, 1:7, :]

    if state["AS"] == 0:
        raise ValueError("state.AS must be non-zero for lattice wake setup")

    lattice = _wakesetup2(lattice, state, ref)

    i_idx, k_idx = flap_indices(geo)
    if i_idx.size:
        noof_flaps = int(np.sum(geo["flapped"]))
        for k in range(1, noof_flaps + 1):
            deflection = float(geo["flap_vector"][k_idx[k - 1], i_idx[k - 1]])
            lattice = _setrudder3(k, deflection, lattice, geo)

    dim2 = lattice["VORTEX"].shape[1]
    if mode == 1:
        if dim2 == 8:
            idx = [0, 3, 4, 7]
        else:
            idx = [0, 2, 3, 5]
        temporary = lattice["VORTEX"][:, idx, :].copy()
        temporary[:, 0, 2] = temporary[:, 1, 2]
        temporary[:, 3, 2] = temporary[:, 2, 2]
        lattice["VORTEX"] = temporary

    npan = lattice["XYZ"].shape[0]
    lattice["npan"] = npan
    lattice["X"] = lattice["XYZ"][:, :, 0]
    lattice["Y"] = lattice["XYZ"][:, :, 1]

    return lattice, ref
