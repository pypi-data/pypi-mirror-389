"""
Molecular Dynamics Engine
==========================

Classical molecular dynamics for materials simulation.

Theoretical Framework:
----------------------
MD integrates Newton's equations of motion:
    F_i = m_i a_i = m_i d²r_i/dt²

For N atoms:
    r_i(t+Δt) = r_i(t) + v_i(t)Δt + (1/2)a_i(t)Δt²
    v_i(t+Δt) = v_i(t) + a_i(t)Δt

where forces F_i = -∇_i E(r₁, r₂, ..., rₙ) come from potential E.

Ensembles:
----------
1. **NVE (Microcanonical)**: Constant N, V, E
   - Energy conserving
   - No thermostat

2. **NVT (Canonical)**: Constant N, V, T
   - Nosé-Hoover thermostat
   - Berendsen thermostat

3. **NPT (Isothermal-isobaric)**: Constant N, P, T
   - Parrinello-Rahman barostat
   - Berendsen barostat

4. **NVE + Langevin**: Stochastic dynamics
   - Friction + random forces

Integration Algorithms:
-----------------------
- **Verlet**: Energy conserving, 2nd order
- **Velocity Verlet**: Improved stability
- **Leapfrog**: Symplectic integrator

Scientific References:
----------------------
[1] Verlet, L. (1967). Computer "experiments" on classical fluids. I.
    Thermodynamical properties of Lennard-Jones molecules.
    Physical Review, 159(1), 98.
    DOI: 10.1103/PhysRev.159.98

[2] Nosé, S. (1984). A molecular dynamics method for simulations in the
    canonical ensemble. Molecular Physics, 52(2), 255-268.
    DOI: 10.1080/00268978400101201

[3] Hoover, W. G. (1985). Canonical dynamics: Equilibrium phase-space distributions.
    Physical Review A, 31(3), 1695.
    DOI: 10.1103/PhysRevA.31.1695

[4] Parrinello, M., & Rahman, A. (1981). Polymorphic transitions in single
    crystals: A new molecular dynamics method.
    Journal of Applied Physics, 52(12), 7182-7190.
    DOI: 10.1063/1.328693

[5] Allen, M. P., & Tildesley, D. J. (2017). Computer simulation of liquids.
    Oxford University Press. ISBN: 978-0198803195
"""

from .integrators import (
    Integrator,
    VelocityVerlet,
    Verlet,
    Leapfrog
)
from .thermostats import (
    Thermostat,
    NoseHoover,
    Berendsen,
    Langevin
)
from .barostats import (
    Barostat,
    ParrinelloRahman,
    BerendsenBarostat
)
from .calculator import MDCalculator

__all__ = [
    # Integrators
    'Integrator', 'VelocityVerlet', 'Verlet', 'Leapfrog',
    # Thermostats
    'Thermostat', 'NoseHoover', 'Berendsen', 'Langevin',
    # Barostats
    'Barostat', 'ParrinelloRahman', 'BerendsenBarostat',
    # Calculator
    'MDCalculator',
]
