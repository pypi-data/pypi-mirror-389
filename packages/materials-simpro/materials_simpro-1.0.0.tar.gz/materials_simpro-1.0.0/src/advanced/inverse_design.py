"""
Inverse Materials Design
========================

Target property ’ Novel material structure.

Workflow:
1. User specifies target properties
2. Generative model proposes candidates
3. Screening with ML potentials
4. DFT validation of top candidates

Reference: Sanchez-Lengeling & Aspuru-Guzik (2018). DOI: 10.1126/science.aat2663
"""

from typing import List, Dict, Callable
from core.structure import Structure
from .generative_models import MaterialVAE, DiffusionModel


class InverseDesigner:
    """
    Inverse design framework: Properties ’ Structures.

    Example:
    --------
    ```python
    designer = InverseDesigner(
        target_properties={'band_gap': 2.0, 'formation_energy': -2.0},
        model=MaterialVAE(latent_dim=256)
    )

    candidates = designer.run(n_candidates=1000, n_select=10)
    ```
    """

    def __init__(
        self,
        target_properties: Dict[str, float],
        model,
        property_predictor: Callable = None
    ):
        self.target_properties = target_properties
        self.model = model  # VAE, GAN, or Diffusion
        self.property_predictor = property_predictor

    def run(self, n_candidates: int = 1000, n_select: int = 10) -> List[Structure]:
        """
        Run inverse design workflow.

        1. Generate candidates
        2. Predict properties
        3. Rank by similarity to target
        4. Return top candidates
        """
        # Generate candidate structures
        candidates = self.model.generate(n_samples=n_candidates)

        # Predict properties
        predicted_props = []
        for struct in candidates:
            props = self.property_predictor(struct)
            predicted_props.append(props)

        # Compute fitness (distance to target)
        fitness = self._compute_fitness(predicted_props)

        # Select top candidates
        top_indices = sorted(range(len(fitness)), key=lambda i: fitness[i])[:n_select]
        top_candidates = [candidates[i] for i in top_indices]

        return top_candidates

    def _compute_fitness(self, predicted_props: List[Dict]) -> List[float]:
        """
        Fitness = negative distance to target properties.

        Lower is better (closer to target).
        """
        fitness = []
        for props in predicted_props:
            distance = sum(
                (props.get(key, 0) - target_val)**2
                for key, target_val in self.target_properties.items()
            )
            fitness.append(distance)

        return fitness


__all__ = ['InverseDesigner']
