"""hier_data.py: read the Lagrangian positions and forces that the IB examples
of Using IB Software write (X.NNNNN and F.NNNNN in hier_data_IB2d or
hier_data_IB3d), in Python.

The files are PETSc ASCII vectors written by the examples' output_data()
(chapter 11). Each holds NDIM numbers per Lagrangian point, in Lagrangian
order (all structures together, in the order of structure_names in the input
file): x, y[, z] of point 0, then of point 1, and so on. The first lines name
the vector ("Vec Object: 3 MPI processes", "  type: mpi") and each process's
block starts with a line "Process [k]"; those lines are skipped. The file's
number is the time step, so the time is that number times DT.

    from hier_data import read_vec, read_series, read_input
    t, X = read_series("hier_data_IB2d", "X", dt=1.0e-4)   # t: times; X[k]: (npts, NDIM) array at time t[k]
    t, F = read_series("hier_data_IB2d", "F", dt=1.0e-4)
    drag = F[k][:, 0].sum()                                  # the sum of the x forces at time t[k]

Run it as a script to check a folder:  python3 hier_data.py <run folder>
"""
import glob
import os
import re
import sys

import numpy as np


def read_vec(path, ndim=2):
    """One X.NNNNN or F.NNNNN file as an (npts, ndim) array."""
    vals = []
    with open(path) as f:
        for line in f:
            s = line.strip()
            if not s or s[0].isalpha() or s.startswith("Process"):
                continue  # "Vec Object: ...", "  type: ...", "Process [k]"
            try:
                vals.append(float(s))
            except ValueError:
                pass
    v = np.array(vals)
    if v.size % ndim:
        raise ValueError("%s holds %d numbers, not a multiple of %d" % (path, v.size, ndim))
    return v.reshape(-1, ndim)


def read_series(folder, kind="X", dt=None, ndim=2):
    """All X.* (or F.*) files of a folder, in time order: (times, [arrays]).

    dt is the time step of the run (DT in the input file); with dt=None the
    "times" are the step numbers."""
    files = sorted(glob.glob(os.path.join(folder, kind + ".*")), key=lambda p: int(p.rsplit(".", 1)[1]))
    steps = np.array([int(p.rsplit(".", 1)[1]) for p in files])
    t = steps * dt if dt is not None else steps
    return t, [read_vec(p, ndim) for p in files]


def read_input(path, key):
    """A number from an IBAMR input file, e.g. read_input('input2d', 'DT')."""
    txt = open(path).read()
    m = re.search(r"^\s*%s\s*=\s*([-+0-9.eE]+)" % re.escape(key), txt, re.M)
    if m is None:
        raise KeyError("%s not found in %s" % (key, path))
    return float(m.group(1))


if __name__ == "__main__":
    run = sys.argv[1] if len(sys.argv) > 1 else "."
    folder = [d for d in ("hier_data_IB2d", "hier_data_IB3d") if os.path.isdir(os.path.join(run, d))]
    if not folder:
        sys.exit("no hier_data_IB2d or hier_data_IB3d in " + run)
    folder = os.path.join(run, folder[0])
    ndim = 3 if folder.endswith("3d") else 2
    dt = read_input(os.path.join(run, "input%dd" % ndim), "DT")
    t, X = read_series(folder, "X", dt, ndim)
    t, F = read_series(folder, "F", dt, ndim)
    print("%s: %d frames, t = %g to %g, %d points, %dD" % (folder, len(t), t[0], t[-1], X[0].shape[0], ndim))
    for k in (0, len(t) // 2, len(t) - 1):
        print("  t = %-8g sum F = %s   x range %.4g..%.4g" % (t[k], np.array2string(F[k].sum(axis=0), precision=4), X[k][:, 0].min(), X[k][:, 0].max()))
