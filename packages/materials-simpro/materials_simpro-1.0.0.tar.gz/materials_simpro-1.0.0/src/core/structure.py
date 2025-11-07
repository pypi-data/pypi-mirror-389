"""
Crystal Structure Representation
=================================

This module provides classes for representing crystal structures, lattices,
and atomic sites with full crystallographic information.

Scientific References:
----------------------
[1] Ashcroft, N. W., & Mermin, N. D. (1976). Solid State Physics.
    Holt, Rinehart and Winston. (Chapter 4: Crystal Lattices)

[2] International Tables for Crystallography, Volume A: Space-group symmetry.
    DOI: 10.1107/97809553602060000114

[3] Setyawan, W., & Curtarolo, S. (2010). High-throughput electronic band
    structure calculations: Challenges and tools. Computational Materials
    Science, 49(2), 299-312.
    DOI: 10.1016/j.commatsci.2010.05.010

[4] Aroyo, M. I., et al. (2006). Bilbao Crystallographic Server: I. Databases
    and crystallographic computing programs. Zeitschrift für Kristallographie,
    221(1), 15-27.
    DOI: 10.1524/zkri.2006.221.1.15
"""

import numpy as np
from typing import List, Tuple, Optional, Union, Dict
from dataclasses import dataclass
from enum import Enum
import copy

from .constants import BOHR_TO_ANGSTROM, ANGSTROM_TO_BOHR, ATOMIC_MASSES, COVALENT_RADII


class LatticeSystem(Enum):
    """
    Seven crystal lattice systems (Bravais lattices).

    Reference: International Tables for Crystallography, Volume A
    DOI: 10.1107/97809553602060000114
    """
    TRICLINIC = "triclinic"      # a≠b≠c, α≠β≠γ
    MONOCLINIC = "monoclinic"    # a≠b≠c, α=γ=90°≠β
    ORTHORHOMBIC = "orthorhombic"  # a≠b≠c, α=β=γ=90°
    TETRAGONAL = "tetragonal"    # a=b≠c, α=β=γ=90°
    TRIGONAL = "trigonal"        # a=b=c, α=β=γ<120°,≠90°
    HEXAGONAL = "hexagonal"      # a=b≠c, α=β=90°, γ=120°
    CUBIC = "cubic"              # a=b=c, α=β=γ=90°


@dataclass
class Site:
    """
    Represents an atomic site in a crystal structure.

    Attributes:
        element: Chemical symbol (e.g., 'Fe', 'O')
        position: Fractional coordinates [x, y, z] in the lattice basis
        cartesian: Cartesian coordinates (Å) - computed from fractional
        magnetic_moment: Magnetic moment (μB) - optional
        oxidation_state: Oxidation state - optional
        wyckoff: Wyckoff position label - optional
    """
    element: str
    position: np.ndarray  # fractional coordinates
    cartesian: Optional[np.ndarray] = None  # Cartesian coordinates (Å)
    magnetic_moment: Optional[float] = None
    oxidation_state: Optional[int] = None
    wyckoff: Optional[str] = None

    def __post_init__(self):
        self.position = np.array(self.position, dtype=np.float64)
        if self.cartesian is not None:
            self.cartesian = np.array(self.cartesian, dtype=np.float64)

    @property
    def mass(self) -> float:
        """Atomic mass in amu."""
        return ATOMIC_MASSES.get(self.element, 0.0)

    @property
    def covalent_radius(self) -> float:
        """Covalent radius in Angstrom."""
        return COVALENT_RADII.get(self.element, 1.0)


class Lattice:
    """
    Represents a crystal lattice with full crystallographic information.

    The lattice is defined by three lattice vectors a, b, c or equivalently
    by lattice parameters (a, b, c, α, β, γ).

    Mathematical Framework:
    -----------------------
    Lattice vectors form the basis for the real-space crystal:
        r = n₁a + n₂b + n₃c  where n₁, n₂, n₃ ∈ ℤ

    Reciprocal lattice vectors (k-space basis):
        b₁ = 2π(a₂ × a₃)/(a₁·(a₂ × a₃))
        b₂ = 2π(a₃ × a₁)/(a₁·(a₂ × a₃))
        b₃ = 2π(a₁ × a₂)/(a₁·(a₂ × a₃))

    Reference: Ashcroft & Mermin (1976), Chapter 5
    """

    def __init__(
        self,
        matrix: Optional[np.ndarray] = None,
        a: Optional[float] = None,
        b: Optional[float] = None,
        c: Optional[float] = None,
        alpha: Optional[float] = None,
        beta: Optional[float] = None,
        gamma: Optional[float] = None,
    ):
        """
        Initialize lattice either from matrix or lattice parameters.

        Args:
            matrix: 3x3 matrix where rows are lattice vectors a, b, c (Å)
            a, b, c: Lattice parameters (Å)
            alpha, beta, gamma: Lattice angles (degrees)
        """
        if matrix is not None:
            self.matrix = np.array(matrix, dtype=np.float64)
            if self.matrix.shape != (3, 3):
                raise ValueError("Lattice matrix must be 3x3")
        elif all(x is not None for x in [a, b, c, alpha, beta, gamma]):
            self.matrix = self._parameters_to_matrix(a, b, c, alpha, beta, gamma)
        else:
            raise ValueError("Must provide either matrix or lattice parameters")

        self._reciprocal_matrix = None
        self._volume = None

    @staticmethod
    def _parameters_to_matrix(
        a: float, b: float, c: float,
        alpha: float, beta: float, gamma: float
    ) -> np.ndarray:
        """
        Convert lattice parameters to matrix form.

        Convention: a along x-axis, b in xy-plane

        Reference: International Tables for Crystallography, Volume B
        DOI: 10.1107/97809553602060000114
        """
        alpha_rad = np.radians(alpha)
        beta_rad = np.radians(beta)
        gamma_rad = np.radians(gamma)

        # Volume from lattice parameters
        cos_alpha = np.cos(alpha_rad)
        cos_beta = np.cos(beta_rad)
        cos_gamma = np.cos(gamma_rad)
        sin_gamma = np.sin(gamma_rad)

        # c vector z-component
        val = (cos_alpha - cos_beta * cos_gamma) / sin_gamma
        c_z = c * np.sqrt(1 - cos_beta**2 - val**2)

        matrix = np.array([
            [a, 0, 0],
            [b * cos_gamma, b * sin_gamma, 0],
            [c * cos_beta, c * val, c_z]
        ])

        return matrix

    @property
    def a(self) -> float:
        """Lattice parameter a (Å)."""
        return np.linalg.norm(self.matrix[0])

    @property
    def b(self) -> float:
        """Lattice parameter b (Å)."""
        return np.linalg.norm(self.matrix[1])

    @property
    def c(self) -> float:
        """Lattice parameter c (Å)."""
        return np.linalg.norm(self.matrix[2])

    @property
    def alpha(self) -> float:
        """Angle between b and c (degrees)."""
        return np.degrees(np.arccos(
            np.dot(self.matrix[1], self.matrix[2]) / (self.b * self.c)
        ))

    @property
    def beta(self) -> float:
        """Angle between a and c (degrees)."""
        return np.degrees(np.arccos(
            np.dot(self.matrix[0], self.matrix[2]) / (self.a * self.c)
        ))

    @property
    def gamma(self) -> float:
        """Angle between a and b (degrees)."""
        return np.degrees(np.arccos(
            np.dot(self.matrix[0], self.matrix[1]) / (self.a * self.b)
        ))

    @property
    def volume(self) -> float:
        """
        Unit cell volume (Å³).

        V = |a · (b × c)| = |det(lattice_matrix)|
        """
        if self._volume is None:
            self._volume = abs(np.linalg.det(self.matrix))
        return self._volume

    @property
    def reciprocal_lattice(self) -> np.ndarray:
        """
        Reciprocal lattice matrix (2π/Å).

        Used for k-space calculations in DFT.

        Mathematical definition:
            b_i · a_j = 2π δ_ij

        Reference: Ashcroft & Mermin (1976), Chapter 5
        DOI: (Solid State Physics textbook)
        """
        if self._reciprocal_matrix is None:
            # b₁ = 2π(a₂ × a₃)/V
            # b₂ = 2π(a₃ × a₁)/V
            # b₃ = 2π(a₁ × a₂)/V
            a1, a2, a3 = self.matrix
            volume = self.volume

            b1 = 2 * np.pi * np.cross(a2, a3) / volume
            b2 = 2 * np.pi * np.cross(a3, a1) / volume
            b3 = 2 * np.pi * np.cross(a1, a2) / volume

            self._reciprocal_matrix = np.array([b1, b2, b3])

        return self._reciprocal_matrix

    def get_cartesian_coords(self, fractional: np.ndarray) -> np.ndarray:
        """
        Convert fractional coordinates to Cartesian (Å).

        r_cart = M · r_frac
        where M is the lattice matrix.
        """
        return np.dot(fractional, self.matrix)

    def get_fractional_coords(self, cartesian: np.ndarray) -> np.ndarray:
        """
        Convert Cartesian coordinates (Å) to fractional.

        r_frac = M⁻¹ · r_cart
        """
        return np.dot(cartesian, np.linalg.inv(self.matrix))

    def get_lattice_system(self) -> LatticeSystem:
        """
        Determine the lattice system based on lattice parameters.

        Reference: International Tables for Crystallography
        DOI: 10.1107/97809553602060000114
        """
        a, b, c = self.a, self.b, self.c
        alpha, beta, gamma = self.alpha, self.beta, self.gamma

        tol = 1e-5

        # Check cubic: a=b=c, α=β=γ=90°
        if (abs(a - b) < tol and abs(b - c) < tol and
            abs(alpha - 90) < tol and abs(beta - 90) < tol and abs(gamma - 90) < tol):
            return LatticeSystem.CUBIC

        # Check hexagonal: a=b≠c, α=β=90°, γ=120°
        if (abs(a - b) < tol and abs(c - a) > tol and
            abs(alpha - 90) < tol and abs(beta - 90) < tol and abs(gamma - 120) < tol):
            return LatticeSystem.HEXAGONAL

        # Check tetragonal: a=b≠c, α=β=γ=90°
        if (abs(a - b) < tol and abs(c - a) > tol and
            abs(alpha - 90) < tol and abs(beta - 90) < tol and abs(gamma - 90) < tol):
            return LatticeSystem.TETRAGONAL

        # Check orthorhombic: a≠b≠c, α=β=γ=90°
        if (abs(alpha - 90) < tol and abs(beta - 90) < tol and abs(gamma - 90) < tol):
            return LatticeSystem.ORTHORHOMBIC

        # Check monoclinic: α=γ=90°≠β
        if (abs(alpha - 90) < tol and abs(gamma - 90) < tol and abs(beta - 90) > tol):
            return LatticeSystem.MONOCLINIC

        # Check trigonal: a=b=c, α=β=γ≠90°
        if (abs(a - b) < tol and abs(b - c) < tol and
            abs(alpha - beta) < tol and abs(beta - gamma) < tol and abs(alpha - 90) > tol):
            return LatticeSystem.TRIGONAL

        # Otherwise triclinic
        return LatticeSystem.TRICLINIC

    def __repr__(self) -> str:
        return (f"Lattice(a={self.a:.4f}, b={self.b:.4f}, c={self.c:.4f}, "
                f"α={self.alpha:.2f}°, β={self.beta:.2f}°, γ={self.gamma:.2f}°, "
                f"V={self.volume:.4f} Å³)")


class Structure:
    """
    Complete crystal structure with lattice and atomic sites.

    This class represents a periodic crystal structure with full
    crystallographic information including lattice, atomic positions,
    and symmetry.

    Scientific Context:
    -------------------
    A crystal structure is uniquely defined by:
    1. Lattice (Bravais lattice type + parameters)
    2. Basis (atomic positions in fractional coordinates)
    3. Space group symmetry

    Reference: International Tables for Crystallography, Volume A
    DOI: 10.1107/97809553602060000114
    """

    def __init__(
        self,
        lattice: Lattice,
        sites: List[Site],
        space_group: Optional[int] = None,
        formula: Optional[str] = None,
        properties: Optional[Dict] = None
    ):
        """
        Initialize crystal structure.

        Args:
            lattice: Crystal lattice
            sites: List of atomic sites
            space_group: International space group number (1-230)
            formula: Chemical formula (e.g., 'Fe2O3')
            properties: Dictionary of computed/experimental properties
        """
        self.lattice = lattice
        self.sites = sites
        self.space_group = space_group
        self.formula = formula
        self.properties = properties or {}

        # Compute Cartesian coordinates for all sites
        for site in self.sites:
            if site.cartesian is None:
                site.cartesian = self.lattice.get_cartesian_coords(site.position)

    @property
    def num_sites(self) -> int:
        """Number of atomic sites in the unit cell."""
        return len(self.sites)

    @property
    def composition(self) -> Dict[str, int]:
        """
        Chemical composition as element: count dictionary.

        Example: {'Fe': 2, 'O': 3} for Fe₂O₃
        """
        comp = {}
        for site in self.sites:
            comp[site.element] = comp.get(site.element, 0) + 1
        return comp

    @property
    def density(self) -> float:
        """
        Mass density in g/cm³.

        ρ = (Σ m_i) / (V · N_A) · 10²⁴
        where m_i are atomic masses, V is volume in Å³
        """
        total_mass = sum(site.mass for site in self.sites)  # amu
        volume_cm3 = self.lattice.volume * 1e-24  # Å³ to cm³
        from .constants import AVOGADRO
        return total_mass / (volume_cm3 * AVOGADRO)

    def get_distance(self, site1_idx: int, site2_idx: int, pbc: bool = True) -> float:
        """
        Calculate distance between two sites (Å).

        Args:
            site1_idx: Index of first site
            site2_idx: Index of second site
            pbc: Apply periodic boundary conditions

        Returns:
            Distance in Angstroms
        """
        pos1 = self.sites[site1_idx].cartesian
        pos2 = self.sites[site2_idx].cartesian

        if not pbc:
            return np.linalg.norm(pos2 - pos1)

        # Minimum image convention for PBC
        frac1 = self.lattice.get_fractional_coords(pos1)
        frac2 = self.lattice.get_fractional_coords(pos2)

        # Find minimum image
        min_dist = np.inf
        for i in [-1, 0, 1]:
            for j in [-1, 0, 1]:
                for k in [-1, 0, 1]:
                    image = frac2 + np.array([i, j, k])
                    cart_image = self.lattice.get_cartesian_coords(image)
                    dist = np.linalg.norm(cart_image - pos1)
                    if dist < min_dist:
                        min_dist = dist

        return min_dist

    def get_all_distances(self, cutoff: float = 5.0) -> List[Tuple[int, int, float]]:
        """
        Get all interatomic distances within cutoff radius.

        Args:
            cutoff: Maximum distance to consider (Å)

        Returns:
            List of (site1_idx, site2_idx, distance) tuples
        """
        distances = []
        for i in range(self.num_sites):
            for j in range(i + 1, self.num_sites):
                dist = self.get_distance(i, j, pbc=True)
                if dist <= cutoff:
                    distances.append((i, j, dist))
        return distances

    def copy(self) -> 'Structure':
        """Return a deep copy of the structure."""
        return copy.deepcopy(self)

    def to_dict(self) -> Dict:
        """
        Serialize structure to dictionary.

        Compatible with Materials Project API format.
        """
        return {
            'lattice': {
                'matrix': self.lattice.matrix.tolist(),
                'a': self.lattice.a,
                'b': self.lattice.b,
                'c': self.lattice.c,
                'alpha': self.lattice.alpha,
                'beta': self.lattice.beta,
                'gamma': self.lattice.gamma,
                'volume': self.lattice.volume,
            },
            'sites': [
                {
                    'element': site.element,
                    'position': site.position.tolist(),
                    'cartesian': site.cartesian.tolist() if site.cartesian is not None else None,
                    'magnetic_moment': site.magnetic_moment,
                    'oxidation_state': site.oxidation_state,
                }
                for site in self.sites
            ],
            'space_group': self.space_group,
            'formula': self.formula,
            'composition': self.composition,
            'density': self.density,
            'properties': self.properties,
        }

    @classmethod
    def from_dict(cls, d: Dict) -> 'Structure':
        """Deserialize structure from dictionary."""
        lattice = Lattice(matrix=np.array(d['lattice']['matrix']))
        sites = [
            Site(
                element=s['element'],
                position=np.array(s['position']),
                cartesian=np.array(s['cartesian']) if s['cartesian'] else None,
                magnetic_moment=s.get('magnetic_moment'),
                oxidation_state=s.get('oxidation_state'),
            )
            for s in d['sites']
        ]
        return cls(
            lattice=lattice,
            sites=sites,
            space_group=d.get('space_group'),
            formula=d.get('formula'),
            properties=d.get('properties', {}),
        )

    def __repr__(self) -> str:
        formula_str = self.formula or "Unknown"
        sg_str = f"SG {self.space_group}" if self.space_group else "Unknown SG"
        return (f"Structure({formula_str}, {sg_str}, "
                f"{self.num_sites} sites, "
                f"{self.lattice.get_lattice_system().value})")

    def __len__(self) -> int:
        return self.num_sites


# ============================================================================
# Common Structure Generators
# ============================================================================

def make_fcc(element: str, a: float) -> Structure:
    """
    Create FCC (face-centered cubic) structure.

    Space group: Fm-3m (225)
    Pearson symbol: cF4

    Args:
        element: Chemical symbol
        a: Lattice constant (Å)

    Reference: Kittel, C. (2005). Introduction to Solid State Physics, 8th ed.
    """
    lattice = Lattice(a=a, b=a, c=a, alpha=90, beta=90, gamma=90)
    sites = [
        Site(element, [0.0, 0.0, 0.0]),
        Site(element, [0.5, 0.5, 0.0]),
        Site(element, [0.5, 0.0, 0.5]),
        Site(element, [0.0, 0.5, 0.5]),
    ]
    return Structure(lattice, sites, space_group=225, formula=element)


def make_bcc(element: str, a: float) -> Structure:
    """
    Create BCC (body-centered cubic) structure.

    Space group: Im-3m (229)
    Pearson symbol: cI2
    """
    lattice = Lattice(a=a, b=a, c=a, alpha=90, beta=90, gamma=90)
    sites = [
        Site(element, [0.0, 0.0, 0.0]),
        Site(element, [0.5, 0.5, 0.5]),
    ]
    return Structure(lattice, sites, space_group=229, formula=element)


def make_diamond(element: str, a: float) -> Structure:
    """
    Create diamond structure (e.g., Si, Ge, C).

    Space group: Fd-3m (227)
    Pearson symbol: cF8
    """
    lattice = Lattice(a=a, b=a, c=a, alpha=90, beta=90, gamma=90)
    sites = [
        Site(element, [0.00, 0.00, 0.00]),
        Site(element, [0.25, 0.25, 0.25]),
        Site(element, [0.50, 0.50, 0.00]),
        Site(element, [0.75, 0.75, 0.25]),
        Site(element, [0.50, 0.00, 0.50]),
        Site(element, [0.75, 0.25, 0.75]),
        Site(element, [0.00, 0.50, 0.50]),
        Site(element, [0.25, 0.75, 0.75]),
    ]
    return Structure(lattice, sites, space_group=227, formula=element)


def make_rocksalt(cation: str, anion: str, a: float) -> Structure:
    """
    Create rocksalt (NaCl) structure.

    Space group: Fm-3m (225)
    Example: NaCl, MgO, LiF
    """
    lattice = Lattice(a=a, b=a, c=a, alpha=90, beta=90, gamma=90)
    sites = [
        Site(cation, [0.0, 0.0, 0.0]),
        Site(cation, [0.5, 0.5, 0.0]),
        Site(cation, [0.5, 0.0, 0.5]),
        Site(cation, [0.0, 0.5, 0.5]),
        Site(anion, [0.5, 0.0, 0.0]),
        Site(anion, [0.0, 0.5, 0.0]),
        Site(anion, [0.0, 0.0, 0.5]),
        Site(anion, [0.5, 0.5, 0.5]),
    ]
    return Structure(lattice, sites, space_group=225, formula=f"{cation}{anion}")


__all__ = [
    'LatticeSystem',
    'Site',
    'Lattice',
    'Structure',
    'make_fcc',
    'make_bcc',
    'make_diamond',
    'make_rocksalt',
]
