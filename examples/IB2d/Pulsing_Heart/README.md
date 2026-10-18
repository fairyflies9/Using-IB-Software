# Pulsing_Heart (pyIB2d): target points that interpolate between two shapes

Chapter 4c of *Using IB Software*. A Python port of IB2d's `matIB2d/Examples/Example_Pulsing_Heart/32x32`: a cartoon
heart of 384 target points (stiffness 1e8) in a 1 x 1 box on a 32 x 32 grid, whose targets move from an expanded
shape (phase 1) to a contracted one (phase 2) in 0.025 and back in 0.025, with a smooth blend that starts and ends at
rest. Two beats in 0.1 (10 000 steps of 1e-5), a dump every 50 steps.

Files

| file | what |
|---|---|
| `heart.vertex`, `heart.target` | the MATLAB example's files with the target indices shifted to pyIB2d's 0-based numbering (384 points) |
| `All_Positions.txt` | the two phases, one line per point: x1 y1 x2 y2 (the MATLAB example's file, unchanged) |
| `update_Target_Point_Positions.py` | blends the phases as a function of time (the second style of chapter 4c: no drift); reads the phase file once |
| `input2d` | the MATLAB example's parameters without the trailing semicolons |
| `main2d.py` | the run script |

Run it

```bash
python3 main2d.py            # about half a minute on a desktop PC; 200 dumps
```

The generator `Pulsing_Heart.m` of the MATLAB example builds the two shapes and `All_Positions.txt`; it is not ported
(the files are data). To draw your own two phases, write them as this file's four columns and keep the point order.
