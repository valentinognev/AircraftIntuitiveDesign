"""DATCOM, AVL and Tornado report the same signs, in Forward-Right-Down.

This is the regression guard for all of Deliverable 1. Tasks 1.1-1.3 built the
machinery: ``aid.axes`` holds the per-solver sign map, it is applied at the
solver boundary, and ``compare.py`` inverts it before diffing MATLAB gold. Every
other test in the suite checks that machinery *locally* -- one runner against its
own bare parser. This file is the only place where the three solvers are placed
side by side, which is the only place a frame error affecting all three
identically would be visible.

Three things this file deliberately does not do:

* **It does not read the MATLAB gold.** Every coefficient here comes from a live
  run of all three solvers at the *same* alpha. The gold sits at alpha = -1.9 deg
  and is not comparable to any condition below; a previous task compared against
  it anyway and drew a false conclusion.
* **It does not assert the sign of a numerically-zero coefficient.** ``Cl_Q``
  measures ``+8.1e-14`` and ``Cn_Q`` ``-7.6e-14`` at alpha = -4 deg -- both are
  round-off. See ``test_damping_derivatives_still_agree``. (They are *in* the
  sign map, correctly: the map is right by rule and not by which of its entries
  happen to be non-zero on one airframe.)
* **It does not assert a tolerance on those either.** A band around an
  analytically-zero quantity passes identically for a correct sign and for a
  frame flip that happens to be small, so it carries no information. The
  near-zero pairs are omitted and their well-conditioned partners asserted.

All comparisons are at alpha = -4 deg unless a test names otherwise, and
``test_all_three_solvers_fly_the_same_alpha`` pins that rather than assuming it.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from aid.aircraft import aero_beta, load_jsonc
from aid.avl_io import run_avl_full
from aid.avl_parse import parse_sb
from aid.datcom_run import run_datcom
from aid.paths import datcom_wrapper
from aid.tornado.boundary import set_boundary
from aid.tornado.coeff import coeff_create
from aid.tornado.lattice import lattice_setup
from aid.tornado.solver import solve
from aid.tornado_io import tornado_io

MODELS = Path(__file__).resolve().parents[1] / "models"
CESSNA = MODELS / "Cessna 172.jsonc"

# Cessna's own ALSCHD, -4..+12 deg. DATCOM and AVL sweep all of it.
_LADDER_17 = [-4.0, -3.0, -2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0]

# tornado_io flies ``alschd[ceil(n/2) - 1]`` (tornado_io.py:378), so the middle rung
# is the alpha Tornado gets. These two ladders put it at -4 deg and +10 deg.
_LADDER_NEG4 = [-6.0, -5.0, -4.0, -3.0, -2.0]
_LADDER_AXIAL = [8.0, 9.0, 10.0, 11.0, 12.0]

_ALPHA_NEG4 = -4.0
_ALPHA_AXIAL = 10.0

# DATCOM's ND/NDM "not computed" sentinel (datcom_parse.py:7). Same threshold
# solver_overlay.py:181 uses to mask it.
_ND = 99998.0

# |CA| below this fraction of (|CD| + |CL|) is a cancellation of two comparable
# terms rather than a measurable axial force, so its sign says nothing about the
# frame. Measured on Cessna, the axial force is 0.0018 of the force scale at
# alpha = 4 deg and 0.0167 at alpha = 5 deg, so 0.01 falls in that gap by an
# order of magnitude. It is relative, so it scales with the airframe rather than
# hard-coding an absolute drag number.
_CANCEL = 0.01


def _require_datcom() -> None:
    if not datcom_wrapper().is_file():
        pytest.skip(f"DATCOM binary missing at {datcom_wrapper()}")


def _run_tornado(ac, tmp: Path):
    geo, state = tornado_io(ac, ("10", "5"))
    lattice, ref = lattice_setup(geo, state, 0)
    lattice = set_boundary(lattice, geo, state)
    return coeff_create(solve(state, geo, lattice), lattice, state, ref, geo), state


@pytest.fixture(scope="module")
def sweep(tmp_path_factory):
    """DATCOM and AVL on Cessna's own 17-rung ladder, plus Tornado at -4 deg.

    DATCOM and AVL both sweep ``ALSCHD``, and Tornado flies a different ladder
    whose middle rung is -4 deg -- so the shared condition is the ladder's *first*
    rung, which is where DATCOM's beta derivatives are real (see
    ``test_datcom_beta_derivatives_are_real_only_at_the_first_rung``).
    """
    _require_datcom()
    tmp = tmp_path_factory.mktemp("frd_sweep")
    ac = load_jsonc(CESSNA)
    ac.AERO["ALSCHD"] = _LADDER_17
    datcom = run_datcom(ac, tmp / "datcom")
    avl = run_avl_full(ac, ("10", "10"), tmp / "avl")
    tor_ac = load_jsonc(CESSNA)
    tor_ac.AERO["ALSCHD"] = _LADDER_NEG4
    tornado, state = _run_tornado(tor_ac, tmp)
    return datcom, avl, tornado, state


@pytest.fixture(scope="module")
def at_axial(tmp_path_factory):
    """All three solvers at alpha = +10 deg, where the axial force is real."""
    _require_datcom()
    tmp = tmp_path_factory.mktemp("frd_axial")
    ac = load_jsonc(CESSNA)
    ac.AERO["ALSCHD"] = _LADDER_AXIAL
    datcom = run_datcom(ac, tmp / "datcom")
    avl = run_avl_full(ac, ("10", "10"), tmp / "avl")
    tornado, state = _run_tornado(ac, tmp)
    return datcom, avl, tornado, state


def _avl_at(avl: dict, alpha: float) -> dict:
    """AVL's scalars at ``alpha``, length-filtered, then matched by value.

    Matching on the alpha *value* rather than on ``len(alpha)//2`` is deliberate:
    a middle index is only the right alpha by coincidence of a particular ladder
    and would silently compare different conditions if the ladder changed.

    The length filter is what makes this safe. AVL's dict also carries
    ``surface`` (a list of length 0) and ``ref`` (a dict); indexing those at the
    sweep's length either raises ``IndexError`` or picks a wrong-length key.
    """
    n = len(avl["alpha"])
    for i, a in enumerate(avl["alpha"]):
        if abs(float(a) - alpha) <= 1e-6:
            return {k: v[i] for k, v in avl.items() if isinstance(v, list) and len(v) == n}
    raise AssertionError(f"AVL swept {avl['alpha']}, which does not contain alpha = {alpha}")


def test_all_three_solvers_fly_the_same_alpha(sweep, at_axial):
    """Precondition for every comparison in this file: one shared condition.

    DATCOM and AVL sweep a ladder and Tornado flies one of its own, so the two
    must be shown to meet at one alpha. If a future change separates them, every
    sign assertion below would still be individually plausible and jointly
    meaningless -- which is the exact failure this file exists to catch.
    """
    datcom, avl, _tornado, state = sweep
    assert float(datcom["alpha"][0]) == pytest.approx(_ALPHA_NEG4)
    assert float(avl["alpha"][0]) == pytest.approx(_ALPHA_NEG4)
    assert float(np.degrees(state["alpha"])) == pytest.approx(_ALPHA_NEG4)

    datcom, avl, _tornado, state = at_axial
    assert float(np.degrees(state["alpha"])) == pytest.approx(_ALPHA_AXIAL)
    assert _ALPHA_AXIAL in [float(a) for a in datcom["alpha"]]
    assert _ALPHA_AXIAL in [float(a) for a in avl["alpha"]]


def test_datcom_beta_derivatives_are_real_only_at_the_first_rung(sweep):
    """DATCOM prints CNB/CYB only at the ladder's first alpha; the rest are ND.

    Measured on the 17-rung sweep: ``cnb`` and ``cyb`` are ``99999.0`` (the ND
    sentinel) at alphas -3..+12 and real only at alpha = -4. ``clb`` is real
    everywhere. This is pinned because it is a live vacuity hazard --
    ``np.sign(99999.0)`` is ``+1``, so a comparison made against the sentinel
    would pass for ``Cnb`` while testing nothing at all.

    It is also why the shared condition is the *first* rung: the brief indexed
    ``datcom["cnb"][0]`` while reading AVL and Tornado at the ladder's middle
    rung, i.e. it compared DATCOM at -4 deg against the other two at +4 deg. The
    values happened to agree in sign, so it passed -- having measured nothing.
    """
    datcom, _avl, _tornado, _state = sweep
    real = [i for i, v in enumerate(datcom["cnb"]) if abs(v) < _ND]
    assert real == [0], f"expected cnb to be real at rung 0 only, got rungs {real}"
    assert abs(datcom["cnb"][0]) < _ND and abs(datcom["cyb"][0]) < _ND
    assert all(abs(v) >= _ND for v in datcom["cnb"][1:]), "rungs 1..16 must stay ND"
    assert all(abs(v) < _ND for v in datcom["clb"]), "clb is real at every rung"


def test_beta_is_zero(sweep, at_axial):
    """Correction: assert betha == 0 rather than assuming it.

    ``tornado_io.py:384`` used to hardcode ``"betha": 0.0``; since Task 3.1 it
    reads ``math.radians(aero_beta(ac))``, so ``betha`` is now whatever the model
    carries in ``AERO["BETA"]`` -- DATCOM and AVL are swept at the same beta, but
    whether these three solvers are flying a sideslip at all is a property of the
    *aircraft file*, not of this file.

    **So the sideslip is a property of the aircraft file, not of this test.**
    No shipped model declares ``AERO["BETA"]`` at all -- ``grep -rl BETA
    Python/models/`` finds nothing, and ``aircraft.py:13-15`` says so outright
    ("no .mat and no shipped .jsonc has them"; they are Python-only defaults).
    ``aero_beta`` resolves the absent key to 0.0 through ``AERO_DEFAULTS``, so
    that default -- and not any declared zero -- is what satisfies the assertions
    above, which is why the precondition is asserted against the *value* rather
    than assumed: the key is one hand-edit from existing, and the comparisons
    below would silently start mixing three solvers flown at different conditions
    the moment it did. So a change fails loudly and names itself.

    When the model does gain a sideslip, the fix is not to relax the assertion. It
    is to sweep all three solvers at that beta and keep the comparisons
    like-for-like.
    """
    for solvers in (sweep, at_axial):
        _datcom, _avl, _tornado, state = solvers
        assert float(state["betha"]) == 0.0, "the cross-solver comparison assumes betha = 0"
    assert aero_beta(load_jsonc(CESSNA)) == 0.0, (
        "Cessna 172's AERO.BETA is no longer 0, so the sweeps above were flown at a "
        "sideslip that the derivative rows below are not compared at. Sweep all three "
        "solvers at that beta instead of relaxing the assertion."
    )


def test_normal_force_agrees_in_sign(sweep, at_axial):
    """F-R-D normal force has the same sign in all three solvers, at both alphas.

    Measured: at alpha = -4 deg, DATCOM cn +0.226, AVL CZtot +0.18487, Tornado CZ
    +0.210324; at alpha = +10 deg, DATCOM cn -1.149, AVL CZtot -1.03329, Tornado CZ
    -1.095953. This is the best-conditioned force channel in the file -- CZ is
    ~90% of the force scale at both conditions, not a cancellation -- so it is
    the one that carries an ungated three-way sign claim at alpha = -4 deg.
    """
    for solvers, alpha in ((sweep, _ALPHA_NEG4), (at_axial, _ALPHA_AXIAL)):
        datcom, avl, tornado, _state = solvers
        i = int(np.argmin(np.abs(np.asarray(datcom["alpha"], float) - alpha)))
        a = _avl_at(avl, alpha)
        signs = {np.sign(datcom["cn"][i]), np.sign(a["CZtot"]), np.sign(tornado["CZ"])}
        assert len(signs) == 1, (
            f"normal force signs disagree at alpha = {alpha}: "
            f"datcom {datcom['cn'][i]}, avl {a['CZtot']}, tornado {tornado['CZ']}"
        )


def test_axial_force_agrees_in_sign(at_axial):
    """Three-way axial sign agreement, ungated, at alpha = +10 deg.

    Cessna's minimum-drag alpha is near -2..+4 deg, where the axial force is a
    near-cancellation of CL*sin(alpha) and CD*cos(alpha) and its sign is set by
    each solver's own drag prediction rather than by the frame -- measured, at
    alpha = 4 deg the three solvers actually *straddle* the crossover (see
    ``test_axial_force_agrees_in_sign_across_the_sweep``). At alpha = +10 deg the
    axial force is 7-10% of the force scale for all three, so the sign is
    meaningful and no gate is needed:

        DATCOM ca +0.109, AVL CXtot +0.10641, Tornado CX +0.083146
    """
    datcom, avl, tornado, state = at_axial
    alpha = float(np.degrees(state["alpha"]))
    i = int(np.argmin(np.abs(np.asarray(datcom["alpha"], float) - alpha)))
    a = _avl_at(avl, alpha)
    signs = {np.sign(datcom["ca"][i]), np.sign(a["CXtot"]), np.sign(tornado["CX"])}
    assert len(signs) == 1, (
        f"axial force signs disagree at alpha = {alpha}: "
        f"datcom {datcom['ca'][i]}, avl {a['CXtot']}, tornado {tornado['CX']}"
    )
    assert np.sign(tornado["CX"]) > 0, "at alpha = +10 deg the axial force is forward-positive"


def test_axial_force_agrees_in_sign_across_the_sweep(sweep):
    """DATCOM vs AVL axial sign at every alpha where the axial force resolves.

    Both sweep the same 17-rung ladder, so this is 15 real comparisons rather
    than the single one the brief's index arithmetic would have given -- and it
    is where the sign map earns its keep.

    Measured: the two solvers' axial signs agree at **15 of 17** alphas, and
    **disagree at alpha = +4 deg**:

        alpha = +4:  DATCOM ca -0.0010, AVL CXtot +0.004940
        alpha = +5:  DATCOM ca +0.0110, AVL CXtot +0.016410

    That is physical, not a frame error. Cessna's drag minimum sits at about
    alpha = +4 deg, where the axial force is 0.0018 (DATCOM) / 0.0090 (AVL) of the
    total force scale -- a cancellation of two comparable terms. The solvers
    straddle the crossover because they predict CD differently (0.0370 vs
    0.0315), and all 15 other alphas agree. Every other disagreement-free alpha
    confirms the map.

    Two guards keep the cancellation gate honest: ``compared >= 12`` so it cannot
    be used to hollow the test out (measured 15), and ``skipped == {3.0, 4.0}``
    so it cannot be loosened to exclude alphas that *should* be compared -- AVL's
    own axial force at alpha = 3 deg is 0.0098 of the force scale, just under the
    band.
    """
    datcom, avl, _tornado, _state = sweep
    compared: list[float] = []
    skipped: list[float] = []
    for i, raw_alpha in enumerate(datcom["alpha"]):
        alpha = float(raw_alpha)
        a = _avl_at(avl, alpha)
        d_scale = abs(datcom["cd"][i]) + abs(datcom["cl"][i])
        a_scale = abs(a["CDtot"]) + abs(a["CLtot"])
        if abs(datcom["ca"][i]) < _CANCEL * d_scale or abs(a["CXtot"]) < _CANCEL * a_scale:
            skipped.append(alpha)
            continue
        compared.append(alpha)
        assert np.sign(datcom["ca"][i]) == np.sign(a["CXtot"]), (
            f"axial force signs disagree at alpha = {alpha}: "
            f"datcom {datcom['ca'][i]}, avl {a['CXtot']}"
        )
    assert len(compared) >= 12, (
        f"only {len(compared)} alphas resolved the axial force (skipped {skipped}); "
        "the cancellation gate must not hollow this test out"
    )
    assert skipped == [3.0, 4.0], f"unexpected alphas inside the cancellation band: {skipped}"


def test_beta_derivatives_agree_in_sign(sweep):
    """All three solvers agree on the sign of the sideslip derivatives.

    Measured at alpha = -4 deg, beta = 0 (DATCOM's only rung with real values):

        Cnb:  DATCOM +0.045550, AVL +0.183805, Tornado +0.306882
        Clb:  DATCOM -0.090470, AVL -0.073277, Tornado -0.071587
        CYb:  DATCOM -0.691560, AVL -0.398866, Tornado -0.398707

    All three are well conditioned even at beta = 0, because they are
    derivatives, so no gate is needed.

    This is the test the teeth check breaks: with ``to_frd("tornado", ...)``
    removed from ``tornado/coeff.py``, ``Cl_b`` and ``Cn_b`` come back
    un-mirrored and the roll and yaw rows fail.
    """
    datcom, avl, tornado, _state = sweep
    a = _avl_at(avl, _ALPHA_NEG4)
    for label, d, v, t in (
        ("yaw", datcom["cnb"][0] * 180 / np.pi, a["Cnb"], tornado["Cn_b"]),
        ("roll", datcom["clb"][0] * 180 / np.pi, a["Clb"], tornado["Cl_b"]),
        ("side", datcom["cyb"][0] * 180 / np.pi, a["CYb"], tornado["CY_b"]),
    ):
        signs = {np.sign(d), np.sign(v), np.sign(t)}
        assert len(signs) == 1, f"{label} beta-derivative signs disagree: {signs}"


def test_damping_derivatives_still_agree(sweep):
    """Roll and yaw damping stay negative and keep agreeing with AVL.

    These three are the falsifiable core of the tornado rate-derivative entries.
    They are there for a structural reason, not a measured one: ``p`` is about x
    and ``r`` about z, the two axes that reverse between tornado's frame and
    F-R-D, while the roll and yaw moment channels reverse too -- so the two signs
    cancel and ``Cl_P``/``Cl_R``/``Cn_P``/``Cn_R`` take no entry. The measurement
    below confirms that is what the map already does. Measured at alpha = -4 deg:

        Clp:  AVL -0.486877, Tornado Cl_P -0.475617  (ratio 0.98)
        Cnr:  AVL -0.204695, Tornado Cn_R -0.293870  (ratio 1.44)
        Cmq:  AVL -18.466129, Tornado Cm_Q -33.251274 (ratio 1.80)

    **The cancellation is not universal, and these three do not show it.** It
    holds only for channels whose own sign is -1. ``Cm_Q`` survives it for the
    trivial reason that ``Cm`` does not reverse at all, and it says nothing about
    the q axis; a q-derivative whose channel *does* reverse keeps that sign,
    because q is about y and y is the one axis both frames share. That is
    ``CZ_Q``, and it is asserted against AVL in
    ``test_pitch_rate_derivative_agrees_with_avl``. Likewise ``CY_P``/``CY_R`` and
    ``Cm_P``/``Cm_R`` do not cancel, their channels being +1.
    """
    _datcom, avl, tornado, _state = sweep
    a = _avl_at(avl, _ALPHA_NEG4)
    assert np.sign(a["Clp"]) == np.sign(tornado["Cl_P"]) < 0
    assert np.sign(a["Cnr"]) == np.sign(tornado["Cn_R"]) < 0
    assert np.sign(a["Cmq"]) == np.sign(tornado["Cm_Q"]) < 0


@pytest.fixture(scope="module")
def pitch_rate_frame(tmp_path_factory):
    """Tornado's ``CZ_Q`` beside AVL's own ``CZq``, at one shared alpha.

    ``run_avl_full`` returns the merged ``.st`` block, which has no ``CZq``; that
    one is in the ``.sb`` geometry-axis block (``avl_parse.parse_sb``), so this
    fixture parses it directly rather than widening every other caller.
    """
    tmp = tmp_path_factory.mktemp("frd_pitchrate")
    ac = load_jsonc(CESSNA)
    ac.AERO["ALSCHD"] = [_ALPHA_NEG4]
    tornado, state = _run_tornado(ac, tmp)
    assert float(np.degrees(state["alpha"])) == pytest.approx(_ALPHA_NEG4)
    avl_ac = load_jsonc(CESSNA)
    avl_ac.AERO["ALSCHD"] = [_ALPHA_NEG4]
    avl_dir = tmp / "avl"
    run_avl_full(avl_ac, ("10", "10"), avl_dir)
    sb = parse_sb(avl_dir / "geometry.sb")
    assert sb.get("CZq") is not None, "AVL printed no CZq; this fixture is broken, not the map"
    return tornado, sb


def test_pitch_rate_derivative_agrees_with_avl(pitch_rate_frame):
    """``CZ_Q`` has the same sign in tornado and AVL, and is the same size.

    The one live, cross-solver, magnitude-bearing witness for the q-derivatives.
    q is the only body rate whose axis (y, right) both frames share, so a
    q-derivative keeps its channel's sign instead of cancelling -- and ``CZ_Q``
    is the q-derivative with a number on it. AVL is natively F-R-D, so its
    printed ``CZq`` is already the answer: **-9.927762** at alpha = -4 deg on
    Cessna 172, against tornado's ``-9.465924`` after ``to_frd``. Before the
    ``CZ_Q`` entry it read **+9.465924**, i.e. the opposite sign.

    The magnitude band is what stops the sign assertion from passing on two
    same-signed but unrelated quantities: the measured agreement is 4.7% here and
    under 8% across alpha = -4, 0, +4, +6 on Cessna and -4..+6 on Learjet 23,
    while an unflipped value is off by -95%. 0.5..2.0 is the band around that.
    """
    tornado, sb = pitch_rate_frame
    assert np.sign(tornado["CZ_Q"]) == np.sign(sb["CZq"]) < 0
    ratio = abs(tornado["CZ_Q"]) / abs(sb["CZq"])
    assert 0.5 <= ratio <= 2.0, f"|CZ_Q| / |CZq| = {ratio}"


def test_cl_r_derivative_agrees_in_sign(sweep):
    """``Cl_R`` is the fourth sign-stable member of the p/r cancellation.

    ``Cl_R`` needs no map entry for a structural reason -- ``Cl`` and the yaw rate
    axis both reverse, so the two signs cancel -- and this is the measurement that
    says the map has it right, not the reason. Do not read it as support for
    "rate derivatives are never flipped": that is false, and ``CZ_Q``
    (``test_pitch_rate_derivative_agrees_with_avl``) and ``CY_R``/``Cm_R`` are the
    counter-examples.

    The brief's damping test covers ``Clp``/``Cnr``/``Cmq`` only, which leaves
    this other sign-stable pair unpinned. Measured at alpha = -4 deg, AVL ``Clr``
    +0.013363 against Tornado ``Cl_R`` +0.047417 (ratio 3.55) -- same sign at
    both -4 deg and +4 deg (+0.135087 / +0.044525, ratio 0.33).

    **``Cn_P`` is excluded and the reason is not "it failed".** Measured
    ``Cnp`` +0.070706 against Tornado ``Cn_P`` -0.052579 at alpha = -4 deg, but
    +0.007108 / +0.068671 at alpha = +4 deg: the sign is not stable across alpha,
    because both values are ~1e-2 cross-coupling terms between axes that barely
    couple on a Cessna. A sign assertion on an alpha-dependent sign is not an
    invariant of the sign convention, so it is reported rather than asserted.
    Its magnitude ratio is 0.74 (-4 deg) and 9.66 (+4 deg), which is why it is
    also outside the band in
    ``test_lateral_derivatives_are_the_same_order_as_avl``.
    """
    _datcom, avl, tornado, _state = sweep
    a = _avl_at(avl, _ALPHA_NEG4)
    assert np.sign(a["Clr"]) == np.sign(tornado["Cl_R"]), (
        f"AVL Clr {a['Clr']} vs Tornado Cl_R {tornado['Cl_R']}"
    )


def test_frd_physical_signs_hold(sweep):
    """The classical stability signs hold in Forward-Right-Down.

    This pins the map against aerodynamics rather than against another solver: a
    weathervane has to weathervane (Cn_beta > 0), dihedral has to roll away from
    the sideslip (Cl_beta < 0), and the damping terms have to damp. It is the
    check that would catch a map that mirrored two solvers' entries
    consistently -- the one failure mode a cross-solver comparison cannot see.
    """
    _datcom, avl, tornado, _state = sweep
    a = _avl_at(avl, _ALPHA_NEG4)
    assert a["Cnb"] > 0.0, "weathercock stability: Cn_beta must be positive"
    assert a["Clb"] < 0.0, "dihedral effect: Cl_beta must be negative"
    assert a["CYb"] < 0.0, "side force opposes sideslip"
    assert a["Clp"] < 0.0 and a["Cnr"] < 0.0 and a["Cmq"] < 0.0
    assert tornado["Cn_b"] > 0.0 and tornado["Cl_b"] < 0.0 and tornado["CY_b"] < 0.0


def test_lateral_derivatives_are_the_same_order_as_avl(sweep):
    """Tornado's sideslip derivatives are within a factor of 5 of AVL's.

    Two different solvers by two different methods, so only the order of
    magnitude is claimed. Measured at alpha = -4 deg the band is not close to
    binding -- the ratios are 1.67, 0.98 and 1.00, all within 1.7x of unity --
    so the band was left at the brief's 0.2..5.0 rather than widened to fit.

    The band is deliberately *not* applied to ``Cl_R``/``Cn_P``: measured ratios
    are 3.55 and 0.74 at alpha = -4 deg, but 0.33 and 9.66 at alpha = +4 deg.
    Both are ~1e-2 cross-coupling terms on an airframe whose axes barely couple,
    so their ratio is noise-dominated, and a band wide enough to hold ``Cn_P`` at
    both alphas would be wider than the quantity. ``Cl_R`` is covered by sign in
    ``test_cl_r_derivative_agrees_in_sign``; ``Cn_P`` is excluded for the
    alpha-dependence documented there.
    """
    _datcom, avl, tornado, _state = sweep
    a = _avl_at(avl, _ALPHA_NEG4)
    for label, v, t in (
        ("Cnb", a["Cnb"], tornado["Cn_b"]),
        ("Clb", a["Clb"], tornado["Cl_b"]),
        ("CYb", a["CYb"], tornado["CY_b"]),
    ):
        ratio = abs(t / v)
        assert 0.2 < ratio < 5.0, f"{label}: Tornado {t} vs AVL {v}, ratio {ratio:.4f}"
