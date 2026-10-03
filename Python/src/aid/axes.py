"""Solver sign conventions, normalized to Forward-Right-Down (F-R-D).

F-R-D is x forward, y right, z down; roll is right-wing-down positive, pitch is
nose-up positive, yaw is nose-right positive. It is AVL's native frame and the
standard aerospace convention, so AVL needs no conversion and MATLAB-gold
parity stays a real check rather than a tautology.

Each solver's own output was measured against the identity that defines it, not
read out of documentation:

* **avl** -- ``Results/*/avl/geometry.st:12`` prints
  ``Standard axis orientation, X fwd, Z down``; ``CXtot = -CDtot`` and
  ``CZtot = -CLtot`` hold to all printed digits on every model checked. Already
  F-R-D, so the map is empty.
* **datcom** -- the table header is ``ALPHA CD CL CM CN CA XCP`` with UPPERCASE
  ``CN`` and ``CA``, i.e. forces (``datcom_parse.py:28``); the wind/body
  rotation ``CL = CN*cos(a) - CA*sin(a)`` and ``CD = CN*sin(a) + CA*cos(a)``
  reproduces the printed Cessna 172 values at alpha = 4 deg exactly. So datcom
  reports forces aft-positive / up-positive and only ``ca`` and ``cn`` need
  mirroring. Lowercase ``cl``/``cnb`` are moments and already follow the
  standard; ``xcp`` is printed as ``CM/CN`` (``datcom.f:1010``) and is not
  flipped.
* **tornado** -- ``tornado/coeff.py:80-95`` builds ``b2w`` with the drag
  direction first, giving ``CX = CD*cos(a) - CL*sin(a)`` (verified: Cessna at
  alpha = 4 deg gives -0.01946 against the printed -0.01940), and the body
  frame is x aft, y right, z up, so ``cross()`` in ``tornado/solver.py:154``
  yields left-wing-down ``Cl`` and nose-left ``Cn``. The ``p``/``q``/``r``
  derivatives use the same cross product on rotation rates and land standard,
  which is why the beta terms flip and the rate terms are mapped explicitly
  rather than blanket-flipped. ``CY`` and ``CC`` (``coeff.py:104``) are already
  F-R-D.
* **flow5** -- ``FLOW5/flow5-lib/api/aeroforces.h:89,101`` documents ``Cli()``
  and ``Cni()`` as already F-R-D, and the emitted keys are longitudinal only
  today, so the map is empty.
* **handbook** -- ``Matlab/fsroot/code/Lateral_Static_Stability.m:100`` already
  yields F-R-D signs. It has no entry here; asking for it raises ``KeyError``.

Only the sign changes. No coefficient changes value in magnitude, and the raw
solver vectors ``F``/``M``/``FORCE``/``MOMENTS`` are deliberately not mapped:
they are solver internals, already excluded from the Sections table, and
``FORCE`` is needed to rebuild ``cp``.
"""

from __future__ import annotations

from typing import Any, Mapping

import numpy as np

__all__ = ["to_frd", "from_frd"]

_SIGN_MAP: dict[str, dict[str, int]] = {
    "avl": {},
    "datcom": {"ca": -1, "cn": -1},
    "tornado": {
        "CX": -1, "CZ": -1, "Cl": -1, "Cn": -1,
        "CX_a": -1, "CZ_a": -1, "Cl_a": -1, "Cn_a": -1,
        "Cl_b": -1, "Cn_b": -1,
        "Cl_P": -1, "Cl_Q": -1, "Cl_R": -1,
        "Cn_P": -1, "Cn_Q": -1, "Cn_R": -1,
        "CX_d": -1, "CZ_d": -1, "Cl_d": -1, "Cn_d": -1,
    },
    "flow5": {},
}


def _scaled(value: Any, factor: int) -> Any:
    """``factor * value`` for numbers, arrays and lists of numbers, else unchanged."""
    if isinstance(value, np.ndarray) or isinstance(value, (int, float)):
        return factor * value
    if isinstance(value, list) and all(isinstance(v, (int, float)) for v in value):
        return [factor * v for v in value]
    return value


def _convert(solver: str, data: Mapping[str, Any]) -> dict[str, Any]:
    """Shallow-copy ``data``, scaling each mapped key by its sign.

    Every sign in the map is +/-1, and a sign flip is its own inverse, so this
    one function is both directions: ``to_frd`` and ``from_frd`` differ only in
    which end of the conversion they are documented as reading.

    Keys absent from ``data`` stay absent rather than being filled with zeros,
    and keys not in the solver's map pass through by identity.
    """
    signs = _SIGN_MAP[solver]
    out = dict(data)
    for key, sign in signs.items():
        if key in out:
            out[key] = _scaled(out[key], sign)
    return out


def to_frd(solver: str, data: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize one solver's coefficients to F-R-D."""
    return _convert(solver, data)


def from_frd(solver: str, data: Mapping[str, Any]) -> dict[str, Any]:
    """Undo :func:`to_frd`, back to the solver's own frame. Exists for
    ``compare.py``, to re-raw the Python side before diffing it against MATLAB
    gold."""
    return _convert(solver, data)