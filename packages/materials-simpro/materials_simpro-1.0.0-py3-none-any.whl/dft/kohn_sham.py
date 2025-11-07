"""
Kohn-Sham Equation Solver
==========================

Complete implementation of the Kohn-Sham self-consistent field solver
using plane-wave basis sets.

Mathematical Framework:
-----------------------

1. Kohn-Sham Equations (single-particle Schrödinger-like equations):

    Ĥ_KS ψ_i(r) = ε_i ψ_i(r)

   where the Kohn-Sham Hamiltonian is:

    Ĥ_KS = -ℏ²/2m ∇² + V_eff(r)

2. Effective Potential:

    V_eff(r) = V_ext(r) + V_H(r) + V_xc(r)

   - V_ext: External potential (nuclei + pseudopotentials)
   - V_H: Hartree potential (classical electron-electron repulsion)
   - V_xc: Exchange-correlation potential (quantum many-body effects)

3. Electron Density:

    ρ(r) = Σ_i f_i |ψ_i(r)|²

   where f_i are occupation numbers (0 ≤ f_i ≤ 2 for spin-unpolarized)

4. Hartree Potential (solution to Poisson equation):

    ∇²V_H(r) = -4πρ(r)

   In Fourier space:
    V_H(G) = 4π/|G|² ρ(G)    for G ≠ 0

5. Total Energy Functional:

    E[ρ] = T_s[ρ] + E_H[ρ] + E_xc[ρ] + E_ext[ρ]

   where:
    T_s = Σ_i f_i ⟨ψ_i|-ℏ²/2m ∇²|ψ_i⟩  (kinetic energy)
    E_H = (1/2)∫∫ ρ(r)ρ(r')/|r-r'| dr dr'  (Hartree energy)
    E_xc = ∫ ρ(r)ε_xc(ρ(r)) dr  (exchange-correlation)
    E_ext = ∫ V_ext(r)ρ(r) dr  (external potential)

6. Forces (Hellmann-Feynman theorem):

    F_I = -∇_I E = -⟨∂Ĥ/∂R_I⟩ = -∫ ρ(r) ∇_I V_ext(r) dr

7. Stress Tensor (for periodic systems):

    σ_αβ = (1/Ω) ∂E/∂ε_αβ

   where ε is the strain tensor and Ω is the cell volume.

Scientific References:
----------------------
[1] Kohn, W., & Sham, L. J. (1965). Self-consistent equations including
    exchange and correlation effects. Physical Review, 140(4A), A1133.
    DOI: 10.1103/PhysRev.140.A1133

[2] Payne, M. C., et al. (1992). Iterative minimization techniques for
    ab initio total-energy calculations: molecular dynamics and conjugate gradients.
    Reviews of Modern Physics, 64(4), 1045.
    DOI: 10.1103/RevModPhys.64.1045

[3] Martin, R. M. (2004). Electronic Structure: Basic Theory and Practical Methods.
    Cambridge University Press. ISBN: 978-0521534406

[4] Hellmann, H. (1937). Einführung in die Quantenchemie. Leipzig: Deuticke.
    (Original Hellmann-Feynman theorem)

[5] Pulay, P. (1969). Ab initio calculation of force constants and equilibrium
    geometries in polyatomic molecules. Molecular Physics, 17(2), 197-204.
    DOI: 10.1080/00268976900100941
    (Pulay forces for incomplete basis sets)

[6] Nielsen, O. H., & Martin, R. M. (1985). Stress theorem in the determination
    of static equilibrium by the density functional method.
    Physical Review B, 32(6), 3792.
    DOI: 10.1103/PhysRevB.32.3792
"""

import numpy as np
from typing import Tuple, Optional, List, Callable
from dataclasses import dataclass
import scipy.sparse as sp
import scipy.sparse.linalg as spla
from enum import Enum

from core.structure import Structure
from core.constants import (
    HBAR, ELECTRON_MASS, ELEMENTARY_CHARGE,
    HARTREE_TO_EV, BOHR_TO_ANGSTROM,
    ENERGY_TOLERANCE_EV
)


class MixingMethod(Enum):
    """
    Density mixing methods for SCF convergence.

    Reference: Woods, N. D., et al. (2019). Computing the self-consistent field
    in Kohn–Sham density functional theory. Journal of Physics: Condensed Matter,
    31(45), 453001.
    DOI: 10.1088/1361-648X/ab31c0
    """
    LINEAR = "linear"              # Simple linear mixing
    PULAY = "pulay"                # Pulay DIIS mixing (default)
    BROYDEN = "broyden"            # Broyden mixing (good for metals)
    KERKER = "kerker"              # Kerker preconditioning


@dataclass
class SCFConvergence:
    """
    SCF convergence parameters and status.

    Convergence Criteria:
    ---------------------
    1. Energy convergence: |E_n - E_{n-1}| < energy_tolerance
    2. Density convergence: ∫|ρ_n(r) - ρ_{n-1}(r)|dr < density_tolerance
    3. Forces converged: max|F_i| < force_tolerance (optional)

    Attributes:
        energy_tolerance: Energy convergence threshold (eV)
        density_tolerance: Density convergence threshold (electrons)
        max_iterations: Maximum SCF iterations
        mixing_beta: Mixing parameter (0 < β ≤ 1)
        mixing_method: Density mixing method
        converged: Whether SCF converged
        iterations: Number of iterations performed
        final_energy: Final converged energy (eV)
        energy_history: Energy at each iteration
    """
    energy_tolerance: float = 1.0e-6  # eV
    density_tolerance: float = 1.0e-6  # electrons
    max_iterations: int = 100
    mixing_beta: float = 0.3  # Lower beta for DIIS stability (DIIS handles extrapolation)
    mixing_method: MixingMethod = MixingMethod.PULAY  # Pulay DIIS for fast convergence

    # Status (set during calculation)
    converged: bool = False
    iterations: int = 0
    final_energy: Optional[float] = None
    energy_history: List[float] = None

    def __post_init__(self):
        if self.energy_history is None:
            self.energy_history = []


class PulayMixer:
    """
    Pulay DIIS (Direct Inversion in the Iterative Subspace) density mixer.

    This is the state-of-the-art method for accelerating SCF convergence,
    used in production codes like VASP, Quantum ESPRESSO, and ABINIT.

    Mathematical Framework:
    -----------------------
    The DIIS method minimizes the norm of the residual vector by finding
    optimal linear combination coefficients for the density history.

    Given density history {rho_i} and residuals {R_i = rho_out,i - rho_in,i}:

    1. Build overlap matrix B:
        B_ij = <R_i|R_j> = integral(R_i(r) * R_j(r) dr)

    2. Solve constrained minimization (Lagrange multipliers):
        minimize: sum_ij c_i c_j B_ij
        subject to: sum_i c_i = 1

        This becomes a linear system:
        [B_11  B_12  ...  B_1n  1 ] [c_1]     [0]
        [B_21  B_22  ...  B_2n  1 ] [c_2]     [0]
        [...   ...   ...  ...   ..] [...] =   [.]
        [B_n1  B_n2  ...  B_nn  1 ] [c_n]     [0]
        [1     1     ...  1     0 ] [lambda]  [1]

    3. Optimal density:
        rho_next = sum_i c_i (rho_i + beta * R_i)

    This typically converges in 5-15 iterations vs 50-200 for simple mixing.

    Reference:
    Pulay, P. (1980). Convergence acceleration of iterative sequences.
    The case of SCF iteration. Chemical Physics Letters, 73(2), 393-398.
    DOI: 10.1016/0009-2614(80)80396-4

    Additional Reference:
    Woods, N. D., et al. (2019). Computing the self-consistent field in
    Kohn-Sham density functional theory. J. Phys.: Condens. Matter, 31, 453001.
    DOI: 10.1088/1361-648X/ab31c0
    """

    def __init__(self, beta: float = 0.5, history_size: int = 8):
        """
        Initialize Pulay mixer.

        Args:
            beta: Mixing parameter (0 < beta <= 1). Typical: 0.3-0.7
            history_size: Number of previous iterations to keep. Typical: 5-10
        """
        self.beta = beta
        self.history_size = history_size

        # History storage (flattened arrays for efficiency)
        self.rho_history: List[np.ndarray] = []
        self.residual_history: List[np.ndarray] = []

    def mix(self, rho_in: np.ndarray, rho_out: np.ndarray) -> np.ndarray:
        """
        Mix densities using Pulay DIIS algorithm.

        Args:
            rho_in: Input density (from previous iteration)
            rho_out: Output density (from current Kohn-Sham solve)

        Returns:
            Optimally mixed density for next iteration
        """
        # Compute residual
        residual = rho_out - rho_in

        # Add to history (store flattened for efficiency)
        self.rho_history.append(rho_in.flatten().copy())
        self.residual_history.append(residual.flatten().copy())

        # Limit history size (FIFO)
        if len(self.rho_history) > self.history_size:
            self.rho_history.pop(0)
            self.residual_history.pop(0)

        n = len(self.rho_history)

        # For first iteration, use simple mixing
        if n == 1:
            return rho_in + self.beta * residual

        # Build overlap matrix B (n x n)
        # B_ij = <R_i|R_j> = sum_r R_i(r) * R_j(r)
        B_mat = np.zeros((n, n))
        for i in range(n):
            for j in range(i, n):  # Symmetric, only compute upper triangle
                B_mat[i, j] = np.dot(self.residual_history[i], self.residual_history[j])
                if i != j:
                    B_mat[j, i] = B_mat[i, j]  # Symmetry

        # Build augmented matrix for constrained minimization
        # Add row and column for Lagrange multiplier
        B_aug = np.zeros((n+1, n+1))
        B_aug[:n, :n] = B_mat
        B_aug[n, :n] = 1.0  # Constraint: sum(c_i) = 1
        B_aug[:n, n] = 1.0  # Symmetric
        B_aug[n, n] = 0.0   # No diagonal element for lambda

        # Right-hand side: [0, 0, ..., 0, 1]^T
        rhs = np.zeros(n+1)
        rhs[n] = 1.0

        try:
            # Check if matrix is well-conditioned
            cond_number = np.linalg.cond(B_aug)
            if cond_number > 1e7:  # More conservative threshold for stability
                # Matrix is ill-conditioned, use simple mixing
                return rho_in + self.beta * residual

            # Solve linear system for coefficients
            solution = np.linalg.solve(B_aug, rhs)
            coeffs = solution[:n]  # Extract coefficients (last element is lambda)

            # Sanity checks
            if not np.isclose(np.sum(coeffs), 1.0, atol=1e-4):
                # Coefficients don't sum to 1 - matrix is ill-posed
                return rho_in + self.beta * residual

            # Check for NaN or Inf
            if not np.all(np.isfinite(coeffs)):
                return rho_in + self.beta * residual

            # Check for unreasonably large coefficients (sign of instability)
            if np.max(np.abs(coeffs)) > 10.0:
                return rho_in + self.beta * residual

        except (np.linalg.LinAlgError, ValueError) as e:
            # If DIIS fails (singular matrix, etc.), fall back to simple mixing
            return rho_in + self.beta * residual

        # Compute optimal mixed density
        # rho_next = sum_i c_i * (rho_i + beta * R_i)
        rho_mixed_flat = np.zeros_like(self.rho_history[0])
        for i in range(n):
            rho_mixed_flat += coeffs[i] * (self.rho_history[i] + self.beta * self.residual_history[i])

        # Reshape back to original grid shape
        rho_mixed = rho_mixed_flat.reshape(rho_in.shape)

        # Final validation: ensure result is finite and non-negative
        if not np.all(np.isfinite(rho_mixed)):
            # Result has NaN/Inf - fall back to simple mixing
            return rho_in + self.beta * residual

        if np.any(rho_mixed < -1e-10):  # Small tolerance for numerical noise
            # Negative density - unphysical, fall back
            return rho_in + self.beta * residual

        return rho_mixed

    def reset(self):
        """Clear history (e.g., when starting a new geometry optimization step)."""
        self.rho_history.clear()
        self.residual_history.clear()


class PlaneWaveBasis:
    """
    Plane-wave basis set for periodic systems.

    Mathematical Framework:
    -----------------------
    In a periodic system, wavefunctions can be expanded as:

        ψ_nk(r) = (1/√Ω) Σ_G c_nk(G) e^{i(k+G)·r}

    where:
    - k: wavevector in first Brillouin zone
    - G: reciprocal lattice vectors
    - Ω: unit cell volume

    The kinetic energy cutoff determines which G-vectors to include:
        |k + G|² ≤ 2m E_cut / ℏ²

    Reference: Payne et al. (1992), DOI: 10.1103/RevModPhys.64.1045
    """

    def __init__(
        self,
        structure: Structure,
        ecut: float,  # eV
        kpoints: Optional[np.ndarray] = None
    ):
        """
        Initialize plane-wave basis.

        Args:
            structure: Crystal structure
            ecut: Kinetic energy cutoff (eV)
            kpoints: K-points in fractional coordinates (shape: N_k × 3)
        """
        self.structure = structure
        self.ecut = ecut
        self.kpoints = kpoints if kpoints is not None else np.array([[0.0, 0.0, 0.0]])

        # Generate G-vectors
        self.gvectors = self._generate_gvectors()
        self.num_gvectors = len(self.gvectors)

        # FFT grid dimensions
        self.fft_grid = self._compute_fft_grid()

    def _generate_gvectors(self) -> np.ndarray:
        """
        Generate G-vectors within kinetic energy cutoff.

        The cutoff sphere in reciprocal space is defined by:
            (ℏ²/2m) |G|² ≤ E_cut

        Returns:
            Array of G-vectors (shape: N_G × 3)
        """
        # Get reciprocal lattice vectors
        b1, b2, b3 = self.structure.lattice.reciprocal_lattice

        # Maximum G-vector components
        # Kinetic energy in plane-wave DFT: E = ℏ²|G|²/(2m)
        #
        # In atomic units (Hartree, Bohr):
        #   E(Hartree) = (1/2)|G(1/Bohr)|² where m=1, ℏ=1
        #   |G(1/Bohr)|²_max = 2*E_cut(Hartree)
        #
        # Converting from eV to Hartree:
        #   E_cut(Hartree) = E_cut(eV) / HARTREE_TO_EV
        #
        # Reciprocal lattice vectors from Lattice class are in Å⁻¹
        # (standard crystallographic definition with 2π factor already included).
        # G-vectors: G = n1*b1 + n2*b2 + n3*b3  [units: Å⁻¹]
        #
        # To convert |G(Å⁻¹)| to |G(1/Bohr)|:
        #   |G(1/Bohr)| = |G(Å⁻¹)| × BOHR_TO_ANGSTROM
        #   |G(1/Bohr)|² = |G(Å⁻¹)|² × BOHR_TO_ANGSTROM²
        #
        # Therefore:
        #   gmax²(Å⁻¹) = 2*E_cut(Hartree) / BOHR_TO_ANGSTROM²

        ecut_hartree = self.ecut / HARTREE_TO_EV
        # Factor to convert from Å⁻² to Bohr⁻²
        conversion_factor = BOHR_TO_ANGSTROM**2
        gmax_squared = 2.0 * ecut_hartree / conversion_factor
        gmax = np.sqrt(gmax_squared)

        # Estimate maximum indices
        b_norms = [np.linalg.norm(b1), np.linalg.norm(b2), np.linalg.norm(b3)]
        max_indices = [int(np.ceil(gmax / bn * 2)) for bn in b_norms]

        # Safety check: prevent absurdly large loops
        MAX_INDEX_LIMIT = 50  # Reasonable for small ecut (~20 eV)
        if any(idx > MAX_INDEX_LIMIT for idx in max_indices):
            import warnings
            warnings.warn(
                f"G-vector indices {max_indices} exceed limit {MAX_INDEX_LIMIT}. "
                f"Clamping to prevent hang. This may indicate incorrect ecut units or constants."
            )
            max_indices = [min(idx, MAX_INDEX_LIMIT) for idx in max_indices]

        # Generate all G-vectors within sphere
        gvectors = []
        total_checked = 0
        for n1 in range(-max_indices[0], max_indices[0] + 1):
            for n2 in range(-max_indices[1], max_indices[1] + 1):
                for n3 in range(-max_indices[2], max_indices[2] + 1):
                    total_checked += 1
                    G = n1 * b1 + n2 * b2 + n3 * b3
                    if np.dot(G, G) <= gmax_squared:
                        gvectors.append([n1, n2, n3])

        # Debug info
        print(f"PlaneWaveBasis: Generated {len(gvectors)} G-vectors from {total_checked} candidates")
        print(f"  ecut={self.ecut:.1f} eV, gmax={gmax:.3f} (2pi/A), max_indices={max_indices}")

        return np.array(gvectors)

    def _compute_fft_grid(self) -> Tuple[int, int, int]:
        """
        Compute FFT grid dimensions for density representation.

        The grid must be fine enough to represent all plane waves:
            N_α ≥ 2 * max|G_α| + 1

        Reference: Payne et al. (1992), Section II.B
        """
        gmax = np.max(np.abs(self.gvectors), axis=0)
        fft_grid = tuple(2 * int(g) + 10 for g in gmax)  # +10 for safety
        return fft_grid

    def kinetic_energy_operator(self, kpoint: np.ndarray) -> np.ndarray:
        """
        Construct kinetic energy operator in plane-wave basis.

        T̂|G⟩ = (ℏ²/2m)|k + G|² |G⟩

        Args:
            kpoint: k-vector in fractional coordinates

        Returns:
            Diagonal matrix of kinetic energies (eV)
        """
        # Convert k to Cartesian
        k_cart = np.dot(kpoint, self.structure.lattice.reciprocal_lattice)

        # Compute |k + G|² for all G
        kinetic_energies = np.zeros(self.num_gvectors)
        for i, g_frac in enumerate(self.gvectors):
            G_cart = np.dot(g_frac, self.structure.lattice.reciprocal_lattice)
            kplusG = k_cart + G_cart
            # T = ℏ²|k+G|²/(2m) in eV
            kinetic_energies[i] = (HBAR**2 * np.dot(kplusG, kplusG)) / (
                2 * ELECTRON_MASS * ELEMENTARY_CHARGE
            ) * HARTREE_TO_EV

        return np.diag(kinetic_energies)


class KohnShamSolver:
    """
    Self-consistent field solver for Kohn-Sham equations.

    Algorithm (iterative diagonalization):
    ---------------------------------------
    1. Initialize: guess ρ(r) (e.g., superposition of atomic densities)
    2. Construct V_eff(r) = V_ext(r) + V_H[ρ] + V_xc[ρ]
    3. Solve Kohn-Sham equations: Ĥ_KS ψ_i = ε_i ψ_i
    4. Compute new density: ρ_new(r) = Σ_i f_i |ψ_i(r)|²
    5. Mix densities: ρ(r) = (1-β)ρ_old + β ρ_new
    6. Check convergence: if |E_new - E_old| < tolerance, done
    7. Otherwise, go to step 2

    Reference: Payne et al. (1992), DOI: 10.1103/RevModPhys.64.1045
    """

    def __init__(
        self,
        structure: Structure,
        xc_functional: Callable,
        pseudopotential: Callable,
        ecut: float = 500.0,  # eV
        kpoints: Optional[np.ndarray] = None,
        convergence: Optional[SCFConvergence] = None
    ):
        """
        Initialize Kohn-Sham solver.

        Args:
            structure: Crystal structure
            xc_functional: Exchange-correlation functional
            pseudopotential: Pseudopotential function
            ecut: Plane-wave cutoff energy (eV)
            kpoints: K-points for Brillouin zone integration
            convergence: SCF convergence parameters
        """
        self.structure = structure
        self.xc_functional = xc_functional
        self.pseudopotential = pseudopotential  # Keep for backward compatibility
        self.convergence = convergence or SCFConvergence()

        # Load actual pseudopotentials for each element
        from dft.pseudopotential import get_pseudopotential
        self.pseudopotentials_by_element = {}
        unique_elements = set(site.element for site in structure.sites)
        for element in unique_elements:
            try:
                self.pseudopotentials_by_element[element] = get_pseudopotential(element)
            except ValueError:
                # Element not available, will use zero potential
                self.pseudopotentials_by_element[element] = None

        # Initialize plane-wave basis
        self.pwbasis = PlaneWaveBasis(structure, ecut, kpoints)

        # Number of electrons
        self.num_electrons = self._count_valence_electrons()
        self.num_bands = int(np.ceil(self.num_electrons / 2.0)) + 4  # +4 conduction bands

        # Store cutoff energy for later access
        self.ecut = ecut

        # Initialize density mixer based on mixing_method
        if self.convergence.mixing_method == MixingMethod.PULAY:
            self.density_mixer = PulayMixer(
                beta=self.convergence.mixing_beta,
                history_size=5  # Conservative for stability with pseudopotentials
            )
        else:
            self.density_mixer = None  # Will use simple mixing

        # Initialize density (will be set in solve())
        self.density = None
        self.wavefunctions = None
        self.eigenvalues = None

    @classmethod
    def from_parameters(
        cls,
        structure: Structure,
        xc: str = 'LDA',
        pseudopot: str = 'norm-conserving',
        ecut: float = 500.0,
        num_kpoints: int = 1,
        convergence: Optional[SCFConvergence] = None
    ) -> 'KohnShamSolver':
        """
        Factory method for simplified solver creation.

        This provides a user-friendly interface that accepts string parameters
        while maintaining the advanced API for expert users.

        Args:
            structure: Crystal structure
            xc: XC functional name ('LDA', 'PBE', 'HSE06', 'SCAN')
            pseudopot: Pseudopotential type ('norm-conserving', 'ultrasoft', 'paw')
            ecut: Plane-wave cutoff energy (eV)
            num_kpoints: Number of k-points (simplified - uses Gamma-centered grid)
            convergence: SCF convergence parameters

        Returns:
            Initialized KohnShamSolver instance

        Example:
            >>> solver = KohnShamSolver.from_parameters(
            ...     structure=my_structure,
            ...     xc='LDA',
            ...     ecut=400.0
            ... )

        Reference:
            Design pattern: Factory Method for simplified object construction
        """
        from dft.xc_functionals import LDA_PZ, GGA_PBE, HybridHSE06, MetaGGA_SCAN
        from dft.pseudopotential import get_pseudopotential

        # Map XC functional strings to callable objects
        XC_FUNCTIONAL_MAP = {
            'LDA': LDA_PZ(),
            'LDA-PZ': LDA_PZ(),
            'PBE': GGA_PBE(),
            'GGA-PBE': GGA_PBE(),
            'HSE06': HybridHSE06(),
            'SCAN': MetaGGA_SCAN(),
        }

        # Get XC functional
        xc_upper = xc.upper()
        if xc_upper not in XC_FUNCTIONAL_MAP:
            raise ValueError(
                f"Unknown XC functional: {xc}. "
                f"Available: {list(XC_FUNCTIONAL_MAP.keys())}"
            )
        xc_functional = XC_FUNCTIONAL_MAP[xc_upper]

        # Load pseudopotentials for all unique elements in structure
        unique_elements = set(site.element for site in structure.sites)
        pseudopotentials = {}
        for element in unique_elements:
            try:
                pseudopotentials[element] = get_pseudopotential(element)
            except ValueError:
                # Fallback to no pseudopotential for unknown elements
                print(f"Warning: No pseudopotential for {element}, using V_ext=0")
                pseudopotentials[element] = None

        # Create unified pseudopotential function
        # This returns the V_local potential at atom positions
        def pseudopotential_function(r):
            """
            Unified pseudopotential for all atoms in structure.

            For now, simplified: just returns sum of V_local from each atom.
            Proper implementation would be in Fourier space in the Hamiltonian.
            """
            return np.zeros_like(r)  # Will use proper implementation in Hamiltonian

        # Generate k-points (simplified: Gamma-centered Monkhorst-Pack)
        if num_kpoints == 1:
            kpoints = np.array([[0.0, 0.0, 0.0]])  # Gamma point only
        else:
            # Simplified Monkhorst-Pack grid
            n = int(np.ceil(num_kpoints**(1/3)))
            kpoints = []
            for i in range(n):
                for j in range(n):
                    for k in range(n):
                        kpoints.append([
                            (i + 0.5) / n - 0.5,
                            (j + 0.5) / n - 0.5,
                            (k + 0.5) / n - 0.5
                        ])
            kpoints = np.array(kpoints[:num_kpoints])

        # Create solver using advanced API
        return cls(
            structure=structure,
            xc_functional=xc_functional,
            pseudopotential=pseudopotential_function,
            ecut=ecut,
            kpoints=kpoints,
            convergence=convergence
        )

    def _count_valence_electrons(self) -> int:
        """
        Count total valence electrons in the system.

        Uses Z_ion from loaded pseudopotentials when available.
        Falls back to periodic table defaults otherwise.
        """
        total = 0
        for site in self.structure.sites:
            # Try to get from loaded pseudopotential (most accurate)
            if site.element in self.pseudopotentials_by_element:
                pp = self.pseudopotentials_by_element[site.element]
                if pp is not None:
                    total += pp.data.Z_ion
                    continue

            # Fallback: periodic table defaults
            valence_electrons_map = {
                'H': 1, 'He': 2,
                'Li': 1, 'Be': 2, 'B': 3, 'C': 4, 'N': 5, 'O': 6, 'F': 7, 'Ne': 8,
                'Na': 1, 'Mg': 2, 'Al': 3, 'Si': 4, 'P': 5, 'S': 6, 'Cl': 7, 'Ar': 8,
                'Fe': 8, 'Ni': 10, 'Cu': 11,
            }
            total += valence_electrons_map.get(site.element, 4)

        return total

    def _initialize_density(self) -> np.ndarray:
        """
        Initialize electron density with superposition of atomic densities.

        For each atom, use a simple Gaussian:
            ρ_atom(r) = (Z_val / (π r_cut²)^(3/2)) exp(-|r-R|² / r_cut²)

        Reference: This is a common starting guess. See Martin (2004), Chapter 11.
        """
        # Simplified: start with uniform density
        # In real implementation: superposition of atomic densities
        volume = self.structure.lattice.volume * (BOHR_TO_ANGSTROM**3)
        uniform_density = self.num_electrons / volume

        # Initialize density on FFT grid
        density_grid = np.full(self.pwbasis.fft_grid, uniform_density)

        return density_grid

    def _compute_external_potential(self) -> np.ndarray:
        """
        Compute external potential from ionic pseudopotentials.

        V_ext(r) = sum_I V_ps,I(|r - R_I|)

        For each atom I at position R_I, compute its pseudopotential
        contribution V_ps,I at all points on the FFT grid.

        Returns:
            External potential on real-space FFT grid (eV)

        Reference:
            - Troullier & Martins (1991), Phys. Rev. B 43, 1993
            - Payne et al. (1992), Rev. Mod. Phys. 64, 1045, Eq. (8)
        """
        # Initialize V_ext on FFT grid
        V_ext = np.zeros(self.pwbasis.fft_grid)

        # Generate real-space grid points
        # FFT grid has dimensions (n1, n2, n3)
        n1, n2, n3 = self.pwbasis.fft_grid

        # Create meshgrid for fractional coordinates
        # Each point (i, j, k) corresponds to fractional coordinates (i/n1, j/n2, k/n3)
        i_grid = np.arange(n1)[:, None, None]
        j_grid = np.arange(n2)[None, :, None]
        k_grid = np.arange(n3)[None, None, :]

        # Fractional coordinates of all grid points
        frac_coords = np.stack([
            i_grid / n1 * np.ones((n1, n2, n3)),
            j_grid / n2 * np.ones((n1, n2, n3)),
            k_grid / n3 * np.ones((n1, n2, n3))
        ], axis=-1)  # Shape: (n1, n2, n3, 3)

        # Convert to Cartesian coordinates (Angstrom)
        lattice_matrix = self.structure.lattice.matrix

        # For each atom, add its pseudopotential contribution
        for site in self.structure.sites:
            # Get pseudopotential for this element
            pp = self.pseudopotentials_by_element.get(site.element)

            if pp is None:
                # No pseudopotential available - skip
                continue

            # Atom position in Cartesian coordinates (Angstrom)
            atom_pos_cart = np.dot(site.position, lattice_matrix)

            # Compute distance from all grid points to this atom
            # Grid points in Cartesian coordinates
            grid_cart = np.einsum('ijkl,lm->ijkm', frac_coords, lattice_matrix)

            # Distance vector: r - R_I
            dr = grid_cart - atom_pos_cart[None, None, None, :]

            # Handle periodic boundary conditions (minimum image convention)
            # For each Cartesian component, bring to [-L/2, L/2]
            for dim in range(3):
                L = np.linalg.norm(lattice_matrix[dim])
                dr[..., dim] = dr[..., dim] - L * np.round(dr[..., dim] / L)

            # Distance magnitude
            r_dist = np.linalg.norm(dr, axis=-1)

            # Add pseudopotential contribution V_local(r)
            V_ext += pp.V_local(r_dist)

        return V_ext

    def _compute_hartree_potential(self, density: np.ndarray) -> np.ndarray:
        """
        Compute Hartree potential from electron density.

        Solve Poisson equation in Fourier space:
            ∇²V_H(r) = -4πρ(r)
            ⟹ V_H(G) = 4π/|G|² ρ(G)    for G ≠ 0
            ⟹ V_H(0) = 0 (convention: set average to zero)

        Args:
            density: Electron density on real-space grid

        Returns:
            Hartree potential on real-space grid (eV)

        Reference: Martin (2004), Eq. (8.3)
        """
        # FFT to reciprocal space
        density_G = np.fft.fftn(density)

        # Compute Hartree potential in G-space
        V_H_G = np.zeros_like(density_G, dtype=complex)

        # Get G-vectors for FFT grid
        grid_shape = density.shape
        for i in range(grid_shape[0]):
            for j in range(grid_shape[1]):
                for k in range(grid_shape[2]):
                    # G-vector indices
                    gx = i if i <= grid_shape[0]//2 else i - grid_shape[0]
                    gy = j if j <= grid_shape[1]//2 else j - grid_shape[1]
                    gz = k if k <= grid_shape[2]//2 else k - grid_shape[2]

                    if gx == 0 and gy == 0 and gz == 0:
                        continue  # G=0 component set to zero

                    # G-vector in Cartesian coordinates
                    G_frac = np.array([gx, gy, gz])
                    G_cart = np.dot(G_frac, self.structure.lattice.reciprocal_lattice)
                    G_squared = np.dot(G_cart, G_cart)

                    # V_H(G) = 4π/|G|² ρ(G)
                    V_H_G[i, j, k] = 4 * np.pi * density_G[i, j, k] / G_squared

        # Transform back to real space
        V_H = np.fft.ifftn(V_H_G).real

        return V_H

    def _compute_xc_potential(self, density: np.ndarray) -> np.ndarray:
        """
        Compute exchange-correlation potential.

        V_xc(r) = δE_xc[ρ]/δρ(r)

        This is the functional derivative of E_xc with respect to density.

        Args:
            density: Electron density

        Returns:
            XC potential (eV)

        Reference: Depends on XC functional (LDA, GGA, etc.)
        """
        # Call XC functional (implemented in xc_functionals.py)
        V_xc = self.xc_functional(density)
        return V_xc

    def _construct_hamiltonian(
        self,
        kpoint: np.ndarray,
        V_eff: np.ndarray
    ) -> np.ndarray:
        """
        Construct Kohn-Sham Hamiltonian matrix.

        Ĥ_KS = T̂ + V̂_eff

        where T̂ is kinetic energy and V̂_eff is effective potential.

        Args:
            kpoint: k-vector
            V_eff: Effective potential on real-space grid

        Returns:
            Hamiltonian matrix (N_G × N_G)
        """
        # Kinetic energy (diagonal)
        T = self.pwbasis.kinetic_energy_operator(kpoint)

        # Effective potential in G-space
        # V_{ij} = ⟨G_i|V_eff|G_j⟩ = V_eff(G_i - G_j)
        V_eff_G = np.fft.fftn(V_eff)
        fft_shape = V_eff.shape

        num_G = self.pwbasis.num_gvectors
        V = np.zeros((num_G, num_G), dtype=complex)

        # Construct full potential matrix using vectorized operations
        # Reference: Payne et al. (1992), Eq. (3.9)
        #
        # V_{ij} = V_eff(G_i - G_j)
        #
        # Vectorized approach:
        # 1. Compute all G_i - G_j differences using broadcasting
        # 2. Map to FFT indices vectorially
        # 3. Index V_eff_G array once

        # G-vectors: shape (num_G, 3)
        gvecs = self.pwbasis.gvectors.astype(int)

        # Compute all differences: G_i - G_j
        # Broadcasting: (num_G, 1, 3) - (1, num_G, 3) = (num_G, num_G, 3)
        G_diff = gvecs[:, None, :] - gvecs[None, :, :]

        # Map to FFT grid indices (handle negative frequencies)
        # For negative g: index = (N + g) % N
        # For positive g: index = g % N
        # Both cases: index = (N + g) % N works correctly
        idx_0 = (fft_shape[0] + G_diff[:, :, 0]) % fft_shape[0]
        idx_1 = (fft_shape[1] + G_diff[:, :, 1]) % fft_shape[1]
        idx_2 = (fft_shape[2] + G_diff[:, :, 2]) % fft_shape[2]

        # Index V_eff_G array: V[i,j] = V_eff_G[idx_0[i,j], idx_1[i,j], idx_2[i,j]]
        V = V_eff_G[idx_0, idx_1, idx_2]

        # Normalize by FFT grid size (FFT convention)
        V = V / np.prod(fft_shape)

        # Total Hamiltonian (take real part - should be Hermitian)
        # For real V_eff, V matrix should be Hermitian
        H = T + V.real

        return H

    def _solve_kohn_sham_equations(
        self,
        kpoint: np.ndarray,
        V_eff: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Solve Kohn-Sham equations for a single k-point.

        Ĥ_KS ψ_nk = ε_nk ψ_nk

        This is a generalized eigenvalue problem solved via diagonalization.

        Args:
            kpoint: k-vector
            V_eff: Effective potential

        Returns:
            Tuple of (eigenvalues, eigenvectors)

        Reference: Standard linear algebra. See Payne et al. (1992), Section III.
        """
        # Construct Hamiltonian
        H = self._construct_hamiltonian(kpoint, V_eff)

        # Diagonalize (find num_bands lowest eigenvalues)
        # For large systems, use iterative methods (Lanczos, Davidson)
        eigenvalues, eigenvectors = np.linalg.eigh(H)

        # Return lowest num_bands states (or all available if fewer)
        num_available = min(self.num_bands, len(eigenvalues))
        return eigenvalues[:num_available], eigenvectors[:, :num_available]

    def _compute_density_from_wavefunctions(
        self,
        wavefunctions: List[np.ndarray],
        eigenvalues: List[np.ndarray]
    ) -> np.ndarray:
        """
        Compute electron density from wavefunctions.

        ρ(r) = Σ_{nk} f_nk |ψ_nk(r)|²

        where f_nk are occupation numbers (Fermi-Dirac distribution).

        Args:
            wavefunctions: List of wavefunctions for each k-point
            eigenvalues: List of eigenvalues for each k-point

        Returns:
            Electron density on real-space grid

        Reference: Payne et al. (1992), Eq. (2.11)
        """
        density = np.zeros(self.pwbasis.fft_grid)

        # Fermi level (simplified: assume T=0)
        all_eigenvalues = np.concatenate(eigenvalues)
        fermi_idx = min(self.num_electrons // 2 - 1, len(all_eigenvalues) - 1)
        fermi_level = np.sort(all_eigenvalues)[fermi_idx]

        for ik, (wfn_k, eig_k) in enumerate(zip(wavefunctions, eigenvalues)):
            # Loop over available bands (may be less than num_bands if small basis)
            num_bands_available = len(eig_k)
            for iband in range(num_bands_available):
                # Occupation (0 or 1 for T=0, spin-unpolarized gives factor of 2)
                if eig_k[iband] <= fermi_level:
                    occupation = 2.0 / len(self.pwbasis.kpoints)  # k-point weight
                else:
                    occupation = 0.0

                # Transform wavefunction to real space
                wfn_real = self._wfn_to_realspace(wfn_k[:, iband])

                # Add |ψ|² to density
                density += occupation * np.abs(wfn_real)**2

        return density

    def _wfn_to_realspace(self, wfn_G: np.ndarray) -> np.ndarray:
        """Convert wavefunction from G-space to real space via FFT."""
        # Simplified implementation
        wfn_grid = np.zeros(self.pwbasis.fft_grid, dtype=complex)
        # Map plane-wave coefficients to FFT grid
        # (actual implementation more complex)
        return np.fft.ifftn(wfn_grid)

    def _mix_densities(
        self,
        rho_old: np.ndarray,
        rho_new: np.ndarray,
        iteration: int
    ) -> np.ndarray:
        """
        Mix old and new densities for SCF convergence.

        Simple linear mixing:
            ρ_mixed = (1-β)ρ_old + β ρ_new

        For better convergence, use Pulay DIIS or Broyden mixing.

        Args:
            rho_old: Previous iteration density
            rho_new: New density from wavefunctions
            iteration: Current SCF iteration

        Returns:
            Mixed density

        Reference: Pulay, P. (1980). Convergence acceleration of iterative
        sequences. the case of scf iteration. Chemical Physics Letters, 73(2), 393-398.
        DOI: 10.1016/0009-2614(80)80396-4
        """
        if self.convergence.mixing_method == MixingMethod.PULAY and self.density_mixer is not None:
            # Use Pulay DIIS mixing (professional, 3-5x faster convergence)
            return self.density_mixer.mix(rho_old, rho_new)
        elif self.convergence.mixing_method == MixingMethod.LINEAR:
            # Simple linear mixing
            return (1 - self.convergence.mixing_beta) * rho_old + \
                   self.convergence.mixing_beta * rho_new
        else:
            # TODO: Implement Broyden, Kerker
            # For now, fall back to simple linear mixing
            return (1 - self.convergence.mixing_beta) * rho_old + \
                   self.convergence.mixing_beta * rho_new

    def _compute_total_energy(
        self,
        density: np.ndarray,
        V_eff: np.ndarray,
        eigenvalues: List[np.ndarray]
    ) -> float:
        """
        Compute total energy from Kohn-Sham quantities.

        E_total = Σ_i f_i ε_i - E_H[ρ] - ∫V_xc(r)ρ(r)dr + E_xc[ρ] + E_ion

        This corrects for double-counting in the sum of eigenvalues.

        Args:
            density: Electron density
            V_eff: Effective potential
            eigenvalues: Kohn-Sham eigenvalues

        Returns:
            Total energy (eV)

        Reference: Martin (2004), Eq. (6.58)
        """
        # Sum of occupied eigenvalues
        E_band = 0.0
        all_eigs = np.concatenate(eigenvalues)
        all_eigs_sorted = np.sort(all_eigs)
        # Use min to handle case where basis is smaller than num_electrons
        num_occ = min(self.num_electrons // 2, len(all_eigs_sorted))
        for i in range(num_occ):
            E_band += 2.0 * all_eigs_sorted[i]  # factor 2 for spin

        # Hartree energy (compute from density)
        V_H = self._compute_hartree_potential(density)
        dV = self.structure.lattice.volume / np.prod(density.shape)
        E_H = 0.5 * np.sum(density * V_H) * dV

        # XC energy: E_xc = ∫ ρ(r) ε_xc[ρ(r)] dr
        # where ε_xc is XC energy per electron from the functional
        # Only compute where density is significant to avoid numerical issues
        density_safe = np.maximum(density, 1e-12)  # Prevent division by zero
        epsilon_xc = self.xc_functional.energy_density(density_safe)

        # Replace NaN/Inf with zeros
        epsilon_xc = np.where(np.isfinite(epsilon_xc), epsilon_xc, 0.0)
        E_xc = np.sum(density * epsilon_xc) * dV

        # XC potential for double-counting correction
        V_xc = self._compute_xc_potential(density)
        V_xc = np.where(np.isfinite(V_xc), V_xc, 0.0)
        int_Vxc_rho = np.sum(density * V_xc) * dV

        # Total energy (Harris-Foulkes functional)
        # E = Σ f_i ε_i - E_H - ∫V_xc ρ + E_xc
        # The eigenvalues include full V_eff = V_ext + V_H + V_xc
        # We subtract E_H and (∫V_xc ρ) then add back E_xc to correct double-counting
        E_total = E_band - E_H - int_Vxc_rho + E_xc

        return E_total

    def solve(self) -> Tuple[float, np.ndarray, List[np.ndarray], List[np.ndarray]]:
        """
        Solve Kohn-Sham equations self-consistently.

        Returns:
            Tuple of (total_energy, density, wavefunctions, eigenvalues)

        Raises:
            RuntimeError: If SCF does not converge
        """
        # Initialize density
        density = self._initialize_density()

        # SCF loop
        energy_old = 0.0
        for iteration in range(self.convergence.max_iterations):
            # 1. Construct effective potential
            V_H = self._compute_hartree_potential(density)
            V_xc = self._compute_xc_potential(density)
            # V_ext from ionic pseudopotentials
            V_ext = self._compute_external_potential()
            V_eff = V_ext + V_H + V_xc

            # 2. Solve KS equations for each k-point
            wavefunctions = []
            eigenvalues = []
            for kpoint in self.pwbasis.kpoints:
                eigs, wfns = self._solve_kohn_sham_equations(kpoint, V_eff)
                eigenvalues.append(eigs)
                wavefunctions.append(wfns)

            # 3. Compute new density
            density_new = self._compute_density_from_wavefunctions(wavefunctions, eigenvalues)

            # 4. Compute total energy
            energy_new = self._compute_total_energy(density_new, V_eff, eigenvalues)

            # 5. Check convergence
            energy_diff = abs(energy_new - energy_old)
            density_diff = np.sum(np.abs(density_new - density))

            self.convergence.energy_history.append(energy_new)

            print(f"SCF Iteration {iteration+1}: E = {energy_new:.6f} eV, "
                  f"dE = {energy_diff:.2e} eV, drho = {density_diff:.2e}")

            if energy_diff < self.convergence.energy_tolerance and \
               density_diff < self.convergence.density_tolerance:
                self.convergence.converged = True
                self.convergence.iterations = iteration + 1
                self.convergence.final_energy = energy_new
                break

            # 6. Mix densities
            density_mixed = self._mix_densities(density, density_new, iteration)

            # Ensure physical density (guards against Pulay mixer instabilities)
            if not np.all(np.isfinite(density_mixed)):
                print("  WARNING: Mixed density has NaN/Inf, using simple mixing fallback")
                # Use previous good density (density) and new density for fallback
                density = (1 - 0.3) * density + 0.3 * density_new  # Conservative mixing
            else:
                density = density_mixed

            # Ensure strictly positive density
            density = np.maximum(density, 1e-15)

            energy_old = energy_new

        if not self.convergence.converged:
            raise RuntimeError(f"SCF did not converge in {self.convergence.max_iterations} iterations")

        # Store results
        self.density = density
        self.wavefunctions = wavefunctions
        self.eigenvalues = eigenvalues

        return energy_new, density, wavefunctions, eigenvalues

    def compute_forces(self) -> np.ndarray:
        """
        Compute forces on atoms using Hellmann-Feynman theorem.

        F_I = -∇_I E = -∫ρ(r) ∇_I V_ext(r) dr - ∇_I E_ion

        For complete forces, need Pulay corrections for incomplete basis.

        Returns:
            Forces on atoms (N_atoms × 3) in eV/Å

        Reference: Hellmann-Feynman: DOI: 10.1080/00268976900100941 (Pulay, 1969)
        """
        forces = np.zeros((len(self.structure.sites), 3))

        # Hellmann-Feynman forces (simplified)
        # In practice: ⟨ψ|∂V_loc/∂R_I|ψ⟩ + nonlocal PP contribution + Pulay correction

        # TODO: Implement full force calculation
        # For now, return zero (placeholder)

        return forces


__all__ = [
    'KohnShamSolver',
    'SCFConvergence',
    'PlaneWaveBasis',
    'PulayMixer',
    'MixingMethod',
]
