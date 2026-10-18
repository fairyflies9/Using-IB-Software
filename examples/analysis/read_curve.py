"""read_curve.py: VisIt's .curve files (File > Set Save Options > curve, then Save; or SaveWindow with format CURVE)
into NumPy (chapter 29).

    from read_curve import read_curve
    c = read_curve("pick.curve")          # {'U_x': (t, u), 'speed': (t, s)}: one entry per curve in the file
    python3 read_curve.py file.curve ...  # prints each curve's name, length and range

A .curve file is plain text: a line "# name" before each curve, then one "x y" pair per line (VisIt 3.5; a pick
through time of two variables gives two curves in one file). numpy.loadtxt(path, comments="#") reads a file with one
curve; this reader keeps several apart.
"""
import sys
import numpy as np


def read_curve(path):
    out, name, xs, ys = {}, None, [], []
    with open(path) as f:
        for line in f:
            s = line.strip()
            if not s:
                continue
            if s.startswith("#"):
                if name is not None:
                    out[name] = (np.array(xs), np.array(ys))
                name, xs, ys = s[1:].strip(), [], []
            else:
                a, b = s.split()[:2]
                xs.append(float(a)); ys.append(float(b))
    if name is not None:
        out[name] = (np.array(xs), np.array(ys))
    elif xs:
        out["curve"] = (np.array(xs), np.array(ys))
    return out


if __name__ == "__main__":
    for p in sys.argv[1:]:
        for name, (x, y) in read_curve(p).items():
            print("%s: %s, %d points, x %g .. %g, y %g .. %g" % (p, name, len(x), x.min(), x.max(), y.min(), y.max()))
