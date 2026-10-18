# Planktos: agents in this series' flows

Chapters 34 and 35 of *Using IB Software*. Planktos (W. C. Strickland et al., <https://github.com/mountaindust/Planktos>,
GPL-3.0; Strickland, Battista, Hamlet and Miller, *Bull. Math. Biol.* 84 (2022) 72) moves agents (point organisms that
do not change the flow) through a flow computed beforehand. These scripts run it on flows of this series: the IB2d
starfish channel of chapter 4f and the IBFE flow tank of chapter 22. Each one starts with a docstring that says how to
run it and what it writes.

| file | what it does | chapters |
|---|---|---|
| `brinkman_first.py [out]` | chapter 35's first run in one script: an environment, Planktos's analytic Brinkman-layer flow, a swarm and its properties, 24 s of drift-diffusion, the plots, `save_data`, CSV and VTK output (and a movie if `ffmpeg` is on the PATH; not tried here, where there is none); no input data | 35 |
| `starfish_env.py` | `load(run)`: the starfish run (`viz_IB2d/u.####.vtk`, `starfish_channel.vertex`, `input2d`) as an `Environment`, with the starfish (not the walls) as a closed immersed mesh; imported by the four scripts below | 34, 35 |
| `starfish_kde.py <run> [out]` | 1000 agents released upstream of the starfish, carried by the flow with a little diffusion; Planktos's plot with the vorticity and the kernel density estimates in the margins | 34, 35 |
| `starfish_capture.py <run> [out]` | a capture experiment: agents within 1.5 cm of the outline, sticky collisions and a `captured` state (chapter 35's `CaptureSwarm`); the captured share against time with the flow and in still water | 34, 35 |
| `starfish_ftle.py <run> [out] [nx ny]` | `calculate_FTLE` over the pulse for tracers and for swimmers (the fluid plus 0.1 m/s in x): two maps of the largest forward-time exponent | 34, 35 |
| `starfish_vicsek.py <run> [out]` | Vicsek alignment (chapter 35's capstone rule, wrapped on the periodic axis only) in still water and in the flow; the polarization against time and the headings at the end | 34, 35 |
| `ibamr_plate.py <IBAMR_db_000.vtk or folder> [out]` | an IBAMR run in Planktos: IBFE/10's last dump as a steady flow (through `examples/analysis/resample_export.py` and `vtk_for_planktos.py`), the plate as an STL box, a sheet of agents carried past it | 33, 35 |

Licences: Planktos is GPL-3.0. `starfish_capture.py` follows the pattern of one of its examples and is GPL-3.0 too
(it says so); the other scripts are this repository's code (`LICENSE-CODE`, BSD 3-Clause).

`<run>` is the folder of chapter 4f's starfish run (`examples/IB2d/Mesh_From_SVG/Starfish_Channel`, run with pyIB2d):
it holds `input2d`, `starfish_channel.vertex` and `viz_IB2d/`. For `ibamr_plate.py`, first (chapter 33)

```bash
visit -nowin -cli -s resample_export.py -- viz_IB3d/dumps.visit U plate_visit nx=97 ny=49 nz=49 x0=-4 x1=8 y0=-3 y1=3 z0=-3 z1=3 states=20 format=binary
```

```bash
python vtk_for_planktos.py plate_visit plate_planktos
```

then `python ibamr_plate.py plate_planktos/IBAMR_db_000.vtk`.

## What they gave (October 2026: Planktos 1.0.3 from git a1c2128, Python 3.12 in Anaconda on Windows, a desktop PC)

| script | time | result |
|---|---|---|
| `brinkman_first.py` | 4 s | 110 of 200 agents still in the box after 24 s (the default `zero` boundaries removed the others: 88 through x = 20, 2 through the y boundaries); 241 VTK files, one per stored time |
| `starfish_kde.py` | 40 s | 380 steps of 1 ms; the agents moved about 3 cm downstream and split around the starfish (two peaks in y) |
| `starfish_capture.py` | 90 s | 1500 agents: 4.7 % captured by t = 0.38 s with the flow, none in still water (D = 1e-6 m^2/s) |
| `starfish_ftle.py` | 5 min | 256 x 64 starting points: tracers 140 s, swimmers 139 s; exponents up to 26 1/s in the jet's vortex rings by the forcing box (29 1/s on the periodic seam x = 0 = 1 at the box's top and bottom edges); ridges around the starfish |
| `starfish_vicsek.py` | 25 s | polarization in the flow 0.88 after the first step and 0.98 by t = 0.02 s (the stream dominates the neighbours' mean velocity); briefly below 0.2 (0.16 at t = 0.196 s) as the stream near the agents dies away (its mean u from 0.31 m/s at t = 0.08 s to 0 at t = 0.18 s), 0.68 at the end; in still water it grows from 0.17 to about 0.6 (0.55 at the end) |
| `ibamr_plate.py` | 40 s | 900 agents, 600 steps of 0.1 s; 86 agent-steps touched the plate; the sheet bends round it, the agents behind it lag, and 18 still sit against its upstream face |

## Things these scripts work around (Planktos 1.0.3 and pyIB2d, October 2026)

- **pyIB2d writes the first dump's velocity transposed.** `IBM_Driver.py` writes dump 0 with `U, V` and every later
  dump with `U.T, V.T`, so `u.0000.vtk` and `uX.0000.vtk` say `DIMENSIONS 128 512 1` for a 512 x 128 grid
  (`Omega.0000.vtk` and `uMag.0000.vtk` are right). IB2d's open issue #12 reports the same for the MATLAB version.
  Planktos's `read_IB2d_fluid_data` then stops ("all the input array dimensions ... must match"). The fluid is at rest
  in dump 0: read from dump 1 (`d_start=1`); Planktos's clock then starts at the run's 0.02 s.
- **A static `.vertex` file and `method='adjacent'`:** `periodic=True` is ignored (only the moving-mesh branch reads it),
  so the outline stays open (404 segments for 405 points). Close it with `add_idx_list=[(404, 0)]`: the indices are
  used from 0, although the docstring says from 1 (`(405, 1)` gives `IndexError`).
- **`method='proximity'`** joins points closer than 0.501 grid cells; the starfish's points are 0.503 cells apart, so it
  joined 13 segments and left 381 points unconnected. With `res_factor=0.6` it closed the outline but added 37 chords.
- **The channel walls** cross the periodic x boundary, which Planktos does not handle: only the starfish is loaded, and
  noflux box edges stand in for the walls.
- **`rho` and `mu`** go to the constructor: the `nu` and `rho` setters compute `mu = nu/rho` in 1.0.3 (chapter 35).
- **`plot_all(fluid="vort")` on a static flow** stops in 1.0.3 ("ValueError: not enough values to unpack (expected 2,
  got 1)", before a frame is drawn): `brinkman_first.py` animates its Brinkman layer with `fluid="quiver"`.
- VisIt's VTK export keeps the vector as a field array; `vtk_for_planktos.py` makes it the active vector, which
  `read_IBAMR3d_vtk_data` needs. VTK may print "Could not read dimensions or extents from the file" while reading these
  binary files' headers; the grids come out whole (the scripts print their sizes).
