# AiiDA imports.
from aiida.common import AttributeDict
from aiida.engine import ToContext, WorkChain, if_
from aiida.orm import CalcJobNode, load_code
from aiida.plugins import DataFactory, WorkflowFactory

# AiiDA Quantum ESPRESSO plugin inputs.
from aiida_quantumespresso.common.types import ElectronicType, RelaxType, SpinType
from aiida_quantumespresso.utils.mapping import prepare_process_inputs

# Data objects and work chains.
PwRelaxWorkChain = WorkflowFactory("quantumespresso.pw.relax")
PwBandsWorkChain = WorkflowFactory("quantumespresso.pw.bands")
PdosWorkChain = WorkflowFactory("quantumespresso.pdos")

Bool = DataFactory("core.bool")
Float = DataFactory("core.float")
Dict = DataFactory("core.dict")
Str = DataFactory("core.str")
XyData = DataFactory("core.array.xy")
StructureData = DataFactory("core.structure")
BandsData = DataFactory("core.array.bands")
Orbital = DataFactory("core.orbital")


# load entry points
def get_entries(entry_point_name="aiidalab_qe.configuration"):
    from importlib.metadata import entry_points

    entries = {}
    for entry_point in entry_points().get(entry_point_name, []):
        entries[entry_point.name] = entry_point.load()

    return entries


entries = get_entries("aiidalab_qe.subworkchain")


class QeAppWorkChain(WorkChain):
    """WorkChain designed to calculate the requested properties in the AiiDAlab Quantum ESPRESSO app."""

    @classmethod
    def define(cls, spec):
        """Define the process specification."""
        # yapf: disable
        super().define(spec)
        spec.input('structure', valid_type=StructureData,
                   help='The inputs structure.')
        spec.input('clean_workdir', valid_type=Bool, default=lambda: Bool(False),
                   help='If `True`, work directories of all called calculation will be cleaned at the end of execution.')
        spec.expose_inputs(PwRelaxWorkChain, namespace='relax', exclude=('clean_workdir', 'structure'),
                           namespace_options={'required': False, 'populate_defaults': False,
                                              'help': 'Inputs for the `PwRelaxWorkChain`, if not specified at all, the relaxation step is skipped.'})
        for name, entry_point in entries.items():
            plugin_workchain = entry_point[0]
            spec.expose_inputs(
                plugin_workchain,
                namespace=name,
                namespace_options={
                    "required": False,
                    "populate_defaults": False,
                    "help": f"Inputs for the {name} plugin.",
                },
            )
            spec.exit_code(
                404 + 1,
                f"ERROR_SUB_PROCESS_FAILED_{name}",
                message=f"The plugin {name} WorkChain sub process failed",
            )
        spec.outline(
            cls.setup,
            if_(cls.should_run_relax)(
                cls.run_relax,
                cls.inspect_relax
            ),
            cls.run_plugin,
            cls.inspect_plugin,
            cls.results
        )
        spec.exit_code(401, 'ERROR_SUB_PROCESS_FAILED_RELAX',
                       message='The PwRelaxWorkChain sub process failed')
        spec.exit_code(403, 'ERROR_SUB_PROCESS_FAILED_BANDS',
                       message='The PwBandsWorkChain sub process failed')
        spec.exit_code(404, 'ERROR_SUB_PROCESS_FAILED_PDOS',
                       message='The PdosWorkChain sub process failed')
        spec.output('structure', valid_type=StructureData, required=False)
        # yapf: enable

    @classmethod
    def get_builder_from_protocol(
        cls,
        structure,
        parameters=None,
    ):
        """Return a builder prepopulated with inputs selected according to the chosen protocol."""
        builder = cls.get_builder()
        builder.structure = structure
        protocol = parameters["basic"].pop("protocol", "moderate")
        codes = parameters.pop("codes", {})
        #
        parameters["workflow"]["relax_type"] = RelaxType(
            parameters["workflow"]["relax_type"]
        )
        parameters["basic"]["electronic_type"] = ElectronicType(
            parameters["basic"]["electronic_type"]
        )
        parameters["basic"]["spin_type"] = SpinType(parameters["basic"]["spin_type"])
        # Relax
        if parameters["workflow"]["relax_type"] is not RelaxType.NONE:
            relax_parameters, relax_overrides = cls.get_relax_parameters(parameters)
            relax = PwRelaxWorkChain.get_builder_from_protocol(
                code=load_code(codes.get("pw_code", None)),
                structure=structure,
                protocol=protocol,
                overrides=relax_overrides,
                **relax_parameters,
            )
            relax.pop("structure", None)
            relax.pop("clean_workdir", None)
            relax.pop("base_final_scf", None)
            builder.relax = relax
        else:
            builder.pop("relax", None)
        # builder.clean_workdir = overrides.get("clean_workdir", Bool(False))
        # add plugin workchain
        for name, entry_point in entries.items():
            if parameters["workflow"]["properties"][name]:
                plugin_builder = entry_point[1](codes, structure, parameters)
                setattr(builder, name, plugin_builder)
            else:
                builder.pop(name, None)
        return builder

    def setup(self):
        """Perform the initial setup of the work chain."""
        self.ctx.current_structure = self.inputs.structure
        self.ctx.current_number_of_bands = None
        self.ctx.scf_parent_folder = None

    @classmethod
    def get_relax_parameters(cls, parameters):
        # developer should get the plugin parameters and override from the parameters
        new_parameters = parameters["basic"]
        pw = parameters["advance"].get("pw", {})
        pw["pseudo_family"] = parameters["advance"].get("pseudo_family", None)
        overrides = {
            "base": pw,
            "base_final_scf": pw,
        }

        return new_parameters, overrides

    def should_run_relax(self):
        """Check if the geometry of the input structure should be optimized."""
        return "relax" in self.inputs

    def run_relax(self):
        """Run the `PwRelaxWorkChain`."""
        inputs = AttributeDict(self.exposed_inputs(PwRelaxWorkChain, namespace="relax"))
        inputs.metadata.call_link_label = "relax"
        inputs.structure = self.ctx.current_structure

        inputs = prepare_process_inputs(PwRelaxWorkChain, inputs)
        running = self.submit(PwRelaxWorkChain, **inputs)

        self.report(f"launching PwRelaxWorkChain<{running.pk}>")

        return ToContext(workchain_relax=running)

    def inspect_relax(self):
        """Verify that the `PwRelaxWorkChain` finished successfully."""
        workchain = self.ctx.workchain_relax

        if not workchain.is_finished_ok:
            self.report(
                f"PwRelaxWorkChain failed with exit status {workchain.exit_status}"
            )
            return self.exit_codes.ERROR_SUB_PROCESS_FAILED_RELAX

        if "output_structure" in workchain.outputs:
            self.ctx.current_structure = workchain.outputs.output_structure
            self.ctx.current_number_of_bands = (
                workchain.outputs.output_parameters.get_attribute("number_of_bands")
            )
            self.out("structure", self.ctx.current_structure)

    def should_run_plugin(self, name):
        return name in self.inputs

    def run_plugin(self):
        """Run the `PdosWorkChain`."""
        self.ctx.plugin_entries = entries
        plugin_running = {}
        self.report(f"Plugins: {entries}")
        for name, entry_point in entries.items():
            if not self.should_run_plugin(name):
                continue
            self.report(f"Run plugin : {name}")
            plugin_workchain = entry_point[0]
            inputs = AttributeDict(
                self.exposed_inputs(plugin_workchain, namespace=name)
            )
            inputs.metadata.call_link_label = name
            inputs.structure = self.ctx.current_structure
            inputs = prepare_process_inputs(plugin_workchain, inputs)
            self.report(f"plugin inputs: {inputs}")
            running = self.submit(plugin_workchain, **inputs)
            self.report(f"launching plugin {name} <{running.pk}>")
            plugin_running[name] = running

        return ToContext(**plugin_running)

    def inspect_plugin(self):
        """Verify that the `pluginWorkChain` finished successfully."""
        self.report(f"Inspect plugins: {self.ctx.keys()}")
        for name in self.ctx.plugin_entries:
            if not self.should_run_plugin(name):
                continue
            workchain = self.ctx[name]
            if not workchain.is_finished_ok:
                self.report(
                    f"Plugin {name} WorkChain failed with exit status {workchain.exit_status}"
                )
                return self.exit_codes.get(f"ERROR_SUB_PROCESS_FAILED_{name}")

    def results(self):
        """Add the results to the outputs."""
        pass

    def on_terminated(self):
        """Clean the working directories of all child calculations if `clean_workdir=True` in the inputs."""
        super().on_terminated()

        if self.inputs.clean_workdir.value is False:
            self.report("remote folders will not be cleaned")
            return

        cleaned_calcs = []

        for called_descendant in self.node.called_descendants:
            if isinstance(called_descendant, CalcJobNode):
                try:
                    called_descendant.outputs.remote_folder._clean()  # pylint: disable=protected-access
                    cleaned_calcs.append(called_descendant.pk)
                except (OSError, KeyError):
                    pass

        if cleaned_calcs:
            self.report(
                f"cleaned remote folders of calculations: {' '.join(map(str, cleaned_calcs))}"
            )


__version__ = "23.4.1"
