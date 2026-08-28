import math
import os

import numpy as np

os.environ.setdefault("QT_API", "pyside6")
_OFFSCREEN = os.environ.get("QT_QPA_PLATFORM") == "offscreen"
if _OFFSCREEN:
    os.environ.setdefault("PYVISTA_OFF_SCREEN", "true")
    os.environ.setdefault("VTK_DEFAULT_RENDER_WINDOW_OFFSCREEN", "1")

import pyvista as pv
from PySide6.QtCore import QEvent, Qt
from PySide6.QtWidgets import QFileDialog, QMenu, QVBoxLayout, QWidget

if _OFFSCREEN:
    pv.OFF_SCREEN = True

from aid.aircraft import Aircraft
from aid.viz import aircraft_surfaces
from aid_gui.context_menu import build_plot_context_menu
from aid_gui.estimate_cg import column_for_surface, part_for_column

_BG = "#3c3c3c"
_COLOR = (1.0, 1.0, 1.0)
_MISSING_CG_COLOR = (1.0, 0.0, 0.0)
_AXIS_PREFIX = "matlab_axis_"
_PICK_DRAG_PX = 5.0
_BG_ACTOR = "aid_background"


def _part_for_surface_name(ac: Aircraft, name: str) -> dict | None:
    col = column_for_surface(name)
    if col is None:
        return None
    return part_for_column(ac, col)


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


class _KeyAcceptHost(QWidget):
    """Stand-in for QtInteractor offscreen: accepts KeyPress so it does not bubble."""

    def keyPressEvent(self, event) -> None:
        event.accept()


def _actor_prop(plotter, actor):
    if isinstance(actor, str):
        return plotter.actors[actor].GetProperty()
    return actor.GetProperty()


def _vtk_actor(plotter, actor):
    if isinstance(actor, str):
        return plotter.actors[actor]
    return actor


def _same_component(surf_name: str, isolate_key: str) -> bool:
    col_iso = column_for_surface(isolate_key)
    col_surf = column_for_surface(surf_name)
    if col_iso is not None and col_surf is not None:
        return col_iso == col_surf
    return surf_name == isolate_key or surf_name.startswith(isolate_key)


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
        self._part_click_handler = None
        self._mesh_part_names: list[str] = []
        self._pending_part: str | None = None
        self._press_xy: tuple[float, float] | None = None
        self._pointer_xy_override: tuple[float, float] | None = None
        self._release_observer = None
        self._isolated_part: str | None = None
        self._background_path: str | None = None
        self._background_hidden = True
        self._bg_flip = False
        self._bg_rot90 = 0
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._on_context_menu)
        if isinstance(self._plotter, QWidget):
            self._key_host = self._plotter
        else:
            self._key_host = _KeyAcceptHost(self)
            self._key_host.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._key_host.installEventFilter(self)
        if not _OFFSCREEN:
            interactor = self._plotter
            set_policy = getattr(interactor, "setContextMenuPolicy", None)
            if callable(set_policy):
                set_policy(Qt.ContextMenuPolicy.CustomContextMenu)
                interactor.customContextMenuRequested.connect(self._on_context_menu)

    def plotter_widget(self) -> QWidget:
        return self._key_host

    def eventFilter(self, obj, event) -> bool:
        if obj is self._key_host and event.type() == QEvent.Type.KeyPress:
            parent = self.window()
            handler = getattr(parent, "isolate_from_key", None)
            if callable(handler):
                handler(event)
            return False
        return super().eventFilter(obj, event)

    def missing_cg_highlights(self) -> int:
        return self._missing_cg_highlights

    def set_estimate_cg(self, enabled: bool) -> None:
        self._estimate_cg = bool(enabled)
        if self._aircraft is not None:
            self._draw_meshes(self._aircraft)
        self._setup_picking()

    def set_part_click_handler(self, handler) -> None:
        self._part_click_handler = handler
        self._setup_picking()

    def mesh_count(self) -> int:
        return self._mesh_count

    def mesh_part_names(self) -> list[str]:
        return list(self._mesh_part_names)

    def mesh_visibility(self) -> list[bool]:
        out = []
        for actor in self._mesh_actor_names:
            vtk_actor = _vtk_actor(self._plotter, actor)
            out.append(bool(vtk_actor.GetVisibility()))
        return out

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
        keep_camera: bool = False,
    ) -> None:
        self._aircraft = ac
        if res is not None:
            self._res = tuple(res)
        if angle is not None:
            self._angle = bool(angle)
        cam = None
        if keep_camera:
            try:
                cam = self._plotter.camera_position
            except Exception:
                cam = None
        self._plotter.clear()
        self._mesh_count = 0
        self._mesh_actor_names = []
        self._axis_actor_names = []
        self._overlay_actor_names = []
        self._draw_meshes(ac)
        self._add_lights()
        if keep_camera and cam is not None:
            self._plotter.camera_position = cam
        else:
            self._plotter.reset_camera()
            if self._show_axes:
                self._add_matlab_axes()
                self._plotter.enable_parallel_projection()
            self.apply_matlab_view()
            self._restore_background()
            self._apply_isolate()
            return
        if self._show_axes:
            self._add_matlab_axes()
            self._plotter.enable_parallel_projection()
        self._restore_background()
        self._apply_isolate()

    def _draw_meshes(self, ac: Aircraft) -> None:
        for name in self._mesh_actor_names:
            self._plotter.remove_actor(name)
        self._mesh_actor_names = []
        self._mesh_part_names = []
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
                pickable=True,
            )
            self._mesh_actor_names.append(actor)
            self._mesh_part_names.append(surf.name)
            self._mesh_count += 1
        self._setup_picking()
        self._apply_isolate()

    def _setup_picking(self) -> None:
        plotter = self._plotter
        self._clear_release_observer()
        disable = getattr(plotter, "disable_picking", None)
        if callable(disable):
            try:
                disable()
            except Exception:
                pass
        if not self._estimate_cg or self._part_click_handler is None:
            return
        enable = getattr(plotter, "enable_mesh_picking", None)
        if not callable(enable):
            return
        try:
            enable(
                callback=self._on_mesh_picked,
                show=False,
                show_message=False,
                picker="cell",
                use_actor=True,
                left_clicking=True,
            )
        except TypeError:
            try:
                enable(
                    callback=self._on_mesh_picked,
                    use_actor=True,
                    left_clicking=True,
                )
            except Exception:
                return
        except Exception:
            return
        self._attach_release_observer()

    def _clear_release_observer(self) -> None:
        iren = getattr(self._plotter, "iren", None)
        if self._release_observer is not None and iren is not None:
            try:
                iren.remove_observer(self._release_observer)
            except Exception:
                pass
        self._release_observer = None

    def _attach_release_observer(self) -> None:
        iren = getattr(self._plotter, "iren", None)
        if iren is None:
            return
        add = getattr(iren, "add_observer", None)
        if not callable(add):
            return
        try:
            self._release_observer = add("LeftButtonReleaseEvent", lambda *_: self.finish_pick())
        except Exception:
            self._release_observer = None

    def set_pointer_xy(self, x: float, y: float) -> None:
        self._pointer_xy_override = (float(x), float(y))

    def _pointer_xy(self) -> tuple[float, float] | None:
        if self._pointer_xy_override is not None:
            return self._pointer_xy_override
        pos = getattr(self._plotter, "mouse_position", None)
        if pos is not None and len(pos) >= 2 and pos[0] is not None:
            return float(pos[0]), float(pos[1])
        iren = getattr(self._plotter, "iren", None)
        if iren is not None:
            get = getattr(iren, "get_event_position", None) or getattr(iren, "GetEventPosition", None)
            if callable(get):
                try:
                    event_pos = get()
                    return float(event_pos[0]), float(event_pos[1])
                except Exception:
                    pass
        return None

    def _picked_object_name(self, picked) -> str | None:
        if picked is None:
            return None
        if isinstance(picked, str):
            return picked
        name = getattr(picked, "name", None)
        if isinstance(name, str) and name:
            return name
        return None

    def _part_name_for_picked(self, picked) -> str | None:
        actors = self._mesh_actor_names
        parts = self._mesh_part_names
        if not actors or len(actors) != len(parts):
            return None
        for actor, part in zip(actors, parts, strict=True):
            if picked is actor:
                return part
        picked_name = self._picked_object_name(picked)
        if not picked_name:
            return None
        for i, actor in enumerate(actors):
            actor_name = actor if isinstance(actor, str) else self._picked_object_name(actor)
            if actor_name == picked_name or picked_name == f"ac_mesh_{i}":
                return parts[i]
        return None

    def _on_mesh_picked(self, picked) -> None:
        if not self._estimate_cg or self._part_click_handler is None:
            return
        part = self._part_name_for_picked(picked)
        if part is None:
            self._pending_part = None
            return
        self._pending_part = part
        self._press_xy = self._pointer_xy()

    def finish_pick(self) -> None:
        part = self._pending_part
        press = self._press_xy
        self._pending_part = None
        self._press_xy = None
        if not self._estimate_cg or self._part_click_handler is None or part is None:
            return
        now = self._pointer_xy()
        if press is not None and now is not None:
            dx = now[0] - press[0]
            dy = now[1] - press[1]
            if math.hypot(dx, dy) > _PICK_DRAG_PX:
                return
        self._part_click_handler(part)

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
        self._apply_az_el(-37.5, 30.0)

    def apply_view(self, preset: str) -> None:
        if preset == "Side":
            self._apply_az_el(0.0, 0.0)
        elif preset == "Top":
            self._apply_az_el(0.0, 90.0)
        elif preset == "Front":
            self._apply_az_el(-90.0, 0.0)
        else:
            self.apply_matlab_view()

    def _apply_az_el(self, az_deg: float, el_deg: float) -> None:
        az = math.radians(az_deg)
        el = math.radians(el_deg)
        dx = math.cos(el) * math.sin(az)
        dy = -math.cos(el) * math.cos(az)
        dz = math.sin(el)
        viewup = (0.0, 0.0, 1.0)
        if abs(el_deg) >= 89.0:
            dx, dy, dz = 0.0, 0.0, 1.0 if el_deg > 0 else -1.0
            viewup = (0.0, 1.0, 0.0)
        self._plotter.view_vector((dx, dy, dz), viewup=viewup)

    def isolate_part(self, part: str | None) -> None:
        self._isolated_part = part
        self._apply_isolate()

    def _apply_isolate(self) -> None:
        part = self._isolated_part
        for actor, name in zip(self._mesh_actor_names, self._mesh_part_names):
            visible = part is None or _same_component(name, part)
            try:
                _vtk_actor(self._plotter, actor).SetVisibility(int(visible))
            except Exception:
                pass

    def reset_plot(self) -> None:
        self._isolated_part = None
        self._apply_isolate()
        self.apply_matlab_view()

    def plot_context_menu(self) -> QMenu:
        return build_plot_context_menu(self)

    def _on_context_menu(self, pos) -> None:
        self.plot_context_menu().exec(self.mapToGlobal(pos))

    def keyPressEvent(self, event) -> None:
        parent = self.window()
        handler = getattr(parent, "isolate_from_key", None)
        if callable(handler):
            handler(event)
        super().keyPressEvent(event)

    def prompt_load_background(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Choose Background Image File",
            "",
            "Image Files (*.png *.jpg *.gif *.jpeg *.bmp)",
        )
        if path:
            self.load_background(path)

    def load_background(self, path: str) -> None:
        self._background_path = path
        self._background_hidden = False
        self._add_background_actor()

    def hide_background(self) -> None:
        self._background_hidden = True
        self._remove_background_actor()

    def background_visible(self) -> bool:
        if self._background_hidden or not self._background_path:
            return False
        actors = getattr(self._plotter, "actors", {}) or {}
        if _BG_ACTOR in actors:
            return bool(actors[_BG_ACTOR].GetVisibility())
        return False

    def flip_background(self) -> None:
        if self._background_hidden or not self._background_path:
            return
        self._bg_flip = not self._bg_flip
        self._add_background_actor()

    def rotate_background(self) -> None:
        if self._background_hidden or not self._background_path:
            return
        self._bg_rot90 = (self._bg_rot90 + 90) % 360
        self._add_background_actor()

    def _restore_background(self) -> None:
        if not self._background_hidden and self._background_path:
            self._add_background_actor()

    def _remove_background_actor(self) -> None:
        try:
            self._plotter.remove_actor(_BG_ACTOR)
        except Exception:
            pass

    def _add_background_actor(self) -> None:
        self._remove_background_actor()
        if self._background_hidden or not self._background_path:
            return
        d = max(self._body_half_length(), 0.5)
        plane = pv.Plane(
            center=(d, 0.0, 0.0),
            direction=(0.0, 1.0, 0.0),
            i_size=max(4.0 * d, 1.0),
            j_size=max(2.0 * d, 1.0),
        )
        if self._bg_rot90:
            plane.rotate_z(self._bg_rot90, inplace=True)
        if self._bg_flip:
            plane.points[:, 0] *= -1.0
        kwargs = {"name": _BG_ACTOR, "pickable": False}
        try:
            tex = pv.read_texture(self._background_path)
            self._plotter.add_mesh(plane, texture=tex, **kwargs)
        except Exception:
            self._plotter.add_mesh(plane, color="white", **kwargs)

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
