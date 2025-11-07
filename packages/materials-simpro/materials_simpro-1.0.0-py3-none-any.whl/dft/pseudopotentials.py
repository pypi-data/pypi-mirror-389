"""
Pseudopotentials for DFT
=========================

Pseudopotentials replace the full electron-nuclear interaction with an
effective potential that:
1. Reproduces valence electron behavior exactly
2. Eliminates core electrons (frozen-core approximation)
3. Smooths the potential near nuclei → fewer plane waves needed

Types of Pseudopotentials:
---------------------------
1. Norm-conserving (NC): ∫|ψ_pseudo|²dr = ∫|ψ_all-electron|²dr
2. Ultrasoft (US): Relaxed norm-conservation → softer potentials
3. Projector Augmented Wave (PAW): Most accurate, all-electron reconstruction

Scientific References:
----------------------
[1] Hamann, D. R., Schlüter, M., & Chiang, C. (1979). Norm-conserving
    pseudopotentials. Physical Review Letters, 43(20), 1494.
    DOI: 10.1103/PhysRevLett.43.1494

[2] Vanderbilt, D. (1990). Soft self-consistent pseudopotentials in a
    generalized eigenvalue formalism. Physical Review B, 41(11), 7892.
    DOI: 10.1103/PhysRevB.41.7892

[3] Blöchl, P. E. (1994). Projector augmented-wave method.
    Physical Review B, 50(24), 17953.
    DOI: 10.1103/PhysRevB.50.17953

[4] Kresse, G., & Joubert, D. (1999). From ultrasoft pseudopotentials
    to the projector augmented-wave method.
    Physical Review B, 59(3), 1758.
    DOI: 10.1103/PhysRevB.59.1758
"""

import numpy as np
from typing import Optional, Dict, List
from dataclasses import dataclass
from enum import Enum


class PseudopotentialType(Enum):
    """Types of pseudopotentials."""
    NORM_CONSERVING = "norm-conserving"
    ULTRASOFT = "ultrasoft"
    PAW = "projector-augmented-wave"


@dataclass
class Pseudopotential:
    """
    Pseudopotential data structure.

    Attributes:
        element: Chemical symbol
        pp_type: Pseudopotential type
        z_val: Number of valence electrons
        r_cut: Cutoff radius (Bohr)
        v_local: Local potential V_loc(r)
        v_nonlocal: Nonlocal potential projectors
        energy_cutoff_recommended: Recommended plane-wave cutoff (eV)
    """
    element: str
    pp_type: PseudopotentialType
    z_val: int
    r_cut: float  # Bohr
    v_local: Optional[np.ndarray] = None
    v_nonlocal: Optional[Dict] = None
    energy_cutoff_recommended: float = 500.0  # eV

    def __repr__(self) -> str:
        return (f"Pseudopotential({self.element}, {self.pp_type.value}, "
                f"Z_val={self.z_val}, r_cut={self.r_cut:.2f} Bohr)")


def load_pseudopotential(
    element: str,
    pp_type: PseudopotentialType = PseudopotentialType.PAW,
    xc_functional: str = "PBE"
) -> Pseudopotential:
    """
    Load pseudopotential for given element.

    In production, this would load from pseudopotential libraries:
    - GBRV (http://www.physics.rutgers.edu/gbrv/)
    - SG15 (http://www.quantum-simulation.org/potentials/sg15_oncv/)
    - PSlibrary (http://pseudopotentials.quantum-espresso.org/)
    - VASP PAW potentials

    Args:
        element: Chemical symbol
        pp_type: Type of pseudopotential
        xc_functional: XC functional (LDA, PBE, etc.)

    Returns:
        Pseudopotential object

    Reference: Pseudopotential libraries are standardized formats
    (UPF, PSP8, etc.). See Quantum ESPRESSO documentation.
    """
    # Valence electron count (simplified)
    valence_electrons = {
        'H': 1, 'He': 2,
        'Li': 1, 'Be': 2, 'B': 3, 'C': 4, 'N': 5, 'O': 6, 'F': 7, 'Ne': 8,
        'Na': 1, 'Mg': 2, 'Al': 3, 'Si': 4, 'P': 5, 'S': 6, 'Cl': 7, 'Ar': 8,
        'K': 9, 'Ca': 10, 'Sc': 11, 'Ti': 12, 'V': 13, 'Cr': 14, 'Mn': 15, 'Fe': 16,
        'Co': 9, 'Ni': 10, 'Cu': 11, 'Zn': 12,
    }

    z_val = valence_electrons.get(element, 4)

    # Cutoff radii (Bohr) - typical values
    cutoff_radii = {
        'H': 1.2, 'He': 0.8,
        'C': 1.5, 'N': 1.5, 'O': 1.4, 'F': 1.3,
        'Si': 1.9, 'P': 1.9, 'S': 1.8, 'Cl': 1.7,
        'Fe': 2.2, 'Ni': 2.1, 'Cu': 2.0,
    }

    r_cut = cutoff_radii.get(element, 2.0)

    # Recommended cutoffs (eV)
    cutoff_energies = {
        'H': 400.0, 'C': 500.0, 'N': 500.0, 'O': 500.0,
        'Si': 450.0, 'Fe': 600.0,
    }

    ecut_rec = cutoff_energies.get(element, 500.0)

    # Create pseudopotential object (without actual potential data)
    pp = Pseudopotential(
        element=element,
        pp_type=pp_type,
        z_val=z_val,
        r_cut=r_cut,
        energy_cutoff_recommended=ecut_rec
    )

    return pp


def generate_local_potential(
    r: np.ndarray,
    element: str,
    z_val: int,
    r_cut: float
) -> np.ndarray:
    """
    Generate local pseudopotential (simplified analytical form).

    V_loc(r) = -Z_val/r * erf(r/r_cut)

    This is a smoothed Coulomb potential.

    Args:
        r: Radial grid (Bohr)
        element: Chemical symbol
        z_val: Valence charge
        r_cut: Cutoff radius

    Returns:
        Local potential V_loc(r) in Hartree

    Reference: This is a simple model. Production pseudopotentials
    are generated from all-electron calculations.
    """
    from scipy.special import erf

    # Smoothed Coulomb potential
    V_loc = -z_val / (r + 1e-10) * erf(r / r_cut)

    return V_loc


__all__ = [
    'PseudopotentialType',
    'Pseudopotential',
    'load_pseudopotential',
    'generate_local_potential',
]
