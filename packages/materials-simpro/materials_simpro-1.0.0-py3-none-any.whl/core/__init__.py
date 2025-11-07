"""
Core computation engines and base classes
==========================================

This module provides the foundational classes for all computation methods:
- Base computation engine interface
- Calculator abstract class
- Multi-fidelity management
- Adaptive method selection

Scientific References:
----------------------
[1] Kohn, W., & Sham, L. J. (1965). Self-consistent equations including
    exchange and correlation effects. Physical Review, 140(4A), A1133.
    DOI: 10.1103/PhysRev.140.A1133

[2] Behler, J., & Parrinello, M. (2007). Generalized neural-network
    representation of high-dimensional potential-energy surfaces.
    Physical Review Letters, 98(14), 146401.
    DOI: 10.1103/PhysRevLett.98.146401

[3] Unke, O. T., et al. (2021). Machine learning force fields.
    Chemical Reviews, 121(16), 10142-10186.
    DOI: 10.1021/acs.chemrev.0c01111
"""

from .base import ComputationEngine, Calculator, FidelityLevel
from .structure import Structure, Lattice, Site
from .constants import *

__all__ = [
    "ComputationEngine",
    "Calculator",
    "FidelityLevel",
    "Structure",
    "Lattice",
    "Site",
]
