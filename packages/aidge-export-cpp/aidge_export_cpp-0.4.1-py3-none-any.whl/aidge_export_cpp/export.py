import os
import shutil
from pathlib import Path
from typing import List, Union

import aidge_core
from aidge_core.mem_info import generate_optimized_memory_info
from aidge_core.export_utils import scheduler_export, generate_main_cpp

from aidge_export_cpp import ExportLibCpp
from aidge_export_cpp.export_utils import *


def export(export_folder_name: str,
           model: aidge_core.GraphView,
           scheduler: Union[List[aidge_core.Node],
                            aidge_core.Scheduler],
           inputs_tensor: List[aidge_core.Tensor] = None,
           labels: aidge_core.Tensor = None,
           dev_mode: bool = False,
           aidge_cmp: bool = False,
           memory_manager = generate_optimized_memory_info,
           memory_manager_args = {}):

    """ Export an aidge_core.Scheduler to C++ code

    :param export_folder_name: Export folder name
    :type export_folder_name: str
    :param model: An instance of :py:class:`aidge_core.graph_view`, providing access to nodes and
                       ordered input/output data within the computational graph.
    :type model: aidge_core.GraphView
    :param scheduler: Scheduler instance managing the computation graph.
                      Uses `graph_view` and `get_sequential_static_scheduling` methods
    :param inputs_tensor: argument to provide external tensors to use in the main function
                          By default, the input of the given graph will be exported.
    :type input_tensor: List[aidge_core.Tensor]
                    to retrieve the computation graph layout and ordered nodes.
    :type scheduler: aidge_core.Scheduler
    :param labels: Argument to provide labels tensor to generate and use in the main function.
    :type labels: aidge_core.Tensor
    :param dev_mode: Wether or not the developer mode is enabled. If enabled, the export files
                     will be symlinks from the aidge_export_cpp module. Therefore, modifying
                     a file within the export will change the module as well.
    :type dev_mode: boolean
    """

    # Graph Log (Save the state of the graph through export steps)
    os.makedirs("graph_log", exist_ok=True)
    model.save(f"graph_log/0_export_start")

    # Remove scaling producers from the export
    exclude_unwanted_producers(model)

    # Fuse nodes into MetaOps adapted to the CPP Export
    cpp_fuse_to_metaops(model)
    model.save(f"graph_log/1_fused_model")

    # Reset the scheduler after graph modification
    scheduler = aidge_core.SequentialScheduler(model) if scheduler is None else scheduler
    scheduler.reset_scheduling()
    scheduler.generate_scheduling()

    # Normalize nodes names
    set_nodes_names(scheduler)
    model.save(f"graph_log/2_named_model")

    # Last inference to set the inputs as well as the ifmaps (aidge_cmp)
    if inputs_tensor is not None:
        output_array = propagate(model, scheduler, inputs_tensor)
        aidge_core.Log.notice(f"Exported sample results : {np.argmax(output_array)} ( {str(np.max(output_array))} )")
        aidge_core.Log.notice(f"Label : {labels}")
    elif aidge_cmp:
        aidge_cmp = False
        aidge_core.Log.error("aidge_cmp : No input_tensor has been provided to the export() function.\n\
                             Therefore ifmaps have not been generated and aidge_cmp cannot be used.")

    # Set nodes datatypes if the model has been quantized
    # TODO : Should be changed with future quantization feature
    if inputs_tensor is not None:
        if inputs_tensor[0].dtype == aidge_core.dtype.int32:
            set_nodes_datatypes(model)      # Set datatype to int8 only
            for input in inputs_tensor:
                input.set_datatype(aidge_core.dtype.int8)
            model.save(f"graph_log/3_set_datatypes")

    # [aidge_cmp] Export feature maps tensors as json 
    if aidge_cmp:
        generate_aidge_ifmaps(model)

    # [aidge_cmp] Set flags on each node
    if aidge_cmp:
        for node in model.get_nodes():
            node.attributes().aidge_cmp = True

    # [dev_mode] Set flags on each node
    if dev_mode:
        for node in model.get_nodes():
            node.attributes().dev_mode = True

    # Set model's dataformat (NHWC)
    ## Inputs of the graph
    for in_node in model.get_ordered_inputs():
        input = in_node[0].get_operator().get_input(0)
        if input is not None:
            # Transpose the input
            input_cpy = input.clone()
            if (len(input.dims) == 4):
                input_cpy.set_data_format(aidge_core.dformat.nchw)
                input_cpy.set_data_format(aidge_core.dformat.nhwc)
            elif (len(input.dims) == 3):
                input_cpy.set_data_format(aidge_core.dformat.chw)
                input_cpy.set_data_format(aidge_core.dformat.hwc)
            in_node[0].get_operator().set_input(0, input_cpy)
    ## Inputs tensors
    if inputs_tensor is not None:
        for i in range(len(inputs_tensor)):
            input_cpy = inputs_tensor[i].clone()
            if input_cpy.dformat == aidge_core.dformat.default:
                if (len(input.dims) == 4):
                    input_cpy.set_data_format(aidge_core.dformat.nchw)
                elif (len(input.dims) == 3):
                    input_cpy.set_data_format(aidge_core.dformat.chw)
            if (len(input.dims) == 4):
                input_cpy.set_data_format(aidge_core.dformat.nhwc)
            elif (len(input.dims) == 3):
                input_cpy.set_data_format(aidge_core.dformat.hwc)
            inputs_tensor[i] = input_cpy
    ## Rest of the graph
    model.set_dataformat(aidge_core.dformat.nhwc)
    model.save(f"graph_log/4_set_dataformats")

    # Set model's backend
    model.set_backend(ExportLibCpp._name)

    # Adapt the graph to the selected backend
    aidge_core.adapt_to_backend(model)
    model.save(f"graph_log/5_adapt_to_backend")
    aidge_core.adapt_fc_params_format(model)
    model.save(f"graph_log/6_adapt_fc_params_format")

    # At this point, the graph dimensions are supposed to be statically
    # forwardable, thus allow_data_dependency can be safely set to True
    dims = []
    for in_node in model.get_ordered_inputs():
        is_optional = int(in_node[0].get_operator().input_category(in_node[1])) & int(aidge_core.InputCategory.Optional)
        if not is_optional:
            dims.append(in_node[0].get_operator().get_input(0).dims)
    model.forward_dims(dims=dims, allow_data_dependency=True)

    # Reset the scheduling as the graph may have been changed
    scheduler.reset_scheduling()
    scheduler.generate_scheduling()

    # Remove existing export
    export_folder_name = Path(export_folder_name)
    if os.path.isdir(export_folder_name):
        print("Removing existing export directory...")
        shutil.rmtree(export_folder_name)

    # Save the model
    model.save("graph_log/7_exported_model")

    # Setup stats folder
    if "stats_folder" not in memory_manager_args:
        memory_manager_args["stats_folder"] = f"{export_folder_name}/stats"

    # memory_manager_args["auto_concat"] = True

    # Generate the export
    scheduler_export(scheduler,
                     export_folder_name,
                     ExportLibCpp,
                     memory_manager=memory_manager,
                     memory_manager_args=memory_manager_args,
                     dev_mode=dev_mode)

    # Generate main file
    generate_main_cpp(export_folder_name, model, labels=labels, inputs_tensor=inputs_tensor)

    # Generate log files (aidge_cmp option)
    if aidge_cmp:
        export_aidge_ifmaps(export_folder_name)
