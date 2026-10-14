# ConstraintIB/01 Oscillating cylinder

A rigid disc of diameter 1 m, filled with Lagrangian points, oscillates along x in a quiescent fluid with the velocity U∞ cos(2πft), f = 0.2 Hz and U∞ = 1 m/s, at Re = ρU∞D/μ = 100. The motion is prescribed. The constraint immersed boundary method (`ConstraintIBMethod`) makes the fluid inside the disc move with it after every fluid solve and reports the force this takes, which is the drag on the cylinder, split into an inertial part and a constraint part. This is the case of section 7.1.4 of Bhalla et al. (2013) and the first example of the 2020 lecture on ConstraintIB. It goes with chapter 14 of *Using IB Software*.

| | |
|---|---|
| Method | Constraint IB (`ConstraintIBMethod` with a `ConstraintIBKinematics` subclass): prescribed kinematics, a rigid body |
| Dimension | 2D |
| Chapters | 14 (constraint IB), 7 (boundary conditions and domain), 11 (forces), 15 (the upstream examples) |
| Run time | 11 minutes on 8 ranks of a laptop (6,667 steps of 0.0015 s; WSL, three examples running at once) |
| Tested with | IBAMR 0.19.0 (autoibamr; GCC 13.3, Open MPI 4.1.6, Ubuntu 24.04) |
| Upstream relative | `examples/ConstraintIB/oscillating_rigid_cylinder` in IBAMR: this is that example, with the edits listed under "History" |

## Files

| File | What it is |
|---|---|
| `main.cpp` | The upstream `example.cpp`: the program of IB/01 with `ConstraintIBMethod` in place of `IBMethod`, one `OscillatingCylinderKinematics` object created from the `Cylinder` sub-block of `ConstraintIBKinematics` and registered with the method, and a `ForcingFunction` hook (unused here) |
| `OscillatingCylinderKinematics.cpp`, `.h` | The kinematics class: reads `frequency` and `U_infinity` from its input block (it stops with an error if either is missing), and before every step sets the x-velocity of every point of the disc to `prescribed_trans_velocity + U_infinity cos(2π frequency t)`; `setShape` does nothing, since the disc does not deform |
| `input2d` | Physical, grid, solver and output settings; the `ConstraintIBMethod` block with its `PrintOutput` sub-block; the `ConstraintIBKinematics` block with the `Cylinder` sub-block |
| `cylinder2d.vertex` | 12,851 points: every cell centre of the finest grid level (1/128 m apart) that lies inside the disc, shifted so that their mean is exactly the origin |
| `Cylinder2d.m`, `generate_cylinder2d.py` | MATLAB/Octave and Python scripts that write the vertex file. They write identical files, byte for byte (checked with Octave 8.4 and Python 3.12), and the file equals the one shipped upstream |
| `CMakeLists.txt` | Build instructions for CMake. It lists both `.cpp` files. |
| `job.slurm` | Batch script for Puma |

## The physics

- **The constraint.** The fluid is solved everywhere, including inside the disc. After each fluid solve the method interpolates the fluid velocity to the disc's points, replaces it by the velocity the kinematics object prescribes, spreads the corrected velocity back to the grid, and moves the points with it. The force needed to do this is the force the body exerts on the fluid; its negative is the drag. `ConstraintIBMethod` writes it every step (see "What you should see").
- **Prescribed motion.** `calculate_translational_momentum = 0,0,0` and `calculate_rotational_momentum = 0,0,0` lock every rigid degree of freedom: the disc moves exactly as the kinematics object says. Example 02 unlocks them.
- **Numbers.** D = 1 m, ρ = 1, μ = 2R/Re = 0.01 (Re = 100 on U∞ and D). The amplitude of the oscillation is U∞/(2πf) = 0.80 m, so the Keulegan–Carpenter number U∞/(fD) is 5: the cylinder travels 1.6 diameters each half period. The box is 32 m × 16 m, periodic in both directions, far enough that the cylinder does not see itself in two periods.
- **Grid.** `N = 16` cells per 8 m on the coarsest level (the box is 4N × 2N = 64 × 32 cells, 0.5 m each) and four levels refined by 4, so the finest cells are 1/128 m: 128 cells across the diameter, one Lagrangian point per finest cell. The finest level follows the vorticity (`vorticity_rel_thresh = 0.25`).
- **Time step.** `DT_MAX = 0.0015` with `CFL_MAX = 0.3`; the period is 5 s, so a period is about 3,300 steps.

## Build and run

Load the compilers that IBAMR was built with and source autoibamr's `enable.sh` (chapter 1, 2 or 3), then from this folder:

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j 4
mpirun -np 4 ./build/main2d input2d
```

On Puma: `sbatch job.slurm`. The run writes `viz_cylinder2d/` (VisIt), `Dump--Cylinder/` (the text outputs below) and `IB2d_cylinder2d.log`.

## What you should see

The log prints `FREQUENCY ================= 0.2` and `U_INFINITY ================= 1` as the kinematics object reads its keys, then the usual time-step banners. `Dump--Cylinder/` holds one text file per output quantity switched on in `PrintOutput`, one line per step (`output_interval = 1`), tab-separated, time first:

| File | Columns |
|---|---|
| `Cylinder_Drag_force_struct_no_0` | t, inertial force (x y z), constraint force (x y z): the force on the fluid from the change of the body points' velocity, and from the constraint correction, each times ρ_solid/Δt |
| `Cylinder_Trans_vel_struct_no_0` | t, rigid translational velocity (x y z; zero here, every component is locked), velocity of the centre of mass due to the prescribed kinematics (x y z) |
| `Cylinder_Rot_vel_struct_no_0` | t, rigid angular velocity (x y z; zero here), angular velocity due to the kinematics (x y z) |
| `Cylinder_COM_coordinates_struct_no_0` | t, centre of mass (x y z) |
| `Cylinder_MOI_struct_no_0` | t, the moment-of-inertia tensor |

Measured from these files (`tools/ch14_figures.py` of the tutorial repository reads them):

| Quantity | Measured |
|---|---|
| Centre of mass | amplitude 0.7958 m, reached at t = 1.25 s (U∞/2πf = 0.7958 m); never more than 1e-6 m from 0.80 sin(2πft) |
| Force on the fluid, second period (t = 5 to 10 s) | between −3.44 and +3.46 N/m; Fourier component in phase with the acceleration 3.36 N/m (the inviscid estimate 2ρπR²a_max = 1.97 N/m), in phase with the velocity 0.91 N/m (a drag coefficient 2F/ρU∞²D of 1.8) |
| Start-up | the first step's constraint force is 523 N/m: the velocity jumps from 0 to U∞ at t = 0 and the method supplies that impulse in one step |

The figure `ch14-oscillating-cylinder.png` in the chapter plots the centre of mass and the force against time.

Things to notice:

- The centre of mass follows (U∞/2πf) sin(2πft) = 0.80 sin(2πft) exactly: the method imposes the velocity, so the position is its integral to the accuracy of the time stepping.
- The force has two parts. The inertial part is ρ times the acceleration of the fluid that the body displaces; the constraint part is what the fluid's own dynamics did not already provide. Their sum is the force on the fluid, and minus that sum is the drag on the cylinder, which for an oscillating body has a component in phase with the acceleration (added mass) and one in phase with the velocity (drag proper).
- `Dump--Cylinder` and the files in it are created by the method; nothing in `main.cpp` writes them.

## Looking at it in VisIt

Open `viz_cylinder2d/dumps.visit`, add a Pseudocolor plot of `Omega` (set the limits to ±5) and a Mesh plot of `cylinder2d_vertices` from `lag_data.visit`; the 2020 lecture showed this at t = 72 s. The vortices shed at each reversal travel with the cylinder and are run into on the way back; this is what makes the force at KC = 5 differ from the drag of a steadily towed cylinder.

## Things to try

- Make the cylinder go up and down instead: in `OscillatingCylinderKinematics.cpp`, `setOscillatingCylinderSpecificVelocity`, set `d_current_kinematics_vel[0][1][k]` (component 1 is y) instead of `[0][0][k]`. This is the lecture's exercise.
- Tow it instead of oscillating it: `U_infinity = 0` and `prescribed_trans_velocity = 1.0` give a cylinder moving at constant speed through fluid at rest, the upstream `flow_past_cylinder` case.
- Change `frequency` and `U_infinity`; the Keulegan–Carpenter number U∞/(fD) sets how far the cylinder runs into its own wake.
- Switch `output_power = TRUE` in `PrintOutput` to get the power the motion costs.
- A quick version: three levels instead of four (`MAX_LEVELS = 3`) with the 796-point disc of example 02 (its `generate_cylinder2d.py` uses 1024 cells per 32 m); it runs in minutes.

## History

This is IBAMR's `examples/ConstraintIB/oscillating_rigid_cylinder` (A. P. S. Bhalla, 2016–2019), which the 2020 lecture *Looking at ConstraintIB examples of prescribed and rigid body motion* walked through. Edits for the tutorial:

- `example.cpp` is renamed `main.cpp`, with the tutorial's CMake file (the upstream one uses IBAMR's own build helpers).
- `END_TIME` is 10 s (two periods) instead of 130 s; `viz_dump_interval` is 100 steps instead of 40; `domain_boxes` is written with `N`, as the comment next to `N` says, instead of the literal 63 and 31.
- The upstream input had a second `PrintOutput` block at top level, outside `ConstraintIBMethod`, with a key `output_drag_kinetic_energy`. Nothing reads it: `ConstraintIBMethod` takes the `PrintOutput` sub-block inside its own block, and the drag key is `output_drag`. The 2020 lecture's slide 10 showed this stray block; it is removed here and the real one is documented above.
- `Cylinder2d.m` writes to this folder instead of one level up, and its `plot` line is commented out so that it runs under `octave-cli`; `generate_cylinder2d.py` is new.
