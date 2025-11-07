#ifndef __AIDGE_EXPORT_CPP_KERNELS_HARDMAX__
#define __AIDGE_EXPORT_CPP_KERNELS_HARDMAX__

#include "utils/cpp/typedefs.hpp"
#include "utils/cpp/utils.hpp"
#include <cstddef>

// Todo add border value and border type (Reflect, Constant, Wrap...) and add
// the two missing pad value (bottom and right)

namespace export_cpp {

template <size_t AXIS_DIM_SIZE,
          size_t PREAXIS_STRIDE,
          size_t AXIS_STRIDE,
          size_t POSTAXIS_STRIDE,
          size_t NB_ELTS,
          typename Input_T,
          typename Output_T>
// void HardmaxImpl_cpu_forward_kernel(std::int32_t axis_, const
// std::vector<DimSize_t>& dims, const void* input_, void* output_)
__attribute__((always_inline)) inline void
hardmax2d_forward(const Input_T *__restrict input,
                  Output_T *__restrict output) {

    // fill output with 0
    for (Output_T *i = output; i != output + NB_ELTS; ++i) {
        *i = 0;
    }

    // For each index on all the axes before and after 'axis', we have a
    // different max element to find
    for (size_t i = 0, preAxisOffset = 0; i < PREAXIS_STRIDE;
         ++i, preAxisOffset += AXIS_DIM_SIZE * POSTAXIS_STRIDE) {

        for (size_t j = 0; j < POSTAXIS_STRIDE; ++j) {
            // Init the max with first element
            size_t maxIdx = 0;
            Input_T maxVal = input[preAxisOffset + j];
            // Loop over the elements on 'axis'
            // Since we start at 0th idx, we already initialize the values like
            // the 1st iteration has been done
            for (size_t k = 1,
                              postAxisOffset = preAxisOffset + POSTAXIS_STRIDE;
                 k < AXIS_DIM_SIZE;
                 ++k, postAxisOffset += POSTAXIS_STRIDE) {

                Input_T currVal = input[postAxisOffset + j];
                // Update max elements
                if (currVal > maxVal) {
                    maxIdx = k;
                    maxVal = currVal;
                }
            }
            output[preAxisOffset + maxIdx * POSTAXIS_STRIDE + j] = 1;
        }
    }
}

} // namespace export_cpp

#endif // __AIDGE_EXPORT_CPP_KERNELS_HARDMAX__
