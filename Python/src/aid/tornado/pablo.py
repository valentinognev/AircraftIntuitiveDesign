"""Port of Tornado fPablo.m (linear-strength vortex + Thwaites/Michel/Head)."""

from __future__ import annotations

import numpy as np
from scipy.interpolate import CubicSpline
from scipy.optimize import minimize_scalar

__all__ = ["pablo"]


def pablo(z: np.ndarray, alpha_rad: float, reynolds: float) -> dict:
    """Section cl, cd, cm and boundary-layer states.

    z is (N, 2) airfoil coordinates, either a Pablo file
    (header row ``[n_upper, n_lower]`` then upper LE→TE then lower LE→TE)
    or raw coordinates (upper LE→TE stacked on lower LE→TE).
    alpha_rad is geometric angle of attack in radians (fPablo's alfa is degrees;
    fViscCorr passes ``alpha*180/pi``).
    """
    coord = _ensure_file_format(np.asarray(z, dtype=float))
    n_panels_target = 100
    surf = library(n_panels_target // 2, coord)
    clcm = vortex(surf, float(alpha_rad))
    n_pts = surf.shape[0]
    cl = float(clcm[0])
    cm = float(clcm[1])
    ue = np.asarray(clcm[2 : 2 + n_pts], dtype=float).copy()
    isp = stagnation_point(ue)
    ue[isp] = 0.0

    z_up = surf[isp::-1, :]
    z_lo = surf[isp:, :]
    ue_up = -ue[isp::-1]
    ue_lo = ue[isp:]

    res_up = solvebl(float(reynolds), z_up, ue_up)
    res_lo = solvebl(float(reynolds), z_lo, ue_lo)
    cd = sy(res_up[0], res_up[1], res_up[2], res_lo[0], res_lo[1], res_lo[2])
    return {
        "cl": cl,
        "cd": float(cd),
        "cm": cm,
        "upperbl": res_up,
        "lowerbl": res_lo,
    }


def _ensure_file_format(z: np.ndarray) -> np.ndarray:
    if z.ndim != 2 or z.shape[1] != 2:
        raise ValueError("z must have shape (N, 2)")
    if _is_pablo_file(z):
        return z
    if z.shape[0] < 4:
        raise ValueError("airfoil coordinate array is too short")
    n_up = z.shape[0] // 2
    n_lo = z.shape[0] - n_up
    header = np.array([[n_up, n_lo]], dtype=float)
    return np.vstack([header, z])


def _is_pablo_file(z: np.ndarray) -> bool:
    if z.shape[0] < 5:
        return False
    n_up, n_lo = float(z[0, 0]), float(z[0, 1])
    if n_up < 2 or n_lo < 2:
        return False
    if abs(n_up - round(n_up)) > 1e-6 or abs(n_lo - round(n_lo)) > 1e-6:
        return False
    return int(round(n_up)) + int(round(n_lo)) + 1 == z.shape[0]


def _dist(z: np.ndarray, i: int, j: int) -> float:
    return float(np.hypot(z[i, 0] - z[j, 0], z[i, 1] - z[j, 1]))


def _cubic(x: np.ndarray, y: np.ndarray) -> CubicSpline:
    x = np.asarray(x, dtype=float).ravel()
    y = np.asarray(y, dtype=float).ravel()
    n = min(x.size, y.size)
    x = x[:n].copy()
    y = y[:n].copy()
    for k in range(1, x.size):
        if x[k] <= x[k - 1]:
            x[k] = x[k - 1] + 1e-12
    if x.size < 2:
        x = np.array([0.0, 1.0])
        y = np.array([y[0] if y.size else 0.0, y[0] if y.size else 0.0])
    return CubicSpline(x, y, bc_type="not-a-knot", extrapolate=True)


def _matlab_round(val: float) -> float:
    return float(np.sign(val) * np.floor(np.abs(val) + 0.5))


def library(nbpo2: int, coord: np.ndarray) -> np.ndarray:
    """Resample an airfoil file onto a cosine chord grid. Port of library()."""
    nbpo2 = int(nbpo2)
    coord = np.asarray(coord, dtype=float)
    nbup = int(round(coord[0, 0]))
    nblo = int(round(coord[0, 1]))
    nbp = nbup + nblo - 1

    xdat = np.zeros(nbp + 1)
    ydat = np.zeros(nbp + 1)
    xdat[1 : nbup + 1] = coord[nbup:0:-1, 0]
    ydat[1 : nbup + 1] = coord[nbup:0:-1, 1]
    xdat[nbup + 1 : nbp + 1] = coord[nbup + 2 : nbup + nblo + 1, 0]
    ydat[nbup + 1 : nbp + 1] = coord[nbup + 2 : nbup + nblo + 1, 1]

    s = np.zeros(nbp + 1)
    s[1] = 0.0
    seg = np.hypot(np.diff(xdat[1 : nbp + 1]), np.diff(ydat[1 : nbp + 1]))
    s[2 : nbp + 1] = np.cumsum(seg)
    for k in range(2, nbp + 1):
        if s[k] <= s[k - 1]:
            s[k] = s[k - 1] + 1e-12

    ppx = _cubic(s[1 : nbp + 1], xdat[1 : nbp + 1])
    ppy = _cubic(s[1 : nbp + 1], ydat[1 : nbp + 1])
    sle = float(
        minimize_scalar(
            lambda sv: float(ppx(sv)),
            bounds=(float(s[1]), float(s[nbp])),
            method="bounded",
            options={"xatol": 1e-6},
        ).x
    )

    i1 = int(np.flatnonzero(s[1 : nbp + 1] >= sle)[0]) + 1
    if i1 < 2:
        i1 = 2
    tt = 0.1 * (s[i1] - s[i1 - 1])

    if sle - s[i1 - 1] < tt:
        ile = i1 - 1
        xdat_up = xdat[ile:0:-1]
        ydat_up = ydat[ile:0:-1]
        xdat_lo = xdat[ile : nbp + 1]
        ydat_lo = ydat[ile : nbp + 1]
    elif s[i1] - sle < tt:
        ile = i1
        xdat_up = xdat[ile:0:-1]
        ydat_up = ydat[ile:0:-1]
        xdat_lo = xdat[ile : nbp + 1]
        ydat_lo = ydat[ile : nbp + 1]
    else:
        ile = i1
        x2 = np.zeros(nbp + 2)
        y2 = np.zeros(nbp + 2)
        x2[1:ile] = xdat[1:ile]
        x2[ile] = float(ppx(sle))
        x2[ile + 1 : nbp + 2] = xdat[ile : nbp + 1]
        y2[1:ile] = ydat[1:ile]
        y2[ile] = float(ppy(sle))
        y2[ile + 1 : nbp + 2] = ydat[ile : nbp + 1]
        xdat_up = x2[ile:0:-1]
        ydat_up = y2[ile:0:-1]
        xdat_lo = x2[ile : nbp + 2]
        ydat_lo = y2[ile : nbp + 2]

    # xdat_up runs LE → TE. MATLAB chord = xdatup(ile) - xdatup(1), and
    # xdatup has length ile so the last entry is the trailing edge.
    chord = float(xdat_up[-1] - xdat_up[0])
    if chord == 0.0:
        chord = 1.0
    xle = float(xdat_up[0])
    yle = float(ydat_up[0])
    xdat_up = (xdat_up - xle) / chord
    xdat_lo = (xdat_lo - xle) / chord
    ydat_up = (ydat_up - yle) / chord
    ydat_lo = (ydat_lo - yle) / chord

    sup = np.zeros(xdat_up.size)
    slo = np.zeros(xdat_lo.size)
    if xdat_up.size > 1:
        sup[1:] = np.cumsum(np.hypot(np.diff(xdat_up), np.diff(ydat_up)))
    if xdat_lo.size > 1:
        slo[1:] = np.cumsum(np.hypot(np.diff(xdat_lo), np.diff(ydat_lo)))

    beta = np.linspace(0.0, np.pi, nbpo2 + 1)
    xc = 0.5 * (1.0 - np.cos(beta))
    vxc = np.sqrt(xc)

    s_up = _cubic(np.sqrt(np.maximum(xdat_up, 0.0)), sup)(vxc)
    ycup = _cubic(sup, ydat_up)(s_up)
    s_lo = _cubic(np.sqrt(np.maximum(xdat_lo, 0.0)), slo)(vxc)
    yclo = _cubic(slo, ydat_lo)(s_lo)

    upper = np.column_stack((xc[::-1], np.asarray(ycup, dtype=float)[::-1]))
    lower = np.column_stack((xc[1:], np.asarray(yclo, dtype=float)[1:]))
    return np.vstack((upper, lower))


def vortex(za: np.ndarray, alpha_rad: float) -> np.ndarray:
    """Linear-strength vortex panel solution. Port of vortex().

    alpha_rad is radians. MATLAB vortex() takes degrees and converts
    with ``pi*alfa/180``; the public pablo() API is already in radians.
    """
    za = np.asarray(za, dtype=float)
    nbp = za.shape[0] - 1
    chord = 1.0
    v_zero = 1.0
    alfar = float(alpha_rad)

    z = za[:, 0] + 1j * za[:, 1]
    z = z[::-1]
    m = (z[:nbp] + z[1 : nbp + 1]) / 2.0
    th = np.imag(np.log((z[1 : nbp + 1] - z[:nbp]).astype(complex)))

    rhs = np.zeros(nbp + 2, dtype=float)
    rhs[:nbp] = np.cos(alfar) * np.sin(th) - np.sin(alfar) * np.cos(th)

    z_start = z[:nbp]
    xzt = m[:, None] - z_start[None, :]
    xt = np.real(xzt)
    zt = np.imag(xzt)
    xz2t = np.diff(z)
    x2t = np.real(xz2t)
    z2t = np.imag(xz2t)

    cth = np.cos(th)[None, :]
    sth = np.sin(th)[None, :]
    x_mat = xt * cth + zt * sth
    z_mat = -xt * sth + zt * cth
    x2 = x2t * np.cos(th) + z2t * np.sin(th)

    mii = np.repeat(m[:, None], nbp, axis=1)
    zjj = np.repeat(z_start[None, :], nbp, axis=0)
    zjjp1 = np.repeat(z[1 : nbp + 1][None, :], nbp, axis=0)
    r1 = np.abs(zjj - mii)
    r2 = np.abs(zjjp1 - mii)
    angle = np.imag(np.log(((zjjp1 - mii) / (zjj - mii)).astype(complex)))
    angle = np.mod(angle - np.pi, 2.0 * np.pi) - np.pi
    x2mat = np.repeat(x2[None, :], nbp, axis=0)

    th2mth1 = angle / (2.0 * np.pi * x2mat)
    rr = np.log(r2 / r1) / (2.0 * np.pi * x2mat)
    u2l = z_mat * rr + x_mat * th2mth1
    u1l = -(u2l - x2mat * th2mth1)
    tmp = 1.0 / (2.0 * np.pi) - z_mat * th2mth1
    w1l = -tmp + (x2mat - x_mat) * rr
    w2l = tmp + x_mat * rr

    diag_u1 = np.diag(u1l) + 0.5 * (np.diag(x_mat) - x2) / x2
    u1l = u1l - np.diag(diag_u1)
    diag_u2 = np.diag(u2l) - 0.5 * np.diag(x_mat) / x2
    u2l = u2l - np.diag(diag_u2)
    w1l = w1l - np.diag(np.diag(w1l) + 1.0 / (2.0 * np.pi))
    w2l = w2l - np.diag(np.diag(w2l) - 1.0 / (2.0 * np.pi))

    ca = np.cos(-th)[None, :]
    sa = np.sin(-th)[None, :]
    u1 = u1l * ca + w1l * sa
    u2 = u2l * ca + w2l * sa
    w1 = -u1l * sa + w1l * ca
    w2 = -u2l * sa + w2l * ca

    ca_col = np.cos(th)[:, None]
    sa_col = np.sin(th)[:, None]
    aij = np.zeros((nbp, nbp + 1), dtype=float)
    bij = np.zeros((nbp, nbp + 1), dtype=float)
    aij[:, :nbp] = np.real(-u1 * sa_col + w1 * ca_col)
    bij[:, :nbp] = np.real(u1 * ca_col + w1 * sa_col)
    aij[:, 1 : nbp + 1] = aij[:, 1 : nbp + 1] + np.real(-u2 * sa_col + w2 * ca_col)
    bij[:, 1 : nbp + 1] = bij[:, 1 : nbp + 1] + np.real(u2 * ca_col + w2 * sa_col)

    d1n = _dist(za, nbp - 1, nbp)
    d12 = _dist(za, 1, 0)
    xp = (za[nbp - 1, 0] - za[nbp, 0]) / d1n + (za[1, 0] - za[0, 0]) / d12
    yp = (za[nbp - 1, 1] - za[nbp, 1]) / d1n + (za[1, 1] - za[0, 1]) / d12
    dpo = float(np.hypot(xp, yp))
    zi1 = (za[0, 0] + za[nbp, 0]) / 2.0 - chord * 2000.0 * xp / dpo
    zi2 = (za[0, 1] + za[nbp, 1]) / 2.0 - chord * 2000.0 * yp / dpo
    zi = zi1 + 1j * zi2
    zte = z[0]
    d1 = zte - m
    d2 = zi - m
    angle_w = np.imag(np.log((d1 / d2).astype(complex)))
    angle_w = np.mod(angle_w - np.pi, 2.0 * np.pi) - np.pi
    r1or2 = np.abs(d1) / np.abs(d2)
    u = angle_w / (2.0 * np.pi)
    w = -np.log(r1or2) / (2.0 * np.pi)
    ca_v = np.cos(-th)
    sa_v = np.sin(-th)
    ug = u * ca_v + w * sa_v
    wg = -u * sa_v + w * ca_v
    aw = np.real(-ug * np.sin(th) + wg * np.cos(th))

    a_full = np.zeros((nbp + 2, nbp + 2), dtype=float)
    a_full[:nbp, : nbp + 1] = aij
    a_full[:nbp, nbp + 1] = aw
    a_full[nbp, 0] = 1.0
    a_full[nbp + 1, nbp] = 1.0

    gamma = np.linalg.solve(a_full, rhs)
    gamma = np.real(gamma[: nbp + 1])
    vel = bij @ gamma
    velocity = vel + np.cos(alfar) * np.cos(th) + np.sin(alfar) * np.sin(th)

    z = z[::-1]
    velocity = -velocity[::-1]
    qtj = (velocity[: nbp - 1] + velocity[1:nbp]) / 2.0

    dz12 = abs(z[0] - z[1])
    dz23 = abs(z[2] - z[1])
    dznbp1 = abs(z[nbp - 1] - z[0])
    dznbp_m1 = abs(z[nbp - 1] - z[nbp - 2])
    qtj1 = qtj[0] + dz12 * (qtj[0] - qtj[1]) / dz23
    qtj2 = qtj[nbp - 2] + dznbp1 * (qtj[nbp - 2] - qtj[nbp - 3]) / dznbp_m1

    nodal = np.zeros(nbp + 1, dtype=float)
    nodal[0] = (qtj1 - qtj2) / 2.0
    nodal[1:nbp] = qtj
    nodal[nbp] = -nodal[0]

    cp = 1.0 - velocity**2 / v_zero**2
    cpmax = float(np.max(cp))
    cpmin = float(np.min(cp))

    fx = 0.0
    fy = 0.0
    cm = 0.0
    cmle = 0.0
    for jj in range(nbp):
        dz = z[jj + 1] - z[jj]
        fxj = -cp[jj] * np.imag(dz)
        fyj = cp[jj] * np.real(dz)
        fx += fxj
        fy += fyj
        cm += fxj * np.imag(m[jj]) - fyj * (np.real(m[jj]) - chord / 4.0)
        cmle += fxj * np.imag(m[jj]) - fyj * np.real(m[jj])

    cl = fy * np.cos(alfar) - fx * np.sin(alfar)
    if fy == 0.0:
        xcp = 0.0
    else:
        xcp = -cmle / fy
    if abs(cl) < 0.001:
        cl = 0.0
        cm = 0.0
        xcp = 0.0
    else:
        cl = float(np.floor(10000.0 * cl) / 10000.0)
        cm = float(np.floor(10000.0 * cm) / 10000.0)
    xcp = float(np.floor(100.0 * xcp) / 100.0)

    res = np.zeros(nbp + 6, dtype=float)
    res[0] = float(np.real(cl))
    res[1] = float(np.real(cm))
    res[2 : 2 + nbp + 1] = np.real(nodal)
    res[nbp + 3] = xcp
    res[nbp + 4] = cpmin
    res[nbp + 5] = cpmax
    return res


def stagnation_point(qtj: np.ndarray) -> int:
    """0-based index of the stagnation node. Port of stagnation_point()."""
    qtj = np.asarray(qtj, dtype=float).ravel()
    n = qtj.size
    isp = 1
    if isp >= n:
        return 0
    if qtj[isp] > 0.0:
        while isp < n - 1 and qtj[isp] > 0.0:
            isp += 1
    elif qtj[isp] < 0.0:
        while isp < n - 1 and qtj[isp] < 0.0:
            isp += 1
    ispu = isp - 1
    ispl = min(isp, n - 1)
    if abs(qtj[ispu]) < abs(qtj[ispl]):
        return ispu
    return ispl


def solvebl(re: float, z: np.ndarray, ue_nodes: np.ndarray) -> np.ndarray:
    """Thwaites laminar, Michel transition, Head turbulent. Port of solvebl()."""
    z = np.asarray(z, dtype=float)
    ue_nodes = np.asarray(ue_nodes, dtype=float).ravel()
    n = int(z.shape[0])
    nbp2 = 200

    ss = np.zeros(n + 1)
    ss[1] = 0.0
    for ii in range(2, n + 1):
        ss[ii] = ss[ii - 1] + _dist(z, ii - 1, ii - 2)

    coff = 0.98
    nm = int(np.floor(0.5 * n))
    if nm < 1:
        nm = 1
    se = float(_cubic(z[nm - 1 : n, 0], ss[nm : n + 1])(coff))
    if not np.isfinite(se) or se <= 0.0:
        se = float(ss[n]) * coff
    s = np.linspace(0.0, se, nbp2 + 1)

    spues = _cubic(ss[1 : n + 1], ue_nodes[:n])
    ues = np.asarray(spues(s), dtype=float)
    if np.any(ues < 0.0) and n >= 4:
        ue2 = np.zeros(n + 3)
        ss2 = np.zeros(n + 3)
        ue2[0] = ue_nodes[0]
        ue2[1] = 0.5 * (ue_nodes[1] + ue_nodes[0])
        ue2[2] = ue_nodes[1]
        ue2[3] = 0.5 * (ue_nodes[2] + ue_nodes[1])
        ue2[4] = ue_nodes[2]
        ue2[5] = 0.5 * (ue_nodes[3] + ue_nodes[2])
        ue2[6:] = ue_nodes[3:n]
        ss2[0] = ss[1]
        ss2[1] = 0.5 * (ss[2] + ss[1])
        ss2[2] = ss[2]
        ss2[3] = 0.5 * (ss[3] + ss[2])
        ss2[4] = ss[3]
        ss2[5] = 0.5 * (ss[4] + ss[3])
        ss2[6:] = ss[4 : n + 1]
        spues = _cubic(ss2, ue2)
        ues = np.asarray(spues(s), dtype=float)

    spx = _cubic(ss[1 : n + 1], z[:n, 0])
    ue = ues
    n_s = ue.size
    s_arr = s

    dueds = np.zeros(n_s)
    v1, v2, v3 = ue[0], ue[1], ue[2]
    x1, x2, x3 = s_arr[0], s_arr[1], s_arr[2]
    gamma = 1.0 / (x3 - x2) * ((v3 - v1) / (x3 - x1) - (v2 - v1) / (x2 - x1))
    fac = (v2 - v1) / (x2 - x1)
    dueds[0] = gamma * (x1 - x2) + fac
    if dueds[0] < 0.0:
        dueds[0] = (v2 - v1) / (x2 - x1)

    v1a = ue[:-2]
    v2a = ue[1:-1]
    v3a = ue[2:]
    x1a = s_arr[:-2]
    x2a = s_arr[1:-1]
    x3a = s_arr[2:]
    gamma_a = 1.0 / (x3a - x2a) * ((v3a - v1a) / (x3a - x1a) - (v2a - v1a) / (x2a - x1a))
    fac_a = (v2a - v1a) / (x2a - x1a)
    dueds[1 : n_s - 1] = gamma_a * (x2a - x1a) + fac_a

    v1, v2, v3 = ue[n_s - 3], ue[n_s - 2], ue[n_s - 1]
    x1, x2, x3 = s_arr[n_s - 3], s_arr[n_s - 2], s_arr[n_s - 1]
    gamma = 1.0 / (x3 - x2) * ((v3 - v1) / (x3 - x1) - (v2 - v1) / (x2 - x1))
    fac = (v2 - v1) / (x2 - x1)
    dueds[n_s - 1] = gamma * (2.0 * x3 - x1 - x2) + fac

    def u_at(i: int) -> float:
        return float(ue[i - 1])

    def s_at(i: int) -> float:
        return float(s_arr[i - 1])

    def d_at(i: int) -> float:
        return float(dueds[i - 1])

    n_bl = n_s
    theta = np.zeros(n_bl + 1)
    shape_h = np.zeros(n_bl + 1)
    # Skin friction follows fPablo solvebl; the returned vector does not include it.
    cf = np.zeros(n_bl + 1)
    lsep = 0
    trans = 0
    endofsurf = 0
    dued0 = dueds[0]
    if dued0 == 0.0:
        dued0 = 1e-8
    theta[1] = float(np.sqrt(0.075 / (re * dued0)))
    i = 1
    itrans = n_bl
    coeff = float(np.sqrt(3.0 / 5.0))
    k_th = 0.45 / re
    ret = 0.0
    retmax = 0.0

    while lsep == 0 and trans == 0 and endofsurf == 0:
        lam = theta[i] ** 2 * d_at(i) * re
        if lam < -0.09:
            lsep = 1
            itrans = i
            break
        shape_h[i] = fH(lam)
        ell = fL(lam)
        cf[i] = 2.0 * ell / (re * theta[i])
        if i > 1 and u_at(i) != 0.0:
            cf[i] = cf[i] / u_at(i)
        i = i + 1
        if i > n_bl:
            endofsurf = 1
            itrans = n_bl
            break
        xm = (s_at(i) + s_at(i - 1)) / 2.0
        dx = s_at(i) - s_at(i - 1)
        f1 = float(spues(xm - coeff * dx / 2.0)) ** 5
        f2 = float(spues(xm)) ** 5
        f3 = float(spues(xm + coeff * dx / 2.0)) ** 5
        dth2ue6 = k_th * dx / 18.0 * (5.0 * f1 + 8.0 * f2 + 5.0 * f3)
        ue_i = u_at(i)
        if ue_i == 0.0:
            ue_i = 1e-8
        theta[i] = float(
            np.sqrt((theta[i - 1] ** 2 * u_at(i - 1) ** 6 + dth2ue6) / ue_i**6)
        )
        rex = re * s_at(i) * u_at(i)
        ret = re * theta[i] * u_at(i)
        retmax = 1.174 * (rex**0.46 + 22400.0 * rex ** (-0.54))
        if ret > retmax:
            trans = 1
            itrans = i

    transorlamsep = 0.0
    transloc = 1.0
    tsep = 0.0
    y = None

    if itrans < n_bl and (trans == 1 or lsep == 1) and i > 1:
        uei = u_at(i)
        thi = theta[i]
        si = s_at(i)
        duedsi = d_at(i)
        ueim1 = u_at(i - 1)
        thim1 = theta[i - 1]
        sim1 = s_at(i - 1)
        duedsim1 = d_at(i - 1)
        if trans == 1:
            fxi = ret - retmax
            rex = re * sim1 * ueim1
            ret_m = re * thim1 * ueim1
            retmax_m = 1.174 * (rex**0.46 + 22400.0 * rex ** (-0.54))
            fxim1 = ret_m - retmax_m
            transorlamsep = 1.0
        else:
            fxi = thi**2 * duedsi * re + 0.09
            fxim1 = thim1**2 * duedsim1 * re + 0.09
            transorlamsep = 2.0
        denom = (fxi - fxim1) / (si - sim1) if si != sim1 else 1.0
        if denom == 0.0:
            denom = 1.0
        st = sim1 - fxim1 / denom
        transloc = 100.0 * float(spx(st))
        uet = float(spues(st))
        v1, v2, v3 = ueim1, uet, uei
        x1, x2, x3 = sim1, st, si
        if x3 == x2:
            duedst = duedsi
        else:
            gamma = 1.0 / (x3 - x2) * ((v3 - v1) / (x3 - x1) - (v2 - v1) / (x2 - x1))
            fac = (v2 - v1) / (x2 - x1) if x2 != x1 else 0.0
            duedst = gamma * (x2 - x1) + fac
        xm = (st + sim1) / 2.0
        dx = st - sim1
        f1 = float(spues(xm - coeff * dx / 2.0)) ** 5
        f2 = float(spues(xm)) ** 5
        f3 = float(spues(xm + coeff * dx / 2.0)) ** 5
        dth2ue6 = k_th * dx / 18.0 * (5.0 * f1 + 8.0 * f2 + 5.0 * f3)
        uei_den = uei if uei != 0.0 else 1e-8
        thetat = float(np.sqrt((thim1**2 * ueim1**6 + dth2ue6) / uei_den**6))
        lambdat = thetat**2 * duedst * re
        ht = fH(lambdat)
        if ht < 1.1:
            ht = 1.2
        if ht > 2.0:
            ht = 2.0
        y = np.array([thetat, H1ofH(ht)], dtype=float)
        y = runge(s_at(i) - st, y, re, uet, duedst, u_at(i), d_at(i))
        theta[i] = y[0]
        shape_h[i] = HofH1(y[1])
        rtheta = re * u_at(i) * theta[i]
        cf[i] = cfturb(rtheta, shape_h[i])

        tsep = 0.0
        i = i + 1
        while endofsurf == 0 and tsep == 0.0 and y is not None:
            y = runge(s_at(i) - s_at(i - 1), y, re, u_at(i - 1), d_at(i - 1), u_at(i), d_at(i))
            theta[i] = y[0]
            shape_h[i] = HofH1(y[1])
            if shape_h[i] == 3.0:
                tsep = 100.0 * float(spx(s_at(i)))
                i = i - 1
            rtheta = re * u_at(i) * theta[i]
            cf[i] = cfturb(rtheta, shape_h[i])
            i = i + 1
            if i > n_bl:
                endofsurf = 1

    if i < 2:
        i = 2
    res = np.zeros(6, dtype=float)
    res[0] = theta[i - 1]
    res[1] = shape_h[i - 1]
    res[2] = ue[i - 2]
    res[3] = transorlamsep
    res[4] = np.floor(100.0 * transloc) / 100.0
    res[5] = np.floor(100.0 * tsep) / 100.0
    return res


def sy(th_up, h_up, ue_te_up, th_lo, h_lo, ue_te_lo) -> float:
    """Squire-Young drag. Port of sy()."""
    cd = 2.0 * th_up * (ue_te_up ** ((h_up + 5.0) / 2.0)) + 2.0 * th_lo * (
        ue_te_lo ** ((h_lo + 5.0) / 2.0)
    )
    cd = complex(cd) if np.iscomplexobj(cd) else complex(float(cd), 0.0)
    if abs(cd.imag) > 1e-8 or not np.isfinite(cd.real):
        return float("nan")
    cd_r = cd.real
    cd_r = np.floor(_matlab_round(10000.0 * cd_r)) / 10000.0
    return float(cd_r)


def runge(dx, y, re, uei, duedsi, ueip1, duedsip1) -> np.ndarray:
    """One Head step. Port of runge()."""
    y = np.asarray(y, dtype=float)
    tsep = 0
    yt = y.copy()
    h1 = float(yt[1])
    shape = HofH1(h1)
    if shape == 3.0:
        tsep = 1
    ynp1 = np.array([-2.0, 0.0])
    if tsep == 0 and uei != 0.0 and yt[0] != 0.0:
        rtheta = re * uei * yt[0]
        yp0 = -(shape + 2.0) * yt[0] * duedsi / uei + 0.5 * cfturb(rtheta, shape)
        yp1 = -h1 * (duedsi / uei + yp0 / yt[0]) + 0.0306 * (h1 - 3.0) ** (-0.6169) / yt[0]
        yt = np.array([y[0] + dx * yp0, y[1] + dx * yp1])
        ys = np.array([y[0] + 0.5 * dx * yp0, y[1] + 0.5 * dx * yp1])
        h1 = float(yt[1])
        shape = HofH1(h1)
        if shape == 3.0:
            tsep = 1
        if tsep == 0 and ueip1 != 0.0 and yt[0] != 0.0:
            rtheta = re * ueip1 * yt[0]
            yp0 = -(shape + 2.0) * yt[0] * duedsip1 / ueip1 + 0.5 * cfturb(rtheta, shape)
            yp1 = -h1 * (duedsip1 / ueip1 + yp0 / yt[0]) + 0.0306 * (h1 - 3.0) ** (-0.6169) / yt[0]
            ynp1 = np.array([ys[0] + 0.5 * dx * yp0, ys[1] + 0.5 * dx * yp1])
    if tsep == 1:
        ynp1 = np.array([-2.0, 0.0])
    return ynp1


def cfturb(rtheta, shape) -> float:
    return float(0.246 * (10.0 ** (-0.678 * shape)) * rtheta ** (-0.268))


def HofH1(h1: float) -> float:
    if h1 <= 3.32:
        return 3.0
    if h1 < 5.3:
        return float(0.6778 + 1.1536 * (h1 - 3.3) ** (-0.326))
    return float(1.1 + 0.86 * (h1 - 3.3) ** (-0.777))


def H1ofH(shape: float) -> float:
    if shape < 1.1:
        return 16.0
    if shape <= 1.6:
        return float(3.3 + 0.8234 * (shape - 1.1) ** (-1.287))
    return float(3.3 + 1.5501 * (shape - 0.6778) ** (-3.064))


def fH(lam: float) -> float:
    if lam < 0.0:
        if lam == -0.14:
            lam = -0.139
        return float(2.088 + 0.0731 / (lam + 0.14))
    return float(2.61 - 3.75 * lam + 5.24 * lam**2)


def fL(lam: float) -> float:
    if lam < 0.0:
        if lam == -0.107:
            lam = -0.106
        return float(0.22 + 1.402 * lam + (0.018 * lam) / (lam + 0.107))
    return float(0.22 + 1.57 * lam - 1.8 * lam**2)
