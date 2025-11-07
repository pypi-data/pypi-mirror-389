#ifndef __AIDGE_EXPORT_CPP_KERNELS_REDUCEMEAN__
#define __AIDGE_EXPORT_CPP_KERNELS_REDUCEMEAN__

#include "utils/cpp/typedefs.hpp"
#include "utils/cpp/utils.hpp"
#include <cmath>
#include <type_traits>
#include <cstddef>

namespace export_cpp {

template <typename T>
using Acc_T =
    typename std::conditional_t<std::is_floating_point<T>::value, T, double>;

// computes iterative mean
template <typename T>
typename std::enable_if<std::is_floating_point<T>::value, T>::type
stableMean(const T *vec, std::size_t len, std::size_t stride) {
    T mean = 0;
    for (std::size_t i = 0; i < len; ++i) {
        mean = std::fma(vec[i * stride] - mean,
                        static_cast<T>(1) / static_cast<T>(i + 1),
                        mean);
    }
    return mean;
}

// Specialization for integers: perform the mean computation in float
template <typename T>
typename std::enable_if_t<!std::is_floating_point<T>::value, double>
stableMean(const T *vec, std::size_t len, std::size_t stride) {
    double mean = 0;
    for (size_t i = 0; i < len; ++i) {
        mean = std::fma<double>(static_cast<double>(vec[i * stride]) - mean,
                                1.0 / static_cast<double>(i + 1),
                                mean);
    }
    return mean;
}

template <typename T>
typename std::enable_if_t<std::is_floating_point<T>::value, T>
castFromFloat(T value) {
    return value;
}

template <typename T>
typename std::enable_if_t<!std::is_floating_point<T>::value, T>
castFromFloat(double value) {
    return static_cast<T>(std::nearbyint(value));
}

/**
 * @brief computes the mean of the tensor values over specified axis
 * This function can be called in a for loop to compute along different axes
 iteratively
 * @param[in] iDim : input dimensions of the tensor along axis to reduce
 * @param[in] preAxisNbElts : nb of elements on each axis before the axis to
 reduce.
 * @param[in] postAxisNbElts : nb of elements on each axis after the axis to
 reduce
 * @param[in] axisNbElts : nb of elements on the axis to reduce
 * @param[inout] prevAcc: Values returned by previous computation, if 1st
 * iteration, its the input tensor.
 * @param[inout] currAcc: output of computation : tensor with averaged
 values
 * along given axis
 */
template <typename Input_T, typename Output_T>
Output_T *computeMeanOverAxis(const size_t preAxisNbElts,
                              const size_t postAxisNbElts,
                              const size_t axisNbElts,
                              const size_t iDim,
                              const Input_T *__restrict__ prevAcc,
                              Output_T *currAcc) {
    for (size_t preAxisIdx = 0, iPreAxisOffset = 0, oPreAxisOffset = 0;
         preAxisIdx < preAxisNbElts;
         ++preAxisIdx,
                     iPreAxisOffset += axisNbElts,
                     oPreAxisOffset += postAxisNbElts) {

        for (size_t postAxisIdx = 0; postAxisIdx < postAxisNbElts;
             ++postAxisIdx) {
            currAcc[oPreAxisOffset + postAxisIdx] = castFromFloat<Output_T>(
                stableMean(prevAcc + iPreAxisOffset + postAxisIdx,
                           iDim,
                           postAxisNbElts));
        }
    }
    return currAcc;
}

template <size_t IN_NB_DIMS,
          size_t IN_NB_ELTS,
          size_t OUT_NB_ELTS,
          size_t NB_AXES_TO_REDUCE,
          typename Input_T,
          typename Output_T>
__attribute__((always_inline)) inline void
reducemean_forward(const size_t axesToReduce[NB_AXES_TO_REDUCE],
                   const size_t iDims[IN_NB_DIMS],
                   const size_t preAxisStrides[IN_NB_DIMS],
                   const size_t postAxisStrides[IN_NB_DIMS],
                   const Input_T *__restrict input,
                   Output_T *__restrict output) {

    switch (NB_AXES_TO_REDUCE) {
    case 0: {
        copy_n(input, IN_NB_ELTS, output);
        break;
    }
    case 1: {
        output = computeMeanOverAxis<Input_T, Output_T>(
            preAxisStrides[axesToReduce[0]],
            postAxisStrides[axesToReduce[0]],
            iDims[axesToReduce[0]] * postAxisStrides[axesToReduce[0]],
            iDims[axesToReduce[0]],
            input,
            output);
        break;
    }
    default: {

        // the set up for th elfor loop is basically just unrolling the 1st
        // iteration.
        size_t outputElements = IN_NB_ELTS / iDims[axesToReduce[0]];
        Acc_T<Output_T> *currAcc = new Acc_T<Input_T>[outputElements];
        Acc_T<Input_T> *prevAcc = nullptr;
        prevAcc = computeMeanOverAxis<Input_T, Output_T>(
            preAxisStrides[axesToReduce[0]],
            postAxisStrides[axesToReduce[0]],
            iDims[axesToReduce[0]] * postAxisStrides[axesToReduce[0]],
            iDims[axesToReduce[0]],
            input,
            currAcc);

        // mutable copy of preAxisStride to avoid modifying input values
        size_t preAxisStrides_mut[IN_NB_DIMS];
        for (size_t i = 0; i < IN_NB_DIMS; ++i) {
            preAxisStrides_mut[i] =
                i < axesToReduce[0] + 1
                    ? preAxisStrides[i]
                    : preAxisStrides[i] / iDims[axesToReduce[0]];
        }

        for (size_t i = 1; i < NB_AXES_TO_REDUCE; ++i) {
            const size_t axis = axesToReduce[i];
            outputElements /= iDims[i];
            currAcc = new Acc_T<Input_T>[outputElements];
            currAcc = computeMeanOverAxis<Acc_T<Input_T>, Acc_T<Output_T>>(
                preAxisStrides_mut[axis],
                postAxisStrides[axis],
                iDims[axis] * postAxisStrides[axis],
                iDims[axis],
                prevAcc,
                currAcc);

            for (size_t j = axis + 1; j < IN_NB_DIMS; ++j) {
                preAxisStrides_mut[j] /= iDims[axis];
            }
            delete[] prevAcc;
            prevAcc = currAcc;
        }

        for (size_t i = 0; i < OUT_NB_ELTS; ++i) {
            output[i] = castFromFloat<Output_T>(currAcc[i]);
        }

        if (currAcc) {
            delete[] currAcc;
        }
    }
    }
}

} // namespace export_cpp

#endif // __AIDGE_EXPORT_CPP_KERNELS_REDUCEMEAN__
