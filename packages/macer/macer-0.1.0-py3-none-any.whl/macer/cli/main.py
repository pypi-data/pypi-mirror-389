import argparse
import sys
import os
import glob

from macer.utils.logger import Logger
from macer.relaxation.optimizer import relax_structure
from macer.io.writers import write_pydefect_dummy_files
from macer.molecular_dynamics.cli import get_md_parser, run_md_simulation # Import get_md_parser and run_md_simulation

def main():
    parser = argparse.ArgumentParser(
        description="macer: MACE+ASE based ML-accerlatied relaxer and molecular dynamics engine with VASP compatible format.",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Relaxation command
    relax_parser = subparsers.add_parser(
        "relax",
        description="Relax atomic structures using MACE with VASP-like ISIF modes. Supports multiple input files (POSCAR-*).",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    relax_parser.add_argument("--poscar", "-p", type=str, nargs="+", default=["POSCAR"],
                        help="Input POSCAR file(s) or pattern(s) (VASP format atomic structure input, e.g. POSCAR-*).")
    relax_parser.add_argument("--model", type=str, default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "mace-model", "mace-omat-0-small-fp32.model"),
                        help="Path to the MACE model file.")
    relax_parser.add_argument("--fmax", type=float, default=0.01, help="Force convergence threshold (eV/Å).")
    relax_parser.add_argument("--smax", type=float, default=0.001, help="Stress convergence threshold (eV/Å³).")
    relax_parser.add_argument("--device", type=str, default="cpu", choices=["cpu", "mps", "cuda"])
    relax_parser.add_argument("--isif", type=int, default=2, choices=list(range(8)))
    relax_parser.add_argument("--fix-axis", type=str, default="")
    relax_parser.add_argument("--quiet", action="store_true")
    relax_parser.add_argument("--no-pdf", action="store_true", help="Disable log PDF output")
    relax_parser.add_argument("--pydefect", action="store_true", help="Write PyDefect-compatible files (calc_results.json, unitcell.yaml, perfect_band_edge_state.json).")
    relax_parser.add_argument("--contcar", type=str, default=None, help="Output CONTCAR file name.")
    relax_parser.add_argument("--outcar", type=str, default=None, help="Output OUTCAR file name.")
    relax_parser.add_argument("--vasprun", type=str, default=None, help="Output vasprun.xml file name.")

    # MD command
    # Get the MD parser from md.py and use it as a parent
    md_base_parser = get_md_parser()
    md_parser = subparsers.add_parser(
        "md",
        description=md_base_parser.description, # Use description from md_base_parser
        epilog=md_base_parser.epilog,           # Use epilog from md_base_parser
        formatter_class=argparse.RawDescriptionHelpFormatter,
        parents=[md_base_parser]                # Add md_base_parser as a parent
    )

    args = parser.parse_args()

    if args.command == "relax":
        fix_axis = [ax.strip().lower() for ax in args.fix_axis.split(",") if ax.strip()]

        input_patterns = args.poscar
        input_files = []
        for pat in input_patterns:
            input_files.extend(glob.glob(pat))
        input_files = sorted(set(input_files))

        if not input_files:
            print(f"❌ No files match pattern(s): {input_patterns}")
            sys.exit(1)

        if (args.contcar or args.outcar or args.vasprun) and len(input_files) > 1:
            print("⚠️ WARNING: Custom output names (--contcar, --outcar, --vasprun) are used with multiple input files.")
            print("Output files may be overwritten. Consider running files one by one.")

        orig_stdout = sys.stdout

        for infile in input_files:
            prefix = os.path.basename(infile)
            output_dir = os.path.dirname(infile) or "."
            log_name = os.path.join(output_dir, f"relax-{prefix}_log.txt")

            contcar_name = os.path.join(output_dir, args.contcar or f"CONTCAR-{prefix}")
            outcar_name = os.path.join(output_dir, args.outcar or f"OUTCAR-{prefix}")
            xml_name = os.path.join(output_dir, args.vasprun or f"vasprun-{prefix}.xml")

            try:
                with Logger(log_name) as lg:
                    sys.stdout = lg
                    if args.pydefect:
                        write_pydefect_dummy_files(output_dir)
                        print("NOTE: perfect_band_edge_state.json and unitcell.yaml were written as dummy files for pydefect dei and pydefect des.")
                    print(f"▶ Using MACE on '{infile}' | ISIF={args.isif} | fmax={args.fmax} | smax={args.smax} | device={args.device}")
                    relax_structure(
                        input_file=infile,
                        fmax=args.fmax,
                        smax=args.smax,
                        device=args.device,
                        isif=args.isif,
                        fix_axis=fix_axis,
                        quiet=args.quiet,
                        contcar_name=contcar_name,
                        outcar_name=outcar_name,
                        xml_name=xml_name,
                        make_pdf=not args.no_pdf,
                        write_json=args.pydefect,
                        model_path=args.model
                    )
                    results_path_info = f"in '{output_dir}'" if output_dir else "in the current directory"
                    print(f"✅ Finished {infile} → Results saved {results_path_info}")
                    print("-" * 80)
            except Exception as e:
                sys.stdout = orig_stdout
                print(f"[SKIP] {infile}: {e}")
                continue
            finally:
                sys.stdout = orig_stdout

    elif args.command == "md":
        run_md_simulation(args) # Call the run_md_simulation function with parsed args

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
