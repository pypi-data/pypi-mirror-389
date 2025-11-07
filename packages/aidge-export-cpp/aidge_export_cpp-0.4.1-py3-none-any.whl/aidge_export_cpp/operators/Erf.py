import aidge_core
from aidge_core.export_utils import ExportNodeCpp, get_node_from_metaop
from aidge_export_cpp import ROOT, ExportLibCpp, set_scaling_attributes

@ExportLibCpp.register("Erf",
    aidge_core.ImplSpec(aidge_core.IOSpec(aidge_core.dtype.float32)),
    aidge_core.ProdConso.in_place_model)
class ErfCPP(ExportNodeCpp):
    def __init__(self, node, mem_info):
        super().__init__(node, mem_info)
        self.attributes["activation"] = "Linear"
        self.attributes["rescaling"] = "NoScaling"

        self.config_template = str(
            ROOT / "templates" / "configuration" / "erf_config.jinja")
        self.forward_template = str(
            ROOT / "templates" / "kernel_forward" / "erf_forward.jinja")
        self.include_list = []
        self.add_kernel_to_copy(ROOT / "kernels" / "erf.hpp", "include/kernels/cpp")
        self.add_kernel_to_copy(ROOT / "kernels" / "activation.hpp", "include/utils/cpp", fwd_include=False)