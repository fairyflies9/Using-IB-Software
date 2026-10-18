# IB/09 Curling beam

A straight flexible beam lies in a box of still fluid, clamped at its left end by two target points. Before every time step the program raises the beams' preferred curvature, from zero at t = 0 to that of a quarter circle at t = 1 s, so the beam curls upward into a quarter circle and then settles. This example goes with the resting-curvature chapter of *Using IB Software* (chapter 10): it is the course's `Example_2Dbeams_curvature` ("the curvature of a 2D fiber is increased at each time step; at t = 1 it should form a quarter circle") rebuilt on the leaf of IB/03.

| | |
|---|---|
| Method | Immersed boundary (IB): springs, beams with a time-dependent preferred curvature, two target points |
| Dimension | 2D |
| Chapters | 10 (resting curvature and beams), 9a (update functions), 6 (structure files), 11 (forces) |
| Run time | about 12 minutes on 3 cores (0.012 s per step on a desktop PC under WSL; 60,000 steps) |
| Tested with | IBAMR 0.16.0 and 0.19.0 (autoibamr; GCC 13.3, Open MPI 4.1.6, Ubuntu 24.04) |
| Upstream relative | `examples/IB/explicit/ex3` in IBAMR (a filament of springs and beams, with zero preferred curvature) |

## Files

| File | What it is |
|---|---|
| `main.cpp` | The IBAMR program: the program of IB/07 with `update_beams()` called before each time step instead of `update_target_point_positions()`. The time over which the curvature grows, `T_CURL`, is read from the input file. It also writes the positions and forces every few steps (`output_data`). |
| `update_beams.cpp`, `.h` | The function that sets every beam's preferred curvature (`IBBeamForceSpec::getMeshDependentCurvatures()`) to the second difference of a quarter circle of radius R(t) |
| `input2d` | Physical, grid, solver and output settings, the boundary conditions (no-slip walls) and `T_CURL = 1.0` |
| `beam_512.vertex` | 103 points on the line y = 0, from x = −0.05 (point 0, the clamped end) to x = +0.05 (point 102, the free end) |
| `beam_512.spring` | 102 springs joining neighbors: `i j stiffness rest_length` |
| `beam_512.beam` | 101 beams, one for each three neighbors: `i−1 i i+1 stiffness` (four columns: the preferred curvature starts at zero and the program sets it) |
| `beam_512.target` | the two target points, 0 and 1: `index stiffness`. Two points fix the end's position and direction. |
| `generate_mesh2d.m`, `generate_mesh2d.py` | MATLAB/Octave and Python scripts that write the four structure files. They write identical files (checked with Octave 8.4 and Python 3.12). |
| `CMakeLists.txt` | Build instructions for CMake. It lists both `.cpp` files. |
| `job.slurm` | Batch script for Puma |

## The physics

- **Domain:** 1 m by 1 m, not periodic, with no-slip walls (the boundary conditions of IB/03 with the flow speed `V` set to 0).
- **Fluid:** density 1000 kg/m³ and viscosity 4 N s/m² (IB/03's). The beam's tip moves at a few centimetres per second, so the Reynolds number ρUℓ/μ is about 1.
- **Grid:** 3 levels of adaptive refinement with ratio 4 and 32 cells on the coarsest level, so the finest grid has 512 cells across and Δx = 1/512 m ≈ 2 mm.
- **Beam:** 0.1 m long, with 103 points ds = 0.1/102 m ≈ Δx/2 apart.
- **Springs:** stiffness K = 30 (tension per unit strain); the `.spring` file holds K/ds = 3.06 × 10⁴. Rest length ds.
- **Beams:** bending stiffness k_b = 2 × 10⁻², four times the leaf's; the `.beam` file holds it divided by ds³, 2.12 × 10⁷.
- **Target points:** points 0 and 1, pulled toward where they start with κ = 30/ds = 3.06 × 10⁴.
- **The curvature:** IBAMR's beam pushes the middle point of each triple toward X_{i−1} + X_{i+1} − 2X_i = C_i, the preferred second difference (chapter 10). `update_beams.cpp` sets C_i to the second difference of the points X_i = (R sin φ_i, R (1 − cos φ_i)), φ_i = i (π/2)/(npts − 1), a quarter circle that leaves the clamp along +x and curls upward, with R(t) = R_final · min(t/T_CURL, 1) and R_final = 0.1/(π/2) = 0.0637 m, the radius whose quarter circle is as long as the beam. Because the beam's points are ds apart while the circle's are R Δφ apart, the curvature the beam is asked for is R(t)/R_final²: it grows linearly from 0 to 1/R_final, and before t = 1 s the preferred shape is a flatter arc of the same length.
- **Time:** 60,000 steps of 5 × 10⁻⁵ s (3 s): the curl takes 1 s, then the beam settles over the next two.

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

The first line of the run log says what the program will do:

```
Curling beam: the preferred curvature reaches a quarter circle at t = 1 s
```

## What you should see

Every 800 steps the screen shows a line like

```
integral{F} = -0.336556 0.117695
```

That is the sum of the Lagrangian forces: the force on the two target points, since the springs and beams pull their own points with forces that cancel in the sum (chapter 11). It is the force the clamp needs to hold the beam while it curls.

Measured from the saved positions (`tools/ch10_figures.py` of the tutorial repository; the beam's tip is point 102, the clamp is at (−0.05, 0)):

| Time (s) | Tip, x and y from the clamp (cm) | Largest distance between the beam and the arc its curvature asks for (mm) |
|---|---|---|
| 0.25 | 9.96, 0.25 | 16 |
| 0.5 | 9.89, 0.54 | 32 |
| 0.75 | 9.70, 0.99 | 44 |
| 1.0 | 9.19, 1.98 | 52 |
| 1.5 | 8.32, 3.85 | 32 |
| 2.0 | 7.27, 5.45 | 13 |
| 2.5 | 6.38, 6.39 | 0.3 |
| 3.0 | 6.02, 6.71 | 5 |

The quarter circle's tip is at (6.37, 6.37) cm from the clamp.

What to notice:

- The beam lags the arc its curvature asks for while the curvature is changing (5 cm at t = 1 s), and settles onto the quarter circle over the next two seconds (within 5 mm at t = 3 s). The lag is dynamic: the fluid has to be pushed out of the way, and a beam of this stiffness in a fluid of this viscosity takes about a second to do it.
- Near the clamp the beam first dips below y = 0: the curvature lifts the far part, and the reaction, with the clamp holding the base, bends the near part down until the whole beam has turned.
- With the leaf's own stiffness (k_b = 5 × 10⁻³, `DT = 1.0e-4`, μ = 0.1) the run works too, but the beam is 44 mm from its arc at t = 1 s and still 13 mm at 1.5 s. With k_b = 2 × 10⁻² and μ = 0.1 (a Reynolds number of about 100) the beam overshoots the quarter circle and oscillates about it with a period of about 1 s (29 mm from the arc at t = 1 s, 2 mm at 1.3 s, 21 mm at 1.8 s); with μ = 1 it lags 41 mm at t = 1 s and settles like the shipped run; the viscosity of 4 N s/m² damps the oscillation out. `DT = 1.0e-4` with k_b = 2 × 10⁻² stops at the CFL limit; `DT = 5.0e-5` runs (chapter 8a's rule: four times the stiffness, half the step).

The output folders:

- `viz_IB2d/dumps.visit` holds the fluid data on the adaptive grid: velocity `U`, pressure `P`, vorticity `Omega` and `Div U` (51 frames).
- `viz_IB2d/lag_data.visit` holds the beam as the mesh `beam_512_mesh`.
- `hier_data_IB2d/X.NNNNN` and `F.NNNNN` are the points' positions and forces as plain-text PETSc vectors, with x and y alternating. Chapter 11 reads them in MATLAB and Python.
- `IB2d.log` is the log file.

## Looking at it in VisIt

1. Open `viz_IB2d/lag_data.visit`, then **Add → Mesh → beam_512_mesh** and **Draw**; step through the frames to watch the curl.
2. Open `viz_IB2d/dumps.visit` as a second database and add **Pseudocolor → Omega** or a **Vector** plot of `U`: the curling tip sheds a pair of eddies that the viscous fluid damps quickly.

IBAMR 0.19 writes the velocity only as the vector `U`. Older versions also wrote `U_x` and `U_y`.

## Things to try

- `T_CURL = 2.0` (and `END_TIME = 3.0`): a slower curl lags less.
- Make the beam curl the other way (change the sign of `curv[1]` in `update_beams.cpp`), or into a half circle (let φ run to π and double R_final).
- Give the beam the quarter circle's curvature in the `.beam` file from the start (six columns: the second differences of the circle, chapter 10's worksheet recipe) and comment out the call to `update_beams()`: the beam springs into shape at once.
- Lower the viscosity to 0.1 and watch the overshoot; raise the stiffness to 5 × 10⁻² and lower `DT` to 2.5e-5 to follow the arc more closely.
- Untether the beam (empty the `.target` file: write `0` on its first line): it curls and drifts, and the sum of the forces is then zero.

## History

This example is new in the tutorial. The course's `Example_2Dbeams_curvature.zip` (2013; also offered in the 2018 "Changing Resting Curvature" deck) is no longer in the course folders, so the example was rebuilt from the slides' fragments of `update_beams.C` on the leaf of IB/03. Changes from those fragments:

- The point's number along the beam is counted from the structure's first Lagrangian index (`getLagrangianStructureIndexRange`), not from the global index `lag_idx`, so the function is right whatever comes before this structure in `structure_names`.
- The angle step is (π/2)/(npts − 1) (npts − 1 gaps between npts points); the course divided by npts.
- The radius of the quarter circle comes from the beam's length and `T_CURL` from the input file, instead of the hard-coded `current_time/(10*pi/2)` (which is the same quarter circle, of radius 1/(5π), for a 0.1 m beam at t = 1).
- The arc starts along the clamp's direction (the course's circle, like the 2013 worksheet's, started vertically).
- The curvature is an `IBTK::Vector` taken by reference (`Point&` in the 2018 slides, `TinyVector<double, 2>&` in 2013); ghost nodes are visited; the loop uses the current IBAMR style.
- The beam is clamped by two target points, so that its orientation is fixed; the preferred curvature is a vector in laboratory coordinates and would otherwise fight any rotation of the beam (chapter 10).
