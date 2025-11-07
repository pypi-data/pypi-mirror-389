import aidge_core
from aidge_core.export_utils import ExportNodeCpp
from aidge_export_cpp import ROOT
from aidge_export_cpp import ExportLibCpp
import numpy as np

# Consumer-Producer model to allow memory wrapping for Pad in-place operator
class PadInPlace_CP(aidge_core.ProdConso):
    def __init__(self, op: aidge_core.Operator):
        aidge_core.ProdConso.__init__(self, op, False)

    def default_model(op: aidge_core.Operator):
        return PadInPlace_CP(op)

    def get_nb_required_protected(self, input_idx):
        if input_idx != 0:
            return super().get_nb_required_protected(input_idx)

        pad_op = self.get_operator()
        input = pad_op.get_input(0)
        if input:
            output = pad_op.get_output(0)
            return aidge_core.Elts_t.data_elts(max(0, output.size - input.size))
        else:
            return aidge_core.Elts_t.none_elts()


@ExportLibCpp.register("Pad",
    aidge_core.ImplSpec(aidge_core.IOSpec(aidge_core.dtype.any)),
    PadInPlace_CP.default_model)
class CppPad(ExportNodeCpp):
    def __init__(self, node, mem_info):
        super().__init__(node, mem_info)

        # Initialize kernel attributes
        self.attributes["padding"] = node.get_operator().attr.pads
        self.attributes["mode"] = node.get_operator().attr.mode
        self.attributes["constant_value"] = np.array(
            node.get_operator().attr.constant_value
        ).item()

        assert (
            self.attributes["mode"] == aidge_core.PaddingMode.CONSTANT
        ), f"export Pad: mode == {node.get_operator().attr.mode} not implemented"

        # Template for layer configutation file generation
        self.config_template = str(ROOT / "templates" / "configuration" / "pad_config.jinja")

        # Template layer call function generation within the forward file
        self.forward_template = str(ROOT / "templates" / "kernel_forward" / "pad_forward.jinja")

        # Files to include within the generated forward.cpp file
        self.include_list = []

        # Path to the kernel(s) files to copy
        self.add_kernel_to_copy(ROOT / "kernels" / "pad.hpp", "include/kernels/cpp")

        # Include aidge outputs within the fwd file
        if self.attributes["aidge_cmp"]:
            self.include_list.append("utils/cpp/utils.hpp")   # aidge_cmp function
            self.include_list.append("data/aidge_outputs/" + node.name() + ".hpp")
