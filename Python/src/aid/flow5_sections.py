from copy import deepcopy

from aid.flow5_foils import naca_digits
from aid.flow5_units import ft_to_m
from aid.geometry import geometry


def _foil_name(pt: dict) -> str:
    naca = pt["NACA"]
    code = naca[0] if isinstance(naca, (list, tuple)) else naca
    return f"NACA {naca_digits(str(code))}"


def _twist_at(pt: dict, eta: float) -> float:
    i = float(pt.get("i", 0) or 0)
    twista = float(pt.get("TWISTA", 0) or 0)
    return i - twista * eta


def _section_ny(ny: int, n_sections: int, index: int) -> int:
    if index >= n_sections - 1:
        return 0
    if n_sections <= 1:
        return max(1, ny)
    return max(1, ny // (n_sections - 1))


def planform_sections(
    pt: dict, *, nx: int, ny: int, vertical: bool = False
) -> dict:
    pt = deepcopy(pt)
    geo_type = "v" if vertical else ""
    geometry(pt, angl=False, type=geo_type)

    foil = _foil_name(pt)
    x_root = float(pt["X"])
    y_root = float(pt["Y"])
    sspn = float(pt["SSPN"])
    sspnop = float(pt.get("SSPNOP") or 0)

    if sspnop:
        stations = [
            {
                "chord": float(pt["CHRDR"]),
                "x": x_root,
                "y": y_root,
                "dihedral": float(pt["DHDADI"]),
                "eta": 0.0,
            },
            {
                "chord": float(pt["CHRDBP"]),
                "x": float(pt["Xbrk"]),
                "y": y_root + sspnop,
                "dihedral": float(pt["DHDADI"]),
                "eta": sspnop / sspn,
            },
            {
                "chord": float(pt["CHRDTP"]),
                "x": float(pt["Xtip"]),
                "y": y_root + sspn,
                "dihedral": float(pt["DHDADO"]),
                "eta": 1.0,
            },
        ]
    else:
        dhdadi = float(pt["DHDADI"])
        stations = [
            {
                "chord": float(pt["CHRDR"]),
                "x": x_root,
                "y": y_root,
                "dihedral": dhdadi,
                "eta": 0.0,
            },
            {
                "chord": float(pt["CHRDTP"]),
                "x": float(pt["Xtip"]),
                "y": y_root + sspn,
                "dihedral": dhdadi,
                "eta": 1.0,
            },
        ]

    n_sections = len(stations)
    sections = []
    for i, st in enumerate(stations):
        y_m = ft_to_m(st["y"] - y_root)
        sections.append(
            {
                "y_m": y_m,
                "chord_m": ft_to_m(st["chord"]),
                "x_offset_m": ft_to_m(st["x"] - x_root),
                "dihedral_deg": st["dihedral"],
                "twist_deg": _twist_at(pt, st["eta"]),
                "ny": _section_ny(ny, n_sections, i),
                "foil": foil,
            }
        )

    return {
        "position_m": [ft_to_m(pt["X"]), ft_to_m(pt["Y"]), ft_to_m(pt["Z"])],
        "ry_deg": float(pt.get("i", 0) or 0) if not vertical else 0.0,
        "rx_deg": -90.0 if vertical else 0.0,
        "closed_inner": vertical,
        "nx": nx,
        "sections": sections,
    }
