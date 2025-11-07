"""
FILE PARSERS - Chemical & Material Structure File Formats
==========================================================

Parsers for common scientific file formats:
- SDF (Structure Data File) - PubChem, ChEMBL
- MOL (MDL Molfile) - Single molecule structures
- CIF (Crystallographic Information File) - Crystal structures
- PDB (Protein Data Bank) - Protein/biomolecule structures
- XYZ - Simple Cartesian coordinates

Features:
- Fast parsing with regex
- Error handling for malformed files
- Memory-efficient streaming for large files
- Geometry extraction
- Property parsing

Author: Materials-SimPro Team
Date: 2025-11-04
"""

import re
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Iterator, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class Atom:
    """Atomic position and properties"""
    element: str
    position: np.ndarray  # [x, y, z]
    charge: float = 0.0
    index: int = 0


@dataclass
class Molecule:
    """Molecular structure"""
    name: str
    formula: str
    atoms: List[Atom]
    bonds: List[Tuple[int, int, int]]  # [(atom1, atom2, bond_order)]
    properties: Dict[str, any]


@dataclass
class Crystal:
    """Crystal structure"""
    name: str
    formula: str
    lattice_params: np.ndarray  # [a, b, c, alpha, beta, gamma]
    space_group: str
    atoms: List[Atom]
    properties: Dict[str, any]


class SDFParser:
    """
    SDF (Structure Data File) Parser

    Format used by PubChem, ChEMBL, ZINC for bulk molecule distribution
    Supports multiple molecules per file (SD file)

    Format specification: http://c4.cabrillo.edu/404/ctfile.pdf
    """

    @staticmethod
    def parse_file(filepath: str) -> Iterator[Molecule]:
        """
        Parse SDF file and yield molecules

        Args:
            filepath: Path to .sdf file

        Yields:
            Molecule objects
        """
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            current_block = []

            for line in f:
                current_block.append(line)

                # SDF delimiter
                if line.strip() == "$$$$":
                    if len(current_block) > 3:
                        mol = SDFParser._parse_mol_block(current_block)
                        if mol:
                            yield mol
                    current_block = []

            # Last molecule if file doesn't end with $$$$
            if len(current_block) > 3:
                mol = SDFParser._parse_mol_block(current_block)
                if mol:
                    yield mol

    @staticmethod
    def _parse_mol_block(lines: List[str]) -> Optional[Molecule]:
        """Parse single MOL block from SDF"""
        try:
            # Line 1: Molecule name
            name = lines[0].strip() if lines else "Unknown"

            # Line 4: Counts line (V2000 format)
            if len(lines) < 4:
                return None

            counts_line = lines[3]
            try:
                num_atoms = int(counts_line[0:3])
                num_bonds = int(counts_line[3:6])
            except (ValueError, IndexError):
                return None

            # Parse atoms
            atoms = []
            atom_start = 4
            for i in range(num_atoms):
                if atom_start + i >= len(lines):
                    break

                atom_line = lines[atom_start + i]
                if len(atom_line) < 39:
                    continue

                try:
                    x = float(atom_line[0:10])
                    y = float(atom_line[10:20])
                    z = float(atom_line[20:30])
                    element = atom_line[31:34].strip()

                    atoms.append(Atom(
                        element=element,
                        position=np.array([x, y, z]),
                        index=i
                    ))
                except (ValueError, IndexError):
                    continue

            # Parse bonds
            bonds = []
            bond_start = atom_start + num_atoms
            for i in range(num_bonds):
                if bond_start + i >= len(lines):
                    break

                bond_line = lines[bond_start + i]
                if len(bond_line) < 9:
                    continue

                try:
                    atom1 = int(bond_line[0:3]) - 1  # 0-indexed
                    atom2 = int(bond_line[3:6]) - 1
                    bond_order = int(bond_line[6:9])
                    bonds.append((atom1, atom2, bond_order))
                except (ValueError, IndexError):
                    continue

            # Parse properties (after M  END)
            properties = {}
            in_properties = False
            for line in lines[bond_start + num_bonds:]:
                if line.strip() == "M  END":
                    in_properties = True
                    continue

                if in_properties and line.startswith(">"):
                    # Property header: > <PROPERTY_NAME>
                    prop_name = re.search(r'<(.+?)>', line)
                    if prop_name:
                        prop_name = prop_name.group(1)
                        # Next line has value
                        idx = lines.index(line) + 1
                        if idx < len(lines):
                            properties[prop_name] = lines[idx].strip()

            # Calculate formula from atoms
            element_counts = {}
            for atom in atoms:
                element_counts[atom.element] = element_counts.get(atom.element, 0) + 1

            # Sort formula: C, H, then alphabetical
            formula_parts = []
            for element in ['C', 'H']:
                if element in element_counts:
                    count = element_counts[element]
                    formula_parts.append(f"{element}{count if count > 1 else ''}")
                    del element_counts[element]

            for element in sorted(element_counts.keys()):
                count = element_counts[element]
                formula_parts.append(f"{element}{count if count > 1 else ''}")

            formula = ''.join(formula_parts)

            return Molecule(
                name=name,
                formula=formula,
                atoms=atoms,
                bonds=bonds,
                properties=properties
            )

        except Exception as e:
            logger.warning(f"Error parsing MOL block: {e}")
            return None


class CIFParser:
    """
    CIF (Crystallographic Information File) Parser

    Format used for crystal structures (ICSD, COD, Materials Project)

    Format specification: https://www.iucr.org/resources/cif
    """

    @staticmethod
    def parse_file(filepath: str) -> Optional[Crystal]:
        """
        Parse CIF file

        Args:
            filepath: Path to .cif file

        Returns:
            Crystal object or None
        """
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        return CIFParser._parse_cif_content(content)

    @staticmethod
    def _parse_cif_content(content: str) -> Optional[Crystal]:
        """Parse CIF file content"""
        try:
            # Extract key parameters
            name = CIFParser._extract_value(content, r'_chemical_name_systematic\s+[\'"]?(.+?)[\'"]?\s*\n')
            if not name:
                name = CIFParser._extract_value(content, r'_chemical_formula_sum\s+[\'"]?(.+?)[\'"]?\s*\n')

            formula = CIFParser._extract_value(content, r'_chemical_formula_sum\s+[\'"]?(.+?)[\'"]?\s*\n')
            space_group = CIFParser._extract_value(content, r'_space_group_name_H-M_alt\s+[\'"]?(.+?)[\'"]?\s*\n')

            # Lattice parameters
            a = float(CIFParser._extract_value(content, r'_cell_length_a\s+([\d.]+)') or 0)
            b = float(CIFParser._extract_value(content, r'_cell_length_b\s+([\d.]+)') or 0)
            c = float(CIFParser._extract_value(content, r'_cell_length_c\s+([\d.]+)') or 0)
            alpha = float(CIFParser._extract_value(content, r'_cell_angle_alpha\s+([\d.]+)') or 90)
            beta = float(CIFParser._extract_value(content, r'_cell_angle_beta\s+([\d.]+)') or 90)
            gamma = float(CIFParser._extract_value(content, r'_cell_angle_gamma\s+([\d.]+)') or 90)

            lattice_params = np.array([a, b, c, alpha, beta, gamma])

            # Parse atomic positions
            atoms = CIFParser._parse_atom_sites(content)

            return Crystal(
                name=name or "Unknown",
                formula=formula or "Unknown",
                lattice_params=lattice_params,
                space_group=space_group or "Unknown",
                atoms=atoms,
                properties={}
            )

        except Exception as e:
            logger.error(f"Error parsing CIF: {e}")
            return None

    @staticmethod
    def _extract_value(content: str, pattern: str) -> Optional[str]:
        """Extract value using regex"""
        match = re.search(pattern, content, re.IGNORECASE)
        return match.group(1).strip() if match else None

    @staticmethod
    def _parse_atom_sites(content: str) -> List[Atom]:
        """Parse atom site coordinates from CIF"""
        atoms = []

        # Find atom_site loop
        loop_match = re.search(r'loop_\s+_atom_site.*?\n(.*?)(?=loop_|\ndata_|\Z)', content, re.DOTALL)
        if not loop_match:
            return atoms

        lines = loop_match.group(1).strip().split('\n')

        for line in lines:
            parts = line.split()
            if len(parts) >= 6:  # label, type, fract_x, fract_y, fract_z, occupancy
                try:
                    element = parts[1]
                    x = float(parts[2])
                    y = float(parts[3])
                    z = float(parts[4])

                    atoms.append(Atom(
                        element=element,
                        position=np.array([x, y, z]),
                        index=len(atoms)
                    ))
                except (ValueError, IndexError):
                    continue

        return atoms


class PDBParser:
    """
    PDB (Protein Data Bank) Parser

    Format for protein and biomolecule structures

    Format specification: https://www.wwpdb.org/documentation/file-format
    """

    @staticmethod
    def parse_file(filepath: str) -> Optional[Molecule]:
        """
        Parse PDB file

        Args:
            filepath: Path to .pdb file

        Returns:
            Molecule object or None
        """
        atoms = []
        name = "Unknown"
        formula = ""

        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                # HEADER line
                if line.startswith("HEADER"):
                    name = line[10:50].strip()

                # COMPND line (compound name)
                elif line.startswith("COMPND"):
                    if not name or name == "Unknown":
                        name = line[10:].strip()

                # ATOM/HETATM lines
                elif line.startswith("ATOM") or line.startswith("HETATM"):
                    try:
                        element = line[76:78].strip()
                        if not element:  # Fallback to atom name
                            element = line[12:16].strip()[0]

                        x = float(line[30:38])
                        y = float(line[38:46])
                        z = float(line[46:54])

                        atoms.append(Atom(
                            element=element,
                            position=np.array([x, y, z]),
                            index=len(atoms)
                        ))
                    except (ValueError, IndexError):
                        continue

        # Calculate formula
        element_counts = {}
        for atom in atoms:
            element_counts[atom.element] = element_counts.get(atom.element, 0) + 1

        formula_parts = []
        for element in sorted(element_counts.keys()):
            count = element_counts[element]
            formula_parts.append(f"{element}{count if count > 1 else ''}")

        formula = ''.join(formula_parts)

        return Molecule(
            name=name,
            formula=formula,
            atoms=atoms,
            bonds=[],  # PDB doesn't usually contain bond information
            properties={'num_atoms': len(atoms)}
        )


class XYZParser:
    """
    XYZ Format Parser

    Simple Cartesian coordinate format

    Format:
    Line 1: Number of atoms
    Line 2: Comment line
    Lines 3+: Element X Y Z
    """

    @staticmethod
    def parse_file(filepath: str) -> Optional[Molecule]:
        """
        Parse XYZ file

        Args:
            filepath: Path to .xyz file

        Returns:
            Molecule object or None
        """
        atoms = []

        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()

        if len(lines) < 3:
            return None

        try:
            num_atoms = int(lines[0].strip())
            name = lines[1].strip()

            for i in range(2, 2 + num_atoms):
                if i >= len(lines):
                    break

                parts = lines[i].split()
                if len(parts) < 4:
                    continue

                element = parts[0]
                x = float(parts[1])
                y = float(parts[2])
                z = float(parts[3])

                atoms.append(Atom(
                    element=element,
                    position=np.array([x, y, z]),
                    index=len(atoms)
                ))

            # Calculate formula
            element_counts = {}
            for atom in atoms:
                element_counts[atom.element] = element_counts.get(atom.element, 0) + 1

            formula_parts = []
            for element in sorted(element_counts.keys()):
                count = element_counts[element]
                formula_parts.append(f"{element}{count if count > 1 else ''}")

            formula = ''.join(formula_parts)

            return Molecule(
                name=name or "Unknown",
                formula=formula,
                atoms=atoms,
                bonds=[],
                properties={}
            )

        except (ValueError, IndexError) as e:
            logger.error(f"Error parsing XYZ file: {e}")
            return None


def test_parsers():
    """Test file parsers with sample data"""
    print("FILE PARSER TESTS")
    print("=" * 70)

    # Test SDF parser with sample MOL data
    print("\n1. Testing SDF/MOL Parser...")
    sample_mol = """aspirin
  -OEChem-11042502283D

 21 21  0     0  0  0  0  0  0999 V2000
    1.2333    0.5540    0.7792 O   0  0  0  0  0  0  0  0  0  0  0  0
   -0.6952   -2.7148   -0.7502 O   0  0  0  0  0  0  0  0  0  0  0  0
    0.7958   -2.1843    0.8685 O   0  0  0  0  0  0  0  0  0  0  0  0
    1.7813    0.8105   -1.4821 O   0  0  0  0  0  0  0  0  0  0  0  0
   -0.0857    0.6088    0.4403 C   0  0  0  0  0  0  0  0  0  0  0  0
   -0.7927   -0.5515    0.1244 C   0  0  0  0  0  0  0  0  0  0  0  0
   -0.7288    1.8464    0.4133 C   0  0  0  0  0  0  0  0  0  0  0  0
   -2.1426   -0.4741   -0.2184 C   0  0  0  0  0  0  0  0  0  0  0  0
   -2.0787    1.9238    0.0706 C   0  0  0  0  0  0  0  0  0  0  0  0
   -2.7855    0.7636   -0.2453 C   0  0  0  0  0  0  0  0  0  0  0  0
   -0.1409   -1.8536    0.1477 C   0  0  0  0  0  0  0  0  0  0  0  0
    2.1094    0.6715   -0.3113 C   0  0  0  0  0  0  0  0  0  0  0  0
    3.5305    0.5996    0.1635 C   0  0  0  0  0  0  0  0  0  0  0  0
   -0.1851    2.7545    0.6593 H   0  0  0  0  0  0  0  0  0  0  0  0
   -2.6621   -1.3908   -0.4564 H   0  0  0  0  0  0  0  0  0  0  0  0
   -2.5797    2.8872    0.0506 H   0  0  0  0  0  0  0  0  0  0  0  0
   -3.8374    0.8238   -0.5090 H   0  0  0  0  0  0  0  0  0  0  0  0
    3.7290    1.4184    0.8593 H   0  0  0  0  0  0  0  0  0  0  0  0
    4.2045    0.6969   -0.6924 H   0  0  0  0  0  0  0  0  0  0  0  0
    3.7105   -0.3659    0.6426 H   0  0  0  0  0  0  0  0  0  0  0  0
    1.7837   -0.0736   -2.1318 H   0  0  0  0  0  0  0  0  0  0  0  0
  1  5  1  0  0  0  0
  1 12  1  0  0  0  0
  2 11  2  0  0  0  0
  3 11  1  0  0  0  0
  4 12  1  0  0  0  0
  4 21  1  0  0  0  0
  5  6  2  0  0  0  0
  5  7  1  0  0  0  0
  6  8  1  0  0  0  0
  6 11  1  0  0  0  0
  7  9  2  0  0  0  0
  7 14  1  0  0  0  0
  8 10  2  0  0  0  0
  8 15  1  0  0  0  0
  9 10  1  0  0  0  0
  9 16  1  0  0  0  0
 10 17  1  0  0  0  0
 12 13  1  0  0  0  0
 13 18  1  0  0  0  0
 13 19  1  0  0  0  0
 13 20  1  0  0  0  0
M  END
> <PUBCHEM_COMPOUND_CID>
2244

> <PUBCHEM_MOLECULAR_FORMULA>
C9H8O4

> <PUBCHEM_MOLECULAR_WEIGHT>
180.16

$$$$
"""

    # Save to temp file
    temp_file = Path("temp_test.sdf")
    temp_file.write_text(sample_mol)

    sdf_parser = SDFParser()
    for mol in sdf_parser.parse_file(str(temp_file)):
        print(f"   [OK] Parsed: {mol.name}")
        print(f"        Formula: {mol.formula}")
        print(f"        Atoms: {len(mol.atoms)}")
        print(f"        Bonds: {len(mol.bonds)}")
        print(f"        Properties: {list(mol.properties.keys())}")

    temp_file.unlink()

    print("\n" + "=" * 70)
    print("FILE PARSER TESTS COMPLETE")


if __name__ == "__main__":
    test_parsers()
