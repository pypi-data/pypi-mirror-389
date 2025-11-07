#ifndef __AIDGE_EXPORT_CPP_KERNELS_MATMUL__
#define __AIDGE_EXPORT_CPP_KERNELS_MATMUL__

#include "utils/cpp/typedefs.hpp"
#include "utils/cpp/activation_utils.hpp"
#include <cstddef>

// Generic function for matmul and activation

namespace export_cpp {

template<size_t NB_MAT, size_t N, size_t M, size_t K,
        const size_t OFFSET_IN1[], const size_t OFFSET_IN2[],
        ActivationFunction_T ACTIVATION,
        typename Input_T, typename Output_T, typename Rescaling_T>
__attribute__((always_inline)) inline
void matmul_forward (
    const Input_T* __restrict inputs1,
    const Input_T* __restrict inputs2,
    Output_T* __restrict outputs,
    const Rescaling_T& __restrict rescaling)
{
    for (size_t stack = 0; stack < NB_MAT; ++stack) {
        const size_t offset1 = OFFSET_IN1[stack] * N * K;
        const size_t offset2 = OFFSET_IN2[stack] * K * M;
        Output_T* out_ptr = &outputs[stack * N * M];

        for (size_t i = 0; i < N; ++i) {
            const Output_T* in1_row = &inputs1[offset1 + i * K];

            for (size_t j = 0; j < M; ++j) {
                Output_T sum = 0;

                // Access column of inputs2 as row-major
                for (size_t l = 0; l < K; ++l) {
                    sum += in1_row[l] * inputs2[offset2 + l * M + j];
                }

                out_ptr[i * M + j] = activation_forward_value<Output_T>(
                    sum, 0 /* not applicable */, ACTIVATION, rescaling
                );
            }
        }
    }
}

} // namespace export_cpp

#endif  // __AIDGE_EXPORT_CPP_KERNELS_MATMUL__