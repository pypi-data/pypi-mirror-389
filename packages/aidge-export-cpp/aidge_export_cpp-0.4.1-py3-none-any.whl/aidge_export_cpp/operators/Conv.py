import aidge_core
from aidge_core.export_utils import ExportNodeCpp, get_node_from_metaop, get_chan, get_width, get_height
from aidge_export_cpp import ROOT, ExportLibCpp, set_scaling_attributes

# Consumer-Producer model to allow memory wrapping for Conv/PaddedConv
# (and Pool/PaddedPool), keeping one input line margin in NHWC data format
# (one input line = W*C)
class PaddedInPlace_CP(aidge_core.ProdConso):
    def __init__(self, op: aidge_core.Operator):
        aidge_core.ProdConso.__init__(self, op, False)

    def default_model(op: aidge_core.Operator):
        return PaddedInPlace_CP(op)

    def get_nb_required_protected(self, input_idx):
        if input_idx != 0:
            return super().get_nb_required_protected(input_idx)

        input = self.get_operator().get_input(0)
        if not input:
            return aidge_core.Elts_t.none_elts()
        output = self.get_operator().get_output(0)

        # Non-Padded case: margin = one input line
        stride = 1
        padding = 0
        if not self.get_operator().is_atomic():
            # Padded case: margin = (padding_y / stride_y) input lines
            # or in 1D: margin = (padding_x / stride_x) pixels
            sub_graph = self.get_operator().get_micro_graph().clone()
            aidge_core.expand_metaops(sub_graph, True)

            for node in sub_graph.get_nodes():
                if hasattr(node.get_operator().attr, 'stride_dims'):
                    if len(node.get_operator().attr.stride_dims) >= 1:
                        stride = node.get_operator().attr.stride_dims[0]
                elif hasattr(node.get_operator().attr, 'pads'):
                    if len(node.get_operator().attr.pads) >= 2:
                        padding = node.get_operator().attr.pads[0]

        margin = 0
        if len(input.dims) == 4:
            # 2D: one input line = W*C
            # Note: there should be a way to turn the loop into a closed form
            # expression!
            out_write = 0
            for out_line in range(get_height(output)):
                prev_in_line = max(0, out_line * stride - padding)
                in_last_read = prev_in_line * get_chan(input) * get_width(input)
                out_write += get_chan(output) * get_width(output)
                margin = max(margin, out_write - in_last_read)
        elif len(input.dims) == 3:
            # 1D: one input line = C
            out_write = 0
            for out_line in range(get_height(output)):
                prev_in_line = max(0, out_line * stride - padding)
                in_last_read = prev_in_line * get_chan(input)
                out_write += get_chan(output)
                margin = max(margin, out_write - in_last_read)
        else:
            raise NotImplementedError(f"Conv with input of dim {input.dims} is not supported")

        return aidge_core.Elts_t.data_elts(margin)


@ExportLibCpp.register("Conv1D",
    aidge_core.ImplSpec(
        [ # Input specifications
            aidge_core.IOSpec(aidge_core.dtype.any, aidge_core.dformat.nwc),
            aidge_core.IOSpec(aidge_core.dtype.any, aidge_core.dformat.nwc),
            aidge_core.IOSpec(aidge_core.dtype.any, aidge_core.dformat.any)
        ],
        [ # Output specifications
            aidge_core.IOSpec(aidge_core.dtype.any, aidge_core.dformat.nwc)
        ],
    ),
    PaddedInPlace_CP.default_model)
class Conv1D(ExportNodeCpp):
    def __init__(self, node, mem_info):
        super().__init__(node, mem_info)

        # Initialize kernel attributes
        self.attributes["padding"] = [0, 0, 0, 0]
        self.attributes["activation"] = "Linear"

        ## Scaling
        self.attributes["rescaling"] = "NoScaling"
        self.attributes["shift_value"] = 0

        # Browse the metaop to update kernel attributes
        ConvNode = get_node_from_metaop(node, "Conv1D")
        self.attributes["kernel_dims"] = ConvNode[0].get_operator().attr.kernel_dims
        self.attributes["stride_dims"] = ConvNode[0].get_operator().attr.stride_dims
        self.attributes["dilation_dims"] = ConvNode[0].get_operator().attr.dilation_dims
        self.attributes["bias_default_type"] = "float"

        # Template for layer configutation file generation
        self.config_template = str(ROOT / "templates" / "configuration" / "convolution_config.jinja")

        # Template layer call function generation within the forward file
        self.forward_template = str(ROOT / "templates" / "kernel_forward" / "convolution_forward.jinja")

        # Files to include within the generated forward.cpp file
        self.include_list = []

        # Path to the kernel(s) files to copy
        self.add_kernel_to_copy(ROOT / "kernels" / "convolution.hpp", "include/kernels/cpp")
        self.add_kernel_to_copy(ROOT / "static" / "macs.hpp", "include/utils/cpp", fwd_include=False)

        # Include aidge outputs within the fwd file
        if self.attributes["aidge_cmp"]:
            self.include_list.append("utils/cpp/utils.hpp")   # aidge_cmp function
            self.include_list.append("data/aidge_outputs/" + node.name() + ".hpp")


@ExportLibCpp.register("Conv2D",
    aidge_core.ImplSpec(
        [ # Input specifications
            aidge_core.IOSpec(aidge_core.dtype.any, aidge_core.dformat.nhwc),
            aidge_core.IOSpec(aidge_core.dtype.any, aidge_core.dformat.nhwc),
            aidge_core.IOSpec(aidge_core.dtype.any, aidge_core.dformat.any)
        ],
        [ # Output specifications
            aidge_core.IOSpec(aidge_core.dtype.any, aidge_core.dformat.nhwc)
        ],
    ),
    PaddedInPlace_CP.default_model)
class Conv2D(ExportNodeCpp):
    def __init__(self, node, mem_info):
        super().__init__(node, mem_info)

        # Initialize kernel attributes
        self.attributes["padding"] = [0, 0, 0, 0]
        self.attributes["activation"] = "Linear"
        self.attributes["aidge_cmp"] = node.attributes().has_attr("aidge_cmp")
        self.attributes["dev_mode"] = node.attributes().has_attr("dev_mode")

        ## Scaling
        self.attributes["rescaling"] = "NoScaling"
        self.attributes["shift_value"] = 0

        # Browse the metaop to update kernel attributes
        ConvNode = get_node_from_metaop(node, "Conv2D")
        self.attributes["kernel_dims"] = ConvNode[0].get_operator().attr.kernel_dims
        self.attributes["stride_dims"] = ConvNode[0].get_operator().attr.stride_dims
        self.attributes["dilation_dims"] = ConvNode[0].get_operator().attr.dilation_dims
        self.attributes["bias_default_type"] = "float"

        # Template for layer configutation file generation
        self.config_template = str(ROOT / "templates" / "configuration" / "convolution_config.jinja")

        # Template layer call function generation within the forward file
        self.forward_template = str(ROOT / "templates" / "kernel_forward" / "convolution_forward.jinja")

        # Files to include within the generated forward.cpp file
        self.include_list = []

        # Path to the kernel(s) files to copy
        self.add_kernel_to_copy(ROOT / "kernels" / "convolution.hpp", "include/kernels/cpp")
        self.add_kernel_to_copy(ROOT / "static" / "macs.hpp", "include/utils/cpp", fwd_include=False)

        # Include aidge outputs within the fwd file
        if self.attributes["aidge_cmp"]:
            self.include_list.append("utils/cpp/utils.hpp")   # aidge_cmp function
            self.include_list.append("data/aidge_outputs/" + node.name() + ".hpp")


@ExportLibCpp.register_metaop("QConv",
    aidge_core.ImplSpec(
        [ # Input specifications
            aidge_core.IOSpec(aidge_core.dtype.any, aidge_core.dformat.nhwc),
            aidge_core.IOSpec(aidge_core.dtype.any, aidge_core.dformat.nhwc),
            aidge_core.IOSpec(aidge_core.dtype.any, aidge_core.dformat.any)
        ],
        [ # Output specifications
            aidge_core.IOSpec(aidge_core.dtype.any, aidge_core.dformat.nhwc)
        ],
    ),
    PaddedInPlace_CP.default_model)
class QConv(Conv2D):
    def __init__(self, node, mem_info):
        super().__init__(node, mem_info)

        # Look for Quantizer node and set shift and coef export node attributes
        set_scaling_attributes(self, node)

        ## Set the scaling type
        if self.attributes["shift_value"] != 0:
            self.attributes["rescaling"] = "SingleShiftScaling"

        ## Set the bias default type (used if bias input is None)
        self.attributes["bias_default_type"] = "int32_t"


@ExportLibCpp.register_metaop(["PaddedConv2D", "PadConv"],
    aidge_core.ImplSpec(
        [ # Input specifications
            aidge_core.IOSpec(aidge_core.dtype.any, aidge_core.dformat.nhwc),
            aidge_core.IOSpec(aidge_core.dtype.any, aidge_core.dformat.nhwc),
            aidge_core.IOSpec(aidge_core.dtype.any, aidge_core.dformat.any)
        ],
        [ # Output specifications
            aidge_core.IOSpec(aidge_core.dtype.any, aidge_core.dformat.nhwc)
        ],
    ),
    PaddedInPlace_CP.default_model)
class PadConv(QConv):
    def __init__(self, node, mem_info):
        super().__init__(node, mem_info)

        # Browse the metaop to update kernel attributes
        PadNode = get_node_from_metaop(node, "Pad")
        self.attributes["padding"] = PadNode[0].get_operator().attr.pads


@ExportLibCpp.register_metaop("ConvAct",
    aidge_core.ImplSpec(
        [ # Input specifications
            aidge_core.IOSpec(aidge_core.dtype.any, aidge_core.dformat.nhwc),
            aidge_core.IOSpec(aidge_core.dtype.any, aidge_core.dformat.nhwc),
            aidge_core.IOSpec(aidge_core.dtype.any, aidge_core.dformat.any)
        ],
        [ # Output specifications
            aidge_core.IOSpec(aidge_core.dtype.any, aidge_core.dformat.nhwc)
        ],
    ),
    PaddedInPlace_CP.default_model)
class ConvAct(QConv):
    def __init__(self, node, mem_info):
        super().__init__(node, mem_info)

        # Browse the metaop to update kernel attributes
        if get_node_from_metaop(node, "ReLU"):
            self.attributes["activation"] = "Rectifier"
        else:
            aidge_core.Log.error(f"{node.type()} activation is not yet supported.")

@ExportLibCpp.register_metaop("PadConvAct",
    aidge_core.ImplSpec(
        [ # Input specifications
            aidge_core.IOSpec(aidge_core.dtype.any, aidge_core.dformat.nhwc),
            aidge_core.IOSpec(aidge_core.dtype.any, aidge_core.dformat.nhwc),
            aidge_core.IOSpec(aidge_core.dtype.any, aidge_core.dformat.any)
        ],
        [ # Output specifications
            aidge_core.IOSpec(aidge_core.dtype.any, aidge_core.dformat.nhwc)
        ],
    ),
    PaddedInPlace_CP.default_model)
class PadConvAct(PadConv, ConvAct):
    def __init__(self, node, mem_info):
        super().__init__(node, mem_info)
