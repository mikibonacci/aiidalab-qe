import ipywidgets as ipw
from aiida_quantumespresso.workflows.pw.base import PwBaseWorkChain

from aiidalab_qe.panel import Panel
from aiidalab_qe.pseudos import PseudoFamilySelector


class AdvanceSettings(Panel):
    properties_title = ipw.HTML(
        """<div style="padding-top: 0px; padding-bottom: 0px">
        <h4>Properties</h4></div>"""
    )
    smearing_description = ipw.HTML(
        """<p>
        The smearing type and width is set by the chosen <b>protocol</b>.
        Tick the box to override the default, not advised unless you've mastered <b>smearing effects</b> (click <a href="http://theossrv1.epfl.ch/Main/ElectronicTemperature"
        target="_blank">here</a> for a discussion).
    </p>"""
    )
    kpoints_distance_description = ipw.HTML(
        """<div>
        The k-points mesh density of the SCF calculation is set by the <b>protocol</b>.
        The value below represents the maximum distance between the k-points in each direction of reciprocal space.
        Tick the box to override the default, smaller is more accurate and costly. </div>"""
    )

    def __init__(self, **kwargs):
        # Work chain protocol
        self.workchain_protocol = ipw.ToggleButtons(
            options=["fast", "moderate", "precise"],
            value="moderate",
        )
        self.pseudo_family_selector = PseudoFamilySelector()
        #
        self.smearing = ipw.Dropdown(
            options=["cold", "gaussian", "fermi-dirac", "methfessel-paxton"],
            value="cold",
            description="Smearing type:",
            disabled=False,
            style={"description_width": "initial"},
        )
        self.degauss = ipw.FloatText(
            value=0.01,
            step=0.005,
            description="Smearing width (Ry):",
            disabled=False,
            style={"description_width": "initial"},
        )
        self.kpoints_distance = ipw.FloatText(
            value=0.15,
            step=0.05,
            description="K-points distance (1/Å):",
            disabled=False,
            style={"description_width": "initial"},
        )
        # update settings based on protocol
        ipw.dlink(
            (self.workchain_protocol, "value"),
            (self.kpoints_distance, "value"),
            lambda protocol: PwBaseWorkChain.get_protocol_inputs(protocol)[
                "kpoints_distance"
            ],
        )

        ipw.dlink(
            (self.workchain_protocol, "value"),
            (self.degauss, "value"),
            lambda protocol: PwBaseWorkChain.get_protocol_inputs(protocol)["pw"][
                "parameters"
            ]["SYSTEM"]["degauss"],
        )

        ipw.dlink(
            (self.workchain_protocol, "value"),
            (self.smearing, "value"),
            lambda protocol: PwBaseWorkChain.get_protocol_inputs(protocol)["pw"][
                "parameters"
            ]["SYSTEM"]["smearing"],
        )
        #
        children = [
            self.pseudo_family_selector,
            self.kpoints_distance_description,
            self.kpoints_distance,
            self.smearing_description,
            self.smearing,
        ]
        # get other parameters from entry point
        super().__init__(
            children=children,
            **kwargs,
        )

    def get_panel_value(self):
        """Return the value of all the widgets in the panel as a dictionary.

        :return: a dictionary of the values of all the widgets in the panel.
        """

        parameters = {
            "pseudo_family": self.pseudo_family_selector.value,
            "pw": {
                "kpoints_distance": self.kpoints_distance.value,
                "parameters": {
                    "SYSTEM": {
                        "degauss": self.degauss.value,
                        "smearing": self.smearing.value,
                    }
                },
            },
        }
        return parameters

    def load_panel_value(self, parameters):
        """Load a dictionary to set the value of the widgets in the panel.

        :param parameters: a dictionary of the values of all the widgets in the panel.
        """
        self.pseudo_family_selector.value = parameters.get("pseudo_family")
        self.pseudo_family_selector.dft_functional.value = parameters.get(
            "pseudo_family"
        ).split("/")[2]
        self.pseudo_family_selector.protocol_selection.value = parameters.get(
            "pseudo_family"
        ).split("/")[3]
        if parameters.get("pw") is not None:
            self.kpoints_distance.value = parameters["pw"]["kpoints_distance"]
            self.degauss.value = parameters["pw"]["parameters"]["SYSTEM"]["degauss"]
            self.smearing.value = parameters["pw"]["parameters"]["SYSTEM"]["smearing"]
