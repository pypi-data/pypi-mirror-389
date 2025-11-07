"""
Advanced Research Methods
==========================

Cutting-edge quantum chemistry and generative AI for materials discovery.

Modules:
- quantum_chemistry: CCSD(T), MRCI, advanced correlation
- generative_models: VAE, GAN, diffusion models for inverse design
- inverse_design: Target property ’ Structure generation

References:
- Bartlett & MusiaB (2007). DOI: 10.1103/RevModPhys.79.291
- Kingma & Welling (2013). arXiv:1312.6114
- Ho et al. (2020). arXiv:2006.11239
"""

from .quantum_chemistry import CCSDSolver, MRCISolver
from .generative_models import MaterialVAE, MaterialGAN, DiffusionModel
from .inverse_design import InverseDesigner

__all__ = [
    'CCSDSolver',
    'MRCISolver',
    'MaterialVAE',
    'MaterialGAN',
    'DiffusionModel',
    'InverseDesigner',
]
