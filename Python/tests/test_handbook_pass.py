import os

import numpy as np

from aid.aircraft import load_mat
from aid.handbook_pass import apply_handbook
from aid.paths import matlab_code
from aid.trim import trim_incidence


def test_cessna_handbook_pass_has_dynamic_and_lateral_keys():
    ac = load_mat(matlab_code() / "Models" / "Cessna 172.mat")
    out = apply_handbook(
        ac, angl=True, slipstream=False, slipstream_data=(0.5, 0.9),
        multhopp=True, trim_mode=0, trim_fix="both",
    )
    assert np.isfinite(out["CLa"])
    assert np.isfinite(out["CD0"])
    assert "CYb" in out["lateral"]
    assert out["dynamic"]["A"].shape == (4, 4)
    assert np.isfinite(out["dynamic"]["Xu"])


def test_finish_tornado_keeps_inviscid_coeffs_when_hooks_fail(monkeypatch):
    """MainWindow._finish_tornado saves CL/CD before viscous and neutral-point hooks."""
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication, QMessageBox

    from aid.tornado.static_margin import StaticMarginError
    from aid_gui.main_window import MainWindow

    QApplication.instance() or QApplication([])
    window = MainWindow()
    coeffs = {"CL": 0.41, "CD": 0.03}
    saved = {}

    def bad_viscous(*_args, **_kwargs):
        saved["before_viscous"] = window.last_results.get("tornado") is coeffs
        raise RuntimeError("strip failed")

    def bad_margin(*_args, **_kwargs):
        saved["before_margin"] = window.last_results.get("tornado") is coeffs
        raise StaticMarginError("Max iterations in fFindstaticmargin")

    monkeypatch.setattr("aid_gui.main_window.viscous_correction", bad_viscous)
    monkeypatch.setattr("aid_gui.main_window.find_static_margin", bad_margin)
    monkeypatch.setenv("QT_QPA_PLATFORM", "minimal")
    monkeypatch.setattr(
        "aid_gui.main_window.QMessageBox.question",
        lambda *_a, **_k: QMessageBox.StandardButton.Yes,
    )
    window.settings.viscous_strip = True
    window._finish_tornado(coeffs, {}, {}, {}, {}, 0)

    assert saved["before_viscous"] is True
    assert saved["before_margin"] is True
    published = window.last_results["tornado"]
    assert published["CL"] == 0.41
    assert published["CD"] == 0.03
    assert "viscous" not in published
    assert "N0" not in published


def test_zero_slope_neutral_point_keeps_coeffs_and_refreshes(monkeypatch):
    """A ZeroDivisionError from find_static_margin leaves CL/CD and still refreshes."""
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication, QMessageBox

    from aid_gui.main_window import MainWindow

    QApplication.instance() or QApplication([])
    window = MainWindow()
    coeffs = {"CL": 0.41, "CD": 0.03}
    refreshed = {"n": 0}

    def zero_slope(*_args, **_kwargs):
        raise ZeroDivisionError("float division by zero")

    monkeypatch.setattr("aid_gui.main_window.find_static_margin", zero_slope)
    monkeypatch.setenv("QT_QPA_PLATFORM", "minimal")
    monkeypatch.setattr(
        "aid_gui.main_window.QMessageBox.question",
        lambda *_a, **_k: QMessageBox.StandardButton.Yes,
    )
    monkeypatch.setattr(window, "_refresh_plots", lambda *_a, **_k: refreshed.__setitem__("n", refreshed["n"] + 1))
    window._finish_tornado(coeffs, {}, {}, {}, {}, 0)

    published = window.last_results["tornado"]
    assert published is coeffs
    assert published["CL"] == 0.41
    assert published["CD"] == 0.03
    assert "N0" not in published
    assert refreshed["n"] == 1


def test_trim_mode_2_writes_ht_arm_before_trim(monkeypatch):
    ac = load_mat(matlab_code() / "Models" / "Cessna 172.mat")
    ht = ac.HT
    cbar = float(np.asarray(ht["cbar"], dtype=float).reshape(-1)[-1])
    xmac = float(np.asarray(ht.get("xmac", 0.0), dtype=float).reshape(-1)[-1])
    old_xcg = float(ac.AERO["XCG"])
    old_arm = float(ht["X"]) + float(ht["x_ac"]) * cbar + xmac - old_xcg
    ac.HT["l"] = -999.0
    ac.AERO["XCG"] = old_xcg + 0.5
    seen = {}

    def wrapped(aircraft, **kwargs):
        tail = aircraft.HT
        mac = float(np.asarray(tail["cbar"], dtype=float).reshape(-1)[-1])
        x_mac = float(np.asarray(tail.get("xmac", 0.0), dtype=float).reshape(-1)[-1])
        seen["l"] = float(aircraft.HT["l"])
        seen["expected"] = (
            float(tail["X"]) + float(tail["x_ac"]) * mac + x_mac - float(aircraft.AERO["XCG"])
        )
        return trim_incidence(aircraft, **kwargs)

    monkeypatch.setattr("aid.handbook_pass.trim_incidence", wrapped)
    apply_handbook(
        ac, angl=True, slipstream=False, slipstream_data=(0.5, 0.9),
        multhopp=True, trim_mode=2, trim_fix="both",
    )
    assert seen["l"] == seen["expected"]
    assert seen["l"] != -999.0
    assert abs(seen["l"] - (old_arm - 0.5)) < 1e-6
