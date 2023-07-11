"""Results view widgets (MOVE TO OTHER MODULE!)

Authors:

    * Xing Wang <xing.wang@psi.ch>
"""

from aiidalab_qe.panel import ResultPanel
import ipywidgets as ipw


class Result(ResultPanel):
    title = "EOS"
    workchain_label = "eos"

    def _update_view(self):
        import plotly.graph_objects as go
        from ase.eos import EquationOfState
        # init figure
        g = go.FigureWidget(
            layout=go.Layout(
                title=dict(text="Equation of State"),
                barmode="overlay",
            )
        )
        g.layout.xaxis.title = "Volume (A^3)"
        g.layout.yaxis.title = "Energy (eV)"
        #
        eos = self.node.outputs.eos.get_dict()
        volumes = eos["volumes"]
        energies = eos["energies"]
        eos = EquationOfState(volumes, energies, eos="birchmurnaghan")
        v0, e0, B = eos.fit()
        plotdata = eos.getplotdata()
        g.add_scatter(x=volumes, y=energies, mode="markers", marker=dict(size=10), name="DFT")
        g.add_scatter(x=plotdata[4], y=plotdata[5], mode="lines", name="Birch-Murnaghan")
        #
        self.summary_view = ipw.HTML(
            """<div style="padding-top: 0px; padding-bottom: 0px">
            <h4>Parameters</h4>
            <table>
                <tr>
                    <td>V0</td>
                    <td>{:1.3f}</td>
                </tr>
                <tr>
                    <td>E0</td>
                    <td>{:1.3f}</td>
                </tr>
                <tr>
                    <td>B</td>
                    <td>{:1.3f}</td>
                </tr>
                </table>
            </div>""".format(v0, e0, B)
        )
        self.children = [
            ipw.HBox(
                    children=[self.summary_view, g],
                    layout=ipw.Layout(justify_content="space-between", margin="10px"),
                ),
            ]
