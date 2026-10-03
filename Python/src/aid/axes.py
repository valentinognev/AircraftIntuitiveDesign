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
  yields left-wing-down ``Cl`` and nose-left ``Cn``. The force channels
  (``CX``, ``CZ``) and the roll/yaw moment channels (``Cl``, ``Cn``) are
  therefore mirrored, and their alpha, beta and control derivatives inherit
  their channel's frame, so all of those take a ``-1``.

  The ``p``/``q``/``r`` rate derivatives are the exception and take **no**
  entry: measured raw Tornado ``Cl_P`` -0.486 against AVL ``Clp`` -0.470 and
  raw ``Cn_R`` -0.286 against AVL ``Cnr`` -0.212, they already agree with AVL
  once AVL is left alone, so they are already F-R-D. Flipping them would
  destroy that agreement -- which is why ``test_damping_derivatives_still_agree``
  (Task 1.4) asserts ``sign(avl_Clp) == sign(tornado_Cl_P) < 0`` and would
  fail. The independent cross-check on the other side of the line is flow5's
  ``CZa``, which measures ``-5.2562`` and is already F-R-D, against Tornado's
  raw ``CZ_a``, which is up-positive: after ``to_frd`` the two have to land on
  the same number, which is what fixes the alpha derivatives as flipped and the
  rate derivatives as not.

  ``CY`` and ``CC`` (``coeff.py:104``, wind-axis side force) are already F-R-D
  and are never flipped, by any solver.
* **flow5** -- empty for now, because the emitted keys are longitudinal only
  today. The lateral channels are **known to need flips** and the header
  comments at ``FLOW5/flow5-lib/api/aeroforces.h:87-88,97-98``, which claim
  ``Cli()`` and ``Cni()`` are already F-R-D, are wrong: measured on Cessna at
  beta = +5 deg, alpha = 0, ``Cli`` = +0.0047339 against a F-R-D prediction of
  ``Clb*beta`` = -0.0046262, and ``Cni`` = -0.0142629 against ``Cnb*beta`` =
  +0.0147063 -- both opposite, so both take a ``-1``. Task 2.3 owns filling
  this map in as ``{"Cx": -1, "Cz": -1, "Cl": -1, "Cn": -1}``; ``CXa``/``CZa``
  get no entry there, because ``CZa`` already measures -5.2562 and raw
  ``CXa`` is ``CL - dCD/dalpha`` rather than a bare ``-dCD/dalpha``. The
  measurements are recorded here so that task does not have to re-derive
  them.
* **handbook** -- ``Matlab/fsroot/code/Lateral_Static_Stability.m:100`` already
  yields F-R-D signs. It has no entry here; asking for it raises ``KeyError``.

Only the sign changes. No coefficient changes value in magnitude, and the raw
solver vectors ``F``/``M``/``FORCE``/``MOMENTS`` are deliberately not mapped:
they are solver internals, already excluded from the Sections table, and
``FORCE`` is needed to rebuild ``cp``.

Every entry in ``_SIGN_MAP`` is +/-1, and a sign flip is its own inverse, so
:func:`to_frd` and :func:`from_frd` are the same map read in two directions --
that is what makes the round trip exact. This coincidence is a property of the
values, not of the design: a future non-+/-1 entry (a scale factor, say) would
make ``from_frd`` need the negation restored, and the map's shape stays honest
only if the docstring above keeps matching it key for key.
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
    which end of the conversion they are documented as reading. A non-+/-1 entry
    would have to restore the negation here.

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