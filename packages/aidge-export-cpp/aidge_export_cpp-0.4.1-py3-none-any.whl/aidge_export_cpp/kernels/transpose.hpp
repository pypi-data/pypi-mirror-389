/********************************************************************************
 * Copyright (c) 2023 CEA-List
 *
 * This program and the accompanying materials are made available under the
 * terms of the Eclipse Public License 2.0 which is available at
 * http://www.eclipse.org/legal/epl-2.0.
 *
 * SPDX-License-Identifier: EPL-2.0
 *
 ********************************************************************************/

#ifndef __AIDGE_EXPORT_CPP_KERNELS_TRANSPOSE__
#define __AIDGE_EXPORT_CPP_KERNELS_TRANSPOSE__

#include <cstddef>

namespace export_cpp {

/**
 * @brief Transposes an N-dimensional tensor based on the specified permutation.
 *
 * This function rearranges the dimensions of an N-dimensional tensor according to the
 * permutation array provided. The input tensor is expected to have dimensions specified
 * by `in_dims`, and the output tensor will have dimensions reordered as specified by the
 * `permute` array.
 *
 * Based on Tensor::copyTranspose from aidge.aidge_core
 *
 * @tparam T        Data type of the tensor elements.
 * @tparam NB_DIMS  Number of dimensions of the input tensor.
 * @param[in]  inputs      Pointer to the input tensor data stored in contiguous memory.
 * @param[out] outputs     Pointer to the pre-allocated memory for the transposed tensor.
 *                         Ensure this memory is appropriately sized to hold the transposed data.
 */
template <typename T,
    size_t NB_DIMS,
    size_t NB_ELTS,
    const size_t PERMUTE[],
    const size_t IN_DIMS[],
    const size_t OUT_STRIDE[],
    // Memory mapping: inputs
    int INPUT_MEM_CONT_OFFSET,
    int INPUT_MEM_CONT_SIZE,
    int INPUT_MEM_WRAP_OFFSET,
    int INPUT_MEM_WRAP_SIZE,
    int INPUT_MEM_STRIDE,
    // Memory mapping: outputs
    int OUTPUT_MEM_CONT_OFFSET,
    int OUTPUT_MEM_CONT_SIZE,
    int OUTPUT_MEM_WRAP_OFFSET,
    int OUTPUT_MEM_WRAP_SIZE,
    int OUTPUT_MEM_STRIDE>
__attribute__((always_inline)) inline
void transpose_ND_forward(const T *__restrict inputs,
                          T *__restrict outputs)
{
    int inOffset = 0;
    size_t current_idx[NB_DIMS] = {0};

    // Iterate over all elements in the input tensor
    for (size_t idx = 0; idx < NB_ELTS; ++idx) {
        // Compute output index using current_idx
        int output_index = 0;
        for (size_t i = 0; i < NB_DIMS; ++i) {
            output_index += current_idx[PERMUTE[i]] * OUT_STRIDE[i];
        }

        if (INPUT_MEM_WRAP_SIZE > 0 && idx == INPUT_MEM_CONT_SIZE / sizeof(T)) {
            inOffset = (INPUT_MEM_WRAP_OFFSET - INPUT_MEM_CONT_OFFSET
                        - INPUT_MEM_CONT_SIZE) / static_cast<int>(sizeof(T));
        }

        if (OUTPUT_MEM_WRAP_SIZE > 0 && output_index >= OUTPUT_MEM_CONT_SIZE / static_cast<int>(sizeof(T))) {
            output_index += (OUTPUT_MEM_WRAP_OFFSET - OUTPUT_MEM_CONT_OFFSET
                        - OUTPUT_MEM_CONT_SIZE) / static_cast<int>(sizeof(T));
        }

        outputs[output_index] = inputs[inOffset + idx];

        // Increment current_idx as a multidimensional counter
        for (int i = NB_DIMS - 1; i >= 0; --i) {
            if (++current_idx[i] < IN_DIMS[i]) {
                break;
            }
            else {
                current_idx[i] = 0;
            }
        }
    }
}

} // namespace export_cpp

#endif // __AIDGE_EXPORT_CPP_KERNELS_TRANSPOSE__
