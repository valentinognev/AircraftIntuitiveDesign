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
