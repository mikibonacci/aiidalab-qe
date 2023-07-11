"""Implementation of the MultiplyAddWorkChain for testing and demonstration purposes."""
from aiida.common import AttributeDict
from aiida.engine import ToContext, WorkChain, calcfunction
from aiida.orm import AbstractCode, Int, Float, Dict, Code, StructureData, load_code
from aiida.plugins import WorkflowFactory
from aiida_quantumespresso.utils.mapping import prepare_process_inputs


PwBaseWorkChain = WorkflowFactory('quantumespresso.pw.base')


class EOSWorkChain(WorkChain):
    """WorkChain to calcalculate the equation of state of a crystal."""
    label = "eos"

    @classmethod
    def define(cls, spec):
        """Specify inputs and outputs."""
        super().define(spec)
        spec.expose_inputs(
            PwBaseWorkChain,
            namespace='scf',
            exclude=('clean_workdir', 'pw.structure', 'pw.parent_folder'),
            namespace_options={
                'required': False,
                'populate_defaults': False,
                'help': 'Inputs for the `PwBaseWorkChain` of the `scf` calculation.',
            }
        )
        spec.input('structure', valid_type=StructureData)
        spec.input('scale', valid_type=Float)
        spec.input('npoint', valid_type=Int)
        spec.outline(
            cls.run_eos,
            cls.result,
        )
        spec.output('eos', valid_type=Dict)
        spec.exit_code(400, 'ERROR_NEGATIVE_NUMBER', message='The result is a negative number.')

    @classmethod
    def get_builder_from_protocol(
        cls,
        pw_code=None,
        structure=None,
        protocol="fast",
        overrides=None,
        parameters=None,
    ):
        builder = cls.get_builder()
        builder.structure = structure
        # scf
        args = (pw_code, structure, protocol)
        scf = PwBaseWorkChain.get_builder_from_protocol(
            *args,
            overrides=overrides,
            **parameters,
        )
        builder.scf = scf
        builder.scale = parameters["eos"]["scale"]
        builder.npoint = parameters["eos"]["npoint"]
        return builder

    def run_eos(self):
        """Run all scf calculations."""
        import numpy as np
        factors = np.linspace(1-self.inputs.scale.value, 1+self.inputs.scale.value, self.inputs.npoint.value)
        labels = []
        futures = {}
        structure = self.inputs.structure
        for i, factor in enumerate(factors):
            label = f"s_{i}"
            atoms = structure.get_ase()
            atoms.set_cell(atoms.get_cell()*factor, scale_atoms = True)
            scaled_structure = StructureData(ase=atoms)
            inputs = AttributeDict(self.exposed_inputs(PwBaseWorkChain, namespace="scf"))
            inputs.metadata.call_link_label = "pw"
            inputs.pw.structure = scaled_structure
            inputs.pw.parameters = inputs.pw.parameters.get_dict()
            inputs = prepare_process_inputs(PwBaseWorkChain, inputs)
            running = self.submit(PwBaseWorkChain, **inputs)
            futures[label] = running
            labels.append(label)
            self.report(f"Running an SCF calculation with scale factor {factor}")
        self.ctx.labels = labels
        return ToContext(**futures)


    def result(self):
        """Add the result to the outputs."""
        from ase.eos import EquationOfState
        volumes = []
        energies = []
        self.report(f"keys: {self.ctx.keys()}")
        for label in self.ctx.labels:
            result = self.ctx[label].outputs.output_parameters
            volumes.append(result.dict.volume)
            energies.append(result.dict.energy)
            unit = result.dict.energy_units
        #
        eos = EquationOfState(volumes, energies)
        v0, e0, B = eos.fit()
        eos = Dict({"volumes": volumes, "energies": energies,
                    "unit": unit,
                    "v0": v0,
                    "e0": e0,
                    "B": B,
        })
        eos.store()
        self.out("eos", eos)


def get_builder(codes, structure, parameters):
    protocol = parameters["basic"].pop('protocol', "fast")
    pw_code = load_code(codes.get('pw_code'))
    overrides = {
        "pw": parameters["advance"],
    }
    builder = EOSWorkChain.get_builder_from_protocol(
                pw_code=pw_code,
                structure=structure,
                protocol=protocol,
                overrides=overrides,
                parameters=parameters,
            )
    return builder

workchain_and_builder = [EOSWorkChain, get_builder]
