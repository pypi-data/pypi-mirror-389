"""
Jupyter Notebook Integration
=============================

Interactive widgets for Materials-SimPro in Jupyter notebooks.

Usage:
------
```python
from materials_simpro.jupyter import StructureWidget, CalculationWidget

# Create structure viewer
widget = StructureWidget(structure)
display(widget)

# Run calculation
calc_widget = CalculationWidget()
display(calc_widget)
```

Reference: ipywidgets documentation (https://ipywidgets.readthedocs.io/)
"""

from .widgets import StructureWidget, CalculationWidget

__all__ = ['StructureWidget', 'CalculationWidget']
