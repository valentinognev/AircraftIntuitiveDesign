from aid.viz import _as_airfoils


def mesh_fields(ac, solver: str) -> tuple[list[str], list[str]]:
    prompts = ["Spanwise Nodes", "Chordwise Nodes"]
    if solver == "tornado":
        defaults = ["10", "5"]
        twist_def, foil_def = "2", "3"
    elif solver == "avl":
        defaults = ["10", "10"]
        twist_def, foil_def = "1", "1"
    elif solver == "flow5":
        defaults = ["10", "10"]
        twist_def, foil_def = "1", "1"
    else:
        raise ValueError(solver)
    if ac.WG.get("TWISTA"):
        prompts.append("Twist Linearity")
        defaults.append(twist_def)
    if len(_as_airfoils(ac.WG.get("DATA"))) > 1:
        prompts.append("Airfoil Interpolation Linearity")
        defaults.append(foil_def)
    return prompts, defaults
