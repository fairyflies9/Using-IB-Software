# ConstraintIB/02 Impulsively started cylinder

A rigid disc of diameter 1 m rests in a quiescent periodic box. For the first hundredth of a second a body force 400 e^(−400 t) N/m³ in the x direction acts on the fluid inside the disc (a `ForcingFunction` block, evaluated by muParser), and then nothing: the disc is free, and the constraint immersed boundary method computes its translation and rotation from the momentum of the fluid it occupies. This is the momentum-conservation check of section 7.2.2 of Bhalla et al. (2013) and the second example of the 2020 lecture on ConstraintIB: a rigid body in free motion, where example 01 was prescribed motion. It goes with chapter 14 of *Using IB Software*.

| | |
|---|---|
| Method | Constraint IB (`ConstraintIBMethod` with the `RigidBodyKinematics` class): free rigid-body motion from momentum conservation, a body-force impulse |
| Dimension | 2D |
| Chapters | 14 (constraint IB), 7 (boundary conditions, body forces), 11 (forces), 13 (mass), 15 (the upstream examples) |
| Run time | two and a half minutes on 4 ranks of a laptop (2,000 steps of 0.002 s) |
| Tested with | IBAMR 0.19.0 (autoibamr; GCC 13.3, Open MPI 4.1.6, Ubuntu 24.04) |
| Upstream relative | `examples/ConstraintIB/impulsively_started_cylinder` in IBAMR: this is that example, with the edits listed under "History" |

## Files

| File | What it is |
|---|---|
| `main.cpp` | The upstream `example.cpp`: the program of example 01 with a `RigidBodyKinematics` object in place of the oscillating one, created from the `Cylinder2d` sub-block of `ConstraintIBKinematics`; the `ForcingFunction` block of the input becomes the body force |
| `RigidBodyKinematics.cpp`, `.h` | The kinematics class for a body that does not deform: it reads `kinematics_velocity_function_0` and `_1` (muParser expressions of `t` and of the centre of mass `X0`, `X1`; "0.0" here) and gives every point that velocity; the rigid translation and rotation are not its business, `ConstraintIBMethod` adds them |
| `input2d` | Physical, grid, solver and output settings; `ForcingFunction` (the impulse); `ConstraintIBMethod` with `needs_divfree_projection = TRUE` and `output_eulerian_mom = TRUE`; `ConstraintIBKinematics` with the rigid degrees of freedom unlocked |
| `cylinder2d.vertex` | 795 points: every cell centre of the finest grid level (1/32 m apart) that lies inside the disc, shifted so that their mean is exactly the origin |
| `Cylinder2d.m`, `generate_cylinder2d.py` | MATLAB/Octave and Python scripts that write the vertex file (the upstream folder has no generator; this is the one of `flow_past_cylinder`, which writes the same file). They write identical files, byte for byte, and the file equals the one shipped upstream |
| `CMakeLists.txt` | Build instructions for CMake. It lists both `.cpp` files. |
| `job.slurm` | Batch script for Puma |

## The physics

- **Free motion.** `calculate_translational_momentum = 1,1,0` and `calculate_rotational_momentum = 0,0,1` unlock translation in x and y and rotation about z (the three rigid degrees of freedom of a 2D body; the z components are the third dimension, which does not exist here). After each fluid solve the method interpolates the fluid velocity to the disc's points, takes their mean as the rigid translational velocity and their moment about the centre of mass as the angular velocity, replaces the points' velocities by that rigid motion, and spreads the correction back. The fluid in the disc region therefore moves as a rigid body, and the body's momentum is what the fluid gave it: nothing else is solved for.
- **The impulse.** `function_0 = "(X0 - XCOM)^2 + (X1-YCOM)^2 < RADIUS^2 ? 400*exp(-400*t) : 0"` is a muParser expression with a ternary: inside the disc the force density is 400 e^(−400 t), outside it is zero. Its time integral is 1 N s/m³, so the impulse is the disc's area, π/4 ≈ 0.785 N s per metre of depth. The key `F = RHO/DT_MAX` in that block is defined and never used.
- **What to expect.** With ρ_solid = ρ_fluid, the impulse is shared between the disc and the fluid it must push aside. For a cylinder the added mass equals the displaced mass, so the disc should take up half the impulse: a velocity of about 0.5 m/s once the impulse is over (by t ≈ 0.02 s), then a slow decay by viscous drag at Re = 200 (`MU = 2R/Re = 0.005`). The total fluid momentum (`output_eulerian_mom`) should stay at the impulse: the method conserves it.
- **The projection.** `needs_divfree_projection = TRUE`: the velocity correction spread from the body is projected to be divergence-free before the fluid continues. Example 01 does not need it (the prescribed motion of a rigid disc is divergence-free already); here the method builds a Poisson solver for it at start-up.
- **Grid.** `N = 16` cells per 8 m on the coarsest level (the 32 m × 16 m box is 64 × 32 cells) and three levels refined by 4: finest cells 1/32 m, 32 across the diameter, one Lagrangian point per finest cell.
- **Time step.** `DT_MAX = 0.002`; the impulse is resolved by about ten steps.

## Build and run

Load the compilers that IBAMR was built with and source autoibamr's `enable.sh` (chapter 1, 2 or 3), then from this folder:

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j 4
mpirun -np 4 ./build/main2d input2d
```

On Puma: `sbatch job.slurm`. The run writes `viz_Cylinder_IB2d/` (VisIt), `Cylinder_Dump/` (the text outputs below), a restart folder at the end, and `Cylinder_IB2d.log`.

## What you should see

`Cylinder_Dump/` holds the method's text outputs, one line every 10 steps (`output_interval = 10`), tab-separated, time first:

| File | Columns |
|---|---|
| `CylinderDiv_Trans_vel_struct_no_0` | t, rigid translational velocity of the disc (x y z), velocity of the centre of mass due to the kinematics (zero here) |
| `CylinderDiv_Rot_vel_struct_no_0` | t, rigid angular velocity (x y z; only z can be non-zero) |
| `CylinderDiv_COM_coordinates_struct_no_0` | t, centre of mass (x y z) |
| `CylinderDiv_Drag_force_struct_no_0` | t, inertial force (x y z), constraint force (x y z) |
| `CylinderDiv_EULERIAN_MOMENTUM.TXT` | t, total momentum of the fluid in the box (x y z) |

Measured from these files (`tools/ch14_figures.py` of the tutorial repository reads them):

| Quantity | Measured |
|---|---|
| Disc velocity | peak 0.449 m/s at t = 0.020 s, when the impulse is spent (an ideal disc of the fluid's density taking half the impulse: 0.5); 0.424 at 0.1 s, 0.339 at 1 s, 0.223 at 4 s |
| Disc position | x = 1.199 m at 4 s; y within 0.002 m of 0 |
| Fluid momentum (x) | 0.764 at 0.1 s, 0.762 at 4 s; the 795 forcing cells of 1/32 m give 0.776, the disc's area 0.785 |
| Angular velocity | below 0.006 1/s throughout |

The figure `ch14-impulsive-cylinder.png` in the chapter plots the disc's velocity and position and the total momentum against time.

Things to notice:

- The disc's velocity rises during the impulse and settles near half of what the impulse alone would give it: the other half is in the fluid that the disc drags along (the added mass). This is the paper's check that momentum is exchanged correctly between the body and the fluid.
- The total momentum in the box stays at the value the impulse delivered: the constraint force exchanges momentum between body and fluid without creating any, and a periodic box has no walls to absorb it.
- The angular velocity stays at the round-off level: nothing in a symmetric problem turns the disc.
- The position file is the integral of the velocity file.

## Looking at it in VisIt

Open `viz_Cylinder_IB2d/dumps.visit`, Pseudocolor `Omega` and a Mesh plot of `cylinder2d_vertices`. A pair of vortices forms at the back of the disc as it starts and follows it; the box is periodic, so after a long run the wake comes round.

## Things to try

- Push the disc in y instead (`function_1` gets the ternary, `function_0 = "0.0"`); or push it off-centre (`XCOM`, `YCOM` moved by 0.2) so that the impulse has a moment and the disc turns.
- `needs_divfree_projection = FALSE`: compare the velocity and the momentum file.
- `Re = 20` and `Re = 2000` (the viscosity follows): the decay of the disc's speed changes from viscous to inertial.
- Run longer (`END_TIME = 20`) with `viz_dump_interval` raised accordingly; the upstream input runs "until stopped".
- Lock one direction: `calculate_translational_momentum = 1,0,0`.

## History

This is IBAMR's `examples/ConstraintIB/impulsively_started_cylinder` (A. P. S. Bhalla, 2016–2019), the second example of the 2020 lecture *Looking at ConstraintIB examples of prescribed and rigid body motion*. Edits for the tutorial:

- `example.cpp` is renamed `main.cpp`, with the tutorial's CMake file.
- `END_TIME` is 4 s instead of 10,000; `viz_dump_interval` is 50 steps instead of 1,000; `domain_boxes` is written with `N`.
- The lecture's slide 15 said that `RigidBodyKinematics.cpp` applies the decaying force and computes the centre of mass and momenta. It does neither: the force is the `ForcingFunction` block of the input, applied by the fluid solver, and the centre of mass and momenta are computed by `ConstraintIBMethod` according to the `calculate_*` flags. The class only evaluates the two `kinematics_velocity_function` expressions, which are zero here. Slide 17's `function_1 = "0.0“` had a curly closing quote, which the parser would reject; the file has straight quotes.
- `Cylinder2d.m` (from `flow_past_cylinder`) writes to this folder and its `plot` line is commented out; `generate_cylinder2d.py` is new.
