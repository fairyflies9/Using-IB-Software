# IB/08 Glycocalyx in 3D

One glycocalyx fiber, a cylinder made of 13,600 target points, stands on the floor of a box of fluid. The lid of the box slides sideways, so the fluid is sheared past the fiber. The box is periodic in x and y, so the run models one fiber in an endless square array of fibers. This is the 3D IBAMR example in *Using IB Software*. It shows a box that is not a cube, periodic and wall boundaries together, a moving wall, target points in 3D, and 3D output for VisIt.

| | |
|---|---|
| Method | Immersed boundary (IB), target points only |
| Dimension | 3D |
| Chapters | 12 (3D simulations), 7 (boundary conditions), 9 (moving target points), 27 (3D visualization) |
| Run time | about 20 minutes on 4 cores (0.052 s per step on a laptop; 20,000 steps) |
| Tested with | IBAMR 0.16.0 and 0.19.0 (autoibamr; GCC 13.3, Open MPI 4.1.6, Ubuntu 24.04) |
| Upstream relative | `examples/IB/explicit/ex7` in IBAMR (3D posts held by target points and moved by changing the target positions) |

## Files

| File | What it is |
|---|---|
| `main.cpp` | The IBAMR program: the rubber band's program (IB/01) plus the call that moves the target points |
| `update_target_point_positions.cpp`, `.h` | Moves every target point in x by `TARGET_VELOCITY` × Δt each step. It is called only when `TARGET_VELOCITY` is not 0. |
| `input3d` | Physical, grid, solver and output settings, the boundary conditions, and the options `SHEAR_START` and `TARGET_VELOCITY` |
| `glyco_512.vertex` | 13,600 points: 160 rings of 85 points, one `x y z` per line |
| `glyco_512.target` | Every point is a target point, with stiffness 3.19 × 10⁴ |
| `generate_mesh3d.m` | MATLAB or Octave script that writes the two structure files |
| `generate_mesh3d.py` | Python 3 version of `generate_mesh3d.m` (standard library only): `python3 generate_mesh3d.py`. Its `.target` file is identical to the one in this folder. In its `.vertex` file 160 of the 40,800 coordinates differ in the last digit, by about 10⁻¹⁷ m, the ordinary round-off of sine and cosine in different math libraries (Octave gives the same 160 differences). |
| `CMakeLists.txt` | Build instructions for CMake. The program has two source files. |
| `job.slurm` | Batch script for Puma |

## The physics

- **Box:** 1/8 m by 1/8 m by 1 m. It runs from −1/16 to 1/16 in x and y and from −0.5 to 0.5 in z, and it is periodic in x and y.
- **Grid:** 3 levels with refinement ratio 4: 4 × 4 × 32 cells on the coarsest level and the equivalent of 64 × 64 × 512 on the finest, so Δx = 1/512 m. The finest level covers only a box around the fiber (40 × 40 × 96 cells). The whole grid has 161,280 cells.
- **Fluid:** density 1000 kg/m³ and viscosity 40 N s/m².
- **Walls:** the floor (z = −0.5) is fixed. The lid (z = 0.5) moves in x with speed V tanh(2t), with V = 0.1 m/s, so it reaches 96% of V by t = 1 s.
- **Fiber:** a cylinder of radius 0.0132 m (1/64 m minus 1.25 Δx, which allows for the width of the delta function) and height 10/64 = 0.156 m, standing on the floor. Its 160 rings of 85 points are spaced about Δx/2 apart. Every point is a target point with stiffness 3.19 × 10⁴ N/m, which holds it in place.
- **Reynolds number:** ρ V_glyco h/μ = 0.061, where h = 0.156 m is the fiber's height and V_glyco = V h/L = 0.0156 m/s is the speed of the steady shear flow at that height.

The target stiffness in `glyco_512.target` is κ/ds with κ = 5. In `generate_mesh3d.m`, ds = radius/(points around − 1) = 1.6 × 10⁻⁴ m. That is **not** the spacing of the points around the cylinder, which is 2π × radius/85 = 9.7 × 10⁻⁴ m. So the stiffness is 6.2 times what dividing by the true spacing would give. The scripts keep this value so that the files match every earlier version.

**How long the flow takes to reach the fiber.** The lid drags the fluid from the top, and the motion spreads down by viscous diffusion, with ν = μ/ρ = 0.04 m²/s. The 1D solution of this start-up shear flow (without the fiber) gives, at the height of the fiber's top, 0.5% of the final speed at t = 1 s, 13% at 2 s, 55% at 4 s and 96% at 10 s. The course version therefore ran to t = 10 s, which is a million time steps. The default here stops at t = 0.2 s, before the flow reaches the fiber. To see the flow past the fiber in a short run, set `SHEAR_START = 1` (below).

## Build and run

On Puma, work inside an interactive session or a batch job, because the modules load only on compute nodes. On a laptop with autoibamr, skip the `module` line.

```bash
module load gnu13 openmpi5
source ~/autoibamr/configuration/enable.sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j 4
mpirun -np 4 ./build/main3d input3d
```

On Puma, submit `job.slurm` with `sbatch job.slurm` instead.

To continue a finished run, raise `END_TIME` in `input3d` and give the restart folder and the last step number:

```bash
mpirun -np 4 ./build/main3d input3d restart_IB3d 20000
```

The program writes restart files at the start, every simulated second, and at the end of a run.

## What you should see

The run takes 20,000 time steps of 10⁻⁵ s. On 4 cores of a desktop PC (Intel i9-12900KF under WSL) a step took 0.052 s when nothing else was running and 0.060 s with other jobs on the machine, so the run takes about 20 minutes. When the machine was full, a step took up to 0.1 s and the run took 31 minutes. IBAMR 0.16.0 and 0.19.0 run at the same speed.

Every 400 steps the screen shows a line like

```
integral{F} = 0 5.4653e-20 0
```

That is the total target force on the fiber. It stays at round-off level, about 10⁻¹¹ N or less, because no flow reaches the fiber in 0.2 s.

The flow that is there is a layer under the lid. Averaged over x and y, the x-velocity at t = 0.2 s is:

| Height z (m) | IBAMR (m/s) | 1D solution (m/s) |
|---|---|---|
| 0.5 (lid) | 0.0380 | 0.0380 |
| 0.469 | 0.0255 | 0.0255 |
| 0.438 | 0.0165 | 0.0164 |
| 0.406 | 0.0103 | 0.0102 |
| 0.375 | 0.0062 | 0.0061 |
| 0.344 | 0.0035 | 0.0035 |

The IBAMR numbers come from the coarsest grid level in the VisIt files. The 1D solution is the start-up shear flow without the fiber, solved separately. Near the lid they agree to within 1%; lower down, the coarse grid (32 cells over the 1 m height) blurs the thin layer by a few percent. IBAMR 0.16.0 and 0.19.0 give the same velocities to all 7 digits that the VisIt files store (compared at t = 0.07 s) and the same `integral{F}` lines.

The grid does not change during the run: 161,280 cells, with the finest level only around the fiber. The output (IBAMR 0.19.0):

- `viz_IB3d/dumps.visit`: 21 frames of the fluid (velocity `U`, pressure `P`, vorticity `Omega` and `Div_U`), 79 MB in all. IBAMR 0.16.0 also writes the separate components such as `U_x`, which makes its frames about 1.8 times larger.
- `viz_IB3d/lag_data.visit`: the fiber's points, 184 kB per frame.
- `hier_data_IB3d/X.NNNNN` and `F.NNNNN`: the points' positions and forces every 400 steps (50 of each, 27 MB).
- `restart_IB3d/`: restart files at steps 0 and 20,000 (12 MB and 22 MB).
- `IB3d.log`: the log file.

## Starting from the steady shear flow

With `SHEAR_START = 1` the fluid starts in the steady shear flow and the lid moves at V from the first step, so the flow pushes on the fiber at once. The first number of each `integral{F}` line is then the force in x that the target points exert to hold the fiber against the flow, so minus it is the drag on the fiber: −0.47 N at t = 0.01 s, −0.40 N at 0.02 s, −0.37 N at 0.04 s and −0.31 N at 0.11 s (IBAMR 0.19.0; 0.16.0 gives the same curve, −0.397 N at 0.02 s and −0.373 N at 0.04 s). The drag falls slowly because the fiber slows the fluid around it: in a box that is periodic in x and y the fiber is one of an endless array, and together they slow the flow near the floor. The very first value, at t = 0.004 s, is larger (about 1 N) because the flow starts impulsively.

## Looking at it in VisIt

1. Open `viz_IB3d/dumps.visit`, then choose **Add → Pseudocolor** with the expression `U[0]` (the x-velocity) and **Draw**. You see only the outside of the box.
2. To look inside, add **Operators → Slicing → Slice** and set its normal to the y-axis (0, 1, 0) through the origin. The slice is the x-z plane through the fiber. With the default run, the moving fluid is a layer under the lid.
3. Open `viz_IB3d/lag_data.visit` as a second database, then choose **Add → Mesh → glyco_512_vertices** and **Draw**. The fiber's 13,600 points appear as a cylinder of dots.
4. Chapter 27 shows how to add a **ThreeSlice**, contours, and streamlines around the fiber (run with `SHEAR_START = 1` first, so that there is flow around it).

IBAMR 0.19 writes the velocity only as the vector `U`. Older versions also wrote `U_x`, `U_y` and `U_z`. The expressions above work in both.

## Things to try

- Set `SHEAR_START = 1` to see the flow push on the fiber within the default 0.2 s (results above).
- Drag the fiber through the fluid with `TARGET_VELOCITY`. With `TARGET_VELOCITY = 0.05` (m/s) the run is unstable: the velocity near the fiber grows until, at step 709, the run stops with `Internal RefineSchedule<DIM> error`. With `TARGET_VELOCITY = 0.01` the run goes on, but the target force grows steadily, from 13 N at t = 0.01 s to 111 N at t = 0.04 s, probably because the fiber's bottom ring of points sits on the floor, where the no-slip condition holds the fluid still: those points cannot follow their targets, and the force on them grows with the distance their targets have moved. To drag a fiber, start it above the floor (change the lowest z in `generate_mesh3d.m`) or do not tether its bottom ring.
- Set the viscosity from a Reynolds number, as the 2014 version did: comment out `MU = 40` and uncomment the two `RE` lines. With `RE = 1` the viscosity is 2.44 N s/m², and the lid's motion spreads down 16 times more slowly, so with `SHEAR_START = 0` nothing reaches the fiber in 0.2 s either. With `SHEAR_START = 1` as well, the force on the fiber is 6 to 7 times smaller than with `MU = 40`: −0.063 N at t = 0.03 s and −0.046 N at 0.1 s (against −0.38 and −0.32 N). The impulsive start rings for the first 0.02 s (forces of +7.5, −3.7 and +0.3 N at t = 0.004, 0.008 and 0.016 s) before the force settles.
- Run the course's full 10 s. Set `END_TIME = 10.0`, or continue a finished run from its restart files (see "Build and run"). From the measured 0.052 to 0.060 s per step, the million steps take about 15 to 17 hours on 4 cores, or about 60 core-hours. The course's job script asked for 1 core for 4 hours. On one core a step took 0.35 s in a short test on a busy laptop (the 4-core run on the same machine took 0.06 s per step at the time), so one core would need about 4 days for the million steps, and the 4-hour job would have reached only t ≈ 0.4 s.
- Change the time step `DT`. With `SHEAR_START = 1`, `DT = 2.0e-5` runs, but by t = 0.045 s the force on the fiber is 33% smaller than with `DT = 1.0e-5` (−0.244 instead of −0.367 N), so the result depends on the step. With `DT = 5.0e-5` the run is unstable: the largest velocity grows about tenfold every step, and after 4 steps the run stops with `Internal RefineSchedule<DIM> error`. (Tested with IBAMR 0.16.0.)

## History

The first version of this example is in the IBAMR-Examples repository (`3DGlycocalyx`, 2014, built against IBAMR at UNC before release 0.1). It set the viscosity from a Reynolds number (`RE = 1`, so `MU = 2.44`) and had code that moved the target points, with the speed set to 0. The UNC course version (2018) and the University of Arizona version (2020–2024) set `MU = 40` and left out the moving target points. All three use the same structure files. The changes for current IBAMR:

- A CMake build replaces the Makefile, and the helper file `update_target_point_positions.C` became `.cpp`.
- `main.cpp` starts IBAMR with `IBTKInit` and no longer includes the old configuration headers. It is the rubber band's program (IB/01) with the target-point update added.
- The 2014 version's options are back as input settings: the Reynolds-number viscosity (commented out in `input3d`) and the moving target points (`TARGET_VELOCITY`, default 0).
- `SHEAR_START` is new. With its default, 0, the run is the course version's.
- The lid speed is the input variable `V`. The course version defined `V = 0.1` but wrote 0.1 into the boundary condition, so changing `V` did nothing.
- The comments in `generate_mesh3d.m` described a rectangular "leaf" held by "a line of target points" (copied from a 2D example). They now describe the fiber, and they explain what `ds` scales. The stale input comment "Change Re, f, A0, c and L to match the simulation" is gone.
- `END_TIME` is 0.2 instead of 10, and the output intervals scale with it. The course version wrote a VisIt frame every 10,000 steps and the X/F files every 999 steps, because `int(0.01/DT)` rounds 999.99… down. Its restart interval, `int(1.0/DT)`, was 99,999 steps for the same reason.
- The input file has Unix line endings, so it no longer needs `//` at the end of every line.
- `generate_mesh3d.py`, a Python version of the MATLAB script, is new.

The 2014 folder also held an 83 MB compiled `main3d`, an `input2d` from another example and an editor backup file. They are not carried over. The course versions are in `examples/legacy/` (`UA-Examples/IBAMR Examples/4-Example_3DGlycocalyx` and `UNC-Examples/4-Example_3DGlycocalyx`); the 2014 version stays in the IBAMR-Examples repository.
