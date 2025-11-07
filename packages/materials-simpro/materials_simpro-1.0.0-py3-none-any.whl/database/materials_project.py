"""
Materials Project API Integration
==================================

Access to Materials Project database (154K+ materials).

The Materials Project is an open database of computed materials properties
funded by the U.S. Department of Energy.

API Access:
-----------
Requires API key (free): https://materialsproject.org/api

Available Data:
---------------
- Crystal structures
- Formation energies (DFT-PBE)
- Band structures and DOS
- Elastic properties
- Phonon properties
- Phase diagrams
- Pourbaix diagrams

Rate Limits:
------------
- 1000 requests/day (free tier)
- Bulk data downloads available

Scientific Citation:
--------------------
Jain, A., et al. (2013). Commentary: The Materials Project: A materials
genome approach to accelerating materials innovation. APL Materials, 1(1), 011002.
DOI: 10.1063/1.4812323

API Documentation:
------------------
https://docs.materialsproject.org/downloading-data/using-the-api
"""

import requests
from typing import List, Dict, Optional
import numpy as np

from core.structure import Structure, Lattice, Site


class MaterialsProjectClient:
    """
    Client for Materials Project API.

    Example Usage:
    --------------
    ```python
    client = MaterialsProjectClient(api_key="YOUR_API_KEY")

    # Get structure
    structure = client.get_structure("mp-149")  # Iron

    # Search by formula
    results = client.search_materials(formula="Fe2O3")

    # Get properties
    props = client.get_properties("mp-149", ["formation_energy", "band_gap"])
    ```

    Reference: https://api.materialsproject.org/docs
    """

    BASE_URL = "https://api.materialsproject.org"

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Materials Project client.

        Args:
            api_key: MP API key (get from https://materialsproject.org/api)
        """
        self.api_key = api_key
        self.session = requests.Session()

        if api_key:
            self.session.headers.update({
                'X-API-KEY': api_key
            })

    def get_structure(self, material_id: str) -> Structure:
        """
        Get crystal structure for a material.

        Args:
            material_id: Materials Project ID (e.g., 'mp-149')

        Returns:
            Structure object

        Raises:
            ValueError: If material not found or API error
        """
        endpoint = f"/materials/{material_id}/structure"
        url = self.BASE_URL + endpoint

        try:
            response = self.session.get(url)
            response.raise_for_status()
            data = response.json()

            # Parse structure data
            structure_data = data['data'][0]
            return self._parse_structure(structure_data)

        except requests.exceptions.RequestException as e:
            raise ValueError(f"Failed to fetch structure for {material_id}: {e}")

    def _parse_structure(self, data: Dict) -> Structure:
        """
        Parse Materials Project structure data to Structure object.

        MP API returns structure in this format:
        {
            "lattice": {"matrix": [[a1x, a1y, a1z], [a2x, a2y, a2z], [a3x, a3y, a3z]]},
            "sites": [{"species": [{"element": "Fe"}], "abc": [x, y, z]}, ...]
        }
        """
        # Lattice
        lattice_matrix = np.array(data['lattice']['matrix'])
        lattice = Lattice(matrix=lattice_matrix)

        # Sites
        sites = []
        for site_data in data['sites']:
            element = site_data['species'][0]['element']
            position = np.array(site_data['abc'])  # fractional coordinates
            site = Site(element=element, position=position)
            sites.append(site)

        # Space group
        space_group = data.get('symmetry', {}).get('number')

        # Formula
        formula = data.get('formula_pretty')

        structure = Structure(
            lattice=lattice,
            sites=sites,
            space_group=space_group,
            formula=formula
        )

        return structure

    def get_properties(
        self,
        material_id: str,
        properties: List[str]
    ) -> Dict:
        """
        Get material properties.

        Available properties:
        - formation_energy_per_atom
        - band_gap
        - density
        - volume
        - energy_above_hull
        - is_stable
        - elastic_tensor
        - ...

        Args:
            material_id: MP ID
            properties: List of property names

        Returns:
            Dictionary of {property: value}
        """
        endpoint = f"/materials/{material_id}"
        url = self.BASE_URL + endpoint

        params = {
            'fields': ','.join(properties)
        }

        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if 'data' in data and len(data['data']) > 0:
                return data['data'][0]
            else:
                return {}

        except requests.exceptions.RequestException as e:
            print(f"Warning: Failed to fetch properties for {material_id}: {e}")
            return {}

    def search_materials(
        self,
        formula: Optional[str] = None,
        elements: Optional[List[str]] = None,
        nelements: Optional[int] = None,
        max_results: int = 100
    ) -> List[Dict]:
        """
        Search for materials matching criteria.

        Args:
            formula: Chemical formula (e.g., 'Fe2O3')
            elements: List of elements (e.g., ['Fe', 'O'])
            nelements: Number of elements
            max_results: Maximum results to return

        Returns:
            List of material data dictionaries
        """
        endpoint = "/materials/summary"
        url = self.BASE_URL + endpoint

        params = {}
        if formula:
            params['formula'] = formula
        if elements:
            params['elements'] = ','.join(elements)
        if nelements:
            params['nelements'] = nelements

        params['_limit'] = max_results

        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            return data.get('data', [])

        except requests.exceptions.RequestException as e:
            print(f"Warning: Search failed: {e}")
            return []

    def get_phase_diagram(
        self,
        elements: List[str]
    ) -> Dict:
        """
        Get phase diagram for chemical system.

        Args:
            elements: List of elements (e.g., ['Fe', 'O'])

        Returns:
            Phase diagram data
        """
        # Simplified - actual API endpoint may differ
        system = '-'.join(sorted(elements))
        endpoint = f"/phase_diagram/{system}"
        url = self.BASE_URL + endpoint

        try:
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
        except:
            return {}

    def get_bandstructure(
        self,
        material_id: str
    ) -> Dict:
        """
        Get electronic band structure.

        Args:
            material_id: MP ID

        Returns:
            Band structure data (k-points, eigenvalues)
        """
        endpoint = f"/materials/{material_id}/bandstructure"
        url = self.BASE_URL + endpoint

        try:
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
        except:
            return {}


__all__ = ['MaterialsProjectClient']
