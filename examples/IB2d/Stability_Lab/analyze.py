"""analyze.py: the band's shape in time from a run's viz_IB2d/lagsPts.*.vtk dumps (chapter 4d).

    python3 analyze.py [run_folder]        # default: the current folder

writes series.csv in the run folder with one row per dump: t, cx, cy (the centroid), rx, ry (half the band's extent
in x and y), rmean (the mean distance from the centroid), perimeter, area (enclosed, by the shoelace formula:
the fluid is incompressible, so a band that does not leak keeps its area; the shipped band has one point per cell,
ds = 0.97 dx, and leaks). The band starts as an ellipse (0.2 along x, 0.4 along y) and,
with springs of zero resting length, pulls itself towards a circle of the same area (radius sqrt(0.08) = 0.283)
while the fluid inside resists; rx and ry oscillate about that radius with decaying amplitude.

The reader below handles both legacy VTK layouts IB2d writes (MATLAB's "2.0" and the Python vtk module's "5.1").
"""
import glob
import math
import os
import sys


def read_points(fname):
    """The POINTS block of a legacy ASCII VTK file: a list of (x, y, z)."""
    pts = []
    with open(fname) as f:
        for line in f:
            if line.startswith("POINTS"):
                n = int(line.split()[1])
                vals = []
                while len(vals) < 3 * n:
                    vals.extend(float(v) for v in f.readline().split())
                pts = [(vals[3 * i], vals[3 * i + 1], vals[3 * i + 2]) for i in range(n)]
                break
    return pts


def shape(pts):
    n = len(pts)
    cx = sum(p[0] for p in pts) / n
    cy = sum(p[1] for p in pts) / n
    rx = (max(p[0] for p in pts) - min(p[0] for p in pts)) / 2
    ry = (max(p[1] for p in pts) - min(p[1] for p in pts)) / 2
    rmean = sum(math.hypot(p[0] - cx, p[1] - cy) for p in pts) / n
    per = sum(math.hypot(pts[(i + 1) % n][0] - pts[i][0], pts[(i + 1) % n][1] - pts[i][1]) for i in range(n))
    area = abs(sum(pts[i][0] * pts[(i + 1) % n][1] - pts[(i + 1) % n][0] * pts[i][1] for i in range(n))) / 2
    return cx, cy, rx, ry, rmean, per, area


def series(rundir=".", dt=None, print_dump=None):
    """One row per dump. dt and print_dump give the dump times; read from input2d when not given."""
    if dt is None or print_dump is None:
        dt, print_dump = params(os.path.join(rundir, "input2d"))
    rows = []
    for k, fname in enumerate(sorted(glob.glob(os.path.join(rundir, "viz_IB2d", "lagsPts.*.vtk")))):
        pts = read_points(fname)
        if not pts or any(math.isnan(p[0]) or math.isnan(p[1]) for p in pts):
            break
        rows.append((k * print_dump * dt,) + shape(pts))
    with open(os.path.join(rundir, "series.csv"), "w", newline="\n") as f:
        f.write("t,cx,cy,rx,ry,rmean,perimeter,area\n")
        for r in rows:
            f.write(",".join("%.8g" % v for v in r) + "\n")
    return rows


def params(input2d):
    dt = pd = None
    for line in open(input2d):
        s = line.split("%")[0].split("#")[0].strip()
        if s.startswith("dt ="):
            dt = float(s.split("=")[1])
        if s.startswith("print_dump ="):
            pd = int(s.split("=")[1])
    return dt, pd


if __name__ == "__main__":
    d = sys.argv[1] if len(sys.argv) > 1 else "."
    rows = series(d)
    print("%d dumps; last at t = %.4g: rx = %.4f ry = %.4f rmean = %.4f perimeter = %.4f area = %.4f (%.1f%% of the start)"
          % (len(rows), rows[-1][0], rows[-1][3], rows[-1][4], rows[-1][5], rows[-1][6], rows[-1][7], 100 * rows[-1][7] / rows[0][7]) if rows else "no dumps")
