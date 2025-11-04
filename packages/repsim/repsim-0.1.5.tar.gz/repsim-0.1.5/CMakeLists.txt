cmake_minimum_required(VERSION 3.18)
project(repsim LANGUAGES CXX)

# -----------------------------
# Build options
# -----------------------------
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)  # good for shared libs everywhere

# Silence deprecation for old FindPython* modules; we use the modern path.
if(POLICY CMP0148)
  cmake_policy(SET CMP0148 NEW)
endif()

# -----------------------------
# Python & pybind11 (modern)
# -----------------------------
# Prefer FindPython over FindPythonInterp/FindPythonLibs
set(PYBIND11_FINDPYTHON ON)  # belt & suspenders; also set this in pyproject if you like
find_package(Python COMPONENTS Interpreter Development.Module REQUIRED)
find_package(pybind11 CONFIG REQUIRED)

# -----------------------------
# Vendored Eigen (header-only)
# -----------------------------
set(EIGEN3_INCLUDE_DIR "${CMAKE_SOURCE_DIR}/third_party/eigen")
if(NOT EXISTS "${EIGEN3_INCLUDE_DIR}/Eigen/Core")
  message(FATAL_ERROR "Vendored Eigen headers not found at ${EIGEN3_INCLUDE_DIR}")
endif()

# -----------------------------
# Extension module
# -----------------------------
# Your binding translation unit and any C++ sources it calls.
pybind11_add_module(_repsim
  src/repsim_bindings.cpp
)

target_include_directories(_repsim PRIVATE
  ${CMAKE_SOURCE_DIR}/src           # your project headers
  ${EIGEN3_INCLUDE_DIR}             # vendored Eigen
)

# Keep Eigen in MPL2-only mode (optional safety define)
target_compile_definitions(_repsim PRIVATE EIGEN_MPL2_ONLY=1)

# -----------------------------
# Install into the Python package inside the wheel
# -----------------------------
# scikit-build-core provides SKBUILD_PLATLIB_DIR (site-packages path within the wheel)
# We must install the built extension into <site-packages>/repsim
install(TARGETS _repsim
  LIBRARY DESTINATION "${SKBUILD_PLATLIB_DIR}/repsim"  # .so/.dylib (Unix)
  RUNTIME DESTINATION "${SKBUILD_PLATLIB_DIR}/repsim"  # .pyd/.dll (Windows)
  ARCHIVE DESTINATION "${SKBUILD_PLATLIB_DIR}/repsim"  # static libs (rare)
)
