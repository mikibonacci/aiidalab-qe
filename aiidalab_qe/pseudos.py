# -*- coding: utf-8 -*-
import re

import ipywidgets as ipw
import traitlets

from aiidalab_qe.parameters import DEFAULT_PARAMETERS


class PseudoFamilySelector(ipw.VBox):
    title = ipw.HTML(
        """<div style="padding-top: 0px; padding-bottom: 10px">
        <h4>Accuracy and precision</h4></div>"""
    )

    description = ipw.HTML(
        """<div style="line-height: 140%; padding-top: 0px; padding-bottom: 10px">
        The exchange-correlation functional and pseudopotential library is set by
        the <b>protocol</b> configured in the "Workflow" tab. Here you can
        override the defaults if desired.</div>""",
        layout=ipw.Layout(max_width="60%"),
    )

    pseudo_family_prompt = ipw.HTML(
        """<div style="line-height: 140%; padding-top: 0px; padding-bottom: 10px; opacity:0.5;">
        <b><a href="https://www.materialscloud.org/discover/sssp/table/efficiency"
        target="_blank">Standard solid-state pseudopotentials</a> (SSSP)</b></div>"""
    )
    pseudo_family_help = ipw.HTML(
        """<div style="line-height: 140%; padding-top: 10px; padding-bottom: 0px; opacity:0.5;">
        If you are unsure, select 'SSSP efficiency', which for
        most calculations will produce sufficiently accurate results at
        comparatively small computational costs. If your calculations require a
        higher accuracy, select 'SSSP accuracy', which will be computationally
        more expensive.</div>"""
    )

    dft_functional_prompt = ipw.HTML(
        """
        <div style="line-height: 140%; padding-top: 0px; padding-bottom: 10px; opacity:0.5;"><b>
        Exchange-correlation  functional</b></div>"""
    )
    dft_functional_help = ipw.HTML(
        """<div style="line-height: 140%; padding-top: 10px; padding-bottom: 10px; opacity:0.5;">
        The exchange-correlation energy is calculated using this functional. We currently provide support for two
        well-established generalised gradient approximation (GGA) functionals:
        PBE and PBEsol.</div>"""
    )
    disabled = traitlets.Bool()

    value = traitlets.Unicode(
        default_value=DEFAULT_PARAMETERS["advance"]["pseudo_family"],
    )

    def __init__(self, **kwargs):
        self.show_ui = ipw.Valid(value=True)

        # Choose the DFT functional
        self.dft_functional = ipw.Dropdown(
            options=["PBE", "PBEsol"],
            value=DEFAULT_PARAMETERS["advance"]["pseudo_family"].split("/")[2],
            style={"description_width": "initial"},
            disable=False,
        )
        self.dft_functional.observe(self.set_value_trait, "value")

        self.protocol_selection = ipw.ToggleButtons(
            options=["efficiency", "precision"],
            value=DEFAULT_PARAMETERS["advance"]["pseudo_family"].split("/")[3],
            layout=ipw.Layout(max_width="80%"),
            disable=False,
        )
        self.protocol_selection.observe(self.set_value_trait, "value")

        self.dft_functional_box = ipw.VBox(
            children=[
                self.dft_functional_prompt,
                self.dft_functional,
                self.dft_functional_help,
            ],
            layout=ipw.Layout(max_width="40%"),
        )
        self.pseudo_protocol_box = ipw.VBox(
            children=[
                self.pseudo_family_prompt,
                self.protocol_selection,
                self.pseudo_family_help,
            ],
            layout=ipw.Layout(max_width="60%"),
        )

        self.set_value_trait()

        super().__init__(
            children=[
                self.title,
                ipw.HBox(
                    [self.description],
                    layout=ipw.Layout(height="50px", justify_content="space-between"),
                ),
                ipw.HBox([self.dft_functional_box, self.pseudo_protocol_box]),
            ]
        )

    def set_value_trait(self, _=None):
        self.value = (
            f"SSSP/1.2/{self.dft_functional.value}/{self.protocol_selection.value}"
        )

    def set_show_ui(self, change):
        self.show_ui.value = not change.new

    def set_text_color(self, change):
        opacity = 1.0 if change.new else 0.5

        for html in (
            self.pseudo_family_prompt,
            self.pseudo_family_help,
            self.dft_functional_help,
            self.dft_functional_prompt,
        ):
            old_opacity = re.match(
                r"[\s\S]+opacity:([\S]+);[\S\s]+", html.value
            ).groups()[0]
            html.value = html.value.replace(
                f"opacity:{old_opacity};", f"opacity:{opacity};"
            )

    def reset(self):
        self.protocol_selection.value = "efficiency"
