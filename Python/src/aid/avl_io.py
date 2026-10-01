import math
import subprocess
from copy import deepcopy
from pathlib import Path

import numpy as np

from aid.aircraft import Aircraft
from aid.avl_parse import parse_run_case_header, parse_st
from aid.paths import avl_bin
from aid.tornado_io import tornado_io


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
    *,
    cspace: float | None = None,
    sspace: float | None = None,
) -> None:
    n = int(geo["nelem"][k])

    fid.write("\n#======================================================\n")
    fid.write("SURFACE\n")
    fid.write(f"{label}\n")
    if cspace is None or sspace is None:
        if n >= 4 or n == nj - 1:
            c_use, s_use = 1.0, -2.0
        else:
            c_use, s_use = 1.0, -1.1
        if cspace is None:
            cspace = c_use
        if sspace is None:
            sspace = s_use
    fid.write(f"{ni} {cspace} {nj} {sspace}\n")

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
        # AVL_IO.m updates geo.starty(k,i-1) in place; dy/dz use the running value.
        dy = float(geo["starty"][k, i] - starty[i - 1])
        dz = float(geo["startz"][k, i] - startz[i - 1])
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
    *,
    cspace: float | None = None,
    sspace: float | None = None,
) -> None:
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)

    geo = deepcopy(geo)
    _prepare_flap_data(geo)

    case_id = "geometry"
    avl_path = run_dir / f"{case_id}.avl"
    cd0 = _cdp(ac)

    labels = ["WG", "HT", "VT"] + [f"Planform {i + 4}" for i in range(3)]
    control_names = ["flap", "elevator", "rudder", "", "", ""]

    # AVL cannot use NP{4} propeller; keep WG/HT/VT only (MATLAB AVL_IO nwing<=3).
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
                cspace=cspace,
                sspace=sspace,
            )


def write_case(case_id: str, state: dict, run_dir: Path, alphas: list[float]) -> None:
    """One AVL process, one solved angle per ``alphas`` entry (degrees)."""
    if not alphas:
        raise ValueError("AERO.ALSCHD is empty")
    run_dir = Path(run_dir)
    run_path = run_dir / f"{case_id}.run"
    as_val = float(state["AS"])
    sb_at = next((i for i, angle in enumerate(alphas) if float(angle) == 0.0), 0)

    with run_path.open("w", encoding="ascii") as fid:
        fid.write(f"LOAD {case_id}.avl\n")
        mass_path = run_dir / f"{case_id}.mass"
        if mass_path.is_file():
            fid.write(f"MASS {case_id}.mass\n")
            fid.write("MSET 1\n")
        fid.write("0\n")
        fid.write("PLOP\ng\n\n")
        fid.write("OPER\n")
        fid.write("c1\n")
        fid.write(f"v {as_val:6.4f}\n\n")
        for i, angle in enumerate(alphas):
            fid.write(f"a a {float(angle):.4f}\n")
            fid.write("x\n")
            fid.write("st\n")
            fid.write(f"{case_id}_{i}.st\n")
            if i == sb_at:
                fid.write("sb\n")
                fid.write(f"{case_id}.sb\n")
        fid.write("\n")
        fid.write("Quit\n")


_AVL_RUN_KEYS = (
    "alpha",
    "beta",
    "mach",
    "CXtot",
    "CYtot",
    "CZtot",
    "Cltot",
    "Cmtot",
    "Cntot",
    "CLtot",
    "CDtot",
    "CDvis",
    "CDind",
    "CDff",
    "CLff",
    "CYff",
    "e",
    "surface",
)


def merge_avl_st(path: Path) -> dict:
    """Stability-axis derivatives plus run-case totals from one ``.st`` file."""
    st = parse_st(path)
    rc = parse_run_case_header(path)
    for key in _AVL_RUN_KEYS:
        if key not in rc:
            continue
        if key not in st or st[key] in ([], None):
            st[key] = rc[key]
    return st


_SWEEP_TOTALS = (
    "CXtot", "CYtot", "CZtot", "Cltot", "Cmtot", "Cntot",
    "CLtot", "CDtot", "CDvis", "CDind", "CDff", "CLff", "CYff", "e",
)
_SWEEP_DERIVS = (
    "CLa", "CYa", "Cla", "Cma", "Cna",
    "CLb", "CYb", "Clb", "Cmb", "Cnb",
    "CLp", "CYp", "Clp", "Cmp", "Cnp",
    "CLq", "CYq", "Clq", "Cmq", "Cnq",
    "CLr", "CYr", "Clr", "Cmr", "Cnr",
    "NP",
)


def stack_avl_cases(paths: list[Path]) -> dict:
    """One merged ``.st`` per angle, in path order. No interpolation."""
    if not paths:
        raise ValueError("AVL sweep is empty")
    cases = [merge_avl_st(path) for path in paths]
    out: dict = {
        "alpha": [float(case["alpha"]) for case in cases],
        "surface": list(cases[0].get("surface") or []),
    }
    for key in (*_SWEEP_TOTALS, *_SWEEP_DERIVS):
        out[key] = [float(case[key]) for case in cases]
    return out


def run_avl(run_dir: Path, *, timeout: float = 120) -> None:
    """Run AVL in ``run_dir`` with ``geometry.run`` on stdin."""
    run_dir = Path(run_dir)
    run_file = run_dir / "geometry.run"
    with run_file.open(encoding="ascii") as run_in:
        subprocess.run(
            [str(avl_bin())],
            stdin=run_in,
            cwd=run_dir,
            check=False,
            timeout=timeout,
            capture_output=True,
            text=True,
        )


def _avl_spacing_attempts(ni: int, nj: int) -> list[tuple[int, int, float | None, float | None]]:
    """Primary mesh, then documented fallbacks used only when a geometry_{i}.st is missing.

    Each tuple is (ni, nj, cspace, sspace). None spacing keeps the writer default
    (cosine -2 when nelem>=4, else weighted outboard -1.1).
    """
    nj2 = max(nj + 2, min(nj * 2, nj + 8))
    nj_lo = max(4, nj - 2)
    return [
        (ni, nj, None, None),
        (ni, nj, 1.0, -1.1),
        (ni, nj, 1.0, 0.0),
        (ni, nj2, 1.0, -2.0),
        (ni, nj2, 1.0, 0.0),
        (ni, nj_lo, 1.0, 0.0),
    ]


def _insert_ref_solve(run_path: Path) -> None:
    """Unconstrained OPER ``x`` before the first commanded ``a a``."""
    text = run_path.read_text(encoding="ascii")
    marker = "\na a "
    idx = text.find(marker)
    if idx < 0:
        raise ValueError("geometry.run has no alpha command")
    text = text[: idx + 1] + "x\nst\ngeometry_ref.st\n" + text[idx + 1 :]
    run_path.write_text(text, encoding="ascii")


def run_avl_full(ac: Aircraft, mesh: tuple[str, str], run_dir: Path) -> dict:
    """Tornado geo → AVL geometry/case → run → stack one case per scheduled angle.

    An unconstrained solve is inserted before the first ``a a`` and returned as
    ``ref``. If AVL rejects the primary cosine mesh (a ``geometry_{i}.st`` or
    ``geometry_ref.st`` is missing), retry with weighted-outboard / equal
    spanwise spacing and slightly finer or coarser nj from the same dialog
    values. Coefficients are never invented.
    """
    run_dir = Path(run_dir)
    geo, state = tornado_io(ac, mesh)
    alphas = [float(a) for a in np.asarray(ac.AERO["ALSCHD"], dtype=float).reshape(-1)]
    if not alphas:
        raise ValueError("AERO.ALSCHD is empty")
    nj = int(mesh[0])
    ni = int(mesh[1])
    last_exc: Exception | None = None
    for try_ni, try_nj, cspace, sspace in _avl_spacing_attempts(ni, nj):
        write_avl_geometry(
            ac, geo, state, run_dir, try_ni, try_nj, cspace=cspace, sspace=sspace
        )
        write_case("geometry", state, run_dir, alphas)
        _insert_ref_solve(run_dir / "geometry.run")
        for path in run_dir.glob("geometry_*.st"):
            path.unlink()
        sb_path = run_dir / "geometry.sb"
        if sb_path.is_file():
            sb_path.unlink()
        st_paths = [run_dir / f"geometry_{i}.st" for i in range(len(alphas))]
        ref_path = run_dir / "geometry_ref.st"
        if ref_path.is_file():
            ref_path.unlink()

        def _ready() -> bool:
            return ref_path.is_file() and all(path.is_file() for path in st_paths)

        try:
            run_avl(run_dir, timeout=120 * len(alphas))
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
            last_exc = exc
            if not _ready():
                continue
            raise
        if _ready():
            out = stack_avl_cases(st_paths)
            out["ref"] = merge_avl_st(ref_path)
            return out
        missing = ref_path if not ref_path.is_file() else next(
            path for path in st_paths if not path.is_file()
        )
        last_exc = FileNotFoundError(f"AVL produced no {missing}")
    if last_exc is not None:
        raise last_exc
    raise FileNotFoundError(f"AVL produced no geometry.st in {run_dir}")
