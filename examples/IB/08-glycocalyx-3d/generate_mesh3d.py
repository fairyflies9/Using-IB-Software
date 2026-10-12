"""generate_mesh3d.py: writes glyco_512.vertex and glyco_512.target for example
IB/08 (Using IB Software). Python version of generate_mesh3d.m; it writes the
same files. Run it from this folder:  python3 generate_mesh3d.py

The files describe one glycocalyx fiber: the surface of a cylinder standing on
the floor of the domain, made of rings of points. Every point is a target
point, so the fiber is held in place. Point indices in the IBAMR files start
at 0.

The domain in input3d is 1/8 by 1/8 by 1 (m) and the finest grid has N = 512
cells across the height L = 1, so dx = 1/512. The points are spaced about
dx/2 apart, both up the cylinder and around it.
"""
import math

L = 1.0                                       # height of computational domain (m)
N = 512                                       # number of Cartesian grid meshwidths at the finest level of the AMR grid
dx = L / N                                    # Cartesian mesh width (m)

glyco_length = 10 / 64                        # glyco length (m)
glyco_radius = 1 / 64                         # glyco radius (m)
glyco_radius = glyco_radius - 1.25 * dx       # glyco radius adjustment for width of delta functions
npts_height = math.ceil(2 * (glyco_length / L) * N)               # number of points along the height (160)
npts_circum = math.ceil(2 * (2 * math.pi * glyco_radius / L) * N)  # number of points along the circumference (85)
npts = npts_height * npts_circum              # total number of points in the fiber (13600)
dq = glyco_length / (npts_height - 1)         # glyco mesh spacing along the height (m)

# ds is NOT the spacing of the points around the cylinder. That spacing is
# 2*pi*glyco_radius/npts_circum = 9.7e-4 m (about dx/2), while
# ds = glyco_radius/(npts_circum-1) = 1.6e-4 m is 6.2 times smaller.
# ds is used only to scale the target stiffness below: each target point gets
# kappa_target/ds = 3.19e4. Dividing by the true spacing would give 5.13e3.
# The value is kept so that the files match the ones every earlier version of
# this example used.
ds = glyco_radius / (npts_circum - 1)         # scale for the target stiffness (m)

mesh_name = "glyco_"                          # structure name
offset = -0.5 * L + dq                        # glyco base from bottom of domain (m)

kappa_spring = 5e0                            # spring constant (Newton)
kappa_beam = 0.0                              # beam stiffness constant (Newton m^2); not used
kappa_target = kappa_spring                   # target point penalty spring constant (Newton)

# Write out the vertex information: one ring of npts_circum points at each of
# the npts_height heights, starting at the ring nearest the floor.
with open(f"{mesh_name}{N}.vertex", "w", newline="\n") as f:
    f.write(f"{npts}\n")
    for q in range(npts_height):
        for s in range(npts_circum):
            x = 0.0 + glyco_radius * math.cos(s * 2 * math.pi / npts_circum)
            y = 0.0 + glyco_radius * math.sin(s * 2 * math.pi / npts_circum)
            z = offset + q * dq
            f.write("%1.16e %1.16e %1.16e\n" % (x, y, z))

# Springs and beams are not used: the target points alone hold the fiber.
# generate_mesh3d.m keeps commented-out code that shows how to write them.

# Write out the target point information: every point of the fiber is a
# target point, all the way up the cylinder.
with open(f"{mesh_name}{N}.target", "w", newline="\n") as f:
    f.write(f"{npts_height * npts_circum}\n")
    for q in range(npts_height):
        for s in range(npts_circum):
            f.write("%d %1.16e\n" % (q * npts_circum + s, kappa_target * ds / (ds ** 2)))
