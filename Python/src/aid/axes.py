"""Solver sign conventions, normalized to Forward-Right-Down (F-R-D).

F-R-D is x forward, y right, z down; roll is right-wing-down positive, pitch is
nose-up positive, yaw is nose-right positive. It is AVL's native frame and the
standard aerospace convention, so AVL needs no conversion and MATLAB-gold
parity stays a real check rather than a tautology.

Each solver's own output was measured against the identity that defines it, not
read out of documentation:

* **avl** -- ``Results/*/avl/geometry.st:12`` prints
  ``Standard axis orientation, X fwd, Z down`` on every model checked, which is
  what the empty map rests on. That frame declaration is the evidence; the
  coefficient identities are not, and must not be cited as though they were:
  ``CXtot = -CDtot`` holds *exactly* only at alpha = 0, where the wind and body
  axes coincide. Away from it the lift tilts into the axial component and
  ``CXtot + CDtot`` grows to +0.2521 at alpha = 12 deg on Cessna (0.0018 of the
  force scale at alpha = 4 deg, which is why the solvers straddle the drag
  crossover there). Only ``CZtot = -CLtot`` keeps its sign against ``CLtot``
  across the sweep. So AVL is already F-R-D by declaration, and the map is empty.
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

  The rate derivatives follow one rule, and the rule -- not any measured pair --
  is what the entries above encode. tornado's body frame is x aft / y right /
  z up and F-R-D is x fwd / y right / z down, so going between them is a 180 deg
  rotation about y: **x and z reverse, y does not**. A component along axis i
  therefore picks up ``s_i``, and a body rate about axis j picks up ``s_j`` as
  well, so ``dC_i/d(omega_j) -> s_i * s_j``. Alpha, beta and control deflections
  rotate the flow rather than the body axes, so they contribute nothing and the
  alpha/beta/control derivatives simply inherit ``s_i``.

  Read through that rule, ``p`` and ``r`` are about x and z -- the two axes that
  reverse -- so for every channel whose own sign is ``-1`` the two signs cancel:
  ``CX_P``, ``CZ_P``, ``Cl_P``, ``Cn_P``, ``CX_R``, ``CZ_R``, ``Cl_R`` and
  ``Cn_R`` take **no** entry. ``q`` is about y, the one axis the two frames
  share, so the cancellation breaks there and the four q-derivatives keep their
  channel's own sign: ``CX_Q``, ``CZ_Q``, ``Cl_Q`` and ``Cn_Q`` each take a
  ``-1``. ``Cm_Q`` takes none because ``Cm`` takes none.

  ``CY`` and ``Cm`` are the two channels whose own sign is ``+1`` *and* which are
  measured against a reversing rate, so the cancellation never gets to happen
  there: ``CY_P``, ``CY_R``, ``Cm_P`` and ``Cm_R`` all take a ``-1`` while
  ``CY_Q`` and ``Cm_Q`` take none. This is the case the shorthand "``CY``/``Cm``
  are never flipped" used to hide -- those channels and their flow-angle
  derivatives are never flipped, their p/r rate derivatives are.

  The measurements. On the cancelling side, raw tornado ``Cl_P`` -0.486 against
  AVL ``Clp`` -0.470, ``Cn_R`` -0.286 against ``Cnr`` -0.212 and ``Cm_Q`` -33.3
  against ``Cmq`` -18.6 all already agree with a solver that needs no conversion,
  which is why flipping them would break
  ``test_damping_derivatives_still_agree``. On the non-cancelling side, AVL's own
  printed values *are* F-R-D (its map is empty), and they are opposite to the
  unflipped tornado values on every point measured:

  ==============  ================  ==============  ==============
  key             AVL               tornado raw    after ``to_frd``
  ==============  ================  ==============  ==============
  ``CZq`` Cessna  -9.93..-8.86     +9.47..+9.74   -9.47..-9.74
  ``CZq`` Learjet -8.35..-8.27     +8.84..+8.88   -8.84..-8.88
  ``CYr`` Cessna  +0.427           -0.387         +0.387
  ``CYr`` Learjet +0.539           -0.450         +0.450
  ``CYp`` Cessna  -0.182           +0.160         -0.160
  ``CYp`` Learjet -0.0360          +0.0622        -0.0622
  ``Clq`` Cessna  -0.00635         +0.00853       -0.00853
  ``Cnq`` Cessna  +0.0776          -0.0489        +0.0489
  ``Cmr`` Cessna  +0.0838          -0.0703        +0.0703
  ==============  ================  ==============  ==============

  (the ``CZq`` row spans alpha = -4, 0, +4, +6; every other row is alpha = +4 with
  the ``Clq``/``Cnq``/``Cmr`` ones taken at beta = +5, which is the only condition
  at which those three are above tornado's own ~1e-5 noise floor. ``Clq`` and
  ``Cnq`` are ~1e-13 at beta = 0 and AVL prints exactly 0 for both on Learjet 23,
  a fuselage-less airframe.) Textbook sign agrees on the two best-conditioned of
  these: a typical transport has ``CY_r`` about +0.3, ``CZ_q`` negative, and
  ``aid/longitudinal_dynamic.py`` sets ``czq = -clq`` with ``clq > 0``.

  Three of the ten entries rest on the rule alone and have **no** usable
  second-solver witness. ``Cm_P`` is 1e-6 at beta = 0 and its one larger value
  (Cessna, beta = 5: -0.113 against AVL's -0.0226) disagrees by 5x in magnitude,
  which makes it a magnitude disagreement between solvers rather than evidence
  about a frame. AVL emits no ``CZb``/``CXb`` at all, so ``CX_b``/``CZ_b`` are
  structural: same channel as the already-confirmed ``CX_a``/``CZ_a``, different
  invariant angle, therefore the same sign.

  The separate cross-check on the *alpha* derivatives is flow5's ``CZa``: it
  measures -5.2562 and is already F-R-D, against tornado's raw up-positive
  ``CZ_a``, and after ``to_frd`` the two have to land on the same number. That
  pins ``CZ_a`` as flipped. It says nothing at all about the rate derivatives --
  it constrains alpha derivatives only -- so it is not part of why the p/r keys
  are absent.

  ``CY`` and ``CC`` (``coeff.py:104``, wind-axis side force) are already F-R-D,
  as are the wind-axis ``CL``/``CD``/``CC`` and their derivatives
  (``coeff.py:76-100,164`` computes them from the ``b2w`` rotation directly), so
  those channels and their alpha/beta/control derivatives are never flipped, by
  any solver. Only ``CY_P``/``CY_R`` above are exceptions.
* **flow5** -- ``{"Cx": -1, "Cz": -1, "Cl": -1, "Cn": -1}``, filled in by Task
  2.3 (commit ``588a3a0``); it used to be empty and the text here used to say
  so. All four flips were measured. The header comments at
  ``FLOW5/flow5-lib/api/aeroforces.h:87-88,97-98``, which claim ``Cli()`` and
  ``Cni()`` are already F-R-D, are wrong: at beta = +5 deg, alpha = 0, ``Cli`` =
  +0.0047339 against a F-R-D prediction of ``Clb*beta`` = -0.0046262, and ``Cni``
  = -0.0142629 against ``Cnb*beta`` = +0.0147063 -- both opposite, so both take a
  ``-1``. ``Cx``/``Cz`` are aft-positive and up-positive, measured as ``Cx`` =
  ``CD*cos(a) - CL*sin(a)`` to 1.4e-13 across the sweep and ``Cz`` = ``CL`` at
  alpha = 0. ``CXa``/``CZa`` deliberately get **no** entry: raw ``CZa`` measures
  -5.2562 and is already down-positive (it equals the gold's own
  ``CZa = -CLa - CD``), and raw ``CXa`` is ``CL - dCD/dalpha``, not a bare
  ``-dCD/dalpha``, so both are already F-R-D.
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
``test_axes.py``'s ``derived_tornado_signs`` re-derives the tornado map from
``AXIS_SIGN``/``CHANNEL_AXIS``/``RATE_AXIS`` above and asserts the two are equal
as sets, so a key added to either side without the other fails by name.
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
        "CX_b": -1, "CZ_b": -1, "Cl_b": -1, "Cn_b": -1,
        "CX_d": -1, "CZ_d": -1, "Cl_d": -1, "Cn_d": -1,
        "CX_Q": -1, "CZ_Q": -1, "Cl_Q": -1, "Cn_Q": -1,
        "CY_P": -1, "CY_R": -1, "Cm_P": -1, "Cm_R": -1,
    },
    "flow5": {"Cx": -1, "Cz": -1, "Cl": -1, "Cn": -1},
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