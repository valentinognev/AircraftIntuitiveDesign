"""NACA 4- and 6-series ordinates. Does not call the naca456 binary."""

from dataclasses import dataclass

import numpy as np

from aid.naca456.camber import (
    combine_thickness_and_camber,
    interpolate_upper_and_lower,
    mean_line2,
    mean_line3,
    mean_line3_reflex,
    mean_line6,
    mean_line6m,
)
from aid.naca456.thickness import load_x, thickness4, thickness4m, thickness6

_SIX = {
    "63": 1,
    "64": 2,
    "65": 3,
    "66": 4,
    "67": 5,
    "63A": 6,
    "64A": 7,
    "65A": 8,
}


@dataclass(frozen=True)
class NacaSpec:
    name: str
    profile: str
    camber: str
    toc: float
    cl: float = 0.0
    dencode: int = 3
    a: float = 1.0
    cmax: float = 0.0
    xmaxc: float = 0.0
    chord: float = 1.0


def _thickness(spec: NacaSpec, x):
    profile = spec.profile.strip().upper()
    if profile == "4":
        return thickness4(spec.toc, x)
    if profile == "4M":
        # leIndex=6 and xmaxt=0.3 are the Fortran defaults; NacaSpec has no fields for them.
        return thickness4m(spec.toc, 6.0, 0.3, x)
    family = _SIX.get(profile)
    if family is None:
        raise ValueError(f"Not a valid profile: {spec.profile}")
    return thickness6(family, spec.toc, x)


def _camber(spec: NacaSpec, x):
    camber = spec.camber.strip().upper()
    if camber == "0":
        z = np.zeros_like(x)
        return z, z.copy()
    if camber == "2":
        return mean_line2(spec.cmax, spec.xmaxc, x)
    if camber == "3":
        return mean_line3(spec.cl, spec.xmaxc, x)
    if camber == "3R":
        return mean_line3_reflex(spec.cl, spec.xmaxc, x)
    if camber == "6":
        return mean_line6(spec.a, spec.cl, x)
    if camber in ("6A", "6M"):
        return mean_line6m(spec.cl, x)
    raise ValueError(f"Not a valid mean line: {spec.camber}")


def ordinates(spec: NacaSpec) -> np.ndarray:
    """(N, 2) x,y in naca.gnu order. First half upper, second half lower."""
    x = load_x(spec.dencode)
    yt, ytp = _thickness(spec, x)
    ymean, ymeanp = _camber(spec, x)
    if np.max(np.abs(ymean)) == 0.0:
        yu = yt
        yl = -yt
    else:
        xupper, yupper, xlower, ylower = combine_thickness_and_camber(x, yt, ymean, ymeanp)
        yu, yl = interpolate_upper_and_lower(xupper, yupper, xlower, ylower, x)
    chord = spec.chord
    xu = chord * x
    yu = chord * yu
    xl = chord * x
    yl = chord * yl
    return np.column_stack((np.concatenate((xu, xl)), np.concatenate((yu, yl))))
