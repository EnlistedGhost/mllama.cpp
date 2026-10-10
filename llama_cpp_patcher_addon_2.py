import re
import os
import io
from pathlib import Path

basedir = os.path.abspath(os.path.dirname(__file__))
folder = os.path.join(basedir, "ggml/CMakeLists.txt")
folderPath = Path(folder)

def patch_ggml_cmake_part2():
    """
    Surgically applies the second half of the specialized hardware configuration
    overrides to ggml/CMakeLists.txt.
    """
    if not folderPath.exists():
        print(f"  ⚠️ Skip: {folderPath.name} not found inside {basedir.name}.")
        return

    content = folderPath.read_text(encoding="utf-8")

    # 1. FlashAttention, CUDA Graphs, and NCCL Toggles
    # Replacing the older layout with your multi-line explicit overrides
    cuda_opts_pattern = (
        r'option\(GGML_CUDA_FA_ALL_QUANTS\s+"ggml: compile all quants for FlashAttention"\s+OFF\)\n'
        r'option\(GGML_CUDA_GRAPHS\s+"ggml: use CUDA graphs \(llama\.cpp only\)"\s+\$\{GGML_CUDA_GRAPHS_DEFAULT\}\)\n'
        r'option\(GGML_CUDA_NCCL\s+"ggml: use NVIDIA Collective Comm\. Library"\s+ON\)'
    )
    clean_cuda_opts = (
        'option(GGML_CUDA_FA_ALL_QUANTS              "ggml: compile all quants for FlashAttention"     ON)\n'
        'option(GGML_CUDA_GRAPHS                     "ggml: use CUDA graphs (llama.cpp only)"          ON)\n'
        'option(GGML_CUDA_NCCL                       "ggml: use NVIDIA Collective Comm. Library"       OFF)'
    )
    content = re.sub(cuda_opts_pattern, clean_cuda_opts, content)

    # 2. Strip HIP / ROCm Optimizations
    content = content.replace('option(GGML_HIP_GRAPHS                      "ggml: use HIP graph"                              ON)', 'option(GGML_HIP_GRAPHS                      "ggml: use HIP graph"                             OFF)')
    content = content.replace('option(GGML_HIP_NO_VMM                      "ggml: do not try to use HIP VMM"                 ON)', 'option(GGML_HIP_NO_VMM                      "ggml: do not try to use HIP VMM"                 OFF)')
    content = content.replace('option(GGML_HIP_MMQ_MFMA                    "ggml: enable MFMA MMA for CDNA in MMQ"           ON)', 'option(GGML_HIP_MMQ_MFMA                    "ggml: enable MFMA MMA for CDNA in MMQ"           OFF)')

    # 3. Disable WebAssembly JSPI
    content = content.replace('option(GGML_WEBGPU_JSPI                     "ggml: use JSPI for WebGPU"                       ON)', 'option(GGML_WEBGPU_JSPI                     "ggml: use JSPI for WebGPU"                       OFF)')

    # 4. Deep-Strip Remaining Apple Metal Framework Linking
    content = content.replace('option(GGML_METAL                           "ggml: use Metal"                                 ${GGML_METAL_DEFAULT})', 'option(GGML_METAL                           "ggml: use Metal"                                 OFF)')
    content = content.replace('option(GGML_METAL_NDEBUG                    "ggml: disable Metal debugging"                   OFF)', 'option(GGML_METAL_NDEBUG                    "ggml: disable Metal debugging"                   ON)')
    content = content.replace('option(GGML_METAL_EMBED_LIBRARY             "ggml: embed Metal library"                       ${GGML_METAL})', 'option(GGML_METAL_EMBED_LIBRARY             "ggml: embed Metal library"                       OFF)')
    
    # Safely clear the min version option block strings if present
    content = content.replace('set   (GGML_METAL_TARGET_OS "macos" CACHE STRING\n                                            "ggml: metal -mtargetos OS name (macos, ios, xros, tvos)")\n', '')

    # 5. Clean out embedded OpenMP Fetch hooks
    content = content.replace('option(GGML_OPENMP_FETCH                    "ggml: fetch LLVM OpenMP"                         OFF)\n', '')

    # 6. Disable Intel SYCL Pipeline Backends
    content = content.replace('option(GGML_SYCL_GRAPH                      "ggml: enable graphs in the SYCL backend"         ON)', 'option(GGML_SYCL_GRAPH                      "ggml: enable graphs in the SYCL backend"         OFF)')
    content = content.replace('option(GGML_SYCL_HOST_MEM_FALLBACK          "ggml: allow host memory fallback in SYCL reorder (requires kernel 6.8+)" ON)', 'option(GGML_SYCL_HOST_MEM_FALLBACK          "ggml: fallback in SYCL reorder (kernel 6.8+)"    OFF)')
    content = content.replace('option(GGML_SYCL_SUPPORT_LEVEL_ZERO_API     "ggml: use Level Zero API in SYCL backend"  ON)', 'option(GGML_SYCL_SUPPORT_LEVEL_ZERO_API     "ggml: use Level Zero API in SYCL backend"        OFF)')
    content = content.replace('option(GGML_SYCL_DNN                        "ggml: enable oneDNN in the SYCL backend"         ON)', 'option(GGML_SYCL_DNN                        "ggml: enable oneDNN in the SYCL backend"         OFF)')

    # 7. Strip Legacy OpenCL Hardware Accelerations
    content = content.replace('option(GGML_OPENCL_EMBED_KERNELS            "ggml: embed kernels"                             ON)', 'option(GGML_OPENCL_EMBED_KERNELS            "ggml: embed kernels"                             OFF)')
    content = content.replace('option(GGML_OPENCL_USE_ADRENO_KERNELS       "ggml: use optimized kernels for Adreno"          ON)', 'option(GGML_OPENCL_USE_ADRENO_KERNELS       "ggml: use optimized kernels for Adreno"          OFF)')

    # 8. Decouple Downstream Tests and Examples from the Build Tree
    content = content.replace('option(GGML_BUILD_TESTS    "ggml: build tests"    ${GGML_STANDALONE})', 'option(GGML_BUILD_TESTS    "ggml: build tests"    OFF)')
    content = content.replace('option(GGML_BUILD_EXAMPLES "ggml: build examples" ${GGML_STANDALONE})', 'option(GGML_BUILD_EXAMPLES "ggml: build examples" OFF)')

    # Commit modifications back out to disk
    folderPath.write_text(content, encoding="utf-8")
    print(f"  ⚡ Phase 2 configuration applied to ggml/{folderPath.name}")
