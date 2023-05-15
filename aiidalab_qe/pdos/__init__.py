from aiidalab_qe.panel import OutlinePanel
from aiidalab_qe.pdos.result import Result
from aiidalab_qe.pdos.setting import Setting
from aiidalab_qe.pdos.workchain import workchain_and_builder


class PDOSOutline(OutlinePanel):
    title = "Projected density of states (PDOS)"


property = {
    "outline": PDOSOutline,
    "setting": Setting,
    "result": Result,
    "workchain": workchain_and_builder,
}
