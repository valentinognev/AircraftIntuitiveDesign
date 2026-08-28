# Python/tests/test_solver_overlay.py
import numpy as np

from aid.solver_overlay import overlay_vs_alpha, overlay_derivative


def _st() -> dict:
    return {
        "alpha": 4.0,
        "CL0": 0.25,
        "CLa": 0.08,
        "CL": 0.57,
        "Cm0": 0.05,
        "Cma": -0.01,
        "Cm_CL": -0.12,
    }


def test_overlay_groups_datcom_tornado_avl_on_cl():
    st = _st()
    results = {
        "datcom": {
            "alpha": np.array([-4.0, 0.0, 4.0]),
            "cl": np.array([-0.2, 0.13, 0.52]),
        },
        "tornado": {
            "alpha": float(np.deg2rad(4.0)),
            "CL": 0.50,
            "CL_a": 5.0,
            "CL0": 0.50 - 5.0 * np.deg2rad(4.0),
        },
        "avl": {"alpha": 4.0, "CLtot": 0.51, "CLa": 5.2},
    }
    series = overlay_vs_alpha(
        results,
        st,
        datcom="cl",
        tornado=("CL", "CL_a"),
        avl=("CLtot", "CLa"),
    )
    labels = [s["label"] for s in series]
    assert labels == ["DATCOM", "Tornado", "AVL"]
    datcom = series[0]
    assert np.allclose(datcom["x"], [-4.0, 0.0, 4.0])
    assert np.allclose(datcom["y"], [-0.2, 0.13, 0.52])
    torn = series[1]
    a4 = np.interp(4.0, torn["x"], torn["y"])
    assert abs(a4 - 0.50) < 1e-9
    avl = series[2]
    a4a = np.interp(4.0, avl["x"], avl["y"])
    assert abs(a4a - 0.51) < 1e-9


def test_overlay_omits_missing_solvers():
    st = _st()
    results = {"datcom": {"alpha": np.array([0.0]), "cd": np.array([0.03])}}
    series = overlay_vs_alpha(results, st, datcom="cd", tornado=("CD", "CD_a"), avl=("CDtot", None))
    assert [s["label"] for s in series] == ["DATCOM"]


def test_overlay_cn_uses_tornado_cz():
    st = _st()
    results = {
        "datcom": {"alpha": np.array([0.0, 4.0]), "cn": np.array([0.13, 0.52])},
        "tornado": {
            "alpha": float(np.deg2rad(4.0)),
            "CZ": -0.50,
            "CZ_a": -5.0,
        },
        "avl": {"alpha": 4.0, "CZtot": -0.51},
    }
    series = overlay_vs_alpha(
        results, st, datcom="cn", tornado=("CZ", "CZ_a"), avl=("CZtot", None)
    )
    assert [s["label"] for s in series] == ["DATCOM", "Tornado", "AVL"]


def test_overlay_masks_datcom_nd_as_nan():
    st = _st()
    results = {
        "datcom": {
            "alpha": np.array([0.0, 4.0]),
            "cyb": np.array([99999.0, -0.012]),
        }
    }
    series = overlay_vs_alpha(results, st, datcom="cyb")
    assert np.isnan(series[0]["y"][0])
    assert abs(series[0]["y"][1] + 0.012) < 1e-12


def test_derivative_overlay_datcom_curve_and_vlm_hline():
    st = _st()
    results = {
        "datcom": {
            "alpha": np.array([-4.0, 4.0]),
            "cla": np.array([0.085, 0.100]),
        },
        "tornado": {"CL_a": 5.0},
        "avl": {"CLa": 5.2},
    }
    series = overlay_derivative(results, st, datcom="cla", tornado="CL_a", avl="CLa")
    labels = [s["label"] for s in series]
    assert labels == ["DATCOM", "Tornado", "AVL"]
    assert series[1]["kind"] == "hline"
    assert abs(series[1]["y"] - 5.0 * np.pi / 180) < 1e-12
    assert abs(series[2]["y"] - 5.2 * np.pi / 180) < 1e-12
