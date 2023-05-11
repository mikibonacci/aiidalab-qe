from aiida.orm import Bool, Dict, Group, QueryBuilder, load_code
from aiida.plugins import WorkflowFactory

XpsWorkChain = WorkflowFactory("quantumespresso.xps")


def get_pseudo(group, element):
    pseudos = {pseudo.element: pseudo for pseudo in group.nodes}
    return pseudos.get(element, None)


def get_builder(codes, structure, parameters):
    pseudo_set = Group
    xps_overrides = parameters.get("xps", {})
    pseudo_family = parameters["advance"].get("pseudo_family", None)
    # set pseudo for normal elements
    if pseudo_family is not None:
        xps_overrides.setdefault("ch_scf", {})["pseudo_family"] = pseudo_family
    # load pseudo for excited-state and group-state.
    es_pseudo_family = xps_overrides.pop("es_pseudo", "core_hole")
    gs_pseudo_family = xps_overrides.pop("gs_pseudo", "gipaw")
    es_pseudo_family = (
        QueryBuilder().append(pseudo_set, filters={"label": es_pseudo_family}).one()[0]
    )
    gs_pseudo_family = (
        QueryBuilder().append(pseudo_set, filters={"label": gs_pseudo_family}).one()[0]
    )
    # set pseudo and core hole treatment for element
    pseudos = {}
    core_hole_treatments = {}
    core_hole_treatment = xps_overrides.pop("core_hole_treatment", "full")
    elements_list = xps_overrides.pop("elements_list", None)
    if not elements_list:
        elements_list = [kind.symbol for kind in structure.kinds]
    for element in elements_list:
        es_pseudo = get_pseudo(es_pseudo_family, element)
        gs_pseudo = get_pseudo(gs_pseudo_family, element)
        if es_pseudo is not None and gs_pseudo is not None:
            pseudos[element] = {
                "core_hole": es_pseudo,
                "gipaw": gs_pseudo,
            }
        core_hole_treatments[element] = core_hole_treatment
    # binding energy
    calc_binding_energy = xps_overrides.pop("calc_binding_energy", False)
    correction_energies = xps_overrides.pop("correction_energies", {})
    # TODO should we override the cutoff_wfc, cutoff_rho by the new pseudo?
    structure_preparation_settings = xps_overrides.pop(
        "structure_preparation_settings", Dict({})
    )

    protocol = parameters["basic"].pop("protocol", "fast")
    pw_code = load_code(codes.get("pw_code"))
    pw = parameters["advance"].get("pw", {})
    pw["pseudo_family"] = parameters["advance"].get("pseudo_family", None)
    overrides = {
        "scf": pw,
        "bands": pw,
    }
    parameters = parameters["basic"]
    builder = XpsWorkChain.get_builder_from_protocol(
        code=pw_code,
        structure=structure,
        protocol=protocol,
        overrides=overrides,
        pseudos=pseudos,
        elements_list=elements_list,
        calc_binding_energy=Bool(calc_binding_energy),
        correction_energies=Dict(correction_energies),
        core_hole_treatments=core_hole_treatments,
        overrides=xps_overrides,
        structure_preparation_settings=structure_preparation_settings,
        **parameters,
    )
    builder.pop("relax")
    builder.pop("clean_workdir", None)
    return builder


subworkchain = [XpsWorkChain, get_builder]
