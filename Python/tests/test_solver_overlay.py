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
        "avl": {"alpha": [-4.0, 0.0, 4.0], "CLtot": [0.10, 0.30, 0.51], "CLa": 5.2},
    }
    series = overlay_vs_alpha(
        results,
        st,
        datcom="cl",
        tornado=("CL", "CL_a"),
        avl="CLtot",
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
    series = overlay_vs_alpha(results, st, datcom="cd", tornado=("CD", "CD_a"), avl="CDtot")
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
        results, st, datcom="cn", tornado=("CZ", "CZ_a"), avl="CZtot"
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


def test_overlay_includes_flow5_cl_table():
    st = _st()
    results = {
        "flow5": {"alpha": np.array([-4.0, 0.0, 4.0]), "CL": np.array([-0.1, 0.2, 0.5])},
    }
    series = overlay_vs_alpha(
        results,
        st,
        datcom="cl",
        tornado=("CL", "CL_a"),
        avl="CLtot",
        flow5="CL",
    )
    labels = [s["label"] for s in series]
    assert "flow5" in labels
    f = next(s for s in series if s["label"] == "flow5")
    assert np.allclose(f["y"], [-0.1, 0.2, 0.5])
    assert f["style"] == "y.-"
    assert f["kind"] == "line"
    assert np.allclose(f["x"], [-4.0, 0.0, 4.0])


def test_overlay_omits_flow5_when_key_missing():
    st = _st()
    results = {
        "flow5": {"alpha": np.array([0.0, 4.0]), "CD": np.array([0.03, 0.04])},
    }
    series = overlay_vs_alpha(results, st, flow5="CL")
    assert [s["label"] for s in series] == []


def test_derivative_overlay_includes_flow5_hline():
    st = _st()
    results = {
        "flow5": {"CLa": 5.0, "Cma": -0.8},
    }
    series = overlay_derivative(results, st, flow5="CLa")
    labels = [s["label"] for s in series]
    assert labels == ["flow5"]
    assert series[0]["kind"] == "hline"
    assert series[0]["style"] == "y-"
    assert abs(series[0]["y"] - 5.0 * np.pi / 180) < 1e-12

    series_cm = overlay_derivative(results, st, flow5="Cma")
    assert len(series_cm) == 1
    assert abs(series_cm[0]["y"] - (-0.8) * np.pi / 180) < 1e-12


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
    assert labels == ["DATCOM", "Tornado"]
    assert series[1]["kind"] == "hline"
    assert abs(series[1]["y"] - 5.0 * np.pi / 180) < 1e-12
    assert all(s["label"] != "AVL" for s in series)


def test_overlay_avl_plots_solved_samples_not_slope():
    st = _st()
    results = {
        "avl": {
            "alpha": [-4.0, 0.0, 4.0],
            "CLtot": [0.1, 0.4, 0.7],
            "CLa": [5.2, 5.2, 5.2],
            "CDtot": [0.01, 0.02, 0.04],
            "CZtot": [-0.1, -0.4, -0.69],
            "CXtot": [0.02, 0.02, 0.05],
        }
    }
    cl = overlay_vs_alpha(results, st, avl="CLtot")
    assert len(cl) == 1
    assert np.allclose(cl[0]["x"], [-4.0, 0.0, 4.0])
    assert np.allclose(cl[0]["y"], [0.1, 0.4, 0.7])
    assert cl[0]["kind"] == "line"
    # slope from CLa at 0 would be 0.4 at every nearby angle only if extrapolated;
    # the sample at -4 is 0.1, not 0.4 + 5.2 * radians(-4)
    assert abs(cl[0]["y"][0] - 0.1) < 1e-12

    cd = overlay_vs_alpha(results, st, avl="CDtot")
    assert np.allclose(cd[0]["y"], [0.01, 0.02, 0.04])
    cn = overlay_vs_alpha(results, st, avl="CZtot")
    assert np.allclose(cn[0]["y"], [-0.1, -0.4, -0.69])
    ca = overlay_vs_alpha(results, st, avl="CXtot")
    assert np.allclose(ca[0]["y"], [0.02, 0.02, 0.05])


def test_overlay_avl_one_angle_is_a_marker():
    st = _st()
    results = {"avl": {"alpha": [4.0], "CDtot": [0.03]}}
    series = overlay_vs_alpha(results, st, avl="CDtot")
    assert series[0]["kind"] == "marker"
    assert np.allclose(series[0]["x"], [4.0])
    assert np.allclose(series[0]["y"], [0.03])


def test_overlay_avl_derivative_stays_on_solved_alphas():
    st = _st()
    results = {"avl": {"alpha": [-4.0, 0.0, 4.0], "CLa": [5.0, 5.2, 5.1]}}
    series = overlay_derivative(results, st, avl="CLa")
    assert series[0]["kind"] == "line"
    assert np.allclose(series[0]["x"], [-4.0, 0.0, 4.0])
    assert np.allclose(series[0]["y"], np.array([5.0, 5.2, 5.1]) * np.pi / 180.0)
