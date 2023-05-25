FUNCTIONAL_LINK_MAP = {
    "PBE": "https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.77.3865",
    "PBEsol": "https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.100.136406",
}

PSEUDO_LINK_MAP = {
    "SSSP": "https://www.materialscloud.org/discover/sssp/table/efficiency"
}

PROTOCOL_PSEUDO_MAP = {
    "fast": "SSSP/1.2/PBE/efficiency",
    "moderate": "SSSP/1.2/PBE/efficiency",
    "precise": "SSSP/1.2/PBE/precision",
}

FUNCTIONAL_REPORT_MAP = {
    "LDA": "local density approximation (LDA)",
    "PBE": "generalized gradient approximation of Perdew-Burke-Ernzerhof (PBE)",
    "PBEsol": "the revised generalized gradient approximation of Perdew-Burke-Ernzerhof (PBE) for solids",
}


def _generate_report_dict(builder_parameters: dict):
    """Read from the bulider parameters and generate a dictionacry
    for reporting the inputs for the `QeAppWorkChain` with proper name corresponding
    to the template.
    """
    # Workflow logic
    yield "relax_method", builder_parameters["relax_type"]
    yield "relaxed", builder_parameters["run_relax"]
    yield "bands_computed", builder_parameters["run_bands"]
    yield "pdos_computed", builder_parameters["run_pdos"]

    # Material settings
    yield "material_magnetic", builder_parameters["spin_type"]
    yield "electronic_type", builder_parameters["electronic_type"]

    # Calculation settings
    yield "protocol", builder_parameters["protocol"]

    # Pseudopotential settings
    yield "pseudo_family", builder_parameters["pseudo_family"]
    yield "pseudo_version", builder_parameters["pseudo_version"]
    yield "pseudo_protocol", builder_parameters["pseudo_protocol"]

    pseudo_library = builder_parameters["pseudo_library"]
    functional = builder_parameters["functional"]
    yield "pseudo_library", pseudo_library
    yield "functional", functional

    yield "pseudo_link", PSEUDO_LINK_MAP[pseudo_library]
    yield "functional_link", FUNCTIONAL_LINK_MAP[functional]

    # Detail calculation parameters
    yield "energy_cutoff_wfc", builder_parameters["energy_cutoff_wfc"]
    yield "energy_cutoff_rho", builder_parameters["energy_cutoff_rho"]
    yield "scf_kpoints_distance", builder_parameters["scf_kpoints_distance"]
    yield "bands_kpoints_distance", builder_parameters["bands_kpoints_distance"]
    yield "nscf_kpoints_distance", builder_parameters["nscf_kpoints_distance"]

    occupation = builder_parameters["occupation"]
    yield "occupation_type", occupation

    if occupation == "smearing":
        yield "degauss", builder_parameters["degauss"]
        yield "smearing", builder_parameters["smearing"]


def _generate_report_html(report):
    """Read from the bulider parameters and generate a html for reporting
    the inputs for the `QeAppWorkChain`.
    """
    from importlib import resources

    from jinja2 import Environment

    from aiidalab_qe.app import static

    def _fmt_yes_no(truthy):
        return "Yes" if truthy else "No"

    env = Environment()
    env.filters.update(
        {
            "fmt_yes_no": _fmt_yes_no,
        }
    )
    template = resources.read_text(static, "workflow_summary.jinja")
    style = resources.read_text(static, "style.css")

    return env.from_string(template).render(style=style, **report)


def generate_report_html(qeapp_wc):
    """Generate a html for reporting the inputs for the `QeAppWorkChain`"""
    builder_parameters = qeapp_wc.base.extras.get("builder_parameters", {})
    report = dict(_generate_report_dict(builder_parameters))

    return _generate_report_html(report)


def generate_report_text(report_dict):
    """Generate a text for reporting the inputs for the `QeAppWorkChain`

    :param report_dict: dictionary generated by the `generate_report_dict` function.
    """

    report_string = (
        "All calculations are performed within the density-functional "
        "theory formalism as implemented in the Quantum ESPRESSO code. "
        "The pseudopotential for each element is extracted from the "
        f'{report_dict["Pseudopotential library"][0]} '
        "library. The wave functions "
        "of the valence electrons are expanded in a plane wave basis set, using an "
        "energy cutoff equal to "
        f'{round(report_dict["Plane wave energy cutoff (wave functions)"][0])} Ry '
        "for the wave functions and "
        f'{round(report_dict["Plane wave energy cutoff (charge density)"][0])} Ry '
        "for the charge density and potential. "
        "The exchange-correlation energy is "
        "calculated using the "
        f'{FUNCTIONAL_REPORT_MAP[report_dict["Functional"][0]]}. '
        "A Monkhorst-Pack mesh is used for sampling the Brillouin zone, where the "
        "distance between the k-points is set to "
    )
    kpoints_distances = []
    kpoints_calculations = []

    for calc in ("SCF", "NSCF", "Bands"):
        if f"K-point mesh distance ({calc})" in report_dict:
            kpoints_distances.append(
                str(report_dict[f"K-point mesh distance ({calc})"][0])
            )
            kpoints_calculations.append(calc)

    report_string += ", ".join(kpoints_distances)
    report_string += " for the "
    report_string += ", ".join(kpoints_calculations)
    report_string += " calculation"
    if len(kpoints_distances) > 1:
        report_string += "s, respectively"
    report_string += "."

    return report_string