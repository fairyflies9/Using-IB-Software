# Sawtooth (pyIB2d): a channel of teeth whose top row pumps

Chapter 4c of *Using IB Software*. A Python port of IB2d's `matIB2d/Examples/Example_Sawtooth` (Nick Battista's
sawtooth pump), with the grid, the number of teeth and the box as parameters. Two rows of twelve teeth (height and
width 0.63, gap 0.325) form a channel in a 12 x 3 box; every point is a target point; the top row's targets move down
and up as a sine (amplitude 0.1685, 2 cycles per unit time: the top row descends to the channel's centreline and halves
the gap of 0.325), the bottom row's stay.

Files

| file | what |
|---|---|
| `Sawtooth.py [Nx [Ny [teeth [Lx [Ly]]]]]` | writes `sawtooth.vertex` and `sawtooth.target` (0-based) and `sawtooth_geometry.png`; prints G and N_top; default 256 x 64 (1656 points); `1024 256` gives the original 6552 points, identical to the MATLAB file to 2e-15 |
| `update_Target_Point_Positions.py` | the top row's targets from the original positions (read once) as a function of time; N_top taken from the file, not typed in |
| `input2d` | the MATLAB example's fluid (mu = 2.234, rho = 1000) on 256 x 64, dt = 2.5e-5, Tfinal = 0.5 (one cycle), a dump every 400 steps |
| `main2d.py` | the run script, as in every pyIB2d example |

Run it

```bash
python3 Sawtooth.py 1024 256   # the original geometry; edit input2d to 1024 x 256 as well
python3 main2d.py              # with input2d at 1024 x 256 and Tfinal = 10, as the MATLAB example: 400 000 steps, 20 cycles, hours
```

**This example needs its full grid.** The MATLAB example tethers its points with k_target = 1e11 at 1024 x 256
and runs (its folder holds an analysis of its first three cycles). On the coarser grids tried on a desktop PC in October 2026 every run failed
with NaN positions (an IndexError in the delta-function indices is how Python reports it) before one cycle was done:

| grid | k_target | dt | stroke a | fails at t |
|---|---|---|---|---|
| 256 x 64 | 1e11 | 2.5e-5 | 0.337 | 0.02 |
| 256 x 64 | 1e9 | 2.5e-5 | 0.337 | 0.03 |
| 256 x 64 | 1e8 | 2.5e-5 and 1e-5 | 0.337 | 0.065 / 0.068 |
| 256 x 64 | 1e7 | 2.5e-5 | 0.337 | 0.12 (and the wall lags its targets by two cells) |
| 256 x 64 | 1e7 | 2.5e-5 | 0.25 / 0.30 | 0.15 / 0.13 |
| 384 x 192, 4 teeth, 4 x 2 box | 1e11 / 1e10 | 2.5e-5 | 0.337 | 0.22 / 0.02 |

The run that reaches a tenth of a second (256 x 64, 1e7) is what chapter 4c shows; the chapter's working
low-resolution pump is the `Pulsing_Heart` example next door, and chapter 4d takes the stiffness, grid and time-step
question up as a measurement. `Sawtooth.py` keeps the MATLAB stiffness (1e11) as its default so that it reproduces the
original files; set `k_Target` at the top of the file for an experiment.

The MATLAB `input2d` carries trailing semicolons on its `save_*` lines, which the Python parser rejects; this
`input2d` has none.
