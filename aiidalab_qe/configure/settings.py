import ipywidgets as ipw
import traitlets

from aiidalab_qe.parameters import DEFAULT_PARAMETERS
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


class BasicSettings(ipw.VBox):
    materials_help = ipw.HTML(
        """<div style="line-height: 140%; padding-top: 10px; padding-bottom: 10px">
        Below you can indicate both if the material should be treated as an insulator
        or a metal (if in doubt, choose "Metal"),
        and if it should be studied with magnetization/spin polarization,
        switch magnetism On or Off (On is at least twice more costly).
        </div>"""
    )

    protocol_title = ipw.HTML(
        """<div style="padding-top: 0px; padding-bottom: 0px">
        <h4>Protocol</h4></div>"""
    )
    protocol_help = ipw.HTML(
        """<div style="line-height: 140%; padding-top: 6px; padding-bottom: 0px">
        The "moderate" protocol represents a trade-off between
        accuracy and speed. Choose the "fast" protocol for a faster calculation
        with less precision and the "precise" protocol to aim at best accuracy (at the price of longer/costlier calculations).</div>"""
    )

    def __init__(self, **kwargs):
        # SpinType: magnetic properties of material
        self.spin_type = ipw.ToggleButtons(
            options=[("Off", "none"), ("On", "collinear")],
            value=DEFAULT_PARAMETERS["spin_type"],
            style={"description_width": "initial"},
        )

        # ElectronicType: electronic properties of material
        self.electronic_type = ipw.ToggleButtons(
            options=[("Metal", "metal"), ("Insulator", "insulator")],
            value=DEFAULT_PARAMETERS["electronic_type"],
            style={"description_width": "initial"},
        )

        # Work chain protocol
        self.workchain_protocol = ipw.ToggleButtons(
            options=["fast", "moderate", "precise"],
            value="moderate",
        )

        children = (
            self.materials_help,
            ipw.HBox(
                children=[
                    ipw.Label(
                        "Electronic Type:",
                        layout=ipw.Layout(justify_content="flex-start", width="120px"),
                    ),
                    self.electronic_type,
                ]
            ),
            ipw.HBox(
                children=[
                    ipw.Label(
                        "Magnetism:",
                        layout=ipw.Layout(justify_content="flex-start", width="120px"),
                    ),
                    self.spin_type,
                ]
            ),
            self.protocol_title,
            ipw.HTML("Select the protocol:", layout=ipw.Layout(flex="1 1 auto")),
            self.workchain_protocol,
            self.protocol_help,
        )
        super().__init__(
            children=children,
            **kwargs,
        )


class SmearingSettings(ipw.VBox):
    smearing_description = ipw.HTML(
        """<p>
        The smearing type and width is set by the chosen <b>protocol</b>.
        Tick the box to override the default, not advised unless you've mastered <b>smearing effects</b> (click <a href="http://theossrv1.epfl.ch/Main/ElectronicTemperature"
        target="_blank">here</a> for a discussion).
    </p>"""
    )

    # The default of `smearing` and `degauss` the type and width
    # must be linked to the `protocol`
    degauss_default = traitlets.Float(default_value=0.01)
    smearing_default = traitlets.Unicode(default_value="cold")

    def __init__(self, **kwargs):
        self.override_protocol_smearing = ipw.Checkbox(
            description="Override",
            indent=False,
            value=False,
        )
        self.smearing = ipw.Dropdown(
            options=["cold", "gaussian", "fermi-dirac", "methfessel-paxton"],
            value=self.smearing_default,
            description="Smearing type:",
            disabled=False,
            style={"description_width": "initial"},
        )
        self.degauss = ipw.FloatText(
            value=self.degauss_default,
            step=0.005,
            description="Smearing width (Ry):",
            disabled=False,
            style={"description_width": "initial"},
        )
        ipw.dlink(
            (self.override_protocol_smearing, "value"),
            (self.degauss, "disabled"),
            lambda override: not override,
        )
        ipw.dlink(
            (self.override_protocol_smearing, "value"),
            (self.smearing, "disabled"),
            lambda override: not override,
        )
        self.degauss.observe(self.set_smearing, "value")
        self.smearing.observe(self.set_smearing, "value")
        self.override_protocol_smearing.observe(self.set_smearing, "value")

        super().__init__(
            children=[
                self.smearing_description,
                ipw.HBox(
                    [self.override_protocol_smearing, self.smearing, self.degauss]
                ),
            ],
            layout=ipw.Layout(justify_content="space-between"),
            **kwargs,
        )

    def set_smearing(self, _=None):
        self.degauss.value = (
            self.degauss.value
            if self.override_protocol_smearing.value
            else self.degauss_default
        )
        self.smearing.value = (
            self.smearing.value
            if self.override_protocol_smearing.value
            else self.smearing_default
        )


class KpointSettings(ipw.VBox):
    kpoints_distance_description = ipw.HTML(
        """<div>
        The k-points mesh density of the SCF calculation is set by the <b>protocol</b>.
        The value below represents the maximum distance between the k-points in each direction of reciprocal space.
        Tick the box to override the default, smaller is more accurate and costly. </div>"""
    )

    # The default of `kpoints_distance` must be linked to the `protocol`
    kpoints_distance_default = traitlets.Float(default_value=0.15)

    def __init__(self, **kwargs):
        self.override_protocol_kpoints = ipw.Checkbox(
            description="Override",
            indent=False,
            value=False,
        )
        self.kpoints_distance = ipw.FloatText(
            value=self.kpoints_distance_default,
            step=0.05,
            description="K-points distance (1/Å):",
            disabled=False,
            style={"description_width": "initial"},
        )
        ipw.dlink(
            (self.override_protocol_kpoints, "value"),
            (self.kpoints_distance, "disabled"),
            lambda override: not override,
        )
        self.kpoints_distance.observe(self.set_kpoints_distance, "value")
        self.override_protocol_kpoints.observe(self.set_kpoints_distance, "value")
        self.observe(self.set_kpoints_distance, "kpoints_distance_default")

        super().__init__(
            children=[
                self.kpoints_distance_description,
                ipw.HBox([self.override_protocol_kpoints, self.kpoints_distance]),
            ],
            layout=ipw.Layout(justify_content="space-between"),
            **kwargs,
        )

    def set_kpoints_distance(self, _=None):
        self.kpoints_distance.value = (
            self.kpoints_distance.value
            if self.override_protocol_kpoints.value
            else self.kpoints_distance_default
        )
