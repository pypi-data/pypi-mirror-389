#ifndef __AIDGE_EXPORT_CPP_KERNELS_ERP__
#define __AIDGE_EXPORT_CPP_KERNELS_ERP__

#include "utils/cpp/typedefs.hpp"
#include "math.h"
#include <cstddef>

namespace export_cpp {

template<size_t NB_ELTS,
         typename Input_T, typename Output_T>
__attribute__((always_inline)) inline 
void erf_forward (
    const Input_T* __restrict inputs,
    Output_T* __restrict outputs)
{
    constexpr double a1 =  0.254829592;
    constexpr double a2 = -0.284496736;
    constexpr double a3 =  1.421413741;
    constexpr double a4 = -1.453152027;
    constexpr double a5 =  1.061405429;
    constexpr double p  =  0.3275911;

    #ifdef _OPENMP
    #pragma omp parallel for
    #endif
    for (size_t i = 0; i < NB_ELTS; ++i) {
        int sign = 1;
        if (inputs[i] < 0)
            sign = -1;
        const double abs_value = abs(inputs[i]);
        
        // A&S formula 7.1.26
        const double t = 1.0/(1.0 + p*abs_value);
        const double y = 1.0 - (((((a5*t + a4)*t) + a3)*t + a2)*t + a1)*t*exp(-abs_value*abs_value);
        outputs[i] = sign*y;

    }
}

} // namespace export_cpp

#endif  // __AIDGE_EXPORT_CPP_KERNELS_ERP_