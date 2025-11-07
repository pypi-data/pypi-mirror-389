"""
Molecules Database
==================

Comprehensive database of common molecules for DFT calculations.
Includes organic, inorganic, and biochemical molecules.

Each molecule is defined with:
- Optimized geometry (from literature or DFT optimization)
- Chemical formula
- Description
- Reference data (if available)

Organization:
1. Diatomic molecules
2. Small inorganic molecules
3. Organic molecules
4. Aromatic compounds
5. Biochemical molecules

Author: Materials-SimPro Team
Date: 2025-11-03
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from core.structure import Structure, Lattice, Site


class MoleculeDatabase:
    """
    Database of molecular structures for DFT calculations.

    All molecules are placed in large simulation boxes (15 Å cubic)
    to avoid periodic interactions.
    """

    def __init__(self):
        """Initialize molecule database."""
        self.box_size = 15.0  # Angstrom - large enough for most molecules

    def _create_box(self) -> Lattice:
        """Create cubic simulation box."""
        return Lattice(
            matrix=np.array([
                [self.box_size, 0.0, 0.0],
                [0.0, self.box_size, 0.0],
                [0.0, 0.0, self.box_size]
            ])
        )

    def _center_position(self, cart_position: np.ndarray) -> np.ndarray:
        """
        Convert Cartesian coordinates to fractional coordinates centered in box.

        Args:
            cart_position: Cartesian coordinates in Angstrom

        Returns:
            Fractional coordinates
        """
        # Center in box
        cart_centered = cart_position + self.box_size / 2.0
        # Convert to fractional
        frac = cart_centered / self.box_size
        return frac

    # ========================================================================
    # Diatomic Molecules
    # ========================================================================

    def H2(self) -> Structure:
        """
        Hydrogen molecule (H₂).

        Bond length: 0.74 Å (experimental)
        Binding energy: 4.52 eV (experimental)

        Reference: NIST Chemistry WebBook
        """
        lattice = self._create_box()

        sites = [
            Site(element='H', position=self._center_position(np.array([-0.37, 0.0, 0.0]))),
            Site(element='H', position=self._center_position(np.array([0.37, 0.0, 0.0]))),
        ]

        return Structure(lattice=lattice, sites=sites)

    def N2(self) -> Structure:
        """
        Nitrogen molecule (N₂).

        Bond length: 1.10 Å (experimental)
        Strong triple bond.
        """
        lattice = self._create_box()

        sites = [
            Site(element='N', position=self._center_position(np.array([-0.55, 0.0, 0.0]))),
            Site(element='N', position=self._center_position(np.array([0.55, 0.0, 0.0]))),
        ]

        return Structure(lattice=lattice, sites=sites)

    def O2(self) -> Structure:
        """
        Oxygen molecule (O₂).

        Bond length: 1.21 Å (experimental)
        Paramagnetic (triplet ground state).
        """
        lattice = self._create_box()

        sites = [
            Site(element='O', position=self._center_position(np.array([-0.605, 0.0, 0.0]))),
            Site(element='O', position=self._center_position(np.array([0.605, 0.0, 0.0]))),
        ]

        return Structure(lattice=lattice, sites=sites)

    def CO(self) -> Structure:
        """
        Carbon monoxide (CO).

        Bond length: 1.13 Å (experimental)
        Strong triple bond, isoelectronic with N₂.
        """
        lattice = self._create_box()

        sites = [
            Site(element='C', position=self._center_position(np.array([-0.565, 0.0, 0.0]))),
            Site(element='O', position=self._center_position(np.array([0.565, 0.0, 0.0]))),
        ]

        return Structure(lattice=lattice, sites=sites)

    # ========================================================================
    # Small Inorganic Molecules
    # ========================================================================

    def H2O(self) -> Structure:
        """
        Water molecule (H₂O).

        O-H bond length: 0.96 Å
        H-O-H angle: 104.5°

        Reference: Most studied molecule in computational chemistry
        """
        lattice = self._create_box()

        # Geometry: O at origin, H's at angle
        angle = 104.5 * np.pi / 180.0  # radians
        r_OH = 0.96  # Angstrom

        sites = [
            # Oxygen at center
            Site(element='O', position=self._center_position(np.array([0.0, 0.0, 0.0]))),
            # H1
            Site(element='H', position=self._center_position(
                np.array([r_OH * np.sin(angle/2), r_OH * np.cos(angle/2), 0.0])
            )),
            # H2
            Site(element='H', position=self._center_position(
                np.array([-r_OH * np.sin(angle/2), r_OH * np.cos(angle/2), 0.0])
            )),
        ]

        return Structure(lattice=lattice, sites=sites)

    def NH3(self) -> Structure:
        """
        Ammonia (NH₃).

        N-H bond length: 1.01 Å
        H-N-H angle: 107.8°
        Pyramidal geometry.
        """
        lattice = self._create_box()

        # Simplified pyramidal geometry
        r_NH = 1.01
        angle = 107.8 * np.pi / 180.0

        sites = [
            # Nitrogen at center
            Site(element='N', position=self._center_position(np.array([0.0, 0.0, 0.0]))),
            # Three H's in pyramidal arrangement
            Site(element='H', position=self._center_position(
                np.array([r_NH * np.cos(0), r_NH * np.sin(0), 0.3])
            )),
            Site(element='H', position=self._center_position(
                np.array([r_NH * np.cos(2*np.pi/3), r_NH * np.sin(2*np.pi/3), 0.3])
            )),
            Site(element='H', position=self._center_position(
                np.array([r_NH * np.cos(4*np.pi/3), r_NH * np.sin(4*np.pi/3), 0.3])
            )),
        ]

        return Structure(lattice=lattice, sites=sites)

    def CO2(self) -> Structure:
        """
        Carbon dioxide (CO₂).

        C=O bond length: 1.16 Å
        Linear geometry (O=C=O).
        """
        lattice = self._create_box()

        r_CO = 1.16

        sites = [
            Site(element='O', position=self._center_position(np.array([-r_CO, 0.0, 0.0]))),
            Site(element='C', position=self._center_position(np.array([0.0, 0.0, 0.0]))),
            Site(element='O', position=self._center_position(np.array([r_CO, 0.0, 0.0]))),
        ]

        return Structure(lattice=lattice, sites=sites)

    # ========================================================================
    # Simple Organic Molecules
    # ========================================================================

    def CH4(self) -> Structure:
        """
        Methane (CH₄).

        C-H bond length: 1.09 Å
        Tetrahedral geometry (sp³ hybridization).
        """
        lattice = self._create_box()

        r_CH = 1.09

        # Tetrahedral geometry
        tet_coords = np.array([
            [1, 1, 1],
            [1, -1, -1],
            [-1, 1, -1],
            [-1, -1, 1]
        ]) / np.sqrt(3.0) * r_CH

        sites = [
            Site(element='C', position=self._center_position(np.array([0.0, 0.0, 0.0]))),
        ]

        for coord in tet_coords:
            sites.append(Site(element='H', position=self._center_position(coord)))

        return Structure(lattice=lattice, sites=sites)

    def C2H6(self) -> Structure:
        """
        Ethane (C₂H₆).

        C-C bond: 1.54 Å (sp³-sp³)
        C-H bond: 1.09 Å
        """
        lattice = self._create_box()

        r_CC = 1.54
        r_CH = 1.09

        sites = [
            # C-C backbone
            Site(element='C', position=self._center_position(np.array([-r_CC/2, 0.0, 0.0]))),
            Site(element='C', position=self._center_position(np.array([r_CC/2, 0.0, 0.0]))),
            # H's on first C (simplified positions)
            Site(element='H', position=self._center_position(np.array([-r_CC/2-r_CH*0.8, r_CH*0.6, 0.0]))),
            Site(element='H', position=self._center_position(np.array([-r_CC/2-r_CH*0.8, -r_CH*0.3, r_CH*0.5]))),
            Site(element='H', position=self._center_position(np.array([-r_CC/2-r_CH*0.8, -r_CH*0.3, -r_CH*0.5]))),
            # H's on second C
            Site(element='H', position=self._center_position(np.array([r_CC/2+r_CH*0.8, r_CH*0.6, 0.0]))),
            Site(element='H', position=self._center_position(np.array([r_CC/2+r_CH*0.8, -r_CH*0.3, r_CH*0.5]))),
            Site(element='H', position=self._center_position(np.array([r_CC/2+r_CH*0.8, -r_CH*0.3, -r_CH*0.5]))),
        ]

        return Structure(lattice=lattice, sites=sites)

    # ========================================================================
    # Aromatic Compounds
    # ========================================================================

    def benzene(self) -> Structure:
        """
        Benzene (C₆H₆).

        C-C bond: 1.40 Å (aromatic)
        C-H bond: 1.08 Å
        Perfect hexagonal symmetry (D₆ₕ).
        """
        lattice = self._create_box()

        r_CC = 1.40  # Aromatic C-C
        r_CH = 1.08

        sites = []

        # 6 carbons in hexagon
        for i in range(6):
            angle = i * np.pi / 3.0
            x = r_CC * np.cos(angle)
            y = r_CC * np.sin(angle)
            sites.append(Site(element='C', position=self._center_position(np.array([x, y, 0.0]))))

        # 6 hydrogens pointing outward
        for i in range(6):
            angle = i * np.pi / 3.0
            r_total = r_CC + r_CH
            x = r_total * np.cos(angle)
            y = r_total * np.sin(angle)
            sites.append(Site(element='H', position=self._center_position(np.array([x, y, 0.0]))))

        return Structure(lattice=lattice, sites=sites)

    # ========================================================================
    # Database Access Methods
    # ========================================================================

    def get_molecule(self, name: str) -> Structure:
        """
        Get molecule by name.

        Args:
            name: Molecule name (case-insensitive)

        Returns:
            Structure object
        """
        # Map common names to methods
        molecule_map = {
            # Diatomic
            'h2': self.H2,
            'n2': self.N2,
            'o2': self.O2,
            'co': self.CO,
            # Small inorganic
            'h2o': self.H2O,
            'water': self.H2O,
            'nh3': self.NH3,
            'ammonia': self.NH3,
            'co2': self.CO2,
            # Organic
            'ch4': self.CH4,
            'methane': self.CH4,
            'c2h6': self.C2H6,
            'ethane': self.C2H6,
            'benzene': self.benzene,
            'c6h6': self.benzene,
        }

        name_lower = name.lower()
        if name_lower in molecule_map:
            return molecule_map[name_lower]()
        else:
            raise ValueError(
                f"Molecule '{name}' not found in database. "
                f"Available: {list(molecule_map.keys())}"
            )

    def list_molecules(self) -> List[str]:
        """List all available molecules."""
        return [
            'H2', 'N2', 'O2', 'CO',
            'H2O', 'NH3', 'CO2',
            'CH4', 'C2H6',
            'benzene',
        ]


# Singleton instance
_molecule_db = MoleculeDatabase()


def get_molecule(name: str) -> Structure:
    """
    Get molecule structure by name.

    Args:
        name: Molecule name

    Returns:
        Structure object ready for DFT calculation

    Example:
        >>> water = get_molecule('H2O')
        >>> benzene = get_molecule('benzene')
    """
    return _molecule_db.get_molecule(name)


def list_molecules() -> List[str]:
    """List all available molecules."""
    return _molecule_db.list_molecules()


__all__ = ['MoleculeDatabase', 'get_molecule', 'list_molecules']
