# IB/03 Tethered beam

A flexible beam, the "leaf", stands upright in a box of fluid, held at its middle by two target points. The boundary conditions make the fluid flow past it, starting from rest and speeding up smoothly to 0.1 m/s, and the leaf bends downstream. This example goes with the boundary-conditions chapter of *Using IB Software*.

| | |
|---|---|
| Method | Immersed boundary (IB): springs, beams and two target points |
| Dimension | 2D |
| Chapters | 7 (boundary conditions), 6 (structure files), 10 (beams) |
| Run time | about 7 minutes on 4 cores (0.02 s per step on a desktop PC under WSL; 20,000 steps) |
| Tested with | IBAMR 0.16.0 and 0.19.0 (autoibamr; GCC 13.3, Open MPI 4.1.6, Ubuntu 24.04) |
| Upstream relative | `examples/IB/explicit/ex3` in IBAMR (a filament made of springs and beams); the program is adapted from `examples/IB/explicit/ex1` |

## Files

| File | What it is |
|---|---|
| `main.cpp` | The IBAMR program, the same one as for IB/01 and IB/02. It also writes the leaf's positions and forces every few steps (`output_data`). |
| `input2d` | Physical, grid, solver and output settings, and the boundary conditions |
| `leaf_512.vertex` | 103 points on the line x = 0, from y = 0.05 (point 0) down to y = −0.05 (point 102) |
| `leaf_512.spring` | 102 springs joining neighbors: `i j stiffness rest_length` |
| `leaf_512.beam` | 101 beams, one for each three neighbors: `i−1 i i+1 stiffness` |
| `leaf_512.target` | the two target points, 50 and 51: `index stiffness` |
| `generate_mesh2d.m`, `generate_mesh2d.py` | MATLAB/Octave and Python scripts that write the four structure files. They write identical files (checked with Octave 8.4 and Python 3.12). |
| `CMakeLists.txt` | Build instructions for CMake |
| `job.slurm` | Batch script for Puma |

## The physics

- **Domain:** 1 m by 1 m, not periodic.
- **Fluid:** density 1000 kg/m³ and viscosity 4 N s/m². With the leaf's length ℓ = 0.1 m and the flow speed V = 0.1 m/s, the Reynolds number is ρVℓ/μ = 2.5.
- **Grid:** 3 levels of adaptive refinement with ratio 4 and 32 cells on the coarsest level, so the finest grid has 512 cells across and Δx = 1/512 m ≈ 2 mm.
- **Leaf:** 0.1 m long, with 103 points ds = 0.1/102 m ≈ Δx/2 apart.
- **Springs:** stiffness K = 30 (tension per unit strain); the `.spring` file holds K/ds = 3.06 × 10⁴. Their rest length is ds, so they start unstretched.
- **Beams:** bending stiffness 5 × 10⁻³; the `.beam` file holds it divided by ds³, 5.31 × 10⁶. The leaf is straight, so the beams have no preferred curvature.
- **Target points:** points 50 and 51, at y = ds and y = 0, are pulled toward where they started with the force κ (X_target − X), κ = 30/ds = 3.06 × 10⁴.
- **Boundary conditions:** on all four sides the x-velocity is V tanh(2t) and the y-velocity is 0. The fluid flows in on the left and out on the right, and the top and bottom of the box slide along with the flow. tanh(2t) reaches 0.96 at t = 1 s.

The two target points hold the middle of the leaf in place but do not stop it from turning, so the leaf can tilt as well as bend. The flow pushes both halves downstream; the beams resist the bending and the springs keep the leaf from stretching.

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

## What you should see

The run takes 20,000 time steps of 10⁻⁴ s and saves 50 frames. Every 400 steps the screen shows a line like

```
integral{F} = -4.6921 -0.0505867
```

That is the sum of all the forces on the leaf's points. The spring and beam forces cancel in pairs, so what is left is the force of the two target points, which is minus the force of the flow on the leaf: the first number is minus the drag.

Measured from the saved positions (the tips are points 0 and 102, which start at y = ±0.05):

| Time (s) | Top tip moved downstream (m) | Bottom tip moved downstream (m) | Drag (N) |
|---|---|---|---|
| 0.04 | 0.0002 | 0.0002 | 1.20 |
| 0.24 | 0.0064 | 0.0065 | 4.55 |
| 0.44 | 0.0124 | 0.0130 | 6.54 |
| 0.64 | 0.0144 | 0.0156 | 6.67 |
| 0.84 | 0.0137 | 0.0158 | 6.29 |
| 1.04 | 0.0117 | 0.0146 | 5.60 |
| 1.44 | 0.0099 | 0.0124 | 4.85 |
| 2.0 | 0.0090 | 0.0122 | 4.67 |

The leaf bends most at about t = 0.7 s, while the flow is still speeding up, and then straightens a little as the flow around it settles. The tips end up about 1 cm downstream, with the bottom half bent a little more than the top half, and the middle segment tilted by 1.6°. The middle stays within 10⁻⁴ m of its starting point: the target points hold it with a stiff spring, so they lag by the drag divided by κ. A test run with `DT = 2.0e-4` continued to t = 5 s: by then the drag has settled at 4.15 N and the tips at 0.007 m (top) and 0.012 m (bottom), changing by less than 1% per second. The course version ran to 20 s.

The time step: runs with `DT` from 2.0e-5 to 2.0e-4 agree closely (the tip positions at t = 0.4 s to 4 digits), and `DT = 5.0e-4` or larger stops after a few steps with `Time step size change encountered` (chapter 16). The course's `DT = 1.0e-5` gives tip positions and drag that differ from these by under 1%, a difference that appears between t = 0.02 and 0.03 s and whose cause was not found. IBAMR 0.16.0 and 0.19.0 give byte-identical positions and forces (checked at t = 0.04 s).

The output folders:

- `viz_IB2d/dumps.visit` holds the fluid data on the adaptive grid: velocity `U`, pressure `P`, vorticity `Omega` and `Div U` (51 frames, 11 MB).
- `viz_IB2d/lag_data.visit` holds the leaf itself.
- `hier_data_IB2d/X.NNNNN` and `F.NNNNN` are the leaf's positions and forces as plain-text PETSc vectors, with x and y alternating. Chapter 11 reads them in MATLAB.
- `IB2d.log` is the log file.

## Looking at it in VisIt

1. Open `viz_IB2d/dumps.visit`, then choose **Add → Pseudocolor → Omega** and **Draw**. The vorticity shows the two shear layers that leave the tips of the leaf.
2. Open `viz_IB2d/lag_data.visit` as a second database, then choose **Add → Mesh → leaf_512_mesh** and **Draw**. Step through the frames to watch the leaf bend.
3. For speed, use the expression `magnitude(U)`. For one component of velocity, use `U[0]` or `U[1]`. A **Vector** plot of `U` shows the flow going around the leaf.

IBAMR 0.19 writes the velocity only as the vector `U`. Older versions also wrote `U_x` and `U_y`. The expressions above work in both.

## Things to try

- Change the boundary conditions. Make the top and bottom walls stick (`gcoef_function_2` and `gcoef_function_3` of `VelocityBcCoefs_0` to `"0.0"`), or make the flow come in from the top instead. Chapter 7 explains the `acoef`, `bcoef` and `gcoef` functions.
- Make the leaf more or less flexible with `kappa_beam` in `generate_mesh2d.m`, and write new structure files. Without the beams (delete the `.beam` file) the leaf has no bending stiffness and folds over.
- Hold the leaf by its bottom end instead of its middle: change the two target points in `generate_mesh2d.m` to points 101 and 102.
- Raise the flow speed `V` or lower the viscosity `MU` for a higher Reynolds number. A faster flow may need a smaller `DT`.

## History

This example comes from the UNC course version (`4-Example_2DTetheredBeam`, 2014–2020; 16 cores for 2 hours on a debug queue) and the University of Arizona version (2020–2024; 1 core for 4 hours). The changes for current IBAMR:

- A CMake build replaces the Makefile.
- `main.cpp` starts IBAMR with `IBTKInit` and no longer includes the old configuration headers. It is the rubber band's program (IB/01).
- The course version called `update_target_point_positions()` before every time step, but that function moved the target points by V Δt with V = 0, so it did nothing. The call and the function are removed; IB/04 and IB/07 show how to move target points.
- The time step is 1.0e-4 s instead of 1.0e-5 s, and the run stops at 2 s instead of 20 s (20 s would be 200,000 steps).
- The flow speed is the input variable `V`. The course version wrote 0.1 into each boundary condition.
- The input file has Unix line endings, so it no longer needs `//` at the end of every line.
- `generate_mesh2d.m` has explanatory comments and says what each stiffness divides by; `generate_mesh2d.py` is new. Both write exactly the course's structure files.

The original files are in `examples/legacy/`.
