import aidge_core
from aidge_core.export_utils import ExportNodeCpp, get_node_from_metaop
from aidge_export_cpp import ROOT, ExportLibCpp, set_scaling_attributes

@ExportLibCpp.register("Sigmoid",
    aidge_core.ImplSpec(aidge_core.IOSpec(aidge_core.dtype.any)),
    aidge_core.ProdConso.in_place_model)
class SigmoidCPP(ExportNodeCpp):
    def __init__(self, node, mem_info):
        super().__init__(node, mem_info)
        self.attributes["activation"] = "Linear"
        self.attributes["rescaling"] = "NoScaling"

        self.config_template = str(ROOT / "templates" / "configuration" / "sigmoid_config.jinja")
        self.forward_template = str(ROOT / "templates" / "kernel_forward" / "sigmoid_forward.jinja")
        self.include_list = []
        self.add_kernel_to_copy(ROOT / "kernels" / "sigmoid.hpp", "include/kernels/cpp")

        # Include aidge outputs within the fwd file
        if self.attributes["aidge_cmp"]:
            self.include_list.append("utils/cpp/utils.hpp")   # aidge_cmp function
            self.include_list.append("data/aidge_outputs/" + node.name() + ".hpp")
