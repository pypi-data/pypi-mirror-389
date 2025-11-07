"""
Exchange-Correlation Functionals
=================================

Implementation of exchange-correlation (XC) functionals for DFT.

The XC functional is the only unknown part of Kohn-Sham DFT. It accounts for:
1. Exchange: Pauli exclusion principle (quantum mechanical)
2. Correlation: Many-body electron-electron interactions beyond Hartree

Mathematical Framework:
-----------------------

The XC energy is a functional of the electron density:
    E_xc[ρ] = ∫ ρ(r) ε_xc(ρ(r), ∇ρ(r), ...) dr

where ε_xc is the XC energy per particle.

The XC potential (functional derivative):
    V_xc(r) = δE_xc[ρ]/δρ(r) = ε_xc + ρ ∂ε_xc/∂ρ + ...

Hierarchy of Approximations ("Jacob's Ladder"):
-----------------------------------------------
1. LDA (Local Density Approximation): ε_xc = ε_xc(ρ)
2. GGA (Generalized Gradient Approximation): ε_xc = ε_xc(ρ, |∇ρ|)
3. meta-GGA: ε_xc = ε_xc(ρ, |∇ρ|, ∇²ρ, τ)
4. Hybrid: Mix exact exchange with DFT
5. RPA: Random phase approximation (beyond DFT)

where τ = (1/2)Σ_i|∇ψ_i|² is the kinetic energy density.

Scientific References:
----------------------
[1] Perdew, J. P., & Zunger, A. (1981). Self-interaction correction to
    density-functional approximations for many-electron systems.
    Physical Review B, 23(10), 5048-5079.
    DOI: 10.1103/PhysRevB.23.5048
    (LDA parametrization - Perdew-Zunger)

[2] Perdew, J. P., Burke, K., & Ernzerhof, M. (1996). Generalized gradient
    approximation made simple. Physical Review Letters, 77(18), 3865-3868.
    DOI: 10.1103/PhysRevLett.77.3865
    (GGA-PBE functional - most widely used)

[3] Heyd, J., Scuseria, G. E., & Ernzerhof, M. (2003). Hybrid functionals
    based on a screened Coulomb potential. Journal of Chemical Physics, 118(18), 8207-8215.
    DOI: 10.1063/1.1564060
    (HSE06 screened hybrid functional - band gaps)

[4] Sun, J., Ruzsinszky, A., & Perdew, J. P. (2015). Strongly constrained and
    appropriately normed semilocal density functional.
    Physical Review Letters, 115(3), 036402.
    DOI: 10.1103/PhysRevLett.115.036402
    (SCAN meta-GGA - state-of-the-art semilocal)

[5] Perdew, J. P., et al. (2001). Jacob's ladder of density functional approximations
    for the exchange-correlation energy. AIP Conference Proceedings, 577(1), 1-20.
    DOI: 10.1063/1.1390175
"""

import numpy as np
from abc import ABC, abstractmethod
from typing import Tuple, Optional
from enum import Enum

from core.constants import (
    PBE_KAPPA, PBE_MU,
    HSE_OMEGA, HSE_ALPHA,
    SCAN_C1C, SCAN_C2C, SCAN_K1
)


class XCFunctional(ABC):
    """
    Abstract base class for exchange-correlation functionals.

    All XC functionals must implement:
    - energy_density: ε_xc(ρ, ∇ρ, ...) energy per particle
    - potential: V_xc(ρ, ∇ρ, ...) XC potential
    """

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def energy_density(
        self,
        rho: np.ndarray,
        grad_rho: Optional[np.ndarray] = None,
        tau: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """
        Compute XC energy density ε_xc in eV.

        Args:
            rho: Electron density (electrons/Å³)
            grad_rho: Gradient of density (for GGA) - shape: (..., 3)
            tau: Kinetic energy density (for meta-GGA)

        Returns:
            XC energy density (eV per electron)
        """
        pass

    @abstractmethod
    def potential(
        self,
        rho: np.ndarray,
        grad_rho: Optional[np.ndarray] = None,
        tau: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """
        Compute XC potential V_xc = δE_xc/δρ in eV.

        Returns:
            XC potential (eV)
        """
        pass

    def total_energy(
        self,
        rho: np.ndarray,
        volume: float,
        grad_rho: Optional[np.ndarray] = None,
        tau: Optional[np.ndarray] = None
    ) -> float:
        """
        Compute total XC energy E_xc = ∫ρ(r)ε_xc(r)dr.

        Args:
            rho: Electron density
            volume: Integration volume (Å³)
            grad_rho: Density gradient
            tau: Kinetic energy density

        Returns:
            Total XC energy (eV)
        """
        epsilon_xc = self.energy_density(rho, grad_rho, tau)
        # Integrate: E_xc = Σ ρ_i ε_xc_i ΔV
        dV = volume / np.prod(rho.shape)
        return np.sum(rho * epsilon_xc) * dV

    def __call__(self, rho: np.ndarray, **kwargs) -> np.ndarray:
        """Convenience: calling functional returns potential."""
        return self.potential(rho, **kwargs)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}')"


# ============================================================================
# LDA - Local Density Approximation
# ============================================================================

class LDA_PZ(XCFunctional):
    """
    LDA with Perdew-Zunger parametrization of Ceperley-Alder QMC data.

    Exchange Energy (exact for uniform electron gas):
    --------------------------------------------------
        ε_x(ρ) = -C_x ρ^(1/3)

    where C_x = (3/4)(3/π)^(1/3) ≈ 0.7386 in Hartree atomic units.

    Correlation Energy (Perdew-Zunger fit to QMC):
    -----------------------------------------------
    High density (r_s < 1):
        ε_c(r_s) = A ln(r_s) + B + C r_s ln(r_s) + D r_s

    Low density (r_s ≥ 1):
        ε_c(r_s) = γ/(1 + β₁√r_s + β₂r_s)

    where r_s = (3/(4πρ))^(1/3) is the Wigner-Seitz radius.

    Parameters from Perdew & Zunger (1981):
    High density: A = 0.0311, B = -0.048, C = 0.002, D = -0.0116
    Low density: γ = -0.1423, β₁ = 1.0529, β₂ = 0.3334

    Reference: DOI: 10.1103/PhysRevB.23.5048
    """

    def __init__(self):
        super().__init__("LDA-PZ")

        # Perdew-Zunger parameters (Hartree atomic units)
        # High density (r_s < 1)
        self.A_high = 0.0311
        self.B_high = -0.048
        self.C_high = 0.002
        self.D_high = -0.0116

        # Low density (r_s >= 1)
        self.gamma_low = -0.1423
        self.beta1_low = 1.0529
        self.beta2_low = 0.3334

        # Exchange constant C_x = (3/4)(3/π)^(1/3)
        self.C_x = 0.7386  # Hartree a.u.

    def _rs_from_density(self, rho: np.ndarray) -> np.ndarray:
        """
        Compute Wigner-Seitz radius r_s = (3/(4πρ))^(1/3).

        Args:
            rho: Electron density (electrons/Å³)

        Returns:
            r_s in Bohr radii
        """
        # Convert density from electrons/Å³ to electrons/Bohr³
        from core.constants import BOHR_TO_ANGSTROM
        rho_bohr = rho * (BOHR_TO_ANGSTROM**3)

        # r_s = (3/(4πρ))^(1/3)
        r_s = (3.0 / (4.0 * np.pi * rho_bohr))**(1.0/3.0)
        return r_s

    def exchange_energy(self, rho: np.ndarray) -> np.ndarray:
        """
        LDA exchange energy per particle (Hartree).

        ε_x = -C_x ρ^(1/3) = -C_x / r_s  (where ρ ∝ r_s^(-3))

        Exact for uniform electron gas.
        """
        r_s = self._rs_from_density(rho)
        epsilon_x = -self.C_x / r_s
        return epsilon_x

    def correlation_energy(self, rho: np.ndarray) -> np.ndarray:
        """
        LDA correlation energy per particle (Hartree).

        Perdew-Zunger parametrization of Ceperley-Alder QMC data.
        """
        r_s = self._rs_from_density(rho)

        # Initialize output
        epsilon_c = np.zeros_like(r_s)

        # High density region (r_s < 1)
        mask_high = r_s < 1.0
        rs_high = r_s[mask_high]
        epsilon_c[mask_high] = (
            self.A_high * np.log(rs_high) +
            self.B_high +
            self.C_high * rs_high * np.log(rs_high) +
            self.D_high * rs_high
        )

        # Low density region (r_s >= 1)
        mask_low = r_s >= 1.0
        rs_low = r_s[mask_low]
        sqrt_rs = np.sqrt(rs_low)
        epsilon_c[mask_low] = self.gamma_low / (
            1.0 + self.beta1_low * sqrt_rs + self.beta2_low * rs_low
        )

        return epsilon_c

    def energy_density(
        self,
        rho: np.ndarray,
        grad_rho: Optional[np.ndarray] = None,
        tau: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """
        Total XC energy density: ε_xc = ε_x + ε_c (Hartree).

        Convert to eV before returning.
        """
        epsilon_x = self.exchange_energy(rho)
        epsilon_c = self.correlation_energy(rho)
        epsilon_xc = epsilon_x + epsilon_c

        # Convert Hartree to eV
        from core.constants import HARTREE_TO_EV
        return epsilon_xc * HARTREE_TO_EV

    def potential(
        self,
        rho: np.ndarray,
        grad_rho: Optional[np.ndarray] = None,
        tau: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """
        XC potential V_xc = ε_xc + ρ dε_xc/dρ.

        For LDA: V_xc = dE_xc/dρ = ε_xc + ρ dε_xc/dρ

        Using chain rule: dε_xc/dρ = (dε_xc/dr_s)(dr_s/dρ)
        where dr_s/dρ = -(1/3)r_s/ρ

        Exchange potential:
            V_x = (4/3)ε_x

        Correlation potential:
            V_c = ε_c + (r_s/3)(dε_c/dr_s)

        Reference: Martin (2004), Appendix D
        """
        r_s = self._rs_from_density(rho)

        # Exchange potential
        epsilon_x = self.exchange_energy(rho)
        V_x = (4.0/3.0) * epsilon_x

        # Correlation potential (need derivative)
        epsilon_c = self.correlation_energy(rho)

        # Compute dε_c/dr_s numerically (or analytically)
        deps_drs = np.zeros_like(r_s)

        # High density
        mask_high = r_s < 1.0
        rs_high = r_s[mask_high]
        deps_drs[mask_high] = (
            self.A_high / rs_high +
            self.C_high * (np.log(rs_high) + 1.0) +
            self.D_high
        )

        # Low density
        mask_low = r_s >= 1.0
        rs_low = r_s[mask_low]
        sqrt_rs = np.sqrt(rs_low)
        denom = 1.0 + self.beta1_low * sqrt_rs + self.beta2_low * rs_low
        deps_drs[mask_low] = -self.gamma_low * (
            self.beta1_low / (2.0 * sqrt_rs) + self.beta2_low
        ) / (denom**2)

        V_c = epsilon_c + (r_s / 3.0) * deps_drs

        # Total potential
        V_xc = V_x + V_c

        # Convert to eV
        from core.constants import HARTREE_TO_EV
        return V_xc * HARTREE_TO_EV


# ============================================================================
# GGA - Generalized Gradient Approximation
# ============================================================================

class GGA_PBE(XCFunctional):
    """
    PBE (Perdew-Burke-Ernzerhof) GGA functional.

    The most widely used GGA functional (>100,000 citations).

    Exchange Enhancement Factor:
    ----------------------------
        E_x^GGA = ∫ ρ ε_x^LDA F_x(s) dr

    where F_x(s) is the exchange enhancement factor:
        F_x(s) = 1 + κ - κ/(1 + μs²/κ)

    with s = |∇ρ|/(2k_F ρ) the reduced density gradient,
    k_F = (3π²ρ)^(1/3) the Fermi wavevector,
    and parameters κ = 0.804, μ = 0.2195149727645171.

    Correlation:
    ------------
    PBE correlation is more complex, based on GGA expansion of
    the correlation hole. See Perdew et al. (1996) Eq. (8).

    These parameters satisfy exact constraints:
    - Slowly varying density limit (correct to 2nd order)
    - LDA recovery when |∇ρ| → 0
    - Lieb-Oxford bound on E_x

    Reference: DOI: 10.1103/PhysRevLett.77.3865
    """

    def __init__(self):
        super().__init__("GGA-PBE")
        self.kappa = PBE_KAPPA  # 0.804
        self.mu = PBE_MU        # 0.2195149727645171
        self.lda = LDA_PZ()     # Use LDA as base

    def _reduced_gradient(
        self,
        rho: np.ndarray,
        grad_rho: np.ndarray
    ) -> np.ndarray:
        """
        Compute reduced density gradient s = |∇ρ|/(2k_F ρ).

        This is a dimensionless measure of density inhomogeneity.

        Args:
            rho: Density
            grad_rho: Gradient of density (shape: ..., 3)

        Returns:
            Reduced gradient s
        """
        # Fermi wavevector k_F = (3π²ρ)^(1/3)
        k_F = (3.0 * np.pi**2 * rho)**(1.0/3.0)

        # |∇ρ|
        grad_rho_norm = np.linalg.norm(grad_rho, axis=-1)

        # s = |∇ρ|/(2k_F ρ)
        s = grad_rho_norm / (2.0 * k_F * rho + 1e-12)  # +eps to avoid /0

        return s

    def exchange_enhancement(self, s: np.ndarray) -> np.ndarray:
        """
        PBE exchange enhancement factor F_x(s).

        F_x(s) = 1 + κ - κ/(1 + μs²/κ)

        This interpolates between:
        - F_x(0) = 1 (LDA limit)
        - F_x(s→∞) → 1 + κ (large gradient limit)

        Reference: PBE paper, Eq. (12)
        """
        F_x = 1.0 + self.kappa - self.kappa / (1.0 + self.mu * s**2 / self.kappa)
        return F_x

    def energy_density(
        self,
        rho: np.ndarray,
        grad_rho: Optional[np.ndarray] = None,
        tau: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """
        PBE XC energy density.

        E_x^PBE = E_x^LDA * F_x(s)
        E_c^PBE = E_c^LDA + H(r_s, t, ζ) (more complex for correlation)

        Simplified: Use LDA correlation (full PBE correlation is lengthy)
        """
        if grad_rho is None:
            # Fallback to LDA if gradient not provided
            return self.lda.energy_density(rho)

        # LDA part
        epsilon_x_lda = self.lda.exchange_energy(rho)
        epsilon_c_lda = self.lda.correlation_energy(rho)

        # Reduced gradient
        s = self._reduced_gradient(rho, grad_rho)

        # Enhancement factor
        F_x = self.exchange_enhancement(s)

        # PBE exchange
        epsilon_x_pbe = epsilon_x_lda * F_x

        # PBE correlation (simplified: use LDA)
        # Full PBE correlation is complex, see original paper Eq. (8)
        epsilon_c_pbe = epsilon_c_lda

        epsilon_xc = epsilon_x_pbe + epsilon_c_pbe

        # Convert to eV
        from core.constants import HARTREE_TO_EV
        return epsilon_xc * HARTREE_TO_EV

    def potential(
        self,
        rho: np.ndarray,
        grad_rho: Optional[np.ndarray] = None,
        tau: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """
        PBE XC potential.

        For GGA, the potential has two parts:
            V_xc = δE_xc/δρ - ∇·(δE_xc/δ∇ρ)

        This requires computing functional derivatives w.r.t. both ρ and ∇ρ.

        Simplified implementation: use LDA potential as approximation.
        Full GGA potential requires solving additional equations.

        Reference: Theoretical framework in Martin (2004), Section 6.4.3
        """
        if grad_rho is None:
            return self.lda.potential(rho)

        # Simplified: Use LDA potential (full GGA potential more complex)
        # In production code, compute dF_x/ds and apply chain rule
        return self.lda.potential(rho)


# ============================================================================
# Hybrid Functionals
# ============================================================================

class HybridHSE06(XCFunctional):
    """
    HSE06 (Heyd-Scuseria-Ernzerhof) screened hybrid functional.

    Hybrid functionals mix a fraction of exact (Hartree-Fock) exchange
    with DFT exchange-correlation:

        E_xc^hybrid = α E_x^HF + (1-α) E_x^DFT + E_c^DFT

    HSE06 uses range-separated exchange:
        1/r = (1/r)^SR + (1/r)^LR
            = [erfc(ωr)]/r + [erf(ωr)]/r

    Only short-range (SR) HF exchange is included:
        E_xc^HSE = α E_x^HF,SR(ω) + (1-α) E_x^PBE,SR(ω) + E_x^PBE,LR(ω) + E_c^PBE

    Parameters:
    -----------
    - α = 0.25 (mixing parameter)
    - ω = 0.11 bohr⁻¹ (screening parameter)

    Advantages:
    -----------
    - Accurate band gaps (corrects DFT underestimation)
    - Reduced computational cost vs full hybrids (PBE0)
    - Better for solids than unscreened hybrids

    Applications:
    -------------
    - Semiconductors and insulators
    - Band structure calculations
    - Defect formation energies

    Reference: DOI: 10.1063/1.1564060
    """

    def __init__(self):
        super().__init__("Hybrid-HSE06")
        self.alpha = HSE_ALPHA  # 0.25
        self.omega = HSE_OMEGA  # 0.11 bohr⁻¹
        self.pbe = GGA_PBE()

    def energy_density(
        self,
        rho: np.ndarray,
        grad_rho: Optional[np.ndarray] = None,
        tau: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """
        HSE06 XC energy density.

        Note: Exact exchange computation requires wavefunctions,
        not just density. This is a simplified interface.

        In practice, HSE06 is implemented in the SCF loop where
        wavefunctions are available.

        Returns approximate energy using PBE.
        """
        # Simplified: return PBE energy (exact exchange needs wavefunctions)
        return self.pbe.energy_density(rho, grad_rho, tau)

    def potential(
        self,
        rho: np.ndarray,
        grad_rho: Optional[np.ndarray] = None,
        tau: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """HSE06 potential (simplified)."""
        return self.pbe.potential(rho, grad_rho, tau)


# ============================================================================
# meta-GGA
# ============================================================================

class MetaGGA_SCAN(XCFunctional):
    """
    SCAN (Strongly Constrained and Appropriately Normed) meta-GGA.

    SCAN is a state-of-the-art non-empirical functional that satisfies
    17 exact constraints, making it "Jacob's Ladder" rung 3.

    Beyond GGA, meta-GGA uses:
    - ρ(r): density
    - ∇ρ(r): density gradient
    - τ(r) = (1/2)Σ_i|∇ψ_i|²: kinetic energy density

    SCAN interpolates between different regimes:
    - Slowly varying density
    - Covalent bonding
    - Metallic bonding

    using α(r), a function that distinguishes these regions.

    Performance:
    ------------
    - Better lattice constants than PBE
    - Improved band gaps
    - Accurate atomization energies
    - Self-interaction error reduced

    Equations:
    ----------
    See Sun et al. (2015), Eqs. (4)-(10) for full mathematical form.
    Implementation requires careful numerical treatment of α(r).

    Reference: DOI: 10.1103/PhysRevLett.115.036402
    """

    def __init__(self):
        super().__init__("meta-GGA-SCAN")
        self.c1c = SCAN_C1C
        self.c2c = SCAN_C2C
        self.k1 = SCAN_K1
        self.lda = LDA_PZ()

    def _alpha_parameter(
        self,
        rho: np.ndarray,
        grad_rho: np.ndarray,
        tau: np.ndarray
    ) -> np.ndarray:
        """
        Compute α parameter for SCAN.

        α measures departure from single-orbital regime:
            α = (τ - τ_W) / τ_unif

        where:
        - τ: kinetic energy density
        - τ_W = |∇ρ|²/(8ρ): von Weizsäcker KED (single orbital)
        - τ_unif = (3/10)(3π²)^(2/3) ρ^(5/3): uniform gas KED

        Reference: SCAN paper, Eq. (5)
        """
        # τ_W = |∇ρ|²/(8ρ)
        grad_rho_norm = np.linalg.norm(grad_rho, axis=-1)
        tau_W = grad_rho_norm**2 / (8.0 * rho + 1e-12)

        # τ_unif = (3/10)(3π²)^(2/3) ρ^(5/3)
        tau_unif = (3.0/10.0) * (3.0 * np.pi**2)**(2.0/3.0) * rho**(5.0/3.0)

        # α = (τ - τ_W) / τ_unif
        alpha = (tau - tau_W) / (tau_unif + 1e-12)

        # Clip to physical range [0, 1]
        alpha = np.clip(alpha, 0.0, 1.0)

        return alpha

    def energy_density(
        self,
        rho: np.ndarray,
        grad_rho: Optional[np.ndarray] = None,
        tau: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """
        SCAN XC energy density.

        Requires ρ, ∇ρ, and τ.

        Simplified implementation (full SCAN is very complex).
        """
        if grad_rho is None or tau is None:
            # Fallback to LDA
            return self.lda.energy_density(rho)

        # Use LDA as base (full SCAN implementation is ~500 lines)
        epsilon_xc_lda = self.lda.energy_density(rho) / HARTREE_TO_EV

        # Compute α parameter
        alpha = self._alpha_parameter(rho, grad_rho, tau)

        # SCAN interpolation (simplified)
        # Full formula in Sun et al. (2015), Eqs. (6)-(8)
        epsilon_xc_scan = epsilon_xc_lda * (1.0 + self.k1 * alpha)

        return epsilon_xc_scan * HARTREE_TO_EV

    def potential(
        self,
        rho: np.ndarray,
        grad_rho: Optional[np.ndarray] = None,
        tau: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """SCAN XC potential (simplified)."""
        if grad_rho is None or tau is None:
            return self.lda.potential(rho)

        # Simplified: use LDA potential
        # Full SCAN potential requires complex derivatives
        return self.lda.potential(rho)


__all__ = [
    'XCFunctional',
    'LDA_PZ',
    'GGA_PBE',
    'HybridHSE06',
    'MetaGGA_SCAN',
]
