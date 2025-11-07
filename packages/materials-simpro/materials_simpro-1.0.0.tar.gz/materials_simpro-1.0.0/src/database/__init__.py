"""
Universal Materials Database
=============================

Integration of major materials databases:
- Materials Project (154K+ materials)
- OQMD (1.5M compounds)
- AFLOW (3.7M entries)
- Proprietary computed data

Database Architecture:
----------------------

Multi-modal storage:
1. **PostgreSQL**: Structured data (compositions, properties)
2. **MongoDB**: Document store (calculation metadata)
3. **Neo4j**: Graph database (materials similarity)
4. **Redis**: Cache (fast lookups)
5. **Elasticsearch**: Full-text search

Target: 5M+ materials with comprehensive property data.

Materials Project API:
----------------------
The Materials Project provides open access to computed materials properties:
- Formation energies
- Band structures
- Elastic constants
- Phase diagrams
- Crystal structures

API Documentation: https://docs.materialsproject.org/
Citation: Jain, A., et al. (2013). Commentary: The Materials Project: A materials
genome approach to accelerating materials innovation. APL Materials, 1(1), 011002.
DOI: 10.1063/1.4812323

Scientific References:
----------------------
[1] Jain, A., et al. (2013). Commentary: The Materials Project: A materials
    genome approach to accelerating materials innovation. APL Materials, 1(1), 011002.
    DOI: 10.1063/1.4812323

[2] Kirklin, S., et al. (2015). The Open Quantum Materials Database (OQMD):
    assessing the accuracy of DFT formation energies. npj Computational Materials, 1, 15010.
    DOI: 10.1038/npjcompumats.2015.10

[3] Curtarolo, S., et al. (2012). AFLOW: An automatic framework for
    high-throughput materials discovery. Computational Materials Science, 58, 218-226.
    DOI: 10.1016/j.commatsci.2012.02.005
"""

from .models import (
    MaterialEntry,
    DBCalculationResult,
    PropertyData
)
from .materials_project import MaterialsProjectClient
from .client import DatabaseClient

__all__ = [
    'MaterialEntry',
    'DBCalculationResult',
    'PropertyData',
    'MaterialsProjectClient',
    'DatabaseClient',
]
