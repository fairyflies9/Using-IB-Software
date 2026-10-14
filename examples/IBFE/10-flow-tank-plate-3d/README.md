# IBFE/10 Flow tank with a plate (3D)

A thin elastic plate stands across a uniform stream in a 3D flow tank. A band across the middle of the plate is held in place by a tether (target) force, and the parts above and below the band are free to bend with the flow. This is the 3D IBFE example in *Using IB Software*. It reads a tetrahedral mesh made with gmsh, uses a compressible neo-Hookean material, applies a tether force to part of the body, and writes the plate's motion to an ExodusII file.

| | |
|---|---|
| Method | Immersed boundary finite element (IBFE) |
| Dimension | 3D |
| Chapters | 22 (3D flow past objects; the flow tank), 18 (making meshes with gmsh), 19 (stress and body forces), 27 and 28 (VisIt in 3D and finite element data) |
| Run time | about 30 to 50 minutes on 4 cores (0.3 s per step on a quiet laptop, up to 0.6 s with other jobs running; 5000 steps) |
| Tested with | IBAMR 0.16.0 and 0.19.0 (autoibamr; GCC 13.3, Open MPI 4.1.6, Ubuntu 24.04) |
| Upstream relatives | `examples/IBFE/explicit/ex4` (compressible neo-Hookean solid with a β log J term, 2D and 3D) and `ex5` (a body held in a flow by penalty springs, with drag output) in IBAMR |

## Files

| File | What it is |
|---|---|
| `main.cpp` | The IBAMR program: the tether force, the stress functions, the optional coordinate mapping, and `output_data`, which computes the tether force |
| `input3d` | Physical, grid, solver and output settings, the boundary conditions, and the options `TRANSLATE_X` and `TWO_MATERIALS` |
| `plate2.msh` | The plate's mesh: 3,386 nodes and 11,481 tetrahedra in gmsh's MSH 2.2 text format, with one physical volume named `plate2` |
| `CMakeLists.txt` | Build instructions for CMake |
| `job.slurm` | Batch script for Puma |

## The physics

- **Tank:** 32 by 16 by 16, from x = −8 to 24 and from −8 to 8 in y and z. It is not periodic.
- **Grid:** 3 levels with refinement ratio 4: 32 × 16 × 16 cells on the coarsest level (Δx = 1) and Δx = 1/16 = 0.0625 on the finest level, which covers the plate and the flow near it.
- **Fluid:** density 1 and viscosity 0.01. The input file writes the viscosity as `MU = 1/Re` with `Re = 100`, which is the Reynolds number for a speed of 1 and a length of 1.
- **Stream:** on all six sides of the tank the velocity is (U tanh(2t), 0, 0) with U = 0.1, so the water starts at rest and reaches 96% of U by t = 1. With the plate's width D = 2 as the length, the Reynolds number is ρUD/μ = 20.
- **Plate:** 0.125 thick (0 < x < 0.125) and 2 by 2 (−1 < y < 1, −1 < z < 1). It is a compressible neo-Hookean solid. Its first Piola–Kirchhoff stress is μ_s**F** + (−μ_s + β ln J)**F**⁻ᵀ, with J = det **F**, shear modulus μ_s = 0.538 and β = 0.404 (`MU_STEM` and `BETA_STEM`). At **F** = **I** the stress is zero.
- **Tether:** the band |z| < 0.1 across the middle of the plate (in the mesh's coordinates) is pulled toward its starting position with force κ(starting position − current position) per unit volume, with κ = 10⁵ (`KAPPA_S`). The rest of the plate is free, so its upper and lower parts act like two flaps.

**A note on `MU_STEM`.** The input file computes the material constants from Young's modulus E and Poisson's ratio ν = 0.3: μ = E/(2(1 + ν)) and β = Eν/((1 + ν)(1 − 2ν)). In the course version (kept here) the two μ lines use each other's E: `MU_STEM` uses `E_LEAF = 1.4` and `MU_LEAF` uses `E_STEM = 0.7`, while the β lines use their own E. So the plate has μ_s = 0.538 (E = 1.4) and β = 0.404 (E = 0.7), which together correspond to E ≈ 1.31 and ν ≈ 0.21. Whether the swap was intended is not known; the values are kept so the runs match the course's.

## Build and run

On Puma, work inside an interactive session or a batch job, because the modules load only on compute nodes. On a laptop with autoibamr, skip the `module` line.

```bash
module load gnu13 openmpi5
source ~/autoibamr/configuration/enable.sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j 4
mpirun -np 4 ./build/main3d input3d
```

On Puma, submit `job.slurm` with `sbatch job.slurm` instead.

## What you should see

The run takes 5000 time steps of 10⁻⁴ and saves 21 frames. Every 50 steps the screen shows a line like

```
tether force = -0.106699 0.00112701 0.00150725   J from 0.822529 to 1.72649
```

The three numbers after `tether force =` are the total tether force on the plate (x, y, z). Minus it is the force of the flow on the tethered band and, once the flaps have stopped bending, minus the drag on the whole plate. The same numbers go to `hier_data_IB3d/tether_force.txt`. `J from ... to ...` is the range of J = det **F** over the plate's quadrature points since the last line; J = 1 means no change of volume.

The stream speeds up as tanh(2t), reaching 0.076 by t = 0.5, and the force on the plate grows with it. Measured from the screen lines and from `output.ex2` (the free edges are the nodes at z = ±1 in the mesh file):

| Time | Tether force (x) | Top edge moved downstream | Bottom edge moved downstream | J range since the last line |
|---|---|---|---|---|
| 0.05 | −0.107 | | | 0.82 to 1.73 |
| 0.1 | −0.106 | 0.0011 | 0.0010 | 0.66 to 2.51 |
| 0.2 | −0.192 | 0.0040 | 0.0035 | 0.35 to 2.72 |
| 0.3 | −0.215 | 0.0076 | 0.0065 | |
| 0.4 | −0.239 | 0.0102 | 0.0085 | |
| 0.5 | −0.276 | 0.0116 | 0.0094 | 0.21 to 2.10 |

The two flaps bend downstream slowly (the plate is 2 wide, so a displacement of 0.01 at the edge is a small bend), the top flap a little more than the bottom one, and the tethered band stays within 3 × 10⁻⁵ of its place. A few nodes move much more, up to 0.05 by t = 0.5: they belong to the flat "sliver" tetrahedra described under "How the mesh was made", which are also where J strays far from 1 while the rest of the plate stays close to it. In the VisIt files the stream goes around the plate and a slow wake forms behind it.

The output (IBAMR 0.19.0):

- `viz_IB3d/dumps.visit`: 21 frames of the fluid (velocity `U`, pressure `P`, vorticity `Omega`, `Div_U` and the force density `F`), and `viz_IB3d/output.ex2`, the plate (7 MB); 95 MB in all. IBAMR 0.16.0 also writes the separate velocity and force components (`U_x`, ...), which makes its frames larger.
- `hier_data_IB3d/tether_force.txt`: the tether force at the 100 data steps.
- `restart_IB3d/`: restart files at the end of the run (10 MB).
- `IB3d.log`: the log file.

IBAMR 0.16.0 and 0.19.0 both run this input to the end and print the same final tether force to all six digits (−0.27576, 0.0357986, −0.0147232) and the same range of J.

## Looking at it in VisIt

1. Open `viz_IB3d/dumps.visit`, then choose **Add → Pseudocolor** with the expression `U[0]` (the x-velocity) and **Draw**.
2. Add **Operators → Slicing → Slice** and set its normal to the y-axis (0, 1, 0) through the origin. The slice is the x-z plane through the middle of the plate, where you can see the slow wake behind it.
3. Open `viz_IB3d/output.ex2`, choose **Add → Mesh** and pick the plate's mesh. It is drawn in its starting position.
4. To move it with the plate, make a vector expression in **Controls → Expressions**: name `dX`, type *Vector*, definition `{dX_0, dX_1, dX_2}`. Then add **Operators → Transforms → Displace** to the mesh plot and set its variable to `dX`. A **Pseudocolor** plot of `dX_0` on the plate shows how far each part has bent downstream.

`dumps.visit` also has the pressure `P`, the vorticity `Omega`, `Div_U` and the force density `F` that the plate puts on the fluid. `output.ex2` has, at each node, the displacement `dX_0`, `dX_1`, `dX_2`, the position `X_0`, `X_1`, `X_2`, the force `F_0`, `F_1`, `F_2` and the velocity `U_0`, `U_1`, `U_2`. Chapters 27 and 28 cover 3D plots and finite element data.

## Options from the 2017 version

Both options are off by default, which gives the course version's plate.

- `TRANSLATE_X` moves the plate and its tether along x at the start through an initial coordinate mapping (`registerInitialCoordinateMappingFunction` in `main.cpp`), so the mesh file does not change. The 2017 version used −7 in a tank from x = −16 to 16. In this tank, which runs from x = −8 to 24, `TRANSLATE_X = 4.0` puts the plate at x = 4, 12 units from the inflow side. Tested to t = 0.1 with IBAMR 0.19.0: the plate sits at x = 4 (its mean x in `output.ex2` is 4.06), and the tether force on it at t = 0.1 is the same as in the default run to four digits (−0.1064), so in this large tank the plate's position hardly matters. Note that the displacement `dX` in `output.ex2` then includes the 4-unit shift, because the mesh file still has the plate at x = 0.
- `TWO_MATERIALS = TRUE` gives the band |z| < `STEM_HALF_WIDTH` the stem material (μ = 0.538, β = 0.404) and the rest of the plate the softer leaf material (μ = 0.269, β = 0.808), as in the 2017 version, so the flaps bend more. Tested to t = 0.1 with IBAMR 0.19.0: the force on the plate at t = 0.1 is 9% smaller (−0.097 against −0.106), the flap edges have moved the same 0.001 downstream, and J ranges a little further (0.64 to 2.96). The softer flaps should bend more later in the run.

## Things to try

- Run the course's full 2 time units: set `END_TIME = 2.0`, or continue a finished run from its restart files with `mpirun -np 4 ./build/main3d input3d restart_IB3d 5000`. The stream reaches 96% of U by t = 1.
- Make the plate softer or stiffer by changing `E_STEM` (and read the note on `MU_STEM` above).
- Widen the tethered band with `TETHER_HALF_WIDTH`, or move it: the tether is applied where the reference z-coordinate is within `TETHER_HALF_WIDTH` of 0, in `target_force_function()` in `main.cpp`.
- Turn on the 2017 options above.
- Raise the Reynolds number with `Re`. A lower viscosity may need a smaller `DT`.

## How the mesh was made

`plate2.msh` was made in the gmsh window, as the chapter 22 slides show:

1. **Geometry → Elementary entities → Add → Point**: the four corners (0, 1, 1), (0, −1, 1), (0, −1, −1) and (0, 1, −1), each with the prescribed mesh element size 0.0625 (the finest grid spacing).
2. **Add → Straight Line** four times to join them, then **Add → Plane Surface** on the square.
3. **Translate → Extrude Surface** by 0.125 in x, which makes a plate about two elements thick, then **Add → Volume**.
4. **Physical Groups → Add → Volume**, named `plate2`. Saving only the physical group leaves out the lines and surfaces that libMesh would reject.
5. **Mesh → 3D**, then **File → Save Mesh** in MSH 2.2 text format (libMesh 1.7 reads MSH 2.2 and 4 text files, not binary ones).

The mesh has a few very flat ("sliver") tetrahedra: 80 of its 11,481 elements have a shape quality below 0.05 on a scale where a regular tetrahedron is 1, and 4 are below 0.01. They are the elements whose J changes most (see "What you should see"). Gmsh's **Mesh → Optimize 3D** can improve them.

## History

The flow tank was a UNC course example in 2017. That version moved the plate 7 units upstream with an initial coordinate mapping and gave the plate a stiffer "stem" band (|z| < 0.25) and softer "leaf" parts. Its lecture slides describe a tank from x = −16 to 16, but the input file shipped with it already has the tank at −8 < x < 24 (the same `x_lo = -0.5*L`, `x_up = 1.5*L` as here), so the shifted plate stood one unit from the inflow face. That may be why the translation seemed "not working" later. The UNC (2018) and University of Arizona (2020–2024) versions dropped the move (a 2020 slide says the feature "is not working as it used to in newer versions of IBAMR"), shifted the tank to −8 < x < 24 instead, and used the stem material everywhere. The changes for current IBAMR:

- A CMake build replaces the Makefile.
- `main.cpp` starts IBAMR with `IBTKInit`, no longer includes the old configuration headers, and uses `libMesh::Order`, `std::make_unique` and `std::abs`.
- `output_data` was empty (its body was commented out) but was called every time step (`data_dump_interval = 1`). It now computes the tether force, 100 times per run.
- The program printed "Max Jacobian 1" and "Min Jacobian 1" every step, because nothing ever updated those numbers. The range of J is now recorded in the stress function and printed with the tether force.
- The unused `s_dump`, `dx` and `ds` are removed, and the comment "Note x is actual position" names `X`.
- The 2017 options are back as input settings, tested with IBAMR 0.16.0 and 0.19.0: `TRANSLATE_X` (the coordinate mapping) and `TWO_MATERIALS` (stem and leaf). `TETHER_HALF_WIDTH` replaces the 0.1 written into the code.
- The obsolete input keys `use_IB_spread_operator` and `use_IB_interp_operator` (and `USE_IB_DELTA_FUNCTIONS`, which only fed them) are removed.
- `END_TIME` is 0.5 instead of 2.0, the output intervals scale with it, and restart files are written every 0.5 time units and at the end.
- The flow speed is the input variable `U_FLOW`; the course version wrote 0.1 into each of the six boundary conditions.
- The input file has Unix line endings, so it no longer needs `//` at the end of every line.

The course versions are in `examples/legacy/` (`UA-Examples/IBFE Examples/3-IBFE-Example_FlowTank-MidPlate` and `UNC-Examples/3-IBFE-Example_FlowTank-MidPlate`, which differ only in `AutoPtr`).
