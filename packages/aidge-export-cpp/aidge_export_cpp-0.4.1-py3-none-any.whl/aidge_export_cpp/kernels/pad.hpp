#ifndef __AIDGE_EXPORT_CPP_KERNELS_PAD2D__
#define __AIDGE_EXPORT_CPP_KERNELS_PAD2D__

#include "utils/cpp/typedefs.hpp"
#include "utils/cpp/utils.hpp"
#include <cstddef>

// TODO : add border value and border type (Reflect, Constant, Wrap...) and add
// the two missing pad value (bottom and right)

namespace export_cpp {

template <size_t NB_BATCHES,
          size_t NB_CHANNELS,
          size_t CHANNELS_HEIGHT,
          size_t CHANNELS_WIDTH,
          size_t NB_OUTPUTS,
          size_t OUTPUTS_HEIGHT,
          size_t OUTPUTS_WIDTH,
          int PADDING_TOP,
          int PADDING_LEFT,
          int PADDING_BOTTOM,
          int PADDING_RIGHT,
          typename Input_T,
          typename Output_T>
__attribute__((always_inline)) inline void
pad_forward(double borderValue,
            const Input_T *__restrict inputs,
            Output_T *__restrict outputs) {
    constexpr size_t oySize =
        CHANNELS_HEIGHT + PADDING_TOP + PADDING_BOTTOM;
    constexpr size_t oxSize =
        CHANNELS_WIDTH + PADDING_LEFT + PADDING_RIGHT;

    constexpr size_t inputStrides[3] = {
        NB_CHANNELS * CHANNELS_HEIGHT * CHANNELS_WIDTH,
        CHANNELS_WIDTH * CHANNELS_HEIGHT,
        CHANNELS_WIDTH};
    constexpr size_t outputStrides[3] = {
        NB_CHANNELS * oySize * oxSize,
        oySize * oxSize,
        oxSize,
    };

    for (size_t batch = 0, inBatchOffset = 0, outBatchOffset = 0;
         batch < NB_BATCHES;
         ++batch,
                      inBatchOffset += inputStrides[0],
                      outBatchOffset += outputStrides[0]) {

        for (size_t ch = 0,
                          inChannelOffset = inBatchOffset,
                          outChannelOffset = outBatchOffset;
             ch < NB_CHANNELS;
             ++ch,
                          inChannelOffset += inputStrides[1],
                          outChannelOffset += outputStrides[1]) {

            for (int oY = 0,
                     oDimYOffset = outChannelOffset,
                     iY = oY - PADDING_TOP,
                     // iDimOffset won't be used unless iY >= 0 hence no risk
                     // of negative idx
                 iDimYOffset = inChannelOffset + iY * inputStrides[2];
                 static_cast<size_t>(oY) < oySize;
                 ++oY,
                     ++iY,
                     iDimYOffset += inputStrides[2],
                     oDimYOffset += outputStrides[2]) {

                if (iY < 0 or iY >= CHANNELS_HEIGHT) {
                    for (Output_T *o = outputs + oDimYOffset;
                         o != outputs + oDimYOffset + outputStrides[2];
                         ++o) {
                        *o = borderValue;
                    }
                    continue;
                }
                for (size_t oX = 0; oX < oxSize; ++oX) {
                    const int iX = static_cast<int>(oX - PADDING_LEFT);
                    if (iX < 0 or iX >= CHANNELS_WIDTH) {
                        outputs[oDimYOffset + oX] = borderValue;
                    } else {
                        outputs[oDimYOffset + oX] = inputs[iDimYOffset + iX];
                    }
                }
            }
        }
    }
}

} // namespace export_cpp

#endif // __AIDGE_EXPORT_CPP_KERNELS_PAD2D__
