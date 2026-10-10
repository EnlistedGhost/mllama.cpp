import re
import os
import io
from pathlib import Path
from llama_cpp_patcher_addon_2 import patch_ggml_cmake_part2

basedir = os.path.abspath(os.path.dirname(__file__))
folder = os.path.join(basedir, 'ggml/CMakeLists.txt')
folderPath = Path(folder)

def patch_ggml_cmake_part1():
    """
    Surgically applies the first half of the specialized hardware configuration
    overrides to ggml/CMakeLists.txt.
    """
    if not folderPath.exists():
        print(f"  ⚠️ Skip: {folderPath.name} not found inside {basedir.name}.")
        return

    content = folderPath.read_text(encoding="utf-8")

    # 1. Structural Setup Variables
    content = content.replace("set(GGML_STANDALONE OFF)", "set(GGML_STANDALONE ON)")
    content = content.replace("set(BUILD_SHARED_LIBS_DEFAULT OFF)", "set(BUILD_SHARED_LIBS_DEFAULT ON)")

    # 2. Dynamic Backend Layer & Shared Libs Enforced
    content = content.replace(
        'option(BUILD_SHARED_LIBS           "ggml: build shared libraries" ${BUILD_SHARED_LIBS_DEFAULT})',
        'option(BUILD_SHARED_LIBS           "ggml: build shared libraries"       ON)'
    )
    content = content.replace(
        'option(GGML_BACKEND_DL             "ggml: build backends as dynamic libraries (requires BUILD_SHARED_LIBS)" OFF)',
        'option(GGML_BACKEND_DL             "ggml: build backends as dynamic"    ON)'
    )
    content = content.replace(
        'set(GGML_BACKEND_DIR "" CACHE PATH "ggml: directory to load dynamic backends from (requires GGML_BACKEND_DL")',
        'set(GGBackend_DIR "" CACHE PATH "ggml: directory to load dynamic")'
    )

    # 3. Strip Metal Fallbacks & Force Native Optimization Flags
    apple_metal_block = (
        r"if \(APPLE\).*?endif\(\)\n\n"
        r"if \(CMAKE_CROSSCOMPILING OR DEFINED ENV\{SOURCE_DATE_EPOCH\}\).*?endif\(\)"
    )
    clean_native_block = (
        "set(GGML_METAL_DEFAULT OFF)\n"
        "set(GGML_BLAS_DEFAULT OFF)\n"
        "set(GGML_BLAS_VENDOR_DEFAULT \"Generic\")\n\n"
        "#if (CMAKE_CROSSCOMPILING OR DEFINED ENV{SOURCE_DATE_EPOCH})\n"
        "#    message(STATUS \"Setting GGML_NATIVE_DEFAULT to OFF\")\n"
        "#    set(GGML_NATIVE_DEFAULT OFF)\n"
        "#else()\n"
        "    set(GGML_NATIVE_DEFAULT ON)\n"
        "#endif()"
    )
    content = re.sub(apple_metal_block, clean_native_block, content, flags=re.DOTALL)

    # 4. Default Layer Overrides
    content = content.replace("set(GGML_LLAMAFILE_DEFAULT OFF)", "set(GGML_LLAMAFILE_DEFAULT ON)")
    content = content.replace("set(GGML_CUDA_GRAPHS_DEFAULT OFF)", "set(GGML_CUDA_GRAPHS_DEFAULT ON)")

    # 5. Native Optimizer & Link-Time Optimization (LTO)
    content = content.replace(
        'option(GGML_NATIVE "ggml: optimize the build for the current system" ${GGML_NATIVE_DEFAULT})',
        'option(GGML_NATIVE "ggml: optimize the build for the current system" ON)'
    )
    content = content.replace(
        'option(GGML_LTO    "ggml: enable link time optimization"             OFF)',
        'option(GGML_LTO    "ggml: enable link time optimization"             ON)'
    )
    content = content.replace(
        'option(GGML_GPROF                  "ggml: enable gprof"                                   OFF)',
        'option(GGML_GPROF                  "ggml: enable gprof"                                   ON)'
    )

    # 6. Set Local Binary Output & Debug Message Anchors
    debug_msg_pattern = (
        r"message\(DEBUG \"GGML_NATIVE         : \$\{GGML_NATIVE\}\"\)\n"
        r"message\(DEBUG \"GGML_NATIVE_DEFAULT : \$\{GGML_NATIVE_DEFAULT\}\"\)"
    )
    clean_debug_block = (
        "set(CMAKE_BINARY_DIR ${CMAKE_CURRENT_SOURCE_DIR}/build)\n\n"
        "message(DEBUG \"GGML_NATIVE         : ON\")\n"
        "message(DEBUG \"GGML_NATIVE_DEFAULT : ON\")"
    )
    content = re.sub(debug_msg_pattern, clean_debug_block, content)

    # 7. Strip Archaic Instruction Trees (RISC-V Fallbacks)
    content = content.replace('option(GGML_RV_ZFH           "ggml: enable riscv zfh"         ON)', 'option(GGML_RV_ZFH           "ggml: enable riscv zfh"         OFF)')
    content = content.replace('option(GGML_RV_ZVFH          "ggml: enable riscv zvfh"        ON)', 'option(GGML_RV_ZVFH          "ggml: enable riscv zvfh"        OFF)')
    content = content.replace('option(GGML_RV_ZICBOP        "ggml: enable riscv zicbop"      ON)', 'option(GGML_RV_ZICBOP        "ggml: enable riscv zicbop"      OFF)')
    content = content.replace('option(GGML_RV_ZIHINTPAUSE   "ggml: enable riscv zihintpause" ON)', 'option(GGML_RV_ZIHINTPAUSE   "ggml: enable riscv zihintpause" OFF)')

    # 8. Core Scheduling, BLAS Execution, & CUDA Backend Injection
    content = content.replace('option(GGML_CPU_ALL_VARIANTS "ggml: build all variants of the CPU backend (requires GGML_BACKEND_DL)" OFF)', 'option(GGML_CPU_ALL_VARIANTS "ggml: build all variants of the CPU backend (requires GGML_BACKEND_DL)" ON)')
    content = content.replace('set(GGML_SCHED_MAX_COPIES  "4" CACHE STRING "ggml: max input copies for pipeline parallelism")', 'set(GGML_SCHED_MAX_COPIES  "2" CACHE STRING "ggml: max input copies for pipeline parallelism")')
    content = content.replace('option(GGML_BLAS                            "ggml: use BLAS"                                  ${GGML_BLAS_DEFAULT})', 'option(GGML_BLAS                            "ggml: use BLAS"                                  ON)')
    content = content.replace('option(GGML_LLAMAFILE                       "ggml: use LLAMAFILE"                             ${GGML_LLAMAFILE_DEFAULT})', 'option(GGML_LLAMAFILE                       "ggml: use LLAMAFILE"                             ON)')
    content = content.replace('option(GGML_CUDA                            "ggml: use CUDA"                                  OFF)', 'option(GGML_CUDA                            "ggml: use CUDA"                                  ON)')
    content = content.replace('option(GGML_CUDA_FORCE_CUBLAS               "ggml: always use cuBLAS instead of mmq kernels"  OFF)', 'option(GGML_CUDA_FORCE_CUBLAS               "ggml: always use cuBLAS instead of mmq kernels"  ON)')

    # Write the modified content back
    folderPath.write_text(content, encoding="utf-8")
    print(f"  ⚡ Phase 1 configuration applied to ggml/{folderPath.name}")

def complete_both():
    patch_ggml_cmake_part1()
    patch_ggml_cmake_part2()

if __name__ == "__main__":
    complete_both()