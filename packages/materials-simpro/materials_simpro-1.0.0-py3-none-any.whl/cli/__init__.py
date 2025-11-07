"""
Command-Line Interface
======================

Materials-SimPro CLI for all operations:
- Structure manipulation
- DFT/ML calculations
- Database queries
- Workflow automation

Built with Click framework.

Usage:
------
```bash
matsim calculate structure.cif --method dft
matsim search --formula "LiFePO4" --energy -3.5
matsim optimize structure.cif --algorithm bayesian
matsim discover "high-k dielectrics"
```

Reference: Click documentation (https://click.palletsprojects.com/)
"""

from .main import cli

__all__ = ['cli']
