"""
Four steps
len(app.steps) == 4
app.steps[0][0]         app.steps[0][1]
('Select structure', structure_selection_step),
('Configure workflow', configure_qe_app_work_chain_step),
('Choose computational resources', submit_qe_app_work_chain_step),
('Status & Results', view_qe_app_work_chain_status_and_results_step),

"""


def test_steps():
    from aiida.plugins import DataFactory
    from aiidalab_widgets_base import WizardAppWidgetStep
    from ase.io import read

    from aiidalab_qe.app import QEApp
    from aiidalab_qe.structures import Examples

    #
    app = QEApp()
    was = WizardAppWidgetStep()
    # step 1
    # select structure
    StructureData = DataFactory("core.structure")
    mol = read(Examples[0][1])
    mol = StructureData(ase=mol)
    mol.store()
    #
    s1 = app.steps.steps[0][1]
    structure = s1.manager.children[0].children[2]
    structure.search()
    key = [key for key in structure.results.options if key.startswith(f"PK: {mol.pk}")][
        0
    ]
    structure.results.value = structure.results.options[key]
    s1.confirm()
    # step 2
    s2 = app.steps.steps[1][1]
    s2.workchain_settings.relax_type.value = "none"
    s2.workchain_settings.properties["pdos"].run.value = True
    s2.workchain_settings.properties["bands"].run.value = True
    # s2.workchain_settings.properties["eos"].run.value = True
    # s2.workchain_settings.properties["hello_world"].run.value = True
    s2.basic_settings.workchain_protocol.value = "fast"
    s2.confirm()
    # step 3
    #
    s3 = app.steps.steps[2][1]
    assert s3.previous_step_state == was.State.SUCCESS
    assert s3.state == s3.State.CONFIGURED
    s3.resources_config.num_cpus.value = 4
    assert s3.resources_config.num_cpus.value == 4
    s3.submit()
    assert s3.state == was.State.SUCCESS
