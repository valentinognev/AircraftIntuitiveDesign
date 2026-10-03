"""flow5's stability derivatives: computed by the library, thrown away by the helper.

``PlaneTask::setComputeDerivatives(false)`` meant every ``StabDerivatives`` block
flow5 builds was discarded at the end of each operating point, so flow5 reached
the comparison tables with a lift slope and nothing else -- no sideslip
derivatives, no damping, no neutral point. The helper now asks for them.

Two things this file exists to pin:

* The values are emitted **raw**, in flow5's own frame. ``computeStability-
  Derivatives`` projects onto the *stability* axes (panelanalysis.cpp:845-846,
  axes defined at :663-665), which is already Forward-Right-Down, so every
  derivative here takes **no** sign-map entry -- including ``CZa``, which is
  already negative. Task 2.3 owns the sign map; its flow5 entry is exactly
  ``{"Cx": -1, "Cz": -1, "Cl": -1, "Cn": -1}`` for the per-point channels only.
* ``CLa`` and ``Cma`` keep their **OLS** values. ``StabDerivatives`` has its own
  ``Cma`` (measured -1.0966 at the reference point) and writing it under the same
  key would silently move a channel that
  ``test_flow5_force_channels.py`` already pins, so only the twelve scalars below
  are copied out of the library block.
"""

from pathlib import Path

import numpy as np
import pytest

from aid.aircraft import load_jsonc
from aid.avl_io import run_avl_full
from aid.flow5_io import run_flow5
from aid.paths import flow5_bin, models_dir

FLOW5_BIN = flow5_bin()
MODELS = Path(__file__).resolve().parents[1] / "models"
MESH = ("10", "10")

pytestmark = pytest.mark.skipif(
    not FLOW5_BIN.is_file(), reason="flow5 helper not built"
)

# flow5's OLS slope over the alpha sweep, NOT StabDerivatives::Cma. Taken from
# the live binary; the brief's transcription differs in the 13th digit.
OLS_CLA = 5.1769701450913255
OLS_CMA = -1.5769862731689508

DERIVS = (
    "CXa", "CZa", "CYb", "CYp", "CYr",
    "Clb", "Clp", "Clr", "Cnb", "Cnp", "Cnr",
    "XNP",
)

# Pinned from the live binary at the reference operating point (alpha = 0 of the
# -4..+12 sweep). These are raw flow5 values in flow5's own frame; a mutation
# that flipped a sign, changed the reference point, or silently zeroed a
# derivative would move them.
REF_CXA = 0.0594656070239
REF_CZA = -5.25622764739
REF_CLB = -0.0530086955584
REF_CLR = 0.0267395655294
REF_CLP = -0.538490254394
REF_CNB = 0.168533813917
REF_CNP = 0.0403024469417
REF_CNR = -0.206015838634
REF_CYB = -0.41070604616
REF_CYP = -0.207290592126
REF_CYR = 0.410263604584
REF_XNP = 1.02329073033


@pytest.fixture(scope="module")
def pair(tmp_path_factory):
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    tmp = tmp_path_factory.mktemp("flow5_derivs")
    return run_flow5(ac, MESH), run_avl_full(ac, MESH, tmp / "avl")


def avl_reference(avl):
    """AVL's middle scheduled alpha -- index 8 of the same -4..+12 sweep.

    Only the full-length sweeps are indexed: ``avl["ref"]`` and friends are not
    arrays of 17, so a plain ``isinstance(v, list)`` filter would index off the
    end of them.
    """
    n = len(avl["alpha"])
    mid = n // 2
    return {
        k: v[mid]
        for k, v in avl.items()
        if isinstance(v, list) and len(v) == n
    }


def test_flow5_emits_finite_derivatives(pair):
    flow5, _ = pair
    for key in DERIVS:
        assert key in flow5, key
        value = float(flow5[key])
        assert np.isfinite(value), f"{key} is not finite: {value}"


def test_flow5_derivatives_are_the_measured_values(pair):
    # Exact, not approximate: the helper must copy flow5's numbers verbatim.
    # The only judgement call is *which* operating point, and the pins settle
    # it -- they are the alpha = 0 block (spike err_b0.txt, lines 191-236), not
    # the first or the middle alpha of the sweep.
    flow5, _ = pair
    measured = {
        "CXa": REF_CXA, "CZa": REF_CZA,
        "CYb": REF_CYB, "CYp": REF_CYP, "CYr": REF_CYR,
        "Clb": REF_CLB, "Clp": REF_CLP, "Clr": REF_CLR,
        "Cnb": REF_CNB, "Cnp": REF_CNP, "Cnr": REF_CNR,
        "XNP": REF_XNP,
    }
    for key, value in measured.items():
        assert flow5[key] == pytest.approx(value, rel=1e-9), key


def test_flow5_beta_derivatives_hold_the_physical_signs(pair):
    flow5, avl = pair
    a = avl_reference(avl)
    assert flow5["Cnb"] > 0.0 and np.sign(flow5["Cnb"]) == np.sign(a["Cnb"])
    assert flow5["Clb"] < 0.0 and np.sign(flow5["Clb"]) == np.sign(a["Clb"])
    assert flow5["CYb"] < 0.0 and np.sign(flow5["CYb"]) == np.sign(a["CYb"])


def test_flow5_damping_derivatives_are_negative(pair):
    flow5, _ = pair
    assert flow5["Clp"] < 0.0, "roll damping must be negative"
    assert flow5["Cnr"] < 0.0, "yaw damping must be negative"
    # CZa is the ALPHA derivative, dCZ/dalpha -- not a q-derivative, and not a
    # damping term. It is negative in the raw frame and stays negative in
    # Forward-Right-Down, so it takes no sign-map entry: measured -5.2562, and
    # CZa = -CLa - CD exactly (CLa 5.2550, CD 0.0012 at alpha = 0), matching the
    # gold's Longitudinal_Dynamic_Stability.m:35 `CZa = -AC.CLa - AC.CD`.
    assert flow5["CZa"] < 0.0, "CZa = -CLa - CD is negative; CZa takes no sign-map entry"


def test_flow5_lateral_derivatives_are_the_same_order_as_avl(pair):
    flow5, avl = pair
    a = avl_reference(avl)
    for key in ("Cnb", "Clb", "CYb"):
        assert 0.1 < abs(flow5[key] / a[key]) < 10.0, key


def test_flow5_cma_agrees_with_the_ols_slope(pair):
    flow5, _ = pair
    assert flow5["Cma"] == pytest.approx(OLS_CMA, rel=0.25)


def test_flow5_ols_channels_are_unchanged(pair):
    # CLa and Cma are the OLS slopes and are NOT the library's StabDerivatives
    # block: flow5's own Cma is -1.0966 at the reference point, so copying the
    # block under these keys would move a pinned channel.
    flow5, _ = pair
    assert flow5["CLa"] == pytest.approx(OLS_CLA, rel=1e-9)
    assert flow5["Cma"] == pytest.approx(OLS_CMA, rel=1e-9)
