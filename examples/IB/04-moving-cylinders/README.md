# IB/04 Moving cylinders

A row of 9 small cylinders ("bristles") is dragged through a box of very viscous fluid. Every point of the cylinders is a target point, and a short C++ function, `update_target_point_positions()`, moves the target points a little before each time step, so the cylinders follow them. This is the first example in *Using IB Software* that changes the structure while the simulation runs.

| | |
|---|---|
| Method | Immersed boundary (IB): moving target points |
| Dimension | 2D |
| Chapters | 9 (target points and springs), 6 (structure files), 11 (forces) |
| Run time | about 6 minutes on 4 cores (0.03 s per step on a laptop; 10,000 steps) |
| Tested with | IBAMR 0.16.0 and 0.19.0 (autoibamr; GCC 13.3, Open MPI 4.1.6, Ubuntu 24.04) |
| Upstream relative | `examples/IB/explicit/ex2` in IBAMR holds a cylinder still with target points in a flow; `examples/ConstraintIB/moving_plate` moves a body with prescribed motion instead of target points |

## Files

| File | What it is |
|---|---|
| `main.cpp` | The IBAMR program: the program of IB/01 plus a call to `update_target_point_positions()` before each time step. It also writes the positions and forces every few steps. |
| `update_target_point_positions.cpp`, `.h` | The function that moves the target points |
| `input2d` | Physical, grid, solver and output settings |
| `bristles1024.vertex` | 297 points: 9 cylinders of 33 points each |
| `bristles1024.target` | every point is a target point: `index stiffness` |
| `generate_mesh2d.m`, `generate_mesh2d.py` | MATLAB/Octave and Python scripts that write the two structure files (see the note below) |
| `CMakeLists.txt` | Build instructions for CMake. It lists both `.cpp` files. |
| `job.slurm` | Batch script for Puma |

The course had no generator for the structure files, so `generate_mesh2d.m` and `generate_mesh2d.py` were written in 2026. `generate_mesh2d.py` (Python 3.12) and Octave 8.4 write exactly the files in this folder. MATLAB R2024a writes the same files except for 9 of the 594 coordinates: the y coordinate of the 12th point on each cylinder differs in the 17th significant digit, by 4 × 10⁻¹⁹ m, because MATLAB's sine rounds that one angle differently. The course's original file has MATLAB's value.

## The physics

- **Domain:** 1 m by 1 m, periodic in both directions.
- **Fluid:** density 1000 kg/m³ and viscosity 100 N s/m², so the flow is very slow and viscous.
- **Grid:** 4 levels of adaptive refinement with ratio 4 and 16 cells on the coarsest level, so the finest grid has 1024 cells across and Δx = 1/1024 m ≈ 1 mm.
- **Cylinders:** radius 2.5 mm (5 Δx across), centers 0.05 m apart on the x axis from x = −0.2 to x = 0.2. Each has 33 points, about Δx/2 apart.
- **Target points:** every point is pulled toward its target position with the force κ (X_target − X), κ = 4.096 × 10⁶.
- **Motion:** `update_target_point_positions.cpp` moves the targets up (in +y). The speed rises linearly from 0 to V = 0.2 m/s over the first 0.1 s and then stays at 0.2 m/s, so the row has moved 0.01 m by t = 0.1 s and 0.03 m by t = 0.2 s. The Reynolds number based on one cylinder's diameter is ρVd/μ = 0.01, and based on the whole row (0.405 m) it is about 0.8.

Each cylinder is a closed ring of target points with fluid inside; the fluid inside moves with the ring. The gaps between the cylinders are 0.045 m, 18 times a cylinder's diameter, yet at this low Reynolds number the row drags most of the fluid between the cylinders along with it: a "leaky rake", as in the bristled wings of tiny insects.

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

The program has two source files. Both must be listed in `CMakeLists.txt` (`add_executable(main2d main.cpp update_target_point_positions.cpp)`); if one is missing, the link step fails with `undefined reference to update_target_point_positions`.

## What you should see

The run takes 10,000 time steps of 2 × 10⁻⁵ s and saves 50 frames. Every 200 steps the screen shows a line like

```
integral{F} = -0.0117541 249.646
```

That is the sum of the target-point forces on all 297 points: the force that drags the row through the fluid, which is minus the drag of the fluid on the row. Its x-component stays near zero by symmetry.

Measured from the saved positions (the row's position is the average y of all points):

| Time (s) | Row has moved up (m) | Drag (N) |
|---|---|---|
| 0.01 | 0.0001 | 130 |
| 0.04 | 0.0016 | 357 |
| 0.06 | 0.0036 | 454 |
| 0.10 | 0.0100 | 595 |
| 0.11 | 0.0120 | 494 |
| 0.16 | 0.0220 | 295 |
| 0.20 | 0.0300 | 239 |

The row follows its target points exactly to the digits shown: the lag is the force divided by the stiffness, about 5 × 10⁻⁷ m, and all nine cylinders move together (their positions agree to 10⁻⁷ m). The drag peaks at the end of the acceleration, at t = 0.1 s, and then falls as more and more of the surrounding fluid is set in motion along with the row.

The time step: `DT = 2.0e-5` is the largest step that runs. With `DT = 5.0e-5` or larger the run stops within a few steps with `Time step size change encountered` (chapter 16): the target points are stiff (κ = 4 × 10⁶) and need a small step. IBAMR 0.16.0 and 0.19.0 give byte-identical positions and forces (checked at t = 0.01 s).

The output folders:

- `viz_IB2d/dumps.visit` holds the fluid data on the adaptive grid: velocity `U`, pressure `P`, vorticity `Omega` and `Div_U` (51 frames, about 30 MB).
- `viz_IB2d/lag_data.visit` holds the cylinders.
- `hier_data_IB2d/X.NNNNN` and `F.NNNNN` are the points' positions and forces as plain-text PETSc vectors, with x and y alternating. Chapter 11 reads them in MATLAB.
- `IB2d.log` is the log file.

## Looking at it in VisIt

1. Open `viz_IB2d/dumps.visit`, then choose **Add → Pseudocolor** with the expression `magnitude(U)` and **Draw**. The fluid between the cylinders moves with them, and the moving region spreads out with time.
2. Open `viz_IB2d/lag_data.visit` as a second database, then choose **Add → Mesh → bristles1024_mesh** and **Draw**. Step through the frames to watch the row move up.
3. A **Vector** plot of `U` shows how much fluid leaks between the cylinders. For one component of velocity, use `U[0]` or `U[1]`.

IBAMR 0.19 writes the velocity only as the vector `U`. Older versions also wrote `U_x` and `U_y`. The expressions above work in both.

## Things to try

- Change the spacing or the number of cylinders in `generate_mesh2d.m` (and write new structure files) to see how much fluid leaks through a sparser row.
- Lower the viscosity `MU` to 10 or 1. At a higher Reynolds number more fluid leaks between the cylinders.
- Change `V` or `time_to_acc` in `update_target_point_positions.cpp` (and rebuild), or make the row move sideways instead of up.
- Run the course's full 2 s (`END_TIME = 2.0`, 100,000 steps, about an hour on 4 cores). The row moves 0.39 m.

## History

This example comes from the UNC course version (`5-Example_2DMovingCylinders`, 2014–2020; 16 cores for 2 hours on a debug queue) and the University of Arizona version (`4-IBAMR-Example_2DMovingCylinders`, 2020–2024; 1 core for 4 hours, with a second script for 16 cores on Ocelote). The changes for current IBAMR:

- A CMake build replaces the Makefile, and `update_target_point_positions.C` became `.cpp`.
- `main.cpp` starts IBAMR with `IBTKInit` and no longer includes the old configuration headers. It is the rubber band's program (IB/01) with the target-point update added.
- The comments in `update_target_point_positions.cpp` now say that the row moves up, in y. The course comments said the targets move "to the left or right" and called the row "the wing". Unused variables are removed.
- The time step is 2.0e-5 s instead of 1.0e-6 s, and the run stops at 0.2 s instead of 2 s.
- The input file has Unix line endings, so it no longer needs `//` at the end of every line.
- `generate_mesh2d.m` and `generate_mesh2d.py` are new.

The original files are in `examples/legacy/`.
