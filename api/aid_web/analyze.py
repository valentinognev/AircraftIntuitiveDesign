from __future__ import annotations

import math
from pathlib import Path
from tempfile import TemporaryDirectory

from aid.aircraft import Aircraft
from aid.avl_io import run_avl_full
from aid.control_report import control_report
from aid.datcom_run import run_datcom
from aid.flow5_io import run_flow5
from aid.lifting_line import lifting_line
from aid.tornado.boundary import set_boundary
from aid.tornado.coeff import coeff_create
from aid.tornado.lattice import lattice_setup
from aid.tornado.solver import solve
from aid.tornado.spanwise import tornado_spanwise
from aid.tornado_io import tornado_io
from aid.viz import planform_stations

SOLVERS = frozenset({"datcom", "tornado", "avl", "flow5"})
DEFAULT_MESH = {
    "tornado": ("10", "5"),
    "avl": ("10", "10"),
    "flow5": ("10", "10"),
}


def _jsonable(value):
    if isinstance(value, dict):
        return {k: _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    if hasattr(value, "tolist"):
        converted = value.tolist()
        if isinstance(converted, (list, tuple, dict)):
            return _jsonable(converted)
        value = converted
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def _as_float_list(value) -> list[float]:
    if value is None:
        return []
    if hasattr(value, "tolist"):
        value = value.tolist()
    if isinstance(value, (list, tuple)):
        return [float(x) for x in value]
    return [float(value)]


def _coeff_row(raw: dict, *keys: str) -> list[float]:
    for key in keys:
        if key in raw:
            return _as_float_list(raw[key])
    return []


def to_handshake_payload(raw: dict, mach: float, solver: str = "datcom") -> dict:
    return {
        "source": "aid",
        "solver": solver,
        "axes": {
            "mach": [float(mach)],
            "alpha": _as_float_list(raw.get("alpha")),
            "beta": [0],
        },
        "tables": {
            "cl": [_coeff_row(raw, "CL", "cl", "CLtot")],
            "cd": [_coeff_row(raw, "CD", "cd", "CDtot")],
            "cm": [_coeff_row(raw, "Cm", "cm", "Cmtot")],
        },
        "ref": {},
    }


payload_from_aid_raw = to_handshake_payload


def mapper_shaped_raw(aid_raw: dict) -> dict:
    raw = _jsonable(aid_raw)
    raw["alpha"] = _as_float_list(raw.get("alpha"))
    raw["CL"] = _coeff_row(raw, "CL", "cl", "CLtot")
    raw["CD"] = _coeff_row(raw, "CD", "cd", "CDtot")
    raw["Cm"] = _coeff_row(raw, "Cm", "cm", "Cmtot")
    mach = raw["MACH"] if "MACH" in raw else raw.get("mach")
    raw["MACH"] = _as_float_list(mach)
    return raw


def _mach_float(raw: dict) -> float:
    machs = _as_float_list(raw.get("MACH", raw.get("mach")))
    return machs[0] if machs else 0.3


def _finite_floats(value) -> list[float] | None:
    if hasattr(value, "tolist"):
        value = value.tolist()
    if not isinstance(value, (list, tuple)):
        return None
    out: list[float] = []
    for item in value:
        try:
            number = float(item)
        except (TypeError, ValueError):
            return None
        if not math.isfinite(number):
            return None
        out.append(number)
    return out


def handbook_spanwise(ac: Aircraft) -> dict | None:
    try:
        y, c, _, _, theta = planform_stations(ac.WG, 12, True, "wing")
        dist = lifting_line(ac, y, c, theta)
        ys = _finite_floats(dist["y"])
        cls = _finite_floats(dist["Cl"])
        if ys is None or cls is None or len(ys) != len(cls):
            return None
        return {"y": ys, "Cl": cls}
    except Exception:
        return None


def _analyze_result(solver: str, aid_raw: dict, ac: Aircraft) -> dict:
    raw = mapper_shaped_raw(aid_raw)
    result = {
        "ok": True,
        "solver": solver,
        "raw": raw,
        "payload": to_handshake_payload(raw, _mach_float(raw), solver=solver),
    }
    handbook = handbook_spanwise(ac)
    if isinstance(handbook, dict):
        result["handbook"] = handbook
    return result


def _mesh_tuple(solver: str, mesh: tuple[str, ...] | None) -> tuple[str, ...]:
    if mesh:
        return tuple(str(x) for x in mesh)
    return DEFAULT_MESH[solver]


def run_tornado(ac: Aircraft, mesh: tuple[str, ...]) -> dict:
    geo, state = tornado_io(ac, mesh)
    lattice, ref = lattice_setup(geo, state, 0)
    lattice = set_boundary(lattice, geo, state)
    raw = solve(state, geo, lattice)
    coeffs = coeff_create(raw, lattice, state, ref, geo)
    coeffs["alpha"] = float(state["alpha"]) * 180.0 / math.pi
    if "MACH" not in coeffs and "mach" not in coeffs:
        coeffs["MACH"] = ac.AERO.get("MACH")
    try:
        coeffs["spanwise"] = tornado_spanwise(coeffs, lattice, geo, state, ac)
    except Exception:
        pass
    return coeffs


def analyze_datcom(ac: Aircraft) -> dict:
    with TemporaryDirectory() as td:
        aid_raw = run_datcom(ac, Path(td))
    return _analyze_result("datcom", aid_raw, ac)


def analyze_tornado(ac: Aircraft, mesh: tuple[str, ...]) -> dict:
    return _analyze_result("tornado", run_tornado(ac, mesh), ac)


def analyze_avl(ac: Aircraft, mesh: tuple[str, ...]) -> dict:
    with TemporaryDirectory() as td:
        aid_raw = run_avl_full(ac, mesh, Path(td))
    return _analyze_result("avl", aid_raw, ac)


def analyze_flow5(ac: Aircraft, mesh: tuple[str, ...]) -> dict:
    return _analyze_result("flow5", run_flow5(ac, mesh), ac)


def analyze(
    ac: Aircraft,
    solver: str = "datcom",
    mesh: tuple[str, ...] | None = None,
) -> dict:
    solver = solver or "datcom"
    if solver not in SOLVERS:
        raise ValueError(f"unknown solver: {solver}")
    if solver == "datcom":
        return analyze_datcom(ac)
    mesh = _mesh_tuple(solver, mesh)
    if solver == "tornado":
        return analyze_tornado(ac, mesh)
    if solver == "avl":
        return analyze_avl(ac, mesh)
    return analyze_flow5(ac, mesh)


def control_derivatives(
    ac: Aircraft,
    solver: str,
    deltas_deg=None,
    mesh: tuple[str, ...] | None = None,
) -> dict:
    if solver in DEFAULT_MESH:
        mesh = _mesh_tuple(solver, mesh)
    return control_report(ac, solver, deltas_deg=deltas_deg, mesh=mesh)
