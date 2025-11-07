"""
Materials-SimPro: The World's Most Advanced Materials Simulation Platform
==========================================================================

A comprehensive materials simulation platform integrating:
- Multi-fidelity computation (ML → DFT → Post-DFT)
- AI-powered materials discovery
- Universal materials database (5M+ materials)
- Cloud-native infrastructure

Authors: Materials-SimPro Development Team
License: MIT
Version: 1.0.0-alpha
"""

__version__ = "1.0.0-alpha"
__author__ = "Materials-SimPro Development Team"
__license__ = "MIT"

from .core.base import ComputationEngine, Calculator
from .core.structure import Structure, Lattice
from .core.constants import *

__all__ = [
    "ComputationEngine",
    "Calculator",
    "Structure",
    "Lattice",
    "__version__",
]
