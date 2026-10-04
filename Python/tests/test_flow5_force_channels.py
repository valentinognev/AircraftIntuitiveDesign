"""flow5's raw, pre-normalization channels: what it computes but never reads.

The helper used to emit only polar variables 1, 4, 5 and 9 (``alpha``, ``CL``,
``CD``, ``Cm``), which left every lateral panel structurally empty for flow5.
These channels are flow5's own raw output in its own frame -- x aft, y right,
z up -- so ``Cx``/``Cz`` are aft/up-positive and ``Cli``/``Cni`` are mirrored
relative to Forward-Right-Down.

``run_flow5`` returns them **normalized** as of Task 2.3, whose ``flow5`` entry
in ``aid/axes.py`` is ``{"Cx": -1, "Cz": -1, "Cl": -1, "Cn": -1}``. So the tests
below that care about the solver's own frame go through ``run_flow5_native``;
the rest are sign-agnostic and read ``run_flow5`` like every other caller.
``test_flow5_overlay_signs.py`` covers the normalized side.
"""

import json
import subprocess

import numpy as np
import pytest

from aid.aircraft import load_jsonc
from aid.flow5_io import run_flow5, run_flow5_native, write_flow5_deck
from aid.paths import flow5_bin, models_dir

FLOW5_BIN = flow5_bin()
MESH = ("10", "10")

pytestmark = pytest.mark.skipif(
    not FLOW5_BIN.is_file(), reason="flow5 helper not built"
)

# Recorded from FLOW5/run/flow5_run at mesh ("10","10") before these channels
# existed, so this file also pins that emitting them changed nothing else.
REF_CL0 = -0.23527030355832992
REF_CD0 = 0.002445512723296366
REF_CM0 = 0.06768149276941772
REF_CLA = 5.1769701450913255
REF_CMA = -1.5769862731689508


@pytest.fixture(scope="module")
def cessna():
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    return run_flow5(ac, MESH)


@pytest.fixture(scope="module")
def base_deck():
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    return write_flow5_deck(ac, MESH)


@pytest.fixture(scope="module")
def cessna_raw(base_deck):
    """The same Cessna solve still in flow5's own frame: no ``to_frd``."""
    return run_flow5_native(base_deck)


def test_flow5_emits_the_new_channels(cessna):
    for key in ("beta", "CY", "Cl", "Cn", "Cx", "Cz", "CDvis", "CDind"):
        assert key in cessna, key
        assert len(cessna[key]) == len(cessna["alpha"]), key


def test_flow5_existing_channels_are_unchanged(cessna):
    # Byte-for-byte the pre-change values: the new channels are read-only
    # additions to the polar, so nothing that existed may move.
    assert cessna["CL"][0] == pytest.approx(REF_CL0, abs=1e-9)
    assert cessna["CD"][0] == pytest.approx(REF_CD0, abs=1e-9)
    assert cessna["Cm"][0] == pytest.approx(REF_CM0, abs=1e-9)
    assert cessna["CLa"] == pytest.approx(REF_CLA, abs=1e-9)
    assert cessna["Cma"] == pytest.approx(REF_CMA, abs=1e-9)


def test_flow5_lateral_channels_are_zero_at_beta_zero(cessna):
    # atol=1e-5, NOT 1e-9: these are panel-method round-off residuals, not zeros.
    # Measured max|v| over the 17 Cessna alphas at beta = 0 (spike err_b0.txt):
    #   CY 6.750e-07, Cl 6.662e-08, Cn 3.767e-07 -- all fail atol=1e-9.
    assert np.allclose(cessna["beta"], 0.0)
    for key in ("CY", "Cl", "Cn"):
        assert np.allclose(cessna[key], 0.0, atol=1e-5), key


def test_flow5_cx_is_aft_positive_and_cz_is_up_positive(cessna_raw):
    # Pre-normalization frame: x aft, z up. Settled by Task 2.0 spike 4 -- do NOT
    # assert a bare sign at one alpha. Raw Cx = CD*cos(a) - CL*sin(a), so it is
    # aft-positive only while CD*cos(a) > CL*sin(a) and goes NEGATIVE at high alpha
    # (measured: positive at just 2 of the 17 sweep alphas, alpha = -1 and 0;
    # -0.1828 at alpha = +12). A single-point sign test would pass by luck, which
    # is exactly why the brief's original `Cx[i] < 0` at argmax(CL) did. Assert
    # the identity instead, which holds everywhere: residual <= 3.2e-13.
    a = np.deg2rad(np.asarray(cessna_raw["alpha"]))
    assert np.allclose(
        np.asarray(cessna_raw["Cx"]),
        np.asarray(cessna_raw["CD"]) * np.cos(a) - np.asarray(cessna_raw["CL"]) * np.sin(a),
        atol=3.2e-13,
    )
    # Aft-positive, checked where the identity is unambiguous: alpha = 0, where
    # Cx reduces to CD exactly (measured Cx = +0.0012434 vs CD = +0.0012434).
    i = int(np.argmin(np.abs(np.asarray(cessna_raw["alpha"]))))
    assert cessna_raw["Cx"][i] > 0.0, (
        "at alpha = 0 the axial component reduces to CD, so it is aft-positive"
    )
    # Up-positive: Cz is +1.1948 at alpha = +12 with CL = +1.2067.
    j = int(np.argmax(cessna_raw["CL"]))
    assert cessna_raw["Cz"][j] > 0.0
    # And note Cz == CL only at alpha = 0 -- do not assert it across the sweep.
    # Measured: Cz - CL is 0 at alpha = 0 but -1.19e-2 at alpha = +12.


def test_flow5_cd_splits_into_viscous_and_induced(cessna):
    total = np.asarray(cessna["CDvis"]) + np.asarray(cessna["CDind"])
    assert np.allclose(total, cessna["CD"], atol=1e-12)


def test_flow5_beta_deg_reaches_the_solver(base_deck):
    # Task 2.3's deck writer sets polar.beta_deg. Before this, the helper had no
    # way to read it: Polar3D::setBetaSpec is the only lever, and PlaneTask::run
    # picks it up for T1 polars (planetask.cpp:605), rotating the mesh about the
    # CG rather than yawing the geometry.
    base = run_flow5_native(base_deck)
    tilted = dict(base_deck)
    tilted["polar"] = {**base_deck["polar"], "beta_deg": 5.0}
    swept = run_flow5_native(tilted)

    assert np.allclose(base["beta"], 0.0)
    assert np.allclose(swept["beta"], 5.0)
    # Measured (spike err_betap5.txt, alpha = -4 deg): Cy goes from -6.75e-07
    # to -0.03608, i.e. five orders of magnitude past the beta = 0 round-off.
    assert abs(base["CY"][0]) < 1e-5
    assert swept["CY"][0] == pytest.approx(-0.0360813086569, abs=1e-9)
    # And the moments move with it: Cli/Cni are the mirrored channels Task 2.3
    # flips, so their raw signs are what the sign map has to invert.
    assert swept["Cl"][0] == pytest.approx(0.00504129201653, abs=1e-9)
    assert swept["Cn"][0] == pytest.approx(-0.0156115938743, abs=1e-9)


def test_flow5_rejects_a_beta_key_that_is_not_beta_deg(base_deck, tmp_path):
    # R14: the helper has no deck whitelist, so an unknown key is silently
    # ignored -- which would let a typo'd beta key masquerade as beta = 0. The
    # guard is deliberately one purpose, not a general whitelist.
    #
    # The three range cases are the same defect one step on: a beta_deg of the right
    # *type* that is not a sideslip. Nothing downstream bounds it -- PlaneTask::run
    # reads betaSpec() and rotates the mesh by it (planetask.cpp:605, :748) with no
    # range check, so 1e9 deg would come back as a plausible-looking wrong answer
    # rather than an error. The PySide GUI clamps AERO.BETA to +/-89
    # (aid_gui/tabs.py clamp_value, "deg" kind, error_check_data[1] = 89); the API
    # and a hand-edited deck did not, and now hit the same ceiling.
    #
    # The last two are rejected at the deck-parse step rather than by read_beta_spec,
    # so they name the deck and not the key -- which is why each case carries the
    # substring it must produce. A literal too large for a double additionally used
    # to abort the process: the lexer's number-overflow throw is a
    # detail::out_of_range, not a json::parse_error, so main's narrower catch missed
    # it (rc = -6, SIGABRT). Hence the rc > 0 assertion below.
    cases = (
        ("beta_deg", "5", "beta"),  # present but not a number -> json_number() would
        ("beta_deg", None, "beta"),  # silently fall back to 0.0
        ("beta_degg", 5.0, "beta"),  # near-miss typo
        ("BETA_DEG", 5.0, "beta"),
        ("beta_deg", 1e9, "beta_deg"),
        ("beta_deg", -1e9, "beta_deg"),
        ("beta_deg", 89.0001, "beta_deg"),
        ("beta_deg", float("nan"), "json deck"),
        ("beta_deg", float("inf"), "json deck"),
    )
    for i, (polar_key, value, expected) in enumerate(cases):
        deck = dict(base_deck)
        deck["polar"] = {**base_deck["polar"], polar_key: value}
        path = tmp_path / f"deck_{i}.json"
        path.write_text(json.dumps(deck))
        r = subprocess.run(
            [str(FLOW5_BIN), "--deck", str(path)],
            capture_output=True,
            text=True,
            timeout=180,
        )
        assert r.returncode != 0, f"{polar_key}={value!r} was accepted: {r.stdout}"
        assert r.returncode > 0, f"{polar_key}={value!r} crashed: rc={r.returncode}"
        assert r.stdout.strip() == "", f"{polar_key}={value!r} emitted JSON anyway"
        assert expected in r.stderr.lower(), r.stderr


def test_flow5_accepts_beta_deg_at_the_clamps_limit(base_deck):
    # The rejection above is a bound, not a ban: the PySide clamp permits exactly
    # +/-89, so 89.0 must still run.
    out = run_flow5_native(
        {**base_deck, "polar": {**base_deck["polar"], "beta_deg": 89.0}}
    )
    assert np.allclose(out["beta"], 89.0)


def test_flow5_omitted_beta_deg_still_runs_at_beta_zero(base_deck):
    # Absent is not the same as rejected: omitting beta_deg is the normal path
    # and must keep working, and must be indistinguishable from beta_deg = 0.
    plain = run_flow5_native(base_deck)
    explicit = run_flow5_native(
        {**base_deck, "polar": {**base_deck["polar"], "beta_deg": 0.0}}
    )
    for key in ("alpha", "CL", "CD", "Cm", "CY", "Cl", "Cn", "Cx", "Cz"):
        assert plain[key] == explicit[key], key
