"""
Active Learning Pipeline
========================

Query DFT selectively based on ML uncertainty.

Algorithm (Query by Committee):
-------------------------------
1. Train ensemble of ML models
2. Predict with uncertainty estimates
3. Query DFT for high-uncertainty structures
4. Retrain models
5. Repeat

Target: <10% DFT queries (90% cost reduction)

References:
-----------
[1] Settles (2009). Active Learning Literature Survey.
[2] Lookman et al. (2019). DOI: 10.1038/s41524-019-0153-8
"""

import numpy as np
from typing import List, Tuple
from dataclasses import dataclass

from core.structure import Structure
from core.base import Calculator


@dataclass
class TrainingPoint:
    """Training data point."""
    structure: Structure
    energy: float
    source: str  # 'ML' or 'DFT'


class UncertaintySampler:
    """
    Acquisition function based on prediction uncertainty.

    σ(x) = std(E₁(x), E₂(x), ..., Eₘ(x))  for ensemble

    Reference: Gal & Ghahramani (2016). Dropout as Bayesian approximation.
    """

    def __init__(self, threshold: float = 0.1):
        self.threshold = threshold  # eV/atom

    def should_query(self, uncertainty: float) -> bool:
        """Decide if structure needs DFT validation."""
        return uncertainty > self.threshold


class ActiveLearning:
    """
    Complete active learning loop.

    Workflow:
    ---------
    while not converged:
        candidates = generate_candidates()
        predictions, uncertainties = ml_model.predict_batch(candidates)
        high_uncertainty = filter(lambda x: x.unc > threshold, zip(candidates, uncertainties))
        dft_results = dft_calc.calculate_batch(high_uncertainty)
        ml_model.retrain(training_data + dft_results)
    """

    def __init__(
        self,
        ml_calculator: Calculator,
        dft_calculator: Calculator,
        uncertainty_threshold: float = 0.1,
        max_dft_queries: int = 1000
    ):
        self.ml_calc = ml_calculator
        self.dft_calc = dft_calculator
        self.sampler = UncertaintySampler(uncertainty_threshold)
        self.max_dft_queries = max_dft_queries

        self.training_data: List[TrainingPoint] = []
        self.query_count = 0

    def run_campaign(
        self,
        candidate_structures: List[Structure],
        target_accuracy: float = 0.01
    ) -> List[TrainingPoint]:
        """
        Run active learning campaign.

        Args:
            candidate_structures: Pool of structures to screen
            target_accuracy: Target accuracy (eV/atom)

        Returns:
            Training dataset with DFT-validated points
        """
        for structure in candidate_structures:
            if self.query_count >= self.max_dft_queries:
                break

            # ML prediction with uncertainty
            ml_result = self.ml_calc.calculate(structure)
            uncertainty = self.ml_calc.get_uncertainty(structure)

            if uncertainty and self.sampler.should_query(uncertainty):
                # Query DFT
                dft_result = self.dft_calc.calculate(structure)
                self.training_data.append(TrainingPoint(
                    structure=structure,
                    energy=dft_result.energy,
                    source='DFT'
                ))
                self.query_count += 1

                # Retrain ML model (simplified - actual retraining would happen here)
                # self.ml_calc.model.retrain(self.training_data)
            else:
                # Use ML prediction
                self.training_data.append(TrainingPoint(
                    structure=structure,
                    energy=ml_result.energy,
                    source='ML'
                ))

        return self.training_data

    def get_query_rate(self) -> float:
        """Fraction of structures queried to DFT."""
        total = len(self.training_data)
        if total == 0:
            return 0.0
        return self.query_count / total


__all__ = ['ActiveLearning', 'UncertaintySampler', 'TrainingPoint']
