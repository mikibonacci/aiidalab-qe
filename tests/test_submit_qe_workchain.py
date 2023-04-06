import pytest


@pytest.mark.usefixtures("aiida_profile_clean")
def test_get_input_parameters(data_regression, pw_code, dos_code, projwfc_code):
    from aiida import orm

    from aiidalab_qe.pseudos import PseudoFamilySelector
    from aiidalab_qe.steps import (
        KpointSettings,
        SmearingSettings,
        SubmitQeAppWorkChainStep,
        WorkChainSettings,
    )

    submit_step = SubmitQeAppWorkChainStep(qe_auto_setup=False)

    submit_step.workchain_settings = WorkChainSettings()
    submit_step.pseudo_family_selector = PseudoFamilySelector()
    submit_step.kpoints_settings = KpointSettings()
    submit_step.smearing_settings = SmearingSettings()

    submit_step.pw_code.value = pw_code.uuid
    submit_step.dos_code.value = dos_code.uuid
    submit_step.projwfc_code.value = projwfc_code.uuid

    parameters = submit_step.get_input_parameters()

    # Check and validate the parameters
    # The dict store code uuids, but we want to check the labels.
    parameters["pw_code"] = orm.load_code(parameters["pw_code"]).label
    parameters["dos_code"] = orm.load_code(parameters["dos_code"]).label
    parameters["projwfc_code"] = orm.load_code(parameters["projwfc_code"]).label

    data_regression.check(parameters)