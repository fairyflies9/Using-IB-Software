# IBFE/06 Active tension

A free elastic plate in a periodic box of fluid contracts because of an active tension along its length, like a strip of muscle. One setting in the input file, `FIBER_MODE`, chooses where and when the tension acts. This example shows how to add an active stress to the passive material model, and why the tension in the code is not quite the tension in the deformed plate.

| | |
|---|---|
| Method | Immersed boundary finite element (IBFE) |
| Dimension | 2D |
| Chapters | 20 (fiber tension and active stress), 19 (stress functions), 28 (finite element data in VisIt) |
| Run time | under a minute on 4 cores (23 to 41 s on a laptop, depending on the mode and the IBAMR version) |
| Tested with | IBAMR 0.16.0 and 0.19.0 (autoibamr; GCC 13.3, Open MPI 4.1.6, Ubuntu 24.04) |
| Upstream relative | `examples/IBFE/explicit/ex2` in IBAMR (same passive stress model) |

## The three modes

Set `FIBER_MODE` near the top of `input2d`:

| `FIBER_MODE` | Where and when the tension acts | Peak tension |
|---|---|---|
| `"STATIC"` | The whole plate, during the first half of every second. | `TENSION_STATIC = 20` |
| `"MOVING"` | A pulse of tension, a Gaussian of width 0.1 (`PULSE_WIDTH`), travels along the plate from x = −0.5 to x = 0.5 once a second. | `TENSION_MOVING = 40` |
| `"ALTERNATING"` | The same moving pulse, but only in the bottom half of the plate (reference y < 0), so the plate bends. | `TENSION_ALTERNATING = 30` |

In the course versions these were three separate folders (`FiberStress2D`, `MovingFiberStress2D` and `AltMovingFiberStress2D`) with nearly identical programs. The values above are theirs, and each mode gives exactly the same results as its course program (checked with IBAMR 0.19.0: the node positions agree to the last digit).

## Files

| File | What it is |
|---|---|
| `main.cpp` | The IBAMR program, including the active stress and the passive stress functions |
| `input2d` | Physical, grid, solver and output settings, and the `FIBER_MODE` choice |
| `IBFE_Mesh2D_128.mat` | The plate's mesh: 101 nodes and 130 triangles, in libMesh's MATLAB mesh format (the same mesh as IBFE/01, which explains how it was made) |
| `CMakeLists.txt` | Build instructions for CMake |
| `job.slurm` | Batch script for Puma |

## The physics

- **Domain:** 2 by 2, periodic in both directions, with 2 grid levels (32 cells across the coarse level, 128 on the fine level).
- **Fluid:** density 1 and viscosity 0.01.
- **Plate:** 1.0 long and 0.0312 thick, centered at the origin, with nothing holding it in place. Its passive material is neo-Hookean with shear modulus μ = 10 (`SHEAR_MODULUS`), split into a deviatoric part μ**F** and a dilational part −μ**F**⁻ᵀ as in IBFE/01.
- **Active stress:** the fibers run along the plate, in the direction **f**₀ = (1, 0) of the reference (starting) configuration. The active first Piola–Kirchhoff stress is

  **P**ₐ = J T **F** (**f**₀ ⊗ **f**₀),  J = det **F**,

  and it is registered as a third stress function, which IBFE adds to the two passive ones.

### What T means

T is a tension measured in the reference configuration. In the deformed plate a fiber has been stretched by λ = |**F** **f**₀| and points along **f** = **F** **f**₀ / λ. The true (Cauchy) stress of the active part is

  σₐ = J⁻¹ **P**ₐ **F**ᵀ = T λ² **f** ⊗ **f**,

so the true tension is T λ², not T. The two agree only while the plate is unstretched (λ = 1). When the plate contracts, λ < 1 and the true tension is smaller than T. In the STATIC run below the plate shortens to about 0.68 of its length, so at that moment the true tension is about 20 × 0.68² ≈ 9. (In terms of the second Piola–Kirchhoff stress, **S** = **F**⁻¹ **P**ₐ = J T **f**₀ ⊗ **f**₀, which lives entirely in the reference configuration.)

The sign of **f**₀ does not matter, because only **f**₀ ⊗ **f**₀ enters the stress. The course files used (−1, 0); this version uses (1, 0) and gets the same stress.

## Build and run

On Puma, work inside an interactive session or a batch job, because the modules load only on compute nodes. On a laptop with autoibamr, skip the `module` line.

```bash
module load gnu13 openmpi5
source ~/autoibamr/configuration/enable.sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j 4
mpirun -np 4 ./build/main2d input2d
```

On Puma, submit `job.slurm` with `sbatch job.slurm` instead.

If `FIBER_MODE` is misspelled, the run stops at once with

```
Unknown FIBER_MODE = "..." in the input file.
Valid options are: STATIC, MOVING, ALTERNATING
```

## What you should see

Each run takes 4000 time steps and saves 41 frames. Measured from `output.ex2` (length = distance between the nodes that start at x = −0.5 and x = 0.5 on the center line; bend = height of the middle node above the average of those two ends):

**STATIC**: the plate shortens quickly while the tension is on and springs back when it is off.

| Time | Length | Notes |
|---|---|---|
| 0 | 1.000 | |
| 0.2 | 0.676 | shortest in the first cycle; the plate is 0.047 thick instead of 0.031 |
| 0.4 | 0.786 | still under tension, but slightly longer again |
| 0.8 | 1.094 | tension off since t = 0.5: the plate overshoots its rest length |
| 1.2 | 0.663 | the next cycles repeat this (0.663 at t = 2.2 and 0.662 at t = 3.2) |

In the fourth cycle the plate also starts to bend: at t = 3.8 its middle is 0.047 below its ends. The bend grows from tiny asymmetries, and this part of the run is the most sensitive to round-off (IBAMR 0.16.0 and 0.19.0 differ there by 1 × 10⁻⁵).

**MOVING**: the plate stays straight. After the first moments its length stays between 0.910 and 0.961 as the pulse travels, and it swims slowly in the direction the pulse travels: its center moves to x = 0.014 at t = 1, 0.027 at t = 2, 0.041 at t = 3 and 0.054 at t = 4.

**ALTERNATING**: the bottom half shortens and the top half does not, so the plate bends with its ends down. The bend grows every cycle: 0.038 at t = 1, 0.091 at t = 2, 0.148 at t = 3 and 0.191 at t = 4.

IBAMR 0.16.0 and 0.19.0 give the same numbers.

The output folder `viz_IB2d/` holds `dumps.visit` (the fluid: `U`, `P`, `Omega`, `F`, `Div_U`) and `output.ex2` (the plate: `dX_0`, `dX_1`, `X_0`, `X_1`, `F_0`, `F_1`, `U_0`, `U_1`). It is 12 to 13 MB with IBAMR 0.19.0 and 17 to 18 MB with 0.16.0, which also writes `U_x`, `U_y`, `F_x` and `F_y`.

## Looking at it in VisIt

1. Open `viz_IB2d/dumps.visit`, then choose **Add → Pseudocolor → Omega** and **Draw**.
2. Open `viz_IB2d/output.ex2`, choose **Add → Mesh**, and pick the plate's mesh.
3. To move the mesh with the plate, make a vector expression in **Controls → Expressions**: name `dX`, type *Vector*, definition `{dX_0, dX_1}`. Then add **Operators → Transforms → Displace** to the mesh plot and set its variable to `dX`.

The plate is thin, so zoom in to see it shorten and thicken.

## Things to try

- Make the plate stiffer with `SHEAR_MODULUS = 40` and `FIBER_MODE = "STATIC"`. It then shortens only to 0.873 (instead of 0.662) and springs back to at most 1.033.
- Do the course homework: let a sine wave of tension travel along the plate. In `active_tension()`, replace the two lines after the `if` in the `MOVING` case with

  ```cpp
  const double body_length = 1.0;
  return 0.5 * T_max * (1.0 + std::sin(2.0 * libMesh::pi * (s(0) / body_length + time)));
  ```

  The factor 0.5 (1 + sin …) keeps the tension between 0 and `T_max`, so it never pushes. (The formula on the course slide had an unclosed parenthesis.)
- Squeeze the top and the bottom halves out of phase, the second part of the homework: use the sign of `s(1)` to shift the phase of the wave in one half.

## History

The fiber tension examples were adapted from Alex Hoover's for the UNC IBFE tutorials (2014–2018). The University of Arizona versions (2022–2024) already used `std::unique_ptr` and had commented out the old configuration headers; one of their folders also carried a 13 MB compiled program, which is not kept. The changes for current IBAMR:

- A CMake build replaces the Makefile.
- `main.cpp` starts IBAMR with `IBTKInit` and uses `libMesh::Order`.
- The three folders became one program with the `FIBER_MODE` setting.
- The fiber direction `f_0` is declared once, as a unit vector. The course files also had a commented-out second declaration with the wrong type (`TensorValue`).
- The comments and this README explain what T means.
- The mesh file, shear modulus, tensions and pulse width can be set in `input2d`.
- Restarted runs now save and reload the plate's finite element data and append to `output.ex2`, as IBAMR's own examples do. Unlike those examples, only processor 0 reopens `output.ex2`: when every process reopens it, a restart on more than one process leaves a file that can no longer be read (tested with IBAMR 0.16.0 and 0.19.0).
- The input file has Unix line endings. The keys `use_IB_spread_operator` and `use_IB_interp_operator`, which IBAMR no longer reads, are removed.
- The course job scripts asked for 94 cores for 12 hours. Four cores run each mode in under a minute.

The original files are in `examples/legacy/`.
