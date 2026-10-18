# IB/06 Growing springs

A straight fiber made of springs lies in a box of very viscous fluid, and a short C++ function, `update_springs()`, makes every spring's rest length grow a little before each time step. The springs push their ends apart, so the fiber gets longer. This example goes with the target-points-and-springs chapter of *Using IB Software* and shows how to change spring parameters while the simulation runs. It also shows what springs do without beams: once the fluid's drag compresses them, the fiber folds.

| | |
|---|---|
| Method | Immersed boundary (IB): springs whose rest lengths change during the run |
| Dimension | 2D |
| Chapters | 9 (target points and springs), 6 (structure files), 10 (beams) |
| Run time | about 3 minutes on 4 cores (0.035 s per step on a desktop PC under WSL; 5000 steps) |
| Tested with | IBAMR 0.16.0 and 0.19.0 (autoibamr; GCC 13.3, Open MPI 4.1.6, Ubuntu 24.04) |
| Upstream relative | `examples/IB/explicit/ex1` in IBAMR, which the program is adapted from; IBAMR's `IBSpringForceSpec` class documentation describes the spring parameters |

## Files

| File | What it is |
|---|---|
| `main.cpp` | The IBAMR program: the program of IB/01 plus a call to `update_springs()` before each time step. It also writes the positions and forces every few steps. |
| `update_springs.cpp`, `.h` | The function that lengthens the springs |
| `input2d` | Physical, grid, solver and output settings |
| `wing_512.vertex` | 103 points on the x axis from x = 0.1 (point 0) to x = 0 (point 102). The name "wing" is historical. |
| `wing_512.spring` | 102 springs joining neighbors: `i j stiffness rest_length` |
| `generate_mesh2d.m`, `generate_mesh2d.py` | MATLAB/Octave and Python scripts that write the two structure files. They write identical files (checked with Octave 8.4 and Python 3.12). |
| `CMakeLists.txt` | Build instructions for CMake. It lists both `.cpp` files. |
| `job.slurm` | Batch script for Puma |

## The physics

- **Domain:** 1 m by 1 m, periodic in both directions.
- **Fluid:** density 1000 kg/m³ and viscosity 100 N s/m², so the flow is very slow and viscous.
- **Grid:** 4 levels of adaptive refinement with ratio 4 and 8 cells on the coarsest level, so the finest grid has 512 cells across and Δx = 1/512 m ≈ 2 mm.
- **Fiber:** 0.1 m long, on the x axis, with 103 points ds = 0.1/102 m ≈ Δx/2 apart. There are no beams and no target points, so nothing resists bending and nothing holds the fiber in place.
- **Springs:** stiffness K = 2000 (tension per unit strain); the `.spring` file holds K/ds = 2.04 × 10⁶. The rest length starts at ds, so the springs start unstretched.
- **Growth:** `update_springs.cpp` adds 0.01 × Δt to every rest length before each step, so each rest length grows at 0.01 m/s. After 0.5 s it is 6.1 times its starting value, and the rest lengths add up to 0.61 m.

A spring that is longer than its rest length pulls its ends together, and one that is shorter pushes them apart. As the rest lengths grow, the springs push, the fiber lengthens, and the fluid's drag compresses the springs a little. A straight line of compressed springs with no bending stiffness is unstable, like a column that buckles: a tiny sideways disturbance grows. The fiber therefore stays straight only for a while and then folds (see below). Example IB/03 shows what beams add: bending stiffness, which keeps a structure straight.

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

The program has two source files. Both must be listed in `CMakeLists.txt` (`add_executable(main2d main.cpp update_springs.cpp)`); if one is missing, the link step fails with `undefined reference to update_springs`.

## What you should see

The run takes 5000 time steps of 10⁻⁴ s and saves 51 frames (dump 0 and 50 more). Every 100 steps the screen shows a line like

```
integral{F} = -8.88178e-15 -2.66454e-14
```

That is the sum of all the spring forces. Each spring pulls or pushes its two ends with equal and opposite forces, so the sum stays at round-off level.

The fiber, measured from the saved positions (end to end = distance between the first and last points; length = the sum of the distances between neighbors):

| Time (s) | End to end (m) | Length (m) | Rest lengths add up to (m) | Largest sideways displacement (m) |
|---|---|---|---|---|
| 0.01 | 0.103 | 0.103 | 0.110 | 0.000 |
| 0.06 | 0.150 | 0.150 | 0.161 | 0.000 |
| 0.11 | 0.202 | 0.202 | 0.212 | 0.000 |
| 0.16 | 0.249 | 0.259 | 0.263 | 0.003 |
| 0.21 | 0.272 | 0.312 | 0.314 | 0.005 |
| 0.31 | 0.295 | 0.415 | 0.416 | 0.009 |
| 0.46 | 0.309 | 0.568 | 0.569 | 0.013 |

For about the first 0.12 s the fiber stays straight and lengthens almost as fast as the rest lengths grow; the springs are compressed by up to 5% by the drag of the fluid. Then it buckles. By t = 0.16 s it zigzags, with the folds only a few points long, and from then on the springs are nearly unstretched (the length matches the rest lengths), the folds grow (up to 7 grid cells sideways by t = 0.5 s), and the end-to-end distance grows only slowly. Because the folding is an instability that grows from tiny disturbances, its details depend on the time step: at t = 0.2 s the end-to-end distance is 0.268 m with the default `DT = 1.0e-4` and 0.255 m with `DT = 5.0e-5`. (With `DT = 5.0e-4` the run stops after 136 steps with `Time step size change encountered`; chapter 16 explains that error.) IBAMR 0.16.0 and 0.19.0 give byte-identical positions and forces (checked at t = 0.04 s).

The output folders:

- `viz_IB2d/dumps.visit` holds the fluid data on the adaptive grid: velocity `U`, pressure `P`, vorticity `Omega` and `Div U` (51 frames, 18 MB).
- `viz_IB2d/lag_data.visit` holds the fiber itself.
- `hier_data_IB2d/X.NNNNN` and `F.NNNNN` are the fiber's positions and forces as plain-text PETSc vectors, with x and y alternating. Chapter 11 reads them in MATLAB.
- `IB2d.log` is the log file.

## Looking at it in VisIt

1. Open `viz_IB2d/dumps.visit`, then choose **Add → Pseudocolor → Omega** and **Draw**. The vorticity shows the pairs of eddies that the growing fiber pushes out at its ends, and later the small eddies along the folds.
2. Open `viz_IB2d/lag_data.visit` as a second database, then choose **Add → Mesh → wing_512_mesh** and **Draw**. Step through the frames to watch the fiber lengthen and then fold.
3. For speed, use the expression `magnitude(U)`. For one component of velocity, use `U[0]` or `U[1]`.

IBAMR 0.19 writes the velocity only as the vector `U`. Older versions also wrote `U_x` and `U_y`. The expressions above work in both.

## Things to try

- Change `growth_rate` in `update_springs.cpp` (and rebuild). With a slower growth the drag is smaller, so the fiber should stay straight longer.
- Give the fiber bending stiffness: add a `.beam` file, as `generate_mesh2d.m` in IB/03 does, and keep the same base name (IBAMR reads a `.beam` file with the structure's name automatically). The fiber should then lengthen without folding (not tested here).
- Lower the viscosity `MU` to 10. The fluid resists the lengthening less.
- Change the stiffness `kappa_spring` in `generate_mesh2d.m` and write new structure files. Stiffer springs need a smaller `DT`.

## History

This example comes from the UNC course version (`5-Example_2DSprings`, 2018). Its job script asked for 16 cores for 2 hours on a debug queue, and its `README.txt` says only that "the resting lengths of the springs increase over time". The changes for current IBAMR:

- A CMake build replaces the Makefile, and `update_springs.C` became `.cpp`.
- `main.cpp` starts IBAMR with `IBTKInit` and no longer includes the old configuration headers. It is the rubber band's program (IB/01) with the spring update added.
- The course's `update_springs.C` already changed the rest length through a reference (an edit marked "Change 2-14"; it first appears in the 2018 course copy), but it kept the older code as comments, and the lecture slides show that older code: `double resting_length = spring_spec->getParameters()[0][1]; resting_length += 0.01*dt;`. That changes only a local copy, so the springs never grow. The comments in `update_springs.cpp` explain this.
- `update_springs()` now changes every spring of each master point, not only the first one (`getParameters()[0]`). In this fiber every point is the master of at most one spring, so the result is the same.
- The time step is 1.0e-4 s instead of 1.0e-6 s, and the run stops at 0.5 s instead of 2 s. By 0.5 s the rest lengths add up to 0.61 m; by 2 s they would add up to 2 m, twice the width of the periodic box.
- The input file has Unix line endings, so it no longer needs `//` at the end of every line.
- `generate_mesh2d.m` and `generate_mesh2d.py` are new (the course folder had only the structure files). They write exactly the files in this folder.

The original files are in `examples/legacy/`.
