import math
import os

import numpy as np

os.environ.setdefault("QT_API", "pyside6")
_OFFSCREEN = os.environ.get("QT_QPA_PLATFORM") == "offscreen"
if _OFFSCREEN:
    os.environ.setdefault("PYVISTA_OFF_SCREEN", "true")
    os.environ.setdefault("VTK_DEFAULT_RENDER_WINDOW_OFFSCREEN", "1")

import pyvista as pv
from PySide6.QtWidgets import QVBoxLayout, QWidget

if _OFFSCREEN:
    pv.OFF_SCREEN = True

from aid.aircraft import Aircraft
from aid.viz import aircraft_surfaces

_BG = "#3c3c3c"
_COLOR = (1.0, 1.0, 1.0)
_MISSING_CG_COLOR = (1.0, 0.0, 0.0)
_AXIS_PREFIX = "matlab_axis_"


def _part_for_surface_name(ac: Aircraft, name: str) -> dict | None:
    if name.startswith("WG"):
        return ac.WG
    if name.startswith("HT"):
        return ac.HT
    if name.startswith("VT"):
        return ac.VT
    if name == "BD" or name.startswith("BD"):
        return ac.BD
    if name.startswith("NP{"):
        idx = int(name[3]) - 1
        if 0 <= idx < len(ac.NP):
            part = ac.NP[idx]
            return part if isinstance(part, dict) else None
    if name == "prop" and len(ac.NP) > 3:
        part = ac.NP[3]
        return part if isinstance(part, dict) else None
    if name.startswith("NB{"):
        idx = int(name[3]) - 1
        if 0 <= idx < len(ac.NB):
            part = ac.NB[idx]
            return part if isinstance(part, dict) else None
    return None


def _part_missing_xcg(part: dict | None) -> bool:
    return part is None or "XCG" not in part


def _count_missing_xcg_components(ac: Aircraft) -> int:
    flags = list(ac.plot_cmp) + [1] * 8
    parts: list[dict | None] = []
    if flags[0]:
        parts.append(ac.WG)
    if flags[1]:
        parts.append(ac.HT)
    if flags[2]:
        parts.append(ac.VT)
    if flags[3]:
        parts.append(ac.BD)
    for pt in ac.NP:
        if pt:
            parts.append(pt if isinstance(pt, dict) else None)
    for pt in ac.NB:
        if pt:
            parts.append(pt if isinstance(pt, dict) else None)
    return sum(1 for part in parts if _part_missing_xcg(part))


def _make_plotter(parent: QWidget):
    """QtInteractor on a real display; headless Plotter under Qt offscreen tests."""
    if _OFFSCREEN:
        return pv.Plotter(off_screen=True)
    from pyvistaqt import QtInteractor

    plotter = QtInteractor(parent)
    plotter.setMinimumSize(0, 0)
    return plotter


def _actor_prop(plotter, actor):
    if isinstance(actor, str):
        return plotter.actors[actor].GetProperty()
    return actor.GetProperty()


class View3D(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self._plotter = _make_plotter(self)
        if not _OFFSCREEN:
            layout.addWidget(self._plotter)
        self._plotter.set_background(_BG)
        self._plotter.hide_axes()
        self._mesh_count = 0
        self._mesh_actor_names: list[str] = []
        self._axis_actor_names: list[str] = []
        self._overlay_actor_names: list[str] = []
        self._aircraft: Aircraft | None = None
        self._opacity = 1.0
        self._mesh_color = _COLOR
        self._smooth_shading = True
        self._show_edges = False
        self._show_axes = False
        self._res: tuple[int, int, int] = (100, 101, 51)
        self._angle = True
        self._estimate_cg = False
        self._missing_cg_highlights = 0

    def missing_cg_highlights(self) -> int:
        return self._missing_cg_highlights

    def set_estimate_cg(self, enabled: bool) -> None:
        self._estimate_cg = bool(enabled)
        if self._aircraft is not None:
            self._draw_meshes(self._aircraft)

    def mesh_count(self) -> int:
        return self._mesh_count

    def line_count(self) -> int:
        return self._mesh_count

    def overlay_count(self) -> int:
        return len(self._overlay_actor_names)

    def mesh_opacity(self) -> float:
        if not self._mesh_actor_names:
            return self._opacity
        prop = _actor_prop(self._plotter, self._mesh_actor_names[0])
        return float(prop.GetOpacity())

    def mesh_color(self) -> tuple[float, float, float]:
        if not self._mesh_actor_names:
            return self._mesh_color
        prop = _actor_prop(self._plotter, self._mesh_actor_names[0])
        return tuple(prop.GetColor())

    def smooth_shading(self) -> bool:
        return self._smooth_shading

    def axis_actor_count(self) -> int:
        return len(self._axis_actor_names)

    def is_parallel_projection(self) -> bool:
        return bool(self._plotter.camera.parallel_projection)

    def set_opacity(self, opacity: float) -> None:
        self._opacity = float(opacity)
        for name in self._mesh_actor_names:
            _actor_prop(self._plotter, name).SetOpacity(self._opacity)

    def set_shading(self, smooth: bool) -> None:
        self._smooth_shading = bool(smooth)
        self._show_edges = not self._smooth_shading
        if self._aircraft is not None:
            self._draw_meshes(self._aircraft)

    def set_mesh_color(self, color: tuple[float, float, float]) -> None:
        self._mesh_color = tuple(color[:3])
        if self._aircraft is not None:
            self._draw_meshes(self._aircraft)

    def set_show_axes(self, show: bool) -> None:
        self._show_axes = bool(show)
        if show:
            self._add_matlab_axes()
            self._plotter.enable_parallel_projection()
        else:
            self._remove_matlab_axes()
            self._plotter.disable_parallel_projection()
            self.apply_matlab_view()

    def plot_aircraft(
        self,
        ac: Aircraft,
        *,
        res: tuple[int, int, int] | None = None,
        angle: bool | None = None,
    ) -> None:
        self._aircraft = ac
        if res is not None:
            self._res = tuple(res)
        if angle is not None:
            self._angle = bool(angle)
        self._plotter.clear()
        self._mesh_count = 0
        self._mesh_actor_names = []
        self._axis_actor_names = []
        self._overlay_actor_names = []
        self._draw_meshes(ac)
        self._add_lights()
        self._plotter.reset_camera()
        if self._show_axes:
            self._add_matlab_axes()
            self._plotter.enable_parallel_projection()
        self.apply_matlab_view()

    def _draw_meshes(self, ac: Aircraft) -> None:
        for name in self._mesh_actor_names:
            self._plotter.remove_actor(name)
        self._mesh_actor_names = []
        self._mesh_count = 0
        self._missing_cg_highlights = _count_missing_xcg_components(ac) if self._estimate_cg else 0
        for i, surf in enumerate(aircraft_surfaces(ac, angle=self._angle, res=self._res)):
            grid = pv.StructuredGrid(surf.x, surf.y, surf.z)
            if self._estimate_cg and _part_missing_xcg(_part_for_surface_name(ac, surf.name)):
                color = _MISSING_CG_COLOR
            else:
                color = self._mesh_color
            actor = self._plotter.add_mesh(
                grid,
                color=color,
                smooth_shading=self._smooth_shading,
                specular=0.55,
                specular_power=25,
                ambient=0.22,
                diffuse=0.75,
                show_edges=self._show_edges,
                opacity=self._opacity,
                name=f"ac_mesh_{i}",
            )
            self._mesh_actor_names.append(actor)
            self._mesh_count += 1

    def plot_lift_overlay(self, ov: dict, tornado_sw=None) -> None:
        """Prandtl lift distribution: blue Cl, dashed black Cl_ideal, lift arrows."""
        for name in self._overlay_actor_names:
            self._plotter.remove_actor(name)
        self._overlay_actor_names = []

        x = np.asarray(ov["X"], dtype=float)
        y = np.asarray(ov["Y"], dtype=float)
        z0 = np.asarray(ov["Z0"], dtype=float)
        cl = np.asarray(ov["Cl"], dtype=float)
        cl_ideal = np.asarray(ov["Cl_ideal"], dtype=float)

        cl_line = _polyline(np.column_stack([x, y, z0 + cl]))
        actor_cl = self._plotter.add_mesh(cl_line, color="blue", line_width=2, name="lift_cl")
        self._overlay_actor_names.append(actor_cl)

        ideal_line = _polyline(np.column_stack([x, y, z0 + cl_ideal]))
        actor_ideal = self._plotter.add_mesh(
            ideal_line, color="black", line_width=2, name="lift_cl_ideal"
        )
        ideal_prop = (
            self._plotter.actors[actor_ideal].GetProperty()
            if isinstance(actor_ideal, str)
            else actor_ideal.GetProperty()
        )
        ideal_prop.SetLineStipplePattern(0xF0F0)
        ideal_prop.SetLineStippleRepeatFactor(1)
        self._overlay_actor_names.append(actor_ideal)

        arrow_mesh = _vertical_segments(x, y, z0, cl)
        actor_arrows = self._plotter.add_mesh(
            arrow_mesh, color=(0.5, 0.6, 1.0), line_width=1, name="lift_arrows"
        )
        self._overlay_actor_names.append(actor_arrows)

        if tornado_sw is not None:
            y_sw = np.asarray(tornado_sw["y"], dtype=float)
            cl_sw = np.asarray(tornado_sw["Cl"], dtype=float)
            ll_cl = np.asarray(ov["ll_Cl"], dtype=float)
            scale = float(ov["ll_scale"])
            chrdr = float(np.max(np.abs(cl_ideal)))
            cl_sw = cl_sw * np.max(np.abs(ll_cl)) / np.max(cl_sw)
            cl_sw = cl_sw / scale * chrdr
            x_sw = float(x[0])
            z_wg = float(z0[0])
            tornado_line = _polyline(np.column_stack([np.full(y_sw.shape, x_sw), y_sw, z_wg + cl_sw]))
            actor_tornado = self._plotter.add_mesh(
                tornado_line, color="red", line_width=2, name="lift_tornado"
            )
            self._overlay_actor_names.append(actor_tornado)

    def apply_matlab_view(self) -> None:
        """MATLAB view(3): az=-37.5°, el=30°."""
        az = math.radians(-37.5)
        el = math.radians(30.0)
        dx = math.cos(el) * math.sin(az)
        dy = -math.cos(el) * math.cos(az)
        dz = math.sin(el)
        self._plotter.view_vector((dx, dy, dz), viewup=(0, 0, 1))

    def _body_half_length(self) -> float:
        if self._aircraft is None:
            return 1.0
        x = np.asarray(self._aircraft.BD["X"], dtype=float).reshape(-1)
        return float(x[-1]) / 2.0

    def _add_matlab_axes(self) -> None:
        self._remove_matlab_axes()
        d = self._body_half_length()
        axes = [
            (pv.Line((0.0, -1.25 * d, 0.0), (0.0, 1.25 * d, 0.0)), "y_line"),
            (pv.Line((-0.4 * d, 0.0, 0.0), (2.4 * d, 0.0, 0.0)), "x_line"),
            (pv.Line((0.0, 0.0, -0.7 * d), (0.0, 0.0, 0.7 * d)), "z_line"),
        ]
        for line, tag in axes:
            actor = self._plotter.add_mesh(
                line, color="black", line_width=2, name=f"{_AXIS_PREFIX}{tag}"
            )
            self._axis_actor_names.append(actor)
        labels = [
            ((0.0, 1.35 * d, 0.0), "y"),
            ((2.45 * d, 0.0, 0.0), "x"),
            ((0.0, 0.0, 0.8 * d), "z"),
        ]
        for point, text in labels:
            actor = self._plotter.add_point_labels(
                [point],
                [text],
                font_size=14,
                text_color="white",
                show_points=False,
                name=f"{_AXIS_PREFIX}label_{text}",
            )
            self._axis_actor_names.append(actor)

    def _remove_matlab_axes(self) -> None:
        for name in self._axis_actor_names:
            self._plotter.remove_actor(name)
        self._axis_actor_names = []

    def camera_xyz(self) -> tuple[float, float, float]:
        pos, _, _ = self._plotter.camera_position
        return tuple(pos)

    def camera_focus(self) -> tuple[float, float, float]:
        _, foc, _ = self._plotter.camera_position
        return tuple(foc)

    def _add_lights(self) -> None:
        self._plotter.remove_all_lights()
        self._plotter.add_light(
            pv.Light(position=(-0.26, -1.0, 0.5), light_type="scene light", intensity=0.7)
        )
        self._plotter.add_light(
            pv.Light(position=(0.26, -1.0, 0.5), light_type="scene light", intensity=0.7)
        )


def _polyline(points: np.ndarray) -> pv.PolyData:
    n = len(points)
    cells = np.empty(n + 1, dtype=np.int_)
    cells[0] = n
    cells[1:] = np.arange(n)
    return pv.PolyData(points, lines=cells)


def _vertical_segments(x: np.ndarray, y: np.ndarray, z0: np.ndarray, dz: np.ndarray) -> pv.PolyData:
    n = len(x)
    points = np.empty((2 * n, 3), dtype=float)
    points[0::2] = np.column_stack([x, y, z0])
    points[1::2] = np.column_stack([x, y, z0 + dz])
    lines = np.empty((n, 3), dtype=np.int_)
    lines[:, 0] = 2
    lines[:, 1] = np.arange(0, 2 * n, 2)
    lines[:, 2] = np.arange(1, 2 * n, 2)
    return pv.PolyData(points, lines=lines)
