import aidge_core
from aidge_core.export_utils import ExportNodeCpp
from aidge_export_cpp import ROOT
from aidge_export_cpp import ExportLibCpp

@ExportLibCpp.register("MatMul", aidge_core.ImplSpec(aidge_core.IOSpec(aidge_core.dtype.float32)))
class MatMulCPP(ExportNodeCpp):
    def __init__(self, node, mem_info):
        super().__init__(node, mem_info)
        self.attributes["activation"] = "Linear"
        self.attributes["rescaling"] = "NoScaling"

        # Initialize arrays storing broadcasted(or not) dims
        nbdims_out = len(self.attributes["out_dims"][0])
        dims_a = self.attributes["in_dims"][0]
        dims_b = self.attributes["in_dims"][1]
        ndim_a = [0] * nbdims_out
        ndim_b = [0] * nbdims_out

        if len(dims_a) == 1:
            ndim_a[0] = 1
            ndim_a[1] = dims_a[0]

        if len(dims_b) == 1:
            ndim_b[0] = 1
            ndim_b[1] = dims_b[0]

        idx_a = nbdims_out - len(dims_a)
        for i in range(nbdims_out):
            ndim_a[i] = 1 if i < idx_a else dims_a[i - idx_a]

        idx_b = nbdims_out - len(dims_b)
        for i in range(nbdims_out):
            ndim_b[i] = 1 if i < idx_b else dims_b[i - idx_b]

        # Initialize strides for broadcasting
        stride_post0 = [0] * (nbdims_out - 2)
        stride_post1 = [0] * (nbdims_out - 2)
        stride_step0 = [0] * (nbdims_out - 2)
        stride_step1 = [0] * (nbdims_out - 2)

        if nbdims_out > 2:
            stride_post0[nbdims_out - 3] = 1
            stride_post1[nbdims_out - 3] = 1
            for i in range(nbdims_out - 4, -1, -1):
                stride_post0[i] = stride_post0[i + 1] * ndim_a[i + 1]
                stride_post1[i] = stride_post1[i + 1] * ndim_b[i + 1]

            for i in range(nbdims_out - 2):
                stride_step0[i] = 1 - stride_post0[i] if ndim_a[i] == 1 else 1
                stride_step1[i] = 1 - stride_post1[i] if ndim_b[i] == 1 else 1

        # if len(dims_b) == len(dims_a), then len(dims_a) == nbdims_out == len(dims_b); 
        # else it will be broadcasted to the correct dims
        nbMatrices = 1
        for i in range(nbdims_out - 3, -1, -1):
            nbMatrices *= self.attributes["out_dims"][0][i]

        offsetIn0 = 0
        offsetIn1 = 0
        self.attributes["offset_in1"] = [0]
        self.attributes["offset_in2"] = [0]

        for stack in range(1, nbMatrices):
            dim = nbdims_out - 3
            tmp_stack = stack
            while tmp_stack % self.attributes["out_dims"][0][dim] == 0:
                tmp_stack //= self.attributes["out_dims"][0][dim]
                dim -= 1
            offsetIn0 += stride_step0[dim]
            offsetIn1 += stride_step1[dim]

            self.attributes["offset_in1"].append(offsetIn0)
            self.attributes["offset_in2"].append(offsetIn1)

        self.attributes["n"] = ndim_a[nbdims_out - 2]
        self.attributes["m"] = ndim_b[nbdims_out - 1]
        self.attributes["k"] = ndim_a[nbdims_out - 1]

        self.config_template = str(ROOT / "templates" / "configuration" / "matmul_config.jinja")
        self.forward_template = str(ROOT / "templates" / "kernel_forward" / "matmul_forward.jinja")
        self.include_list = []
        self.add_kernel_to_copy(ROOT / "kernels" / "matmul.hpp", "include/kernels/cpp")

        # Include aidge outputs within the fwd file
        if self.attributes["aidge_cmp"]:
            self.include_list.append("utils/cpp/utils.hpp")   # aidge_cmp function
            self.include_list.append("data/aidge_outputs/" + node.name() + ".hpp") 
