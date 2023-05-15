from aiidalab_qe.bands.result import Result
from aiidalab_qe.bands.setting import Setting
from aiidalab_qe.bands.workchain import workchain_and_builder
from aiidalab_qe.panel import OutlinePanel


class BandsOutline(OutlinePanel):
    title = "Electronic band structure"
    help = """The band structure workflow will
automatically detect the default path in reciprocal space using the
<a href="https://www.materialscloud.org/work/tools/seekpath" target="_blank">
SeeK-path tool</a>.
"""


property = {
    "outline": BandsOutline,
    "setting": Setting,
    "result": Result,
    "workchain": workchain_and_builder,
}
