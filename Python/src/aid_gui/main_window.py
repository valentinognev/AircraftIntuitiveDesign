import subprocess
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMainWindow, QMessageBox, QSplitter

from aid.aircraft import Aircraft
from aid.avl_io import run_avl_full
from aid.datcom_run import run_datcom
from aid.paths import avl_bin, datcom_wrapper, results_dir
from aid.tornado.boundary import set_boundary
from aid.tornado.coeff import coeff_create
from aid.tornado.lattice import lattice_setup
from aid.tornado.solver import solve
from aid.tornado_io import tornado_io
from aid_gui.menus import build_menus
from aid_gui.results_panel import ResultsPanel
from aid_gui.tabs import build_tabs, populate_from_aircraft
from aid_gui.view3d import View3D

_TORNADO_MESH = ("10", "5")
_AVL_MESH = ("10", "10")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Aircraft Intuitive Design Tool")
        self.resize(960, 600)
        self.aircraft = None
        self._aircraft_stem: str | None = None
        self.last_results: dict = {}
        build_menus(self)
        build_tabs(self)
        tab_widget = self.centralWidget()
        self.view3d = View3D()
        self.results_panel = ResultsPanel()
        right_splitter = QSplitter(Qt.Orientation.Vertical)
        right_splitter.addWidget(self.view3d)
        right_splitter.addWidget(self.results_panel)
        right_splitter.setStretchFactor(0, 1)
        right_splitter.setStretchFactor(1, 0)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(tab_widget)
        splitter.addWidget(right_splitter)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        self.setCentralWidget(splitter)

    def load_aircraft(self, ac: Aircraft, *, source_stem: str | None = None) -> None:
        self.aircraft = ac
        if source_stem is not None:
            self._aircraft_stem = source_stem
        populate_from_aircraft(self, ac)
        self.view3d.plot_aircraft(ac)

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

    def run_datcom(self) -> None:
        if not self._require_aircraft():
            return
        workdir = self._analysis_workdir("datcom")
        try:
            coeffs = run_datcom(self.aircraft, workdir)
        except (FileNotFoundError, OSError):
            QMessageBox.critical(
                self,
                "DATCOM",
                f"DATCOM binary not found or could not be executed:\n{datcom_wrapper()}",
            )
            return
        except subprocess.CalledProcessError:
            QMessageBox.critical(
                self,
                "DATCOM",
                f"DATCOM run failed.\nBinary: {datcom_wrapper()}\nWorkdir: {workdir}",
            )
            return
        self.last_results["datcom"] = coeffs
        self.results_panel.plot_datcom(coeffs)

    def run_tornado(self) -> None:
        if not self._require_aircraft():
            return
        geo, state = tornado_io(self.aircraft, _TORNADO_MESH)
        lattice, ref = lattice_setup(geo, state, 0)
        lattice = set_boundary(lattice, geo, state)
        raw = solve(state, geo, lattice)
        coeffs = coeff_create(raw, lattice, state, ref, geo)
        self.last_results["tornado"] = coeffs

    def run_avl(self) -> None:
        if not self._require_aircraft():
            return
        workdir = self._analysis_workdir("avl")
        try:
            coeffs = run_avl_full(self.aircraft, _AVL_MESH, workdir)
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
