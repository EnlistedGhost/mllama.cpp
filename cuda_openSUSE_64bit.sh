# Clean previous build cache (if any)
rm -rf build

# Reconfigure NVCC environment variables + CMake flags
PATH=$PATH:/usr/local/cuda-12.8/bin
# Force the NVCC to shut-up about compute_70 deprecation
export NVCC_PREPEND_FLAGS="-Wno-deprecated-gpu-targets"
# Cont... (if building for other archs use: 50;61;86;89)
NVCC_CCBIN=/usr/bin/g++-13 CUDAHOSTCXX=/usr/bin/g++-13 CC=gcc-13 CXX=g++-13 \
cmake -B build \
  -DGGML_CUDA=ON \
  -DGGML_CUDA_NCCL=OFF \
  -DCMAKE_C_COMPILER=gcc-13 \
  -DCMAKE_CXX_COMPILER=g++-13 \
  -DCMAKE_CUDA_HOST_COMPILER=/usr/bin/g++-13 \
  -DCMAKE_CUDA_COMPILER=/usr/local/cuda-12.8/bin/nvcc \
  -DCMAKE_CUDA_ARCHITECTURES="50;52;61;70;75" \
  -DCMAKE_BUILD_TYPE=Release

#Compile targeted llama-server binary
cmake --build build --config Release --target llama-server ggml ggml-base ggml-cuda llama-gguf-split llama-quantize llama-tts mtmd -j 16