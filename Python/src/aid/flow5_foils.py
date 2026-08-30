import re

from aid.aircraft import Aircraft


def naca_digits(code: str) -> int:
    matches = re.findall(r"\d{3,5}", code)
    if not matches:
        raise ValueError(f"No NACA digits in {code!r}")
    return int(matches[-1])


def _cmp_enabled(plot_cmp: list, index: int) -> bool:
    if index >= len(plot_cmp):
        return True
    return bool(plot_cmp[index])


def _foil_from_planform(pt: dict) -> dict | None:
    naca = pt.get("NACA")
    if naca is None:
        return None
    code = naca[0] if isinstance(naca, (list, tuple)) else naca
    try:
        digits = naca_digits(str(code))
    except ValueError:
        return None
    return {"name": f"NACA {digits}", "naca": digits}


def foils_for_aircraft(ac: Aircraft) -> list[dict]:
    cmp = ac.plot_cmp
    seen: set[int] = set()
    foils: list[dict] = []

    def add(pt: dict | None) -> None:
        if not pt:
            return
        foil = _foil_from_planform(pt)
        if foil is None or foil["naca"] in seen:
            return
        seen.add(foil["naca"])
        foils.append(foil)

    if _cmp_enabled(cmp, 0):
        add(ac.WG)
    if _cmp_enabled(cmp, 1):
        add(ac.HT)
    if _cmp_enabled(cmp, 2):
        add(ac.VT)

    for i in range(min(3, len(ac.NP))):
        np_pt = ac.NP[i]
        if np_pt and _cmp_enabled(cmp, 4 + i):
            add(np_pt)

    return foils
