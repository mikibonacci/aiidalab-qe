def test_step1_select_structure():
    from aiidalab_widgets_base import WizardAppWidgetStep

    from aiidalab_qe.app import QEApp
    from aiidalab_qe.structures import Examples

    app = QEApp()
    was = WizardAppWidgetStep()
    # step 1
    # from example
    s1 = app.steps.steps[0][1]
    structure = s1.manager.children[0].children[3]
    structure._select_structure.value = Examples[2][1]
    assert len(structure.structure) == 16
    s1.confirm()
    assert s1.state == was.State.SUCCESS
