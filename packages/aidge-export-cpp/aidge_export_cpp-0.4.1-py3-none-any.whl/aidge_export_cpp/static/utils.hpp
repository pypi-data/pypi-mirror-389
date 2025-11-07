#ifndef __AIDGE_EXPORT_CPP_NETWORK_UTILS__
#define __AIDGE_EXPORT_CPP_NETWORK_UTILS__

#if SAVE_OUTPUTS
#include <sys/types.h>
#include <sys/stat.h>
#include <cstdio>      // fprintf
#include <type_traits> // std::is_floating_point
#endif

#if AIDGE_CMP
#include <string>
#endif

#include "utils/cpp/typedefs.hpp"

namespace export_cpp {

/**
 * @brief   Integer clamping
 * @param[in]  v   Value to be clamped
 * @param[in]  lo  Saturating lower bound
 * @param[in]  hi  Saturating higher bound
 * @returns         Value clamped between lo and hi
 *
 */
__attribute__((always_inline)) static inline
int clamp (int v, int lo, int hi)
{
    if(v < lo) {
        return lo;
    }
    else if(v > hi) {
        return hi;
    }
    else {
        return v;
    }
}

/**
 * @brief   Maximum of two integer values
 */
__attribute__((always_inline)) static inline
int max (int lhs, int rhs)
{
    return (lhs >= rhs) ? lhs : rhs;
}

/**
 * @brief   Minimum of two integer values
 */
__attribute__((always_inline)) static inline
int min (int lhs, int rhs)
{
    return (lhs <= rhs) ? lhs : rhs;
}

template <class InputIt, class Size, class OutputIt>
__attribute__((always_inline))
static inline OutputIt copy_n(InputIt first, Size count, OutputIt result) {
    if (count > 0) {
        *result = *first;
        ++result;
        for (Size i = 1; i != count; ++i, ++result) {
            *result = *++first;
        }
    }

    return result;
}

#if SAVE_OUTPUTS || AIDGE_CMP

enum class Format {
    DEFAULT,
    CHW,
    HWC,
    NCW,
    NWC,
    NCHW,
    NHWC,
    CHWN,
    NCDHW,
    NDHWC,
    CDHWN
};

#endif  // SAVE_OUTPUTS || AIDGE_CMP

#if SAVE_OUTPUTS

template<int NB_OUTPUTS, int OUT_HEIGHT, int OUT_WIDTH,
    size_t MEM_CONT_OFFSET,
    size_t MEM_CONT_SIZE,
    size_t MEM_WRAP_OFFSET,
    size_t MEM_WRAP_SIZE,
    DataFormat_T FMT, typename Output_T>
inline void saveOutputs(const Output_T* __restrict outputs, FILE* pFile) {
    int offset = 0;

    // NCHW
    if (FMT == DataFormat_T::NCHW || FMT == DataFormat_T::CHW || FMT == DataFormat_T::NCW || FMT == DataFormat_T::DEFAULT) {
        fprintf(pFile, "{");
        for (auto out = 0; out < NB_OUTPUTS; ++out) {
            fprintf(pFile, "{");
            for (auto h = 0; h < OUT_HEIGHT; ++h) {
                fprintf(pFile, "{");
                for (auto w = 0; w < OUT_WIDTH; ++w) {
                    if (MEM_WRAP_SIZE > 0 && offset == static_cast<int>(MEM_CONT_SIZE / sizeof(Output_T))) {
                        offset += (MEM_WRAP_OFFSET - MEM_CONT_OFFSET
                                    - MEM_CONT_SIZE) / sizeof(Output_T);
                    }

                    if (std::is_floating_point<Output_T>::value)
                        fprintf(pFile, "%.18f", static_cast<float>(outputs[offset]));
                    else
                        fprintf(pFile, "%d", static_cast<int>(outputs[offset]));
                    ++offset;

                    fprintf(pFile, ", ");

                }
                fprintf(pFile, "}\n");
            }
            fprintf(pFile, "}\n");
        }
        fprintf(pFile, "}\n");

    // NHWC
    } else if (FMT == DataFormat_T::NHWC || FMT == DataFormat_T::HWC || FMT == DataFormat_T::NWC) {
        fprintf(pFile, "{\n"); 
        for (auto c = 0; c < NB_OUTPUTS; ++c) {
            fprintf(pFile, "  {\n");
            for (auto h = 0; h < OUT_HEIGHT; ++h) { 
                fprintf(pFile, "    { "); 
                for (auto w = 0; w < OUT_WIDTH; ++w) {

                    // Compute offset in NHWC layout
                    size_t offset_nhwc = ((h * OUT_WIDTH) + w) * NB_OUTPUTS + c;

                    if (MEM_WRAP_SIZE > 0 && offset_nhwc >= static_cast<int>(MEM_CONT_SIZE / sizeof(Output_T))) {
                        offset_nhwc += (MEM_WRAP_OFFSET - MEM_CONT_OFFSET
                                        - MEM_CONT_SIZE) / sizeof(Output_T);
                    }

                    if (std::is_floating_point<Output_T>::value)
                        fprintf(pFile, "%.18f", static_cast<double>(outputs[offset_nhwc]));
                    else
                        fprintf(pFile, "%4d", static_cast<int>(outputs[offset_nhwc]));

                    // Add comma except for last element in width
                    if (w != OUT_WIDTH - 1)
                        fprintf(pFile, ",");
                }
                fprintf(pFile, " },\n"); // Close width loop
            }
            fprintf(pFile, "  },\n"); // Close height loop
        }
        fprintf(pFile, "}\n"); // Close outer brace

    } else {
        printf("[ERROR] - DataFormat_T is not supported.\n");
        printf("[ERROR] - Aborting save outputs...\n");
        return;
    }
}
#endif // SAVE_OUTPUTS

#if AIDGE_CMP

template<int NB_OUTPUTS, int OUT_WIDTH, int OUT_HEIGHT, DataFormat_T FMT>
int get_ofst_from_fmt(int out, int h, int w) {
    if (FMT == DataFormat_T::NCHW || FMT == DataFormat_T::CHW || FMT == DataFormat_T::NCW || FMT == DataFormat_T::DEFAULT)
        return out * OUT_HEIGHT * OUT_WIDTH + h * OUT_WIDTH + w;
    else if (FMT == DataFormat_T::NHWC || FMT == DataFormat_T::HWC || FMT == DataFormat_T::NWC)
        return h * OUT_WIDTH * NB_OUTPUTS + w * NB_OUTPUTS + out;
    else {
        printf("[ERROR] - This data format is not supported.\n");
        return -1;
    }
}

template<int NB_OUTPUTS, int OUT_WIDTH, int OUT_HEIGHT,
    size_t MEM_CONT_OFFSET,
    size_t MEM_CONT_SIZE,
    size_t MEM_WRAP_OFFSET,
    size_t MEM_WRAP_SIZE,
    DataFormat_T AIDGE_FMT, DataFormat_T DEV_FMT, typename AidgeOutput_T, typename DevOutput_T>
void aidge_cmp(std::string layer_name, AidgeOutput_T* aidge_output, DevOutput_T* dev_output) {

    printf("[NOTICE] - Comparing with Aidge ref for node : %s -> ", layer_name.c_str());

    const float atol = 1e-5f;   // Absolute
    const float rtol = 1e-3f;   // Relative

    for (auto out = 0; out < NB_OUTPUTS; ++out) {
        for (auto h = 0; h < OUT_HEIGHT; ++h) {
            for (auto w = 0; w < OUT_WIDTH; ++w) {

                const int aidge_ofst = get_ofst_from_fmt<NB_OUTPUTS, OUT_WIDTH, OUT_HEIGHT, AIDGE_FMT>(out, h, w);
                int dev_ofst   = get_ofst_from_fmt<NB_OUTPUTS, OUT_WIDTH, OUT_HEIGHT, DEV_FMT>(out, h, w);

                if (aidge_ofst == -1 || dev_ofst == -1) {
                    printf("[FAILURE]\n");
                    printf("[ERROR] - Aborting this layer comparison...\n");
                    return;
                }

                if (MEM_WRAP_SIZE > 0 && dev_ofst >= static_cast<int>(MEM_CONT_SIZE / sizeof(DevOutput_T))) {
                    dev_ofst += (MEM_WRAP_OFFSET - MEM_CONT_OFFSET
                                - MEM_CONT_SIZE) / sizeof(DevOutput_T);
                }

                // Float Comparison
                if (std::is_floating_point<DevOutput_T>::value) {

                    const float diff = std::abs(aidge_output[aidge_ofst] - dev_output[dev_ofst]);
                    const float tolerance = atol + rtol * std::abs(dev_output[dev_ofst]);

                    if (diff > tolerance) {
                            printf("[FAILURE]\n");
                            printf("[ERROR] - First error detected at %dx%dx%d (out x h x w) : aidge_out = %.18f vs dev_out = %.18f\n",
                                    out, h, w, static_cast<double>(aidge_output[aidge_ofst]), static_cast<double>(dev_output[dev_ofst]));
                            printf("Abort program.\n");
                            exit(1);
                    }
                
                // Int Comparison
                } else {    
                    if (aidge_output[aidge_ofst] != dev_output[dev_ofst]) {
                        printf("[FAILURE]\n");
                        printf("[ERROR] - First error detected at %dx%dx%d (out x h x w) : aidge_out = %d vs dev_out = %d\n",
                                out, h, w, static_cast<int>(aidge_output[aidge_ofst]), static_cast<int>(dev_output[dev_ofst]));
                        printf("[ERROR] - Abort program.\n");
                        exit(1);
                    }
                }
            }
        }
    }
    printf("[SUCCESS]\n\n");
}

#endif  // AIDGE_CMP

};  // namespace export_cpp

#endif // __AIDGE_EXPORT_CPP_NETWORK_UTILS__
