#ifndef __AIDGE_EXPORT_CPP_RESCALING_UTILS_HPP__
#define __AIDGE_EXPORT_CPP_RESCALING_UTILS_HPP__

#include <cstdint>
#include <cstddef>

namespace export_cpp {

// ---------------------------------------------------
// ----------------- Saturate Utils ------------------
// ---------------------------------------------------

constexpr int64_t toInt64(uint32_t lo, uint32_t hi) {
    return (int64_t) (((uint64_t) hi) << 32ull) | ((uint64_t) lo);
}

constexpr int64_t smlal(int32_t lhs, int32_t rhs, 
                     uint32_t accumLo, uint32_t accumHi) 
{
    return ((int64_t) lhs) * ((int64_t) rhs) + toInt64(accumLo, accumHi);
}

// ---------------------------------------------------
// ------------------- No Scaling --------------------
// ---------------------------------------------------

struct NoScaling {
    template<typename Sum_T>
    Sum_T operator()(Sum_T weightedSum, size_t /*output*/) const {
        return weightedSum;
    }
};

struct FloatingPointScaling {
    template<typename Sum_T>
    Sum_T operator()(Sum_T weightedSum, size_t /*output*/) const {
        return round(weightedSum*mScaling);
    }

    double mScaling;
};

template<size_t SIZE>
struct FloatingPointScalingPerChannel {
    template<typename Sum_T>
    Sum_T operator()(Sum_T weightedSum, size_t output) const {
        return round(weightedSum * mScaling[output]);
    }

    double mScaling[SIZE];
};

template<size_t SIZE>
struct FloatingPointClippingAndScaling {
    template<typename Sum_T>
    Sum_T operator()(Sum_T weightedSum, size_t /*output*/) const {
        Sum_T clipValue = weightedSum;
        clipValue = (clipValue < Sum_T(0)) ?
                    Sum_T(0) : (clipValue > Sum_T(mClipping)) ?
                    Sum_T(mClipping) : clipValue;
        return round(clipValue * mScaling);
    }

    double mScaling;
    int32_t mClipping;
};

template<size_t SIZE>
struct FloatingPointClippingAndScalingPerChannel {
    template<typename Sum_T>
    Sum_T operator()(Sum_T weightedSum, size_t output) const {
        Sum_T clipValue = weightedSum;
        clipValue = (clipValue < Sum_T(0)) ? 
                    Sum_T(0) : (clipValue > Sum_T(mClipping[output])) ? 
                    Sum_T(mClipping[output]) : clipValue;
        return round(clipValue * mScaling[output]);
    }

    double mScaling[SIZE];
    int32_t mClipping[SIZE];
};

template<int32_t SCALING, int64_t FRACTIONAL_BITS>
struct FixedPointScaling {
    template<typename Sum_T>
    Sum_T operator()(Sum_T weightedSum, size_t /*output*/) const {
        // Different rounding if weightesSum < 0
        // if(weightedSum < 0) {
        //     HALF--; 
        // }
        
        return smlal(weightedSum, SCALING, HALF_LO, HALF_HI) >> FRACTIONAL_BITS; 
    }

    static const uint32_t HALF_LO = (FRACTIONAL_BITS > 0)
        ? (1ull << (FRACTIONAL_BITS - 1)) & 0xFFFFFFFF : 0;
    static const uint32_t HALF_HI = (FRACTIONAL_BITS > 0)
        ? (1ull << (FRACTIONAL_BITS - 1)) >> 32u : 0;
};

template<size_t SIZE, int64_t FRACTIONAL_BITS>
struct FixedPointScalingScalingPerChannel {
    template<typename Sum_T>
    Sum_T operator()(Sum_T weightedSum, size_t output) const {
        // Different rounding if weightesSum < 0
        // if(weightedSum < 0) {
        //     HALF--; 
        // }

        return smlal(weightedSum, mScaling[output], HALF_LO, HALF_HI) >> FRACTIONAL_BITS; 
    }

    static const uint32_t HALF_LO = (FRACTIONAL_BITS > 0)
        ? (1ull << (FRACTIONAL_BITS - 1)) & 0xFFFFFFFF : 0;
    static const uint32_t HALF_HI = (FRACTIONAL_BITS > 0)
        ? (1ull << (FRACTIONAL_BITS - 1)) >> 32u : 0;

    int32_t mScaling[SIZE];
};

template<size_t SIZE, int64_t FRACTIONAL_BITS>
struct FixedPointClippingAndScalingPerChannel {
    template<typename Sum_T>
    Sum_T operator()(Sum_T weightedSum, size_t output) const {
        // Different rounding if weightesSum < 0
        // if(weightedSum < 0) {
        //     HALF--; 
        // }
        Sum_T clipValue = weightedSum;
        clipValue = (clipValue < Sum_T(0)) ? 
                    Sum_T(0) : (clipValue > Sum_T(mClipping[output])) ? 
                    Sum_T(mClipping[output]) : clipValue;

        return smlal(clipValue, mScaling[output], HALF_LO, HALF_HI) >> FRACTIONAL_BITS; 
    }

    static const uint32_t HALF_LO = (1ull << (FRACTIONAL_BITS - 1)) & 0xFFFFFFFF;
    static const uint32_t HALF_HI = (1ull << (FRACTIONAL_BITS - 1)) >> 32u;

    int32_t mScaling[SIZE];
    int32_t mClipping[SIZE];
};

template<size_t SHIFT>
struct SingleShiftScaling {
    template<typename Sum_T>
    Sum_T operator()(Sum_T weightedSum, size_t /*output*/) const {
        return (SHIFT != 0) ? ((weightedSum >> (SHIFT - 1)) + 1) >> 1   // Rounding
                            : weightedSum;
    }
};

template<size_t SIZE>
struct SingleShiftScalingPerChannel {
    template<typename Sum_T>
    Sum_T operator()(Sum_T weightedSum, size_t output) const {
        return (mScaling[output] != 0) ? ((weightedSum >> (mScaling[output] - 1)) + 1) >> 1   // Rounding
                            : weightedSum;
    }

    unsigned char mScaling[SIZE];
};

template<size_t SHIFT1, size_t SHIFT2, typename Sum_T>
struct DoubleShiftScaling {
    Sum_T operator()(Sum_T weightedSum, size_t /*output*/) const {
        // Different rounding if weightesSum < 0
        // if(weightedSum < 0) {
        //     HALF--; 
        // }

        return (weightedSum + (weightedSum << SHIFT1) + HALF) >> SHIFT2;
    }

    static const Sum_T HALF = ((Sum_T) 1) << (SHIFT2 - 1);
};

template<size_t SIZE, bool UNSIGNED_WEIGHTED_SUM, typename Sum_T>
struct DoubleShiftScalingPerChannel {
    Sum_T operator()(Sum_T weightedSum, size_t output) const {
        const Sum_T SHIFT1 = mScaling[output][0];
        const Sum_T SHIFT2 = mScaling[output][1];
        const Sum_T HALF = mScaling[output][2];
        
        // Different rounding if weightesSum < 0
        // if(weightedSum < 0) {
        //     HALF--; 
        // }

        return (weightedSum + (weightedSum << SHIFT1) + HALF) >> SHIFT2;
    }

    Sum_T mScaling[SIZE][3];
};

};  // namespace export_cpp

#endif
