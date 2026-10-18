# Data-analysis protocol: <study name>

A written protocol, after Lindsay Waldrop's VisIt guide (chapter 29 of *Using IB Software*): detailed enough that
someone with a basic familiarity with VisIt could reproduce every output file without asking you.

## 1. Where the data were collected

For every box, point and line: its coordinates, the variable, and a labelled figure.

| name | kind | coordinates | variable | figure |
|---|---|---|---|---|
| | box (`xmin xmax ymin ymax [zmin zmax]`, Some or All) | | | |
| | point (`x y [z]`) | | | |
| | line (`x0 y0 [z0]` to `x1 y1 [z1]`, samples) | | | |

## 2. What was done with them

For each: the query (Average Value, Weighted Variable Sum, Min, Max, Pick through time, Lineout, ...), frame by frame
or through time, the time axis (time, cycle or index), and any expression used (write its definition).

## 3. Step by step, for each output file

1. Open ...
2. ...
3. Save as ... (`.curve`, `.csv`, `.png`), in ...

Or: the script that does it, its command line, and its version.

## 4. Checks

Every number checked a second way (for example a time query against a few single frames, an average against a flow
rate, one line against another), with the result.

## 5. Plots and code

Where the plotting code lives and how to run it.

---

## Example (IB/11, chapter 29)

| name | kind | coordinates | variable | figure |
|---|---|---|---|---|
| top stripe | box, Some | `0 0.01 0.10 0.20` | `U_x = U[0]` | `ch29-box.png` |
| centre of the top vessel | point | `0 0.15` | `U_x`, `speed = magnitude(U)` | `ch29-pick.png` |
| across the top vessel | line, 50 samples | `0 0.10` to `0 0.20` | `U_n` (velocity across the line) | `ch29-profiles.png` |

Done by `examples/analysis/visit_queries.py` (VisIt 3.5.0):
`visit -nowin -cli -s visit_queries.py -- viz_IB2d/dumps.visit out` (defaults as above). Checks: the box average
frame by frame against the flow rate across the line divided by the diameter (within 2.9 %); the query through time
against the same query frame by frame (8 % low: not used).
