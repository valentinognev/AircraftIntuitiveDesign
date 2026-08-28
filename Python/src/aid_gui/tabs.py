import ast

from PySide6.QtCore import Qt
from PySide6.QtGui import QWheelEvent
from PySide6.QtWidgets import (
    QFormLayout,
    QFrame,
    QLabel,
    QLineEdit,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from aid.aircraft import Aircraft

_ANGLE_FIELDS = frozenset(
    {
        "SAVSI",
        "SAVSO",
        "DHDADI",
        "DHDADO",
        "TWISTA",
        "i",
        "PHETE",
        "PHETEP",
        "DELTA",
        "DELTAL",
        "DELTAR",
    }
)
_LENGTH_FIELDS = frozenset(
    {
        "CHRDR",
        "CHRDBP",
        "CHRDTP",
        "SSPN",
        "SSPNOP",
        "X",
        "Y",
        "Z",
        "SPANFI",
        "SPANFO",
        "CHRDFI",
        "CHRDFO",
        "CB",
    }
)
_POSITIVE_MIN_LENGTH_FIELDS = frozenset({"CHRDR", "CHRDBP", "CHRDTP", "SSPN"})
_POSITION_FIELDS = frozenset({"X", "Y", "Z"})
_CONTROL_LENGTH_FIELDS = frozenset({"SPANFI", "SPANFO", "CHRDFI", "CHRDFO", "CB"})

PLANFORM_RP = [
    ("CHRDR", "Root Chord"),
    ("CHRDBP", "Break Chord"),
    ("CHRDTP", "Tip Chord"),
    ("SSPN", "Semi-Span"),
    ("SSPNOP", "Break Span"),
    ("SAVSI", "Inboard Sweep"),
    ("SAVSO", "Outboard Sweep"),
    ("CHSTAT", "Sweep Reference"),
    ("DHDADI", "Inboard Dihedral"),
    ("DHDADO", "Outboard Dihedral"),
    ("TC", "Thickness"),
    ("TWISTA", "Washout"),
    ("i", "Incidence"),
    ("X", "Position, X"),
    ("Y", "Position, Y"),
    ("Z", "Position, Z"),
    ("NACA", "airfoil id"),
    ("DATA", "airfoil xy"),
]

AERO_FIELDS = [
    ("ALSCHD", "Angle(s) of Attack"),
    ("ALT", "Altitude"),
    ("MACH", "Mach Number"),
    ("WT", "Weight"),
    ("XCG", "CG Location, X"),
]

CONTROL_SECTIONS = [
    (
        "F",
        "Flap",
        [
            ("FTYPE", "Flap Type"),
            ("PHETE", "Trailing-Edge Angle"),
            ("PHETEP", "Trailing-Edge Angle (prime)"),
            ("TC", "Thickness"),
            ("CB", "Balance Chord"),
            ("SPANFI", "Inboard Span"),
            ("SPANFO", "Outboard Span"),
            ("CHRDFI", "Inboard Chord"),
            ("CHRDFO", "Outboard Chord"),
            ("DELTA", "Deflection"),
        ],
    ),
    (
        "A",
        "Aileron",
        [
            ("STYPE", "Aileron Type"),
            ("SPANFI", "Inboard Span"),
            ("SPANFO", "Outboard Span"),
            ("CHRDFI", "Inboard Chord"),
            ("CHRDFO", "Outboard Chord"),
            ("DELTAL", "Left Deflection"),
            ("DELTAR", "Right Deflection"),
            ("Kb", "Effectiveness"),
        ],
    ),
    (
        "E",
        "Elevator",
        [
            ("FTYPE", "Flap Type"),
            ("PHETE", "Trailing-Edge Angle"),
            ("PHETEP", "Trailing-Edge Angle (prime)"),
            ("TC", "Thickness"),
            ("CB", "Balance Chord"),
            ("SPANFI", "Inboard Span"),
            ("SPANFO", "Outboard Span"),
            ("CHRDFI", "Inboard Chord"),
            ("CHRDFO", "Outboard Chord"),
            ("DELTA", "Deflection"),
        ],
    ),
    (
        "R",
        "Rudder",
        [
            ("SPANFI", "Inboard Span"),
            ("SPANFO", "Outboard Span"),
            ("CHRDFI", "Inboard Chord"),
            ("CHRDFO", "Outboard Chord"),
            ("DELTA", "Deflection"),
        ],
    ),
]

BODY_FIELDS = [
    ("NX", "Number of Stations"),
    ("X", "Station X"),
    ("ZU", "Upper Body"),
    ("ZL", "Lower Body"),
    ("R", "Body Half-Width"),
    ("S", "Cross-Section Area"),
    ("N", "Station Index"),
    ("P", "Shape Parameter"),
    ("ITYPE", "Body Type"),
]


def _field_kind(key: str) -> str:
    field = key.split(".", 1)[1]
    if field == "CHSTAT":
        return "chstat"
    if field == "TC" and not key.startswith("AERO."):
        return "tc"
    if field in _ANGLE_FIELDS:
        return "angle"
    if field in _LENGTH_FIELDS:
        return "length"
    return "other"


def _minimum_limit(window, min_setting: float) -> float:
    if min_setting == 0:
        return float(window.settings.scroll_delta)
    return float(min_setting)


def _parse_scalar(text: str) -> float | None:
    try:
        value = ast.literal_eval(text)
    except (ValueError, SyntaxError):
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def clamp_value(window, key: str, value: float) -> float:
    if not window.settings.error_check:
        return value
    max_len, max_angle, min_setting = window.settings.error_limits
    field = key.split(".", 1)[1]
    kind = _field_kind(key)
    if field in _POSITIVE_MIN_LENGTH_FIELDS:
        minimum = _minimum_limit(window, min_setting)
        return max(minimum, min(value, max_len))
    if field == "SSPNOP" or field in _CONTROL_LENGTH_FIELDS:
        return max(0.0, min(value, max_len))
    if field in _POSITION_FIELDS:
        return max(-max_len, min(value, max_len))
    if kind == "angle":
        return max(-max_angle, min(value, max_angle))
    if kind == "chstat":
        return max(0.0, min(value, 1.0))
    if kind == "tc":
        return max(0.01, min(value, 0.99))
    return value


def _nudge_delta(window, key: str) -> float:
    kind = _field_kind(key)
    if kind == "length":
        return float(window.settings.scroll_delta)
    if kind == "angle":
        return 1.0
    if kind in ("chstat", "tc"):
        return 0.01
    return float(window.settings.scroll_delta)


def nudge_field(window, edit: QLineEdit, direction: int) -> None:
    key = getattr(edit, "_field_key", None)
    if key is None:
        return
    text = edit.text().strip()
    if not text:
        base = 0.0
    else:
        parsed = _parse_scalar(text)
        if parsed is None:
            return
        base = parsed
    new_val = base + _nudge_delta(window, key) * direction
    if window.settings.error_check:
        new_val = clamp_value(window, key, new_val)
    edit.setText(_format_value(new_val))


class AidLineEdit(QLineEdit):
    def __init__(self, window, key: str) -> None:
        super().__init__()
        self._window = window
        self._field_key = key
        self.editingFinished.connect(lambda: _clamp_edit(window, key, self))

    def wheelEvent(self, event: QWheelEvent) -> None:
        delta = event.angleDelta().y()
        if delta == 0:
            super().wheelEvent(event)
            return
        direction = 1 if delta > 0 else -1
        nudge_field(self._window, self, direction)
        event.accept()


def _clamp_edit(window, key: str, edit: QLineEdit) -> None:
    if not window.settings.error_check:
        return
    text = edit.text().strip()
    if not text:
        return
    value = _parse_scalar(text)
    if value is None:
        return
    clamped = clamp_value(window, key, value)
    if clamped != value:
        edit.setText(_format_value(clamped))


def build_tabs(window) -> None:
    window._field_edits: dict[str, QLineEdit] = {}
    tab_widget = QTabWidget()

    for prefix, title in [("WG", "Wing"), ("HT", "HT"), ("VT", "VT")]:
        tab_widget.addTab(_scrollable(_planform_tab(window, prefix)), title)

    tab_widget.addTab(_scrollable(_control_tab(window)), "Control")
    tab_widget.addTab(_scrollable(_body_tab(window)), "Body")
    tab_widget.addTab(_scrollable(_aero_tab(window)), "Aero")
    tab_widget.addTab(_scrollable(_plus_tab()), "+")

    window.setCentralWidget(tab_widget)


def _scrollable(inner: QWidget) -> QScrollArea:
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.Shape.NoFrame)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    scroll.setWidget(inner)
    return scroll


def _register_field(window, key: str, layout: QFormLayout, label: str) -> QLineEdit:
    edit = AidLineEdit(window, key)
    window._field_edits[key] = edit
    layout.addRow(label, edit)
    return edit


def _planform_tab(window, prefix: str) -> QWidget:
    tab = QWidget()
    layout = QFormLayout(tab)
    for field, label in PLANFORM_RP:
        edit = _register_field(window, f"{prefix}.{field}", layout, label)
        if prefix == "WG" and field == "CHRDR":
            window._wing_chrdr_edit = edit
    return tab


def _control_tab(window) -> QWidget:
    tab = QWidget()
    outer = QVBoxLayout(tab)
    for prefix, section_title, fields in CONTROL_SECTIONS:
        group = QWidget()
        layout = QFormLayout(group)
        layout.addRow(QLabel(f"<b>{section_title}</b>"))
        for field, label in fields:
            _register_field(window, f"{prefix}.{field}", layout, label)
        outer.addWidget(group)
    outer.addStretch()
    return tab


def _body_tab(window) -> QWidget:
    tab = QWidget()
    layout = QFormLayout(tab)
    for field, label in BODY_FIELDS:
        _register_field(window, f"BD.{field}", layout, label)
    return tab


def _aero_tab(window) -> QWidget:
    tab = QWidget()
    layout = QFormLayout(tab)
    for field, label in AERO_FIELDS:
        _register_field(window, f"AERO.{field}", layout, label)
    return tab


def _plus_tab() -> QWidget:
    tab = QWidget()
    layout = QVBoxLayout(tab)
    layout.addWidget(QLabel("Add part (not implemented)"))
    layout.addStretch()
    return tab


def _format_value(value) -> str:
    if isinstance(value, list):
        return str(value)
    return str(value)


def _value_from_aircraft(ac: Aircraft, key: str):
    section, field = key.split(".", 1)
    section_data = getattr(ac, section)
    if not isinstance(section_data, dict):
        return None
    return section_data.get(field)


def populate_from_aircraft(window, ac: Aircraft) -> None:
    for key, edit in window._field_edits.items():
        value = _value_from_aircraft(ac, key)
        if value is None:
            edit.clear()
        else:
            edit.setText(_format_value(value))


def clear_fields(window) -> None:
    for edit in window._field_edits.values():
        edit.clear()


def set_aero_cg_fields_enabled(window, enabled: bool) -> None:
    for key in ("AERO.WT", "AERO.XCG"):
        edit = window._field_edits.get(key)
        if edit is not None:
            edit.setEnabled(enabled)


def sync_fields_to_aircraft(window) -> None:
    ac: Aircraft = window.aircraft
    if ac is None:
        return
    for key, edit in window._field_edits.items():
        text = edit.text().strip()
        if not text:
            continue
        section, field = key.split(".", 1)
        section_data = getattr(ac, section)
        if not isinstance(section_data, dict):
            continue
        try:
            value = ast.literal_eval(text)
        except (ValueError, SyntaxError):
            value = text
        if field in ("NACA", "DATA") and isinstance(value, (int, float)):
            value = text
        section_data[field] = value
