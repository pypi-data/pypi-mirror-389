"""
Property Calculators
====================

Compute materials properties from DFT/ML calculations:
- Elastic constants
- Phonon spectra
- Optical properties
- Electronic properties (band structure, DOS)

References:
-----------
[1] Wallace, D. C. (1972). Thermodynamics of crystals.
    Wiley. ISBN: 978-0471918554

[2] Baroni, S., et al. (2001). Phonons and related crystal properties from
    density-functional perturbation theory. Reviews of Modern Physics, 73(2), 515.
    DOI: 10.1103/RevModPhys.73.515
"""

from .elastic import ElasticCalculator
from .phonon import PhononCalculator
from .electronic import BandStructureCalculator, DOSCalculator

__all__ = [
    'ElasticCalculator',
    'PhononCalculator',
    'BandStructureCalculator',
    'DOSCalculator',
]
