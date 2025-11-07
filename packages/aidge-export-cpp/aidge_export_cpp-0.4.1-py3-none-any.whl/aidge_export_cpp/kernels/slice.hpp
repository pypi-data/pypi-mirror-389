#ifndef __AIDGE_EXPORT_CPP_KERNELS_SLICE__
#define __AIDGE_EXPORT_CPP_KERNELS_SLICE__

#include "utils/cpp/typedefs.hpp"
#include <cstddef>

// Generic function for slice
// Note : implementation differs from cpu_backend's but this one uses no additional buffer.

namespace export_cpp {

template <typename T,
         size_t NB_DIMS, size_t NB_ELTS, size_t NB_AXES,
         const size_t STARTS[], const size_t ENDS[], const size_t STEPS[],
         const size_t AXES_MOD[], const size_t AXES_DIV[],
         typename Input_T, typename Output_T>
__attribute__((always_inline)) inline
void slice_forward (
    const Input_T* __restrict inputs,
    Output_T* __restrict outputs)
{
    // iterate on each element and check if it belongs into the slice
    size_t o = 0;
    for (size_t e=0; e<NB_ELTS; e++){
        bool is_sliced=true;
        for (size_t i=0; i<NB_AXES; i++){ // check for for each sliced ax
            const size_t ax_idx = (e % AXES_MOD[i]) / AXES_DIV[i];
            // check steps and boundaries
            if (((ax_idx - STARTS[i]) % STEPS[i] != 0) || (ax_idx < STARTS[i]) ||  (ax_idx >= ENDS[i])){
                is_sliced = false;
                break;
            }
        }
        // If the element is in the slice, copy it to output
        if (is_sliced){
            outputs[o] = inputs[e];
            o++;
        }
    }
}

} // namespace export_cpp

#endif  // __AIDGE_EXPORT_CPP_KERNELS_SLICE__