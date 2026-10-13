# IB/12 Spider ballooning

A point mass hangs at the lower end of a massless, nearly inextensible dragline in a box of still air, and falls under gravity; the dragline slows it down. The mass is given to the point by the penalty immersed boundary method: a massive copy of the point that moves by Newton's law and is tied to the point by a stiff spring. This example goes with the adding-mass chapter of *Using IB Software* (chapter 13): it is the course's `8-AddingMass-Spider` (2020, "a simplified model of spider ballooning") ported to current IBAMR.

| | |
|---|---|
| Method | Penalty immersed boundary (`PenaltyIBMethod`): springs, beams, one massive point, gravity |
| Dimension | 2D |
| Chapters | 13 (adding mass), 6 (structure files), 8b (dimensionless parameters), 11 (forces), 23 (the lab's spider-ballooning research codes) |
| Run time | about 20 minutes on 3 cores (0.03 s per step on a laptop; 40,000 steps) |
| Tested with | IBAMR 0.16.0 and 0.19.0 (autoibamr; GCC 13.3, Open MPI 4.1.6, Ubuntu 24.04) |
| Upstream relative | `examples/IB/explicit/ex3` in IBAMR (a filament of springs and beams with mass, by the same penalty method) |

## Files

| File | What it is |
|---|---|
| `main.cpp` | The IBAMR program: the program of IB/01 with `PenaltyIBMethod` in place of `IBMethod` (two lines). It also writes the positions and forces every few steps (`output_data`). |
| `input2d` | Physical, grid, solver and output settings, the walls, and the `PenaltyIBMethod` block with `gravitational_acceleration` |
| `spider2d_256.vertex` | 171 points on the line x = 0.15, from y = 0.5 (point 0, the top of the dragline) down to y = 0.4 (point 170, the spider) |
| `spider2d_256.spring` | 170 springs joining neighbors: `i j stiffness rest_length` |
| `spider2d_256.beam` | 169 beams, one for each three neighbors: `i−1 i i+1 stiffness`, very weak |
| `spider2d_256.mass` | the one massive point, `170 2e-05 20`: index, mass, penalty stiffness |
| `generate_mesh2d.m`, `generate_mesh2d.py` | MATLAB/Octave and Python scripts that write the four structure files. They write identical files (checked with Octave 8.4 and Python 3.12). |
| `CMakeLists.txt` | Build instructions for CMake |
| `job.slurm` | Batch script for Puma |

## The physics

- **Domain:** 0.3 m wide by 0.6 m high, periodic across (x) with no-slip walls at the bottom and the top.
- **Fluid:** air, density 1.177 kg/m³ and viscosity 1.846 × 10⁻⁵ N s/m².
- **Grid:** 2 levels of refinement with ratio 2 and 128 × 256 cells on the coarsest level, so the finest grid has 256 cells across and Δx = 0.3/256 ≈ 1.2 mm. Cells are tagged for refinement around the dragline and where the vorticity is large.
- **Dragline:** 0.1 m long, 171 points ds = 0.1/170 ≈ 0.59 mm apart (half a cell), hanging from (0.15, 0.5) to (0.15, 0.4). Springs of stiffness 20 N (the file holds the number as written, since the generator's K ds/ds is K) with rest length ds; beams of bending stiffness 5 × 10⁻¹⁵ N m², "resists bending (a little)". No target points: the top of the line is free, and the whole line falls with the spider.
- **The spider:** the last point, mass 2 × 10⁻⁵ kg per unit depth ("I had to estimate what a 2D spider sheet would weigh", 2020), tied to its massive copy by a penalty spring of stiffness 20 N/m. Gravity is 9.8 m/s² downward, on the copy. Its weight is 1.96 × 10⁻⁴ N per unit depth, which the log's first `integral{F}` line shows as the force on the point.
- **Time:** 40,000 steps of 5 × 10⁻⁵ s (2 s); 40 saved frames. The explicit update of the copy needs Δt < 2 √(m/K) = 2 × 10⁻³ s, so the step is forty times below that limit; it is set by the fluid and the springs.

The copy obeys m Ÿ = −K (Y − X) + m g and the point feels +K (Y − X), which it spreads onto the air (chapter 13). At steady fall the copy hangs m g/K = 10⁻⁵ m below the point. The spider has no body of its own (the 2020 model's "zero body diameter, body drag neglected"), so the drag that sets its terminal speed is the dragline's, plus the drag of the point's own delta-function footprint.

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

Every 1000 steps the screen shows a line like

```
integral{F} = 3.38507e-12 -0.000201235
```

That is the sum of the Lagrangian forces. Springs and beams cancel in the sum (chapter 11); what is left is the penalty force on the spider, which at the start equals its weight, −1.96 × 10⁻⁴ N, and later is the weight minus the air's drag on the whole line.

Measured from the saved positions (`tools/ch13_figures.py` of the tutorial repository; the spider is the last point):

| Time (s) | Spider's height y (m) | Fall (m) | Speed (m/s) | Top of the dragline y (m) |
|---|---|---|---|---|
| 0.10 | 0.3976 | 0.0012 | 0.031 | 0.4984 |
| 0.25 | 0.3901 | 0.0087 | 0.064 | 0.4907 |
| 0.50 | 0.3690 | 0.0298 | 0.099 | 0.4698 |
| 0.75 | 0.3410 | 0.0578 | 0.123 | 0.4417 |
| 1.00 | 0.3082 | 0.0906 | 0.140 | 0.4088 |
| 1.50 | 0.2327 | 0.1661 | 0.161 | 0.3330 |
| 2.00 | 0.1501 | 0.2487 | 0.167 | 0.2497 |

The speed levels off near 0.17 m/s (mean 0.159 m/s over the second second), the terminal speed at which the air's drag on the dragline balances the spider's weight.

What to notice:

- The spider accelerates at first and settles to a terminal speed as the dragline's drag builds up; the dragline trails above it, nearly straight.
- The top of the dragline falls with the spider: nothing holds it. Tether the top point (a one-line `.target` file) and the spider hangs instead, stretching the line by m g/K_spring = 10⁻⁵ m.
- The run is 2 s of the course's 20 s. By 20 s the spider has reached the floor; the lecture's point was the settling speed, which the first second shows.

The output folders:

- `viz_IB2d/dumps.visit` holds the fluid data on the adaptive grid: velocity `U`, pressure `P`, vorticity `Omega` and `Div_U` (41 frames).
- `viz_IB2d/lag_data.visit` holds the dragline as the mesh `spider2d_256_mesh`.
- `hier_data_IB2d/X.NNNNN` and `F.NNNNN` are the points' positions and forces as plain-text PETSc vectors, with x and y alternating. Chapter 11 reads them in MATLAB and Python.
- `IB2d.log` is the log file.

## Looking at it in VisIt

1. Open `viz_IB2d/dumps.visit`, then choose **Add → Pseudocolor → Omega** and **Draw**: the falling line sheds a pair of vortices of opposite sign that trail behind the spider.
2. Open `viz_IB2d/lag_data.visit` as a second database, then **Add → Mesh → spider2d_256_mesh** and **Draw**; step through the frames to watch the fall.

IBAMR 0.19 writes the velocity only as the vector `U`. Older versions also wrote `U_x` and `U_y`.

## Things to try

- Change `mass` in the generator (and rewrite the structure files): twice the mass falls faster; find how the terminal speed scales.
- Change `drag_length`: a longer line has more drag.
- Raise the penalty stiffness `kappa_mass` to 200 (the copy follows more closely; the step limit falls to 6 × 10⁻⁴ s) and lower it to 2 (the copy lags by 10⁻⁴ m).
- Tether the top point with a `.target` file (one line: `0 20`) and watch the line hang.
- Put the spider in a cross-wind: give the walls a horizontal velocity that ramps up, as IB/03's boundary conditions do (chapter 7); the 2020 study's uniform-flow and shear-flow cases.
- Run the course's 20 s (`END_TIME = 20.0`): the spider reaches the floor.

## History

This example is the course's `8-AddingMass-Spider` (2020; the folder in the course files was misspelt), which ran under the 2018 UNC IBAMR module with a Makefile. The changes for current IBAMR and for the tutorial:

- A CMake build replaces the Makefile; `main.C` became `main.cpp`, starts IBAMR with `IBTKInit` and no longer includes the old configuration headers. It is IB/01's program with `PenaltyIBMethod` in place of `IBMethod`.
- The course program also carried a temperature field: an advection-diffusion integrator with a Boussinesq body force (`BoussinesqForcing.cpp`, `KAPPA`, `GAMMA`, the `Temperature*` and `AdvDiff*` input blocks). The lecture never mentioned it and the spider does not use it; it is left out, and the input file's blocks with it. Chapter 19 has thermal forcing where it belongs.
- The generator's beam loop wrote one beam too many, naming a point past the end of the line, under a header that did not count it; the loop now stops at the last valid triple. The mass point is the last point of the dragline (the course file put it on the one before).
- The input file has Unix line endings and no trailing `//` on every line; `DT` is a plain number; the Silo writer is enabled so that the dragline appears in VisIt; the run is 2 s instead of 20.
- `generate_mesh2d.py` is new; `generate_mesh2d.m` is the course's with the two fixes. Both write identical files.
- `output_data` writes the positions and forces every 1000 steps; the course program did not.

The original files are in `examples/legacy/`.
