import aidge_core
from aidge_core.export_utils import ExportNodeCpp
from aidge_export_cpp import ROOT
from aidge_export_cpp import ExportLibCpp

@ExportLibCpp.register("Transpose", aidge_core.ImplSpec(aidge_core.IOSpec(aidge_core.dtype.any)))
class TransposeCPP(ExportNodeCpp):
    def __init__(self, node, mem_info):
        super().__init__(node, mem_info)

        nbdims = len(self.attributes["in_dims"][0])

        # Compute input strides
        in_strides = [0] * nbdims
        in_strides[nbdims - 1] = 1
        for i in range(nbdims - 2, -1, -1):
            in_strides[i] = in_strides[i + 1] * self.attributes["in_dims"][0][i + 1]

        # Compute output dimensions based on permutation
        out_dims = [self.attributes["in_dims"][0][self.attributes["output_dims_order"][i]] for i in range(nbdims)]

        # Compute output strides
        out_strides = [0] * nbdims
        out_strides[nbdims - 1] = 1
        for i in range(nbdims - 2, -1, -1):
            out_strides[i] = out_strides[i + 1] * out_dims[i + 1]

        self.attributes["in_strides"] = in_strides
        self.attributes["out_strides"] = out_strides

        self.config_template = str(ROOT / "templates" / "configuration" / "transpose_ND_config.jinja")
        self.forward_template = str(ROOT / "templates" / "kernel_forward" / "transpose_ND_forward.jinja")
        self.include_list = []
        self.add_kernel_to_copy(ROOT / "kernels" / "transpose.hpp", "include/kernels/cpp")

        # Include aidge outputs within the fwd file
        if self.attributes["aidge_cmp"]:
            self.include_list.append("utils/cpp/utils.hpp")   # aidge_cmp function
            self.include_list.append("data/aidge_outputs/" + node.name() + ".hpp")
