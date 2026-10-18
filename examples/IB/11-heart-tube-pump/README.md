# IB/11 Heart-tube pump

An elastic tube in a closed loop (a "racetrack") inside a rigid pericardium, with passive marker points in the fluid, is driven five ways: a dynamic suction pump by moving target points or by an applied force, and peristalsis by a travelling applied force, a travelling stiffness, or a travelling wave of target points. The applied forces are spring force functions of your own, registered under force function indices 1 and 2. This example goes with the custom-spring-forces chapter of *Using IB Software* (chapter 9b) and is the starting point of the two-point valveless pump of chapter 36.

| | |
|---|---|
| Method | Immersed boundary (IB): springs, beams, target points, custom spring force functions, five actuation modes |
| Dimension | 2D |
| Chapters | 9b (custom spring forces and active pumping), 9a (target points and update functions), 6 (structure files), 11 (forces), 36 (two-point pump) |
| Run time | about 55 to 65 minutes per mode on 3 cores (0.08 s per step on a laptop; 40,000 steps); the five modes can run at the same time |
| Tested with | IBAMR 0.16.0 and 0.19.0 (autoibamr; GCC 13.3, Open MPI 4.1.6, Ubuntu 24.04) |
| Upstream relative | `examples/IB/explicit/ex3` in IBAMR registers its own spring force function (under index 0, replacing the default) |

## Files

| File | What it is |
|---|---|
| `main.cpp` | The IBAMR program: the program of IB/07 plus the force function `applied_force` (and its derivative), registered under force function indices 1 and 2, and a switch on the input key `ACTUATION` that calls one of the five driving functions before each time step. It also writes the positions and forces every few steps. |
| `pump_geometry.h` | The few numbers of the generator that the driving functions need (tube diameter, wall positions, point spacing, squeeze amplitude, wavelength). Keep them equal to the generator's. |
| `update_target_point_positions.cpp`, `.h` | Mode `TARGET_VP`: moves the actuator's target points in and out with a sine of the time |
| `update_springs_vp_aforce.cpp`, `.h` | Mode `FORCE_VP`: writes the phase of the applied force, ½(1 + sin(2πft − π/2)), into the second parameter of every spring of `vp_aforce_512` |
| `update_springs_peri_aforce.cpp`, `.h` | Mode `FORCE_PERI`: writes a travelling Gaussian packet, exp(−(x − x_c)²/w²), tapered at the ends of the piece, into the second parameter of every spring of `peri_aforce_512` |
| `update_springs_peri_kwave.cpp`, `.h` | Mode `STIFFNESS_PERI`: writes the same travelling packet as a stiffness into the first parameter of every (default, Hookean) spring of `peri_kwave_512` |
| `update_target_point_positions_peri.cpp`, `.h` | Mode `TARGET_PERI`: moves the target points of `pperi_top_512` and `pperi_bot_512` as a travelling sine wave, tapered at the ends of the piece |
| `input2d` | Physical, grid, solver and output settings for mode `TARGET_VP`, and the packet's width and speed (`PERI_WIDTH`, `PERI_SPEED`) for the peristaltic modes. `structure_names` lists the driving structures first. |
| `input2d.force-vp`, `input2d.force-peri`, `input2d.stiffness-peri`, `input2d.target-peri` | The same file for the other four modes: only `ACTUATION` and `structure_names` differ. `make_inputs.py` writes them from `input2d`. |
| `heart_tube_512.vertex`, `.spring`, `.beam`, `.target` | The elastic section of the tube: two straight walls of 430 points each (860), 858 springs, 856 beams, and 40 target points (the ten rigid points at each end of each wall) |
| `heart_tube_stiff_512.vertex`, `.spring`, `.beam`, `.target` | The same elastic section with beams ten times stiffer (EI = 0.1), used by mode `FORCE_PERI` (see "What you should see") |
| `heart_race_512.vertex`, `.target` | The rigid rest of the loop: 3436 target points |
| `heart_peri_512.vertex`, `.target` | The pericardium: a rigid box around the elastic section, 1066 target points |
| `markers_512.vertex` | 121 passive points inside the elastic section (11 columns of 11) that move with the fluid |
| `actuator_top_512`, `actuator_bot_512` (`.vertex`, `.target`) | Mode `TARGET_VP`: the 41 + 41 driven points of the actuator, a 4 cm piece of each wall centred a quarter of the way along the straight section |
| `vp_aforce_512.vertex`, `.spring` | Mode `FORCE_VP`: the same 82 points, with a "spring" from each top point to the bottom point under it carrying `Fmag_vp`, the phase and force function index 1 |
| `peri_aforce_512.vertex`, `.spring` | Mode `FORCE_PERI`: the middle 0.32 m of both walls (328 + 328 points) with springs across the tube carrying `Fmag`, the phase and force function index 2 |
| `peri_kwave_512.vertex`, `.spring` | Mode `STIFFNESS_PERI`: the same 656 points with ordinary springs (index 0) of stiffness 0 and rest length 0.05 m (half the diameter) |
| `pperi_top_512`, `pperi_bot_512` (`.vertex`, `.target`) | Mode `TARGET_PERI`: the middle 0.3 m of each wall (308 + 308 points), every point a target |
| `generate_mesh2d.m`, `generate_mesh2d.py` | MATLAB/Octave and Python scripts that write all 27 structure files. They write identical files (checked with Octave 8.4 and Python 3.12). |
| `make_inputs.py` | Writes the four other input files from `input2d` |
| `CMakeLists.txt` | Build instructions for CMake. It lists all six `.cpp` files. |
| `job.slurm` | Batch script for Puma |

The driven points of the actuators are copies of points of `heart_tube_512`: the actuator structures hold their own vertices at the same places, and the tube's points there are ordinary elastic points. In the target modes the actuator points are tethered to moving targets and drag the tube's wall through the fluid; in the force modes the "springs" of the driving structure pull its own points together, and those points carry the tube's wall with them because they sit on the same grid cells.

Point numbers start at 0 in each structure's files. IBAMR numbers the points of all structures together in the order of `structure_names`, which is why the driving structure is listed first in every input file: each update function asks for structure 0 (and 1) with `getLagrangianStructureIndexRange()`. The marker points have no springs, beams or targets and simply go with the flow.

## The physics

- **Domain:** 1 m by 1 m, periodic in both directions, with the loop well inside it.
- **Fluid:** density 1000 kg/m³ and viscosity 0.157 N s/m², set in the input from the Womersley number: `MU = 2πf ρ D² / (4 Wo²)` with `WO = 10`, `FRE = 1` Hz and `D = 0.1` m.
- **Grid:** 4 levels of adaptive refinement with ratio 4 and 8 cells on the coarsest level, so the finest grid has 512 cells across and Δx = 1/512 m ≈ 2 mm. Cells are tagged for refinement around the structures and where the vorticity exceeds 0.1 s⁻¹.
- **The loop:** a tube of diameter 0.1 m; the straight sections are 0.42 m long and the bends have inner radius 0.1 m, so the loop's centre lines are at y = ±0.15 m. The bottom straight section is the elastic part (springs, beams, and rigid ends); everything else is target points. The pericardium is a rigid box 0.2 m across around the elastic section. Points are ds = 1/1024 m apart, half a grid cell.
- **Springs:** stiffness K = 2 (tension per unit strain, chapter 6); the `.spring` file holds K/ds = 2048, rest length ds.
- **Beams:** bending stiffness EI = 10⁻²; the `.beam` file holds it divided by ds³, 1.07 × 10⁷.
- **Target points:** κ = 2; the `.target` files hold κ/ds = 2048.
- **Driving (suction modes):** the actuator is 0.04 m long, centred a quarter of the way along the straight section (at x ≈ −0.105 m). The targets move each wall in by `amp` = 0.8 × D/2 = 0.04 m at full squeeze, `squeeze(t) = (amp/2)(1 + sin(2πft − π/2))`, so the tube closes to 20 % of its diameter once per period. The applied force uses the same time course as its phase, with `Fmag_vp = 0.25` from the generator (the 2014 code's 4, "my best guess at a reasonable applied force", closes the tube; so do 2, 1 and 0.5; see below).
- **Driving (peristaltic modes):** `FORCE_PERI` sends a Gaussian packet of width `PERI_WIDTH` = 0.025 m along the 0.32 m piece at `PERI_SPEED` = 1.3 piece lengths per period, starting 15 % of a piece length before it, once per period, with its amplitude tapered to zero over 5 cm at each end of the piece; `STIFFNESS_PERI` sends the same packet as a stiffness, k_max = (K/10)/ds = 102.4 in file units, on springs of rest length 0.05 m (half the diameter); `TARGET_PERI` moves the walls of the 0.3 m piece as one sine wavelength travelling at f wavelengths per second, with the amplitude ramped up over the first half period and tapered to zero over 5 cm at each end of the piece.
- **Time:** two pumping periods (`END_TIME = 2.0`) at `DT = 5.0e-5` s, 40,000 steps, 51 dumps (t = 0 and every 800 steps).

The pump works without valves: the squeeze is not in the middle of the elastic section, so the fluid on the two sides of it meets different resistance (one side is closer to the stiff racetrack), and the tube's elastic waves travel differently each way. The net flow round the loop is Liebau's valveless pumping; chapter 36 studies it with two actuators.

## Build and run

On Puma, work inside an interactive session or a batch job, because the modules load only on compute nodes. On a laptop with autoibamr, skip the `module` line.

```bash
module load gnu13 openmpi5
source ~/autoibamr/configuration/enable.sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j 4
mpirun -np 4 ./build/main2d input2d                  # TARGET_VP
mpirun -np 4 ./build/main2d input2d.force-vp         # FORCE_VP
mpirun -np 4 ./build/main2d input2d.force-peri       # FORCE_PERI
mpirun -np 4 ./build/main2d input2d.stiffness-peri   # STIFFNESS_PERI
mpirun -np 4 ./build/main2d input2d.target-peri      # TARGET_PERI
```

Run each mode in its own folder (copy the structure files and the one input file there), or the output folders of one run overwrite the other's. On Puma, submit `job.slurm` with `sbatch job.slurm`; it takes the input file as its first argument.

The program has six source files. All must be listed in `CMakeLists.txt`; if one is missing, the link step fails with `undefined reference to update_...`.

The first line of the run log says which mode is running:

```
Heart-tube pump: ACTUATION = TARGET_VP, pumping frequency 1 Hz
```

An `ACTUATION` value that is not one of the five stops the program with `Unsupported ACTUATION`.

## What you should see

Every 800 steps the screen shows a line like

```
integral{F} = 0.976499 6.99228
```

That is the sum of all Lagrangian forces. For the force modes it is close to zero in the first steps (every applied force acts on a pair of points and cancels) and grows as the tube's own springs, beams and tethers respond; for the target modes it is the net tether force.

Measured from the saved positions (`tools/ch9b_figures.py` of the tutorial repository reads them; the markers' mean x position measures how far those 121 parcels drift along the elastic section, which is not always the direction of the net flow round the loop (below), and the smallest distance between the two walls measures the squeeze):

| Mode | Runs to | Markers' transport, period 1 / period 2 | Smallest opening, period 1 / period 2 | What happens |
|---|---|---|---|---|
| `TARGET_VP` | 2 s | −0.8 cm / −1.6 cm | 1.9 cm (t = 0.48 s) / 1.3 cm (t = 2.0 s) | the second minimum is beside the actuator, not in it: the reopening actuator sucks the neighbouring elastic wall in |
| `FORCE_VP` (`Fmag_vp` = 0.25) | 2 s | +1.1 cm / +1.0 cm | 5.0 cm (t = 1.0 s) / 1.5 cm (t = 1.76 s) | the squeeze lags the force by about half a period; the markers drift steadily the other way from `TARGET_VP`'s, although the net flow round the loop turns the same way (below) |
| `FORCE_PERI` (stiffer tube, `Fmag` = 1) | 2 s | +0.8 cm / −2.6 cm | 3.1 cm (t = 0.60 s) / 4.7 cm (t = 1.68 s) | runs, but sloshes: the fluid pushed ahead of each packet flows back when the packet leaves the piece |
| `STIFFNESS_PERI` | stops at 0.64 s | −1.3 cm by 0.64 s | walls within two cells from 0.56 s, crossed at 0.64 s | `Time step size change encountered` at the left end of the piece |
| `TARGET_PERI` | 2 s | +3.1 cm / +2.4 cm | 0.07 cm (t = 0.84 s) / 0.09 cm (t = 1.0 s) | the wave closes the tube and the targets pull it open again, every period |

Walls within two grid cells of each other (0.4 cm; the finest mesh width is 0.195 cm) share cells and stick, which is what "closes" means throughout. Transport is the change of the markers' mean x position over 0–1 s and over 1–2 s.

The figure `ch9b-pump-transport.png` in the chapter plots both against time, `ch9b-pump-shapes.png` shows the tube at its smallest opening in each mode, and `ch9b-pump-fmag.png` compares the applied-force modes at the 2014 and at smaller forces.

Things to notice:

- The target-driven modes squeeze as told (the targets close to 2 cm, 20 % of the diameter; the elastic walls between the tethered copies go a little further). The applied-force modes squeeze as far as `Fmag` can push against the tube and the fluid, and nothing tells them to stop: "depending on the choice of Fmag, the contraction may be too much or too little. You will need to tune it as you change parameters" (2014). With the 2014 code's `Fmag = 4` the suction pump's walls were within two grid cells at t = 0.24 s and the pinched section slid along the tube until the run aborted at 1.16 s; with 2 they closed at 0.32 s (aborted at 0.72 s); with 1 at 0.44 s (the run finishes, and the pinch slides 4 cm along the tube in the second period). Walls that meet share grid cells and stick: the IB method has no contact handling, so a closed pinch stays closed. With 0.5 the first squeeze reaches 1.0 cm at 0.80 s, the walls reopen to 3.6 cm, and the second squeeze closes them at 1.44 s, so the two periods cancel (+1.0 cm, then −1.0 cm). The shipped `Fmag_vp = 0.25` never closes the tube: its first squeeze bottoms out at 5.0 cm at t = 1.0 s, half a period after the force's peak (the soft tube and the viscous fluid lag the force), its second at 1.5 cm at 1.76 s, and it moves the markers +1.1 and +1.0 cm per period.
- The markers' drift has a direction, and it depends on the squeeze: with the actuator a quarter of the way along the elastic section, the target-driven suction pump moves the markers toward the nearer end (−2.4 cm in two periods) and the force-driven one, which squeezes less and later, moves them the other way (+2.1 cm); the target wave moves them with the wave (+5.6 cm); the force-driven wave on the stiffer tube moves them +0.8 cm in its first period and −2.6 cm in its second, so two periods do not settle its direction (see "Things to try"). The net flow round the loop is a different measurement. Integrated across the tube from the velocity (chapter 29, `examples/analysis/visit_queries.py`), both suction modes turn the loop clockwise, +x along the top straight and -x along the elastic section: over the two periods 1.6e-3 m^2/s per unit depth for `TARGET_VP` (a mean speed of 1.6 cm/s through the 10 cm tube; the flow reverses during each period) and 6.6-6.7e-4 m^2/s for `FORCE_VP` (0.67 cm/s; it never reverses), the same on the top straight and on both bends. So the force-driven markers drift against the net flow. Chapter 36 studies how the direction and the rate depend on where the actuator sits and on the frequency.
- The net flow per period is the figure of merit of a pump. Measure it from the velocity across the tube (chapter 29), not from the markers' drift or the squeeze.
- All three peristalsis modes, run with the 2014 parameters, stopped between t = 0.67 and 0.77 s with `Time step size change encountered` (the CFL limit, chapter 16): the 2014 target wave did not vanish at the ends of its piece, so the last driven point stood up to 4 cm from the first free point one spacing away and tore the wall; the 5 mm force packet with `Fmag = 4` closed the tube at the first pinch and the walls crossed; the 5 mm stiffness packet with a 2 cm rest length overshot to 4 mm and stuck. The shipped version tapers the target wave to zero over 5 cm at each end of its piece (`TARGET_PERI` then runs two periods), uses the lecture's 25 mm packet, `Fmag = 1` and a 5 cm rest length, and runs the applied-force wave on a tube ten times stiffer in bending (`heart_tube_stiff_512`, with `DT = 2.5e-5`): with the 2014 tube the fluid pushed ahead of the packet piles up in a bulge and the slack tube behind the packet collapses into contact, whatever the force (tapering the packet was tried and does not help). With the shipped settings the force-driven wave runs two periods without closing (smallest openings 3.1 and 4.7 cm) but is not yet a pump: the markers go +0.8 cm in the first period and −2.6 cm in the second, the fluid pushed ahead of each packet flowing back when the packet leaves the piece. The stiffness wave, with the 25 mm packet and the 5 cm rest length, still closes the tube at the left end of its piece (walls within two cells at 0.56 s, crossed at 0.64 s) and stops with `Time step size change encountered`; it ships as it is, as the mode the 2014 code actually ran, with the stop reported here and in the chapter.

The output folders:

- `viz_IB2d/dumps.visit` holds the fluid data on the adaptive grid: velocity `U`, pressure `P`, vorticity `Omega` and `Div_U` (51 frames).
- `viz_IB2d/lag_data.visit` holds every structure as `<name>_vertices` (its points), and a structure with springs also as `<name>_mesh` (the points joined by the springs): `heart_tube_512_mesh`, `markers_512_vertices`, ....
- `hier_data_IB2d/X.NNNNN` and `F.NNNNN` are the points' positions and forces as plain-text PETSc vectors, with x and y alternating, in the order of `structure_names`. Chapter 11 reads them in MATLAB and Python.
- `IB2d.log` is the log file.

## Looking at it in VisIt

1. Open `viz_IB2d/dumps.visit`, then choose **Add → Pseudocolor → P** and **Draw**. Step through the frames: the pressure rises ahead of the squeeze and falls behind it.
2. Open `viz_IB2d/lag_data.visit` as a second database, then **Add → Mesh → heart_tube_512_mesh**, and again for `markers_512_vertices` (and `heart_race_512_vertices`, `heart_peri_512_vertices` for the whole loop), and **Draw**. The markers show where those 121 parcels have gone (not the net flow: chapter 29).
3. A **Vector** plot of `U`, or **Add → Pseudocolor → Omega**, shows the jets leaving the squeeze in both directions and the net drift round the loop.

IBAMR 0.19 writes the velocity only as the vector `U`. Older versions also wrote `U_x` and `U_y`.

## Things to try

- Find the `Fmag` at which `FORCE_VP` gives the same squeeze as `TARGET_VP` (change `Fmag_vp` in the generator and rewrite the structure files, or edit the third column of `vp_aforce_512.spring`). Compare the net flow per period (chapter 29) and the markers' drift.
- `FORCE_PERI` on the stiffer tube does not pump yet. Raise `Fmag` in the generator (2 and 4 on `heart_tube_stiff_512` have not been run) and run four periods (`END_TIME = 4.0`) to see whether the transport settles into a direction; then try the 2014 tube with a stiffer pericardium-side support, or a shorter packet with a smaller force.
- Change the Womersley number `WO` (the viscosity follows) or the frequency `FRE` in the input file; nothing else needs editing, since the update functions take the frequency from the input.
- Move the actuator along the tube with `Ca` in the generator (0.25 of the straight section's length as shipped), or widen it with `La`. The net flow changes sign when the actuator crosses the middle.
- Remove the pericardium or the racetrack: delete them from `structure_names` (and their sub-blocks). Without the racetrack the tube is open at both ends into the periodic box.
- Run the course's 10 s (`END_TIME = 10.0`) to see the flow settle into a periodic state.
- Make the walls stiffer or floppier with `kappa_spring` and `kappa_beam` in the generator, and watch what that does to the squeeze the applied force achieves.

## History

This example is the lab's 2014 `Forced-tube-pump` code (UNC, the lecture *Designing your own spring force function: examples for peristalsis and dynamic suction pumping*, June 2014), which selected its actuation mode by commenting calls in and out of `main.C`. The changes for current IBAMR and for the tutorial:

- A CMake build replaces the Makefile, and the `.C` files became `.cpp`.
- `main.cpp` starts IBAMR with `IBTKInit` (the program of IB/07) and reads the actuation mode (`ACTUATION`) and the pumping frequency (`FRE`) from the input file. The 2014 code repeated the frequency and the geometry as static constants in every update file; they are now in the input file and in `pump_geometry.h`.
- One force function, `applied_force` (tension = `Fmag` × phase, both from the spring's parameters), is registered under indices 1 and 2. The 2014 code had two identical functions, `vp_spring_force` and `peri_spring_force`; the lecture's slides registered index 2 with the VP function, which was harmless for the same reason.
- The 2014 code's peristaltic force had an ad-hoc penalty term, `F*(phase - 1/(R*512/4)^2)`, meant to stop the walls from meeting. It is not shipped; the lecture's clean `F*phase` is, and the stiffness-wave version the 2014 code actually ran (`update_springs_peri_aforce.C` writing a Gaussian stiffness into the default springs) is shipped as its own mode, `STIFFNESS_PERI`.
- The lecture's Gaussian-wave loop used an undefined variable `c` (it meant the wave speed) and added the packets of all earlier pulses, which had long left the piece; one packet per period is the same thing and is what the code does. The width and speed are input keys (`PERI_WIDTH`, `PERI_SPEED`); shipped are the lecture's 25 mm width and the 2014 code's speed of 1.3 piece lengths per period (the code's 5 mm packet closed the tube; the lecture's slides had 0.025 m and 1.0).
- The `.spring` files of the force modes reuse the rest-length column for the phase; this is now documented in the generator and in the update functions.
- The time step is 5.0e-5 s instead of 1.0e-5 s (2.5e-5 s for mode `FORCE_PERI` on its stiffer tube), and the run stops at 2 s instead of 10 s.
- `generate_mesh2d.m` is the 2014 generator with a few edits (it writes `peri_aforce_512.spring` with `Fmag`, phase and index 2, as the lecture describes, `peri_kwave_512.*` for the stiffness-wave mode and `heart_tube_stiff_512.*` for the force-driven wave; the actuator's force is `Fmag_vp`; `percont` is 0.5 and `Fmag` 1 instead of 0.8 and 4); `generate_mesh2d.py` is new. Both write identical files (27).
- The 2015 public-folder example `14-YourOwnForceEx` (a sinusoidal force `F*sin(2πft)` on a "muscle" structure, with `update_springs_freq.C`) shipped without input or structure files; its force function is the `FORCE_VP` mode of this example.

The original files are in `examples/legacy/`.
