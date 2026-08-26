"""Parse AVL text output (stability derivatives, run cases, etc.)."""

import re
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


def parse_run_case_header(path: Path) -> dict:
    """Parse AVL run-case header (alpha, beta, totals, surface deflections).

    Port of ``parseRunCaseHeader.m``. Locates ``Run case:`` (case insensitive),
    extracts flight-condition and force/moment totals via ``find_value``, then
    reads control-surface names and deflection angles from lines after ``e =``.
    """
    lines = path.read_text().splitlines()
    area_end = len(lines) - 1

    for i, line in enumerate(lines):
        if "run case:" not in line.lower():
            continue

        area = (i, area_end)
        e_value, e_line = find_value(lines, "e =", area)
        result = {
            "alpha": _find_in_area(lines, "Alpha =", area),
            "beta": _find_in_area(lines, "Beta  =", area),
            "mach": _find_in_area(lines, "Mach  =", area),
            "pb2v": _find_in_area(lines, "pb/2V =", area),
            "qc2v": _find_in_area(lines, "qc/2V =", area),
            "rb2v": _find_in_area(lines, "rb/2V =", area),
            "ppb2v": _find_in_area(lines, "p'b/2V =", area),
            "rpb2v": _find_in_area(lines, "r'b/2V =", area),
            "CXtot": _find_in_area(lines, "CXtot =", area),
            "CYtot": _find_in_area(lines, "CYtot =", area),
            "CZtot": _find_in_area(lines, "CZtot =", area),
            "Cltot": _find_in_area(lines, "Cltot =", area),
            "Cmtot": _find_in_area(lines, "Cmtot =", area),
            "Cntot": _find_in_area(lines, "Cntot =", area),
            "Clptot": _find_in_area(lines, "Cl'tot", area),
            "Cnptot": _find_in_area(lines, "Cn'tot", area),
            "CLtot": _find_in_area(lines, "CLtot =", area),
            "CDtot": _find_in_area(lines, "CDtot =", area),
            "CDvis": _find_in_area(lines, "CDvis =", area),
            "CLff": _find_in_area(lines, "CLff  =", area),
            "CYff": _find_in_area(lines, "CYff  =", area),
            "CDind": _find_in_area(lines, "CDind =", area),
            "CDff": _find_in_area(lines, "CDff  =", area),
            "e": e_value,
            "surface": [],
        }

        j = e_line + 2
        while j < len(lines):
            surf_line = lines[j]
            name = "".join(re.findall(r"[a-z]", surf_line, re.IGNORECASE))
            if name:
                parts = surf_line.split("=", 1)
                angle_tokens = parts[1].split() if len(parts) > 1 else []
                angle = float(angle_tokens[0]) if angle_tokens else 0.0
                result["surface"].append({"name": name, "angle": angle})
            elif not surf_line:
                break
            j += 1

        return result

    return {}


def parse_sb(path: Path) -> dict:
    """Parse AVL geometry-axis stability derivatives from a ``.sb`` output file.

    Port of ``parseSB.m``. Locates ``Geometry-axis derivatives...`` (case
    insensitive), extracts CXu…Cnr via ``find_value``, then attaches control-
    surface deflection derivatives (CXdN, …) for surfaces from
    ``parse_run_case_header``.
    """
    lines = path.read_text().splitlines()
    area_end = len(lines) - 1

    for i, line in enumerate(lines):
        if "geometry-axis derivatives" not in line.lower():
            continue

        area = (i, area_end)
        result = {
            "CXu": _find_in_area(lines, "CXu =", area),
            "CYu": _find_in_area(lines, "CYu =", area),
            "CZu": _find_in_area(lines, "CZu =", area),
            "Clu": _find_in_area(lines, "Clu =", area),
            "Cmu": _find_in_area(lines, "Cmu =", area),
            "Cnu": _find_in_area(lines, "Cnu =", area),
            "CXv": _find_in_area(lines, "CXv =", area),
            "CYv": _find_in_area(lines, "CYv =", area),
            "CZv": _find_in_area(lines, "CZv =", area),
            "Clv": _find_in_area(lines, "Clv =", area),
            "Cmv": _find_in_area(lines, "Cmv =", area),
            "Cnv": _find_in_area(lines, "Cnv =", area),
            "CXw": _find_in_area(lines, "CXw =", area),
            "CYw": _find_in_area(lines, "CYw =", area),
            "CZw": _find_in_area(lines, "CZw =", area),
            "Clw": _find_in_area(lines, "Clw =", area),
            "Cmw": _find_in_area(lines, "Cmw =", area),
            "Cnw": _find_in_area(lines, "Cnw =", area),
            "CXp": _find_in_area(lines, "CXp =", area),
            "CYp": _find_in_area(lines, "CYp =", area),
            "CZp": _find_in_area(lines, "CZp =", area),
            "Clp": _find_in_area(lines, "Clp =", area),
            "Cmp": _find_in_area(lines, "Cmp =", area),
            "Cnp": _find_in_area(lines, "Cnp =", area),
            "CXq": _find_in_area(lines, "CXq =", area),
            "CYq": _find_in_area(lines, "CYq =", area),
            "CZq": _find_in_area(lines, "CZq =", area),
            "Clq": _find_in_area(lines, "Clq =", area),
            "Cmq": _find_in_area(lines, "Cmq =", area),
            "Cnq": _find_in_area(lines, "Cnq =", area),
            "CXr": _find_in_area(lines, "CXr =", area),
            "CYr": _find_in_area(lines, "CYr =", area),
            "CZr": _find_in_area(lines, "CZr =", area),
            "Clr": _find_in_area(lines, "Clr =", area),
            "Cmr": _find_in_area(lines, "Cmr =", area),
            "Cnr": _find_in_area(lines, "Cnr =", area),
            "surface": [],
        }

        rc = parse_run_case_header(path)
        for surf_idx, surf in enumerate(rc.get("surface", []), start=1):
            result["surface"].append(
                {
                    "name": surf["name"],
                    "CX": _find_in_area(lines, f"CXd{surf_idx} =", area),
                    "CY": _find_in_area(lines, f"CYd{surf_idx} =", area),
                    "CZ": _find_in_area(lines, f"CZd{surf_idx} =", area),
                    "Cl": _find_in_area(lines, f"Cld{surf_idx} =", area),
                    "Cm": _find_in_area(lines, f"Cmd{surf_idx} =", area),
                    "Cn": _find_in_area(lines, f"Cnd{surf_idx} =", area),
                }
            )

        return result

    return {"surface": []}
