import json
import subprocess
import tempfile
from pathlib import Path

import numpy as np

from aid.aircraft import Aircraft, aero_beta
from aid.axes import to_frd
from aid.paths import flow5_bin
from aid.flow5_foils import _cmp_enabled, foils_for_aircraft
from aid.flow5_sections import planform_sections
from aid.flow5_units import ft2_to_m2, ft_to_m, lb_to_kg, polar_state

_NP_NAMES = ("Wing 2", "HT 2", "VT 2")
_NP_VERTICAL = (False, False, True)


def _as_list(value) -> list:
    if isinstance(value, (list, tuple)):
        return list(value)
    return [value]


def _first(val) -> float:
    return float(np.asarray(val).reshape(-1)[0])


def write_flow5_deck(ac: Aircraft, mesh: tuple[str, str], beta: float | None = None) -> dict:
    # ``beta=None`` is the model speaking: AERO["BETA"], degrees, 0.0 by default.
    # run_flow5 forwards its own ``beta`` unchanged, so this is the one place the
    # default is resolved for both entry points.
    beta = aero_beta(ac) if beta is None else float(beta)
    ny = int(mesh[0])
    nx = int(mesh[1])
    cmp = ac.plot_cmp
    aero = ac.AERO

    wings: list[dict] = []

    if _cmp_enabled(cmp, 0):
        wing = planform_sections(ac.WG, nx=nx, ny=ny, vertical=False)
        wing["role"] = "main"
        wing["name"] = "Wing"
        wings.append(wing)

    if _cmp_enabled(cmp, 1):
        wing = planform_sections(ac.HT, nx=nx, ny=ny, vertical=False)
        wing["role"] = "elevator"
        wing["name"] = "HT"
        wings.append(wing)

    if _cmp_enabled(cmp, 2):
        wing = planform_sections(ac.VT, nx=nx, ny=ny, vertical=True)
        wing["role"] = "fin"
        wing["name"] = "VT"
        wings.append(wing)

    for i in range(min(3, len(ac.NP))):
        np_pt = ac.NP[i]
        if np_pt and _cmp_enabled(cmp, 4 + i):
            wing = planform_sections(
                np_pt, nx=nx, ny=ny, vertical=_NP_VERTICAL[i]
            )
            wing["role"] = "other"
            wing["name"] = _NP_NAMES[i]
            wings.append(wing)

    polar = {
        "type": "T1",
        "method": "VLM2",
        "thin": True,
        "viscous": False,
        **polar_state(ac),
        "sref_m2": ft2_to_m2(_first(aero["SREF"])),
        "cref_m": ft_to_m(_first(aero["CBARR"])),
        "bref_m": ft_to_m(_first(aero["BLREF"])),
        "cog_m": [
            ft_to_m(_first(aero["XCG"])),
            0.0,
            ft_to_m(_first(aero["ZCG"])),
        ],
        "mass_kg": lb_to_kg(_first(aero["WT"])),
        "alpha_deg": [float(x) for x in _as_list(aero["ALSCHD"])],
        # flow5 sweeps alpha only, so beta is the polar's one extra axis.
        # PlaneTask::run reads betaSpec() (planetask.cpp:605) and rotates the
        # mesh about the CG (planetask.cpp:748), leaving the geometry put and
        # yawing the flow. Written explicitly even at 0.0 because the helper
        # rejects any near-miss beta key rather than ignoring it, so an omitted
        # key and a zero one must be the same intent.
        "beta_deg": beta,
    }

    return {
        "name": getattr(ac, "source_stem", None) or "plane",
        "foils": foils_for_aircraft(ac),
        "wings": wings,
        "polar": polar,
    }


def run_flow5_native(deck: dict, *, timeout: float = 180) -> dict:
    exe = flow5_bin()
    if not exe.is_file():
        raise FileNotFoundError(str(exe))
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(deck, f)
        deck_path = f.name
    try:
        result = subprocess.run(
            [str(exe), "--deck", deck_path],
            check=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return json.loads(result.stdout)
    finally:
        Path(deck_path).unlink(missing_ok=True)


def run_flow5(
    ac: Aircraft,
    mesh: tuple[str, str],
    beta: float | None = None,
    *,
    timeout: float = 180,
) -> dict:
    # The one boundary where flow5's raw output becomes Forward-Right-Down. The
    # map is four keys wide and the measured justification for each lives in
    # aid/axes.py; do not add to it from Tornado's pattern, which flow5 matches
    # for its forces and not for its moments.
    return to_frd(
        "flow5",
        run_flow5_native(write_flow5_deck(ac, mesh, beta=beta), timeout=timeout),
    )
