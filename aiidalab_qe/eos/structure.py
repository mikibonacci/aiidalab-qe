import ipywidgets as ipw
import traitlets as tl
from ase import Atoms

class EOSStructure(ipw.VBox):
    """Create structure use ASE builder."""

    structure = tl.Instance(Atoms, allow_none=True)

    def __init__(self, title="From ASE"):
        self.title = title
        self.bulk_symbol = ipw.Text(placeholder="Au")
        self.create_bulk_structure_btn = ipw.Button(
            description="Generate bulk",
            button_style="primary",
            tooltip="Generate bulk from symbol",
        )
        self.create_bulk_structure_btn.on_click(self._on_bulk_button_pressed)

        self.fcc111_symbol = ipw.Text(placeholder="Au")
        self.create_fcc111_structure_btn = ipw.Button(
            description="FCC111 surface",
            button_style="primary",
            tooltip="Generate surface from symbol",
        )
        self.create_fcc111_structure_btn.on_click(self._on_fcc111_button_pressed)
        children = (
            ipw.HBox([self.bulk_symbol, self.create_bulk_structure_btn]),
            ipw.HBox([self.fcc111_symbol, self.create_fcc111_structure_btn]),
        )
        super().__init__(children=children)

    def _on_bulk_button_pressed(self, change=None):
        """Create a ase structure when button is pressed."""
        from ase.build import bulk
        if not self.bulk_symbol.value:
            return
        self.structure = bulk(self.bulk_symbol.value)

    def _on_fcc111_button_pressed(self, change=None):
        """Create a ase structure when button is pressed."""
        from ase.build import fcc111
        if not self.fcc111_symbol.value:
            return
        atoms = fcc111(self.fcc111_symbol.value, (1, 1, 4), vacuum=3)
        atoms.pbc = True
        # remote tags
        atoms.set_tags(0)
        self.structure = atoms


    @tl.default("structure")
    def _default_structure(self):
        return None
