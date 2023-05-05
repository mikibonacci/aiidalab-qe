# AiiDA imports.
from aiida.common import AttributeDict
from aiida.engine import ToContext, WorkChain, if_
from aiida.orm import CalcJobNode, WorkChainNode, load_code
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
def get_entries(entry_point_name="aiidalab_qe_configuration"):
    from importlib.metadata import entry_points

    entries = {}
    for entry_point in entry_points().get(entry_point_name, []):
        entries[entry_point.name] = entry_point.load()

    return entries


class QeAppWorkChain(WorkChain):
    """WorkChain designed to calculate the requested properties in the AiiDAlab Quantum ESPRESSO app."""

    @classmethod
    def define(cls, spec):
        """Define the process specification."""
        entries = get_entries("aiidalab_qe_subworkchain")
        for name, entry_point in entries.items():
            plugin_workchain = entry_point
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

        # yapf: disable
        super().define(spec)
        spec.input('structure', valid_type=StructureData,
                   help='The inputs structure.')
        spec.input('clean_workdir', valid_type=Bool, default=lambda: Bool(False),
                   help='If `True`, work directories of all called calculation will be cleaned at the end of execution.')
        spec.expose_inputs(PwRelaxWorkChain, namespace='relax', exclude=('clean_workdir', 'structure'),
                           namespace_options={'required': False, 'populate_defaults': False,
                                              'help': 'Inputs for the `PwRelaxWorkChain`, if not specified at all, the relaxation step is skipped.'})
        spec.expose_inputs(PwBandsWorkChain, namespace='bands',
                           exclude=('clean_workdir', 'structure', 'relax'),
                           namespace_options={'required': False, 'populate_defaults': False,
                                              'help': 'Inputs for the `PwBandsWorkChain`.'})
        spec.expose_inputs(PdosWorkChain, namespace='pdos',
                           exclude=('clean_workdir', 'structure'),
                           namespace_options={'required': False, 'populate_defaults': False,
                                              'help': 'Inputs for the `PdosWorkChain`.'})
        spec.input(
            'kpoints_distance_override', valid_type=Float, required=False,
            help='Override for the kpoints distance value of all `PwBaseWorkChains` except for the `nscf` calculations.'
        )
        spec.input(
            'degauss_override', valid_type=Float, required=False,
            help='Override for the `degauss` value of all `PwBaseWorkChains` except for the `nscf` calculations.'
        )
        spec.input(
            'smearing_override', valid_type=Str, required=False,
            help='Override for the `smearing` value of all `PwBaseWorkChains` save for the `nscf` calculations.'
        )
        spec.outline(
            cls.setup,
            if_(cls.should_run_relax)(
                cls.run_relax,
                cls.inspect_relax
            ),
            if_(cls.should_run_bands)(
                cls.run_bands,
                cls.inspect_bands
            ),
            if_(cls.should_run_pdos)(
                cls.run_pdos,
                cls.inspect_pdos
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
        spec.output('band_parameters', valid_type=Dict, required=False)
        spec.output('band_structure', valid_type=BandsData, required=False)
        spec.output('nscf_parameters', valid_type=Dict, required=False)
        spec.output('dos', valid_type=XyData, required=False)
        spec.output('projections', valid_type=Orbital, required=False)
        spec.output('projections_up', valid_type=Orbital, required=False)
        spec.output('projections_down', valid_type=Orbital, required=False)
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
        # Bands
        if parameters["workflow"]["properties"]["bands"]:
            bands_parameters, bands_overrides = cls.get_bands_parameters(parameters)
            bands = PwBandsWorkChain.get_builder_from_protocol(
                code=load_code(codes.get("pw_code", None)),
                structure=structure,
                protocol=protocol,
                overrides=bands_overrides,
                **bands_parameters,
            )
            bands.pop("relax")
            bands.pop("structure", None)
            bands.pop("clean_workdir", None)
            builder.bands = bands
        else:
            builder.pop("bands", None)
        # PDOS
        if parameters["workflow"]["properties"]["pdos"]:
            pdos_parameters, pdos_overrides = cls.get_pdos_parameters(parameters)
            pdos = PdosWorkChain.get_builder_from_protocol(
                pw_code=load_code(codes.get("pw_code", None)),
                dos_code=load_code(codes.get("dos_code", None)),
                projwfc_code=load_code(codes.get("projwfc_code", None)),
                structure=structure,
                protocol=protocol,
                overrides=pdos_overrides,
                **pdos_parameters,
            )
            pdos.pop("structure", None)
            pdos.pop("clean_workdir", None)
            builder.pdos = pdos
        else:
            builder.pop("pdos", None)

        # builder.clean_workdir = overrides.get("clean_workdir", Bool(False))
        # add plugin workchain
        entries = get_entries("aiidalab_qe_subworkchain")
        for name, entry_point in entries.items():
            if parameters["workflow"]["properties"][name]:
                workchain = entry_point
                plugin = workchain.get_builder_from_protocol(
                    codes=codes,
                    structure=structure,
                    parameters=parameters,
                )
                setattr(builder, name, plugin)
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

    @classmethod
    def get_bands_parameters(cls, parameters):
        # developer should get the plugin parameters and override from the parameters
        new_parameters = parameters["basic"]
        pw = parameters["advance"].get("pw", {})
        pw["pseudo_family"] = parameters["advance"].get("pseudo_family", None)
        overrides = {
            "scf": pw,
            "bands": pw,
        }

        return new_parameters, overrides

    @classmethod
    def get_pdos_parameters(cls, parameters):
        # developer should get the plugin parameters and override from the parameters
        new_parameters = parameters["basic"]
        pw = parameters["advance"].get("pw", {})
        pw["pseudo_family"] = parameters["advance"].get("pseudo_family", None)
        overrides = {
            "scf": pw,
            "bands": pw,
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

    def should_run_bands(self):
        """Check if the band structure should be calculated."""
        return "bands" in self.inputs

    def run_bands(self):
        """Run the `PwBandsWorkChain`."""
        inputs = AttributeDict(self.exposed_inputs(PwBandsWorkChain, namespace="bands"))
        inputs.metadata.call_link_label = "bands"
        inputs.structure = self.ctx.current_structure
        inputs.scf.pw.parameters = inputs.scf.pw.parameters.get_dict()

        if self.ctx.current_number_of_bands:
            inputs.scf.pw.parameters.setdefault("SYSTEM", {}).setdefault(
                "nbnd", self.ctx.current_number_of_bands
            )

        inputs = prepare_process_inputs(PwBandsWorkChain, inputs)
        running = self.submit(PwBandsWorkChain, **inputs)

        self.report(f"launching PwBandsWorkChain<{running.pk}>")

        return ToContext(workchain_bands=running)

    def inspect_bands(self):
        """Verify that the `PwBandsWorkChain` finished successfully."""
        workchain = self.ctx.workchain_bands

        if not workchain.is_finished_ok:
            self.report(
                f"PwBandsWorkChain failed with exit status {workchain.exit_status}"
            )
            return self.exit_codes.ERROR_SUB_PROCESS_FAILED_BANDS

        scf = workchain.get_outgoing(WorkChainNode, link_label_filter="scf").one().node
        self.ctx.scf_parent_folder = scf.outputs.remote_folder
        self.ctx.current_structure = workchain.outputs.primitive_structure

    def should_run_pdos(self):
        """Check if the projected density of states should be calculated."""
        return "pdos" in self.inputs

    def run_pdos(self):
        """Run the `PdosWorkChain`."""
        inputs = AttributeDict(self.exposed_inputs(PdosWorkChain, namespace="pdos"))
        inputs.metadata.call_link_label = "pdos"
        inputs.structure = self.ctx.current_structure
        inputs.nscf.pw.parameters = inputs.nscf.pw.parameters.get_dict()

        if self.ctx.current_number_of_bands:
            inputs.nscf.pw.parameters.setdefault("SYSTEM", {}).setdefault(
                "nbnd", self.ctx.current_number_of_bands
            )

        if self.ctx.scf_parent_folder:
            inputs.pop("scf")
            inputs.nscf.pw.parent_folder = self.ctx.scf_parent_folder

        inputs = prepare_process_inputs(PdosWorkChain, inputs)
        running = self.submit(PdosWorkChain, **inputs)

        self.report(f"launching PdosWorkChain<{running.pk}>")

        return ToContext(workchain_pdos=running)

    def inspect_pdos(self):
        """Verify that the `PdosWorkChain` finished successfully."""
        workchain = self.ctx.workchain_pdos

        if not workchain.is_finished_ok:
            self.report(
                f"PdosWorkChain failed with exit status {workchain.exit_status}"
            )
            return self.exit_codes.ERROR_SUB_PROCESS_FAILED_PDOS

    def should_run_plugin(self, name):
        return name in self.inputs

    def run_plugin(self):
        """Run the `PdosWorkChain`."""
        entries = get_entries("aiidalab_qe_subworkchain")
        self.ctx.plugin_entries = entries
        plugin_running = {}
        self.report(f"Plugins: {entries}")
        for name, entry_point in entries.items():
            if not self.should_run_plugin(name):
                continue
            self.report(f"Run plugin : {name}")
            plugin_workchain = entry_point
            inputs = AttributeDict(
                self.exposed_inputs(plugin_workchain, namespace=name)
            )
            inputs.metadata.call_link_label = name
            inputs.structure = self.ctx.current_structure
            inputs = prepare_process_inputs(plugin_workchain, inputs)
            self.report(f"plugin inputs: {inputs}")
            running = self.submit(plugin_workchain, **inputs)
            self.report(f"launching plugin {name} <{running.pk}>")
            plugin_running = {name: running}

        return ToContext(**plugin_running)

    def inspect_plugin(self):
        """Verify that the `pluginWorkChain` finished successfully."""
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
        if "workchain_bands" in self.ctx:
            self.out(
                "band_parameters", self.ctx.workchain_bands.outputs.band_parameters
            )
            self.out("band_structure", self.ctx.workchain_bands.outputs.band_structure)

        if "workchain_pdos" in self.ctx:
            self.out(
                "nscf_parameters",
                self.ctx.workchain_pdos.outputs.nscf.output_parameters,
            )
            self.out("dos", self.ctx.workchain_pdos.outputs.dos.output_dos)
            if "projections_up" in self.ctx.workchain_pdos.outputs.projwfc:
                self.out(
                    "projections_up",
                    self.ctx.workchain_pdos.outputs.projwfc.projections_up,
                )
                self.out(
                    "projections_down",
                    self.ctx.workchain_pdos.outputs.projwfc.projections_down,
                )
            else:
                self.out(
                    "projections", self.ctx.workchain_pdos.outputs.projwfc.projections
                )

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
