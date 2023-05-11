# -*- coding: utf-8 -*-
"""Panel for Bands plugin.

Authors:

    * Xing Wang <xing.wang@psi.ch>
"""
import ipywidgets as ipw
from aiida.orm import Int, Str

from aiidalab_qe.panel import Panel


class Settings(Panel):
    title = "XPS Settings"

    core_hole_treatment_title = ipw.HTML(
        """<div style="padding-top: 0px; padding-bottom: 0px">
        <h4>Core hole treatment</h4></div>"""
    )
    core_hole_treatment_help = ipw.HTML(
        """<div style="line-height: 140%; padding-top: 0px; padding-bottom: 5px">
        You have four options:<br>
        </div>"""
    )

    pseudo_title = ipw.HTML(
        """<div style="padding-top: 0px; padding-bottom: 0px">
        <h4>Pseudo-potential</h4></div>"""
    )
    pseudo_help = ipw.HTML(
        """<div style="line-height: 140%; padding-top: 10px; padding-bottom: 0px">
        Ground-state and excited-state pseudopotentials for each absorbing element.
        </div>"""
    )

    element_title = ipw.HTML(
        """<div style="padding-top: 0px; padding-bottom: 0px">
        <h4>Select element</h4></div>"""
    )
    element_help = ipw.HTML(
        """<div style="line-height: 140%; padding-top: 6px; padding-bottom: 0px">
        The list of elements (e.g. C, O) to be considered for analysis. If no elements list is given, we instead calculate all elements in the structure.
        </div>"""
    )
    structure_title = ipw.HTML(
        """<div style="padding-top: 0px; padding-bottom: 0px">
        <h4>Structure</h4></div>"""
    )
    structure_help = ipw.HTML(
        """<div style="line-height: 140%; padding-top: 10px; padding-bottom: 10px">
        Below you can indicate both if the material should be treated as an molecule
        or a crystal.
        </div>"""
    )
    supercell_title = ipw.HTML(
        """<div style="padding-top: 0px; padding-bottom: 0px">
        <h4>Supercell</h4></div>"""
    )
    supercell_help = ipw.HTML(
        """<div style="line-height: 140%; padding-top: 10px; padding-bottom: 10px">
        Defining the minimum cell length in angstrom for the resulting supercell, and thus all output
        structures. The default value of 8.0 angstrom will be used
        if no input is given. Setting this value to 0.0 will
        instruct the CF to not scale up the input structure.
        </div>"""
    )
    binding_energy_title = ipw.HTML(
        """<div style="padding-top: 0px; padding-bottom: 0px">
        <h4>Absolute binding energy</h4></div>"""
    )
    binding_energy_help = ipw.HTML(
        """<div style="line-height: 140%; padding-top: 10px; padding-bottom: 10px">
        To calculate the absolute binding energy, you need to provide the correction energy for the core electrons. The correction energy is Ecorr = E_core_hole - E_gipaw, where E_core_hole and E_gipaw are calculated by Etot - Etotps. Etot and Etotps can be found in the output when generating the pseudo potential. A offset corretion by fitting the experimental data is also added. Here is a example: C:339.79,O:668.22,F:955.73,Si:153.19
        </div>"""
    )

    def __init__(self, **kwargs):
        # Core hole treatment type
        self.core_hole_treatment = ipw.ToggleButtons(
            options=[
                ("Full", "full"),
                ("Half", "half"),
                ("Xch_fixed", "xch_fixed"),
                ("Xch_smear", "xch_smear"),
            ],
            value="full",
        )
        self.es_pseudo = ipw.Text(
            description="excited-state pseudopotentials:",
            value="core_hole",
            style={"description_width": "initial"},
            disabled=False,
        )
        self.gs_pseudo = ipw.Text(
            description="ground-state pseudopotentials:",
            value="gipaw",
            style={"description_width": "initial"},
            disabled=False,
        )
        self.core_wfc_data = ipw.Text(
            description="core wavefunction data",
            value="core_wfc_data",
            style={"description_width": "initial"},
            disabled=False,
        )
        self.elements_list = ipw.Text(
            description="Select element:",
            value="",
            style={"description_width": "initial"},
            disabled=False,
        )
        self.structure_type = ipw.ToggleButtons(
            options=[
                ("Molecule", "molecule"),
                ("Crystal", "crystal"),
            ],
            value="crystal",
        )
        self.supercell_min_parameter = ipw.FloatText(
            value=8.0,
            description="The minimum cell length (Å):",
            disabled=False,
            style={"description_width": "initial"},
        )
        self.calc_binding_energy = ipw.Checkbox(
            description="Calculate binding energy: ",
            indent=False,
            value=False,
        )
        self.correction_energies = ipw.Text(
            description="Correction energies (eV):",
            value="",
            style={"description_width": "initial"},
            disabled=False,
        )

        ipw.dlink(
            (self.calc_binding_energy, "value"),
            (self.correction_energies, "disabled"),
            lambda override: not override,
        )

        self.children = [
            self.core_hole_treatment_title,
            self.core_hole_treatment_help,
            ipw.HBox(
                children=[
                    ipw.Label(
                        "Core Hole Treatment Type:",
                        layout=ipw.Layout(justify_content="flex-start", width="120px"),
                    ),
                    self.core_hole_treatment,
                ]
            ),
            self.pseudo_title,
            self.pseudo_help,
            ipw.HBox(
                [self.es_pseudo, self.gs_pseudo, self.core_wfc_data],
            ),
            self.element_title,
            self.element_help,
            ipw.HBox(
                [self.elements_list],
            ),
            self.structure_title,
            self.structure_help,
            ipw.HBox(
                [self.structure_type],
            ),
            self.supercell_title,
            self.supercell_help,
            ipw.HBox(
                [self.supercell_min_parameter],
            ),
            self.binding_energy_title,
            self.binding_energy_help,
            ipw.HBox(
                [self.calc_binding_energy, self.correction_energies],
            ),
        ]
        super().__init__(**kwargs)

    def get_panel_value(self):
        """Return a dictionary with the input parameters for the plugin."""
        return {
            "path": Str(self.path.value),
            "npoint": Int(self.npoint.value),
        }

    def load_panel_value(self, input_dict):
        """Load a dictionary with the input parameters for the plugin."""
        self.path.value = input_dict.get("path", 1)
        self.npoint.value = input_dict.get("npoint", 2)
