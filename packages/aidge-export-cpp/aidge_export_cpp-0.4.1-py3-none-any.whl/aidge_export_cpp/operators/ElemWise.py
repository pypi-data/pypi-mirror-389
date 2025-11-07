import aidge_core
from aidge_core.export_utils import ExportNodeCpp, get_node_from_metaop
from aidge_export_cpp import ROOT, ExportLibCpp, set_scaling_attributes

class ElemWise(ExportNodeCpp):
    def __init__(self, node, mem_info):
        super().__init__(node, mem_info)

        # Initialize kernel attributes
        self.attributes["activation"] = "Linear"

        ## Scaling
        self.attributes["rescaling"] = "NoScaling"
        self.attributes["shift_value"] = 0
        self.attributes["coef_value"] = 1

        ## Accumulation type
        self.attributes["accumulation_type"] = "float"

        nbdims_out = len(self.attributes["out_dims"][0])
        dims_a = self.attributes["in_dims"][0]
        dims_b = self.attributes["in_dims"][1]
        ndim_a = [0] * nbdims_out
        ndim_b = [0] * nbdims_out

        idx_a = nbdims_out - len(dims_a)
        for i in range(nbdims_out):
            ndim_a[i] = 1 if i < idx_a else dims_a[i - idx_a]

        idx_b = nbdims_out - len(dims_b)
        for i in range(nbdims_out):
            ndim_b[i] = 1 if i < idx_b else dims_b[i - idx_b]

        # Find highest equal dimension
        contiguousIdx = nbdims_out - 1
        for i in range(nbdims_out - 1, -1, -1):
            if ndim_a[i] != ndim_b[i]:
                break
            contiguousIdx = i

        # Compute the highest number of contiguous data
        input0_contiguous_size = 1
        input1_contiguous_size = 1
        output_contiguous_size = 1
        for i in range(contiguousIdx, nbdims_out):
            input0_contiguous_size *= ndim_a[i]
            input1_contiguous_size *= ndim_b[i]
            output_contiguous_size *= self.attributes["out_dims"][0][i]

        self.attributes["input1_cont_size"] = input0_contiguous_size
        self.attributes["input2_cont_size"] = input1_contiguous_size
        self.attributes["output_cont_size"] = output_contiguous_size

        # Initialize strides for broadcasting
        stride_post0 = [0] * contiguousIdx
        stride_post1 = [0] * contiguousIdx
        stride_step0 = [0] * contiguousIdx
        stride_step1 = [0] * contiguousIdx

        if contiguousIdx > 0:
            stride_post0[contiguousIdx - 1] = 1
            stride_post1[contiguousIdx - 1] = 1
            for i in range(contiguousIdx - 2, -1, -1):
                stride_post0[i] = stride_post0[i + 1] * ndim_a[i + 1]
                stride_post1[i] = stride_post1[i + 1] * ndim_b[i + 1]

            for i in range(contiguousIdx):
                stride_step0[i] = 1 - stride_post0[i] if ndim_a[i] == 1 else 1
                stride_step1[i] = 1 - stride_post1[i] if ndim_b[i] == 1 else 1

        # Offset and matrix count
        offsetIn0 = 0
        offsetIn1 = 0
        nbMatrices = 1
        for i in range(contiguousIdx):
            nbMatrices *= self.attributes["out_dims"][0][i]


        self.attributes["offset_in1"] = [0]
        self.attributes["offset_in2"] = [0]

        for stack in range(1, nbMatrices):
            dim = contiguousIdx - 1
            tmp_stack = stack
            while tmp_stack % self.attributes["out_dims"][0][dim] == 0:
                tmp_stack //= self.attributes["out_dims"][0][dim]
                dim -= 1
            offsetIn0 += stride_step0[dim]
            offsetIn1 += stride_step1[dim]

            self.attributes["offset_in1"].append(offsetIn0)
            self.attributes["offset_in2"].append(offsetIn1)

        # Template for layer configutation file generation
        self.config_template = str(ROOT / "templates" / "configuration" / "elemwise_config.jinja")

        # Template layer call function generation within the forward file
        self.forward_template = str(ROOT / "templates" / "kernel_forward" / "elemwise_forward.jinja")

        # Files to include within the generated forward.cpp file
        self.include_list = []

        # Path to the kernel(s) files to copy
        self.add_kernel_to_copy(ROOT / "kernels" / "elemwise.hpp", "include/kernels/cpp")
        
        # Include aidge outputs within the fwd file
        if self.attributes["aidge_cmp"]:
            self.include_list.append("utils/cpp/utils.hpp")   # aidge_cmp function
            self.include_list.append("data/aidge_outputs/" + node.name() + ".hpp")


class QElemWise(ElemWise):
    def __init__(self, node, mem_info):
        super().__init__(node, mem_info)

        # Browse the metaop to update kernel attributes
        set_scaling_attributes(self, node)

        ## Set the scaling type
        if self.attributes["coef_value"] != 1:
            self.attributes["rescaling"] = "FixedPointScaling"
        elif self.attributes["shift_value"] != 0:
            self.attributes["rescaling"] = "SingleShiftScaling"

        ## Accumulation type
        self.attributes["accumulation_type"] = "int32_t"


@ExportLibCpp.register("Add",
    aidge_core.ImplSpec(aidge_core.IOSpec(aidge_core.dtype.any)),
    aidge_core.ProdConso.in_place_model)
class Add(ElemWise):
    def __init__(self, node, mem_info):
        super().__init__(node, mem_info)
        self.attributes["elemwise_op"] = "Add"


@ExportLibCpp.register_metaop("QAdd",
    aidge_core.ImplSpec(aidge_core.IOSpec(aidge_core.dtype.any)),
    aidge_core.ProdConso.in_place_model)
class QAdd(QElemWise, Add):
    def __init__(self, node, mem_info):
        super().__init__(node, mem_info)


@ExportLibCpp.register_metaop("AddAct",
    aidge_core.ImplSpec(aidge_core.IOSpec(aidge_core.dtype.any)),
    aidge_core.ProdConso.in_place_model)
class AddAct(Add):
    def __init__(self, node, mem_info):
        super().__init__(node, mem_info)

        # Browse the metaop to update kernel attributes
        if get_node_from_metaop(node, "ReLU"):
            self.attributes["activation"] = "Rectifier"
        else:
            aidge_core.Log.error(f"{node.type()} activation is not yet supported.") 


@ExportLibCpp.register_metaop("QAddAct",
    aidge_core.ImplSpec(aidge_core.IOSpec(aidge_core.dtype.any)),
    aidge_core.ProdConso.in_place_model)
class QAddAct(QAdd):
    def __init__(self, node, mem_info):
        super().__init__(node, mem_info)

        # Browse the metaop to update kernel attributes
        if get_node_from_metaop(node, "ReLU"):
            self.attributes["activation"] = "Rectifier"
        else:
            aidge_core.Log.error(f"{node.type()} activation is not yet supported.") 


@ExportLibCpp.register("Sub",
    aidge_core.ImplSpec(aidge_core.IOSpec(aidge_core.dtype.any)),
    aidge_core.ProdConso.in_place_model)
class Sub(ElemWise):
    def __init__(self, node, mem_info):
        super().__init__(node, mem_info)
        self.attributes["elemwise_op"] = "Sub"


@ExportLibCpp.register_metaop("QSub",
    aidge_core.ImplSpec(aidge_core.IOSpec(aidge_core.dtype.any)),
    aidge_core.ProdConso.in_place_model)
class QSub(QElemWise, Sub):
    def __init__(self, node, mem_info):
        super().__init__(node, mem_info)


@ExportLibCpp.register_metaop("SubAct",
    aidge_core.ImplSpec(aidge_core.IOSpec(aidge_core.dtype.any)),
    aidge_core.ProdConso.in_place_model)
class SubAct(Sub):
    def __init__(self, node, mem_info):
        super().__init__(node, mem_info)

        # Browse the metaop to update kernel attributes
        if get_node_from_metaop(node, "ReLU"):
            self.attributes["activation"] = "Rectifier"
        else:
            aidge_core.Log.error(f"{node.type()} activation is not yet supported.") 


@ExportLibCpp.register_metaop("QSubAct",
    aidge_core.ImplSpec(aidge_core.IOSpec(aidge_core.dtype.any)),
    aidge_core.ProdConso.in_place_model)
class QSubAct(QSub):
    def __init__(self, node, mem_info):
        super().__init__(node, mem_info)

        # Browse the metaop to update kernel attributes
        if get_node_from_metaop(node, "ReLU"):
            self.attributes["activation"] = "Rectifier"
        else:
            aidge_core.Log.error(f"{node.type()} activation is not yet supported.") 


@ExportLibCpp.register("Mul",
    aidge_core.ImplSpec(aidge_core.IOSpec(aidge_core.dtype.any)),
    aidge_core.ProdConso.in_place_model)
class Mul(ElemWise):
    def __init__(self, node, mem_info):
        super().__init__(node, mem_info)
        self.attributes["elemwise_op"] = "Mul"


# QMul and QMulAct -> Quantizer operator


@ExportLibCpp.register_metaop("MulAct",
    aidge_core.ImplSpec(aidge_core.IOSpec(aidge_core.dtype.any)),
    aidge_core.ProdConso.in_place_model)
class MulAct(Mul):
    def __init__(self, node, mem_info):
        super().__init__(node, mem_info)

        # Browse the metaop to update kernel attributes
        if get_node_from_metaop(node, "ReLU"):
            self.attributes["activation"] = "Rectifier"
        else:
            aidge_core.Log.error(f"{node.type()} activation is not yet supported.")


@ExportLibCpp.register("Div",
    aidge_core.ImplSpec(aidge_core.IOSpec(aidge_core.dtype.any)),
    aidge_core.ProdConso.in_place_model)
class Div(ElemWise):
    def __init__(self, node, mem_info):
        super().__init__(node, mem_info)
        self.attributes["elemwise_op"] = "Div"


@ExportLibCpp.register_metaop("QDiv",
    aidge_core.ImplSpec(aidge_core.IOSpec(aidge_core.dtype.any)),
    aidge_core.ProdConso.in_place_model)
class QDiv(QElemWise):
    def __init__(self, node, mem_info):
        super().__init__(node, mem_info)
        self.attributes["elemwise_op"] = "Div"


@ExportLibCpp.register_metaop("DivAct",
    aidge_core.ImplSpec(aidge_core.IOSpec(aidge_core.dtype.any)),
    aidge_core.ProdConso.in_place_model)
class DivAct(Div):
    def __init__(self, node, mem_info):
        super().__init__(node, mem_info)

        # Browse the metaop to update kernel attributes
        if get_node_from_metaop(node, "ReLU"):
            self.attributes["activation"] = "Rectifier"
        else:
            aidge_core.Log.error(f"{node.type()} activation is not yet supported.")


@ExportLibCpp.register_metaop("QDivAct",
    aidge_core.ImplSpec(aidge_core.IOSpec(aidge_core.dtype.any)),
    aidge_core.ProdConso.in_place_model)
class QDivAct(QDiv):
    def __init__(self, node, mem_info):
        super().__init__(node, mem_info)

        # Browse the metaop to update kernel attributes
        if get_node_from_metaop(node, "ReLU"):
            self.attributes["activation"] = "Rectifier"
        else:
            aidge_core.Log.error(f"{node.type()} activation is not yet supported.")