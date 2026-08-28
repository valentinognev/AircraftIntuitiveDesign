import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("PYVISTA_OFF_SCREEN", "true")

from PySide6.QtWidgets import QApplication

from aid.aircraft import load_jsonc
from aid.paths import models_dir
from aid_gui.main_window import MainWindow
from aid_gui.tabs import sync_fields_to_aircraft


def _window():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    w.load_aircraft(load_jsonc(models_dir() / "Cessna 172.jsonc"))
    return w


def test_aero_tab_matlab_fields_exist():
    w = _window()
    for key in (
        "AERO.ALSCHD",
        "AERO.ALT",
        "AERO.MACH",
        "AERO.WT",
        "AERO.XCG",
        "AERO.ZCG",
        "AERO.XI",
        "AERO.YI",
        "WG.NACA[0]",
        "WG.NACA[1]",
        "HT.NACA",
    ):
        assert key in w._field_edits, key
    assert w._mac_checkbox is not None
    assert w._cg_slider is not None
    assert abs(float(w._field_edits["AERO.ZCG"].text()) - 0.0) < 1e-9
    assert abs(float(w._field_edits["AERO.XI"].text()) - 100.0) < 1e-9
    assert abs(float(w._field_edits["AERO.YI"].text()) - 100.0) < 1e-9
    assert w._field_edits["WG.NACA[0]"].text() == "2412"
    assert w._field_edits["WG.NACA[1]"].text() == "2412"
    assert w._field_edits["HT.NACA"].text() == "0012"


def test_aero_fields_round_trip_into_aircraft():
    w = _window()
    w._field_edits["AERO.ZCG"].setText("1.25")
    w._field_edits["AERO.XI"].setText("80")
    w._field_edits["AERO.YI"].setText("90")
    w._field_edits["WG.NACA[0]"].setText("4412")
    w._field_edits["WG.NACA[1]"].setText("4415")
    w._field_edits["HT.NACA"].setText("0015")
    sync_fields_to_aircraft(w)
    assert w.aircraft.AERO["ZCG"] == 1.25
    assert w.aircraft.AERO["XI"] == 80
    assert w.aircraft.AERO["YI"] == 90
    assert w.aircraft.WG["NACA"][0] == "4412"
    assert w.aircraft.WG["NACA"][1] == "4415"
    assert w.aircraft.HT["NACA"] == "0015"
    assert isinstance(w.aircraft.HT["NACA"], str)


def test_cg_slider_updates_xcg_and_edit():
    w = _window()
    w._cg_slider.set_xcg(4.0)
    assert abs(float(w._field_edits["AERO.XCG"].text()) - 4.0) < 1e-3
    assert abs(float(w.aircraft.AERO["XCG"]) - 4.0) < 1e-3


def test_mac_checkbox_switches_slider_range():
    w = _window()
    bd_end = float(w.aircraft.BD["X"][-1])
    wg = w.aircraft.WG
    mac_le = float(wg["X"]) + float(wg["xmac"])
    cbar = float(wg["cbar"]) if not isinstance(wg["cbar"], list) else float(wg["cbar"][-1])
    mac_te = mac_le + cbar

    mn, mx = w._cg_slider.x_range()
    assert abs(mn - 0.0) < 1e-9
    assert abs(mx - bd_end) < 1e-9

    w._mac_checkbox.setChecked(True)
    mn, mx = w._cg_slider.x_range()
    assert abs(mn - mac_le) < 1e-9
    assert abs(mx - mac_te) < 1e-9

    w._mac_checkbox.setChecked(False)
    mn, mx = w._cg_slider.x_range()
    assert abs(mn - 0.0) < 1e-9
    assert abs(mx - bd_end) < 1e-9
