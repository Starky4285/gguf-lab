cmake_minimum_required(VERSION 3.22.1)

project("gguflab")

set(CMAKE_CXX_STANDARD 17)

# Path to your cloned llama.cpp repo (keep it up to date: cd llama.cpp && git pull)
set(LLAMA_CPP_DIR "${CMAKE_SOURCE_DIR}/../../../../llama.cpp")

# Build options
set(BUILD_SHARED_LIBS OFF CACHE BOOL "" FORCE)
set(LLAMA_BUILD_TESTS OFF CACHE BOOL "" FORCE)
set(LLAMA_BUILD_EXAMPLES OFF CACHE BOOL "" FORCE)
set(LLAMA_BUILD_TOOLS OFF CACHE BOOL "" FORCE)
set(LLAMA_BUILD_SERVER OFF CACHE BOOL "" FORCE)
set(LLAMA_BUILD_COMMON OFF CACHE BOOL "" FORCE)
set(LLAMA_CURL OFF CACHE BOOL "" FORCE)
set(LLAMA_OPENSSL OFF CACHE BOOL "" FORCE)

# CPU speed settings for phones
set(GGML_NATIVE OFF CACHE BOOL "" FORCE)    # we cross-compile, so never "native"
set(GGML_OPENMP OFF CACHE BOOL "" FORCE)    # ggml's own thread pool works better on Android
# dotprod/fp16 make Q4 models ~2x faster. Any phone from ~2019 onward supports them.
# If the app crashes with SIGILL on a very old phone, change this to "armv8-a".
if(ANDROID_ABI STREQUAL "arm64-v8a")
    set(GGML_CPU_ARM_ARCH "armv8.2-a+dotprod+fp16" CACHE STRING "" FORCE)
endif()

# Add llama.cpp
add_subdirectory(${LLAMA_CPP_DIR} ${CMAKE_BINARY_DIR}/llama_build)

# Your JNI bridge
add_library(
        native-lib
        SHARED
        native-lib.cpp
)

find_library(
        log-lib
        log
)

target_include_directories(native-lib PRIVATE
        ${LLAMA_CPP_DIR}/include
        ${LLAMA_CPP_DIR}/ggml/include
)

target_link_libraries(
        native-lib
        ${log-lib}
        llama
)
