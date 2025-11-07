#ifndef __AIDGE_EXPORT_CPP_NETWORK_TYPEDEFS__
#define __AIDGE_EXPORT_CPP_NETWORK_TYPEDEFS__

#include <cassert>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <type_traits>
#include <limits>

namespace export_cpp {

enum class ActivationFunction_T {
    Tanh,
    Saturation,
    Rectifier,
    Linear,
    Softplus
};

enum class Pooling_T {
    Max,
    Average
};

enum class ElemWise_T {
    Add,
    Sub,
    Mul,
    Div
};

enum class CoeffMode_T {
    PerLayer,
    PerInput,
    PerChannel
};

enum class DataFormat_T {
    DEFAULT,
    NCHW,
    NHWC,
    CHWN,
    NCDHW,
    NDHWC,
    CDHWN,
    CHW,
    HWC,
    NCW,
    NWC
};

};  // namespace export_cpp

// ----------------------------------------------------------------------------
// -------------------- Generic custom bit-width types ------------------------
// ----------------------------------------------------------------------------

template <std::size_t N_PACK, std::size_t N_BITS, bool SIGNED = true>
struct packed_bitint {};

template<std::size_t N_PACK, std::size_t N_BITS>
using packed_bituint = packed_bitint<N_PACK, N_BITS, false>;

template<std::size_t N_BITS>
using bitint = packed_bitint<1, N_BITS>;

template<std::size_t N_BITS>
using bituint = packed_bituint<1, N_BITS>;

namespace std {
    // Specialization of STL, allows to use std::is_unsigned<> for example.
    template <std::size_t N_PACK, std::size_t N_BITS, bool SIGNED>
    struct is_integral<packed_bitint<N_PACK, N_BITS, SIGNED>> : std::integral_constant<bool, true> {};
    template <std::size_t N_PACK, std::size_t N_BITS, bool SIGNED>
    struct is_floating_point<packed_bitint<N_PACK, N_BITS, SIGNED>> : std::integral_constant<bool, false> {};
    template <std::size_t N_PACK, std::size_t N_BITS, bool SIGNED>
    struct is_unsigned<packed_bitint<N_PACK, N_BITS, SIGNED>> : std::integral_constant<bool, !SIGNED> {};

    template <std::size_t N_PACK, std::size_t N_BITS, bool SIGNED>
    class numeric_limits<packed_bitint<N_PACK, N_BITS, SIGNED>> {
    public:
        static constexpr int is_integer = true;
        static constexpr int is_signed = SIGNED;
        static constexpr int digits = N_BITS;
        static constexpr decltype(packed_bitint<N_PACK, N_BITS, SIGNED>::value) min() noexcept
            { return (SIGNED) ? -(1 << (N_BITS - 1)) : 0; };
        static constexpr decltype(packed_bitint<N_PACK, N_BITS, SIGNED>::value) lowest() noexcept
            { return (SIGNED) ? -(1 << (N_BITS - 1)) : 0; };
        static constexpr decltype(packed_bitint<N_PACK, N_BITS, SIGNED>::value) max() noexcept
            { return (SIGNED) ? (1 << (N_BITS - 1)) - 1 : (1 << N_BITS) - 1; };
    };
}

template <typename T>
struct is_packed : std::integral_constant<bool, false> {};

template <std::size_t N_PACK, std::size_t N_BITS, bool SIGNED>
struct is_packed<packed_bitint<N_PACK, N_BITS, SIGNED>> : std::integral_constant<bool, (N_PACK > 1)> {};

template <typename T>
struct n_pack : std::integral_constant<int, 1> {};

template <std::size_t N_PACK, std::size_t N_BITS, bool SIGNED>
struct n_pack<packed_bitint<N_PACK, N_BITS, SIGNED>> : std::integral_constant<int, N_PACK> {};

template <typename T, typename std::enable_if<(n_pack<T>() == 1)>::type* = nullptr>
constexpr auto pack_rev_get(T& data, int /*i*/) {
    return data;
}

template <typename T, typename std::enable_if<(n_pack<T>() > 1)>::type* = nullptr>
constexpr auto pack_rev_get(T& data, int i) {
    assert((i < n_pack<T>()) && "pack index out of range");
    switch (i) {
        case 0: return data.rev_fields.op0;
        case 1: return data.rev_fields.op1;
        case 2: return data.rev_fields.op2;
        case 3: return data.rev_fields.op3;
        case 4: return data.rev_fields.op4;
        case 5: return data.rev_fields.op5;
        case 6: return data.rev_fields.op6;
        default: return data.rev_fields.op7;
    }
}

template <typename T, typename std::enable_if<(n_pack<T>() == 1)>::type* = nullptr>
constexpr void pack_rev_set(T& data, int /*i*/, T val) {
    data = val;
}

template <typename T, typename std::enable_if<(n_pack<T>() > 1)>::type* = nullptr>
constexpr void pack_rev_set(T& data, int i, decltype(data.fields.op0) val) {
    assert((i < n_pack<T>()) && "pack index out of range");
    switch (i) {
        case 0: data.rev_fields.op0 = val; break;
        case 1: data.rev_fields.op1 = val; break;
        case 2: data.rev_fields.op2 = val; break;
        case 3: data.rev_fields.op3 = val; break;
        case 4: data.rev_fields.op4 = val; break;
        case 5: data.rev_fields.op5 = val; break;
        case 6: data.rev_fields.op6 = val; break;
        default: data.rev_fields.op7 = val; break;
    }
}


// ----------------------------------------------------------------------------
// -------------- Custom bit-width types operator overloading -----------------
// ----------------------------------------------------------------------------

template <std::size_t N_BITS, bool SIGNED, typename T>
constexpr packed_bitint<1, N_BITS, SIGNED>& operator+=(packed_bitint<1, N_BITS, SIGNED>& d, T rhs)
    {d.value += static_cast<decltype(d.value)>(rhs); return d;}

template <std::size_t N_BITS, bool SIGNED, typename T>
constexpr packed_bitint<1, N_BITS, SIGNED> operator+(packed_bitint<1, N_BITS, SIGNED> d, T rhs)
    {d += rhs; return d;}

template <std::size_t N_BITS, bool SIGNED, typename T>
constexpr packed_bitint<1, N_BITS, SIGNED>& operator-=(packed_bitint<1, N_BITS, SIGNED>& d, T rhs)
    {d.value -= static_cast<decltype(d.value)>(rhs); return d;}

template <std::size_t N_BITS, bool SIGNED, typename T>
constexpr packed_bitint<1, N_BITS, SIGNED> operator-(packed_bitint<1, N_BITS, SIGNED> d, T rhs)
    {d -= rhs; return d;}

template <std::size_t N_BITS, bool SIGNED, typename T>
constexpr packed_bitint<1, N_BITS, SIGNED>& operator*=(packed_bitint<1, N_BITS, SIGNED>& d, T rhs)
    {d.value *= static_cast<decltype(d.value)>(rhs); return d;}

template <std::size_t N_BITS, bool SIGNED, typename T>
constexpr packed_bitint<1, N_BITS, SIGNED> operator*(packed_bitint<1, N_BITS, SIGNED> d, T rhs)
    {d *= rhs; return d;}

template <std::size_t N_BITS, bool SIGNED, typename T>
constexpr packed_bitint<1, N_BITS, SIGNED>& operator/=(packed_bitint<1, N_BITS, SIGNED>& d, T rhs)
    {d.value /= static_cast<decltype(d.value)>(rhs); return d;}

template <std::size_t N_BITS, bool SIGNED, typename T>
constexpr packed_bitint<1, N_BITS, SIGNED> operator/(packed_bitint<1, N_BITS, SIGNED> d, T rhs)
    {d /= rhs; return d;}


// ----------------------------------------------------------------------------
// ---------------- Custom bit-width types specializations --------------------
// ----------------------------------------------------------------------------

// Data structure for binary
template <>
struct packed_bitint<1, 1, false> // alias: bituint<1>
{
    packed_bitint<1, 1, false>() = default;
    constexpr packed_bitint<1, 1, false>(std::uint8_t v): value(v) {};
    constexpr operator uint8_t() const { return value; }
    union {
        std::uint8_t value : 1;
    };
};

// Data structure for octo_binary
template <>
struct packed_bitint<8, 1, false> // alias: packed_bituint<8, 1>
{
   packed_bitint() = default;
    constexpr packed_bitint(std::uint8_t v): value(v) {};
    constexpr operator uint8_t() const { return value; }
    union {
        std::uint8_t value;
        struct
        {
            std::uint8_t op0 : 1; // lsb
            std::uint8_t op1 : 1;
            std::uint8_t op2 : 1;
            std::uint8_t op3 : 1;
            std::uint8_t op4 : 1;
            std::uint8_t op5 : 1;
            std::uint8_t op6 : 1;
            std::uint8_t op7 : 1; // msb
        } fields;
        struct
        {
            std::uint8_t op7 : 1; // lsb
            std::uint8_t op6 : 1;
            std::uint8_t op5 : 1;
            std::uint8_t op4 : 1;
            std::uint8_t op3 : 1;
            std::uint8_t op2 : 1;
            std::uint8_t op1 : 1;
            std::uint8_t op0 : 1; // msb
        } rev_fields;
    };
};

// Data structure for int2
template <>
struct packed_bitint<1, 2> // alias: bitint<2>
{
    packed_bitint() = default;
    constexpr packed_bitint(std::int8_t v): value(v) {};
    constexpr operator int8_t() const { return value; }
    union {
        std::int8_t value : 2;
    };
};

// Data structure for quad_int2
template <>
struct packed_bitint<4, 2>
{
    packed_bitint() = default;
    constexpr packed_bitint(std::uint8_t v): value(v) {};
    constexpr operator uint8_t() const { return value; }
    union {
        std::uint8_t value;
        struct
        {
            std::int8_t op0 : 2; // lsb
            std::int8_t op1 : 2;
            std::int8_t op2 : 2;
            std::int8_t op3 : 2; // msb
        } fields;
        struct
        {
            std::int8_t op3 : 2; // lsb
            std::int8_t op2 : 2;
            std::int8_t op1 : 2;
            std::int8_t op0 : 2; // msb
        } rev_fields;
    };
};

// Data structure for uint2
template <>
struct packed_bitint<1, 2, false> // alias: bituint<2>
{
    packed_bitint() = default;
    constexpr packed_bitint(std::uint8_t v): value(v) {};
    constexpr operator uint8_t() const { return value; }
    union {
        std::uint8_t value : 2;
    };
};

// Data structure for quad_uint2
template <>
struct packed_bitint<4, 2, false> // alias: packed_bituint<4, 2>
{
    packed_bitint() = default;
    constexpr packed_bitint(std::uint8_t v): value(v) {};
    constexpr operator uint8_t() const { return value; }
    union {
        std::uint8_t value;
        struct
        {
            std::int8_t op0 : 2; // lsb
            std::int8_t op1 : 2;
            std::int8_t op2 : 2;
            std::int8_t op3 : 2; // msb
        } fields;
        struct
        {
            std::int8_t op3 : 2; // lsb
            std::int8_t op2 : 2;
            std::int8_t op1 : 2;
            std::int8_t op0 : 2; // msb
        } rev_fields;
    };
};

// Data structure for int3
template <>
struct packed_bitint<1, 3> // alias: bitint<3>
{
    packed_bitint() = default;
    constexpr packed_bitint(std::int8_t v): value(v) {};
    constexpr operator int8_t() const { return value; }
    union {
        std::int8_t value : 3;
    };
};

// Data structure for dual_int3
template <>
struct packed_bitint<2, 3>
{
    packed_bitint() = default;
    constexpr packed_bitint(std::uint8_t v): value(v) {};
    constexpr operator uint8_t() const { return value; }
    union {
        std::uint8_t value;
        struct
        {
            std::int8_t op0 : 3; // lsb
            std::int8_t op1 : 3; // msb
        } fields;
        struct
        {
            std::int8_t op1 : 3; // lsb
            std::int8_t op0 : 3; // msb
        } rev_fields;
    };
};

// Data structure for uint3
template <>
struct packed_bitint<1, 3, false> // alias: bituint<3>
{
    packed_bitint() = default;
    constexpr packed_bitint(std::uint8_t v): value(v) {};
    constexpr operator uint8_t() const { return value; }
    union {
        std::uint8_t value : 3;
    };
};

// Data structure for dual_uint3
template <>
struct packed_bitint<2, 3, false> // alias: packed_bituint<2, 3>
{
    packed_bitint() = default;
    constexpr packed_bitint(std::uint8_t v): value(v) {};
    constexpr operator uint8_t() const { return value; }
    union {
        std::uint8_t value;
        struct
        {
            std::int8_t op0 : 3; // lsb
            std::int8_t op1 : 3; // msb
        } fields;
        struct
        {
            std::int8_t op1 : 3; // lsb
            std::int8_t op0 : 3; // msb
        } rev_fields;
    };
};

// Data structure for int4
template <>
struct packed_bitint<1, 4> // alias: bitint<4>
{
    packed_bitint() = default;
    constexpr packed_bitint(std::int8_t v): value(v) {};
    constexpr operator int8_t() const { return value; }
    union {
        std::int8_t value : 4;
    };
};

// Data structure for dual_int4
template <>
struct packed_bitint<2, 4>
{
    packed_bitint() = default;
    constexpr packed_bitint(std::uint8_t v): value(v) {};
    constexpr operator uint8_t() const { return value; }
    union {
        std::uint8_t value;
        struct
        {
            std::int8_t op0 : 4; // lsb
            std::int8_t op1 : 4; // msb
        } fields;
        struct
        {
            std::int8_t op1 : 4; // lsb
            std::int8_t op0 : 4; // msb
        } rev_fields;
    };
};

// Data structure for uint4
template <>
struct packed_bitint<1, 4, false> // alias: bituint<4>
{
    packed_bitint() = default;
    constexpr packed_bitint(std::uint8_t v): value(v) {};
    constexpr operator uint8_t() const { return value; }
    union {
        std::uint8_t value : 4;
    };
};

// Data structure for dual_uint4
template <>
struct packed_bitint<2, 4, false> // alias: packed_bituint<2, 4>
{
    packed_bitint() = default;
    constexpr packed_bitint(std::uint8_t v): value(v) {};
    constexpr operator uint8_t() const { return value; }
    union {
        std::uint8_t value;
        struct
        {
            std::int8_t op0 : 4; // lsb
            std::int8_t op1 : 4; // msb
        } fields;
        struct
        {
            std::int8_t op1 : 4; // lsb
            std::int8_t op0 : 4; // msb
        } rev_fields;
    };
};

// Data structure for int5
template <>
struct packed_bitint<1, 5> // alias: bitint<5>
{
    packed_bitint() = default;
    constexpr packed_bitint(std::int8_t v): value(v) {};
    constexpr operator int8_t() const { return value; }
    union {
        std::int8_t value : 5;
    };
};

// Data structure for uint5
template <>
struct packed_bitint<1, 5, false> // alias: bituint<5>
{
    packed_bitint() = default;
    constexpr packed_bitint(std::uint8_t v): value(v) {};
    constexpr operator uint8_t() const { return value; }
    union {
        std::uint8_t value : 5;
    };
};

// Data structure for int6
template <>
struct packed_bitint<1, 6> // alias: bitint<6>
{
    packed_bitint() = default;
    constexpr packed_bitint(std::int8_t v): value(v) {};
    constexpr operator int8_t() const { return value; }
    union {
        std::int8_t value : 6;
    };
};

// Data structure for uint6
template <>
struct packed_bitint<1, 6, false> // alias: bituint<6>
{
    packed_bitint() = default;
    constexpr packed_bitint(std::uint8_t v): value(v) {};
    constexpr operator uint8_t() const { return value; }
    union {
        std::uint8_t value : 6;
    };
};

// Data structure for int7
template <>
struct packed_bitint<1, 7> // alias: bitint<7>
{
    packed_bitint() = default;
    constexpr packed_bitint(std::int8_t v): value(v) {};
    constexpr operator int8_t() const { return value; }
    union {
        std::int8_t value : 7;
    };
};

// Data structure for uint7
template <>
struct packed_bitint<1, 7, false> // alias: bituint<7>
{
    packed_bitint() = default;
    constexpr packed_bitint(std::uint8_t v): value(v) {};
    constexpr operator uint8_t() const { return value; }
    union {
        std::uint8_t value : 7;
    };
};


// ----------------------------------------------------------------------------
// ------------------------- Structures and Unions ----------------------------
// ----------------------------------------------------------------------------

/* Object for compressing the outputs after mac operations */
typedef struct PackSupport {
    std::uint8_t         accumulator;
    unsigned int    cptAccumulator;
} PackSupport;

#endif  // __AIDGE_EXPORT_CPP_NETWORK_TYPEDEFS__
