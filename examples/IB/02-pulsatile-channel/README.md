# IB/02 Pulsatile channel

Fluid pulses through a straight channel whose walls are rows of Lagrangian points held in place by target-point forces. The inflow and outflow velocities are set with time-dependent boundary conditions written as muParser expressions. This example goes with the boundary-conditions chapter of *Using IB Software*.

| | |
|---|---|
| Method | Immersed boundary (IB): target points, plus springs and beams that do nothing |
| Dimension | 2D |
| Chapters | 7 (boundary conditions), 6 (structure files), 3 (input-file errors) |
| Run time | about 5 to 6 minutes on 4 cores (318 s with IBAMR 0.16.0 on a laptop) |
| Tested with | IBAMR 0.16.0 and 0.19.0 (autoibamr; GCC 13.3, Open MPI 4.1.6, Ubuntu 24.04) |
| Upstream relative | `examples/IB/explicit/ex2` in IBAMR (flow past a cylinder held by target points, with an inflow condition) |

## Files

| File | What it is |
|---|---|
| `main.cpp` | The IBAMR program; the same program as the rubber band (IB/01) |
| `input2d` | Physical, grid, solver and output settings, and the boundary conditions |
| `channel.vertex` | 2048 points: two rows of 1024, at y = +0.5 and y = −0.5 |
| `channel.target` | every point is a target point, stiffness 2.048 × 10⁶ |
| `channel.spring`, `channel.beam` | springs and beams along each wall with stiffness 10⁻¹⁰ |
| `Channel_Flow.m` | MATLAB script by Nick Battista (2013) that writes the four structure files |
| `CMakeLists.txt` | Build instructions for CMake |
| `job.slurm` | Batch script for Puma |

## The physics

- **Domain:** 5 by 5, not periodic, with 3 grid levels (32 cells across the coarse level, 512 on the finest).
- **Fluid:** density 1000 and viscosity 100.
- **Channel:** width d = 1, walls at y = ±0.5 running the full length of the box.
- **Walls:** target points with stiffness κ = 10⁴ per unit length, written to the file as κ/ds = 2.048 × 10⁶. They hold the walls still against the flow.
- **Springs and beams:** stiffness 10⁻¹⁰, so they have no effect. They are there to show the `.spring` and `.beam` file formats, including the beam file's optional curvature columns.
- **Boundary conditions:** on the left and right ends of the box (sides 0 and 1) the x-velocity is a parabola across the channel,

  u(y, t) = (4/d²) (0.5 + 0.5 sin 2πft) (d²/4 − y²) for |y| < d/2, and 0 outside,

  so the peak speed at the center pulses between 0 and 1 at f = 5 Hz. All other velocity components and sides are 0.

## The boundary-condition expression

muParser, the expression parser IBAMR uses, has no `if()` function. The course version used one:

```
gcoef_function_0 = "if( X_1 <= -0.5*d,0.0,if( X_1 >= 0.5*d,0.0,4.0/(d*d)*(0.5 + 0.5*sin(2*PI*f*t))*( (0.25*d*d) - X_1*X_1 ) ) )"
```

With IBAMR 0.19.0 that stops the run at the first time step:

```
muParserRobinBcCoefs::setDataOnPatch():
  error: Unexpected token "if" found at position 0.
```

This version uses the conditional operator `condition ? a : b`:

```
gcoef_function_0 = "(X_1 <= -0.5*d) ? 0.0 : ((X_1 >= 0.5*d) ? 0.0 : 4.0/(d*d)*(0.5 + 0.5*sin(2*PI*f*t))*((0.25*d*d) - X_1*X_1))"
```

`X_0` and `X_1` are the coordinates and `t` is time. The constants `PI`, `f` and `d` are defined at the top of the `VelocityBcCoefs_0` block.

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

The run takes 20,000 time steps and saves 51 frames of VisIt output (49 MB) and 50 pairs of position and force files.

Every 400 steps the program prints `integral{F}`, the sum of the target forces holding the walls in place:

```
integral{F} = -15545 -0.134877
integral{F} = -2599.14 -0.314447
integral{F} = -1814.96 -0.303586
...
integral{F} = -22835.6 -0.388076
```

The x-component balances the drag of the flow on the walls, so it is negative and pulses with the inflow. The samples are 0.04 s apart, five per 0.2 s cycle. The force grows from cycle to cycle because the flow in the channel is still developing: with this viscosity and density, momentum takes about ρd²/μ = 10 s to diffuse across the channel. IBAMR 0.16.0 and 0.19.0 print the same numbers.

The output folders are the same as for the rubber band: `viz_IB2d/dumps.visit` for the fluid, `viz_IB2d/lag_data.visit` for the walls, and `hier_data_IB2d/` for the position and force files.

## Looking at it in VisIt

1. Open `viz_IB2d/dumps.visit`, then choose **Add → Pseudocolor**, use the expression `U[0]` for the x-velocity, and **Draw**. Step through time to watch the profile pulse.
2. Open `viz_IB2d/lag_data.visit` and choose **Add → Mesh** to draw the walls.
3. A **Lineout** across the channel shows the velocity profile against the parabola (chapter 29).

IBAMR 0.19 writes the velocity only as the vector `U`, so use `U[0]` instead of the older `U_x`.

## Things to try

- Change the pulsing frequency `f` in the `VelocityBcCoefs_0` block.
- Make the flow steady by replacing `(0.5 + 0.5*sin(2*PI*f*t))` with `1.0`, then run long enough for the profile to settle.
- Run longer, with a larger `END_TIME`, and watch the force settle into a repeating cycle.

## History

The geometry script is by Nick Battista (2013). The example was part of the UNC course (2018) and the University of Arizona course (2022–2024). The changes for current IBAMR:

- A CMake build replaces the Makefile, and `main.cpp` is the modernized program shared with IB/01.
- The `if()` boundary expressions are rewritten with `? :`.
- The output intervals scale with the run: the course version wrote a VisIt frame every 10,000 steps, only 3 frames in all.
- The unused constant `V = 0.1` is removed, and comments explain the boundary conditions and the near-zero springs and beams.
- The input file has Unix line endings, so it no longer needs `//` at the end of every line.

The original files are in `examples/legacy/`.
