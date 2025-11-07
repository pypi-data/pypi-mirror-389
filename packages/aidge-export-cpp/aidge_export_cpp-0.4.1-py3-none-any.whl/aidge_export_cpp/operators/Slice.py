import aidge_core
from aidge_core.export_utils import ExportNodeCpp
from aidge_export_cpp import ROOT
from aidge_export_cpp import ExportLibCpp

@ExportLibCpp.register("Slice",
    aidge_core.ImplSpec(aidge_core.IOSpec(aidge_core.dtype.any)))
class SliceCPP(ExportNodeCpp):
    def __init__(self, node, mem_info):
        super().__init__(node, mem_info)
        # Secure retrieve parameter attributes
        input_dims = self.attributes["in_dims"][0]
        axes = [a if a>=0 else a+len(input_dims) for a in node.get_operator().attr.axes] # postive axes
        starts, ends, steps = node.get_operator().attr.starts, node.get_operator().attr.ends, node.get_operator().attr.steps
        assert len(starts) == len(axes)
        assert len(ends) == len(axes)
        assert len(steps) == len(steps)
        # positive start and ends indices
        starts = [s if  s>=0 else s+input_dims[axes[i]] for i,s in enumerate(starts)] 
        ends = [e if e>=0 else e+input_dims[axes[i]] for i,e in enumerate(ends)]
        # assert boundaries
        for a in axes: assert a>=0 and a < len(input_dims)
        for i,e in enumerate(ends): assert e>=0 and e <= input_dims[axes[i]]
        for i,s in enumerate(starts): assert s>=0 and s < ends[i]
        for st in steps: assert st >= 1
        self.attributes["starts"] = starts
        self.attributes["ends"] = ends
        self.attributes["steps"] = steps
        
        #Compute mod and div values that will be used to convert input flat-index to axes-index
        axes_mod = [input_dims[a] for a in axes]
        axes_div = len(axes) * [1]
        for i,ax in enumerate(axes):
            for j in range(ax+1, len(input_dims)):
                axes_mod[i] *= input_dims[j]
                axes_div[i] *= input_dims[j]
        self.attributes["axes_mod"] = axes_mod
        self.attributes["axes_div"] = axes_div

        self.config_template = str(ROOT / "templates" / "configuration" / "slice_config.jinja")
        self.forward_template = str(ROOT / "templates" / "kernel_forward" / "slice_forward.jinja")
        self.include_list = []
        self.add_kernel_to_copy(ROOT / "kernels" / "slice.hpp", "include/kernels/cpp")
        
        # Include aidge outputs within the fwd file
        if self.attributes["aidge_cmp"]:
            self.include_list.append("utils/cpp/utils.hpp")   # aidge_cmp function
            self.include_list.append("data/aidge_outputs/" + node.name() + ".hpp")
