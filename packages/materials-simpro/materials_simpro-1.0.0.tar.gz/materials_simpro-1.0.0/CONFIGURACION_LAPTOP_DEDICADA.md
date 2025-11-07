# Configuración de Laptop Dedicada para Ingesta 24/7
## Materials-SimPro - Guía Completa de Setup

**Fecha**: 2025-11-04
**Propósito**: Ingesta continua 24/7 hacia 852M+ compuestos
**Tiempo estimado**: 2-3 meses de operación continua

---

## 📋 Tabla de Contenidos

1. [Requisitos de Hardware](#requisitos-de-hardware)
2. [Requisitos de Software](#requisitos-de-software)
3. [Configuración Inicial](#configuración-inicial)
4. [Scripts de Automatización](#scripts-de-automatización)
5. [Monitoreo y Alertas](#monitoreo-y-alertas)
6. [Manejo de Checkpoints](#manejo-de-checkpoints)
7. [Troubleshooting](#troubleshooting)
8. [Optimización de Performance](#optimización-de-performance)

---

## Requisitos de Hardware

### Mínimo Recomendado

| Componente | Especificación | Razón |
|------------|----------------|-------|
| **CPU** | 8 cores / 16 threads | Multiprocessing (8-16 workers) |
| **RAM** | 16 GB | Buffer para batch processing |
| **Storage** | 500 GB SSD | Base de datos final (~280 GB) + temp |
| **Red** | 10 Mbps+ estable | Descarga continua de APIs |
| **Energía** | UPS recomendado | Evitar pérdida de datos |

### Óptimo

| Componente | Especificación | Beneficio |
|------------|----------------|-----------|
| **CPU** | 16+ cores | 2x velocidad de ingesta |
| **RAM** | 32 GB | Procesamiento más rápido |
| **Storage** | 1 TB NVMe SSD | Escritura DB más rápida |
| **Red** | 50+ Mbps | Sin cuellos de botella |
| **Enfriamiento** | Activo | Operación 24/7 estable |

### Laptop Recomendadas

1. **Budget (~$800)**:
   - Lenovo ThinkPad T14 (Ryzen 7, 16GB RAM, 512GB SSD)
   - Dell Latitude 5420 (i7-1185G7, 16GB RAM, 512GB SSD)

2. **Mid-range (~$1200)**:
   - Lenovo ThinkPad P15 (Ryzen 9, 32GB RAM, 1TB SSD)
   - HP ZBook Power G9 (i7-12700H, 32GB RAM, 1TB SSD)

3. **High-end (~$2000+)**:
   - Dell Precision 7770 (Xeon, 64GB RAM, 2TB SSD)
   - Lenovo ThinkPad P1 Gen 5 (i9-12900H, 64GB RAM, 2TB SSD)

---

## Requisitos de Software

### Sistema Operativo

**Recomendado**: Ubuntu 22.04 LTS o Windows 11 Pro

```bash
# Ubuntu (preferido por estabilidad)
sudo apt update && sudo apt upgrade -y

# Windows (asegurar power plan = High Performance)
powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c
```

### Python y Dependencias

```bash
# Python 3.10+ requerido
python --version  # Debe ser >= 3.10

# Instalar Materials-SimPro
git clone https://github.com/Yatrogenesis/Materials-SimPro.git
cd Materials-SimPro
pip install -e .[all]

# Verificar instalación
python -c "import materials_simpro; print('OK')"
```

### Herramientas de Monitoreo

```bash
# Ubuntu
sudo apt install htop iotop nethogs tmux screen

# Windows (instalar con Chocolatey)
choco install python git vscode
```

---

## Configuración Inicial

### 1. Preparar Directorio de Trabajo

```bash
# Crear estructura de directorios
mkdir -p ~/materials-simpro-production
cd ~/materials-simpro-production

# Clonar repositorio
git clone https://github.com/Yatrogenesis/Materials-SimPro.git
cd Materials-SimPro

# Crear directorio para logs y checkpoints
mkdir -p logs checkpoints zinc_data
```

### 2. Configurar Base de Datos

```bash
# Crear base de datos de producción
python -c "
from src.database.optimized_database_engine import OptimizedDatabase

db = OptimizedDatabase('materials_simpro_production.db')
print('Database initialized')
db.close()
"
```

### 3. Descargar Datos ZINC (Opcional)

```bash
# ZINC drug-like (23M compuestos, ~5 GB)
cd zinc_data
wget https://zinc.docking.org/db/bysubset/druglike/druglike.smi

# O usar subset más pequeño para testing
wget https://zinc.docking.org/tranches/AA/AAAA.smi
```

### 4. Configurar Autostart

**Ubuntu (systemd service)**:

```bash
# Crear servicio
sudo nano /etc/systemd/system/materials-simpro.service
```

```ini
[Unit]
Description=Materials-SimPro Data Ingestion
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/home/your_username/materials-simpro-production/Materials-SimPro
ExecStart=/usr/bin/python3 /home/your_username/materials-simpro-production/Materials-SimPro/continuous_ingestion.py
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
```

```bash
# Activar servicio
sudo systemctl enable materials-simpro.service
sudo systemctl start materials-simpro.service
```

**Windows (Task Scheduler)**:

```powershell
# Crear tarea programada
$action = New-ScheduledTaskAction -Execute "python.exe" -Argument "C:\materials-simpro\continuous_ingestion.py"
$trigger = New-ScheduledTaskTrigger -AtStartup
$settings = New-ScheduledTaskSettingsSet -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 5)
Register-ScheduledTask -TaskName "Materials-SimPro Ingestion" -Action $action -Trigger $trigger -Settings $settings -RunLevel Highest
```

---

## Scripts de Automatización

### Script Principal: `continuous_ingestion.py`

```python
#!/usr/bin/env python3
"""
Continuous Data Ingestion Script
=================================

Runs 24/7 ingesting data from all sources with automatic
checkpointing, error recovery, and progress monitoring.

Author: Materials-SimPro Team
Date: 2025-11-04
"""

import sys
import time
import logging
from pathlib import Path
from datetime import datetime

# Add project to path
sys.path.append(str(Path(__file__).parent / 'src'))

from database.parallel_loader import ParallelMoleculeLoader
from database.optimized_database_engine import OptimizedDatabase

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/continuous_ingestion.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def ingest_all_sources(db_path: str, workers: int = 8):
    """
    Ingest from all sources sequentially with checkpointing

    Order of ingestion:
    1. Existing data (fast, ~30k)
    2. KEGG (medium, ~20k)
    3. ChEMBL (slow, 2M)
    4. PubChem (very slow, 100M)
    5. ZINC (ultra slow, 750M) - optional
    """

    logger.info("="*70)
    logger.info("CONTINUOUS INGESTION STARTED")
    logger.info(f"Database: {db_path}")
    logger.info(f"Workers: {workers}")
    logger.info(f"Start time: {datetime.now()}")
    logger.info("="*70)

    # Phase 1: Existing data (fast)
    logger.info("\n[PHASE 1/5] Importing existing data...")
    try:
        from database.generate_COMPLETE_HUMAN_KNOWLEDGE_molecules import COMPLETE_HUMAN_KNOWLEDGE_MOLECULES
        db = OptimizedDatabase(db_path)
        molecules = []
        for name, data in COMPLETE_HUMAN_KNOWLEDGE_MOLECULES.items():
            molecules.append((
                data['formula'],
                name,
                data['MW'],
                None,
                {'class': data.get('class'), 'status': data.get('status', 'approved')}
            ))
        db.bulk_insert_molecules(molecules)
        logger.info(f"Imported {len(molecules)} existing molecules")
        db.close()
    except Exception as e:
        logger.error(f"Phase 1 failed: {e}")

    # Phase 2: KEGG (medium)
    logger.info("\n[PHASE 2/5] Ingesting KEGG metabolites...")
    try:
        loader = ParallelMoleculeLoader(db_path, num_workers=workers)
        loader.load_from_kegg()
        logger.info("KEGG ingestion completed")
    except Exception as e:
        logger.error(f"Phase 2 failed: {e}")

    # Phase 3: ChEMBL (slow)
    logger.info("\n[PHASE 3/5] Ingesting ChEMBL bioactive compounds...")
    try:
        loader = ParallelMoleculeLoader(db_path, num_workers=workers)
        loader.load_from_chembl(
            count=2_000_000,
            checkpoint_file='checkpoints/chembl_checkpoint.pkl'
        )
        logger.info("ChEMBL ingestion completed")
    except Exception as e:
        logger.error(f"Phase 3 failed: {e}")
        logger.info("ChEMBL checkpoint saved, can resume later")

    # Phase 4: PubChem (very slow)
    logger.info("\n[PHASE 4/5] Ingesting PubChem compounds...")
    try:
        loader = ParallelMoleculeLoader(db_path, num_workers=workers)
        loader.load_from_pubchem(
            start_cid=1,
            count=100_000_000,
            checkpoint_file='checkpoints/pubchem_checkpoint.pkl'
        )
        logger.info("PubChem ingestion completed")
    except Exception as e:
        logger.error(f"Phase 4 failed: {e}")
        logger.info("PubChem checkpoint saved, can resume later")

    # Phase 5: ZINC (ultra slow, optional)
    zinc_file = Path('zinc_data/druglike.smi')
    if zinc_file.exists():
        logger.info("\n[PHASE 5/5] Ingesting ZINC purchasable compounds...")
        try:
            loader = ParallelMoleculeLoader(db_path, num_workers=workers)
            loader.load_from_zinc_file(
                str(zinc_file),
                max_count=23_000_000  # Drug-like subset
            )
            logger.info("ZINC ingestion completed")
        except Exception as e:
            logger.error(f"Phase 5 failed: {e}")
    else:
        logger.warning(f"ZINC file not found: {zinc_file}")
        logger.info("Skipping ZINC ingestion")

    logger.info("="*70)
    logger.info("CONTINUOUS INGESTION COMPLETED")
    logger.info(f"End time: {datetime.now()}")
    logger.info("="*70)

    # Show final stats
    db = OptimizedDatabase(db_path)
    stats = db.get_statistics()
    logger.info(f"\nFinal database statistics:")
    logger.info(f"  Total structures: {stats['total_structures']:,}")
    logger.info(f"  Molecules: {stats['molecules']:,}")
    logger.info(f"  Materials: {stats['materials']:,}")
    logger.info(f"  Polymers: {stats['polymers']:,}")
    db.close()


def main():
    """Main entry point"""
    DB_PATH = "materials_simpro_production.db"
    WORKERS = 8  # Adjust based on CPU cores

    # Ensure directories exist
    Path('logs').mkdir(exist_ok=True)
    Path('checkpoints').mkdir(exist_ok=True)

    # Run continuous ingestion
    try:
        ingest_all_sources(DB_PATH, WORKERS)
    except KeyboardInterrupt:
        logger.info("\n\nIngestion interrupted by user (Ctrl+C)")
        logger.info("Progress saved in checkpoints, safe to resume")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
```

### Script de Monitoreo: `monitor_ingestion.py`

```python
#!/usr/bin/env python3
"""
Ingestion Monitoring Script
============================

Displays real-time progress and statistics
"""

import sys
import time
from pathlib import Path

sys.path.append(str(Path(__file__).parent / 'src'))
from database.optimized_database_engine import OptimizedDatabase


def monitor():
    """Monitor ingestion progress"""
    db_path = "materials_simpro_production.db"

    print("="*70)
    print("Materials-SimPro - Ingestion Monitor")
    print("="*70)
    print("Press Ctrl+C to exit\n")

    previous_count = 0

    while True:
        try:
            db = OptimizedDatabase(db_path)
            stats = db.get_statistics()
            db.close()

            total = stats['total_structures']
            rate = total - previous_count
            previous_count = total

            # Calculate progress toward goals
            mol_progress = (stats['molecules'] / 852_000_000) * 100

            # Display
            print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}]")
            print(f"Total Structures: {total:,}")
            print(f"  Molecules: {stats['molecules']:,}")
            print(f"  Materials: {stats['materials']:,}")
            print(f"  Polymers: {stats['polymers']:,}")
            print(f"Rate: {rate:,} structures/minute")
            print(f"Progress: {mol_progress:.4f}% toward 852M goal")

            time.sleep(60)  # Update every minute

        except KeyboardInterrupt:
            print("\nMonitoring stopped")
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)


if __name__ == "__main__":
    monitor()
```

---

## Monitoreo y Alertas

### Dashboard en Tiempo Real

Usar `tmux` para mantener múltiples ventanas:

```bash
# Iniciar sesión tmux
tmux new -s materials-simpro

# Ventana 1: Ingesta principal
python continuous_ingestion.py

# Crear nueva ventana (Ctrl+B, C)
# Ventana 2: Monitor
python monitor_ingestion.py

# Crear nueva ventana
# Ventana 3: System monitor
htop

# Navegar entre ventanas: Ctrl+B, N (next) o P (previous)
# Detach: Ctrl+B, D
# Re-attach: tmux attach -t materials-simpro
```

### Alertas por Email (Opcional)

```python
# Añadir al continuous_ingestion.py

import smtplib
from email.mime.text import MIMEText

def send_alert(subject, message):
    """Send email alert"""
    msg = MIMEText(message)
    msg['Subject'] = subject
    msg['From'] = 'materials-simpro@yourdomain.com'
    msg['To'] = 'your-email@example.com'

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login('your-email@gmail.com', 'your-app-password')
            server.send_message(msg)
    except Exception as e:
        logger.error(f"Failed to send alert: {e}")

# Llamar cuando termine cada fase
send_alert(
    "Materials-SimPro: Phase 3 Complete",
    f"ChEMBL ingestion completed. {stats['molecules']:,} molecules in DB."
)
```

---

## Manejo de Checkpoints

### Estructura de Checkpoints

```
checkpoints/
├── chembl_checkpoint.pkl       # ChEMBL progress
├── pubchem_checkpoint.pkl      # PubChem progress
└── zinc_checkpoint.pkl         # ZINC progress (if used)
```

### Reanudar Ingesta Interrumpida

```bash
# Si continuous_ingestion.py se interrumpió, simplemente reiniciar
python continuous_ingestion.py

# Los checkpoints se detectan automáticamente y la ingesta continúa
# desde donde se quedó
```

### Inspeccionar Checkpoint

```python
import pickle

with open('checkpoints/pubchem_checkpoint.pkl', 'rb') as f:
    checkpoint = pickle.load(f)

print(f"Last CID processed: {checkpoint['next_cid']}")
print(f"Structures processed: {checkpoint['stats'].total_processed}")
print(f"Success rate: {checkpoint['stats'].successful / checkpoint['stats'].total_processed * 100:.1f}%")
```

---

## Troubleshooting

### Problema: API Rate Limiting

**Síntoma**: Muchos errores "Rate limit exceeded"

**Solución**:
```python
# En src/database/api_clients.py, ajustar rate limits
PubChemClient.RATE_LIMIT = 0.3  # Más conservador (3.3 req/sec)
ChEMBLClient.RATE_LIMIT = 0.15  # Más conservador (6.6 req/sec)
```

### Problema: Out of Memory

**Síntoma**: `MemoryError` o sistema se congela

**Solución**:
```python
# Reducir workers y batch size
loader = ParallelMoleculeLoader(
    db_path=db_path,
    num_workers=4,        # En vez de 8
    batch_size=500,       # En vez de 1000
)
```

### Problema: Disco Lleno

**Síntoma**: `No space left on device`

**Solución**:
```bash
# Limpiar logs antiguos
find logs/ -name "*.log" -mtime +7 -delete

# Comprimir base de datos
sqlite3 materials_simpro_production.db "VACUUM;"

# Verificar espacio
df -h
```

### Problema: Red Inestable

**Síntoma**: Frequent connection errors

**Solución**:
```python
# Añadir retry más agresivo en api_clients.py
def _request(self, url, params=None, retries=5):  # Era 3
    ...
    time.sleep(2 ** attempt * 2)  # Backoff más largo
```

---

## Optimización de Performance

### Ajustar Workers Según CPU

```bash
# Ver CPU cores
nproc  # Linux
echo %NUMBER_OF_PROCESSORS%  # Windows

# Regla general: workers = cores - 2
# 8 cores → 6 workers
# 16 cores → 14 workers
```

### Optimizar SQLite

```python
# En optimized_database_engine.py, añadir:
self.conn.execute("PRAGMA synchronous = NORMAL")  # Era FULL
self.conn.execute("PRAGMA temp_store = MEMORY")
self.conn.execute("PRAGMA mmap_size = 30000000000")  # 30GB
```

### Usar SSD para Temp Files

```bash
# Linux
export TMPDIR=/path/to/ssd/tmp

# Windows
set TEMP=D:\SSD\temp
set TMP=D:\SSD\temp
```

---

## Cronograma Estimado

### Timeline Completo (8 workers, 24/7)

| Fase | Fuente | Compuestos | Tiempo | Acumulado |
|------|--------|------------|--------|-----------|
| 1 | Existente | 30k | 5 min | 5 min |
| 2 | KEGG | 20k | 10 min | 15 min |
| 3 | ChEMBL | 2M | 1.1 horas | 1.3 horas |
| 4 | PubChem | 100M | 20.5 días | 20.5 días |
| 5 | ZINC | 23M | 6.4 horas | 20.8 días |

**Total: ~21 días** para ~125M compuestos

Si se incluye ZINC completo (750M):
- ZINC 750M: ~8.7 días adicionales
- **Total: ~30 días** para ~875M compuestos

---

## Checklist de Deployment

### Pre-deployment

- [ ] Hardware verificado (CPU, RAM, Storage, Red)
- [ ] Sistema operativo actualizado
- [ ] Python 3.10+ instalado
- [ ] Materials-SimPro clonado y dependencies instaladas
- [ ] Directorio de trabajo creado
- [ ] ZINC data descargado (si se usará)
- [ ] UPS conectado (recomendado)

### Deployment

- [ ] Base de datos inicializada
- [ ] `continuous_ingestion.py` creado
- [ ] `monitor_ingestion.py` creado
- [ ] Autostart configurado (systemd/Task Scheduler)
- [ ] Tmux session iniciado
- [ ] Monitor en segunda ventana
- [ ] Logs verificados

### Post-deployment

- [ ] Verificar ingesta después de 1 hora
- [ ] Verificar checkpoint funcionando
- [ ] Verificar rate de ingesta (>500 struct/sec)
- [ ] Configurar alertas (opcional)
- [ ] Documentar progreso

---

## Comandos Útiles

```bash
# Ver progreso actual
python -c "
from src.database.optimized_database_engine import OptimizedDatabase
db = OptimizedDatabase('materials_simpro_production.db')
stats = db.get_statistics()
print(f'Total: {stats[\"total_structures\"]:,}')
db.close()
"

# Ver últimas 100 líneas del log
tail -n 100 logs/continuous_ingestion.log

# Ver tasa de ingesta en tiempo real
watch -n 60 'python monitor_ingestion.py'

# Backup de base de datos
cp materials_simpro_production.db materials_simpro_production_backup_$(date +%Y%m%d).db

# Comprimir backup
gzip materials_simpro_production_backup_*.db
```

---

## Contacto y Soporte

Para issues o preguntas:
- GitHub Issues: https://github.com/Yatrogenesis/Materials-SimPro/issues
- Email: materials-simpro@example.com

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>

---

**Fecha**: 2025-11-04
**Versión**: 1.0.0
**Estado**: Guía Completa para Laptop Dedicada 24/7
**Target**: 852M+ compuestos en 2-3 meses
