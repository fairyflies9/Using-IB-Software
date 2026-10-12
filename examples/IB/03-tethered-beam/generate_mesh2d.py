"""generate_mesh2d.py: writes leaf_512.vertex, leaf_512.spring, leaf_512.beam
and leaf_512.target for example IB/03 (Using IB Software). Python version of
generate_mesh2d.m; it writes the same files. Run it from this folder:
    python3 generate_mesh2d.py

The "leaf" is a straight vertical beam of length 0.1 m centered on the
origin. Its points are joined by springs (stretching) and beams (bending).
Two points in the middle are target points that hold the leaf in place.
Point indices in the IBAMR files start at 0.
"""
import math

L = 1.0                                       # length of computational domain (m)
N = 512                                       # number of Cartesian grid meshwidths at the finest level of the AMR grid
dx = L / N                                    # Cartesian mesh width (m)

plate_length = 0.1                            # leaf length (m)
npts = math.ceil(2 * (plate_length / L) * N)  # number of points along the leaf (103)
ds = plate_length / (npts - 1)                # physical distance between neighboring Lagrangian mesh points (m)

mesh_name = "leaf_"                           # structure name
offset = 0.0                                  # x position of the leaf (m)

kappa_spring = 3.0e1                          # stretching stiffness K (tension per unit strain).
                                              # The .spring file stores K/ds, written below as kappa_spring*ds/(ds^2).
kappa_beam = 5.0e-3                           # bending stiffness. The .beam file stores kappa_beam/ds^3,
                                              # written below as kappa_beam*ds/(ds^4).
kappa_target = kappa_spring                   # target point stiffness. The .target file stores kappa_target/ds.

# newline="\n" gives Unix line endings even on Windows, as IBAMR needs.

# Write out the vertex information: point 0 is the top end (y = 0.05) and
# point npts-1 is the bottom end (y = -0.05).
with open(f"{mesh_name}{N}.vertex", "w", newline="\n") as f:
    f.write("%d\n" % npts)
    for s in range(npts):
        x = offset
        y = 0.0 + 0.5 * plate_length - s * ds
        f.write("%1.16e %1.16e\n" % (x, y))

# Write out the spring information: one spring between each pair of
# neighbors, with rest length ds (the starting spacing).
with open(f"{mesh_name}{N}.spring", "w", newline="\n") as f:
    f.write("%d\n" % (npts - 1))
    for s in range(npts - 1):
        f.write("%d %d %1.16e %1.16e\n" % (s, s + 1, kappa_spring * ds / (ds ** 2), ds))

# Write out the beam information: one beam for each three neighboring points.
# The leaf is straight, so the beams have no preferred curvature.
with open(f"{mesh_name}{N}.beam", "w", newline="\n") as f:
    f.write("%d\n" % (npts - 2))
    for s in range(npts - 2):
        f.write("%d %d %d %1.16e\n" % (s, s + 1, s + 2, kappa_beam * ds / (ds ** 4)))

# Write out the target point information: the two middle points, 50 (at
# y = ds) and 51 (at y = 0), are tethered to where they start.
with open(f"{mesh_name}{N}.target", "w", newline="\n") as f:
    f.write("%d\n" % 2)
    s = math.floor(npts / 2) - 1
    f.write("%d %1.16e\n" % (s, kappa_target * ds / (ds ** 2)))
    s = math.floor(npts / 2)
    f.write("%d %1.16e\n" % (s, kappa_target * ds / (ds ** 2)))
