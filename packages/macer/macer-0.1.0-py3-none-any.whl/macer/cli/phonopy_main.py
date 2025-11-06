import argparse
import sys
import os
from pathlib import Path

from macer.phonopy.relax_unit import run_relax_unit
from macer.phonopy.phonon_band import _generate_band_conf, run_macer_workflow # Updated import

def _call_run_macer_workflow(args):
    """
    Helper function to adapt parsed arguments to run_macer_workflow.
    Handles multiple input POSCAR files.
    """
    original_cwd = os.getcwd()
    is_plusminus_val = 'auto'
    if args.is_plusminus: # Check for --pm flag
        is_plusminus_val = True
    
    is_diagonal_val = True
    if not args.is_diagonal: # Check for --nodiag flag
        is_diagonal_val = False

    for filepath_str in args.input_files:
        input_path = Path(filepath_str).resolve()
        output_dir = input_path.parent
        output_dir.mkdir(exist_ok=True)

        model_path_abs = Path(args.model).resolve() if args.model else None

        try:
            os.chdir(output_dir)
            run_macer_workflow(
                input_path=input_path,
                min_length=args.length,
                displacement_distance=args.amplitude,
                is_plusminus=is_plusminus_val,
                    is_diagonal=args.is_diagonal,
                macer_device=args.device,
                # Arguments for _generate_band_conf
                yaml_path_arg=args.yaml,
                out_path_arg=args.out,
                gamma_label=args.gamma,
                symprec_seekpath=args.symprec,
                dim_override=args.dim,
                no_defaults_band_conf=args.no_defaults,
                atom_names_override=args.atom_names,
                rename_override=args.rename,
                tolerance=args.tolerance,
            )
        finally:
            os.chdir(original_cwd)

def main():
    parser = argparse.ArgumentParser(
        description="macer_phonopy: Phonopy-related utilities for MACE-based calculations.",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # relax-unit command (unchanged)
    relax_unit_parser = subparsers.add_parser(
        "relax-unit", aliases=["ru"],
        description="Iteratively relax and symmetrize a unit cell using MACE and spglib.",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    relax_unit_parser.add_argument("--poscar", "-p", type=str, default="POSCAR",
                                   help="Input POSCAR file.")
    relax_unit_parser.add_argument("--model", type=str, default=None,
                                   help="Path to the MACE model file. Defaults to the bundled mace-omat-0-small-fp32.model.")
    relax_unit_parser.add_argument("--device", type=str, default="cpu", choices=["cpu", "mps", "cuda"],
                                   help="Compute device for MACE (cpu, mps, or cuda).")
    relax_unit_parser.add_argument("--tolerance", type=float, default=0.01,
                                   help="Symmetry tolerance for spglib (in Angstrom).")
    relax_unit_parser.add_argument("--tolerance-sym", type=float, default=None,
                                   help="Symmetry tolerance for space group detection (in Angstrom). If not set, uses --tolerance.")
    relax_unit_parser.add_argument("--max-iterations", type=int, default=10,
                                   help="Maximum number of relaxation-symmetrization iterations.")
    relax_unit_parser.add_argument("--fmax", type=float, default=0.01,
                                   help="Force convergence threshold for relaxation (eV/Å).")
    relax_unit_parser.add_argument("--smax", type=float, default=0.001,
                                   help="Stress convergence threshold for relaxation (eV/Å³).")
    relax_unit_parser.add_argument("--quiet", action="store_true",
                                   help="Suppress verbose output during relaxation steps.")
    relax_unit_parser.add_argument("--output-prefix", type=str, default=None,
                                   help="Prefix for output files (e.g., final-symmetrized.vasp). Defaults to input POSCAR filename.")
    relax_unit_parser.set_defaults(func=run_relax_unit)

    # band-path command (modified)
    phonon_band_parser = subparsers.add_parser(
        "phonon-band", aliases=["pb"],
        description="Full phonopy workflow using macer for phonon dispersion calculation, including band.conf generation.",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    # Arguments from scripts/run_macer_phonopy.py
    phonon_band_parser.add_argument(
        "-p", "--poscar",
        dest="input_files",
        required=True,
        nargs='+',
        help="One or more input cell files in VASP POSCAR format."
    )
    phonon_band_parser.add_argument(
        "-l", "--length",
        type=float,
        default=20.0,
        help="Minimum length of supercell lattice vectors in Angstroms (default: 20.0)"
    )
    phonon_band_parser.add_argument(
        "--amplitude",
        type=float,
        default=0.01,
        help="Displacement amplitude in Angstroms (default: 0.01)"
    )
    phonon_band_parser.add_argument(
        '--tolerance',
        type=float,
        default=1e-3,
        help='Symmetry tolerance for spglib in macer_phonopy ru (default: 1e-3)'
    )
    phonon_band_parser.add_argument(
        '--pm',
        dest='is_plusminus',
        action="store_true",
        help='Generate plus and minus displacements for each direction.',
    )
    phonon_band_parser.add_argument(
        '--nodiag',
        dest='is_diagonal',
        action="store_false",
        help='Do not generate diagonal displacements.',
    )
    phonon_band_parser.add_argument(
        '--model',
        type=str,
        default=None,
        help='Path to the MACE model file for macer.'
    )
    phonon_band_parser.add_argument(
        '--device',
        type=str,
        default='cpu',
        choices=['cpu', 'mps', 'cuda'],
        help='Device for macer computation.'
    )
    # Original arguments for band.conf generation (now passed to run_macer_workflow)
    phonon_band_parser.add_argument("--yaml", default="phonopy_disp.yaml", type=Path,
                                  help="Path to phonopy_disp.yaml to read DIM from (for band.conf).")
    phonon_band_parser.add_argument("--out", default="band.conf", type=Path,
                                  help="Output band.conf file name.")
    phonon_band_parser.add_argument("--gamma", default="GM",
                                  help="Gamma label for BAND_LABELS (e.g., GM or Γ).")
    phonon_band_parser.add_argument("--symprec", type=float, default=1e-5,
                                  help="Symmetry tolerance passed to SeeK-path (for band.conf, default: 1e-5).")
    phonon_band_parser.add_argument("--dim", default=None,
                                  help='Override DIM as a string "a b c" (e.g., "3 3 3") (for band.conf).')
    phonon_band_parser.add_argument("--no-defaults", action="store_true",
                                  help="Do not include default FORCE_SETS, FC_SYMMETRY, EIGENVECTORS lines (for band.conf).")
    phonon_band_parser.add_argument("--atom-names", default=None,
                                  help='Override ATOM_NAME, e.g. "K Zr P O" (for band.conf).')
    phonon_band_parser.add_argument("--rename", default=None,
                                  help='Rename mapping, e.g. "Na=K,Zr=Zr" (for band.conf).')

    phonon_band_parser.set_defaults(func=_call_run_macer_workflow) # Link to the new helper function

    args = parser.parse_args()

    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
