from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
from scipy.io import loadmat
from scipy.io.matlab._mio5_params import mat_struct

from aid import field_docs
from aid.jsonc import dumps_jsonc, loads_jsonc


# AERO keys every aircraft is guaranteed to have, as Python-only defaults: the
# MATLAB save list in Matlab/fsroot/code/AID.m does not carry them, so no .mat and
# no shipped .jsonc has them. Same treatment cg_data and results already get.
AERO_DEFAULTS: dict[str, float] = {"BETA": 0.0}


def _aero_scalar(value, default: float = 0.0) -> float:
    """First element of a MATLAB-shaped scalar, with absent/NaN landing on default."""
    if value is None:
        return default
    out = float(np.asarray(value, dtype=float).reshape(-1)[0])
    return default if out != out else out


def _aero_from_any(aero) -> dict:
    """The AERO block with AERO_DEFAULTS filled in and their values as floats.

    Handles the "key missing" and "container missing" cases in one place, so
    load_jsonc, load_mat and a hand-built dict all resolve AERO["BETA"] to 0.0.
    """
    out = {} if not isinstance(aero, dict) else dict(aero)
    for key, default in AERO_DEFAULTS.items():
        out[key] = _aero_scalar(out.get(key, default), default)
    return out


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
    results: dict | None = None


def aero_beta(ac: Aircraft, default: float = 0.0) -> float:
    """The sideslip angle in degrees, as a float, for engines that read AERO."""
    return _aero_scalar(ac.AERO.get("BETA", default), default)


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


def _results_from_dict(d: dict) -> dict | None:
    results = d.get("results")
    if not isinstance(results, dict) or not results:
        return None
    return results


def _aircraft_from_dict(d: dict) -> Aircraft:
    return Aircraft(
        WG=d["WG"],
        HT=d["HT"],
        VT=d["VT"],
        F=d["F"],
        A=d["A"],
        E=d["E"],
        R=d["R"],
        BD=d["BD"],
        NP=d["NP"],
        NB=d["NB"],
        AERO=_aero_from_any(d.get("AERO")),
        plot_cmp=d["plot_cmp"],
        unit=d["unit"],
        cg_data=d.get("cg_data"),
        results=_results_from_dict(d),
    )


def load_jsonc(path: Path) -> Aircraft:
    return _aircraft_from_dict(loads_jsonc(path.read_text()))


def save_jsonc(ac: Aircraft, path: Path) -> None:
    data = asdict(ac)
    if data.get("cg_data") is None:
        data.pop("cg_data", None)
    results = data.get("results")
    if not isinstance(results, dict) or not results:
        data.pop("results", None)
    aero = data.get("AERO")
    if isinstance(aero, dict):
        # A loaded model carries every AERO_DEFAULTS key, but the shipped files
        # predate them, so writing a default back would append a line to all 23
        # and break the byte-identical geometry round trip. Same reasoning as
        # dropping an empty cg_data / results above: only non-defaults are news.
        # A non-default still round-trips, and loads back to the same float.
        for key, default in AERO_DEFAULTS.items():
            if key in aero and _aero_scalar(aero[key], default) == default:
                aero.pop(key)
    path.write_text(dumps_jsonc(data, field_docs.DOCS))


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
        AERO=_aero_from_any(_convert_mat(raw["AERO"]) if "AERO" in raw else {}),
        plot_cmp=_convert_mat(raw["plot_cmp"]),
        unit=_convert_mat(raw["unit"]) if "unit" in raw else "ft",
        cg_data=cg_data,
        results=None,
    )
