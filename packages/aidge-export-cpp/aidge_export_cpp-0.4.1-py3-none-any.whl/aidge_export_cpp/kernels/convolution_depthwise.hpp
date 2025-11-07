#ifndef __AIDGE_EXPORT_CPP_KERNELS_CONVOLUTION_DEPTHWISE__
#define __AIDGE_EXPORT_CPP_KERNELS_CONVOLUTION_DEPTHWISE__

#include "utils/cpp/typedefs.hpp"
#include "utils/cpp/rescaling_utils.hpp"
#include "utils/cpp/utils.hpp"
#include "utils/cpp/macs.hpp"
#include "utils/cpp/activation_utils.hpp"
#include <cstddef>

namespace export_cpp {

template<size_t NB_CHANNELS,
         size_t CHANNELS_HEIGHT, size_t CHANNELS_WIDTH,
         size_t NB_OUTPUTS,
         size_t OUTPUTS_HEIGHT, size_t OUTPUTS_WIDTH,
         size_t PADDING_Y, size_t PADDING_X,
         size_t STRIDE_Y, size_t STRIDE_X,
         size_t DILATION_Y, size_t DILATION_X,
         size_t KERNEL_HEIGHT, size_t KERNEL_WIDTH,
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
void convolution_depthwise_forward(
    const Input_T* __restrict inputs,
    Output_T* __restrict outputs,
    const Weight_T* __restrict weights,
    const Bias_T* __restrict biases,
    const Rescaling_T& __restrict rescaling)
{
    static_assert(NB_OUTPUTS % NB_CHANNELS == 0,
        "NB_OUTPUTS should be a multiple of NB_CHANNELS.");

    constexpr size_t NB_I_CHANNELS_PACKED = (NB_CHANNELS + n_pack<Input_T>() - 1) / n_pack<Input_T>();
    constexpr size_t NB_OUTPUTS_PACKED = (NB_OUTPUTS + n_pack<Output_T>() - 1) / n_pack<Output_T>();
    constexpr size_t NB_OUTPUTS_REM = NB_OUTPUTS % n_pack<Output_T>();

    constexpr size_t DILATED_KERNEL_HEIGHT
            = KERNEL_HEIGHT + (DILATION_Y - 1) * (KERNEL_HEIGHT - 1);

    constexpr size_t DILATED_KERNEL_WIDTH
            = KERNEL_WIDTH + (DILATION_X - 1) * (KERNEL_WIDTH - 1);

    constexpr size_t OUTPUTS_HEIGHT_NOPAD
        = (CHANNELS_HEIGHT - DILATION_Y * (KERNEL_HEIGHT - 1) - 1 + STRIDE_Y) / STRIDE_Y;
    constexpr size_t OUTPUTS_WIDTH_NOPAD
        = (CHANNELS_WIDTH - DILATION_X * (KERNEL_WIDTH - 1) - 1 + STRIDE_X) / STRIDE_X;

    for (size_t oy = 0; oy < OUTPUTS_HEIGHT; ++oy) {
        const size_t syMin = (PADDING_Y == 0) ? 0
            : max(PADDING_Y - (oy * STRIDE_Y), 0);
        const size_t syMax = (PADDING_Y == 0
                && OUTPUTS_HEIGHT == OUTPUTS_HEIGHT_NOPAD) ? DILATED_KERNEL_HEIGHT
            : clamp(CHANNELS_HEIGHT + PADDING_Y - (oy * STRIDE_Y),
                    0, DILATED_KERNEL_HEIGHT);
        const int iy = static_cast<int>(oy * STRIDE_Y) - static_cast<int>(PADDING_Y);

        // oy loop should not be parallelized to allow memory wrapping: memory
        // lines must be processed in order.
#ifdef _OPENMP
#pragma omp parallel for collapse(2)
#endif
        for (size_t ox = 0; ox < OUTPUTS_WIDTH; ++ox) {
            for (size_t outputPack = 0; outputPack < NB_OUTPUTS_PACKED; ++outputPack) {
                Output_T packedOutputVal;

                const size_t oPos = (ox + OUTPUTS_WIDTH * oy);
                int oOffset = (OUTPUT_MEM_STRIDE / sizeof(Output_T)) * oPos;

                if (OUTPUT_MEM_WRAP_SIZE > 0 && oOffset >= OUTPUT_MEM_CONT_SIZE / static_cast<int>(sizeof(Output_T))) {
                    oOffset += (OUTPUT_MEM_WRAP_OFFSET - OUTPUT_MEM_CONT_OFFSET
                                - OUTPUT_MEM_CONT_SIZE) / static_cast<int>(sizeof(Output_T));
                }

                for (size_t packElt = 0; packElt < n_pack<Output_T>(); ++packElt) {
                    if (NB_OUTPUTS_REM != 0 && packElt == NB_OUTPUTS_REM) {
                        break;
                    }

                    const size_t output = outputPack * n_pack<Output_T>() + packElt;

                    // moved to inner loop for collapsing -->
                    const size_t sxMin = (PADDING_X == 0) ? 0
                        : max(PADDING_X - (ox * STRIDE_X), 0);
                    const size_t sxMax = (PADDING_X == 0
                            && OUTPUTS_WIDTH == OUTPUTS_WIDTH_NOPAD)
                                ? DILATED_KERNEL_WIDTH
                        : clamp(CHANNELS_WIDTH + PADDING_X - (ox * STRIDE_X),
                                0, DILATED_KERNEL_WIDTH);
                    const int ix = static_cast<int>(ox * STRIDE_X) - static_cast<int>(PADDING_X);
                    // <--

                    const size_t channel = (output * NB_CHANNELS) / NB_OUTPUTS;

                    Bias_T weightedSum = biases ? biases[output] : Bias_T(0);

                    for (size_t sy = 0; sy < KERNEL_HEIGHT; ++sy) {
                        if ((PADDING_Y != 0
                                || OUTPUTS_HEIGHT != OUTPUTS_HEIGHT_NOPAD)
                            && ((sy*DILATION_Y < syMin) || (sy*DILATION_Y >= syMax)))
                        {
                            continue;
                        }

                        const size_t iPos = (ix + sxMin)
                            + CHANNELS_WIDTH * (iy + sy * DILATION_Y);
                        int iOffset = (INPUT_MEM_STRIDE / sizeof(Input_T)) * iPos;

                        // Wrapping cannot occur in the middle of a line, except if
                        // there is only one line (1D)!
                        bool wrapInRange = false;

                        if (INPUT_MEM_WRAP_SIZE > 0
                            && iOffset >= INPUT_MEM_CONT_SIZE / static_cast<int>(sizeof(Input_T)))
                        {
                            iOffset += (INPUT_MEM_WRAP_OFFSET - INPUT_MEM_CONT_OFFSET
                                        - INPUT_MEM_CONT_SIZE) / static_cast<int>(sizeof(Input_T));
                        }
                        else if (INPUT_MEM_WRAP_SIZE > 0 && KERNEL_WIDTH > 1
                            && CHANNELS_HEIGHT == 1 // single line (1D)!
                            && iOffset + KERNEL_WIDTH * NB_I_CHANNELS_PACKED
                                > (INPUT_MEM_CONT_SIZE / static_cast<int>(sizeof(Input_T))))
                        {
                            wrapInRange = true;
                        }

                        const size_t wOffset = (output*KERNEL_HEIGHT + sy)
                                            * KERNEL_WIDTH;
                        const auto inPackOffset = channel % n_pack<Input_T>();

                        if (!wrapInRange && NB_I_CHANNELS_PACKED == (INPUT_MEM_STRIDE / sizeof(Input_T))
                            && DILATION_X == 1 && ((PADDING_X == 0
                                && OUTPUTS_WIDTH == OUTPUTS_WIDTH_NOPAD)
                            || sxMax - sxMin == KERNEL_WIDTH))
                        {
                            const auto wPackOffset = wOffset % n_pack<Weight_T>();

                            if (inPackOffset == 0 && wPackOffset == 0) {
                                macsOnRange<KERNEL_WIDTH, NB_I_CHANNELS_PACKED>(
                                    inputs + iOffset + channel / n_pack<Input_T>(),
                                    weights + wOffset / n_pack<Weight_T>(),
                                    weightedSum);
                            }
                            else {
                                for (size_t sx = 0; sx < KERNEL_WIDTH; ++sx) {
                                    const int iOffsetInRange = iOffset
                                        + (sx * DILATION_X - sxMin) * (INPUT_MEM_STRIDE / sizeof(Input_T));

                                    const auto in = inputs[iOffsetInRange + channel / n_pack<Input_T>()];
                                    const auto w = weights[(wOffset + sx) / n_pack<Weight_T>()];

                                    weightedSum += pack_rev_get(in, inPackOffset)
                                                    * pack_rev_get(w, (wOffset + sx) % n_pack<Weight_T>());
                                }
                            }
                        }
                        else {
                            for (size_t sx = 0; sx < KERNEL_WIDTH; ++sx) {
                                if ((PADDING_X != 0
                                        || OUTPUTS_WIDTH != OUTPUTS_WIDTH_NOPAD)
                                    && ((sx*DILATION_X < sxMin) || (sx*DILATION_X >= sxMax)))
                                {
                                    continue;
                                }

                                int iOffsetInRange = iOffset
                                    + (sx * DILATION_X - sxMin) * (INPUT_MEM_STRIDE / sizeof(Input_T));

                                if (wrapInRange
                                    && iOffsetInRange >= INPUT_MEM_CONT_SIZE / static_cast<int>(sizeof(Input_T)))
                                {
                                    iOffsetInRange += (INPUT_MEM_WRAP_OFFSET
                                                - INPUT_MEM_CONT_OFFSET
                                                - INPUT_MEM_CONT_SIZE) / static_cast<int>(sizeof(Input_T));
                                }

                                const auto in = inputs[iOffsetInRange + channel / n_pack<Input_T>()];
                                const auto w = weights[(wOffset + sx) / n_pack<Weight_T>()];
                                weightedSum += pack_rev_get(in, inPackOffset)
                                                * pack_rev_get(w, (wOffset + sx) % n_pack<Weight_T>());
                            }
                        }
                    }

                    const auto outputVal
                        = activation_forward_value<Output_T>(weightedSum, output, ACTIVATION, rescaling);
                    pack_rev_set(packedOutputVal, packElt, outputVal);
                }

                outputs[oOffset + outputPack] = packedOutputVal;
            }
        }
    }
}

// Template specialization when biases are not given to the convolution
template<int NB_CHANNELS,
         int CHANNELS_HEIGHT, int CHANNELS_WIDTH,
         int NB_OUTPUTS,
         int OUTPUTS_HEIGHT, int OUTPUTS_WIDTH,
         int PADDING_Y, int PADDING_X,
         int STRIDE_Y, int STRIDE_X,
         int DILATION_Y, int DILATION_X,
         int KERNEL_HEIGHT, int KERNEL_WIDTH,
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
         typename Weight_T,
         typename Rescaling_T>
__attribute__((always_inline)) inline
void convolution_depthwise_forward(
    const Input_T* __restrict inputs,
    Output_T* __restrict outputs,
    const Weight_T* __restrict weights,
    std::nullptr_t,
    const Rescaling_T& __restrict rescaling)
{
    const float* b = nullptr;

    convolution_depthwise_forward<NB_CHANNELS,
                        CHANNELS_HEIGHT,
                        CHANNELS_WIDTH,
                        NB_OUTPUTS,
                        OUTPUTS_HEIGHT,
                        OUTPUTS_WIDTH,
                        PADDING_Y,
                        PADDING_X,
                        STRIDE_Y,
                        STRIDE_X,
                        DILATION_Y,
                        DILATION_X,
                        KERNEL_HEIGHT,
                        KERNEL_WIDTH,
                        ACTIVATION,
                        // Memory mapping: inputs
                        INPUT_MEM_CONT_OFFSET,
                        INPUT_MEM_CONT_SIZE,
                        INPUT_MEM_WRAP_OFFSET,
                        INPUT_MEM_WRAP_SIZE,
                        INPUT_MEM_STRIDE,
                        // Memory mapping: outputs
                        OUTPUT_MEM_CONT_OFFSET,
                        OUTPUT_MEM_CONT_SIZE,
                        OUTPUT_MEM_WRAP_OFFSET,
                        OUTPUT_MEM_WRAP_SIZE,
                        OUTPUT_MEM_STRIDE>
                        (inputs, outputs, weights, b, rescaling);
}

} // namespace export_cpp

#endif  // __AIDGE_EXPORT_CPP_KERNELS_CONVOLUTION_DEPTHWISE__
