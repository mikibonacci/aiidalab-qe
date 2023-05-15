import ipywidgets as ipw
import traitlets
from aiida.plugins import DataFactory
from aiidalab_widgets_base import WizardAppWidgetStep

from aiidalab_qe.configure.advance import AdvanceSettings
from aiidalab_qe.configure.basic import BasicSettings
from aiidalab_qe.configure.workflow import WorkChainSettings
from aiidalab_qe.parameters import DEFAULT_PARAMETERS
from aiidalab_qe.utils import get_entry_items

StructureData = DataFactory("core.structure")


class ConfigureQeAppWorkChainStep(ipw.VBox, WizardAppWidgetStep):
    confirmed = traitlets.Bool()
    previous_step_state = traitlets.UseEnum(WizardAppWidgetStep.State)
    input_structure = traitlets.Instance(StructureData, allow_none=True)

    def __init__(self, parent, **kwargs):
        self.parent = parent

        self.workchain_settings = WorkChainSettings()
        self.basic_settings = BasicSettings()
        self.advance_settings = AdvanceSettings()
        self.workchain_settings.relax_type.observe(self._update_state, "value")
        ipw.dlink(
            (self.basic_settings.workchain_protocol, "value"),
            (self.advance_settings.workchain_protocol, "value"),
        )
        #
        self.tab = ipw.Tab(
            children=[
                self.workchain_settings,
                self.basic_settings,
                self.advance_settings,
            ],
            layout=ipw.Layout(min_height="250px"),
        )

        self.tab.set_title(0, "Workflow")
        self.tab.set_title(1, "Basic settings")
        self.tab.set_title(2, "Advance settings")

        # add plugin specific settings
        self.settings = {
            "workflow": self.workchain_settings,
            "basic": self.basic_settings,
            "advance": self.advance_settings,
        }
        # add plugin specific settings
        entries = get_entry_items("aiidalab_qe.property", "setting")
        for name, entry_point in entries.items():
            self.settings[name] = entry_point(parent=self)
            # link basic protocol to all plugin specific protocols
            if hasattr(self.settings[name], "workchain_protocol"):
                ipw.dlink(
                    (self.basic_settings.workchain_protocol, "value"),
                    (self.settings[name].workchain_protocol, "value"),
                )
            if name in self.workchain_settings.properties:
                self.workchain_settings.properties[name].run.observe(
                    self._update_panel, "value"
                )

        self._submission_blocker_messages = ipw.HTML()

        self.confirm_button = ipw.Button(
            description="Confirm",
            tooltip="Confirm the currently selected settings and go to the next step.",
            button_style="success",
            icon="check-circle",
            disabled=True,
            layout=ipw.Layout(width="auto"),
        )

        self.confirm_button.on_click(self.confirm)

        super().__init__(
            children=[
                self.tab,
                self._submission_blocker_messages,
                self.confirm_button,
            ],
            **kwargs,
        )

    @traitlets.observe("previous_step_state")
    def _observe_previous_step_state(self, change):
        self._update_state()

    def get_input_parameters(self):
        """Get the builder parameters based on the GUI inputs."""

        parameters = dict()
        for name, settings in self.settings.items():
            parameters.update({name: settings.get_panel_value()})
        return parameters

    def set_input_parameters(self, parameters):
        """Set the inputs in the GUI based on a set of parameters."""

        with self.hold_trait_notifications():
            for name, settings in self.settings.items():
                if parameters.get(name, False):
                    settings.load_panel_value(parameters[name])

    def _update_state(self, _=None):
        if self.previous_step_state == self.State.SUCCESS:
            self.confirm_button.disabled = False
            self._submission_blocker_messages.value = ""
            self.state = self.State.CONFIGURED
            # update plugin specific settings
            for _, settings in self.settings.items():
                settings._update_state()
        elif self.previous_step_state == self.State.FAIL:
            self.state = self.State.FAIL
        else:
            self.confirm_button.disabled = True
            self.state = self.State.INIT
            self.set_input_parameters(DEFAULT_PARAMETERS)

    def confirm(self, _=None):
        self.confirm_button.disabled = False
        self.state = self.State.SUCCESS

    @traitlets.default("state")
    def _default_state(self):
        return self.State.INIT

    def reset(self):
        with self.hold_trait_notifications():
            self.set_input_parameters(DEFAULT_PARAMETERS)

    def _update_panel(self, _=None):
        """Dynamic add/remove the panel based on the the the workchain settings."""
        self.tab.children = [
            self.workchain_settings,
            self.basic_settings,
            self.advance_settings,
        ]
        for name in self.workchain_settings.properties:
            if (
                name in self.settings
                and self.workchain_settings.properties[name].run.value
            ):
                self.tab.children += (self.settings[name],)
                self.tab.set_title(
                    len(self.tab.children) - 1, self.settings[name].title
                )
