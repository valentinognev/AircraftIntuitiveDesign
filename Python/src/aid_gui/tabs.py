from PySide6.QtWidgets import QFormLayout, QLabel, QLineEdit, QTabWidget, QVBoxLayout, QWidget

from aid.aircraft import Aircraft

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


def build_tabs(window) -> None:
    window._field_edits: dict[str, QLineEdit] = {}
    tab_widget = QTabWidget()

    for prefix, title in [("WG", "Wing"), ("HT", "HT"), ("VT", "VT")]:
        tab_widget.addTab(_planform_tab(window, prefix), title)

    tab_widget.addTab(_control_tab(window), "Control")
    tab_widget.addTab(_body_tab(window), "Body")
    tab_widget.addTab(_aero_tab(window), "Aero")
    tab_widget.addTab(_plus_tab(), "+")

    window.setCentralWidget(tab_widget)


def _register_field(window, key: str, layout: QFormLayout, label: str) -> QLineEdit:
    edit = QLineEdit()
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
    return getattr(ac, section)[field]


def populate_from_aircraft(window, ac: Aircraft) -> None:
    for key, edit in window._field_edits.items():
        edit.setText(_format_value(_value_from_aircraft(ac, key)))


def clear_fields(window) -> None:
    for edit in window._field_edits.values():
        edit.clear()
