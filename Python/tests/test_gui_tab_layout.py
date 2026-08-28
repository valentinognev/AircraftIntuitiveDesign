"""Python tab field order/position matches MATLAB Initialize_GUI.m."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("PYVISTA_OFF_SCREEN", "true")

from PySide6.QtWidgets import QApplication, QCheckBox, QLabel, QPushButton, QScrollArea

from aid.aircraft import load_jsonc
from aid.paths import models_dir
from aid_gui.main_window import MainWindow

PLANFORM_LABELS = [
    "Root Chord",
    "Break Chord",
    "Tip Chord",
    "Semi-Span",
    "Break Span",
    "Inboard Sweep",
    "Outboard Sweep",
    "Sweep Reference",
    "Inboard Dihedral",
    "Outboard Dihedral",
    "Thickness",
    "Washout",
    "Incidence",
    "Position, X",
    "Position, Y",
    "Position, Z",
]

AERO_LABELS = [
    "Angle(s) of Attack",
    "Altitude",
    "Mach Number",
    "Weight",
    "CG Location, X",
    "CG Location, Z",
    "Inertia, X",
    "Inertia, Y",
    "Wing Root Airfoil",
    "Wing Tip Airfoil",
    "Tail Airfoil",
]


def _window(name="Cessna 172.jsonc"):
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    w.load_aircraft(load_jsonc(models_dir() / name))
    return w


def _inner(w, title: str):
    tw = w._tab_widget
    for i in range(tw.count()):
        if tw.tabText(i) == title:
            widget = tw.widget(i)
            if isinstance(widget, QScrollArea):
                return widget.widget()
            return widget
    raise AssertionError(f"no tab {title}")


def _label_texts(w, title: str) -> list[str]:
    return [lab.text() for lab in _inner(w, title).findChildren(QLabel) if lab.text()]


def _ordered(labels: list[str], expected: list[str]) -> list[str]:
    return [text for text in labels if text in expected]


def test_wing_ht_vt_field_order_and_units():
    w = _window()
    for title in ("Wing", "HT", "VT"):
        texts = _label_texts(w, title)
        assert _ordered(texts, PLANFORM_LABELS) == PLANFORM_LABELS, title
        assert "airfoil id" not in texts
        assert "airfoil xy" not in texts
        assert texts.count("ft") >= 8
        assert texts.count("deg") >= 5
        assert "LE-TE" in texts
        assert "chord" in texts
        inner = _inner(w, title)
        assert inner.findChildren(QCheckBox), title
    assert "WG.NACA" not in w._field_edits
    assert "WG.DATA" not in w._field_edits
    assert "WG.NACA[0]" in w._field_edits


def test_control_tab_inboard_outboard_grid():
    w = _window()
    texts = _label_texts(w, "Control")
    assert texts.count("Inboard") == 4
    assert texts.count("Outboard") == 4
    assert "Flaps:" in texts
    assert "Ailerons:" in texts
    assert "Elevator:" in texts
    assert "Rudder:" in texts
    assert texts.count("Span") == 4
    assert texts.count("Chord") == 4
    assert texts.count("Deflection") == 4
    assert "F.SPANFI" in w._field_edits
    assert "F.SPANFO" in w._field_edits
    assert "F.CHRDFI" in w._field_edits
    assert "A.DELTAL" in w._field_edits
    assert "A.DELTAR" in w._field_edits
    assert "F.FTYPE" not in w._field_edits
    assert "A.STYPE" not in w._field_edits
    assert "A.Kb" not in w._field_edits


def test_body_tab_station_table():
    w = _window()
    texts = _label_texts(w, "Body")
    assert "Station" in texts
    buttons = {b.text(): b for b in _inner(w, "Body").findChildren(QPushButton)}
    assert "Adjust" in buttons
    assert "Shape" in buttons
    assert "Circular Cross-Section" in buttons
    assert "BD.N[0]" in w._field_edits
    assert "BD.X[0]" in w._field_edits
    assert "BD.P[0]" in w._field_edits
    assert "BD.ITYPE" not in w._field_edits
    assert "BD.ZU" not in w._field_edits
    assert abs(float(w._field_edits["BD.N[0]"].text()) - 1) < 1e-9
    assert abs(float(w._field_edits["BD.X[0]"].text()) - 0.0) < 1e-9


def test_aero_tab_order_units_and_cg_adjust():
    w = _window()
    texts = _label_texts(w, "Aero")
    assert _ordered(texts, AERO_LABELS) == AERO_LABELS
    assert "deg" in texts
    assert "lb" in texts
    assert "NACA" in texts
    assert "CG Adjust:" in texts
    assert "%MAC" in w._mac_checkbox.text() or w._mac_checkbox.text() == "%MAC"


def test_plus_tab_button_order():
    w = _window("Navion.jsonc")
    inner = _inner(w, "+")
    texts = _label_texts(w, "+")
    assert "Choose a Component to Add:" in texts
    buttons = [b.text() for b in inner.findChildren(QPushButton)]
    assert buttons[:5] == ["New Body", "Propeller", "New Wing", "New HT", "New VT"]
