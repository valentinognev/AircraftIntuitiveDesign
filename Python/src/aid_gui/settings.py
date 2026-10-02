from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtGui import QAction, QColor
from PySide6.QtWidgets import (
    QColorDialog,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
)

if TYPE_CHECKING:
    from aid_gui.main_window import MainWindow


class ScaleDialog(QDialog):
    def __init__(self, parent: "MainWindow | None" = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Scale")
        self._accepted = False
        self._factor_edit = QLineEdit("1")
        form = QFormLayout()
        form.addRow("Scaling Factor", self._factor_edit)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def accept(self) -> None:
        self._accepted = True
        super().accept()

    def reject(self) -> None:
        self._accepted = False
        super().reject()

    def factor(self) -> float | None:
        if not self._accepted:
            return None
        try:
            return float(self._factor_edit.text())
        except ValueError:
            return None


class PlotResDialog(QDialog):
    def __init__(self, res: tuple[int, int, int], parent: "MainWindow | None" = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Plot Resolution")
        self._accepted = False
        self._edits: list[QLineEdit] = []
        form = QFormLayout()
        for label, value in zip(("Body", "Wing", "Tail"), res, strict=True):
            edit = QLineEdit(str(value))
            form.addRow(label, edit)
            self._edits.append(edit)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def accept(self) -> None:
        self._accepted = True
        super().accept()

    def reject(self) -> None:
        self._accepted = False
        super().reject()

    def values(self) -> tuple[int, int, int] | None:
        if not self._accepted:
            return None
        try:
            return tuple(int(edit.text()) for edit in self._edits)
        except ValueError:
            return None


class SettingsState:
    """MATLAB Initialize_GUI.m settings defaults and menu action registry."""

    def __init__(self) -> None:
        self.estimate_cg = False
        self.transparent = False
        self.transparent_alpha = 0.3
        self.show_axes = False
        self.plot_res = (100, 101, 51)
        self.shading = True
        self.project_dims = False
        self.angle = True
        self.ac_color = (1.0, 1.0, 1.0)
        self.trim_mode = False
        self.trim_mode_data = [0, 30]
        self.slipstream = False
        self.slipstream_data = [0.5, 0.9]
        self.multhopp = True
        self.viscous_strip = False
        self.units_in = False
        self.units_kts = True
        self.check_io = False
        self.error_check = True
        self.error_check_data = [999, 89, 0]
        self.scroll = False
        self.scroll_data = 0.1
        self._actions: dict[tuple[str, ...], QAction] = {}
        self._window: MainWindow | None = None

    @property
    def error_limits(self) -> tuple[float, float, float]:
        return tuple(self.error_check_data)

    @error_limits.setter
    def error_limits(self, value: tuple[float, float, float]) -> None:
        self.error_check_data = list(value)

    @property
    def scroll_delta(self) -> float:
        return self.scroll_data

    @scroll_delta.setter
    def scroll_delta(self, value: float) -> None:
        self.scroll_data = float(value)

    def bind_window(self, window: MainWindow) -> None:
        self._window = window

    def action(self, path: tuple[str, ...]) -> QAction:
        return self._actions[path]

    def register(self, path: tuple[str, ...], action: QAction) -> None:
        self._actions[path] = action

    def add_checkable(
        self,
        path: tuple[str, ...],
        action: QAction,
        *,
        checked: bool,
    ) -> None:
        action.setCheckable(True)
        action.setChecked(checked)
        self.register(path, action)

    def add_action(self, path: tuple[str, ...], action: QAction) -> None:
        self.register(path, action)

    def set_units_menu(self, units_in: bool) -> None:
        self.units_in = units_in
        self.units_kts = not units_in
        self.action(("Units", "in-oz-ft/s")).setChecked(units_in)
        self.action(("Units", "ft-lb-kts")).setChecked(not units_in)

    def on_estimate_cg(self, action: QAction) -> None:
        self.estimate_cg = action.isChecked()
        if self._window is None:
            return
        from aid_gui.estimate_cg import ensure_cg_data, recompute_aero_cg
        from aid_gui.tabs import populate_from_aircraft, set_aero_cg_fields_enabled

        if self.estimate_cg and self._window.aircraft is not None:
            ensure_cg_data(self._window.aircraft)
            if recompute_aero_cg(self._window.aircraft):
                populate_from_aircraft(self._window, self._window.aircraft)
        set_aero_cg_fields_enabled(self._window, not self.estimate_cg)
        self._window.view3d.set_estimate_cg(self.estimate_cg)

    def on_transparent(self, action: QAction) -> None:
        if self._window is None:
            return
        opacity = self.transparent_alpha if action.isChecked() else 1.0
        self._window.view3d.set_opacity(opacity)

    def on_show_axes(self, action: QAction) -> None:
        if self._window is None:
            return
        self._window.view3d.set_show_axes(action.isChecked())

    def on_shading(self, action: QAction) -> None:
        if self._window is None:
            return
        self._window.view3d.set_shading(action.isChecked())

    def on_ac_color(self) -> None:
        if self._window is None:
            return
        r, g, b = self.ac_color
        initial = QColor(int(r * 255), int(g * 255), int(b * 255))
        color = QColorDialog.getColor(initial, self._window, "Aircraft Color")
        if not color.isValid():
            return
        self.set_ac_color((color.redF(), color.greenF(), color.blueF()))

    def set_ac_color(self, rgb: tuple[float, float, float]) -> None:
        self.ac_color = tuple(rgb[:3])
        if self._window is None or self._window.aircraft is None:
            return
        self._window.view3d.set_mesh_color(self.ac_color)

    def set_plot_res(self, res: tuple[int, int, int]) -> None:
        self.plot_res = tuple(res)
        self._rebuild_aircraft()

    def set_trim(self, mode: int, delta_max: float = 30) -> None:
        self.trim_mode = bool(mode)
        self.trim_mode_data = [int(mode), float(delta_max)]
        try:
            self.action(("Calculations", "Trim Mode")).setChecked(self.trim_mode)
        except KeyError:
            pass

    def sync_calculation_actions(self) -> None:
        """Read Calculations menu QAction state into SettingsState."""
        try:
            self.trim_mode = self.action(("Calculations", "Trim Mode")).isChecked()
            self.slipstream = self.action(("Calculations", "Estimate Slipstream")).isChecked()
            self.multhopp = self.action(("Calculations", "Multhopp's Method")).isChecked()
            self.viscous_strip = self.action(("Calculations", "Viscous Strip")).isChecked()
        except KeyError:
            pass

    def on_trim_mode(self, action: QAction) -> None:
        self.trim_mode = action.isChecked()
        if not self.trim_mode:
            self.trim_mode_data[0] = 0
        elif self.trim_mode_data[0] == 0:
            self.trim_mode_data[0] = 1
        self._apply_calculations()

    def on_slipstream(self, action: QAction) -> None:
        self.slipstream = action.isChecked()
        self._apply_calculations()

    def on_multhopp(self, action: QAction) -> None:
        self.multhopp = action.isChecked()
        self._apply_calculations()

    def on_viscous_strip(self, action: QAction) -> None:
        """Tornado-only. Default off so gold compares stay inviscid."""
        self.viscous_strip = action.isChecked()

    def _apply_calculations(self) -> None:
        if self._window is not None:
            self._window.apply_calculations()

    def on_scale(self) -> None:
        if self._window is None:
            return
        dlg = ScaleDialog(self._window)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        factor = dlg.factor()
        if factor is None:
            return
        self._window.apply_scale(factor)

    def on_plot_res(self) -> None:
        if self._window is None:
            return
        dlg = PlotResDialog(tuple(self.plot_res), self._window)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        values = dlg.values()
        if values is None:
            return
        self.set_plot_res(values)

    def on_project_dims(self, action: QAction) -> None:
        self.project_dims = action.isChecked()
        self.angle = not action.isChecked()
        self._rebuild_aircraft()

    def on_units_in(self, action: QAction) -> None:
        if self._window is None:
            return
        other = self.action(("Units", "ft-lb-kts"))
        other.setChecked(False)
        action.setChecked(True)
        if self.units_in:
            return
        scale_size = self._units_scale_dialog(to_in=True)
        if scale_size is None:
            action.setChecked(False)
            other.setChecked(True)
            return
        self._window.apply_units(to_in=True, scale_size=scale_size)

    def on_check_io(self, action: QAction) -> None:
        self.check_io = action.isChecked()

    def on_error_check(self, action: QAction) -> None:
        self.error_check = action.isChecked()

    def on_units_kts(self, action: QAction) -> None:
        if self._window is None:
            return
        other = self.action(("Units", "in-oz-ft/s"))
        other.setChecked(False)
        action.setChecked(True)
        if self.units_kts:
            return
        scale_size = self._units_scale_dialog(to_in=False)
        if scale_size is None:
            action.setChecked(False)
            other.setChecked(True)
            return
        self._window.apply_units(to_in=False, scale_size=scale_size)

    def _units_scale_dialog(self, to_in: bool) -> bool | None:
        if self._window is None or self._window.aircraft is None:
            return False
        ac = self._window.aircraft
        unit = ac.unit
        length = float(ac.BD["X"][-1]) - float(ac.BD["X"][0])
        if to_in:
            new_length = length * 12.0
            new_unit = "in"
        else:
            new_length = length / 12.0
            new_unit = "ft"
        yes = f"Yes (length will remain {length:.0f} {unit})"
        no = f"No (new length will be {new_length:.0f} {new_unit})"
        box = QMessageBox(self._window)
        box.setWindowTitle("Change Units")
        box.setText("Scale dimensions to maintain size?")
        yes_btn = box.addButton(yes, QMessageBox.ButtonRole.YesRole)
        no_btn = box.addButton(no, QMessageBox.ButtonRole.NoRole)
        box.setDefaultButton(no_btn)
        box.exec()
        clicked = box.clickedButton()
        if clicked is yes_btn:
            return True
        if clicked is no_btn:
            return False
        return None

    def _rebuild_aircraft(self) -> None:
        if self._window is None or self._window.aircraft is None:
            return
        self._window.view3d.plot_aircraft(
            self._window.aircraft,
            res=tuple(self.plot_res),
            angle=self.angle,
        )
        if self._window.plot_mode() in ("Aerodynamics", "Stability"):
            self._window._refresh_plots()
