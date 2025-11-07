import aidge_core
from aidge_core.export_utils import ExportNodeCpp
from aidge_export_cpp import ROOT
from aidge_export_cpp import ExportLibCpp

@ExportLibCpp.register("Sqrt",
    aidge_core.ImplSpec(aidge_core.IOSpec(aidge_core.dtype.float32)),
    aidge_core.ProdConso.in_place_model)
class SqrtCPP(ExportNodeCpp):
    def __init__(self, node, mem_info):
        super().__init__(node, mem_info)
        self.config_template = str(ROOT / "templates" / "configuration" / "sqrt_config.jinja")
        self.forward_template = str(ROOT / "templates" / "kernel_forward" / "sqrt_forward.jinja")
        self.include_list = []
        self.add_kernel_to_copy(ROOT / "kernels" / "sqrt.hpp", "include/kernels/cpp")

        # Include aidge outputs within the fwd file
        if self.attributes["aidge_cmp"]:
            self.include_list.append("utils/cpp/utils.hpp")   # aidge_cmp function
            self.include_list.append("data/aidge_outputs/" + node.name() + ".hpp")
