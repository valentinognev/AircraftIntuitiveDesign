import numpy as np

from aid.aircraft import Aircraft


def _last(val) -> float:
    return float(np.asarray(val).reshape(-1)[-1])


def _as_list(value):
    if isinstance(value, (list, tuple)):
        return list(value)
    return [value]


def _fmt_values(values, fmt):
    return "".join(fmt % v for v in values)


def _write_namelist_array(parts, name, vals, fmt):
    """Append one DATCOM namelist array (12 + 6 continuation) matching write_namelist_array."""
    first_lim = 12
    cont_lim = 6
    arr = np.asarray(vals, dtype=float).reshape(-1)
    n = arr.size
    if n > first_lim + cont_lim:
        idx = np.round(np.linspace(0, n - 1, first_lim + cont_lim)).astype(int)
        arr = arr[idx]
        n = arr.size
    parts.append(f"\n  {name}=")
    chunk_end = min(first_lim, n)
    parts.append(_fmt_values(arr[:chunk_end], fmt))
    if chunk_end < n:
        parts.append("\n  ")
        parts.append(_fmt_values(arr[chunk_end : chunk_end + cont_lim], fmt))


def write_fltcon(ac: Aircraft, lines: list) -> None:
    """Append DATCOM $FLTCON namelist lines matching DATCOM_IO.m."""
    aero = ac.AERO
    alschd = _as_list(aero["ALSCHD"])
    alt = _as_list(aero["ALT"])
    mach = _as_list(aero["MACH"])
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
    body_max = 18
    if body["NX"] > body_max:
        idx = np.round(np.linspace(0, int(body["NX"]) - 1, body_max)).astype(int)
        for key in ("X", "ZU", "ZL", "R", "P", "S"):
            body[key] = np.asarray(body[key], dtype=float)[idx].tolist()
        body["NX"] = body_max

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
    parts.append("$")
    lines.append("".join(parts))


def naca_wing_line(ac: Aircraft) -> str:
    """Return NACA-W card string from WG.NACA matching DATCOM_IO.m."""
    naca = ac.WG["NACA"]
    if isinstance(naca, (list, tuple)):
        naca = naca[0]
    return f"NACA-W-{len(naca)}-{naca}"


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


def _planform_field(pt, key: str) -> float:
    if key == "SSPNOP":
        sspnop = float(pt.get("SSPNOP", 0.0))
        if sspnop:
            return float(pt.get("SSPN", 0.0)) - sspnop
        return 0.0
    return float(pt.get(key, 0.0))


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


def _has_nonzero(vals) -> bool:
    arr = np.asarray(vals, dtype=float).reshape(-1)
    return bool(np.any(arr != 0))


def write_symflp(pt: dict, lines: list) -> None:
    """Append DATCOM $SYMFLP namelist matching DATCOM_IO.m."""
    parts = [" $SYMFLP "]
    for i, key in enumerate(_SYMFLP_RF, start=1):
        parts.append(f"{key}={float(pt[key]):.3f},")
        if i == 4 and len(_SYMFLP_RF) > i:
            parts.append("\n  ")
    delta = _as_list(pt["DELTA"])
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
    deltal = _as_list(pt["DELTAL"])
    deltar = _as_list(pt["DELTAR"])
    parts.append(f"NDELTA={len(deltal):.1f},")
    parts.append("\n  DELTAL=")
    parts.append(_fmt_values(deltal, "%.1f,"))
    parts.append("\n  DELTAR=")
    parts.append(_fmt_values(deltar, "%.1f,"))
    parts.append("$")
    lines.append("".join(parts))


def write_controls(ac: Aircraft, lines: list) -> None:
    """Append control namelists when deflections are nonzero (batch, not wing-only)."""
    if _has_nonzero(ac.F.get("DELTA", 0)):
        write_symflp(ac.F, lines)
    if _has_nonzero(ac.A.get("DELTAL", 0)) or _has_nonzero(ac.A.get("DELTAR", 0)):
        write_asyflp(ac.A, lines)
    e = ac.E
    if _has_nonzero(e.get("DELTA", 0)) and float(e.get("SPANFI", 0)) >= 0.01:
        write_symflp(e, lines)
