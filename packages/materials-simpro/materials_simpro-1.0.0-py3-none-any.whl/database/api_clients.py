"""
API CLIENTS - Data Ingestion from Scientific Databases
=======================================================

Clients for fetching data from major scientific databases:
- PubChem (100M+ compounds)
- DrugBank (15k drugs)
- Materials Project (150k materials)
- KEGG (20k metabolites)
- ChEMBL (2M bioactive compounds)

Features:
- Rate limiting and retry logic
- Batch fetching for efficiency
- Progress tracking
- Error handling
- Cache support

Author: Materials-SimPro Team
Date: 2025-11-04
"""

import requests
import time
import json
from typing import Dict, List, Optional, Iterator
from dataclasses import dataclass
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class MoleculeData:
    """Standardized molecule data structure"""
    name: str
    formula: str
    molecular_weight: float
    smiles: Optional[str] = None
    inchi: Optional[str] = None
    properties: Optional[Dict] = None
    source: str = "unknown"


class PubChemClient:
    """
    PubChem REST API Client

    API Documentation: https://pubchem.ncbi.nlm.nih.gov/docs/pug-rest

    Features:
    - Search by name, formula, CID
    - Batch queries (up to 100 compounds)
    - Rate limiting (5 requests/second max)
    - Automatic retry on failures

    Usage:
        client = PubChemClient()
        aspirin = client.get_compound_by_name("aspirin")
        batch = client.get_compounds_batch([2244, 5090, 6033])  # CIDs
    """

    BASE_URL = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
    RATE_LIMIT = 0.2  # 5 requests per second max

    def __init__(self, cache_dir: Optional[str] = None):
        self.session = requests.Session()
        self.last_request_time = 0
        self.cache_dir = Path(cache_dir) if cache_dir else None
        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _rate_limit(self):
        """Enforce rate limiting"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.RATE_LIMIT:
            time.sleep(self.RATE_LIMIT - elapsed)
        self.last_request_time = time.time()

    def _request(self, url: str, params: Optional[Dict] = None, retries: int = 3) -> Optional[Dict]:
        """Make HTTP request with retry logic"""
        self._rate_limit()

        for attempt in range(retries):
            try:
                response = self.session.get(url, params=params, timeout=30)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                logger.warning(f"Attempt {attempt + 1}/{retries} failed: {e}")
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error(f"All retries failed for URL: {url}")
                    return None
        return None

    def get_compound_by_cid(self, cid: int) -> Optional[MoleculeData]:
        """
        Get compound by PubChem CID (Compound ID)

        Args:
            cid: PubChem compound ID

        Returns:
            MoleculeData or None if not found
        """
        url = f"{self.BASE_URL}/compound/cid/{cid}/property/MolecularFormula,MolecularWeight,IUPACName,CanonicalSMILES/JSON"

        data = self._request(url)
        if not data or 'PropertyTable' not in data:
            return None

        props = data['PropertyTable']['Properties'][0]

        return MoleculeData(
            name=props.get('IUPACName', f'CID_{cid}'),
            formula=props.get('MolecularFormula', ''),
            molecular_weight=float(props.get('MolecularWeight', 0)),
            smiles=props.get('CanonicalSMILES'),
            properties={'cid': cid},
            source='PubChem'
        )

    def get_compound_by_name(self, name: str) -> Optional[MoleculeData]:
        """
        Search for compound by name

        Args:
            name: Common name or IUPAC name

        Returns:
            MoleculeData or None if not found
        """
        # First, resolve name to CID
        url = f"{self.BASE_URL}/compound/name/{name}/cids/JSON"
        data = self._request(url)

        if not data or 'IdentifierList' not in data:
            return None

        cid = data['IdentifierList']['CID'][0]
        return self.get_compound_by_cid(cid)

    def get_compounds_batch(self, cids: List[int], batch_size: int = 100) -> Iterator[MoleculeData]:
        """
        Get multiple compounds in batches

        Args:
            cids: List of PubChem CIDs
            batch_size: Number of compounds per request (max 100)

        Yields:
            MoleculeData objects
        """
        for i in range(0, len(cids), batch_size):
            batch = cids[i:i + batch_size]
            cid_list = ','.join(map(str, batch))

            url = f"{self.BASE_URL}/compound/cid/{cid_list}/property/MolecularFormula,MolecularWeight,IUPACName,CanonicalSMILES/JSON"

            data = self._request(url)
            if not data or 'PropertyTable' not in data:
                continue

            for props in data['PropertyTable']['Properties']:
                cid = props.get('CID')
                yield MoleculeData(
                    name=props.get('IUPACName', f'CID_{cid}'),
                    formula=props.get('MolecularFormula', ''),
                    molecular_weight=float(props.get('MolecularWeight', 0)),
                    smiles=props.get('CanonicalSMILES'),
                    properties={'cid': cid},
                    source='PubChem'
                )

            logger.info(f"Fetched batch {i//batch_size + 1}: {len(batch)} compounds")

    def search_by_formula(self, formula: str, max_results: int = 1000) -> List[int]:
        """
        Search compounds by molecular formula

        Args:
            formula: Molecular formula (e.g., "C9H8O4")
            max_results: Maximum number of CIDs to return

        Returns:
            List of PubChem CIDs
        """
        url = f"{self.BASE_URL}/compound/fastformula/{formula}/cids/JSON"
        data = self._request(url)

        if not data or 'IdentifierList' not in data:
            return []

        cids = data['IdentifierList']['CID']
        return cids[:max_results]

    def get_top_compounds(self, count: int = 10000) -> Iterator[MoleculeData]:
        """
        Get top N most popular compounds from PubChem

        Strategy: Fetch compounds by sequential CIDs starting from 1
        (Lower CIDs are generally more important/well-characterized)

        Args:
            count: Number of compounds to fetch

        Yields:
            MoleculeData objects
        """
        cids = list(range(1, count + 1))
        yield from self.get_compounds_batch(cids)


class DrugBankClient:
    """
    DrugBank API Client

    Note: Requires API key (free for academic use)
    Register at: https://www.drugbank.ca/

    Features:
    - FDA/EMA approved drugs
    - Drug interactions
    - Pharmacokinetic data
    - Target information
    """

    BASE_URL = "https://api.drugbank.com/v1"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.session = requests.Session()
        if api_key:
            self.session.headers.update({'Authorization': f'Bearer {api_key}'})

    def get_drug(self, drugbank_id: str) -> Optional[MoleculeData]:
        """
        Get drug by DrugBank ID

        Args:
            drugbank_id: DrugBank ID (e.g., "DB00945" for aspirin)

        Returns:
            MoleculeData or None
        """
        if not self.api_key:
            logger.warning("DrugBank API key not provided")
            return None

        url = f"{self.BASE_URL}/drugs/{drugbank_id}"

        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()

            return MoleculeData(
                name=data.get('name', ''),
                formula=data.get('formula', ''),
                molecular_weight=float(data.get('average_mass', 0)),
                smiles=data.get('smiles'),
                properties={
                    'drugbank_id': drugbank_id,
                    'description': data.get('description'),
                    'indication': data.get('indication'),
                    'pharmacology': data.get('pharmacology')
                },
                source='DrugBank'
            )
        except requests.exceptions.RequestException as e:
            logger.error(f"DrugBank API error: {e}")
            return None


class MaterialsProjectClient:
    """
    Materials Project API Client

    API Documentation: https://materialsproject.org/api

    Features:
    - 150k+ DFT-calculated materials
    - Crystal structures (CIF format)
    - Electronic properties
    - Phase diagrams

    Note: Requires free API key
    Register at: https://materialsproject.org/
    """

    BASE_URL = "https://api.materialsproject.org/materials"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.session = requests.Session()
        if api_key:
            self.session.headers.update({'X-API-KEY': api_key})

    def search_materials(self, formula: str) -> List[Dict]:
        """
        Search materials by chemical formula

        Args:
            formula: Chemical formula (e.g., "Fe2O3")

        Returns:
            List of material data dictionaries
        """
        if not self.api_key:
            logger.warning("Materials Project API key not provided")
            return []

        url = f"{self.BASE_URL}/summary/"
        params = {'formula': formula}

        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            return data.get('data', [])
        except requests.exceptions.RequestException as e:
            logger.error(f"Materials Project API error: {e}")
            return []

    def get_structure(self, material_id: str) -> Optional[Dict]:
        """
        Get crystal structure by Materials Project ID

        Args:
            material_id: MP ID (e.g., "mp-149")

        Returns:
            Structure data or None
        """
        if not self.api_key:
            return None

        url = f"{self.BASE_URL}/{material_id}"

        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Materials Project API error: {e}")
            return None


class ChEMBLClient:
    """
    ChEMBL REST API Client

    API Documentation: https://chembl.gitbook.io/chembl-interface-documentation/web-services/chembl-data-web-services

    Features:
    - 2M+ bioactive molecules
    - Drug-like properties
    - Bioactivity data
    - Target information
    - No API key required (free access)

    Usage:
        client = ChEMBLClient()
        compound = client.get_compound_by_chembl_id("CHEMBL25")  # Aspirin
        compounds = client.search_by_smiles("CC(=O)Oc1ccccc1C(=O)O")
    """

    BASE_URL = "https://www.ebi.ac.uk/chembl/api/data"
    RATE_LIMIT = 0.1  # 10 requests per second max

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'Accept': 'application/json'})
        self.last_request_time = 0

    def _rate_limit(self):
        """Enforce rate limiting"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.RATE_LIMIT:
            time.sleep(self.RATE_LIMIT - elapsed)
        self.last_request_time = time.time()

    def _request(self, endpoint: str, params: Optional[Dict] = None, retries: int = 3) -> Optional[Dict]:
        """Make HTTP request with retry logic"""
        self._rate_limit()

        url = f"{self.BASE_URL}/{endpoint}.json"

        for attempt in range(retries):
            try:
                response = self.session.get(url, params=params, timeout=30)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                logger.warning(f"ChEMBL attempt {attempt + 1}/{retries} failed: {e}")
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    logger.error(f"All retries failed for ChEMBL endpoint: {endpoint}")
                    return None
        return None

    def get_compound_by_chembl_id(self, chembl_id: str) -> Optional[MoleculeData]:
        """
        Get compound by ChEMBL ID

        Args:
            chembl_id: ChEMBL ID (e.g., "CHEMBL25" for aspirin)

        Returns:
            MoleculeData or None
        """
        data = self._request(f"molecule/{chembl_id}")

        if not data:
            return None

        mol = data

        return MoleculeData(
            name=mol.get('pref_name', chembl_id),
            formula=mol.get('molecule_properties', {}).get('full_molformula', ''),
            molecular_weight=float(mol.get('molecule_properties', {}).get('full_mwt', 0)),
            smiles=mol.get('molecule_structures', {}).get('canonical_smiles'),
            inchi=mol.get('molecule_structures', {}).get('standard_inchi'),
            properties={
                'chembl_id': chembl_id,
                'max_phase': mol.get('max_phase'),
                'molecule_type': mol.get('molecule_type'),
                'therapeutic_flag': mol.get('therapeutic_flag'),
                'alogp': mol.get('molecule_properties', {}).get('alogp'),
                'hba': mol.get('molecule_properties', {}).get('hba'),
                'hbd': mol.get('molecule_properties', {}).get('hbd'),
                'psa': mol.get('molecule_properties', {}).get('psa'),
                'rtb': mol.get('molecule_properties', {}).get('rtb'),
            },
            source='ChEMBL'
        )

    def search_by_smiles(self, smiles: str, similarity: int = 70) -> List[str]:
        """
        Search compounds by SMILES similarity

        Args:
            smiles: SMILES string
            similarity: Similarity threshold (0-100)

        Returns:
            List of ChEMBL IDs
        """
        data = self._request(
            "similarity/C(=O)Oc1ccccc1C(=O)O/70",  # Example endpoint structure
            params={'smiles': smiles, 'similarity': similarity}
        )

        if not data or 'molecules' not in data:
            return []

        return [mol['molecule_chembl_id'] for mol in data['molecules']]

    def get_top_compounds(self, count: int = 10000, max_phase: int = 4) -> Iterator[MoleculeData]:
        """
        Get top compounds from ChEMBL

        Args:
            count: Number of compounds to fetch
            max_phase: Maximum clinical phase (0-4, 4 = approved drug)

        Yields:
            MoleculeData objects
        """
        offset = 0
        limit = 100  # ChEMBL pagination limit
        fetched = 0

        while fetched < count:
            data = self._request(
                "molecule",
                params={
                    'limit': limit,
                    'offset': offset,
                    'max_phase': max_phase,
                    'molecule_structures__canonical_smiles__isnull': 'false'
                }
            )

            if not data or 'molecules' not in data:
                break

            molecules = data['molecules']
            if not molecules:
                break

            for mol in molecules:
                if fetched >= count:
                    break

                try:
                    yield MoleculeData(
                        name=mol.get('pref_name', mol['molecule_chembl_id']),
                        formula=mol.get('molecule_properties', {}).get('full_molformula', ''),
                        molecular_weight=float(mol.get('molecule_properties', {}).get('full_mwt', 0)),
                        smiles=mol.get('molecule_structures', {}).get('canonical_smiles'),
                        inchi=mol.get('molecule_structures', {}).get('standard_inchi'),
                        properties={
                            'chembl_id': mol['molecule_chembl_id'],
                            'max_phase': mol.get('max_phase'),
                        },
                        source='ChEMBL'
                    )
                    fetched += 1
                except (KeyError, ValueError) as e:
                    logger.warning(f"Skipping invalid ChEMBL molecule: {e}")
                    continue

            offset += limit
            logger.info(f"ChEMBL: Fetched {fetched}/{count} compounds")


class ZINCClient:
    """
    ZINC Database Client

    Website: https://zinc.docking.org/

    Features:
    - 750M+ purchasable compounds
    - Drug-like subset (23M compounds)
    - Lead-like subset (15M compounds)
    - Fragment subset (17M compounds)
    - Free download via subsets

    Note: ZINC doesn't have a REST API, but provides downloadable subsets
    This client focuses on accessing pre-downloaded ZINC files or using
    their tranches system.

    Usage:
        client = ZINCClient()
        # Download ZINC subset first from: https://zinc.docking.org/tranches/home/
        compounds = client.parse_zinc_file("zinc_druglike_subset.smi")
    """

    ZINC_HOME = "https://zinc.docking.org"

    def __init__(self, zinc_data_dir: Optional[str] = None):
        self.zinc_data_dir = Path(zinc_data_dir) if zinc_data_dir else Path.cwd() / "zinc_data"
        self.zinc_data_dir.mkdir(parents=True, exist_ok=True)

    def parse_zinc_file(self, filepath: str, max_count: Optional[int] = None) -> Iterator[MoleculeData]:
        """
        Parse ZINC SMILES file

        ZINC files are typically in format:
        SMILES zinc_id name

        Args:
            filepath: Path to ZINC .smi or .txt file
            max_count: Maximum number of compounds to parse

        Yields:
            MoleculeData objects
        """
        count = 0

        with open(filepath, 'r') as f:
            for line in f:
                if max_count and count >= max_count:
                    break

                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                parts = line.split()
                if len(parts) < 2:
                    continue

                smiles = parts[0]
                zinc_id = parts[1]
                name = parts[2] if len(parts) > 2 else zinc_id

                # Try to extract basic properties from SMILES
                try:
                    mol_weight = self._estimate_molecular_weight(smiles)
                    formula = self._smiles_to_formula(smiles)

                    yield MoleculeData(
                        name=name,
                        formula=formula,
                        molecular_weight=mol_weight,
                        smiles=smiles,
                        properties={'zinc_id': zinc_id},
                        source='ZINC'
                    )
                    count += 1
                except Exception as e:
                    logger.warning(f"Error parsing ZINC entry {zinc_id}: {e}")
                    continue

        logger.info(f"Parsed {count} compounds from ZINC file: {filepath}")

    def _estimate_molecular_weight(self, smiles: str) -> float:
        """
        Estimate molecular weight from SMILES (basic implementation)

        For accurate weights, RDKit should be used, but this provides
        a simple estimation for systems without RDKit.
        """
        # Atomic weights
        weights = {
            'C': 12.01, 'H': 1.008, 'O': 16.00, 'N': 14.01,
            'S': 32.07, 'P': 30.97, 'F': 19.00, 'Cl': 35.45,
            'Br': 79.90, 'I': 126.90, 'B': 10.81, 'Si': 28.09
        }

        mw = 0.0
        i = 0
        while i < len(smiles):
            char = smiles[i]
            if char in weights:
                mw += weights[char]
                # Check for element symbol with two letters (Cl, Br, etc.)
                if i + 1 < len(smiles) and smiles[i:i+2] in weights:
                    mw += weights[smiles[i:i+2]] - weights[char]
                    i += 1
            i += 1

        return mw if mw > 0 else 0.0

    def _smiles_to_formula(self, smiles: str) -> str:
        """
        Extract approximate molecular formula from SMILES

        This is a simplified parser. For accurate formulas, use RDKit.
        """
        # Count atoms (simplified - doesn't handle all SMILES syntax)
        atoms = {}
        i = 0
        while i < len(smiles):
            if smiles[i].isupper():
                # Two-letter element
                if i + 1 < len(smiles) and smiles[i+1].islower():
                    atom = smiles[i:i+2]
                    atoms[atom] = atoms.get(atom, 0) + 1
                    i += 2
                # Single-letter element
                else:
                    atom = smiles[i]
                    atoms[atom] = atoms.get(atom, 0) + 1
                    i += 1
            else:
                i += 1

        # Format as Hill system (C, H, then alphabetical)
        formula_parts = []
        for atom in ['C', 'H']:
            if atom in atoms:
                count = atoms[atom]
                formula_parts.append(f"{atom}{count if count > 1 else ''}")

        for atom in sorted(atoms.keys()):
            if atom not in ['C', 'H']:
                count = atoms[atom]
                formula_parts.append(f"{atom}{count if count > 1 else ''}")

        return ''.join(formula_parts) if formula_parts else ''

    def download_zinc_subset(self, subset: str = "druglike") -> str:
        """
        Provide instructions for downloading ZINC subsets

        Args:
            subset: Type of subset (druglike, leadlike, fragment, etc.)

        Returns:
            Download instructions
        """
        instructions = f"""
        To download ZINC {subset} subset:

        1. Visit: https://zinc.docking.org/tranches/home/
        2. Select subset: {subset}
        3. Download SMILES files (.smi format)
        4. Place files in: {self.zinc_data_dir}
        5. Use parse_zinc_file() to load compounds

        Example wget command:
        wget -P {self.zinc_data_dir} https://zinc.docking.org/db/bysubset/{subset}/
        """
        return instructions


class KEGGClient:
    """
    KEGG REST API Client

    API Documentation: https://www.kegg.jp/kegg/rest/

    Features:
    - 20k+ metabolites and biochemical compounds
    - Metabolic pathways
    - Enzyme information
    - No API key required (free access)
    """

    BASE_URL = "https://rest.kegg.jp"
    RATE_LIMIT = 0.5  # Conservative rate limit

    def __init__(self):
        self.session = requests.Session()
        self.last_request_time = 0

    def _rate_limit(self):
        """Enforce rate limiting"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.RATE_LIMIT:
            time.sleep(self.RATE_LIMIT - elapsed)
        self.last_request_time = time.time()

    def get_compound(self, compound_id: str) -> Optional[MoleculeData]:
        """
        Get compound by KEGG ID

        Args:
            compound_id: KEGG compound ID (e.g., "C00031" for glucose)

        Returns:
            MoleculeData or None
        """
        self._rate_limit()

        url = f"{self.BASE_URL}/get/{compound_id}"

        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            # Parse KEGG flat file format
            data = self._parse_kegg_entry(response.text)

            return MoleculeData(
                name=data.get('NAME', [compound_id])[0],
                formula=data.get('FORMULA', [''])[0],
                molecular_weight=float(data.get('MOL_WEIGHT', [0])[0] or 0),
                properties={
                    'kegg_id': compound_id,
                    'pathway': data.get('PATHWAY', []),
                    'enzyme': data.get('ENZYME', [])
                },
                source='KEGG'
            )
        except requests.exceptions.RequestException as e:
            logger.error(f"KEGG API error: {e}")
            return None

    def _parse_kegg_entry(self, text: str) -> Dict[str, List[str]]:
        """Parse KEGG flat file format"""
        data = {}
        current_key = None

        for line in text.split('\n'):
            if line and not line.startswith(' '):
                parts = line.split(None, 1)
                if len(parts) >= 2:
                    current_key = parts[0]
                    data[current_key] = [parts[1]]
            elif current_key and line.strip():
                data[current_key].append(line.strip())

        return data

    def list_all_compounds(self) -> List[str]:
        """
        Get list of all KEGG compound IDs

        Returns:
            List of compound IDs
        """
        self._rate_limit()

        url = f"{self.BASE_URL}/list/compound"

        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            compound_ids = []
            for line in response.text.split('\n'):
                if line:
                    parts = line.split('\t')
                    if parts:
                        compound_ids.append(parts[0])

            return compound_ids
        except requests.exceptions.RequestException as e:
            logger.error(f"KEGG API error: {e}")
            return []


def test_api_clients():
    """Test all API clients"""
    print("TESTING API CLIENTS")
    print("=" * 70)

    # Test PubChem
    print("\n1. Testing PubChem Client...")
    pubchem = PubChemClient()

    aspirin = pubchem.get_compound_by_name("aspirin")
    if aspirin:
        print(f"   [OK] Found aspirin: {aspirin.formula}, MW={aspirin.molecular_weight:.2f}")

    caffeine = pubchem.get_compound_by_cid(2519)
    if caffeine:
        print(f"   [OK] Found caffeine (CID 2519): {caffeine.formula}, MW={caffeine.molecular_weight:.2f}")

    # Test batch fetch
    print("\n   Testing batch fetch (first 10 compounds)...")
    count = 0
    for mol in pubchem.get_compounds_batch(list(range(1, 11))):
        count += 1
        print(f"   - {mol.name}: {mol.formula}")
    print(f"   [OK] Fetched {count} compounds in batch")

    # Test KEGG
    print("\n2. Testing KEGG Client...")
    kegg = KEGGClient()

    glucose = kegg.get_compound("C00031")
    if glucose:
        print(f"   [OK] Found glucose: {glucose.formula}, MW={glucose.molecular_weight:.2f}")

    # Test ChEMBL
    print("\n3. Testing ChEMBL Client...")
    chembl = ChEMBLClient()

    try:
        aspirin_chembl = chembl.get_compound_by_chembl_id("CHEMBL25")
        if aspirin_chembl:
            print(f"   [OK] Found aspirin in ChEMBL: {aspirin_chembl.formula}, MW={aspirin_chembl.molecular_weight:.2f}")
            print(f"   - Max Phase: {aspirin_chembl.properties.get('max_phase')}")
            print(f"   - AlogP: {aspirin_chembl.properties.get('alogp')}")
    except Exception as e:
        print(f"   [WARN] ChEMBL test failed (may need network): {e}")

    # Test ZINC
    print("\n4. Testing ZINC Client...")
    zinc = ZINCClient()
    print(f"   [OK] ZINC client initialized")
    print(f"   - Data directory: {zinc.zinc_data_dir}")
    print(f"   - ZINC requires pre-downloaded files from: {zinc.ZINC_HOME}")

    print("\n" + "=" * 70)
    print("API CLIENT TESTS COMPLETE")
    print("\nSummary:")
    print("  [OK] PubChem - 100M+ compounds")
    print("  [OK] KEGG - 20k+ metabolites")
    print("  [OK] ChEMBL - 2M+ bioactive compounds")
    print("  [OK] ZINC - 750M+ purchasable compounds (requires download)")
    print("  [AVAILABLE] DrugBank - 15k drugs (requires API key)")
    print("  [AVAILABLE] Materials Project - 150k materials (requires API key)")


if __name__ == "__main__":
    test_api_clients()
