import ast
import os
import re

import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtGui import QWheelEvent
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSlider,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from aid.aircraft import Aircraft, aero_beta
from aid.geometry import geometry
from aid_gui.profile_sketch_dialog import ProfileSketchDialog

_INDEXED_KEY = re.compile(r"^([A-Za-z]+)\.([A-Za-z]+)\[(\d+)\]$")
_LIST_KEY = re.compile(r"^([A-Za-z]+)\[(\d+)\]\.(.+)$")
_INDEXED_FIELD = re.compile(r"^([A-Za-z]+)\[(\d+)\]$")

# Fields entered in degrees: geometric ones (sweep, dihedral, incidence, washout)
# and the flight condition AERO.BETA. What the set buys them is the same in both
# cases -- the +/-max_angle error-check clamp and the wheel-nudge step.
_DEGREES_FIELDS = frozenset(
    {
        "BETA",
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
        "X0",
        "Y0",
        "Z0",
        "SPANFI",
        "SPANFO",
        "CHRDFI",
        "CHRDFO",
        "CB",
    }
)
_POSITIVE_MIN_LENGTH_FIELDS = frozenset({"CHRDR", "CHRDBP", "CHRDTP", "SSPN"})
_POSITION_FIELDS = frozenset({"X", "Y", "Z", "X0", "Y0", "Z0"})
_CONTROL_LENGTH_FIELDS = frozenset({"SPANFI", "SPANFO", "CHRDFI", "CHRDFO", "CB"})

PLANFORM_RP = [
    ("CHRDR", "Root Chord", "len"),
    ("CHRDBP", "Break Chord", "len"),
    ("CHRDTP", "Tip Chord", "len"),
    ("SSPN", "Semi-Span", "len"),
    ("SSPNOP", "Break Span", "len"),
    ("SAVSI", "Inboard Sweep", "deg"),
    ("SAVSO", "Outboard Sweep", "deg"),
    ("CHSTAT", "Sweep Reference", "le_te"),
    ("DHDADI", "Inboard Dihedral", "deg"),
    ("DHDADO", "Outboard Dihedral", "deg"),
    ("TC", "Thickness", "chord"),
    ("TWISTA", "Washout", "deg"),
    ("i", "Incidence", "deg"),
    ("X", "Position, X", "len"),
    ("Y", "Position, Y", "len"),
    ("Z", "Position, Z", "len"),
]
PLANFORM_BREAKS = (3, 5, 8, 10, 13)

AERO_FIELDS = [
    ("ALSCHD", "Angle(s) of Attack", "deg"),
    ("ALT", "Altitude", "alt"),
    ("MACH", "Mach Number", "mach"),
    ("BETA", "Beta", "deg"),
    ("WT", "Weight", "wt"),
    ("XCG", "CG Location, X", "len"),
    ("ZCG", "CG Location, Z", "len"),
    ("XI", "Inertia, X", "inertia"),
    ("YI", "Inertia, Y", "inertia"),
]
AERO_BREAKS = (1, 5, 7, 9, 12)

# Fields whose empty text is a value, not an absence. AERO.BETA is 0.0 for every
# model that never mentions it (save_jsonc omits default-valued AERO keys), so a
# blank field has to mean the same thing on the way back.
_BLANK_AS_ZERO = frozenset({"AERO.BETA"})

AERO_NACA_FIELDS = [
    ("WG.NACA[0]", "Wing Root Airfoil", 0),
    ("WG.NACA[1]", "Wing Tip Airfoil", 0),
    ("HT.NACA", "Tail Airfoil", 1),
]

CONTROL_BLOCKS = [
    (
        "F",
        "Flaps:",
        0,
        (
            ("SPANFI", "SPANFO", "Span", "len"),
            ("CHRDFI", "CHRDFO", "Chord", "len"),
            ("DELTA", None, "Deflection", "deg"),
        ),
    ),
    (
        "A",
        "Ailerons:",
        0,
        (
            ("SPANFI", "SPANFO", "Span", "len"),
            ("CHRDFI", "CHRDFO", "Chord", "len"),
            ("DELTAL", "DELTAR", "Deflection", "deg"),
        ),
    ),
    (
        "E",
        "Elevator:",
        1,
        (
            ("SPANFI", "SPANFO", "Span", "len"),
            ("CHRDFI", "CHRDFO", "Chord", "len"),
            ("DELTA", None, "Deflection", "deg"),
        ),
    ),
    (
        "R",
        "Rudder:",
        2,
        (
            ("SPANFI", "SPANFO", "Span", "len"),
            ("CHRDFI", "CHRDFO", "Chord", "len"),
            ("DELTA", None, "Deflection", "deg"),
        ),
    ),
]

BODY_STATION_ROWS = 11
EXTRA_BODY_STATION_ROWS = 7
_STATION_KEY = re.compile(r"^(?:BD|NB\[\d+\])\.(N|X|P)\[\d+\]$")

PLUS_PARTS = ("New Body", "Propeller", "New Wing", "New HT", "New VT")
_EXTRA_TAB_TITLES = frozenset({"Body 2", "Body 3", "Prop", "Wing 2", "HT 2", "VT 2"})
_PLANFORM_NUMERIC = [field for field, _label, _kind in PLANFORM_RP]


def _field_name(key: str) -> str:
    listed = _LIST_KEY.match(key)
    if listed:
        rest = listed.group(3)
        indexed = _INDEXED_FIELD.match(rest)
        return indexed.group(1) if indexed else rest
    matched = _INDEXED_KEY.match(key)
    if matched:
        return matched.group(2)
    if "." not in key:
        return key
    return key.split(".", 1)[1].split("[", 1)[0]


def _field_kind(key: str) -> str:
    field = _field_name(key)
    if field == "CHSTAT":
        return "chstat"
    if field == "TC" and not key.startswith("AERO."):
        return "tc"
    if field in _DEGREES_FIELDS:
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
    field = _field_name(key)
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
    _notify_field_edit(window)


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


class CgSlider(QSlider):
    """Float XCG slider; Qt provides integer ticks only."""

    SCALE = 1000

    def __init__(self, parent=None) -> None:
        super().__init__(Qt.Orientation.Horizontal, parent)
        self._xmin = 0.0
        self._xmax = 1.0
        self.setRange(0, self.SCALE)

    def x_range(self) -> tuple[float, float]:
        return self._xmin, self._xmax

    def set_x_range(self, xmin: float, xmax: float) -> None:
        self._xmin = float(xmin)
        self._xmax = float(xmax) if xmax > xmin else float(xmin) + 1e-9

    def xcg(self) -> float:
        span = self._xmax - self._xmin
        return self._xmin + span * self.value() / self.SCALE

    def set_xcg(self, x: float) -> None:
        span = self._xmax - self._xmin
        if span <= 0:
            self.setValue(0)
            return
        x = min(max(float(x), self._xmin), self._xmax)
        self.setValue(int(round((x - self._xmin) / span * self.SCALE)))


def _clamp_edit(window, key: str, edit: QLineEdit) -> None:
    if window.settings.error_check:
        text = edit.text().strip()
        if text:
            value = _parse_scalar(text)
            if value is not None:
                clamped = clamp_value(window, key, value)
                if clamped != value:
                    edit.setText(_format_value(clamped))
    canonical = window._field_edits.get(key)
    if canonical is not None and canonical is not edit:
        canonical.setText(edit.text())
    _notify_field_edit(window)


def _notify_field_edit(window) -> None:
    apply = getattr(window, "apply_field_edit", None)
    if callable(apply):
        apply()


def build_tabs(window) -> None:
    window._field_edits: dict[str, QLineEdit] = {}
    window._field_edits_extra: dict[str, list[QLineEdit]] = {}
    window._plus_buttons: dict[str, QPushButton] = {}
    window._extra_tab_fields: dict[str, list[str]] = {}
    window._extra_cmp: dict[int, QCheckBox] = {}
    window._unit_labels: list[tuple[QLabel, str]] = []
    window._cmp_boxes: dict[int, QCheckBox] = {}
    window._cmp_edits: dict[int, list[QLineEdit]] = {}
    window._body_station_rows: dict[str, list[tuple[QLineEdit, QLineEdit, QLineEdit]]] = {}
    window._beta_widgets: dict[str, QLineEdit] = {}
    tab_widget = QTabWidget()
    window._tab_widget = tab_widget

    cmp_for = {"WG": 0, "HT": 1, "VT": 2}
    for prefix, title in [("WG", "Wing"), ("HT", "HT"), ("VT", "VT")]:
        tab_widget.addTab(_scrollable(_planform_tab(window, prefix, cmp_for[prefix])), title)

    tab_widget.addTab(_scrollable(_control_tab(window)), "Control")
    tab_widget.addTab(_scrollable(_body_tab(window, "BD", BODY_STATION_ROWS, 3)), "Body")
    tab_widget.addTab(_scrollable(_aero_tab(window)), "Aero")
    tab_widget.addTab(_scrollable(_plus_tab(window)), "+")
    _refresh_unit_labels(window)

    window.setCentralWidget(tab_widget)


def _scrollable(inner: QWidget) -> QScrollArea:
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.Shape.NoFrame)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    scroll.setWidget(inner)
    return scroll


def _unit_text(kind: str, unit: str, kts: bool) -> str:
    if kind == "len":
        return unit
    if kind == "deg":
        return "deg"
    if kind == "le_te":
        return "LE-TE"
    if kind == "chord":
        return "chord"
    if kind == "alt":
        return "ft"
    if kind == "mach":
        return "(or kts)" if kts else "(or ft/s)"
    if kind == "wt":
        return "lb"
    if kind == "inertia":
        return "oz*in^2" if unit == "in" else "slug*ft^2"
    if kind == "naca":
        return "NACA"
    if kind == "pos_hdr":
        return f"Position, {unit}"
    return kind


def _refresh_unit_labels(window) -> None:
    ac = getattr(window, "aircraft", None)
    unit = ac.unit if ac is not None else "ft"
    kts = bool(getattr(getattr(window, "settings", None), "units_kts", True))
    alive: list[tuple[QLabel, str]] = []
    for lab, kind in getattr(window, "_unit_labels", []):
        try:
            lab.setText(_unit_text(kind, unit, kts))
        except RuntimeError:
            continue
        alive.append((lab, kind))
    window._unit_labels = alive


def _separator() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setStyleSheet("background-color: rgb(204, 204, 204);")
    line.setFixedHeight(2)
    return line


def _add_break(layout: QGridLayout, row: int, cols: int) -> int:
    layout.addWidget(_separator(), row, 0, 1, cols)
    return row + 1


def _right_label(text: str, checkbox: QCheckBox | None = None) -> QWidget:
    cell = QWidget()
    row = QHBoxLayout(cell)
    row.setContentsMargins(0, 0, 0, 0)
    row.setSpacing(2)
    if checkbox is not None:
        checkbox.setText("")
        row.addWidget(checkbox, 0)
    row.addStretch(1)
    lab = QLabel(text)
    lab.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    row.addWidget(lab, 0)
    return cell


def _make_edit(window, key: str) -> QLineEdit:
    edit = AidLineEdit(window, key)
    if key in window._field_edits:
        window._field_edits_extra.setdefault(key, []).append(window._field_edits[key])
    window._field_edits[key] = edit
    edit.setObjectName(key)
    return edit


def _add_unit(window, layout: QGridLayout, row: int, col: int, kind: str) -> QLabel:
    lab = QLabel()
    lab.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
    window._unit_labels.append((lab, kind))
    layout.addWidget(lab, row, col)
    return lab


def _track_cmp_edit(window, index: int, edit: QLineEdit) -> None:
    window._cmp_edits.setdefault(index, []).append(edit)


def _cmp_checkbox(window, index: int) -> QCheckBox:
    chk = QCheckBox()
    chk.setChecked(True)
    window._cmp_boxes[index] = chk
    if index >= 4:
        window._extra_cmp[index] = chk
    chk.toggled.connect(lambda checked, i=index: _on_cmp(window, i, checked))
    return chk


def _on_cmp(window, index: int, checked: bool) -> None:
    ac = getattr(window, "aircraft", None)
    if ac is not None:
        _ensure_plot_cmp(ac)
        ac.plot_cmp[index] = 1 if checked else 0
    for edit in window._cmp_edits.get(index, []):
        try:
            edit.setEnabled(checked)
        except RuntimeError:
            continue
    if ac is not None:
        _replot(window)


def _is_station_key(key: str) -> bool:
    return bool(_STATION_KEY.match(key))


def _planform_tab(window, prefix: str, cmp_index: int) -> QWidget:
    tab = QWidget()
    layout = QGridLayout(tab)
    layout.setContentsMargins(4, 4, 4, 4)
    layout.setHorizontalSpacing(4)
    layout.setVerticalSpacing(2)
    layout.setColumnStretch(0, 5)
    layout.setColumnStretch(1, 3)
    layout.setColumnStretch(2, 2)
    chk = _cmp_checkbox(window, cmp_index)
    row = 0
    for i, (field, label, kind) in enumerate(PLANFORM_RP, start=1):
        layout.addWidget(_right_label(label, chk if i == 1 else None), row, 0)
        edit = _make_edit(window, f"{prefix}.{field}")
        layout.addWidget(edit, row, 1)
        _track_cmp_edit(window, cmp_index, edit)
        _add_unit(window, layout, row, 2, kind)
        if prefix == "WG" and field == "CHRDR":
            window._wing_chrdr_edit = edit
        row += 1
        if i in PLANFORM_BREAKS:
            row = _add_break(layout, row, 3)
    layout.setRowStretch(row, 1)
    return tab


def _control_tab(window) -> QWidget:
    tab = QWidget()
    layout = QGridLayout(tab)
    layout.setContentsMargins(4, 4, 4, 4)
    layout.setHorizontalSpacing(4)
    layout.setVerticalSpacing(2)
    layout.setColumnStretch(0, 3)
    layout.setColumnStretch(1, 3)
    layout.setColumnStretch(2, 3)
    layout.setColumnStretch(3, 2)
    row = 0
    last = len(CONTROL_BLOCKS) - 1
    for bi, (prefix, title, cmp_index, specs) in enumerate(CONTROL_BLOCKS):
        layout.addWidget(QLabel(title), row, 0)
        in_h = QLabel("Inboard")
        in_h.setAlignment(Qt.AlignmentFlag.AlignCenter)
        out_h = QLabel("Outboard")
        out_h.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(in_h, row, 1)
        layout.addWidget(out_h, row, 2)
        row += 1
        for left, right, label, kind in specs:
            layout.addWidget(_right_label(label), row, 0)
            if right is None:
                edit = _make_edit(window, f"{prefix}.{left}")
                layout.addWidget(edit, row, 1, 1, 2)
                _track_cmp_edit(window, cmp_index, edit)
            else:
                e1 = _make_edit(window, f"{prefix}.{left}")
                e2 = _make_edit(window, f"{prefix}.{right}")
                layout.addWidget(e1, row, 1)
                layout.addWidget(e2, row, 2)
                _track_cmp_edit(window, cmp_index, e1)
                _track_cmp_edit(window, cmp_index, e2)
            _add_unit(window, layout, row, 3, kind)
            row += 1
        if bi != last:
            row = _add_break(layout, row, 4)
    layout.setRowStretch(row, 1)
    return tab


def _body_tab(
    window,
    prefix: str,
    n_rows: int,
    cmp_index: int,
    *,
    extra_xyz: bool = False,
    extra_title: str | None = None,
) -> QWidget:
    tab = QWidget()
    layout = QGridLayout(tab)
    layout.setContentsMargins(4, 4, 4, 4)
    layout.setHorizontalSpacing(4)
    layout.setVerticalSpacing(2)
    layout.setColumnStretch(0, 1)
    layout.setColumnStretch(1, 1)
    layout.setColumnStretch(2, 1)
    chk = _cmp_checkbox(window, cmp_index)
    layout.addWidget(chk, 0, 0, Qt.AlignmentFlag.AlignLeft)
    adjust = QPushButton("Adjust")
    adjust.setMinimumHeight(28)
    adjust.clicked.connect(lambda *_: _open_body_sketcher(window, prefix))
    layout.addWidget(adjust, 1, 0, 1, 2)
    sketch = QPushButton("Sketch")
    sketch.setMinimumHeight(28)
    sketch.clicked.connect(lambda *_: _open_profile_sketch(window, prefix))
    layout.addWidget(sketch, 1, 2)
    layout.addWidget(QLabel("Station"), 2, 0, Qt.AlignmentFlag.AlignCenter)
    pos_hdr = QLabel()
    pos_hdr.setAlignment(Qt.AlignmentFlag.AlignCenter)
    window._unit_labels.append((pos_hdr, "pos_hdr"))
    layout.addWidget(pos_hdr, 2, 1)
    shape = QPushButton("Shape")
    shape.clicked.connect(lambda *_: _cycle_body_shape(window, prefix, n_rows))
    layout.addWidget(shape, 2, 2)
    keys: list[str] = []
    rows: list[tuple[QLineEdit, QLineEdit, QLineEdit]] = []
    row = 3
    for i in range(n_rows):
        n_edit = _make_edit(window, f"{prefix}.N[{i}]")
        x_edit = _make_edit(window, f"{prefix}.X[{i}]")
        p_edit = _make_edit(window, f"{prefix}.P[{i}]")
        layout.addWidget(n_edit, row, 0)
        layout.addWidget(x_edit, row, 1)
        layout.addWidget(p_edit, row, 2)
        _track_cmp_edit(window, cmp_index, n_edit)
        _track_cmp_edit(window, cmp_index, x_edit)
        _track_cmp_edit(window, cmp_index, p_edit)
        rows.append((n_edit, x_edit, p_edit))
        keys.extend([f"{prefix}.N[{i}]", f"{prefix}.X[{i}]", f"{prefix}.P[{i}]"])
        row += 1
    window._body_station_rows[prefix] = rows
    circ = QPushButton("Circular Cross-Section")
    circ.clicked.connect(lambda *_: _circularize_body(window, prefix))
    layout.addWidget(circ, row, 0, 1, 3)
    row += 1
    if extra_xyz:
        for field, label in (("X0", "Position, X"), ("Y0", "Position, Y"), ("Z0", "Position, Z")):
            layout.addWidget(_right_label(label), row, 0)
            edit = _make_edit(window, f"{prefix}.{field}")
            layout.addWidget(edit, row, 1)
            _add_unit(window, layout, row, 2, "len")
            _track_cmp_edit(window, cmp_index, edit)
            keys.append(f"{prefix}.{field}")
            row += 1
    if extra_title:
        window._extra_tab_fields[extra_title] = keys
    layout.setRowStretch(row, 1)
    return tab


def _aero_tab(window) -> QWidget:
    tab = QWidget()
    layout = QGridLayout(tab)
    layout.setContentsMargins(4, 4, 4, 4)
    layout.setHorizontalSpacing(4)
    layout.setVerticalSpacing(2)
    layout.setColumnStretch(0, 5)
    layout.setColumnStretch(1, 3)
    layout.setColumnStretch(2, 2)
    row = 0
    i = 0
    for field, label, kind in AERO_FIELDS:
        i += 1
        layout.addWidget(_right_label(label), row, 0)
        edit = _make_edit(window, f"AERO.{field}")
        layout.addWidget(edit, row, 1)
        if field == "BETA":
            # The sideslip field has its own handle: it is the one AERO key the
            # GUI owns end to end, and the overlays need to know its value.
            window._beta_widgets[field] = edit
        _add_unit(window, layout, row, 2, kind)
        row += 1
        if i in AERO_BREAKS:
            row = _add_break(layout, row, 3)
    for key, label, cmp_index in AERO_NACA_FIELDS:
        i += 1
        layout.addWidget(_right_label(label), row, 0)
        edit = _make_edit(window, key)
        layout.addWidget(edit, row, 1)
        _track_cmp_edit(window, cmp_index, edit)
        _add_unit(window, layout, row, 2, "naca")
        row += 1
        if i in AERO_BREAKS:
            row = _add_break(layout, row, 3)
    cg_row = QWidget()
    cg_l = QHBoxLayout(cg_row)
    cg_l.setContentsMargins(0, 8, 0, 0)
    cg_l.addWidget(QLabel("CG Adjust:"))
    mac = QCheckBox("%MAC")
    cg_l.addWidget(mac)
    cg_l.addStretch(1)
    layout.addWidget(cg_row, row, 0, 1, 3)
    row += 1
    slider = CgSlider()
    layout.addWidget(slider, row, 0, 1, 3)
    window._mac_checkbox = mac
    window._cg_slider = slider
    mac.toggled.connect(lambda checked: _on_mac_checkbox(window, checked))
    slider.valueChanged.connect(lambda _: _on_cg_slider(window))
    return tab


def _plus_tab(window) -> QWidget:
    tab = QWidget()
    layout = QVBoxLayout(tab)
    layout.setContentsMargins(12, 8, 12, 8)
    layout.setSpacing(10)
    layout.addWidget(QLabel("Choose a Component to Add:"))
    window._plus_buttons = {}
    for i, name in enumerate(PLUS_PARTS, start=1):
        btn = QPushButton(name)
        btn.setMinimumHeight(32)
        btn.clicked.connect(lambda checked=False, c=i: add_part(window, c))
        window._plus_buttons[name] = btn
        layout.addWidget(btn)
    layout.addStretch()
    return tab


def _body_section(ac: Aircraft, prefix: str):
    if prefix == "BD":
        return ac.BD
    listed = _LIST_KEY.match(f"{prefix}.X")
    if listed:
        return _section_dict(ac, listed.group(1), int(listed.group(2)))
    return None


def _open_profile_sketch(window, prefix: str) -> None:
    ac = getattr(window, "aircraft", None)
    if ac is None:
        return
    section = _body_section(ac, prefix)
    if not isinstance(section, dict):
        return
    ProfileSketchDialog(section, window).exec()
    populate_from_aircraft(window, ac)
    view = getattr(window, "view3d", None)
    settings = getattr(window, "settings", None)
    if view is not None and settings is not None:
        view.plot_aircraft(
            ac,
            res=tuple(settings.plot_res),
            angle=settings.angle,
            keep_camera=True,
        )


def _open_body_sketcher(window, prefix: str) -> None:
    ac = getattr(window, "aircraft", None)
    opener = getattr(window, "open_profile_sketcher", None)
    if ac is None or not callable(opener):
        return
    section = _body_section(ac, prefix)
    if isinstance(section, dict):
        opener(section)


def _cycle_body_shape(window, prefix: str, n_rows: int) -> None:
    ac = getattr(window, "aircraft", None)
    rows = getattr(window, "_body_station_rows", {}).get(prefix)
    if ac is None or not rows:
        return
    section = _body_section(ac, prefix)
    if not isinstance(section, dict):
        return
    p = np.asarray(section.get("P", [1]), dtype=float).reshape(-1)
    nx = int(section.get("NX") or len(p) or 1)
    for _n, _x, p_e in rows:
        _set_edit_text(p_e, "")
    if np.all(p == 0):
        val = "1"
    elif np.all((p > 0) & (p < 5)):
        val = "5"
    else:
        val = "0"
    _set_edit_text(rows[0][2], val)
    last = min(nx, n_rows) - 1
    if last > 0:
        _set_edit_text(rows[last][2], val)
    _notify_field_edit(window)


def _circularize_body(window, prefix: str) -> None:
    ac = getattr(window, "aircraft", None)
    if ac is None:
        return
    section = _body_section(ac, prefix)
    if not isinstance(section, dict):
        return
    zu = np.asarray(section.get("ZU", [0.0]), dtype=float).reshape(-1)
    zl = np.asarray(section.get("ZL", [0.0]), dtype=float).reshape(-1)
    r = np.asarray(section.get("R", [0.0]), dtype=float).reshape(-1)
    el = 30.0
    view = getattr(window, "view3d", None)
    if view is not None:
        try:
            pos = np.asarray(view.camera_xyz(), dtype=float)
            foc = np.asarray(view.camera_focus(), dtype=float)
            d = pos - foc
            el = float(np.degrees(np.arctan2(d[2], np.hypot(d[0], d[1]))))
        except Exception:
            pass
    if el > 45:
        section["ZU"] = r.tolist()
        section["ZL"] = (-r).tolist()
    else:
        n = min(len(zu), len(zl))
        section["R"] = ((zu[:n] - zl[:n]) / 2.0).tolist()
    _notify_field_edit(window)


def _cmp_enabled_for_edits(window, edits) -> bool:
    sample = edits[0][0] if edits else None
    if sample is None:
        return True
    for i, box in getattr(window, "_cmp_boxes", {}).items():
        if sample in window._cmp_edits.get(i, []):
            try:
                return box.isChecked()
            except RuntimeError:
                return True
    return True


def _populate_body_stations(window, ac: Aircraft) -> None:
    for prefix, rows in getattr(window, "_body_station_rows", {}).items():
        section = _body_section(ac, prefix)
        if not isinstance(section, dict):
            continue
        parent_on = _cmp_enabled_for_edits(window, rows)
        x = [float(v) for v in np.asarray(section.get("X", []), dtype=float).reshape(-1)]
        p = [float(v) for v in np.asarray(section.get("P", [1] * max(len(x), 1)), dtype=float).reshape(-1)]
        nx = int(section.get("NX") or len(x) or 1)
        n_raw = section.get("N")
        if n_raw is None or (isinstance(n_raw, list) and len(n_raw) == 0):
            n_list = list(range(1, min(nx, len(rows)) + 1))
        else:
            n_list = [int(v) for v in np.asarray(n_raw, dtype=float).reshape(-1)]
        p_all_equal = len(p) > 1 and (max(p) - min(p) == 0)
        for i, (n_e, x_e, p_e) in enumerate(rows):
            active = i < min(nx, len(rows)) and i < len(n_list)
            enabled = active and parent_on
            n_e.setEnabled(enabled)
            x_e.setEnabled(enabled)
            p_e.setEnabled(enabled)
            if not active:
                _set_edit_text(n_e, "")
                _set_edit_text(x_e, "")
                _set_edit_text(p_e, "")
                continue
            n = n_list[i]
            _set_edit_text(n_e, str(n))
            xi = n - 1
            if 0 <= xi < len(x):
                _set_edit_text(x_e, _format_value(x[xi]))
            else:
                _set_edit_text(x_e, "")
            if p_all_equal and 0 < i < len(rows) - 1:
                _set_edit_text(p_e, "")
            elif 0 <= xi < len(p):
                _set_edit_text(p_e, _format_value(p[xi]))
            else:
                _set_edit_text(p_e, "")


def _sync_body_stations(window, ac: Aircraft) -> None:
    for prefix, rows in getattr(window, "_body_station_rows", {}).items():
        section = _body_section(ac, prefix)
        if not isinstance(section, dict):
            continue
        x = [float(v) for v in np.asarray(section.get("X", [0.0]), dtype=float).reshape(-1)]
        p = [float(v) for v in np.asarray(section.get("P", [1.0] * max(len(x), 1)), dtype=float).reshape(-1)]
        nx = max(int(section.get("NX") or len(x) or 1), len(x), 1)
        while len(x) < nx:
            x.append((x[-1] + 1e-6) if x else 0.0)
        while len(p) < nx:
            p.append(1.0)
        n_out: list[int] = []
        p_ctrl: list[float] = []
        x_ctrl: list[float] = []
        for n_e, x_e, p_e in rows:
            nt = n_e.text().strip()
            if not nt:
                continue
            try:
                n = int(float(nt))
            except ValueError:
                continue
            n = max(1, min(n, nx))
            n_out.append(n)
            xt = x_e.text().strip()
            parsed_x = _parse_scalar(xt) if xt else None
            if parsed_x is not None:
                x[n - 1] = parsed_x
            pt = p_e.text().strip()
            parsed_p = _parse_scalar(pt) if pt else None
            if parsed_p is not None:
                p_ctrl.append(parsed_p)
                x_ctrl.append(x[n - 1])
        section["N"] = n_out
        section["X"] = x
        if len(p_ctrl) >= 2:
            order = np.argsort(x_ctrl)
            xs = np.asarray(x_ctrl, dtype=float)[order]
            ps = np.asarray(p_ctrl, dtype=float)[order]
            uniq = np.concatenate(([True], np.diff(xs) > 1e-12))
            section["P"] = np.interp(x, xs[uniq], ps[uniq]).tolist()
        elif len(p_ctrl) == 1:
            section["P"] = [p_ctrl[0]] * nx
        else:
            section["P"] = p


def _sync_cmp_boxes(window, ac: Aircraft) -> None:
    flags = list(ac.plot_cmp) + [1] * 8
    for i, box in getattr(window, "_cmp_boxes", {}).items():
        try:
            box.blockSignals(True)
            box.setChecked(bool(flags[i]) if i < len(flags) else True)
            box.blockSignals(False)
            enabled = box.isChecked()
            for edit in window._cmp_edits.get(i, []):
                edit.setEnabled(enabled)
        except RuntimeError:
            continue


def _format_value(value) -> str:
    if isinstance(value, list):
        return str(value)
    return str(value)


def _parse_field_key(key: str) -> tuple[str, str, int | None, int | None]:
    listed = _LIST_KEY.match(key)
    if listed:
        section, slot, rest = listed.group(1), int(listed.group(2)), listed.group(3)
        indexed = _INDEXED_FIELD.match(rest)
        if indexed:
            return section, indexed.group(1), int(indexed.group(2)), slot
        return section, rest, None, slot
    matched = _INDEXED_KEY.match(key)
    if matched:
        return matched.group(1), matched.group(2), int(matched.group(3)), None
    section, field = key.split(".", 1)
    return section, field, None, None


def _section_dict(ac: Aircraft, section: str, slot: int | None):
    data = getattr(ac, section, None)
    if slot is not None:
        if not isinstance(data, list) or slot >= len(data):
            return None
        item = data[slot]
        return item if isinstance(item, dict) else None
    return data if isinstance(data, dict) else None


def _value_from_aircraft(ac: Aircraft, key: str):
    section, field, index, slot = _parse_field_key(key)
    section_data = _section_dict(ac, section, slot)
    if not isinstance(section_data, dict):
        return None
    value = section_data.get(field)
    if index is None:
        return value
    if isinstance(value, list):
        return value[index] if index < len(value) else None
    if index == 0:
        return value
    return None


def _assign_field(section_data: dict, field: str, index: int | None, text: str, value) -> None:
    if field in ("NACA", "DATA") and isinstance(value, (int, float)):
        value = text
    if index is None:
        section_data[field] = value
        return
    current = section_data.get(field)
    if not isinstance(current, list):
        current = [] if current is None else [current]
    current = list(current)
    while len(current) <= index:
        current.append("0")
    current[index] = text if field in ("NACA", "DATA") else value
    section_data[field] = current


def _set_edit_text(edit: QLineEdit, text: str) -> None:
    edit.blockSignals(True)
    edit.setText(text)
    edit.blockSignals(False)


def _populate_value(ac: Aircraft, key: str):
    if key == "AERO.BETA":
        # Resolved, not read raw: a hand-built Aircraft or a .mat model has no
        # BETA key, and "0.0" is a truer field than a blank one.
        return aero_beta(ac)
    return _value_from_aircraft(ac, key)


def populate_from_aircraft(window, ac: Aircraft) -> None:
    for key, edit in window._field_edits.items():
        if _is_station_key(key):
            continue
        value = _populate_value(ac, key)
        text = "" if value is None else _format_value(value)
        _set_edit_text(edit, text)
        for extra in window._field_edits_extra.get(key, []):
            _set_edit_text(extra, text)
    _sync_cmp_boxes(window, ac)
    _populate_body_stations(window, ac)
    _refresh_unit_labels(window)
    _sync_cg_slider_from_aircraft(window, ac)


def clear_fields(window) -> None:
    for edit in window._field_edits.values():
        edit.clear()
    for extras in window._field_edits_extra.values():
        for extra in extras:
            extra.clear()


def set_aero_cg_fields_enabled(window, enabled: bool) -> None:
    for key in ("AERO.WT", "AERO.XCG", "AERO.ZCG"):
        edit = window._field_edits.get(key)
        if edit is not None:
            edit.setEnabled(enabled)
    slider = getattr(window, "_cg_slider", None)
    if slider is not None:
        slider.setVisible(enabled)


def _on_mac_checkbox(window, checked: bool) -> None:
    ac = getattr(window, "aircraft", None)
    if ac is None:
        return
    apply_cg_slider_limits(window, ac, mac=checked)


def _on_cg_slider(window) -> None:
    ac = getattr(window, "aircraft", None)
    slider = getattr(window, "_cg_slider", None)
    if ac is None or slider is None:
        return
    xcg = slider.xcg()
    ac.AERO["XCG"] = xcg
    edit = window._field_edits.get("AERO.XCG")
    if edit is not None:
        _set_edit_text(edit, _format_value(xcg))


def apply_cg_slider_limits(window, ac: Aircraft, *, mac: bool | None = None) -> None:
    slider = getattr(window, "_cg_slider", None)
    box = getattr(window, "_mac_checkbox", None)
    if slider is None:
        return
    use_mac = box.isChecked() if mac is None and box is not None else bool(mac)
    estimate_on = bool(getattr(getattr(window, "settings", None), "estimate_cg", False))
    if use_mac:
        wg = ac.WG
        xmac = float(np.asarray(wg.get("xmac", 0), dtype=float).reshape(-1)[-1])
        cbar = float(np.asarray(wg.get("cbar", 1), dtype=float).reshape(-1)[-1])
        xmin = float(wg["X"]) + xmac
        xmax = xmin + cbar
    else:
        xmin = 0.0
        xmax = float(np.asarray(ac.BD["X"], dtype=float).reshape(-1)[-1])
    slider.blockSignals(True)
    slider.set_x_range(xmin, xmax)
    xcg = float(ac.AERO.get("XCG") or 0)
    if use_mac and not estimate_on:
        xcg = min(max(xcg, xmin), xmax)
        ac.AERO["XCG"] = xcg
        edit = window._field_edits.get("AERO.XCG")
        if edit is not None:
            _set_edit_text(edit, _format_value(xcg))
    slider.set_xcg(xcg)
    slider.blockSignals(False)


def _sync_cg_slider_from_aircraft(window, ac: Aircraft) -> None:
    slider = getattr(window, "_cg_slider", None)
    if slider is None:
        return
    box = getattr(window, "_mac_checkbox", None)
    apply_cg_slider_limits(window, ac, mac=box.isChecked() if box is not None else False)


def sync_fields_to_aircraft(window) -> None:
    ac: Aircraft = window.aircraft
    if ac is None:
        return
    for key, edit in window._field_edits.items():
        if _is_station_key(key):
            continue
        text = edit.text().strip()
        if not text:
            if key in _BLANK_AS_ZERO:
                # Blank is a value here, not an absence: clearing the sideslip
                # field after typing 5 must not leave the aircraft flying 5.
                section, field, index, slot = _parse_field_key(key)
                section_data = _section_dict(ac, section, slot)
                if isinstance(section_data, dict):
                    _assign_field(section_data, field, index, text, 0.0)
            continue
        section, field, index, slot = _parse_field_key(key)
        section_data = _section_dict(ac, section, slot)
        if not isinstance(section_data, dict):
            continue
        try:
            value = ast.literal_eval(text)
        except (ValueError, SyntaxError):
            value = text
        _assign_field(section_data, field, index, text, value)
    _sync_body_stations(window, ac)


def _ensure_np_nb(ac: Aircraft) -> None:
    np_list = list(ac.NP) if ac.NP else []
    while len(np_list) < 4:
        np_list.append(None)
    ac.NP = np_list
    nb_list = list(ac.NB) if ac.NB else []
    while len(nb_list) < 2:
        nb_list.append(None)
    ac.NB = nb_list


def _ensure_plot_cmp(ac: Aircraft) -> None:
    flags = [int(v) for v in list(ac.plot_cmp)]
    while len(flags) < 10:
        flags.append(1)
    ac.plot_cmp = flags


def _body_length(ac: Aircraft) -> float:
    x = np.asarray(ac.BD.get("X", [0.0, 1.0]), dtype=float).reshape(-1)
    if x.size < 2:
        return 1.0
    return float(x[-1] - x[0])


def _naca4_data(code: str, n: int) -> list[list[float]]:
    digits = "".join(ch for ch in str(code) if ch.isdigit())
    if len(digits) < 4:
        digits = "0012"
    m = int(digits[0]) / 100.0
    p = int(digits[1]) / 10.0
    t = int(digits[2:4]) / 100.0
    x = 0.5 * (1.0 - np.cos(np.linspace(0.0, np.pi, n)))
    yt = 5.0 * t * (
        0.2969 * np.sqrt(np.maximum(x, 0.0))
        - 0.1260 * x
        - 0.3516 * x**2
        + 0.2843 * x**3
        - 0.1015 * x**4
    )
    if p == 0 or m == 0:
        xu, yu, xl, yl = x, yt, x, -yt
    else:
        yc = np.zeros_like(x)
        dyc = np.zeros_like(x)
        fwd = x < p
        yc[fwd] = m / p**2 * (2 * p * x[fwd] - x[fwd] ** 2)
        dyc[fwd] = 2 * m / p**2 * (p - x[fwd])
        aft = ~fwd
        yc[aft] = m / (1 - p) ** 2 * ((1 - 2 * p) + 2 * p * x[aft] - x[aft] ** 2)
        dyc[aft] = 2 * m / (1 - p) ** 2 * (p - x[aft])
        th = np.arctan(dyc)
        xu = x - yt * np.sin(th)
        yu = yc + yt * np.cos(th)
        xl = x + yt * np.sin(th)
        yl = yc - yt * np.cos(th)
    lower = [[float(xl[i]), float(yl[i])] for i in range(n - 1, -1, -1)]
    upper = [[float(xu[i]), float(yu[i])] for i in range(1, n)]
    return lower + upper


def _airfoil_data(naca: str, npts: int, donor: dict | None):
    if donor:
        dn = donor.get("NACA")
        if isinstance(dn, list):
            dn = dn[0] if dn else ""
        if str(dn) == str(naca) and donor.get("DATA"):
            return donor["DATA"]
    return _naca4_data(naca, npts)


def _default_planform(ac: Aircraft, slot: int, *, winglet: bool) -> dict:
    L = _body_length(ac)
    if slot == 0:
        vals = [L / 4, L / 4, L / 4, L / 2, 0, 0, 0, 0.25, 0, 0, 0.12, 0, 0, L / 4, 0, 0]
        naca, npts, donor = "2412", 101, ac.WG
    elif slot == 1:
        vals = [L / 8, L / 8, L / 8, L / 4, 0, 0, 0, 1, 0, 0, 0.12, 0, 0, 7 * L / 8, 0, 0]
        naca, npts, donor = "0012", 51, ac.HT
    elif slot == 2:
        vals = [L / 8, L / 8, L / 8, L / 4, 0, 0, 0, 1, 0, 0, 0.12, 0, 0, 7 * L / 8, 0, 0]
        naca, npts, donor = "0012", 51, ac.VT
    else:
        vals = [L / 32, L / 32, L / 64, L / 8, 0, 0, 0, 0, 0, 0, 0.12, 30, 30, L / 4, L / 4, 0]
        naca, npts, donor = "0012", 51, ac.HT
    if slot == 0 and winglet:
        wg = ac.WG
        if "Xtip" not in wg:
            geometry(wg, angl=True)
        chrdr = float(wg["CHRDTP"])
        vals[0] = chrdr
        vals[2] = chrdr / 2
        vals[3] = float(wg["SSPN"]) / 10
        vals[5] = 60
        vals[7] = 1
        vals[8] = 60
        vals[10] = float(wg.get("TC") or 0.12)
        vals[12] = float(wg.get("i") or 0) - float(wg.get("TWISTA") or 0)
        vals[13] = float(wg.get("Xtip") or wg.get("X") or 0)
        vals[14] = float(wg.get("Ytip") or wg.get("Y") or 0)
        vals[15] = float(wg.get("Ztip") or wg.get("Z") or 0)
    pt = {field: vals[i] for i, field in enumerate(_PLANFORM_NUMERIC)}
    pt["NACA"] = naca
    pt["DATA"] = _airfoil_data(naca, npts, donor)
    pt["SSPNE"] = pt["SSPN"]
    return pt


def _default_body(ac: Aircraft) -> dict:
    L = _body_length(ac)
    nx = 7
    x = np.linspace(0.0, L / 4, nx).tolist()
    zu = [L / 24.0] * nx
    return {
        "NX": nx,
        "X": x,
        "ZU": zu,
        "ZL": [-L / 24.0] * nx,
        "R": [L / 24.0] * nx,
        "S": [float(np.pi * (L / 24.0) ** 2)] * nx,
        "N": list(range(1, nx + 1)),
        "P": [1] * nx,
        "ITYPE": 1,
        "X0": L / 4,
        "Y0": L / 4,
        "Z0": 0.0,
    }


def _ask_create_winglet(window) -> bool:
    if os.environ.get("QT_QPA_PLATFORM") == "offscreen":
        return False
    ans = QMessageBox.question(
        window,
        "Winglet",
        "Create winglet?",
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.Yes,
    )
    return ans == QMessageBox.StandardButton.Yes


def _tab_titles(window) -> list[str]:
    tw = getattr(window, "_tab_widget", None)
    if tw is None:
        return []
    return [tw.tabText(i) for i in range(tw.count())]


def _replot(window) -> None:
    view = getattr(window, "view3d", None)
    ac = getattr(window, "aircraft", None)
    if view is None or ac is None:
        return
    view.plot_aircraft(
        ac,
        res=tuple(window.settings.plot_res),
        angle=window.settings.angle,
        keep_camera=True,
    )


def _on_extra_cmp(window, index: int, checked: bool) -> None:
    _on_cmp(window, index, checked)


def _extra_planform_tab(window, prefix: str, title: str, cmp_index: int) -> QWidget:
    tab = _planform_tab(window, prefix, cmp_index)
    keys = [f"{prefix}.{field}" for field, _label, _kind in PLANFORM_RP]
    window._extra_tab_fields[title] = keys
    return tab


def _extra_body_tab(window, prefix: str, title: str, cmp_index: int) -> QWidget:
    return _body_tab(
        window,
        prefix,
        EXTRA_BODY_STATION_ROWS,
        cmp_index,
        extra_xyz=True,
        extra_title=title,
    )


def _hide_plus_button(window, name: str) -> None:
    btn = getattr(window, "_plus_buttons", {}).get(name)
    if btn is not None:
        btn.setVisible(False)


def _remove_extra_tabs(window) -> None:
    tw = getattr(window, "_tab_widget", None)
    if tw is None:
        return
    fields_map = getattr(window, "_extra_tab_fields", {})
    for i in range(tw.count() - 1, -1, -1):
        title = tw.tabText(i)
        if title not in _EXTRA_TAB_TITLES:
            continue
        for key in fields_map.pop(title, []):
            window._field_edits.pop(key, None)
            window._field_edits_extra.pop(key, None)
        widget = tw.widget(i)
        tw.removeTab(i)
        if widget is not None:
            widget.deleteLater()
    for idx in list(getattr(window, "_cmp_boxes", {})):
        if idx >= 4:
            window._cmp_boxes.pop(idx, None)
            window._cmp_edits.pop(idx, None)
    for prefix in list(getattr(window, "_body_station_rows", {})):
        if prefix.startswith("NB"):
            window._body_station_rows.pop(prefix, None)
    window._extra_cmp = {}
    for btn in getattr(window, "_plus_buttons", {}).values():
        btn.setVisible(True)


def add_part(window, component: int, *, imported: bool = False) -> None:
    ac = getattr(window, "aircraft", None)
    tw = getattr(window, "_tab_widget", None)
    if ac is None or tw is None:
        return
    _ensure_np_nb(ac)
    titles = _tab_titles(window)
    inner = None
    title = ""
    hide_name = None
    if component == 1:
        if "Body 2" not in titles:
            title, slot, cmp_index = "Body 2", 0, 8
        else:
            title, slot, cmp_index = "Body 3", 1, 9
            hide_name = "New Body"
        if title in titles:
            return
        if not isinstance(ac.NB[slot], dict):
            ac.NB[slot] = _default_body(ac)
        inner = _extra_body_tab(window, f"NB[{slot}]", title, cmp_index)
    elif component == 2:
        title, slot, cmp_index, hide_name = "Prop", 3, 7, "Propeller"
        if title in titles:
            return
        if not isinstance(ac.NP[slot], dict):
            ac.NP[slot] = _default_planform(ac, slot, winglet=False)
            geometry(ac.NP[slot], angl=bool(window.settings.angle))
        inner = _extra_planform_tab(window, f"NP[{slot}]", title, cmp_index)
    elif component == 3:
        title, slot, cmp_index, hide_name = "Wing 2", 0, 4, "New Wing"
        if title in titles:
            return
        if not isinstance(ac.NP[slot], dict):
            winglet = False if imported else _ask_create_winglet(window)
            ac.NP[slot] = _default_planform(ac, slot, winglet=winglet)
            geometry(ac.NP[slot], angl=bool(window.settings.angle))
        inner = _extra_planform_tab(window, f"NP[{slot}]", title, cmp_index)
    elif component == 4:
        title, slot, cmp_index, hide_name = "HT 2", 1, 5, "New HT"
        if title in titles:
            return
        if not isinstance(ac.NP[slot], dict):
            ac.NP[slot] = _default_planform(ac, slot, winglet=False)
            geometry(ac.NP[slot], angl=bool(window.settings.angle))
        inner = _extra_planform_tab(window, f"NP[{slot}]", title, cmp_index)
    elif component == 5:
        title, slot, cmp_index, hide_name = "VT 2", 2, 6, "New VT"
        if title in titles:
            return
        if not isinstance(ac.NP[slot], dict):
            ac.NP[slot] = _default_planform(ac, slot, winglet=False)
            geometry(ac.NP[slot], angl=bool(window.settings.angle))
        inner = _extra_planform_tab(window, f"NP[{slot}]", title, cmp_index)
    else:
        return
    tw.addTab(_scrollable(inner), title)
    if hide_name:
        _hide_plus_button(window, hide_name)
    if not imported:
        populate_from_aircraft(window, ac)
        tw.setCurrentIndex(tw.count() - 1)
        _replot(window)


def sync_extra_parts(window) -> None:
    _remove_extra_tabs(window)
    ac = getattr(window, "aircraft", None)
    if ac is None:
        return
    _ensure_np_nb(ac)
    if isinstance(ac.NB[0], dict) or isinstance(ac.NB[1], dict):
        add_part(window, 1, imported=True)
    if isinstance(ac.NB[1], dict):
        add_part(window, 1, imported=True)
    if isinstance(ac.NP[3], dict):
        add_part(window, 2, imported=True)
    if isinstance(ac.NP[0], dict):
        add_part(window, 3, imported=True)
    if isinstance(ac.NP[1], dict):
        add_part(window, 4, imported=True)
    if isinstance(ac.NP[2], dict):
        add_part(window, 5, imported=True)

