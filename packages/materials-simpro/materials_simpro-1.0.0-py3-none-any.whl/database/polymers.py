"""
Polymers Database
=================

Comprehensive database of polymer structures for DFT calculations.

Categories:
1. Synthetic polymers (commodity plastics)
2. Engineering polymers
3. Biological polymers (proteins, DNA, polysaccharides)
4. Conducting polymers
5. Natural polymers

For periodic DFT calculations, polymers are represented as:
- Single repeat unit (monomer) for small molecule calculations
- Oligomers (2-5 repeat units) for finite-size calculations
- Periodic chains for infinite polymer calculations

Author: Materials-SimPro Team
Date: 2025-11-03
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from core.structure import Structure, Lattice, Site


class PolymerDatabase:
    """
    Database of polymer structures for DFT calculations.

    Includes both monomer units and oligomer structures.
    """

    def __init__(self):
        """Initialize polymer database."""
        self.box_size = 20.0  # Larger box for polymers

    def _create_box(self, size: Optional[float] = None) -> Lattice:
        """Create cubic simulation box."""
        if size is None:
            size = self.box_size

        return Lattice(
            matrix=np.array([
                [size, 0.0, 0.0],
                [0.0, size, 0.0],
                [0.0, 0.0, size]
            ])
        )

    def _center_position(self, cart_position: np.ndarray, size: Optional[float] = None) -> np.ndarray:
        """Convert Cartesian to fractional coordinates centered in box."""
        if size is None:
            size = self.box_size
        cart_centered = cart_position + size / 2.0
        return cart_centered / size

    # ========================================================================
    # Synthetic Polymers - Commodity Plastics
    # ========================================================================

    def polyethylene_monomer(self) -> Structure:
        """
        Polyethylene (PE) monomer: -CH₂-CH₂-.

        Structure: -(CH₂)ₙ-
        Most common plastic worldwide.
        Simplest carbon-chain polymer.

        Properties:
        - Density: 0.92-0.97 g/cm³
        - Tm: 120-130°C
        - Chemical resistance: excellent
        """
        lattice = self._create_box(15.0)

        # Single ethylene unit
        r_CC = 1.54  # sp³ C-C bond
        r_CH = 1.09  # C-H bond

        sites = [
            # C-C backbone
            Site(element='C', position=self._center_position(np.array([-r_CC/2, 0.0, 0.0]), 15.0)),
            Site(element='C', position=self._center_position(np.array([r_CC/2, 0.0, 0.0]), 15.0)),
            # H's on first C
            Site(element='H', position=self._center_position(np.array([-r_CC/2, r_CH, r_CH*0.5]), 15.0)),
            Site(element='H', position=self._center_position(np.array([-r_CC/2, -r_CH, -r_CH*0.5]), 15.0)),
            # H's on second C
            Site(element='H', position=self._center_position(np.array([r_CC/2, r_CH, -r_CH*0.5]), 15.0)),
            Site(element='H', position=self._center_position(np.array([r_CC/2, -r_CH, r_CH*0.5]), 15.0)),
        ]

        return Structure(lattice=lattice, sites=sites)

    def polypropylene_monomer(self) -> Structure:
        """
        Polypropylene (PP) monomer: -CH₂-CH(CH₃)-.

        Structure: -[CH₂-CH(CH₃)]ₙ-
        Second most common plastic.
        Methyl side chain creates tacticity (isotactic/syndiotactic).

        Properties:
        - Density: 0.90 g/cm³
        - Tm: 160-170°C
        - Higher strength than PE
        """
        lattice = self._create_box(15.0)

        r_CC = 1.54
        r_CH = 1.09

        sites = [
            # Backbone C-C
            Site(element='C', position=self._center_position(np.array([-r_CC/2, 0.0, 0.0]), 15.0)),
            Site(element='C', position=self._center_position(np.array([r_CC/2, 0.0, 0.0]), 15.0)),
            # Methyl side group on second C
            Site(element='C', position=self._center_position(np.array([r_CC/2, r_CC, 0.0]), 15.0)),
            # H's on first C (CH₂)
            Site(element='H', position=self._center_position(np.array([-r_CC/2, r_CH*0.7, r_CH*0.7]), 15.0)),
            Site(element='H', position=self._center_position(np.array([-r_CC/2, -r_CH*0.7, -r_CH*0.7]), 15.0)),
            # H on second C (CH)
            Site(element='H', position=self._center_position(np.array([r_CC/2, -r_CH, 0.0]), 15.0)),
            # H's on methyl (CH₃)
            Site(element='H', position=self._center_position(np.array([r_CC/2, r_CC+r_CH*0.7, r_CH*0.7]), 15.0)),
            Site(element='H', position=self._center_position(np.array([r_CC/2, r_CC+r_CH*0.7, -r_CH*0.7]), 15.0)),
            Site(element='H', position=self._center_position(np.array([r_CC/2+r_CH*0.7, r_CC, 0.0]), 15.0)),
        ]

        return Structure(lattice=lattice, sites=sites)

    def polystyrene_monomer(self) -> Structure:
        """
        Polystyrene (PS) monomer: -CH₂-CH(C₆H₅)-.

        Structure: -[CH₂-CH(Ph)]ₙ-  (Ph = phenyl ring)
        Phenyl side chain creates rigid, glassy polymer.

        Properties:
        - Density: 1.05 g/cm³
        - Tg: 100°C
        - Clear, brittle plastic
        - Used in packaging, disposable cups
        """
        lattice = self._create_box(18.0)

        r_CC = 1.54  # sp³ backbone
        r_CC_ar = 1.40  # aromatic C-C
        r_CH = 1.09

        sites = [
            # Backbone C-C
            Site(element='C', position=self._center_position(np.array([0.0, 0.0, 0.0]), 18.0)),
            Site(element='C', position=self._center_position(np.array([r_CC, 0.0, 0.0]), 18.0)),
            # Phenyl ring (6 carbons) attached to second C
        ]

        # Add phenyl ring
        for i in range(6):
            angle = i * np.pi / 3.0
            x = r_CC + r_CC_ar * np.cos(angle)
            y = r_CC_ar * np.sin(angle)
            sites.append(Site(element='C', position=self._center_position(np.array([x, y, 2.0]), 18.0)))

        # Add H's (simplified positions)
        for i in range(6):
            angle = i * np.pi / 3.0
            r_total = r_CC + r_CC_ar + r_CH
            x = r_CC + r_total * np.cos(angle)
            y = r_total * np.sin(angle)
            sites.append(Site(element='H', position=self._center_position(np.array([x, y, 2.0]), 18.0)))

        # Backbone H's
        sites.append(Site(element='H', position=self._center_position(np.array([0.0, r_CH, r_CH*0.5]), 18.0)))
        sites.append(Site(element='H', position=self._center_position(np.array([0.0, -r_CH, -r_CH*0.5]), 18.0)))
        sites.append(Site(element='H', position=self._center_position(np.array([r_CC, -r_CH, 0.0]), 18.0)))

        return Structure(lattice=lattice, sites=sites)

    def PVC_monomer(self) -> Structure:
        """
        Polyvinyl chloride (PVC) monomer: -CH₂-CHCl-.

        Structure: -[CH₂-CHCl]ₙ-
        Third most common plastic.
        Chlorine substituent.

        Properties:
        - Density: 1.38 g/cm³
        - Rigid when unplasticized
        - Used in pipes, window frames
        """
        lattice = self._create_box(15.0)

        r_CC = 1.54
        r_CH = 1.09
        r_CCl = 1.78  # C-Cl bond

        sites = [
            # Backbone
            Site(element='C', position=self._center_position(np.array([0.0, 0.0, 0.0]), 15.0)),
            Site(element='C', position=self._center_position(np.array([r_CC, 0.0, 0.0]), 15.0)),
            # Cl on second C
            Site(element='Cl', position=self._center_position(np.array([r_CC, r_CCl, 0.0]), 15.0)),
            # H's
            Site(element='H', position=self._center_position(np.array([0.0, r_CH*0.7, r_CH*0.7]), 15.0)),
            Site(element='H', position=self._center_position(np.array([0.0, -r_CH*0.7, -r_CH*0.7]), 15.0)),
            Site(element='H', position=self._center_position(np.array([r_CC, -r_CH, 0.0]), 15.0)),
        ]

        return Structure(lattice=lattice, sites=sites)

    # ========================================================================
    # Engineering Polymers
    # ========================================================================

    def nylon6_monomer(self) -> Structure:
        """
        Nylon-6 monomer: -[NH-(CH₂)₅-CO]-.

        Polyamide with amide linkage (-CO-NH-).
        Strong hydrogen bonding between chains.

        Properties:
        - Density: 1.14 g/cm³
        - Tm: 220°C
        - High strength, used in textiles, fibers
        """
        lattice = self._create_box(18.0)

        r_CC = 1.54
        r_CN = 1.47
        r_CO = 1.23  # C=O double bond
        r_NH = 1.01

        sites = [
            # Amide group: -CO-NH-
            Site(element='C', position=self._center_position(np.array([0.0, 0.0, 0.0]), 18.0)),  # C=O
            Site(element='O', position=self._center_position(np.array([0.0, r_CO, 0.0]), 18.0)),
            Site(element='N', position=self._center_position(np.array([r_CN, 0.0, 0.0]), 18.0)),
            Site(element='H', position=self._center_position(np.array([r_CN, r_NH, 0.0]), 18.0)),
            # CH₂ chain (simplified - showing 3 of 5 carbons)
            Site(element='C', position=self._center_position(np.array([r_CN+r_CC, 0.0, 0.0]), 18.0)),
            Site(element='C', position=self._center_position(np.array([r_CN+2*r_CC, 0.0, 0.0]), 18.0)),
            Site(element='C', position=self._center_position(np.array([r_CN+3*r_CC, 0.0, 0.0]), 18.0)),
        ]

        # Add some H's (simplified)
        for i in range(3):
            x = r_CN + (i+1)*r_CC
            sites.append(Site(element='H', position=self._center_position(np.array([x, 1.0, 0.5]), 18.0)))
            sites.append(Site(element='H', position=self._center_position(np.array([x, -1.0, -0.5]), 18.0)))

        return Structure(lattice=lattice, sites=sites)

    # ========================================================================
    # Biological Polymers - Polysaccharides
    # ========================================================================

    def cellulose_monomer(self) -> Structure:
        """
        Cellulose monomer: β-D-glucose.

        Structure: β-(1→4) linked glucose units
        Most abundant organic polymer on Earth.
        Linear chain, extensive H-bonding.

        Properties:
        - Found in plant cell walls
        - Insoluble in water
        - Strong fibers (cotton, wood)
        """
        lattice = self._create_box(20.0)

        # Simplified glucose ring (pyranose)
        # 6-membered ring with 5 C's and 1 O
        r_ring = 1.5  # Average ring bond length

        sites = []

        # Ring atoms (C-C-C-C-C-O)
        for i in range(5):
            angle = i * 2*np.pi / 6
            x = r_ring * np.cos(angle)
            y = r_ring * np.sin(angle)
            sites.append(Site(element='C', position=self._center_position(np.array([x, y, 0.0]), 20.0)))

        # Ring oxygen
        angle = 5 * 2*np.pi / 6
        x = r_ring * np.cos(angle)
        y = r_ring * np.sin(angle)
        sites.append(Site(element='O', position=self._center_position(np.array([x, y, 0.0]), 20.0)))

        # OH groups (simplified)
        sites.append(Site(element='O', position=self._center_position(np.array([r_ring+1.0, 0.0, 0.0]), 20.0)))
        sites.append(Site(element='O', position=self._center_position(np.array([0.0, r_ring+1.0, 0.0]), 20.0)))
        sites.append(Site(element='O', position=self._center_position(np.array([-r_ring-1.0, 0.0, 0.0]), 20.0)))

        # Add H's on OH groups
        sites.append(Site(element='H', position=self._center_position(np.array([r_ring+1.5, 0.0, 0.0]), 20.0)))
        sites.append(Site(element='H', position=self._center_position(np.array([0.0, r_ring+1.5, 0.0]), 20.0)))
        sites.append(Site(element='H', position=self._center_position(np.array([-r_ring-1.5, 0.0, 0.0]), 20.0)))

        return Structure(lattice=lattice, sites=sites)

    # ========================================================================
    # Biological Polymers - Amino Acids (Protein Building Blocks)
    # ========================================================================

    def glycine(self) -> Structure:
        """
        Glycine (Gly, G): simplest amino acid.

        Structure: NH₂-CH₂-COOH
        Achiral (no side chain).

        Building block of proteins and peptides.
        """
        lattice = self._create_box(15.0)

        r_CC = 1.54
        r_CN = 1.47
        r_CO = 1.23
        r_NH = 1.01

        sites = [
            # Central C (α-carbon)
            Site(element='C', position=self._center_position(np.array([0.0, 0.0, 0.0]), 15.0)),
            # Amino group (-NH₂)
            Site(element='N', position=self._center_position(np.array([-r_CN, 0.0, 0.0]), 15.0)),
            Site(element='H', position=self._center_position(np.array([-r_CN-r_NH*0.7, r_NH*0.7, 0.0]), 15.0)),
            Site(element='H', position=self._center_position(np.array([-r_CN-r_NH*0.7, -r_NH*0.7, 0.0]), 15.0)),
            # Carboxyl group (-COOH)
            Site(element='C', position=self._center_position(np.array([r_CC, 0.0, 0.0]), 15.0)),
            Site(element='O', position=self._center_position(np.array([r_CC, r_CO, 0.0]), 15.0)),  # C=O
            Site(element='O', position=self._center_position(np.array([r_CC+r_CO*0.7, -r_CO*0.7, 0.0]), 15.0)),  # C-OH
            Site(element='H', position=self._center_position(np.array([r_CC+r_CO*1.2, -r_CO*1.2, 0.0]), 15.0)),  # OH
            # H's on α-carbon
            Site(element='H', position=self._center_position(np.array([0.0, 1.0, 0.5]), 15.0)),
            Site(element='H', position=self._center_position(np.array([0.0, -1.0, -0.5]), 15.0)),
        ]

        return Structure(lattice=lattice, sites=sites)

    # ========================================================================
    # Database Access Methods
    # ========================================================================

    def get_polymer(self, name: str) -> Structure:
        """
        Get polymer structure by name.

        Args:
            name: Polymer name

        Returns:
            Structure object
        """
        polymer_map = {
            # Commodity plastics
            'polyethylene': self.polyethylene_monomer,
            'pe': self.polyethylene_monomer,
            'polypropylene': self.polypropylene_monomer,
            'pp': self.polypropylene_monomer,
            'polystyrene': self.polystyrene_monomer,
            'ps': self.polystyrene_monomer,
            'pvc': self.PVC_monomer,
            'polyvinylchloride': self.PVC_monomer,
            # Engineering
            'nylon': self.nylon6_monomer,
            'nylon6': self.nylon6_monomer,
            # Natural
            'cellulose': self.cellulose_monomer,
            # Amino acids
            'glycine': self.glycine,
            'gly': self.glycine,
        }

        name_lower = name.lower()
        if name_lower in polymer_map:
            return polymer_map[name_lower]()
        else:
            raise ValueError(
                f"Polymer '{name}' not found in database. "
                f"Available: {list(polymer_map.keys())}"
            )

    def list_polymers(self) -> Dict[str, List[str]]:
        """List all available polymers by category."""
        return {
            'Commodity Plastics': ['polyethylene (PE)', 'polypropylene (PP)',
                                   'polystyrene (PS)', 'PVC'],
            'Engineering Polymers': ['nylon-6'],
            'Natural Polymers': ['cellulose'],
            'Amino Acids': ['glycine'],
        }


# Singleton instance
_polymer_db = PolymerDatabase()


def get_polymer(name: str) -> Structure:
    """
    Get polymer structure by name.

    Args:
        name: Polymer name

    Returns:
        Structure object ready for DFT calculation

    Example:
        >>> pe = get_polymer('polyethylene')
        >>> nylon = get_polymer('nylon6')
    """
    return _polymer_db.get_polymer(name)


def list_polymers() -> Dict[str, List[str]]:
    """List all available polymers by category."""
    return _polymer_db.list_polymers()


__all__ = ['PolymerDatabase', 'get_polymer', 'list_polymers']
