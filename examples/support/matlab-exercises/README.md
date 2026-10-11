# MATLAB exercises, with Python versions

The small MATLAB exercises from the course (the originals are in [`originals/MATLAB codes/`](../../../originals/MATLAB%20codes/)), each with a Python version that does the same thing.

| MATLAB | Python | What it does |
|---|---|---|
| `heat_equation.m` | `heat_equation.py N T` | Solves the heat equation u_t = u_xx on 0 < x < 1 with an explicit finite-difference scheme and compares with the exact solution at t = 0.1. Shows that the scheme needs r = dt/dx² ≤ 1/2. |
| `stiff_ode_example.m` | `stiff_ode_example.py DT TFINAL` | Euler's method for the stiff equation y' = −15y. Shows smooth decay (dt < 1/15), sign oscillation (1/15 < dt < 2/15) and instability (dt > 2/15). |
| `test_IB2d_IBAMR_Geometry.m` | `test_ib_geometry.py [NAME] [--ibamr]` | Plots a structure's points with their index numbers, then its spring connections. Use it to check a `.vertex` and `.spring` pair before running a simulation. IB2d numbers points from 1 and IBAMR from 0 (`flag_IBAMR` in MATLAB, `--ibamr` in Python). |
| `read_Vertex_Points_and_Plot_Them.m` | `read_vertex_points_and_plot_them.py NAME` | Reads `NAME.vertex` and plots the points. |
| `rubberband.vertex`, `rubberband.spring` | | A 64-point IB2d rubber band to try them on |

## Running them

In MATLAB or Octave, from this folder: `heat_equation(19,100)`, `stiff_ode_example(0.05,1)`, `test_IB2d_IBAMR_Geometry`, `read_Vertex_Points_and_Plot_Them('rubberband')`.

In Python (with NumPy and Matplotlib), from this folder:

```bash
python3 heat_equation.py 19 100
```

```bash
python3 stiff_ode_example.py 0.1 1
```

```bash
python3 test_ib_geometry.py rubberband
```

The Python versions save their plots as PNG files, so they also work on a cluster without a display. Add `--show` to open the plots in a window.

## Changes from the course versions

- `heat_equation.m`: the comment gave the initial condition as sin(3πx); the code, and the exact solution it plots, use sin(2πx). The comment is corrected.
- `stiff_ode_example.m`: `zeros(N)` made N-by-N matrices, so the plot drew N curves; the arrays are now vectors. The time grid now reaches `tfinal` (it stopped one step short).

## Checks

Octave ran the computational part of the two `.m` solvers, and the Python versions gave identical numbers for `heat_equation 19 100` and for `stiff_ode_example` with dt = 0.05 and 0.15. In the unstable heat-equation case `19 70` (r = 0.57), the two differ by about 10⁻⁹. That is rounding error, which the instability amplifies differently in each program. The geometry scripts read 64 points and 64 springs from the rubber band files.
