# IB/07 Moving plates

Two flexible plates start side by side, 5 mm apart, and are pulled apart by moving target points. Each plate is a separate structure with its own structure files, so the program can tell the plates apart and move them in opposite directions. This example goes with the target-points chapter of *Using IB Software* (moving target points and more than one structure).

| | |
|---|---|
| Method | Immersed boundary (IB): springs, beams and moving target points; two structures |
| Dimension | 2D |
| Chapters | 9 (target points, springs and multiple structures), 6 (structure files), 11 (forces) |
| Run time | about 5 to 8 minutes on 4 cores (0.03 to 0.05 s per step on a laptop; 10,000 steps) |
| Tested with | IBAMR 0.16.0 and 0.19.0 (autoibamr; GCC 13.3, Open MPI 4.1.6, Ubuntu 24.04) |
| Upstream relative | `examples/ConstraintIB/moving_plate` in IBAMR moves a rigid plate with prescribed motion instead of target points |

## Files

| File | What it is |
|---|---|
| `main.cpp` | The IBAMR program: the program of IB/01 plus a call to `update_target_point_positions()` before each time step. It also writes the positions and forces every few steps. |
| `update_target_point_positions.cpp`, `.h` | The function that moves the left plate's target points left and the right plate's right |
| `input2d` | Physical, grid, solver and output settings. `structure_names` lists the two plates. |
| `plate2d_left_512.vertex`, `.spring`, `.beam`, `.target` | The left plate: 103 points on the line x = −2.5 mm, 102 springs, 101 beams, and 103 target points (every point) |
| `plate2d_rght_512.vertex`, `.spring`, `.beam`, `.target` | The right plate, the same at x = +2.5 mm |
| `generate_mesh2d.m`, `generate_mesh2d.py` | MATLAB/Octave and Python scripts that write all eight structure files. They write identical files (checked with Octave 8.4 and Python 3.12). |
| `CMakeLists.txt` | Build instructions for CMake. It lists both `.cpp` files. |
| `job.slurm` | Batch script for Puma |

Point numbers start at 0 in each plate's files. IBAMR numbers the points of all structures together in the order of `structure_names`, so the left plate's points are 0 to 102 and the right plate's are 103 to 205. `update_target_point_positions.cpp` asks IBAMR for each plate's range with `getLagrangianStructureIndexRange(0, ...)` and `(1, ...)`.

## The physics

- **Domain:** 1 m by 1 m, periodic in both directions.
- **Fluid:** density 1000 kg/m³ and viscosity 100 N s/m², so the flow is very slow and viscous.
- **Grid:** 4 levels of adaptive refinement with ratio 4 and 8 cells on the coarsest level, so the finest grid has 512 cells across and Δx = 1/512 m ≈ 2 mm.
- **Plates:** each 0.1 m long and vertical, centered on y = 0, at x = −2.5 mm and x = +2.5 mm. Each has 103 points, ds = 0.1/102 m ≈ Δx/2 apart.
- **Springs:** stiffness K = 2000 (tension per unit strain); the `.spring` files hold K/ds = 2.04 × 10⁶. Rest length ds, so they start unstretched.
- **Beams:** bending stiffness 5 × 10⁻³; the `.beam` files hold it divided by ds³, 5.31 × 10⁶.
- **Target points:** every point is pulled toward its target position with the force κ (X_target − X), κ = 2000/ds = 2.04 × 10⁶.
- **Motion:** `update_target_point_positions.cpp` moves the left plate's targets to the left and the right plate's to the right. The speed rises linearly from 0 to V = 0.2 m/s over the first 0.1 s and then stays at 0.2 m/s, so each plate has moved 0.01 m by t = 0.1 s and 0.19 m by t = 1 s.

The plates start only 5 mm apart, 2.6 grid cells. The IB_4 delta function spreads each point's force over 4 grid cells in each direction, so at first the two plates push and pull the same grid cells: the fluid between them is nearly trapped and moves with both plates. As they separate, fluid has to flow into the widening gap from above and below. This is the "fling" half of the clap-and-fling motion of some small insects' wings.

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

The program has two source files. Both must be listed in `CMakeLists.txt` (`add_executable(main2d main.cpp update_target_point_positions.cpp)`); if one is missing, the link step fails with `undefined reference to update_target_point_positions`.

## What you should see

The run takes 10,000 time steps of 10⁻⁴ s and saves 50 frames. Every 200 steps the screen shows a line like

```
integral{F} = -0.172314 0.147064
```

That is the sum of the target-point forces on both plates. The two plates are pulled in opposite directions with nearly equal force, so the sum is small; the force on each plate is in the saved force files (`hier_data_IB2d/F.NNNNN`, the left plate's points first).

Measured from the saved positions and forces:

| Time (s) | Gap between the plates (m) | Force pulling each plate (N) |
|---|---|---|
| 0.02 | 0.0052 | 63,000 |
| 0.06 | 0.0116 | 63,500 |
| 0.10 | 0.0249 | 8,800 |
| 0.14 | 0.0410 | 2,470 |
| 0.22 | 0.0730 | 780 |
| 0.30 | 0.1050 | 465 |
| 0.50 | 0.1850 | 264 |
| 1.0 | 0.3850 | 177 |

While the gap is only a few grid cells wide, the force needed to pull the plates apart is enormous (63,000 N on each plate), because the fluid between them cannot get out of the way and new fluid has to be sucked into the gap from its ends. Once the gap is a few centimeters wide the force drops a hundredfold. The plates follow their targets to within 3 × 10⁻⁴ m (the force divided by the total stiffness of a plate's 103 target points) and stay straight: the spread of each plate's x positions is under 10⁻³ m while the gap is small and 4 × 10⁻⁵ m afterwards.

The time step: `DT = 1.0e-4` runs; `DT = 5.0e-5` gives the same gap and forces to 4 digits at t = 0.2 s; `DT = 2.0e-4` stops after 7 steps with `Time step size change encountered` (chapter 16). IBAMR 0.16.0 and 0.19.0 give byte-identical positions and forces (checked at t = 0.04 s).

The output folders:

- `viz_IB2d/dumps.visit` holds the fluid data on the adaptive grid: velocity `U`, pressure `P`, vorticity `Omega` and `Div_U` (51 frames, 16 MB).
- `viz_IB2d/lag_data.visit` holds both plates, as the two meshes `plate2d_left_512_mesh` and `plate2d_rght_512_mesh`.
- `hier_data_IB2d/X.NNNNN` and `F.NNNNN` are the points' positions and forces as plain-text PETSc vectors, with x and y alternating, the left plate's 103 points first. Chapter 11 reads them in MATLAB.
- `IB2d.log` is the log file.

## Looking at it in VisIt

1. Open `viz_IB2d/dumps.visit`, then choose **Add → Pseudocolor → P** and **Draw**. The pressure in the gap is far below the pressure outside while the plates are close together.
2. Open `viz_IB2d/lag_data.visit` as a second database, then choose **Add → Mesh → plate2d_left_512_mesh**, and again for `plate2d_rght_512_mesh`, and **Draw**.
3. A **Vector** plot of `U`, or **Add → Pseudocolor → Omega**, shows the fluid rushing into the gap around the ends of the plates and the pair of eddies that forms there.

IBAMR 0.19 writes the velocity only as the vector `U`. Older versions also wrote `U_x` and `U_y`. The expressions above work in both.

## Things to try

- Run the course's full 2 s (`END_TIME = 2.0`). Each plate then moves 0.39 m, so the plates end up 0.22 m apart through the periodic boundary and approach each other from the other side.
- Change the starting gap with `offset` in `generate_mesh2d.m` (and write new structure files). With a wider gap the starting force is much smaller.
- Move only one plate: in `update_target_point_positions.cpp` leave the right plate's targets alone (and rebuild).
- Make the plates floppier with `kappa_beam` in `generate_mesh2d.m`, or tether only some of their points by writing fewer lines into the `.target` files, so that the free parts bend as the plates are pulled apart.
- Lower the viscosity `MU` to 10. At a higher Reynolds number the fling sheds vortices from the tips.

## History

This example comes from the UNC course version (`5-Example_2Dmoving_plates`, 2014–2020; 16 cores for 2 hours on a debug queue). The changes for current IBAMR:

- A CMake build replaces the Makefile, and `update_target_point_positions.C` became `.cpp`.
- `main.cpp` starts IBAMR with `IBTKInit` and no longer includes the old configuration headers. It is the rubber band's program (IB/01) with the target-point update added; a commented-out call to `update_springs()` is removed.
- The comments in `update_target_point_positions.cpp` describe the plates. The course comments called them "the wing". Unused variables are removed.
- The time step is 1.0e-4 s instead of 1.0e-6 s, and the run stops at 1 s instead of 2 s.
- The input file has Unix line endings, so it no longer needs `//` at the end of every line.
- `generate_mesh2d.m` has explanatory comments and says what each stiffness divides by; `generate_mesh2d.py` is new. Both write exactly the course's structure files.

The original files are in `examples/legacy/`.
