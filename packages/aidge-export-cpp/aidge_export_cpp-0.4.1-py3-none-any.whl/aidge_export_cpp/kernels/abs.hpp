#ifndef AIDGE_EXPORT_CPP_KERNELS_ABS_
#define AIDGE_EXPORT_CPP_KERNELS_ABS_

#include "utils/cpp/typedefs.hpp"
#include <cstddef> // std::size_t
#include <type_traits> // std::enable_if, std::is_same, std::is_signed, std::is_unsigned

using namespace export_cpp;

template <std::size_t NB_ELTS,
          typename Input_T,
          typename Output_T,
          std::enable_if_t<!std::is_same<Input_T, Output_T>::value, bool> = true,
          std::enable_if_t<std::is_signed<Input_T>::value, bool> = true>
inline void abs_forward(const Input_T *__restrict inputs,
                        Output_T *__restrict outputs) {
#ifdef _OPENMP
#pragma omp parallel for
#endif
    for (std::size_t i = 0; i < NB_ELTS; ++i) {
        outputs[i] = (inputs[i] < 0) ? static_cast<Output_T>(-inputs[i])
                                     : static_cast<Output_T>(inputs)[i];
    }
}

template <std::size_t NB_ELTS,
          typename Input_T,
          typename Output_T,
          std::enable_if_t<!std::is_same<Input_T, Output_T>::value, bool> = true,
          std::enable_if_t<std::is_unsigned<Input_T>::value, bool> = true>
inline void abs_forward(const Input_T *__restrict inputs,
                        Output_T *__restrict outputs) {
#ifdef _OPENMP
#pragma omp parallel for
#endif
    for (std::size_t i = 0; i < NB_ELTS; ++i) {
        outputs[i] = static_cast<Output_T>(inputs[i]);
    }
}

template <std::size_t NB_ELTS,
          typename Input_T,
          typename Output_T,
          std::enable_if_t<std::is_same<Input_T, Output_T>::value, bool> = true,
          std::enable_if_t<std::is_signed<Input_T>::value, bool> = true>
inline void abs_forward(const Input_T *__restrict inputs,
                        Output_T *__restrict outputs) {
#ifdef _OPENMP
#pragma omp parallel for
#endif
    for (std::size_t i = 0; i < NB_ELTS; ++i) {
        outputs[i] = (inputs[i] < 0) ? -inputs[i] : inputs[i];
    }
}

template <std::size_t NB_ELTS,
          typename Input_T,
          typename Output_T,
          std::enable_if_t<std::is_same<Input_T, Output_T>::value, bool> = true,
          std::enable_if_t<std::is_unsigned<Input_T>::value, bool> = true>
inline void abs_forward(const Input_T *__restrict inputs,
                        Output_T *__restrict outputs) {
#ifdef _OPENMP
#pragma omp parallel for
#endif
    for (std::size_t i = 0; i < NB_ELTS; ++i) {
        outputs[i] = inputs[i];
    }
}

#endif // AIDGE_EXPORT_CPP_KERNELS_ABS_
