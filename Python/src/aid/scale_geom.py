from __future__ import annotations

import numpy as np

from aid.aircraft import Aircraft

PLANFORM_LENGTH_KEYS = (
    "CHRDR",
    "CHRDBP",
    "CHRDTP",
    "SSPN",
    "SSPNOP",
    "X",
    "Y",
    "Z",
)
BODY_LENGTH_KEYS = ("X", "ZU", "ZL", "R")
NB_BODY_KEYS = ("X", "ZU", "ZL", "R", "X0", "Y0", "Z0")


def _scale_value(value, factor: float):
    if isinstance(value, (list, tuple)):
        return [_scale_value(item, factor) for item in value]
    if isinstance(value, np.ndarray):
        return (np.asarray(value, dtype=float) * factor).tolist()
    if isinstance(value, (int, float)):
        return value * factor
    return value


def _scale_dict(part: dict, keys: tuple[str, ...], factor: float) -> None:
    for key in keys:
        if key in part:
            part[key] = _scale_value(part[key], factor)


def scale_lengths(ac: Aircraft, factor: float) -> Aircraft:
    if factor in (0, 1):
        return ac

    for name in ("WG", "HT", "VT"):
        _scale_dict(getattr(ac, name), PLANFORM_LENGTH_KEYS, factor)

    for part in ac.NP:
        if isinstance(part, dict):
            _scale_dict(part, PLANFORM_LENGTH_KEYS, factor)

    _scale_dict(ac.BD, BODY_LENGTH_KEYS, factor)

    for part in ac.NB:
        if isinstance(part, dict):
            _scale_dict(part, NB_BODY_KEYS, factor)

    _scale_dict(ac.AERO, ("XCG",), factor)

    return ac


def scale_aircraft(ac: Aircraft, factor: float) -> Aircraft:
    if factor in (0, 1):
        return ac

    scale_lengths(ac, factor)
    _scale_dict(ac.AERO, ("WT",), factor)

    return ac
