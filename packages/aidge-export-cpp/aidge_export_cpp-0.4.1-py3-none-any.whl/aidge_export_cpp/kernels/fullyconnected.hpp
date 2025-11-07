#ifndef __AIDGE_EXPORT_CPP_KERNELS_FULLYCONNECTED__
#define __AIDGE_EXPORT_CPP_KERNELS_FULLYCONNECTED__

#include "utils/cpp/typedefs.hpp"
#include "utils/cpp/rescaling_utils.hpp"
#include "utils/cpp/utils.hpp"
#include "utils/cpp/macs.hpp"
#include "utils/cpp/activation_utils.hpp"
#include <cstddef>

namespace export_cpp {

/**
 * @brief Kernel to use when the input is in the NHWC format, and the
 * weights have been transposed accordingly.
 */
template<size_t NB_CHANNELS,
         size_t CHANNELS_HEIGHT, size_t CHANNELS_WIDTH,
         size_t NB_OUTPUTS,
         size_t OUTPUTS_HEIGHT, size_t OUTPUTS_WIDTH,
         ActivationFunction_T ACTIVATION,
         // Memory mapping: inputs
         int INPUT_MEM_CONT_OFFSET,
         int INPUT_MEM_CONT_SIZE,
         int INPUT_MEM_WRAP_OFFSET,
         int INPUT_MEM_WRAP_SIZE,
         int INPUT_MEM_STRIDE,
         // Memory mapping: outputs
         int OUTPUT_MEM_CONT_OFFSET,
         int OUTPUT_MEM_CONT_SIZE,
         int OUTPUT_MEM_WRAP_OFFSET,
         int OUTPUT_MEM_WRAP_SIZE,
         int OUTPUT_MEM_STRIDE,
         typename Input_T, typename Output_T,
         typename Weight_T, typename Bias_T,
         typename Rescaling_T>
__attribute__((always_inline)) inline
void fullyconnected_forward (
    const Input_T* __restrict inputs,
    Output_T* __restrict outputs,
    const Weight_T* __restrict weights,
    const Bias_T* __restrict biases,
    const Rescaling_T& __restrict rescaling)
{
    constexpr size_t NB_W_CHANNELS_PACKED = (NB_CHANNELS + n_pack<Weight_T>() - 1) / n_pack<Weight_T>();

    constexpr size_t NB_OUTPUTS_PACKED = (NB_OUTPUTS + n_pack<Output_T>() - 1) / n_pack<Output_T>();
    constexpr size_t NB_OUTPUTS_REM = NB_OUTPUTS % n_pack<Output_T>();

#ifdef _OPENMP
#pragma omp parallel for
#endif
    for (size_t outputPack = 0; outputPack < NB_OUTPUTS_PACKED; ++outputPack) {
        Output_T packedOutputVal;

        for (size_t packElt = 0; packElt < n_pack<Output_T>(); ++packElt) {
            if (NB_OUTPUTS_REM != 0 && packElt == NB_OUTPUTS_REM) {
                break;
            }

            const size_t och = outputPack * n_pack<Output_T>() + packElt;

            Bias_T weightedSum = (biases) ? biases[och] : Bias_T(0);

            for (size_t iy = 0; iy < CHANNELS_HEIGHT; ++iy) {
                const int iPos = (CHANNELS_WIDTH * iy);
                int iOffset = (INPUT_MEM_STRIDE / sizeof(Input_T)) * iPos;

                // Wrapping cannot occur in the middle of a line, except if
                // there is only one line (1D)!
                bool wrapInRange = false;

                if (INPUT_MEM_WRAP_SIZE > 0 && iOffset >= INPUT_MEM_CONT_SIZE / static_cast<int>(sizeof(Input_T))) {
                    iOffset += (INPUT_MEM_WRAP_OFFSET - INPUT_MEM_CONT_OFFSET
                                - INPUT_MEM_CONT_SIZE) / static_cast<int>(sizeof(Input_T));
                }
                else if (INPUT_MEM_WRAP_SIZE > 0 && CHANNELS_WIDTH > 1
                    && CHANNELS_HEIGHT == 1 // single line (1D)!
                    && iOffset + CHANNELS_WIDTH * NB_CHANNELS
                        > (INPUT_MEM_CONT_SIZE / static_cast<int>(sizeof(Input_T))))
                {
                    wrapInRange = true;
                }

                const size_t wOffset = NB_W_CHANNELS_PACKED * CHANNELS_WIDTH
                                        * (iy + CHANNELS_HEIGHT * och);

                if (!wrapInRange && (INPUT_MEM_STRIDE / sizeof(Input_T)) == NB_CHANNELS) {
                    macsOnRange<NB_CHANNELS * CHANNELS_WIDTH>(
                        inputs + iOffset,
                        weights + wOffset,
                        weightedSum);
                }
                else {
                    for (size_t ix = 0; ix < CHANNELS_WIDTH; ++ix) {
                        int iOffsetInRange = iOffset + ix * (INPUT_MEM_STRIDE / sizeof(Input_T));

                        if (wrapInRange
                            && iOffsetInRange >= INPUT_MEM_CONT_SIZE / static_cast<int>(sizeof(Input_T)))
                        {
                            iOffsetInRange += (INPUT_MEM_WRAP_OFFSET
                                        - INPUT_MEM_CONT_OFFSET
                                        - INPUT_MEM_CONT_SIZE) / static_cast<int>(sizeof(Input_T));
                        }

                        macsOnRange<NB_CHANNELS>(
                            inputs + iOffsetInRange,
                            weights + wOffset + ix * NB_W_CHANNELS_PACKED,
                            weightedSum);
                    }
                }
            }

            const auto outputVal
                = activation_forward_value<Output_T>(weightedSum, och, ACTIVATION, rescaling);
            pack_rev_set(packedOutputVal, packElt, outputVal);
        }

        outputs[outputPack] = packedOutputVal;
    }
}

/**
 * @brief Kernel to use when the input is in the NCHW or Default format
 * format (4D or 2D).
 */
template<size_t NB_CHANNELS,
         size_t CHANNELS_HEIGHT, size_t CHANNELS_WIDTH,
         size_t NB_OUTPUTS,
         size_t OUTPUTS_HEIGHT, size_t OUTPUTS_WIDTH,
         ActivationFunction_T ACTIVATION,
         // Memory mapping: inputs
         int INPUT_MEM_CONT_OFFSET,
         int INPUT_MEM_CONT_SIZE,
         int INPUT_MEM_WRAP_OFFSET,
         int INPUT_MEM_WRAP_SIZE,
         int INPUT_MEM_STRIDE,
         // Memory mapping: outputs
         int OUTPUT_MEM_CONT_OFFSET,
         int OUTPUT_MEM_CONT_SIZE,
         int OUTPUT_MEM_WRAP_OFFSET,
         int OUTPUT_MEM_WRAP_SIZE,
         int OUTPUT_MEM_STRIDE,
         typename Input_T, typename Output_T,
         typename Weight_T, typename Bias_T,
         typename Rescaling_T>
__attribute__((always_inline)) inline
void fullyconnected_default_forward (
    const Input_T* __restrict inputs,
    Output_T* __restrict outputs,
    const Weight_T* __restrict weights,
    const Bias_T* __restrict biases,
    const Rescaling_T& __restrict rescaling)
{
    constexpr size_t NB_W_CHANNELS_PACKED = (NB_CHANNELS + n_pack<Weight_T>() - 1) / n_pack<Weight_T>();
    constexpr size_t WEIGHT_SPATIAL_SIZE = CHANNELS_WIDTH * CHANNELS_HEIGHT;

    constexpr size_t NB_OUTPUTS_PACKED = (NB_OUTPUTS + n_pack<Output_T>() - 1) / n_pack<Output_T>();
    constexpr size_t NB_OUTPUTS_REM = NB_OUTPUTS % n_pack<Output_T>();

#ifdef _OPENMP
#pragma omp parallel for
#endif
    for (size_t outputPack = 0; outputPack < NB_OUTPUTS_PACKED; ++outputPack) {
        Output_T packedOutputVal;

        for (size_t packElt = 0; packElt < n_pack<Output_T>(); ++packElt) {
            if (NB_OUTPUTS_REM != 0 && packElt == NB_OUTPUTS_REM) {
                break;
            }

            const size_t och = outputPack * n_pack<Output_T>() + packElt;

            Bias_T weightedSum = (biases) ? biases[och] : Bias_T(0);

            const size_t wOffset = NB_W_CHANNELS_PACKED * WEIGHT_SPATIAL_SIZE * och;

            if (INPUT_MEM_WRAP_SIZE > 0) {
                if (INPUT_MEM_CONT_SIZE > 0) {
                    macsOnRange<INPUT_MEM_CONT_SIZE / sizeof(Input_T)>(
                        inputs,
                        weights + wOffset,
                        weightedSum);
                }

                const size_t wWrapOffset = wOffset + NB_W_CHANNELS_PACKED * INPUT_MEM_CONT_SIZE / NB_CHANNELS / sizeof(Input_T);
                const int iOffset = (INPUT_MEM_WRAP_OFFSET - INPUT_MEM_CONT_OFFSET)
                                        / static_cast<int>(sizeof(Input_T));

                macsOnRange<INPUT_MEM_WRAP_SIZE / sizeof(Input_T)>(
                    inputs + iOffset,
                    weights + wWrapOffset,
                    weightedSum);
            }
            else {
                macsOnRange<NB_CHANNELS * WEIGHT_SPATIAL_SIZE>(
                    inputs,
                    weights + wOffset,
                    weightedSum);
            }

            const auto outputVal
                = activation_forward_value<Output_T>(weightedSum, och, ACTIVATION, rescaling);
            pack_rev_set(packedOutputVal, packElt, outputVal);
        }

        outputs[outputPack] = packedOutputVal;
    }
}

/**
 * @brief Kernel to use when the input is in the NHWC format, but the
 * weights have not been transposed and still follow the NCHW format order.
 */
template<size_t NB_CHANNELS,
         size_t CHANNELS_HEIGHT, size_t CHANNELS_WIDTH,
         size_t NB_OUTPUTS,
         size_t OUTPUTS_HEIGHT, size_t OUTPUTS_WIDTH,
         ActivationFunction_T ACTIVATION,
         // Memory mapping: inputs
         size_t INPUT_MEM_CONT_OFFSET,
         size_t INPUT_MEM_CONT_SIZE,
         size_t INPUT_MEM_WRAP_OFFSET,
         size_t INPUT_MEM_WRAP_SIZE,
         size_t INPUT_MEM_STRIDE,
         // Memory mapping: outputs
         size_t OUTPUT_MEM_CONT_OFFSET,
         size_t OUTPUT_MEM_CONT_SIZE,
         size_t OUTPUT_MEM_WRAP_OFFSET,
         size_t OUTPUT_MEM_WRAP_SIZE,
         size_t OUTPUT_MEM_STRIDE,
         typename Input_T, typename Output_T,
         typename Weight_T, typename Bias_T,
         typename Rescaling_T>
__attribute__((always_inline)) inline
void fullyconnected_transpose_forward (
    const Input_T* __restrict inputs,
    Output_T* __restrict outputs,
    const Weight_T* __restrict weights,
    const Bias_T* __restrict biases,
    const Rescaling_T& __restrict rescaling)
{
    constexpr size_t NB_I_CHANNELS_PACKED = (NB_CHANNELS + n_pack<Input_T>() - 1) / n_pack<Input_T>();
    constexpr size_t NB_W_CHANNELS_PACKED = (NB_CHANNELS + n_pack<Weight_T>() - 1) / n_pack<Weight_T>();
    constexpr size_t WEIGHT_SPATIAL_SIZE = CHANNELS_WIDTH * CHANNELS_HEIGHT;

    constexpr size_t NB_OUTPUTS_PACKED = (NB_OUTPUTS + n_pack<Output_T>() - 1) / n_pack<Output_T>();
    constexpr size_t NB_OUTPUTS_REM = NB_OUTPUTS % n_pack<Output_T>();

#ifdef _OPENMP
#pragma omp parallel for
#endif
    for (size_t outputPack = 0; outputPack < NB_OUTPUTS_PACKED; ++outputPack) {
        Output_T packedOutputVal;

        for (size_t packElt = 0; packElt < n_pack<Output_T>(); ++packElt) {
            if (NB_OUTPUTS_REM != 0 && packElt == NB_OUTPUTS_REM) {
                break;
            }

            const size_t och = outputPack * n_pack<Output_T>() + packElt;

            Bias_T weightedSum = (biases) ? biases[och] : Bias_T(0);

            for (size_t iy = 0; iy < CHANNELS_HEIGHT; ++iy) {
                const int iPos = (CHANNELS_WIDTH * iy);
                int iOffset = (INPUT_MEM_STRIDE / sizeof(Input_T)) * iPos;

                // Wrapping cannot occur in the middle of a line, except if
                // there is only one line (1D)!
                bool wrapInRange = false;

                if (INPUT_MEM_WRAP_SIZE > 0 && iOffset >= INPUT_MEM_CONT_SIZE / static_cast<int>(sizeof(Input_T))) {
                    iOffset += (INPUT_MEM_WRAP_OFFSET - INPUT_MEM_CONT_OFFSET
                                - INPUT_MEM_CONT_SIZE) / static_cast<int>(sizeof(Input_T));
                }
                else if (INPUT_MEM_WRAP_SIZE > 0 && CHANNELS_WIDTH > 1
                    && CHANNELS_HEIGHT == 1 // single line (1D)!
                    && iOffset + CHANNELS_WIDTH * NB_I_CHANNELS_PACKED
                        > (INPUT_MEM_CONT_SIZE / static_cast<int>(sizeof(Input_T))))
                {
                    wrapInRange = true;
                }

                const int wOffset = CHANNELS_WIDTH
                                        * (iy + CHANNELS_HEIGHT * NB_W_CHANNELS_PACKED * och);

                for (size_t ix = 0; ix < CHANNELS_WIDTH; ++ix) {
                    int iOffsetInRange = iOffset + ix * (INPUT_MEM_STRIDE / sizeof(Input_T));

                    if (wrapInRange
                        && iOffsetInRange >= INPUT_MEM_CONT_SIZE / static_cast<int>(sizeof(Input_T)))
                    {
                        iOffsetInRange += (INPUT_MEM_WRAP_OFFSET
                                    - INPUT_MEM_CONT_OFFSET
                                    - INPUT_MEM_CONT_SIZE) / static_cast<int>(sizeof(Input_T));
                    }

                    // Beware that the pointer increment for weights is
                    // CHANNELS_HEIGHT*CHANNELS_WIDTH
                    macsOnRange<NB_CHANNELS, WEIGHT_SPATIAL_SIZE>(
                        inputs + iOffsetInRange,
                        weights + wOffset + ix,
                        weightedSum);
                }
            }

            const auto outputVal
                = activation_forward_value<Output_T>(weightedSum, och, ACTIVATION, rescaling);
            pack_rev_set(packedOutputVal, packElt, outputVal);
        }

        outputs[outputPack] = packedOutputVal;
    }
}

} // namespace export_cpp

#endif  // __AIDGE_EXPORT_CPP_KERNELS_FULLYCONNECTED__
