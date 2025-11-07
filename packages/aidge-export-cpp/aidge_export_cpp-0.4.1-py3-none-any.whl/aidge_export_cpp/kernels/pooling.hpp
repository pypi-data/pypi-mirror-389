#ifndef __AIDGE_EXPORT_CPP_KERNELS_POOLING__
#define __AIDGE_EXPORT_CPP_KERNELS_POOLING__

#include "utils/cpp/typedefs.hpp"
#include "utils/cpp/utils.hpp"
#include <limits>
#include <cmath>
#include <cstddef>

namespace export_cpp {

// ----------------------------------------------------------------------------
// Max pooling helpers - Unpacked inputs
// ----------------------------------------------------------------------------

template<class Input_T,
            typename std::enable_if<(n_pack<Input_T>() == 1)>::type* = nullptr>
static void fillMaxVal(Input_T& __restrict maxVal)
{
    maxVal = std::numeric_limits<Input_T>::lowest();
}

template<class Input_T,
            typename std::enable_if<(n_pack<Input_T>() == 1)>::type* = nullptr>
static void findMaxVal(const Input_T& __restrict inputs, Input_T& __restrict maxVal)
{
    if (inputs > maxVal){
        maxVal = inputs;
    }
}

// ----------------------------------------------------------------------------
// Max pooling helpers - Packed <2> inputs
// ----------------------------------------------------------------------------

template<class Input_T,
            typename std::enable_if<(n_pack<Input_T>() == 2)>::type* = nullptr>
static void fillMaxVal(Input_T& __restrict maxVal)
{
    maxVal.rev_fields.op0 = std::numeric_limits<Input_T>::lowest();
    maxVal.rev_fields.op1 = std::numeric_limits<Input_T>::lowest();
}

template<class Input_T,
            typename std::enable_if<(n_pack<Input_T>() == 2)>::type* = nullptr>
static void findMaxVal(const Input_T& __restrict inputs, Input_T& __restrict maxVal)
{
    if (inputs.rev_fields.op0 > maxVal.rev_fields.op0){
        maxVal.rev_fields.op0 = inputs.rev_fields.op0;
    }

    if (inputs.rev_fields.op1 > maxVal.rev_fields.op1){
        maxVal.rev_fields.op1 = inputs.rev_fields.op1;
    }
}

// ----------------------------------------------------------------------------
// Max pooling helpers - Packed <4> inputs
// ----------------------------------------------------------------------------

template<class Input_T,
            typename std::enable_if<(n_pack<Input_T>() == 4)>::type* = nullptr>
static void fillMaxVal(Input_T& __restrict maxVal)
{
    maxVal.rev_fields.op0 = std::numeric_limits<Input_T>::lowest();
    maxVal.rev_fields.op1 = std::numeric_limits<Input_T>::lowest();
    maxVal.rev_fields.op2 = std::numeric_limits<Input_T>::lowest();
    maxVal.rev_fields.op3 = std::numeric_limits<Input_T>::lowest();
}

template<class Input_T,
            typename std::enable_if<(n_pack<Input_T>() == 4)>::type* = nullptr>
static void findMaxVal(const Input_T& __restrict inputs, Input_T& __restrict maxVal)
{
    if (inputs.rev_fields.op0 > maxVal.rev_fields.op0){
        maxVal.rev_fields.op0 = inputs.rev_fields.op0;
    }

    if (inputs.rev_fields.op1 > maxVal.rev_fields.op1){
        maxVal.rev_fields.op1 = inputs.rev_fields.op1;
    }

    if (inputs.rev_fields.op2 > maxVal.rev_fields.op2){
        maxVal.rev_fields.op2 = inputs.rev_fields.op2;
    }

    if (inputs.rev_fields.op3 > maxVal.rev_fields.op3){
        maxVal.rev_fields.op3 = inputs.rev_fields.op3;
    }
}


template<size_t NB_CHANNELS,
         size_t CHANNELS_HEIGHT, size_t CHANNELS_WIDTH,
         size_t NB_OUTPUTS,
         size_t OUTPUTS_HEIGHT, size_t OUTPUTS_WIDTH,
         size_t PADDING_Y, size_t PADDING_X,
         size_t STRIDE_Y, size_t STRIDE_X,
         size_t POOL_HEIGHT, size_t POOL_WIDTH,
         Pooling_T POOLING_TYPE,
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
         typename Input_T, typename Output_T>
__attribute__((always_inline)) inline
void pooling_forward(
    const Input_T* __restrict inputs,
    Output_T* __restrict outputs)
{
    static_assert(POOLING_TYPE == Pooling_T::Max || POOLING_TYPE == Pooling_T::Average, "Only Max and Average pooling are supported");
    static_assert(POOLING_TYPE != Pooling_T::Average || (!is_packed<Input_T>() && !is_packed<Output_T>()), "I/O packing not yet supported for Average pooling");

    constexpr size_t OUTPUTS_HEIGHT_NOPAD
        = (CHANNELS_HEIGHT - POOL_HEIGHT + STRIDE_Y) / STRIDE_Y;
    constexpr size_t OUTPUTS_WIDTH_NOPAD
        = (CHANNELS_WIDTH - POOL_WIDTH + STRIDE_X) / STRIDE_X;

    for (size_t oy = 0; oy < OUTPUTS_HEIGHT; ++oy) {
        const size_t syMin = (PADDING_Y == 0) ? 0
            : max(PADDING_Y - (oy * STRIDE_Y), 0);
        const size_t syMax = (PADDING_Y == 0
                && OUTPUTS_HEIGHT == OUTPUTS_HEIGHT_NOPAD) ? POOL_HEIGHT
            : clamp(CHANNELS_HEIGHT + PADDING_Y - (oy * STRIDE_Y),
                    0, POOL_HEIGHT);
        const int iy = static_cast<int>(oy * STRIDE_Y) - static_cast<int>(PADDING_Y);

        // oy loop should not be parallelized to allow memory wrapping: memory
        // lines must be processed in order.
#ifdef _OPENMP
#pragma omp parallel for collapse(2)
#endif
        for (size_t ox = 0; ox < OUTPUTS_WIDTH; ++ox) {
            for (size_t output = 0; output < NB_OUTPUTS; ++output) {
                // moved to inner loop for collapsing -->
                const size_t sxMin = (PADDING_X == 0) ? 0
                    : max(PADDING_X - (ox * STRIDE_X), 0);
                const size_t sxMax = (PADDING_X == 0
                        && OUTPUTS_WIDTH == OUTPUTS_WIDTH_NOPAD)
                            ? POOL_WIDTH
                    : clamp(CHANNELS_WIDTH + PADDING_X - (ox * STRIDE_X),
                            0, POOL_WIDTH);
                const int ix = static_cast<int>(ox * STRIDE_X) - static_cast<int>(PADDING_X);

                const size_t oPos = (ox + OUTPUTS_WIDTH * oy);
                int oOffset = (OUTPUT_MEM_STRIDE / sizeof(Output_T)) * oPos;

                if (OUTPUT_MEM_WRAP_SIZE > 0 && oOffset >= OUTPUT_MEM_CONT_SIZE / static_cast<int>(sizeof(Output_T))) {
                    oOffset += (OUTPUT_MEM_WRAP_OFFSET - OUTPUT_MEM_CONT_OFFSET
                                - OUTPUT_MEM_CONT_SIZE) / static_cast<int>(sizeof(Output_T));
                }
                // <--

                if (POOLING_TYPE == Pooling_T::Max) {
                    Input_T maxVal;
                    fillMaxVal(maxVal);

                    for (size_t sy = 0; sy < POOL_HEIGHT; ++sy) {
                        if ((PADDING_Y != 0
                                || OUTPUTS_HEIGHT != OUTPUTS_HEIGHT_NOPAD)
                            && sy >= syMax - syMin)
                        {
                            break;
                        }

                        const size_t iPos = static_cast<size_t>(sxMin + ix)
                                            + CHANNELS_WIDTH * (static_cast<size_t>(iy + syMin + sy));
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
                        else if (INPUT_MEM_WRAP_SIZE > 0 && POOL_WIDTH > 1
                            && CHANNELS_HEIGHT == 1 // single line (1D)!
                            && iOffset + POOL_WIDTH * (INPUT_MEM_CONT_SIZE / static_cast<int>(sizeof(Input_T)))
                                > (INPUT_MEM_CONT_SIZE / static_cast<int>(sizeof(Input_T))))
                        {
                            wrapInRange = true;
                        }

                        for (size_t sx = 0; sx < POOL_WIDTH; ++sx) {
                            if ((PADDING_X != 0
                                    || OUTPUTS_WIDTH != OUTPUTS_WIDTH_NOPAD)
                                && sx >= sxMax - sxMin)
                            {
                                break;
                            }

                            int iOffsetInRange = iOffset + output
                                + sx * (INPUT_MEM_STRIDE / sizeof(Input_T));

                            if (wrapInRange &&
                                iOffsetInRange >= INPUT_MEM_CONT_SIZE / static_cast<int>(sizeof(Input_T)))
                            {
                                iOffsetInRange += (INPUT_MEM_WRAP_OFFSET
                                            - INPUT_MEM_CONT_OFFSET
                                            - INPUT_MEM_CONT_SIZE) / static_cast<int>(sizeof(Input_T));
                            }

                            findMaxVal(inputs[iOffsetInRange], maxVal);
                        }
                    }

                    outputs[oOffset + output] = maxVal;
                }
                else if (POOLING_TYPE == Pooling_T::Average) {
                    float sum = 0;

                    for (size_t sy = 0; sy < POOL_HEIGHT; ++sy) {
                        if ((PADDING_Y != 0
                                || OUTPUTS_HEIGHT != OUTPUTS_HEIGHT_NOPAD)
                            && sy >= syMax - syMin)
                        {
                            break;
                        }

                        const size_t iPos = static_cast<size_t>(sxMin + ix)
                                            + CHANNELS_WIDTH * (static_cast<size_t>(iy + syMin + sy));
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
                        else if (INPUT_MEM_WRAP_SIZE > 0 && POOL_WIDTH > 1
                            && CHANNELS_HEIGHT == 1 // single line (1D)!
                            && iOffset + POOL_WIDTH * (INPUT_MEM_STRIDE / static_cast<int>(sizeof(Input_T)))
                                > (INPUT_MEM_CONT_SIZE / static_cast<int>(sizeof(Input_T))))
                        {
                            wrapInRange = true;
                        }

                        for (size_t sx = 0; sx < POOL_WIDTH; ++sx) {
                            if ((PADDING_X != 0
                                    || OUTPUTS_WIDTH != OUTPUTS_WIDTH_NOPAD)
                                && sx >= sxMax - sxMin)
                            {
                                break;
                            }

                            int iOffsetInRange = iOffset + output
                                + sx * (INPUT_MEM_STRIDE / sizeof(Input_T));

                            if (wrapInRange &&
                                iOffsetInRange >= INPUT_MEM_CONT_SIZE / static_cast<int>(sizeof(Input_T)))
                            {
                                iOffsetInRange += (INPUT_MEM_WRAP_OFFSET
                                            - INPUT_MEM_CONT_OFFSET
                                            - INPUT_MEM_CONT_SIZE) / static_cast<int>(sizeof(Input_T));
                            }

                            sum += inputs[iOffsetInRange];
                        }
                    }

                    outputs[oOffset + output] = static_cast<Output_T>(
                        std::is_integral<Output_T>::value ? std::round(sum / (POOL_HEIGHT * POOL_WIDTH)) : sum / (POOL_HEIGHT * POOL_WIDTH)
                    );

                }
            }
        }
    }
}

} // namespace export_cpp

#endif  // __AIDGE_EXPORT_CPP_KERNELS_POOLING__
