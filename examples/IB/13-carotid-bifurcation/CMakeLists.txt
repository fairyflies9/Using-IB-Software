# IB/13 carotid bifurcation: pulsatile flow through a carotid bifurcation whose walls are held by target points.
#
# Build (after loading the compilers used for IBAMR and sourcing autoibamr's
# enable.sh, which sets IBAMR_ROOT):
#   cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
#   cmake --build build -j 4
# Run from this folder:
#   mpirun -np 4 ./build/main2d input2d
# The version range turns on the newer CMake policies, which silences two
# harmless developer warnings that IBAMR's own CMake files would print.
cmake_minimum_required(VERSION 3.15...3.30)
project(ib13_carotid_bifurcation LANGUAGES C CXX)

# Accepts IBAMR 0.16.0 or newer. CMake finds it through the IBAMR_ROOT
# environment variable, or pass -DIBAMR_ROOT=/path/to/IBAMR.
find_package(IBAMR 0.16.0 REQUIRED)

add_executable(main2d main.cpp)
target_link_libraries(main2d PRIVATE IBAMR::IBAMR2d)
