"""
Database Models
===============

SQLAlchemy models for PostgreSQL storage.

Schema Design:
--------------
- materials: Core material entries
- calculations: DFT/ML calculation results
- properties: Computed/experimental properties
- similarity: Material similarity graph

Reference: SQLAlchemy documentation
https://docs.sqlalchemy.org/
"""

from sqlalchemy import Column, Integer, String, Float, JSON, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class MaterialEntry(Base):
    """
    Core material entry.

    Stores:
    - Crystal structure
    - Composition
    - Space group
    - Database provenance (MP, OQMD, AFLOW)
    """
    __tablename__ = 'materials'

    id = Column(Integer, primary_key=True)
    material_id = Column(String(50), unique=True, nullable=False, index=True)  # e.g., mp-149
    formula = Column(String(100), nullable=False, index=True)  # e.g., Fe2O3
    reduced_formula = Column(String(100), index=True)  # e.g., FeO1.5

    # Crystal structure (JSON)
    structure = Column(JSON, nullable=False)  # Full structure data

    # Crystallographic info
    space_group = Column(Integer)  # International space group number
    lattice_system = Column(String(20))  # cubic, hexagonal, etc.
    point_group = Column(String(20))

    # Composition
    elements = Column(JSON)  # List of elements
    nelements = Column(Integer)  # Number of unique elements
    nsites = Column(Integer)  # Number of atoms in unit cell

    # Database provenance
    source = Column(String(20), index=True)  # 'MP', 'OQMD', 'AFLOW', 'computed'
    source_id = Column(String(50))  # Original ID from source database

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    calculations = relationship('DBCalculationResult', back_populates='material')
    properties = relationship('PropertyData', back_populates='material')

    def __repr__(self):
        return f"<MaterialEntry(id='{self.material_id}', formula='{self.formula}')>"


class DBCalculationResult(Base):
    """
    Calculation results (DFT, ML, MD).

    Stores:
    - Method used (DFT/GGA-PBE, ML/Orb, etc.)
    - Energy, forces, stress
    - Convergence status
    - Computational cost
    """
    __tablename__ = 'calculations'

    id = Column(Integer, primary_key=True)
    material_id = Column(String(50), ForeignKey('materials.material_id'), nullable=False, index=True)

    # Method
    method = Column(String(50), nullable=False)  # 'DFT', 'ML-Orb', 'MD'
    functional = Column(String(50))  # 'PBE', 'HSE06', etc. (for DFT)
    fidelity = Column(String(20))  # 'ML', 'DFT', 'POST_DFT'

    # Results
    energy = Column(Float)  # eV
    energy_per_atom = Column(Float)  # eV/atom
    forces = Column(JSON)  # List of forces (eV/Å)
    stress = Column(JSON)  # Stress tensor (eV/Å³)

    # Convergence
    converged = Column(Boolean, default=True)
    scf_iterations = Column(Integer)  # For DFT

    # Computational cost
    walltime = Column(Float)  # seconds
    n_atoms = Column(Integer)

    # Metadata
    parameters = Column(JSON)  # Method-specific parameters
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    material = relationship('MaterialEntry', back_populates='calculations')

    def __repr__(self):
        return f"<Calculation(material='{self.material_id}', method='{self.method}', E={self.energy:.3f} eV)>"


class PropertyData(Base):
    """
    Computed/experimental material properties.

    Includes:
    - Formation energy
    - Band gap
    - Elastic constants
    - Phonon frequencies
    - Magnetic properties
    """
    __tablename__ = 'properties'

    id = Column(Integer, primary_key=True)
    material_id = Column(String(50), ForeignKey('materials.material_id'), nullable=False, index=True)

    # Thermodynamic properties
    formation_energy = Column(Float)  # eV/atom
    decomposition_energy = Column(Float)  # eV/atom (energy above hull)
    is_stable = Column(Boolean)

    # Electronic properties
    band_gap = Column(Float)  # eV
    is_metal = Column(Boolean)
    is_magnetic = Column(Boolean)
    total_magnetization = Column(Float)  # μB

    # Mechanical properties
    elastic_tensor = Column(JSON)  # 6x6 elastic tensor (GPa)
    bulk_modulus = Column(Float)  # GPa
    shear_modulus = Column(Float)  # GPa

    # Phonon properties
    has_phonon_data = Column(Boolean, default=False)
    phonon_frequencies = Column(JSON)

    # Other properties
    density = Column(Float)  # g/cm³
    volume = Column(Float)  # Å³

    # Metadata
    property_source = Column(String(50))  # 'computed', 'MP', 'experimental'
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    material = relationship('MaterialEntry', back_populates='properties')

    def __repr__(self):
        return f"<PropertyData(material='{self.material_id}', Ef={self.formation_energy:.3f} eV/atom)>"


__all__ = [
    'Base',
    'MaterialEntry',
    'DBCalculationResult',
    'PropertyData',
]
