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
        pt["b"] = pt["SSPN"] * 2
        cr, cb, ct = pt["CHRDR"], pt["CHRDBP"], pt["CHRDTP"]

        tr_i = cb / cr
        cbar_i = 2 / 3 * cr * (1 + tr_i + tr_i**2) / (1 + tr_i)
        b_i = 2 * pt["SSPNOP"]
        s_i = (cr + cb) / 2 * b_i
        ar_i = b_i**2 / s_i
        swp_i = atand(
            tand(pt["SAVSI"])
            - 4 * (-pt["CHSTAT"]) * (1 - tr_i) / (ar_i * (1 + tr_i))
        )

        tr_o = ct / cb
        cbar_o = 2 / 3 * cb * (1 + tr_o + tr_o**2) / (1 + tr_o)
        b_o = 2 * (pt["SSPN"] - pt["SSPNOP"])
        s_o = (cb + ct) / 2 * b_o
        ar_o = b_o**2 / s_o
        swp_o = atand(
            tand(pt["SAVSO"])
            - 4 * (-pt["CHSTAT"]) * (1 - tr_o) / (ar_o * (1 + tr_o))
        )

        pt["S"] = [s_i, s_o, s_i + s_o]
        pt["AR"] = [ar_i, ar_o, pt["b"] ** 2 / pt["S"][-1]]
        pt["cbar"] = [cbar_i, cbar_o, (cbar_i * s_i + cbar_o * s_o) / pt["S"][-1]]

        k = 3 * pt["b"] * pt["cbar"][-1] / (4 * pt["S"][-1])
        a = 1 - k
        b_quad = 1 - 2 * k
        c = 1 - k
        disc = b_quad**2 - 4 * a * c
        if cbar_o > cbar_i:
            tr_equiv = (-b_quad + np.sqrt(disc)) / (2 * a)
        else:
            tr_equiv = (-b_quad - np.sqrt(disc)) / (2 * a)
        pt["TR"] = [tr_i, tr_o, tr_equiv]

        swp = [swp_i, swp_o, (swp_i * b_i + swp_o * b_o) / pt["b"]]
        pt["gamma"] = (pt["DHDADI"] * b_i + pt["DHDADO"] * b_o) / pt["b"]

        pt["Xbrk"] = pt["X"] + b_i / 2 * tand(swp_i)
        pt["Xtip"] = pt["Xbrk"] + b_o / 2 * tand(swp_o)
        if angl:
            if type == "v":
                pt["Ybrk"] = pt["Z"] + b_i / 2 * cosd(pt["DHDADI"])
                pt["Zbrk"] = pt["Y"] + b_i / 2 * sind(pt["DHDADI"])
            else:
                pt["Ybrk"] = pt["Y"] + b_i / 2 * cosd(pt["DHDADI"])
                pt["Zbrk"] = pt["Z"] + b_i / 2 * sind(pt["DHDADI"])
            pt["Ytip"] = pt["Ybrk"] + b_o / 2 * cosd(pt["DHDADO"])
            pt["Ztip"] = pt["Zbrk"] + b_o / 2 * sind(pt["DHDADO"])
        else:
            if type == "v":
                pt["Zbrk"] = pt["Y"] + b_i / 2 * tand(pt["DHDADI"])
            else:
                pt["Zbrk"] = pt["Z"] + b_i / 2 * tand(pt["DHDADI"])
            pt["Ybrk"] = pt["SSPNOP"]
            pt["Ytip"] = pt["SSPN"]
            pt["Ztip"] = pt["Zbrk"] + b_o / 2 * tand(pt["DHDADO"])

    else:
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
