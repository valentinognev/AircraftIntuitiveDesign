from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QAction, QDesktopServices
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from aid.aircraft import load_jsonc, save_jsonc
from aid.paths import matlab_code, models_dir
from aid_gui import recent as recent_store
from aid_gui.tabs import clear_fields, sync_extra_parts

QUICK_START_TEXT = (
    "1. File → Load an aircraft, or Help → Examples for bundled JSONC models.\n\n"
    "2. Edit geometry and flight condition on the Wing, HT, VT, Control, Body, "
    "and Aero tabs.\n\n"
    "3. Analyze → DATCOM, Tornado, AVL, or flow5.\n\n"
    "4. Results: Geometry, Stability, or Aerodynamics."
)

# MATLAB Initialize_GUI.m 198–216 (empty labels are separators).
CONTROL_LEGEND_ITEMS = [
    "",
    "Interactive Controls:",
    "===================",
    "Scroll - Adjust Selection/Zoom",
    "Left Click - Select/Rotate",
    "Double Click - Adjust Profile",
    "Right Click - Drag Plot/Pan",
    " -> Model - Weight/Balance",
    " -> Background - Options",
    "Center/Shift Click - Drag Part",
    "Space Key - Assign to Variable",
    "Any Other Key - Isolate Part",
    "===================",
    "",
    "Background Image:",
    "===================",
    "Scroll - Scale Image",
    "Left Click - Drag Image",
    "Right Click - Options",
    "===================",
    "",
]


def build_menus(window: QMainWindow) -> None:
    _build_file_menu(window)
    _build_analyze_menu(window)
    _build_settings_menu(window)
    _build_help_menu(window)


def _build_file_menu(window: QMainWindow) -> None:
    file_menu = window.menuBar().addMenu("File")

    new_action = QAction("New", window)
    new_action.triggered.connect(lambda: _on_new(window))
    file_menu.addAction(new_action)

    load_action = QAction("Load", window)
    load_action.triggered.connect(lambda: _on_load(window))
    file_menu.addAction(load_action)

    save_action = QAction("Save", window)
    save_action.triggered.connect(lambda: _on_save(window))
    file_menu.addAction(save_action)

    file_menu.addSeparator()
    window._recent_menu = file_menu.addMenu("Recent")
    _rebuild_recent_menu(window)


def _rebuild_recent_menu(window: QMainWindow) -> None:
    menu = window._recent_menu
    menu.clear()
    for path in recent_store.recent_paths():
        action = QAction(Path(path).name, window)
        action.setToolTip(path)
        action.triggered.connect(lambda checked=False, p=path: _on_load_recent(window, p))
        menu.addAction(action)


def _on_load_recent(window: QMainWindow, path: str) -> None:
    p = Path(path)
    if not p.is_file():
        _rebuild_recent_menu(window)
        return
    window.load_aircraft(load_jsonc(p), source_stem=p.stem)
    recent_store.remember_recent(p)
    _rebuild_recent_menu(window)


def _on_new(window: QMainWindow) -> None:
    window.aircraft = None
    sync_extra_parts(window)
    clear_fields(window)
    window.settings.set_units_menu(False)
    if hasattr(window, "results_bar"):
        window.results_bar.set_summary([])


def _on_load(window: QMainWindow, start_dir: str = "") -> None:
    path, _ = QFileDialog.getOpenFileName(
        window,
        "Load Aircraft",
        start_dir,
        "JSONC Files (*.jsonc);;All Files (*)",
    )
    if not path:
        return
    p = Path(path)
    window.load_aircraft(load_jsonc(p), source_stem=p.stem)
    recent_store.remember_recent(p)
    _rebuild_recent_menu(window)


def _on_save(window: QMainWindow) -> None:
    if window.aircraft is None:
        return
    path, _ = QFileDialog.getSaveFileName(
        window,
        "Save Aircraft",
        "",
        "JSONC Files (*.jsonc);;All Files (*)",
    )
    if not path:
        return
    save_jsonc(window.aircraft, Path(path))


def _build_analyze_menu(window: QMainWindow) -> None:
    analyze_menu = window.menuBar().addMenu("Analyze")

    datcom_action = QAction("DATCOM", window)
    datcom_action.triggered.connect(window.run_datcom)
    analyze_menu.addAction(datcom_action)

    tornado_action = QAction("Tornado", window)
    tornado_action.triggered.connect(lambda: window.run_tornado())
    analyze_menu.addAction(tornado_action)

    avl_action = QAction("AVL", window)
    avl_action.triggered.connect(lambda: window.run_avl())
    analyze_menu.addAction(avl_action)

    flow5_action = QAction("flow5", window)
    flow5_action.triggered.connect(lambda: window.run_flow5())
    analyze_menu.addAction(flow5_action)


def _build_settings_menu(window: QMainWindow) -> None:
    settings = window.settings
    settings_menu = window.menuBar().addMenu("Settings")

    scale_action = QAction("Scale A/C Size", window)
    settings.add_action(("Scale A/C Size",), scale_action)
    scale_action.triggered.connect(settings.on_scale)
    settings_menu.addAction(scale_action)

    estimate_cg_action = QAction("Estimate CG", window)
    settings.add_checkable(
        ("Estimate CG",), estimate_cg_action, checked=settings.estimate_cg
    )
    estimate_cg_action.triggered.connect(
        lambda: settings.on_estimate_cg(estimate_cg_action)
    )
    settings_menu.addAction(estimate_cg_action)

    plot_options_menu = settings_menu.addMenu("Plot Options")
    transparent_action = QAction("Transparent", window)
    settings.add_checkable(
        ("Plot Options", "Transparent"),
        transparent_action,
        checked=settings.transparent,
    )
    transparent_action.triggered.connect(
        lambda: settings.on_transparent(transparent_action)
    )
    plot_options_menu.addAction(transparent_action)

    show_axes_action = QAction("Show Axes", window)
    settings.add_checkable(
        ("Plot Options", "Show Axes"), show_axes_action, checked=settings.show_axes
    )
    show_axes_action.triggered.connect(lambda: settings.on_show_axes(show_axes_action))
    plot_options_menu.addAction(show_axes_action)

    plot_res_action = QAction("Plot Resolution", window)
    settings.add_action(("Plot Options", "Plot Resolution"), plot_res_action)
    plot_res_action.triggered.connect(settings.on_plot_res)
    plot_options_menu.addAction(plot_res_action)

    shading_action = QAction("Interpolated Shading", window)
    settings.add_checkable(
        ("Plot Options", "Interpolated Shading"),
        shading_action,
        checked=settings.shading,
    )
    shading_action.triggered.connect(lambda: settings.on_shading(shading_action))
    plot_options_menu.addAction(shading_action)

    project_dims_action = QAction("Project Dimensions", window)
    settings.add_checkable(
        ("Plot Options", "Project Dimensions"),
        project_dims_action,
        checked=settings.project_dims,
    )
    project_dims_action.triggered.connect(
        lambda: settings.on_project_dims(project_dims_action)
    )
    plot_options_menu.addAction(project_dims_action)

    ac_color_action = QAction("Aircraft Color", window)
    settings.add_action(("Plot Options", "Aircraft Color"), ac_color_action)
    ac_color_action.triggered.connect(settings.on_ac_color)
    plot_options_menu.addAction(ac_color_action)

    calculations_menu = settings_menu.addMenu("Calculations")
    trim_action = QAction("Trim Mode", window)
    settings.add_checkable(
        ("Calculations", "Trim Mode"), trim_action, checked=settings.trim_mode
    )
    trim_action.triggered.connect(lambda: settings.on_trim_mode(trim_action))
    calculations_menu.addAction(trim_action)

    slipstream_action = QAction("Estimate Slipstream", window)
    settings.add_checkable(
        ("Calculations", "Estimate Slipstream"),
        slipstream_action,
        checked=settings.slipstream,
    )
    slipstream_action.triggered.connect(lambda: settings.on_slipstream(slipstream_action))
    calculations_menu.addAction(slipstream_action)

    multhopp_action = QAction("Multhopp's Method", window)
    settings.add_checkable(
        ("Calculations", "Multhopp's Method"),
        multhopp_action,
        checked=settings.multhopp,
    )
    multhopp_action.triggered.connect(lambda: settings.on_multhopp(multhopp_action))
    calculations_menu.addAction(multhopp_action)

    units_menu = settings_menu.addMenu("Units")
    units_in_action = QAction("in-oz-ft/s", window)
    settings.add_checkable(
        ("Units", "in-oz-ft/s"), units_in_action, checked=settings.units_in
    )
    units_in_action.triggered.connect(lambda: settings.on_units_in(units_in_action))
    units_menu.addAction(units_in_action)

    units_kts_action = QAction("ft-lb-kts", window)
    settings.add_checkable(
        ("Units", "ft-lb-kts"), units_kts_action, checked=settings.units_kts
    )
    units_kts_action.triggered.connect(lambda: settings.on_units_kts(units_kts_action))
    units_menu.addAction(units_kts_action)

    check_io_action = QAction("Inputs/Outputs", window)
    settings.add_checkable(
        ("Inputs/Outputs",), check_io_action, checked=settings.check_io
    )
    check_io_action.triggered.connect(lambda: settings.on_check_io(check_io_action))
    settings_menu.addAction(check_io_action)

    error_check_action = QAction("Error Check", window)
    settings.add_checkable(
        ("Error Check",), error_check_action, checked=settings.error_check
    )
    error_check_action.triggered.connect(
        lambda: settings.on_error_check(error_check_action)
    )
    settings_menu.addAction(error_check_action)

    scroll_action = QAction("Scroll Sensitivity", window)
    settings.add_checkable(
        ("Scroll Sensitivity",), scroll_action, checked=settings.scroll
    )
    settings_menu.addAction(scroll_action)


def _build_help_menu(window: QMainWindow) -> None:
    help_menu = window.menuBar().addMenu("Help")

    examples_action = QAction("Examples", window)
    examples_action.triggered.connect(lambda: _on_examples(window))
    help_menu.addAction(examples_action)

    quick_start_action = QAction("Quick Start", window)
    quick_start_action.triggered.connect(lambda: _on_quick_start(window))
    help_menu.addAction(quick_start_action)

    manual_action = QAction("User's Manual", window)
    manual_action.triggered.connect(lambda: _on_users_manual(window))
    help_menu.addAction(manual_action)

    for label in CONTROL_LEGEND_ITEMS:
        if not label:
            help_menu.addSeparator()
            continue
        item = QAction(label, window)
        item.setEnabled(False)
        help_menu.addAction(item)


class QuickStartDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Quick Start")
        self._label = QLabel(QUICK_START_TEXT)
        self._label.setWordWrap(True)
        manual_btn = QPushButton("User's Manual")
        manual_btn.clicked.connect(lambda: _on_users_manual(parent))
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addWidget(self._label)
        layout.addWidget(manual_btn)
        layout.addWidget(buttons)

    def body_text(self) -> str:
        return self._label.text()


def _on_examples(window: QMainWindow) -> None:
    _on_load(window, start_dir=str(models_dir()))


def _on_quick_start(window: QMainWindow) -> None:
    QuickStartDialog(window).exec()


def _on_users_manual(window: QMainWindow | QWidget | None) -> None:
    pdf = matlab_code() / "AID_Documentation.pdf"
    QDesktopServices.openUrl(QUrl.fromLocalFile(str(pdf)))
