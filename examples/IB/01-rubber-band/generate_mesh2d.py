"""generate_mesh2d.py: writes rubber_band_512.vertex and rubber_band_512.spring
for example IB/01 (Using IB Software). Python version of generate_mesh2d.m;
it writes the same files. Run it from this folder:  python3 generate_mesh2d.py

The band is an ellipse with semi-axes radius+epsilon (x) and radius (y), and
the springs' rest length is the spacing ds of a circle of radius `radius`,
so the band starts stretched and relaxes toward a circle.
Point indices in the IBAMR files start at 0.
"""
import math

L = 1.0                                       # length of computational domain (m)
N = 512                                       # number of Cartesian grid meshwidths at the finest level of the AMR grid
dx = L / N                                    # Cartesian mesh width (m)

center_x = 0.0                                # x-coordinate of the center of the circle
center_y = 0.0                                # y-coordinate of the center of the circle

radius = 0.1                                  # radius of band (m)
epsilon = 0.02                                # deformation in the x-direction
band_length = 2 * math.pi * radius            # rubber band length (m)
npts = math.ceil(2 * (band_length / L) * N)   # number of points along the rubber band
ds = band_length / npts                       # physical distance between neighboring Lagrangian mesh points (m)
dtheta = 2 * math.pi / npts

mesh_name = "rubber_band_"                    # structure name
kappa_spring = 2.0e3                          # band stiffness K: tension per unit strain.
                                              # The .spring file stores K/ds, written below as kappa_spring*ds/(ds^2).

# Write out the vertex information
with open(f"{mesh_name}{N}.vertex", "w", newline="\n") as f:
    f.write(f"{npts}\n")
    for s in range(npts):
        x = (radius + epsilon) * math.sin(s * dtheta) + center_x
        y = radius * math.cos(s * dtheta) + center_y
        f.write("%1.16e %1.16e\n" % (x, y))

# Write out the spring information: point s is joined to s+1, and the last
# point back to point 0
with open(f"{mesh_name}{N}.spring", "w", newline="\n") as f:
    f.write(f"{npts}\n")
    for s in range(npts):
        f.write("%d %d %1.16e %1.16e\n" % (s, (s + 1) % npts, kappa_spring * ds / (ds ** 2), ds))
