from copy import deepcopy
from pathlib import Path
import warnings

import numpy as np
from scipy.interpolate import CubicSpline

from aid.aircraft import Aircraft

DATCOM_STMACH = 0.6
DATCOM_SSPNE_MIN = 0.01
DATCOM_NDELTA_MAX = 9
DATCOM_BODY_MAX = 200
DATCOM_CARD_WIDTH = 80
DATCOM_ARRAY_PER_LINE = 10


class DatcomInputWarning(UserWarning):
    """Solver-input clamp; stored aircraft fields are not changed."""



def _last(val) -> float:
    return float(np.asarray(val).reshape(-1)[-1])


def with_aid_exposed_spans(ac: Aircraft) -> Aircraft:
    """Copy of `ac` with WG/HT/VT SSPNE matching AID.m GUI geometry update.

    AID.m interpolates body radius at each planform LE/TE
    (`interp1(..., 'spline', 'extrap')`) and sets
    `SSPNE = SSPN - (R_LE + R_TE) / 2`. Batch gold keeps stored SSPNE.
    """
    ac = deepcopy(ac)
    x = np.asarray(ac.BD["X"], dtype=float).reshape(-1)
    r = np.asarray(ac.BD["R"], dtype=float).reshape(-1)
    spline = CubicSpline(x, r, extrapolate=True)
    for pt in (ac.WG, ac.HT, ac.VT):
        x_le = float(pt["X"])
        x_te = x_le + float(pt["CHRDR"])
        r_le = float(spline(x_le))
        r_te = float(spline(x_te))
        pt["SSPNE"] = float(pt["SSPN"]) - (r_le + r_te) / 2.0
    return ac


def _as_list(value):
    if isinstance(value, (list, tuple)):
        return list(value)
    return [value]


def _fmt_values(values, fmt):
    return "".join(fmt % v for v in values)


def format_wrapped_array(name, vals, fmt) -> str:
    """10 values/line, wrap at <=80 columns, 2-space indent. MATLAB format_wrapped_array."""
    arr = np.asarray(vals, dtype=float).reshape(-1)
    header = f"  {name}="
    chunks: list[str] = []
    line = header
    n_on_line = 0
    for val in arr:
        tok = fmt % val
        would = len(line) + len(tok)
        if n_on_line > 0 and (n_on_line >= DATCOM_ARRAY_PER_LINE or would > DATCOM_CARD_WIDTH):
            chunks.append(line)
            line = "  " + tok
            n_on_line = 1
        else:
            line += tok
            n_on_line += 1
    chunks.append(line)
    return "\n".join(chunks)


def _write_namelist_array(parts, name, vals, fmt):
    """Append one DATCOM namelist array; wrap at <=80 columns. No 18-point downsample."""
    parts.append("\n")
    parts.append(format_wrapped_array(name, vals, fmt))


def write_fltcon(ac: Aircraft, lines: list) -> None:
    """Append DATCOM $FLTCON namelist lines matching DATCOM_IO.m."""
    aero = ac.AERO
    alschd = _as_list(aero["ALSCHD"])
    alt = _as_list(aero["ALT"])
    raw_mach = [float(m) for m in _as_list(aero["MACH"])]
    mach = [min(m, DATCOM_STMACH) for m in raw_mach]
    if any(m > DATCOM_STMACH for m in raw_mach):
        warnings.warn(
            f"DATCOM MACH clamped to {DATCOM_STMACH} (STMACH); "
            "stored AERO.MACH unchanged.",
            DatcomInputWarning,
            stacklevel=2,
        )
    wt = aero["WT"]

    parts = [f" $FLTCON NALPHA={len(alschd):.1f},ALSCHD="]
    if len(alschd) > 10:
        parts.append(_fmt_values(alschd[:10], "%.1f,"))
        parts.append("\n  ")
        parts.append(_fmt_values(alschd[10:], "%.1f,"))
    else:
        parts.append(_fmt_values(alschd, "%.1f,"))

    parts.append(f"\n  NALT={len(alt):.1f},ALT=")
    parts.append(_fmt_values(alt, "%.1f,"))
    parts.append(f"\n  NMACH={len(mach):.1f},MACH=")
    parts.append(_fmt_values(mach, "%.3f,"))
    parts.append(f"\n  WT={wt:.2f},LOOP=2.0$")

    lines.append("".join(parts))


def write_optins(ac: Aircraft, lines: list) -> None:
    """Append DATCOM $OPTINS namelist matching DATCOM_IO.m."""
    wg = ac.WG
    sref = _last(wg["S"])
    cbarr = _last(wg["cbar"])
    blref = wg["b"]
    lines.append(f" $OPTINS SREF={sref:.2f},CBARR={cbarr:.2f},BLREF={blref:.2f}$")


def write_synths(ac: Aircraft, lines: list) -> None:
    """Append DATCOM-safe $SYNTHS namelist (no YW/YH) matching DATCOM_IO.m."""
    aero = ac.AERO
    wg = ac.WG
    ht = ac.HT
    vt = ac.VT
    parts = [
        f" $SYNTHS XCG={aero['XCG']:.2f},ZCG={aero['ZCG']:.2f},"
        f"XW={wg['X']:.2f},ZW={wg['Z']:.2f},",
        f"ALIW={wg['i']:.2f},\n  ",
        f"XH={ht['X']:.2f},ZH={ht['Z']:.2f},",
        f"ALIH={ht['i']:.2f},XV={vt['X']:.2f},YV={vt['Y']:.2f},",
        f"ZV={vt['Z']:.2f},VERTUP=.TRUE.$",
    ]
    lines.append("".join(parts))


def write_body(ac: Aircraft, lines: list) -> None:
    """Append DATCOM $BODY namelist from BD matching DATCOM_IO.m."""
    bd = ac.BD
    body = {
        "NX": float(bd["NX"]),
        "X": _as_list(bd["X"]),
        "ZU": _as_list(bd["ZU"]),
        "ZL": _as_list(bd["ZL"]),
        "R": _as_list(bd["R"]),
        "P": _as_list(bd["P"]),
        "S": _as_list(bd["S"]),
    }
    nx = int(body["NX"])
    if nx > DATCOM_BODY_MAX:
        idx = np.round(np.linspace(0, nx - 1, DATCOM_BODY_MAX)).astype(int)
        for key in ("X", "ZU", "ZL", "R", "P", "S"):
            body[key] = np.asarray(body[key], dtype=float)[idx].tolist()
        body["NX"] = DATCOM_BODY_MAX
        warnings.warn(
            f"DATCOM BODY NX clamped to {DATCOM_BODY_MAX}; stored BD.NX unchanged.",
            DatcomInputWarning,
            stacklevel=2,
        )

    s_arr = np.asarray(body["S"], dtype=float)
    precision = "%.3f," if np.min(s_arr) < 0.01 else "%.2f,"

    parts = [f" $BODY NX={body['NX']:.1f},ITYPE=1.0,"]
    for name, fmt in (
        ("X", "%.2f,"),
        ("ZU", "%.2f,"),
        ("ZL", "%.2f,"),
        ("R", "%.2f,"),
        ("P", "%.2f,"),
        ("S", precision),
    ):
        _write_namelist_array(parts, name, body[name], fmt)
    joined = "".join(parts)
    last_line_len = len(joined) - joined.rfind("\n") - 1
    parts.append("\n$" if last_line_len + 1 > DATCOM_CARD_WIDTH else "$")
    lines.append("".join(parts))


def _naca_airfoil_code(naca) -> str:
    """First cell that parses as a NACA series (skip Data./paths). MATLAB naca_airfoil_code."""
    cells = naca if isinstance(naca, (list, tuple)) else [naca]
    for s in cells:
        if s is None:
            continue
        s = str(s).strip()
        if not s:
            continue
        low = s.lower()
        if low in ("data.", "load_pts.", "type_pts.") or "/" in s or "\\" in s:
            continue
        try:
            if len(s) == 6:
                float(s[0:2] + s[3:6])
            else:
                float(s)
        except ValueError:
            continue
        return s
    return ""


def _naca_card(prefix: str, naca, default: str) -> str:
    code = _naca_airfoil_code(naca) or default
    if code != (naca[0] if isinstance(naca, (list, tuple)) else naca):
        first = naca[0] if isinstance(naca, (list, tuple)) else naca
        if first and str(first) != code:
            warnings.warn(
                f"NACA{{1}} is not a numeric code ({first!r}); "
                f"imported section DATA is not sent to DATCOM "
                f"(NACA card {code} used instead).",
                DatcomInputWarning,
                stacklevel=3,
            )
    return f"NACA-{prefix}-{len(code)}-{code}"


def naca_wing_line(ac: Aircraft) -> str:
    """Return NACA-W card string from WG.NACA matching DATCOM_IO.m."""
    return _naca_card("W", ac.WG["NACA"], "2412")


def naca_ht_line(ac: Aircraft) -> str:
    """Return NACA-H card string from HT.NACA matching DATCOM_IO.m."""
    return _naca_card("H", ac.HT["NACA"], "2412")


def naca_vt_line(ac: Aircraft) -> str:
    """Return NACA-V card string from VT.NACA matching DATCOM_IO.m."""
    return _naca_card("V", ac.VT["NACA"], "0012")


_WGPLNF_RP = (
    "CHRDR",
    "CHRDBP",
    "CHRDTP",
    "SSPN",
    "SSPNE",
    "SSPNOP",
    "SAVSI",
    "SAVSO",
    "CHSTAT",
    "DHDADI",
    "DHDADO",
)


def _planform_is_datcom_legal(pt) -> bool:
    """False when DATCOM would see an illegal exposed planform (do not mutate pt)."""
    sspn = float(pt.get("SSPN", 0.0) or 0.0)
    chrdr = float(pt.get("CHRDR", 0.0) or 0.0)
    if sspn <= 0.0 or chrdr <= 0.0:
        return False
    raw_sspne = float(pt.get("SSPNE", sspn) or 0.0)
    if raw_sspne < 0.0:
        return False
    sspne = max(raw_sspne, DATCOM_SSPNE_MIN)
    if sspne > sspn:
        return False
    s_raw = pt.get("S", 0.0)
    if s_raw is not None and s_raw != 0:
        try:
            area = _last(s_raw)
        except (TypeError, ValueError, IndexError):
            area = 0.0
        if area < 0.0:
            return False
    return True


def _control_is_datcom_legal(pt) -> bool:
    """False when flap/aileron/elevator span is empty or inverted.

    MATLAB still writes SPANFO past the parent planform (DA20 elevator 4.7 vs
    HT SSPN 4.2764). Only SPANFO<=SPANFI is omitted. SPANFO may be clamped
    to parent SSPN at write time so DATCOM does not crash.
    """
    spanfi = float(pt.get("SPANFI", 0.0) or 0.0)
    spanfo = float(pt.get("SPANFO", 0.0) or 0.0)
    return spanfo > spanfi


def _control_for_write(pt, parent_sspn: float) -> dict:
    """Copy *pt* with SPANFO clamped to *parent_sspn* if needed. Stored dict unchanged."""
    spanfo = float(pt.get("SPANFO", 0.0) or 0.0)
    if spanfo <= parent_sspn:
        return pt
    warnings.warn(
        f"DATCOM SPANFO clamped to parent SSPN {parent_sspn:.3f}; "
        "stored control SPANFO unchanged.",
        DatcomInputWarning,
        stacklevel=3,
    )
    out = dict(pt)
    out["SPANFO"] = parent_sspn
    return out


def _planform_field(pt, key: str) -> float:
    if key == "SSPNOP":
        sspnop = float(pt.get("SSPNOP", 0.0))
        if sspnop:
            return float(pt.get("SSPN", 0.0)) - sspnop
        return 0.0
    val = float(pt.get(key, 0.0))
    if key == "SSPNE" and val < DATCOM_SSPNE_MIN:
        warnings.warn(
            f"DATCOM SSPNE clamped to {DATCOM_SSPNE_MIN}; stored planform SSPNE unchanged.",
            DatcomInputWarning,
            stacklevel=3,
        )
        return DATCOM_SSPNE_MIN
    return val


def write_wgplnf(pt, lines: list, label: str = "") -> None:
    """Append DATCOM $WGPLNF planform namelist matching DATCOM_IO.m."""
    name = label or "WGPLNF"
    parts = [f" ${name} "]
    for i, key in enumerate(_WGPLNF_RP, start=1):
        parts.append(f"{key}={_planform_field(pt, key):.2f},")
        if i % 4 == 0:
            parts.append("\n  ")
    parts.append("TYPE=1.0$")
    lines.append("".join(parts))


_SYMFLP_RF = (
    "SPANFI",
    "SPANFO",
    "CHRDFI",
    "CHRDFO",
    "FTYPE",
    "PHETE",
    "PHETEP",
    "TC",
    "CB",
)

_ASYFLP_RC = (
    "SPANFI",
    "SPANFO",
    "CHRDFI",
    "CHRDFO",
    "STYPE",
)


def _delta_list(vals) -> list:
    arr = _as_list(vals)
    if len(arr) > DATCOM_NDELTA_MAX:
        warnings.warn(
            f"DATCOM NDELTA capped at {DATCOM_NDELTA_MAX}; extra deflections omitted.",
            DatcomInputWarning,
            stacklevel=3,
        )
        arr = arr[:DATCOM_NDELTA_MAX]
    return arr


def write_symflp(pt: dict, lines: list) -> None:
    """Append DATCOM $SYMFLP namelist matching DATCOM_IO.m."""
    parts = [" $SYMFLP "]
    for i, key in enumerate(_SYMFLP_RF, start=1):
        parts.append(f"{key}={float(pt[key]):.3f},")
        if i == 4 and len(_SYMFLP_RF) > i:
            parts.append("\n  ")
    delta = _delta_list(pt["DELTA"])
    parts.append(f"\n  NDELTA={len(delta):.1f},")
    parts.append("DELTA=")
    parts.append(_fmt_values(delta, "%.1f,"))
    parts.append("$")
    lines.append("".join(parts))


def write_asyflp(pt: dict, lines: list) -> None:
    """Append DATCOM $ASYFLP namelist matching DATCOM_IO.m."""
    parts = [" $ASYFLP "]
    for i, key in enumerate(_ASYFLP_RC, start=1):
        parts.append(f"{key}={float(pt[key]):.3f},")
        if i == 4 and len(_ASYFLP_RC) > i:
            parts.append("\n  ")
    deltal = _delta_list(pt["DELTAL"])
    deltar = _delta_list(pt["DELTAR"])
    n = min(len(deltal), len(deltar), DATCOM_NDELTA_MAX)
    deltal, deltar = deltal[:n], deltar[:n]
    parts.append(f"NDELTA={len(deltal):.1f},")
    parts.append("\n  DELTAL=")
    parts.append(_fmt_values(deltal, "%.1f,"))
    parts.append("\n  DELTAR=")
    parts.append(_fmt_values(deltar, "%.1f,"))
    parts.append("$")
    lines.append("".join(parts))


def write_controls(ac: Aircraft, lines: list, *, ht_written: bool = True) -> None:
    """Append control namelists matching DATCOM_IO.m (even at zero deflection).

    Skip a namelist when SPANFO<=SPANFI (empty/inverted). Elevator is omitted
    if HT was omitted. SPANFO past the parent SSPN is still written, clamped
    to parent SSPN so Digital DATCOM does not SIGSEGV.
    """
    wg_sspn = float(ac.WG.get("SSPN", 0.0) or 0.0)
    if _control_is_datcom_legal(ac.F):
        write_symflp(_control_for_write(ac.F, wg_sspn), lines)
    else:
        warnings.warn(
            "DATCOM $SYMFLP flap omitted (illegal SPANFI/SPANFO); "
            "stored F unchanged.",
            DatcomInputWarning,
            stacklevel=2,
        )
    if _control_is_datcom_legal(ac.A):
        write_asyflp(_control_for_write(ac.A, wg_sspn), lines)
    else:
        warnings.warn(
            "DATCOM $ASYFLP aileron omitted (illegal SPANFI/SPANFO); "
            "stored A unchanged.",
            DatcomInputWarning,
            stacklevel=2,
        )
    if not ht_written:
        return
    if _control_is_datcom_legal(ac.E):
        ht_sspn = float(ac.HT.get("SSPN", 0.0) or 0.0)
        write_symflp(_control_for_write(ac.E, ht_sspn), lines)
    else:
        warnings.warn(
            "DATCOM elevator $SYMFLP omitted (illegal SPANFI/SPANFO); "
            "stored E unchanged.",
            DatcomInputWarning,
            stacklevel=2,
        )


def _cmp_enabled(plot_cmp, index: int) -> bool:
    """True if component index is on; missing/short plot_cmp pads True.

    Matches tornado_io._cmp_enabled and MATLAB DATCOM_IO.m cmp(i) defaults.
    Python plot_cmp is [wing, HT, VT, body] (JSON 0/1).
    """
    if plot_cmp is None or index >= len(plot_cmp):
        return True
    return bool(plot_cmp[index])


def write_for005(ac: Aircraft, path: Path, *, unit: str) -> None:
    """Assemble and write a full DATCOM for005 input file matching DATCOM_IO.m.

    Wing planform is always written. HT, VT, and body follow ``ac.plot_cmp``
    indices 1, 2, 3 (MATLAB cmp(2), cmp(3), cmp(4)).
    """
    lines: list[str] = []
    cmp = ac.plot_cmp
    if unit == "in":
        lines.append("DIM IN")
    lines.append(f"CASEID {path.stem}")
    write_fltcon(ac, lines)
    write_optins(ac, lines)
    write_synths(ac, lines)
    if _cmp_enabled(cmp, 3):
        write_body(ac, lines)
    lines.append(naca_wing_line(ac))
    write_wgplnf(ac.WG, lines)
    ht_written = False
    if _cmp_enabled(cmp, 1):
        if _planform_is_datcom_legal(ac.HT):
            lines.append(naca_ht_line(ac))
            write_wgplnf(ac.HT, lines, label="HTPLNF")
            ht_written = True
        else:
            warnings.warn(
                "DATCOM HT omitted (illegal SSPNE/SSPN/area); stored HT unchanged.",
                DatcomInputWarning,
                stacklevel=2,
            )
    if _cmp_enabled(cmp, 2):
        if _planform_is_datcom_legal(ac.VT):
            lines.append(naca_vt_line(ac))
            write_wgplnf(ac.VT, lines, label="VTPLNF")
        else:
            warnings.warn(
                "DATCOM VT omitted (illegal SSPNE/SSPN/area); stored VT unchanged.",
                DatcomInputWarning,
                stacklevel=2,
            )
    write_controls(ac, lines, ht_written=ht_written)
    lines.append("PLOT")
    lines.append("NEXT CASE")
    path.write_text("\n".join(lines))
