#ifndef __AIDGE_EXPORT_CPP_MACS_HPP__
#define __AIDGE_EXPORT_CPP_MACS_HPP__

#include <type_traits>

#include "typedefs.hpp"

namespace export_cpp {

template <int NB_ITERATIONS,
          int INPUTS_INC = 1,
          int WEIGHTS_INC = 1,
          typename Weight_T,
          typename Sum_T,
          class Input_T>
static typename std::enable_if_t<NB_ITERATIONS == 0>
macsOnRange(const Input_T *__restrict /*inputs*/,
            const Weight_T *__restrict /*weights*/,
            Sum_T &__restrict /*weightedSum*/) {}

// ----------------------------------------------------------------------------
// Packed <*> weights - Unpacked inputs
// ----------------------------------------------------------------------------

template <int NB_ITERATIONS,
          int INPUTS_INC = 1,
          int WEIGHTS_INC = 1,
          typename Weight_T,
          typename Sum_T,
          class Input_T>
static typename std::enable_if_t<(is_packed<Weight_T>() &&
                                  n_pack<Weight_T>() < 8 &&
                                  NB_ITERATIONS == 1 && !is_packed<Input_T>())>
macsOnRange(const Input_T *__restrict inputs,
            const Weight_T *__restrict weights,
            Sum_T &__restrict weightedSum) {
    weightedSum += (*inputs) * weights[0 * WEIGHTS_INC].rev_fields.op0;
}

// ----------------------------------------------------------------------------
// Packed <2> weights - Unpacked inputs
// ----------------------------------------------------------------------------

template<int INPUTS_INC = 1,
            int WEIGHTS_INC = 1,
            typename Input_T,
            typename Weight_T, typename Sum_T,
            typename std::enable_if<(n_pack<Weight_T>() == 2
            && !is_packed<Input_T>())>::type* = nullptr>
static Sum_T dualMac(const Input_T* __restrict inputs,
                                        const Weight_T* __restrict weights,
                                        Sum_T weightedSum)
{
    weightedSum += inputs[0*INPUTS_INC] * weights[0*WEIGHTS_INC].rev_fields.op0
        + inputs[1*INPUTS_INC] * weights[0*WEIGHTS_INC].rev_fields.op1;

    return weightedSum;
}

template<int NB_ITERATIONS,
            int INPUTS_INC = 1,
            int WEIGHTS_INC = 1,
            typename Weight_T, typename Sum_T,
            class Input_T,
            typename std::enable_if<(n_pack<Weight_T>() == 2
            && NB_ITERATIONS >= 2 && !is_packed<Input_T>())>::type* = nullptr>
static void macsOnRange(const Input_T* __restrict inputs,
                                            const Weight_T* __restrict weights,
                                            Sum_T& __restrict weightedSum)
{
    weightedSum = dualMac<INPUTS_INC, WEIGHTS_INC>(inputs, weights, weightedSum);
    macsOnRange<NB_ITERATIONS-2, INPUTS_INC, WEIGHTS_INC>(
        inputs + 2*INPUTS_INC, weights + WEIGHTS_INC, weightedSum);
}

// ----------------------------------------------------------------------------
// Packed <2> weights - Packed <2> inputs
// ----------------------------------------------------------------------------

template<int NB_ITERATIONS,
            int INPUTS_INC = 1,
            int WEIGHTS_INC = 1,
            typename Weight_T, typename Sum_T,
            class Input_T,
            typename std::enable_if<(is_packed<Weight_T>()
            && n_pack<Weight_T>() == n_pack<Input_T>()
            && NB_ITERATIONS == 1)>::type* = nullptr>
static void macsOnRange(const Input_T* __restrict inputs,
                                            const Weight_T* __restrict weights,
                                            Sum_T& __restrict weightedSum)
{
    weightedSum += inputs[0*INPUTS_INC].rev_fields.op0
                    * weights[0*WEIGHTS_INC].rev_fields.op0;
}

template<int INPUTS_INC = 1,
            int WEIGHTS_INC = 1,
            typename Input_T,
            typename Weight_T, typename Sum_T,
            typename std::enable_if<(n_pack<Weight_T>() == 2
            && n_pack<Input_T>() == 2)>::type* = nullptr>
static Sum_T dualMac(const Input_T* __restrict inputs,
                                        const Weight_T* __restrict weights,
                                        Sum_T weightedSum)
{
    weightedSum
        + inputs[0*INPUTS_INC].rev_fields.op0
            * weights[0*WEIGHTS_INC].rev_fields.op0
        += inputs[0*INPUTS_INC].rev_fields.op1
            * weights[0*WEIGHTS_INC].rev_fields.op1;

    return weightedSum;
}

template<int NB_ITERATIONS,
            int INPUTS_INC = 1,
            int WEIGHTS_INC = 1,
            typename Weight_T, typename Sum_T,
            class Input_T,
            typename std::enable_if<(n_pack<Weight_T>() == 2
            && NB_ITERATIONS >=2 && n_pack<Input_T>() == 2)>::type* = nullptr>
static void macsOnRange(const Input_T* __restrict inputs,
                                            const Weight_T* __restrict weights,
                                            Sum_T& __restrict weightedSum)
{
    weightedSum = dualMac<INPUTS_INC, WEIGHTS_INC>(inputs, weights, weightedSum);
    macsOnRange<NB_ITERATIONS-2, INPUTS_INC, WEIGHTS_INC>(
        inputs + INPUTS_INC, weights + WEIGHTS_INC, weightedSum);
}

// ----------------------------------------------------------------------------
// Unpacked weights - Packed <*> inputs
// ----------------------------------------------------------------------------

template<int NB_ITERATIONS,
        int INPUTS_INC = 1,
        int WEIGHTS_INC = 1,
        typename Weight_T, typename Sum_T,
        class Input_T,
        typename std::enable_if<(!is_packed<Weight_T>()
        && NB_ITERATIONS == 1 && is_packed<Input_T>())>::type* = nullptr>
static void macsOnRange(const Input_T* __restrict inputs,
                                            const Weight_T* __restrict weights,
                                            Sum_T& __restrict weightedSum)
{
    weightedSum += inputs[0*INPUTS_INC].rev_fields.op0 * weights[0*WEIGHTS_INC];
}

// ----------------------------------------------------------------------------
// Unpacked weights - Packed <2> inputs
// ----------------------------------------------------------------------------

template<int INPUTS_INC = 1,
            int WEIGHTS_INC = 1,
            typename Input_T,
            typename Weight_T, typename Sum_T,
            typename std::enable_if<(!is_packed<Weight_T>()
            && n_pack<Input_T>() == 2)>::type* = nullptr>
static Sum_T dualMac(const Input_T* __restrict inputs,
                                        const Weight_T* __restrict weights,
                                        Sum_T weightedSum)
{
    weightedSum += inputs[0*INPUTS_INC].rev_fields.op0 * weights[0*WEIGHTS_INC]
        + inputs[0*INPUTS_INC].rev_fields.op1 * weights[1*WEIGHTS_INC];

    return weightedSum;
}

template<int NB_ITERATIONS,
            int INPUTS_INC = 1,
            int WEIGHTS_INC = 1,
            typename Weight_T, typename Sum_T,
            class Input_T,
            typename std::enable_if<(!is_packed<Weight_T>()
            && NB_ITERATIONS >= 2 && n_pack<Input_T>() == 2)>::type* = nullptr>
static void macsOnRange(const Input_T* __restrict inputs,
                                            const Weight_T* __restrict weights,
                                            Sum_T& __restrict weightedSum)
{
    weightedSum = dualMac<INPUTS_INC, WEIGHTS_INC>(inputs, weights, weightedSum);
    macsOnRange<NB_ITERATIONS-2, INPUTS_INC, WEIGHTS_INC>(
        inputs + INPUTS_INC, weights + 2*WEIGHTS_INC, weightedSum);
}

// ----------------------------------------------------------------------------
// Packed <4> weights - Unpacked inputs
// ----------------------------------------------------------------------------

template<int INPUTS_INC = 1,
            int WEIGHTS_INC = 1,
            typename Input_T,
            typename Weight_T, typename Sum_T,
            typename std::enable_if<(n_pack<Weight_T>() == 4
            && !is_packed<Input_T>())>::type* = nullptr>
static Sum_T dualMac(const Input_T* __restrict inputs,
                                        const Weight_T* __restrict weights,
                                        Sum_T weightedSum)
{
    weightedSum += inputs[0*INPUTS_INC] * weights[0*WEIGHTS_INC].rev_fields.op0
        + inputs[1*INPUTS_INC] * weights[0*WEIGHTS_INC].rev_fields.op1;

    return weightedSum;
}

template<int INPUTS_INC = 1,
            int WEIGHTS_INC = 1,
            typename Input_T,
            typename Weight_T, typename Sum_T,
            typename std::enable_if<(n_pack<Weight_T>() == 4
            && !is_packed<Input_T>())>::type* = nullptr>
static Sum_T tripleMac(const Input_T* __restrict inputs,
                                        const Weight_T* __restrict weights,
                                        Sum_T weightedSum)
{
    weightedSum += inputs[0*INPUTS_INC] * weights[0*WEIGHTS_INC].rev_fields.op0
        + inputs[1*INPUTS_INC] * weights[0*WEIGHTS_INC].rev_fields.op1
        + inputs[2*INPUTS_INC] * weights[0*WEIGHTS_INC].rev_fields.op2;

    return weightedSum;
}

template<int INPUTS_INC = 1,
            int WEIGHTS_INC = 1,
            typename Input_T,
            typename Weight_T, typename Sum_T,
            typename std::enable_if<(n_pack<Weight_T>() == 4
            && !is_packed<Input_T>())>::type* = nullptr>
static Sum_T quadMac(const Input_T* __restrict inputs,
                                        const Weight_T* __restrict weights,
                                        Sum_T weightedSum)
{
    weightedSum += inputs[0*INPUTS_INC] * weights[0*WEIGHTS_INC].rev_fields.op0
        + inputs[1*INPUTS_INC] * weights[0*WEIGHTS_INC].rev_fields.op1
        + inputs[2*INPUTS_INC] * weights[0*WEIGHTS_INC].rev_fields.op2
        + inputs[3*INPUTS_INC] * weights[0*WEIGHTS_INC].rev_fields.op3;

    return weightedSum;
}

template<int NB_ITERATIONS,
            int INPUTS_INC = 1,
            int WEIGHTS_INC = 1,
            typename Weight_T, typename Sum_T,
            class Input_T,
            typename std::enable_if<(n_pack<Weight_T>() == 4
            && NB_ITERATIONS == 2 && !is_packed<Input_T>())>::type* = nullptr>
static void macsOnRange(const Input_T* __restrict inputs,
                                            const Weight_T* __restrict weights,
                                            Sum_T& __restrict weightedSum)
{
    weightedSum = dualMac<INPUTS_INC, WEIGHTS_INC>(inputs, weights, weightedSum);
}

template<int NB_ITERATIONS,
            int INPUTS_INC = 1,
            int WEIGHTS_INC = 1,
            typename Weight_T, typename Sum_T,
            class Input_T,
            typename std::enable_if<(n_pack<Weight_T>() == 4
            && NB_ITERATIONS == 3 && !is_packed<Input_T>())>::type* = nullptr>
static void macsOnRange(const Input_T* __restrict inputs,
                                            const Weight_T* __restrict weights,
                                            Sum_T& __restrict weightedSum)
{
    weightedSum = tripleMac<INPUTS_INC, WEIGHTS_INC>(inputs, weights, weightedSum);
}

template<int NB_ITERATIONS,
            int INPUTS_INC = 1,
            int WEIGHTS_INC = 1,
            typename Weight_T, typename Sum_T,
            class Input_T,
            typename std::enable_if<(n_pack<Weight_T>() == 4
            && NB_ITERATIONS >= 4 && !is_packed<Input_T>())>::type* = nullptr>
static void macsOnRange(const Input_T* __restrict inputs,
                                            const Weight_T* __restrict weights,
                                            Sum_T& __restrict weightedSum)
{
    weightedSum = quadMac<INPUTS_INC, WEIGHTS_INC>(inputs, weights, weightedSum);
    macsOnRange<NB_ITERATIONS-4, INPUTS_INC, WEIGHTS_INC>(
        inputs + 4*INPUTS_INC, weights + WEIGHTS_INC, weightedSum);
}

// ----------------------------------------------------------------------------
// Packed <8> weights - Unpacked inputs
// ----------------------------------------------------------------------------

template<int NB_ITERATIONS,
            int INPUTS_INC = 1,
            int WEIGHTS_INC = 1,
            typename Weight_T, typename Sum_T,
            class Input_T,
            typename std::enable_if<(n_pack<Weight_T>() == 8 && !std::is_unsigned<Weight_T>()
            && NB_ITERATIONS == 1 && !is_packed<Input_T>())>::type* = nullptr>
static void macsOnRange(const Input_T* __restrict inputs,
                                            const Weight_T* __restrict weights,
                                            Sum_T& __restrict weightedSum)
{
    weightedSum += ((weights[0*WEIGHTS_INC].rev_fields.op0 == 0)
            ? (Sum_T)(-(*inputs)) : (Sum_T)(*inputs));
}

template<int NB_ITERATIONS,
            int INPUTS_INC = 1,
            int WEIGHTS_INC = 1,
            typename Weight_T, typename Sum_T,
            class Input_T,
            typename std::enable_if<(n_pack<Weight_T>() == 8 && !std::is_unsigned<Weight_T>()
            && NB_ITERATIONS == 2 && !is_packed<Input_T>())>::type* = nullptr>
static void macsOnRange(const Input_T* __restrict inputs,
                                            const Weight_T* __restrict weights,
                                            Sum_T& __restrict weightedSum)
{
    weightedSum += ((weights[0*WEIGHTS_INC].rev_fields.op0 == 0)
            ? (Sum_T)(-inputs[0*INPUTS_INC]) : (Sum_T)inputs[0*INPUTS_INC])
        + ((weights[0*WEIGHTS_INC].rev_fields.op1 == 0)
            ? (Sum_T)(-inputs[1*INPUTS_INC]) : (Sum_T)inputs[1*INPUTS_INC]);
}

template<int NB_ITERATIONS,
            int INPUTS_INC = 1,
            int WEIGHTS_INC = 1,
            typename Weight_T, typename Sum_T,
            class Input_T,
            typename std::enable_if<(n_pack<Weight_T>() == 8 && !std::is_unsigned<Weight_T>()
            && NB_ITERATIONS == 3 && !is_packed<Input_T>())>::type* = nullptr>
static void macsOnRange(const Input_T* __restrict inputs,
                                            const Weight_T* __restrict weights,
                                            Sum_T& __restrict weightedSum)
{
    weightedSum += ((weights[0*WEIGHTS_INC].rev_fields.op0 == 0)
            ? (Sum_T)(-inputs[0*INPUTS_INC]) : (Sum_T)inputs[0*INPUTS_INC])
        + ((weights[0*WEIGHTS_INC].rev_fields.op1 == 0)
            ? (Sum_T)(-inputs[1*INPUTS_INC]) : (Sum_T)inputs[1*INPUTS_INC])
        + ((weights[0*WEIGHTS_INC].rev_fields.op2 == 0)
            ? (Sum_T)(-inputs[2*INPUTS_INC]) : (Sum_T)inputs[2*INPUTS_INC]);
}

template<int NB_ITERATIONS,
            int INPUTS_INC = 1,
            int WEIGHTS_INC = 1,
            typename Weight_T, typename Sum_T,
            class Input_T,
            typename std::enable_if<(n_pack<Weight_T>() == 8 && !std::is_unsigned<Weight_T>()
            && NB_ITERATIONS == 4 && !is_packed<Input_T>())>::type* = nullptr>
static void macsOnRange(const Input_T* __restrict inputs,
                                            const Weight_T* __restrict weights,
                                            Sum_T& __restrict weightedSum)
{
    weightedSum += ((weights[0*WEIGHTS_INC].rev_fields.op0 == 0)
            ? (Sum_T)(-inputs[0*INPUTS_INC]) : (Sum_T)inputs[0*INPUTS_INC])
        + ((weights[0*WEIGHTS_INC].rev_fields.op1 == 0)
            ? (Sum_T)(-inputs[1*INPUTS_INC]) : (Sum_T)inputs[1*INPUTS_INC])
        + ((weights[0*WEIGHTS_INC].rev_fields.op2 == 0)
            ? (Sum_T)(-inputs[2*INPUTS_INC]) : (Sum_T)inputs[2*INPUTS_INC])
        + ((weights[0*WEIGHTS_INC].rev_fields.op3 == 0)
            ? (Sum_T)(-inputs[3*INPUTS_INC]) : (Sum_T)inputs[3*INPUTS_INC]);
}

template<int NB_ITERATIONS,
            int INPUTS_INC = 1,
            int WEIGHTS_INC = 1,
            typename Weight_T, typename Sum_T,
            class Input_T,
            typename std::enable_if<(n_pack<Weight_T>() == 8 && !std::is_unsigned<Weight_T>()
            && NB_ITERATIONS == 5 && !is_packed<Input_T>())>::type* = nullptr>
static void macsOnRange(const Input_T* __restrict inputs,
                                            const Weight_T* __restrict weights,
                                            Sum_T& __restrict weightedSum)
{
    weightedSum += ((weights[0*WEIGHTS_INC].rev_fields.op0 == 0)
            ? (Sum_T)(-inputs[0*INPUTS_INC]) : (Sum_T)inputs[0*INPUTS_INC])
        + ((weights[0*WEIGHTS_INC].rev_fields.op1 == 0)
            ? (Sum_T)(-inputs[1*INPUTS_INC]) : (Sum_T)inputs[1*INPUTS_INC])
        + ((weights[0*WEIGHTS_INC].rev_fields.op2 == 0)
            ? (Sum_T)(-inputs[2*INPUTS_INC]) : (Sum_T)inputs[2*INPUTS_INC])
        + ((weights[0*WEIGHTS_INC].rev_fields.op3 == 0)
            ? (Sum_T)(-inputs[3*INPUTS_INC]) : (Sum_T)inputs[3*INPUTS_INC])
        + ((weights[0*WEIGHTS_INC].rev_fields.op4 == 0)
            ? (Sum_T)(-inputs[4*INPUTS_INC]) : (Sum_T)inputs[4*INPUTS_INC]);
}

template<int NB_ITERATIONS,
            int INPUTS_INC = 1,
            int WEIGHTS_INC = 1,
            typename Weight_T, typename Sum_T,
            class Input_T,
            typename std::enable_if<(n_pack<Weight_T>() == 8 && !std::is_unsigned<Weight_T>()
            && NB_ITERATIONS == 6 && !is_packed<Input_T>())>::type* = nullptr>
static void macsOnRange(const Input_T* __restrict inputs,
                                            const Weight_T* __restrict weights,
                                            Sum_T& __restrict weightedSum)
{
    weightedSum += ((weights[0*WEIGHTS_INC].rev_fields.op0 == 0)
            ? (Sum_T)(-inputs[0*INPUTS_INC]) : (Sum_T)inputs[0*INPUTS_INC])
        + ((weights[0*WEIGHTS_INC].rev_fields.op1 == 0)
            ? (Sum_T)(-inputs[1*INPUTS_INC]) : (Sum_T)inputs[1*INPUTS_INC])
        + ((weights[0*WEIGHTS_INC].rev_fields.op2 == 0)
            ? (Sum_T)(-inputs[2*INPUTS_INC]) : (Sum_T)inputs[2*INPUTS_INC])
        + ((weights[0*WEIGHTS_INC].rev_fields.op3 == 0)
            ? (Sum_T)(-inputs[3*INPUTS_INC]) : (Sum_T)inputs[3*INPUTS_INC])
        + ((weights[0*WEIGHTS_INC].rev_fields.op4 == 0)
            ? (Sum_T)(-inputs[4*INPUTS_INC]) : (Sum_T)inputs[4*INPUTS_INC])
        + ((weights[0*WEIGHTS_INC].rev_fields.op5 == 0)
            ? (Sum_T)(-inputs[5*INPUTS_INC]) : (Sum_T)inputs[5*INPUTS_INC]);
}

template<int NB_ITERATIONS,
            int INPUTS_INC = 1,
            int WEIGHTS_INC = 1,
            typename Weight_T, typename Sum_T,
            class Input_T,
            typename std::enable_if<(n_pack<Weight_T>() == 8 && !std::is_unsigned<Weight_T>()
            && NB_ITERATIONS == 7 && !is_packed<Input_T>())>::type* = nullptr>
static void macsOnRange(const Input_T* __restrict inputs,
                                            const Weight_T* __restrict weights,
                                            Sum_T& __restrict weightedSum)
{
    weightedSum += ((weights[0*WEIGHTS_INC].rev_fields.op0 == 0)
            ? (Sum_T)(-inputs[0*INPUTS_INC]) : (Sum_T)inputs[0*INPUTS_INC])
        + ((weights[0*WEIGHTS_INC].rev_fields.op1 == 0)
            ? (Sum_T)(-inputs[1*INPUTS_INC]) : (Sum_T)inputs[1*INPUTS_INC])
        + ((weights[0*WEIGHTS_INC].rev_fields.op2 == 0)
            ? (Sum_T)(-inputs[2*INPUTS_INC]) : (Sum_T)inputs[2*INPUTS_INC])
        + ((weights[0*WEIGHTS_INC].rev_fields.op3 == 0)
            ? (Sum_T)(-inputs[3*INPUTS_INC]) : (Sum_T)inputs[3*INPUTS_INC])
        + ((weights[0*WEIGHTS_INC].rev_fields.op4 == 0)
            ? (Sum_T)(-inputs[4*INPUTS_INC]) : (Sum_T)inputs[4*INPUTS_INC])
        + ((weights[0*WEIGHTS_INC].rev_fields.op5 == 0)
            ? (Sum_T)(-inputs[5*INPUTS_INC]) : (Sum_T)inputs[5*INPUTS_INC])
        + ((weights[0*WEIGHTS_INC].rev_fields.op6 == 0)
            ? (Sum_T)(-inputs[6*INPUTS_INC]) : (Sum_T)inputs[6*INPUTS_INC]);
}

template<int INPUTS_INC = 1,
            int WEIGHTS_INC = 1,
            typename Input_T,
            typename Weight_T, typename Sum_T,
            typename std::enable_if<(n_pack<Weight_T>() == 8 && !std::is_unsigned<Weight_T>()
            && !is_packed<Input_T>())>::type* = nullptr>
static Sum_T octoMac(const Input_T* __restrict inputs,
                                        const Weight_T* __restrict weights,
                                        Sum_T weightedSum)
{
    weightedSum += ((weights[0*WEIGHTS_INC].rev_fields.op0 == 0)
            ? (Sum_T)(-inputs[0*INPUTS_INC]) : (Sum_T)inputs[0*INPUTS_INC])
        + ((weights[0*WEIGHTS_INC].rev_fields.op1 == 0)
            ? (Sum_T)(-inputs[1*INPUTS_INC]) : (Sum_T)inputs[1*INPUTS_INC])
        + ((weights[0*WEIGHTS_INC].rev_fields.op2 == 0)
            ? (Sum_T)(-inputs[2*INPUTS_INC]) : (Sum_T)inputs[2*INPUTS_INC])
        + ((weights[0*WEIGHTS_INC].rev_fields.op3 == 0)
            ? (Sum_T)(-inputs[3*INPUTS_INC]) : (Sum_T)inputs[3*INPUTS_INC])
        + ((weights[0*WEIGHTS_INC].rev_fields.op4 == 0)
            ? (Sum_T)(-inputs[4*INPUTS_INC]) : (Sum_T)inputs[4*INPUTS_INC])
        + ((weights[0*WEIGHTS_INC].rev_fields.op5 == 0)
            ? (Sum_T)(-inputs[5*INPUTS_INC]) : (Sum_T)inputs[5*INPUTS_INC])
        + ((weights[0*WEIGHTS_INC].rev_fields.op6 == 0)
            ? (Sum_T)(-inputs[6*INPUTS_INC]) : (Sum_T)inputs[6*INPUTS_INC])
        + ((weights[0*WEIGHTS_INC].rev_fields.op7 == 0)
            ? (Sum_T)(-inputs[7*INPUTS_INC]) : (Sum_T)inputs[7*INPUTS_INC]);

    return weightedSum;
}

template<int NB_ITERATIONS,
            int INPUTS_INC = 1,
            int WEIGHTS_INC = 1,
            typename Weight_T, typename Sum_T,
            class Input_T,
            typename std::enable_if<(n_pack<Weight_T>() == 8
            && NB_ITERATIONS >= 8 && !is_packed<Input_T>())>::type* = nullptr>
static void macsOnRange(const Input_T* __restrict inputs,
                                            const Weight_T* __restrict weights,
                                            Sum_T& __restrict weightedSum)
{
    weightedSum = octoMac<INPUTS_INC, WEIGHTS_INC>(inputs, weights, weightedSum);
    macsOnRange<NB_ITERATIONS-8, INPUTS_INC, WEIGHTS_INC>(
        inputs + 8*INPUTS_INC, weights + WEIGHTS_INC, weightedSum);
}

// ----------------------------------------------------------------------------
// Packed <8> weights - Packed <2> inputs
// ----------------------------------------------------------------------------

template<int NB_ITERATIONS,
            int INPUTS_INC = 1,
            int WEIGHTS_INC = 1,
            typename Weight_T, typename Sum_T,
            class Input_T,
            typename std::enable_if<(n_pack<Weight_T>() == 8 && !std::is_unsigned<Weight_T>()
            && NB_ITERATIONS == 1 && n_pack<Input_T>() == 2)>::type* = nullptr>
static void macsOnRange(const Input_T* __restrict inputs,
                                            const Weight_T* __restrict weights,
                                            Sum_T& __restrict weightedSum)
{
    weightedSum += ((weights[0*WEIGHTS_INC].rev_fields.op0 == 0)
            ? (Sum_T)(-inputs[0*INPUTS_INC].rev_fields.op0) : (Sum_T)inputs[0*INPUTS_INC].rev_fields.op0);
}

template<int NB_ITERATIONS,
            int INPUTS_INC = 1,
            int WEIGHTS_INC = 1,
            typename Weight_T, typename Sum_T,
            class Input_T,
            typename std::enable_if<(n_pack<Weight_T>() == 8 && !std::is_unsigned<Weight_T>()
            && NB_ITERATIONS == 2 && n_pack<Input_T>() == 2)>::type* = nullptr>
static void macsOnRange(const Input_T* __restrict inputs,
                                            const Weight_T* __restrict weights,
                                            Sum_T& __restrict weightedSum)
{
    weightedSum += ((weights[0*WEIGHTS_INC].rev_fields.op0 == 0)
            ? (Sum_T)(-inputs[0*INPUTS_INC].rev_fields.op0) : (Sum_T)inputs[0*INPUTS_INC].rev_fields.op0)
        + ((weights[0*WEIGHTS_INC].rev_fields.op1 == 0)
            ? (Sum_T)(-inputs[0*INPUTS_INC].rev_fields.op1) : (Sum_T)inputs[0*INPUTS_INC].rev_fields.op1);
}

template<int NB_ITERATIONS,
            int INPUTS_INC = 1,
            int WEIGHTS_INC = 1,
            typename Weight_T, typename Sum_T,
            class Input_T,
            typename std::enable_if<(n_pack<Weight_T>() == 8 && !std::is_unsigned<Weight_T>()
            && NB_ITERATIONS == 3 && n_pack<Input_T>() == 2)>::type* = nullptr>
static void macsOnRange(const Input_T* __restrict inputs,
                                            const Weight_T* __restrict weights,
                                            Sum_T& __restrict weightedSum)
{
    weightedSum += ((weights[0*WEIGHTS_INC].rev_fields.op0 == 0)
            ? (Sum_T)(-inputs[0*INPUTS_INC].rev_fields.op0) : (Sum_T)inputs[0*INPUTS_INC].rev_fields.op0)
        + ((weights[0*WEIGHTS_INC].rev_fields.op1 == 0)
            ? (Sum_T)(-inputs[0*INPUTS_INC].rev_fields.op1) : (Sum_T)inputs[0*INPUTS_INC].rev_fields.op1)
        + ((weights[0*WEIGHTS_INC].rev_fields.op2 == 0)
            ? (Sum_T)(-inputs[1*INPUTS_INC].rev_fields.op0) : (Sum_T)inputs[1*INPUTS_INC].rev_fields.op0);
}

template<int NB_ITERATIONS,
            int INPUTS_INC = 1,
            int WEIGHTS_INC = 1,
            typename Weight_T, typename Sum_T,
            class Input_T,
            typename std::enable_if<(n_pack<Weight_T>() == 8 && !std::is_unsigned<Weight_T>()
            && NB_ITERATIONS == 4 && n_pack<Input_T>() == 2)>::type* = nullptr>
static void macsOnRange(const Input_T* __restrict inputs,
                                            const Weight_T* __restrict weights,
                                            Sum_T& __restrict weightedSum)
{
    weightedSum += ((weights[0*WEIGHTS_INC].rev_fields.op0 == 0)
            ? (Sum_T)(-inputs[0*INPUTS_INC].rev_fields.op0) : (Sum_T)inputs[0*INPUTS_INC].rev_fields.op0)
        + ((weights[0*WEIGHTS_INC].rev_fields.op1 == 0)
            ? (Sum_T)(-inputs[0*INPUTS_INC].rev_fields.op1) : (Sum_T)inputs[0*INPUTS_INC].rev_fields.op1)
        + ((weights[0*WEIGHTS_INC].rev_fields.op2 == 0)
            ? (Sum_T)(-inputs[1*INPUTS_INC].rev_fields.op0) : (Sum_T)inputs[1*INPUTS_INC].rev_fields.op0)
        + ((weights[0*WEIGHTS_INC].rev_fields.op3 == 0)
            ? (Sum_T)(-inputs[1*INPUTS_INC].rev_fields.op1) : (Sum_T)inputs[1*INPUTS_INC].rev_fields.op1);
}

template<int NB_ITERATIONS,
            int INPUTS_INC = 1,
            int WEIGHTS_INC = 1,
            typename Weight_T, typename Sum_T,
            class Input_T,
            typename std::enable_if<(n_pack<Weight_T>() == 8 && !std::is_unsigned<Weight_T>()
            && NB_ITERATIONS == 5 && n_pack<Input_T>() == 2)>::type* = nullptr>
static void macsOnRange(const Input_T* __restrict inputs,
                                            const Weight_T* __restrict weights,
                                            Sum_T& __restrict weightedSum)
{
    weightedSum += ((weights[0*WEIGHTS_INC].rev_fields.op0 == 0)
            ? (Sum_T)(-inputs[0*INPUTS_INC].rev_fields.op0) : (Sum_T)inputs[0*INPUTS_INC].rev_fields.op0)
        + ((weights[0*WEIGHTS_INC].rev_fields.op1 == 0)
            ? (Sum_T)(-inputs[0*INPUTS_INC].rev_fields.op1) : (Sum_T)inputs[0*INPUTS_INC].rev_fields.op1)
        + ((weights[0*WEIGHTS_INC].rev_fields.op2 == 0)
            ? (Sum_T)(-inputs[1*INPUTS_INC].rev_fields.op0) : (Sum_T)inputs[1*INPUTS_INC].rev_fields.op0)
        + ((weights[0*WEIGHTS_INC].rev_fields.op3 == 0)
            ? (Sum_T)(-inputs[1*INPUTS_INC].rev_fields.op1) : (Sum_T)inputs[1*INPUTS_INC].rev_fields.op1)
        + ((weights[0*WEIGHTS_INC].rev_fields.op4 == 0)
            ? (Sum_T)(-inputs[2*INPUTS_INC].rev_fields.op0) : (Sum_T)inputs[2*INPUTS_INC].rev_fields.op0);
}

template<int NB_ITERATIONS,
            int INPUTS_INC = 1,
            int WEIGHTS_INC = 1,
            typename Weight_T, typename Sum_T,
            class Input_T,
            typename std::enable_if<(n_pack<Weight_T>() == 8 && !std::is_unsigned<Weight_T>()
            && NB_ITERATIONS == 6 && n_pack<Input_T>() == 2)>::type* = nullptr>
static void macsOnRange(const Input_T* __restrict inputs,
                                            const Weight_T* __restrict weights,
                                            Sum_T& __restrict weightedSum)
{
    weightedSum += ((weights[0*WEIGHTS_INC].rev_fields.op0 == 0)
            ? (Sum_T)(-inputs[0*INPUTS_INC].rev_fields.op0) : (Sum_T)inputs[0*INPUTS_INC].rev_fields.op0)
        + ((weights[0*WEIGHTS_INC].rev_fields.op1 == 0)
            ? (Sum_T)(-inputs[0*INPUTS_INC].rev_fields.op1) : (Sum_T)inputs[0*INPUTS_INC].rev_fields.op1)
        + ((weights[0*WEIGHTS_INC].rev_fields.op2 == 0)
            ? (Sum_T)(-inputs[1*INPUTS_INC].rev_fields.op0) : (Sum_T)inputs[1*INPUTS_INC].rev_fields.op0)
        + ((weights[0*WEIGHTS_INC].rev_fields.op3 == 0)
            ? (Sum_T)(-inputs[1*INPUTS_INC].rev_fields.op1) : (Sum_T)inputs[1*INPUTS_INC].rev_fields.op1)
        + ((weights[0*WEIGHTS_INC].rev_fields.op4 == 0)
            ? (Sum_T)(-inputs[2*INPUTS_INC].rev_fields.op0) : (Sum_T)inputs[2*INPUTS_INC].rev_fields.op0)
        + ((weights[0*WEIGHTS_INC].rev_fields.op5 == 0)
            ? (Sum_T)(-inputs[2*INPUTS_INC].rev_fields.op1) : (Sum_T)inputs[2*INPUTS_INC].rev_fields.op1);
}

template<int NB_ITERATIONS,
            int INPUTS_INC = 1,
            int WEIGHTS_INC = 1,
            typename Weight_T, typename Sum_T,
            class Input_T,
            typename std::enable_if<(n_pack<Weight_T>() == 8 && !std::is_unsigned<Weight_T>()
            && NB_ITERATIONS == 7 && n_pack<Input_T>() == 2)>::type* = nullptr>
static void macsOnRange(const Input_T* __restrict inputs,
                                            const Weight_T* __restrict weights,
                                            Sum_T& __restrict weightedSum)
{
    weightedSum += ((weights[0*WEIGHTS_INC].rev_fields.op0 == 0)
            ? (Sum_T)(-inputs[0*INPUTS_INC].rev_fields.op0) : (Sum_T)inputs[0*INPUTS_INC].rev_fields.op0)
        + ((weights[0*WEIGHTS_INC].rev_fields.op1 == 0)
            ? (Sum_T)(-inputs[0*INPUTS_INC].rev_fields.op1) : (Sum_T)inputs[0*INPUTS_INC].rev_fields.op1)
        + ((weights[0*WEIGHTS_INC].rev_fields.op2 == 0)
            ? (Sum_T)(-inputs[1*INPUTS_INC].rev_fields.op0) : (Sum_T)inputs[1*INPUTS_INC].rev_fields.op0)
        + ((weights[0*WEIGHTS_INC].rev_fields.op3 == 0)
            ? (Sum_T)(-inputs[1*INPUTS_INC].rev_fields.op1) : (Sum_T)inputs[1*INPUTS_INC].rev_fields.op1)
        + ((weights[0*WEIGHTS_INC].rev_fields.op4 == 0)
            ? (Sum_T)(-inputs[2*INPUTS_INC].rev_fields.op0) : (Sum_T)inputs[2*INPUTS_INC].rev_fields.op0)
        + ((weights[0*WEIGHTS_INC].rev_fields.op5 == 0)
            ? (Sum_T)(-inputs[2*INPUTS_INC].rev_fields.op1) : (Sum_T)inputs[2*INPUTS_INC].rev_fields.op1)
        + ((weights[0*WEIGHTS_INC].rev_fields.op6 == 0)
            ? (Sum_T)(-inputs[3*INPUTS_INC].rev_fields.op0) : (Sum_T)inputs[3*INPUTS_INC].rev_fields.op0);
}

template<int INPUTS_INC = 1,
            int WEIGHTS_INC = 1,
            typename Input_T,
            typename Weight_T, typename Sum_T,
            typename std::enable_if<(n_pack<Weight_T>() == 8 && !std::is_unsigned<Weight_T>()
            && n_pack<Input_T>() == 2)>::type* = nullptr>
static Sum_T octoMac(const Input_T* __restrict inputs,
                                        const Weight_T* __restrict weights,
                                        Sum_T weightedSum)
{
    weightedSum += ((weights[0*WEIGHTS_INC].rev_fields.op0 == 0)
            ? (Sum_T)(-inputs[0*INPUTS_INC].rev_fields.op0) : (Sum_T)inputs[0*INPUTS_INC].rev_fields.op0)
        + ((weights[0*WEIGHTS_INC].rev_fields.op1 == 0)
            ? (Sum_T)(-inputs[0*INPUTS_INC].rev_fields.op1) : (Sum_T)inputs[0*INPUTS_INC].rev_fields.op1)
        + ((weights[0*WEIGHTS_INC].rev_fields.op2 == 0)
            ? (Sum_T)(-inputs[1*INPUTS_INC].rev_fields.op0) : (Sum_T)inputs[1*INPUTS_INC].rev_fields.op0)
        + ((weights[0*WEIGHTS_INC].rev_fields.op3 == 0)
            ? (Sum_T)(-inputs[1*INPUTS_INC].rev_fields.op1) : (Sum_T)inputs[1*INPUTS_INC].rev_fields.op1)
        + ((weights[0*WEIGHTS_INC].rev_fields.op4 == 0)
            ? (Sum_T)(-inputs[2*INPUTS_INC].rev_fields.op0) : (Sum_T)inputs[2*INPUTS_INC].rev_fields.op0)
        + ((weights[0*WEIGHTS_INC].rev_fields.op5 == 0)
            ? (Sum_T)(-inputs[2*INPUTS_INC].rev_fields.op1) : (Sum_T)inputs[2*INPUTS_INC].rev_fields.op1)
        + ((weights[0*WEIGHTS_INC].rev_fields.op6 == 0)
            ? (Sum_T)(-inputs[3*INPUTS_INC].rev_fields.op0) : (Sum_T)inputs[3*INPUTS_INC].rev_fields.op0)
        + ((weights[0*WEIGHTS_INC].rev_fields.op7 == 0)
            ? (Sum_T)(-inputs[3*INPUTS_INC].rev_fields.op1) : (Sum_T)inputs[3*INPUTS_INC].rev_fields.op1);

    return weightedSum;
}

template<int NB_ITERATIONS,
            int INPUTS_INC = 1,
            int WEIGHTS_INC = 1,
            typename Weight_T, typename Sum_T,
            class Input_T,
            typename std::enable_if<(n_pack<Weight_T>() == 8
            && NB_ITERATIONS >= 8 && n_pack<Input_T>() == 2)>::type* = nullptr>
static void macsOnRange(const Input_T* __restrict inputs,
                                            const Weight_T* __restrict weights,
                                            Sum_T& __restrict weightedSum)
{
    weightedSum = octoMac<INPUTS_INC, WEIGHTS_INC>(inputs, weights, weightedSum);
    macsOnRange<NB_ITERATIONS-8, INPUTS_INC, WEIGHTS_INC>(
        inputs + 4*INPUTS_INC, weights + WEIGHTS_INC, weightedSum);
}

// ----------------------------------------------------------------------------
// Packed <8> weights - Packed <4> inputs
// ----------------------------------------------------------------------------

template<int NB_ITERATIONS,
            int INPUTS_INC = 1,
            int WEIGHTS_INC = 1,
            typename Weight_T, typename Sum_T,
            class Input_T,
            typename std::enable_if<(n_pack<Weight_T>() == 8 && !std::is_unsigned<Weight_T>()
            && NB_ITERATIONS == 1 && n_pack<Input_T>() == 4)>::type* = nullptr>
static void macsOnRange(const Input_T* __restrict inputs,
                                            const Weight_T* __restrict weights,
                                            Sum_T& __restrict weightedSum)
{
    weightedSum += ((weights[0*WEIGHTS_INC].rev_fields.op0 == 0)
            ? (Sum_T)(-inputs[0*INPUTS_INC].rev_fields.op0) : (Sum_T)inputs[0*INPUTS_INC].rev_fields.op0);
}

template<int NB_ITERATIONS,
            int INPUTS_INC = 1,
            int WEIGHTS_INC = 1,
            typename Weight_T, typename Sum_T,
            class Input_T,
            typename std::enable_if<(n_pack<Weight_T>() == 8 && !std::is_unsigned<Weight_T>()
            && NB_ITERATIONS == 2 && n_pack<Input_T>() == 4)>::type* = nullptr>
static void macsOnRange(const Input_T* __restrict inputs,
                                            const Weight_T* __restrict weights,
                                            Sum_T& __restrict weightedSum)
{
    weightedSum += ((weights[0*WEIGHTS_INC].rev_fields.op0 == 0)
            ? (Sum_T)(-inputs[0*INPUTS_INC].rev_fields.op0) : (Sum_T)inputs[0*INPUTS_INC].rev_fields.op0)
        + ((weights[0*WEIGHTS_INC].rev_fields.op1 == 0)
            ? (Sum_T)(-inputs[0*INPUTS_INC].rev_fields.op1) : (Sum_T)inputs[0*INPUTS_INC].rev_fields.op1);
}

template<int NB_ITERATIONS,
            int INPUTS_INC = 1,
            int WEIGHTS_INC = 1,
            typename Weight_T, typename Sum_T,
            class Input_T,
            typename std::enable_if<(n_pack<Weight_T>() == 8 && !std::is_unsigned<Weight_T>()
            && NB_ITERATIONS == 3 && n_pack<Input_T>() == 4)>::type* = nullptr>
static void macsOnRange(const Input_T* __restrict inputs,
                                            const Weight_T* __restrict weights,
                                            Sum_T& __restrict weightedSum)
{
    weightedSum += ((weights[0*WEIGHTS_INC].rev_fields.op0 == 0)
            ? (Sum_T)(-inputs[0*INPUTS_INC].rev_fields.op0) : (Sum_T)inputs[0*INPUTS_INC].rev_fields.op0)
        + ((weights[0*WEIGHTS_INC].rev_fields.op1 == 0)
            ? (Sum_T)(-inputs[0*INPUTS_INC].rev_fields.op1) : (Sum_T)inputs[0*INPUTS_INC].rev_fields.op1)
        + ((weights[0*WEIGHTS_INC].rev_fields.op2 == 0)
            ? (Sum_T)(-inputs[0*INPUTS_INC].rev_fields.op2) : (Sum_T)inputs[0*INPUTS_INC].rev_fields.op2);
}

template<int NB_ITERATIONS,
            int INPUTS_INC = 1,
            int WEIGHTS_INC = 1,
            typename Weight_T, typename Sum_T,
            class Input_T,
            typename std::enable_if<(n_pack<Weight_T>() == 8 && !std::is_unsigned<Weight_T>()
            && NB_ITERATIONS == 4 && n_pack<Input_T>() == 4)>::type* = nullptr>
static void macsOnRange(const Input_T* __restrict inputs,
                                            const Weight_T* __restrict weights,
                                            Sum_T& __restrict weightedSum)
{
    weightedSum += ((weights[0*WEIGHTS_INC].rev_fields.op0 == 0)
            ? (Sum_T)(-inputs[0*INPUTS_INC].rev_fields.op0) : (Sum_T)inputs[0*INPUTS_INC].rev_fields.op0)
        + ((weights[0*WEIGHTS_INC].rev_fields.op1 == 0)
            ? (Sum_T)(-inputs[0*INPUTS_INC].rev_fields.op1) : (Sum_T)inputs[0*INPUTS_INC].rev_fields.op1)
        + ((weights[0*WEIGHTS_INC].rev_fields.op2 == 0)
            ? (Sum_T)(-inputs[0*INPUTS_INC].rev_fields.op2) : (Sum_T)inputs[0*INPUTS_INC].rev_fields.op2)
        + ((weights[0*WEIGHTS_INC].rev_fields.op3 == 0)
            ? (Sum_T)(-inputs[0*INPUTS_INC].rev_fields.op3) : (Sum_T)inputs[0*INPUTS_INC].rev_fields.op3);
}

template<int NB_ITERATIONS,
            int INPUTS_INC = 1,
            int WEIGHTS_INC = 1,
            typename Weight_T, typename Sum_T,
            class Input_T,
            typename std::enable_if<(n_pack<Weight_T>() == 8 && !std::is_unsigned<Weight_T>()
            && NB_ITERATIONS == 5 && n_pack<Input_T>() == 4)>::type* = nullptr>
static void macsOnRange(const Input_T* __restrict inputs,
                                            const Weight_T* __restrict weights,
                                            Sum_T& __restrict weightedSum)
{
    weightedSum += ((weights[0*WEIGHTS_INC].rev_fields.op0 == 0)
            ? (Sum_T)(-inputs[0*INPUTS_INC].rev_fields.op0) : (Sum_T)inputs[0*INPUTS_INC].rev_fields.op0)
        + ((weights[0*WEIGHTS_INC].rev_fields.op1 == 0)
            ? (Sum_T)(-inputs[0*INPUTS_INC].rev_fields.op1) : (Sum_T)inputs[0*INPUTS_INC].rev_fields.op1)
        + ((weights[0*WEIGHTS_INC].rev_fields.op2 == 0)
            ? (Sum_T)(-inputs[0*INPUTS_INC].rev_fields.op2) : (Sum_T)inputs[0*INPUTS_INC].rev_fields.op2)
        + ((weights[0*WEIGHTS_INC].rev_fields.op3 == 0)
            ? (Sum_T)(-inputs[0*INPUTS_INC].rev_fields.op3) : (Sum_T)inputs[0*INPUTS_INC].rev_fields.op3)
        + ((weights[0*WEIGHTS_INC].rev_fields.op4 == 0)
            ? (Sum_T)(-inputs[1*INPUTS_INC].rev_fields.op0) : (Sum_T)inputs[1*INPUTS_INC].rev_fields.op0);
}

template<int NB_ITERATIONS,
            int INPUTS_INC = 1,
            int WEIGHTS_INC = 1,
            typename Weight_T, typename Sum_T,
            class Input_T,
            typename std::enable_if<(n_pack<Weight_T>() == 8 && !std::is_unsigned<Weight_T>()
            && NB_ITERATIONS == 6 && n_pack<Input_T>() == 4)>::type* = nullptr>
static void macsOnRange(const Input_T* __restrict inputs,
                                            const Weight_T* __restrict weights,
                                            Sum_T& __restrict weightedSum)
{
    weightedSum += ((weights[0*WEIGHTS_INC].rev_fields.op0 == 0)
            ? (Sum_T)(-inputs[0*INPUTS_INC].rev_fields.op0) : (Sum_T)inputs[0*INPUTS_INC].rev_fields.op0)
        + ((weights[0*WEIGHTS_INC].rev_fields.op1 == 0)
            ? (Sum_T)(-inputs[0*INPUTS_INC].rev_fields.op1) : (Sum_T)inputs[0*INPUTS_INC].rev_fields.op1)
        + ((weights[0*WEIGHTS_INC].rev_fields.op2 == 0)
            ? (Sum_T)(-inputs[0*INPUTS_INC].rev_fields.op2) : (Sum_T)inputs[0*INPUTS_INC].rev_fields.op2)
        + ((weights[0*WEIGHTS_INC].rev_fields.op3 == 0)
            ? (Sum_T)(-inputs[0*INPUTS_INC].rev_fields.op3) : (Sum_T)inputs[0*INPUTS_INC].rev_fields.op3)
        + ((weights[0*WEIGHTS_INC].rev_fields.op4 == 0)
            ? (Sum_T)(-inputs[1*INPUTS_INC].rev_fields.op0) : (Sum_T)inputs[1*INPUTS_INC].rev_fields.op0)
        + ((weights[0*WEIGHTS_INC].rev_fields.op5 == 0)
            ? (Sum_T)(-inputs[1*INPUTS_INC].rev_fields.op1) : (Sum_T)inputs[1*INPUTS_INC].rev_fields.op1);
}

template<int NB_ITERATIONS,
            int INPUTS_INC = 1,
            int WEIGHTS_INC = 1,
            typename Weight_T, typename Sum_T,
            class Input_T,
            typename std::enable_if<(n_pack<Weight_T>() == 8 && !std::is_unsigned<Weight_T>()
            && NB_ITERATIONS == 7 && n_pack<Input_T>() == 4)>::type* = nullptr>
static void macsOnRange(const Input_T* __restrict inputs,
                                            const Weight_T* __restrict weights,
                                            Sum_T& __restrict weightedSum)
{
    weightedSum += ((weights[0*WEIGHTS_INC].rev_fields.op0 == 0)
            ? (Sum_T)(-inputs[0*INPUTS_INC].rev_fields.op0) : (Sum_T)inputs[0*INPUTS_INC].rev_fields.op0)
        + ((weights[0*WEIGHTS_INC].rev_fields.op1 == 0)
            ? (Sum_T)(-inputs[0*INPUTS_INC].rev_fields.op1) : (Sum_T)inputs[0*INPUTS_INC].rev_fields.op1)
        + ((weights[0*WEIGHTS_INC].rev_fields.op2 == 0)
            ? (Sum_T)(-inputs[0*INPUTS_INC].rev_fields.op2) : (Sum_T)inputs[0*INPUTS_INC].rev_fields.op2)
        + ((weights[0*WEIGHTS_INC].rev_fields.op3 == 0)
            ? (Sum_T)(-inputs[0*INPUTS_INC].rev_fields.op3) : (Sum_T)inputs[0*INPUTS_INC].rev_fields.op3)
        + ((weights[0*WEIGHTS_INC].rev_fields.op4 == 0)
            ? (Sum_T)(-inputs[1*INPUTS_INC].rev_fields.op0) : (Sum_T)inputs[1*INPUTS_INC].rev_fields.op0)
        + ((weights[0*WEIGHTS_INC].rev_fields.op5 == 0)
            ? (Sum_T)(-inputs[1*INPUTS_INC].rev_fields.op1) : (Sum_T)inputs[1*INPUTS_INC].rev_fields.op1)
        + ((weights[0*WEIGHTS_INC].rev_fields.op6 == 0)
            ? (Sum_T)(-inputs[1*INPUTS_INC].rev_fields.op2) : (Sum_T)inputs[1*INPUTS_INC].rev_fields.op2);
}

template<int INPUTS_INC = 1,
            int WEIGHTS_INC = 1,
            typename Input_T,
            typename Weight_T, typename Sum_T,
            typename std::enable_if<(n_pack<Weight_T>() == 8 && !std::is_unsigned<Weight_T>()
            && n_pack<Input_T>() == 4)>::type* = nullptr>
static Sum_T octoMac(const Input_T* __restrict inputs,
                                        const Weight_T* __restrict weights,
                                        Sum_T weightedSum)
{
    weightedSum += ((weights[0*WEIGHTS_INC].rev_fields.op0 == 0)
            ? (Sum_T)(-inputs[0*INPUTS_INC].rev_fields.op0) : (Sum_T)inputs[0*INPUTS_INC].rev_fields.op0)
        + ((weights[0*WEIGHTS_INC].rev_fields.op1 == 0)
            ? (Sum_T)(-inputs[0*INPUTS_INC].rev_fields.op1) : (Sum_T)inputs[0*INPUTS_INC].rev_fields.op1)
        + ((weights[0*WEIGHTS_INC].rev_fields.op2 == 0)
            ? (Sum_T)(-inputs[0*INPUTS_INC].rev_fields.op2) : (Sum_T)inputs[0*INPUTS_INC].rev_fields.op2)
        + ((weights[0*WEIGHTS_INC].rev_fields.op3 == 0)
            ? (Sum_T)(-inputs[0*INPUTS_INC].rev_fields.op3) : (Sum_T)inputs[0*INPUTS_INC].rev_fields.op3)
        + ((weights[0*WEIGHTS_INC].rev_fields.op4 == 0)
            ? (Sum_T)(-inputs[1*INPUTS_INC].rev_fields.op0) : (Sum_T)inputs[1*INPUTS_INC].rev_fields.op0)
        + ((weights[0*WEIGHTS_INC].rev_fields.op5 == 0)
            ? (Sum_T)(-inputs[1*INPUTS_INC].rev_fields.op1) : (Sum_T)inputs[1*INPUTS_INC].rev_fields.op1)
        + ((weights[0*WEIGHTS_INC].rev_fields.op6 == 0)
            ? (Sum_T)(-inputs[1*INPUTS_INC].rev_fields.op2) : (Sum_T)inputs[1*INPUTS_INC].rev_fields.op2)
        + ((weights[0*WEIGHTS_INC].rev_fields.op7 == 0)
            ? (Sum_T)(-inputs[1*INPUTS_INC].rev_fields.op3) : (Sum_T)inputs[1*INPUTS_INC].rev_fields.op3);

    return weightedSum;
}

template<int NB_ITERATIONS,
            int INPUTS_INC = 1,
            int WEIGHTS_INC = 1,
            typename Weight_T, typename Sum_T,
            class Input_T,
            typename std::enable_if<(n_pack<Weight_T>() == 8
            && NB_ITERATIONS >= 8 && n_pack<Input_T>() == 4)>::type* = nullptr>
static void macsOnRange(const Input_T* __restrict inputs,
                                            const Weight_T* __restrict weights,
                                            Sum_T& __restrict weightedSum)
{
    weightedSum = octoMac<INPUTS_INC, WEIGHTS_INC>(inputs, weights, weightedSum);
    macsOnRange<NB_ITERATIONS-8, INPUTS_INC, WEIGHTS_INC>(
        inputs + 2*INPUTS_INC, weights + WEIGHTS_INC, weightedSum);
}

// ----------------------------------------------------------------------------
// Unpacked weights - Packed <4> inputs
// ----------------------------------------------------------------------------

template<int INPUTS_INC = 1,
            int WEIGHTS_INC = 1,
            typename Input_T,
            typename Weight_T, typename Sum_T,
            typename std::enable_if<(!is_packed<Weight_T>()
            && n_pack<Input_T>() == 4)>::type* = nullptr>
static Sum_T dualMac(const Input_T* __restrict inputs,
                                        const Weight_T* __restrict weights,
                                        Sum_T weightedSum)
{
    weightedSum += weights[0*WEIGHTS_INC] * inputs[0*INPUTS_INC].rev_fields.op0
        + weights[1*WEIGHTS_INC] * inputs[0*INPUTS_INC].rev_fields.op1;

    return weightedSum;
}

template<int INPUTS_INC = 1,
            int WEIGHTS_INC = 1,
            typename Input_T,
            typename Weight_T, typename Sum_T,
            typename std::enable_if<(!is_packed<Weight_T>()
            && n_pack<Input_T>() == 4)>::type* = nullptr>
static Sum_T tripleMac(const Input_T* __restrict inputs,
                                        const Weight_T* __restrict weights,
                                        Sum_T weightedSum)
{
    weightedSum += weights[0*WEIGHTS_INC] * inputs[0*INPUTS_INC].rev_fields.op0
        + weights[1*WEIGHTS_INC] * inputs[0*INPUTS_INC].rev_fields.op1
        + weights[2*WEIGHTS_INC] * inputs[0*INPUTS_INC].rev_fields.op2;

    return weightedSum;
}

template<int INPUTS_INC = 1,
            int WEIGHTS_INC = 1,
            typename Input_T,
            typename Weight_T, typename Sum_T,
            typename std::enable_if<(!is_packed<Weight_T>()
            && n_pack<Input_T>() == 4)>::type* = nullptr>
static Sum_T quadMac(const Input_T* __restrict inputs,
                                        const Weight_T* __restrict weights,
                                        Sum_T weightedSum)
{
    weightedSum += weights[0*WEIGHTS_INC] * inputs[0*INPUTS_INC].rev_fields.op0
        + weights[1*WEIGHTS_INC] * inputs[0*INPUTS_INC].rev_fields.op1
        + weights[2*WEIGHTS_INC] * inputs[0*INPUTS_INC].rev_fields.op2
        + weights[3*WEIGHTS_INC] * inputs[0*INPUTS_INC].rev_fields.op3;

    return weightedSum;
}

template<int NB_ITERATIONS,
            int INPUTS_INC = 1,
            int WEIGHTS_INC = 1,
            typename Weight_T, typename Sum_T,
            class Input_T,
            typename std::enable_if<(!is_packed<Weight_T>()
            && NB_ITERATIONS == 2 && n_pack<Input_T>() == 4)>::type* = nullptr>
static void macsOnRange(const Input_T* __restrict inputs,
                                            const Weight_T* __restrict weights,
                                            Sum_T& __restrict weightedSum)
{
    weightedSum = dualMac<INPUTS_INC, WEIGHTS_INC>(inputs, weights, weightedSum);
}

template<int NB_ITERATIONS,
            int INPUTS_INC = 1,
            int WEIGHTS_INC = 1,
            typename Weight_T, typename Sum_T,
            class Input_T,
            typename std::enable_if<(!is_packed<Weight_T>()
            && NB_ITERATIONS == 3 && n_pack<Input_T>() == 4)>::type* = nullptr>
static void macsOnRange(const Input_T* __restrict inputs,
                                            const Weight_T* __restrict weights,
                                            Sum_T& __restrict weightedSum)
{
    weightedSum = tripleMac<INPUTS_INC, WEIGHTS_INC>(inputs, weights, weightedSum);
}

template<int NB_ITERATIONS,
            int INPUTS_INC = 1,
            int WEIGHTS_INC = 1,
            typename Weight_T, typename Sum_T,
            class Input_T,
            typename std::enable_if<(!is_packed<Weight_T>()
            && NB_ITERATIONS >= 4 && n_pack<Input_T>() == 4)>::type* = nullptr>
static void macsOnRange(const Input_T* __restrict inputs,
                                            const Weight_T* __restrict weights,
                                            Sum_T& __restrict weightedSum)
{
    weightedSum = quadMac<INPUTS_INC, WEIGHTS_INC>(inputs, weights, weightedSum);
    macsOnRange<NB_ITERATIONS-4, INPUTS_INC, WEIGHTS_INC>(
        inputs + INPUTS_INC, weights + 4*WEIGHTS_INC, weightedSum);
}

// ----------------------------------------------------------------------------
// Unpacked weights - Unpacked inputs
// ----------------------------------------------------------------------------

template<int NB_ITERATIONS,
            int INPUTS_INC = 1,
            int WEIGHTS_INC = 1,
            typename Weight_T, typename Sum_T,
            class Input_T,
            typename std::enable_if<(NB_ITERATIONS > 0 && !is_packed<Weight_T>()
            && !is_packed<Input_T>())>::type* = nullptr>
static void macsOnRange(const Input_T* __restrict inputs,
                                            const Weight_T* __restrict weights,
                                            Sum_T& __restrict weightedSum)
{
    for (int iter = 0; iter < NB_ITERATIONS; ++iter) {
        weightedSum += inputs[iter*INPUTS_INC] * weights[iter*WEIGHTS_INC];
    }
}

}; // namespace export_cpp

#endif
