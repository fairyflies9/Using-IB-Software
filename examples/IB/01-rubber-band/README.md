# IB/01 Rubber band

An elastic band made of 644 Lagrangian points joined by springs starts as an ellipse in a periodic box of fluid and relaxes into a circle. This is the first IBAMR example in *Using IB Software*. It shows the structure files, the input file, the CMake build, running with MPI, and looking at the results in VisIt.

| | |
|---|---|
| Method | Immersed boundary (IB), springs only |
| Dimension | 2D |
| Chapters | 3 (building and running), 6 (structure files), 26 (VisIt) |
| Run time | about 3 minutes on 4 cores for the full 2 s (166 s with IBAMR 0.16.0 and 181 s with 0.19.0 on a laptop) |
| Tested with | IBAMR 0.16.0 and 0.19.0 (autoibamr; GCC 13.3, Open MPI 4.1.6, Ubuntu 24.04) |
| Upstream relative | `examples/IB/explicit/ex1` in IBAMR, which this program is adapted from |

## Files

| File | What it is |
|---|---|
| `main.cpp` | The IBAMR program. It also writes the band's positions and forces every few steps (`output_data`). |
| `input2d` | Physical, grid, solver and output settings |
| `rubber_band_512.vertex` | 644 points: the first line is the count, then one `x y` pair per line |
| `rubber_band_512.spring` | 644 springs: the count, then `i j stiffness rest_length`, with indices starting at 0 |
| `generate_mesh2d.m` | MATLAB or Octave script that writes the two structure files |
| `generate_mesh2d.py` | Python version of the same script (standard library only): `python3 generate_mesh2d.py`. Its `.spring` file is identical to the one in this folder; in its `.vertex` file a few dozen of the 1288 coordinates differ in the last digit, by about 10⁻¹⁷. Sine and cosine round slightly differently in different math libraries, so which coordinates differ depends on the computer. That is the size of ordinary round-off error. |
| `CMakeLists.txt` | Build instructions for CMake |
| `job.slurm` | Batch script for Puma |
| `job_array.slurm`, `params.txt` | A three-run viscosity sweep as a Slurm job array |

## The physics

- **Domain:** 1 m by 1 m, periodic in both directions.
- **Fluid:** density 1000 kg/m³ and viscosity 100 N s/m², so the flow is very slow and viscous.
- **Grid:** 4 levels of adaptive refinement with ratio 4 and 8 cells on the coarsest level, so the finest grid has 512 cells across and Δx = 1/512 m.
- **Band:** an ellipse with semi-axes 0.12 m in x and 0.10 m in y. The point spacing is about Δx/2.
- **Springs:** each spring's rest length is the spacing of points on a circle of radius 0.1 m, so every spring starts stretched. The third column of the `.spring` file is K/ds, where K = 2000 is the band's stiffness set in `generate_mesh2d.m` and ds is the point spacing.

The band pulls inward, but the fluid inside cannot escape, so the enclosed area stays the same. The band ends as a circle of radius √(0.12 × 0.10) ≈ 0.1095 m, still slightly stretched, with the pressure inside balancing the tension.

## Build and run

On Puma, work inside an interactive session or a batch job, because the modules load only on compute nodes. On a laptop with autoibamr, skip the `module` line.

```bash
module load gnu13 openmpi5
source ~/autoibamr/configuration/enable.sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j 4
mpirun -np 4 ./build/main2d input2d
```

On Puma, submit the batch script instead of running `mpirun` yourself:

```bash
sbatch job.slurm
```

The input file must have Unix line endings. If you edited it on Windows and see `Illegal character token in input`, convert it with `dos2unix input2d`.

## What you should see

The run takes 20,000 time steps. Every 400 steps the screen shows a line like

```
integral{F} = 2.27374e-13 0
```

That is the sum of all the spring forces on the band. Each spring pulls its two ends with equal and opposite forces, so the sum stays at round-off level.

The band's width and height, measured from the saved positions:

| Time (s) | Width (m) | Height (m) | Width / height |
|---|---|---|---|
| 0 | 0.2400 | 0.2000 | 1.200 |
| 0.12 | 0.2285 | 0.2100 | 1.088 |
| 0.4 | 0.2187 | 0.2195 | 0.996 |
| 1.0 | 0.2191 | 0.2191 | 1.000 |
| 2.0 | 0.2191 | 0.2191 | 1.000 |

The ratio dips slightly below 1 around t = 0.4 s before settling, so the relaxation slightly overshoots.

The output folders:

- `viz_IB2d/dumps.visit` holds the fluid data on the adaptive grid: velocity `U`, pressure `P`, vorticity `Omega` and `Div_U`.
- `viz_IB2d/lag_data.visit` holds the band itself.
- `hier_data_IB2d/X.NNNNN` and `F.NNNNN` are the band's positions and forces as plain-text PETSc vectors, with x and y alternating. Chapter 11 reads them in MATLAB.
- `IB2d.log` is the log file.

## Looking at it in VisIt

1. Open `viz_IB2d/dumps.visit`, then choose **Add → Pseudocolor → Omega** and **Draw**.
2. Open `viz_IB2d/lag_data.visit` as a second database, then choose **Add → Mesh → rubber_band_512_mesh** and **Draw**.
3. For speed, use the expression `magnitude(U)`. For one component of velocity, use `U[0]` or `U[1]`.

IBAMR 0.19 writes the velocity only as the vector `U`. Older versions also wrote `U_x` and `U_y`. The expressions above work in both.

## Things to try

- Lower the viscosity `MU` to 10 or 1. The band then overshoots and swings between wide and tall, about once every 0.3 s, before it settles. With `MU = 1` the swinging lasts longest.
- Change `epsilon` in `generate_mesh2d.m` to start from a more or less stretched ellipse.
- Make the band stiffer or softer by changing `kappa_spring`.
- Raise `DT` to 1.0e-3 to see the error `Time step size change encountered`, which chapter 16 explains.

## Running a parameter sweep on Puma

`job_array.slurm` runs one simulation per line of `params.txt` as a Slurm job array. Each line holds a viscosity `MU` (100, 10 and 1). Build the example first, then submit from this folder:

```bash
sbatch job_array.slurm
```

Task *i* reads line *i* of `params.txt`, makes the folder `run_i`, copies the structure files there, writes `run_i/input2d` with that line's `MU`, and runs. Chapter 3 explains how it works. To sweep another parameter, change the `awk` line that replaces `MU`.

## History

This example comes from the University of Arizona course version (`3-IBAMR-Example_2Drubber_band`, 2022), which descends from the UNC course version (2014–2020). The UNC copy was missing the spring that closes the band, so it had 643 springs instead of 644. The changes for current IBAMR:

- A CMake build replaces the Makefile, which needed a Makefile build of IBAMR that autoibamr does not make.
- `main.cpp` starts IBAMR with `IBTKInit` and no longer includes the old configuration headers.
- The time step is 1.0e-4 s instead of 1.0e-6 s. The band's shape is the same to 4 digits, and the full run takes minutes instead of hours.
- The input file has Unix line endings, so it no longer needs `//` at the end of every line.

The original files are in `examples/legacy/`.
