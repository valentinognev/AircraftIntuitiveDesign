from copy import deepcopy

from aid.aircraft import Aircraft

SURFACES = ("flap", "aileron", "elevator", "rudder")
COEFFS = ("CL", "CD", "Cm", "CY", "Cl", "Cn")
DEFAULT_DELTAS_DEG = (0.0, 5.0)
H_DEG = 1.0

_DELTA_ATTR = {"flap": "F", "elevator": "E", "rudder": "R"}


def blank_row(surface: str, delta_deg: float, *, available: bool, reason: str = "") -> dict:
    row = {
        "surface": surface,
        "delta_deg": delta_deg,
        "available": available,
        "reason": reason,
    }
    for name in COEFFS:
        row[name] = None
    return row


def central_difference(plus: dict, minus: dict, h_deg: float = H_DEG) -> dict:
    slope = {}
    for name in COEFFS:
        hi = plus.get(name)
        lo = minus.get(name)
        if hi is None or lo is None:
            slope[name] = None
        else:
            slope[name] = (hi - lo) / (2.0 * h_deg)
    return slope


def with_probe(ac: Aircraft, surface: str, delta_deg: float) -> Aircraft:
    probed = deepcopy(ac)
    if surface == "aileron":
        probed.A["DELTAR"] = delta_deg
        probed.A["DELTAL"] = -delta_deg
    elif surface in _DELTA_ATTR:
        getattr(probed, _DELTA_ATTR[surface])["DELTA"] = delta_deg
    else:
        raise ValueError(f"unknown control surface {surface!r}")
    return probed


def iter_rows(
    deltas_deg: tuple[float, ...] | list[float] | None,
) -> list[tuple[str, float]]:
    deltas = DEFAULT_DELTAS_DEG if deltas_deg is None else deltas_deg
    return [(surface, float(delta)) for surface in SURFACES for delta in deltas]
