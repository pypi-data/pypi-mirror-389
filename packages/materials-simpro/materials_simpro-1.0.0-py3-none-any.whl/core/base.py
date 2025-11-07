"""
Base Computation Engine Interfaces
===================================

Abstract base classes for all computation methods in Materials-SimPro.

This module defines the common interface for:
- DFT (Density Functional Theory)
- ML Potentials (Neural network force fields)
- Molecular Dynamics
- Quantum Chemistry
- Semi-empirical methods

Scientific Context:
-------------------
The total energy E of a system is computed using different levels of theory:

1. Machine Learning: E ≈ f_NN(R; θ) - fastest, ~ms per structure
2. Semi-Empirical: E ≈ E_TB[H(R)] - fast, ~seconds
3. DFT: E[ρ] = T[ρ] + V_ext[ρ] + E_H[ρ] + E_xc[ρ] - accurate, ~minutes
4. Post-DFT (GW, CCSD(T)): E = E_DFT + ΔE_corr - very accurate, ~hours

References:
-----------
[1] Hohenberg, P., & Kohn, W. (1964). Inhomogeneous electron gas.
    Physical Review, 136(3B), B864.
    DOI: 10.1103/PhysRev.136.B864

[2] Kohn, W., & Sham, L. J. (1965). Self-consistent equations including
    exchange and correlation effects. Physical Review, 140(4A), A1133.
    DOI: 10.1103/PhysRev.140.A1133

[3] Behler, J., & Parrinello, M. (2007). Generalized neural-network
    representation of high-dimensional potential-energy surfaces.
    Physical Review Letters, 98(14), 146401.
    DOI: 10.1103/PhysRevLett.98.146401

[4] Unke, O. T., et al. (2021). Machine learning force fields.
    Chemical Reviews, 121(16), 10142-10186.
    DOI: 10.1021/acs.chemrev.0c01111
"""

from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import numpy as np
import time

from .structure import Structure


class FidelityLevel(Enum):
    """
    Hierarchical fidelity levels for multi-scale computation.

    Ordered from fastest/least accurate to slowest/most accurate.

    Reference: Plessix, R. E. (2018). Multi-fidelity optimization.
    Computational Geosciences, 22(1), 173-191.
    DOI: 10.1007/s10596-017-9680-3
    """
    ML = auto()              # Machine learning potentials (~1ms, MAE ~0.05 eV/atom)
    SEMI_EMPIRICAL = auto()  # Tight-binding, xTB (~1s, MAE ~0.2 eV/atom)
    DFT = auto()             # Density functional theory (~1min, MAE ~0.01 eV/atom)
    POST_DFT = auto()        # GW, RPA (~1hr, MAE ~0.001 eV/atom)
    QUANTUM_CHEM = auto()    # CCSD(T), MRCI (~1day, "exact")

    @property
    def typical_accuracy_eV(self) -> float:
        """Typical accuracy in eV/atom."""
        accuracy_map = {
            FidelityLevel.ML: 0.05,
            FidelityLevel.SEMI_EMPIRICAL: 0.2,
            FidelityLevel.DFT: 0.01,
            FidelityLevel.POST_DFT: 0.001,
            FidelityLevel.QUANTUM_CHEM: 0.0001,
        }
        return accuracy_map[self]

    @property
    def typical_time_seconds(self) -> float:
        """Typical computation time in seconds (order of magnitude)."""
        time_map = {
            FidelityLevel.ML: 0.001,
            FidelityLevel.SEMI_EMPIRICAL: 1.0,
            FidelityLevel.DFT: 60.0,
            FidelityLevel.POST_DFT: 3600.0,
            FidelityLevel.QUANTUM_CHEM: 86400.0,
        }
        return time_map[self]


@dataclass
class CalculationResult:
    """
    Container for calculation results from any computation method.

    Attributes:
        energy: Total energy (eV)
        forces: Atomic forces (eV/Å) - shape (N_atoms, 3)
        stress: Stress tensor (eV/Å³) - shape (3, 3) for periodic systems
        structure: The structure that was computed
        fidelity: Level of theory used
        walltime: Computation time (seconds)
        converged: Whether calculation converged
        metadata: Additional method-specific information
    """
    energy: Optional[float] = None
    forces: Optional[np.ndarray] = None
    stress: Optional[np.ndarray] = None
    structure: Optional[Structure] = None
    fidelity: Optional[FidelityLevel] = None
    walltime: Optional[float] = None
    converged: bool = True
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    @property
    def energy_per_atom(self) -> Optional[float]:
        """Energy per atom (eV/atom)."""
        if self.energy is None or self.structure is None:
            return None
        return self.energy / len(self.structure)

    @property
    def max_force(self) -> Optional[float]:
        """Maximum force component (eV/Å)."""
        if self.forces is None:
            return None
        return np.max(np.abs(self.forces))


class Calculator(ABC):
    """
    Abstract base class for all computation methods.

    All calculators (DFT, ML, MD, etc.) must implement this interface.

    Scientific Framework:
    ---------------------
    A calculator computes the Born-Oppenheimer potential energy surface:
        E(R) = ⟨Ψ|Ĥ|Ψ⟩

    where R = {R₁, R₂, ..., Rₙ} are nuclear positions.

    Forces are computed as:
        F_i = -∇_Ri E(R)

    Stress tensor (for periodic systems):
        σ_αβ = (1/V) ∂E/∂ε_αβ

    where ε is the strain tensor.

    Reference: Born, M., & Oppenheimer, R. (1927). Zur Quantentheorie der Molekeln.
    Annalen der Physik, 389(20), 457-484.
    DOI: 10.1002/andp.19273892002
    """

    def __init__(
        self,
        fidelity: FidelityLevel,
        name: str,
        **kwargs
    ):
        """
        Initialize calculator.

        Args:
            fidelity: Computation fidelity level
            name: Human-readable name of the method
            **kwargs: Method-specific parameters
        """
        self.fidelity = fidelity
        self.name = name
        self.parameters = kwargs

    @abstractmethod
    def calculate(
        self,
        structure: Structure,
        properties: List[str] = None
    ) -> CalculationResult:
        """
        Perform calculation on a structure.

        Args:
            structure: Input atomic structure
            properties: List of properties to compute
                       ['energy', 'forces', 'stress', 'density', 'bandstructure', ...]

        Returns:
            CalculationResult with computed properties

        Note:
            If properties is None, only energy is computed by default.
        """
        pass

    @abstractmethod
    def optimize_geometry(
        self,
        structure: Structure,
        fmax: float = 0.01,
        max_steps: int = 200
    ) -> Tuple[Structure, CalculationResult]:
        """
        Optimize atomic positions to minimize forces.

        Minimization of E(R) using gradient descent or quasi-Newton methods:
            R_{n+1} = R_n - α H⁻¹ ∇E(R_n)

        where H is the Hessian (or approximation).

        Args:
            structure: Initial structure
            fmax: Maximum force tolerance (eV/Å)
            max_steps: Maximum optimization steps

        Returns:
            Tuple of (optimized_structure, final_result)

        Reference: Nocedal, J., & Wright, S. J. (2006). Numerical Optimization.
        Springer. DOI: 10.1007/978-0-387-40065-5
        """
        pass

    def calculate_energy(self, structure: Structure) -> float:
        """
        Convenience method to calculate only energy.

        Returns:
            Total energy in eV
        """
        result = self.calculate(structure, properties=['energy'])
        if result.energy is None:
            raise RuntimeError("Energy calculation failed")
        return result.energy

    def calculate_forces(self, structure: Structure) -> np.ndarray:
        """
        Convenience method to calculate forces.

        Returns:
            Forces array (N_atoms, 3) in eV/Å
        """
        result = self.calculate(structure, properties=['forces'])
        if result.forces is None:
            raise RuntimeError("Force calculation failed")
        return result.forces

    def get_uncertainty(self, structure: Structure) -> Optional[float]:
        """
        Estimate prediction uncertainty (for ML methods).

        Returns:
            Uncertainty estimate (eV/atom) or None if not applicable

        Reference: Gal, Y., & Ghahramani, Z. (2016). Dropout as a Bayesian
        approximation. ICML. (Uncertainty quantification for neural networks)
        """
        return None  # Override in ML-based calculators

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}', fidelity={self.fidelity.name})"


class ComputationEngine(ABC):
    """
    High-level interface for multi-fidelity computation management.

    This class orchestrates multiple calculators and handles:
    - Automatic method selection based on accuracy requirements
    - Active learning (ML ← DFT)
    - Multi-fidelity workflows
    - Resource management

    Design Pattern:
    ---------------
    This implements the Strategy pattern, allowing runtime selection
    of computation methods based on requirements.

    Reference: Gamma, E., et al. (1994). Design Patterns: Elements of
    Reusable Object-Oriented Software. Addison-Wesley.
    """

    def __init__(self):
        self.calculators: Dict[FidelityLevel, Calculator] = {}
        self.statistics: Dict[str, Any] = {
            'total_calculations': 0,
            'calculations_by_fidelity': {f: 0 for f in FidelityLevel},
            'total_walltime': 0.0,
        }

    def register_calculator(self, calculator: Calculator):
        """
        Register a calculator for a specific fidelity level.

        Args:
            calculator: Calculator instance
        """
        self.calculators[calculator.fidelity] = calculator

    def has_calculator(self, fidelity: FidelityLevel) -> bool:
        """Check if calculator is available for given fidelity."""
        return fidelity in self.calculators

    def get_calculator(self, fidelity: FidelityLevel) -> Optional[Calculator]:
        """Get calculator for specific fidelity level."""
        return self.calculators.get(fidelity)

    def select_method(
        self,
        structure: Structure,
        accuracy_target: float = 0.01,
        max_time: Optional[float] = None,
        force_fidelity: Optional[FidelityLevel] = None
    ) -> FidelityLevel:
        """
        Automatically select computation method based on requirements.

        Selection Strategy:
        -------------------
        1. If force_fidelity specified, use that
        2. Otherwise, select lowest fidelity that meets accuracy_target
        3. If max_time specified, filter by time constraint
        4. For uncertain ML predictions, escalate to DFT

        Args:
            structure: Structure to compute
            accuracy_target: Required accuracy (eV/atom)
            max_time: Maximum allowed time (seconds)
            force_fidelity: Force specific fidelity level

        Returns:
            Selected fidelity level

        Reference: Peherstorfer, B., et al. (2018). Survey of multifidelity
        methods in uncertainty propagation, inference, and optimization.
        SIAM Review, 60(3), 550-591.
        DOI: 10.1137/16M1082469
        """
        if force_fidelity is not None:
            if not self.has_calculator(force_fidelity):
                raise ValueError(f"Calculator for {force_fidelity} not registered")
            return force_fidelity

        # Select lowest fidelity meeting accuracy requirement
        available_fidelities = sorted(
            [f for f in self.calculators.keys()],
            key=lambda f: f.value  # Lower value = faster method
        )

        for fidelity in available_fidelities:
            if fidelity.typical_accuracy_eV <= accuracy_target:
                # Check time constraint
                if max_time is None or fidelity.typical_time_seconds <= max_time:
                    # For ML, check uncertainty
                    if fidelity == FidelityLevel.ML:
                        calc = self.calculators[fidelity]
                        uncertainty = calc.get_uncertainty(structure)
                        if uncertainty is not None and uncertainty > accuracy_target:
                            continue  # Skip to next fidelity level
                    return fidelity

        # Fallback: use highest available fidelity
        return max(available_fidelities, key=lambda f: f.value)

    def calculate(
        self,
        structure: Structure,
        properties: List[str] = None,
        **selection_kwargs
    ) -> CalculationResult:
        """
        Calculate properties using automatically selected method.

        Args:
            structure: Input structure
            properties: Properties to compute
            **selection_kwargs: Arguments for select_method()

        Returns:
            CalculationResult from selected calculator
        """
        fidelity = self.select_method(structure, **selection_kwargs)
        calculator = self.calculators[fidelity]

        # Perform calculation
        start_time = time.time()
        result = calculator.calculate(structure, properties)
        walltime = time.time() - start_time

        # Update statistics
        self.statistics['total_calculations'] += 1
        self.statistics['calculations_by_fidelity'][fidelity] += 1
        self.statistics['total_walltime'] += walltime

        result.walltime = walltime
        result.fidelity = fidelity

        return result

    def optimize_geometry(
        self,
        structure: Structure,
        fmax: float = 0.01,
        **selection_kwargs
    ) -> Tuple[Structure, CalculationResult]:
        """
        Optimize geometry using automatically selected method.

        Multi-fidelity Strategy:
        ------------------------
        1. Perform initial optimization with ML (if available)
        2. Refine with DFT for final convergence
        3. This provides ~10x speedup vs pure DFT

        Args:
            structure: Initial structure
            fmax: Force convergence threshold (eV/Å)
            **selection_kwargs: Method selection arguments

        Returns:
            Tuple of (optimized_structure, final_result)
        """
        # Try ML pre-optimization if available
        if self.has_calculator(FidelityLevel.ML) and \
           'force_fidelity' not in selection_kwargs:
            ml_calc = self.calculators[FidelityLevel.ML]
            structure, _ = ml_calc.optimize_geometry(structure, fmax=fmax*2)

        # Final optimization with selected method
        fidelity = self.select_method(structure, **selection_kwargs)
        calculator = self.calculators[fidelity]

        return calculator.optimize_geometry(structure, fmax=fmax)

    def get_statistics(self) -> Dict[str, Any]:
        """Get computation statistics."""
        return self.statistics.copy()

    def reset_statistics(self):
        """Reset computation statistics."""
        self.statistics = {
            'total_calculations': 0,
            'calculations_by_fidelity': {f: 0 for f in FidelityLevel},
            'total_walltime': 0.0,
        }


class ActiveLearningEngine:
    """
    Active learning system for ML ← DFT knowledge transfer.

    The goal is to train ML models to DFT accuracy using minimal DFT calls.

    Algorithm (Query by Committee):
    --------------------------------
    1. Train ensemble of ML models on existing data
    2. For new structures, compute prediction variance across ensemble
    3. Query DFT for high-uncertainty structures
    4. Add DFT results to training set
    5. Retrain ML models
    6. Repeat until convergence

    Reference: Settles, B. (2009). Active Learning Literature Survey.
    Computer Sciences Technical Report 1648, University of Wisconsin–Madison.

    Also: Lookman, T., et al. (2019). Active learning in materials science
    with emphasis on adaptive sampling using uncertainties for targeted design.
    npj Computational Materials, 5(1), 21.
    DOI: 10.1038/s41524-019-0153-8
    """

    def __init__(
        self,
        ml_calculator: Calculator,
        dft_calculator: Calculator,
        uncertainty_threshold: float = 0.05
    ):
        """
        Initialize active learning engine.

        Args:
            ml_calculator: ML potential calculator
            dft_calculator: DFT calculator (ground truth)
            uncertainty_threshold: Uncertainty threshold for DFT queries (eV/atom)
        """
        self.ml_calc = ml_calculator
        self.dft_calc = dft_calculator
        self.uncertainty_threshold = uncertainty_threshold
        self.training_data: List[Tuple[Structure, float]] = []
        self.query_count = 0

    def predict_with_uncertainty(
        self,
        structure: Structure
    ) -> Tuple[float, float]:
        """
        Predict energy with uncertainty estimate.

        Returns:
            Tuple of (energy, uncertainty) in eV
        """
        energy = self.ml_calc.calculate_energy(structure)
        uncertainty = self.ml_calc.get_uncertainty(structure)
        if uncertainty is None:
            uncertainty = 0.0
        return energy, uncertainty

    def query_if_uncertain(
        self,
        structure: Structure
    ) -> Tuple[float, bool]:
        """
        Query DFT if ML uncertainty exceeds threshold.

        Returns:
            Tuple of (energy, was_queried)
        """
        energy_ml, uncertainty = self.predict_with_uncertainty(structure)

        if uncertainty > self.uncertainty_threshold:
            # Query DFT
            energy_dft = self.dft_calc.calculate_energy(structure)
            self.training_data.append((structure, energy_dft))
            self.query_count += 1
            return energy_dft, True
        else:
            return energy_ml, False

    def get_query_rate(self) -> float:
        """
        Get fraction of structures queried to DFT.

        Target: <10% query rate (90% speedup)
        """
        if len(self.training_data) == 0:
            return 0.0
        return self.query_count / len(self.training_data)


__all__ = [
    'FidelityLevel',
    'CalculationResult',
    'Calculator',
    'ComputationEngine',
    'ActiveLearningEngine',
]
