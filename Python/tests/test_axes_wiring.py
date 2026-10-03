"""The solver boundary returns Forward-Right-Down; the parsers behind it stay raw.

Each test here pairs the wrapped entry point with the bare parser it wraps, so a
sign can only come from ``aid.axes`` and never from an accidental edit to
``parse_for006``/``parse_st``/``parse_sb``/``parse_run_case_header``.
"""

import json
from pathlib import Path

import numpy as np
import pytest

from aid.aircraft import load_jsonc
from aid.axes import from_frd
from aid.avl_io import run_avl_full
from aid.datcom_parse import parse_for006
from aid.datcom_run import run_datcom
from aid.paths import results_dir

GOLD = results_dir() / "matlab" / "Cessna 172"


def _cessna():
    return load_jsonc(Path(__file__).resolve().parents[1] / "models" / "Cessna 172.jsonc")


def _datcom_output(workdir: Path) -> Path:
    """Whichever file ``run_datcom`` read -- ``for006.dat``, else ``datcom.out``."""
    for name in ("for006.dat", "datcom.out"):
        candidate = workdir / name
        if candidate.is_file():
            return candidate
    raise AssertionError(f"DATCOM produced no output in {workdir}")


def test_run_datcom_flips_ca_and_cn(tmp_path):
    ac = _cessna()
    gold = json.loads((GOLD / "datcom.json").read_text())
    ac.AERO["ALSCHD"] = list(gold["alpha"])
    got = run_datcom(ac, tmp_path / "w")
    assert np.allclose(got["ca"], -np.asarray(gold["ca"]), atol=1e-6)
    assert np.allclose(got["cn"], -np.asarray(gold["cn"]), atol=1e-6)
    assert np.allclose(got["cl"], gold["cl"], atol=1e-6)
    assert np.allclose(got["cd"], gold["cd"], atol=1e-6)
    # The MATLAB gold carries no xcp, but the rule that decides it is checkable
    # here: DATCOM prints XCP = CM/CN in its own frame, and only `cn` is mirrored,
    # so the F-R-D dict must satisfy xcp == -cm/cn. Flipping xcp as well would
    # break this, and so would not flipping cn. The tolerance is DATCOM's own
    # print precision -- XCP carries three decimals where CM/CN carry four.
    assert np.allclose(
        np.asarray(got["xcp"], dtype=float),
        -np.asarray(got["cm"], dtype=float) / np.asarray(got["cn"], dtype=float),
        atol=5e-4,
    )


def test_run_datcom_is_the_inverse_of_the_bare_parser(tmp_path):
    ac = _cessna()
    got = run_datcom(ac, tmp_path / "w")
    raw = parse_for006(_datcom_output(tmp_path / "w").read_text())
    for key in ("alpha", "cd", "cl", "cm", "cn", "ca", "xcp", "cla", "cma", "cyb", "cnb", "clb"):
        assert np.allclose(from_frd("datcom", got)[key], raw[key], atol=1e-9), key


def test_tornado_coeff_create_flips_cz_and_cn():
    from aid.tornado.boundary import set_boundary
    from aid.tornado.coeff import coeff_create
    from aid.tornado.lattice import lattice_setup
    from aid.tornado.solver import solve
    from aid.tornado_io import tornado_io

    ac = _cessna()
    geo, state = tornado_io(ac, ("10", "5"))
    lattice, ref = lattice_setup(geo, state, 0)
    lattice = set_boundary(lattice, geo, state)
    raw = solve(state, geo, lattice)
    got = coeff_create(raw, lattice, state, ref, geo)
    assert got["CZ"] < 0.0, "lift must be negative z in Forward-Right-Down"
    assert got["CL"] > 0.0 and got["CD"] > 0.0, "wind-axis signs are untouched"
    q_sref = 0.5 * state["rho"] * state["AS"] ** 2 * ref["S_ref"]
    # solve()'s FORCE is the summed force at every perturbation, so it is
    # (n_deriv, 3); coeff_create re-exposes it as force[0, :], the 1-D 3-vector at
    # the baseline case. Both are left raw, so the F-R-D CZ is their negative.
    assert np.asarray(raw["FORCE"]).shape[0] > 2
    assert got["CZ"] == pytest.approx(-raw["FORCE"][0, 2] / q_sref)
    assert got["FORCE"][2] == pytest.approx(raw["FORCE"][0, 2])
    # CZ is not simply -CL: the body-axis force is the wind-axis one rotated by
    # alpha, and raw Tornado's z is up-positive while x is already the negation
    # of Forward-Right-Down's. F-R-D body axes are X = -D cos a + L sin a,
    # Z = -(D sin a + L cos a), which is what pins the x axis as forward -- at
    # Cessna's default 4 deg the drag contribution is small enough that the
    # lifted L sin a term wins and X legitimately comes out positive.
    alpha = float(state["alpha"])
    assert got["CZ"] == pytest.approx(
        -(got["CD"] * np.sin(alpha) + got["CL"] * np.cos(alpha))
    )
    assert got["CX"] == pytest.approx(
        -got["CD"] * np.cos(alpha) + got["CL"] * np.sin(alpha)
    )


def test_tornado_coeff_create_leaves_the_raw_vectors_alone():
    """``F``/``M``/``FORCE``/``MOMENTS`` are solver internals, not coefficients."""
    from aid.tornado.boundary import set_boundary
    from aid.tornado.coeff import coeff_create
    from aid.tornado.lattice import lattice_setup
    from aid.tornado.solver import solve
    from aid.tornado_io import tornado_io

    ac = _cessna()
    geo, state = tornado_io(ac, ("10", "5"))
    lattice, ref = lattice_setup(geo, state, 0)
    lattice = set_boundary(lattice, geo, state)
    raw = solve(state, geo, lattice)
    got = coeff_create(raw, lattice, state, ref, geo)
    for key in ("F", "M"):
        assert np.array_equal(got[key], raw[key][:, 0, :]), key
    for key in ("FORCE", "MOMENTS"):
        assert np.array_equal(got[key], raw[key][0, :]), key


def test_avl_stack_cases_is_identity(tmp_path):
    ac = _cessna()
    got = run_avl_full(ac, ("10", "10"), tmp_path)
    for key in ("CXtot", "CZtot", "CYtot", "Cltot", "Cmtot", "Cntot"):
        assert got[key] == from_frd("avl", got)[key]
    # AVL is natively X fwd, Z down, so the empty map has to be the truth. At
    # alpha = 0 the body- and wind-axis frames coincide, so the body-axis force
    # coefficients are exactly the negated wind-axis ones; away from it they
    # differ by the rotation, and CXtot legitimately turns positive as lift tilts
    # into a thrust component, so only CZtot keeps a fixed sign against CLtot.
    zero = [i for i, a in enumerate(got["alpha"]) if a == 0.0]
    assert zero, "the sweep must contain alpha = 0"
    i = zero[0]
    assert got["CXtot"][i] == pytest.approx(-got["CDtot"][i], abs=1e-9)
    assert got["CZtot"][i] == pytest.approx(-got["CLtot"][i], abs=1e-9)
    cl = np.asarray(got["CLtot"])
    cz = np.asarray(got["CZtot"])
    assert np.all(np.sign(cz[cl > 0.0]) < 0.0)
    assert np.all(np.sign(cz[cl < 0.0]) > 0.0)
