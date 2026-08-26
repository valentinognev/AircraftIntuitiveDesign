"""Parse AVL text output (stability derivatives, run cases, etc.)."""

from pathlib import Path


def find_value(
    lines: list[str],
    name: str,
    area: str | tuple[int, int] = "",
) -> tuple[float, int]:
    """Find a numeric value after ``name`` in AVL output lines.

    Port of ``findValue.m``. Scans each line in ``area`` for ``name``; takes the
    remainder after the match, splits on spaces, and returns the first token that
    parses as a float (skipping ``=`` and other non-numeric tokens like MATLAB
    ``str2double`` → NaN).

    Parameters
    ----------
    lines:
        File contents as a list of lines (no trailing newlines required).
    name:
        Keyword to search for within each line (substring match).
    area:
        ``""`` searches all lines. A ``(start, end)`` tuple gives inclusive
        0-based line indices for bounded scans (e.g. parseST sections).

    Returns
    -------
    value, line
        Parsed float and 0-based line index. Returns ``(0.0, 0)`` when not found.
    """
    if area == "":
        start, end = 0, len(lines) - 1
    else:
        start, end = area

    for line_idx in range(start, end + 1):
        line = lines[line_idx]
        header = line.find(name)
        if header == -1:
            continue

        remainder = line[header + len(name) :]
        for token in remainder.split():
            if not token:
                continue
            try:
                return float(token), line_idx
            except ValueError:
                continue

    return 0.0, 0


def _find_in_area(lines: list[str], name: str, area: tuple[int, int]) -> float:
    value, _ = find_value(lines, name, area)
    return value


def parse_st(path: Path) -> dict:
    """Parse AVL stability-derivative section from a ``.st`` output file.

    Port of ``parseST.m``. Locates ``Stability-axis derivatives...`` (case
    insensitive), then extracts stability derivatives and neutral point via
    ``find_value``. Control-surface deflection derivatives are not parsed here
    (``surface`` is always ``[]`` until ``parseRunCaseHeader`` is ported).
    """
    lines = path.read_text().splitlines()
    area_end = len(lines) - 1

    for i, line in enumerate(lines):
        if "stability-axis derivatives" not in line.lower():
            continue

        area = (i, area_end)
        return {
            "CLa": _find_in_area(lines, "CLa =", area),
            "CYa": _find_in_area(lines, "CYa =", area),
            "Cla": _find_in_area(lines, "Cla =", area),
            "Cma": _find_in_area(lines, "Cma =", area),
            "Cna": _find_in_area(lines, "Cna =", area),
            "CLb": _find_in_area(lines, "CLb =", area),
            "CYb": _find_in_area(lines, "CYb =", area),
            "Clb": _find_in_area(lines, "Clb =", area),
            "Cmb": _find_in_area(lines, "Cmb =", area),
            "Cnb": _find_in_area(lines, "Cnb =", area),
            "CLp": _find_in_area(lines, "CLp =", area),
            "CYp": _find_in_area(lines, "CYp =", area),
            "Clp": _find_in_area(lines, "Clp =", area),
            "Cmp": _find_in_area(lines, "Cmp =", area),
            "Cnp": _find_in_area(lines, "Cnp =", area),
            "CLq": _find_in_area(lines, "CLq =", area),
            "CYq": _find_in_area(lines, "CYq =", area),
            "Clq": _find_in_area(lines, "Clq =", area),
            "Cmq": _find_in_area(lines, "Cmq =", area),
            "Cnq": _find_in_area(lines, "Cnq =", area),
            "CLr": _find_in_area(lines, "CLr =", area),
            "CYr": _find_in_area(lines, "CYr =", area),
            "Clr": _find_in_area(lines, "Clr =", area),
            "Cmr": _find_in_area(lines, "Cmr =", area),
            "Cnr": _find_in_area(lines, "Cnr =", area),
            "NP": _find_in_area(lines, "Xnp =", area),
            "surface": [],
        }

    return {"surface": []}
