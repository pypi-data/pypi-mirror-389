#!/usr/bin/env python3
"""
COMPLETE HUMAN KNOWLEDGE INGESTION
===================================

Master script for populating Materials-SimPro database with ALL documented
human knowledge of molecules, materials, and polymers.

Target: 100+ million structures from:
- PubChem: 100M+ compounds
- ChEMBL: 2M+ bioactive compounds
- ZINC: 750M+ purchasable compounds
- KEGG: 20k metabolites
- DrugBank: 15k approved drugs (requires API key)
- Materials Project: 150k materials (requires API key)
- And more...

Usage:
    python ingest_complete_knowledge.py --source pubchem --count 10000
    python ingest_complete_knowledge.py --source chembl --count 50000
    python ingest_complete_knowledge.py --source zinc --zinc-file zinc_druglike.smi
    python ingest_complete_knowledge.py --source kegg
    python ingest_complete_knowledge.py --source all --workers 8

Author: Materials-SimPro Team
Date: 2025-11-04
"""

import argparse
import sys
import logging
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

from database.parallel_loader import ParallelMoleculeLoader
from database.optimized_database_engine import OptimizedDatabase

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ingestion.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def ingest_pubchem(count: int, workers: int, db_path: str, checkpoint: str):
    """
    Ingest molecules from PubChem

    Args:
        count: Number of compounds to fetch
        workers: Number of parallel workers
        db_path: Database file path
        checkpoint: Checkpoint file for resume capability
    """
    logger.info("="*70)
    logger.info("PUBCHEM INGESTION")
    logger.info("="*70)
    logger.info(f"Target: {count:,} compounds")
    logger.info(f"Workers: {workers}")
    logger.info(f"Database: {db_path}")
    logger.info("="*70)

    loader = ParallelMoleculeLoader(
        db_path=db_path,
        num_workers=workers,
        batch_size=100,
        checkpoint_interval=10000
    )

    try:
        loader.load_from_pubchem(
            start_cid=1,
            count=count,
            checkpoint_file=checkpoint
        )
        logger.info("PubChem ingestion completed successfully")
    except Exception as e:
        logger.error(f"PubChem ingestion failed: {e}")
        raise


def ingest_kegg(workers: int, db_path: str):
    """
    Ingest all KEGG compounds (~20,000 metabolites)

    Args:
        workers: Number of parallel workers
        db_path: Database file path
    """
    logger.info("="*70)
    logger.info("KEGG INGESTION")
    logger.info("="*70)
    logger.info(f"Target: All KEGG compounds (~20,000)")
    logger.info(f"Workers: {workers}")
    logger.info(f"Database: {db_path}")
    logger.info("="*70)

    loader = ParallelMoleculeLoader(
        db_path=db_path,
        num_workers=workers,
        batch_size=100
    )

    try:
        loader.load_from_kegg()
        logger.info("KEGG ingestion completed successfully")
    except Exception as e:
        logger.error(f"KEGG ingestion failed: {e}")
        raise


def ingest_chembl(count: int, workers: int, db_path: str, checkpoint: str):
    """
    Ingest bioactive compounds from ChEMBL

    Args:
        count: Number of compounds to fetch
        workers: Number of parallel workers
        db_path: Database file path
        checkpoint: Checkpoint file for resume capability
    """
    logger.info("="*70)
    logger.info("CHEMBL INGESTION")
    logger.info("="*70)
    logger.info(f"Target: {count:,} bioactive compounds")
    logger.info(f"Workers: {workers}")
    logger.info(f"Database: {db_path}")
    logger.info("="*70)

    loader = ParallelMoleculeLoader(
        db_path=db_path,
        num_workers=workers,
        batch_size=100,
        checkpoint_interval=10000
    )

    try:
        loader.load_from_chembl(
            count=count,
            checkpoint_file=checkpoint
        )
        logger.info("ChEMBL ingestion completed successfully")
    except Exception as e:
        logger.error(f"ChEMBL ingestion failed: {e}")
        raise


def ingest_zinc(zinc_file: str, count: int, workers: int, db_path: str):
    """
    Ingest purchasable compounds from ZINC database

    Note: Requires pre-downloaded ZINC files from https://zinc.docking.org/

    Args:
        zinc_file: Path to ZINC SMILES file
        count: Maximum number of compounds to ingest
        workers: Number of parallel workers
        db_path: Database file path
    """
    logger.info("="*70)
    logger.info("ZINC INGESTION")
    logger.info("="*70)
    logger.info(f"File: {zinc_file}")
    logger.info(f"Target: {count:,} compounds")
    logger.info(f"Workers: {workers}")
    logger.info(f"Database: {db_path}")
    logger.info("="*70)

    if not Path(zinc_file).exists():
        logger.error(f"ZINC file not found: {zinc_file}")
        logger.info("Download ZINC files from: https://zinc.docking.org/tranches/home/")
        raise FileNotFoundError(f"ZINC file not found: {zinc_file}")

    loader = ParallelMoleculeLoader(
        db_path=db_path,
        num_workers=workers,
        batch_size=1000  # Larger batches for file parsing
    )

    try:
        loader.load_from_zinc_file(zinc_file, max_count=count)
        logger.info("ZINC ingestion completed successfully")
    except Exception as e:
        logger.error(f"ZINC ingestion failed: {e}")
        raise


def ingest_existing_data(db_path: str):
    """
    Import existing generated data from previous expansions

    This includes:
    - 90 FDA approved drugs from generate_COMPLETE_HUMAN_KNOWLEDGE_molecules.py
    - 108 molecules from generate_ULTRA_MASSIVE_molecules.py
    - 90 materials from generate_ULTRA_MASSIVE_materials.py
    - 160 polymers from generate_MEGA_POLYMER_database.py
    """
    logger.info("="*70)
    logger.info("IMPORTING EXISTING GENERATED DATA")
    logger.info("="*70)

    db = OptimizedDatabase(db_path)

    # Import molecules
    try:
        from database.generate_COMPLETE_HUMAN_KNOWLEDGE_molecules import COMPLETE_HUMAN_KNOWLEDGE_MOLECULES

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
        logger.info(f"Imported {len(molecules)} FDA approved drugs")

    except ImportError:
        logger.warning("Could not import COMPLETE_HUMAN_KNOWLEDGE_MOLECULES")

    # Import ultra massive molecules
    try:
        from database.generate_ULTRA_MASSIVE_molecules import ULTRA_MASSIVE_MOLECULES

        molecules = []
        for name, data in ULTRA_MASSIVE_MOLECULES.items():
            molecules.append((
                data['formula'],
                name,
                data['MW'],
                None,
                {'note': data.get('note'), 'class': data.get('class')}
            ))

        db.bulk_insert_molecules(molecules)
        logger.info(f"Imported {len(molecules)} ultra massive molecules")

    except ImportError:
        logger.warning("Could not import ULTRA_MASSIVE_MOLECULES")

    # Get stats
    stats = db.get_statistics()
    logger.info(f"Database now contains: {stats['total']:,} total structures")
    logger.info(f"  - Molecules: {stats['molecules']:,}")
    logger.info(f"  - Materials: {stats['materials']:,}")
    logger.info(f"  - Polymers: {stats['polymers']:,}")

    db.close()
    logger.info("="*70)


def show_status(db_path: str):
    """Show current database status"""
    db = OptimizedDatabase(db_path)
    stats = db.get_statistics()

    print("\n" + "="*70)
    print("DATABASE STATUS")
    print("="*70)
    print(f"Total structures: {stats['total']:,}")
    print(f"\nBreakdown:")
    print(f"  Molecules: {stats['molecules']:,}")
    print(f"  Materials: {stats['materials']:,}")
    print(f"  Polymers: {stats['polymers']:,}")
    print(f"\nCache Performance:")
    print(f"  Hit rate: {stats['cache_hit_rate']:.2%}")
    print(f"  Cache size: {stats['cache_size']:,} entries")
    print(f"\nQuery Statistics:")
    print(f"  Total queries: {stats['queries']:,}")
    print(f"  Cache hits: {stats['cache_hits']:,}")
    print(f"  DB queries: {stats['db_queries']:,}")
    print("="*70)

    # Progress toward complete knowledge
    target_molecules = 100_000_000  # 100M target
    target_materials = 1_000_000    # 1M target
    target_polymers = 100_000       # 100k target

    mol_progress = (stats['molecules'] / target_molecules) * 100
    mat_progress = (stats['materials'] / target_materials) * 100
    poly_progress = (stats['polymers'] / target_polymers) * 100

    print("\nPROGRESS TOWARD COMPLETE HUMAN KNOWLEDGE:")
    print(f"  Molecules: {mol_progress:.4f}% ({stats['molecules']:,} / {target_molecules:,})")
    print(f"  Materials: {mat_progress:.4f}% ({stats['materials']:,} / {target_materials:,})")
    print(f"  Polymers: {poly_progress:.4f}% ({stats['polymers']:,} / {target_polymers:,})")
    print("="*70 + "\n")

    db.close()


def main():
    parser = argparse.ArgumentParser(
        description='Ingest complete human knowledge into Materials-SimPro database',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Ingest 10,000 compounds from PubChem
  python ingest_complete_knowledge.py --source pubchem --count 10000

  # Ingest bioactive compounds from ChEMBL
  python ingest_complete_knowledge.py --source chembl --count 50000

  # Ingest purchasable compounds from ZINC (requires pre-downloaded file)
  python ingest_complete_knowledge.py --source zinc --zinc-file zinc_druglike.smi --count 100000

  # Ingest all KEGG metabolites
  python ingest_complete_knowledge.py --source kegg

  # Import existing generated data
  python ingest_complete_knowledge.py --source existing

  # Show database status
  python ingest_complete_knowledge.py --status

  # Full ingestion with 8 workers (WARNING: Takes days/weeks!)
  python ingest_complete_knowledge.py --source all --count 1000000 --workers 8
        """
    )

    parser.add_argument('--source', type=str,
                        choices=['pubchem', 'chembl', 'zinc', 'kegg', 'existing', 'all'],
                        help='Data source to ingest')
    parser.add_argument('--count', type=int, default=10000,
                        help='Number of structures to ingest (default: 10000)')
    parser.add_argument('--workers', type=int, default=4,
                        help='Number of parallel workers (default: 4)')
    parser.add_argument('--db', type=str, default='materials_simpro_complete.db',
                        help='Database file path (default: materials_simpro_complete.db)')
    parser.add_argument('--checkpoint', type=str, default='ingestion_checkpoint.pkl',
                        help='Checkpoint file for resume capability')
    parser.add_argument('--zinc-file', type=str, default='zinc_druglike.smi',
                        help='Path to ZINC SMILES file (required for --source zinc)')
    parser.add_argument('--status', action='store_true',
                        help='Show database status and exit')

    args = parser.parse_args()

    # Show status if requested
    if args.status:
        show_status(args.db)
        return

    # Validate source
    if not args.source:
        parser.print_help()
        print("\nError: --source is required (use --status to show database status)")
        sys.exit(1)

    logger.info("Materials-SimPro: Complete Human Knowledge Ingestion")
    logger.info(f"Database: {args.db}")

    try:
        if args.source == 'existing':
            ingest_existing_data(args.db)

        elif args.source == 'pubchem':
            ingest_pubchem(args.count, args.workers, args.db, args.checkpoint)

        elif args.source == 'chembl':
            ingest_chembl(args.count, args.workers, args.db, args.checkpoint)

        elif args.source == 'zinc':
            ingest_zinc(args.zinc_file, args.count, args.workers, args.db)

        elif args.source == 'kegg':
            ingest_kegg(args.workers, args.db)

        elif args.source == 'all':
            logger.info("Starting complete ingestion from all sources...")
            ingest_existing_data(args.db)
            ingest_kegg(args.workers, args.db)
            ingest_chembl(args.count, args.workers, args.db, f"{args.checkpoint}.chembl")
            ingest_pubchem(args.count, args.workers, args.db, f"{args.checkpoint}.pubchem")

        # Show final status
        show_status(args.db)

    except KeyboardInterrupt:
        logger.info("\nIngestion interrupted by user")
        logger.info("Progress has been saved in checkpoint file")
        show_status(args.db)
        sys.exit(0)

    except Exception as e:
        logger.error(f"Ingestion failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
