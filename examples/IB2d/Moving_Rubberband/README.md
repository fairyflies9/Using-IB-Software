# Moving_Rubberband (pyIB2d): target points dragged along a zig-zag

Chapter 4c of *Using IB Software*. A Python port of IB2d's `matIB2d/Examples/Example_Moving_Rubberband`: a circle of
64 target points (radius 0.2, centre (0.25, 0.25), stiffness 1e7) in a viscous fluid (mu = 10, rho = 1) on a 32 x 32
grid, dragged to the right during the first half of each period of 0.05 and to the left during the second, and
upward all the time (speed 20 sideways, 10 up). The structure's positions are never set directly: the targets move
and the points follow through the target force.

Files

| file | what |
|---|---|
| `Rubberband.py` | writes `rubberband.vertex` and `rubberband.target` (0-based indices, as pyIB2d reads them) and a check figure |
| `update_Target_Point_Positions.py` | called by the driver every step (`update_target = 1`): increments the targets' x and y |
| `input2d` | the parameters: 32 x 32, dt = 1e-4, Tfinal = 0.05, a dump every 5 steps, plotting off |
| `main2d.py` | the run script (reads `input2d`, calls `IBM_Driver`); the same as every pyIB2d example's |

Run it

```bash
# put this folder under pyIB2d/Examples/ of an IB2d clone (main2d.py finds ../../IBM_Blackbox there)
python3 Rubberband.py        # 64 points; ds = 0.63 dx
python3 main2d.py            # about 3 s on a desktop PC; 100 dumps in viz_IB2d/
```

What to look at: `lagsPts.NNNN.vtk` in VisIt (chapter 4b) or with `examples/analysis/read_vtk_legacy.py`: the band's
centre goes (0.25, 0.25) -> (0.75, 0.50) at t = 0.025 -> (0.26, 0.75) at the end. The geometry file reproduces the
MATLAB example's to round-off; the index base is the difference.

The motion is written as an increment per step (the MATLAB original's style). Chapter 4c's second style, the
targets as a function of time and of the original positions, is the one the sawtooth example uses; exercise 4 of
the chapter rewrites this function that way.
