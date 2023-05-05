def test_workchain_settings():
    from aiidalab_qe.configure.workflow import WorkChainSettings

    wcs = WorkChainSettings()
    assert wcs.relax_type.value == "positions_cell"
    assert wcs.properties["bands"].run.value is False
    # get value
    parameters = wcs.get_panel_value()
    assert parameters["properties"]["bands"] is False
    # set value
    parameters = {"relax": "positions", "properties": {"bands": True}}
    wcs.load_panel_value(parameters)
    assert wcs.relax_type.value == "positions"
    assert wcs.properties["bands"].run.value is True
