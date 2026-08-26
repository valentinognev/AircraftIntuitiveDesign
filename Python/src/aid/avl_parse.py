"""Parse AVL text output (stability derivatives, run cases, etc.)."""


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
