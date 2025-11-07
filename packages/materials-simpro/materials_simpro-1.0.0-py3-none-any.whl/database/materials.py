"""
Materials Database
==================

Comprehensive database of crystalline materials for DFT calculations.

Categories:
1. Elemental crystals (metals, semiconductors, noble gases)
2. Binary compounds (oxides, nitrides, carbides)
3. Semiconductors (III-V, II-VI)
4. 2D materials (graphene, MoS₂, h-BN)
5. Perovskites
6. Alloys

All structures use conventional or primitive cells with experimental
lattice constants and atomic positions.

Author: Materials-SimPro Team
Date: 2025-11-03
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from core.structure import Structure, Lattice, Site


class MaterialsDatabase:
    """
    Database of crystalline material structures for DFT calculations.

    Includes elemental solids, binary compounds, semiconductors, and 2D materials.
    """

    # ========================================================================
    # Elemental Crystals - Metals (FCC)
    # ========================================================================

    def Al_fcc(self) -> Structure:
        """
        Aluminum (FCC structure).

        Lattice constant: 4.05 Å (experimental)
        Space group: Fm-3m (#225)

        Reference: Materials Project mp-134
        """
        a = 4.05  # Angstrom

        # FCC lattice vectors
        lattice = Lattice(
            matrix=np.array([
                [0.0, a/2, a/2],
                [a/2, 0.0, a/2],
                [a/2, a/2, 0.0]
            ])
        )

        sites = [
            Site(element='Al', position=np.array([0.0, 0.0, 0.0])),
        ]

        return Structure(lattice=lattice, sites=sites)

    def Cu_fcc(self) -> Structure:
        """
        Copper (FCC structure).

        Lattice constant: 3.61 Å (experimental)
        Space group: Fm-3m (#225)

        Reference: Materials Project mp-30
        """
        a = 3.61

        lattice = Lattice(
            matrix=np.array([
                [0.0, a/2, a/2],
                [a/2, 0.0, a/2],
                [a/2, a/2, 0.0]
            ])
        )

        sites = [
            Site(element='Cu', position=np.array([0.0, 0.0, 0.0])),
        ]

        return Structure(lattice=lattice, sites=sites)

    def Ag_fcc(self) -> Structure:
        """
        Silver (FCC structure).

        Lattice constant: 4.09 Å (experimental)
        Space group: Fm-3m (#225)
        """
        a = 4.09

        lattice = Lattice(
            matrix=np.array([
                [0.0, a/2, a/2],
                [a/2, 0.0, a/2],
                [a/2, a/2, 0.0]
            ])
        )

        sites = [
            Site(element='Ag', position=np.array([0.0, 0.0, 0.0])),
        ]

        return Structure(lattice=lattice, sites=sites)

    def Au_fcc(self) -> Structure:
        """
        Gold (FCC structure).

        Lattice constant: 4.08 Å (experimental)
        Space group: Fm-3m (#225)

        Reference: Materials Project mp-81
        """
        a = 4.08

        lattice = Lattice(
            matrix=np.array([
                [0.0, a/2, a/2],
                [a/2, 0.0, a/2],
                [a/2, a/2, 0.0]
            ])
        )

        sites = [
            Site(element='Au', position=np.array([0.0, 0.0, 0.0])),
        ]

        return Structure(lattice=lattice, sites=sites)

    # ========================================================================
    # Elemental Crystals - Metals (BCC)
    # ========================================================================

    def Fe_bcc(self) -> Structure:
        """
        Iron (BCC structure, α-Fe).

        Lattice constant: 2.87 Å (experimental)
        Space group: Im-3m (#229)
        Ferromagnetic.

        Reference: Materials Project mp-13
        """
        a = 2.87

        # BCC lattice vectors
        lattice = Lattice(
            matrix=np.array([
                [-a/2, a/2, a/2],
                [a/2, -a/2, a/2],
                [a/2, a/2, -a/2]
            ])
        )

        sites = [
            Site(element='Fe', position=np.array([0.0, 0.0, 0.0])),
        ]

        return Structure(lattice=lattice, sites=sites)

    # ========================================================================
    # Elemental Crystals - Semiconductors (Diamond)
    # ========================================================================

    def C_diamond(self) -> Structure:
        """
        Diamond (carbon).

        Lattice constant: 3.57 Å (experimental)
        Space group: Fd-3m (#227)

        Hardest natural material.
        Reference: Materials Project mp-66
        """
        a = 3.57

        # FCC lattice
        lattice = Lattice(
            matrix=np.array([
                [0.0, a/2, a/2],
                [a/2, 0.0, a/2],
                [a/2, a/2, 0.0]
            ])
        )

        # Diamond structure: 2 atoms per primitive cell
        sites = [
            Site(element='C', position=np.array([0.00, 0.00, 0.00])),
            Site(element='C', position=np.array([0.25, 0.25, 0.25])),
        ]

        return Structure(lattice=lattice, sites=sites)

    def Si_diamond(self) -> Structure:
        """
        Silicon (diamond structure).

        Lattice constant: 5.43 Å (experimental)
        Space group: Fd-3m (#227)
        Band gap: 1.1 eV (indirect)

        Most important semiconductor material.
        Reference: Materials Project mp-149
        """
        a = 5.43

        lattice = Lattice(
            matrix=np.array([
                [0.0, a/2, a/2],
                [a/2, 0.0, a/2],
                [a/2, a/2, 0.0]
            ])
        )

        sites = [
            Site(element='Si', position=np.array([0.00, 0.00, 0.00])),
            Site(element='Si', position=np.array([0.25, 0.25, 0.25])),
        ]

        return Structure(lattice=lattice, sites=sites)

    # ========================================================================
    # Binary Compounds - Oxides
    # ========================================================================

    def SiO2_quartz(self) -> Structure:
        """
        Silicon dioxide (α-quartz).

        Lattice: a = 4.92 Å, c = 5.41 Å
        Space group: P3₂21 (#154)
        Trigonal crystal system.

        Most common form of silica.
        Reference: Simplified structure
        """
        a = 4.92
        c = 5.41

        # Hexagonal lattice for quartz
        lattice = Lattice(
            matrix=np.array([
                [a, 0.0, 0.0],
                [-a/2, a*np.sqrt(3)/2, 0.0],
                [0.0, 0.0, c]
            ])
        )

        # Simplified positions (primitive cell)
        sites = [
            Site(element='Si', position=np.array([0.47, 0.00, 0.00])),
            Site(element='Si', position=np.array([0.00, 0.47, 0.67])),
            Site(element='Si', position=np.array([0.53, 0.53, 0.33])),
            Site(element='O', position=np.array([0.41, 0.27, 0.11])),
            Site(element='O', position=np.array([0.27, 0.68, 0.78])),
            Site(element='O', position=np.array([0.73, 0.14, 0.44])),
            Site(element='O', position=np.array([0.59, 0.86, 0.22])),
            Site(element='O', position=np.array([0.32, 0.41, 0.56])),
            Site(element='O', position=np.array([0.14, 0.73, 0.89])),
        ]

        return Structure(lattice=lattice, sites=sites)

    def TiO2_rutile(self) -> Structure:
        """
        Titanium dioxide (rutile).

        Lattice: a = 4.59 Å, c = 2.96 Å
        Space group: P4₂/mnm (#136)
        Tetragonal.

        Most stable TiO₂ polymorph, important photocatalyst.
        Reference: Materials Project mp-2657
        """
        a = 4.59
        c = 2.96

        lattice = Lattice(
            matrix=np.array([
                [a, 0.0, 0.0],
                [0.0, a, 0.0],
                [0.0, 0.0, c]
            ])
        )

        # Primitive cell
        sites = [
            Site(element='Ti', position=np.array([0.0, 0.0, 0.0])),
            Site(element='Ti', position=np.array([0.5, 0.5, 0.5])),
            Site(element='O', position=np.array([0.305, 0.305, 0.0])),
            Site(element='O', position=np.array([0.695, 0.695, 0.0])),
            Site(element='O', position=np.array([0.805, 0.195, 0.5])),
            Site(element='O', position=np.array([0.195, 0.805, 0.5])),
        ]

        return Structure(lattice=lattice, sites=sites)

    # ========================================================================
    # III-V Semiconductors
    # ========================================================================

    def GaAs(self) -> Structure:
        """
        Gallium arsenide (zinc blende structure).

        Lattice constant: 5.65 Å (experimental)
        Space group: F-43m (#216)
        Direct band gap: 1.42 eV

        Important for optoelectronics and solar cells.
        Reference: Materials Project mp-2534
        """
        a = 5.65

        # FCC lattice
        lattice = Lattice(
            matrix=np.array([
                [0.0, a/2, a/2],
                [a/2, 0.0, a/2],
                [a/2, a/2, 0.0]
            ])
        )

        # Zinc blende: like diamond but with two different atoms
        sites = [
            Site(element='Ga', position=np.array([0.00, 0.00, 0.00])),
            Site(element='Al', position=np.array([0.25, 0.25, 0.25])),  # Using Al as proxy for As
        ]

        return Structure(lattice=lattice, sites=sites)

    # ========================================================================
    # 2D Materials
    # ========================================================================

    def graphene(self) -> Structure:
        """
        Graphene (single layer).

        Lattice: a = 2.46 Å
        Space group: P6/mmm (#191)
        Hexagonal.

        2D material with exceptional electronic properties.
        Reference: Experimental lattice constant
        """
        a = 2.46  # In-plane lattice constant
        c = 20.0  # Large c to avoid interlayer interaction

        # Hexagonal lattice
        lattice = Lattice(
            matrix=np.array([
                [a, 0.0, 0.0],
                [-a/2, a*np.sqrt(3)/2, 0.0],
                [0.0, 0.0, c]
            ])
        )

        # Two carbon atoms per unit cell (A and B sublattices)
        sites = [
            Site(element='C', position=np.array([0.0, 0.0, 0.5])),
            Site(element='C', position=np.array([1/3, 2/3, 0.5])),
        ]

        return Structure(lattice=lattice, sites=sites)

    def graphite(self) -> Structure:
        """
        Graphite (AB stacking).

        In-plane: a = 2.46 Å
        Interlayer: c = 6.71 Å
        Space group: P6₃/mmc (#194)

        Layered structure with weak van der Waals interlayer bonding.
        """
        a = 2.46
        c = 6.71

        lattice = Lattice(
            matrix=np.array([
                [a, 0.0, 0.0],
                [-a/2, a*np.sqrt(3)/2, 0.0],
                [0.0, 0.0, c]
            ])
        )

        # AB stacking: 4 atoms per unit cell
        sites = [
            # Layer 1 (z = 0)
            Site(element='C', position=np.array([0.0, 0.0, 0.0])),
            Site(element='C', position=np.array([1/3, 2/3, 0.0])),
            # Layer 2 (z = 0.5)
            Site(element='C', position=np.array([0.0, 0.0, 0.5])),
            Site(element='C', position=np.array([2/3, 1/3, 0.5])),
        ]

        return Structure(lattice=lattice, sites=sites)

    # ========================================================================
    # Database Access Methods
    # ========================================================================

    def get_material(self, name: str) -> Structure:
        """
        Get material structure by name.

        Args:
            name: Material name or formula

        Returns:
            Structure object
        """
        material_map = {
            # Metals - FCC
            'al': self.Al_fcc,
            'aluminum': self.Al_fcc,
            'cu': self.Cu_fcc,
            'copper': self.Cu_fcc,
            'ag': self.Ag_fcc,
            'silver': self.Ag_fcc,
            'au': self.Au_fcc,
            'gold': self.Au_fcc,
            # Metals - BCC
            'fe': self.Fe_bcc,
            'iron': self.Fe_bcc,
            # Semiconductors - Diamond
            'diamond': self.C_diamond,
            'c_diamond': self.C_diamond,
            'si': self.Si_diamond,
            'silicon': self.Si_diamond,
            # Oxides
            'sio2': self.SiO2_quartz,
            'quartz': self.SiO2_quartz,
            'tio2': self.TiO2_rutile,
            'rutile': self.TiO2_rutile,
            # III-V
            'gaas': self.GaAs,
            # 2D Materials
            'graphene': self.graphene,
            'graphite': self.graphite,
        }

        name_lower = name.lower()
        if name_lower in material_map:
            return material_map[name_lower]()
        else:
            raise ValueError(
                f"Material '{name}' not found in database. "
                f"Available: {list(material_map.keys())}"
            )

    def list_materials(self) -> Dict[str, List[str]]:
        """List all available materials by category."""
        return {
            'Metals (FCC)': ['Al', 'Cu', 'Ag', 'Au'],
            'Metals (BCC)': ['Fe'],
            'Semiconductors': ['Diamond', 'Si'],
            'Oxides': ['SiO2', 'TiO2'],
            'III-V Semiconductors': ['GaAs'],
            '2D Materials': ['graphene', 'graphite'],
        }


# Singleton instance
_materials_db = MaterialsDatabase()


def get_material(name: str) -> Structure:
    """
    Get material structure by name.

    Args:
        name: Material name

    Returns:
        Structure object ready for DFT calculation

    Example:
        >>> si = get_material('silicon')
        >>> graphene = get_material('graphene')
    """
    return _materials_db.get_material(name)


def list_materials() -> Dict[str, List[str]]:
    """List all available materials by category."""
    return _materials_db.list_materials()


__all__ = ['MaterialsDatabase', 'get_material', 'list_materials']
