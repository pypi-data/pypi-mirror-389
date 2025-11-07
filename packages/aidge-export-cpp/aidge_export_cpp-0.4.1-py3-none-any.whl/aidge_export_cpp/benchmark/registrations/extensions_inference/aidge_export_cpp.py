"""
Copyright (c) 2023 CEA-List

This program and the accompanying materials are made available under the
terms of the Eclipse Public License 2.0 which is available at
http://www.eclipse.org/legal/epl-2.0.

SPDX-License-Identifier: EPL-2.0
"""

import contextlib
import os
from shutil import rmtree
from subprocess import run
from typing import TYPE_CHECKING

import numpy as np

import aidge_core
import aidge_backend_cpu
import aidge_export_cpp

if TYPE_CHECKING:
    from aidge_benchmark import NamedTensor


def _prepare_model_scheduler_inputs(
    model: aidge_core.GraphView, inputs: list["NamedTensor"]
) -> tuple[aidge_core.GraphView, aidge_core.SequentialScheduler]:
    # load and set up the model
    model_prepared = model.clone()

    model_prepared.set_backend("cpu")

    # create input Tensor list for the GraphView
    ordered_inputs: list[aidge_core.Tensor] = [
        aidge_core.Tensor(i.array) for i in inputs
    ]

    # set inputs for the export
    for i, inp in enumerate(model_prepared.get_ordered_inputs()):
        if (i >= len(ordered_inputs)):
            break
        op = inp[0].get_operator()
        ordered_inputs[i].to_dformat(aidge_core.dformat.nchw)
        op.associate_input(i, ordered_inputs[i])

    scheduler = aidge_core.SequentialScheduler(model_prepared)
    scheduler.generate_scheduling()

    for i in range(len(ordered_inputs)):
        ordered_inputs[i].to_dformat(aidge_core.dformat.nhwc)

    model_prepared.set_dataformat(aidge_core.dformat.nhwc)
    model_prepared.set_backend(aidge_export_cpp.ExportLibCpp._name)
    aidge_core.adapt_to_backend(model_prepared)
    aidge_core.adapt_fc_params_format(model_prepared)
    model_prepared.forward_dims([t.dims for t in ordered_inputs])

    scheduler.reset_scheduling()
    scheduler.generate_scheduling()

    return model_prepared, scheduler, ordered_inputs

def measure_inference_time(
    model: aidge_core.GraphView,
    inputs: list["NamedTensor"],
    nb_warmup: int = 10,
    nb_iterations: int = 50,
) -> list[float]:
    model_prepared, scheduler, _ = _prepare_model_scheduler_inputs(model, inputs)

    # for ordered_input in ordered_inputs:
    # ordered_input.set_backend("cpu")
    operator_type: str = model_prepared.get_ordered_outputs()[0][0].get_operator().type()

    folder_name: str = f"{operator_type.lower()}_test_export_cpp"
    with open("/dev/null", "w") as f, contextlib.redirect_stdout(f):
        aidge_core.export_utils.scheduler_export(
            scheduler,
            folder_name,
            aidge_export_cpp.ExportLibCpp,
            memory_manager=aidge_core.mem_info.generate_optimized_memory_info,
            memory_manager_args={"wrapping": False},
        )
        aidge_core.export_utils.generate_main_inference_time_cpp(
            folder_name, model_prepared, nb_iterations, nb_warmup
        )

    with open("/dev/null", "w") as f, contextlib.redirect_stdout(f):
        run(["make"], cwd=folder_name, stdout=f)

    timings_str = run(f"./{folder_name}/bin/run_export", capture_output=True, text=True)

    folder_path = os.path.abspath(folder_name)
    if os.path.exists(folder_path):
        rmtree(folder_path, ignore_errors=True)

    timings = [float(t) for t in timings_str.stdout.split(" ") if t.strip()]
    return timings


def compute_output(
    model: aidge_core.GraphView, inputs: list["NamedTensor"]
) -> list[np.ndarray]:
    model_prepared, scheduler, _ = _prepare_model_scheduler_inputs(model, inputs)

    operator_type: str = model_prepared.get_ordered_outputs()[0][0].get_operator().type()

    folder_name: str = f"{operator_type.lower()}_test_export_cpp"
    with open("/dev/null", "w") as f, contextlib.redirect_stdout(f):
        aidge_core.export_utils.scheduler_export(
            scheduler,
            folder_name,
            aidge_export_cpp.ExportLibCpp,
            memory_manager=aidge_core.mem_info.generate_optimized_memory_info,
            memory_manager_args={"wrapping": False},
        )
        aidge_core.export_utils.generate_main_display_output_cpp(folder_name, model_prepared)

    with open("/dev/null", "w") as f, contextlib.redirect_stdout(f):
        run(["make"], cwd=folder_name, stdout=f)

    output_str: str = run(
        f"./{folder_name}/bin/run_export", capture_output=True, text=True
    )
    folder_path = os.path.abspath(folder_name)
    if os.path.exists(folder_path):
        rmtree(folder_path, ignore_errors=True)

    outputs_str: list[str] = output_str.stdout.strip().split("\n")
    outputs = [
        np.array([float(val) for val in single_output_str.split(" ") if val.strip()])
        for i, single_output_str in enumerate(outputs_str)
    ]
    output_tensors = []
    outputs_dims = [
        pair[0].get_operator().get_output(pair[1]).dims
        for pair in model_prepared.get_ordered_outputs()
    ]
    for out_idx, arr in enumerate(outputs):
        t = aidge_core.Tensor(arr.reshape(outputs_dims[out_idx]))
        t.to_dformat(aidge_core.dformat.nhwc)
        t.to_dformat(aidge_core.dformat.nchw)
        output_tensors.append(np.array(t))

    return output_tensors
