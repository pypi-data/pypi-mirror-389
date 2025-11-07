# Nuevas Fuentes de Datos - ChEMBL y ZINC
## Expansión de Fuentes para Materials-SimPro

**Fecha**: 2025-11-04
**Estado**: Implementado
**Impacto**: +752M compuestos adicionales disponibles

---

## Resumen Ejecutivo

Se han integrado **2 nuevas fuentes de datos** masivas al sistema de ingesta de Materials-SimPro:

| Fuente | Compuestos | Tipo | API | Estado |
|--------|------------|------|-----|--------|
| **ChEMBL** | 2M+ | Bioactivos | REST (gratis) | Listo |
| **ZINC** | 750M+ | Comprables | Archivo descargable | Listo |

**Total anterior**: ~100M compuestos (PubChem, KEGG, DrugBank, Materials Project)
**Total ahora**: ~852M+ compuestos
**Incremento**: 752% más compuestos disponibles

---

## 1. ChEMBL - Compuestos Bioactivos

### Descripción

ChEMBL es una base de datos de bioactividad de moléculas con actividad similar a fármacos, mantenida por el Instituto Europeo de Bioinformática (EMBL-EBI).

### Características

- **2M+ compuestos bioactivos** con datos experimentales
- **Datos farmacológicos**: IC50, Ki, EC50
- **Información de objetivos**: proteínas, enzimas, receptores
- **Propiedades ADME**: AlogP, PSA, HBA, HBD, RTB
- **Fases clínicas**: 0 (preclinical) a 4 (aprobado)
- **API REST gratis**: No requiere API key
- **Rate limit**: 10 req/seg

### Implementación

```python
# src/database/api_clients.py
class ChEMBLClient:
    BASE_URL = "https://www.ebi.ac.uk/chembl/api/data"
    RATE_LIMIT = 0.1  # 10 requests/second

    def get_compound_by_chembl_id(self, chembl_id: str)
    def search_by_smiles(self, smiles: str, similarity: int)
    def get_top_compounds(self, count: int, max_phase: int)
```

### Uso

```bash
# Ingerir compuestos bioactivos de ChEMBL
python ingest_complete_knowledge.py --source chembl --count 50000 --workers 4

# Solo fármacos aprobados (max_phase=4)
python ingest_complete_knowledge.py --source chembl --count 10000

# Modo background con checkpoint
nohup python ingest_complete_knowledge.py --source chembl --count 2000000 --workers 8 &
```

### Datos Extraídos

Para cada compuesto:
- **Estructura**: SMILES, InChI
- **Propiedades básicas**: Fórmula, peso molecular
- **Propiedades calculadas**: AlogP, PSA, HBA, HBD, RTB
- **Metadatos**: ChEMBL ID, fase clínica, tipo de molécula

### Ventajas

- Compuestos de alta calidad con actividad biológica validada
- Ideal para drug discovery y virtual screening
- Propiedades farmacológicas pre-calculadas
- API estable y bien documentada

---

## 2. ZINC - Compuestos Comprables

### Descripción

ZINC es una base de datos curada de compuestos químicos disponibles comercialmente para virtual screening, mantenida por el Shoichet Laboratory de UCSF.

### Características

- **750M+ compuestos comercialmente disponibles**
- **23M compuestos drug-like** (subset recomendado)
- **15M compuestos lead-like** para drug discovery
- **17M fragmentos** para fragment-based design
- **Tranches**: organizados por propiedades fisicoquímicas
- **Gratuito**: Descarga directa sin registro

### Subsets Disponibles

| Subset | Compuestos | Tamaño | Uso |
|--------|------------|---------|-----|
| **Drug-like** | 23M | ~5 GB | Screening general |
| **Lead-like** | 15M | ~3 GB | Desarrollo de leads |
| **Fragment** | 17M | ~1 GB | Fragment-based design |
| **Biogenic** | 500k | ~100 MB | Natural product-like |
| **Complete** | 750M | ~150 GB | Investigación avanzada |

### Implementación

```python
# src/database/api_clients.py
class ZINCClient:
    ZINC_HOME = "https://zinc.docking.org"

    def parse_zinc_file(self, filepath: str, max_count: int)
    def _estimate_molecular_weight(self, smiles: str)
    def _smiles_to_formula(self, smiles: str)
    def download_zinc_subset(self, subset: str)
```

### Descarga de Datos

1. **Visitar**: https://zinc.docking.org/tranches/home/
2. **Seleccionar subset**: drug-like, lead-like, etc.
3. **Descargar archivos SMILES** (.smi format)
4. **Colocar en directorio**: `zinc_data/`

```bash
# Ejemplo: Descargar drug-like subset
wget -P zinc_data/ https://zinc.docking.org/db/bysubset/druglike/

# O descarga específica de tranche
wget https://zinc.docking.org/tranches/AAAA.smi
```

### Uso

```bash
# Ingerir desde archivo ZINC pre-descargado
python ingest_complete_knowledge.py --source zinc --zinc-file zinc_data/druglike.smi --count 100000

# Ingerir drug-like complete
python ingest_complete_knowledge.py --source zinc --zinc-file zinc_druglike_complete.smi --count 23000000 --workers 8

# Background ingestion
nohup python ingest_complete_knowledge.py --source zinc --zinc-file zinc_all.smi --count 750000000 --workers 16 &
```

### Formato de Archivo

ZINC usa formato SMILES:
```
CC(C)CC1=CC=C(C=C1)C(C)C(=O)O ZINC000000000001 Ibuprofen
CC(=O)OC1=CC=CC=C1C(=O)O ZINC000000000002 Aspirin
```

### Ventajas

- Compuestos disponibles comercialmente (comprables)
- Volumen masivo: 750M compuestos
- Sin límites de rate limit (descarga local)
- Organización por propiedades fisicoquímicas

---

## Comparación con Fuentes Existentes

### Tabla Completa de Fuentes

| Fuente | Compuestos | Tipo | API | Key | Estado |
|--------|------------|------|-----|-----|--------|
| **PubChem** | 100M+ | General | REST | No | ✅ Activo |
| **ChEMBL** | 2M+ | Bioactivos | REST | No | ✅ Nuevo |
| **ZINC** | 750M+ | Comprables | Archivo | No | ✅ Nuevo |
| **KEGG** | 20k | Metabolitos | REST | No | ✅ Activo |
| **DrugBank** | 15k | Fármacos | REST | Sí | ⏸️ Requiere key |
| **Materials Project** | 150k | Materiales | REST | Sí | ⏸️ Requiere key |

### Distribución por Categoría

```
General (PubChem):                100,000,000 ████████████████████
Comprables (ZINC):                750,000,000 ████████████████████████████████████████████████████████████
Bioactivos (ChEMBL):                2,000,000 █
Metabolitos (KEGG):                    20,000
Fármacos (DrugBank):                   15,000
Materiales (Materials Project):       150,000
───────────────────────────────────────────────────────────────────
TOTAL:                            852,185,000 compuestos
```

---

## Arquitectura Técnica

### API Clients (api_clients.py)

Nuevas clases añadidas:

```python
class ChEMBLClient:
    """
    ChEMBL REST API Client
    - Rate limiting: 10 req/sec
    - Retry logic con backoff exponencial
    - Paginación automática
    """

class ZINCClient:
    """
    ZINC File Parser
    - Parseo de formato SMILES
    - Estimación de peso molecular
    - Conversión SMILES → fórmula
    """
```

### Parallel Loader (parallel_loader.py)

Nuevos métodos añadidos:

```python
class ParallelMoleculeLoader:
    def load_from_chembl(self, count, max_phase, checkpoint_file):
        """
        - Multiprocessing con 4-16 workers
        - Checkpoint cada 10,000 compuestos
        - Progress tracking con ETA
        """

    def load_from_zinc_file(self, filepath, max_count):
        """
        - Parseo de archivos SMILES
        - Batch insertion (1000 por lote)
        - Sin límite de rate (archivo local)
        """
```

### Ingestion Script (ingest_complete_knowledge.py)

```bash
# Nuevas opciones añadidas
--source chembl    # Ingerir de ChEMBL
--source zinc      # Ingerir de ZINC
--zinc-file PATH   # Especificar archivo ZINC

# Ejemplos
python ingest_complete_knowledge.py --source chembl --count 50000
python ingest_complete_knowledge.py --source zinc --zinc-file zinc_druglike.smi
```

---

## Performance Estimado

### ChEMBL

- **Rate limit API**: 10 req/seg
- **Batch size**: 100 compuestos/request
- **Throughput teórico**: 1,000 compuestos/seg
- **Throughput real**: ~500 compuestos/seg (overhead)

**Tiempos estimados**:
- 10,000 compuestos: 20 segundos
- 100,000 compuestos: 3.3 minutos
- 1,000,000 compuestos: 33 minutos
- 2,000,000 compuestos completos: **1.1 horas**

### ZINC

- **Sin rate limit** (archivo local)
- **Parseo**: ~10,000 líneas/seg
- **Inserción DB**: ~1,000 compuestos/seg (batch insert)

**Tiempos estimados**:
- 100,000 compuestos: 1.7 minutos
- 1,000,000 compuestos: 17 minutos
- 23,000,000 compuestos (drug-like): **6.4 horas**
- 750,000,000 compuestos completos: **8.7 días**

---

## Estrategia de Ingesta Recomendada

### Para Desarrollo/Testing

```bash
# 1. Datos existentes (617 estructuras)
python ingest_complete_knowledge.py --source existing

# 2. KEGG metabolitos (20k)
python ingest_complete_knowledge.py --source kegg

# 3. ChEMBL bioactivos aprobados (10k)
python ingest_complete_knowledge.py --source chembl --count 10000

# Total: ~30k estructuras en <5 minutos
```

### Para Investigación General

```bash
# 1. PubChem top 100k
python ingest_complete_knowledge.py --source pubchem --count 100000

# 2. ChEMBL bioactivos (100k)
python ingest_complete_knowledge.py --source chembl --count 100000

# 3. ZINC drug-like (100k)
python ingest_complete_knowledge.py --source zinc --zinc-file zinc_druglike.smi --count 100000

# Total: ~300k estructuras en <20 minutos
```

### Para Instituciones (Laptop Dedicada)

```bash
# Ingesta completa 24/7
nohup python ingest_complete_knowledge.py --source all --count 100000000 --workers 16 &

# O por fuente (paralelo en múltiples terminales)
nohup python ingest_complete_knowledge.py --source pubchem --count 100000000 --workers 8 &
nohup python ingest_complete_knowledge.py --source chembl --count 2000000 --workers 4 &
nohup python ingest_complete_knowledge.py --source zinc --zinc-file zinc_complete.smi --count 750000000 --workers 4 &

# Total: ~852M estructuras en ~2-3 meses
```

---

## Tamaño de Base de Datos

### Actualización de Estimaciones

| Dataset | Estructuras | Tamaño DB | Tiempo Ingesta |
|---------|-------------|-----------|----------------|
| Mínimo | 30k | 10 MB | 5 min |
| Estándar | 300k | 100 MB | 20 min |
| Grande | 3M | 1 GB | 3 horas |
| **Completa (nuevo)** | **852M** | **~280 GB** | **2-3 meses** |

**Nota**: Estimación basada en 330 bytes/estructura promedio

---

## Casos de Uso

### 1. Drug Discovery

```bash
# Fármacos aprobados + bioactivos + drug-like
python ingest_complete_knowledge.py --source chembl --count 100000
python ingest_complete_knowledge.py --source zinc --zinc-file zinc_druglike.smi --count 1000000
```

**Uso**: Screening virtual de candidatos a fármacos

### 2. Lead Optimization

```bash
# Lead-like subset de ZINC + ChEMBL fase 1-3
python ingest_complete_knowledge.py --source zinc --zinc-file zinc_leadlike.smi --count 1000000
```

**Uso**: Optimización de compounds leads

### 3. Fragment-Based Design

```bash
# Fragment subset de ZINC
python ingest_complete_knowledge.py --source zinc --zinc-file zinc_fragment.smi --count 500000
```

**Uso**: Diseño basado en fragmentos

### 4. Investigación Académica

```bash
# Todo lo disponible
python ingest_complete_knowledge.py --source all --count 10000000 --workers 8
```

**Uso**: Investigación general, machine learning, cheminformatics

---

## Testing

### Test ChEMBL

```bash
cd G:\Materials-SimPro
python -c "
from src.database.api_clients import ChEMBLClient

client = ChEMBLClient()
aspirin = client.get_compound_by_chembl_id('CHEMBL25')

print(f'Name: {aspirin.name}')
print(f'Formula: {aspirin.formula}')
print(f'MW: {aspirin.molecular_weight}')
print(f'SMILES: {aspirin.smiles}')
print(f'Max Phase: {aspirin.properties[\"max_phase\"]}')
"
```

### Test ZINC

```bash
# Crear archivo de prueba
echo "CC(=O)OC1=CC=CC=C1C(=O)O ZINC000000000001 Aspirin" > test_zinc.smi
echo "CC(C)CC1=CC=C(C=C1)C(C)C(=O)O ZINC000000000002 Ibuprofen" >> test_zinc.smi

# Probar parseo
python -c "
from src.database.api_clients import ZINCClient

client = ZINCClient()
for mol in client.parse_zinc_file('test_zinc.smi'):
    print(f'{mol.name}: {mol.formula}, MW={mol.molecular_weight:.2f}')
"
```

---

## Próximos Pasos

### ✅ Completado

- [x] Implementar ChEMBLClient con API REST
- [x] Implementar ZINCClient para archivos SMILES
- [x] Añadir load_from_chembl() a ParallelMoleculeLoader
- [x] Añadir load_from_zinc_file() a ParallelMoleculeLoader
- [x] Integrar en ingest_complete_knowledge.py
- [x] Actualizar documentación y ejemplos

### 🔄 En Progreso

- [ ] Crear guía para laptop dedicada 24/7
- [ ] Configurar monitoreo de ingesta continua
- [ ] Scripts de automatización y checkpointing

### 📋 Pendiente

- [ ] Añadir más subsets de ZINC (biogenic, natural products)
- [ ] Implementar filtros por propiedades fisicoquímicas
- [ ] Añadir validación de estructuras con RDKit
- [ ] Integrar DrugBank (requiere API key)
- [ ] Integrar Materials Project (requiere API key)

---

## Conclusión

Con la integración de **ChEMBL** y **ZINC**, Materials-SimPro ahora tiene acceso a:

- **852M+ compuestos** totales (vs 100M anteriormente)
- **6 fuentes de datos** diferentes
- **Cobertura completa**: desde metabolitos hasta materiales
- **Flexibilidad**: API en tiempo real + archivos bulk

El sistema está listo para ingesta a escala institucional en laptop dedicada 24/7.

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>

---

**Fecha**: 2025-11-04
**Versión**: 1.1.0
**Estado**: Nuevas Fuentes Implementadas
**Archivos Modificados**:
- `src/database/api_clients.py` (+365 líneas)
- `src/database/parallel_loader.py` (+140 líneas)
- `ingest_complete_knowledge.py` (+89 líneas)
