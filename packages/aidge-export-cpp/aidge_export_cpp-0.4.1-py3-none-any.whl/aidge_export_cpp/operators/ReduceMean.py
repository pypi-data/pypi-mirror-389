import aidge_core
from aidge_core.export_utils import ExportNodeCpp
from aidge_export_cpp import ROOT, ExportLibCpp, set_scaling_attributes

@ExportLibCpp.register("ReduceMean", aidge_core.ImplSpec(aidge_core.IOSpec(aidge_core.dtype.float32)))
class ReducemeanCPP(ExportNodeCpp):
    def __init__(self, node, mem_info):
        super().__init__(node, mem_info)

        if self.operator.get_input(0) is None:
            raise AttributeError("Input 0 not found for operator ReduceMean")

        input_T = self.operator.get_input(0)

        # COMPUTING PRE/POST AXES STRIDES:
        # Example :
        # input dims {3, 3, 2}
        # stride_pre = {1,3,9}
        # stride_post = {6, 2, 1}
        post_axis_strides = input_T.strides

        pre_axis_strides = [1]
        for i in range(1, len(post_axis_strides)):
            pre_axis_strides.append(pre_axis_strides[i - 1] * input_T.dims[i - 1])

        in_nb_elts = input_T.dims[0] * input_T.strides[0]
        out_nb_elts = in_nb_elts
        axes_to_reduce = self.node.get_operator().attr.axes
        for i in axes_to_reduce:
            out_nb_elts = out_nb_elts // input_T.dims[i]

        self.attributes["in_dims"] = input_T.dims
        self.attributes["in_nb_dims"] = len(input_T.dims)
        self.attributes["in_nb_elts"] = in_nb_elts
        self.attributes["out_nb_elts"] = out_nb_elts
        self.attributes["nb_axes_to_reduce"] = len(self.operator.attr.axes)
        self.attributes["axes_to_reduce"] = self.node.get_operator().attr.axes
        self.attributes["pre_axis_strides"] = pre_axis_strides
        self.attributes["post_axis_strides"] = post_axis_strides

        # axis = node.get_operator().attr.axis if node.get_operator().attr.axis >= 0 else node.get_operator().attr.axis + nbDims

        self.config_template = str(ROOT / "templates" / "configuration" / "reducemean_config.jinja")
        self.forward_template = str(ROOT / "templates" / "kernel_forward" / "reducemean_forward.jinja")
        self.include_list = []
        self.add_kernel_to_copy(ROOT / "kernels" / "reducemean.hpp", "include/kernels/cpp")

        # Include aidge outputs within the fwd file
        if self.attributes["aidge_cmp"]:
            self.include_list.append("utils/cpp/utils.hpp")   # aidge_cmp function
            self.include_list.append("data/aidge_outputs/" + node.name() + ".hpp")
