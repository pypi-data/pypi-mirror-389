#ifndef __AIDGE_EXPORT_CPP_KERNELS_CONCAT__
#define __AIDGE_EXPORT_CPP_KERNELS_CONCAT__

#include <cstddef>

namespace export_cpp {

template<size_t AXIS_SIZE_POST,
         size_t AXIS_SIZE_PRE,
         const size_t AXIS_SIZE[],
         size_t TOTAL_AXIS_SIZE,
         size_t NB_INPUTS,
         typename T>
__attribute__((always_inline)) inline static
void concat_forward (
    const T* const * __restrict inputs,
    T* __restrict output)
{
    for (size_t i = 0; i < AXIS_SIZE_PRE; ++i) {
        // Loop over post-axis (e.g., dims after axis 1)
        for (size_t j = 0; j < AXIS_SIZE_POST; ++j) {
            size_t axis_offset = 0;

            // Loop over each input tensor
            for (size_t n = 0; n < NB_INPUTS; ++n) {
                for (size_t k = 0; k < AXIS_SIZE[n]; ++k) {
                    const size_t input_idx  = i * AXIS_SIZE[n] * AXIS_SIZE_POST + k * AXIS_SIZE_POST + j;

                    output[i * TOTAL_AXIS_SIZE * AXIS_SIZE_POST + (axis_offset + k) * AXIS_SIZE_POST + j] =
                        inputs[n][input_idx];
                }

                axis_offset += AXIS_SIZE[n];  // move along axis in output
            }
        }
    }
}

} // namespace export_cpp

#endif  // __AIDGE_EXPORT_CPP_KERNELS_CONCAT__