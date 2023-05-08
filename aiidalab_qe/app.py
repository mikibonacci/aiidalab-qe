import ipywidgets as ipw
from aiida.orm import load_node
from aiidalab_widgets_base import (
    BasicCellEditor,
    BasicStructureEditor,
    OptimadeQueryWidget,
    StructureBrowserWidget,
    StructureExamplesWidget,
    StructureManagerWidget,
    StructureUploadWidget,
    WizardAppWidget,
    WizardAppWidgetStep,
)

from aiidalab_qe.configure.configure import ConfigureQeAppWorkChainStep
from aiidalab_qe.process import WorkChainSelector
from aiidalab_qe.steps import (
    SubmitQeAppWorkChainStep,
    ViewQeAppWorkChainStatusAndResultsStep,
)
from aiidalab_qe.structures import Examples, StructureSelectionStep
from aiidalab_qe.utils import get_entries

OptimadeQueryWidget.title = "OPTIMADE"  # monkeypatch


def load_structure_importers():
    # add plugin specific structure importers
    importers = [
        StructureUploadWidget(title="Upload file"),
        OptimadeQueryWidget(embedded=False),
        StructureBrowserWidget(title="AiiDA database"),
        StructureExamplesWidget(title="From Examples", examples=Examples),
    ]
    entries = get_entries("aiidalab_qe.structure.importer")
    for _name, entry_point in entries.items():
        importers.append(entry_point())
    return importers


class QEApp:
    def __init__(self) -> None:
        # Create the application steps
        structure_manager_widget = StructureManagerWidget(
            importers=load_structure_importers,
            editors=[
                BasicCellEditor(title="Edit cell"),
                BasicStructureEditor(title="Edit structure"),
            ],
            node_class="StructureData",
            storable=False,
            configuration_tabs=["Cell", "Selection", "Appearance", "Download"],
        )
        self.structure_step = StructureSelectionStep(
            parent=self, manager=structure_manager_widget, auto_advance=True
        )
        self.configure_step = ConfigureQeAppWorkChainStep(
            parent=self, auto_advance=True
        )
        self.submit_step = SubmitQeAppWorkChainStep(parent=self, auto_advance=True)
        self.results_step = ViewQeAppWorkChainStatusAndResultsStep(parent=self)

        # Link the application steps
        ipw.dlink(
            (self.structure_step, "state"),
            (self.configure_step, "previous_step_state"),
        )
        ipw.dlink(
            (self.configure_step, "state"),
            (self.submit_step, "previous_step_state"),
        )
        ipw.dlink(
            (self.structure_step, "confirmed_structure"),
            (self.submit_step, "input_structure"),
        )
        ipw.dlink(
            (self.submit_step, "process"),
            (self.results_step, "process"),
            transform=lambda node: node.uuid if node is not None else None,
        )

        # Add the application steps to the application
        self.steps = WizardAppWidget(
            steps=[
                ("Select structure", self.structure_step),
                ("Configure workflow", self.configure_step),
                ("Choose computational resources", self.submit_step),
                ("Status & Results", self.results_step),
            ]
        )

        # Reset all subsequent steps in case that a new structure is selected
        def _observe_structure_selection(change):
            with self.structure_step.hold_sync():
                if (
                    self.structure_step.confirmed_structure is not None
                    and self.structure_step.confirmed_structure != change["new"]
                ):
                    self.steps.reset()

        self.structure_step.observe(_observe_structure_selection, "structure")

        # Add process selection header
        self.work_chain_selector = WorkChainSelector(layout=ipw.Layout(width="auto"))

        def _observe_process_selection(change):
            if change["old"] == change["new"]:
                return
            pk = change["new"]
            if pk is None:
                self.steps.reset()
                self.steps.selected_index = 0
            else:
                process = load_node(pk)
                with structure_manager_widget.hold_sync():
                    with self.structure_step.hold_sync():
                        self.steps.selected_index = 3
                        structure_manager_widget.input_structure = (
                            process.inputs.structure
                        )
                        self.structure_step.structure = process.inputs.structure
                        self.structure_step.confirmed_structure = (
                            process.inputs.structure
                        )
                        self.configure_step.state = WizardAppWidgetStep.State.SUCCESS
                        self.submit_step.process = process

        self.work_chain_selector.observe(_observe_process_selection, "value")
        ipw.dlink(
            (self.submit_step, "process"),
            (self.work_chain_selector, "value"),
            transform=lambda node: None if node is None else node.pk,
        )
        self.work_chain = ipw.VBox(children=[self.work_chain_selector, self.steps])
