import argparse
import os
import sys
import glob
import csv
import numpy as np

from ase.io import read
from ase.io.trajectory import Trajectory
from ase.md.npt import NPT
# NVT: prefer Nose–Hoover chain; fallback to Berendsen if unavailable.
try:
    from ase.md.nose_hoover_chain import NoseHooverChainNVT as NVT_NHC
except Exception:
    NVT_NHC = None
try:
    from ase.md.nvtberendsen import NVTBerendsen as NVT_Ber
except Exception:
    NVT_Ber = None

from ase.md.logger import MDLogger
from ase.geometry import cellpar_to_cell
from ase.md.velocitydistribution import MaxwellBoltzmannDistribution, Stationary, ZeroRotation
import ase.units as u

from macer.calculator.mace import get_mace_calculator

# --- Defaults -----------------------------------------------------------------

# Unit conversion: 1 (eV/Å^3) = 160.21766208 GPa
EV_A3_TO_GPa = 160.21766208


def parse_poscar_header_for_xdatcar(poscar_path="POSCAR"):
    """Read species and counts from POSCAR header for XDATCAR blocks."""
    with open(poscar_path, "r") as f:
        lines = [next(f) for _ in range(7)]
    species = lines[5].split()
    counts = [int(x) for x in lines[6].split()]
    return species, counts


def get_md_parser():
    parser = argparse.ArgumentParser(
        description="Minimal NpT or NVT (NTE) MD with MACE + ASE (inputs: POSCAR; outputs: md.traj/md.log/XDATCAR/md.csv)",
        epilog="""
Examples:
  # NPT (Nose–Hoover barostat) — 600 K, 1 GPa, GPU (MPS), save every 100 steps
  macer md --ensemble npt --temp 600 --press 1.0 --ttau 100 --ptau 1000 --device mps --nsteps 20000 --save-every 100

  # NVT (NTE; prefers Nose–Hoover chain, falls back to Berendsen) — 600 K, 5000 steps
  macer md --ensemble nte --temp 600 --ttau 100 --nsteps 5000

  # Reproducible run (fixed seed) + adjusted print/save intervals
  macer md --ensemble npt --temp 300 --press 0.0 --ttau 100 --ptau 1000 --seed 42 --print-every 10 --save-every 100
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False # Don't add help here, main parser will handle it
    )

    parser.add_argument("--poscar", "-p", type=str, default="POSCAR",
                        help="Input POSCAR file (VASP format atomic structure input).")
    parser.add_argument("--model", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "mace-model", "mace-omat-0-small-fp32.model"), help="MACE model path")
    parser.add_argument("--device", choices=["cpu", "mps", "cuda"], default="cpu", help="compute device")
    parser.add_argument("--ensemble", choices=["npt", "nte"], default="npt",
                        help="MD ensemble: npt (Nose–Hoover barostat) or nte (=NVT; Nose–Hoover chain preferred, else Berendsen)")
    parser.add_argument("--temp", type=float, default=300.0, help="target temperature [K]")
    parser.add_argument("--press", type=float, default=0.0, help="target pressure [GPa] (NPT only)")
    parser.add_argument("--tstep", type=float, default=2.0, help="MD time step [fs]")
    parser.add_argument("--nsteps", type=int, default=20000, help="number of MD steps")
    parser.add_argument("--ttau", type=float, default=100.0, help="thermostat time constant [fs]")
    parser.add_argument("--ptau", type=float, default=1000.0, help="barostat time constant [fs] (NPT only)")
    parser.add_argument("--save-every", type=int, default=100, help="traj/log save interval")
    parser.add_argument("--xdat-every", type=int, default=1, help="XDATCAR write interval")
    parser.add_argument("--print-every", type=int, default=1, help="stdout print interval")
    parser.add_argument("--seed", type=int, default=None, help="random seed (None for random)")
    parser.add_argument("--csv", default="md.csv", help="CSV log path for MD outputs")
    parser.add_argument("--xdatcar", default="XDATCAR", help="XDATCAR path")
    parser.add_argument("--traj", default="md.traj", help="ASE trajectory path")
    parser.add_argument("--log", default="md.log", help="MD text log path")

    return parser


def run_md_simulation(args):
    # 0) Read input structure.
    atoms = read(args.poscar)

    # Upper-triangular cell is recommended for NPT (harmless for NVT; keeps cell normalized).
    tri_cell = cellpar_to_cell(atoms.cell.cellpar())
    atoms.set_cell(tri_cell, scale_atoms=True)
    atoms.pbc = True

    # Calculator.
    # get_mace_calculator now expects a list for model_paths
    atoms.calc = get_mace_calculator(model_paths=[args.model], device=args.device)

    # Initialize velocities; remove net translation and rotation.
    rng = (np.random.default_rng(args.seed) if args.seed is not None else None)
    MaxwellBoltzmannDistribution(atoms, temperature_K=args.temp, force_temp=True, rng=rng)
    Stationary(atoms)
    ZeroRotation(atoms)

    # 1) MD integrator setup.
    timestep = args.tstep * u.fs
    ttime = args.ttau * u.fs

    if args.ensemble == "npt":
        # NPT with Nose–Hoover barostat (ASE NPT).
        extstress = args.press * u.GPa
        pfact = (args.ptau * u.fs) ** 2 * u.GPa
        dyn = NPT(
            atoms,
            timestep=timestep,
            temperature_K=args.temp,
            externalstress=extstress,
            ttime=ttime,
            pfactor=pfact,
        )
    else:
        # NVT (NTE): prefer Nose–Hoover chain; fallback to Berendsen.
        if NVT_NHC is not None:
            dyn = NVT_NHC(
                atoms,
                timestep=timestep,
                temperature_K=args.temp,
                tdamp=ttime,  # thermostat damping time constant
            )
        elif NVT_Ber is not None:
            dyn = NVT_Ber(
                atoms,
                timestep=timestep,
                temperature_K=args.temp,
                taut=ttime,  # Berendsen thermostat time constant
            )
        else:
            raise ImportError(
                "NVT integrator not found in this ASE installation. "
                "Please install/update ASE with NoseHooverChainNVT or NVTBerendsen."
            )

    # 2) Logging: trajectory + text logger.
    traj = Trajectory(args.traj, "w", atoms)
    dyn.attach(traj.write, interval=args.save_every)
    logfile = open(args.log, "w")
    dyn.attach(MDLogger(dyn, atoms, logfile, header=True, stress=True, peratom=False),
               interval=args.save_every)

    # 3) XDATCAR setup.
    species, counts = parse_poscar_header_for_xdatcar(args.poscar)
    xdat_handle = open(args.xdatcar, "w")

    # 4) CSV (custom observables) setup.
    csv_handle = open(args.csv, "w", newline="")
    csv_writer = csv.writer(csv_handle)
    csv_writer.writerow(["step", "time_fs", "Epot_eV", "Ekin_eV", "Etot_eV", "T_K", "Vol_A3", "P_GPa", "H_eV"])

    # State & utilities.
    config_idx = 0
    step_counter = 0

    def write_xdatcar_block():
        """Append one XDATCAR configuration block from current Atoms state."""
        nonlocal config_idx
        config_idx += 1
        xdat_handle.write(" ".join(species) + "\n")
        xdat_handle.write("    1.000000\n")
        cell = atoms.cell.array
        for vec in cell:
            xdat_handle.write(f" {vec[0]:12.6f} {vec[1]:12.6f} {vec[2]:12.6f}\n")
        xdat_handle.write(" " + "              ".join(species) + "\n")
        xdat_handle.write("".join([f"{c:17d}" for c in counts]) + "\n")
        xdat_handle.write(f"Direct configuration= {config_idx:5d}\n")
        for s in atoms.get_scaled_positions(wrap=True):
            xdat_handle.write(f"   {s[0]:.8f}   {s[1]:.8f}   {s[2]:.8f}\n")

    def collect_observables():
        """Compute a set of common MD observables from the current state."""
        epot = atoms.get_potential_energy()
        ekin = atoms.get_kinetic_energy()
        etot = epot + ekin
        temp = atoms.get_temperature()
        vol = atoms.get_volume()
        sigma = atoms.get_stress(voigt=False)  # stress tensor in eV/Å^3
        p_eVa3 = -np.trace(sigma) / 3.0
        p_GPa = p_eVa3 * EV_A3_TO_GPa
        H = etot + p_eVa3 * vol  # enthalpy-like quantity (E + pV) in eV
        t_fs = step_counter * args.tstep
        return epot, ekin, etot, temp, vol, p_GPa, H, t_fs

    def print_status_line(epot, ekin, etot, temp, vol, p_GPa, H, t_fs):
        """Pretty single-line status for stdout."""
        print(
            f"Step{step_counter:7d} | t={t_fs:7.2f} fs | "
            f"Epot={epot: .6f} eV | Ekin={ekin: .6f} eV | Etot={etot: .6f} eV | "
            f"T={temp:7.2f} K | Vol={vol:8.3f} Å^3 | P={p_GPa: 7.4f} GPa | H={H: .6f} eV"
        )

    def write_csv_line(epot, ekin, etot, temp, vol, p_GPa, H, t_fs):
        """Append one row of observables to the CSV log."""
        csv_writer.writerow([step_counter, t_fs, epot, ekin, etot, temp, vol, p_GPa, H])

    # ▶ Initial (step 0) record: console + XDATCAR + CSV.
    epot, ekin, etot, temp, vol, p_GPa, H, t_fs = collect_observables()
    print_status_line(epot, ekin, etot, temp, vol, p_GPa, H, t_fs)
    write_xdatcar_block()
    write_csv_line(epot, ekin, etot, temp, vol, p_GPa, H, t_fs)
    step_counter += 1  # subsequent integration starts at step 1

    # Per-step callback.
    def on_step():
        """Callback executed every step."""
        nonlocal step_counter
        epot, ekin, etot, temp, vol, p_GPa, H, t_fs = collect_observables()
        if (step_counter % args.print_every) == 0:
            print_status_line(epot, ekin, etot, temp, vol, p_GPa, H, t_fs)
        if (step_counter % args.xdat_every) == 0:
            write_xdatcar_block()
        write_csv_line(epot, ekin, etot, temp, vol, p_GPa, H, t_fs)
        step_counter += 1

    dyn.attach(on_step, interval=1)

    # 5) Run MD.
    dyn.run(args.nsteps)

    # 6) Finalize.
    xdat_handle.close()
    csv_handle.close()
    print(f"Done ({args.ensemble.upper()} MD): outputs → {args.traj} / {args.log} / {args.xdatcar} / {args.csv}")
