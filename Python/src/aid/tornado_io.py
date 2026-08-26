import math
from copy import deepcopy

import numpy as np

from aid.aircraft import Aircraft
from aid.atmosphere import atmosphere
from aid.geometry import geometry


def _as_list(value):
    if isinstance(value, (list, tuple)):
        return list(value)
    return [value]


def _first(val) -> float:
    return float(np.asarray(val).reshape(-1)[0])


def _has_deflection(obj: dict, key: str) -> bool:
    val = obj.get(key, 0)
    if isinstance(val, (list, tuple)):
        arr = np.asarray(val).reshape(-1)
        return arr.size > 1 or bool(arr.size and np.any(arr))
    return bool(val)


def _swp_val(pt: dict, row: int = 1, col: int = 0) -> float:
    swp = np.asarray(pt["swp"], dtype=float)
    if swp.ndim == 1:
        return float(swp[row] if row < swp.size else swp[0])
    return float(swp[row, col])


def _ensure_planform(pt: dict, *, vertical: bool = False) -> dict:
    pt = deepcopy(pt)
    if "Xtip" not in pt or "swp" not in pt:
        geometry(pt, angl=False, type="v" if vertical else "")
    return pt


def _is_varying_airfoil(data) -> bool:
    if not isinstance(data, (list, tuple)) or len(data) != 2:
        return False
    a, b = data[0], data[1]
    if not isinstance(a, (list, tuple)) or not isinstance(b, (list, tuple)):
        return False
    if not a or not b:
        return False
    return isinstance(a[0], (list, tuple, np.ndarray))


def _init_geo(aero: dict) -> dict:
    return {
        "nwing": 0,
        "ref_point": np.array([0.0, 0.0, 0.0]),
        "CG": np.array([float(aero["XCG"]), 0.0, 0.0]),
        "nelem": [],
        "c": [],
        "T": [],
        "SW": [],
        "dihed": [],
        "b": [],
        "symetric": [],
        "startx": [],
        "starty": [],
        "startz": [],
        "TW": [],
        "foil": [],
        "fnx": [],
        "fsym": [],
        "fc": [],
        "flapped": [],
        "flap_vector": [],
        "flap_id": [],
        "meshtype": [],
        "ny": [],
        "nx": [],
    }


def _pad_rows(rows: list[np.ndarray]) -> np.ndarray:
    if not rows:
        return np.empty((0, 0))
    max_n = max(np.asarray(row).size for row in rows)
    padded = []
    for row in rows:
        arr = np.asarray(row, dtype=float).reshape(1, -1)
        if arr.shape[1] < max_n:
            arr = np.pad(arr, ((0, 0), (0, max_n - arr.shape[1])), constant_values=0)
        padded.append(arr)
    return np.vstack(padded)


def _finalize_geo(geo: dict) -> dict:
    array_keys_2d = (
        "c",
        "T",
        "SW",
        "dihed",
        "b",
        "startx",
        "starty",
        "startz",
        "fnx",
        "fsym",
        "fc",
        "flapped",
        "flap_vector",
        "meshtype",
        "ny",
        "nx",
    )
    for key in array_keys_2d:
        geo[key] = _pad_rows(geo[key])

    tw_rows = geo["TW"]
    if tw_rows:
        max_n = max(row.shape[1] for row in tw_rows)
        padded = []
        for row in tw_rows:
            if row.shape[1] < max_n:
                pad = np.zeros((1, max_n - row.shape[1], row.shape[2]))
                row = np.concatenate([row, pad], axis=1)
            padded.append(row)
        geo["TW"] = np.concatenate(padded, axis=0)
    else:
        geo["TW"] = np.empty((0, 0, 0))

    flap_id_rows = geo["flap_id"]
    if flap_id_rows:
        max_n = max(row.shape[0] for row in flap_id_rows)
        padded = []
        for row in flap_id_rows:
            arr = np.asarray(row, dtype=float)
            if arr.shape[0] < max_n:
                pad = np.zeros((max_n - arr.shape[0], arr.shape[1]))
                arr = np.vstack([arr, pad])
            padded.append(arr.reshape(1, max_n, arr.shape[1]))
        geo["flap_id"] = np.concatenate(padded, axis=0)
    else:
        geo["flap_id"] = np.empty((0, 0, 0))

    geo["nelem"] = np.asarray(geo["nelem"], dtype=int)
    geo["symetric"] = np.asarray(geo["symetric"], dtype=float)
    return geo


def write_geometry(
    pt: dict,
    controls: list,
    ni: int,
    nj: int,
    m: tuple[int, int],
    geo: dict | None = None,
    type: str = "h",
) -> dict:
    if geo is None:
        geo = _init_geo({"XCG": 0.0})

    pt = _ensure_planform(pt, vertical=(type == "v"))

    geo["nwing"] = geo["nwing"] + 1
    geo["symetric"].append(1.0)

    eta = np.array([0.0, 1.0])
    if m[0] > 1 or m[1] > 1:
        eta = np.cos(np.linspace(np.pi / 2, 0, nj))
        nj = 1
    flap_id = np.zeros_like(eta)

    sspn = float(pt["SSPN"])
    for i, cs in enumerate(controls):
        spanfi = float(cs["SPANFI"]) / sspn
        spanfo = float(cs["SPANFO"]) / sspn
        eta = np.concatenate([[spanfi, spanfo], eta])
        flap_id = np.concatenate([[i + 1, i + 1], flap_id])

    jbrk = None
    sspnop = float(pt.get("SSPNOP") or 0)
    if sspnop:
        eta = np.concatenate([eta, [sspnop / sspn]])
        jbrk = len(eta)
        flap_id = np.concatenate([flap_id, [0.0]])

    eta, index = np.unique(eta, return_index=True)
    flap_id = flap_id[index]
    flap_pos = np.where(flap_id)[0]
    flap_index: list[list[int]] = []
    if flap_pos.size == 2:
        flap_index.append(list(range(flap_pos[0], flap_pos[1])))
    elif flap_pos.size == 3:
        flap_index.append(list(range(flap_pos[0], flap_pos[1])))
        flap_index.append(list(range(flap_pos[1], flap_pos[2])))
    elif flap_pos.size == 4:
        flap_index.append(list(range(flap_pos[0], flap_pos[1])))
        flap_index.append(list(range(flap_pos[2], flap_pos[3])))

    if sspnop:
        eta0 = np.array([0.0, sspnop / sspn, 1.0])
        c0 = np.array([pt["CHRDR"], pt["CHRDBP"], pt["CHRDTP"]], dtype=float)
        x0 = np.array([pt["X"], pt["Xbrk"], pt["Xtip"]], dtype=float)
        y0 = np.array([pt["Y"], pt["Y"] + sspnop, pt["Y"] + sspn], dtype=float)
        z0 = np.array([pt["Z"], pt["Zbrk"], pt["Ztip"]], dtype=float)
        jbrk_idx = int(np.where(index == jbrk - 1)[0][0]) if jbrk is not None else None
        jspan = (
            list(range(jbrk_idx, len(index) - 1))
            if jbrk_idx is not None
            else []
        )
    else:
        eta0 = np.array([0.0, 1.0])
        c0 = np.array([pt["CHRDR"], pt["CHRDTP"]], dtype=float)
        x0 = np.array([pt["X"], pt["Xtip"]], dtype=float)
        y0 = np.array([pt["Y"], pt["Y"] + sspn], dtype=float)
        z0 = np.array([pt["Z"], pt["Ztip"]], dtype=float)
        jspan = []

    n = len(eta) - 1
    geo["nelem"].append(n)
    c = np.interp(eta, eta0, c0)
    geo["c"].append(c[:-1])
    geo["T"].append(c[1:] / c[:-1])
    sw_row = np.full(n, np.deg2rad(_swp_val(pt, 1, 0)))
    if jspan:
        sw_row[jspan] = np.deg2rad(_swp_val(pt, 1, 1))
    geo["SW"].append(sw_row)
    dihed_row = np.full(n, np.deg2rad(float(pt["DHDADI"])))
    if jspan:
        dihed_row[jspan] = np.deg2rad(float(pt["DHDADO"]))
    geo["dihed"].append(dihed_row)
    geo["b"].append((eta[1:] - eta[:-1]) * sspn)
    geo["startx"].append(np.interp(eta[:-1], eta0, x0))
    geo["starty"].append(np.interp(eta[:-1], eta0, y0))
    geo["startz"].append(np.interp(eta[:-1], eta0, z0))

    theta = (float(pt["i"]) - float(pt["TWISTA"]) * eta ** m[0]) * np.pi / 180
    tw = np.zeros((1, n, 2))
    tw[0, :, 0] = theta[:-1]
    tw[0, :, 1] = theta[1:]
    geo["TW"].append(tw)

    data = pt["DATA"]
    foil_wing: list[list] = [[None] * n for _ in range(2)]
    if _is_varying_airfoil(data):
        data1 = np.asarray(data[0], dtype=float)
        data2 = np.asarray(data[1], dtype=float)
        n_pts = min(len(data1), len(data2))
        if len(data1) > len(data2):
            pts1 = np.unique(np.round(np.linspace(0, len(data1) - 1, n_pts)).astype(int))
            data1 = data1[pts1]
        elif len(data2) > len(data1):
            pts2 = np.unique(np.round(np.linspace(0, len(data2) - 1, n_pts)).astype(int))
            data2 = data2[pts2]
        le = int(math.ceil(n_pts / 2))
        if n_pts % 2:
            data1 = np.insert(data1, le, data1[le - 1], axis=0)
            data2 = np.insert(data2, le, data2[le - 1], axis=0)
        x1, z1 = data1[:, 0], data1[:, 1]
        x2, z2 = data2[:, 0], data2[:, 1]
        x = x1 + (x2 - x1) * eta[:, np.newaxis] ** m[1]
        z = z1 + (z2 - z1) * eta[:, np.newaxis] ** m[1]
        foil_wing[0][0] = np.column_stack([x[:, 0], z[:, 0]])
        foil_wing[1][0] = np.column_stack([x[:, 1], z[:, 1]])
        for i in range(1, n):
            foil_wing[0][i] = np.column_stack([x[:, i], z[:, i]])
            foil_wing[1][i] = np.column_stack([x[:, i + 1], z[:, i + 1]])
    else:
        foil_coords = np.asarray(data, dtype=float)
        for j in range(n):
            foil_wing[0][j] = foil_coords
            foil_wing[1][j] = foil_coords
    geo["foil"].append(foil_wing)

    fnx_row = np.zeros(n)
    fsym_row = np.zeros(n)
    fc_row = np.zeros(n)
    flapped_row = np.zeros(n)
    flap_vector_row = np.zeros(n)
    flap_id_row = np.zeros((n, 2))

    for i, cs in enumerate(controls):
        if i >= len(flap_index):
            break
        idxs = flap_index[i]
        flap_id_row[idxs, i] = i + 1
        fsym_row[idxs] = 1.0
        root_i = int(np.where(flap_id == i + 1)[0][0])
        fc_row[idxs] = float(cs["CHRDFI"]) / float(c[root_i])
        ni_flap = int(math.ceil(fc_row[idxs[0]] * ni))
        fnx_row[idxs] = ni_flap
        flapped_row[idxs] = 1.0
        if "DELTA" not in cs:
            if cs.get("DELTAR", 0) != -cs.get("DELTAR", 0):
                fsym_row[idxs] = 0.0
            cs = dict(cs)
            cs["DELTA"] = -float(cs.get("DELTAL", 0))
        delta = cs["DELTA"]
        delta_val = float(np.asarray(delta).reshape(-1)[0]) * np.pi / 180
        flap_vector_row[idxs] = delta_val

    geo["fnx"].append(fnx_row)
    geo["fsym"].append(fsym_row)
    geo["fc"].append(fc_row)
    geo["flapped"].append(flapped_row)
    geo["flap_vector"].append(flap_vector_row)
    geo["flap_id"].append(flap_id_row)

    meshtype_row = np.full(n, 6.0)
    meshtype_row[-1] = 3.0
    geo["meshtype"].append(meshtype_row)
    geo["nx"].append(np.full(n, ni) - fnx_row)
    geo["ny"].append(np.ceil(nj * geo["b"][-1] / sspn))

    if type == "v":
        geo["dihed"][-1] = np.pi / 2 - np.abs(geo["dihed"][-1])
        if not pt.get("gamma") and not pt.get("Y"):
            geo["symetric"][-1] = 0.0
        else:
            geo["symetric"][-1] = 1.0

    return geo


def _build_state(ac: Aircraft, atm: dict) -> dict:
    aero = ac.AERO
    mach = _first(aero["MACH"])
    alschd = _as_list(aero["ALSCHD"])
    n = len(alschd)
    alpha_deg = float(alschd[max(0, math.ceil(n / 2) - 1)])
    alt_ft = _first(aero["ALT"])

    return {
        "AS": mach * atm["a"] / 3.28084,
        "alpha": alpha_deg * np.pi / 180,
        "betha": 0.0,
        "P": 0.0,
        "Q": 0.0,
        "R": 0.0,
        "alphadot": 0.0,
        "bethadot": 0.0,
        "ALT": alt_ft / 3.28084,
        "rho": atm["D"] * 515.379,
        "pgcorr": 0.0,
    }


def _cmp_enabled(plot_cmp: list, index: int) -> bool:
    if index >= len(plot_cmp):
        return False
    return bool(plot_cmp[index])


def tornado_io(ac: Aircraft, mesh: tuple[str, str]) -> tuple[dict, dict]:
    nj = int(mesh[0])
    ni = int(mesh[1])
    m = [1, 1]
    if len(mesh) == 3:
        if ac.WG.get("TWISTA"):
            m[0] = int(mesh[2])
        else:
            m[1] = int(mesh[2])
    elif len(mesh) >= 4:
        m[0] = int(mesh[2])
        m[1] = int(mesh[3])

    geo = None
    cmp = ac.plot_cmp

    if _cmp_enabled(cmp, 0):
        cs: list = []
        if _has_deflection(ac.F, "DELTA"):
            cs.append(ac.F)
        if _has_deflection(ac.A, "DELTAL") or _has_deflection(ac.A, "DELTAR"):
            cs.append(ac.A)
        if geo is None:
            geo = _init_geo(ac.AERO)
        geo = write_geometry(ac.WG, cs, ni, nj, tuple(m), geo)

    if _cmp_enabled(cmp, 1):
        cs = []
        if _has_deflection(ac.E, "DELTA"):
            cs.append(ac.E)
        if geo is None:
            geo = _init_geo(ac.AERO)
        geo = write_geometry(
            ac.HT, cs, round(ni / 2), round(nj / 2), (1, 1), geo
        )

    if _cmp_enabled(cmp, 2):
        cs = []
        if _has_deflection(ac.R, "DELTA"):
            cs.append(ac.R)
        if geo is None:
            geo = _init_geo(ac.AERO)
        geo = write_geometry(
            ac.VT, cs, round(ni / 2), round(nj / 2), (1, 1), geo, type="v"
        )

    np_types = ("h", "h", "v", "v")
    for i in range(3):
        np_pt = ac.NP[i] if i < len(ac.NP) else None
        if np_pt and _cmp_enabled(cmp, 4 + i):
            if geo is None:
                geo = _init_geo(ac.AERO)
            geo = write_geometry(
                np_pt,
                [],
                round(ni / 2),
                round(nj / 2),
                (1, 1),
                geo,
                type=np_types[i],
            )

    if geo is None:
        geo = _init_geo(ac.AERO)
    geo = _finalize_geo(geo)

    alt_ft = _first(ac.AERO["ALT"])
    atm = atmosphere(alt_ft)
    state = _build_state(ac, atm)
    return geo, state
