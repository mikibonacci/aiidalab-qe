from aiidalab_qe.panel import PropertyPanel


class BandsProperty(PropertyPanel):
    title = "Electronic band structure"
    help = """The band structure workflow will
automatically detect the default path in reciprocal space using the
<a href="https://www.materialscloud.org/work/tools/seekpath" target="_blank">
SeeK-path tool</a>.
"""
