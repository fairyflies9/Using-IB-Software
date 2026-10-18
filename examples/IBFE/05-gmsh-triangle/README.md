# IBFE/05 Triangle meshed with gmsh

A right triangle, meshed with gmsh, is pulled through a periodic box of fluid by target ("tether") forces. The tether moves exactly as in example IBFE/01 with `MOTION = "FULL"`: up, then down, then the triangle is released. What is new here is the mesh. This example shows how to make a 2D mesh with gmsh that libMesh and IBAMR can read, and what goes wrong when a mesh file is not quite right.

| | |
|---|---|
| Method | Immersed boundary finite element (IBFE) |
| Dimension | 2D |
| Chapters | 18 (creating meshes), 17 (getting started with IBFE), 28 (finite element data in VisIt) |
| Run time | about 2 minutes on 4 cores (100 s with IBAMR 0.16.0 and 103 s with 0.19.0 on a desktop PC under WSL) |
| Tested with | IBAMR 0.16.0 and 0.19.0 (autoibamr; GCC 13.3, Open MPI 4.1.6, Ubuntu 24.04); gmsh 4.12.1 |
| Upstream relatives | `examples/IBFE/explicit/ex2` (same stress model, mesh built in the program) and `examples/IBLevelSet/ex0` (reads a gmsh mesh) in IBAMR |

## Files

| File | What it is |
|---|---|
| `main.cpp` | The IBAMR program, including the tether force and the stress functions |
| `input2d` | Physical, grid, solver and output settings; `MESH_FILENAME` chooses the mesh |
| `triangle.msh` | The course mesh: 759 nodes and 1404 triangles, in gmsh's ASCII MSH 2.2 format. Its node order was fixed for current IBAMR (see below). |
| `triangle.geo` | gmsh script that makes the same triangle |
| `fix_orientation.py` | Python 3 script that makes every triangle of an MSH 2.2 file counterclockwise. It was used to fix `triangle.msh`. |
| `CMakeLists.txt` | Build instructions for CMake |
| `job.slurm` | Batch script for Puma |

## The physics

- **Domain:** 2 by 2, periodic in both directions, with 2 grid levels (32 cells across the coarse level, 128 on the fine level, so the fine grid spacing is 2/128 = 0.0156).
- **Fluid:** density 1 and viscosity 0.01.
- **Triangle:** corners (0, 0), (0.5, 0) and (0, 0.5). It is a neo-Hookean solid with shear modulus μ = 10 (`SHEAR_MODULUS`), with the same split stress as IBFE/01.
- **Tether:** each point is pulled toward its target with force κ (target − current position), κ = 10⁶ (`KAPPA_S`). The target moves up at speed 0.5 until t = 1, down until t = 3, and then the force is switched off.
- **Element size:** the course chose triangles about one fine grid cell across (`lc = 0.0156` in `triangle.geo`) and set `IB_POINT_DENSITY = 1.0`. The time step is 5 × 10⁻⁴ (`DT`), half of IBFE/01's.

## Making the mesh with gmsh

`triangle.geo` places three points, joins them with three lines, makes a plane surface from the lines, and puts the surface in a physical group. To make a mesh file that libMesh can read:

```bash
gmsh -2 -format msh22 triangle.geo -o triangle_gmsh.msh
```

`-2` makes a 2D mesh and `-format msh22` writes an ASCII file in MSH format 2.2. Then set `MESH_FILENAME = "triangle_gmsh.msh"` in `input2d`. libMesh also reads gmsh 4's own ASCII format (MSH 4.1, what `gmsh -2` writes without `-format`), but not binary files. If you use gmsh's graphical interface instead, choose an ASCII version of the MSH format when you export.

With gmsh 4.12.1 this makes a mesh with the same numbers of nodes and triangles as the course mesh (759 and 1404). All 112 boundary nodes are the same, and so are 379 of the 647 interior nodes. The `Mesh.Algorithm = 5;` line (Delaunay) is what makes the counts match. Without it, gmsh 4 uses its default algorithm and makes 687 nodes and 1260 triangles.

Two settings in the `.geo` file matter for IBAMR:

- **Go around the surface counterclockwise.** The curve loop `{1, 2, -3}` goes (0, 0.5) → (0, 0) → (0.5, 0) → (0, 0.5). gmsh numbers the corners of every triangle in the same direction as the loop. A clockwise loop, `{3, -2, -1}`, makes every triangle clockwise, and IBAMR stops (see below). The gmsh command `ReverseMesh Surface{5};` turns them around.
- **Use a Physical Surface.** Once a file has any physical group, gmsh saves only the elements in physical groups. With only a `Physical Curve`, the file holds just the 112 boundary lines and no triangles.

## When the mesh file is wrong

| Problem | What IBAMR prints | Fix |
|---|---|---|
| The file is binary (`gmsh -bin`, or a binary format chosen when exporting) | `Error: Unknown data format for mesh in Gmsh reader.` | Save as ASCII text. |
| The triangles are clockwise | `IBAMR requires that the Jacobian of each element must be positive, but the present element has at least one point at which the Jacobian is either negative or zero.` followed by the element's corners and `To get around this error, you will need to edit the problematic mesh either by hand or with a CAD program.` | Make the curve loop counterclockwise, add `ReverseMesh Surface{...};`, or run `python3 fix_orientation.py old.msh new.msh`. |
| There is a Physical Curve but no Physical Surface | `Failed assertion: mesh->mesh_dimension() == mesh->spatial_dimension()` | Add a `Physical Surface` that contains the surface. |

All three were run with IBAMR 0.16.0 and 0.19.0 and give the same messages.

The course mesh `triangle.msh` had the second problem: all 1404 of its triangles were clockwise. IBAMR has checked for this since version 0.11.0 (2022); the course versions were written for older IBAMR builds. The `triangle.msh` in this folder was made from the course file with

```bash
python3 fix_orientation.py course_triangle.msh triangle.msh
```

It has the same 759 nodes and the same 1404 triangles; only the order of the last two corners of each triangle changed.

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

The run takes 8000 time steps and saves 81 frames. Positions measured from `output.ex2` (center = average of the 759 nodes, which starts at (0.168, 0.168); top corner = the node that starts at (0, 0.5)):

| Time | Center y | Top corner y | Notes |
|---|---|---|---|
| 0 | 0.168 | 0.500 | |
| 1.0 | 0.668 | 0.997 | top of the motion; the top corner is just below the top of the box (y = 1) |
| 2.0 | 0.168 | 0.500 | |
| 3.0 | −0.332 | 0.000 | released |
| 3.5 | −0.556 | −0.230 | still moving down: the fluid around it keeps moving |
| 4.0 | −0.740 | −0.432 | |

While it is tethered, every node stays within 0.011 of its target, less than one fine grid cell; the largest lag comes just after the target turns around at t = 1. After it is released the triangle also starts to turn: at t = 4 its right corner (0.526, −0.848) is higher than its lower-left corner (0.023, −0.924).

IBAMR 0.16.0 and 0.19.0 give identical results. The mesh made with `triangle.geo` gives the same numbers to 3 decimals.

The output folder `viz_IB2d/` holds

- `dumps.visit`: the fluid on the adaptive grid (velocity `U`, pressure `P`, vorticity `Omega`, force `F`, `Div U`);
- `output.ex2`: the triangle, as an ExodusII file with the nodal variables `dX_0`, `dX_1` (displacement), `X_0`, `X_1` (position), `F_0`, `F_1` (force) and `U_0`, `U_1` (velocity).

The output folder is 32 MB with IBAMR 0.19.0 and 45 MB with 0.16.0, which also writes the velocity and force components separately (`U_x`, `U_y`, `F_x`, `F_y`).

## Looking at it in VisIt

1. Open `viz_IB2d/dumps.visit`, then choose **Add → Pseudocolor → Omega** and **Draw**.
2. Open `viz_IB2d/output.ex2`, choose **Add → Mesh**, and pick the triangle's mesh.
3. The mesh is drawn in its starting position. To move it with the triangle, make a vector expression in **Controls → Expressions**: name `dX`, type *Vector*, definition `{dX_0, dX_1}`. Then add **Operators → Transforms → Displace** to the mesh plot and set its variable to `dX`.

Chapter 28 covers finite element output in more detail.

## Things to try

- Run with the mesh that `triangle.geo` makes (see "Making the mesh with gmsh"). The positions above agree to 3 decimals.
- Make the triangles twice as large: set `lc = 0.0312` in `triangle.geo` and make a new mesh. gmsh then makes 213 nodes and 367 triangles. The corners end up within 0.005 of where they are with the default mesh at t = 4.
- Make your own shape: copy `triangle.geo`, change the points and lines, and check the two settings above (not tested here).

## History

The UNC version (2016–2018) went with the lecture "Make your own mesh and move it!". The University of Arizona version (2022–2024) fixed the `AutoPtr` error and made restarted runs append to the ExodusII file. The changes for current IBAMR:

- A CMake build replaces the Makefile.
- `main.cpp` starts IBAMR with `IBTKInit`, no longer includes the old configuration headers, and uses `libMesh::Order`.
- The mesh file, tether stiffness and shear modulus can be set in `input2d`.
- Restarted runs now save and reload the triangle's finite element data and append to `output.ex2`, as IBAMR's own examples do. Unlike those examples, only processor 0 reopens `output.ex2`: when every process reopens it, a restart on more than one process leaves a file that can no longer be read (tested with IBAMR 0.16.0 and 0.19.0).
- `triangle.msh` had clockwise triangles, which IBAMR 0.11.0 and newer reject. Their node order is fixed.
- `triangle.geo` is new. The course folder had no `.geo` file.
- The input file has Unix line endings, so it no longer needs `//` at the end of every line. The keys `use_IB_spread_operator` and `use_IB_interp_operator`, which IBAMR no longer reads, are removed.

The original files are in `examples/legacy/`.
