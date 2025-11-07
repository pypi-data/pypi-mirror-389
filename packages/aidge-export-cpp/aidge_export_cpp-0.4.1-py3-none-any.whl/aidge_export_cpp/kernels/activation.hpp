#ifndef __AIDGE_EXPORT_CPP_KERNELS_ACTIVATION__
#define __AIDGE_EXPORT_CPP_KERNELS_ACTIVATION__

#include "utils/cpp/activation_utils.hpp"
#include "utils/cpp/rescaling_utils.hpp"
#include <cstddef>

namespace export_cpp {

template<size_t NB_ELTS,
         ActivationFunction_T ACTIVATION,
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
         typename Sum_T,
         typename Input_T, typename Output_T, typename Rescaling_T>
__attribute__((always_inline)) inline
void activation_forward (
    const Input_T* __restrict inputs,
    Output_T* __restrict outputs,
    const Rescaling_T& __restrict rescaling)
{
    int inOffset = 0;
    int outOffset = 0;

    for (size_t i = 0; i < NB_ELTS; ++i) {
        if (INPUT_MEM_WRAP_SIZE > 0 && i == INPUT_MEM_CONT_SIZE / sizeof(Input_T)) {
            inOffset = (INPUT_MEM_WRAP_OFFSET - INPUT_MEM_CONT_OFFSET
                        - INPUT_MEM_CONT_SIZE) / static_cast<int>(sizeof(Input_T));
        }

        if (OUTPUT_MEM_WRAP_SIZE > 0 && i == OUTPUT_MEM_CONT_SIZE / sizeof(Output_T)) {
            outOffset = (OUTPUT_MEM_WRAP_OFFSET - OUTPUT_MEM_CONT_OFFSET
                        - OUTPUT_MEM_CONT_SIZE) / static_cast<int>(sizeof(Output_T));
        }

        outputs[outOffset + i] = activation_forward_value<Output_T>((Sum_T) inputs[inOffset + i], i, ACTIVATION, rescaling);
    }
}

} // namespace export_cpp

#endif  // __AIDGE_EXPORT_CPP_KERNELS_ACTIVATION__
