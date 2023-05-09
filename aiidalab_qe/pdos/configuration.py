# -*- coding: utf-8 -*-
"""Panel for PDOS plugin.

Authors:

    * Xing Wang <xing.wang@psi.ch>
"""
import ipywidgets as ipw
from aiida.orm import Float, Int

from aiidalab_qe.panel import Panel


class PDOSSettings(Panel):
    title = "PDOS Settings"

    def __init__(self, **kwargs):
        self.settings_title = ipw.HTML(
            """<div style="padding-top: 0px; padding-bottom: 0px">
            <h4>Settings</h4></div>"""
        )
        self.settings_help = ipw.HTML(
            """<div style="line-height: 140%; padding-top: 0px; padding-bottom: 5px">
            Please set the value of Emin and number of points.
            </div>"""
        )
        self.workchain_protocol = ipw.ToggleButtons(
            options=["fast", "moderate", "precise"],
            value="moderate",
        )
        self.Emin = ipw.FloatText(
            value=-10.0,
            description="Min energy (eV):",
            disabled=False,
            style={"description_width": "initial"},
        )
        self.Emax = ipw.FloatText(
            value=10.0,
            description="Max energy (eV):",
            disabled=False,
            style={"description_width": "initial"},
        )
        self.DeltaE = ipw.FloatText(
            value=0.1,
            description="Energy grid step (eV):",
            disabled=False,
            style={"description_width": "initial"},
        )

        self.children = [
            self.settings_title,
            self.settings_help,
            self.Emin,
            self.Emax,
        ]
        super().__init__(**kwargs)

    def get_panel_value(self):
        """Return a dictionary with the input parameters for the plugin."""
        return {
            "Emin": Float(self.Emin.value),
            "Emax": Int(self.Emax.value),
        }

    def load_panel_value(self, input_dict):
        """Load a dictionary with the input parameters for the plugin."""
        self.Emin.value = input_dict.get("Emin", 1)
        self.Emax.value = input_dict.get("Emax", 2)
