import aidge_core
from aidge_core.export_utils import ExportNodeCpp
from aidge_export_cpp import ROOT, ExportLibCpp

@ExportLibCpp.register("Resize", 
    aidge_core.ImplSpec(
        [ # Input specifications
            aidge_core.IOSpec(aidge_core.dtype.any, aidge_core.dformat.nhwc),
            aidge_core.IOSpec(aidge_core.dtype.any, aidge_core.dformat.any),
            aidge_core.IOSpec(aidge_core.dtype.any, aidge_core.dformat.any)
        ],
        [ # Output specifications
            aidge_core.IOSpec(aidge_core.dtype.any, aidge_core.dformat.nhwc)
        ],
        [aidge_core.mandatory_attrs(aidge_core.DynamicAttributes({"interpolation_mode": aidge_core.Interpolation.Mode.ROUND_PREFER_FLOOR}))]
    ))
class Resize(ExportNodeCpp):
    def __init__(self, node, mem_info):
        super().__init__(node, mem_info)

        # Initialize kernel attributes
        self.attributes["mem_ofst"] = mem_info[0]["offset"]

        # Initialize mandatory ExportNode's lists
        self.include_list = []      # Files to include within the generated forward.cpp file

        # Template for layer configutation file generation
        self.config_template = str(ROOT / "templates" / "configuration" / "resize_config.jinja")
        # Template layer call function generation within the forward file
        self.forward_template = str(ROOT / "templates" / "kernel_forward" / "resize_forward.jinja")
        # Path to the kernel(s) files to copy
        self.add_kernel_to_copy(ROOT / "kernels" / "resize.hpp", "include/kernels/cpp")

        # Include aidge outputs within the fwd file
        if self.attributes["aidge_cmp"]:
            self.include_list.append("data/aidge_outputs/" + node.name() + ".hpp")
