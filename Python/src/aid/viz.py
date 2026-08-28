"""Aircraft display meshes from existing planform/body fields.

Ports the loft in ``Plot_Planform.m`` / ``Plot_Body.m`` (no new geometry model),
including flap/aileron/elevator/rudder hinge deflection.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from aid.aircraft import Aircraft
from aid.lifting_line import lifting_line

_XT = 0.25
_NP_TYPES = ("wing 2", "ht 2", "vt 2", "prop")
_RES_BODY = 100
_RES_WING = 101
_RES_TAIL = 51


@dataclass
class SurfaceMesh:
    name: str
    x: np.ndarray
    y: np.ndarray
    z: np.ndarray


def aircraft_surfaces(
    ac: Aircraft,
    *,
    angle: bool = True,
    res: tuple[int, int, int] = (_RES_BODY, _RES_WING, _RES_TAIL),
) -> list[SurfaceMesh]:
    """Loft WG/HT/VT/BD plus extra NP/NB parts honoring ``plot_cmp``."""
    res_body, res_wing, res_tail = res
    flags = list(ac.plot_cmp) + [1] * 8
    out: list[SurfaceMesh] = []
    if flags[0]:
        out.extend(_planform_surfaces(ac.WG, "wing", res_wing, res_wing, angle, ac))
    if flags[1]:
        out.extend(_planform_surfaces(ac.HT, "ht", res_tail, res_tail, angle, ac))
    if flags[2]:
        out.extend(_planform_surfaces(ac.VT, "vt", res_tail, res_tail, angle, ac))
    if flags[3]:
        out.extend(_body_surfaces(ac.BD, n=res_body))
    for i, pt in enumerate(ac.NP):
        if not pt:
            continue
        if not flags[4 + i]:
            continue
        kind = _NP_TYPES[i] if i < len(_NP_TYPES) else "wing 2"
        ni = res_wing if i == 0 else res_tail
        out.extend(_planform_surfaces(pt, kind, ni, ni, angle, ac))
    for i, pt in enumerate(ac.NB):
        if not pt:
            continue
        if not flags[8 + i]:
            continue
        out.extend(_body_surfaces(pt, n=res_body, extra_index=i + 1))
    return out


def _as_airfoils(data) -> list[np.ndarray]:
    if data is None:
        return []
    if not isinstance(data, list) or not data:
        arr = np.asarray(data, dtype=float)
        return [arr] if arr.size else []
    first = data[0]
    if isinstance(first, (list, tuple)) and first and isinstance(first[0], (list, tuple)):
        return [np.asarray(d, dtype=float) for d in data]
    return [np.asarray(data, dtype=float)]


def _resample_airfoil(data: np.ndarray, ni: int) -> tuple[np.ndarray, int, int]:
    n = data.shape[0]
    if ni < n:
        pts = np.unique(np.round(np.linspace(1, n, ni)).astype(int)) - 1
        data = data[pts]
    ni = data.shape[0]
    le = int(np.ceil(ni / 2))
    if ni % 2:
        data = np.insert(data, le, data[le - 1], axis=0)
        ni += 1
    return data, ni, le


def planform_stations(pt: dict, nj: int, angle: bool, kind: str) -> tuple[np.ndarray, ...]:
    """Spanwise stations along the right semi-span (``Plot_Planform`` / ``_stations``)."""
    return _stations(pt, nj, angle, kind)


def lift_overlay(ac: Aircraft, nj: int, *, angle: bool = True) -> dict:
    """Lift distribution polyline coords (``Plot_Planform.m`` case ``lift``)."""
    wg = ac.WG
    y, c, _dx, _dz, theta = planform_stations(wg, nj, angle, "wing")
    ll = lifting_line(ac, y, c, theta)
    chrdr = float(wg["CHRDR"])
    scale = float(ll["scale"])
    cl = ll["Cl"] / scale * chrdr
    cl_ideal = ll["Cl_ideal"] / scale * chrdr
    x = (
        float(wg["X"])
        + float(np.asarray(wg["xmac"]).reshape(-1)[-1])
        + float(np.asarray(wg["cbar"]).reshape(-1)[-1]) / 4
    )
    y_full = ll["y"]
    return {
        "X": np.full(y_full.shape, x),
        "Y": y_full,
        "Z0": np.full(y_full.shape, float(wg["Z"])),
        "Cl": cl,
        "Cl_ideal": cl_ideal,
    }


def _stations(pt: dict, nj: int, angle: bool, kind: str) -> tuple[np.ndarray, ...]:
    y0 = float(pt.get("Y", 0) or 0)
    z0 = float(pt.get("Z", 0) or 0)
    x0 = float(pt.get("X", 0) or 0)
    chrdr = float(pt.get("CHRDR", 0) or 0)
    chrdtp = float(pt.get("CHRDTP", chrdr) or chrdr)
    chrdbp = float(pt.get("CHRDBP", 0) or 0)
    sspn = float(pt.get("SSPN", 0) or 0)
    sspnop = float(pt.get("SSPNOP", 0) or 0)
    savsi = float(pt.get("SAVSI", 0) or 0)
    savso = float(pt.get("SAVSO", 0) or 0)
    chstat = float(pt.get("CHSTAT", 0) or 0)
    dhdadi = float(pt.get("DHDADI", 0) or 0)
    dhdado = float(pt.get("DHDADO", 0) or 0)
    inc = float(pt.get("i", 0) or 0)
    twista = float(pt.get("TWISTA", 0) or 0)

    def tand(deg: float) -> float:
        return np.tan(np.radians(deg))

    if chrdbp and sspnop:
        if angle:
            y_break = sspnop * np.cos(np.radians(dhdadi))
            if kind == "prop":
                y_break = y_break * np.cos(np.radians(savsi))
        else:
            y_break = sspnop
        n1 = max(2, round(nj * abs(y_break) / sspn)) if sspn else nj
        y1 = y0 + np.linspace(0, y_break, n1)
        c1 = chrdr + (y1 - y0) / (y1[-1] - y0) * (chrdbp - chrdr)
        dx1 = x0 + (y1 - y0) * tand(savsi) + chstat * (chrdr - chrdbp) * (y1 - y0) / (y1[-1] - y0)
        dz1 = z0 + (y1 - y0) * tand(dhdadi)
        if angle:
            y_out = y_break + (sspn - sspnop) * np.cos(np.radians(dhdado))
            if kind == "prop":
                y_out = y_break + (y_out - y_break) * np.cos(np.radians(savso))
        else:
            y_out = sspn
        n2 = max(2, nj - n1)
        y2 = y0 + np.linspace(y_break, y_out, n2)
        c2 = chrdbp + (y2 - y2[0]) / (y2[-1] - y2[0]) * (chrdtp - chrdbp)
        dx2 = dx1[-1] + (y2 - y2[0]) * tand(savso) + chstat * (chrdbp - chrdtp) * (y2 - y2[0]) / (
            y2[-1] - y2[0]
        )
        dz2 = dz1[-1] + (y2 - y2[0]) * tand(dhdado)
        y = np.concatenate([y1, y2])
        c = np.concatenate([c1, c2])
        dx = np.concatenate([dx1, dx2])
        dz = np.concatenate([dz1, dz2])
    else:
        if angle:
            y_out = sspn * np.cos(np.radians(dhdadi))
            if kind == "prop":
                y_out = y_out * np.cos(np.radians(savsi))
        else:
            y_out = sspn
        y = y0 + np.linspace(0, y_out, nj)
        span = y[-1] - y0
        frac = (y - y0) / span if span else np.zeros_like(y)
        c = chrdr + frac * (chrdtp - chrdr)
        dx = x0 + (y - y0) * tand(savsi) + chstat * (chrdr - chrdtp) * frac
        dz = z0 + (y - y0) * tand(dhdadi)

    span = y[-1] - y0
    frac = (y - y0) / span if span else np.zeros_like(y)
    theta = inc - frac * twista
    dx = dx + _XT * c
    if angle:
        c = c * np.cos(np.radians(theta))
    return y, c, dx, dz, theta


def _loft(pt: dict, kind: str, ni: int, nj: int, angle: bool) -> tuple[np.ndarray, ...]:
    pt = dict(pt)
    if "vt" in kind or kind == "prop":
        pt["Y"], pt["Z"] = float(pt.get("Z", 0) or 0), float(pt.get("Y", 0) or 0)
    y, c, dx, dz, theta = _stations(pt, nj, angle, kind)
    nj = y.size
    foils = _as_airfoils(pt.get("DATA"))
    if not foils:
        raise ValueError("planform missing DATA airfoil xy")
    if len(foils) == 1:
        data, ni, le = _resample_airfoil(foils[0], ni)
        x = data[:, 0][:, None]
        z = data[:, 1][:, None]
    else:
        d1, ni, le = _resample_airfoil(foils[0], ni)
        d2, _, _ = _resample_airfoil(foils[1], ni)
        ni = min(d1.shape[0], d2.shape[0])
        d1, d2 = d1[:ni], d2[:ni]
        le = int(np.ceil(ni / 2))
        t = (y - y[0]) / (y[-1] - y[0]) if y[-1] != y[0] else np.zeros_like(y)
        x = d1[:, 0][:, None] * (1 - t) + d2[:, 0][:, None] * t
        z = d1[:, 1][:, None] * (1 - t) + d2[:, 1][:, None] * t
    X = (x - _XT) * c[None, :] + dx[None, :]
    Y = np.broadcast_to(y[None, :], (ni, nj)).copy()
    Z = z * c[None, :] + dz[None, :] + (_XT - x) * np.tan(np.radians(theta[None, :])) * c[None, :]
    XL, XU = X[:le, -1], X[le:, -1]
    ZL, ZU = Z[:le, -1], Z[le:, -1]
    YL, YU = Y[:le, -1], Y[le:, -1]
    Xtip = np.column_stack([XL, XU[::-1]])
    Ztip = np.column_stack([ZL, ZU[::-1]])
    Ytip = np.column_stack([YL, YU])
    return X, Y, Z, Xtip, Ytip, Ztip, pt, x, c, le


def _add(out: list[SurfaceMesh], name: str, x, y, z) -> None:
    out.append(SurfaceMesh(name=name, x=np.asarray(x, dtype=float), y=np.asarray(y, dtype=float), z=np.asarray(z, dtype=float)))


def _delta_mean(val) -> float:
    arr = np.atleast_1d(np.asarray(val, dtype=float).reshape(-1))
    if arr.size == 0 or not np.max(np.abs(arr)):
        return 0.0
    return float(np.mean(arr))


def _control_masks(x: np.ndarray, chrdr: float, chrdfi: float, y0: np.ndarray, spanfi: float, spanfo: float):
    xc = np.asarray(x, dtype=float)
    x_le = xc[:, 0] if xc.ndim > 1 else xc
    denom = float(chrdr) if chrdr else 1.0
    i_mask = x_le > (denom - float(chrdfi or 0)) / denom
    j_mask = (float(spanfi or 0) < y0) & (y0 <= float(spanfo or 0))
    first = np.flatnonzero(j_mask)
    if first.size and first[0] > 0:
        j_mask = j_mask.copy()
        j_mask[first[0] - 1] = True
    return i_mask, j_mask


def _rotate_control(X, Z, i_mask, j_mask, c, delta_deg: float, *, z_sign: float):
    """Hinge rotation from ``Plot_Planform.m`` (uses inboard columns 0:nctrl for f)."""
    nctrl = int(np.count_nonzero(j_mask))
    Xc = X[np.ix_(i_mask, j_mask)].copy()
    Zc = Z[np.ix_(i_mask, j_mask)].copy()
    dX_last = np.zeros(int(np.count_nonzero(i_mask)))
    dZ_last = np.zeros_like(dX_last)
    rad = np.radians(delta_deg)
    cos_d, sin_d = np.cos(rad), np.sin(rad)
    for k in range(nctrl):
        x_ctrl = X[i_mask, k]
        span = float(np.max(X[:, k]) - np.min(X[:, k]))
        if span == 0:
            f = np.zeros_like(x_ctrl)
        else:
            f = c[k] * (x_ctrl - np.min(x_ctrl)) / span
        dX = f - f * cos_d
        dZ = f * sin_d
        Xc[:, k] = Xc[:, k] - dX
        Zc[:, k] = Zc[:, k] + z_sign * dZ
        dX_last, dZ_last = dX, dZ
    return Xc, Zc, dX_last, dZ_last


def _blank_parent(X, Z, i_mask, j_mask, *, blank_x: bool) -> None:
    jblank = j_mask.copy()
    first = np.flatnonzero(j_mask)
    if first.size:
        jblank[first[0]] = False
        if not j_mask[-1]:
            jblank[first[-1]] = False
    iblank = i_mask.copy()
    ni_idx = np.flatnonzero(~i_mask)
    if ni_idx.size:
        punch = list(ni_idx)
        if ni_idx[0] > 0:
            punch.append(ni_idx[0] - 1)
        if ni_idx[-1] + 1 < iblank.size:
            punch.append(ni_idx[-1] + 1)
        iblank[np.array(punch, dtype=int)] = False
    if not np.any(iblank) or not np.any(jblank):
        return
    ii, jj = np.ix_(iblank, jblank)
    Z[ii, jj] = np.nan
    if blank_x:
        X[ii, jj] = np.nan


def _apply_tip_defl(Xtip, Ztip, i_mask, le: int, dX, dZ, *, z_sign: float) -> None:
    if dX is None or not np.any(i_mask[:le]):
        return
    half_n = dX.size // 2
    if half_n == 0:
        return
    half_x = dX[:half_n]
    half_z = dZ[:half_n]
    rows = i_mask[:le]
    n_rows = int(np.count_nonzero(rows))
    if n_rows != half_n:
        n = min(n_rows, half_n)
        if n == 0:
            return
        idx = np.flatnonzero(rows)[:n]
        Xtip[idx, :] = Xtip[idx, :] - np.column_stack([half_x[:n], half_x[:n]])
        Ztip[idx, :] = Ztip[idx, :] + z_sign * np.column_stack([half_z[:n], half_z[:n]])
        return
    Xtip[rows, :] = Xtip[rows, :] - np.column_stack([half_x, half_x])
    Ztip[rows, :] = Ztip[rows, :] + z_sign * np.column_stack([half_z, half_z])


def _planform_surfaces(
    pt: dict, kind: str, ni: int, nj: int, angle: bool, ac: Aircraft | None = None
) -> list[SurfaceMesh]:
    X, Y, Z, Xtip, Ytip, Ztip, pt_swapped, x_af, c, le = _loft(pt, kind, ni, nj, angle)
    X, Y, Z = np.array(X, copy=True), np.array(Y, copy=True), np.array(Z, copy=True)
    Xtip, Ytip, Ztip = np.array(Xtip, copy=True), np.array(Ytip, copy=True), np.array(Ztip, copy=True)
    Xtl, Xtr = Xtip.copy(), Xtip.copy()
    Ztl, Ztr = Ztip.copy(), Ztip.copy()
    out: list[SurfaceMesh] = []
    controls: list[SurfaceMesh] = []
    sspn = float(pt.get("SSPN", 0) or 0)
    y0 = np.linspace(0.0, sspn, X.shape[1])
    chrdr = float(pt.get("CHRDR", 0) or 0)

    if kind == "wing" and ac is not None:
        flap_d = _delta_mean(ac.F.get("DELTA", 0))
        if flap_d:
            i_m, j_m = _control_masks(
                x_af, chrdr, float(ac.F.get("CHRDFI", 0) or 0), y0,
                float(ac.F.get("SPANFI", 0) or 0), float(ac.F.get("SPANFO", 0) or 0),
            )
            if np.any(i_m) and np.any(j_m):
                Xf, Zf, dX, dZ = _rotate_control(X, Z, i_m, j_m, c, flap_d, z_sign=-1.0)
                Yf = Y[np.ix_(i_m, j_m)]
                _add(controls, "F", Xf, Yf, Zf)
                _add(controls, "F", Xf, -Yf, Zf)
                if j_m[-1]:
                    _apply_tip_defl(Xtip, Ztip, i_m, le, dX, dZ, z_sign=-1.0)
                _blank_parent(X, Z, i_m, j_m, blank_x=False)
                Xtl, Xtr = Xtip.copy(), Xtip.copy()
                Ztl, Ztr = Ztip.copy(), Ztip.copy()

        al, ar = _delta_mean(ac.A.get("DELTAL", 0)), _delta_mean(ac.A.get("DELTAR", 0))
        if al or ar:
            i_m, j_m = _control_masks(
                x_af, chrdr, float(ac.A.get("CHRDFI", 0) or 0), y0,
                float(ac.A.get("SPANFI", 0) or 0), float(ac.A.get("SPANFO", 0) or 0),
            )
            if np.any(i_m) and np.any(j_m):
                Xal, Zal, dXl, dZl = _rotate_control(X, Z, i_m, j_m, c, al, z_sign=-1.0)
                Xar, Zar, dXr, dZr = _rotate_control(X, Z, i_m, j_m, c, ar, z_sign=1.0)
                Ya = Y[np.ix_(i_m, j_m)]
                _add(controls, "A", Xar, Ya, Zar)
                _add(controls, "A", Xal, -Ya, Zal)
                if j_m[-1]:
                    _apply_tip_defl(Xtl, Ztl, i_m, le, dXl, dZl, z_sign=-1.0)
                    _apply_tip_defl(Xtr, Ztr, i_m, le, dXr, dZr, z_sign=1.0)
                _blank_parent(X, Z, i_m, j_m, blank_x=False)

    elif kind == "ht" and ac is not None:
        el_d = _delta_mean(ac.E.get("DELTA", 0))
        if el_d:
            i_m, j_m = _control_masks(
                x_af, chrdr, float(ac.E.get("CHRDFI", 0) or 0), y0,
                float(ac.E.get("SPANFI", 0) or 0), float(ac.E.get("SPANFO", 0) or 0),
            )
            if np.any(i_m) and np.any(j_m):
                Xe, Ze, dX, dZ = _rotate_control(X, Z, i_m, j_m, c, el_d, z_sign=-1.0)
                Ye = Y[np.ix_(i_m, j_m)]
                _add(controls, "E", Xe, Ye, Ze)
                _add(controls, "E", Xe, -Ye, Ze)
                if j_m[-1]:
                    _apply_tip_defl(Xtip, Ztip, i_m, le, dX, dZ, z_sign=-1.0)
                _blank_parent(X, Z, i_m, j_m, blank_x=True)
                Xtl, Xtr = Xtip.copy(), Xtip.copy()
                Ztl, Ztr = Ztip.copy(), Ztip.copy()

    elif kind == "vt" and ac is not None:
        rd = _delta_mean(ac.R.get("DELTA", 0))
        if rd:
            i_m, j_m = _control_masks(
                x_af, chrdr, float(ac.R.get("CHRDFI", 0) or 0), y0,
                float(ac.R.get("SPANFI", 0) or 0), float(ac.R.get("SPANFO", 0) or 0),
            )
            if np.any(i_m) and np.any(j_m):
                Xr, Zr, dX, dZ = _rotate_control(X, Z, i_m, j_m, c, rd, z_sign=1.0)
                Yr = Y[np.ix_(i_m, j_m)]
                Zr2 = Z[np.ix_(i_m, j_m)].copy()
                nctrl = int(np.count_nonzero(j_m))
                rad = np.radians(rd)
                for k in range(nctrl):
                    x_ctrl = X[i_m, k]
                    span = float(np.max(X[:, k]) - np.min(X[:, k]))
                    f = np.zeros_like(x_ctrl) if span == 0 else c[k] * (x_ctrl - np.min(x_ctrl)) / span
                    Zr2[:, k] = Zr2[:, k] - f * np.sin(rad)
                _add(controls, "R", Xr, Zr, Yr)
                if pt_swapped.get("Z"):
                    _add(controls, "R", Xr, -Zr2, Yr)
                if j_m[-1]:
                    _apply_tip_defl(Xtip, Ztip, i_m, le, dX, dZ, z_sign=1.0)
                _blank_parent(X, Z, i_m, j_m, blank_x=True)

    if kind in ("wing", "wing 2"):
        tag = "WG" if kind == "wing" else "NP{1}"
        _add(out, tag, X, Y, Z)
        _add(out, tag, X, -Y, Z)
        if kind == "wing":
            _add(out, tag + "tip", Xtr, Ytip, Ztr)
            _add(out, tag + "tip", Xtl, -Ytip, Ztl)
        else:
            _add(out, tag + "tip", Xtip, Ytip, Ztip)
            _add(out, tag + "tip", Xtip, -Ytip, Ztip)
    elif kind in ("ht", "ht 2"):
        tag = "HT" if kind == "ht" else "NP{2}"
        _add(out, tag, X, Y, Z)
        _add(out, tag, X, -Y, Z)
        _add(out, tag + "tip", Xtip, Ytip, Ztip)
        _add(out, tag + "tip", Xtip, -Ytip, Ztip)
    elif kind in ("vt", "vt 2"):
        tag = "VT" if kind == "vt" else "NP{3}"
        _add(out, tag, X, Z, Y)
        _add(out, tag + "tip", Xtip, Ztip, Ytip)
        if pt_swapped.get("Z") or pt.get("DHDADI") or pt.get("DHDADO"):
            _add(out, tag, X, -Z, Y)
            ztip2 = Ztip - 2 * float(pt.get("Ztip", 0) or 0)
            _add(out, tag + "tip", Xtip, ztip2, Ytip)
    elif kind == "prop":
        px = float(pt_swapped.get("X", 0) or 0)
        pz = float(pt_swapped.get("Z", 0) or 0)
        py = float(pt_swapped.get("Y", 0) or 0)
        chrdr = float(pt.get("CHRDR", 0) or 0)
        Zp = Z + px - pz
        Zt = Ztip + px - pz
        _add(out, "prop", Zp, X - px + pz - chrdr / 2, Y)
        _add(out, "prop", Zt, Xtip - px + pz - chrdr / 2, Ytip)
        _add(out, "prop", Zp, -X + px + pz + chrdr / 2, -Y + 2 * py)
        _add(out, "prop", Zt, -Xtip + px + pz + chrdr / 2, -Ytip + 2 * py)
    out.extend(controls)
    return out


def _body_surfaces(pt: dict, n: int = _RES_BODY, extra_index: int = 0) -> list[SurfaceMesh]:
    n = n - (n % 4)
    nx = int(pt["NX"])
    x_st = np.asarray(pt["X"], dtype=float).reshape(-1)[:nx]
    zu = np.asarray(pt["ZU"], dtype=float).reshape(-1)[:nx]
    zl = np.asarray(pt["ZL"], dtype=float).reshape(-1)[:nx]
    r = np.asarray(pt["R"], dtype=float).reshape(-1)[:nx]
    zc = (zu + zl) / 2.0
    h = zu - zc
    x0 = float(pt.get("X0", 0) or 0)
    y0 = float(pt.get("Y0", 0) or 0)
    z0 = float(pt.get("Z0", 0) or 0)
    if extra_index:
        x_st = x_st + x0
        zu = zu + z0
        zl = zl + z0
        zc = (zu + zl) / 2.0
        h = zu - zc
    p = np.asarray(pt.get("P", np.ones(nx)), dtype=float).reshape(-1)
    if p.size < nx:
        p = np.ones(nx)
    X = np.zeros((nx, n))
    Y = np.zeros((nx, n))
    Z = np.zeros((nx, n))
    if np.any(p != 1):
        pu = 2.0**p
        pl = 2.0**p
        theta = np.linspace(0, np.pi / 2, n // 4)
        for i in range(nx):
            X[i, :] = x_st[i]
            cu, su = np.cos(theta) ** (2 / pu[i]), np.sin(theta) ** (2 / pu[i])
            cl, sl = np.cos(theta) ** (2 / pl[i]), np.sin(theta) ** (2 / pl[i])
            Y[i, : n // 4] = -r[i] * cu
            Y[i, n // 4 : n // 2] = (r[i] * cu)[::-1]
            Y[i, n // 2 : 3 * n // 4] = r[i] * cl
            Y[i, 3 * n // 4 :] = (-r[i] * cl)[::-1]
            Z[i, : n // 4] = zc[i] + h[i] * su
            Z[i, n // 4 : n // 2] = (zc[i] + h[i] * su)[::-1]
            Z[i, n // 2 : 3 * n // 4] = zc[i] - h[i] * sl
            Z[i, 3 * n // 4 :] = (zc[i] - h[i] * sl)[::-1]
    else:
        theta = np.linspace(0, 2 * np.pi, n)
        for i in range(nx):
            X[i, :] = x_st[i]
            Y[i, :] = r[i] * np.cos(theta)
            Z[i, :] = zc[i] + h[i] * np.sin(theta)
    tag = "BD" if extra_index == 0 else f"NB{{{extra_index}}}"
    out: list[SurfaceMesh] = []
    _add(out, tag, X, Y + y0, Z)
    if extra_index and y0:
        _add(out, tag, X, Y - y0, Z)
    return out
