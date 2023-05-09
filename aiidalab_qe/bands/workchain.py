from aiida.orm import load_code
from aiida.plugins import WorkflowFactory

PwBandsWorkChain = WorkflowFactory("quantumespresso.pw.bands")


def get_builder(codes, structure, parameters):
    protocol = parameters["basic"].pop("protocol", "fast")
    pw_code = load_code(codes.get("pw_code"))
    pw = parameters["advance"].get("pw", {})
    pw["pseudo_family"] = parameters["advance"].get("pseudo_family", None)
    overrides = {
        "scf": pw,
        "bands": pw,
    }
    parameters = parameters["basic"]
    builder = PwBandsWorkChain.get_builder_from_protocol(
        code=pw_code,
        structure=structure,
        protocol=protocol,
        overrides=overrides,
        **parameters,
    )
    builder.pop("relax")
    builder.pop("clean_workdir", None)
    return builder


subworkchain = [PwBandsWorkChain, get_builder]
