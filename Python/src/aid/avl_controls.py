"""AVL control derivatives at a probe deflection."""

import re
import tempfile
from copy import deepcopy
from pathlib import Path

from aid.aircraft import Aircraft
from aid.avl_io import _avl_spacing_attempts, run_avl, write_avl_geometry
from aid.avl_parse import find_value, parse_run_case_header, parse_sb
from aid.control_deriv import SURFACES, blank_row, iter_rows, with_probe
from aid.paths import avl_bin
from aid.tornado_io import tornado_io

_ALPHA_NEAR_ZERO_DEG = 1e-3
_BODY_TAGS = ("CX", "CY", "CZ", "Cl", "Cm", "Cn")
_DERIV_TAGS = _BODY_TAGS + ("CL",)
_BLOCK = {"flap": "F", "aileron": "A", "elevator": "E", "rudder": "R"}
_TAG_RE = re.compile(r"\b(CX|CY|CZ|CL|Cl|Cm|Cn)d(\d+)\s*=")


def _scalar(val) -> float:
    if isinstance(val, (list, tuple)):
        if not val:
            raise ValueError("empty")
        return _scalar(val[0])
    return float(val)


def _legal_surface(block: dict) -> bool:
    for key in ("SPANFI", "SPANFO", "CHRDFI", "CHRDFO"):
        if key not in block or block[key] is None:
            return False
    try:
        spanfi = _scalar(block["SPANFI"])
        spanfo = _scalar(block["SPANFO"])
        _scalar(block["CHRDFI"])
        _scalar(block["CHRDFO"])
    except (TypeError, ValueError):
        return False
    return spanfo > spanfi


def _normalize_deriv_tags(text: str) -> str:
    """Rewrite ``CXd01`` as ``CXd1`` so ``parse_sb``'s ``CXd{n}`` lookup hits."""

    def repl(match: re.Match) -> str:
        return f"{match.group(1)}d{int(match.group(2))} ="

    return _TAG_RE.sub(repl, text)


def _tagged_value(text: str, tag: str, index: int) -> float | None:
    match = re.search(
        rf"\b{re.escape(tag)}d0*{index}\s*=\s*"
        rf"([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)",
        text,
    )
    if match is None:
        return None
    return float(match.group(1))


def _surface_present(text: str, index: int) -> bool:
    return any(_tagged_value(text, tag, index) is not None for tag in _DERIV_TAGS)


def _header_names(text: str) -> list[str]:
    if "run case:" not in text.lower():
        return []
    with tempfile.NamedTemporaryFile(
        "w", suffix=".sb", delete=False, encoding="utf-8"
    ) as handle:
        handle.write(text)
        path = Path(handle.name)
    try:
        header = parse_run_case_header(path)
    finally:
        path.unlink(missing_ok=True)
    return [surf["name"] for surf in header.get("surface", [])]


def _sb_surfaces(text: str, order: list[str]) -> list[dict]:
    """Body-axis control columns from ``parse_sb``, in ``order``."""
    normalized = _normalize_deriv_tags(text)
    if "run case:" not in text.lower():
        preamble = ["Run case: probe", "e = 0", ""]
        preamble.extend(f"{name} = 0" for name in order)
        preamble.append("")
        normalized = "\n".join(preamble) + "\n" + normalized
    with tempfile.NamedTemporaryFile(
        "w", suffix=".sb", delete=False, encoding="utf-8"
    ) as handle:
        handle.write(normalized)
        path = Path(handle.name)
    try:
        parsed = parse_sb(path)
    finally:
        path.unlink(missing_ok=True)
    return list(parsed.get("surface", []))


def _body_value(text: str, parsed: dict | None, tag: str, index: int) -> float | None:
    scanned = _tagged_value(text, tag, index)
    if scanned is None:
        return None
    if parsed is not None and tag in parsed:
        stored = float(parsed[tag])
        if stored != 0.0 or scanned == 0.0:
            return stored
    return scanned


def rows_from_sb(
    sb_text: str,
    delta_deg: float,
    names: tuple[str, ...] = SURFACES,
) -> list[dict]:
    """CL uses a CLd line when present and otherwise -CZd at alpha near 0; .sb control columns are already per degree, and CD is -CX at alpha 0."""
    alpha, _ = find_value(sb_text.splitlines(), "Alpha =")
    near_zero = abs(alpha) <= _ALPHA_NEAR_ZERO_DEG
    order = _header_names(sb_text) or list(names)
    parsed = _sb_surfaces(sb_text, order)
    by_index = {i + 1: surf for i, surf in enumerate(parsed)}
    rows = []
    for name in names:
        if name not in order:
            rows.append(
                blank_row(name, float(delta_deg), available=False, reason="avl surface missing")
            )
            continue
        index = order.index(name) + 1
        if not _surface_present(sb_text, index):
            rows.append(
                blank_row(name, float(delta_deg), available=False, reason="avl surface missing")
            )
            continue
        surf = by_index.get(index)
        row = blank_row(name, float(delta_deg), available=True)
        cld = _tagged_value(sb_text, "CL", index)
        cz = _body_value(sb_text, surf, "CZ", index)
        if cld is not None:
            row["CL"] = cld
        elif near_zero and cz is not None:
            row["CL"] = -cz
        cx = _body_value(sb_text, surf, "CX", index)
        if near_zero and cx is not None:
            row["CD"] = -cx
        for tag in ("Cm", "CY", "Cl", "Cn"):
            value = _body_value(sb_text, surf, tag, index)
            if value is not None:
                row[tag] = value
        rows.append(row)
    # Deliberately no to_frd("avl", ...): these CY/Cl/Cn come straight out of the
    # .sb body-axis tags, which AVL already prints X fwd / Z down, so they are
    # Forward-Right-Down on arrival. Wrapping them by reflex would flip them twice.
    return rows


def _rewrite_control_cards(text: str) -> str:
    """Put the flap-chord fraction in Xhinge and keep aileron SgnDup at -1.

    ``write_avl_geometry`` stores that fraction in the gain slot and only five
    numbers, so AVL reads the trailing -1 as a vertical hinge component and
    leaves SgnDup at +1. Six numbers make the -1 the duplicate sign.
    """
    lines = []
    for line in text.splitlines():
        parts = line.split()
        if not parts or parts[0] not in {"flap", "aileron", "elevator", "rudder"}:
            lines.append(line)
            continue
        try:
            chord_fraction = float(parts[1])
        except ValueError:
            lines.append(line)
            continue
        xhinge = min(0.95, max(0.0, 1.0 - chord_fraction))
        sign = -1 if parts[0] == "aileron" else 1
        lines.append(f"{parts[0]} 1.0 {xhinge:.2f} 0 0 0 {sign}")
    trailing = "\n" if text.endswith("\n") else ""
    return "\n".join(lines) + trailing


def _control_names(avl_text: str) -> list[str]:
    lines = avl_text.splitlines()
    found: list[str] = []
    for i, line in enumerate(lines):
        if line.strip() != "CONTROL":
            continue
        if i + 1 >= len(lines):
            continue
        token = lines[i + 1].split()[0]
        if token not in found:
            found.append(token)
    return found


def write_avl_control_geometry(
    ac: Aircraft,
    run_dir,
    mesh,
    *,
    ni: int | None = None,
    nj: int | None = None,
    cspace: float | None = None,
    sspace: float | None = None,
) -> None:
    """Write ``geometry.avl`` with a CONTROL card for every legal surface."""
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    forced = deepcopy(ac)
    for surface in SURFACES:
        block = getattr(ac, _BLOCK[surface])
        if _legal_surface(block):
            forced = with_probe(forced, surface, 1.0)
    geo, state = tornado_io(forced, tuple(mesh))
    nj_use = int(mesh[0]) if nj is None else nj
    ni_use = int(mesh[1]) if ni is None else ni
    write_avl_geometry(
        forced,
        geo,
        state,
        run_dir,
        ni_use,
        nj_use,
        cspace=cspace,
        sspace=sspace,
    )
    avl_path = run_dir / "geometry.avl"
    avl_path.write_text(_rewrite_control_cards(avl_path.read_text(encoding="ascii")), encoding="ascii")


def write_avl_control_case(run_dir, delta_by_name: dict[str, float]) -> None:
    """Write ``geometry.run`` with one direct ``D{n}`` setting per defined control."""
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    lines = [
        "LOAD geometry.avl",
        "PLOP",
        "g",
        "",
        "OPER",
        "A A 0",
    ]
    index = 1
    for name in SURFACES:
        if name not in delta_by_name:
            continue
        lines.append(f"D{index} D{index} {float(delta_by_name[name]):.4f} ! {name}")
        index += 1
    lines.extend(
        [
            "x",
            "st",
            "geometry.st",
            "sb",
            "geometry.sb",
            "",
            "Quit",
            "",
        ]
    )
    (run_dir / "geometry.run").write_text("\n".join(lines), encoding="ascii")


def avl_controls(
    ac: Aircraft,
    deltas_deg=None,
    mesh: tuple[str, str] = ("10", "10"),
    run_dir=None,
) -> list[dict]:
    """One AVL process per probe angle when ``run_dir`` is omitted and the AVL binary exists."""
    pairs = iter_rows(deltas_deg)
    own_dir = run_dir is None
    cleanup = tempfile.TemporaryDirectory() if own_dir else None
    try:
        run_path = Path(cleanup.name) if cleanup is not None else Path(run_dir)
        ni = int(mesh[1])
        nj = int(mesh[0])
        attempts = _avl_spacing_attempts(ni, nj)
        write_avl_control_geometry(ac, run_path, mesh)
        defined = _control_names((run_path / "geometry.avl").read_text(encoding="ascii"))
        deltas: list[float] = []
        for _, delta in pairs:
            if delta not in deltas:
                deltas.append(delta)
        parsed: dict[tuple[str, float], dict] = {}
        run_binary = own_dir and avl_bin().is_file()
        spacing = attempts
        for delta in deltas:
            sb_text = ""
            if run_binary:
                for try_ni, try_nj, cspace, sspace in spacing:
                    write_avl_control_geometry(
                        ac,
                        run_path,
                        mesh,
                        ni=try_ni,
                        nj=try_nj,
                        cspace=cspace,
                        sspace=sspace,
                    )
                    defined = _control_names(
                        (run_path / "geometry.avl").read_text(encoding="ascii")
                    )
                    write_avl_control_case(
                        run_path, {name: float(delta) for name in defined}
                    )
                    for stale_name in ("geometry.st", "geometry.sb"):
                        stale = run_path / stale_name
                        if stale.is_file():
                            stale.unlink()
                    run_avl(run_path)
                    sb_path = run_path / "geometry.sb"
                    if sb_path.is_file():
                        sb_text = sb_path.read_text(encoding="utf-8")
                        spacing = [(try_ni, try_nj, cspace, sspace)]
                        break
            else:
                write_avl_control_case(
                    run_path, {name: float(delta) for name in defined}
                )
            if not sb_text:
                continue
            for row in rows_from_sb(sb_text, float(delta), names=tuple(defined)):
                parsed[(row["surface"], float(delta))] = row
        rows = []
        for surface, delta in pairs:
            block = getattr(ac, _BLOCK[surface])
            if not _legal_surface(block):
                rows.append(
                    blank_row(surface, float(delta), available=False, reason="illegal span")
                )
                continue
            row = parsed.get((surface, float(delta)))
            if row is None:
                rows.append(
                    blank_row(
                        surface,
                        float(delta),
                        available=False,
                        reason="avl surface missing",
                    )
                )
            else:
                rows.append(row)
        return rows
    finally:
        if cleanup is not None:
            cleanup.cleanup()
