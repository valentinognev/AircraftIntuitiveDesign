"""3D-view context menu (MATLAB Initialize_GUI.m 65–89 idea)."""

from __future__ import annotations

from PySide6.QtWidgets import QMenu, QWidget

TAB_ISOLATE = {
    "Wing": "wing",
    "HT": "ht",
    "VT": "vt",
    "Body": "BD",
    "Wing 2": "wing 2",
    "HT 2": "ht 2",
    "VT 2": "vt 2",
    "Prop": "prop",
    "Body 2": "NB{1}",
    "Body 3": "NB{2}",
}


def isolate_key_for_tab(title: str) -> str | None:
    return TAB_ISOLATE.get(title)


def build_plot_context_menu(view: QWidget) -> QMenu:
    menu = QMenu(view)
    menu.addAction("Reset Plot", view.reset_plot)
    view_menu = menu.addMenu("View")
    for name in ("Side", "Top", "Front"):
        view_menu.addAction(name, lambda checked=False, n=name: view.apply_view(n))
    bg = menu.addMenu("Background")
    bg.addAction("Load", view.prompt_load_background)
    bg.addAction("Hide", view.hide_background)
    bg.addAction("Flip", view.flip_background)
    bg.addAction("Rotate", view.rotate_background)
    return menu
