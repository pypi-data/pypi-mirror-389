"""
REST API
========

FastAPI-based REST API for Materials-SimPro.

Endpoints:
----------
- /calculate/energy - Energy calculations
- /calculate/forces - Force calculations
- /calculate/md - Molecular dynamics
- /search/query - Database queries
- /search/structure/{material_id} - Get structure
- /optimize/structure - Structure optimization
- /discover/auto - AI discovery
- /analyze/elastic - Elastic properties
- /analyze/phonon - Phonon properties

Authentication: API key (Bearer token)

References:
-----------
[1] FastAPI: https://fastapi.tiangolo.com/
[2] OpenAPI 3.0: https://swagger.io/specification/
"""

from .server import app

__all__ = ['app']
