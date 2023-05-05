import ipywidgets as ipw
import traitlets
from aiidalab_widgets_base import WizardAppWidgetStep

from aiidalab_qe.configure.basic import BasicSettings
from aiidalab_qe.configure.workflow import WorkChainSettings
from aiidalab_qe.parameters import DEFAULT_PARAMETERS
from aiidalab_qe.utils import get_entries


class ConfigureQeAppWorkChainStep(ipw.VBox, WizardAppWidgetStep):
    confirmed = traitlets.Bool()
    previous_step_state = traitlets.UseEnum(WizardAppWidgetStep.State)
    workchain_settings = traitlets.Instance(WorkChainSettings, allow_none=True)
    basic_settings = traitlets.Instance(BasicSettings, allow_none=True)

    def __init__(self, **kwargs):
        # add plugin specific settings
        entries = get_entries("aiidalab_qe_configuration")
        for name, entry_point in entries.items():
            new_name = f"{name}_settings"
            setattr(self, new_name, entry_point())

        self.workchain_settings = WorkChainSettings()
        self.basic_settings = BasicSettings()
        self.workchain_settings.relax_type.observe(self._update_state, "value")

        self.tab = ipw.Tab(
            children=[
                self.workchain_settings,
                self.basic_settings,
            ],
            layout=ipw.Layout(min_height="250px"),
        )

        self.tab.set_title(0, "Workflow")
        self.tab.set_title(1, "Basic settings")

        # add plugin specific settings
        self.settings = {
            "workflow": self.workchain_settings,
            "basic": self.basic_settings,
        }
        entries = get_entries("aiidalab_qe_configuration")
        for name, entry_point in entries.items():
            self.settings[name] = entry_point()
            self.tab.children += (self.settings[name],)
            self.tab.set_title(len(self.tab.children) - 1, name)
            # link basic protocol to all plugin specific protocols
            if hasattr(self.settings[name], "workchain_protocol"):
                ipw.dlink(
                    (self.basic_settings.workchain_protocol, "value"),
                    (self.settings[name].workchain_protocol, "value"),
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
