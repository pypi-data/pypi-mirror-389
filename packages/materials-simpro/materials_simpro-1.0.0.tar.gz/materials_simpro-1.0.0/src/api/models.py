"""
API Models
==========

Pydantic models for request/response validation.

References:
-----------
[1] Pydantic: https://docs.pydantic.dev/
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum


# ============================================================================
# Enums
# ============================================================================

class CalculationMethod(str, Enum):
    """Calculation methods."""
    DFT = "dft"
    ORB = "orb"
    EGRET = "egret"
    MACE = "mace"
    CHGNET = "chgnet"


class XCFunctional(str, Enum):
    """Exchange-correlation functionals."""
    LDA = "lda"
    PBE = "pbe"
    HSE06 = "hse06"
    SCAN = "scan"


class OptimizationAlgorithm(str, Enum):
    """Optimization algorithms."""
    BAYESIAN = "bayesian"
    GENETIC = "genetic"
    GRADIENT = "gradient"


class Ensemble(str, Enum):
    """MD ensembles."""
    NVE = "nve"
    NVT = "nvt"
    NPT = "npt"


# ============================================================================
# Request Models
# ============================================================================

class EnergyRequest(BaseModel):
    """Energy calculation request."""
    structure: Dict[str, Any] = Field(..., description="Crystal structure")
    method: CalculationMethod = Field(CalculationMethod.ORB, description="Calculation method")
    xc: XCFunctional = Field(XCFunctional.PBE, description="XC functional (DFT only)")
    ecut: float = Field(40.0, description="Energy cutoff in Rydberg (DFT only)")

    class Config:
        schema_extra = {
            "example": {
                "structure": {
                    "lattice": [[5.43, 0, 0], [0, 5.43, 0], [0, 0, 5.43]],
                    "species": ["Si", "Si"],
                    "coords": [[0, 0, 0], [0.25, 0.25, 0.25]]
                },
                "method": "orb",
                "xc": "pbe",
                "ecut": 40.0
            }
        }


class ForcesRequest(BaseModel):
    """Forces calculation request."""
    structure: Dict[str, Any]
    method: CalculationMethod = CalculationMethod.ORB


class MDRequest(BaseModel):
    """Molecular dynamics request."""
    structure: Dict[str, Any]
    temperature: float = Field(300.0, description="Temperature in Kelvin", gt=0)
    steps: int = Field(1000, description="Number of MD steps", gt=0)
    timestep: float = Field(1.0, description="Timestep in femtoseconds", gt=0)
    ensemble: Ensemble = Field(Ensemble.NVT, description="Statistical ensemble")
    method: CalculationMethod = CalculationMethod.ORB


class SearchRequest(BaseModel):
    """Database search request."""
    formula: Optional[str] = Field(None, description="Chemical formula")
    energy_max: Optional[float] = Field(None, description="Max formation energy (eV/atom)")
    bandgap_min: Optional[float] = Field(None, description="Min band gap (eV)")
    elements: Optional[List[str]] = Field(None, description="Elements to include")
    limit: int = Field(10, description="Max results", gt=0, le=1000)


class OptimizeRequest(BaseModel):
    """Structure optimization request."""
    structure: Dict[str, Any]
    algorithm: OptimizationAlgorithm = OptimizationAlgorithm.BAYESIAN
    iterations: int = Field(50, description="Max iterations", gt=0)
    method: CalculationMethod = CalculationMethod.ORB


class DiscoveryRequest(BaseModel):
    """AI discovery request."""
    goal: str = Field(..., description="Natural language goal")
    candidates: int = Field(1000, description="Number of candidates to screen", gt=0)


class ElasticRequest(BaseModel):
    """Elastic properties request."""
    structure: Dict[str, Any]
    method: CalculationMethod = CalculationMethod.ORB


class PhononRequest(BaseModel):
    """Phonon properties request."""
    structure: Dict[str, Any]
    method: CalculationMethod = CalculationMethod.ORB


# ============================================================================
# Response Models
# ============================================================================

class EnergyResponse(BaseModel):
    """Energy calculation response."""
    total_energy: float = Field(..., description="Total energy (eV)")
    energy_per_atom: float = Field(..., description="Energy per atom (eV/atom)")
    formula: str = Field(..., description="Chemical formula")
    n_atoms: int = Field(..., description="Number of atoms")
    method: str = Field(..., description="Method used")


class ForcesResponse(BaseModel):
    """Forces calculation response."""
    forces: List[List[float]] = Field(..., description="Atomic forces (eV/Å)")
    max_force: float = Field(..., description="Maximum force magnitude (eV/Å)")
    rms_force: float = Field(..., description="RMS force (eV/Å)")


class MDResponse(BaseModel):
    """Molecular dynamics response."""
    trajectory: List[Dict[str, Any]] = Field(..., description="MD trajectory")
    final_temperature: float = Field(..., description="Final temperature (K)")
    total_energy: float = Field(..., description="Final total energy (eV)")


class Material(BaseModel):
    """Material from database."""
    material_id: str
    formula: str
    formation_energy_per_atom: Optional[float] = None
    band_gap: Optional[float] = None
    structure: Optional[Dict[str, Any]] = None


class SearchResponse(BaseModel):
    """Database search response."""
    materials: List[Material]
    count: int


class OptimizeResponse(BaseModel):
    """Optimization response."""
    optimized_structure: Dict[str, Any]
    final_energy: float
    iterations: int
    converged: bool


class DiscoveryResponse(BaseModel):
    """AI discovery response."""
    goal: str
    novel_materials: List[str]
    candidates_screened: int
    properties: Dict[str, List[float]]


class ElasticResponse(BaseModel):
    """Elastic properties response."""
    bulk_modulus: float = Field(..., description="Bulk modulus (GPa)")
    shear_modulus: float = Field(..., description="Shear modulus (GPa)")
    youngs_modulus: float = Field(..., description="Young's modulus (GPa)")
    poisson_ratio: float = Field(..., description="Poisson ratio")
    elastic_tensor: List[List[float]] = Field(..., description="6x6 elastic tensor (GPa)")


class PhononResponse(BaseModel):
    """Phonon properties response."""
    omega_max: float = Field(..., description="Maximum frequency (THz)")
    dos: List[float] = Field(..., description="Phonon density of states")
    frequencies: List[float] = Field(..., description="Phonon frequencies (THz)")


class ErrorResponse(BaseModel):
    """Error response."""
    detail: str
    error_type: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    database_connected: bool
