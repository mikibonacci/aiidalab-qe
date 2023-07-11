from aiidalab_qe.eos.setting import Setting
from aiidalab_qe.eos.workchain import workchain_and_builder
from aiidalab_qe.eos.result import Result
from aiidalab_qe.panel import OutlinePanel


class Outline(OutlinePanel):
    title = "Equation of State (EOS)"


property ={
"outline": Outline,
"setting": Setting,
"result": Result,
"workchain": workchain_and_builder,
}
