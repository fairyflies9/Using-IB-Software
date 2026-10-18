"""Python port of eel2d_straightswimmer.m (IBAMR examples/ConstraintIB/eel2d): the Lagrangian points of a
2D eel of length 1, filled with points one finest-grid cell apart (dx = dy = 1/256), nose at x = -0.5 and tail
at x = 0.5, written to eel2d.vertex. The backbone is the body-shape equation at t = 0, the head is a rounded
cap of width 0.04 and the rest tapers linearly to the tail. The MATLAB script and this one write identical files."""
import math

Ny, Ly = 16 * 4 * 4 * 4, 4
Nx, Lx = 32 * 4 * 4 * 4, 8
dy, dx = Ly / Ny, Lx / Nx

L = 1                    # length of the body
Wh = 0.04 * L            # width of the head
Xh = 0.04

BodyNx = math.ceil(L / dx)
HeadNx = math.ceil(0.04 / dx)

angleRotation = 0.0      # the MATLAB script can rotate the body; the shipped file is unrotated
c, s = math.cos(angleRotation), math.sin(angleRotation)

rows = []                # one row per backbone station: the points above it, then the points below it
NumMatPoints = 0
for i in range(1, BodyNx + 1):
    x = (i - 1) * dx
    y = 0.125 * ((x + 0.03125) / 1.03125) * math.sin(2 * math.pi * x)
    if i <= HeadNx:
        height = math.sqrt(2 * Wh * x - x ** 2)              # the rounded head
    else:
        height = Wh * (L - x) / (L - Xh)                     # the tapering body
    NumPointsInHeight = math.ceil(height / dy)
    xs_up, ys_up, xs_down, ys_down = [], [], [], []
    for j in range(1, NumPointsInHeight + 1):
        xshifted, yshifted = x - 0.5, y
        rx = c * xshifted - s * yshifted
        ry = s * xshifted + c * yshifted
        xs_up.append(rx - (j - 1) * dy * s)
        xs_down.append(rx + j * dy * s)
        ys_up.append(ry + (j - 1) * dy * c)
        ys_down.append(ry - j * dy * c)
        NumMatPoints += 2
    rows.append((xs_up + xs_down, ys_up + ys_down))

with open("eel2d.vertex", "w", newline="\n") as f:   # LF line endings, as the MATLAB script writes on Linux and macOS (on Windows MATLAB's 'wt' mode writes CRLF: the same numbers)
    f.write("%d\n" % NumMatPoints)
    for xs, ys in rows:
        for x, y in zip(xs, ys):
            f.write("%f\t%f\n" % (x, y))
print("eel2d.vertex:", NumMatPoints, "points")
