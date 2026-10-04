"""Pin ``aid.axes._SIGN_MAP``, including the keys that must NOT be flipped.

Every fixture value is non-zero on purpose. A ``0.0`` fixture cannot falsify a
sign: ``-0.0 == 0.0``, and ``-0.0 == pytest.approx(0.0)`` is also ``True``, so
any mutation of that key's sign or membership would survive.
"""

import numpy as np
import pytest

from aid.axes import _SIGN_MAP, from_frd, to_frd

SOLVERS = ("avl", "datcom", "tornado", "flow5")

# The one rule the tornado entries follow, written out instead of enumerated by
# hand, so the map can be checked against a derivation rather than against
# whatever it happens to contain today.
#
# tornado's native body frame is x aft / y right / z up; F-R-D is x fwd / y right /
# z down. That is a 180 deg rotation about y, so x and z reverse and y does not:
#     AXIS_SIGN = {"x": -1, "y": +1, "z": -1}
# A component along axis i therefore picks up AXIS_SIGN[i]. A derivative with
# respect to a body rate about axis j picks up AXIS_SIGN[j] as well, so
#     dC_i/d(omega_j)  ->  AXIS_SIGN[i] * AXIS_SIGN[j]
# and because p is about x and r is about z, those two cancel for every channel,
# while q -- the one axis the two frames share -- leaves the channel's own sign
# standing. Alpha, beta and control deflections are rotations of the *flow*, not
# of the body axes, so they are invariant: they contribute a factor of +1.
AXIS_SIGN = {"x": -1, "y": 1, "z": -1}
# Channel -> the body axis its force or moment component lies along. Note that
# the roll moment is about x and the yaw moment about z, so Cl/Cn follow CX/CZ's
# sign and Cm follows CY's.
CHANNEL_AXIS = {"CX": "x", "CY": "y", "CZ": "z",
                "Cl": "x", "Cm": "y", "Cn": "z"}
# Rate suffix -> the body axis that rate is measured about.
RATE_AXIS = {"P": "x", "Q": "y", "R": "z"}
# Perturbations that leave the body axes alone, so they only carry s_i.
INVARIANT_SUFFIXES = ("", "_a", "_b", "_d")
# The control-derivative values are lists (one per control), the rest scalars.
_LIST_SUFFIXES = ("_d",)


def derived_tornado_signs() -> dict[str, int]:
    """The tornado sign map, derived: ``dC_i/d(omega_j) -> s_i * s_j``."""
    derived: dict[str, int] = {}
    for channel, axis in CHANNEL_AXIS.items():
        s_i = AXIS_SIGN[axis]
        for suffix in INVARIANT_SUFFIXES:
            derived[f"{channel}{suffix}"] = s_i
        for suffix, rate_axis in RATE_AXIS.items():
            derived[f"{channel}_{suffix}"] = s_i * AXIS_SIGN[rate_axis]
    return derived


def _negated(value):
    return [-v for v in value] if isinstance(value, list) else -value


def test_datcom_flips_axial_and_normal_only():
    raw = {"alpha": [1.0, 2.0], "cd": [0.02, 0.03], "cl": [0.1, 0.2],
           "cm": [0.01, -0.02], "cn": [0.1, 0.2], "ca": [0.02, 0.01],
           "xcp": [0.1, 0.05], "cla": [0.09, 0.09], "cyb": [-0.01, -0.01],
           "cnb": [0.001, 0.001], "clb": [-0.002, -0.002]}
    got = to_frd("datcom", raw)
    assert got["ca"] == [-0.02, -0.01]
    assert got["cn"] == [-0.1, -0.2]
    for key in ("cd", "cl", "cm", "xcp", "cla", "cyb", "cnb", "clb", "alpha"):
        assert got[key] == raw[key], key
        assert got[key] is raw[key], key
    assert raw["ca"] == [0.02, 0.01], "to_frd must not mutate its input"


def test_tornado_flips_axial_normal_roll_yaw_and_their_non_rate_derivatives():
    raw = {"CX": -0.04, "CY": 0.12, "CZ": 0.54, "Cl": 0.003, "Cm": -0.95, "Cn": -0.027,
           "CX_a": -0.2, "CY_a": 0.31, "CZ_a": 4.2, "Cl_a": 0.01, "Cm_a": -1.4, "Cn_a": -0.07,
           "CX_b": 0.021, "CY_b": -0.3, "CZ_b": 0.041, "Cl_b": 0.05, "Cn_b": -0.25,
           "CX_P": 0.011, "CY_P": 0.13, "CZ_P": 0.017, "Cl_P": -0.49,
           "Cl_Q": -0.15, "Cl_R": 0.04,
           "CX_Q": 0.021, "CY_Q": -0.22, "CZ_Q": 0.31,
           "Cm_Q": -8.0, "Cn_P": 0.07, "Cn_Q": -0.09, "Cn_R": -0.29,
           "CX_R": -0.013, "CY_R": 0.4, "CZ_R": -0.019,
           "CC": 0.02,
           "CX_d": [-1.0], "CY_d": [0.1], "CZ_d": [-2.0],
           "Cl_d": [0.5], "Cn_d": [0.6]}
    got = to_frd("tornado", raw)
    flipped = ("CX", "CZ", "Cl", "Cn", "CX_a", "CZ_a", "Cl_a", "Cn_a",
               "CX_b", "CZ_b", "Cl_b", "Cn_b", "CX_d", "CZ_d", "Cl_d", "Cn_d",
               # q is the one rate axis both frames share, so the q-derivatives
               # keep their channel's own sign while the p and r ones cancel.
               "CX_Q", "CZ_Q", "Cl_Q", "Cn_Q",
               # ... and CY is the one channel whose own sign is +1, so for its
               # p and r rate derivatives nothing cancels and they do flip.
               "CY_P", "CY_R")
    for key in flipped:
        assert got[key] == pytest.approx(_negated(raw[key])), key
    # p and r reverse with the axes they are measured about, so for every
    # p/r-flavoured channel the two flips cancel and no entry may be applied.
    # Cl_P -0.486 already agrees with AVL's Clp -0.470, which is the measured
    # confirmation; Cl_R and Cn_P say the same about r and about a fuselage.
    not_flipped = ("CY", "Cm", "CY_a", "CY_b", "CY_Q", "CC", "Cm_a", "Cm_Q",
                   "CX_P", "CZ_P", "Cl_P", "Cn_P",
                   "CX_R", "CZ_R", "Cl_R", "Cn_R")
    for key in not_flipped:
        assert got[key] == pytest.approx(raw[key]), key
    assert got["Cl_d"] == [-0.5] and got["Cn_d"] == [-0.6]
    assert got["CY_d"] == [0.1]


def test_tornado_sign_map_is_exactly_the_derived_rule():
    """``_SIGN_MAP["tornado"]`` equals ``dC_i/d(omega_j) -> s_i * s_j``, key for key.

    The named test above pins the interesting keys with realistic magnitudes.
    This one pins the *whole* universe ``coeff_create`` emits, so a channel that
    nobody remembered cannot be missing from the map. Both directions matter and
    are checked here: every key the rule says flips must be flipped, and the map
    must not hold a key the rule leaves alone -- an entry that would be a no-op
    today and a silent mirror the day a solver changes frame.

    Every fixture value is 1.0, which is falsifiable in both directions: 1.0 and
    -1.0 differ, whereas a 0.0 fixture would pass either way.
    """
    derived = derived_tornado_signs()
    raw = {key: [-1.0] if key.endswith(_LIST_SUFFIXES) else 1.0 for key in derived}
    got = to_frd("tornado", raw)

    for key, sign in derived.items():
        expected = _negated(raw[key]) if sign == -1 else raw[key]
        assert got[key] == pytest.approx(expected), key

    assert set(_SIGN_MAP["tornado"]) == {k for k, v in derived.items() if v == -1}
    # The rule must produce both halves, or the equality above is vacuous.
    assert "CX_Q" in _SIGN_MAP["tornado"] and "Cl_P" not in _SIGN_MAP["tornado"]
    assert "CZ_R" not in _SIGN_MAP["tornado"] and "Cn_Q" in _SIGN_MAP["tornado"]
    # CY and Cm are the channels whose own sign is +1, so p and r do not cancel
    # for them and q is the only rate that leaves them alone.
    for key in ("CY_P", "CY_R", "Cm_P", "Cm_R"):
        assert key in _SIGN_MAP["tornado"], key
    for key in ("CY", "CY_Q", "Cm", "Cm_Q", "CY_a", "Cm_a"):
        assert key not in _SIGN_MAP["tornado"], key


def test_tornado_wind_axis_channels_are_never_flipped():
    """``CL``/``CD``/``CC`` and their derivatives are wind-axis, not body-axis.

    ``coeff.py:76-100`` builds them from the ``b2w`` wind rotation directly, so
    none of them is a body component and none of them can pick up an axis sign --
    including their rate derivatives, which is why ``CL_Q`` and ``CD_R`` are
    absent while ``CY_Q`` and ``Cm_Q`` are present for the same rate axis. This
    is the measured claim (raw tornado ``CL`` +0.168 against AVL ``CLtot``
    +0.169, both already lift-positive) rather than an inference from the rule.
    """
    raw = {key: 1.0 for key in ("CL", "CD", "CC", "CLwing", "CDwing", "CYwing")}
    for suffix in ("_a", "_b", "_P", "_Q", "_R"):
        for channel in ("CL", "CD", "CC"):
            raw[f"{channel}{suffix}"] = 1.0
    got = to_frd("tornado", raw)
    assert got == raw
    for key in raw:
        assert got[key] is raw[key], key
    assert not [k for k in _SIGN_MAP["tornado"] if k.startswith(("CL", "CD", "CC"))]


def test_no_other_solver_needs_a_pitch_rate_entry():
    """``CX_Q``-shaped entries are a tornado-only need; the other maps are complete.

    flow5 emits p and r rate derivatives but no q ones: the twelve names in
    ``FLOW5/run/flow5_run.cpp``'s ``stab_derivative_fields()`` (:304-321) are
    ``CXa, CZa, CYb, CYp, CYr, Clb, Clp, Clr, Cnb, Cnp, Cnr, XNP``, and not one of
    them is a q-derivative. The library *does* have them -- ``StabDerivatives``
    declares ``CXq``, ``CZq`` and ``Cmq`` (``FLOW5/flow5-lib/api/
    stabderivatives.h:70``) and computes them from the dimensional ``Xq``/``Zq``/
    ``Mq`` (``stabderivatives.cpp:123-125``) -- the helper just does not forward
    them, and there is no ``CYq``/``Clq``/``Cnq`` in the library at all. Were the
    three ever forwarded they would need no entry, and not because of any axis
    arithmetic: each is projected onto the same stability axis as a derivative that
    is already forwarded and already entry-free -- ``SD.Xq`` and ``SD.Zq`` on ``is``
    and ``ks`` (``panelanalysis.cpp:1057-1058``) against ``CXa``/``CZa`` on the same
    two (``:880-881``), and ``SD.Mq`` on ``js`` (``:1059``) against the ``Cm`` channel.
    So the map would not have to grow; only ``stab_derivative_fields()`` would.
    datcom's parser extracts no rate derivatives at all: ``_COEF_NAMES`` in
    ``datcom_parse.py`` is the alpha/beta set plus ``ca``/``cn``. avl is natively
    F-R-D, so its map is empty by measurement.
    """
    assert not [k for k in _SIGN_MAP["avl"] if k.endswith(("_P", "_Q", "_R"))]
    assert not [k for k in _SIGN_MAP["datcom"] if k.endswith(("_P", "_Q", "_R"))]
    assert not [k for k in _SIGN_MAP["flow5"] if k.endswith(("_P", "_Q", "_R"))]
    assert set(_SIGN_MAP["flow5"]) == {"Cx", "Cz", "Cl", "Cn"}
    assert set(_SIGN_MAP["datcom"]) == {"ca", "cn"}
    assert _SIGN_MAP["avl"] == {}


def test_avl_is_identity():
    raw = {"CXtot": 0.03, "CZtot": -0.6, "CYtot": -0.02, "Cltot": 0.014,
           "Cmtot": -0.2, "Cntot": 0.031, "Clp": -0.47, "CYb": -0.3,
           "Cnb": 0.17, "Clb": -0.028}
    got = to_frd("avl", raw)
    assert got == raw
    for key in raw:
        assert got[key] is raw[key], key


def test_flow5_flips_the_four_lateral_channels_and_nothing_else():
    # R18. flow5 does NOT flip the way Tornado does: the two agree on the force
    # channels (Cx/Cz are raw aft/up-positive) and disagree on the moment ones.
    # Cl/Cn come from polar vars 12/13 (Cli/Cni), which are mirrored -- raw Cl
    # +0.0047339 at beta = +5, alpha = 0, against Clb*beta = -0.0046262. Everything
    # else takes no entry: computeStabilityDerivatives projects onto the
    # stability axes (panelanalysis.cpp:845-846), already Forward-Right-Down, so
    # CXa (which is CL - dCD/dalpha, not a bare -dCD/dalpha), CZa (already
    # -5.2562), CYb, Clb, Cnb and the rate derivatives all pass through.
    raw = {"Cx": -0.031, "Cz": 0.544, "Cl": 0.0047, "Cn": -0.0143,
           "CXa": 0.0595, "CZa": -5.2562, "CY": 0.06, "Cm": -0.95,
           "CYb": -0.4107, "Clb": -0.053, "Cnb": 0.1685,
           "Clp": -0.5385, "Cnr": -0.206}
    got = to_frd("flow5", raw)
    for key in ("Cx", "Cz", "Cl", "Cn"):
        assert got[key] == pytest.approx(-raw[key]), key
    for key in ("CXa", "CZa", "CY", "Cm", "CYb", "Clb", "Cnb", "Clp", "Cnr"):
        assert got[key] == pytest.approx(raw[key]), key
        assert got[key] is raw[key], key
    assert raw["Cl"] == 0.0047, "to_frd must not mutate its input"


def test_cy_and_cc_are_never_flipped():
    """The Global Constraint: the ``CY`` and ``CC`` *channels* pass through every solver.

    Scoped precisely, because the loose phrasing once hid two real entries.
    ``CY`` is the one channel whose own sign is already F-R-D (+1) *and* which is
    measured against a reversing rate, so ``s_i * s_j`` does not cancel for it:
    ``CY_P`` and ``CY_R`` do take a ``-1`` under tornado (AVL's ``CYp`` -0.182 and
    ``CYr`` +0.427 against tornado's raw +0.160 and -0.387, both opposite before
    the flip and within 15% after). Its alpha/beta/control derivatives, and every
    ``CC`` key, are never flipped.
    """
    raw = {"CY": -0.31, "CC": 0.017, "CY_a": 0.42, "CY_b": -0.28,
           "CY_Q": -0.19, "CY_d": [-0.06], "CYtot": -0.09,
           "Cltot": 0.021, "Cntot": -0.044}
    for solver in SOLVERS:
        got = to_frd(solver, raw)
        assert got == raw, solver
        for key in raw:
            assert got[key] == raw[key], (solver, key)
            assert got[key] is raw[key], (solver, key)

    # ... and the two exceptions are pinned from the other side, so the pair of
    # tests together is falsifiable in both directions.
    rate = to_frd("tornado", {"CY": -0.31, "CC": 0.017, "CY_P": 0.16, "CY_R": -0.387})
    assert rate["CY"] == pytest.approx(-0.31)
    assert rate["CC"] == pytest.approx(0.017)
    assert rate["CY_P"] == pytest.approx(-0.16)
    assert rate["CY_R"] == pytest.approx(0.387)
    for solver in ("avl", "datcom", "flow5"):
        assert to_frd(solver, {"CY_P": 0.16, "CY_R": -0.387}) == {"CY_P": 0.16, "CY_R": -0.387}


def test_round_trip_is_identity_for_every_solver():
    raw = {"CX": -0.04, "CZ": 0.54, "Cl": 0.003, "Cn": -0.027,
           "cn": 0.1, "ca": 0.02, "CXtot": 0.03, "Cltot": 0.014, "CZa": -5.2562}
    for solver in SOLVERS:
        assert from_frd(solver, to_frd(solver, raw)) == raw, solver


def test_unknown_solver_raises():
    with pytest.raises(KeyError):
        to_frd("handbook", {"CL": 1.0})
    with pytest.raises(KeyError):
        from_frd("vlm2", {"CL": 1.0})


def test_missing_key_is_absent_not_zero():
    got = to_frd("tornado", {"CL": 0.5})
    assert got == {"CL": 0.5}
    assert "CZ" not in got


def test_structured_values_pass_through_by_identity():
    surface = [{"name": "aileron", "angle": 0.0}]
    high_lift = [{"config": "flap 10", "delta": 10.0, "dcl": [0.3]}]
    cp = np.zeros((4, 3))
    raw = {"surface": surface, "high_lift": high_lift, "cp": cp, "CZ": 0.5}
    got = to_frd("tornado", raw)
    assert got["surface"] is surface
    assert got["high_lift"] is high_lift
    assert got["cp"] is cp
    assert got["CZ"] == -0.5


def test_nd_sentinel_keeps_its_magnitude():
    raw = {"ca": [0.02, 99999.0], "cn": [99999.0, 0.1], "cd": [0.02, 99999.0]}
    got = to_frd("datcom", raw)
    assert got["ca"] == [-0.02, -99999.0]
    assert got["cn"] == [-99999.0, -0.1]
    assert got["cd"] == [0.02, 99999.0]
    masked = np.abs(np.asarray(got["ca"], dtype=float)) >= 99998
    assert list(masked) == [False, True], "a negated ND must still mask"


def test_numpy_arrays_stay_arrays():
    raw = {"CZ": np.array([0.5, 0.6])}
    got = to_frd("tornado", raw)
    assert isinstance(got["CZ"], np.ndarray)
    assert got["CZ"].tolist() == [-0.5, -0.6]