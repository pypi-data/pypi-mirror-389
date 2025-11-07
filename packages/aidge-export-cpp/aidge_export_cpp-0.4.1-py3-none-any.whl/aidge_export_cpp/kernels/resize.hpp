#ifndef __AIDGE_EXPORT_CPP_KERNELS_RESIZE__
#define __AIDGE_EXPORT_CPP_KERNELS_RESIZE__

#include "utils/cpp/typedefs.hpp"
#include "utils/cpp/utils.hpp"

namespace export_cpp {

template<int NB_CHANNELS, 
        int CHANNELS_HEIGHT, int CHANNELS_WIDTH,
        int NB_OUTPUTS,
        int OUTPUTS_HEIGHT, int OUTPUTS_WIDTH,
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
__attribute__((always_inline)) inline static void resize_forward(
        const Input_T* __restrict inputs,
        Output_T* __restrict outputs)
{
    for (int oy = 0; oy < OUTPUTS_HEIGHT; ++oy) {
        for (int ox = 0; ox < OUTPUTS_WIDTH; ++ox) {
            const int oPos = (ox + OUTPUTS_WIDTH * oy);
            int oOffset = OUTPUT_MEM_STRIDE * oPos;

            if (OUTPUT_MEM_WRAP_SIZE > 0 && oOffset >= OUTPUT_MEM_CONT_SIZE) {
                oOffset += OUTPUT_MEM_WRAP_OFFSET - OUTPUT_MEM_CONT_OFFSET
                            - OUTPUT_MEM_CONT_SIZE;
            }

            const int ix = ox * CHANNELS_WIDTH / OUTPUTS_WIDTH;
            const int iy = oy * CHANNELS_HEIGHT / OUTPUTS_HEIGHT;

            const int iPos = (ix + CHANNELS_WIDTH * iy);
            int iOffset = INPUT_MEM_STRIDE * iPos;

            if (INPUT_MEM_WRAP_SIZE > 0 && iOffset >= INPUT_MEM_CONT_SIZE) {
                iOffset += INPUT_MEM_WRAP_OFFSET - INPUT_MEM_CONT_OFFSET
                            - INPUT_MEM_CONT_SIZE;
            }

            for (int output = 0; output < NB_OUTPUTS; ++output) {
                outputs[oOffset + output] = inputs[iOffset + output];
            }
        }
    }
}

} // namespace export_cpp

#endif  // __AIDGE_EXPORT_CPP_KERNELS_RESIZE__
