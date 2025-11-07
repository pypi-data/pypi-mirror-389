import aidge_core
from aidge_core.export_utils import ExportNodeCpp
from aidge_export_cpp import ROOT
from aidge_export_cpp import ExportLibCpp

@ExportLibCpp.register("BatchNorm2D",
    aidge_core.ImplSpec(aidge_core.IOSpec(aidge_core.dtype.float32, aidge_core.dformat.nchw)),
    aidge_core.ProdConso.in_place_model)
class BatchNorm(ExportNodeCpp):
    def __init__(self, node, mem_info):
        super().__init__(node, mem_info)

        # Initialize kernel attributes
        self.attributes["activation"] = "Linear"
        self.attributes["rescaling"] = "NoScaling"
        self.attributes["epsilon"] = node.get_operator().attr.epsilon

        # Template for layer configutation file generation
        self.config_template = str( ROOT / "templates" / "configuration" / "batchnorm_config.jinja")
        
        # Template layer call function generation within the forward file
        self.forward_template = str(ROOT / "templates" / "kernel_forward" / "batchnorm_forward.jinja")
        
        # Files to include within the generated forward.cpp file
        self.include_list = []

        # Path to the kernel(s) files to copy
        self.add_kernel_to_copy(ROOT / "kernels" / "batchnorm.hpp", "include/kernels/cpp")
        self.add_kernel_to_copy(ROOT / "static" / "macs.hpp", "include/utils/cpp", fwd_include=False)

        # Include aidge outputs within the fwd file
        if self.attributes["aidge_cmp"]:
            self.include_list.append("utils/cpp/utils.hpp")   # aidge_cmp function
            self.include_list.append("data/aidge_outputs/" + node.name() + ".hpp")
            