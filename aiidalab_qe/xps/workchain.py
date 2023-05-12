from aiida.orm import Bool, Dict, Group, QueryBuilder, load_code
from aiida.plugins import WorkflowFactory

XpsWorkChain = WorkflowFactory("quantumespresso.xps")


def get_builder(codes, structure, parameters):
    protocol = parameters["basic"].pop("protocol", "fast")
    pseudo_family = parameters["advance"].get("pseudo_family", None)
    xps_parameters = parameters.get("xps", {})
    correction_energies = xps_parameters.pop("correction_energies", {})
    elements_list = xps_parameters.pop("elements_list", None)
    # set core hole treatment for element
    core_hole_treatment = xps_parameters.pop("core_hole_treatment", "xch_smear")
    core_hole_treatments = {}
    for element in elements_list:
        core_hole_treatments[element] = core_hole_treatment
    # load pseudo for excited-state and group-state.
    pseudo_group = xps_parameters.pop("pseudo_group")
    pseudo_group = (
        QueryBuilder().append(Group, filters={"label": pseudo_group}).one()[0]
    )
    # set pseudo for element
    pseudos = {}
    elements = []
    for label in elements_list:
        element = label.split("_")[0]
        pseudos[element] = {
            "core_hole": [pseudo.element: pseudo for pseudo in group.nodes if pseudo.label == label][0],
            "gipaw": [pseudo.element: pseudo for pseudo in group.nodes if pseudo.label == f"{element}_gs"][0],
        }
        elements.append(element)
    # TODO should we override the cutoff_wfc, cutoff_rho by the new pseudo?
    structure_preparation_settings = xps_parameters.pop(
        "structure_preparation_settings", Dict({})
    )
    pw_code = load_code(codes.get("pw_code"))
    overrides = {
        "ch_scf": parameters["advance"].get("pw", {}),
    }
    parameters = parameters["basic"].update(xps_parameters)
    builder = XpsWorkChain.get_builder_from_protocol(
        code=pw_code,
        structure=structure,
        protocol=protocol,
        overrides=overrides,
        pseudos=pseudos,
        elements_list=elements_list,
        calc_binding_energy=Bool(True),
        correction_energies=Dict(correction_energies),
        core_hole_treatments=core_hole_treatments,
        overrides=overrides,
        structure_preparation_settings=structure_preparation_settings,
        **parameters,
    )
    builder.pop("relax")
    builder.pop("clean_workdir", None)
    return builder

subworkchain = [XpsWorkChain, get_builder]
