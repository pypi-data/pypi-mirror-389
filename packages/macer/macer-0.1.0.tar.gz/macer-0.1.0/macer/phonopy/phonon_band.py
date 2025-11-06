#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
phonon_band.py
Make phonopy band.conf directly from POSCAR using SeeK-path (no VASPKIT needed).

- Robust POSCAR parser (VASP4/5, Selective dynamics, Direct/Cartesian)
- POSCAR -> SeeK-path standard k-path (continuous chain)
- DIM: from --dim "a b c" (highest priority) or phonopy_disp.yaml if present; otherwise blank
- BAND: single line, one k-point per node (junctions deduped)
- BAND_LABELS: cleaned (GAMMA->GM by default, underscores removed)
- ATOM_NAME override: --atom-names "K Zr P O" or --rename "Na=K"
- Summary print: POSCAR used, space group, q-path & coords, DIM source
"""

import argparse
import re
import math
import sys
import glob
import subprocess
import shutil
import numpy as np
from types import SimpleNamespace
from pathlib import Path

# (optional) silence DeprecationWarnings from spglib
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Imports for workflow integration with phonopy / ASE / macer
from phonopy import Phonopy
from phonopy.interface.vasp import read_vasp, write_vasp
from phonopy.interface.calculator import write_supercells_with_displacements
from phonopy.cui.create_force_sets import create_FORCE_SETS
from phonopy.interface.phonopy_yaml import PhonopyYaml
from ase.io import read as ase_read
from macer.relaxation.optimizer import relax_structure


# ------------------------- POSCAR I/O -------------------------

def read_poscar(poscar_path: Path):
    with poscar_path.open("r", encoding="utf-8") as f:
        raw = [ln.rstrip("\n") for ln in f]

    def next_nonempty(i):
        while i < len(raw) and raw[i].strip() == "":
            i += 1
        return i

    i = next_nonempty(0)
    if i >= len(raw):
        raise ValueError("POSCAR is empty")

    comment = raw[i]; i = next_nonempty(i+1)
    if i >= len(raw):
        raise ValueError("POSCAR: missing scale line")
    scale = float(raw[i].split()[0]); i = next_nonempty(i+1)

    # lattice vectors
    lat = []
    for _ in range(3):
        if i >= len(raw):
            raise ValueError("POSCAR: missing lattice vectors")
        parts = raw[i].split()
        if len(parts) < 3:
            raise ValueError("POSCAR: lattice vector line has < 3 numbers")
        vec = [float(x) for x in parts[:3]]
        lat.append([scale * v for v in vec])
        i = next_nonempty(i+1)

    if i >= len(raw):
        raise ValueError("POSCAR: missing symbols/counts line")

    tokens = raw[i].split()

    def is_number(x):
        try:
            float(x); return True
        except Exception:
            return False

    vasp5 = (tokens and any(not is_number(t) for t in tokens))
    if vasp5:
        symbols = tokens[:]                   # e.g. Na Zr P O
        i = next_nonempty(i+1)
        if i >= len(raw):
            raise ValueError("POSCAR: missing counts line after symbols")
        counts = [int(x) for x in raw[i].split()]
        i = next_nonempty(i+1)
        if len(symbols) != len(counts):
            if len(symbols) > len(counts):
                symbols = symbols[:len(counts)]
            else:
                symbols = symbols + [f"E{j+1}" for j in range(len(counts)-len(symbols))]
    else:
        # VASP4: counts here, no symbols line
        counts = [int(x) for x in tokens]
        symbols = []  # no symbols; ATOM_NAME will be blank unless overridden
        i = next_nonempty(i+1)

    # Optional "Selective dynamics"
    if i < len(raw) and raw[i].strip().lower().startswith("selective"):
        i = next_nonempty(i+1)

    # Coordinate type
    if i >= len(raw):
        raise ValueError("POSCAR: missing coordinate type line")
    ctok = raw[i].strip().lower()
    direct = ctok.startswith("d")
    cart = ctok.startswith("c")
    if not (direct or cart):
        raise ValueError(f"POSCAR: unknown coordinate type line: {raw[i]}")
    i = next_nonempty(i+1)

    # Atom coordinates
    nat = sum(counts)
    coord_lines, read_cnt = [], 0
    while i < len(raw) and read_cnt < nat:
        if raw[i].strip() != "":
            coord_lines.append(raw[i])
            read_cnt += 1
        i += 1
    if read_cnt < nat:
        raise ValueError("POSCAR: not enough atomic coordinate lines")

    if direct:
        frac = [[float(u) for u in ln.split()[:3]] for ln in coord_lines]
    else:
        A = np.array(lat).T  # columns a,b,c
        Ainv = np.linalg.inv(A)
        frac = []
        for ln in coord_lines:
            cx, cy, cz = [float(u) for u in ln.split()[:3]]
            f = Ainv @ (scale * np.array([cx, cy, cz]))
            frac.append(f.tolist())

    # kinds: build from counts
    kinds = []
    nsp = len(counts)
    for si in range(nsp):
        kinds.extend([si + 1] * counts[si])

    return {
        "comment": comment,
        "lattice": lat,
        "frac": frac,
        "kinds": kinds,
        "symbols": symbols,  # may be []
        "counts": counts,
    }


# ------------------------- phonopy_disp.yaml -> DIM -------------------------

def read_dim_from_yaml(yaml_path: Path):
    """Return [a,b,c] or None if not found or file missing."""
    try:
        return _read_dim_yaml_inner(yaml_path)
    except FileNotFoundError:
        return None

def _read_dim_yaml_inner(yaml_path: Path):
    dim = None
    pat_dim = re.compile(r'^\s*dim:\s*"([^"]+)"', re.IGNORECASE)
    pat_row = re.compile(r'^\s*-\s*\[\s*(-?\d+)\s*,\s*(-?\d+)\s*,\s*(-?\d+)\s*\]')

    # Case 1: explicit dim: "a b c"
    with yaml_path.open("r", encoding="utf-8") as f:
        for ln in f:
            m = pat_dim.match(ln)
            if m:
                parts = m.group(1).split()
                if len(parts) == 3 and all(p.lstrip("-").isdigit() for p in parts):
                    dim = [int(p) for p in parts]
                break
    if dim is not None:
        return dim

    # Case 2: derive DIM from supercell_matrix (diagonal or non-diagonal)
    rows, in_super = [], False
    with yaml_path.open("r", encoding="utf-8") as f:
        for ln in f:
            if "supercell_matrix" in ln:
                in_super = True
                continue
            if in_super:
                if ln.strip().startswith("- ["):
                    m = pat_row.match(ln)
                    if m:
                        rows.append([int(m.group(i)) for i in range(1, 4)])
                else:
                    break

    if rows:
        # If diagonal, use absolute diagonal; if not, use vector norms (rounded)
        if all(rows[i][j] == (rows[i][i] if i == j else 0) for i in range(3) for j in range(3)):
            dim = [abs(rows[i][i]) for i in range(3)]
        else:
            dim = [max(1, int(round(math.sqrt(sum(c*c for c in r))))) for r in rows[:3]]
            print("[WARN] Non-diagonal supercell_matrix; approximated DIM =", dim)

    return dim  # may be None


# ------------------------- helpers -------------------------

def _fmt(x):
    v = float(x)
    if abs(v) < 1e-12:
        v = 0.0
    s = f"{v:.3f}"
    if s == "-0.000":
        s = "0.000"
    return s

def _clean_label(lbl: str, gamma="GM"):
    if lbl.upper() == "GAMMA":
        return gamma
    return lbl.replace("_", "")


# ------------------------- label chain & band -------------------------

def build_label_chain(path_segments):
    if not path_segments:
        return []
    chain = []
    s0, e0 = path_segments[0]
    chain.append(s0); chain.append(e0)
    for (s, e) in path_segments[1:]:
        if chain[-1] != s:
            chain.append(s)
        chain.append(e)
    dedup = [chain[0]]
    for lab in chain[1:]:
        if lab != dedup[-1]:
            dedup.append(lab)
    return dedup

def band_points_one_line_from_seekpath(path_data, gamma_label="GM"):
    pc = path_data["point_coords"]
    segs = path_data["path"]
    chain = build_label_chain(segs)
    labels = [_clean_label(x, gamma_label) for x in chain]
    pts = [f"{_fmt(pc[lab][0])} {_fmt(pc[lab][1])} {_fmt(pc[lab][2])}" for lab in chain]
    band_line = "BAND = " + "    ".join(pts)
    return band_line, labels, chain  # chain: raw labels for summary


# ------------------------- atom-name override -------------------------

def parse_atom_override(args, symbols_from_poscar):
    if args.atom_names:
        return args.atom_names.split()
    if args.rename:
        ren = {}
        for pair in args.rename.split(","):
            old, new = pair.split("=")
            ren[old.strip()] = new.strip()
        if symbols_from_poscar:
            return [ren.get(s, s) for s in symbols_from_poscar]
        else:
            return []
    return symbols_from_poscar


# ------------------------- pretty summary -------------------------

def print_summary(poscar_path: Path, path_data, chain_labels, gamma_cleaned_labels, dim, dim_source):
    try:
        poscar_disp = str(poscar_path.resolve())
    except Exception:
        poscar_disp = str(poscar_path)

    sg_int = path_data.get("spacegroup_international", "?")
    sg_no  = path_data.get("spacegroup_number", "?")
    bravais = path_data.get("bravais_lattice", "?")

    print("------------------------------------------------------------")
    print(f"[Seekpath] POSCAR: {poscar_disp}")
    print(f"[Seekpath] Space group: {sg_int} (No.{sg_no}), Bravais: {bravais}")
    print(f"[Seekpath] Q-path (labels): {' - '.join(gamma_cleaned_labels)}")
    print("[Seekpath] Q-points (reciprocal crystal units):")
    pc = path_data["point_coords"]
    for raw_lab, clean_lab in zip(chain_labels, gamma_cleaned_labels):
        k = pc[raw_lab]
        print(f"  {clean_lab:>4s} : {_fmt(k[0])}  {_fmt(k[1])}  {_fmt(k[2])}")
    print(f"[Seekpath] Total q-points: {len(chain_labels)}")

    if dim is None:
        print("[Info] DIM not set (no phonopy_disp.yaml). The output band.conf will contain 'DIM =' (blank).")
        print("       Provide --yaml phonopy_disp.yaml or use --dim \"a b c\" to set it explicitly.")
    else:
        print(f"[Seekpath] DIM = {dim[0]} {dim[1]} {dim[2]}  (source: {dim_source})")
    print("------------------------------------------------------------")


# ------------------------- _generate_band_conf (renamed from run_band_path) -------------------------

def _generate_band_conf(args):
    # POSCAR -> cell
    pos = read_poscar(args.poscar)
    atom_names = parse_atom_override(args, pos["symbols"])
    lattice, positions, numbers = pos["lattice"], pos["frac"], pos["kinds"]
    cell = (lattice, positions, numbers)

    # SeeK-path (with symprec)
    import seekpath
    path_data = seekpath.get_path(cell, symprec=args.symprec)

    band_line, labels, chain_raw = band_points_one_line_from_seekpath(path_data, gamma_label=args.gamma)

    # DIM priority: --dim > --yaml (if exists) > None (blank)
    dim = None
    dim_source = None
    if args.dim:
        parts = args.dim.split()
        if len(parts) == 3 and all(p.lstrip("-").isdigit() for p in parts):
            dim = [int(p) for p in parts]
            dim_source = "--dim"
        else:
            print("[WARN] --dim must be like: --dim \"3 3 3\"; ignoring it.")
    if dim is None:
        if args.yaml and Path(args.yaml).exists():
            dim = read_dim_from_yaml(Path(args.yaml))
            dim_source = "phonopy_disp.yaml" if dim is not None else None
        else:
            dim = None

    # Write band.conf
    out_lines = []
    if atom_names:
        out_lines.append(f"ATOM_NAME = {' '.join(atom_names)}")
    else:
        out_lines.append("ATOM_NAME =")
    if dim is None:
        out_lines.append("DIM =")  # leave blank as requested
    else:
        out_lines.append(f"DIM = {dim[0]} {dim[1]} {dim[2]}")
    out_lines.append(band_line)
    out_lines.append(f"BAND_LABELS = {' '.join(labels)}")
    if not args.no_defaults:
        out_lines.append("FORCE_SETS = READ")
        out_lines.append("FC_SYMMETRY = .TRUE.")
        out_lines.append("EIGENVECTORS = .TRUE.")

    Path(args.out).write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    print(f"[OK] Wrote {args.out}")

    # Summary
    print_summary(args.poscar, path_data, chain_raw, labels, dim, dim_source)


# ------------------------- INSERT: run_macer_workflow -------------------------

def run_macer_workflow(
    input_path: Path,
    min_length: float,
    displacement_distance: float,
    is_plusminus: bool,
    is_diagonal: bool,
    symprec_seekpath: float = 1e-5,
    gamma_label: str = "GM",
    macer_device: str = "cpu",
    macer_model_path: Path | None = None,
    yaml_path_arg: Path | None = None,
    out_path_arg: Path | None = None,
    dim_override: str | None = None,
    no_defaults_band_conf: bool = False,
    atom_names_override: str | None = None,
    rename_override: str | None = None,
    output_prefix: str | None = None,
    tolerance: float = 1e-3,
):
    """
    End-to-end helper:
      POSCAR -> (seekpath) -> SPOSCAR + displacements -> macer relax -> FORCE_SETS -> FORCE_CONSTANTS
              -> band.conf (via _generate_band_conf) -> phonopy plot -> rename/cleanup

    Parameters
    ----------
    input_path : Path
        Path to input POSCAR-like file.
    output_dir : Path
        Directory to write all outputs.
    scaling_factors : tuple(int,int,int)
        Supercell DIM (used by phonopy for displacements).
    displacement_distance : float
        Displacement distance in Å for phonon displacements.
    symprec_seekpath : float
        Symmetry tolerance passed to SeeK-path (band path).
    gamma_label : str
        Label to use for Γ in BAND_LABELS ("GM" or "Γ" etc.).
    macer_device : str
        "cpu" or "cuda".
    macer_model_path : Path | None
        Optional path to macer model weights.
    yaml_path_arg : Path | None
        Override for YAML path passed to _generate_band_conf().
    out_path_arg : Path | None
        Override for band.conf path passed to _generate_band_conf().
    dim_override : str | None
        Override DIM string (e.g., "3 3 3") passed to _generate_band_conf().
    no_defaults_band_conf : bool
        If True, don't append phonopy defaults in band.conf.
    atom_names_override : str | None
        Override ATOM_NAME string (e.g., "K Zr P O").
    rename_override : str | None
        Rename mapping string (e.g., "Na=K,Zr=Zr").
    output_prefix : str
        Prefix for renamed final outputs.
    tolerance : float
        Symmetry tolerance for spglib in macer_phonopy ru (default: 1e-3).
    """

    print("\n===== macer phonon workflow: START =====")
    input_path = Path(input_path)
    output_dir = Path.cwd()

    if output_prefix is None:
        output_prefix = input_path.stem

    # Canonical paths in output_dir
    unitcell_poscar_path = Path.cwd() / f"{input_path.stem}-symmetrized"
    supercell_poscar_path = Path.cwd() / "SPOSCAR"
    disp_dir_path = Path.cwd() / "disp"
    disp_dir_path.mkdir(exist_ok=True)
    disp_yaml_path = Path.cwd() / "phonopy_disp.yaml"
    force_sets_path = Path.cwd() / "FORCE_SETS"
    force_constants_path = Path.cwd() / "FORCE_CONSTANTS"
    band_conf_path = Path.cwd() / "band.conf"
    band_pdf_path = Path.cwd() / "band.pdf"
    band_yaml_path = Path.cwd() / "band.yaml"

    print(f"Input structure: {input_path}")
    print(f"Output directory: {Path.cwd()}")
    print(f"Displacement distance: {displacement_distance:g} Å")

    # === Step 0: Relax and Symmetrize Unit Cell ===
    print("\n--- Step 0: Relaxing and symmetrizing unit cell ---")
    unitcell_poscar_path = Path.cwd() / f"{input_path.stem}-symmetrized"
    macer_ru_command = [
        'macer_phonopy', 'ru',
        '-p', str(input_path),
        '--output-prefix', input_path.stem,
        '--tolerance', str(tolerance)
    ]
    print(f"Running command: {' '.join(macer_ru_command)}")
    try:
        subprocess.run(macer_ru_command, check=True, capture_output=True, text=True)
        print(f"Symmetrized unit cell created: {unitcell_poscar_path.name}")
        # Update input_path to the symmetrized one for subsequent steps
        input_path = unitcell_poscar_path
    except subprocess.CalledProcessError as e:
        print("Error during macer_phonopy ru execution:")
        print(e.stderr)
        return

    # === Step 1: Generate displacements with phonopy ===
    print("\n--- Step 1: Generating displacements with phonopy ---")
    try:
        unitcell = read_vasp(str(input_path))
    except Exception as e:
        print(f"Error reading input POSCAR: {e}")
        return

    cell = unitcell.cell
    vector_lengths = [np.linalg.norm(v) for v in cell]

    if any(v == 0 for v in vector_lengths):
        print("Error: One of the lattice vectors has a length of zero.")
        return

    scaling_factors = [math.ceil(min_length / v) if v > 0 else 1 for v in vector_lengths]
    supercell_matrix = np.diag(scaling_factors)

    print(f"Supercell matrix determined to be: {scaling_factors}")
    print(f"Supercell (DIM): {scaling_factors[0]} {scaling_factors[1]} {scaling_factors[2]}")

    try:
        # Build phonopy object
        phonon = Phonopy(
            unitcell,
            supercell_matrix=supercell_matrix,
            primitive_matrix="auto"
        )
        # Set displacements
        phonon.generate_displacements(
            distance=displacement_distance,
            is_plusminus=is_plusminus,
            is_diagonal=is_diagonal,
        )

        # Write SPOSCAR (symmetrized supercell)
        write_vasp(str(supercell_poscar_path), phonon.supercell, direct=True)

        # Write displaced supercells into disp/ (POSCAR-001, ...)
        displaced_cells = phonon.supercells_with_displacements
        disp_filenames_for_macer = [disp_dir_path / f'POSCAR-{i+1:03d}' for i in range(len(displaced_cells))]
        for i, cell in enumerate(displaced_cells):
            write_vasp(str(disp_filenames_for_macer[i]), cell)

        # Write phonopy.yaml
        phonon.save(str(disp_yaml_path))

        print(f"Wrote {supercell_poscar_path.name}, {disp_yaml_path.name} and displaced POSCARs in {disp_dir_path}")
    except Exception as e:
        print("Error during phonopy displacement generation:", e)
        return

    # Collect displaced POSCARs for macer relaxation
    disp_filenames_for_macer = sorted(disp_dir_path.glob("POSCAR-*"))
    sposcar_path = supercell_poscar_path

    # === Step 2: Relax structures with macer (SPOSCAR + displacements) ===
    print("\n--- Step 2: Relaxing structures with macer ---")
    print(f"Device: {macer_device}")
    if macer_model_path:
        print(f"Using macer model: {macer_model_path}")

    # Process SPOSCAR
    print(f"Relaxing {sposcar_path.name}...")
    try:
        sposcar_atoms = ase_read(str(sposcar_path))
        relax_structure(
            input_file=sposcar_atoms,
            fmax=0.01,
            smax=0.001,
            device=macer_device,
            isif=0,
            fix_axis=[],
            quiet=True,
            contcar_name=str(Path.cwd() / f"CONTCAR-{sposcar_path.name}"),
            outcar_name=str(Path.cwd() / f"OUTCAR-{sposcar_path.name}"),
            xml_name=str(Path.cwd() / f"vasprun-{sposcar_path.name}.xml"),
            make_pdf=False,
            write_json=False,
            model_path=str(macer_model_path) if macer_model_path else None
        )
        print(f"Relaxation of {sposcar_path.name} completed.")
    except Exception as e:
        print(f"Error during macer relaxation of {sposcar_path.name}: {e}")
        return

    # Process displaced POSCARs
    for disp_poscar_path in disp_filenames_for_macer:
        print(f"Relaxing {disp_poscar_path.name}...")
        try:
            disp_atoms = ase_read(str(disp_poscar_path))
            relax_structure(
                input_file=disp_atoms,
                fmax=0.01,
                smax=0.001,
                device=macer_device,
                isif=0,
                fix_axis=[],
                quiet=True,
                contcar_name=str(Path.cwd() / f"CONTCAR-{disp_poscar_path.name}"),
                outcar_name=str(Path.cwd() / f"OUTCAR-{disp_poscar_path.name}"),
                xml_name=str(Path.cwd() / "disp" / f"vasprun-{disp_poscar_path.name}.xml"),
                make_pdf=False,
                write_json=False,
                model_path=str(macer_model_path) if macer_model_path else None
            )
            print(f"Relaxation of {disp_poscar_path.name} completed.")
        except Exception as e:
            print(f"Error during macer relaxation of {disp_poscar_path.name}: {e}")
            return
    print("macer relaxation completed successfully for all structures.")

    # === Step 3: Create FORCE_SETS with phonopy API ===
    print("\n--- Step 3: Creating FORCE_SETS ---")
    vasprun_files = sorted(glob.glob(str(disp_dir_path / 'vasprun-*.xml')))
    if not vasprun_files:
        print("Error: No vasprun-*.xml files found after macer relaxation.")
        return

    try:
        phonopy_f_command = ['phonopy', '-f'] + vasprun_files
        print(f"Running command: {' '.join(phonopy_f_command)}")
        result = subprocess.run(phonopy_f_command, check=True, capture_output=True, text=True)
        print(result.stdout)
        print(f"{force_sets_path.name} created successfully.")
    except subprocess.CalledProcessError as e:
        print("Error during phonopy -f execution:")
        print(e.stderr)
        return

    # === Step 3.5: Create FORCE_CONSTANTS from FORCE_SETS ===
    print("\n--- Step 3.5: Creating FORCE_CONSTANTS ---")
    dim_string = " ".join(map(str, scaling_factors))
    phonopy_fc_command = [
        'phonopy',
        '-c', str(unitcell_poscar_path),
        '--dim', dim_string,
        '--writefc'
    ]
    print(f"Running command: {' '.join(phonopy_fc_command)}")
    try:
        # This command writes to the CWD, so we must run it in the output_dir
        subprocess.run(phonopy_fc_command, check=True, capture_output=True, text=True)
        print(f"{force_constants_path.name} created successfully.")
    except subprocess.CalledProcessError as e:
        print("Error during phonopy --writefc execution:")
        print(e.stderr)
        return

    # === Step 4: Create band.conf using macer_phonopy API ===
    print("\n--- Step 4: Creating band.conf ---")
    bp_args = SimpleNamespace(
        poscar=unitcell_poscar_path,
        yaml=str(yaml_path_arg) if yaml_path_arg else str(disp_yaml_path),  # Use provided arg or default
        out=str(out_path_arg) if out_path_arg else str(band_conf_path),     # Use provided arg or default
        gamma=gamma_label,
        symprec=symprec_seekpath,
        dim=dim_override,
        no_defaults=no_defaults_band_conf,
        atom_names=atom_names_override,
        rename=rename_override
    )
    try:
        print(f"Calling macer.phonopy.phonon_band._generate_band_conf() to create {band_conf_path.name}")
        _generate_band_conf(bp_args)  # Call the renamed function
        print(f"{band_conf_path.name} created successfully.")
    except Exception as e:
        print("Error during band.conf generation via API:")
        print(e)
        return

    # === Step 5: Plot band structure using phonopy ===
    print("\n--- Step 5: Plotting band structure ---")
    phonopy_plot_command = ['phonopy', '-p', str(band_conf_path), '-s', '-c', str(unitcell_poscar_path)]
    print(f"Running command: {' '.join(phonopy_plot_command)}")
    try:
        # This command also writes to the CWD
        result = subprocess.run(phonopy_plot_command, check=True, capture_output=True, text=True)
        print(result.stdout)
        print(f"{band_pdf_path.name} and {band_yaml_path.name} created successfully.")
    except subprocess.CalledProcessError as e:
        print("Error during phonopy plot execution:")
        print(e.stderr)
        return

    # === Step 6: Rename and Clean up ===
    print("\n--- Step 6: Renaming outputs and cleaning up ---")
    rename_map = {
        disp_yaml_path: disp_yaml_path.with_name(f"phonopy_disp-{output_prefix}.yaml"),
        force_sets_path: force_sets_path.with_name(f"FORCE_SETS_{output_prefix}"),
        force_constants_path: force_constants_path.with_name(f"FORCE_CONSTANTS_{output_prefix}"),
        band_conf_path: band_conf_path.with_name(f"band-{output_prefix}.conf"),
        band_pdf_path: band_pdf_path.with_name(f"band-{output_prefix}.pdf"),
        band_yaml_path: band_yaml_path.with_name(f"band-{output_prefix}.yaml"),
    }
    for old, new in rename_map.items():
        if old.exists():
            old.rename(new)
            print(f"Renamed {old.name} -> {new.name}")

    # Cleanup intermediate files in output_dir
    cleanup_patterns = ['vasprun-*.xml', 'OUTCAR-*', 'CONTCAR-*', 'relax-*.log.*']
    cleanup_items = [supercell_poscar_path, Path.cwd() / 'phonopy.yaml']
    for pattern in cleanup_patterns:
        cleanup_items.extend(Path.cwd().glob(pattern))

    if disp_dir_path.exists():
        shutil.rmtree(disp_dir_path)  # Remove the entire directory

    for item in cleanup_items:
        try:
            if item.is_dir():
                shutil.rmtree(item)
            elif item.exists():
                item.unlink()
        except OSError as e:
            print(f"Error cleaning up {item}: {e}")

    print(f"\nWorkflow for {input_path.name} completed.")
    print("===== macer phonon workflow: DONE =====\n")

