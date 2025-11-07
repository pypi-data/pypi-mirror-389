#ifndef __AIDGE_EXPORT_CPP_KERNELS_SOFTMAX__
#define __AIDGE_EXPORT_CPP_KERNELS_SOFTMAX__

#include "utils/cpp/typedefs.hpp"
#include "utils/cpp/utils.hpp"

#include <type_traits>
#include <cmath>
#include <algorithm>
#include <cstddef>

namespace export_cpp {

template<size_t AXIS_SIZE,
         size_t AXIS_SIZE_POST,
         size_t AXIS_SIZE_PRE,
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
         int OUTPUT_MEM_STRIDE,
         typename Input_T, typename Output_T>
__attribute__((always_inline)) inline
void softmax_forward (
    const Input_T* __restrict inputs,
    Output_T* __restrict outputs)
{
    // Iterate over the "pre-axis" and "post-axis" slices.
    // For each slice along the axis, compute the maximum value,
    // the sum of exponentials, and then write the normalized softmax outputs.
    for (size_t i = 0; i < AXIS_SIZE_PRE; ++i) {
        for (size_t j = 0; j < AXIS_SIZE_POST; ++j) {
            // Compute the base index for this slice.
            const size_t baseIdx = i * AXIS_SIZE * AXIS_SIZE_POST + j;

            // Find the maximum value along the axis.
            Input_T maxVal = inputs[baseIdx];
            for (size_t k = 1; k < AXIS_SIZE; ++k) {
                int inIdx = baseIdx + k * AXIS_SIZE_POST;

                if (INPUT_MEM_WRAP_SIZE > 0 && inIdx >= INPUT_MEM_CONT_SIZE / static_cast<int>(sizeof(Input_T))) {
                    inIdx += (INPUT_MEM_WRAP_OFFSET - INPUT_MEM_CONT_OFFSET
                                - INPUT_MEM_CONT_SIZE) / static_cast<int>(sizeof(Input_T));
                }

                maxVal = std::max(maxVal, inputs[inIdx]);
            }

            // Compute the sum of the exponentials along the axis.
            Input_T sumExp = 0;
            for (size_t k = 0; k < AXIS_SIZE; ++k) {
                int inIdx = baseIdx + k * AXIS_SIZE_POST;
                int outIdx = inIdx;

                if (INPUT_MEM_WRAP_SIZE > 0 && inIdx >= INPUT_MEM_CONT_SIZE / static_cast<int>(sizeof(Input_T))) {
                    inIdx += (INPUT_MEM_WRAP_OFFSET - INPUT_MEM_CONT_OFFSET
                                - INPUT_MEM_CONT_SIZE) / static_cast<int>(sizeof(Input_T));
                }

                if (OUTPUT_MEM_WRAP_SIZE > 0 && outIdx >= OUTPUT_MEM_CONT_SIZE / static_cast<int>(sizeof(Output_T))) {
                    outIdx += (OUTPUT_MEM_WRAP_OFFSET - OUTPUT_MEM_CONT_OFFSET
                                - OUTPUT_MEM_CONT_SIZE) / static_cast<int>(sizeof(Output_T));
                }

                outputs[outIdx] = std::exp(inputs[inIdx] - maxVal);
                sumExp += outputs[outIdx];
            }

            // Write the softmax values to the output.
            for (size_t k = 0; k < AXIS_SIZE; ++k) {
                int inIdx = baseIdx + k * AXIS_SIZE_POST;
                int outIdx = inIdx;

                if (INPUT_MEM_WRAP_SIZE > 0 && inIdx >= INPUT_MEM_CONT_SIZE / static_cast<int>(sizeof(Input_T))) {
                    inIdx += (INPUT_MEM_WRAP_OFFSET - INPUT_MEM_CONT_OFFSET
                                - INPUT_MEM_CONT_SIZE) / static_cast<int>(sizeof(Input_T));
                }

                if (OUTPUT_MEM_WRAP_SIZE > 0 && outIdx >= OUTPUT_MEM_CONT_SIZE / static_cast<int>(sizeof(Output_T))) {
                    outIdx += (OUTPUT_MEM_WRAP_OFFSET - OUTPUT_MEM_CONT_OFFSET
                                - OUTPUT_MEM_CONT_SIZE) / static_cast<int>(sizeof(Output_T));
                }

                outputs[outIdx] /= sumExp;
            }
        }
    }
}

} // namespace export_cpp

#endif  // __AIDGE_EXPORT_CPP_KERNELS_SOFTMAX__
