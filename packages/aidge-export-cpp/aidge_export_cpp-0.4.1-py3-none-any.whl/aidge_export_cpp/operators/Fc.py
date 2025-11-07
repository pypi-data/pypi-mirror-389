import aidge_core
from aidge_core.export_utils import ExportNodeCpp, get_node_from_metaop, aidge2c
from aidge_export_cpp import ROOT, ExportLibCpp, set_scaling_attributes

@ExportLibCpp.register("FC",
    aidge_core.ImplSpec(
        [ # Input specifications
            aidge_core.IOSpec(aidge_core.dtype.any, aidge_core.dformat.default),
            aidge_core.IOSpec(aidge_core.dtype.any, aidge_core.dformat.any)
        ],
        [ # Output specifications
            aidge_core.IOSpec(aidge_core.dtype.any, aidge_core.dformat.any)
        ],
    ))
class FC(ExportNodeCpp):
    def __init__(self, node, mem_info):
        super().__init__(node, mem_info)

        # Initialize kernel attributes
        self.attributes["kernel"] = "default"
        self.attributes["activation"] = "Linear"
        self.attributes["bias_default_type"] = "float"

        ## Scaling
        self.attributes["rescaling"] = "NoScaling"
        self.attributes["shift_value"] = 0

        # Template for layer configutation file generation
        self.config_template = str(ROOT / "templates" / "configuration" / "fullyconnected_config.jinja")
        
        # Template layer call function generation within the forward file
        self.forward_template = str(ROOT / "templates" / "kernel_forward" / "fullyconnected_forward.jinja")
        
        # Files to include within the generated forward.cpp file
        self.include_list = []
        
        # Path to the kernel(s) files to copy
        self.add_kernel_to_copy(ROOT / "kernels" / "fullyconnected.hpp", "include/kernels/cpp")
        self.add_kernel_to_copy(ROOT / "static" / "macs.hpp", "include/utils/cpp", fwd_include=False)

        # Include aidge outputs within the fwd file
        if self.attributes["aidge_cmp"]:
            self.include_list.append("utils/cpp/utils.hpp")   # aidge_cmp function
            self.include_list.append("data/aidge_outputs/" + node.name() + ".hpp")

@ExportLibCpp.register("FC",
    aidge_core.ImplSpec(
        [ # Input specifications
            aidge_core.IOSpec(aidge_core.dtype.any, aidge_core.dformat.nhwc),
            aidge_core.IOSpec(aidge_core.dtype.any, aidge_core.dformat.any)
        ],
        [ # Output specifications
            aidge_core.IOSpec(aidge_core.dtype.any, aidge_core.dformat.any)
        ],
    ))
class FC_NHWC(FC):
    def __init__(self, node, mem_info):
        super().__init__(node, mem_info)
        if node.attributes().has_attr("ignore_input_format"):
            self.attributes["kernel"] = ""
        else:
            self.attributes["kernel"] = "transpose"

@ExportLibCpp.register_metaop("QFC",
    aidge_core.ImplSpec(
        [ # Input specifications
            aidge_core.IOSpec(aidge_core.dtype.any, aidge_core.dformat.default),
            aidge_core.IOSpec(aidge_core.dtype.any, aidge_core.dformat.any)
        ],
        [ # Output specifications
            aidge_core.IOSpec(aidge_core.dtype.any, aidge_core.dformat.any)
        ],
    ))
class QFC(FC):
    def __init__(self, node, mem_info):
        super().__init__(node, mem_info)

        # Browse the metaop to update kernel attributes
        set_scaling_attributes(self, node)

        ## Set the scaling type
        if self.attributes["shift_value"] != 0:
            self.attributes["rescaling"] = "SingleShiftScaling"

        ## Set the bias default type (used if bias input is None)
        self.attributes["bias_default_type"] = "int32_t"

@ExportLibCpp.register_metaop("QFC",
    aidge_core.ImplSpec(
        [ # Input specifications
            aidge_core.IOSpec(aidge_core.dtype.any, aidge_core.dformat.nhwc),
            aidge_core.IOSpec(aidge_core.dtype.any, aidge_core.dformat.any)
        ],
        [ # Output specifications
            aidge_core.IOSpec(aidge_core.dtype.any, aidge_core.dformat.any)
        ],
    ))
class QFC_NHWC(QFC):
    def __init__(self, node, mem_info):
        super().__init__(node, mem_info)
        if node.attributes().has_attr("ignore_input_format"):
            self.attributes["kernel"] = ""
        else:
            self.attributes["kernel"] = "transpose"

@ExportLibCpp.register_metaop("FCAct",
    aidge_core.ImplSpec(
        [ # Input specifications
            aidge_core.IOSpec(aidge_core.dtype.any, aidge_core.dformat.default),
            aidge_core.IOSpec(aidge_core.dtype.any, aidge_core.dformat.any)
        ],
        [ # Output specifications
            aidge_core.IOSpec(aidge_core.dtype.any, aidge_core.dformat.any)
        ],
    ))
class FCAct(QFC):
    def __init__(self, node, mem_info):
        super().__init__(node, mem_info)

        # Browse the metaop to update kernel attributes
        if get_node_from_metaop(node, "ReLU"):
            self.attributes["activation"] = "Rectifier"
        else:
            aidge_core.Log.error(f"{node.type()} activation is not yet supported.")

@ExportLibCpp.register_metaop("FCAct",
    aidge_core.ImplSpec(
        [ # Input specifications
            aidge_core.IOSpec(aidge_core.dtype.any, aidge_core.dformat.nhwc),
            aidge_core.IOSpec(aidge_core.dtype.any, aidge_core.dformat.any)
        ],
        [ # Output specifications
            aidge_core.IOSpec(aidge_core.dtype.any, aidge_core.dformat.any)
        ],
    ))
class FCAct_NHWC(FCAct):
    def __init__(self, node, mem_info):
        super().__init__(node, mem_info)
        if node.attributes().has_attr("ignore_input_format"):
            self.attributes["kernel"] = ""
        else:
            self.attributes["kernel"] = "transpose"
