"""flow5's channels after normalization to Forward-Right-Down.

``run_flow5`` is the boundary where ``aid.axes.to_frd("flow5", ...)`` takes
effect, and this file pins what that boundary does to a real Cessna solve.

Three things it deliberately does **not** assert, each of which the plan and the
spikes settled against a more obvious guess:

* ``CXa``/``CZa`` are **not** flipped. Both already measure down/forward-negative
  (``CZa`` -5.2562, ``CXa`` +0.0595), so they are already Forward-Right-Down.
  The gold's *convention* for that lives at
  ``Matlab/fsroot/code/Longitudinal_Dynamic_Stability.m:22,35`` -- for anyone
  who wants the mechanism, not as a number this file could check. See
  ``test_flow5_cza_is_not_flipped`` below for why the identity itself is not
  asserted here.
* ``Cdvis``/``CDind`` say nothing about viscous drag here. ``flow5_run.cpp:396``
  calls ``setViscous(false)``, so ``CDvis`` is identically 0.0 and ``CDind`` is
  identically ``CD``. That is an honest exposure of a locked setup, not a result,
  and nothing here reads a physical conclusion out of it.
* ``Cl``/``Cn`` **are** flipped, which is why the sweep's moment channels move
  from raw to normalized while ``CY`` does not. flow5 does not flip exactly like
  Tornado: the coincidence holds for its forces and fails for its moments.

The derivatives are a beta = 0 curve by construction -- ``computeStability-
Derivatives`` builds its axes from ``windDirection(alpha, 0.0)``, so all twelve
scalars are byte-identical at beta = 0, +5 and -5 (R13). Labelling that is Task
3.2's job; this file only records it.
"""

import numpy as np
import pytest

from aid.aircraft import load_jsonc
from aid.flow5_io import run_flow5, run_flow5_native, write_flow5_deck
from aid.paths import flow5_bin, models_dir

FLOW5_BIN = flow5_bin()
MESH = ("10", "10")

# Per-test rather than module-level so the key-list tests below, which need no
# solver, keep running where flow5_run is not built; each test that shells out to
# flow5_run carries this instead.
needs_flow5 = pytest.mark.skipif(
    not FLOW5_BIN.is_file(), reason="flow5 helper not built"
)

# The four channels the flow5 sign map names. Everything else run_flow5 returns
# must come out of to_frd unchanged.
FLIPPED = ("Cx", "Cz", "Cl", "Cn")

# Every key run_flow5 returns. Hand-written, and read by the gated solve test
# below, which is what keeps it honest -- that is the one place a channel added
# later shows up as a failure. It is deliberately not cross-checked against
# compare_tabs._SKIP_LEFTOVER: _leftover_groups only ever walks the Tornado and
# AVL result dicts, so a flow5 key named there could not suppress anything.
FLOW5_KEYS = frozenset(
    {
        "alpha", "beta", "CL", "CD", "CDvis", "CDind", "Cm",
        "CY", "Cl", "Cn", "Cx", "Cz",
        "CLa", "Cma",
        "CXa", "CZa", "CYb", "CYp", "CYr",
        "Clb", "Clp", "Clr", "Cnb", "Cnp", "Cnr", "XNP",
    }
)

DERIVATIVES = (
    "CXa", "CZa", "CYb", "CYp", "CYr",
    "Clb", "Clp", "Clr", "Cnb", "Cnp", "Cnr", "XNP",
)


@pytest.fixture(scope="module")
def _ac():
    return load_jsonc(models_dir() / "Cessna 172.jsonc")


@pytest.fixture(scope="module")
def cessna_flow5(_ac):
    """The normalized solve: what every caller and every plot sees."""
    return run_flow5(_ac, MESH)


@pytest.fixture(scope="module")
def cessna_flow5_native(_ac):
    """The same solve one layer down, still in flow5's own frame."""
    return run_flow5_native(write_flow5_deck(_ac, MESH))


@pytest.fixture(scope="module")
def cessna_flow5_beta5(_ac):
    return run_flow5(_ac, MESH, beta=5.0)


def _alpha_zero(ces: dict) -> int:
    return int(np.argmin(np.abs(np.asarray(ces["alpha"]))))


@needs_flow5
def test_flow5_cx_flips_into_forward_right_down(cessna_flow5):
    # At alpha = 0 the axial component reduces to CD exactly (raw Cx - CD is 0.0,
    # measured), which is the one alpha where the aft-positive reading is
    # unambiguous: raw is +0.0012434, so F-R-D must be -0.0012434.
    i = _alpha_zero(cessna_flow5)
    cd = cessna_flow5["CD"][i]
    assert cd > 0.0
    assert cessna_flow5["Cx"][i] == pytest.approx(-cd, abs=0.0, rel=1e-15)
    assert cessna_flow5["Cx"][i] < 0.0, "raw Cx is aft-positive, so F-R-D must be forward-positive"

    # NOT `Cx < 0` at argmax(CL): raw Cx is aft-positive at only 2 of the 17
    # sweep alphas (-1 and 0) and reads -0.1828 at alpha = +12, so after the flip
    # it reads +0.1828 there. A single-point sign test passes by luck. Assert the
    # identity instead, which holds at every alpha: raw Cx = CD*cos(a) -
    # CL*sin(a), so normalized Cx = -(that). Measured residual <= 1.9e-16.
    a = np.deg2rad(np.asarray(cessna_flow5["alpha"]))
    cx = np.asarray(cessna_flow5["Cx"], dtype=float)
    cd_a = np.asarray(cessna_flow5["CD"], dtype=float)
    cl_a = np.asarray(cessna_flow5["CL"], dtype=float)
    assert np.allclose(cx, -(cd_a * np.cos(a) - cl_a * np.sin(a)), atol=3.2e-13)


@needs_flow5
def test_flow5_cz_flips_into_forward_right_down(cessna_flow5):
    # Unlike Cx, Cz stays up-positive for every alpha of this sweep, so the
    # argmax(CL) sign test is sound here: raw is +1.1948 at alpha = +12 with
    # CL = +1.2067, so F-R-D must be -1.1948, i.e. down-negative.
    j = int(np.argmax(np.asarray(cessna_flow5["CL"], dtype=float)))
    assert cessna_flow5["CL"][j] > 0.0
    assert cessna_flow5["Cz"][j] < 0.0
    a = np.deg2rad(np.asarray(cessna_flow5["alpha"]))
    cz = np.asarray(cessna_flow5["Cz"], dtype=float)
    cd_a = np.asarray(cessna_flow5["CD"], dtype=float)
    cl_a = np.asarray(cessna_flow5["CL"], dtype=float)
    assert np.allclose(cz, -(cd_a * np.sin(a) + cl_a * np.cos(a)), atol=3.2e-13)
    # Note Cz == -CL only at alpha = 0; it is -1.19e-2 away from it at alpha = +12.


@needs_flow5
def test_flow5_cy_is_not_flipped_and_cl_cn_are(cessna_flow5, cessna_flow5_native):
    # CY is wind-axis side force and no solver ever flips it (Global Constraint).
    # Cl/Cn come from polar vars 12/13 (Cli/Cni), which are mirrored -- measured
    # raw Cl +0.0047339 at beta = +5, alpha = 0, against a F-R-D prediction of
    # Clb*beta = -0.0046262. Opposite, so both take a -1.
    for key in ("CY", "Cl", "Cn"):
        assert key in cessna_flow5
    assert cessna_flow5["CY"] == cessna_flow5_native["CY"]
    assert cessna_flow5["Cl"] == [-v for v in cessna_flow5_native["Cl"]]
    assert cessna_flow5["Cn"] == [-v for v in cessna_flow5_native["Cn"]]


@needs_flow5
def test_only_the_four_mapped_channels_differ_from_the_raw_solve(cessna_flow5, cessna_flow5_native):
    # Exhaustive, so a future key added to run_flow5 cannot slip through
    # unnormalized by omission: every other key must be identical to raw.
    assert set(cessna_flow5) == set(cessna_flow5_native)
    for key in sorted(cessna_flow5):
        if key in FLIPPED:
            assert cessna_flow5[key] == [-v for v in cessna_flow5_native[key]], key
        else:
            assert cessna_flow5[key] == cessna_flow5_native[key], key


@needs_flow5
def test_flow5_lateral_derivatives_survive_normalization(cessna_flow5):
    assert cessna_flow5["Cnb"] > 0.0, "weathercock stability"
    assert cessna_flow5["Clb"] < 0.0, "dihedral effect"
    assert cessna_flow5["CYb"] < 0.0, "side force opposes sideslip"
    # They take no entry in the sign map because computeStabilityDerivatives
    # projects onto the stability axes (panelanalysis.cpp:845-846), which is
    # already F-R-D -- so they must survive to_frd untouched.
    for key in DERIVATIVES:
        assert float(cessna_flow5[key]) != 0.0, key


@needs_flow5
def test_flow5_cza_is_already_forward_right_down_so_it_takes_no_entry(
    cessna_flow5, cessna_flow5_native
):
    # CZa measures -5.2562 per radian, so dCZ/dalpha is already down-negative and
    # already Forward-Right-Down; a -1 would advertise +5.2562, a lift-curve-slope
    # positive "downforce" channel. Measured value only -- the identity behind it
    # is deliberately NOT asserted here.
    #
    # The gold's convention is Matlab/fsroot/code/Longitudinal_Dynamic_Stability.m:35,
    # `CZa = -AC.CLa - AC.CD`, which is negative because both terms are. It cannot
    # be re-derived from run_flow5's output: it needs the lift slope AT the
    # reference operating point (5.2550), and run_flow5 emits the OLS slope over
    # the whole sweep (5.1770) -- a different number that the helper does not also
    # expose. A comment citing 5.2550 would therefore look verifiable and not be.
    assert cessna_flow5["CZa"] < 0.0
    assert cessna_flow5["CZa"] == cessna_flow5_native["CZa"]


@needs_flow5
def test_the_key_list_matches_a_real_solve(cessna_flow5, cessna_flow5_native):
    # Keeps FLOW5_KEYS honest: run_flow5 emits exactly these 26 keys, so a
    # channel a later task adds lands in neither this list nor the twelve-name
    # FLOW5_BETA_FLAT set, and this fails.
    assert set(cessna_flow5) == FLOW5_KEYS
    assert set(cessna_flow5_native) == FLOW5_KEYS


@needs_flow5
def test_non_zero_beta_changes_the_lateral_channels(cessna_flow5, cessna_flow5_beta5):
    # Deliverable 3's flow5 half is only worth plotting if a sideslip actually
    # reaches the solver. At beta = 0 these three channels are panel-method
    # round-off (max |v| ~ 7e-07); at beta = +5 they are O(1e-2), five orders of
    # magnitude out. CY/Cl/Cn are compared on the normalized channels, so this
    # also shows the flip did not flatten the sideslip.
    zero = cessna_flow5
    tilted = cessna_flow5_beta5
    assert tilted["beta"][0] == pytest.approx(5.0)
    for key in ("CY", "Cl", "Cn"):
        assert abs(zero[key][0]) < 1e-5, f"{key} at beta = 0 should be round-off"
        assert abs(tilted[key][0]) > 1e-3, f"{key} did not respond to beta"
    # Signs settle too, not just magnitudes: CY opposes the sideslip (F-R-D),
    # weathercock yaw is nose-right and dihedral roll is right-wing-down, so with
    # the mirror applied CY < 0, Cn > 0, Cl < 0 at beta = +5.
    assert tilted["CY"][0] < 0.0
    assert tilted["Cn"][0] > 0.0
    assert tilted["Cl"][0] < 0.0


@needs_flow5
def test_beta_leaves_flow5_derivatives_untouched(cessna_flow5, cessna_flow5_beta5):
    # R13: computeStabilityDerivatives builds its axes from
    # windDirection(alpha, 0.0), so the twelve scalars are a beta = 0 curve that
    # will plot identically at any sideslip. Pin it so nobody later reads a
    # sideslip dependence into them.
    for key in DERIVATIVES:
        assert float(cessna_flow5_beta5[key]) == float(cessna_flow5[key]), key


@needs_flow5
def test_beta_tilts_the_flow_and_not_the_planform(cessna_flow5, cessna_flow5_beta5):
    # The alpha schedule is beta-independent: betaSpec is the polar's second
    # axis' value, not an extra sweep. And because PlaneTask::run rotates the mesh
    # about the CG rather than yawing the geometry, the lift curve barely moves
    # (measured max relative shift 1.7% on CL and Cz over the sweep) -- which is
    # what says beta_deg did not leak into the planform.
    assert cessna_flow5_beta5["alpha"] == cessna_flow5["alpha"]
    for key in ("CL", "Cz"):
        flat = np.asarray(cessna_flow5[key], dtype=float)
        tilted = np.asarray(cessna_flow5_beta5[key], dtype=float)
        assert np.allclose(tilted, flat, rtol=0.02), key
    # CD, Cm and Cx are deliberately not bounded relatively: they pass through
    # zero at the low-alpha end of this sweep (CD 1.2e-03, Cm 4.4e-02, Cx
    # -1.4e-02), where a relative tolerance is meaningless. Their absolute shift
    # is real but is the same geometric effect, not a leak.