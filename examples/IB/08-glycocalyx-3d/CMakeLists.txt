# IB/08 glycocalyx in 3D: a cylinder of target points in a sheared box of fluid.
#
# Build (after loading the compilers used for IBAMR and sourcing autoibamr's
# enable.sh, which sets IBAMR_ROOT):
#   cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
#   cmake --build build -j 4
# Run from this folder:
#   mpirun -np 4 ./build/main3d input3d
# The version range turns on the newer CMake policies, which silences two
# harmless developer warnings that IBAMR's own CMake files would print.
cmake_minimum_required(VERSION 3.15...3.30)
project(ib08_glycocalyx_3d LANGUAGES C CXX)

# Accepts IBAMR 0.16.0 or newer. CMake finds it through the IBAMR_ROOT
# environment variable, or pass -DIBAMR_ROOT=/path/to/IBAMR.
find_package(IBAMR 0.16.0 REQUIRED)

add_executable(main3d main.cpp update_target_point_positions.cpp)
target_link_libraries(main3d PRIVATE IBAMR::IBAMR3d)
