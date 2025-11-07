import aidge_core
from aidge_core.export_utils import ExportNodeCpp
from aidge_export_cpp import ROOT, ExportLibCpp, set_scaling_attributes

@ExportLibCpp.register("ReLU",
    aidge_core.ImplSpec(aidge_core.IOSpec(aidge_core.dtype.any)),
    aidge_core.ProdConso.in_place_model)
class ReLU(ExportNodeCpp):
    def __init__(self, node, mem_info):
        super().__init__(node, mem_info)

        # Initialize kernel attributes
        self.attributes["activation"] = "Rectifier"

        ## Scaling
        self.attributes["rescaling"] = "NoScaling"
        self.attributes["shift_value"] = 0
        self.attributes["coef_value"] = 1

        ## Accumulation type
        self.attributes["accumulation_type"] = "float"

        # Template for layer configutation file generation
        self.config_template = str(ROOT / "templates" / "configuration" / "activation_config.jinja")
        
        # Template layer call function generation within the forward file
        self.forward_template = str(ROOT / "templates" / "kernel_forward" / "activation_forward.jinja")
        
        # Files to include within the generated forward.cpp file
        self.include_list = []
        
        # Path to the kernel(s) files to copy
        self.add_kernel_to_copy(ROOT / "kernels" / "activation.hpp")
        
        # Include aidge outputs within the fwd file
        if self.attributes["aidge_cmp"]:
            self.include_list.append("utils/cpp/utils.hpp")   # aidge_cmp function
            self.include_list.append("data/aidge_outputs/" + node.name() + ".hpp")

@ExportLibCpp.register("LeakyReLU",
    aidge_core.ImplSpec(aidge_core.IOSpec(aidge_core.dtype.any)),
    aidge_core.ProdConso.in_place_model)
class LeakyReLU(ExportNodeCpp):
    def __init__(self, node, mem_info):
        super().__init__(node, mem_info)

        # Initialize kernel attributes
        self.attributes["alpha"] = node.get_operator().attr.negative_slope
        self.attributes["aidge_cmp"] = node.attributes().has_attr("aidge_cmp")
        self.attributes["dev_mode"] = node.attributes().has_attr("dev_mode")

        ## Accumulation type
        self.attributes["accumulation_type"] = "float"

        # Template for layer configutation file generation
        self.config_template = str(ROOT / "templates" / "configuration" / "leakyrelu_config.jinja")
        
        # Template layer call function generation within the forward file
        self.forward_template = str(ROOT / "templates" / "kernel_forward" / "leakyrelu_forward.jinja")
        
        # Files to include within the generated forward.cpp file
        self.include_list = []
        
        # Path to the kernel(s) files to copy
        self.add_kernel_to_copy(ROOT / "kernels" / "leakyrelu.hpp", "include/kernels/cpp")

        # Include aidge outputs within the fwd file
        if self.attributes["aidge_cmp"]:
            self.include_list.append("utils/cpp/utils.hpp")   # aidge_cmp function
            self.include_list.append("data/aidge_outputs/" + node.name() + ".hpp")
        
@ExportLibCpp.register_metaop("QReLU", aidge_core.ImplSpec(aidge_core.IOSpec(aidge_core.dtype.any)))
class QReLU(ReLU):
    def __init__(self, node, mem_info):
        super().__init__(node, mem_info)

        # Browse the metaop to update kernel attributes
        set_scaling_attributes(self, node)

        ## Accumulation type
        self.attributes["accumulation_type"] = "int32_t"

        # Update the scaling type
        if self.attributes["coef_value"] != 1:
            self.attributes["rescaling"] = "FixedPointScaling"
        elif self.attributes["shift_value"] != 0:
            self.attributes["rescaling"] = "SingleShiftScaling"
