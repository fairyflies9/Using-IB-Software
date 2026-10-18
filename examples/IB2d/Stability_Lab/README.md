# Stability_Lab (pyIB2d): the rubber band blown up, mapped and refined

Chapter 4d of *Using IB Software*. The shipped `Rubberband_with_Springs` example (a tall ellipse of 64 points with
springs of zero resting length in a 32 x 32 periodic box) with the grid, the stiffness, the resting length and the
number of points per cell as arguments, a sweep script that runs the chapter's groups of cases, and an analysis script
that turns each run's `lagsPts` dumps into the band's shape in time. Every number on the chapter's slides came from
`runs/summary.json` and the `series.csv` files these scripts write (October 2026, Python IB2d, clone of 2024-03-06 with
the tracer fix of chapter 4b, on a desktop PC under WSL).

| file | what |
|---|---|
| `Rubberband.py [Nx [k_Spring [ds_Rest [ppc]]]]` | writes `rubberband.vertex` and `rubberband.spring` (0-based) for `ppc * Nx` points; defaults `32 2.5e4 0 2` reproduce the shipped files to 1e-16; prints N, ds, dx, ds/dx |
| `input2d` | the shipped example's input with the MATLAB plotting off and only vorticity, velocity and the points saved |
| `main2d.py` | the run script, as in every pyIB2d example |
| `sweep.py GROUP ... [--jobs N] [--redo]` | one folder per case under `runs/`: `input2d` rewritten, band files generated, `main2d.py` copied (path adjusted), the run timed, its status and last error line recorded, `series.csv` written |
| `analyze.py [run_folder]` | `series.csv`: t, centroid, half-extents r_x and r_y, mean radius, perimeter, enclosed area, one row per dump |

Put the folder under `pyIB2d/Examples/` of an IB2d clone and run from inside it.

## The groups

| group | runs | what it shows (slide) |
|---|---|---|
| `base` | the shipped example as it is | the band snaps from tall to wide and back ten times in 1.5 time units; its enclosed area falls to 87 % at t = 1 and 73 % at t = 1.5 |
| `blowup` | dt = 1 with T = 100; the band 1000 times stiffer | the two blow-ups of the course's lab; Python's error is `IndexError: index -9223372036854775808 is out of bounds` (a NaN position cast to an index) where MATLAB says `BLOW UP! (*forces TOO large*)` |
| `map`, `map2` | k = 2.5e3 ... 2.5e7 against dt = 1.6e-5 ... 0.064 on 32 x 32, T = 0.3 (41 runs) | the admissible time step falls with the stiffness: up to 4e-3 for the shipped band, 2e-3 at ten times the stiffness (a factor 1.3-4 for ten times k between x1 and x10, at least 8-16 between x0.1 and x1); the band 100 times stiffer fails before the first dump (t < 0.02) at dt = 0.004, 0.002, 0.001 and at t = 0.04-0.08 for dt = 5e-4 down to 1.6e-5; 1000 times stiffer before the first dump at every dt (within the first few steps for dt >= 1.25e-4 by the wall time; about 1100 steps at 1.6e-5) |
| `grid` | 16 ... 256 with k scaled with N, and 64 x 64 with the 32-grid's k | the wrong refinements: the band gets softer (first r_y minimum drifts from t = 0.10 to 0.28) |
| `grid2` | 16 ... 256 with k scaled with N^2, dt with dx | the same band on every grid (first minimum 0.196-0.203 at t = 0.10 from 32 on; 16 is late, at 0.12); the area loss at t = 1 falls from 20 % (16) to 4 % (256), an order between 0.3 and 0.8 |
| `dt`, `dt2` | 64 x 64 at dt = 1e-3, 5e-4, 2.5e-4, 1.25e-4 | r_y(0.98) differences 2.4e-4, 1.1e-4, 5.6e-5 (p = 1.07, 1.02), but these are the one-step lag of the dumps (dump k is written after step k * print_dump + 1, so it is the state at t + dt: r_y' * dt), not the time-stepping error, which is below them; the order in time is not measured by this series (see the chapter's exercise 7) |
| `grid3` | two points per cell with k x 4 | a band twice as tense (first minimum at t = 0.06-0.08): the driver's spreading weight is `Lx/(2 Nx)`, not the file's spacing, so adding points needs k x 2, not x 4 |
| `grid4` | two points per cell with k x 2 | the same band as `grid2` with twice the points; the same area loss to within one percent: the loss is the method's volume error (Peskin and Printz 1993), not fluid between the points |

`sweep.py all` runs everything (73 cases; the 256 x 256 runs take 3-8 minutes each on a desktop PC under WSL; the rest seconds).

## Results at a glance

Grid refinement with the band kept (`grid2`; `k = 2.5e4 (N/32)^2`, `dt = 1e-3 * 32/N`, halved again at 256):

| grid | points | k | dt | first r_y minimum | area left at t = 0.98 | mean radius at 0.98 | wall |
|---|---|---|---|---|---|---|---|
| 16 | 32 | 6.25e3 | 2e-3 | 0.200 at 0.12 | 79.5 % | 0.2526 | 1.9 s |
| 32 | 64 | 2.5e4 | 1e-3 | 0.196 at 0.10 | 87.1 % | 0.2641 | 2.9 s |
| 64 | 128 | 1e5 | 5e-4 | 0.203 at 0.10 | 89.6 % | 0.2677 | 8.6 s |
| 128 | 256 | 4e5 | 2.5e-4 | 0.201 at 0.10 | 93.0 % | 0.2727 | 38 s |
| 256 | 512 | 1.6e6 | 6.25e-5 | 0.203 at 0.10 | 95.9 % | 0.2771 | 384 s |

The same with two points per cell (`grid4`, k doubled): area left 80.6, 88.0, 90.5, 93.3, 96.1 %. The circle with the
ellipse's area has radius 0.283; the mean radius climbs towards it as the loss closes.

Stiffness against time step (`map`, `map2`; 32 x 32, T = 0.3): largest dt that ran to the end: k = 2.5e3: 0.064
(every value tried); 2.5e4: 0.004 (fails at 0.008 after t = 0.14); 2.5e5: 0.002 (fails at 0.003 after t = 0.02);
2.5e6: none (before the first dump at dt = 0.004, 0.002, 0.001; at t = 0.04 for 5e-4, 0.06 for 2.5e-4 and 1.25e-4,
0.08 for 6.25e-5 down to 1.6e-5); 2.5e7: none (before the first dump at every dt).

## Three facts about IB2d the lab turned up

1. The band's geometry function takes `(N, rmin, rmax)` but is called with `(N, a, b) = (N, 0.4, 0.2)`, so the shipped
   band is tall (0.2 along x, 0.4 along y), not wide.
2. `N = 2 Nx` points is "2x resolution of the Eulerian grid" in the generator's comment, but the band's perimeter is
   1.94, so the shipped example has one point per cell (ds = 0.97 dx).
3. The driver spreads forces with its own `ds = Lx/(2 Nx)` (`IBM_Driver.py` line 259; MATLAB line 188 takes the smaller
   direction), whatever the file's spacing: a spring constant is a force density weighted by dx/2, so refining the grid
   with the same k makes a band four times softer per doubling, and doubling the points on one grid halves the tension.

4. Every dump is written one step late: `IBM_Driver.py` line 834 tests the dump counter before it is incremented, so
   dump k holds the state after step k * print_dump + 1 (the state at t + dt, not t). Compare runs with different dt at
   the same step-corrected time, or by the time of a feature (the first minimum), not dump by dump at the nominal time.
   The fork branch `python-updates-2026` (pull request 34 to IB2d) writes the final dump at exactly Tfinal.

The Python port has no `BLOW UP` check (MATLAB's is a try/catch around the same index look-up); a run that has gone
unstable ends with the `IndexError` above, from `Supp.py` line 101 in `please_Move_Lagrangian_Point_Positions`.
