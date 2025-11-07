"""
Physical Constants and Units
=============================

All values according to CODATA 2018 recommended values.

References:
-----------
[1] CODATA 2018: Tiesinga, E., Mohr, P. J., Newell, D. B., & Taylor, B. N. (2021).
    CODATA recommended values of the fundamental physical constants: 2018.
    Reviews of Modern Physics, 93(2), 025010.
    DOI: 10.1103/RevModPhys.93.025010

[2] NIST Reference: https://physics.nist.gov/cuu/Constants/
"""

import numpy as np
from typing import Final

# ============================================================================
# Fundamental Constants (CODATA 2018)
# ============================================================================

# Planck constant (J·s)
# DOI: 10.1103/RevModPhys.93.025010
PLANCK: Final[float] = 6.62607015e-34  # exact

# Reduced Planck constant (ℏ = h/2π) (J·s)
HBAR: Final[float] = 1.054571817e-34  # exact

# Elementary charge (C)
ELEMENTARY_CHARGE: Final[float] = 1.602176634e-19  # exact

# Speed of light in vacuum (m/s)
SPEED_OF_LIGHT: Final[float] = 299792458.0  # exact

# Boltzmann constant (J/K)
BOLTZMANN: Final[float] = 1.380649e-23  # exact

# Avogadro constant (mol⁻¹)
AVOGADRO: Final[float] = 6.02214076e23  # exact

# Electron mass (kg)
ELECTRON_MASS: Final[float] = 9.1093837015e-31  # uncertainty: 2.8e-40

# Proton mass (kg)
PROTON_MASS: Final[float] = 1.67262192369e-27  # uncertainty: 5.1e-37

# Bohr radius (m)
# a₀ = 4πε₀ℏ²/(mₑe²)
BOHR_RADIUS: Final[float] = 5.29177210903e-11  # uncertainty: 8.0e-21

# Hartree energy (J)
# Eₕ = mₑe⁴/(4πε₀)²ℏ²
HARTREE: Final[float] = 4.3597447222071e-18  # uncertainty: 8.5e-30

# Fine structure constant (dimensionless)
# α = e²/(4πε₀ℏc)
FINE_STRUCTURE: Final[float] = 7.2973525693e-3  # uncertainty: 1.1e-12

# Rydberg constant (m⁻¹)
# R∞ = α²mₑc/(2h)
RYDBERG: Final[float] = 10973731.568160  # uncertainty: 2.1e-5

# ============================================================================
# Unit Conversions
# ============================================================================

# Energy conversions to eV
HARTREE_TO_EV: Final[float] = 27.211386245988  # DOI: 10.1103/RevModPhys.93.025010
RYDBERG_TO_EV: Final[float] = 13.605693122994  # Ry = Eₕ/2
JOULE_TO_EV: Final[float] = 6.241509074461e18
KCAL_MOL_TO_EV: Final[float] = 0.043364106  # kcal/mol to eV
KJ_MOL_TO_EV: Final[float] = 0.010364269  # kJ/mol to eV

# Length conversions to Angstrom (Å)
BOHR_TO_ANGSTROM: Final[float] = 0.529177210903  # DOI: 10.1103/RevModPhys.93.025010
ANGSTROM_TO_BOHR: Final[float] = 1.0 / BOHR_TO_ANGSTROM
METER_TO_ANGSTROM: Final[float] = 1.0e10

# Force conversions (eV/Å)
HARTREE_BOHR_TO_EV_ANGSTROM: Final[float] = HARTREE_TO_EV / BOHR_TO_ANGSTROM

# Time conversions
FEMTOSECOND: Final[float] = 1.0e-15  # s
PICOSECOND: Final[float] = 1.0e-12  # s
ATOMIC_TIME_UNIT: Final[float] = HBAR / HARTREE  # ℏ/Eₕ ≈ 2.4189e-17 s

# Temperature
KELVIN_TO_EV: Final[float] = BOLTZMANN / ELEMENTARY_CHARGE  # kB/e ≈ 8.617e-5 eV/K

# ============================================================================
# DFT-Specific Constants
# ============================================================================

# Exchange-correlation functional parameters

# LDA (Local Density Approximation) - Perdew-Zunger parametrization
# Reference: Perdew, J. P., & Zunger, A. (1981). Physical Review B, 23(10), 5048.
# DOI: 10.1103/PhysRevB.23.5048
LDA_A_PARAM: Final[float] = 0.0311  # correlation parameter
LDA_B_PARAM: Final[float] = -0.048  # correlation parameter
LDA_C_PARAM: Final[float] = 0.002  # correlation parameter
LDA_D_PARAM: Final[float] = -0.0116  # correlation parameter

# PBE (Perdew-Burke-Ernzerhof) GGA functional parameters
# Reference: Perdew, J. P., Burke, K., & Ernzerhof, M. (1996).
# Physical Review Letters, 77(18), 3865.
# DOI: 10.1103/PhysRevLett.77.3865
PBE_KAPPA: Final[float] = 0.804  # gradient expansion parameter
PBE_MU: Final[float] = 0.2195149727645171  # β/(3*π²)^(2/3)

# HSE06 (Heyd-Scuseria-Ernzerhof) hybrid functional parameters
# Reference: Heyd, J., Scuseria, G. E., & Ernzerhof, M. (2003).
# Journal of Chemical Physics, 118(18), 8207.
# DOI: 10.1063/1.1564060
HSE_OMEGA: Final[float] = 0.11  # bohr⁻¹ (screening parameter)
HSE_ALPHA: Final[float] = 0.25  # exact exchange mixing parameter

# SCAN (Strongly Constrained and Appropriately Normed) meta-GGA parameters
# Reference: Sun, J., Ruzsinszky, A., & Perdew, J. P. (2015).
# Physical Review Letters, 115(3), 036402.
# DOI: 10.1103/PhysRevLett.115.036402
SCAN_C1C: Final[float] = 0.667  # interpolation parameter
SCAN_C2C: Final[float] = 0.8  # interpolation parameter
SCAN_K1: Final[float] = 0.065  # correlation parameter

# ============================================================================
# Numerical Parameters
# ============================================================================

# Convergence criteria (commonly used in DFT)
ENERGY_TOLERANCE_EV: Final[float] = 1.0e-6  # eV (SCF convergence)
FORCE_TOLERANCE_EV_ANGSTROM: Final[float] = 0.01  # eV/Å (geometry optimization)
STRESS_TOLERANCE_EV_ANGSTROM3: Final[float] = 0.001  # eV/Å³ (stress convergence)

# K-point sampling (Monkhorst-Pack grid density)
# Reference: Monkhorst, H. J., & Pack, J. D. (1976).
# Physical Review B, 13(12), 5188.
# DOI: 10.1103/PhysRevB.13.5188
KPOINT_DENSITY: Final[float] = 0.03  # Å⁻¹ (typical density)

# Plane-wave cutoff energies (eV) - typical values
CUTOFF_SOFT: Final[float] = 300.0  # eV (soft pseudopotentials)
CUTOFF_STANDARD: Final[float] = 500.0  # eV (standard accuracy)
CUTOFF_HARD: Final[float] = 700.0  # eV (hard pseudopotentials/high accuracy)

# ============================================================================
# Machine Learning Specific
# ============================================================================

# Neural network potential training parameters
# Based on: Schütt, K. T., et al. (2018). SchNet: A deep learning architecture
# for molecules and materials. Journal of Chemical Physics, 148(24), 241722.
# DOI: 10.1063/1.5019779
ML_CUTOFF_RADIUS: Final[float] = 5.0  # Å (typical interaction cutoff)
ML_NUM_GAUSSIANS: Final[int] = 50  # Gaussian basis functions for distance encoding

# ============================================================================
# Utility Functions
# ============================================================================

def eV_to_hartree(energy: float) -> float:
    """Convert energy from eV to Hartree."""
    return energy / HARTREE_TO_EV

def hartree_to_eV(energy: float) -> float:
    """Convert energy from Hartree to eV."""
    return energy * HARTREE_TO_EV

def angstrom_to_bohr(length: float) -> float:
    """Convert length from Angstrom to Bohr."""
    return length * ANGSTROM_TO_BOHR

def bohr_to_angstrom(length: float) -> float:
    """Convert length from Bohr to Angstrom."""
    return length * BOHR_TO_ANGSTROM

def kelvin_to_eV(temperature: float) -> float:
    """Convert temperature from Kelvin to eV."""
    return temperature * KELVIN_TO_EV

def eV_to_kelvin(energy: float) -> float:
    """Convert energy from eV to Kelvin."""
    return energy / KELVIN_TO_EV

# ============================================================================
# Atomic Data
# ============================================================================

# Atomic masses (amu) - IUPAC 2016
# Reference: Meija, J., et al. (2016). Pure and Applied Chemistry, 88(3), 265-291.
# DOI: 10.1515/pac-2015-0305
ATOMIC_MASSES = {
    'H': 1.008, 'He': 4.003,
    'Li': 6.941, 'Be': 9.012, 'B': 10.81, 'C': 12.01, 'N': 14.01, 'O': 16.00, 'F': 19.00, 'Ne': 20.18,
    'Na': 22.99, 'Mg': 24.31, 'Al': 26.98, 'Si': 28.09, 'P': 30.97, 'S': 32.07, 'Cl': 35.45, 'Ar': 39.95,
    'K': 39.10, 'Ca': 40.08, 'Sc': 44.96, 'Ti': 47.87, 'V': 50.94, 'Cr': 52.00, 'Mn': 54.94, 'Fe': 55.85,
    'Co': 58.93, 'Ni': 58.69, 'Cu': 63.55, 'Zn': 65.38, 'Ga': 69.72, 'Ge': 72.63, 'As': 74.92, 'Se': 78.97,
    'Br': 79.90, 'Kr': 83.80,
}

# Covalent radii (Å) - Cordero et al.
# Reference: Cordero, B., et al. (2008). Dalton Transactions, (21), 2832-2838.
# DOI: 10.1039/B801115J
COVALENT_RADII = {
    'H': 0.31, 'He': 0.28,
    'Li': 1.28, 'Be': 0.96, 'B': 0.84, 'C': 0.76, 'N': 0.71, 'O': 0.66, 'F': 0.57, 'Ne': 0.58,
    'Na': 1.66, 'Mg': 1.41, 'Al': 1.21, 'Si': 1.11, 'P': 1.07, 'S': 1.05, 'Cl': 1.02, 'Ar': 1.06,
    'K': 2.03, 'Ca': 1.76, 'Sc': 1.70, 'Ti': 1.60, 'V': 1.53, 'Cr': 1.39, 'Mn': 1.39, 'Fe': 1.32,
    'Co': 1.26, 'Ni': 1.24, 'Cu': 1.32, 'Zn': 1.22, 'Ga': 1.22, 'Ge': 1.20, 'As': 1.19, 'Se': 1.20,
    'Br': 1.20, 'Kr': 1.16,
}

__all__ = [
    # Fundamental constants
    'PLANCK', 'HBAR', 'ELEMENTARY_CHARGE', 'SPEED_OF_LIGHT',
    'BOLTZMANN', 'AVOGADRO', 'ELECTRON_MASS', 'PROTON_MASS',
    'BOHR_RADIUS', 'HARTREE', 'FINE_STRUCTURE', 'RYDBERG',
    # Unit conversions
    'HARTREE_TO_EV', 'RYDBERG_TO_EV', 'JOULE_TO_EV',
    'BOHR_TO_ANGSTROM', 'ANGSTROM_TO_BOHR',
    'HARTREE_BOHR_TO_EV_ANGSTROM',
    'FEMTOSECOND', 'PICOSECOND', 'ATOMIC_TIME_UNIT',
    'KELVIN_TO_EV',
    # DFT parameters
    'PBE_KAPPA', 'PBE_MU', 'HSE_OMEGA', 'HSE_ALPHA',
    'SCAN_C1C', 'SCAN_C2C', 'SCAN_K1',
    # Numerical parameters
    'ENERGY_TOLERANCE_EV', 'FORCE_TOLERANCE_EV_ANGSTROM',
    'CUTOFF_SOFT', 'CUTOFF_STANDARD', 'CUTOFF_HARD',
    # ML parameters
    'ML_CUTOFF_RADIUS', 'ML_NUM_GAUSSIANS',
    # Utility functions
    'eV_to_hartree', 'hartree_to_eV',
    'angstrom_to_bohr', 'bohr_to_angstrom',
    'kelvin_to_eV', 'eV_to_kelvin',
    # Atomic data
    'ATOMIC_MASSES', 'COVALENT_RADII',
]
