"""generate_mesh2d.py: writes the structure files for example IB/10 (the
jellyfish bell, Using IB Software): a 2D bell of 2n+1 points from the left
tip through the apex to the right tip, joined by springs and by beams whose
preferred curvature is the bell's own shape at rest (beta = beta_0).
update_beams.cpp changes that curvature in time to make the bell pulse.

The shape (bell_geometry.h): from the apex (r = 0, z = Zs) down one side, the
tangent angle is theta(s) = -1.55 (1 - exp(-s/beta)), s the arc length from
the apex; the positions follow by marching along the curve in steps of ds,
as the 2013 course code did. "The position of the boundary is calculated for
beta_0 = 0.5" (2013).

Run it in this folder: python3 generate_mesh2d.py
generate_mesh2d.m writes the same files (checked with Octave 8.4 and Python 3.12).
"""
import math

L = 4.0                                       # length of computational domain
N = 256                                       # number of Cartesian grid meshwidths at the finest level of the AMR grid
dx = L / N                                    # Cartesian mesh width
ds = L / (2 * N)                              # distance between neighboring Lagrangian mesh points (half a cell)

arc = 1.0                                     # arc length of each half of the bell, apex to tip
n = round(arc / ds)                           # points per half (128); the bell has 2n+1 points
npts = 2 * n + 1
Zs = 1.0                                      # z of the apex at t = 0 (the bell hangs below it, open downward)
theta_max = 1.55                              # the tangent angle tends to -theta_max (nearly -pi/2)
beta_0 = 0.5                                  # the relaxed (open) bell; update_beams.cpp takes it to beta_m = 0.2

mesh_name = "bell_"                           # structure name

kappa_spring = 1.0e3                          # stretching stiffness (tension per unit strain); the file stores kappa_spring/ds
kappa_beam = 1.0                              # bending stiffness; the file stores kappa_beam/ds^3

# The right half of the bell: r[k], z[k] for k = 0 (apex) to n (tip).
r = [0.0] * (n + 1)
z = [0.0] * (n + 1)
z[0] = Zs
for k in range(1, n + 1):
    theta = -theta_max * (1.0 - math.exp(-(k * ds) / beta_0))
    z[k] = z[k - 1] + ds * math.sin(theta)
    r[k] = r[k - 1] + ds * math.cos(theta)

# The whole curve, left tip (point 0) to right tip (point 2n), apex at point n:
# the left half is the mirror image of the right half.
X = [0.0] * npts
Y = [0.0] * npts
for i in range(npts):
    k = abs(i - n)
    X[i] = -r[k] if i < n else r[k]
    Y[i] = z[k]

# newline="\n" gives Unix line endings even on Windows, as IBAMR needs.

# Write out the vertex information.
with open(f"{mesh_name}{N}.vertex", "w", newline="\n") as f:
    f.write("%d\n" % npts)
    for i in range(npts):
        f.write("%1.16e %1.16e\n" % (X[i], Y[i]))

# Write out the link information: a spring between each pair of neighbors,
# with the rest length equal to the distance between them at rest.
with open(f"{mesh_name}{N}.spring", "w", newline="\n") as f:
    f.write("%d\n" % (npts - 1))
    for i in range(npts - 1):
        rest = math.sqrt((X[i + 1] - X[i]) ** 2 + (Y[i + 1] - Y[i]) ** 2)
        f.write("%d %d %1.16e %1.16e\n" % (i, i + 1, kappa_spring * ds / (ds ** 2), rest))

# Write out the beam information: "i-1 i i+1 stiffness C1 C2", with the
# preferred curvature (C1, C2) = X_{i-1} - 2 X_i + X_{i+1} of the resting
# shape, so that the bell is in equilibrium at t = 0. update_beams.cpp
# overwrites C1 and C2 before every time step.
with open(f"{mesh_name}{N}.beam", "w", newline="\n") as f:
    f.write("%d\n" % (npts - 2))
    for i in range(1, npts - 1):
        c1 = X[i - 1] - 2 * X[i] + X[i + 1]
        c2 = Y[i - 1] - 2 * Y[i] + Y[i + 1]
        f.write("%d %d %d %1.16e %1.16e %1.16e\n" % (i - 1, i, i + 1, kappa_beam * ds / (ds ** 4), c1, c2))

print("wrote %s%d.vertex (%d points), .spring (%d), .beam (%d); ds = %.6g, dx = %.6g; bell width %.4f, height %.4f"
      % (mesh_name, N, npts, npts - 1, npts - 2, ds, dx, 2 * r[n], Zs - z[n]))
