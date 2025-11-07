#ifndef __AIDGE_EXPORT_CPP_ACTIVATION_UTILS_HPP__
#define __AIDGE_EXPORT_CPP_ACTIVATION_UTILS_HPP__

#include <type_traits>
#include "utils/cpp/typedefs.hpp"
#include "utils/cpp/utils.hpp"
#include "utils/cpp/rescaling_utils.hpp"

namespace export_cpp {

template<typename Output_T, typename T,
         typename std::enable_if<std::is_floating_point<T>::value>::type* = nullptr>
__attribute__((always_inline)) inline
Output_T saturate (T value, int32_t /*sat*/)
{
    return value;
}

template<typename Output_T, typename T,
         typename std::enable_if<!std::is_floating_point<T>::value>::type* = nullptr>
__attribute__((always_inline)) inline
Output_T saturate (T value, uint32_t sat)
{
    if (std::is_unsigned<Output_T>::value) {
        return clamp(value, T(0), (T(1) << sat) - 1);
    } else {
        return clamp(value, -(T(1) << (sat - 1)), (T(1) << (sat - 1)) - 1);
    }
}

template<typename Output_T,
         typename Sum_T,
         typename Rescaling_T>
__attribute__((always_inline)) inline
Output_T activation_forward_value (Sum_T weightedSum,
                                   int output,
                                   ActivationFunction_T func,
                                   const Rescaling_T& __restrict rescaling)
{
    switch(func) {
        case ActivationFunction_T::Linear:
        case ActivationFunction_T::Saturation: {
            break;
        }
        case ActivationFunction_T::Rectifier: {
            if(weightedSum <= 0) 
                weightedSum = 0;
            break;
        }
        default:
            // Unsupported activation function
            break;
    }

    return saturate<Output_T>(rescaling(weightedSum, output), 8 * sizeof(Output_T));
}

};  // namespace export_cpp

#endif
