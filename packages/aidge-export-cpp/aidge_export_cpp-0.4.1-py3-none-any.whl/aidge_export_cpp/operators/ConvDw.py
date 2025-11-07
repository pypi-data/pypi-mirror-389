import aidge_core
from aidge_core.export_utils import ExportNodeCpp, get_node_from_metaop
from aidge_export_cpp import ROOT, ExportLibCpp, set_scaling_attributes
from .Conv import PaddedInPlace_CP

@ExportLibCpp.register("ConvDepthWise2D",
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
class ConvDw(ExportNodeCpp):
    def __init__(self, node, mem_info):
        super().__init__(node, mem_info)

        # Initialize kernel attributes
        self.attributes["padding"] = [0, 0, 0, 0]
        self.attributes["activation"] = "Linear"
        self.attributes["depthwise"] = True

        ## Scaling
        self.attributes["rescaling"] = "NoScaling"
        self.attributes["shift_value"] = 0

        # Browse the metaop to update kernel attributes
        ConvDwNode = get_node_from_metaop(node, "ConvDepthWise2D") 
        self.attributes["kernel_dims"] = ConvDwNode[0].get_operator().attr.kernel_dims
        self.attributes["stride_dims"] = ConvDwNode[0].get_operator().attr.stride_dims
        self.attributes["dilation_dims"] = ConvDwNode[0].get_operator().attr.dilation_dims
        self.attributes["bias_default_type"] = "float"

        # Template for layer configutation file generation
        self.config_template = str(ROOT / "templates" / "configuration" / "convolution_config.jinja")
        
        # Template layer call function generation within the forward file
        self.forward_template = str(ROOT / "templates" / "kernel_forward" / "convolution_forward.jinja")
        
        # Files to include within the generated forward.cpp file
        self.include_list = []
        
        # Path to the kernel(s) files to copy
        self.add_kernel_to_copy(ROOT / "kernels" / "convolution_depthwise.hpp", "include/kernels/cpp")
        self.add_kernel_to_copy(ROOT / "static" / "macs.hpp", "include/utils/cpp", fwd_include=False)
        
        # Include aidge outputs within the fwd file
        if self.attributes["aidge_cmp"]:
            self.include_list.append("utils/cpp/utils.hpp")   # aidge_cmp function
            self.include_list.append("data/aidge_outputs/" + node.name() + ".hpp") 


@ExportLibCpp.register_metaop("QConvDw",
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
class QConvDw(ConvDw):
    def __init__(self, node, mem_info):
        super().__init__(node, mem_info)

        # Look for Quantizer node and set shift and coef export node attributes
        set_scaling_attributes(self, node)

        ## Set the scaling type
        if self.attributes["shift_value"] != 0:
            self.attributes["rescaling"] = "SingleShiftScaling"

        ## Set the bias default type (used if bias input is None)
        self.attributes["bias_default_type"] = "int32_t"


@ExportLibCpp.register_metaop(["PaddedConvDepthWise2D", "PadConvDw"],
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
class PadConvDw(QConvDw):
    def __init__(self, node, mem_info):
        super().__init__(node, mem_info)

        # Browse the metaop to update kernel attributes
        PadNode = get_node_from_metaop(node, "Pad")
        self.attributes["padding"] = PadNode[0].get_operator().attr.pads


@ExportLibCpp.register_metaop("ConvDwAct",
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
class ConvDwAct(QConvDw):
    def __init__(self, node, mem_info):
        super().__init__(node, mem_info)

        # Browse the metaop to update kernel attributes
        if get_node_from_metaop(node, "ReLU"):
            self.attributes["activation"] = "Rectifier"
        else:
            aidge_core.Log.error(f"{node.type()} activation is not yet supported.")

@ExportLibCpp.register_metaop("PadConvDwAct",
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
class PadConvDwAct(PadConvDw, ConvDwAct):
    def __init__(self, node, mem_info):
        super().__init__(node, mem_info)
