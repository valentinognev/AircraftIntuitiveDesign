import numpy as np

from aid.aircraft import Aircraft
from aid.atmosphere import atmosphere

FT_M = 1.0 / 3.28084
_LB_TO_KG = 0.45359237
_SLUGFT3_TO_KGM3 = 515.379
_LBFT2S_TO_PAS = 47.880208


def ft_to_m(x: float) -> float:
    return x * FT_M


def ft2_to_m2(x: float) -> float:
    return x * FT_M**2


def lb_to_kg(x: float) -> float:
    return x * _LB_TO_KG


def _first(val) -> float:
    return float(np.asarray(val).reshape(-1)[0])


def polar_state(ac: Aircraft) -> dict:
    aero = ac.AERO
    mach = _first(aero["MACH"])
    alt_ft = _first(aero["ALT"])
    atm = atmosphere(alt_ft)

    rho_si = atm["D"] * _SLUGFT3_TO_KGM3
    mu_si = atm["V"] * _LBFT2S_TO_PAS

    return {
        "qinf_mps": mach * atm["a"] / 3.28084,
        "density": rho_si,
        "viscosity": mu_si / rho_si,
    }
