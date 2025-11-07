import aidge_core
from aidge_core.export_utils import ExportNodeCpp
from aidge_export_cpp import ROOT
from aidge_export_cpp import ExportLibCpp

@ExportLibCpp.register("Reshape",
    # Reshape cannot accept any format, because its output format does not necessarily
    # match its input format. So, if the previous layer is changed from NCHW to NHWC
    # by adapt_to_backend(), it won't propagate the new format, ultimately leading
    # to a missing transpose for the next layer!
    aidge_core.ImplSpec(aidge_core.IOSpec(aidge_core.dtype.any, aidge_core.dformat.default)),
    aidge_core.ProdConso.in_place_model)
class ReshapeCPP(ExportNodeCpp):
    def __init__(self, node, mem_info):
        super().__init__(node, mem_info)

        self.config_template = str(
            ROOT / "templates" / "configuration" / "identity_config.jinja")
        self.forward_template = str(
            ROOT / "templates" / "kernel_forward" / "identity_forward.jinja")
        self.include_list = []
        self.add_kernel_to_copy(ROOT / "kernels" / "identity.hpp", "include/kernels/cpp")

        # Include aidge outputs within the fwd file
        if self.attributes["aidge_cmp"]:
            self.include_list.append("utils/cpp/utils.hpp")   # aidge_cmp function
            self.include_list.append("data/aidge_outputs/" + node.name() + ".hpp") 
