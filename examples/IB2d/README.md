# examples/IB2d: the tutorial's own IB2d examples (Python)

Each folder is a pyIB2d example: copy it under `pyIB2d/Examples/` of an IB2d clone
(https://github.com/nickabattista/IB2d; its `IBM_Blackbox` is the solver, GPL-3.0), run the generator, then
`python3 main2d.py`. The structure files use pyIB2d's 0-based indices. Chapters 4a-4c of the tutorial explain them.

| folder | chapter | what |
|---|---|---|
| [Moving_Rubberband](Moving_Rubberband/) | 4c | a circle of target points dragged along a zig-zag (a port of IB2d's `Example_Moving_Rubberband`) |
| [Sawtooth](Sawtooth/) | 4c | the sawtooth pump: the top row of teeth driven by target points (a port of `Example_Sawtooth` with the grid as a parameter; it needs its full 1024 x 256 grid: see its README) |
| [Pulsing_Heart](Pulsing_Heart/) | 4c | a cartoon heart whose target points blend between two stored shapes (a port of `Example_Pulsing_Heart/32x32`; runs in half a minute) |
| [Stability_Lab](Stability_Lab/) | 4d | the shipped rubber band with the grid, stiffness, resting length and points per cell as arguments; `sweep.py` runs the chapter's groups (blow-ups, the stiffness/time-step map, grid and time-step refinement) and `analyze.py` measures the band's shape and enclosed area from the dumps |

Two fixes the shipped Python IB2d (clone of 2024-03-06) needs before some of its own examples run are on the
chapter 4a and 4b slides: the `nonInv_beams` key in `Rubberband_with_Beams/input2d` (should be `beams = 1`), and the
tracer call in `IBM_Driver.py` (the tracers examples stop at the first step).
