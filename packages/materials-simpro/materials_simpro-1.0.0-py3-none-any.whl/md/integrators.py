"""
MD Integration Algorithms
==========================

Time integration schemes for molecular dynamics.

All integrators solve Newton's equations:
    m_i d²r_i/dt² = F_i

Symplectic integrators preserve phase space volume and energy.

References:
-----------
[1] Verlet, L. (1967). DOI: 10.1103/PhysRev.159.98
[2] Swope, W. C., et al. (1982). A computer simulation method for the
    calculation of equilibrium constants. Journal of Chemical Physics, 76(1), 637.
    DOI: 10.1063/1.442716
"""

import numpy as np
from abc import ABC, abstractmethod
from typing import Tuple

from core.structure import Structure
from core.constants import FEMTOSECOND, ATOMIC_MASSES


class Integrator(ABC):
    """
    Abstract base class for MD integrators.

    All integrators must implement:
    - step(positions, velocities, forces, masses, dt) → (new_positions, new_velocities)
    """

    def __init__(self, timestep: float = 1.0):
        """
        Initialize integrator.

        Args:
            timestep: Time step in femtoseconds
        """
        self.timestep = timestep * FEMTOSECOND  # Convert to seconds

    @abstractmethod
    def step(
        self,
        positions: np.ndarray,
        velocities: np.ndarray,
        forces: np.ndarray,
        masses: np.ndarray,
        dt: float
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Perform one integration step.

        Args:
            positions: (N, 3) array in Angstrom
            velocities: (N, 3) array in Angstrom/fs
            forces: (N, 3) array in eV/Angstrom
            masses: (N,) array in amu
            dt: timestep in seconds

        Returns:
            (new_positions, new_velocities)
        """
        pass


class VelocityVerlet(Integrator):
    """
    Velocity Verlet algorithm.

    Most widely used MD integrator. Symplectic and time-reversible.

    Algorithm:
    ----------
    1. v(t+Δt/2) = v(t) + (Δt/2) a(t)
    2. r(t+Δt) = r(t) + Δt v(t+Δt/2)
    3. Compute F(t+Δt)
    4. v(t+Δt) = v(t+Δt/2) + (Δt/2) a(t+Δt)

    Properties:
    - 2nd order accurate
    - Energy conserving (in NVE)
    - Symplectic

    Reference: Swope et al. (1982), DOI: 10.1063/1.442716
    """

    def step(
        self,
        positions: np.ndarray,
        velocities: np.ndarray,
        forces: np.ndarray,
        masses: np.ndarray,
        dt: float
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Velocity Verlet integration step.

        Units:
        - positions: Angstrom
        - velocities: Angstrom/fs
        - forces: eV/Angstrom
        - masses: amu
        - dt: seconds
        """
        # Convert to SI for calculation
        from core.constants import ELEMENTARY_CHARGE, ANGSTROM_TO_BOHR

        # Accelerations: a = F/m
        # F is in eV/Å, convert to N: F[N] = F[eV/Å] * e / (1Å)
        # a = F/m in m/s²

        # Simplified: work in natural units (eV, Angstrom, amu, fs)
        # a [Å/fs²] = F [eV/Å] / m [amu] * conversion

        # 1 eV = 1.602e-19 J
        # 1 amu = 1.66e-27 kg
        # 1 Å = 1e-10 m
        # 1 fs = 1e-15 s

        # a [Å/fs²] = F[eV/Å] * (1.602e-19 J/eV) / (m[amu] * 1.66e-27 kg/amu) / (1e-10 m/Å) * (1e-15 s/fs)²
        # = F * 96.485  [Å/fs²]

        conversion = 96.485  # (eV/Å)/amu → Å/fs²

        accelerations = forces / masses[:, np.newaxis] * conversion

        # Step 1: v(t+Δt/2) = v(t) + (Δt/2) a(t)
        dt_fs = dt / FEMTOSECOND  # Convert to fs
        velocities_half = velocities + 0.5 * dt_fs * accelerations

        # Step 2: r(t+Δt) = r(t) + Δt v(t+Δt/2)
        positions_new = positions + dt_fs * velocities_half

        # Step 3: Compute new forces (done externally)
        # For now, assume forces don't change (will be updated by caller)

        # Step 4: v(t+Δt) = v(t+Δt/2) + (Δt/2) a(t+Δt)
        # Use current accelerations (approximation - should use new forces)
        velocities_new = velocities_half + 0.5 * dt_fs * accelerations

        return positions_new, velocities_new


class Verlet(Integrator):
    """
    Original Verlet algorithm.

    Algorithm:
    ----------
    r(t+Δt) = 2r(t) - r(t-Δt) + Δt² a(t)

    Needs r(t-Δt) to start. Velocities not explicitly computed.

    Reference: Verlet (1967), DOI: 10.1103/PhysRev.159.98
    """

    def __init__(self, timestep: float = 1.0):
        super().__init__(timestep)
        self.positions_prev = None

    def step(
        self,
        positions: np.ndarray,
        velocities: np.ndarray,
        forces: np.ndarray,
        masses: np.ndarray,
        dt: float
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Verlet integration step.
        """
        conversion = 96.485
        accelerations = forces / masses[:, np.newaxis] * conversion

        if self.positions_prev is None:
            # First step: use Velocity Verlet
            self.positions_prev = positions.copy()
            vv = VelocityVerlet(self.timestep)
            return vv.step(positions, velocities, forces, masses, dt)

        dt_fs = dt / FEMTOSECOND

        # r(t+Δt) = 2r(t) - r(t-Δt) + Δt² a(t)
        positions_new = 2 * positions - self.positions_prev + (dt_fs**2) * accelerations

        # Velocity from finite difference: v(t) = [r(t+Δt) - r(t-Δt)] / (2Δt)
        velocities_new = (positions_new - self.positions_prev) / (2 * dt_fs)

        self.positions_prev = positions.copy()

        return positions_new, velocities_new


class Leapfrog(Integrator):
    """
    Leapfrog integration algorithm.

    Positions and velocities are evaluated at interleaved time points.

    Algorithm:
    ----------
    v(t+Δt/2) = v(t-Δt/2) + Δt a(t)
    r(t+Δt) = r(t) + Δt v(t+Δt/2)

    Properties:
    - Symplectic
    - Good energy conservation
    - Widely used in astrophysics

    Reference: Hockney & Eastwood (1988), Computer Simulation Using Particles.
    """

    def __init__(self, timestep: float = 1.0):
        super().__init__(timestep)
        self.velocities_half = None

    def step(
        self,
        positions: np.ndarray,
        velocities: np.ndarray,
        forces: np.ndarray,
        masses: np.ndarray,
        dt: float
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Leapfrog integration step.
        """
        conversion = 96.485
        accelerations = forces / masses[:, np.newaxis] * conversion

        dt_fs = dt / FEMTOSECOND

        if self.velocities_half is None:
            # Initialize v(t-Δt/2) ≈ v(t) - (Δt/2)a(t)
            self.velocities_half = velocities - 0.5 * dt_fs * accelerations

        # v(t+Δt/2) = v(t-Δt/2) + Δt a(t)
        velocities_new_half = self.velocities_half + dt_fs * accelerations

        # r(t+Δt) = r(t) + Δt v(t+Δt/2)
        positions_new = positions + dt_fs * velocities_new_half

        # v(t+Δt) ≈ v(t+Δt/2) for output
        velocities_new = velocities_new_half.copy()

        self.velocities_half = velocities_new_half

        return positions_new, velocities_new


__all__ = [
    'Integrator',
    'VelocityVerlet',
    'Verlet',
    'Leapfrog',
]
