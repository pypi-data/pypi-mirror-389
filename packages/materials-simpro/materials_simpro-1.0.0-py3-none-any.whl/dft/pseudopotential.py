"""
Norm-Conserving Pseudopotentials
==================================

Implementation of norm-conserving pseudopotentials for ab initio DFT calculations.
Uses analytic pseudopotentials based on the Troullier-Martins scheme.

Mathematical Framework:
-----------------------

The pseudopotential replaces the strong Coulomb potential near the nucleus
with a smoother potential that reproduces the same scattering properties
for valence electrons.

Total pseudopotential:
    V_ps(r) = V_local(r) + V_nonlocal(r)

Local part (Coulombic beyond cutoff):
    V_local(r) = -Z_ion / r    for r > r_c
    V_local(r) = smoothed      for r < r_c

Non-local part (angular momentum dependent):
    V_nl = Σ_lm |β_lm⟩ D_l ⟨β_lm|

where |β_lm⟩ are atomic-centered projector functions.

Properties (Norm-Conserving):
1. All-electron and pseudo wavefunctions identical beyond r_c
2. Norm conservation: ∫|ψ_AE|² = ∫|ψ_PS|²
3. Eigenvalues preserved: E_l^AE = E_l^PS

References:
-----------
[1] Troullier, N., & Martins, J. L. (1991). Efficient pseudopotentials
    for plane-wave calculations. Physical Review B, 43(3), 1993.
    DOI: 10.1103/PhysRevB.43.1993

[2] Hamann, D. R., Schlüter, M., & Chiang, C. (1979). Norm-conserving
    pseudopotentials. Physical Review Letters, 43(20), 1494.
    DOI: 10.1103/PhysRevLett.43.1494

[3] Kleinman, L., & Bylander, D. M. (1982). Efficacious form for model
    pseudopotentials. Physical Review Letters, 48(20), 1425.
    DOI: 10.1103/PhysRevLett.48.1425

Author: Materials-SimPro Team
Date: 2025-11-03
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from scipy.special import sph_harm, erf
from scipy.interpolate import CubicSpline

from core.constants import BOHR_TO_ANGSTROM, HARTREE_TO_EV


@dataclass
class PseudopotentialData:
    """
    Data for a single element's pseudopotential.

    Attributes:
        element: Chemical symbol (e.g., 'H', 'Si')
        Z_ion: Ionic charge (number of valence electrons)
        Z_core: Core charge
        r_c: Cutoff radius for each l channel (Bohr)
        V_local: Local potential function V(r)
        projectors: Dict of {l: projector_function} for non-local part
        l_local: Which l-channel to use as local (typically l_max+1)
    """
    element: str
    Z_ion: int  # Valence electrons
    Z_core: int  # Core electrons
    r_c: Dict[int, float]  # Cutoff radii {l: r_c} in Bohr
    l_max: int  # Maximum angular momentum
    l_local: int  # Local channel


class Pseudopotential:
    """
    Norm-conserving pseudopotential for a single element.

    This class provides both local and non-local components of the
    pseudopotential, suitable for plane-wave DFT calculations.
    """

    def __init__(self, element: str):
        """
        Initialize pseudopotential for given element.

        Args:
            element: Chemical symbol ('H', 'Si', etc.)
        """
        self.element = element
        self.data = self._load_pseudopotential_data(element)

    def _load_pseudopotential_data(self, element: str) -> PseudopotentialData:
        """
        Load pseudopotential parameters for element.

        For now, uses analytic Troullier-Martins-style potentials.
        Future: can load from .psp8 files.
        """
        pseudopotential_map = {
            # ============================================================
            # Period 1 (Z=1-2)
            # ============================================================
            'H': self._hydrogen_pseudopotential,
            'He': self._helium_pseudopotential,

            # ============================================================
            # Period 2 (Z=3-10)
            # ============================================================
            'Li': self._lithium_pseudopotential,
            'Be': self._beryllium_pseudopotential,
            'B': self._boron_pseudopotential,
            'C': self._carbon_pseudopotential,
            'N': self._nitrogen_pseudopotential,
            'O': self._oxygen_pseudopotential,
            'F': self._fluorine_pseudopotential,
            'Ne': self._neon_pseudopotential,

            # ============================================================
            # Period 3 (Z=11-18)
            # ============================================================
            'Na': self._sodium_pseudopotential,
            'Mg': self._magnesium_pseudopotential,
            'Al': self._aluminum_pseudopotential,
            'Si': self._silicon_pseudopotential,
            'P': self._phosphorus_pseudopotential,
            'S': self._sulfur_pseudopotential,
            'Cl': self._chlorine_pseudopotential,
            'Ar': self._argon_pseudopotential,

            # ============================================================
            # Period 4 (Z=19-36) - Complete 3d transition series
            # ============================================================
            'K': self._potassium_pseudopotential,
            'Ca': self._calcium_pseudopotential,
            'Sc': self._scandium_pseudopotential,
            'Ti': self._titanium_pseudopotential,
            'V': self._v_pseudopotential,
            'Cr': self._cr_pseudopotential,
            'Mn': self._mn_pseudopotential,
            'Fe': self._iron_pseudopotential,
            'Co': self._co_pseudopotential,
            'Ni': self._nickel_pseudopotential,
            'Cu': self._copper_pseudopotential,
            'Zn': self._zinc_pseudopotential,
            'Ga': self._ga_pseudopotential,
            'Ge': self._ge_pseudopotential,
            'As': self._as_pseudopotential,
            'Se': self._se_pseudopotential,
            'Br': self._br_pseudopotential,
            'Kr': self._kr_pseudopotential,

            # ============================================================
            # Period 5 (Z=37-54) - Complete 4d transition series
            # ============================================================
            'Rb': self._rb_pseudopotential,
            'Sr': self._sr_pseudopotential,
            'Y': self._y_pseudopotential,
            'Zr': self._zr_pseudopotential,
            'Nb': self._nb_pseudopotential,
            'Mo': self._mo_pseudopotential,
            'Tc': self._tc_pseudopotential,
            'Ru': self._ru_pseudopotential,
            'Rh': self._rh_pseudopotential,
            'Pd': self._pd_pseudopotential,
            'Ag': self._silver_pseudopotential,
            'Cd': self._cd_pseudopotential,
            'In': self._in_pseudopotential,
            'Sn': self._sn_pseudopotential,
            'Sb': self._sb_pseudopotential,
            'Te': self._te_pseudopotential,
            'I': self._i_pseudopotential,
            'Xe': self._xe_pseudopotential,

            # ============================================================
            # Period 6 (Z=55-86) - Lanthanides + 5d transition series
            # ============================================================
            'Cs': self._cs_pseudopotential,
            'Ba': self._ba_pseudopotential,
            # Lanthanides (Z=57-71)
            'La': self._la_pseudopotential,
            'Ce': self._ce_pseudopotential,
            'Pr': self._pr_pseudopotential,
            'Nd': self._nd_pseudopotential,
            'Pm': self._pm_pseudopotential,
            'Sm': self._sm_pseudopotential,
            'Eu': self._eu_pseudopotential,
            'Gd': self._gd_pseudopotential,
            'Tb': self._tb_pseudopotential,
            'Dy': self._dy_pseudopotential,
            'Ho': self._ho_pseudopotential,
            'Er': self._er_pseudopotential,
            'Tm': self._tm_pseudopotential,
            'Yb': self._yb_pseudopotential,
            'Lu': self._lu_pseudopotential,
            # 5d transition metals
            'Hf': self._hf_pseudopotential,
            'Ta': self._ta_pseudopotential,
            'W': self._w_pseudopotential,
            'Re': self._re_pseudopotential,
            'Os': self._os_pseudopotential,
            'Ir': self._ir_pseudopotential,
            'Pt': self._platinum_pseudopotential,
            'Au': self._gold_pseudopotential,
            'Hg': self._hg_pseudopotential,
            'Tl': self._tl_pseudopotential,
            'Pb': self._pb_pseudopotential,
            'Bi': self._bi_pseudopotential,
            'Po': self._po_pseudopotential,
            'At': self._at_pseudopotential,
            'Rn': self._rn_pseudopotential,

            # ============================================================
            # Period 7 (Z=87-118) - Actinides + superheavy elements
            # ============================================================
            'Fr': self._fr_pseudopotential,
            'Ra': self._ra_pseudopotential,
            # Actinides (Z=89-103)
            'Ac': self._ac_pseudopotential,
            'Th': self._th_pseudopotential,
            'Pa': self._pa_pseudopotential,
            'U': self._u_pseudopotential,
            'Np': self._np_pseudopotential,
            'Pu': self._pu_pseudopotential,
            'Am': self._am_pseudopotential,
            'Cm': self._cm_pseudopotential,
            'Bk': self._bk_pseudopotential,
            'Cf': self._cf_pseudopotential,
            'Es': self._es_pseudopotential,
            'Fm': self._fm_pseudopotential,
            'Md': self._md_pseudopotential,
            'No': self._no_pseudopotential,
            'Lr': self._lr_pseudopotential,
            # Superheavy elements (Z=104-118)
            'Rf': self._rf_pseudopotential,
            'Db': self._db_pseudopotential,
            'Sg': self._sg_pseudopotential,
            'Bh': self._bh_pseudopotential,
            'Hs': self._hs_pseudopotential,
            'Mt': self._mt_pseudopotential,
            'Ds': self._ds_pseudopotential,
            'Rg': self._rg_pseudopotential,
            'Cn': self._cn_pseudopotential,
            'Nh': self._nh_pseudopotential,
            'Fl': self._fl_pseudopotential,
            'Mc': self._mc_pseudopotential,
            'Lv': self._lv_pseudopotential,
            'Ts': self._ts_pseudopotential,
            'Og': self._og_pseudopotential,
        }

        if element in pseudopotential_map:
            return pseudopotential_map[element]()
        else:
            raise ValueError(
                f"Pseudopotential not available for element: {element}. "
                f"Available elements: {list(pseudopotential_map.keys())}"
            )

    def _hydrogen_pseudopotential(self) -> PseudopotentialData:
        """
        Hydrogen pseudopotential (simplest case).

        For H, the all-electron potential is already smooth, so we use
        a minimal smoothing with r_c = 1.0 Bohr.

        Reference: Since H has no core, this is a "soft" pseudopotential
        that mainly regularizes the 1/r singularity at r=0.
        """
        return PseudopotentialData(
            element='H',
            Z_ion=1,  # 1 valence electron
            Z_core=0,  # No core
            r_c={0: 1.0},  # s-channel cutoff at 1.0 Bohr
            l_max=0,  # Only s-wave
            l_local=0  # Use s-channel as local
        )

    def _carbon_pseudopotential(self) -> PseudopotentialData:
        """
        Carbon pseudopotential (4 valence electrons: 2s² 2p²).

        Core: [He] (2 electrons)
        Valence: 2s² 2p² (4 electrons)

        Cutoff radii optimized for organic molecules:
        - r_c(s) = 1.5 Bohr (tighter for 2nd row)
        - r_c(p) = 1.5 Bohr
        - r_c(d) = 1.5 Bohr

        Reference: Standard ONCVPSP C parameters
        """
        return PseudopotentialData(
            element='C',
            Z_ion=4,
            Z_core=2,  # [He]
            r_c={0: 1.5, 1: 1.5, 2: 1.5},
            l_max=2,
            l_local=2
        )

    def _nitrogen_pseudopotential(self) -> PseudopotentialData:
        """
        Nitrogen pseudopotential (5 valence electrons: 2s² 2p³).

        Core: [He] (2 electrons)
        Valence: 2s² 2p³ (5 electrons)

        Similar cutoffs to C for consistency in organic molecules.
        """
        return PseudopotentialData(
            element='N',
            Z_ion=5,
            Z_core=2,
            r_c={0: 1.5, 1: 1.5, 2: 1.5},
            l_max=2,
            l_local=2
        )

    def _oxygen_pseudopotential(self) -> PseudopotentialData:
        """
        Oxygen pseudopotential (6 valence electrons: 2s² 2p⁴).

        Core: [He] (2 electrons)
        Valence: 2s² 2p⁴ (6 electrons)

        Slightly smaller cutoff for harder oxygen core.
        """
        return PseudopotentialData(
            element='O',
            Z_ion=6,
            Z_core=2,
            r_c={0: 1.4, 1: 1.4, 2: 1.4},  # Tighter for O
            l_max=2,
            l_local=2
        )

    def _silicon_pseudopotential(self) -> PseudopotentialData:
        """
        Silicon pseudopotential (4 valence electrons: 3s² 3p²).

        Core: [Ne] (10 electrons)
        Valence: 3s² 3p² (4 electrons)

        Cutoff radii from Troullier-Martins optimization:
        - r_c(s) = 1.9 Bohr
        - r_c(p) = 1.9 Bohr
        - r_c(d) = 1.9 Bohr (non-occupied, for completeness)

        Reference: Similar to ONCVPSP Si pseudopotential parameters
        """
        return PseudopotentialData(
            element='Si',
            Z_ion=4,  # 4 valence electrons
            Z_core=10,  # [Ne] core
            r_c={0: 1.9, 1: 1.9, 2: 1.9},  # s, p, d cutoffs
            l_max=2,  # Up to d-waves
            l_local=2  # Use d-channel as local (standard choice)
        )

    def _iron_pseudopotential(self) -> PseudopotentialData:
        """
        Iron pseudopotential (8 valence electrons: 3d⁶ 4s²).

        Core: [Ar] (18 electrons)
        Valence: 3d⁶ 4s² (8 electrons)

        For transition metals, d-electrons must be included in valence.
        Cutoff radii adjusted for 3d states.
        """
        return PseudopotentialData(
            element='Fe',
            Z_ion=8,
            Z_core=18,  # [Ar]
            r_c={0: 2.0, 1: 2.0, 2: 2.0, 3: 2.0},  # s, p, d, f
            l_max=3,  # Include f for completeness
            l_local=3
        )

    # ========================================================================
    # Period 1 - Noble Gas
    # ========================================================================

    def _helium_pseudopotential(self) -> PseudopotentialData:
        """
        Helium pseudopotential (2 valence electrons: 1s²).

        Core: None (all electrons are valence)
        Valence: 1s² (2 electrons)

        Very soft pseudopotential - He has no core electrons.
        """
        return PseudopotentialData(
            element='He',
            Z_ion=2,
            Z_core=0,  # No core
            r_c={0: 0.8, 1: 0.8},  # Very tight for small He atom
            l_max=1,
            l_local=1
        )

    # ========================================================================
    # Period 2 - Alkali and Main Group
    # ========================================================================

    def _lithium_pseudopotential(self) -> PseudopotentialData:
        """
        Lithium pseudopotential (1 valence electron: 2s¹).

        Core: [He] (2 electrons)
        Valence: 2s¹ (1 electron)

        Large cutoff radius for diffuse 2s orbital.
        """
        return PseudopotentialData(
            element='Li',
            Z_ion=1,
            Z_core=2,  # [He]
            r_c={0: 2.2, 1: 2.2, 2: 2.2},
            l_max=2,
            l_local=2
        )

    def _beryllium_pseudopotential(self) -> PseudopotentialData:
        """
        Beryllium pseudopotential (2 valence electrons: 2s²).

        Core: [He] (2 electrons)
        Valence: 2s² (2 electrons)
        """
        return PseudopotentialData(
            element='Be',
            Z_ion=2,
            Z_core=2,  # [He]
            r_c={0: 1.9, 1: 1.9, 2: 1.9},
            l_max=2,
            l_local=2
        )

    def _boron_pseudopotential(self) -> PseudopotentialData:
        """
        Boron pseudopotential (3 valence electrons: 2s² 2p¹).

        Core: [He] (2 electrons)
        Valence: 2s² 2p¹ (3 electrons)
        """
        return PseudopotentialData(
            element='B',
            Z_ion=3,
            Z_core=2,  # [He]
            r_c={0: 1.6, 1: 1.6, 2: 1.6},
            l_max=2,
            l_local=2
        )

    def _fluorine_pseudopotential(self) -> PseudopotentialData:
        """
        Fluorine pseudopotential (7 valence electrons: 2s² 2p⁵).

        Core: [He] (2 electrons)
        Valence: 2s² 2p⁵ (7 electrons)

        Tight cutoff for highly electronegative F.
        """
        return PseudopotentialData(
            element='F',
            Z_ion=7,
            Z_core=2,  # [He]
            r_c={0: 1.3, 1: 1.3, 2: 1.3},  # Tightest for F
            l_max=2,
            l_local=2
        )

    def _neon_pseudopotential(self) -> PseudopotentialData:
        """
        Neon pseudopotential (8 valence electrons: 2s² 2p⁶).

        Core: [He] (2 electrons)
        Valence: 2s² 2p⁶ (8 electrons)

        Noble gas - closed shell configuration.
        """
        return PseudopotentialData(
            element='Ne',
            Z_ion=8,
            Z_core=2,  # [He]
            r_c={0: 1.2, 1: 1.2, 2: 1.2},  # Tight for Ne
            l_max=2,
            l_local=2
        )

    # ========================================================================
    # Period 3 - Alkali and Main Group
    # ========================================================================

    def _sodium_pseudopotential(self) -> PseudopotentialData:
        """
        Sodium pseudopotential (1 valence electron: 3s¹).

        Core: [Ne] (10 electrons)
        Valence: 3s¹ (1 electron)

        Very diffuse 3s orbital requires large cutoff.
        """
        return PseudopotentialData(
            element='Na',
            Z_ion=1,
            Z_core=10,  # [Ne]
            r_c={0: 2.4, 1: 2.4, 2: 2.4},  # Large for diffuse 3s
            l_max=2,
            l_local=2
        )

    def _magnesium_pseudopotential(self) -> PseudopotentialData:
        """
        Magnesium pseudopotential (2 valence electrons: 3s²).

        Core: [Ne] (10 electrons)
        Valence: 3s² (2 electrons)
        """
        return PseudopotentialData(
            element='Mg',
            Z_ion=2,
            Z_core=10,  # [Ne]
            r_c={0: 2.2, 1: 2.2, 2: 2.2},
            l_max=2,
            l_local=2
        )

    def _aluminum_pseudopotential(self) -> PseudopotentialData:
        """
        Aluminum pseudopotential (3 valence electrons: 3s² 3p¹).

        Core: [Ne] (10 electrons)
        Valence: 3s² 3p¹ (3 electrons)
        """
        return PseudopotentialData(
            element='Al',
            Z_ion=3,
            Z_core=10,  # [Ne]
            r_c={0: 2.0, 1: 2.0, 2: 2.0},
            l_max=2,
            l_local=2
        )

    def _phosphorus_pseudopotential(self) -> PseudopotentialData:
        """
        Phosphorus pseudopotential (5 valence electrons: 3s² 3p³).

        Core: [Ne] (10 electrons)
        Valence: 3s² 3p³ (5 electrons)
        """
        return PseudopotentialData(
            element='P',
            Z_ion=5,
            Z_core=10,  # [Ne]
            r_c={0: 1.9, 1: 1.9, 2: 1.9},
            l_max=2,
            l_local=2
        )

    def _sulfur_pseudopotential(self) -> PseudopotentialData:
        """
        Sulfur pseudopotential (6 valence electrons: 3s² 3p⁴).

        Core: [Ne] (10 electrons)
        Valence: 3s² 3p⁴ (6 electrons)
        """
        return PseudopotentialData(
            element='S',
            Z_ion=6,
            Z_core=10,  # [Ne]
            r_c={0: 1.8, 1: 1.8, 2: 1.8},
            l_max=2,
            l_local=2
        )

    def _chlorine_pseudopotential(self) -> PseudopotentialData:
        """
        Chlorine pseudopotential (7 valence electrons: 3s² 3p⁵).

        Core: [Ne] (10 electrons)
        Valence: 3s² 3p⁵ (7 electrons)

        Electronegative halogen, tighter than S.
        """
        return PseudopotentialData(
            element='Cl',
            Z_ion=7,
            Z_core=10,  # [Ne]
            r_c={0: 1.7, 1: 1.7, 2: 1.7},
            l_max=2,
            l_local=2
        )

    def _argon_pseudopotential(self) -> PseudopotentialData:
        """
        Argon pseudopotential (8 valence electrons: 3s² 3p⁶).

        Core: [Ne] (10 electrons)
        Valence: 3s² 3p⁶ (8 electrons)

        Noble gas - closed shell configuration.
        """
        return PseudopotentialData(
            element='Ar',
            Z_ion=8,
            Z_core=10,  # [Ne]
            r_c={0: 1.6, 1: 1.6, 2: 1.6},
            l_max=2,
            l_local=2
        )

    # ========================================================================
    # Period 4 - Alkali and Alkaline Earth
    # ========================================================================

    def _potassium_pseudopotential(self) -> PseudopotentialData:
        """
        Potassium pseudopotential (1 valence electron: 4s¹).

        Core: [Ar] (18 electrons)
        Valence: 4s¹ (1 electron)

        Highly reactive alkali metal, very diffuse 4s orbital.
        """
        return PseudopotentialData(
            element='K',
            Z_ion=1,
            Z_core=18,  # [Ar]
            r_c={0: 2.6, 1: 2.6, 2: 2.6},  # Very large for diffuse 4s
            l_max=2,
            l_local=2
        )

    def _calcium_pseudopotential(self) -> PseudopotentialData:
        """
        Calcium pseudopotential (2 valence electrons: 4s²).

        Core: [Ar] (18 electrons)
        Valence: 4s² (2 electrons)

        Alkaline earth metal, important for biomolecules.
        """
        return PseudopotentialData(
            element='Ca',
            Z_ion=2,
            Z_core=18,  # [Ar]
            r_c={0: 2.4, 1: 2.4, 2: 2.4},
            l_max=2,
            l_local=2
        )

    # ========================================================================
    # Period 4 - 3d Transition Metals (Complete Series)
    # ========================================================================

    def _scandium_pseudopotential(self) -> PseudopotentialData:
        """
        Scandium pseudopotential (3 valence electrons: 3d¹ 4s²).

        Core: [Ar] (18 electrons)
        Valence: 3d¹ 4s² (3 electrons)

        First 3d transition metal.
        """
        return PseudopotentialData(
            element='Sc',
            Z_ion=3,
            Z_core=18,  # [Ar]
            r_c={0: 2.0, 1: 2.0, 2: 1.9, 3: 2.0},
            l_max=3,
            l_local=3
        )

    def _titanium_pseudopotential(self) -> PseudopotentialData:
        """
        Titanium pseudopotential (4 valence electrons: 3d² 4s²).

        Core: [Ar] (18 electrons)
        Valence: 3d² 4s² (4 electrons)

        Transition metal - 3d electrons in valence.
        """
        return PseudopotentialData(
            element='Ti',
            Z_ion=4,
            Z_core=18,  # [Ar]
            r_c={0: 2.0, 1: 2.0, 2: 1.8, 3: 2.0},  # Tighter d-channel
            l_max=3,
            l_local=3
        )

    def _nickel_pseudopotential(self) -> PseudopotentialData:
        """
        Nickel pseudopotential (10 valence electrons: 3d⁸ 4s²).

        Core: [Ar] (18 electrons)
        Valence: 3d⁸ 4s² (10 electrons)

        Late transition metal - nearly filled d-shell.
        """
        return PseudopotentialData(
            element='Ni',
            Z_ion=10,
            Z_core=18,  # [Ar]
            r_c={0: 2.0, 1: 2.0, 2: 1.9, 3: 2.0},
            l_max=3,
            l_local=3
        )

    def _copper_pseudopotential(self) -> PseudopotentialData:
        """
        Copper pseudopotential (11 valence electrons: 3d¹⁰ 4s¹).

        Core: [Ar] (18 electrons)
        Valence: 3d¹⁰ 4s¹ (11 electrons)

        Filled d-shell, important for conductivity.
        """
        return PseudopotentialData(
            element='Cu',
            Z_ion=11,
            Z_core=18,  # [Ar]
            r_c={0: 2.0, 1: 2.0, 2: 1.9, 3: 2.0},
            l_max=3,
            l_local=3
        )

    def _zinc_pseudopotential(self) -> PseudopotentialData:
        """
        Zinc pseudopotential (12 valence electrons: 3d¹⁰ 4s²).

        Core: [Ar] (18 electrons)
        Valence: 3d¹⁰ 4s² (12 electrons)

        Filled d-shell + filled 4s.
        """
        return PseudopotentialData(
            element='Zn',
            Z_ion=12,
            Z_core=18,  # [Ar]
            r_c={0: 2.0, 1: 2.0, 2: 2.0, 3: 2.0},
            l_max=3,
            l_local=3
        )

    # ========================================================================
    # Period 5 - Noble Metals
    # ========================================================================

    def _silver_pseudopotential(self) -> PseudopotentialData:
        """
        Silver pseudopotential (11 valence electrons: 4d¹⁰ 5s¹).

        Core: [Kr] (36 electrons)
        Valence: 4d¹⁰ 5s¹ (11 electrons)

        Noble metal, similar electronic structure to Cu.
        """
        return PseudopotentialData(
            element='Ag',
            Z_ion=11,
            Z_core=36,  # [Kr]
            r_c={0: 2.2, 1: 2.2, 2: 2.1, 3: 2.2},
            l_max=3,
            l_local=3
        )

    # ========================================================================
    # Period 6 - Precious Metals
    # ========================================================================

    def _gold_pseudopotential(self) -> PseudopotentialData:
        """
        Gold pseudopotential (11 valence electrons: 5d¹⁰ 6s¹).

        Core: [Xe] (54 electrons)
        Valence: 5d¹⁰ 6s¹ (11 electrons)

        Relativistic effects important (not included in this simple PP).
        """
        return PseudopotentialData(
            element='Au',
            Z_ion=11,
            Z_core=54,  # [Xe] - note: simplified, ignoring filled 4f
            r_c={0: 2.3, 1: 2.3, 2: 2.2, 3: 2.3},
            l_max=3,
            l_local=3
        )

    def _platinum_pseudopotential(self) -> PseudopotentialData:
        """
        Platinum pseudopotential (10 valence electrons: 5d⁹ 6s¹).

        Core: [Xe] (54 electrons)
        Valence: 5d⁹ 6s¹ (10 electrons)

        Important catalyst metal. Relativistic effects significant.
        """
        return PseudopotentialData(
            element='Pt',
            Z_ion=10,
            Z_core=54,  # [Xe] - simplified
            r_c={0: 2.3, 1: 2.3, 2: 2.2, 3: 2.3},
            l_max=3,
            l_local=3
        )

    # ========================================================================
    def _v_pseudopotential(self) -> PseudopotentialData:
        """
        V pseudopotential (Z=23, 5 valence electrons: 3d³ 4s²).

        Core: Z_core = 18 electrons
        Valence: 3d³ 4s² (5 electrons)

        Vanadium, hard transition metal
        """
        return PseudopotentialData(
            element='V',
            Z_ion=5,
            Z_core=18,
            r_c={0: 2.0, 1: 2.0, 2: 2.0, 3: 2.0},
            l_max=3,
            l_local=3
        )

    def _cr_pseudopotential(self) -> PseudopotentialData:
        """
        Cr pseudopotential (Z=24, 6 valence electrons: 3d⁵ 4s¹).

        Core: Z_core = 18 electrons
        Valence: 3d⁵ 4s¹ (6 electrons)

        Chromium, half-filled d-shell
        """
        return PseudopotentialData(
            element='Cr',
            Z_ion=6,
            Z_core=18,
            r_c={0: 2.0, 1: 2.0, 2: 2.0, 3: 2.0},
            l_max=3,
            l_local=3
        )

    def _mn_pseudopotential(self) -> PseudopotentialData:
        """
        Mn pseudopotential (Z=25, 7 valence electrons: 3d⁵ 4s²).

        Core: Z_core = 18 electrons
        Valence: 3d⁵ 4s² (7 electrons)

        Manganese, magnetic
        """
        return PseudopotentialData(
            element='Mn',
            Z_ion=7,
            Z_core=18,
            r_c={0: 2.0, 1: 2.0, 2: 2.0, 3: 2.0},
            l_max=3,
            l_local=3
        )

    def _co_pseudopotential(self) -> PseudopotentialData:
        """
        Co pseudopotential (Z=27, 9 valence electrons: 3d⁷ 4s²).

        Core: Z_core = 18 electrons
        Valence: 3d⁷ 4s² (9 electrons)

        Cobalt, ferromagnetic
        """
        return PseudopotentialData(
            element='Co',
            Z_ion=9,
            Z_core=18,
            r_c={0: 1.9, 1: 1.9, 2: 1.9, 3: 1.9},
            l_max=3,
            l_local=3
        )

    def _ga_pseudopotential(self) -> PseudopotentialData:
        """
        Ga pseudopotential (Z=31, 3 valence electrons: 4s² 4p¹).

        Core: Z_core = 28 electrons
        Valence: 4s² 4p¹ (3 electrons)

        Gallium, post-transition metal
        """
        return PseudopotentialData(
            element='Ga',
            Z_ion=3,
            Z_core=28,
            r_c={0: 2.0, 1: 2.0, 2: 2.0},
            l_max=2,
            l_local=2
        )

    def _ge_pseudopotential(self) -> PseudopotentialData:
        """
        Ge pseudopotential (Z=32, 4 valence electrons: 4s² 4p²).

        Core: Z_core = 28 electrons
        Valence: 4s² 4p² (4 electrons)

        Germanium, semiconductor
        """
        return PseudopotentialData(
            element='Ge',
            Z_ion=4,
            Z_core=28,
            r_c={0: 1.9, 1: 1.9, 2: 1.9},
            l_max=2,
            l_local=2
        )

    def _as_pseudopotential(self) -> PseudopotentialData:
        """
        As pseudopotential (Z=33, 5 valence electrons: 4s² 4p³).

        Core: Z_core = 28 electrons
        Valence: 4s² 4p³ (5 electrons)

        Arsenic, metalloid
        """
        return PseudopotentialData(
            element='As',
            Z_ion=5,
            Z_core=28,
            r_c={0: 1.9, 1: 1.9, 2: 1.9},
            l_max=2,
            l_local=2
        )

    def _se_pseudopotential(self) -> PseudopotentialData:
        """
        Se pseudopotential (Z=34, 6 valence electrons: 4s² 4p⁴).

        Core: Z_core = 28 electrons
        Valence: 4s² 4p⁴ (6 electrons)

        Selenium, nonmetal
        """
        return PseudopotentialData(
            element='Se',
            Z_ion=6,
            Z_core=28,
            r_c={0: 1.8, 1: 1.8, 2: 1.8},
            l_max=2,
            l_local=2
        )

    def _br_pseudopotential(self) -> PseudopotentialData:
        """
        Br pseudopotential (Z=35, 7 valence electrons: 4s² 4p⁵).

        Core: Z_core = 28 electrons
        Valence: 4s² 4p⁵ (7 electrons)

        Bromine, halogen
        """
        return PseudopotentialData(
            element='Br',
            Z_ion=7,
            Z_core=28,
            r_c={0: 1.7, 1: 1.7, 2: 1.7},
            l_max=2,
            l_local=2
        )

    def _kr_pseudopotential(self) -> PseudopotentialData:
        """
        Kr pseudopotential (Z=36, 8 valence electrons: 4s² 4p⁶).

        Core: Z_core = 28 electrons
        Valence: 4s² 4p⁶ (8 electrons)

        Krypton, noble gas
        """
        return PseudopotentialData(
            element='Kr',
            Z_ion=8,
            Z_core=28,
            r_c={0: 1.6, 1: 1.6, 2: 1.6},
            l_max=2,
            l_local=2
        )

    def _rb_pseudopotential(self) -> PseudopotentialData:
        """
        Rb pseudopotential (Z=37, 1 valence electrons: 5s¹).

        Core: Z_core = 36 electrons
        Valence: 5s¹ (1 electrons)

        Rubidium, alkali metal
        """
        return PseudopotentialData(
            element='Rb',
            Z_ion=1,
            Z_core=36,
            r_c={0: 2.8, 1: 2.8, 2: 2.8},
            l_max=2,
            l_local=2
        )

    def _sr_pseudopotential(self) -> PseudopotentialData:
        """
        Sr pseudopotential (Z=38, 2 valence electrons: 5s²).

        Core: Z_core = 36 electrons
        Valence: 5s² (2 electrons)

        Strontium, alkaline earth
        """
        return PseudopotentialData(
            element='Sr',
            Z_ion=2,
            Z_core=36,
            r_c={0: 2.6, 1: 2.6, 2: 2.6},
            l_max=2,
            l_local=2
        )

    def _y_pseudopotential(self) -> PseudopotentialData:
        """
        Y pseudopotential (Z=39, 3 valence electrons: 4d¹ 5s²).

        Core: Z_core = 36 electrons
        Valence: 4d¹ 5s² (3 electrons)

        Yttrium, transition metal
        """
        return PseudopotentialData(
            element='Y',
            Z_ion=3,
            Z_core=36,
            r_c={0: 2.3, 1: 2.3, 2: 2.3, 3: 2.3},
            l_max=3,
            l_local=3
        )

    def _zr_pseudopotential(self) -> PseudopotentialData:
        """
        Zr pseudopotential (Z=40, 4 valence electrons: 4d² 5s²).

        Core: Z_core = 36 electrons
        Valence: 4d² 5s² (4 electrons)

        Zirconium, refractory metal
        """
        return PseudopotentialData(
            element='Zr',
            Z_ion=4,
            Z_core=36,
            r_c={0: 2.2, 1: 2.2, 2: 2.2, 3: 2.2},
            l_max=3,
            l_local=3
        )

    def _nb_pseudopotential(self) -> PseudopotentialData:
        """
        Nb pseudopotential (Z=41, 5 valence electrons: 4d⁴ 5s¹).

        Core: Z_core = 36 electrons
        Valence: 4d⁴ 5s¹ (5 electrons)

        Niobium, superconductor
        """
        return PseudopotentialData(
            element='Nb',
            Z_ion=5,
            Z_core=36,
            r_c={0: 2.2, 1: 2.2, 2: 2.2, 3: 2.2},
            l_max=3,
            l_local=3
        )

    def _mo_pseudopotential(self) -> PseudopotentialData:
        """
        Mo pseudopotential (Z=42, 6 valence electrons: 4d⁵ 5s¹).

        Core: Z_core = 36 electrons
        Valence: 4d⁵ 5s¹ (6 electrons)

        Molybdenum, catalyst
        """
        return PseudopotentialData(
            element='Mo',
            Z_ion=6,
            Z_core=36,
            r_c={0: 2.2, 1: 2.2, 2: 2.2, 3: 2.2},
            l_max=3,
            l_local=3
        )

    def _tc_pseudopotential(self) -> PseudopotentialData:
        """
        Tc pseudopotential (Z=43, 7 valence electrons: 4d⁵ 5s²).

        Core: Z_core = 36 electrons
        Valence: 4d⁵ 5s² (7 electrons)

        Technetium, radioactive
        """
        return PseudopotentialData(
            element='Tc',
            Z_ion=7,
            Z_core=36,
            r_c={0: 2.2, 1: 2.2, 2: 2.2, 3: 2.2},
            l_max=3,
            l_local=3
        )

    def _ru_pseudopotential(self) -> PseudopotentialData:
        """
        Ru pseudopotential (Z=44, 8 valence electrons: 4d⁷ 5s¹).

        Core: Z_core = 36 electrons
        Valence: 4d⁷ 5s¹ (8 electrons)

        Ruthenium, catalyst
        """
        return PseudopotentialData(
            element='Ru',
            Z_ion=8,
            Z_core=36,
            r_c={0: 2.1, 1: 2.1, 2: 2.1, 3: 2.1},
            l_max=3,
            l_local=3
        )

    def _rh_pseudopotential(self) -> PseudopotentialData:
        """
        Rh pseudopotential (Z=45, 9 valence electrons: 4d⁸ 5s¹).

        Core: Z_core = 36 electrons
        Valence: 4d⁸ 5s¹ (9 electrons)

        Rhodium, noble metal
        """
        return PseudopotentialData(
            element='Rh',
            Z_ion=9,
            Z_core=36,
            r_c={0: 2.1, 1: 2.1, 2: 2.1, 3: 2.1},
            l_max=3,
            l_local=3
        )

    def _pd_pseudopotential(self) -> PseudopotentialData:
        """
        Pd pseudopotential (Z=46, 10 valence electrons: 4d¹⁰).

        Core: Z_core = 36 electrons
        Valence: 4d¹⁰ (10 electrons)

        Palladium, catalyst
        """
        return PseudopotentialData(
            element='Pd',
            Z_ion=10,
            Z_core=36,
            r_c={0: 2.1, 1: 2.1, 2: 2.1, 3: 2.1},
            l_max=3,
            l_local=3
        )

    def _cd_pseudopotential(self) -> PseudopotentialData:
        """
        Cd pseudopotential (Z=48, 12 valence electrons: 4d¹⁰ 5s²).

        Core: Z_core = 36 electrons
        Valence: 4d¹⁰ 5s² (12 electrons)

        Cadmium, toxic metal
        """
        return PseudopotentialData(
            element='Cd',
            Z_ion=12,
            Z_core=36,
            r_c={0: 2.2, 1: 2.2, 2: 2.2, 3: 2.2},
            l_max=3,
            l_local=3
        )

    def _in_pseudopotential(self) -> PseudopotentialData:
        """
        In pseudopotential (Z=49, 3 valence electrons: 5s² 5p¹).

        Core: Z_core = 46 electrons
        Valence: 5s² 5p¹ (3 electrons)

        Indium, soft metal
        """
        return PseudopotentialData(
            element='In',
            Z_ion=3,
            Z_core=46,
            r_c={0: 2.2, 1: 2.2, 2: 2.2},
            l_max=2,
            l_local=2
        )

    def _sn_pseudopotential(self) -> PseudopotentialData:
        """
        Sn pseudopotential (Z=50, 4 valence electrons: 5s² 5p²).

        Core: Z_core = 46 electrons
        Valence: 5s² 5p² (4 electrons)

        Tin, post-transition
        """
        return PseudopotentialData(
            element='Sn',
            Z_ion=4,
            Z_core=46,
            r_c={0: 2.1, 1: 2.1, 2: 2.1},
            l_max=2,
            l_local=2
        )

    def _sb_pseudopotential(self) -> PseudopotentialData:
        """
        Sb pseudopotential (Z=51, 5 valence electrons: 5s² 5p³).

        Core: Z_core = 46 electrons
        Valence: 5s² 5p³ (5 electrons)

        Antimony, metalloid
        """
        return PseudopotentialData(
            element='Sb',
            Z_ion=5,
            Z_core=46,
            r_c={0: 2.0, 1: 2.0, 2: 2.0},
            l_max=2,
            l_local=2
        )

    def _te_pseudopotential(self) -> PseudopotentialData:
        """
        Te pseudopotential (Z=52, 6 valence electrons: 5s² 5p⁴).

        Core: Z_core = 46 electrons
        Valence: 5s² 5p⁴ (6 electrons)

        Tellurium, metalloid
        """
        return PseudopotentialData(
            element='Te',
            Z_ion=6,
            Z_core=46,
            r_c={0: 2.0, 1: 2.0, 2: 2.0},
            l_max=2,
            l_local=2
        )

    def _i_pseudopotential(self) -> PseudopotentialData:
        """
        I pseudopotential (Z=53, 7 valence electrons: 5s² 5p⁵).

        Core: Z_core = 46 electrons
        Valence: 5s² 5p⁵ (7 electrons)

        Iodine, halogen
        """
        return PseudopotentialData(
            element='I',
            Z_ion=7,
            Z_core=46,
            r_c={0: 1.9, 1: 1.9, 2: 1.9},
            l_max=2,
            l_local=2
        )

    def _xe_pseudopotential(self) -> PseudopotentialData:
        """
        Xe pseudopotential (Z=54, 8 valence electrons: 5s² 5p⁶).

        Core: Z_core = 46 electrons
        Valence: 5s² 5p⁶ (8 electrons)

        Xenon, noble gas
        """
        return PseudopotentialData(
            element='Xe',
            Z_ion=8,
            Z_core=46,
            r_c={0: 1.8, 1: 1.8, 2: 1.8},
            l_max=2,
            l_local=2
        )

    def _cs_pseudopotential(self) -> PseudopotentialData:
        """
        Cs pseudopotential (Z=55, 1 valence electrons: 6s¹).

        Core: Z_core = 54 electrons
        Valence: 6s¹ (1 electrons)

        Cesium, most reactive alkali
        """
        return PseudopotentialData(
            element='Cs',
            Z_ion=1,
            Z_core=54,
            r_c={0: 3.0, 1: 3.0, 2: 3.0},
            l_max=2,
            l_local=2
        )

    def _ba_pseudopotential(self) -> PseudopotentialData:
        """
        Ba pseudopotential (Z=56, 2 valence electrons: 6s²).

        Core: Z_core = 54 electrons
        Valence: 6s² (2 electrons)

        Barium, alkaline earth
        """
        return PseudopotentialData(
            element='Ba',
            Z_ion=2,
            Z_core=54,
            r_c={0: 2.8, 1: 2.8, 2: 2.8},
            l_max=2,
            l_local=2
        )

    def _la_pseudopotential(self) -> PseudopotentialData:
        """
        La pseudopotential (Z=57, 3 valence electrons: 5d¹ 6s²).

        Core: Z_core = 54 electrons
        Valence: 5d¹ 6s² (3 electrons)

        Lanthanum, rare earth
        """
        return PseudopotentialData(
            element='La',
            Z_ion=3,
            Z_core=54,
            r_c={0: 2.5, 1: 2.5, 2: 2.5, 3: 2.5},
            l_max=3,
            l_local=3
        )

    def _ce_pseudopotential(self) -> PseudopotentialData:
        """
        Ce pseudopotential (Z=58, 4 valence electrons: 4f¹ 5d¹ 6s²).

        Core: Z_core = 54 electrons
        Valence: 4f¹ 5d¹ 6s² (4 electrons)

        Cerium, rare earth
        """
        return PseudopotentialData(
            element='Ce',
            Z_ion=4,
            Z_core=54,
            r_c={0: 2.5, 1: 2.5, 2: 2.5, 3: 2.5, 4: 2.5},
            l_max=4,
            l_local=4
        )

    def _pr_pseudopotential(self) -> PseudopotentialData:
        """
        Pr pseudopotential (Z=59, 5 valence electrons: 4f³ 6s²).

        Core: Z_core = 54 electrons
        Valence: 4f³ 6s² (5 electrons)

        Praseodymium
        """
        return PseudopotentialData(
            element='Pr',
            Z_ion=5,
            Z_core=54,
            r_c={0: 2.5, 1: 2.5, 2: 2.5, 3: 2.5, 4: 2.5},
            l_max=4,
            l_local=4
        )

    def _nd_pseudopotential(self) -> PseudopotentialData:
        """
        Nd pseudopotential (Z=60, 6 valence electrons: 4f⁴ 6s²).

        Core: Z_core = 54 electrons
        Valence: 4f⁴ 6s² (6 electrons)

        Neodymium, magnets
        """
        return PseudopotentialData(
            element='Nd',
            Z_ion=6,
            Z_core=54,
            r_c={0: 2.5, 1: 2.5, 2: 2.5, 3: 2.5, 4: 2.5},
            l_max=4,
            l_local=4
        )

    def _pm_pseudopotential(self) -> PseudopotentialData:
        """
        Pm pseudopotential (Z=61, 7 valence electrons: 4f⁵ 6s²).

        Core: Z_core = 54 electrons
        Valence: 4f⁵ 6s² (7 electrons)

        Promethium, radioactive
        """
        return PseudopotentialData(
            element='Pm',
            Z_ion=7,
            Z_core=54,
            r_c={0: 2.5, 1: 2.5, 2: 2.5, 3: 2.5, 4: 2.5},
            l_max=4,
            l_local=4
        )

    def _sm_pseudopotential(self) -> PseudopotentialData:
        """
        Sm pseudopotential (Z=62, 8 valence electrons: 4f⁶ 6s²).

        Core: Z_core = 54 electrons
        Valence: 4f⁶ 6s² (8 electrons)

        Samarium
        """
        return PseudopotentialData(
            element='Sm',
            Z_ion=8,
            Z_core=54,
            r_c={0: 2.5, 1: 2.5, 2: 2.5, 3: 2.5, 4: 2.5},
            l_max=4,
            l_local=4
        )

    def _eu_pseudopotential(self) -> PseudopotentialData:
        """
        Eu pseudopotential (Z=63, 9 valence electrons: 4f⁷ 6s²).

        Core: Z_core = 54 electrons
        Valence: 4f⁷ 6s² (9 electrons)

        Europium
        """
        return PseudopotentialData(
            element='Eu',
            Z_ion=9,
            Z_core=54,
            r_c={0: 2.5, 1: 2.5, 2: 2.5, 3: 2.5, 4: 2.5},
            l_max=4,
            l_local=4
        )

    def _gd_pseudopotential(self) -> PseudopotentialData:
        """
        Gd pseudopotential (Z=64, 10 valence electrons: 4f⁷ 5d¹ 6s²).

        Core: Z_core = 54 electrons
        Valence: 4f⁷ 5d¹ 6s² (10 electrons)

        Gadolinium, magnetic
        """
        return PseudopotentialData(
            element='Gd',
            Z_ion=10,
            Z_core=54,
            r_c={0: 2.5, 1: 2.5, 2: 2.5, 3: 2.5, 4: 2.5},
            l_max=4,
            l_local=4
        )

    def _tb_pseudopotential(self) -> PseudopotentialData:
        """
        Tb pseudopotential (Z=65, 11 valence electrons: 4f⁹ 6s²).

        Core: Z_core = 54 electrons
        Valence: 4f⁹ 6s² (11 electrons)

        Terbium
        """
        return PseudopotentialData(
            element='Tb',
            Z_ion=11,
            Z_core=54,
            r_c={0: 2.5, 1: 2.5, 2: 2.5, 3: 2.5, 4: 2.5},
            l_max=4,
            l_local=4
        )

    def _dy_pseudopotential(self) -> PseudopotentialData:
        """
        Dy pseudopotential (Z=66, 12 valence electrons: 4f¹⁰ 6s²).

        Core: Z_core = 54 electrons
        Valence: 4f¹⁰ 6s² (12 electrons)

        Dysprosium
        """
        return PseudopotentialData(
            element='Dy',
            Z_ion=12,
            Z_core=54,
            r_c={0: 2.5, 1: 2.5, 2: 2.5, 3: 2.5, 4: 2.5},
            l_max=4,
            l_local=4
        )

    def _ho_pseudopotential(self) -> PseudopotentialData:
        """
        Ho pseudopotential (Z=67, 13 valence electrons: 4f¹¹ 6s²).

        Core: Z_core = 54 electrons
        Valence: 4f¹¹ 6s² (13 electrons)

        Holmium
        """
        return PseudopotentialData(
            element='Ho',
            Z_ion=13,
            Z_core=54,
            r_c={0: 2.5, 1: 2.5, 2: 2.5, 3: 2.5, 4: 2.5},
            l_max=4,
            l_local=4
        )

    def _er_pseudopotential(self) -> PseudopotentialData:
        """
        Er pseudopotential (Z=68, 14 valence electrons: 4f¹² 6s²).

        Core: Z_core = 54 electrons
        Valence: 4f¹² 6s² (14 electrons)

        Erbium
        """
        return PseudopotentialData(
            element='Er',
            Z_ion=14,
            Z_core=54,
            r_c={0: 2.5, 1: 2.5, 2: 2.5, 3: 2.5, 4: 2.5},
            l_max=4,
            l_local=4
        )

    def _tm_pseudopotential(self) -> PseudopotentialData:
        """
        Tm pseudopotential (Z=69, 15 valence electrons: 4f¹³ 6s²).

        Core: Z_core = 54 electrons
        Valence: 4f¹³ 6s² (15 electrons)

        Thulium
        """
        return PseudopotentialData(
            element='Tm',
            Z_ion=15,
            Z_core=54,
            r_c={0: 2.5, 1: 2.5, 2: 2.5, 3: 2.5, 4: 2.5},
            l_max=4,
            l_local=4
        )

    def _yb_pseudopotential(self) -> PseudopotentialData:
        """
        Yb pseudopotential (Z=70, 16 valence electrons: 4f¹⁴ 6s²).

        Core: Z_core = 54 electrons
        Valence: 4f¹⁴ 6s² (16 electrons)

        Ytterbium
        """
        return PseudopotentialData(
            element='Yb',
            Z_ion=16,
            Z_core=54,
            r_c={0: 2.5, 1: 2.5, 2: 2.5, 3: 2.5, 4: 2.5},
            l_max=4,
            l_local=4
        )

    def _lu_pseudopotential(self) -> PseudopotentialData:
        """
        Lu pseudopotential (Z=71, 17 valence electrons: 4f¹⁴ 5d¹ 6s²).

        Core: Z_core = 54 electrons
        Valence: 4f¹⁴ 5d¹ 6s² (17 electrons)

        Lutetium
        """
        return PseudopotentialData(
            element='Lu',
            Z_ion=17,
            Z_core=54,
            r_c={0: 2.5, 1: 2.5, 2: 2.5, 3: 2.5, 4: 2.5},
            l_max=4,
            l_local=4
        )

    def _hf_pseudopotential(self) -> PseudopotentialData:
        """
        Hf pseudopotential (Z=72, 4 valence electrons: 5d² 6s²).

        Core: Z_core = 68 electrons
        Valence: 5d² 6s² (4 electrons)

        Hafnium, refractory
        """
        return PseudopotentialData(
            element='Hf',
            Z_ion=4,
            Z_core=68,
            r_c={0: 2.3, 1: 2.3, 2: 2.3, 3: 2.3},
            l_max=3,
            l_local=3
        )

    def _ta_pseudopotential(self) -> PseudopotentialData:
        """
        Ta pseudopotential (Z=73, 5 valence electrons: 5d³ 6s²).

        Core: Z_core = 68 electrons
        Valence: 5d³ 6s² (5 electrons)

        Tantalum, refractory
        """
        return PseudopotentialData(
            element='Ta',
            Z_ion=5,
            Z_core=68,
            r_c={0: 2.3, 1: 2.3, 2: 2.3, 3: 2.3},
            l_max=3,
            l_local=3
        )

    def _w_pseudopotential(self) -> PseudopotentialData:
        """
        W pseudopotential (Z=74, 6 valence electrons: 5d⁴ 6s²).

        Core: Z_core = 68 electrons
        Valence: 5d⁴ 6s² (6 electrons)

        Tungsten, highest Tm
        """
        return PseudopotentialData(
            element='W',
            Z_ion=6,
            Z_core=68,
            r_c={0: 2.3, 1: 2.3, 2: 2.3, 3: 2.3},
            l_max=3,
            l_local=3
        )

    def _re_pseudopotential(self) -> PseudopotentialData:
        """
        Re pseudopotential (Z=75, 7 valence electrons: 5d⁵ 6s²).

        Core: Z_core = 68 electrons
        Valence: 5d⁵ 6s² (7 electrons)

        Rhenium
        """
        return PseudopotentialData(
            element='Re',
            Z_ion=7,
            Z_core=68,
            r_c={0: 2.3, 1: 2.3, 2: 2.3, 3: 2.3},
            l_max=3,
            l_local=3
        )

    def _os_pseudopotential(self) -> PseudopotentialData:
        """
        Os pseudopotential (Z=76, 8 valence electrons: 5d⁶ 6s²).

        Core: Z_core = 68 electrons
        Valence: 5d⁶ 6s² (8 electrons)

        Osmium, densest element
        """
        return PseudopotentialData(
            element='Os',
            Z_ion=8,
            Z_core=68,
            r_c={0: 2.3, 1: 2.3, 2: 2.3, 3: 2.3},
            l_max=3,
            l_local=3
        )

    def _ir_pseudopotential(self) -> PseudopotentialData:
        """
        Ir pseudopotential (Z=77, 9 valence electrons: 5d⁷ 6s²).

        Core: Z_core = 68 electrons
        Valence: 5d⁷ 6s² (9 electrons)

        Iridium, noble metal
        """
        return PseudopotentialData(
            element='Ir',
            Z_ion=9,
            Z_core=68,
            r_c={0: 2.3, 1: 2.3, 2: 2.3, 3: 2.3},
            l_max=3,
            l_local=3
        )

    def _hg_pseudopotential(self) -> PseudopotentialData:
        """
        Hg pseudopotential (Z=80, 12 valence electrons: 5d¹⁰ 6s²).

        Core: Z_core = 68 electrons
        Valence: 5d¹⁰ 6s² (12 electrons)

        Mercury, liquid metal
        """
        return PseudopotentialData(
            element='Hg',
            Z_ion=12,
            Z_core=68,
            r_c={0: 2.3, 1: 2.3, 2: 2.3, 3: 2.3},
            l_max=3,
            l_local=3
        )

    def _tl_pseudopotential(self) -> PseudopotentialData:
        """
        Tl pseudopotential (Z=81, 3 valence electrons: 6s² 6p¹).

        Core: Z_core = 78 electrons
        Valence: 6s² 6p¹ (3 electrons)

        Thallium, toxic
        """
        return PseudopotentialData(
            element='Tl',
            Z_ion=3,
            Z_core=78,
            r_c={0: 2.4, 1: 2.4, 2: 2.4},
            l_max=2,
            l_local=2
        )

    def _pb_pseudopotential(self) -> PseudopotentialData:
        """
        Pb pseudopotential (Z=82, 4 valence electrons: 6s² 6p²).

        Core: Z_core = 78 electrons
        Valence: 6s² 6p² (4 electrons)

        Lead, heavy metal
        """
        return PseudopotentialData(
            element='Pb',
            Z_ion=4,
            Z_core=78,
            r_c={0: 2.3, 1: 2.3, 2: 2.3},
            l_max=2,
            l_local=2
        )

    def _bi_pseudopotential(self) -> PseudopotentialData:
        """
        Bi pseudopotential (Z=83, 5 valence electrons: 6s² 6p³).

        Core: Z_core = 78 electrons
        Valence: 6s² 6p³ (5 electrons)

        Bismuth
        """
        return PseudopotentialData(
            element='Bi',
            Z_ion=5,
            Z_core=78,
            r_c={0: 2.3, 1: 2.3, 2: 2.3},
            l_max=2,
            l_local=2
        )

    def _po_pseudopotential(self) -> PseudopotentialData:
        """
        Po pseudopotential (Z=84, 6 valence electrons: 6s² 6p⁴).

        Core: Z_core = 78 electrons
        Valence: 6s² 6p⁴ (6 electrons)

        Polonium, radioactive
        """
        return PseudopotentialData(
            element='Po',
            Z_ion=6,
            Z_core=78,
            r_c={0: 2.3, 1: 2.3, 2: 2.3},
            l_max=2,
            l_local=2
        )

    def _at_pseudopotential(self) -> PseudopotentialData:
        """
        At pseudopotential (Z=85, 7 valence electrons: 6s² 6p⁵).

        Core: Z_core = 78 electrons
        Valence: 6s² 6p⁵ (7 electrons)

        Astatine, halogen
        """
        return PseudopotentialData(
            element='At',
            Z_ion=7,
            Z_core=78,
            r_c={0: 2.3, 1: 2.3, 2: 2.3},
            l_max=2,
            l_local=2
        )

    def _rn_pseudopotential(self) -> PseudopotentialData:
        """
        Rn pseudopotential (Z=86, 8 valence electrons: 6s² 6p⁶).

        Core: Z_core = 78 electrons
        Valence: 6s² 6p⁶ (8 electrons)

        Radon, radioactive noble gas
        """
        return PseudopotentialData(
            element='Rn',
            Z_ion=8,
            Z_core=78,
            r_c={0: 2.3, 1: 2.3, 2: 2.3},
            l_max=2,
            l_local=2
        )

    def _fr_pseudopotential(self) -> PseudopotentialData:
        """
        Fr pseudopotential (Z=87, 1 valence electrons: 7s¹).

        Core: Z_core = 86 electrons
        Valence: 7s¹ (1 electrons)

        Francium, most reactive
        """
        return PseudopotentialData(
            element='Fr',
            Z_ion=1,
            Z_core=86,
            r_c={0: 3.2, 1: 3.2, 2: 3.2},
            l_max=2,
            l_local=2
        )

    def _ra_pseudopotential(self) -> PseudopotentialData:
        """
        Ra pseudopotential (Z=88, 2 valence electrons: 7s²).

        Core: Z_core = 86 electrons
        Valence: 7s² (2 electrons)

        Radium, radioactive
        """
        return PseudopotentialData(
            element='Ra',
            Z_ion=2,
            Z_core=86,
            r_c={0: 3.0, 1: 3.0, 2: 3.0},
            l_max=2,
            l_local=2
        )

    def _ac_pseudopotential(self) -> PseudopotentialData:
        """
        Ac pseudopotential (Z=89, 3 valence electrons: 6d¹ 7s²).

        Core: Z_core = 86 electrons
        Valence: 6d¹ 7s² (3 electrons)

        Actinium
        """
        return PseudopotentialData(
            element='Ac',
            Z_ion=3,
            Z_core=86,
            r_c={0: 2.7, 1: 2.7, 2: 2.7, 3: 2.7},
            l_max=3,
            l_local=3
        )

    def _th_pseudopotential(self) -> PseudopotentialData:
        """
        Th pseudopotential (Z=90, 4 valence electrons: 6d² 7s²).

        Core: Z_core = 86 electrons
        Valence: 6d² 7s² (4 electrons)

        Thorium, fissile
        """
        return PseudopotentialData(
            element='Th',
            Z_ion=4,
            Z_core=86,
            r_c={0: 2.7, 1: 2.7, 2: 2.7, 3: 2.7},
            l_max=3,
            l_local=3
        )

    def _pa_pseudopotential(self) -> PseudopotentialData:
        """
        Pa pseudopotential (Z=91, 5 valence electrons: 5f² 6d¹ 7s²).

        Core: Z_core = 86 electrons
        Valence: 5f² 6d¹ 7s² (5 electrons)

        Protactinium
        """
        return PseudopotentialData(
            element='Pa',
            Z_ion=5,
            Z_core=86,
            r_c={0: 2.7, 1: 2.7, 2: 2.7, 3: 2.7, 4: 2.7},
            l_max=4,
            l_local=4
        )

    def _u_pseudopotential(self) -> PseudopotentialData:
        """
        U pseudopotential (Z=92, 6 valence electrons: 5f³ 6d¹ 7s²).

        Core: Z_core = 86 electrons
        Valence: 5f³ 6d¹ 7s² (6 electrons)

        Uranium, fissile/fertile
        """
        return PseudopotentialData(
            element='U',
            Z_ion=6,
            Z_core=86,
            r_c={0: 2.7, 1: 2.7, 2: 2.7, 3: 2.7, 4: 2.7},
            l_max=4,
            l_local=4
        )

    def _np_pseudopotential(self) -> PseudopotentialData:
        """
        Np pseudopotential (Z=93, 7 valence electrons: 5f⁴ 6d¹ 7s²).

        Core: Z_core = 86 electrons
        Valence: 5f⁴ 6d¹ 7s² (7 electrons)

        Neptunium
        """
        return PseudopotentialData(
            element='Np',
            Z_ion=7,
            Z_core=86,
            r_c={0: 2.7, 1: 2.7, 2: 2.7, 3: 2.7, 4: 2.7},
            l_max=4,
            l_local=4
        )

    def _pu_pseudopotential(self) -> PseudopotentialData:
        """
        Pu pseudopotential (Z=94, 8 valence electrons: 5f⁶ 7s²).

        Core: Z_core = 86 electrons
        Valence: 5f⁶ 7s² (8 electrons)

        Plutonium, fissile
        """
        return PseudopotentialData(
            element='Pu',
            Z_ion=8,
            Z_core=86,
            r_c={0: 2.7, 1: 2.7, 2: 2.7, 3: 2.7, 4: 2.7},
            l_max=4,
            l_local=4
        )

    def _am_pseudopotential(self) -> PseudopotentialData:
        """
        Am pseudopotential (Z=95, 9 valence electrons: 5f⁷ 7s²).

        Core: Z_core = 86 electrons
        Valence: 5f⁷ 7s² (9 electrons)

        Americium
        """
        return PseudopotentialData(
            element='Am',
            Z_ion=9,
            Z_core=86,
            r_c={0: 2.7, 1: 2.7, 2: 2.7, 3: 2.7, 4: 2.7},
            l_max=4,
            l_local=4
        )

    def _cm_pseudopotential(self) -> PseudopotentialData:
        """
        Cm pseudopotential (Z=96, 10 valence electrons: 5f⁷ 6d¹ 7s²).

        Core: Z_core = 86 electrons
        Valence: 5f⁷ 6d¹ 7s² (10 electrons)

        Curium
        """
        return PseudopotentialData(
            element='Cm',
            Z_ion=10,
            Z_core=86,
            r_c={0: 2.7, 1: 2.7, 2: 2.7, 3: 2.7, 4: 2.7},
            l_max=4,
            l_local=4
        )

    def _bk_pseudopotential(self) -> PseudopotentialData:
        """
        Bk pseudopotential (Z=97, 11 valence electrons: 5f⁹ 7s²).

        Core: Z_core = 86 electrons
        Valence: 5f⁹ 7s² (11 electrons)

        Berkelium
        """
        return PseudopotentialData(
            element='Bk',
            Z_ion=11,
            Z_core=86,
            r_c={0: 2.7, 1: 2.7, 2: 2.7, 3: 2.7, 4: 2.7},
            l_max=4,
            l_local=4
        )

    def _cf_pseudopotential(self) -> PseudopotentialData:
        """
        Cf pseudopotential (Z=98, 12 valence electrons: 5f¹⁰ 7s²).

        Core: Z_core = 86 electrons
        Valence: 5f¹⁰ 7s² (12 electrons)

        Californium
        """
        return PseudopotentialData(
            element='Cf',
            Z_ion=12,
            Z_core=86,
            r_c={0: 2.7, 1: 2.7, 2: 2.7, 3: 2.7, 4: 2.7},
            l_max=4,
            l_local=4
        )

    def _es_pseudopotential(self) -> PseudopotentialData:
        """
        Es pseudopotential (Z=99, 13 valence electrons: 5f¹¹ 7s²).

        Core: Z_core = 86 electrons
        Valence: 5f¹¹ 7s² (13 electrons)

        Einsteinium
        """
        return PseudopotentialData(
            element='Es',
            Z_ion=13,
            Z_core=86,
            r_c={0: 2.7, 1: 2.7, 2: 2.7, 3: 2.7, 4: 2.7},
            l_max=4,
            l_local=4
        )

    def _fm_pseudopotential(self) -> PseudopotentialData:
        """
        Fm pseudopotential (Z=100, 14 valence electrons: 5f¹² 7s²).

        Core: Z_core = 86 electrons
        Valence: 5f¹² 7s² (14 electrons)

        Fermium
        """
        return PseudopotentialData(
            element='Fm',
            Z_ion=14,
            Z_core=86,
            r_c={0: 2.7, 1: 2.7, 2: 2.7, 3: 2.7, 4: 2.7},
            l_max=4,
            l_local=4
        )

    def _md_pseudopotential(self) -> PseudopotentialData:
        """
        Md pseudopotential (Z=101, 15 valence electrons: 5f¹³ 7s²).

        Core: Z_core = 86 electrons
        Valence: 5f¹³ 7s² (15 electrons)

        Mendelevium
        """
        return PseudopotentialData(
            element='Md',
            Z_ion=15,
            Z_core=86,
            r_c={0: 2.7, 1: 2.7, 2: 2.7, 3: 2.7, 4: 2.7},
            l_max=4,
            l_local=4
        )

    def _no_pseudopotential(self) -> PseudopotentialData:
        """
        No pseudopotential (Z=102, 16 valence electrons: 5f¹⁴ 7s²).

        Core: Z_core = 86 electrons
        Valence: 5f¹⁴ 7s² (16 electrons)

        Nobelium
        """
        return PseudopotentialData(
            element='No',
            Z_ion=16,
            Z_core=86,
            r_c={0: 2.7, 1: 2.7, 2: 2.7, 3: 2.7, 4: 2.7},
            l_max=4,
            l_local=4
        )

    def _lr_pseudopotential(self) -> PseudopotentialData:
        """
        Lr pseudopotential (Z=103, 17 valence electrons: 5f¹⁴ 7s² 7p¹).

        Core: Z_core = 86 electrons
        Valence: 5f¹⁴ 7s² 7p¹ (17 electrons)

        Lawrencium
        """
        return PseudopotentialData(
            element='Lr',
            Z_ion=17,
            Z_core=86,
            r_c={0: 2.7, 1: 2.7, 2: 2.7, 3: 2.7, 4: 2.7},
            l_max=4,
            l_local=4
        )

    def _rf_pseudopotential(self) -> PseudopotentialData:
        """
        Rf pseudopotential (Z=104, 4 valence electrons: 6d² 7s²).

        Core: Z_core = 100 electrons
        Valence: 6d² 7s² (4 electrons)

        Rutherfordium, synthetic
        """
        return PseudopotentialData(
            element='Rf',
            Z_ion=4,
            Z_core=100,
            r_c={0: 2.5, 1: 2.5, 2: 2.5, 3: 2.5},
            l_max=3,
            l_local=3
        )

    def _db_pseudopotential(self) -> PseudopotentialData:
        """
        Db pseudopotential (Z=105, 5 valence electrons: 6d³ 7s²).

        Core: Z_core = 100 electrons
        Valence: 6d³ 7s² (5 electrons)

        Dubnium, synthetic
        """
        return PseudopotentialData(
            element='Db',
            Z_ion=5,
            Z_core=100,
            r_c={0: 2.5, 1: 2.5, 2: 2.5, 3: 2.5},
            l_max=3,
            l_local=3
        )

    def _sg_pseudopotential(self) -> PseudopotentialData:
        """
        Sg pseudopotential (Z=106, 6 valence electrons: 6d⁴ 7s²).

        Core: Z_core = 100 electrons
        Valence: 6d⁴ 7s² (6 electrons)

        Seaborgium, synthetic
        """
        return PseudopotentialData(
            element='Sg',
            Z_ion=6,
            Z_core=100,
            r_c={0: 2.5, 1: 2.5, 2: 2.5, 3: 2.5},
            l_max=3,
            l_local=3
        )

    def _bh_pseudopotential(self) -> PseudopotentialData:
        """
        Bh pseudopotential (Z=107, 7 valence electrons: 6d⁵ 7s²).

        Core: Z_core = 100 electrons
        Valence: 6d⁵ 7s² (7 electrons)

        Bohrium, synthetic
        """
        return PseudopotentialData(
            element='Bh',
            Z_ion=7,
            Z_core=100,
            r_c={0: 2.5, 1: 2.5, 2: 2.5, 3: 2.5},
            l_max=3,
            l_local=3
        )

    def _hs_pseudopotential(self) -> PseudopotentialData:
        """
        Hs pseudopotential (Z=108, 8 valence electrons: 6d⁶ 7s²).

        Core: Z_core = 100 electrons
        Valence: 6d⁶ 7s² (8 electrons)

        Hassium, synthetic
        """
        return PseudopotentialData(
            element='Hs',
            Z_ion=8,
            Z_core=100,
            r_c={0: 2.5, 1: 2.5, 2: 2.5, 3: 2.5},
            l_max=3,
            l_local=3
        )

    def _mt_pseudopotential(self) -> PseudopotentialData:
        """
        Mt pseudopotential (Z=109, 9 valence electrons: 6d⁷ 7s²).

        Core: Z_core = 100 electrons
        Valence: 6d⁷ 7s² (9 electrons)

        Meitnerium, synthetic
        """
        return PseudopotentialData(
            element='Mt',
            Z_ion=9,
            Z_core=100,
            r_c={0: 2.5, 1: 2.5, 2: 2.5, 3: 2.5},
            l_max=3,
            l_local=3
        )

    def _ds_pseudopotential(self) -> PseudopotentialData:
        """
        Ds pseudopotential (Z=110, 10 valence electrons: 6d⁸ 7s²).

        Core: Z_core = 100 electrons
        Valence: 6d⁸ 7s² (10 electrons)

        Darmstadtium, synthetic
        """
        return PseudopotentialData(
            element='Ds',
            Z_ion=10,
            Z_core=100,
            r_c={0: 2.5, 1: 2.5, 2: 2.5, 3: 2.5},
            l_max=3,
            l_local=3
        )

    def _rg_pseudopotential(self) -> PseudopotentialData:
        """
        Rg pseudopotential (Z=111, 11 valence electrons: 6d⁹ 7s²).

        Core: Z_core = 100 electrons
        Valence: 6d⁹ 7s² (11 electrons)

        Roentgenium, synthetic
        """
        return PseudopotentialData(
            element='Rg',
            Z_ion=11,
            Z_core=100,
            r_c={0: 2.5, 1: 2.5, 2: 2.5, 3: 2.5},
            l_max=3,
            l_local=3
        )

    def _cn_pseudopotential(self) -> PseudopotentialData:
        """
        Cn pseudopotential (Z=112, 12 valence electrons: 6d¹⁰ 7s²).

        Core: Z_core = 100 electrons
        Valence: 6d¹⁰ 7s² (12 electrons)

        Copernicium, synthetic
        """
        return PseudopotentialData(
            element='Cn',
            Z_ion=12,
            Z_core=100,
            r_c={0: 2.5, 1: 2.5, 2: 2.5, 3: 2.5},
            l_max=3,
            l_local=3
        )

    def _nh_pseudopotential(self) -> PseudopotentialData:
        """
        Nh pseudopotential (Z=113, 3 valence electrons: 7s² 7p¹).

        Core: Z_core = 110 electrons
        Valence: 7s² 7p¹ (3 electrons)

        Nihonium, synthetic
        """
        return PseudopotentialData(
            element='Nh',
            Z_ion=3,
            Z_core=110,
            r_c={0: 2.5, 1: 2.5, 2: 2.5},
            l_max=2,
            l_local=2
        )

    def _fl_pseudopotential(self) -> PseudopotentialData:
        """
        Fl pseudopotential (Z=114, 4 valence electrons: 7s² 7p²).

        Core: Z_core = 110 electrons
        Valence: 7s² 7p² (4 electrons)

        Flerovium, synthetic
        """
        return PseudopotentialData(
            element='Fl',
            Z_ion=4,
            Z_core=110,
            r_c={0: 2.5, 1: 2.5, 2: 2.5},
            l_max=2,
            l_local=2
        )

    def _mc_pseudopotential(self) -> PseudopotentialData:
        """
        Mc pseudopotential (Z=115, 5 valence electrons: 7s² 7p³).

        Core: Z_core = 110 electrons
        Valence: 7s² 7p³ (5 electrons)

        Moscovium, synthetic
        """
        return PseudopotentialData(
            element='Mc',
            Z_ion=5,
            Z_core=110,
            r_c={0: 2.5, 1: 2.5, 2: 2.5},
            l_max=2,
            l_local=2
        )

    def _lv_pseudopotential(self) -> PseudopotentialData:
        """
        Lv pseudopotential (Z=116, 6 valence electrons: 7s² 7p⁴).

        Core: Z_core = 110 electrons
        Valence: 7s² 7p⁴ (6 electrons)

        Livermorium, synthetic
        """
        return PseudopotentialData(
            element='Lv',
            Z_ion=6,
            Z_core=110,
            r_c={0: 2.5, 1: 2.5, 2: 2.5},
            l_max=2,
            l_local=2
        )

    def _ts_pseudopotential(self) -> PseudopotentialData:
        """
        Ts pseudopotential (Z=117, 7 valence electrons: 7s² 7p⁵).

        Core: Z_core = 110 electrons
        Valence: 7s² 7p⁵ (7 electrons)

        Tennessine, synthetic
        """
        return PseudopotentialData(
            element='Ts',
            Z_ion=7,
            Z_core=110,
            r_c={0: 2.5, 1: 2.5, 2: 2.5},
            l_max=2,
            l_local=2
        )

    def _og_pseudopotential(self) -> PseudopotentialData:
        """
        Og pseudopotential (Z=118, 8 valence electrons: 7s² 7p⁶).

        Core: Z_core = 110 electrons
        Valence: 7s² 7p⁶ (8 electrons)

        Oganesson, synthetic noble gas
        """
        return PseudopotentialData(
            element='Og',
            Z_ion=8,
            Z_core=110,
            r_c={0: 2.5, 1: 2.5, 2: 2.5},
            l_max=2,
            l_local=2
        )
    # Potential Calculation Methods
    # ========================================================================

    def V_local(self, r: np.ndarray) -> np.ndarray:
        """
        Compute local part of pseudopotential.

        Uses error-function smoothed Coulomb potential:
        V_local(r) = -Z_ion * erf(r/r_c) / r

        This smoothly connects to -Z_ion/r at large r.

        Args:
            r: Radial distances (Angstrom)

        Returns:
            Local potential in eV
        """
        # Convert to Bohr
        r_bohr = r / BOHR_TO_ANGSTROM

        # Get local channel parameters
        r_c = self.data.r_c[self.data.l_local]
        Z_ion = self.data.Z_ion

        # Smoothed Coulomb (Troullier-Martins style)
        # V(r) = -Z * erf(sqrt(2) * r / r_c) / r
        # The sqrt(2) factor gives proper asymptotic behavior

        # Avoid division by zero at r=0
        r_safe = np.where(r_bohr < 1e-10, 1e-10, r_bohr)

        V_loc = -Z_ion * erf(np.sqrt(2.0) * r_safe / r_c) / r_safe

        # Convert from Hartree to eV
        V_loc_eV = V_loc * HARTREE_TO_EV

        return V_loc_eV

    def V_local_fourier(self, G: np.ndarray) -> np.ndarray:
        """
        Compute local potential in Fourier space.

        For Coulomb-like potential:
        V_local(G) = -4π Z_ion / |G|² * form_factor(G)

        The form factor depends on the smoothing function.

        Args:
            G: G-vectors (2π/Angstrom)

        Returns:
            V_local(G) in eV
        """
        # Convert to atomic units (1/Bohr)
        G_bohr = G * BOHR_TO_ANGSTROM

        r_c = self.data.r_c[self.data.l_local]
        Z_ion = self.data.Z_ion

        # Avoid division by zero
        G_safe = np.where(G_bohr < 1e-10, 1e-10, G_bohr)

        # Fourier transform of error-function screened Coulomb
        # V(G) = -4π Z / G² * exp(-G² r_c² / 4)
        V_G = -4.0 * np.pi * Z_ion / (G_safe**2) * np.exp(-G_safe**2 * r_c**2 / 4.0)

        # Convert to eV
        V_G_eV = V_G * HARTREE_TO_EV

        return V_G_eV

    def get_nonlocal_projectors(
        self,
        r: np.ndarray,
        l_values: Optional[List[int]] = None
    ) -> Dict[int, np.ndarray]:
        """
        Get non-local projector functions for each l-channel.

        For Kleinman-Bylander form:
        V_nl = Σ_l |β_l⟩ D_l ⟨β_l|

        where β_l(r) are atomic-like projector functions.

        Args:
            r: Radial grid (Angstrom)
            l_values: Which l-channels to compute (default: all up to l_max)

        Returns:
            Dictionary {l: projector_array}
        """
        if l_values is None:
            # All channels except the local one
            l_values = [l for l in range(self.data.l_max + 1)
                       if l != self.data.l_local]

        # Convert to Bohr
        r_bohr = r / BOHR_TO_ANGSTROM

        projectors = {}
        for l in l_values:
            if l not in self.data.r_c:
                continue

            r_c = self.data.r_c[l]

            # Simplified Troullier-Martins projector
            # β_l(r) = r^l * exp(-r²/2r_c²) * normalization

            beta_l = np.power(r_bohr, l) * np.exp(-r_bohr**2 / (2.0 * r_c**2))

            # Normalization (approximate)
            norm = np.sqrt(np.trapz(beta_l**2 * r_bohr**2, r_bohr))
            if norm > 1e-10:
                beta_l /= norm

            projectors[l] = beta_l

        return projectors


# Preload common pseudopotentials
_PSEUDOPOTENTIAL_CACHE: Dict[str, Pseudopotential] = {}


def get_pseudopotential(element: str) -> Pseudopotential:
    """
    Get pseudopotential for element (with caching).

    Args:
        element: Chemical symbol

    Returns:
        Pseudopotential object
    """
    if element not in _PSEUDOPOTENTIAL_CACHE:
        _PSEUDOPOTENTIAL_CACHE[element] = Pseudopotential(element)
    return _PSEUDOPOTENTIAL_CACHE[element]


__all__ = [
    'Pseudopotential',
    'PseudopotentialData',
    'get_pseudopotential',
]
