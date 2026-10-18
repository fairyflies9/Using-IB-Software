# IB/10 Jellyfish bell

A two-dimensional jellyfish bell, a single curve of springs and beams with no tethers, swims upward by changing its preferred curvature: before every time step the program sets each beam's resting curvature to the bell shape for a control parameter β(t) that falls (contraction) and rises (expansion) once per period. This example goes with the resting-curvature chapter of *Using IB Software* (chapter 10): it is the course's `Example_jellyfish_curvature` (2013, "specific example of jellyfish swimming by prescribing curvature") rebuilt from the lecture's description of the bell and its `update_beams.C` fragments.

| | |
|---|---|
| Method | Immersed boundary (IB): springs, beams with a time-dependent preferred curvature; a free (untethered) body |
| Dimension | 2D |
| Chapters | 10 (resting curvature and beams), 9a (update functions), 6 (structure files), 8b (dimensionless parameters), 11 (forces) |
| Run time | about 15 minutes on 2 cores (the commands below use 4; 0.02 s per step on a desktop PC under WSL; 40,000 steps) |
| Tested with | IBAMR 0.16.0 and 0.19.0 (autoibamr; GCC 13.3, Open MPI 4.1.6, Ubuntu 24.04) |
| Upstream relative | `examples/IB/explicit/ex3` in IBAMR (a filament of springs and beams); the bell is that of Herschlag and Miller, *J. Theor. Biol.* 285 (2011) 84–95 |

## Files

| File | What it is |
|---|---|
| `main.cpp` | The IBAMR program: the program of IB/09 with the pulse (`PERIOD`, `T_CONTRACT`) and the bell parameters (`BETA_0`, `BETA_M`) read from the input file and passed to `update_beams()` before each time step. It also writes the positions and forces every few steps (`output_data`). |
| `update_beams.cpp`, `.h` | The function that computes the bell shape for the current β and sets every beam's preferred curvature to its second difference |
| `bell_geometry.h` | The bell's numbers (domain, grid, arc length, apex height) and the shape function, shared by the update function; keep them equal to the generator's |
| `input2d` | Physical, grid, solver and output settings, the walls, and the four pulse and bell keys |
| `bell_256.vertex` | 257 points from the left tip through the apex (point 128) to the right tip, on the resting bell (β = 0.5) |
| `bell_256.spring` | 256 springs joining neighbors, rest length the resting distance |
| `bell_256.beam` | 255 beams, one for each interior point, with six columns: `i−1 i i+1 stiffness C1 C2`, the preferred curvature being the resting bell's own second differences |
| `generate_mesh2d.m`, `generate_mesh2d.py` | MATLAB/Octave and Python scripts that write the three structure files. They write identical files (checked with Octave 8.4 and Python 3.12). |
| `CMakeLists.txt` | Build instructions for CMake. It lists both `.cpp` files. |
| `job.slurm` | Batch script for Puma |

## The physics

Units are dimensionless (chapter 8b): the bell's arc length is 1 per half, the period is 1, the fluid density is 1.

- **Domain:** 4 by 4, not periodic, with no-slip walls; the bell starts with its apex at (0, 1), open downward.
- **Fluid:** density 1 and viscosity 0.01. For a bell 1.2 wide moving at a few tenths per period the Reynolds number ρUD/μ is a few tens, the regime of the 2011 study.
- **Grid:** 3 levels of adaptive refinement with ratio 4 and 16 cells on the coarsest level, so the finest grid has 256 cells across and Δx = 1/64. Cells are tagged for refinement around the bell and where the vorticity exceeds 0.1.
- **The bell:** from the apex (r = 0, z = Zs) down each side, the tangent angle is θ(s) = −1.55 (1 − e^(−s/β)), s the arc length from the apex: horizontal at the apex and nearly vertical (−1.55 ≈ −π/2) for s > β. The positions follow by marching along the curve in steps of ds = 1/128, as the course code did. β = 0.5 is the open bell (width 1.17, height 0.72); β = 0.2 the contracted bell (width 0.57, height 0.89). The left half is the mirror image of the right half, and the whole is one curve of 2n + 1 = 257 points.
- **Springs:** stiffness K = 1000 (tension per unit strain); the `.spring` file holds K/ds = 1.28 × 10⁵. They keep the bell from stretching under the beam forces.
- **Beams:** bending stiffness k_b = 1; the `.beam` file holds it divided by ds³, 2.10 × 10⁶, and the second differences of the resting shape as the preferred curvature, so the bell is in equilibrium at t = 0.
- **The pulse:** every period, β goes linearly from BETA_0 = 0.5 to BETA_M = 0.2 over T_CONTRACT = 0.5 (contraction) and back over the rest of the period (expansion): β = β₀ + (β_m − β₀) t/t₀ and β = β_m + (β₀ − β_m)(t − t₀)/(1 − t₀), the course's formulas with γ = 1. `update_beams.cpp` recomputes the shape for the current β each step and writes its second differences into the beams (`IBBeamForceSpec::getMeshDependentCurvatures()`).
- **Time:** 40,000 steps of 5 × 10⁻⁵ (2 periods), 50 saved frames.

As the bell contracts it pushes the fluid out of its opening and moves up; as it expands it draws fluid back in and recoils. The net motion per pulse is upward: this is jet propulsion with no valves, no prescribed positions and no applied force, only a shape that changes in time.

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
Jellyfish bell: period 1, contraction 0.5, beta from 0.5 to 0.2
```

## What you should see

Every 800 steps the screen shows a line like

```
integral{F} = 5.50671e-14 1.06581e-13
```

That is the sum of the Lagrangian forces, zero to round-off: the bell has no tethers, and springs and beams pull their own points with forces that cancel (chapter 11). The jellyfish can only push against the fluid.

Measured from the saved positions (`tools/ch10_figures.py` of the tutorial's working folder, not published here; the apex is point 128, the tips are points 0 and 256):

| Time | Apex height above its start | Width, tip to tip | What the bell is doing |
|---|---|---|---|
| 0 | 0 | 1.17 | open (β = 0.5) |
| 0.48 | 0.17 | 0.86 | the contraction (to β = 0.2) has just ended; the bell is still closing |
| 0.75 | 0.25 | 0.45 | the narrowest; a quarter period after the shape asked for it (0.57) |
| 1.00 | 0.20 | 0.72 | the first expansion has ended; the apex has fallen back |
| 1.30 | 0.11 | 1.24 | the widest; the recoil of the fluid drawn into the bell |
| 1.75 | 0.31 | 0.57 | the second contraction's narrowest |
| 2.00 | 0.28 | 0.80 | end of the second pulse |

What to notice:

- The bell follows its prescribed shape with a lag of about a quarter period and overshoots a little in both directions (narrowest 0.45 for a target of 0.57; widest 1.24 for a target of 1.17): the beams are stiff enough to drive the bell but not to make it rigidly follow the shape, and the fluid's inertia carries it past.
- The apex rises during the contraction and falls back during the expansion, and gains about 0.14 bell-lengths per pulse. A stiffer bell (k_b = 3, with `DT = 2.5e-5`) follows its shape more closely and swims faster; a softer one does not swim.
- The first version of this example, at the 512 grid (ds = 1/256, 513 points) with k_b = 10⁻³ and K = 1, ran and did nothing: the bending force per unit length, about k_b Δκ/L², was a thousand times too small to move the fluid. k_b of order 1 is needed (chapter 10's estimate), and at ds = 1/256 that stiffness needs a time step of about 10⁻⁵; the shipped run uses half the resolution and `DT = 5.0e-5`.

The output folders:

- `viz_IB2d/dumps.visit` holds the fluid data on the adaptive grid: velocity `U`, pressure `P`, vorticity `Omega` and `Div U` (51 frames).
- `viz_IB2d/lag_data.visit` holds the bell as the mesh `bell_256_mesh`.
- `hier_data_IB2d/X.NNNNN` and `F.NNNNN` are the points' positions and forces as plain-text PETSc vectors, with x and y alternating. Chapter 11 reads them in MATLAB and Python.
- `IB2d.log` is the log file.

## Looking at it in VisIt

1. Open `viz_IB2d/dumps.visit`, then choose **Add → Pseudocolor → Omega** and **Draw**: each contraction sheds a pair of opposite-signed vortices from the bell's margin (a vortex ring, seen in cross-section), and the expansion sheds a weaker pair of the opposite sign into the bell.
2. Open `viz_IB2d/lag_data.visit` as a second database, then **Add → Mesh → bell_256_mesh** and **Draw**; step through the frames.
3. A **Vector** plot of `U` shows the jet out of the opening during contraction and the refilling during expansion.

IBAMR 0.19 writes the velocity only as the vector `U`. Older versions also wrote `U_x` and `U_y`.

## Things to try

- `T_CONTRACT = 0.3`: a fast contraction and a slow expansion, like a real medusa; compare the distance per pulse.
- `BETA_M = 0.3` (a weaker contraction) or `BETA_0 = 0.6` (a flatter bell).
- Double `MU` (half the Reynolds number): the recoil grows and the net motion shrinks, the effect the 2011 paper studied.
- `kappa_beam = 3.0` in the generator with `DT = 2.5e-5`: the bell follows its shape more closely; `kappa_beam = 0.3`: it hardly moves.
- Run 6 periods (`END_TIME = 6.0`) and measure the steady swimming speed from the apex's position (chapter 11).
- The exponent γ of the course's formulas (set to 1 here) changes the time course of the pulse; add it to `update_beams.cpp` as a fifth input key.

## History

This example is new in the tutorial. The course's `Example_jellyfish_curvature.zip` (2013; offered again in the 2018 "Changing Resting Curvature" deck) is no longer in the course folders, so the example was rebuilt from the lecture's description of the bell (the tangent-angle formula, β₀ = 0.5, β_m = 0.2, the contraction and expansion formulas with γ = 1) and its `update_beams.C` fragments. Changes from those fragments:

- The bell is one curve from tip to tip, so every interior point, the apex included, has one beam and one spring on each side; the course indexed an apex point with two sides hanging from it.
- The period, the contraction time and β₀, β_m are input keys. The course code had `pulse_time = current_time - floor(current_time)` (a period of 1) next to a cycle count `ptt = floor(current_time/(2*to))` (a period of 2 t₀); the two agree only for t₀ = 0.5, which is the shipped setting.
- The shape is computed once per step for the half bell and mirrored, instead of per node; the point's number along the bell is counted from the structure's first Lagrangian index; `phi`, which the course set and never used, is gone.
- The curvature is an `IBTK::Vector` taken by reference (`Point&` in the 2018 slides, `TinyVector<double, 2>&` in 2013).
- The stiffnesses, the resolution and the time step were chosen by the estimate in chapter 10 and by trial (see above); the course said only that "some work must be done to ensure the beams and springs are sufficiently stiff in order to generate motion".
