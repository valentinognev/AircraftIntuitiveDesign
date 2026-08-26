from aid.aircraft import Aircraft


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
