import numpy as np


def tand(x):
    return np.tan(np.deg2rad(x))


def atand(x):
    return np.rad2deg(np.arctan(x))


def sind(x):
    return np.sin(np.deg2rad(x))


def cosd(x):
    return np.cos(np.deg2rad(x))


def geometry(pt: dict, angl: bool, type: str = "") -> dict:
    if pt.get("CHRDBP") and pt.get("SSPNOP"):
        raise NotImplementedError("break-span geometry not implemented (Task 30)")

    pt["b"] = pt["SSPN"] * 2
    pt["cbar"] = (pt["CHRDR"] + pt["CHRDTP"]) / 2
    pt["TR"] = pt["CHRDTP"] / pt["CHRDR"]
    pt["S"] = pt["b"] / 2 * pt["CHRDR"] * (1 + pt["TR"])
    pt["AR"] = pt["b"] ** 2 / pt["S"]

    swp = atand(
        tand(pt["SAVSI"])
        - 4 * (0 - pt["CHSTAT"]) * (1 - pt["TR"]) / (pt["AR"] * (1 + pt["TR"]))
    )
    pt["gamma"] = pt["DHDADI"]

    pt["Xtip"] = pt["X"] + pt["SSPN"] * tand(swp)
    if angl:
        if type == "v":
            pt["Xbrk"] = pt["X"]
            pt["Ybrk"] = pt["Z"]
            pt["Zbrk"] = pt["Y"]
            pt["Ytip"] = pt["Z"] + pt["SSPN"] * cosd(pt["DHDADI"])
            pt["Ztip"] = pt["Y"] + pt["SSPN"] * sind(pt["DHDADI"])
        else:
            pt["Xbrk"] = pt["X"]
            pt["Ybrk"] = pt["Y"]
            pt["Zbrk"] = pt["Z"]
            pt["Ytip"] = pt["Y"] + pt["SSPN"] * cosd(pt["DHDADI"])
            pt["Ztip"] = pt["Z"] + pt["SSPN"] * sind(pt["DHDADI"])
    else:
        if type == "v":
            pt["Xbrk"] = pt["X"]
            pt["Zbrk"] = pt["Y"]
            pt["Ztip"] = pt["Y"] + pt["SSPN"] * tand(pt["DHDADI"])
        else:
            pt["Xbrk"] = pt["X"]
            pt["Zbrk"] = pt["Z"]
            pt["Ztip"] = pt["Z"] + pt["SSPN"] * tand(pt["DHDADI"])

    swp_arr = np.atleast_1d(np.asarray(swp, dtype=float))
    tr = np.atleast_1d(np.asarray(pt["TR"], dtype=float))
    ar = np.atleast_1d(np.asarray(pt["AR"], dtype=float))
    n = swp_arr.size
    swp_matrix = np.zeros((4, n))
    swp_matrix[0, :] = np.real(swp_arr)
    swp_matrix[1, :] = np.real(
        atand(tand(swp_arr) - 4 * 0.25 * (1 - tr) / (ar * (1 + tr)))
    )
    swp_matrix[2, :] = np.real(
        atand(tand(swp_arr) - 4 * 0.5 * (1 - tr) / (ar * (1 + tr)))
    )
    swp_matrix[3, :] = np.real(
        atand(tand(swp_arr) - 4 * 1.0 * (1 - tr) / (ar * (1 + tr)))
    )
    pt["swp"] = swp_matrix

    tr_end = tr[-1]
    pt["ymac"] = pt["b"] / 6 * (1 + 2 * tr_end) / (1 + tr_end)
    if type == "v":
        pt["S"] = pt["S"] / 2
        pt["b"] = pt["b"] / 2
        pt["ymac"] = pt["ymac"] * 2
    pt["xmac"] = pt["ymac"] * tand(swp_matrix[0, -1])

    return pt
