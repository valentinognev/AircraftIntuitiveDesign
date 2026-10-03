"""Compare Python solver outputs against MATLAB gold results."""

from __future__ import annotations

import json
import subprocess
from dataclasses import replace
from pathlib import Path
from typing import Any

import numpy as np

from aid.aircraft import Aircraft, load_jsonc
from aid.avl_io import run_avl_full
from aid.datcom_run import run_datcom
from aid.paths import models_dir, results_dir
from aid.tornado.boundary import set_boundary
from aid.tornado.coeff import coeff_create
from aid.tornado.lattice import lattice_setup
from aid.tornado.solver import solve
from aid.tornado_io import tornado_io

# Spec §13 — Tornado port tolerances
_FORCE_RTOL, _FORCE_ATOL = 1e-4, 1e-5
_MOMENT_RTOL, _MOMENT_ATOL = 1e-4, 1e-5
_DERIV_RTOL, _DERIV_ATOL = 1e-3, 1e-4

# Shared Fortran DATCOM/AVL — parser precision
_PARSER_ATOL = 1e-6

_TORNADO_MESH = ("10", "5")
_AVL_MESH = ("10", "10")

_TORNADO_FORCES = ("CL", "CD", "CY")
_TORNADO_MOMENTS = ("Cm", "Cl", "Cn")
_TORNADO_DERIVS = ("CL_a", "Cm_a", "CY_b", "Cl_b", "Cn_b")


def _to_jsonable(obj: Any) -> Any:
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, (np.floating, np.integer)):
        return obj.item()
    if isinstance(obj, dict):
        return {k: _to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_jsonable(v) for v in obj]
    return obj


def _run_datcom_safe(ac: Aircraft, workdir: Path) -> dict:
    workdir.mkdir(parents=True, exist_ok=True)
    try:
        coeffs = run_datcom(ac, workdir)
        return {"status": "ok", "coeffs": _to_jsonable(coeffs), "error": None}
    except (
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
        OSError,
        ValueError,
    ) as exc:
        return {"status": "failed", "coeffs": None, "error": str(exc)}


def _run_tornado(ac: Aircraft) -> dict:
    try:
        geo, state = tornado_io(ac, _TORNADO_MESH)
        lattice, ref = lattice_setup(geo, state, 0)
        lattice = set_boundary(lattice, geo, state)
        raw = solve(state, geo, lattice)
        coeffs = coeff_create(raw, lattice, state, ref, geo)
        slim = {k: coeffs[k] for k in (*_TORNADO_FORCES, *_TORNADO_MOMENTS, *_TORNADO_DERIVS)}
        return {"status": "ok", "coeffs": _to_jsonable(slim), "error": None}
    except Exception as exc:  # noqa: BLE001 — record solver failures in report
        return {"status": "failed", "coeffs": None, "error": str(exc)}


def _run_avl(ac: Aircraft, workdir: Path) -> dict:
    workdir.mkdir(parents=True, exist_ok=True)
    try:
        coeffs = run_avl_full(ac, _AVL_MESH, workdir)
        return {"status": "ok", "coeffs": _to_jsonable(coeffs), "error": None}
    except (
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
        OSError,
        ValueError,
    ) as exc:
        return {"status": "failed", "coeffs": None, "error": str(exc)}


def run_python(ac: Aircraft, work: Path, datcom_ac: Aircraft | None = None) -> dict:
    """Run DATCOM, Tornado, and AVL for *ac* under *work*.

    DATCOM alone may be flown on a different aircraft: ``compare_to_matlab``
    reproduces a gold fixture on its own sweep, and only DATCOM's output depends
    on the alpha grid in that way. Tornado and AVL always get *ac*.
    """
    work = Path(work)
    return {
        "datcom": _run_datcom_safe(
            ac if datcom_ac is None else datcom_ac, work / "datcom"
        ),
        "tornado": _run_tornado(ac),
        "avl": _run_avl(ac, work / "avl"),
    }


def _values_close(a, b, *, rtol: float, atol: float) -> bool:
    try:
        return bool(np.allclose(np.asarray(a, dtype=float), np.asarray(b, dtype=float), rtol=rtol, atol=atol))
    except ValueError:
        # Shapes that cannot broadcast are two different series, not a match.
        return False


# Alpha values are written out in full decimal, so match them only to this much.
_ALPHA_MATCH_ATOL = 1e-6


def _sample_at_alphas(alphas, values, wanted) -> list | None:
    """``values`` sampled at each alpha in ``wanted``, or None if any is absent."""
    sampled = []
    for want in wanted:
        hit = next(
            (
                v
                for a, v in zip(alphas, values)
                if abs(float(a) - float(want)) <= _ALPHA_MATCH_ATOL
            ),
            None,
        )
        if hit is None:
            return None
        sampled.append(hit)
    return sampled


def _compare_datcom(python: dict, gold: dict) -> bool:
    """Compare a DATCOM run against gold, sampling the Python sweep where needed.

    ``compare_to_matlab`` flies the gold's own sweep, but this predicate must
    stay correct for any caller: if the two sweeps differ, a per-alpha series is
    sampled at the gold's ``alpha`` values rather than zipped element-wise. Every
    gold alpha must be present in the Python sweep, and an empty gold series is a
    failure -- sampling must never reduce a comparison to zero values and pass
    vacuously.
    """
    gold_alphas = gold.get("alpha")
    py_alphas = python.get("alpha")
    aligned = (
        isinstance(gold_alphas, list)
        and isinstance(py_alphas, list)
        and bool(gold_alphas)
    )

    for key, gold_val in gold.items():
        if key not in python:
            return False
        py_val = python[key]

        if aligned and key == "alpha":
            # The gold's alphas are the conditions to confirm, not a series to zip.
            if _sample_at_alphas(py_alphas, py_alphas, gold_alphas) is None:
                return False
            continue

        if isinstance(gold_val, list):
            if not gold_val:
                return False
            sampled = None
            if (
                aligned
                and isinstance(py_val, (list, tuple))
                and len(py_val) == len(py_alphas)
            ):
                sampled = _sample_at_alphas(py_alphas, py_val, gold_alphas)
                if sampled is None:
                    return False
            if not _values_close(
                py_val if sampled is None else sampled,
                gold_val,
                rtol=0.0,
                atol=_PARSER_ATOL,
            ):
                return False
        elif isinstance(gold_val, (int, float)):
            if not _values_close(py_val, gold_val, rtol=0.0, atol=_PARSER_ATOL):
                return False
    return True


def _compare_tornado(python: dict, gold: dict) -> bool:
    checks = (
        (_TORNADO_FORCES, _FORCE_RTOL, _FORCE_ATOL),
        (_TORNADO_MOMENTS, _MOMENT_RTOL, _MOMENT_ATOL),
        (_TORNADO_DERIVS, _DERIV_RTOL, _DERIV_ATOL),
    )
    for keys, rtol, atol in checks:
        for key in keys:
            if key not in gold:
                continue
            if not _values_close(python[key], gold[key], rtol=rtol, atol=atol):
                return False
    return True


def _compare_avl(python: dict, gold: dict) -> bool:
    for key, gold_val in gold.items():
        if key == "surface":
            continue
        if key not in python:
            return False
        if isinstance(gold_val, list):
            if not _values_close(python[key], gold_val, rtol=0.0, atol=_PARSER_ATOL):
                return False
        elif isinstance(gold_val, (int, float)):
            py_val = python[key]
            if isinstance(py_val, (list, tuple)):
                ref = python.get("ref")
                if isinstance(ref, dict) and key in ref:
                    if not _values_close(ref[key], gold_val, rtol=0.0, atol=_PARSER_ATOL):
                        return False
                    continue
                alphas = python.get("alpha")
                if not isinstance(alphas, (list, tuple)) or len(alphas) != len(py_val):
                    return False
                sample = next(
                    (v for a, v in zip(alphas, py_val) if abs(float(a) - 0.0) <= 1e-6),
                    None,
                )
                if sample is None or not _values_close(sample, gold_val, rtol=0.0, atol=_PARSER_ATOL):
                    return False
                continue
            if not _values_close(py_val, gold_val, rtol=0.0, atol=_PARSER_ATOL):
                return False
    return True


def _compare_coeffs(solver: str, python: dict | None, gold: dict) -> bool:
    if python is None:
        return False
    if solver == "datcom":
        return _compare_datcom(python, gold)
    if solver == "tornado":
        return _compare_tornado(python, gold)
    if solver == "avl":
        return _compare_avl(python, gold)
    raise ValueError(f"unknown solver {solver!r}")


def _solver_pass(
    solver: str,
    matlab_status: str,
    python_result: dict,
    gold_path: Path,
    *,
    alpha: list[float],
    alpha_source: str,
) -> dict:
    """Grade one solver against its gold, recording the sweep that was flown.

    ``alpha`` and ``alpha_source`` are required, not defaulted: a report that
    says ``pass`` without saying which sweep earned it is not self-describing.
    """
    py_status = python_result["status"]
    entry: dict[str, Any] = {
        "pass": False,
        "matlab_status": matlab_status,
        "python_status": py_status,
        "alpha": alpha,
        "alpha_source": alpha_source,
    }
    if python_result.get("error"):
        entry["error"] = python_result["error"]

    if matlab_status == "failed":
        entry["pass"] = False
        return entry

    if py_status != "ok":
        entry["pass"] = False
        return entry

    if not gold_path.is_file():
        entry["pass"] = False
        entry["error"] = f"missing gold {gold_path.name}"
        return entry

    gold = json.loads(gold_path.read_text())
    entry["pass"] = _compare_coeffs(solver, python_result["coeffs"], gold)
    return entry


def _gold_alpha(matlab_dir: Path) -> list | None:
    """The alpha sweep the DATCOM gold was flown on, if it records one."""
    gold_path = matlab_dir / "datcom.json"
    if not gold_path.is_file():
        return None
    alpha = json.loads(gold_path.read_text()).get("alpha")
    return alpha if isinstance(alpha, list) and alpha else None


def _flown_alpha(ac: Aircraft) -> list[float]:
    """The ``AERO.ALSCHD`` sweep a solver leg would fly for *ac*."""
    alschd = ac.AERO.get("ALSCHD")
    if alschd is None:
        return []
    return [float(a) for a in np.asarray(alschd, dtype=float).reshape(-1)]


def datcom_leg(ac: Aircraft, matlab_dir: Path) -> tuple[Aircraft, str]:
    """The aircraft DATCOM's leg flies for *ac*, and where that sweep came from."""
    gold_alpha = _gold_alpha(matlab_dir)
    if gold_alpha is None:
        return ac, "model"
    # A separate object, so the loaded model is never edited in place.
    return replace(ac, AERO={**ac.AERO, "ALSCHD": list(gold_alpha)}), "gold"


def flown_sweeps(ac: Aircraft, datcom_ac: Aircraft, datcom_source: str) -> dict:
    """Per solver, the ``ALSCHD`` sweep its leg flies and that sweep's provenance."""
    return {
        "datcom": {"alpha": _flown_alpha(datcom_ac), "alpha_source": datcom_source},
        "tornado": {"alpha": _flown_alpha(ac), "alpha_source": "model"},
        "avl": {"alpha": _flown_alpha(ac), "alpha_source": "model"},
    }


def compare_to_matlab(name: str, python: dict | None = None) -> dict:
    """Run Python solvers, compare to MATLAB gold, write ``Results/compare/<name>.json``.

    The gold is a fixture with its own inputs, and DATCOM's output depends on the
    alpha grid it is asked for -- its ``cla``/``cma`` are finite differences along
    it -- so only the DATCOM leg flies the gold's own sweep. Tornado and AVL have
    no gold alpha axis and run on the model's schedule; what each leg actually
    flew, and where that sweep came from, is recorded in the report.

    An already-computed *python* is graded as given, so a batch run that just
    flew these sweeps does not run them twice. The caller is then responsible for
    having flown ``datcom_leg``'s aircraft for DATCOM; ``flown_sweeps`` is what
    records that, and ``run_all.py`` writes it into the batch dump.
    """
    matlab_dir = results_dir() / "matlab" / name
    status = json.loads((matlab_dir / "status.json").read_text())

    ac = load_jsonc(models_dir() / f"{name}.jsonc")
    datcom_ac, datcom_source = datcom_leg(ac, matlab_dir)
    flown = flown_sweeps(ac, datcom_ac, datcom_source)
    if python is None:
        python = run_python(ac, results_dir() / "python" / name, datcom_ac=datcom_ac)

    report = {
        solver: _solver_pass(
            solver,
            status[solver],
            python[solver],
            matlab_dir / f"{solver}.json",
            **flown[solver],
        )
        for solver in ("datcom", "tornado", "avl")
    }

    compare_dir = results_dir() / "compare"
    compare_dir.mkdir(parents=True, exist_ok=True)
    out_path = compare_dir / f"{name}.json"
    out_path.write_text(json.dumps(report, indent=2) + "\n")
    return report
