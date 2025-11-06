import os
import numpy as np
import xml.etree.ElementTree as ET
import json
from pymatgen.io.ase import AseAtomsAdaptor
from monty.json import MontyEncoder

def write_outcar(atoms, energy, outcar_name="OUTCAR"):
    """Write a pymatgen-parsable OUTCAR with more realistic dummy data."""
    forces = atoms.get_forces()
    cart_positions = atoms.get_positions()
    drift = np.mean(forces, axis=0)
    n_atoms = len(atoms)
    volume = atoms.get_volume()

    direct_cell = atoms.get_cell()
    reciprocal_cell = np.linalg.inv(direct_cell).T
    direct_lengths = np.linalg.norm(direct_cell, axis=1)
    reciprocal_lengths = np.linalg.norm(reciprocal_cell, axis=1)
    scaled_positions = atoms.get_scaled_positions()
    symbols = atoms.get_chemical_symbols()
    unique_symbols = sorted(list(set(symbols)))

    with open(outcar_name, "w") as f:
        # --- Dummy Header & Parameters for pymatgen parsing ---
        f.write(" vasp.6.5.0 24Aug23 (build 2023-08-24 10:00:00) complex\n")
        f.write("\n")
        for sym in unique_symbols:
            f.write(f" POTCAR:    PAW_PBE {sym.ljust(2)} 01Jan2000 (PAW_PBE {sym.ljust(2)} 01Jan2000)\n")
        f.write("\n")

        # --- Dummy INCAR section ---
        f.write(" INCAR:\n")
        f.write("   ENCUT  =      520.000\n")
        f.write("   ISMEAR =          0\n")
        f.write("   SIGMA  =        0.05\n")
        f.write("   ISIF   =          3\n")
        f.write("   IBRION =          2\n")
        f.write("\n")

        # --- Dummy Parameters section ---
        f.write(" Parameters (and plain-wave basis):\n")
        f.write(" total plane-waves  NPLWV =      10000\n")
        # --- Dummy table for per-kpoint plane waves ---
        f.write("\n\n\n" + "-"*104 + "\n\n\n")
        f.write(" k-point   1 :       0.0000    0.0000    0.0000\n")
        f.write("  number of plane waves:    10000\n\n")
        f.write(" maximum and minimum number of plane-waves:    10000   10000\n")
        f.write(f"  NELECT =    {float(n_atoms * 6):.4f}\n")
        f.write(f"    k-points           NKPTS =      1   k-points in BZ     NKDIM =      1   number of bands    NBANDS=     10\n")
        f.write(f"  NBANDS =        {n_atoms * 4}\n")
        f.write("\n")

        # --- Lattice and Geometry ---
        f.write(f" volume of cell : {volume:12.4f}\n\n")
        f.write("  direct lattice vectors                    reciprocal lattice vectors\n")
        for i in range(3):
            d = direct_cell[i]
            r = reciprocal_cell[i]
            f.write(f"    {d[0]:12.9f} {d[1]:12.9f} {d[2]:12.9f}    {r[0]:12.9f} {r[1]:12.9f} {r[2]:12.9f}\n")
        f.write("\n")
        f.write("  length of vectors\n")
        f.write(f"    {direct_lengths[0]:12.9f} {direct_lengths[1]:12.9f} {direct_lengths[2]:12.9f}    {reciprocal_lengths[0]:12.9f} {reciprocal_lengths[1]:12.9f} {reciprocal_lengths[2]:12.9f}\n")
        f.write("\n")

        # --- Dummy Electronic Structure ---
        f.write(" E-fermi :   0.0000     alpha+bet :       0.0000     alpha-bet :       0.0000\n\n")

        # --- Positions and Forces ---
        f.write("  position of ions in fractional coordinates (direct lattice)\n")
        for pos in scaled_positions:
            f.write(f"     {pos[0]:11.9f} {pos[1]:11.9f} {pos[2]:11.9f}\n")
        f.write("\n")
        f.write(" POSITION                                       TOTAL-FORCE (eV/Angst)\n")
        f.write(" -----------------------------------------------------------------------------------\n")
        for i in range(n_atoms):
            x, y, z = cart_positions[i]
            fx, fy, fz = forces[i]
            f.write(f" {x:12.5f} {y:12.5f} {z:12.5f}   {fx:12.6f} {fy:12.6f} {fz:12.6f}\n")
        f.write(" -----------------------------------------------------------------------------------\n")
        f.write(f"  total drift:                         {drift[0]:12.6f} {drift[1]:12.6f} {drift[2]:12.6f}\n\n")

        # --- Stress Tensor (converted to kB) ---
        f.write("  TOTAL-FORCE (eV/Angst)  ... external pressure =      0.00 kB  Pullay stress =      0.00 kB\n")
        f.write("  in kB         XX          YY          ZZ          XY          YZ          ZX\n")
        try:
            stress_kBar = atoms.get_stress(voigt=True) * 160.21766208 * 10
            s_vasp = [stress_kBar[0], stress_kBar[1], stress_kBar[2], stress_kBar[5], stress_kBar[3], stress_kBar[4]]
            f.write(f"  Total    {s_vasp[0]:11.4f} {s_vasp[1]:11.4f} {s_vasp[2]:11.4f} {s_vasp[3]:11.4f} {s_vasp[4]:11.4f} {s_vasp[5]:11.4f}\n")
        except Exception:
            f.write("  Total         0.0000      0.0000      0.0000      0.0000      0.0000      0.0000\n")
        f.write("\n")

        # --- Final Energy ---
        f.write(" FREE ENERGIE OF THE ION-ELECTRON SYSTEM (eV)\n")
        f.write(" ---------------------------------------------------\n")
        f.write(f"  free  energy   TOTEN  =  {energy:20.8f} eV\n")
        f.write(f"  energy  without entropy=  {energy:20.8f}  energy(sigma->0) =  {energy:20.8f}\n")
    print(f" Wrote {outcar_name} (with dummy data for pymatgen)")

def write_vasprun_xml(atoms, energy, xml_name="vasprun-mace.xml"):
    """Write vasprun.xml in phonopy-compatible minimal format."""
    forces = atoms.get_forces()
    root = ET.Element("modeling")

    # --- generator ---
    gen = ET.SubElement(root, "generator")
    ET.SubElement(gen, "i", name="program", type="string").text = "vasp"
    ET.SubElement(gen, "i", name="version", type="string").text = "6.5.0"

    # --- atominfo (간단 버전) ---
    atominfo = ET.SubElement(root, "atominfo")
    array = ET.SubElement(atominfo, "array", name="atoms")
    set_node = ET.SubElement(array, "set")
    for i, s in enumerate(atoms.get_chemical_symbols()):
        rc = ET.SubElement(set_node, "rc")
        ET.SubElement(rc, "c").text = str(i + 1)
        ET.SubElement(rc, "c").text = s

    # --- calculation ---
    calc = ET.SubElement(root, "calculation")

    # (A) structure 블록 (참고용) ── phonopy expat은 여기 '안'의 positions는 무시함
    struct = ET.SubElement(calc, "structure", name="finalpos")
    crystal = ET.SubElement(struct, "crystal")
    basis_in_struct = ET.SubElement(crystal, "varray", name="basis")
    for vec in atoms.get_cell():
        ET.SubElement(basis_in_struct, "v").text = f" {vec[0]:18.10f} {vec[1]:18.10f} {vec[2]:18.10f} "
    ET.SubElement(crystal, "i", name="volume").text = f"{atoms.get_volume():.10f}"
    pos_in_struct = ET.SubElement(struct, "varray", name="positions")
    for p in atoms.get_scaled_positions():
        ET.SubElement(pos_in_struct, "v").text = f" {p[0]:18.10f} {p[1]:18.10f} {p[2]:18.10f} "

    # (B) ★ phonopy가 실제로 읽는 부분 ★
    # 구조 블록 '밖'(=형제)으로 basis/positions를 한 번 더 씀
    basis = ET.SubElement(calc, "varray", name="basis")      # not in <structure>
    for vec in atoms.get_cell():
        ET.SubElement(basis, "v").text = f" {vec[0]:18.10f} {vec[1]:18.10f} {vec[2]:18.10f} "
    positions = ET.SubElement(calc, "varray", name="positions")  # not in <structure>
    for p in atoms.get_scaled_positions():
        ET.SubElement(positions, "v").text = f" {p[0]:18.10f} {p[1]:18.10f} {p[2]:18.10f} "

    # energy & forces (원래대로)
    energy_node = ET.SubElement(calc, "energy")
    ET.SubElement(energy_node, "i", name="e_fr_energy").text = f"{energy:.10f}"
    ET.SubElement(energy_node, "i", name="e_wo_entrp").text = f"{energy:.10f}"
    ET.SubElement(energy_node, "i", name="e_entropy").text = "0.00000000"

    forces_node = ET.SubElement(calc, "varray", name="forces")
    for f in forces:
        ET.SubElement(forces_node, "v").text = f" {f[0]:18.10f} {f[1]:18.10f} {f[2]:18.10f} "

    # --- 쓰기 (선언은 ET에 맡김: expat 오류 방지) ---
    ET.indent(root, space="  ", level=0)
    tree = ET.ElementTree(root)
    tree.write(xml_name, encoding="utf-8", xml_declaration=True)


def write_calc_results_json(atoms, energy, filename="calc_results.json"):
    """Write PyDefect-compatible calc_results.json file."""
    pmg_struct = AseAtomsAdaptor.get_structure(atoms)
    data = {
        "@module": "pydefect.analyzer.calc_results",
        "@class": "CalcResults",
        "@version": "0.9.4",
        "structure": pmg_struct.as_dict(),
        "energy": float(energy),
        "magnetization": 0.0,
        "potentials": [0.0 for _ in range(len(atoms))],
        "electronic_conv": True,
        "ionic_conv": True,
    }
    with open(filename, "w") as f:
        json.dump(data, f, cls=MontyEncoder, indent=2)
    print(f"🧩 Wrote {filename} (PyDefect-compatible)")

def write_pydefect_dummy_files(output_dir="."):
    """Write dummy files for pydefect in a specified directory."""
    json_content = '{"@module":"pydefect.analyzer.band_edge_states","@class":"PerfectBandEdgeState","@version":"0.9.7","vbm_info":{"@module":"pydefect.analyzer.band_edge_states","@class":"EdgeInfo","@version":"0.9.7","band_idx":0,"kpt_coord":[0.0,0.0,0.0],"orbital_info":{"@module":"pydefect.analyzer.band_edge_states","@class":"OrbitalInfo","@version":"0.9.7","energy":0.0,"orbitals":{},"occupation":1.0,"participation_ratio":null}},"cbm_info":{"@module":"pydefect.analyzer.band_edge_states","@class":"EdgeInfo","@version":"0.9.7","band_idx":0,"kpt_coord":[0.0,0.0,0.0],"orbital_info":{"@module":"pydefect.analyzer.band_edge_states","@class":"OrbitalInfo","@version":"0.9.7","energy":5.0,"orbitals":{},"occupation":0.0,"participation_ratio":null}}}'
    yaml_content = """system: ZnO
vbm: 0.0
cbm: 5.0
ele_dielectric_const:
- - 1.0
  - 0.0
  - 0.0
- - 0.0
  - 1.0
  - 0.0
- - 0.0
  - 0.0
  - 1.0
ion_dielectric_const:
- - 1.0
  - 0.0
  - 0.0
- - 0.0
  - 1.0
  - 0.0
- - 0.0
  - 0.0
  - 1.0
"""
    with open(os.path.join(output_dir, "perfect_band_edge_state.json"), "w") as f:
        f.write(json_content)
    with open(os.path.join(output_dir, "unitcell.yaml"), "w") as f:
        f.write(yaml_content)
