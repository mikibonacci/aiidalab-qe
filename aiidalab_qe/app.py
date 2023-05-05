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

from aiidalab_qe.process import WorkChainSelector
from aiidalab_qe.steps import (
    SubmitQeAppWorkChainStep,
    ViewQeAppWorkChainStatusAndResultsStep,
)
from aiidalab_qe.structures import Examples, StructureSelectionStep

OptimadeQueryWidget.title = "OPTIMADE"  # monkeypatch


class QEApp:
    def __init__(self) -> None:
        # Create the application steps
        structure_manager_widget = StructureManagerWidget(
            importers=[
                StructureUploadWidget(title="Upload file"),
                OptimadeQueryWidget(embedded=False),
                StructureBrowserWidget(title="AiiDA database"),
                StructureExamplesWidget(title="From Examples", examples=Examples),
            ],
            editors=[
                BasicCellEditor(title="Edit cell"),
                BasicStructureEditor(title="Edit structure"),
            ],
            node_class="StructureData",
            storable=False,
            configuration_tabs=["Cell", "Selection", "Appearance", "Download"],
        )
        structure_selection_step = StructureSelectionStep(
            manager=structure_manager_widget, auto_advance=True
        )
        submit_qe_app_work_chain_step = SubmitQeAppWorkChainStep(auto_advance=True)
        view_qe_app_work_chain_status_and_results_step = (
            ViewQeAppWorkChainStatusAndResultsStep()
        )

        # Link the application steps
        ipw.dlink(
            (structure_selection_step, "state"),
            (submit_qe_app_work_chain_step.configure_step, "previous_step_state"),
        )
        ipw.dlink(
            (structure_selection_step, "confirmed_structure"),
            (submit_qe_app_work_chain_step, "input_structure"),
        )

        ipw.dlink(
            (submit_qe_app_work_chain_step, "process"),
            (view_qe_app_work_chain_status_and_results_step, "process"),
            transform=lambda node: node.uuid if node is not None else None,
        )

        # here I add the configure step to the submit step, so that the submit step can access the configuration parameters
        # maybe we can find a better way to do this

        # Add the application steps to the application
        self.steps = WizardAppWidget(
            steps=[
                ("Select structure", structure_selection_step),
                ("Configure workflow", submit_qe_app_work_chain_step.configure_step),
                ("Choose computational resources", submit_qe_app_work_chain_step),
                ("Status & Results", view_qe_app_work_chain_status_and_results_step),
            ]
        )

        # Reset all subsequent steps in case that a new structure is selected
        def _observe_structure_selection(change):
            with structure_selection_step.hold_sync():
                if (
                    structure_selection_step.confirmed_structure is not None
                    and structure_selection_step.confirmed_structure != change["new"]
                ):
                    self.steps.reset()

        structure_selection_step.observe(_observe_structure_selection, "structure")

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
                    with structure_selection_step.hold_sync():
                        self.steps.selected_index = 3
                        structure_manager_widget.input_structure = (
                            process.inputs.structure
                        )
                        structure_selection_step.structure = process.inputs.structure
                        structure_selection_step.confirmed_structure = (
                            process.inputs.structure
                        )
                        submit_qe_app_work_chain_step.configure_step.state = (
                            WizardAppWidgetStep.State.SUCCESS
                        )
                        submit_qe_app_work_chain_step.process = process

        self.work_chain_selector.observe(_observe_process_selection, "value")
        ipw.dlink(
            (submit_qe_app_work_chain_step, "process"),
            (self.work_chain_selector, "value"),
            transform=lambda node: None if node is None else node.pk,
        )
        self.work_chain = ipw.VBox(children=[self.work_chain_selector, self.steps])
