import math
from copy import deepcopy
from pathlib import Path

import numpy as np

from aid.aircraft import Aircraft


def _last(val) -> float:
    return float(np.asarray(val).reshape(-1)[-1])


def _first(val) -> float:
    return float(np.asarray(val).reshape(-1)[0])


def _cdp(ac: Aircraft) -> float:
    """Match run_aid_batch.m: AC.CD0 = WG.CD0 when present, else 0."""
    if "CD0" in ac.WG:
        return float(ac.WG["CD0"])
    return 0.0


def _prepare_flap_data(geo: dict) -> None:
    flap_id = np.asarray(geo["flap_id"], dtype=float)
    if flap_id.size:
        flap_id = np.concatenate(
            [flap_id, np.zeros((flap_id.shape[0], 1, flap_id.shape[2]))],
            axis=1,
        )
        flap_id[:, 1:, :] = np.maximum(flap_id[:, :-1, :], flap_id[:, 1:, :])
        geo["flap_id"] = flap_id

    fc = np.asarray(geo["fc"], dtype=float)
    if fc.size:
        fc = np.concatenate([fc, np.zeros((fc.shape[0], 1))], axis=1)
        fc[:, 1:] = np.maximum(fc[:, :-1], fc[:, 1:])
        geo["fc"] = fc


def _write_airfoil_file(path: Path, foil: np.ndarray) -> None:
    arr = np.asarray(foil, dtype=float)
    with path.open("w", encoding="ascii") as afid:
        for x, z in arr[::-1]:
            afid.write(f"{x:.6f} {z:.6f}\n")


def _write_surface(
    fid,
    run_dir: Path,
    label: str,
    cs_default: str,
    geo: dict,
    k: int,
    ni: int,
    nj: int,
) -> None:
    n = int(geo["nelem"][k])

    fid.write("\n#======================================================\n")
    fid.write("SURFACE\n")
    fid.write(f"{label}\n")
    if n >= 4 or n == nj - 1:
        fid.write(f"{ni} 1 {nj} -2\n")
    else:
        fid.write(f"{ni} 1.0 {nj} -1.1\n")

    fid.write("\nCOMPONENT\n1\n")

    dihed0 = float(geo["dihed"][k, 0])
    starty0 = float(geo["starty"][k, 0])
    if dihed0 != math.pi / 2 or starty0:
        fid.write("\nYDUPLICATE\n0.0\n")

    fid.write("\nSCALE\n1.0 1.0 1.0\n")
    fid.write("\nTRANSLATE\n0.0 0.0 0.0\n")
    fid.write("\nANGLE\n0.0\n")

    starty = geo["starty"][k, :n].copy()
    startz = geo["startz"][k, :n].copy()
    for i in range(1, n):
        dy = float(geo["starty"][k, i] - geo["starty"][k, i - 1])
        dz = float(geo["startz"][k, i] - geo["startz"][k, i - 1])
        sine = math.sin(float(geo["dihed"][k, i - 1]))
        cosine = math.cos(float(geo["dihed"][k, i - 1]))
        starty[i] = starty[i - 1] + dy * cosine - dz * sine
        startz[i] = startz[i - 1] + dz * cosine + dy * sine

    x = np.concatenate(
        [
            geo["startx"][k, :n],
            [
                geo["startx"][k, n - 1]
                + geo["b"][k, n - 1] * math.tan(float(geo["SW"][k, n - 1]))
            ],
        ]
    )
    y = np.concatenate(
        [
            starty,
            [starty[n - 1] + geo["b"][k, n - 1] * math.cos(float(geo["dihed"][k, n - 1]))],
        ]
    )
    z = np.concatenate(
        [
            startz,
            [startz[n - 1] + geo["b"][k, n - 1] * math.sin(float(geo["dihed"][k, n - 1]))],
        ]
    )

    tip_t = float(geo["T"][k, n - 1])
    if math.isnan(tip_t) or tip_t <= 0:
        tip_c = float(geo["c"][k, n - 1])
    else:
        tip_c = float(geo["c"][k, n - 1] * tip_t)
    c = np.concatenate([geo["c"][k, :n], [tip_c]])

    tw = np.concatenate([geo["TW"][k, :n, 0], [geo["TW"][k, n - 1, 1]]])

    wing_foil = geo["foil"][k]
    foils = [wing_foil[j][0] for j in range(n)] + [wing_foil[n - 1][1]]

    nsect = n + 1
    if math.hypot(y[n] - y[n - 1], z[n] - z[n - 1]) < 0.05:
        nsect = n

    fc_row = geo["fc"][k].copy()
    flap_id = geo["flap_id"][k]

    for j in range(nsect):
        fid.write("\nSECTION\n")
        fid.write(f"{x[j]:.2f} {y[j]:.2f} {z[j]:.2f} {c[j]:.2f} {tw[j]:.2f}\n")

        fname = f"{label}.{j + 1}"
        _write_airfoil_file(run_dir / fname, foils[j])
        fid.write(f"\nAFILE\n{fname}\n")

        cs = cs_default
        if flap_id[j, 0]:
            if label == "WG":
                cs = "flap"
            elif label == "HT":
                cs = "elevator"
            elif label == "VT":
                cs = "rudder"
            fid.write("\nCONTROL\n")
            fid.write(f"{cs} {fc_row[j]:.1f} 0 0 0 1\n")

        if flap_id[j, 1]:
            if flap_id[j, 0]:
                fc_row[j] = fc_row[j + 1]
            fid.write("\nCONTROL\n")
            fid.write(f"aileron {fc_row[j]:.1f} 0 0 0 -1\n")

        foil_arr = np.asarray(foils[j], dtype=float)
        t = float(np.max(foil_arr[:, 1]) - np.min(foil_arr[:, 1]))
        fid.write(f"\nCLAF\n{1 + 0.77 * t:.4f}\n")


def write_avl_geometry(
    ac: Aircraft,
    geo: dict,
    state: dict,
    run_dir: Path,
    ni: int,
    nj: int,
) -> None:
    del state  # used by Task 50 Write_Case / run_avl
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)

    geo = deepcopy(geo)
    _prepare_flap_data(geo)

    case_id = "geometry"
    avl_path = run_dir / f"{case_id}.avl"
    cd0 = _cdp(ac)

    labels = ["WG", "HT", "VT"] + [f"Planform {i + 4}" for i in range(3)]
    control_names = ["flap", "elevator", "rudder", "", "", ""]

    nwing = min(int(geo["nwing"]), 3)

    with avl_path.open("w", encoding="ascii") as fid:
        fid.write(f"{case_id}\n")
        fid.write("\n#MACH\n")
        fid.write(f"{_first(ac.AERO['MACH']):.6f}\n")
        fid.write("\n#IYsym IZsym Zsym\n")
        fid.write("0 0 0.0\n")
        fid.write("\n#Sref Cref Bref\n")
        fid.write(
            f"{_last(ac.WG['S']):.4f} {_last(ac.WG['cbar']):.4f} {float(ac.WG['b']):.4f}\n"
        )
        fid.write("\n#Xref Yref Zref\n")
        fid.write(f"{float(ac.AERO['XCG']):.4f} 0 {float(ac.AERO['ZCG']):.4f}\n")
        fid.write("\n#CDp\n")
        fid.write(f"{cd0:.3f}\n")

        for i in range(nwing):
            _write_surface(
                fid,
                run_dir,
                labels[i],
                control_names[i] if i < len(control_names) else "",
                geo,
                i,
                ni,
                nj,
            )
