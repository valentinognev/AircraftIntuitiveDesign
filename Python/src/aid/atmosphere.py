import math


def atmosphere(h_ft: float) -> dict:
    h = h_ft
    if h <= 36089:
        theta = 1 - h / 145442
        delta = (1 - h / 145442) ** 5.255876
        sigma = (1 - h / 145442) ** 4.255876
    elif h <= 65617:
        theta = 0.751865
        delta = 0.223361 * math.exp(-(h - 36089) / 20806)
        sigma = 0.297076 * math.exp(-(h - 36089) / 20806)
    elif h <= 104987:  # Inversion
        theta = 0.682457 + h / 945374
        delta = (0.988626 + h / 652600) ** -34.16320
        sigma = (0.978261 + h / 659515) ** -35.16320
    elif h <= 154199:  # Inversion
        theta = 0.482561 + h / 337634
        delta = (0.898309 + h / 181373) ** -12.20114
        sigma = (0.857003 + h / 190115) ** -13.20114
    elif h <= 167323:  # Isothermal
        theta = 0.939268
        delta = 0.00109456 * math.exp(-(h - 154199) / 25992)
        sigma = 0.00116533 * math.exp(-(h - 154199) / 25992)
    elif h <= 232940:
        theta = 1.434843 - h / 337634
        delta = (0.838263 - h / 577922) ** 12.20114
        sigma = (0.798990 - h / 606330) ** 11.20114
    elif h <= 278386:
        theta = 1.237723 - h / 472687
        delta = (0.917131 - h / 637919) ** 17.08160
        sigma = (0.900194 - h / 649922) ** 16.08160
    else:
        theta = 0
        delta = 0
        sigma = 0

    T_0 = 518.69  # R
    P_0 = 2116.22  # psf
    D_0 = 0.002377  # slug/ft^3
    V_0 = 3.62e-7  # lb*s/ft^2

    T = T_0 * theta
    P = P_0 * delta
    D = D_0 * sigma
    V = V_0 * theta ** 1.5 * 717.42 / (T + 198.72)
    a = math.sqrt(1.4 * 1716 * T)

    return {"T": T, "P": P, "D": D, "V": V, "a": a}
