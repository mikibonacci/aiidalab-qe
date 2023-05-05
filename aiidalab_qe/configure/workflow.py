import ipywidgets as ipw

from aiidalab_qe.utils import get_entries


class WorkChainSettings(ipw.VBox):
    structure_title = ipw.HTML(
        """<div style="padding-top: 0px; padding-bottom: 0px">
        <h4>Structure</h4></div>"""
    )
    structure_help = ipw.HTML(
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
    properties_help = ipw.HTML(
        """<div style="line-height: 140%; padding-top: 10px; padding-bottom: 0px">
        The band structure workflow will
        automatically detect the default path in reciprocal space using the
        <a href="https://www.materialscloud.org/work/tools/seekpath" target="_blank">
        SeeK-path tool</a>.</div>"""
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
        # Checkbox to see if the band structure should be calculated
        self.bands_run = ipw.Checkbox(
            description="",
            tooltip="Calculate the electronic band structure.",
            indent=False,
            value=True,
            layout=ipw.Layout(max_width="10%"),
        )

        # Checkbox to see if the PDOS should be calculated
        self.pdos_run = ipw.Checkbox(
            description="",
            tooltip="Calculate the electronic PDOS.",
            indent=False,
            value=True,
            layout=ipw.Layout(max_width="10%"),
        )
        properties = (
            self.structure_title,
            self.structure_help,
            self.relax_type,
            self.properties_title,
            ipw.HTML("Select which properties to calculate:"),
            ipw.HBox(children=[ipw.HTML("<b>Band structure</b>"), self.bands_run]),
            ipw.HBox(
                children=[
                    ipw.HTML("<b>Projected density of states (PDOS)</b>"),
                    self.pdos_run,
                ]
            ),
            self.properties_help,
        )
        entries = get_entries("aiidalab_qe_property")
        for _name, entry_point in entries.items():
            properties += (entry_point,)
        super().__init__(
            children=properties,
            **kwargs,
        )
