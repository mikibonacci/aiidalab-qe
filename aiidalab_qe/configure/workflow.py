import ipywidgets as ipw

from aiidalab_qe.panel import PropertyPanel
from aiidalab_qe.utils import get_entries


class BandsProperty(PropertyPanel):
    name = "bands"
    description = "Electronic band structure"
    help = """The band structure workflow will
automatically detect the default path in reciprocal space using the
<a href="https://www.materialscloud.org/work/tools/seekpath" target="_blank">
SeeK-path tool</a>.
"""


class PDOSProperty(PropertyPanel):
    name = "PDOS"
    description = "Projected density of states (PDOS)"


class WorkChainSettings(ipw.VBox):
    relax_title = ipw.HTML(
        """<div style="padding-top: 0px; padding-bottom: 0px">
        <h4>Structure optimization</h4></div>"""
    )
    relax_help = ipw.HTML(
        """<div style="line-height: 140%; padding-top: 0px; padding-bottom: 5px">
        You have three options:<br>
        (1) Structure as is: perform a self consistent calculation using the structure provided as input.<br>
        (2) Atomic positions: perform a full relaxation of the internal atomic coordinates. <br>
        (3) Full geometry: perform a full relaxation for both the internal atomic coordinates and the cell vectors. </div>"""
    )
    properties_title = ipw.HTML(
        """<div style="padding-top: 0px; padding-bottom: 0px">
        <h4>Properties</h4></div>"""
    )

    def __init__(self, **kwargs):
        # RelaxType: degrees of freedom in geometry optimization
        self.relax_type = ipw.ToggleButtons(
            options=[
                ("Structure as is", "none"),
                ("Atomic positions", "positions"),
                ("Full geometry", "positions_cell"),
            ],
            value="positions_cell",
        )
        children = [
            self.relax_title,
            self.relax_help,
            self.relax_type,
            self.properties_title,
            ipw.HTML("Select which properties to calculate:"),
        ]
        self.properties = {}
        entries = get_entries("aiidalab_qe_property")
        for name, entry_point in entries.items():
            self.properties[name] = entry_point()
            children.append(self.properties[name])
        super().__init__(
            children=children,
            **kwargs,
        )

    def get_panel_value(self):
        """Return the value of all the widgets in the panel as a dictionary.

        :return: a dictionary of the values of all the widgets in the panel.
        """
        parameters = {"relax_type": self.relax_type.value, "properties": {}}
        for name, property in self.properties.items():
            parameters["properties"][name] = property.run.value
        return parameters

    def load_panel_value(self, parameters):
        """Load a dictionary to set the value of the widgets in the panel.

        :param parameters: a dictionary of the values of all the widgets in the panel.
        """
        self.relax_type.value = parameters.get("relax_type", "positions_cell")
        for key, value in parameters.get("properties", {}).items():
            if key in self.properties:
                self.properties[key].run.value = value
