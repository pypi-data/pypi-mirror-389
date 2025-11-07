#ifndef __AIDGE_EXPORT_CPP_KERNELS_IDENTITY__
#define __AIDGE_EXPORT_CPP_KERNELS_IDENTITY__

#include "utils/cpp/typedefs.hpp"
#include <cstddef>

// Generic function for identity and activation

namespace export_cpp {

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
void identity_forward (
    const Input_T* __restrict inputs,
    Output_T* __restrict outputs)
{
    // If inputs and outputs pointers are the same, the memory manager has already optimized this function so it is a no-op !
    if (inputs == outputs)
        return;

    int inOffset = 0;
    int outOffset = 0;

    // A identity in c++ world should equal to a Noop
    // We only need to copy the input buffer to the output
    for (size_t i = 0; i < NB_ELTS; ++i) {
        if (INPUT_MEM_WRAP_SIZE > 0 && i == INPUT_MEM_CONT_SIZE / sizeof(Input_T)) {
            inOffset = (INPUT_MEM_WRAP_OFFSET - INPUT_MEM_CONT_OFFSET
                        - INPUT_MEM_CONT_SIZE) / static_cast<int>(sizeof(Input_T));
        }

        if (OUTPUT_MEM_WRAP_SIZE > 0 && i == OUTPUT_MEM_CONT_SIZE / sizeof(Output_T)) {
            outOffset = (OUTPUT_MEM_WRAP_OFFSET - OUTPUT_MEM_CONT_OFFSET
                        - OUTPUT_MEM_CONT_SIZE) / static_cast<int>(sizeof(Output_T));
        }

        outputs[outOffset + i] = inputs[inOffset + i];
    }
}

} // namespace export_cpp

#endif  // __AIDGE_EXPORT_CPP_KERNELS_IDENTITY__