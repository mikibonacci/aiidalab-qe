from aiidalab_qe.panel import OutlinePanel
from aiidalab_qe.xps.result import Result
from aiidalab_qe.xps.setting import Setting
from aiidalab_qe.xps.workchain import workchain_and_builder


class XPSOutline(OutlinePanel):
    title = "X-ray photoelectron spectroscopy (XPS)"
    help = """"""


property = {
    "outline": XPSOutline,
    "setting": Setting,
    "result": Result,
    "workchain": workchain_and_builder,
}
