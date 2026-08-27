from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QAction, QDesktopServices
from PySide6.QtWidgets import QMainWindow, QFileDialog

from aid.aircraft import load_jsonc, save_jsonc
from aid.paths import matlab_code
from aid_gui.tabs import clear_fields


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


def _on_new(window: QMainWindow) -> None:
    window.aircraft = None
    clear_fields(window)


def _on_load(window: QMainWindow) -> None:
    path, _ = QFileDialog.getOpenFileName(
        window,
        "Load Aircraft",
        "",
        "JSONC Files (*.jsonc);;All Files (*)",
    )
    if not path:
        return
    p = Path(path)
    window.load_aircraft(load_jsonc(p), source_stem=p.stem)


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
    tornado_action.triggered.connect(window.run_tornado)
    analyze_menu.addAction(tornado_action)

    avl_action = QAction("AVL", window)
    avl_action.triggered.connect(window.run_avl)
    analyze_menu.addAction(avl_action)


def _build_settings_menu(window: QMainWindow) -> None:
    settings_menu = window.menuBar().addMenu("Settings")

    scale_action = QAction("Scale", window)
    scale_action.setEnabled(False)
    settings_menu.addAction(scale_action)

    estimate_cg_action = QAction("Estimate CG", window)
    estimate_cg_action.setEnabled(False)
    settings_menu.addAction(estimate_cg_action)

    plot_options_menu = settings_menu.addMenu("Plot Options")
    for label in (
        "Transparent",
        "Show Axes",
        "Plot Resolution",
        "Interpolated Shading",
        "Project Dimensions",
        "Aircraft Color",
    ):
        action = QAction(label, window)
        action.setEnabled(False)
        plot_options_menu.addAction(action)

    calculations_menu = settings_menu.addMenu("Calculations")
    for label in ("Trim Mode", "Estimate Slipstream", "Multhopp's Method"):
        action = QAction(label, window)
        action.setEnabled(False)
        calculations_menu.addAction(action)

    units_menu = settings_menu.addMenu("Units")
    for label in ("in-oz-ft/s", "ft-lb-kts"):
        action = QAction(label, window)
        action.setEnabled(False)
        units_menu.addAction(action)

    for label in ("Inputs/Outputs", "Error Check", "Scroll Sensitivity"):
        action = QAction(label, window)
        action.setEnabled(False)
        settings_menu.addAction(action)


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

    legend_action = QAction("control legend", window)
    legend_action.triggered.connect(lambda: _on_control_legend(window))
    help_menu.addAction(legend_action)


def _on_examples(window: QMainWindow) -> None:
    pass


def _on_quick_start(window: QMainWindow) -> None:
    pass


def _on_users_manual(window: QMainWindow) -> None:
    pdf = matlab_code() / "AID_Documentation.pdf"
    QDesktopServices.openUrl(QUrl.fromLocalFile(str(pdf)))


def _on_control_legend(window: QMainWindow) -> None:
    pass
