import aidge_core
from aidge_core.export_utils import ExportNodeCpp
from aidge_export_cpp import ROOT
from aidge_export_cpp import ExportLibCpp

@ExportLibCpp.register("Softmax", aidge_core.ImplSpec(aidge_core.IOSpec(aidge_core.dtype.float32)))
class Softmax(ExportNodeCpp):
    def __init__(self, node, mem_info):
        super().__init__(node, mem_info)

        assert self.node.get_nb_inputs() == 1, (
            f"export softmax: nb_inputs == {self.node.get_nb_inputs()} not implemented"
        )

        tensor = self.operator.get_input(0)
        nbDims = len(tensor.dims)
        axis = node.get_operator().attr.axis if node.get_operator().attr.axis >= 0 else node.get_operator().attr.axis + nbDims

        assert axis < nbDims, (
            f"export softmax: attribute axis == {node.get_operator().attr.axis} should be less than {nbDims}"
        )

        postAxisElems = 1
        for i in range(axis + 1, nbDims):
            postAxisElems *= tensor.dims[i]

        preAxisElems = 1
        for i in range(axis):
            preAxisElems *= tensor.dims[i]

        # Set kernel attributes
        self.attributes["axis_size"] = tensor.dims[axis]
        self.attributes["axis_size_post"] = postAxisElems
        self.attributes["axis_size_pre"] = preAxisElems

        # Template for layer configutation file generation
        self.config_template = str(ROOT / "templates" / "configuration" / "softmax_config.jinja")

        # Template layer call function generation within the forward file
        self.forward_template = str(ROOT / "templates" / "kernel_forward" / "softmax_forward.jinja")

        # Files to include within the generated forward.cpp file
        self.include_list = []

        # Path to the kernel(s) files to copy
        self.add_kernel_to_copy(ROOT / "kernels" / "softmax.hpp", "include/kernels/cpp")

        # Include aidge outputs within the fwd file
        if self.attributes["aidge_cmp"]:
            self.include_list.append("utils/cpp/utils.hpp")   # aidge_cmp function
            self.include_list.append("data/aidge_outputs/" + node.name() + ".hpp")