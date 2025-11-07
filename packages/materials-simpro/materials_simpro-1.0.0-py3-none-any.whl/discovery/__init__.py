"""
AI-Powered Materials Discovery
===============================

Autonomous discovery system using:
- Active learning (ML ← DFT)
- Multi-agent LLM coordination
- Bayesian optimization
- Genetic algorithms
- Natural language workflows

Target: 10,000 materials/day (100x current SOTA)

References:
-----------
[1] Lookman, T., et al. (2019). Active learning in materials science.
    npj Computational Materials, 5(1), 21.
    DOI: 10.1038/s41524-019-0153-8

[2] Settles, B. (2009). Active Learning Literature Survey.
    Computer Sciences Technical Report 1648, University of Wisconsin–Madison.

[3] Shahriari, B., et al. (2016). Taking the human out of the loop: A review
    of Bayesian optimization. Proceedings of the IEEE, 104(1), 148-175.
    DOI: 10.1109/JPROC.2015.2494218
"""

from .active_learning import ActiveLearning, UncertaintySampler
from .agents import AgentOrchestrator, ResearchDirector
from .bayesian import BayesianOptimizer
from .genetic import GeneticOptimizer

__all__ = [
    'ActiveLearning',
    'UncertaintySampler',
    'AgentOrchestrator',
    'ResearchDirector',
    'BayesianOptimizer',
    'GeneticOptimizer',
]
