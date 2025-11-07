"""
Graph Neural Networks for Materials
====================================

Implementation of graph-based architectures for atomic systems.

Graph Representation:
---------------------
    Atoms → Nodes (with features: Z, position)
    Bonds → Edges (with features: distance, direction)

Message Passing Framework:
--------------------------
    1. Initialize: h_i^{(0)} = embed(Z_i)
    2. Message: m_ij^{(l)} = φ_msg(h_i^{(l)}, h_j^{(l)}, e_ij)
    3. Aggregate: a_i^{(l)} = Σ_j m_ij^{(l)}
    4. Update: h_i^{(l+1)} = φ_update(h_i^{(l)}, a_i^{(l)})
    5. Readout: E = Σ_i φ_out(h_i^{(L)})

Scientific References:
----------------------
[1] Gilmer, J., et al. (2017). Neural message passing for quantum chemistry.
    ICML. (Unified message passing framework)

[2] Schütt, K. T., et al. (2017). SchNet: A continuous-filter convolutional
    neural network for modeling quantum interactions.
    NeurIPS. DOI: 10.48550/arXiv.1706.08566

[3] Battaglia, P. W., et al. (2018). Relational inductive biases, deep learning,
    and graph networks. arXiv:1806.01261.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, Optional
import math


class RBFExpansion(nn.Module):
    """
    Radial Basis Function expansion for distances.

    Converts scalar distances to vector representations:
        φ_k(r) = exp(-(r - μ_k)² / (2σ²))

    Reference: Schütt et al. (2017), SchNet paper
    DOI: 10.48550/arXiv.1706.08566
    """

    def __init__(
        self,
        num_rbf: int = 50,
        cutoff: float = 5.0,
        learnable: bool = False
    ):
        super().__init__()
        self.num_rbf = num_rbf
        self.cutoff = cutoff

        # RBF centers uniformly distributed in [0, cutoff]
        means = torch.linspace(0, cutoff, num_rbf)
        sigma = cutoff / num_rbf

        if learnable:
            self.register_parameter('means', nn.Parameter(means))
            self.register_parameter('sigma', nn.Parameter(torch.tensor(sigma)))
        else:
            self.register_buffer('means', means)
            self.register_buffer('sigma', torch.tensor(sigma))

    def forward(self, distances: torch.Tensor) -> torch.Tensor:
        """
        Expand distances into RBF features.

        Args:
            distances: (N_edges,) distances

        Returns:
            (N_edges, num_rbf) RBF features
        """
        # distances: (N_edges,) → (N_edges, 1)
        # means: (num_rbf,) → (1, num_rbf)
        d = distances.unsqueeze(-1)
        mu = self.means.unsqueeze(0)

        # Gaussian RBF
        rbf = torch.exp(-(d - mu)**2 / (2 * self.sigma**2))

        return rbf


class MessagePassingLayer(nn.Module):
    """
    Graph message passing layer.

    Implements:
        m_ij = φ_msg(h_i, h_j, e_ij)
        h_i' = φ_update(h_i, Σ_j m_ij)

    Reference: Gilmer et al. (2017), Message Passing Neural Networks
    """

    def __init__(
        self,
        node_dim: int = 128,
        edge_dim: int = 50,
        hidden_dim: int = 256
    ):
        super().__init__()

        # Message network
        self.message_net = nn.Sequential(
            nn.Linear(2 * node_dim + edge_dim, hidden_dim),
            nn.SiLU(),
            nn.Linear(hidden_dim, node_dim)
        )

        # Update network
        self.update_net = nn.Sequential(
            nn.Linear(2 * node_dim, hidden_dim),
            nn.SiLU(),
            nn.Linear(hidden_dim, node_dim)
        )

    def forward(
        self,
        node_features: torch.Tensor,  # (N_atoms, node_dim)
        edge_index: torch.Tensor,     # (2, N_edges)
        edge_features: torch.Tensor   # (N_edges, edge_dim)
    ) -> torch.Tensor:
        """
        Message passing forward.

        Returns:
            Updated node features (N_atoms, node_dim)
        """
        src, dst = edge_index  # source and destination nodes

        # Gather node features
        h_src = node_features[src]  # (N_edges, node_dim)
        h_dst = node_features[dst]

        # Compute messages
        message_input = torch.cat([h_src, h_dst, edge_features], dim=-1)
        messages = self.message_net(message_input)  # (N_edges, node_dim)

        # Aggregate messages (sum over incoming edges)
        aggregated = torch.zeros_like(node_features)
        aggregated.index_add_(0, dst, messages)

        # Update nodes
        update_input = torch.cat([node_features, aggregated], dim=-1)
        node_features_new = self.update_net(update_input)

        # Residual connection
        return node_features + node_features_new


class GraphNetwork(nn.Module):
    """
    Complete graph neural network for energy prediction.

    Architecture:
    -------------
    1. Embed atomic numbers → node features
    2. Expand distances → edge features (RBF)
    3. L layers of message passing
    4. Global pooling (sum) → total energy

    Reference: SchNet architecture (Schütt et al., 2017)
    """

    def __init__(
        self,
        max_z: int = 94,
        node_dim: int = 128,
        num_rbf: int = 50,
        num_layers: int = 4,
        cutoff: float = 5.0
    ):
        super().__init__()

        # Atomic number embedding
        self.embedding = nn.Embedding(max_z + 1, node_dim)

        # RBF expansion for distances
        self.rbf = RBFExpansion(num_rbf, cutoff)

        # Message passing layers
        self.mp_layers = nn.ModuleList([
            MessagePassingLayer(node_dim, num_rbf)
            for _ in range(num_layers)
        ])

        # Output network (energy per atom)
        self.output_net = nn.Sequential(
            nn.Linear(node_dim, node_dim // 2),
            nn.SiLU(),
            nn.Linear(node_dim // 2, 1)
        )

    def forward(self, graph: Dict[str, torch.Tensor]) -> torch.Tensor:
        """
        Forward pass: graph → total energy.

        Args:
            graph: Dictionary with 'node_features', 'edge_index', 'edge_attr'

        Returns:
            Total energy (scalar)
        """
        atomic_numbers = graph['node_features']  # (N_atoms,)
        edge_index = graph['edge_index']         # (2, N_edges)
        edge_vectors = graph['edge_attr']        # (N_edges, 3)

        # Embed atomic numbers
        h = self.embedding(atomic_numbers)  # (N_atoms, node_dim)

        # Compute edge features (distances → RBF)
        distances = torch.norm(edge_vectors, dim=-1)  # (N_edges,)
        edge_features = self.rbf(distances)           # (N_edges, num_rbf)

        # Message passing
        for mp_layer in self.mp_layers:
            h = mp_layer(h, edge_index, edge_features)

        # Predict atomic energies
        atomic_energies = self.output_net(h)  # (N_atoms, 1)

        # Total energy (sum over atoms)
        total_energy = atomic_energies.sum()

        return total_energy


__all__ = [
    'RBFExpansion',
    'MessagePassingLayer',
    'GraphNetwork',
]
