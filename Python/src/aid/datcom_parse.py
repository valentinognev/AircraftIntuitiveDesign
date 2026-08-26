"""Parse Digital DATCOM for006 / datcom.out stability tables."""

from __future__ import annotations

import re

import numpy as np

ND = 99999.0
_NUM_RE = re.compile(r"-?\d+\.?\d*(?:E[+-]?\d+)?")
_DERIV_NAMES = ("cla", "cma", "cyb", "cnb", "clb")
_COEF_NAMES = ("alpha", "cd", "cl", "cm", "cn", "ca", *_DERIV_NAMES)


def parse_for006(text: str) -> dict:
    """Parse static-stability coefficient table from DATCOM output text."""
    lines = text.splitlines()
    header_idx = _find_stability_header(lines)
    mach, alt = _parse_flight_conditions(lines, header_idx)
    rows = _parse_stability_rows(lines, header_idx)
    if not rows:
        raise ValueError("no stability data rows found")

    result: dict = {"mach": mach, "alt": alt}
    for name in _COEF_NAMES:
        result[name] = np.array([row[name] for row in rows], dtype=float)
    return result


def _find_stability_header(lines: list[str]) -> int:
    for i, line in enumerate(lines):
        body = line[2:] if line.startswith("0 ") else line
        if (
            re.search(r"\bALPHA\b", body)
            and re.search(r"\bCD\b", body)
            and re.search(r"\bCL\b", body)
            and re.search(r"\bCM\b", body)
        ):
            return i
    raise ValueError("stability table header not found")


def _parse_flight_conditions(lines: list[str], header_idx: int) -> tuple[float, float]:
    for i in range(header_idx - 1, max(-1, header_idx - 25), -1):
        if "MACH" not in lines[i] or "ALTITUDE" not in lines[i]:
            continue
        for j in range(i + 1, header_idx):
            line = lines[j]
            if not line.startswith("0 "):
                continue
            parts = line[2:].split()
            if len(parts) < 2:
                continue
            try:
                return float(parts[0]), float(parts[1])
            except ValueError:
                continue
    raise ValueError("flight conditions not found")


def _parse_stability_rows(lines: list[str], header_idx: int) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    for line in lines[header_idx + 1 :]:
        if line.startswith("0"):
            if line.strip() == "0":
                continue
            break
        row = _parse_data_row(line)
        if row is not None:
            rows.append(row)
    return rows


def _parse_data_row(line: str) -> dict[str, float] | None:
    tokens = [float(m.group()) for m in _NUM_RE.finditer(line)]
    if len(tokens) < 7:
        return None

    row: dict[str, float] = dict(
        zip(("alpha", "cd", "cl", "cm", "cn", "ca", "xcp"), tokens[:7])
    )
    deriv = tokens[7:]
    if len(deriv) == 5:
        for name, value in zip(_DERIV_NAMES, deriv):
            row[name] = value
    elif len(deriv) == 3:
        row["cla"], row["cma"], row["clb"] = deriv
        row["cyb"] = row["cnb"] = ND
    else:
        for j, name in enumerate(_DERIV_NAMES):
            row[name] = deriv[j] if j < len(deriv) else ND
    return row
