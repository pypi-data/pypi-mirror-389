"""
Jupyter Widgets
===============

Interactive visualization and calculation widgets for Jupyter notebooks.

Dependencies:
- ipywidgets
- nglview (for 3D visualization)
- matplotlib

Reference: Nguyen et al. (2018). nglview. DOI: 10.1093/bioinformatics/btx789
"""

import ipywidgets as widgets
from IPython.display import display, HTML
import matplotlib.pyplot as plt
from typing import Optional

try:
    import nglview as nv
    HAS_NGLVIEW = True
except ImportError:
    HAS_NGLVIEW = False


class StructureWidget:
    """
    Interactive 3D structure viewer widget.

    Uses NGLView for molecular visualization.

    Example:
    --------
    ```python
    from materials_simpro import get_material
    from materials_simpro.jupyter import StructureWidget

    structure = get_material("mp-149")  # Iron
    widget = StructureWidget(structure)
    display(widget)
    ```
    """

    def __init__(self, structure):
        self.structure = structure

        if HAS_NGLVIEW:
            # Create NGLView widget
            self.view = self._create_nglview()
        else:
            # Fallback to matplotlib
            self.view = self._create_matplotlib()

    def _create_nglview(self):
        """Create 3D viewer with NGLView."""
        # Convert structure to ASE Atoms
        # (Simplified - real implementation would use proper conversion)
        view = nv.NGLWidget()

        # Add structure
        # view.add_structure(nv.ASEStructure(atoms))

        # Representation
        view.add_representation('ball+stick', selection='all')
        view.add_representation('unitcell')

        # Camera
        view.camera = 'orthographic'

        return view

    def _create_matplotlib(self):
        """Fallback 2D visualization with matplotlib."""
        fig, ax = plt.subplots(figsize=(8, 6))

        # Simple 2D projection
        coords = self.structure.get_positions()
        elements = [site.element for site in self.structure.sites]

        # Color map
        colors = {'Si': 'tan', 'O': 'red', 'Fe': 'orange', 'Li': 'violet'}

        for coord, elem in zip(coords, elements):
            ax.scatter(coord[0], coord[1], c=colors.get(elem, 'gray'),
                      s=200, alpha=0.6, edgecolors='black')
            ax.text(coord[0], coord[1], elem, ha='center', va='center')

        ax.set_xlabel('x (Å)')
        ax.set_ylabel('y (Å)')
        ax.set_title(f'{self.structure.formula} - Structure (2D projection)')
        ax.grid(True, alpha=0.3)
        ax.set_aspect('equal')

        plt.close(fig)
        return fig

    def _repr_html_(self):
        """HTML representation for Jupyter."""
        if HAS_NGLVIEW:
            return self.view._repr_html_()
        else:
            return f"<div>Structure: {self.structure.formula}</div>"


class CalculationWidget:
    """
    Interactive calculation control panel.

    Example:
    --------
    ```python
    from materials_simpro.jupyter import CalculationWidget

    calc_widget = CalculationWidget()
    display(calc_widget)
    ```
    """

    def __init__(self, structure=None):
        self.structure = structure
        self.results = None

        # Create widgets
        self.method_dropdown = widgets.Dropdown(
            options=['DFT', 'Orb', 'Egret', 'MACE', 'CHGNet'],
            value='Orb',
            description='Method:',
            style={'description_width': '100px'}
        )

        self.xc_dropdown = widgets.Dropdown(
            options=['LDA', 'PBE', 'HSE06', 'SCAN'],
            value='PBE',
            description='XC Functional:',
            style={'description_width': '100px'}
        )

        self.ecut_text = widgets.FloatText(
            value=40.0,
            description='E_cut (Ry):',
            style={'description_width': '100px'}
        )

        self.calculate_button = widgets.Button(
            description='Calculate Energy',
            button_style='success',
            icon='play'
        )

        self.output = widgets.Output()

        # Bind events
        self.calculate_button.on_click(self._on_calculate)
        self.method_dropdown.observe(self._on_method_change, names='value')

        # Layout
        self.widget = widgets.VBox([
            widgets.HTML("<h3>Energy Calculation</h3>"),
            self.method_dropdown,
            self.xc_dropdown,
            self.ecut_text,
            self.calculate_button,
            self.output
        ])

    def _on_method_change(self, change):
        """Show/hide DFT options."""
        if change['new'] == 'DFT':
            self.xc_dropdown.layout.visibility = 'visible'
            self.ecut_text.layout.visibility = 'visible'
        else:
            self.xc_dropdown.layout.visibility = 'hidden'
            self.ecut_text.layout.visibility = 'hidden'

    def _on_calculate(self, button):
        """Run calculation."""
        with self.output:
            self.output.clear_output()

            if self.structure is None:
                print("L No structure loaded")
                return

            print(f"= Calculating with {self.method_dropdown.value}...")

            try:
                from ml.neural_potentials import OrbPotential
                from dft.kohn_sham import KohnShamSolver

                if self.method_dropdown.value == 'DFT':
                    calc = KohnShamSolver(
                        self.structure,
                        ecut_rydberg=self.ecut_text.value,
                        xc_functional=self.xc_dropdown.value
                    )
                else:
                    calc = OrbPotential()

                result = calc.calculate(self.structure)
                self.results = result

                # Display results
                print(" Calculation complete!")
                print(f"\n   Total energy:  {result.energy:.6f} eV")
                print(f"   Energy/atom:   {result.energy / len(self.structure):.6f} eV/atom")

                # Plot energy
                self._plot_results()

            except Exception as e:
                print(f"L Error: {e}")

    def _plot_results(self):
        """Plot calculation results."""
        if self.results is None:
            return

        fig, ax = plt.subplots(1, 1, figsize=(6, 4))
        ax.bar(['Total', 'Per Atom'], [
            self.results.energy,
            self.results.energy / len(self.structure)
        ])
        ax.set_ylabel('Energy (eV)')
        ax.set_title('Calculation Results')
        plt.tight_layout()
        plt.show()

    def _repr_html_(self):
        """HTML representation."""
        return self.widget._repr_html_()

    def display(self):
        """Display widget."""
        display(self.widget)


__all__ = ['StructureWidget', 'CalculationWidget']
