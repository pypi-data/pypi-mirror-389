"""
Machine Learning Calculator
============================

High-level calculator interface for ML potentials.
"""

import torch
from typing import Optional, Tuple, List

from core.base import Calculator, CalculationResult, FidelityLevel
from core.structure import Structure
from .neural_potentials import (
    NeuralPotential,
    OrbPotential,
    EgretPotential,
    MACEPotential
)


class MLCalculator(Calculator):
    """
    Universal ML calculator supporting multiple backends.

    Supports:
    - Orb (Orbital Materials)
    - Egret (Meta FAIR)
    - MACE (Cambridge)
    - CHGNet (Berkeley)
    - Custom models

    Example:
    --------
    ```python
    from materials_simpro.ml import MLCalculator, OrbPotential

    calc = MLCalculator(potential=OrbPotential())
    result = calc.calculate(structure, properties=['energy', 'forces'])
    ```
    """

    def __init__(
        self,
        potential: Optional[NeuralPotential] = None,
        device: str = 'cpu',
        **kwargs
    ):
        """
        Initialize ML calculator.

        Args:
            potential: Neural potential (default: Orb)
            device: 'cpu' or 'cuda'
        """
        super().__init__(
            fidelity=FidelityLevel.ML,
            name="ML-Potential",
            **kwargs
        )

        self.potential = potential or OrbPotential(device=device)
        self.device = device

    def calculate(
        self,
        structure: Structure,
        properties: List[str] = None
    ) -> CalculationResult:
        """
        Calculate properties using ML potential.

        Args:
            structure: Input structure
            properties: ['energy', 'forces', 'stress']

        Returns:
            CalculationResult
        """
        return self.potential.calculate(structure, properties)

    def optimize_geometry(
        self,
        structure: Structure,
        fmax: float = 0.01,
        max_steps: int = 200
    ) -> Tuple[Structure, CalculationResult]:
        """
        Optimize geometry using ML potential.

        ~1000x faster than DFT optimization!
        """
        return self.potential.optimize_geometry(structure, fmax, max_steps)

    def get_uncertainty(self, structure: Structure) -> Optional[float]:
        """Get prediction uncertainty (eV/atom)."""
        return self.potential.get_uncertainty(structure)


__all__ = ['MLCalculator']
