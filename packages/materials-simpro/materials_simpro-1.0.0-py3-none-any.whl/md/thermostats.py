"""
Thermostats for MD
==================

Temperature control algorithms for NVT ensemble.

A thermostat maintains constant temperature by:
- Rescaling velocities (Berendsen)
- Adding friction + noise (Langevin)
- Extended Lagrangian (Nosé-Hoover)

References:
-----------
[1] Nosé, S. (1984). DOI: 10.1080/00268978400101201
[2] Hoover, W. G. (1985). DOI: 10.1103/PhysRevA.31.1695
[3] Berendsen, H. J., et al. (1984). Molecular dynamics with coupling to an
    external bath. Journal of Chemical Physics, 81(8), 3684-3690.
    DOI: 10.1063/1.448118
"""

import numpy as np
from abc import ABC, abstractmethod
from typing import Tuple

from core.constants import BOLTZMANN, ELEMENTARY_CHARGE, ATOMIC_MASSES


class Thermostat(ABC):
    """
    Abstract base class for thermostats.
    """

    def __init__(self, temperature: float):
        """
        Initialize thermostat.

        Args:
            temperature: Target temperature in Kelvin
        """
        self.temperature = temperature

    @abstractmethod
    def apply(
        self,
        velocities: np.ndarray,
        masses: np.ndarray,
        dt: float
    ) -> np.ndarray:
        """
        Apply thermostat to velocities.

        Args:
            velocities: (N, 3) velocities in Angstrom/fs
            masses: (N,) masses in amu
            dt: timestep in seconds

        Returns:
            Modified velocities
        """
        pass

    def compute_temperature(
        self,
        velocities: np.ndarray,
        masses: np.ndarray
    ) -> float:
        """
        Compute instantaneous temperature.

        From kinetic energy:
        (3/2) N k_B T = (1/2) Σ m_i v_i²

        T = (1/(3Nk_B)) Σ m_i v_i²

        Args:
            velocities: Velocities in Angstrom/fs
            masses: Masses in amu

        Returns:
            Temperature in Kelvin
        """
        # Kinetic energy per atom
        # KE = (1/2) m v²

        # Convert velocities from Å/fs to m/s
        # v[m/s] = v[Å/fs] * 1e-10 / 1e-15 = v * 1e5
        v_si = velocities * 1e5  # m/s

        # Mass in kg
        m_si = masses * 1.66053906660e-27  # kg

        # Kinetic energy in Joules
        ke = 0.5 * np.sum(m_si[:, np.newaxis] * v_si**2)

        # Temperature: T = 2*KE / (3*N*k_B)
        n_atoms = len(masses)
        temperature = 2 * ke / (3 * n_atoms * BOLTZMANN)

        return temperature


class NoseHoover(Thermostat):
    """
    Nosé-Hoover thermostat.

    Adds an extra degree of freedom (heat bath variable ξ) that couples
    to the system kinetically.

    Equations of motion:
    --------------------
    dr/dt = v
    dv/dt = F/m - ξv
    dξ/dt = (T_current - T_target) / τ²

    where τ is the coupling timescale.

    Properties:
    - Generates canonical (NVT) ensemble
    - Time-reversible
    - Deterministic

    References:
    -----------
    Nosé (1984): DOI: 10.1080/00268978400101201
    Hoover (1985): DOI: 10.1103/PhysRevA.31.1695
    """

    def __init__(self, temperature: float, tau: float = 100.0):
        """
        Initialize Nosé-Hoover thermostat.

        Args:
            temperature: Target temperature (K)
            tau: Coupling timescale (fs)
        """
        super().__init__(temperature)
        self.tau = tau
        self.xi = 0.0  # Heat bath variable

    def apply(
        self,
        velocities: np.ndarray,
        masses: np.ndarray,
        dt: float
    ) -> np.ndarray:
        """
        Apply Nosé-Hoover thermostat.
        """
        from core.constants import FEMTOSECOND

        # Current temperature
        T_current = self.compute_temperature(velocities, masses)

        # Update heat bath variable
        # dξ/dt = (T_current - T_target) / τ²
        dt_fs = dt / FEMTOSECOND
        d_xi = (T_current - self.temperature) / (self.tau**2) * dt_fs
        self.xi += d_xi

        # Update velocities: dv/dt = -ξv
        # v(t+dt) = v(t) exp(-ξ dt)
        velocities_new = velocities * np.exp(-self.xi * dt_fs)

        return velocities_new


class Berendsen(Thermostat):
    """
    Berendsen thermostat.

    Simple velocity rescaling with exponential relaxation to target temperature.

    Algorithm:
    ----------
    λ = sqrt(1 + (dt/τ) * (T_target/T_current - 1))
    v_new = λ * v

    Properties:
    - Simple and efficient
    - Does NOT generate canonical ensemble
    - Good for equilibration
    - Poor for production runs (use Nosé-Hoover instead)

    Reference: Berendsen et al. (1984), DOI: 10.1063/1.448118
    """

    def __init__(self, temperature: float, tau: float = 100.0):
        """
        Initialize Berendsen thermostat.

        Args:
            temperature: Target temperature (K)
            tau: Coupling timescale (fs)
        """
        super().__init__(temperature)
        self.tau = tau

    def apply(
        self,
        velocities: np.ndarray,
        masses: np.ndarray,
        dt: float
    ) -> np.ndarray:
        """
        Apply Berendsen thermostat.
        """
        from core.constants import FEMTOSECOND

        T_current = self.compute_temperature(velocities, masses)

        if T_current < 1e-6:
            return velocities

        dt_fs = dt / FEMTOSECOND

        # Scaling factor
        lambda_scale = np.sqrt(1.0 + (dt_fs / self.tau) * (self.temperature / T_current - 1.0))

        velocities_new = lambda_scale * velocities

        return velocities_new


class Langevin(Thermostat):
    """
    Langevin thermostat (stochastic dynamics).

    Adds friction and random forces to maintain temperature:

    dv/dt = F/m - γv + R(t)

    where:
    - γ: friction coefficient
    - R(t): random force (Gaussian white noise)

    ⟨R_i(t)R_j(t')⟩ = 2γk_B T δ_ij δ(t-t')  (fluctuation-dissipation)

    Properties:
    - Generates canonical ensemble
    - Stochastic (not time-reversible)
    - Good for sampling

    Reference: Allen & Tildesley (2017), Computer Simulation of Liquids
    """

    def __init__(self, temperature: float, gamma: float = 0.01):
        """
        Initialize Langevin thermostat.

        Args:
            temperature: Target temperature (K)
            gamma: Friction coefficient (1/fs)
        """
        super().__init__(temperature)
        self.gamma = gamma

    def apply(
        self,
        velocities: np.ndarray,
        masses: np.ndarray,
        dt: float
    ) -> np.ndarray:
        """
        Apply Langevin thermostat.
        """
        from core.constants import FEMTOSECOND

        dt_fs = dt / FEMTOSECOND

        # Friction term: v' = v * exp(-γ dt)
        friction_factor = np.exp(-self.gamma * dt_fs)

        # Random force: σ = sqrt(2γk_B T / m) * sqrt(dt)
        # In reduced units (Å/fs):
        # σ = sqrt(k_B T / m) * sqrt(2γ dt) * conversion

        # k_B T in eV
        from core.constants import KELVIN_TO_EV
        kB_T = self.temperature * KELVIN_TO_EV

        # σ [Å/fs] = sqrt(kB_T[eV] / m[amu]) * sqrt(2γ[1/fs] * dt[fs]) * conversion
        # conversion ≈ 98 (from eV/amu to (Å/fs)²)

        conversion = 98.0
        sigma = np.sqrt(kB_T / masses) * np.sqrt(2 * self.gamma * dt_fs) * conversion

        # Random forces (Gaussian)
        random_forces = np.random.normal(0, 1, velocities.shape)
        random_forces *= sigma[:, np.newaxis]

        # Update velocities
        velocities_new = friction_factor * velocities + random_forces

        return velocities_new


__all__ = [
    'Thermostat',
    'NoseHoover',
    'Berendsen',
    'Langevin',
]
