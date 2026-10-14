# IB/11 heart-tube pump: an elastic tube in a racetrack, driven by moving target
# points or by spring force functions of your own (five actuation modes).
#
# Build (after loading the compilers used for IBAMR and sourcing autoibamr's
# enable.sh, which sets IBAMR_ROOT):
#   cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
#   cmake --build build -j 4
# Run from this folder:
#   mpirun -np 4 ./build/main2d input2d              # target-point suction pump
#   mpirun -np 4 ./build/main2d input2d.force-vp     # the same pump by an applied force
# The version range turns on the newer CMake policies, which silences two
# harmless developer warnings that IBAMR's own CMake files would print.
cmake_minimum_required(VERSION 3.15...3.30)
project(ib11_heart_tube_pump LANGUAGES C CXX)

# Accepts IBAMR 0.16.0 or newer. CMake finds it through the IBAMR_ROOT
# environment variable, or pass -DIBAMR_ROOT=/path/to/IBAMR.
find_package(IBAMR 0.16.0 REQUIRED)

# Every .cpp file of the program must be listed here.
add_executable(main2d main.cpp
                      update_target_point_positions.cpp
                      update_target_point_positions_peri.cpp
                      update_springs_vp_aforce.cpp
                      update_springs_peri_aforce.cpp
                      update_springs_peri_kwave.cpp)
target_link_libraries(main2d PRIVATE IBAMR::IBAMR2d)
