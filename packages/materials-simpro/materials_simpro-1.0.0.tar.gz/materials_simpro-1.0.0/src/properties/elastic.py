"""
Elastic Properties
==================

Calculate elastic constants, moduli, and mechanical properties.

Theory:
-------
Elastic constants relate stress σ to strain ε via Hooke's law:
    σ_ij = C_ijkl ε_kl

For cubic symmetry, reduces to 3 independent constants: C₁₁, C₁₂, C₄₄

Bulk modulus: B = (C₁₁ + 2C₁₂) / 3
Shear modulus: G = (C₁₁ - C₁₂ + 3C₄₄) / 5  (Voigt average)

References:
-----------
[1] Nye, J. F. (1985). Physical properties of crystals.
    Oxford University Press. ISBN: 978-0198511656

[2] Le Page, Y., & Saxe, P. (2002). Symmetry-general least-squares extraction
    of elastic data for strained materials from ab initio calculations of stress.
    Physical Review B, 65(10), 104104.
    DOI: 10.1103/PhysRevB.65.104104
"""

import numpy as np
from typing import Dict

from core.structure import Structure
from core.base import Calculator


class ElasticCalculator:
    """
    Calculate elastic tensor using finite differences.

    Method:
    -------
    1. Apply small strains ε to lattice
    2. Compute stress σ for each strain
    3. Fit C_ijkl via σ = C·ε
    """

    def __init__(self, calculator: Calculator, strain_magnitude: float = 0.01):
        """
        Args:
            calculator: DFT or ML calculator
            strain_magnitude: Strain amplitude (default 1%)
        """
        self.calculator = calculator
        self.strain_magnitude = strain_magnitude

    def calculate(self, structure: Structure) -> Dict:
        """
        Calculate full elastic tensor.

        Returns:
            Dictionary with:
            - elastic_tensor: 6x6 in Voigt notation (GPa)
            - bulk_modulus: B (GPa)
            - shear_modulus: G (GPa)
            - youngs_modulus: E (GPa)
            - poisson_ratio: ν
        """
        # Strain patterns (Voigt notation)
        strains = self._generate_strains()

        stresses = []
        for strain in strains:
            stressed_structure = self._apply_strain(structure, strain)
            result = self.calculator.calculate(stressed_structure, properties=['stress'])
            stress = result.stress if result.stress is not None else np.zeros((3, 3))
            stresses.append(self._stress_to_voigt(stress))

        # Fit elastic tensor
        elastic_tensor = self._fit_elastic_tensor(strains, stresses)

        # Compute moduli
        moduli = self._compute_moduli(elastic_tensor)

        return {
            'elastic_tensor': elastic_tensor,
            **moduli
        }

    def _generate_strains(self) -> np.ndarray:
        """Generate strain patterns for finite difference."""
        δ = self.strain_magnitude

        # 6 independent strains in Voigt notation
        strains = []
        for i in range(6):
            strain = np.zeros(6)
            strain[i] = δ
            strains.append(strain)
            strain[i] = -δ
            strains.append(strain)

        return np.array(strains)

    def _apply_strain(self, structure: Structure, strain_voigt: np.ndarray) -> Structure:
        """Apply strain to structure."""
        # Convert Voigt to matrix
        strain_matrix = np.array([
            [strain_voigt[0], strain_voigt[5]/2, strain_voigt[4]/2],
            [strain_voigt[5]/2, strain_voigt[1], strain_voigt[3]/2],
            [strain_voigt[4]/2, strain_voigt[3]/2, strain_voigt[2]]
        ])

        # Deformation gradient: F = I + ε
        F = np.eye(3) + strain_matrix

        # Apply to lattice
        new_lattice_matrix = np.dot(F, structure.lattice.matrix)

        strained = structure.copy()
        strained.lattice.matrix = new_lattice_matrix

        return strained

    def _stress_to_voigt(self, stress: np.ndarray) -> np.ndarray:
        """Convert 3x3 stress tensor to Voigt notation."""
        return np.array([
            stress[0, 0], stress[1, 1], stress[2, 2],
            stress[1, 2], stress[0, 2], stress[0, 1]
        ])

    def _fit_elastic_tensor(self, strains: np.ndarray, stresses: np.ndarray) -> np.ndarray:
        """Fit elastic tensor from strain-stress data."""
        # σ = C·ε  →  C = σ/ε (least squares)
        # Simplified: assume linear response
        C = np.zeros((6, 6))

        for i in range(6):
            for j in range(6):
                # Finite difference
                idx_plus = 2*j
                idx_minus = 2*j + 1
                C[i, j] = (stresses[idx_plus][i] - stresses[idx_minus][i]) / (2 * self.strain_magnitude)

        return C

    def _compute_moduli(self, C: np.ndarray) -> Dict:
        """
        Compute bulk, shear, Young's moduli.

        Voigt average (upper bound):
        B_V = (C₁₁ + C₂₂ + C₃₃ + 2(C₁₂ + C₁₃ + C₂₃)) / 9
        G_V = (C₁₁ + C₂₂ + C₃₃ - C₁₂ - C₁₃ - C₂₃ + 3(C₄₄ + C₅₅ + C₆₆)) / 15

        Young's modulus: E = 9BG / (3B + G)
        Poisson ratio: ν = (3B - 2G) / (6B + 2G)
        """
        # Bulk modulus (Voigt)
        B = (C[0,0] + C[1,1] + C[2,2] + 2*(C[0,1] + C[0,2] + C[1,2])) / 9.0

        # Shear modulus (Voigt)
        G = (C[0,0] + C[1,1] + C[2,2] - C[0,1] - C[0,2] - C[1,2] + 3*(C[3,3] + C[4,4] + C[5,5])) / 15.0

        # Young's modulus
        E = 9*B*G / (3*B + G)

        # Poisson ratio
        nu = (3*B - 2*G) / (6*B + 2*G)

        return {
            'bulk_modulus': B,
            'shear_modulus': G,
            'youngs_modulus': E,
            'poisson_ratio': nu
        }


__all__ = ['ElasticCalculator']
