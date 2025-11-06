<img src="docs/macer_logo.png" alt="macer Logo" width="20%">

# macer

![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

**macer: A [MACE](https://github.com/ACEsuit/mace) + [ASE](https://github.com/DeepChoudhuri/Atomic-Simulation-Environment) based CLI for fast atomic structure optimization, molecular dynamics, and phonon calculations with VASP compatible formats.**

The `macer` package provides an automated command-line workflow for crystal structure relaxation, molecular dynamics simulations, and phonon calculations, leveraging MACE (Machine-Learned Atomistic Energy) models and ASE (Atomic Simulation Environment).

---

## Key Features

-   **MACE Calculator**: Utilizes MACE as the interatomic potential calculator for both relaxation and MD.
-   **ASE FIRE Optimizer**: Employs the robust FIRE algorithm for geometry relaxation.
-   **VASP ISIF Compatibility**: Supports relaxation modes `ISIF` 0–7.
-   **Molecular Dynamics**: Performs NPT and NVT (Nose–Hoover chain / Berendsen) ensemble simulations.
-   **Phonon Calculations**: Uses Phonopy to calculate phonon dispersion curves and density of states (DOS).
-   **pydefect Integration**: Generates `pydefect`-compatible output files with the `--pydefect` flag for relaxation.
-   **Phonopy Compatibility**: Generates a minimal, Phonopy-compatible `vasprun.xml` for relaxation.
-   **Batch Processing**: Automatically processes multiple structure files (e.g., `POSCAR-*`) for relaxation.
-   **Flexible Model Path**: Specify any MACE model via the `--model` argument for all commands.
-   **Logging & Plotting**: Automatically generates log files and PDF energy/force plots for relaxation. MD simulations produce detailed text logs, trajectory files, XDATCAR, and CSV output files.
-   **Fixed-Axis Relaxation**: Supports fixed-axis relaxation via `--fix-axis a,b,c`.

---

## MACE Model Attribution

This project utilizes the MACE (Machine Learning for Atomistic Calculations) model for interatomic potentials. The MACE model and its foundational work are developed by the ACEsuit team.

For more information, please refer to the official MACE Foundations GitHub repository:
[https://github.com/ACEsuit/mace-foundations](https://github.com/ACEsuit/mace-foundations)

---

## References

If you use the MACE model, please cite these papers:

```bibtex
@inproceedings{Batatia2022mace,
  title={{MACE}: Higher Order Equivariant Message Passing Neural Networks for Fast and Accurate Force Fields},
  author={Ilyes Batatia and David Peter Kovacs and Gregor N. C. Simm and Christoph Ortner and Gabor Csanyi},
  booktitle={Advances in Neural Information Processing Systems},
  editor={Alice H. Oh and Alekh Agarwal and Danielle Belgrave and Kyunghyun Cho},
  year={2022},
  url={https://openreview.net/forum?id=YPpSngE-ZU}
}

@misc{Batatia2022Design,
  title = {The Design Space of E(3)-Equivariant Atom-Centered Interatomic Potentials},
  author = {Batatia, Ilyes and Batzner, Simon and Kov{'a}cs, D{'a}vid P{'e}ter and Musaelian, Albert and Simm, Gregor N. C. and Drautz, Ralf and Ortner, Christoph and Kozinsky, Boris and A. Kozinsky and Cs{'a}nyi, G{'a}bor}, # Corrected author list
  year = {2022},
  number = {arXiv:2205.06643},
  eprint = {2205.06643},
  eprinttype = {arxiv},
  doi = {10.48550/arXiv.2205.06643},
  archiveprefix = {arXiv}
}
```

---

## Installation

You can install `macer` directly from the source directory using `pip`.

```bash
# Navigate to the macer package directory
cd /path/to/macer

# Install the package in editable mode
pip install -e .
```
This will install the package and make the `macer` and `macer_phonopy` commands available in your terminal.

---

## Usage

The `macer` CLI now supports multiple subcommands for different simulation types.

```bash
# Get general help
macer -h

# Get help for the 'relax' command
macer relax -h

# Get help for the 'md' command
macer md -h

# Get help for the 'macer_phonopy' command
macer_phonopy -h
```

### Relaxation Examples (`macer relax`)

```bash
# Standard atomic relaxation (ISIF=2: atomic positions only)
macer relax --poscar POSCAR

# Batch relaxation for multiple structures
macer relax --poscar POSCAR-* --isif 2

# Full cell relaxation (atoms + lattice)
macer relax --poscar POSCAR --isif 3

# Use a different MACE model
macer relax --poscar POSCAR --model /path/to/your/mace.model

# Generate outputs for PyDefect
macer relax --poscar POSCAR --isif 0 --pydefect

# Relaxation with fixed a-axis
macer relax --poscar POSCAR --isif 3 --fix-axis a

# Disable PDF log plotting
macer relax --poscar POSCAR --no-pdf
```

### Molecular Dynamics Examples (`macer md`)

```bash
# NPT (Nose–Hoover barostat) — 600 K, 1 GPa, GPU (MPS), save every 100 steps
macer md --ensemble npt --temp 600 --press 1.0 --ttau 100 --ptau 1000 \
         --device mps --nsteps 20000 --save-every 100

# NVT (NTE; prefers Nose–Hoover chain, falls back to Berendsen) — 600 K, 5000 steps
macer md --ensemble nte --temp 600 --ttau 100 --nsteps 5000

# Reproducible run (fixed seed) + adjusted print/save intervals
macer md --ensemble npt --temp 300 --press 0.0 --ttau 100 --ptau 1000 \
         --seed 42 --print-every 10 --save-every 100
```

### Phonon Calculation Examples (`macer_phonopy`)

The `macer_phonopy` command provides utilities for Phonopy-related tasks, including unit cell relaxation/symmetrization and band path generation.

```bash
# Get basic help for macer_phonopy and its subcommands
macer_phonopy -h
macer_phonopy ru -h
macer_phonopy bp -h
```

#### Unit Cell Relaxation and Symmetrization (`macer_phonopy ru` or `macer_phonopy relax_unit`)

This subcommand iteratively optimizes and symmetrizes a unit cell, which is crucial for preparing structures for phonon calculations.

```bash
# Relax and symmetrize a unit cell using the default MACE model
macer_phonopy ru --poscar POSCAR

# Relax and symmetrize with a specific MACE model and increased symmetry tolerance
macer_phonopy ru --poscar POSCAR --model /path/to/your/mace.model --tolerance 1e-2

# Relax and symmetrize with custom output prefix
macer_phonopy ru --poscar POSCAR --output-prefix my_symmetrized_cell
```

#### Band Path Generation (`macer_phonopy bp` or `macer_phonopy bandpath`)

This subcommand generates a Phonopy `band.conf` file directly from a `POSCAR` using SeeK-path, eliminating the need for external tools like VASPKIT.

```bash
# Generate band.conf from POSCAR
macer_phonopy bp --poscar POSCAR --out band.conf

# Generate band.conf with a specific supercell dimension and custom gamma label
macer_phonopy bp --poscar POSCAR --dim "2 2 2" --gamma "Γ" --out my_band.conf

# Generate band.conf and include default FORCE_SETS, FC_SYMMETRY, EIGENVECTORS
macer_phonopy bp --poscar POSCAR --no-defaults
```

For precise usage of `macer_phonopy` and its subcommands, please refer to `macer_phonopy -h`, `macer_phonopy ru -h`, `macer_phonopy bp -h`, and the official Phonopy documentation.

---

## 📂 Output Files

### Relaxation Output Files

For each input file (e.g., `POSCAR-001`), the following files are produced:

```
CONTCAR-POSCAR-001
OUTCAR-POSCAR-001
vasprun-POSCAR-001.xml
relax-POSCAR-001_log.txt
relax-POSCAR-001_log.pdf
```

If the `--pydefect` flag is used, the following additional files are created:
```
calc_results.json
perfect_band_edge_state.json (dummy)
unitcell.yaml (dummy)
```

### Molecular Dynamics Output Files

For MD simulations, the following files are produced:

```
md.traj       # ASE trajectory file
md.log        # Text log of MD progress
XDATCAR       # VASP-like XDATCAR file
md.csv        # CSV log of observables (energy, temperature, pressure, etc.)
```

### Phonon Calculation Output Files

`macer_phonopy` generates standard Phonopy output files. These may include:

```
band.yaml       # Phonon band structure data
mesh.yaml       # Phonon density of states (DOS) data
total_dos.dat   # Total DOS data
partial_dos.dat # Partial DOS data
```
The exact files generated depend on the options passed to the `macer_phonopy` command and your Phonopy configuration.

---

## Command Line Options

### `macer relax` Options

| Option | Description | Default |
|--------|-------------|---------|
| `-p`, `--poscar` | Input POSCAR file(s) or glob pattern(s) (e.g., `POSCAR-*`) | `POSCAR` |
| `--model` | Path to the MACE model file. By default, it expects `mace-omat-0-small-fp32.model` to be located in the `mace-model` directory. | `mace-model/mace-omat-0-small-fp32.model` |
| `--isif` | VASP ISIF mode (0–7) for relaxation. | 2 |
| `--fmax` | Force convergence threshold (eV/Å). | 0.01 |
| `--smax` | Stress convergence threshold (eV/Å³). | 0.001 |
| `--device` | Calculation device (`cpu`, `mps`, `cuda`). | `cpu` |
| `--fix-axis` | Fix lattice axes (comma-separated, e.g., `a` or `a,c`). | None |
| `--pydefect` | Write PyDefect-compatible output files. | False |
| `--quiet` | Suppress detailed stdout logging. | False |
| `--no-pdf` | Do not write the `relax-*_log.pdf` plot. | False |
| `--contcar`| Custom name for the output CONTCAR file. | `CONTCAR-<prefix>` |
| `--outcar` | Custom name for the output OUTCAR file. | `OUTCAR-<prefix>` |
| `--vasprun`| Custom name for the output vasprun.xml file. | `vasprun-<prefix>.xml` |

### `macer md` Options

| Option | Description | Default |
|--------|-------------|---------|
| `-p`, `--poscar` | Input POSCAR file (VASP format atomic structure input). | `POSCAR` |
| `--model` | MACE model path. | `mace-model/mace-omat-0-small-fp32.model` |
| `--device` | Compute device (`cpu`, `mps`, `cuda`). | `cpu` |
| `--ensemble` | MD ensemble: `npt` (Nose–Hoover barostat) or `nte` (=NVT; Nose–Hoover chain preferred, else Berendsen). | `npt` |
| `--temp` | Target temperature [K]. | 300.0 |
| `--press` | Target pressure [GPa] (NPT only). | 0.0 |
| `--tstep` | MD time step [fs]. | 2.0 |
| `--nsteps` | Number of MD steps. | 20000 |
| `--ttau` | Thermostat time constant [fs]. | 100.0 |
| `--ptau` | Barostat time constant [fs] (NPT only). | 1000.0 |
| `--save-every` | Trajectory/log save interval. | 100 |
| `--xdat-every` | XDATCAR write interval. | 1 |
| `--print-every` | Stdout print interval. | 1 |
| `--seed` | Random seed (None for random). | None |
| `--csv` | CSV log path for MD outputs. | `md.csv` |
| `--xdatcar` | XDATCAR path. | `XDATCAR` |
| `--traj` | ASE trajectory path. | `md.traj` |
| `--log` | MD text log path. | `md.log` |

### `macer_phonopy` Options

The `macer_phonopy` command wraps Phonopy's command-line interface. For detailed options, refer to `macer_phonopy -h` or the official Phonopy documentation. Commonly used options include:

| Option | Description |
|--------|-------------|
| `-c`, `--conf` | Phonopy configuration file (e.g., `phonopy.conf`). |
| `--dim` | Supercell dimensions (e.g., `2 2 2`). |
| `--mesh` | Mesh sampling (e.g., `20 20 20`). |
| `--band` | Band path configuration file (e.g., `band.conf`). |
| `--dos` | Calculate density of states (DOS). |
| `--pdos` | Calculate partial density of states (PDOS). |
| `--readfc` | Read force constants. |
| `--writefc` | Write force constants. |
| `--fmax` | Force convergence threshold (used for MACE calculations). |
| `--model` | Path to the MACE model file. |
| `--device` | Calculation device (`cpu`, `mps`, `cuda`). |

---

## Dependencies

All required Python packages are listed in `pyproject.toml` and will be installed automatically by `pip`.

-   Python ≥ 3.8
-   ASE ≥ 3.20
-   matplotlib
-   numpy
-   mace-torch
-   pymatgen
-   monty

---
## Related packages
-   phonopy [https://github.com/phonopy/phonopy](https://github.com/phonopy/phonopy)
-   pydefect [https://github.com/kumagai-group/pydefect](https://github.com/kumagai-group/pydefect)
---

## Standalone Scripts (Fallback Option)

If you encounter issues with `pip` installation or prefer to run the original scripts directly, standalone versions of the `mace_ase_relax.py` and `mace_ase_md.py` scripts are provided in the `scripts/` directory.

**Usage:**

1.  **Navigate to the `scripts` directory:**
    ```
    cd /path/to/macer_repo/scripts
    ```
2.  **Edit the script:** Open `mace_ase_relax.py` or `mace_ase_md.py` and update the `model_path` variable within the `get_mace_calculator` function to point to your MACE model file.
3.  **Run the script:**
    ```bash
    python mace_ase_relax.py -i POSCAR --isif 3
    python mace_ase_md.py --ensemble npt --temp 300
    ```
    All command-line arguments are identical to the `macer relax` and `macer md` commands, respectively.

---

## License

This project is licensed under the **MIT License**. See the `LICENSE` file for details.

---

## Notes

-   `vasprun-*.xml` is a **minimal** VASP-like XML that Phonopy can parse for forces/energies.
-   For batch runs, the script writes **per-input** outputs with the input file name appended (e.g., `CONTCAR-POSCAR-001`).

---
 ## Contributors
- **Soungmin Bae** — [soungminbae@gmail.com](mailto:soungminbae@gmail.com), Tohoku University  
- **Yasuhide Mochizuki** — [mochigmail](mailto:mochigmail), Institute of Tokyo, Science

