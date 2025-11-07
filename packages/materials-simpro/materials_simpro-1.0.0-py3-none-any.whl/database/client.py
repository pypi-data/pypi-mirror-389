"""
Database Client
===============

High-level interface to the universal materials database.

Provides unified access to:
- Materials Project
- OQMD
- AFLOW
- Local computed data
"""

from typing import List, Optional, Dict
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

from .models import Base, MaterialEntry, DBCalculationResult, PropertyData
from .materials_project import MaterialsProjectClient
from core.structure import Structure


class DatabaseClient:
    """
    Universal materials database client.

    Example Usage:
    --------------
    ```python
    db = DatabaseClient()

    # Search materials
    results = db.search(formula="Fe2O3")

    # Get material
    material = db.get_material("mp-149")

    # Store calculation result
    db.store_calculation(structure, result)

    # Query by properties
    stable_oxides = db.query(
        elements=['O'],
        is_stable=True,
        formation_energy_max=0.0
    )
    ```
    """

    def __init__(
        self,
        db_url: Optional[str] = None,
        mp_api_key: Optional[str] = None
    ):
        """
        Initialize database client.

        Args:
            db_url: PostgreSQL connection URL
            mp_api_key: Materials Project API key
        """
        # Database connection
        if db_url is None:
            db_url = os.environ.get('DATABASE_URL', 'sqlite:///materials.db')

        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)

        Session = sessionmaker(bind=self.engine)
        self.session = Session()

        # Materials Project client
        self.mp_client = MaterialsProjectClient(api_key=mp_api_key)

    def get_material(
        self,
        material_id: str,
        source: str = 'auto'
    ) -> Optional[Structure]:
        """
        Get material structure.

        Args:
            material_id: Material ID (e.g., 'mp-149')
            source: 'local', 'MP', 'OQMD', 'AFLOW', or 'auto'

        Returns:
            Structure object or None if not found
        """
        # Try local database first
        entry = self.session.query(MaterialEntry).filter_by(
            material_id=material_id
        ).first()

        if entry:
            return Structure.from_dict(entry.structure)

        # Query Materials Project if not in local DB
        if source in ['auto', 'MP'] and material_id.startswith('mp-'):
            try:
                structure = self.mp_client.get_structure(material_id)
                # Cache in local DB
                self._cache_material(material_id, structure, source='MP')
                return structure
            except:
                pass

        return None

    def search(
        self,
        formula: Optional[str] = None,
        elements: Optional[List[str]] = None,
        **kwargs
    ) -> List[MaterialEntry]:
        """
        Search materials database.

        Args:
            formula: Chemical formula
            elements: List of elements
            **kwargs: Additional filters (is_stable, band_gap_min, etc.)

        Returns:
            List of matching materials
        """
        query = self.session.query(MaterialEntry)

        if formula:
            query = query.filter(MaterialEntry.formula == formula)

        if elements:
            # Search for materials containing these elements
            # (simplified - use JSON operators in production)
            pass

        results = query.limit(100).all()

        # If no local results, try Materials Project
        if len(results) == 0 and (formula or elements):
            mp_results = self.mp_client.search_materials(
                formula=formula,
                elements=elements
            )

            # Convert MP results to MaterialEntry objects
            for mp_data in mp_results:
                material_id = mp_data.get('material_id')
                if material_id:
                    structure = self.get_material(material_id, source='MP')
                    # (result already cached by get_material)

        return results

    def store_calculation(
        self,
        structure: Structure,
        result,  # CalculationResult from core.base
        material_id: Optional[str] = None
    ):
        """
        Store calculation result in database.

        Args:
            structure: Input structure
            result: CalculationResult object
            material_id: Material ID (generated if None)
        """
        if material_id is None:
            material_id = self._generate_material_id(structure)

        # Check if material exists
        entry = self.session.query(MaterialEntry).filter_by(
            material_id=material_id
        ).first()

        if not entry:
            # Create new material entry
            entry = MaterialEntry(
                material_id=material_id,
                formula=structure.formula or "Unknown",
                structure=structure.to_dict(),
                space_group=structure.space_group,
                nsites=len(structure),
                source='computed'
            )
            self.session.add(entry)
            self.session.commit()

        # Store calculation result
        calc = DBCalculationResult(
            material_id=material_id,
            method=result.metadata.get('model', 'unknown'),
            fidelity=result.fidelity.name if result.fidelity else None,
            energy=result.energy,
            energy_per_atom=result.energy_per_atom,
            converged=result.converged,
            walltime=result.walltime,
            n_atoms=len(structure)
        )

        self.session.add(calc)
        self.session.commit()

    def _cache_material(
        self,
        material_id: str,
        structure: Structure,
        source: str
    ):
        """Cache material in local database."""
        entry = MaterialEntry(
            material_id=material_id,
            formula=structure.formula or "Unknown",
            structure=structure.to_dict(),
            space_group=structure.space_group,
            nsites=len(structure),
            source=source
        )

        self.session.add(entry)
        try:
            self.session.commit()
        except:
            self.session.rollback()

    def _generate_material_id(self, structure: Structure) -> str:
        """Generate unique material ID."""
        import hashlib
        import json

        # Hash structure data
        structure_str = json.dumps(structure.to_dict(), sort_keys=True)
        hash_val = hashlib.md5(structure_str.encode()).hexdigest()[:8]

        return f"local-{hash_val}"

    def close(self):
        """Close database connection."""
        self.session.close()


__all__ = ['DatabaseClient']
