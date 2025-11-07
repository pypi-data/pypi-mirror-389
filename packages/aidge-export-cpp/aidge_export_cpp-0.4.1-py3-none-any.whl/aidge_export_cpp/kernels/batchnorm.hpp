#ifndef __AIDGE_EXPORT_CPP_KERNELS_BATCHNORM__
#define __AIDGE_EXPORT_CPP_KERNELS_BATCHNORM__

#include "utils/cpp/typedefs.hpp"
#include "utils/cpp/activation_utils.hpp"
#include <cstddef>
#include <math.h>

// WARNING: this kernel only works for 32-bits floating point values

namespace export_cpp {

template<size_t NB_BATCHES, size_t NB_OUTPUTS,
         size_t OUTPUTS_HEIGHT, size_t OUTPUTS_WIDTH,
         ActivationFunction_T ACTIVATION,
         typename Input_T, typename Output_T,
         typename Param_T,
         typename Rescaling_T>
__attribute__((always_inline)) inline
void batchnorm_forward (
    const Input_T* __restrict inputs,
    Output_T* __restrict outputs,
    const Param_T* __restrict scales,
    const Param_T* __restrict biases,
    const Param_T* __restrict means,
    const Param_T* __restrict variances,
    const double epsilon,
    const Rescaling_T& __restrict rescaling)
{
    for (size_t batch = 0; batch < NB_BATCHES; ++batch) {
        for (size_t output = 0; output < NB_OUTPUTS; ++output) {
            // If the variance is 0, we need to avoid division by 0
            Output_T var = sqrt(variances[output] > 0.0 ? variances[output] + epsilon : epsilon);

            for (size_t oy = 0; oy < OUTPUTS_HEIGHT; ++oy) {
                for (size_t ox = 0; ox < OUTPUTS_WIDTH; ++ox) {
                    const size_t outputOffset = batch * OUTPUTS_WIDTH * OUTPUTS_HEIGHT * NB_OUTPUTS + output * OUTPUTS_WIDTH * OUTPUTS_HEIGHT + OUTPUTS_WIDTH * oy + ox;

                    const Output_T normalized = (inputs[outputOffset] - means[output]) / var;
                    const Output_T sAs = scales[output] * normalized + biases[output];
                    outputs[outputOffset] = activation_forward_value<Output_T>(sAs, output, ACTIVATION, rescaling);
                }
            }
        }
    }
}

} // namespace export_cpp

#endif  // __AIDGE_EXPORT_CPP_KERNELS_BATCHNORM__
