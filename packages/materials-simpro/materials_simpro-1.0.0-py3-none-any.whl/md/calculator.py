"""
MD Calculator
=============

High-level interface for molecular dynamics simulations.
"""

import numpy as np
from typing import Optional, List, Tuple

from core.base import Calculator, CalculationResult, FidelityLevel
from core.structure import Structure
from .integrators import VelocityVerlet, Integrator
from .thermostats import Thermostat, Berendsen


class MDCalculator(Calculator):
    """
    Molecular dynamics calculator.

    Example:
    --------
    ```python
    md = MDCalculator(
        potential=OrbPotential(),
        integrator=VelocityVerlet(timestep=1.0),
        thermostat=Berendsen(temperature=300),
        ensemble='NVT'
    )

    trajectory = md.run(structure, steps=1000)
    ```
    """

    def __init__(
        self,
        potential: Calculator,
        integrator: Optional[Integrator] = None,
        thermostat: Optional[Thermostat] = None,
        ensemble: str = 'NVE',
        **kwargs
    ):
        super().__init__(
            fidelity=FidelityLevel.ML,  # Typically use ML potentials
            name="MD",
            **kwargs
        )

        self.potential = potential
        self.integrator = integrator or VelocityVerlet(timestep=1.0)
        self.thermostat = thermostat
        self.ensemble = ensemble

    def calculate(
        self,
        structure: Structure,
        properties: List[str] = None
    ) -> CalculationResult:
        """Single point calculation."""
        return self.potential.calculate(structure, properties)

    def run(
        self,
        structure: Structure,
        steps: int = 1000,
        temperature: float = 300.0
    ) -> List[Structure]:
        """
        Run MD simulation.

        Args:
            structure: Initial structure
            steps: Number of MD steps
            temperature: Initial temperature (K)

        Returns:
            List of structures (trajectory)
        """
        from core.constants import ATOMIC_MASSES

        # Initialize
        positions = np.array([site.cartesian for site in structure.sites])
        masses = np.array([ATOMIC_MASSES.get(site.element, 12.0) for site in structure.sites])

        # Initialize velocities (Maxwell-Boltzmann)
        velocities = self._initialize_velocities(masses, temperature)

        trajectory = []

        for step in range(steps):
            # Compute forces
            result = self.potential.calculate(structure, properties=['forces'])
            forces = result.forces if result.forces is not None else np.zeros_like(positions)

            # Integrate
            positions, velocities = self.integrator.step(
                positions, velocities, forces, masses, self.integrator.timestep
            )

            # Apply thermostat
            if self.thermostat:
                velocities = self.thermostat.apply(velocities, masses, self.integrator.timestep)

            # Update structure
            for i, site in enumerate(structure.sites):
                site.cartesian = positions[i]

            if step % 10 == 0:
                trajectory.append(structure.copy())

        return trajectory

    def _initialize_velocities(self, masses: np.ndarray, temperature: float) -> np.ndarray:
        """Initialize velocities from Maxwell-Boltzmann distribution."""
        from core.constants import KELVIN_TO_EV

        kB_T = temperature * KELVIN_TO_EV
        n_atoms = len(masses)

        # σ = sqrt(k_B T / m)
        sigma = np.sqrt(kB_T / masses) * 98.0  # conversion to Å/fs

        velocities = np.random.normal(0, 1, (n_atoms, 3))
        velocities *= sigma[:, np.newaxis]

        # Remove center of mass motion
        velocities -= np.mean(velocities, axis=0)

        return velocities

    def optimize_geometry(self, structure, fmax=0.01, max_steps=200):
        """Use potential's optimizer."""
        return self.potential.optimize_geometry(structure, fmax, max_steps)


__all__ = ['MDCalculator']
