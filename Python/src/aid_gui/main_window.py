import math
import os
import subprocess
import warnings
from pathlib import Path

import numpy as np

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from aid.aircraft import Aircraft
from aid.alpha_schedule import apply_alpha_default
from aid.control_report import control_report
from aid.avl_io import run_avl_full
from aid.datcom_io import DatcomInputWarning, with_aid_exposed_spans, write_for005
from aid.datcom_parse import datcom_user_warning, parse_for006
from aid.flow5_io import run_flow5
from aid.paths import avl_bin, datcom_wrapper, flow5_bin, results_dir
from aid.geometry import geometry
from aid.handbook_pass import apply_handbook
from aid.scale_geom import scale_aircraft, scale_lengths
from aid.stability import aircraft_stability
from aid.tornado.static_margin import find_static_margin
from aid.tornado.viscous import viscous_correction
from aid.lifting_line import lifting_line
from aid.tornado.boundary import set_boundary
from aid.tornado.coeff import coeff_create
from aid.tornado.lattice import lattice_setup
from aid.tornado.solver import solve
from aid.tornado.spanwise import tornado_spanwise
from aid.tornado_io import tornado_io
from aid_gui.menus import build_menus
from aid_gui.io_dialogs import (
    apply_tornado_state,
    prompt_tornado_state,
    prompt_vlm_mode,
    show_io_file_preview,
)
from aid_gui.mesh_dialog import MeshDialog
from aid_gui.settings import SettingsState
from aid_gui.results_bar import ResultsBar
from aid_gui.results_panel import ResultsPanel
from aid_gui.compare_tabs import CompareTabs
from aid_gui.tabs import build_tabs, populate_from_aircraft, sync_extra_parts, sync_fields_to_aircraft
from aid.viz import lift_overlay, planform_stations
from aid_gui.view3d import View3D
from aid_gui.context_menu import isolate_key_for_tab
from aid_gui.profile_sketcher import ProfileSketcherDialog
from aid_gui.estimate_cg import (
    CG_TITLES,
    ComponentCgDialog,
    apply_component,
    column_for_surface,
    default_component_values,
    recompute_aero_cg,
    weight_unit,
)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Aircraft Intuitive Design Tool")
        self.aircraft = None
        self._aircraft_stem: str | None = None
        self.last_results: dict = {}
        self.last_analyze_solver: str | None = None
        self.settings = SettingsState()
        build_menus(self)
        self.settings.bind_window(self)
        build_tabs(self)
        tab_widget = self.centralWidget()
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(tab_widget, 1)
        self.results_bar = ResultsBar()
        self.results_bar.modeChanged.connect(self.set_plot_mode)
        left_layout.addWidget(self.results_bar, 0)
        self.view3d = View3D()
        self.view3d.set_part_click_handler(self.pick_estimate_cg_part)
        self.results_panel = ResultsPanel()
        self.compare_tabs = CompareTabs()
        self._plot_column = QWidget()
        plot_col = QVBoxLayout(self._plot_column)
        plot_col.setContentsMargins(0, 0, 0, 0)
        plot_col.setSpacing(2)
        plot_col.addWidget(self.results_panel, 1)
        plot_col.addWidget(self.compare_tabs, 2)
        self._right_splitter = QSplitter(Qt.Orientation.Vertical)
        self._right_splitter.addWidget(self.view3d)
        self._right_splitter.addWidget(self._plot_column)
        self._right_splitter.setStretchFactor(0, 1)
        self._right_splitter.setStretchFactor(1, 0)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left)
        splitter.addWidget(self._right_splitter)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        self.setCentralWidget(splitter)
        self._plot_mode = "Geometry"
        self._placed = False
        self.resize(960, 600)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if not self._placed:
            self._placed = True
            self._place_on_screen()

    def _place_on_screen(self) -> None:
        screen = self.screen() or QApplication.primaryScreen()
        w, h = 960, 600
        if screen is not None:
            avail = screen.availableGeometry()
            w = min(w, avail.width())
            h = min(h, avail.height())
            self.resize(w, h)
            self.move(
                avail.x() + (avail.width() - w) // 2,
                avail.y() + (avail.height() - h) // 2,
            )
        else:
            self.resize(w, h)

    def _current_tab_title(self) -> str:
        tw = getattr(self, "_tab_widget", None)
        if tw is None:
            return ""
        return tw.tabText(tw.currentIndex())

    def isolate_from_key(self, event) -> None:
        key = event.key()
        if key in (
            Qt.Key.Key_Shift,
            Qt.Key.Key_Control,
            Qt.Key.Key_Alt,
            Qt.Key.Key_Meta,
            Qt.Key.Key_Space,
        ):
            return
        part = isolate_key_for_tab(self._current_tab_title())
        if part is not None:
            self.view3d.isolate_part(part)

    def keyPressEvent(self, event) -> None:
        if isinstance(self.focusWidget(), QLineEdit):
            super().keyPressEvent(event)
            return
        self.isolate_from_key(event)
        super().keyPressEvent(event)

    def open_profile_sketcher(self, bd: dict | None = None) -> None:
        if self.aircraft is None or not hasattr(self, "view3d"):
            return
        target = self.aircraft.BD if bd is None else bd
        dlg = ProfileSketcherDialog(target, parent=self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        dlg.apply_to(target)
        populate_from_aircraft(self, self.aircraft)
        self.view3d.plot_aircraft(
            self.aircraft,
            res=tuple(self.settings.plot_res),
            angle=self.settings.angle,
            keep_camera=True,
        )

    def _stability_kwargs(self) -> dict:
        s = self.settings
        trim = int(s.trim_mode_data[0]) if s.trim_mode else 0
        return {
            "slipstream": s.slipstream,
            "slipstream_data": tuple(s.slipstream_data),
            "multhopp": s.multhopp,
            "trim_mode": trim,
        }

    def stability_for_display(self) -> dict:
        if self.aircraft is None:
            raise RuntimeError("no aircraft loaded")
        return aircraft_stability(self.aircraft, **self._stability_kwargs())

    def apply_calculations(self) -> None:
        if self.aircraft is None:
            return
        self.settings.sync_calculation_actions()
        s = self.settings
        trim = int(s.trim_mode_data[0]) if s.trim_mode else 0
        st = apply_handbook(
            self.aircraft,
            angl=s.angle,
            slipstream=s.slipstream,
            slipstream_data=tuple(s.slipstream_data),
            multhopp=s.multhopp,
            trim_mode=trim,
            trim_fix="both",
        )
        populate_from_aircraft(self, self.aircraft)
        self.results_bar.set_summary(st["summary"])
        if self.plot_mode() in ("Aerodynamics", "Stability"):
            self._refresh_plots(st)

    def apply_trim(self) -> None:
        self.apply_calculations()

    def load_aircraft(self, ac: Aircraft, *, source_stem: str | None = None) -> None:
        self.aircraft = ac
        if source_stem is not None:
            self._aircraft_stem = source_stem
        self.settings.set_units_menu(ac.unit == "in")
        sync_extra_parts(self)
        populate_from_aircraft(self, ac)
        self.view3d.plot_aircraft(
            ac, res=tuple(self.settings.plot_res), angle=self.settings.angle
        )
        st = self.stability_for_display()
        self.results_bar.set_summary(st["summary"])
        self.set_plot_mode(self._plot_mode)

    def apply_field_edit(self) -> None:
        if self.aircraft is None or not hasattr(self, "view3d"):
            return
        sync_fields_to_aircraft(self)
        if self.settings.estimate_cg and recompute_aero_cg(self.aircraft):
            populate_from_aircraft(self, self.aircraft)
        self.view3d.plot_aircraft(
            self.aircraft,
            res=tuple(self.settings.plot_res),
            angle=self.settings.angle,
            keep_camera=True,
        )

    def apply_component_cg(self, col: int, x: float, z: float, wt: float) -> None:
        if self.aircraft is None:
            return
        apply_component(self.aircraft, col, x, z, wt)
        if self.settings.estimate_cg:
            recompute_aero_cg(self.aircraft)
            populate_from_aircraft(self, self.aircraft)
            self.view3d.set_estimate_cg(True)

    def pick_estimate_cg_part(self, surface_name: str) -> None:
        if not self.settings.estimate_cg or self.aircraft is None:
            return
        col = column_for_surface(surface_name)
        if col is None:
            return
        defaults = default_component_values(self.aircraft, col)
        dlg = ComponentCgDialog(
            CG_TITLES[col],
            defaults=defaults,
            unit=self.aircraft.unit,
            wt_unit=weight_unit(self.aircraft),
            parent=self,
        )
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        values = dlg.values()
        if values is None:
            return
        self.apply_component_cg(col, *values)

    def plot_mode(self) -> str:
        return self._plot_mode

    def set_plot_mode(self, mode: str) -> None:
        self._plot_mode = mode
        self.results_bar.set_mode(mode)
        if mode == "Geometry":
            if self.aircraft is not None:
                self.view3d.plot_aircraft(
                    self.aircraft,
                    res=tuple(self.settings.plot_res),
                    angle=self.settings.angle,
                )
            self.view3d.show()
            self.results_panel.hide()
            self.compare_tabs.hide()
        elif mode == "Stability":
            if self.aircraft is not None:
                self.view3d.plot_aircraft(
                    self.aircraft,
                    res=tuple(self.settings.plot_res),
                    angle=self.settings.angle,
                )
            self.view3d.hide()
            self.results_panel.show()
            self.compare_tabs.hide()
            self._right_splitter.setStretchFactor(0, 0)
            self._right_splitter.setStretchFactor(1, 1)
            self._refresh_plots()
        else:
            self.view3d.show()
            self.results_panel.show()
            self.compare_tabs.show()
            self._right_splitter.setStretchFactor(0, 3)
            self._right_splitter.setStretchFactor(1, 2)
            self._right_splitter.setSizes([360, 240])
            self._refresh_plots()

    def _refresh_plots(self, st: dict | None = None) -> None:
        if self.aircraft is None:
            return
        if st is None:
            st = self.stability_for_display()
        if self._plot_mode == "Stability":
            self.results_panel.plot_stability(st, self.last_results)
        elif self._plot_mode == "Aerodynamics":
            self.results_panel.plot_drag(st)
            self.compare_tabs.plot(
                st, self.last_results, self.aircraft, angle=self.settings.angle
            )
            nj = max(8, round(self.settings.plot_res[1] / 4))
            ov = lift_overlay(self.aircraft, nj, angle=self.settings.angle)
            tornado_sw = None
            t_res = self.last_results.get("tornado")
            if isinstance(t_res, dict) and "spanwise" in t_res:
                tornado_sw = t_res["spanwise"][0]
                wg = self.aircraft.WG
                y, c, _, _, theta = planform_stations(wg, nj, self.settings.angle, "wing")
                ll = lifting_line(self.aircraft, y, c, theta)
                ov = {**ov, "ll_Cl": ll["Cl"], "ll_scale": ll["scale"]}
            self.view3d.plot_lift_overlay(ov, tornado_sw=tornado_sw)

    def field_value(self, dotted: str) -> float:
        return float(self._field_edits[dotted].text())

    def wing_chrdr_value(self) -> float:
        return self.field_value("WG.CHRDR")

    def _require_aircraft(self) -> bool:
        if self.aircraft is None:
            box = QMessageBox(
                QMessageBox.Icon.Warning,
                "Analyze",
                "Load an aircraft before running analysis.",
                QMessageBox.StandardButton.Ok,
                self,
            )
            box.show()
            return False
        return True

    def _analysis_workdir(self, solver: str) -> Path:
        stem = self._aircraft_stem or "untitled"
        workdir = results_dir() / "python" / stem / solver
        workdir.mkdir(parents=True, exist_ok=True)
        return workdir

    def apply_units(self, to_in: bool, *, scale_size: bool) -> None:
        if self.aircraft is None:
            return
        sync_fields_to_aircraft(self)
        ac = self.aircraft
        if to_in == (ac.unit == "in"):
            return
        angl = self.settings.angle
        if to_in:
            ac.unit = "in"
            if scale_size:
                scale_lengths(ac, 12.0)
            ac.AERO["WT"] = float(ac.AERO["WT"]) / 12.0
        else:
            ac.unit = "ft"
            if scale_size:
                scale_lengths(ac, 1.0 / 12.0)
            ac.AERO["WT"] = float(ac.AERO["WT"]) * 12.0
        geometry(ac.WG, angl=angl)
        geometry(ac.HT, angl=angl)
        geometry(ac.VT, angl=angl, type="v")
        for part in ac.NP:
            if isinstance(part, dict):
                geometry(part, angl=angl)
        populate_from_aircraft(self, ac)
        self.view3d.plot_aircraft(
            ac,
            res=tuple(self.settings.plot_res),
            angle=angl,
        )
        st = self.stability_for_display()
        self.results_bar.set_summary(st["summary"])
        if self.plot_mode() in ("Aerodynamics", "Stability"):
            self._refresh_plots()
        self.settings.set_units_menu(to_in)

    def apply_scale(self, factor: float) -> None:
        if self.aircraft is None:
            return
        sync_fields_to_aircraft(self)
        scale_aircraft(self.aircraft, factor)
        ac = self.aircraft
        angl = self.settings.angle
        geometry(ac.WG, angl=angl)
        geometry(ac.HT, angl=angl)
        geometry(ac.VT, angl=angl, type="v")
        for part in ac.NP:
            if isinstance(part, dict):
                geometry(part, angl=angl)
        populate_from_aircraft(self, ac)
        self.view3d.plot_aircraft(
            ac,
            res=tuple(self.settings.plot_res),
            angle=angl,
        )
        st = self.stability_for_display()
        self.results_bar.set_summary(st["summary"])
        if self.plot_mode() in ("Aerodynamics", "Stability"):
            self._refresh_plots()

    def run_datcom(self) -> None:
        if not self._require_aircraft():
            return
        sync_fields_to_aircraft(self)
        apply_alpha_default(self.aircraft)
        ac = with_aid_exposed_spans(self.aircraft)
        workdir = self._analysis_workdir("datcom")
        workdir.mkdir(parents=True, exist_ok=True)
        input_path = workdir / "for005.dat"
        try:
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always", DatcomInputWarning)
                write_for005(ac, input_path, unit=ac.unit)
            clamp_notes = [
                str(w.message)
                for w in caught
                if issubclass(w.category, DatcomInputWarning)
            ]
            if self.settings.check_io:
                show_io_file_preview(self, "DATCOM Input", input_path)
            proc = subprocess.run(
                [str(datcom_wrapper())], cwd=workdir, check=False, timeout=120
            )
        except (FileNotFoundError, OSError):
            QMessageBox.critical(
                self,
                "DATCOM",
                f"DATCOM binary not found or could not be executed:\n{datcom_wrapper()}",
            )
            return
        output_path = workdir / "for006.dat"
        if not output_path.is_file():
            dumped = workdir / "datcom.out"
            if dumped.is_file():
                output_path = dumped
        if self.settings.check_io and output_path.is_file():
            show_io_file_preview(self, "DATCOM Output", output_path)
        if not output_path.is_file():
            if proc.returncode:
                QMessageBox.critical(
                    self,
                    "DATCOM",
                    f"DATCOM run failed.\nBinary: {datcom_wrapper()}\nWorkdir: {workdir}",
                )
            else:
                QMessageBox.critical(
                    self,
                    "DATCOM",
                    f"DATCOM produced no output file.\nWorkdir: {workdir}",
                )
            return
        text = output_path.read_text()
        try:
            coeffs = parse_for006(text)
            parse_error: BaseException | None = None
        except ValueError as exc:
            coeffs = None
            parse_error = exc
        msg = datcom_user_warning(text, error=parse_error)
        if clamp_notes:
            clamp_text = "\n".join(clamp_notes)
            msg = f"{clamp_text}\n\n{msg}" if msg else clamp_text
        if msg:
            QMessageBox.warning(self, "DATCOM", f"{msg}\n\nWorkdir: {workdir}")
        if coeffs is None:
            return
        self.last_results["datcom"] = coeffs
        self.last_analyze_solver = "datcom"
        self._refresh_plots()

    def _paint_tornado_cp(self, lattice: dict, coeffs: dict) -> None:
        xyz = lattice.get("XYZ")
        cp = coeffs.get("cp")
        view = getattr(self, "view3d", None)
        if xyz is None or cp is None or view is None:
            return
        xyz = np.asarray(xyz, dtype=float)
        cp = np.asarray(cp, dtype=float).reshape(-1)
        if xyz.ndim != 3 or xyz.shape[0] == 0 or xyz.shape[0] != cp.size:
            return
        if xyz.shape[1] > 4:
            xyz = xyz[:, :4, :]
        view.paint_cp(xyz, cp)

    def _maybe_estimate_neutral_point(self, geo: dict, state: dict, coeffs: dict) -> None:
        """Not a persistent toggle. Offscreen and tests never ask."""
        if os.environ.get("QT_QPA_PLATFORM") == "offscreen":
            return
        answer = QMessageBox.question(
            self,
            "Estimate Neutral Point?",
            "Estimate Neutral Point?",
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            coeffs["N0"] = find_static_margin(geo, state)
        except Exception:
            return

    def run_tornado(
        self,
        mesh: tuple[str, ...] | None = None,
        *,
        vlm_mode: int | None = None,
        state_overrides: dict | None = None,
    ) -> None:
        if not self._require_aircraft():
            return
        sync_fields_to_aircraft(self)
        apply_alpha_default(self.aircraft)
        if not isinstance(mesh, tuple):
            mesh = None
        if mesh is None:
            dlg = MeshDialog(self.aircraft, "tornado", self)
            if dlg.exec() != QDialog.DialogCode.Accepted:
                return
            mesh = dlg.values()
        if mesh is None:
            return
        # AID.m Analyze Tornado: handbook trim alpha, moments about 25% MAC
        st = self.stability_for_display()
        geo, state = tornado_io(self.aircraft, mesh)
        state = dict(state)
        state["alpha"] = float(st["alpha"]) * math.pi / 180.0

        mode = 0
        if self.settings.check_io:
            interactive = vlm_mode is None and state_overrides is None
            if interactive:
                edited = prompt_tornado_state(self, state)
                if edited is not None:
                    state = edited
                mode = prompt_vlm_mode(self)
            else:
                if state_overrides is not None:
                    state = apply_tornado_state(state, state_overrides)
                if vlm_mode is not None:
                    mode = int(vlm_mode)

        lattice, ref = lattice_setup(geo, state, mode)
        lattice = set_boundary(lattice, geo, state)
        mac = np.asarray(ref["mac_pos"], dtype=float).reshape(-1)
        rp = np.array(geo["ref_point"], dtype=float, copy=True)
        rp[0] = float(mac[0]) + float(ref["C_mac"]) / 4.0
        geo = {**geo, "ref_point": rp}
        raw = solve(state, geo, lattice)
        coeffs = coeff_create(raw, lattice, state, ref, geo)
        alpha = float(state["alpha"])
        coeffs["alpha"] = alpha
        coeffs["CL0"] = float(coeffs["CL"]) - float(coeffs["CL_a"]) * alpha
        coeffs["Cm0"] = float(coeffs["Cm"]) - float(coeffs["Cm_a"]) * alpha
        coeffs["spanwise"] = tornado_spanwise(coeffs, lattice, geo, state, self.aircraft)
        self._finish_tornado(coeffs, geo, state, lattice, ref, mode)

    def _finish_tornado(
        self,
        coeffs: dict,
        geo: dict,
        state: dict,
        lattice: dict,
        ref: dict,
        mode: int,
    ) -> None:
        """Save the inviscid Tornado dict, then run the optional hooks.

        A viscous-strip failure or a neutral-point failure does not drop CL or CD.
        Plots still refresh.
        """
        if self.settings.check_io:
            coeffs["vlm_mode"] = mode
        self.last_results["tornado"] = coeffs
        self.last_analyze_solver = "tornado"
        if self.settings.viscous_strip:
            try:
                coeffs["viscous"] = viscous_correction(geo, state, lattice, coeffs, ref)
            except Exception:
                pass
        try:
            self._paint_tornado_cp(lattice, coeffs)
        except Exception:
            pass
        self._maybe_estimate_neutral_point(geo, state, coeffs)
        self._refresh_plots()

    def run_avl(
        self,
        mesh: tuple[str, ...] | None = None,
    ) -> None:
        if not self._require_aircraft():
            return
        sync_fields_to_aircraft(self)
        apply_alpha_default(self.aircraft)
        if not isinstance(mesh, tuple):
            mesh = None
        if mesh is None:
            dlg = MeshDialog(self.aircraft, "avl", self)
            if dlg.exec() != QDialog.DialogCode.Accepted:
                return
            mesh = dlg.values()
        if mesh is None:
            return
        workdir = self._analysis_workdir("avl")
        try:
            coeffs = run_avl_full(self.aircraft, mesh, workdir)
            if self.settings.check_io:
                for name in ("geometry.avl", "geometry.run"):
                    path = workdir / name
                    if path.is_file():
                        show_io_file_preview(self, f"AVL {name}", path)
        except (FileNotFoundError, OSError):
            QMessageBox.critical(
                self,
                "AVL",
                f"AVL binary not found or could not be executed:\n{avl_bin()}",
            )
            return
        except subprocess.CalledProcessError:
            QMessageBox.critical(
                self,
                "AVL",
                f"AVL run failed.\nBinary: {avl_bin()}\nWorkdir: {workdir}",
            )
            return
        self.last_results["avl"] = coeffs
        self.last_analyze_solver = "avl"
        self._refresh_plots()

    def run_flow5(
        self,
        mesh: tuple[str, ...] | None = None,
    ) -> None:
        if not self._require_aircraft():
            return
        sync_fields_to_aircraft(self)
        apply_alpha_default(self.aircraft)
        if not isinstance(mesh, tuple):
            mesh = None
        if mesh is None:
            dlg = MeshDialog(self.aircraft, "flow5", self)
            if dlg.exec() != QDialog.DialogCode.Accepted:
                return
            mesh = dlg.values()
        if mesh is None:
            return
        workdir = self._analysis_workdir("flow5")
        try:
            coeffs = run_flow5(self.aircraft, mesh)
        except (FileNotFoundError, OSError):
            QMessageBox.critical(
                self,
                "flow5",
                f"flow5 binary not found or could not be executed:\n{flow5_bin()}",
            )
            return
        except subprocess.CalledProcessError:
            QMessageBox.critical(
                self,
                "flow5",
                f"flow5 run failed.\nBinary: {flow5_bin()}\nWorkdir: {workdir}",
            )
            return
        self.last_results["flow5"] = coeffs
        self.last_analyze_solver = "flow5"
        self._refresh_plots()

    def run_control_derivatives(self) -> None:
        if not self._require_aircraft():
            return
        sync_fields_to_aircraft(self)
        apply_alpha_default(self.aircraft)
        solver = self.last_analyze_solver or "handbook"
        try:
            report = control_report(self.aircraft, solver, [0.0, 5.0])
        except (
            FileNotFoundError,
            OSError,
            subprocess.CalledProcessError,
            subprocess.TimeoutExpired,
            ValueError,
            KeyError,
        ) as exc:
            QMessageBox.critical(self, "Control derivatives", str(exc))
            return
        self.last_results["control_derivatives"] = report
        self._refresh_plots()
