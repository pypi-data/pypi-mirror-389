#ifndef __AIDGE_EXPORT_CPP_KERNELS_SQRT__
#define __AIDGE_EXPORT_CPP_KERNELS_SQRT__

#include "utils/cpp/typedefs.hpp"
#include <cstddef>

// Generic function for sqrt

using namespace export_cpp;

template<size_t NB_ELTS,
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
void sqrt_forward (
    const Input_T* __restrict inputs,
    Output_T* __restrict outputs)
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

        outputs[outOffset + i] = sqrt(inputs[inOffset + i]);
    }
}

#endif  // __AIDGE_EXPORT_CPP_KERNELS_SQRT__