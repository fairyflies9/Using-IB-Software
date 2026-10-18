# Starfish_Channel (pyIB2d): IB2d's MeshmerizeMe starfish, in Python

Chapter 4f of *Using IB Software*. A port of `matIB2d/Examples/Example_Meshmerize_Me/Flow_Around_Starfish` (MATLAB,
`1024 x 256`) to Python IB2d at half the resolution, with the geometry made from the example's SVG by
`../svg_to_vertex.py`. (The example of the MeshmerizeMe paper, Senter et al. 2021, section 3.3, is the neighbouring
`Starfish` folder: a 2 Hz sine, `uMax = 500`, `w = 0.23`, springs as well as targets. `Flow_Around_Starfish`, ported
here, pulses at 5 Hz with rests.)

| file | what |
|---|---|
| `make_starfish_channel.py path/to/starfish_final.svg` | reads `input2d`; samples the starfish outline at `ds = Lx/(2 Nx)`; sizes it to 0.0803 and centres its bounding box at (0.3125, 0.125) (the MATLAB script centres the mean of its
points there, so this starfish sits 0.0025 higher); adds walls at `y = 0.01` and `0.24` across the box, `ds` apart (the MATLAB example has them `2 ds` apart); writes `starfish_channel.vertex` and `.target` (0-based; target stiffness `2.5e5` on the starfish, `2e7` on the walls, as in MATLAB) |
| `please_Compute_External_Forcing.py` | the MATLAB forcing, ported line for line: in `0.04 <= x <= 0.06`, `0.02 <= y <= 0.22` a penalty `-k (u - u_target)`, `k = 1e4`, towards a parabolic `u_x` with `Umax = 2500`, `w = 0.25`, `sin(2 pi 5 t)` during a 0.2 s pulse and zero during the next 0.2 s (centre-line target `39 sin(10 pi t)`) |
| `input2d` | `512 x 128` on `[0, 1] x [0, 0.25]`, `rho = 1000`, `mu = 0.1`, `dt = 5e-5`, `T = 0.4` (one pulse and one rest), a dump every 400 steps |
| `main2d.py` | the run script (from IB2d's `Turek_Hron` example) |

## Run it

From `pyIB2d/Examples/Starfish_Channel/` of an IB2d clone, with `svg_to_vertex.py` one folder up
(`pyIB2d/Examples/svg_to_vertex.py`):

```bash
python3 make_starfish_channel.py ../../../matIB2d/Examples/Example_Meshmerize_Me/Flow_Around_Starfish/starfish_final.svg
```

```bash
python3 main2d.py
```

The SVG is not copied into this repository: it is part of IB2d (GPL-3.0) and was traced from a NOAA photograph
(J. P. McVey, `Reef0297.jpg`, the paper's reference 47). `main2d.py` (IB2d's file, unchanged) and
`please_Compute_External_Forcing.py` (a port of IB2d's MATLAB file) are GPL-3.0 too, inside this repository whose own
code is under `LICENSE-CODE`; each says so in its header.

## What it gave (October 2026, a desktop PC under WSL)

See the chapter for the pictures. The starfish got 405 points (chords 1.006 ds, the closing one 1.13); the run took
8000 steps in 223 s. The penalty force does not make the fluid follow its target: the centre-line speed
in the forcing box peaks near 1.2 where the target is 39. On its own the penalty would relax a parcel in
`rho/k = 0.1 s` (half the pulse) and reach about 16; but the fluid is incompressible, so between the walls the flux is the
same at every x and the 0.02 x 0.2 box has to drive the whole 1 x 0.23 channel: the time scale is
`rho A_channel / (k A_box)`, about 6 s, which predicts a mean speed of 0.32 at t = 0.1 (the run: 0.31); the box's centre
line reaches 1.2 with the fluid next to the walls flowing back beside it. With the paper's `L = 0.08` the Reynolds
number `rho L U / mu` is about 710 with the largest `|u_x|` near the starfish (0.89) and 250 with the flow arriving at it
(0.31); the paper's 800 (`V = 1 m/s`) is for its 2 Hz run in `Starfish`.

Python IB2d writes dump 0 of `u`, `uX` and `uY` with the grid transposed (`DIMENSIONS Ny Nx`); later dumps are
`Nx Ny` (`IBM_Driver.py`, the initial `print_vtk_files` call passes `U`, `V` where the loop passes `U.T`, `V.T`). That is
with the `vtk` package, as in this run; without it, pyIB2d's plain-text writer gets `u.*.vtk` the other way round.
