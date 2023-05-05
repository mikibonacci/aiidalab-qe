# -*- coding: utf-8 -*-
"""Class to .

Authors:

    * Xing Wang <xing.wang@psi.ch>
"""
import ipywidgets as ipw


class Panel(ipw.VBox):
    """Base class for all the panels.

    The base class has a method to return the value of all the widgets in the panel as a dictionary. The dictionary is used to construct the input file for the calculation. The class also has a method to load a dictionary to set the value of the widgets in the panel.
    """

    def __init__(self, children=None, **kwargs):
        """Initialize the panel.

        :param kwargs: keyword arguments to pass to the ipw.VBox constructor.
        """
        super().__init__(
            children=children,
            **kwargs,
        )

    def get_panel_value(self):
        """Return the value of all the widgets in the panel as a dictionary.

        :return: a dictionary of the values of all the widgets in the panel.
        """
        return {}

    def load_panel_value(self, panel_value):
        """Load a dictionary to set the value of the widgets in the panel.

        :param panel_value: a dictionary of the values of all the widgets in the panel.
        """
        for key, value in panel_value.items():
            if key in self.__dict__:
                setattr(self, key, value)


class ResultPanel(Panel):
    """Base class for all the result panels.

    The base class has a method to load the result of the calculation. And a show method to display it in the panel. It has a update method to update the result in the panel.
    """

    def __init__(self, wc_node=None, children=None, **kwargs):
        """Initialize the panel.

        :param kwargs: keyword arguments to pass to the ipw.VBox constructor.
        """
        self.wc_node = wc_node
        super().__init__(
            children=children,
            **kwargs,
        )

    def load_result(self, result):
        """Load the result of the calculation.

        :param result: the result of the calculation.
        """
        pass

    def show(self):
        """Display the result in the panel."""
        pass

    def update(self, result):
        """Update the result in the panel.

        :param result: the result of the calculation.
        """
        pass
