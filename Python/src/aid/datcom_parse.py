"""Parse Digital DATCOM for006 / datcom.out stability tables."""

from __future__ import annotations

import math
import re

import numpy as np

ND = 99999.0
_MCC_RE = re.compile(r"CREST CRITICAL MACH\s*=\s*([0-9.]+)", re.IGNORECASE)
_BANNER_RE = re.compile(r"\*\*\*\s*(.+?)\s*\*\*\*")
_BANNER_SKIP = (
    "WING DATA FAIRING",
    "WING-BODY",
    "HORIZONTAL TAIL",
    "BODY-WING",
    "NDM PRINTED",
    "NA PRINTED",
    "VEHICLE WEIGHT",
    "LEVEL FLIGHT",
    "NOTE",
    "INPUT DATA CARDS",
)
_BANNER_ALERT = ("EXCEEDED", "ERROR", "FATAL", "INVALID")
_NUM_RE = re.compile(r"-?\d+\.?\d*(?:E[+-]?\d+)?")
_DERIV_NAMES = ("cla", "cma", "cyb", "cnb", "clb")
_COEF_NAMES = ("alpha", "cd", "cl", "cm", "cn", "ca", "xcp", *_DERIV_NAMES)
_ND_TOKENS = {"NDM", "ND", "NA"}
_SECTION_TITLES = (
    ("WING SECTION DEFINITION", "wing"),
    ("HORIZONTAL TAIL SECTION DEFINITION", "ht"),
    ("VERTICAL TAIL SECTION DEFINITION", "vt"),
)
_SECTION_FIELDS = (
    ("IDEAL ANGLE OF ATTACK", "alpha_ideal"),
    ("ZERO LIFT ANGLE OF ATTACK", "alpha_zl"),
    ("IDEAL LIFT COEFFICIENT", "cl_ideal"),
    ("ZERO LIFT PITCHING MOMENT COEFFICIENT", "cm0"),
    ("MACH ZERO LIFT-CURVE-SLOPE", "cla_mach0"),
    ("LEADING EDGE RADIUS", "le_radius"),
    ("MAXIMUM AIRFOIL THICKNESS", "t_c"),
    ("DELTA-Y", "delta_y"),
)


def parse_for006(text: str) -> dict:
    """Parse static-stability coefficient table from DATCOM output text."""
    lines = text.splitlines()
    header_idx = _find_stability_header(lines)
    mach, alt = _parse_flight_conditions(lines, header_idx)
    rows = _parse_stability_rows(lines, header_idx)
    if not rows:
        raise ValueError(_empty_table_message(text))

    result: dict = {"mach": mach, "alt": alt}
    for name in _COEF_NAMES:
        result[name] = np.array([row[name] for row in rows], dtype=float)
    downwash = _parse_downwash(lines)
    if downwash:
        result.update(downwash)
    high_lift = _parse_high_lift(lines)
    if high_lift:
        result["high_lift"] = high_lift
    sections = _parse_sections(lines)
    if sections:
        result["sections"] = sections
    return result


def datcom_method_warnings(text: str) -> list[str]:
    """User-facing DATCOM method-limit notes (crest-critical, similar banners).

    Ignores routine legends such as ``NDM PRINTED WHEN NO DATCOM METHODS EXIST``.
    """
    notes: list[str] = []
    seen: set[str] = set()
    for match in _BANNER_RE.finditer(text):
        body = " ".join(match.group(1).split())
        key = body.upper()
        if any(skip in key for skip in _BANNER_SKIP):
            continue
        if not any(tok in key for tok in _BANNER_ALERT):
            continue
        if key in seen:
            continue
        seen.add(key)
        notes.append(_humanize_method_banner(body, text))
    if _wing_body_fairing_nan(text):
        notes.append(
            "Transonic wing-body fairing is NaN. DATCOM uses transonic methods "
            "above Mach 0.6 (STMACH); this configuration has no transonic CL/Cm. "
            "Use Mach 0.6 or below for subsonic methods."
        )
    return notes


def datcom_user_warning(text: str, *, error: BaseException | None = None) -> str | None:
    """Dialog body when DATCOM has no usable table or flagged a method limit."""
    notes = datcom_method_warnings(text)
    if error is None and not notes:
        return None
    lines = ["DATCOM has no usable stability coefficients for this case."]
    lines.extend(notes)
    if error is not None and not notes:
        lines.append(str(error))
    return "\n\n".join(lines)


def _humanize_method_banner(body: str, text: str) -> str:
    if "CREST CRITICAL" in body.upper():
        mccs = [float(m) for m in _MCC_RE.findall(text)]
        if mccs:
            return (
                f"Crest critical Mach {min(mccs):.2f} exceeded: DATCOM has no "
                "transonic method for these sections at the flight Mach, so CL/Cm are NDM."
            )
    return body.strip() + "."


def _wing_body_fairing_nan(text: str) -> bool:
    idx = text.upper().find("WING-BODY DATA FAIRING")
    if idx < 0:
        return False
    return "NAN" in text[idx : idx + 500].upper()


def _empty_table_message(text: str) -> str:
    msg = "no finite coefficients (missing or ND)"
    if "CREST CRITICAL MACH NUMBER EXCEEDED" in text.upper():
        return msg + "; crest critical Mach exceeded"
    blob = text.upper()
    if "      NAN" in blob or "     INF" in blob or "INFINITY" in blob:
        return msg + "; DATCOM printed NaN/Inf in the stability table"
    return msg


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


def _float_tokens(line: str) -> list[float]:
    out: list[float] = []
    for tok in line.split():
        if tok.upper() in _ND_TOKENS:
            out.append(math.nan)
            continue
        try:
            out.append(float(tok))
        except ValueError:
            continue
    return out


def _parse_downwash(lines: list[str]) -> dict:
    header_idx = None
    for i, line in enumerate(lines):
        if "Q/QINF" in line.upper() and "EPSLON" in line.upper():
            header_idx = i
            break
    if header_idx is None:
        return {}
    alphas: list[float] = []
    qqi: list[float] = []
    eps: list[float] = []
    deps: list[float] = []
    for line in lines[header_idx + 1 :]:
        if line.startswith("0") and line.strip() not in ("0",):
            if alphas:
                break
            continue
        toks = _float_tokens(line)
        if len(toks) < 4:
            continue
        alphas.append(toks[0])
        qqi.append(toks[1])
        eps.append(toks[2])
        deps.append(toks[3])
    if not alphas:
        return {}
    return {
        "q_qinf": np.array(qqi, dtype=float),
        "epslon": np.array(eps, dtype=float),
        "depsda": np.array(deps, dtype=float),
    }


def _config_near(lines: list[str], idx: int) -> str:
    for j in range(idx, max(-1, idx - 12), -1):
        if "CONFIGURATION" in lines[j].upper():
            return " ".join(lines[j].split())
    return ""


def _parse_dcdi(lines: list[str], start: int) -> tuple[np.ndarray, np.ndarray, int]:
    alphas: list[float] = []
    dcdi: list[float] = []
    i = start
    while i < len(lines):
        line = lines[i]
        if "DELTA =" in line.upper():
            i += 1
            continue
        if line.startswith("0") and line.strip() not in ("0",):
            if alphas:
                break
            i += 1
            continue
        if "ALPHA" in line.upper() and not _float_tokens(line):
            i += 1
            continue
        toks = _float_tokens(line)
        if len(toks) >= 2:
            alphas.append(toks[0])
            dcdi.append(toks[1])
        elif alphas:
            break
        i += 1
    return np.array(alphas, dtype=float), np.array(dcdi, dtype=float), i


def _parse_high_lift(lines: list[str]) -> list[dict]:
    blocks: list[dict] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        body = line[2:] if line.startswith("0 ") else line
        if (
            "DELTA" in body.upper()
            and "D(CL)" in body.upper()
            and "D(CM)" in body.upper()
        ):
            config = _config_near(lines, i)
            row = None
            j = i + 1
            while j < len(lines):
                cand = lines[j]
                if "INDUCED DRAG" in cand.upper():
                    break
                toks = _float_tokens(cand)
                if len(toks) >= 5:
                    row = toks
                    break
                j += 1
            if row is None:
                i += 1
                continue
            clad = row[5] if len(row) > 5 else math.nan
            cha = row[6] if len(row) > 6 else math.nan
            chd = row[7] if len(row) > 7 else math.nan
            dcdi_alpha = np.array([], dtype=float)
            dcdi = np.array([], dtype=float)
            for k in range(j, min(j + 40, len(lines))):
                if "D(CDI)" in lines[k].upper() or "INDUCED DRAG" in lines[k].upper():
                    dcdi_alpha, dcdi, _ = _parse_dcdi(lines, k + 1)
                    break
            blocks.append(
                {
                    "config": config,
                    "delta": row[0],
                    "dcl": row[1],
                    "dcm": row[2],
                    "dcl_max": row[3],
                    "dcd_min": row[4],
                    "clad": clad,
                    "cha": cha,
                    "chd": chd,
                    "dcdi_alpha": dcdi_alpha,
                    "dcdi": dcdi,
                }
            )
            i = j + 1
            continue
        i += 1
    return blocks


def _value_after(label: str, block: str) -> float | None:
    idx = block.upper().find(label.upper())
    if idx < 0:
        return None
    rest = block[idx + len(label) :]
    eq = rest.find("=")
    if eq >= 0:
        rest = rest[eq + 1 :]
    toks = _float_tokens(rest)
    return toks[0] if toks else None


def _parse_sections(lines: list[str]) -> dict:
    text = "\n".join(lines)
    sections: dict = {}
    for title, key in _SECTION_TITLES:
        idx = text.upper().find(title)
        if idx < 0:
            continue
        chunk = text[idx : idx + 1200]
        fields: dict[str, float] = {}
        for label, name in _SECTION_FIELDS:
            val = _value_after(label, chunk)
            if val is not None:
                fields[name] = val
        xac = _value_after("XAC", chunk)
        if xac is not None:
            fields["xac"] = xac
        cla_m = None
        for line in chunk.splitlines():
            if "LIFT-CURVE-SLOPE" in line.upper() and "MACH ZERO" not in line.upper():
                cla_m = _value_after("LIFT-CURVE-SLOPE", line)
                break
        if cla_m is not None:
            fields["cla"] = cla_m
        if fields:
            sections[key] = fields
    return sections
