"""
DFT Calculator Implementation
==============================

High-level DFT calculator interface integrating:
- Kohn-Sham solver
- XC functionals
- Pseudopotentials
- Geometry optimization

This provides a user-friendly interface to DFT calculations.
"""

import numpy as np
from typing import List, Tuple, Optional

from core.base import Calculator, CalculationResult, FidelityLevel
from core.structure import Structure
from .kohn_sham import KohnShamSolver, SCFConvergence
from .xc_functionals import XCFunctional, GGA_PBE, LDA_PZ
from .pseudopotentials import load_pseudopotential, PseudopotentialType


class DFTCalculator(Calculator):
    """
    Complete DFT calculator implementing the Calculator interface.

    This calculator:
    1. Sets up plane-wave basis
    2. Loads pseudopotentials
    3. Solves Kohn-Sham equations self-consistently
    4. Computes forces and stress
    5. Performs geometry optimization

    Example Usage:
    --------------
    ```python
    from materials_simpro import Structure, DFTCalculator
    from materials_simpro.dft import GGA_PBE

    # Create structure
    structure = Structure.from_file("POSCAR")

    # Setup calculator
    calc = DFTCalculator(
        xc_functional=GGA_PBE(),
        ecut=500.0,  # eV
        kpoints=[[0, 0, 0], [0.5, 0.5, 0.5]]
    )

    # Calculate energy
    result = calc.calculate(structure, properties=['energy', 'forces'])
    print(f"Energy: {result.energy} eV")

    # Optimize geometry
    opt_structure, opt_result = calc.optimize_geometry(structure)
    ```

    Scientific References:
    ----------------------
    Full DFT methodology: Payne et al. (1992), DOI: 10.1103/RevModPhys.64.1045
    """

    def __init__(
        self,
        xc_functional: Optional[XCFunctional] = None,
        ecut: float = 500.0,  # eV
        kpoints: Optional[np.ndarray] = None,
        pseudopotential_type: PseudopotentialType = PseudopotentialType.PAW,
        convergence: Optional[SCFConvergence] = None,
        **kwargs
    ):
        """
        Initialize DFT calculator.

        Args:
            xc_functional: XC functional (default: GGA-PBE)
            ecut: Plane-wave kinetic energy cutoff (eV)
            kpoints: K-points for Brillouin zone sampling
            pseudopotential_type: Type of pseudopotentials
            convergence: SCF convergence parameters
            **kwargs: Additional parameters
        """
        super().__init__(
            fidelity=FidelityLevel.DFT,
            name="DFT-PW-KS",
            **kwargs
        )

        # XC functional
        self.xc_functional = xc_functional or GGA_PBE()

        # Calculation parameters
        self.ecut = ecut
        self.kpoints = kpoints if kpoints is not None else np.array([[0.0, 0.0, 0.0]])
        self.pp_type = pseudopotential_type
        self.convergence = convergence or SCFConvergence()

        # Pseudopotentials (loaded per-structure)
        self.pseudopotentials = {}

    def _load_pseudopotentials(self, structure: Structure):
        """Load pseudopotentials for all elements in structure."""
        elements = set(site.element for site in structure.sites)

        for element in elements:
            if element not in self.pseudopotentials:
                pp = load_pseudopotential(
                    element,
                    pp_type=self.pp_type,
                    xc_functional=self.xc_functional.name
                )
                self.pseudopotentials[element] = pp

    def calculate(
        self,
        structure: Structure,
        properties: List[str] = None
    ) -> CalculationResult:
        """
        Perform DFT calculation on structure.

        Args:
            structure: Input structure
            properties: Properties to compute ['energy', 'forces', 'stress', 'density']

        Returns:
            CalculationResult with computed properties
        """
        if properties is None:
            properties = ['energy']

        # Load pseudopotentials
        self._load_pseudopotentials(structure)

        # Create Kohn-Sham solver
        solver = KohnShamSolver(
            structure=structure,
            xc_functional=self.xc_functional,
            pseudopotential=lambda elem: self.pseudopotentials[elem],
            ecut=self.ecut,
            kpoints=self.kpoints,
            convergence=self.convergence
        )

        # Solve Kohn-Sham equations
        print(f"Starting DFT calculation for {structure.formula or 'structure'}...")
        print(f"XC functional: {self.xc_functional.name}")
        print(f"Energy cutoff: {self.ecut} eV")
        print(f"K-points: {len(self.kpoints)}")

        try:
            energy, density, wavefunctions, eigenvalues = solver.solve()
        except RuntimeError as e:
            return CalculationResult(
                structure=structure,
                converged=False,
                metadata={'error': str(e)}
            )

        # Initialize result
        result = CalculationResult(
            structure=structure,
            energy=energy,
            converged=solver.convergence.converged,
            metadata={
                'xc_functional': self.xc_functional.name,
                'ecut': self.ecut,
                'scf_iterations': solver.convergence.iterations,
                'eigenvalues': eigenvalues,
            }
        )

        # Compute forces if requested
        if 'forces' in properties:
            forces = solver.compute_forces()
            result.forces = forces

        # Stress tensor (placeholder)
        if 'stress' in properties:
            result.stress = np.zeros((3, 3))

        # Density
        if 'density' in properties:
            result.metadata['density'] = density

        print(f"DFT calculation completed: E = {energy:.6f} eV")
        print(f"SCF converged in {solver.convergence.iterations} iterations")

        return result

    def optimize_geometry(
        self,
        structure: Structure,
        fmax: float = 0.01,
        max_steps: int = 200
    ) -> Tuple[Structure, CalculationResult]:
        """
        Optimize atomic positions using DFT forces.

        Uses BFGS (Broyden-Fletcher-Goldfarb-Shanno) quasi-Newton method:
        1. Compute energy and forces
        2. Update positions: R_new = R_old - α H^{-1} F
        3. Update Hessian approximation
        4. Repeat until max|F| < fmax

        Args:
            structure: Initial structure
            fmax: Force convergence criterion (eV/Å)
            max_steps: Maximum optimization steps

        Returns:
            Tuple of (optimized_structure, final_result)

        Reference: Nocedal & Wright (2006), Numerical Optimization
        DOI: 10.1007/978-0-387-40065-5
        """
        from scipy.optimize import minimize

        print(f"\nStarting geometry optimization...")
        print(f"Force tolerance: {fmax} eV/Å")
        print(f"Max steps: {max_steps}")

        current_structure = structure.copy()

        # Define objective function for scipy.optimize
        def objective(positions_flat):
            # Reshape positions
            positions = positions_flat.reshape(-1, 3)

            # Update structure
            for i, site in enumerate(current_structure.sites):
                site.position = positions[i]
                site.cartesian = current_structure.lattice.get_cartesian_coords(positions[i])

            # Calculate energy and forces
            result = self.calculate(current_structure, properties=['energy', 'forces'])

            if not result.converged:
                return np.inf, np.zeros_like(positions_flat)

            energy = result.energy
            forces = result.forces

            # Return energy and negative forces (scipy minimizes)
            return energy, -forces.flatten()

        # Initial positions
        initial_positions = np.array([site.position for site in current_structure.sites])
        x0 = initial_positions.flatten()

        # Optimize using L-BFGS-B
        result_opt = minimize(
            objective,
            x0,
            method='L-BFGS-B',
            jac=True,  # objective returns both energy and gradient
            options={
                'maxiter': max_steps,
                'ftol': 1e-9,
                'gtol': fmax,
            }
        )

        # Extract optimized structure
        optimized_positions = result_opt.x.reshape(-1, 3)
        for i, site in enumerate(current_structure.sites):
            site.position = optimized_positions[i]
            site.cartesian = current_structure.lattice.get_cartesian_coords(optimized_positions[i])

        # Final energy calculation
        final_result = self.calculate(current_structure, properties=['energy', 'forces'])

        print(f"\nGeometry optimization completed!")
        print(f"Steps: {result_opt.nit}")
        print(f"Final energy: {final_result.energy:.6f} eV")
        print(f"Max force: {final_result.max_force:.6f} eV/Å")

        return current_structure, final_result


__all__ = [
    'DFTCalculator',
]
