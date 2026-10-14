# ConstraintIB/03 Swimming eel

A two-dimensional eel of length 1 m, filled with 2,932 Lagrangian points, bends as a prescribed travelling wave (`body_shape_equation`: amplitude growing from head to tail, one wavelength on the body, period 1 s) and swims freely: its translation and rotation are not prescribed but computed by the constraint immersed boundary method from momentum conservation, as in example 02. This is the free-swimming case of Bhalla et al. (2013) and the third example of the 2020 lecture on ConstraintIB, "a body that deforms in a prescribed manner but is propelled through the water due to rigid body motion". It goes with chapter 14 of *Using IB Software*.

| | |
|---|---|
| Method | Constraint IB (`ConstraintIBMethod` with the `IBEELKinematics` class): prescribed deformation, free rigid motion; the control-volume force evaluator |
| Dimension | 2D |
| Chapters | 14 (constraint IB), 10 (prescribed shapes), 11 (forces), 15 (the upstream examples) |
| Run time | 12 minutes on 8 ranks of a laptop (20,000 steps of 0.0001 s) |
| Tested with | IBAMR 0.19.0 (autoibamr; GCC 13.3, Open MPI 4.1.6, Ubuntu 24.04) |
| Upstream relative | `examples/ConstraintIB/eel2d` in IBAMR: this is that example, with the edits listed under "History"; `eel3d` and `knifefish` are its 3D relatives |

## Files

| File | What it is |
|---|---|
| `main.cpp` | The upstream `example.cpp`: the program of examples 01 and 02 with an `IBEELKinematics` object, plus an `IBHydrodynamicForceEvaluator` that measures the force on the eel from the momentum balance of a control volume (`InitHydroForceBox_0` in the input) that moves with the eel |
| `IBEELKinematics.cpp`, `.h` | The kinematics class: reads `body_shape_equation`, `deformation_velocity_function_0` and `_1` (muParser expressions of the body coordinate `X_0`, time `T` and the body normal `N_0`, `N_1`), `initial_angle_body_axis_0`, the manoeuvring keys and `food_location_in_domain_*`; each step it sets the deformation velocity of every point and, in `setShape`, the body's shape in its own frame (`lag_position_update_method = "CONSTRAINT_POSITION"`: positions are set from the shape, not integrated) |
| `input2d` | Physical, grid, solver and output settings; the `ConstraintIBMethod` block; the `ConstraintIBKinematics` block with the `eel2d` sub-block (shape, deformation velocity, manoeuvring switched off, food location); `InitHydroForceBox_0` |
| `eel2d.vertex` | 2,932 points filling the eel: for each of 256 stations along the body, the points above and below the backbone one finest cell (1/256 m) apart; a rounded head of width 0.04 m and a body tapering linearly to the tail; nose at x = −0.5, tail at x = 0.5 |
| `eel2d_straightswimmer.m`, `generate_eel2d.py` | MATLAB/Octave and Python scripts that write the vertex file. They write identical files, byte for byte, and the file equals the one shipped upstream |
| `CMakeLists.txt` | Build instructions for CMake. It lists both `.cpp` files. |
| `job.slurm` | Batch script for Puma |

## The physics

- **Prescribed deformation, free swimming.** The shape of the eel in its own frame is y(x, t) = 0.125 (x + 0.03125)/1.03125 sin(2πx − 6.28 t) for x from 0 (nose) to 1 (tail): a wave of one body length travelling toward the tail at one body length per second, with an amplitude that grows from 0.004 at the nose to 0.125 at the tail. `deformation_velocity_function_0/1` is the time derivative of that shape, applied along the body normal (`N_0`, `N_1`). `ConstraintIBMethod` subtracts the momentum of the deformation (so the prescribed wave carries none), computes the rigid translation (`1,1,0`) and rotation (`0,0,1`) from the fluid momentum in the body, and moves the eel with their sum. The eel swims because the wave pushes fluid backward.
- **Numbers.** Length 1 m, ρ = 1; `MU = 0.785/Re` with `Re = 5609`, the velocity scale 0.785 m/s being the tail's peak lateral speed (amplitude 0.125 times the angular frequency 2π). The box is 8 m × 4 m, periodic, with the eel at x ∈ [−0.5, 0.5] of a box that runs from −6.52 to 1.48: six body lengths of room to swim in the −x direction. `N = 64` cells per 4 m on the coarsest level (the box is 2N × N cells) and three levels refined by 4: finest cells 1/256 m, ten across the head.
- **Time step.** `DT_MAX = 0.0001`: 10,000 steps per tail beat.
- **The force evaluator.** `IBHydrodynamicForceEvaluator` computes the force and torque on the eel from the rate of change of momentum in a box of 2 m × 1.4 m around it plus the momentum flux through its faces, the control-volume method of Nangia et al. (2017); `main.cpp` moves the box with the eel's centre of mass each step. It writes `Drag_CV_strct_id_0` and `Torque_CV_strct_id_0`.

## Build and run

Load the compilers that IBAMR was built with and source autoibamr's `enable.sh` (chapter 1, 2 or 3), then from this folder:

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j 4
mpirun -np 4 ./build/main2d input2d
```

On Puma: `sbatch job.slurm`. The run writes `viz_eel2d_Str/` (VisIt), `Eel2dStr/` (the text outputs below), `Drag_CV_strct_id_0`, `Torque_CV_strct_id_0`, a restart folder, and `IB2dEelStr.log`.

## What you should see

`Eel2dStr/` holds the method's outputs, one line per step, tab-separated, time first:

| File | Columns |
|---|---|
| `Eel2d_COM_coordinates_struct_no_0` | t, centre of mass (x y z): where the eel is |
| `Eel2d_Trans_vel_struct_no_0` | t, rigid swimming velocity (x y z), velocity of the centre of mass due to the deformation (x y z) |
| `Eel2d_Rot_vel_struct_no_0` | t, rigid angular velocity (x y z; z only), angular velocity of the deformation (x y z) |
| `Eel2d_Drag_force_struct_no_0` | t, inertial force (x y z), constraint force (x y z) |
| `Eel2d_Torque_struct_no_0` | t, torque (z) |

Measured from these files (`tools/ch14_figures.py` of the tutorial repository reads them):

| Quantity | Measured |
|---|---|
| Centre of mass | −0.32 m in the first beat, −0.47 m in the second: −0.78 m in two beats, with +0.04 m sideways |
| Mean swimming speed | 0.32 m/s in the first beat, 0.47 m/s in the second (still accelerating; one body length is 1 m) |
| Yaw rate | up to 0.47 1/s |
| Deformation's centre-of-mass velocity | up to 0.07 m/s, removed by the method each step |

The figure `ch14-eel-swimming.png` in the chapter plots the centre of mass and the swimming speed against time.

Things to notice:

- The eel starts from rest and accelerates in the −x direction: the wave travels toward the tail (+x in the body frame), so the thrust points the other way. The lecture's picture at t = 1 s showed the body about 0.3 lengths from where it started, with the vortex pair shed at the tail behind it.
- The swimming speed oscillates within each tail beat (the body's lateral motion costs thrust twice per period) around a mean that is still rising after two beats; the upstream run of 10 s reaches a steady mean.
- The deformation velocity of the centre of mass (columns 5 to 7 of the velocity file) is not zero: the prescribed wave, as written, carries momentum. `ConstraintIBMethod` measures it every step and subtracts it from the velocity it imposes (`correctVelocityOnLagrangianMesh`: the imposed velocity is the deformation velocity plus the rigid velocity minus the deformation's centre-of-mass velocity), so the wave itself cannot push the eel; only the fluid can.
- The two force files do not agree exactly: `Eel2d_Drag_force` is the constraint force the method applies, `Drag_CV` is the hydrodynamic force measured from a control volume; the first includes the inertia of the fluid in the body, the second is the force on the eel's surface. The chapter and chapter 11 discuss which is which.

## Looking at it in VisIt

Open `viz_eel2d_Str/dumps.visit`, Pseudocolor `Omega` with limits ±20 and a Mesh plot of `eel2d_vertices`. The boundary layers of opposite sign along the two sides of the body peel off the tail once per half beat as a vortex pair, the reverse Kármán street of a swimmer; the evaluator's control volume is plotted too (`registerStructurePlotData`).

## Things to try

- Let it hunt: `body_is_maneuvering = TRUE`. The eel then bends its body axis toward `food_location_in_domain_0/1` (1.0, −3.3) along `maneuvering_axis_equation`; the lecture mentions these "functions for chasing a target / food, swimming in a circle" as what makes the code harder to read. With manoeuvring off, the three keys are read and ignored.
- Change the amplitude (0.125 in both the shape and the velocity functions; they must match) or the frequency (6.28 in both): the swimming speed follows.
- `Re = 500` (the viscosity follows): a more viscous eel swims slower and sheds a tidier wake.
- Run the upstream 10 s (`END_TIME = 10.0`; raise `viz_dump_interval` to 1,000) to reach a steady swimming speed; this takes 100,000 steps.
- Lock the rotation (`calculate_rotational_momentum = 0,0,0`): the eel can no longer yaw, and swims straighter.

## History

This is IBAMR's `examples/ConstraintIB/eel2d` (A. P. S. Bhalla, 2014–2019), the third example of the 2020 lecture *Looking at ConstraintIB examples of prescribed and rigid body motion*. Edits for the tutorial:

- `example.cpp` is renamed `main.cpp`, with the tutorial's CMake file.
- `END_TIME` is 2 s (two tail beats) instead of 10 s; `viz_dump_interval` is 200 steps instead of 40.
- The `ConstraintIBMethod` block repeated the two `calculate_structure_*_mom` keys; the repeat is removed.
- `eel2d_straightswimmer.m` has its `plot` loop commented out so that it runs under `octave-cli`; `generate_eel2d.py` is new.
