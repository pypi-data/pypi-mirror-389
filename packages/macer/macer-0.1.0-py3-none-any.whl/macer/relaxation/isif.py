import numpy as np
from ase.constraints import FixAtoms
from ase.filters import UnitCellFilter, StrainFilter, ExpCellFilter

def build_axis_mask(fix_axis: list[str]):
    mask = np.ones((3, 3), dtype=bool)
    for ax in fix_axis:
        if ax.lower() == "a": mask[0, :] = False
        elif ax.lower() == "b": mask[1, :] = False
        elif ax.lower() == "c": mask[2, :] = False
    return mask

def get_relax_target(atoms, isif: int, fix_axis: list[str]):
    if isif == 0:
        print(" ISIF=0 → Single-point calculation.")
        return atoms
    elif isif == 1:
        print(" ISIF=1 → Stress evaluation only.")
        atoms.set_constraint(FixAtoms(range(len(atoms))))
        return atoms
    elif isif == 2:
        print(" ISIF=2 → Relax atomic positions only.")
        return atoms
    elif isif == 3:
        print("️ ISIF=3 → Relax atoms + full cell (volume & shape).")
        mask = build_axis_mask(fix_axis)
        print(f" Fixed axes: {', '.join(fix_axis).upper() or '(none)'}")
        return UnitCellFilter(atoms, mask=mask)
    elif isif == 4:
        print("️ ISIF=4 → Relax cell only.")
        atoms.set_constraint(FixAtoms(range(len(atoms))))
        return UnitCellFilter(atoms, mask=build_axis_mask(fix_axis))
    elif isif == 5:
        print("️ ISIF=5 → Relax atoms + shape (volume fixed).")
        return ExpCellFilter(atoms, mask=build_axis_mask(fix_axis))
    elif isif == 6:
        print("️ ISIF=6 → Relax atoms + volume (shape fixed).")
        return StrainFilter(atoms, mask=build_axis_mask(fix_axis))
    elif isif == 7:
        print("️ ISIF=7 → Relax atoms + anisotropic shape.")
        return ExpCellFilter(atoms, mask=build_axis_mask(fix_axis))
    else:
        raise ValueError("Unsupported ISIF. Choose 0–7.")
