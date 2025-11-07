#ifndef __AIDGE_EXPORT_CPP_KERNELS_ELEMWISE__
#define __AIDGE_EXPORT_CPP_KERNELS_ELEMWISE__

#include "utils/cpp/typedefs.hpp"
#include "utils/cpp/activation_utils.hpp"
#include <cstddef>

namespace export_cpp {

template<size_t NB_MAT, ElemWise_T ELEM_OP,
         size_t INPUT1_CONT_SIZE, size_t INPUT2_CONT_SIZE, size_t OUTPUT_CONT_SIZE,
         const size_t OFFSET_IN1[], const size_t OFFSET_IN2[],
         ActivationFunction_T ACTIVATION,
         // Memory mapping: inputs
         int INPUT1_MEM_CONT_OFFSET,
         int INPUT1_MEM_CONT_SIZE,
         int INPUT1_MEM_WRAP_OFFSET,
         int INPUT1_MEM_WRAP_SIZE,
         int INPUT1_MEM_STRIDE,
         int INPUT2_MEM_CONT_OFFSET,
         int INPUT2_MEM_CONT_SIZE,
         int INPUT2_MEM_WRAP_OFFSET,
         int INPUT2_MEM_WRAP_SIZE,
         int INPUT2_MEM_STRIDE,
         // Memory mapping: outputs
         int OUTPUT_MEM_CONT_OFFSET,
         int OUTPUT_MEM_CONT_SIZE,
         int OUTPUT_MEM_WRAP_OFFSET,
         int OUTPUT_MEM_WRAP_SIZE,
         int OUTPUT_MEM_STRIDE,
         typename Sum_T, 
         typename Input_T, typename Output_T, typename Rescaling_T>
__attribute__((always_inline)) inline
void elemwise_forward(
    Output_T* __restrict outputs,
    const Rescaling_T& __restrict rescaling,
    const Input_T* __restrict inputs1,
    const Input_T* __restrict inputs2)
{
    static_assert(INPUT1_MEM_WRAP_SIZE == 0, "Incompatible input memory wrapping");
    static_assert(INPUT2_MEM_WRAP_SIZE == 0, "Incompatible input memory wrapping");
    static_assert(OUTPUT_MEM_CONT_SIZE % OUTPUT_CONT_SIZE == 0, "Incompatible output memory wrapping");

    auto apply_op = [](auto a, auto b) -> Sum_T {
        switch (ELEM_OP) {
            case ElemWise_T::Add: return a + b;
            case ElemWise_T::Sub: return a - b;
            case ElemWise_T::Mul: return a * b;
            case ElemWise_T::Div: return a / b;
            default:  return a;
        }
    };

    for (size_t stack = 0; stack < NB_MAT; ++stack) {
        const size_t offset_in1 = OFFSET_IN1[stack] * INPUT1_CONT_SIZE;
        const size_t offset_in2 = OFFSET_IN2[stack] * INPUT2_CONT_SIZE;
        int out_offset = stack * OUTPUT_CONT_SIZE;

        if (OUTPUT_MEM_WRAP_SIZE > 0 && out_offset >= OUTPUT_MEM_CONT_SIZE / static_cast<int>(sizeof(Output_T))) {
            out_offset += (OUTPUT_MEM_WRAP_OFFSET - OUTPUT_MEM_CONT_OFFSET
                        - OUTPUT_MEM_CONT_SIZE) / static_cast<int>(sizeof(Output_T));
        }

        for (size_t i = 0; i < OUTPUT_CONT_SIZE; ++i) {
            const size_t in0_id = (INPUT1_CONT_SIZE != 1) ? i : 0;
            const size_t in1_id = (INPUT2_CONT_SIZE != 1) ? i : 0;
            const size_t out_id = out_offset + i;

            const auto val1 = inputs1[in0_id + offset_in1];
            const auto val2 = inputs2[in1_id + offset_in2];
            const Sum_T val = apply_op(val1, val2);

            outputs[out_id] = activation_forward_value<Output_T>(val, out_id, ACTIVATION, rescaling);
        }
    }
}

} // namespace export_cpp

#endif  // __AIDGE_EXPORT_CPP_KERNELS_ELEMWISE__
