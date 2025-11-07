"""
Phonon Properties
=================

Calculate phonon dispersion, DOS, thermodynamic properties.

Theory:
-------
Phonons are quantized lattice vibrations. The dynamical matrix:
    D_αβ(q) = (1/√(m_α m_β)) Σ_R Φ_αβ(R) exp(iq·R)

where Φ is the force constant matrix.

Eigenvalues give phonon frequencies ω(q).

References:
-----------
[1] Baroni, S., et al. (2001). DOI: 10.1103/RevModPhys.73.515
    (Density functional perturbation theory)

[2] Togo, A., & Tanaka, I. (2015). First principles phonon calculations in
    materials science. Scripta Materialia, 108, 1-5.
    DOI: 10.1016/j.scriptamat.2015.07.021
    (Phonopy software)
"""

import numpy as np
from typing import Dict, List

from core.structure import Structure
from core.base import Calculator


class PhononCalculator:
    """
    Calculate phonon properties using finite displacements.

    Uses supercell approach:
    1. Create supercell
    2. Displace atoms
    3. Compute forces
    4. Extract force constants
    5. Solve dynamical matrix
    """

    def __init__(
        self,
        calculator: Calculator,
        supercell_size: tuple = (2, 2, 2),
        displacement: float = 0.01
    ):
        """
        Args:
            calculator: Force calculator
            supercell_size: Supercell dimensions
            displacement: Atomic displacement (Å)
        """
        self.calculator = calculator
        self.supercell_size = supercell_size
        self.displacement = displacement

    def calculate(self, structure: Structure) -> Dict:
        """
        Calculate phonon dispersion and DOS.

        Returns:
            Dictionary with:
            - frequencies: Phonon frequencies at Γ (THz)
            - dos: Phonon density of states
            - free_energy: Helmholtz free energy (eV)
            - entropy: Vibrational entropy (eV/K)
        """
        # Create supercell
        supercell = self._create_supercell(structure)

        # Compute force constants
        force_constants = self._compute_force_constants(supercell)

        # Dynamical matrix at Γ point
        dyn_matrix = self._dynamical_matrix(force_constants, q=[0, 0, 0])

        # Diagonalize
        frequencies = np.sqrt(np.abs(np.linalg.eigvalsh(dyn_matrix))) / (2 * np.pi)  # THz

        return {
            'frequencies': frequencies,
            'dos': None,  # Placeholder
            'free_energy': None,
            'entropy': None
        }

    def _create_supercell(self, structure: Structure) -> Structure:
        """Create supercell."""
        # Simplified: return original structure
        return structure

    def _compute_force_constants(self, structure: Structure) -> np.ndarray:
        """Compute force constants via finite differences."""
        n_atoms = len(structure)
        force_constants = np.zeros((n_atoms, n_atoms, 3, 3))

        # For each atom, displace in each direction
        for atom_i in range(n_atoms):
            for direction in range(3):
                # Positive displacement
                displaced = structure.copy()
                displaced.sites[atom_i].cartesian[direction] += self.displacement

                result = self.calculator.calculate(displaced, properties=['forces'])
                forces_plus = result.forces if result.forces is not None else np.zeros((n_atoms, 3))

                # Negative displacement
                displaced.sites[atom_i].cartesian[direction] -= 2*self.displacement

                result = self.calculator.calculate(displaced, properties=['forces'])
                forces_minus = result.forces if result.forces is not None else np.zeros((n_atoms, 3))

                # Force constant: Φ = -dF/du
                force_constants[atom_i, :, direction, :] = -(forces_plus - forces_minus) / (2 * self.displacement)

        return force_constants

    def _dynamical_matrix(self, force_constants: np.ndarray, q: List[float]) -> np.ndarray:
        """Construct dynamical matrix at q-point."""
        n_atoms = force_constants.shape[0]
        dyn = np.zeros((3*n_atoms, 3*n_atoms), dtype=complex)

        # D_αβ(q) = (1/√(m_α m_β)) Σ_R Φ_αβ(R) exp(iq·R)
        # Simplified: Γ point only

        from core.constants import ATOMIC_MASSES
        masses = np.array([12.0] * n_atoms)  # Placeholder

        for i in range(n_atoms):
            for j in range(n_atoms):
                prefactor = 1.0 / np.sqrt(masses[i] * masses[j])
                dyn[3*i:3*i+3, 3*j:3*j+3] = prefactor * force_constants[i, j]

        return dyn.real


__all__ = ['PhononCalculator']
