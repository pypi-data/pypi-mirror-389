import os
import sys
import numpy as np
from ase.io import read, write
from ase.build import make_supercell # Not directly used for symmetrization, but useful for supercells
import spglib
from ase import Atoms # Explicitly import Atoms

from macer.calculator.mace import get_mace_calculator
from macer.relaxation.optimizer import relax_structure
from macer.utils.logger import Logger

def run_relax_unit(args):
    input_file = args.poscar
    model_path = args.model
    device = args.device
    tolerance = args.tolerance # Tolerance for standardize_cell
    tolerance_sym = args.tolerance_sym # Tolerance for get_symmetry_dataset
    max_iterations = args.max_iterations
    fmax = args.fmax
    smax = args.smax
    quiet = args.quiet

    # If tolerance_sym is not explicitly set, use the value of tolerance
    if tolerance_sym is None:
        tolerance_sym = tolerance

    # Determine model path if not provided
    if model_path is None:
        # Default model path relative to the main macer package
        # This path needs to be correct from macer/phonopy/relax_unit.py
        model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "mace-model", "mace-omat-0-small-fp32.model")
        if not os.path.exists(model_path):
            print(f"Error: Default MACE model not found at {model_path}. Please specify with --model.")
            sys.exit(1)

    # Initial structure
    atoms = read(input_file, format="vasp")
    initial_spacegroup = None
    current_spacegroup = None
    iteration = 0

    # Determine output prefix
    base_filename = os.path.basename(input_file)
    output_prefix = args.output_prefix or base_filename.replace(".vasp", "").replace(".POSCAR", "").replace("POSCAR", "CONTCAR")

    log_name = f"relax_unit-{output_prefix}_log.txt"
    orig_stdout = sys.stdout

    try:
        with Logger(log_name) as lg:
            sys.stdout = lg
            print(f"Starting iterative relaxation and symmetrization for {input_file}")
            print(f"Symmetry tolerance: {tolerance}, Max iterations: {max_iterations}")

            # --- Print initial space group ---
            cell = atoms.get_cell()
            positions = atoms.get_scaled_positions()
            numbers = atoms.get_atomic_numbers()
            lattice = cell.array

            initial_dataset = spglib.get_symmetry_dataset((lattice, positions, numbers), symprec=tolerance)
            
            initial_sg_number = None
            initial_sg_symbol = "N/A"

            if initial_dataset is not None:
                initial_sg_number = initial_dataset.get('number', None)
                initial_hall_number = initial_dataset.get('hall_number', None)

                try:
                    initial_sg_symbol = initial_dataset.international
                except AttributeError:
                    initial_sg_symbol = initial_dataset.get('international', None)
                
                if not initial_sg_symbol and initial_hall_number is not None:
                    try:
                        sg_type = spglib.get_spacegroup_type(initial_hall_number)
                        initial_sg_symbol = sg_type.get('international_short', "N/A")
                    except Exception:
                        initial_sg_symbol = "N/A"
                elif not initial_sg_symbol:
                    initial_sg_symbol = "N/A"
            
            print(f"  Initial structure space group: {initial_sg_symbol} (No. {initial_sg_number})")
            # --- End print initial space group ---

            # Set a tag for the atoms object for better identification in relax_structure
            atoms.info['tag'] = output_prefix

            while iteration < max_iterations:
                iteration += 1
                print(f"\n--- Iteration {iteration} ---")

                # Step 1: Relax the structure (ISIF=3 for full cell and atoms)
                print("  Relaxing structure (ISIF=3)...")
                # relax_structure now returns the modified atoms object
                atoms = relax_structure(
                    input_file=atoms, # Pass atoms object directly
                    fmax=fmax,
                    smax=smax,
                    device=device,
                    isif=3, # Always ISIF=3 for this process
                    fix_axis=[], # No fixed axis
                    quiet=quiet,
                    model_path=model_path,
                    # Suppress output files from relax_structure for intermediate steps
                    contcar_name=os.devnull,
                    outcar_name=os.devnull,
                    xml_name=os.devnull,
                    make_pdf=False,
                    write_json=False
                )

                # Step 2: Symmetrize the structure
                print("  Symmetrizing structure with spglib...")
                cell = atoms.get_cell()
                positions = atoms.get_scaled_positions()
                numbers = atoms.get_atomic_numbers()
                lattice = cell.array

                # Get space group info
                dataset = spglib.get_symmetry_dataset((lattice, positions, numbers), symprec=tolerance)
                
                
                # Check if dataset is None, which can happen for very distorted structures
                if dataset is None:
                    print("  Warning: spglib could not find symmetry dataset. Skipping symmetrization for this step.")
                    current_spacegroup = None
                international_symbol = "N/A"

                if dataset is None:
                    print("  Warning: spglib could not find symmetry dataset. Skipping symmetrization for this step.")
                else:
                    current_spacegroup = dataset.get('number', None) # This is the international space group number
                    hall_number = dataset.get('hall_number', None) # Get Hall number

                    international_symbol_from_dataset = None # Initialize here

                    # Try to get international_symbol directly from dataset attribute
                    try:
                        international_symbol = dataset.international
                        international_symbol_from_dataset = international_symbol # Assign if successful
                    except AttributeError:
                        # If attribute access fails, try dictionary key access
                        international_symbol = dataset.get('international', None)
                        international_symbol_from_dataset = international_symbol # Assign if successful
                    
                    if not international_symbol_from_dataset and hall_number is not None: # Use the initialized variable
                        # If still not found, use spglib.get_spacegroup_type with hall_number
                        try:
                            sg_type = spglib.get_spacegroup_type(hall_number)
                            international_symbol = sg_type.get('international_short', "N/A")
                        except Exception:
                            international_symbol = "N/A"
                    elif not international_symbol_from_dataset: # Use the initialized variable
                        international_symbol = "N/A" # Fallback if nothing works
                    
                    if international_symbol_from_dataset:
                        international_symbol = international_symbol_from_dataset
                    elif current_spacegroup is not None:
                        # If not found in dataset, try to get it from spglib.get_spacegroup_type
                        try:
                            sg_type = spglib.get_spacegroup_type(current_spacegroup)
                            international_symbol = sg_type.get('international_short', "N/A")
                        except Exception:
                            international_symbol = "N/A"

                    print(f"  Detected space group: {international_symbol} (No. {current_spacegroup})")

                # Standardize cell
                # spglib.standardize_cell returns (lattice, positions, numbers)
                standard_lattice, standard_positions, standard_numbers = spglib.standardize_cell(
                    (lattice, positions, numbers),
                    to_primitive=True, # Return primitive cell
                    symprec=tolerance
                )
                
                if standard_lattice is None: # standardize_cell can return None
                    print("  Warning: spglib could not standardize the cell. Skipping symmetrization for this step.")
                else:
                    # Create a new Atoms object from the standardized cell
                    from ase.data import chemical_symbols
                    symmetrized_symbols = [chemical_symbols[num] for num in standard_numbers]

                    symmetrized_atoms = Atoms(
                        symbols=symmetrized_symbols, # Use symbols derived from standard_numbers
                        cell=standard_lattice,
                        scaled_positions=standard_positions,
                        pbc=True
                    )
                    # Check if the symmetrized structure is significantly different
                    # A simple check is to compare space groups
                    if initial_spacegroup is None:
                        initial_spacegroup = current_spacegroup
                    
                    # Update atoms for next iteration
                    atoms = symmetrized_atoms.copy()
                    atoms.info['tag'] = output_prefix # Maintain tag

                    if current_spacegroup == initial_spacegroup:
                        print(f"  Space group converged to No. {current_spacegroup}.")
                        # More robust convergence check: compare positions/cell after symmetrization
                        # For now, space group convergence is sufficient.
                        break
                    else:
                        print(f"  Space group changed from No. {initial_spacegroup} to No. {current_spacegroup}. Continuing iteration.")
                        initial_spacegroup = current_spacegroup # Update for next comparison

                if iteration == max_iterations:
                    print(f"  Max iterations ({max_iterations}) reached without full convergence.")

            # Final output after the main loop
            final_output_name = f"{output_prefix}-symmetrized"
            write(final_output_name, atoms, format="vasp")
            print(f"\n✅ Final converged structure saved to {final_output_name}")

            # --- Additional check after main loop convergence ---
            # Only perform this if the main loop converged (not just hit max_iterations)
            if iteration < max_iterations: # This means the loop broke due to space group convergence
                print("\n--- Final Convergence Check ---")
                print("  Performing one last relaxation on the symmetrized structure...")
                final_relaxed_atoms = relax_structure(
                    input_file=atoms, # Pass the last symmetrized atoms object
                    fmax=fmax,
                    smax=smax,
                    device=device,
                    isif=3,
                    fix_axis=[],
                    quiet=quiet,
                    model_path=model_path,
                    contcar_name=os.devnull,
                    outcar_name=os.devnull,
                    xml_name=os.devnull,
                    make_pdf=False,
                    write_json=False
                )

                # Perform final symmetry check on the newly relaxed structure
                print("  Checking symmetry of the final relaxed structure...")
                cell = final_relaxed_atoms.get_cell()
                positions = final_relaxed_atoms.get_scaled_positions()
                numbers = final_relaxed_atoms.get_atomic_numbers()
                lattice = cell.array

                final_dataset = spglib.get_symmetry_dataset((lattice, positions, numbers), symprec=tolerance)
                
                final_spacegroup = None
                final_international_symbol = "N/A"

                if final_dataset is None:
                    # If final_dataset is None, keep defaults
                    pass
                else:
                    final_spacegroup = final_dataset.get('number', None)
                    hall_number = final_dataset.get('hall_number', None) # Get Hall number for final check

                    international_symbol_from_dataset = None # Initialize here

                    # Try to get international_symbol directly from dataset attribute
                    try:
                        final_international_symbol = final_dataset.international
                        international_symbol_from_dataset = final_international_symbol
                    except AttributeError:
                        # If attribute access fails, try dictionary key access
                        final_international_symbol = final_dataset.get('international', None)
                        international_symbol_from_dataset = final_international_symbol
                    
                    if not international_symbol_from_dataset and hall_number is not None:
                        # If still not found, use spglib.get_spacegroup_type with hall_number
                        try:
                            sg_type = spglib.get_spacegroup_type(hall_number)
                            final_international_symbol = sg_type.get('international_short', "N/A")
                        except Exception:
                            final_international_symbol = "N/A"
                    elif not international_symbol_from_dataset:
                        final_international_symbol = "N/A" # Fallback if nothing works
                
                print(f"  Final relaxed structure space group: {final_international_symbol} (No. {final_spacegroup})")

                if final_spacegroup == current_spacegroup: # Compare with the spacegroup that caused loop break
                    print("✅ Final relaxed structure maintains converged space group.")
                else:
                    print(f"⚠️ Warning: Final relaxed structure's space group (No. {final_spacegroup}) differs from the last symmetrized space group (No. {current_spacegroup}).")
                    print("           Consider increasing max_iterations or adjusting tolerance.")
            # --- End of Additional check ---

    except Exception as e:
        sys.stdout = orig_stdout
        print(f"❌ An error occurred: {e}")
    finally:
        sys.stdout = orig_stdout
