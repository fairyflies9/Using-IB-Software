# IBFE/12 Advection and diffusion

The half-tethered plate of example IBFE/01 stirs a passive scalar T, for example a temperature or a concentration. The fluid carries T along, and T also spreads out slowly. This example shows how to add an advection–diffusion solver to an IBFE program, and how to choose initial and boundary conditions for T that agree with each other.

| | |
|---|---|
| Method | Immersed boundary finite element (IBFE) with an advected and diffused scalar |
| Dimension | 2D |
| Chapters | 24 (IBFE with advection–diffusion), 7 (boundary conditions), 28 (finite element data in VisIt) |
| Run time | about a minute and a half on 4 cores (69 s with IBAMR 0.16.0 and 91 s with 0.19.0 on a desktop PC under WSL) |
| Tested with | IBAMR 0.16.0 and 0.19.0 (autoibamr; GCC 13.3, Open MPI 4.1.6, Ubuntu 24.04) |
| Upstream relatives | `examples/IB/explicit/ex7` (an IB structure with a dye concentration, set up the same way) and the stand-alone solvers in `examples/adv_diff/` in IBAMR |

## Files

| File | What it is |
|---|---|
| `main.cpp` | The IBAMR program: the plate's tether and stress functions, and the set-up of T |
| `input2d` | Physical, grid, solver and output settings, and the initial and boundary conditions for T |
| `IBFE_Mesh2D_128.mat` | The plate's mesh: 101 nodes and 130 triangles (the same mesh as IBFE/01, which explains how it was made) |
| `CMakeLists.txt` | Build instructions for CMake |
| `job.slurm` | Batch script for Puma |

The course folder also had `Beam_IBFE_Mesh2D.m` and `IBFE_Mesh2D_128.poly`. They are identical to the files in IBFE/01's `extras/` and are not used, so they are not repeated here.

## The physics

- **Domain:** 2 by 2, periodic in both directions, with 2 grid levels (32 cells across the coarse level, 128 on the fine level).
- **Fluid:** density 1 and viscosity 0.01.
- **Plate and tether:** exactly IBFE/01 with `MOTION = "HALF"`. The plate is 1.0 by 0.0312, neo-Hookean with μ = 10, and only its right half (x > 0 at the start) is tethered. The target moves up at speed 0.5 until t = 1, down until t = 3, and is then released.
- **T:** it obeys

  ∂T/∂t + **u** · ∇T = κ ΔT,  κ = 10⁻⁶ (`KAPPA`).

  T does not act back on the fluid or the plate. With κ this small, T is carried almost without spreading: in 4 time units diffusion alone would spread it over about √(κt) = 0.002, less than one fine grid cell (0.0156).

## Initial and boundary conditions for T

In a periodic box the right side (x = 1) touches the left side (x = −1). The initial T must therefore take the same value on both sides, or the box starts with a jump in T where it wraps around.

The course version used T = 0.5 + x. It goes from 0 at the plate's left end to 1 at its right end, but it is −0.5 at x = −1 and 1.5 at x = 1: a jump of 2 at the edge of the box. This version uses

  T = 0.5 + 0.5 sin(2πx/L),

which is periodic and agrees with the course formula at x = −0.5, 0 and 0.5 (T = 0, 0.5 and 1). The course formula and two other course choices are kept as comments in `input2d`. (The two `tanh` profiles there jump where the box wraps around in y.)

The block `TemperatureBcCoefs` gives *a* T + *b* ∂T/∂n = *g* on each side, like the velocity conditions. IBAMR uses it only on sides that are not periodic. Here *a* = 1, *b* = 0 and *g* is the initial T, so if you turn periodicity off (see "Things to try"), T is held at its initial values on the walls, and the initial and boundary conditions agree there too.

## Choosing the solver for T

Set `ADV_DIFF_SOLVER_TYPE` near the top of `input2d` to `"SEMI_IMPLICIT"` (the default) or `"PREDICTOR_CORRECTOR"`. The program prints its choice at the start of the run:

```
Advection-diffusion solver: SEMI_IMPLICIT
```

`PREDICTOR_CORRECTOR` needs one more line. The fluid solver uses Adams–Bashforth time stepping, which takes two cycles in its first step, but the predictor–corrector solver can take only one. Without the extra line the run stops at the first step with

```
INSStaggeredHierarchyIntegrator::preprocessIntegrateHierarchy():
  attempting to perform 2 cycles of fixed point iteration.
  number of cycles required by coupled advection-diffusion solver = 1.
  current implementation requires either that both solvers use the same number of cycles,
  or that the Navier-Stokes solver use only a single cycle.
```

To fix it, remove the `//` in front of `init_convective_time_stepping_type = "FORWARD_EULER"` in the `INSStaggeredHierarchyIntegrator` block. The first fluid step then uses forward Euler for the convective term.

The course version read the solver type from `adv_diff_solver_type` in the `Main` block and used `PREDICTOR_CORRECTOR` when that line was missing. The lecture slides did not show the line, so an input copied from the slides stops with the message above (tested with the course program and IBAMR 0.19.0).

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

The run takes 4000 time steps and saves 41 frames. The plate moves exactly as in IBFE/01 with `MOTION = "HALF"` (the node positions agree to 2 × 10⁻⁸): it tilts by about 39° at t = 1 and is released at t = 3.

T, measured from the VisIt files over the whole box (each place counted once, on the finest grid that covers it):

| Time | Smallest T | Largest T | Average T |
|---|---|---|---|
| 0 | 0.0002 | 0.9998 | 0.50000 |
| 1 | −0.0031 | 1.0003 | 0.49995 |
| 2 | −0.0012 | 1.0000 | 0.50001 |
| 3 | −0.0001 | 1.0022 | 0.49999 |
| 4 | −0.0006 | 1.0053 | 0.49992 |

T should stay between 0 and 1 and its average should stay 0.5. The small over- and undershoots (largest over all frames: 1.008 and −0.0031) come from the advection scheme. IBAMR 0.16.0 and 0.19.0 give the same numbers.

With `ADV_DIFF_SOLVER_TYPE = "PREDICTOR_CORRECTOR"` (and the extra line above), T never rises above its starting maximum (0.9998) and never falls below −0.0003, and its average stays between 0.4999 and 0.5003. This solver limits its slopes (`limiter_type = "MC_LIMITED"`), so it does not overshoot, but it smooths the extremes a little: the largest T falls to 0.9965 by t = 4.

**With the course's initial T = 0.5 + x** (run with the course program), the jump at the edge of the box is carried into the fluid. In the coarse-grid cell next to the right side of the box at mid-height (x = 0.97, y = 0.03), T starts at 1.47 and falls to −0.16 by t = 4: fluid that leaves the box through the left side, where T is about −0.5, comes back in through the right side. The average of T, which should stay 0.5, falls to 0.495.

The output folder `viz_IB2d/` holds

- `dumps.visit`: the fluid and T on the adaptive grid (`U`, `P`, `Omega`, `F`, `Div U` and `T`);
- `output.ex2`: the plate (`dX_0`, `dX_1`, `X_0`, `X_1`, `F_0`, `F_1`, `U_0`, `U_1`).

It is 17 MB with IBAMR 0.19.0 and 23 MB with 0.16.0, which also writes `U_x`, `U_y`, `F_x` and `F_y`.

## Looking at it in VisIt

1. Open `viz_IB2d/dumps.visit`, then choose **Add → Pseudocolor → T** and **Draw**. Watch the plate fold the field as it moves up and down.
2. Open `viz_IB2d/output.ex2`, choose **Add → Mesh**, and pick the plate's mesh.
3. To move the mesh with the plate, make a vector expression in **Controls → Expressions**: name `dX`, type *Vector*, definition `{dX_0, dX_1}`. Then add **Operators → Transforms → Displace** to the mesh plot and set its variable to `dX`.

Chapter 28 covers finite element output in more detail.

## Things to try

- Switch to `ADV_DIFF_SOLVER_TYPE = "PREDICTOR_CORRECTOR"`, with the extra line described above.
- Put walls around the box: set `periodic_dimension = 0,0` in `CartesianGeometry`. The fluid then sticks to the walls (`VelocityBcCoefs_0` and `_1`), and T is held at its initial values there (`TemperatureBcCoefs`). The run works, the plate moves differently (by up to 0.15 at t = 4), and T stays between −0.033 and 1.015.
- Make T diffuse faster: `KAPPA = 1.0e-3`. Diffusion then spreads T over about √(κt) = 0.06 by t = 4, four fine grid cells. The extremes wear down (T stays between 0.017 and 0.979 at t = 4), there are no overshoots, and the average stays within 0.0001 of 0.5.
- Try the course's `function = "0.5+X_0"` and look at T near x = ±1 in VisIt (the numbers above come from the course program with this initial T).

## History

The UNC version (2016–2020) added an advected and diffused quantity to the half-tethered plate. The changes for current IBAMR:

- A CMake build replaces the Makefile.
- `main.cpp` starts IBAMR with `IBTKInit`, no longer includes the old configuration headers, and uses `libMesh::Order`, `nullptr` and `IBTK::rel_equal_eps`.
- The solver type is read from `ADV_DIFF_SOLVER_TYPE` at the top of `input2d` and printed, and the extra line that `PREDICTOR_CORRECTOR` needs is in `input2d`.
- The initial T is periodic, and the boundary conditions for T (used only without periodicity) agree with it.
- The boundary condition object for T is deleted at the end of the run.
- The mesh file, tether stiffness and shear modulus can be set in `input2d`.
- Restarted runs now save and reload the plate's finite element data and append to `output.ex2`, as IBAMR's own examples do. Unlike those examples, only processor 0 reopens `output.ex2`: when every process reopens it, a restart on more than one process leaves a file that can no longer be read (tested with IBAMR 0.16.0 and 0.19.0).
- The input file has Unix line endings. The keys `use_IB_spread_operator` and `use_IB_interp_operator`, which IBAMR no longer reads, are removed.

The original files are in `examples/legacy/`.
