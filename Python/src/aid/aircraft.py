from dataclasses import dataclass
from pathlib import Path

import numpy as np
from scipy.io import loadmat
from scipy.io.matlab._mio5_params import mat_struct


@dataclass
class Aircraft:
    WG: dict
    HT: dict
    VT: dict
    F: dict
    A: dict
    E: dict
    R: dict
    BD: dict
    NP: list
    NB: list
    AERO: dict
    plot_cmp: list
    unit: str
    cg_data: list | None = None


def _convert_cell_element(obj):
    if isinstance(obj, np.ndarray) and obj.size == 0 and np.issubdtype(obj.dtype, np.floating):
        return None
    return _convert_mat(obj)


def _convert_mat(obj):
    if isinstance(obj, mat_struct):
        return {name: _convert_mat(getattr(obj, name)) for name in obj._fieldnames}

    if isinstance(obj, np.ndarray):
        if obj.dtype == object:
            return [_convert_cell_element(x) for x in obj.flat]
        if obj.ndim == 0:
            return _convert_mat(obj.item())
        if obj.ndim == 1:
            return [_convert_mat(x) for x in obj]
        if obj.ndim == 2 and obj.shape[1] == 1:
            return [_convert_mat(x) for x in obj.flat]
        if obj.ndim == 2:
            return [[_convert_mat(x) for x in row] for row in obj]
        return [_convert_mat(x) for x in obj.flat]

    if isinstance(obj, bytes):
        return obj.decode("utf-8")

    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return float(obj)
    if isinstance(obj, np.bool_):
        return bool(obj)

    return obj


def load_mat(path: Path) -> Aircraft:
    raw = loadmat(str(path), squeeze_me=True, struct_as_record=False)
    cg_raw = raw.get("cg_data")
    cg_data = None if cg_raw is None else _convert_mat(cg_raw)
    return Aircraft(
        WG=_convert_mat(raw["WG"]),
        HT=_convert_mat(raw["HT"]),
        VT=_convert_mat(raw["VT"]),
        F=_convert_mat(raw["F"]),
        A=_convert_mat(raw["A"]),
        E=_convert_mat(raw["E"]),
        R=_convert_mat(raw["R"]),
        BD=_convert_mat(raw["BD"]),
        NP=_convert_mat(raw["NP"]),
        NB=_convert_mat(raw["NB"]),
        AERO=_convert_mat(raw["AERO"]),
        plot_cmp=_convert_mat(raw["plot_cmp"]),
        unit=_convert_mat(raw["unit"]),
        cg_data=cg_data,
    )
