"""JSONC field documentation catalog keyed by dotted paths (WG.CHRDR, AERO.MACH, …)."""

from __future__ import annotations


def _planform(prefix: str) -> dict[str, str]:
    """Input and derived planform fields for WG, HT, or VT."""
    p = prefix
    docs: dict[str, str] = {
        f"{p}.CHRDR": "Root Chord, ft (DATCOM CHRDR)",
        f"{p}.CHRDBP": "Break Chord, ft (DATCOM CHRDBP)",
        f"{p}.CHRDTP": "Tip Chord, ft (DATCOM CHRDTP)",
        f"{p}.SSPN": "Semi-Span, ft (DATCOM SSPN)",
        f"{p}.SSPNOP": "Break Span, ft (DATCOM SSPNOP; stored from root)",
        f"{p}.SAVSI": "Inboard Sweep, deg (DATCOM SAVSI)",
        f"{p}.SAVSO": "Outboard Sweep, deg (DATCOM SAVSO)",
        f"{p}.CHSTAT": "Sweep Reference, LE–TE fraction (0=LE, 1=TE)",
        f"{p}.DHDADI": "Inboard Dihedral, deg (DATCOM DHDADI)",
        f"{p}.DHDADO": "Outboard Dihedral, deg (DATCOM DHDADO)",
        f"{p}.TC": "Thickness, chord fraction (DATCOM TC)",
        f"{p}.TWISTA": "Washout, deg (DATCOM TWISTA)",
        f"{p}.i": "Incidence, deg (DATCOM ALIW/ALIH via SYNTHS)",
        f"{p}.X": "Position, X, ft",
        f"{p}.Y": "Position, Y, ft",
        f"{p}.Z": "Position, Z, ft",
        f"{p}.NACA": "airfoil id (NACA string cell)",
        f"{p}.DATA": "airfoil xy (cell of N×2 from NACA_Panel_Maker)",
        # Derived by Geometry.m / Aero.m / Drag.m
        f"{p}.b": "Span (full wingspan), ft",
        f"{p}.cbar": "Mean Aerodynamic Chord, ft",
        f"{p}.TR": "Taper Ratio",
        f"{p}.S": "Planform Area, ft²",
        f"{p}.AR": "Aspect Ratio",
        f"{p}.gamma": "effective dihedral, deg",
        f"{p}.Xtip": "tip X location, ft",
        f"{p}.Xbrk": "break X location, ft",
        f"{p}.Zbrk": "break Z location, ft",
        f"{p}.Ztip": "tip Z location, ft",
        f"{p}.Ybrk": "break Y location, ft",
        f"{p}.Ytip": "tip Y location, ft",
        f"{p}.swp": "sweep at LE/0.25c/0.5c/TE, deg",
        f"{p}.ymac": "Y-position of MAC, ft",
        f"{p}.xmac": "X-position of MAC leading edge, ft",
        f"{p}.SSPNE": "effective semi-span for DATCOM, ft",
        f"{p}.a0": "lift-curve slope per rad",
        f"{p}.alpha0": "zero-lift angle of attack, deg",
        f"{p}.alpha0L": "zero-lift angle adjusted for twist, deg",
        f"{p}.Cm_ac": "pitching moment about aerodynamic center",
        f"{p}.Cm": "pitching moment coefficient",
        f"{p}.CD0": "parasite drag coefficient",
        f"{p}.a": "lift-curve slope (effective)",
        f"{p}.x_ac": "aerodynamic center location (fraction MAC)",
        f"{p}.CL0": "lift coefficient at zero alpha",
        f"{p}.e": "Oswald efficiency factor",
        f"{p}.K": "induced drag factor (1/(π·e·AR))",
        f"{p}.CM0": "pitching moment at zero alpha",
        f"{p}.Cm0": "pitching moment at zero alpha",
    }
    if prefix in ("HT", "VT"):
        docs.update(
            {
                f"{p}.V": "tail volume coefficient",
                f"{p}.l": "tail arm length, ft",
                f"{p}.dwash": "downwash gradient",
                f"{p}.eta": "tail efficiency factor",
                f"{p}.swash": "spanwise downwash distribution",
                f"{p}.AReff": "effective aspect ratio",
                f"{p}.hp": "horizontal tail height parameter",
                f"{p}.lp": "horizontal tail length parameter",
                f"{p}.h": "vertical tail height parameter",
                f"{p}.k": "vertical tail volume parameter",
            }
        )
    return docs


def _controls(prefix: str, *, aileron: bool = False) -> dict[str, str]:
    """Flap/elevator/rudder (F, E, R) or aileron (A) control-surface fields."""
    docs: dict[str, str] = {
        f"{prefix}.SPANFI": "Inboard Span, ft",
        f"{prefix}.SPANFO": "Outboard Span, ft",
        f"{prefix}.CHRDFI": "Inboard Chord, ft",
        f"{prefix}.CHRDFO": "Outboard Chord, ft",
        f"{prefix}.DELTA": "Deflection, deg",
    }
    if aileron:
        docs[f"{prefix}.STYPE"] = "aileron type (DATCOM $ASYFLP)"
        docs[f"{prefix}.DELTAL"] = "left aileron deflection, deg"
        docs[f"{prefix}.DELTAR"] = "right aileron deflection, deg"
        docs[f"{prefix}.Kb"] = "aileron effectiveness factor"
    else:
        docs[f"{prefix}.FTYPE"] = "flap type (DATCOM $SYMFLP)"
        docs[f"{prefix}.PHETE"] = "trailing-edge angle, rad"
        docs[f"{prefix}.PHETEP"] = "trailing-edge angle (prime), rad"
        docs[f"{prefix}.TC"] = "thickness ratio"
        docs[f"{prefix}.CB"] = "balance chord fraction"
    return docs


def _body(prefix: str) -> dict[str, str]:
    return {
        f"{prefix}.NX": "number of body stations",
        f"{prefix}.X": "longitudinal station position, ft",
        f"{prefix}.ZU": "upper body coordinate, ft",
        f"{prefix}.ZL": "lower body coordinate, ft",
        f"{prefix}.R": "body half-width, ft",
        f"{prefix}.S": "cross-section area, ft²",
        f"{prefix}.N": "station index array",
        f"{prefix}.P": "station shape parameter",
        f"{prefix}.ITYPE": "body type code",
        f"{prefix}.CD0": "body parasite drag coefficient",
        f"{prefix}.CMa": "body pitching-moment slope",
        f"{prefix}.Cma": "body pitching-moment slope (alternate)",
        f"{prefix}.CM0": "body pitching moment at zero alpha",
        f"{prefix}.Cm0": "body pitching moment at zero alpha",
        f"{prefix}.CNB": "body yawing-moment due to sideslip",
        f"{prefix}.Cnb": "body yaw stability derivative",
        f"{prefix}.dk": "body drag increment",
    }


def _aero() -> dict[str, str]:
    return {
        "AERO.ALSCHD": "Angle(s) of Attack, deg",
        "AERO.ALT": "Altitude, ft",
        "AERO.MACH": "Mach Number",
        "AERO.WT": "Weight, lb",
        "AERO.XCG": "CG Location, X, ft",
        "AERO.ZCG": "CG Location, Z, ft",
        "AERO.XI": "Inertia, X, slug·ft²",
        "AERO.YI": "Inertia, Y, slug·ft²",
        "AERO.XW": "wing apex X offset for DATCOM SYNTHS, ft",
        "AERO.YW": "wing apex Y offset for DATCOM SYNTHS, ft",
        "AERO.ZW": "wing apex Z offset for DATCOM SYNTHS, ft",
        "AERO.ALIW": "wing incidence for DATCOM SYNTHS, deg",
        "AERO.XH": "horizontal-tail apex X offset, ft",
        "AERO.YH": "horizontal-tail apex Y offset, ft",
        "AERO.ZH": "horizontal-tail apex Z offset, ft",
        "AERO.ALIH": "horizontal-tail incidence, deg",
        "AERO.XV": "vertical-tail apex X offset, ft",
        "AERO.YV": "vertical-tail apex Y offset, ft",
        "AERO.ZV": "vertical-tail apex Z offset, ft",
        "AERO.NALPHA": "number of angle-of-attack points (DATCOM)",
        "AERO.NALT": "number of altitude points (DATCOM)",
        "AERO.NMACH": "number of Mach points (DATCOM)",
        "AERO.LOOP": "DATCOM loop flag",
        "AERO.SREF": "reference area, ft² (DATCOM OPTINS)",
        "AERO.CBARR": "reference mean chord, ft (DATCOM OPTINS)",
        "AERO.BLREF": "reference span, ft (DATCOM OPTINS)",
    }


def _build_docs() -> dict[str, str]:
    docs: dict[str, str] = {}
    for prefix in ("WG", "HT", "VT"):
        docs.update(_planform(prefix))
    docs.update(_controls("F"))
    docs.update(_controls("A", aileron=True))
    docs.update(_controls("E"))
    docs.update(_controls("R"))
    docs.update(_body("BD"))
    docs.update(_aero())
    docs.update(
        {
            "unit": "length unit (ft or in)",
            "plot_cmp": "component visibility [wing, HT, VT, body]",
            "cg_data": "optional CG calculation data",
            "NP": "extra planform cell array (wing 2, HT 2, VT 2, propeller)",
            "NB": "extra body cell array (body 2, body 3)",
        }
    )
    return docs


DOCS: dict[str, str] = _build_docs()
