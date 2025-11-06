import os
import numpy as np
from ase.io import read, write
from ase.optimize import FIRE
from ase.io.trajectory import Trajectory
from ase import Atoms # Added import

from macer.calculator.mace import get_mace_calculator
from macer.relaxation.isif import get_relax_target
from macer.io.writers import (
    write_outcar, write_vasprun_xml, write_calc_results_json
)
from macer.io.plotting import plot_relaxation_log

def relax_structure(
    input_file, fmax=0.01, smax=0.001, # Removed default "POSCAR"
    device="cpu", isif=2, fix_axis=None,
    quiet=False, contcar_name="CONTCAR",
    outcar_name="OUTCAR", xml_name="vasprun-mace.xml",
    make_pdf=True, write_json=False, model_path=None
):
    if isinstance(input_file, Atoms):
        atoms = input_file
        # If input is an Atoms object, we need a prefix for output files.
        # Use a tag if available, otherwise a generic one.
        prefix = atoms.info.get('tag', 'relaxed_structure')
        output_dir = "." # Default output directory to current if Atoms object
        if not quiet:
            print(f" Loaded structure from Atoms object ({len(atoms)} atoms)")
    else:
        atoms = read(input_file)
        prefix = os.path.basename(input_file)
        output_dir = os.path.dirname(input_file) or "."
        if not quiet:
            print(f" Loaded structure from {input_file} ({len(atoms)} atoms)")
    
    if model_path:
        calc = get_mace_calculator(model_paths=[model_path], device=device)
    else:
        calc = get_mace_calculator(model_paths=None, device=device)
    atoms.calc = calc
    target = get_relax_target(atoms, isif, fix_axis or [])

    energies, steps, forces_hist, stress_hist = [], [], [], []

    if isif in (0, 1):
        e = atoms.get_potential_energy()
        write_outcar(atoms, e, outcar_name)
        write_vasprun_xml(atoms, e, xml_name)
        if write_json:
            write_calc_results_json(atoms, e, filename=os.path.join(output_dir, "calc_results.json"))
        write(contcar_name, atoms, format="vasp")
    else:
        if not quiet:
            print(f"⚙️  Starting FIRE relaxation (fmax={fmax:.4f} eV/Å, smax={smax:.4f} eV/Å³, ISIF={isif})")

        # Ensure trajectory file is written to output_dir
        traj_path = os.path.join(output_dir, f"relax-{prefix}.traj")
        with Trajectory(traj_path, "w", target) as traj:
            opt = FIRE(target, maxstep=0.1, dt=0.1, trajectory=traj)

            def log_callback():
                e = atoms.get_potential_energy()
                fmax_cur = np.abs(atoms.get_forces()).max()
                stress_cur = np.abs(atoms.get_stress()).max() if isif >= 3 else 0.0
                steps.append(len(steps))
                energies.append(e)
                forces_hist.append(fmax_cur)
                stress_hist.append(stress_cur)
                print(f" Step {len(steps):4d} | E = {e:.6f} eV | Fmax={fmax_cur:.5f} | σmax={stress_cur:.5f}")
                if fmax_cur < fmax and (isif < 3 or stress_cur < smax):
                    print("✅ Converged: force & stress thresholds satisfied.")
                    if hasattr(opt, "stop"):
                        opt.stop()
                    else:
                        raise SystemExit

            opt.attach(log_callback, interval=1)
            try:
                opt.run(fmax=fmax)
            except SystemExit:
                pass

        e = atoms.get_potential_energy()
        write(contcar_name, atoms, format="vasp")
        write_outcar(atoms, e, outcar_name)
        write_vasprun_xml(atoms, e, xml_name)
        if write_json:
            write_calc_results_json(atoms, e, filename=os.path.join(output_dir, "calc_results.json"))

    if make_pdf:
        plot_relaxation_log(prefix, output_dir, energies, steps, forces_hist, stress_hist, isif, atoms)
    
    return atoms # Return the relaxed atoms object
