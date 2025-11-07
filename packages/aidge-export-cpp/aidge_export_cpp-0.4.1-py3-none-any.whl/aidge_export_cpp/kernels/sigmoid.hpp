#ifndef __AIDGE_EXPORT_CPP_KERNELS_SIGMOID__
#define __AIDGE_EXPORT_CPP_KERNELS_SIGMOID__

#include "utils/cpp/typedefs.hpp"
#include <cmath>
#include <array>
#include <algorithm>
#include <limits>
#include <cstdint>
#include <cstddef>

namespace export_cpp {

template <typename Input_T, class Output_T, size_t LUT_IDX, size_t LUT_SIZE>
constexpr Input_T sigmoid_index()
{
    constexpr auto unitVal = std::numeric_limits<typename std::make_unsigned<Output_T>::type>::max();
    constexpr auto y = 0.5f + 0.5f * static_cast<float>(LUT_IDX) / LUT_SIZE;
    constexpr auto x = std::log(y) - std::log(1.0f - y);
    return unitVal * x;
}

template <typename Input_T, typename Output_T, std::size_t... I>
constexpr auto sigmoid_lookup_helper(std::index_sequence<I...>)
{
    return std::array<Input_T, sizeof...(I)>({sigmoid_index<Input_T, Output_T, I, sizeof...(I)>()...});
}

template <typename Input_T, typename Output_T, size_t LUT_Size>
constexpr auto sigmoid_lookup()
{
    return sigmoid_lookup_helper<Input_T, Output_T>(std::make_index_sequence<LUT_Size>());
}

template <typename Output_T, size_t LUT_SIZE>
constexpr Output_T sigmoid_scale_idx(size_t idx, bool pos) {
    constexpr auto midVal = (std::numeric_limits<Output_T>::max() + 1) / 2;
    return (pos) ? midVal + (midVal*idx) / LUT_SIZE - 1 : midVal - (midVal*idx) / LUT_SIZE;
}

template<size_t NB_ELTS,
         typename Input_T, typename Output_T>
__attribute__((always_inline)) inline 
typename std::enable_if<std::is_floating_point<Input_T>::value || std::is_floating_point<Output_T>::value, void>::type
sigmoid_forward (
    const Input_T* __restrict inputs,
    Output_T* __restrict outputs)
{
    for (size_t i = 0; i < NB_ELTS; ++i) {
        if (inputs[i] > Input_T(0)) {
            outputs[i] = Output_T(1) / (Output_T(1) + std::exp(-inputs[i]));
        }
        else {
            outputs[i] = std::exp(inputs[i]) / (Output_T(1) + std::exp(inputs[i]));
        }
    }
}

template<size_t NB_ELTS,
         typename Input_T, typename Output_T>
__attribute__((always_inline)) inline 
typename std::enable_if<!std::is_floating_point<Input_T>::value && !std::is_floating_point<Output_T>::value, void>::type
sigmoid_forward (
    const Input_T* __restrict inputs,
    Output_T* __restrict outputs)
{
    constexpr size_t LUT_Size = 1 << (8 * sizeof(Output_T) - 1);
    static constexpr auto lut = sigmoid_lookup<Input_T, Output_T, LUT_Size>();

    for (size_t i = 0; i < NB_ELTS; ++i) {
        const auto it = std::lower_bound(std::begin(lut), std::end(lut), std::abs(inputs[i]));
        const auto idx = std::distance(std::begin(lut), it);
        outputs[i] = sigmoid_scale_idx<Output_T, LUT_Size>(idx, inputs[i] > 0);
    }
}

} // namespace export_cpp

#endif  // __AIDGE_EXPORT_CPP_KERNELS_SIGMOID__
