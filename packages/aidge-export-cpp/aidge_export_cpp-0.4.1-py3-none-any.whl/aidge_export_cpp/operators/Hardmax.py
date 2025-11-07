import aidge_core
from aidge_core.export_utils import ExportNodeCpp
from aidge_export_cpp import ROOT, ExportLibCpp

@ExportLibCpp.register("Hardmax", aidge_core.ImplSpec(aidge_core.IOSpec(aidge_core.dtype.float32)))
class HardmaxCPP(ExportNodeCpp):
    def __init__(self, node, mem_info):
        super().__init__(node, mem_info)
        assert self.node.get_nb_inputs() == 1, (
            f"export hardmax: nb_inputs == {self.node.get_nb_inputs()} not implemented"
        )

        tensor = self.operator.get_input(0)
        nbDims = len(tensor.dims)
        axis = node.get_operator().attr.axis if node.get_operator().attr.axis >= 0 else node.get_operator().attr.axis + nbDims

        assert axis >= -nbDims and axis < nbDims, (
            f"export hardmax: attribute axis == {node.get_operator().attr.axis} should be comprised within [-{nbDims},{nbDims}]."
        )

        post_axis_elems = 1
        for i in range(axis + 1, nbDims):
            post_axis_elems *= tensor.dims[i]

        preaxis_elems = 1
        for i in range(axis):
            preaxis_elems *= tensor.dims[i]

        axis_elems = post_axis_elems * tensor.dims[axis]
        nb_elems = preaxis_elems * axis_elems

        self.attributes["axis_dim_size"] = tensor.dims[axis]
        self.attributes["preaxis_stride"] = preaxis_elems
        self.attributes["axis_stride"] = axis_elems
        self.attributes["postaxis_stride"] = post_axis_elems
        self.attributes["out_nb_elts"] = nb_elems

        self.config_template = str(
            ROOT / "templates" / "configuration" / "hardmax_config.jinja")
        self.forward_template = str(
            ROOT / "templates" / "kernel_forward" / "hardmax_forward.jinja")
        self.include_list = []
        self.add_kernel_to_copy(ROOT / "kernels" / "hardmax.hpp", "include/kernels/cpp")
