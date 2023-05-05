import ipywidgets as ipw
import traitlets


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
