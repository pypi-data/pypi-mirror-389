"""
Genetic Algorithms for Materials Discovery
===========================================

Evolutionary optimization inspired by natural selection.

Algorithm:
----------
1. Initialize population
2. Evaluate fitness
3. Select parents (tournament, roulette)
4. Crossover (recombination)
5. Mutation
6. Replace population
7. Repeat

For materials:
- Genotype: Crystal structure (lattice + atomic positions)
- Fitness: Formation energy, band gap, etc.
- Crossover: Mix lattice vectors, swap atom types
- Mutation: Perturb positions, substitute elements

References:
-----------
[1] Goldberg, D. E. (1989). Genetic Algorithms in Search, Optimization and Machine Learning.
    Addison-Wesley. ISBN: 978-0201157675

[2] Oganov, A. R., & Glass, C. W. (2006). Crystal structure prediction using ab initio
    evolutionary techniques: Principles and applications. Journal of Chemical Physics, 124(24), 244704.
    DOI: 10.1063/1.2210932
    (USPEX code - evolutionary crystal structure prediction)
"""

import numpy as np
from typing import List, Callable, Tuple
from dataclasses import dataclass

from core.structure import Structure


@dataclass
class Individual:
    """Individual in population."""
    genome: Structure  # Crystal structure
    fitness: float = None  # Formation energy (or other property)


class GeneticOptimizer:
    """
    Genetic algorithm for materials optimization.

    Example:
    --------
    ```python
    def fitness_func(structure):
        return -formation_energy(structure)  # Negative for minimization

    ga = GeneticOptimizer(
        fitness_func=fitness_func,
        population_size=100,
        generations=50
    )

    best = ga.evolve()
    ```
    """

    def __init__(
        self,
        fitness_func: Callable,
        population_size: int = 100,
        mutation_rate: float = 0.1,
        crossover_rate: float = 0.8,
        elite_fraction: float = 0.1
    ):
        """
        Initialize genetic algorithm.

        Args:
            fitness_func: Fitness function (higher is better)
            population_size: Population size
            mutation_rate: Probability of mutation
            crossover_rate: Probability of crossover
            elite_fraction: Fraction of elite individuals to preserve
        """
        self.fitness_func = fitness_func
        self.population_size = population_size
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.n_elite = int(elite_fraction * population_size)

        self.population: List[Individual] = []

    def initialize_population(self, initial_structures: List[Structure]):
        """Initialize population from seed structures."""
        self.population = [Individual(genome=s) for s in initial_structures[:self.population_size]]

        # Fill remaining with mutations
        while len(self.population) < self.population_size:
            parent = np.random.choice(self.population)
            child = self.mutate(parent.genome)
            self.population.append(Individual(genome=child))

    def evaluate_population(self):
        """Evaluate fitness for all individuals."""
        for individual in self.population:
            if individual.fitness is None:
                individual.fitness = self.fitness_func(individual.genome)

    def select_parents(self) -> Tuple[Individual, Individual]:
        """
        Tournament selection.

        Select k individuals, return the fittest.
        """
        k = 3  # Tournament size
        tournament = np.random.choice(self.population, k, replace=False)
        tournament_sorted = sorted(tournament, key=lambda x: x.fitness, reverse=True)
        return tournament_sorted[0], tournament_sorted[1]

    def crossover(self, parent1: Structure, parent2: Structure) -> Structure:
        """
        Crossover operation on crystal structures.

        Strategy:
        - Mix lattice vectors
        - Swap some atom types
        """
        child = parent1.copy()

        # Mix lattice: child = α*parent1 + (1-α)*parent2
        alpha = np.random.rand()
        child.lattice.matrix = alpha * parent1.lattice.matrix + (1 - alpha) * parent2.lattice.matrix

        # Swap some atoms
        for i in range(min(len(parent1), len(parent2))):
            if np.random.rand() < 0.5:
                child.sites[i].element = parent2.sites[i].element

        return child

    def mutate(self, structure: Structure) -> Structure:
        """
        Mutation operation.

        Strategies:
        - Perturb atomic positions
        - Substitute elements
        - Perturb lattice parameters
        """
        mutated = structure.copy()

        # Perturb positions (±0.1 Å)
        for site in mutated.sites:
            if np.random.rand() < self.mutation_rate:
                site.cartesian += np.random.normal(0, 0.1, 3)

        # Element substitution
        elements = ['Li', 'Na', 'K', 'Mg', 'Ca', 'Fe', 'Co', 'Ni', 'Cu', 'O', 'S', 'F']
        for site in mutated.sites:
            if np.random.rand() < self.mutation_rate * 0.5:
                site.element = np.random.choice(elements)

        return mutated

    def evolve(self, generations: int = 50) -> Individual:
        """
        Run genetic algorithm.

        Args:
            generations: Number of generations

        Returns:
            Best individual found
        """
        # Initial evaluation
        self.evaluate_population()

        for gen in range(generations):
            # Sort by fitness
            self.population.sort(key=lambda x: x.fitness, reverse=True)

            # Track best
            best = self.population[0]
            print(f"Generation {gen+1}/{generations}: Best fitness = {best.fitness:.4f}")

            # Create next generation
            next_generation = []

            # Elitism: preserve best individuals
            next_generation.extend(self.population[:self.n_elite])

            # Generate offspring
            while len(next_generation) < self.population_size:
                parent1, parent2 = self.select_parents()

                # Crossover
                if np.random.rand() < self.crossover_rate:
                    child_genome = self.crossover(parent1.genome, parent2.genome)
                else:
                    child_genome = parent1.genome.copy()

                # Mutation
                child_genome = self.mutate(child_genome)

                next_generation.append(Individual(genome=child_genome))

            self.population = next_generation
            self.evaluate_population()

        # Return best
        self.population.sort(key=lambda x: x.fitness, reverse=True)
        return self.population[0]


__all__ = ['Individual', 'GeneticOptimizer']
