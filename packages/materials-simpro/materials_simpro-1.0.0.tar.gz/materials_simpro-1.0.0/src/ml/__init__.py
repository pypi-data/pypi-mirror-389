"""
Machine Learning Potentials
============================

Neural network force fields and ML-accelerated methods for materials simulation.

The ML Revolution in Materials Science:
---------------------------------------
Machine learning potentials (MLPs) achieve near-DFT accuracy at MD speed (~1000x faster).

Key breakthrough: Learn the Born-Oppenheimer potential energy surface from data:
    E(R) ≈ f_NN(R; θ)

where R = {R₁, R₂, ..., Rₙ} are atomic positions and θ are network parameters.

State-of-the-Art Models (2024-2025):
------------------------------------

1. **Orb (Orbital Materials, 2024)**
   - 100,000 atoms in <1 second
   - Pre-trained on diverse materials (Alexandria dataset)
   - Graph neural network with equivariant message passing
   - Reference: https://docs.orbitalmaterials.com/

2. **Egret (Meta FAIR, 2024)**
   - DFT accuracy at MD speed
   - Active learning framework
   - Target: ~80% computational correlation validation
   - OMat24 dataset (>100M structures)

3. **MACE (2022)**
   - Higher-order message passing
   - Equivariant to SE(3) (rotation + translation)
   - State-of-the-art on MD17, MD22 benchmarks
   - Reference: DOI 10.48550/arXiv.2206.07697

4. **CHGNet (2023)**
   - Crystal Hamiltonian Graph Neural Network
   - Predicts energy, forces, stress, magnetic moments
   - Pre-trained on Materials Project data
   - Reference: DOI 10.1038/s42256-023-00716-3

5. **M3GNet (2022)**
   - Materials 3-body Graph Network
   - Many-body interactions via message passing
   - Universal materials potential
   - Reference: DOI 10.1038/s43588-022-00349-3

Mathematical Framework:
-----------------------

Message Passing Neural Networks:
    h_i^{(l+1)} = φ(h_i^{(l)}, Σ_j ψ(h_i^{(l)}, h_j^{(l)}, r_ij))

where:
- h_i: node (atom) features
- φ, ψ: learnable functions (neural networks)
- r_ij: interatomic distance

Equivariant Networks (preserve rotational symmetry):
    f(R ⊙ Q) = f(R) ⊙ Q   for all rotations Q

This is essential for physical correctness!

Energy Prediction:
    E = Σ_i E_atom(h_i^{(L)})

Forces (autodiff through graph):
    F_i = -∇_{R_i} E

Scientific References:
----------------------
[1] Behler, J., & Parrinello, M. (2007). Generalized neural-network
    representation of high-dimensional potential-energy surfaces.
    Physical Review Letters, 98(14), 146401.
    DOI: 10.1103/PhysRevLett.98.146401
    (Original neural network potential)

[2] Schütt, K. T., et al. (2018). SchNet: A deep learning architecture
    for molecules and materials. Journal of Chemical Physics, 148(24), 241722.
    DOI: 10.1063/1.5019779
    (Continuous-filter convolutional networks)

[3] Unke, O. T., et al. (2021). Machine learning force fields.
    Chemical Reviews, 121(16), 10142-10186.
    DOI: 10.1021/acs.chemrev.0c01111
    (Comprehensive review of ML potentials)

[4] Batatia, I., et al. (2022). MACE: Higher Order Equivariant Message
    Passing Neural Networks for Fast and Accurate Force Fields.
    arXiv:2206.07697.
    DOI: 10.48550/arXiv.2206.07697

[5] Chen, C., & Ong, S. P. (2023). A universal graph deep learning
    interatomic potential for the periodic table.
    Nature Computational Science, 2(11), 718-728.
    DOI: 10.1038/s43588-022-00349-3
    (M3GNet)

[6] Deng, B., et al. (2023). CHGNet as a pretrained universal neural
    network potential for charge-informed atomistic modelling.
    Nature Machine Intelligence, 5(9), 1031-1041.
    DOI: 10.1038/s42256-023-00716-3
"""

from .neural_potentials import (
    NeuralPotential,
    OrbPotential,
    EgretPotential,
    MACEPotential,
    CHGNetPotential
)
from .graph_networks import GraphNetwork, MessagePassingLayer
from .calculator import MLCalculator

__all__ = [
    # Neural potentials
    'NeuralPotential',
    'OrbPotential',
    'EgretPotential',
    'MACEPotential',
    'CHGNetPotential',
    # Graph networks
    'GraphNetwork',
    'MessagePassingLayer',
    # Calculator
    'MLCalculator',
]
