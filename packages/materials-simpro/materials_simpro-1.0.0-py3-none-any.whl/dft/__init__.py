"""
Density Functional Theory (DFT) Engine
=======================================

Complete implementation of Kohn-Sham Density Functional Theory.

Theoretical Framework:
----------------------
DFT is based on the Hohenberg-Kohn theorems (1964):
1. The ground state energy is a unique functional of the electron density ρ(r)
2. The correct ground state density minimizes the energy functional

The Kohn-Sham approach (1965) maps the interacting electron problem
to a non-interacting system with the same density:

    E[ρ] = T_s[ρ] + ∫ V_ext(r)ρ(r)dr + E_H[ρ] + E_xc[ρ]

where:
    T_s[ρ]: Non-interacting kinetic energy
    V_ext: External potential (nuclei)
    E_H[ρ]: Hartree (classical Coulomb) energy
    E_xc[ρ]: Exchange-correlation energy (quantum many-body effects)

The Kohn-Sham equations:
    [-ℏ²/2m ∇² + V_eff(r)]ψ_i(r) = ε_i ψ_i(r)

where the effective potential is:
    V_eff(r) = V_ext(r) + V_H(r) + V_xc(r)

Scientific References:
----------------------
[1] Hohenberg, P., & Kohn, W. (1964). Inhomogeneous electron gas.
    Physical Review, 136(3B), B864.
    DOI: 10.1103/PhysRev.136.B864

[2] Kohn, W., & Sham, L. J. (1965). Self-consistent equations including
    exchange and correlation effects. Physical Review, 140(4A), A1133.
    DOI: 10.1103/PhysRev.140.A1133

[3] Perdew, J. P., & Zunger, A. (1981). Self-interaction correction to
    density-functional approximations for many-electron systems.
    Physical Review B, 23(10), 5048.
    DOI: 10.1103/PhysRevB.23.5048

[4] Perdew, J. P., Burke, K., & Ernzerhof, M. (1996). Generalized gradient
    approximation made simple. Physical Review Letters, 77(18), 3865.
    DOI: 10.1103/PhysRevLett.77.3865

[5] Heyd, J., Scuseria, G. E., & Ernzerhof, M. (2003). Hybrid functionals
    based on a screened Coulomb potential. Journal of Chemical Physics, 118(18), 8207.
    DOI: 10.1063/1.1564060

[6] Sun, J., Ruzsinszky, A., & Perdew, J. P. (2015). Strongly constrained and
    appropriately normed semilocal density functional.
    Physical Review Letters, 115(3), 036402.
    DOI: 10.1103/PhysRevLett.115.036402

Implementation Notes:
---------------------
This implementation provides:
- Kohn-Sham equation solver (plane-wave basis)
- Multiple XC functionals (LDA, GGA-PBE, HSE06, SCAN)
- Pseudopotential support (norm-conserving, ultrasoft, PAW)
- Self-consistent field (SCF) iteration
- Forces and stress tensors (Hellmann-Feynman theorem)
- Band structure and DOS calculation
"""

from .kohn_sham import KohnShamSolver, SCFConvergence
from .xc_functionals import (
    XCFunctional,
    LDA_PZ,
    GGA_PBE,
    HybridHSE06,
    MetaGGA_SCAN
)
from .pseudopotentials import Pseudopotential, load_pseudopotential
from .calculator import DFTCalculator

__all__ = [
    # Kohn-Sham solver
    'KohnShamSolver',
    'SCFConvergence',
    # XC functionals
    'XCFunctional',
    'LDA_PZ',
    'GGA_PBE',
    'HybridHSE06',
    'MetaGGA_SCAN',
    # Pseudopotentials
    'Pseudopotential',
    'load_pseudopotential',
    # Main calculator
    'DFTCalculator',
]
