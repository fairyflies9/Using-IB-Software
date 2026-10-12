# IBFE/08 Plate hits circle

Two structures, each with its own mesh, share a periodic box of fluid. An upright plate is pushed up toward a free disc by a tether (target) force for one second and then coasts; the disc moves only because the fluid moves it. This example shows how to give IBFE several meshes ("parts"), how to register functions for each part, and how to write and view one ExodusII file per part.

| | |
|---|---|
| Method | Immersed boundary finite element (IBFE), two parts |
| Dimension | 2D |
| Chapters | 21 (two or more meshes), 18 (meshes from Trelis and Cubit), 28 (finite element data in VisIt) |
| Run time | about 2 minutes on 4 cores (115 s with IBAMR 0.16.0 and 132 s with 0.19.0 on a laptop) |
| Tested with | IBAMR 0.16.0 and 0.19.0 (autoibamr; GCC 13.3, Open MPI 4.1.6, Ubuntu 24.04) |
| Upstream relatives | `examples/IBFE/explicit/ex6` (a block and a beam, two parts) and `ex8` (three parts) in IBAMR |

## Files

| File | What it is |
|---|---|
| `main.cpp` | The IBAMR program: the tether on the plate, the stress functions, and the set-up of two parts |
| `input2d` | Physical, grid, solver and output settings, and the tether's speed and duration |
| `beam.e` | The plate's mesh: 98 nodes and 126 triangles, an ExodusII file made with Trelis |
| `circle.e` | The disc's mesh: 977 nodes and 1851 triangles, also from Trelis |
| `CMakeLists.txt` | Build instructions for CMake |
| `job.slurm` | Batch script for Puma |

## The physics

- **Domain:** 2 by 2, periodic in both directions, with 2 grid levels (32 cells across the coarse level, 128 on the fine level).
- **Fluid:** density 1 and viscosity 0.01.
- **Plate (part 0):** 0.0312 wide and 0.5 tall, standing upright with its center at (0, −0.5).
- **Disc (part 1):** radius 0.25, centered at (0, 0.5). Its bottom starts 0.5 above the plate's top.
- **Material:** both parts are neo-Hookean with shear modulus μ = 10 (`SHEAR_MODULUS`), with the split stress of IBFE/01.
- **Tether:** each point of the plate is pulled toward a target that moves up at speed 0.25 (`TETHER_SPEED`) until t = 1 (`TETHER_END_TIME`), with stiffness κ = 10⁶ (`KAPPA_S`). Then the force is switched off. The disc has no tether.

## Two meshes in one program

The parts are numbered by their order in the vector of meshes that is given to `IBFEMethod`:

```cpp
std::vector<MeshBase*> meshes = { &beam_mesh, &circle_mesh };   // part 0, part 1
```

Every `register...` call names the part it is for. The plate gets the tether and both stress functions; the disc gets only the stress functions:

```cpp
ib_method_ops->registerLagBodyForceFunction(beam_tether_force_data, 0);
ib_method_ops->registerPK1StressFunction(PK1_dev_stress_data, 0);
ib_method_ops->registerPK1StressFunction(PK1_dil_stress_data, 0);
ib_method_ops->registerPK1StressFunction(PK1_dev_stress_data, 1);
ib_method_ops->registerPK1StressFunction(PK1_dil_stress_data, 1);
```

Each part has its own finite element data (`getFEDataManager(0)` and `getFEDataManager(1)`) and its own ExodusII writer. `getExodusIIFilename("beam_")` puts the prefix in front of the file name from `input2d`, so the files are `viz_IB2d/beam_output.ex2` and `viz_IB2d/circle_output.ex2`.

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

The run takes 8000 time steps and saves 81 frames, one every 0.05 time units (`viz_dump_interval = int(.05/DT)`). Measured from the two ExodusII files:

| Time | Plate top y | Disc bottom y | Gap | Notes |
|---|---|---|---|---|
| 0 | −0.250 | 0.250 | 0.500 | |
| 1.0 | 0.000 | 0.270 | 0.269 | the plate is released |
| 2.0 | 0.146 | 0.301 | 0.156 | |
| 3.0 | 0.222 | 0.335 | 0.113 | |
| 4.0 | 0.274 | 0.368 | 0.094 | about six fine grid cells |

While it is tethered, the plate follows its target: at t = 1 its top is at y = 0.000, where the target puts it. After it is released it keeps rising, more and more slowly, and the gap keeps closing, but in this run the plate does not reach the disc: the disc is moving away too. The disc keeps its shape (its width stays 0.500).

Why does the disc keep moving? The tether pushes the plate, and through it the fluid, upward. In a periodic box that momentum has nowhere to go: after t = 1 the average upward velocity of the fluid stays at 0.016 (measured from the VisIt files: 0.0162 at t = 1, 0.0159 at t = 4). The disc, which sits in the column of fluid above the plate, rises at about 0.033.

IBAMR 0.16.0 and 0.19.0 give the same numbers (the node positions agree to 2 × 10⁻⁸).

The output folder `viz_IB2d/` holds

- `dumps.visit`: the fluid on the adaptive grid (`U`, `P`, `Omega`, `F`, `Div_U`);
- `beam_output.ex2` (0.6 MB) and `circle_output.ex2` (5.2 MB): the two parts, each with `dX_0`, `dX_1`, `X_0`, `X_1`, `F_0`, `F_1`, `U_0`, `U_1`.

The folder is 35 MB with IBAMR 0.19.0 and 48 MB with 0.16.0, which also writes `U_x`, `U_y`, `F_x` and `F_y`.

## Looking at it in VisIt

1. Open `viz_IB2d/dumps.visit`, then choose **Add → Pseudocolor → Omega** and **Draw**.
2. Open `viz_IB2d/beam_output.ex2` and add a **Mesh** plot. Then open `viz_IB2d/circle_output.ex2` and add a second **Mesh** plot. Each file is a separate database, so each needs its own plot.
3. To move each mesh with its part, make the vector expression `dX` = `{dX_0, dX_1}` in **Controls → Expressions**, and add **Operators → Transforms → Displace** with variable `dX` to both mesh plots.

Chapter 28 covers finite element output in more detail.

## Things to try

- Push the plate longer: `TETHER_END_TIME = 2.0`. The plate's top then reaches y = 0.250 at t = 2, and the gap closes to 0.040 (about 2.6 fine grid cells) at t = 2.5. After that it stays near 0.045: the plate never touches the disc, because the fluid between them keeps them apart. The disc is squeezed a little (its width grows to 0.5006 at t = 2).
- Change the material of one part only. Copy the two stress functions, give the copies a different shear modulus, and register them for part 1 instead of the originals.

## How the meshes were made

Both meshes were made with Trelis (now Coreform Cubit) in 2020 and saved as 2D ExodusII files with one block of 3-node triangles. No Trelis journal files came with the course folder. Chapter 18 shows how to make such meshes, and IBFE/05 shows how to make a 2D mesh with gmsh, which IBAMR reads just as well.

## History

The UNC version (2020) went with the lecture "Two Boundaries: Flapping wings and beam hits circle". It already used `std::vector<MeshBase*>` and `std::unique_ptr`. The changes for current IBAMR:

- A CMake build replaces the Makefile.
- `main.cpp` starts IBAMR with `IBTKInit`, no longer includes the old configuration headers, and uses `libMesh::Order` and `IBTK::rel_equal_eps`.
- Commented-out code is removed: coordinate mappings that were not used, and an `output_data` function that could save only one mesh.
- The mesh files, shear modulus, and the tether's stiffness, speed and end time can be set in `input2d`.
- The ExodusII files are called `beam_output.ex2` and `circle_output.ex2` instead of `mesh1output.ex2` and `mesh2output.ex2`.
- Restarted runs now save and reload the finite element data of both parts and append to both ExodusII files, as IBAMR's own examples do. Unlike those examples, only processor 0 reopens the ExodusII files: when every process reopens them, a restart on more than one process leaves files that can no longer be read (tested with IBAMR 0.16.0 and 0.19.0).
- The job script asks for 4 cores on Puma instead of 16 on a UNC queue.
- The input file has Unix line endings. The keys `use_IB_spread_operator` and `use_IB_interp_operator`, which IBAMR no longer reads, are removed.

The original files are in `examples/legacy/`.
