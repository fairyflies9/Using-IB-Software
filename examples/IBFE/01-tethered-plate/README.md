# IBFE/01 Tethered plate

A thin elastic plate, meshed with triangles, is pulled through a periodic box of fluid by target ("tether") forces. One setting in the input file, `MOTION`, chooses how the tether moves. This is the first IBFE example in *Using IB Software*. It shows how IBFE reads a finite element mesh, how stress and force functions are written and registered, and how to look at finite element output in VisIt.

| | |
|---|---|
| Method | Immersed boundary finite element (IBFE) |
| Dimension | 2D |
| Chapters | 17 (getting started with IBFE), 19 (stress and body forces), 28 (finite element data in VisIt) |
| Run time | under a minute on 4 cores (26 s with IBAMR 0.16.0 on a laptop) |
| Tested with | IBAMR 0.16.0 and 0.19.0 (autoibamr; GCC 13.3, Open MPI 4.1.6, Ubuntu 24.04) |
| Upstream relatives | `examples/IBFE/explicit/ex2` (elastic block, same stress model) and `ex1` (thin shell) in IBAMR |

## The three motions

Set `MOTION` near the top of `input2d`:

| `MOTION` | What the tether does |
|---|---|
| `"FULL"` | The whole plate moves up at speed 0.5 until t = 1, then down until t = 3, then is released. |
| `"HALF"` | The same motion, but only the right half of the plate (x > 0 at the start) is tethered, so the plate bends. |
| `"ROTATE"` | The plate turns a quarter turn counterclockwise about its center during 0 < t < 1, then is released. |

In the course versions these were three separate folders (`TetherForceFullPlate2D`, `TetherForceHalfPlate2D` and `TetherForceFullPlate2D-Rotate`) with nearly identical programs.

## Files

| File | What it is |
|---|---|
| `main.cpp` | The IBAMR program, including the tether force and the stress functions |
| `input2d` | Physical, grid, solver and output settings, and the `MOTION` choice |
| `IBFE_Mesh2D_128.mat` | The plate's mesh: 101 nodes and 130 triangles, in libMesh's MATLAB mesh format |
| `CMakeLists.txt` | Build instructions for CMake |
| `job.slurm` | Batch script for Puma |
| `extras/` | A MATLAB script and a Triangle `.poly` file from the course versions. They describe a different rectangle and are not used (see `extras/README.md`). |

## The physics

- **Domain:** 2 by 2, periodic in both directions, with 2 grid levels (32 cells across the coarse level, 128 on the fine level).
- **Fluid:** density 1 and viscosity 0.01.
- **Plate:** 1.0 long and 0.0312 thick, centered at the origin. It is a neo-Hookean solid with shear modulus μ = 10 (`SHEAR_MODULUS`). The first Piola–Kirchhoff stress is split into a deviatoric part, μ**F**, and a dilational part, −μ**F**⁻ᵀ. At **F** = **I** they cancel, so the undeformed plate carries no stress.
- **Tether:** each point of the plate is pulled toward its target position with force κ (target − current position), where κ = 10⁶ (`KAPPA_S`). Setting the target equal to the current position switches the force off, which is how the plate is released.

In the program, `s` is a point's reference (starting) position, with `s(0)` its x-coordinate and `s(1)` its y-coordinate, and `X` is where that point is now.

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

If `MOTION` is misspelled, the run stops at once with

```
Unknown MOTION = "..." in the input file.
Valid options are: FULL, HALF, ROTATE
```

## What you should see

The run takes 4000 time steps and saves 41 frames. Positions measured from `output.ex2` (center = average of the 101 nodes; tips = the nodes that start at x = ±0.5 on the center line):

**FULL**

| Time | Center y | Notes |
|---|---|---|
| 0 | 0.000 | |
| 1.0 | +0.500 | top of the motion |
| 2.0 | 0.000 | |
| 3.0 | −0.500 | released |
| 3.5 | −0.729 | still moving down: the fluid around it keeps moving |
| 4.0 | −0.936 | the ends lag behind the middle, at −0.877 |

**HALF**: the right tip follows the target exactly (y = +0.500 at t = 1, −0.500 at t = 3). The free left half lags, so the plate tilts by about +39° at t = 1 and about −30° from t = 2 on.

**ROTATE**: the plate reaches 90° at t = 1, as prescribed. After it is released, the swirling fluid keeps turning it, to about 140° at t = 2 and about 188° at t = 4. Its center stays at the origin.

IBAMR 0.16.0 and 0.19.0 give the same numbers.

The output folder `viz_IB2d/` holds

- `dumps.visit`: the fluid on the adaptive grid (velocity `U`, pressure `P`, vorticity `Omega`, force `F`, `Div_U`);
- `output.ex2`: the plate, as an ExodusII file with the nodal variables `dX_0`, `dX_1` (displacement), `X_0`, `X_1` (position), `F_0`, `F_1` (force) and `U_0`, `U_1` (velocity).

## Looking at it in VisIt

1. Open `viz_IB2d/dumps.visit`, then choose **Add → Pseudocolor → Omega** and **Draw**.
2. Open `viz_IB2d/output.ex2`, choose **Add → Mesh**, and pick the plate's mesh.
3. The mesh is drawn in its starting position. To move it with the plate, make a vector expression in **Controls → Expressions**: name `dX`, type *Vector*, definition `{dX_0, dX_1}`. Then add **Operators → Transforms → Displace** to the mesh plot and set its variable to `dX`.

Chapter 28 covers finite element output in more detail.

## Things to try

- Make the tether softer, for example `KAPPA_S = 1.0e4`. The plate then trails its target slightly while it is pulled (y = 0.241 instead of 0.250 at t = 0.5) and overshoots when the target turns around (0.507 at t = 1).
- Change `SHEAR_MODULUS` with `MOTION = "HALF"`. At 100 the run is fine and the plate tilts less (about 32° instead of 39° at t = 1). At 1 the free half crumples: its tip moves from x = −0.5 to about −0.15 by t = 1.5, the crumpling plate stirs up fast flow, and the run stops near t = 1.6 with `Time step size change encountered`. Halving `DT` only delays the stop, to about t = 2.05. Chapter 16 explains this error.
- Make your own mesh with gmsh (chapter 18) and set `MESH_FILENAME` to it.

## How the mesh was made

The course used MATLAB's PDE Toolbox. In MATLAB:

```matlab
pdepoly([.5 .5 -.5 -.5], [.0156 -.0156 -.0156 .0156], 'g');
```

This opens the PDE Modeler with the plate's outline. Choose **Mesh → Parameters**, set the maximum edge size to two to four times the fine grid spacing (0.0312 was used here), then **Mesh → Initialize Mesh** and **Mesh → Export Mesh** with the default names `p`, `e` and `t`. Then write the file that libMesh reads:

```matlab
fid = fopen('IBFE_Mesh2D_128.mat', 'w');
fprintf(fid, '%d %d ', length(p), length(t));
fprintf(fid, '%f %f ', p);
fprintf(fid, '%d %d %d %d ', t);
fclose(fid);
```

The order of the four corner points matters. The course README printed the `fopen` line with a curly quote, which MATLAB rejects.

## History

The UNC versions (2014–2018) were developed with Alex Hoover, Julian Wag and Nick Battista. The University of Arizona versions (2022–2024) fixed the `AutoPtr` errors. The changes for current IBAMR:

- A CMake build replaces the Makefile.
- `main.cpp` starts IBAMR with `IBTKInit`, no longer includes the old configuration headers, and uses `libMesh::Order`.
- The three folders became one program with the `MOTION` setting.
- `ROTATE` uses an exact rotation. The course version used x′ = x cos θ, y′ = y + x sin θ, which is exact only on the plate's center line.
- The input files of the half-plate and rotate versions ended with a stray `\\`, which stopped the run with an input parse error. They are fixed.
- Restarted runs now save and reload the plate's finite element data and append to `output.ex2`, as IBAMR's own examples do.
- The input file has Unix line endings, so it no longer needs `//` at the end of every line.

The original files are in `examples/legacy/`.
