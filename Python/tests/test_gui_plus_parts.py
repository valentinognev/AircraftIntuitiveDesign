import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("PYVISTA_OFF_SCREEN", "true")

from PySide6.QtWidgets import QApplication, QPushButton, QTabWidget

from aid.aircraft import load_jsonc
from aid.paths import models_dir
from aid_gui.main_window import MainWindow
from aid_gui.tabs import sync_fields_to_aircraft

PLUS_PARTS = ("New Body", "Propeller", "New Wing", "New HT", "New VT")


def _window(name="Navion.jsonc"):
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    w.load_aircraft(load_jsonc(models_dir() / name))
    return w


def _aircraft_tabs(w):
    tw = getattr(w, "_tab_widget", None)
    if tw is not None:
        return tw
    for tw in w.findChildren(QTabWidget):
        titles = [tw.tabText(i) for i in range(tw.count())]
        if "+" in titles:
            return tw
    raise AssertionError("no + tab")


def _tab_titles(w):
    tw = _aircraft_tabs(w)
    return [tw.tabText(i) for i in range(tw.count())]


def _plus_buttons(w):
    tw = _aircraft_tabs(w)
    plus = None
    for i in range(tw.count()):
        if tw.tabText(i) == "+":
            plus = tw.widget(i)
            break
    assert plus is not None
    found = {b.text(): b for b in plus.findChildren(QPushButton)}
    return found


def test_plus_tab_has_five_add_buttons():
    w = _window()
    found = _plus_buttons(w)
    for name in PLUS_PARTS:
        assert name in found, name


def test_click_add_wing_ht_vt_body_prop_mutates_np_nb():
    w = _window("Navion.jsonc")
    btns = _plus_buttons(w)
    btns["New Wing"].click()
    btns["New HT"].click()
    btns["New VT"].click()
    btns["New Body"].click()
    btns["Propeller"].click()
    titles = _tab_titles(w)
    assert "Wing 2" in titles
    assert "HT 2" in titles
    assert "VT 2" in titles
    assert "Prop" in titles
    assert "Body 2" in titles
    assert isinstance(w.aircraft.NP[0], dict)
    assert isinstance(w.aircraft.NP[1], dict)
    assert isinstance(w.aircraft.NP[2], dict)
    assert isinstance(w.aircraft.NP[3], dict)
    assert isinstance(w.aircraft.NB[0], dict)
    assert w.aircraft.NP[0]["CHRDR"] > 0
    assert w.aircraft.NP[1]["CHRDR"] > 0
    assert w.aircraft.NP[2]["CHRDR"] > 0
    assert w.aircraft.NP[3]["CHRDR"] > 0
    assert int(w.aircraft.NB[0]["NX"]) == 7


def test_second_body_click_fills_nb1():
    w = _window("Navion.jsonc")
    btns = _plus_buttons(w)
    btns["New Body"].click()
    btns["New Body"].click()
    assert isinstance(w.aircraft.NB[0], dict)
    assert isinstance(w.aircraft.NB[1], dict)
    assert "Body 3" in _tab_titles(w)
    assert btns["New Body"].isHidden()


def test_cessna_load_creates_extra_tabs_from_np():
    w = _window("Cessna 172.jsonc")
    titles = _tab_titles(w)
    assert titles[:7] == ["Wing", "HT", "VT", "Control", "Body", "Aero", "+"]
    assert "Wing 2" in titles
    assert "Prop" in titles
    assert "HT 2" not in titles
    assert "Body 2" not in titles
    assert abs(float(w._field_edits["NP[0].CHRDR"].text()) - 0.3) < 1e-9
    assert abs(float(w._field_edits["NP[3].CHRDR"].text()) - 0.3125) < 1e-9
    btns = _plus_buttons(w)
    assert btns["New Wing"].isHidden()
    assert btns["Propeller"].isHidden()
    assert not btns["New HT"].isHidden()
    assert not btns["New Body"].isHidden()
    assert abs(w.field_value("AERO.MACH") - 0.03) < 1e-9
    assert abs(w.field_value("WG.SSPN") - 6.0) < 1e-9
    assert "AERO.ZCG" in w._field_edits
    assert "AERO.XI" in w._field_edits
    assert w._mac_checkbox is not None


def test_extra_planform_field_edit_updates_aircraft():
    w = _window("Cessna 172.jsonc")
    edit = w._field_edits["NP[0].CHRDR"]
    edit.setText("0.55")
    sync_fields_to_aircraft(w)
    assert w.aircraft.NP[0]["CHRDR"] == 0.55
    edit.editingFinished.emit()
    assert w.aircraft.NP[0]["CHRDR"] == 0.55
    w._field_edits["WG.CHRDR"].setText("2.5")
    sync_fields_to_aircraft(w)
    assert w.aircraft.WG["CHRDR"] == 2.5
    w._field_edits["AERO.ZCG"].setText("1.25")
    sync_fields_to_aircraft(w)
    assert w.aircraft.AERO["ZCG"] == 1.25


def test_enterprise_load_creates_body2_tab():
    w = _window("Enterprise.jsonc")
    assert "Body 2" in _tab_titles(w)
    assert isinstance(w.aircraft.NB[0], dict)
    assert "NB[0].X0" in w._field_edits
    assert abs(float(w._field_edits["NB[0].X0"].text()) - 24) < 1e-9
