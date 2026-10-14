"""Python port of Cylinder2d.m (IBAMR examples/ConstraintIB/oscillating_rigid_cylinder): the Lagrangian points of a
solid disc of radius 0.5 centred at the origin, one point per fluid cell of the finest grid level
(dx = 32/4096 = 1/128), written to cylinder2d.vertex. The MATLAB script and this one write identical files."""
import math

Lx, Ly = 32.0, 16.0
Nx, Ny = 64 * 4 * 4 * 4, 32 * 4 * 4 * 4                     # cells on the finest level (four levels of refinement by 4 from 64 x 32)
dx, dy = Lx / Nx, Ly / Ny

X_com, Y_com = 0.0, 0.0
Radius = 0.5
num_pts_x = math.ceil(2 * Radius / dx)
num_pts_y = math.ceil(2 * Radius / dy)

# every finest-grid point inside the disc, column by column
X_array, Y_array = [], []
for i in range(1, num_pts_x + 1):
    x = X_com + ((i - 1) * dx - Radius)
    for j in range(1, num_pts_y + 1):
        y = Y_com + ((j - 1) * dy - Radius)
        if (x - X_com) ** 2 + (y - Y_com) ** 2 <= Radius ** 2:
            X_array.append(x)
            Y_array.append(y)

# shift the cloud so that its centre of mass is exactly the origin
XCOM = sum(X_array) / len(X_array)
YCOM = sum(Y_array) / len(Y_array)
X_array = [x - XCOM for x in X_array]
Y_array = [y - YCOM for y in Y_array]

with open("cylinder2d.vertex", "w", newline="\n") as f:   # LF line endings, as the MATLAB script writes
    f.write("%d\n" % len(X_array))
    for x, y in zip(X_array, Y_array):
        f.write("%f\t%f\n" % (x, y))
print("cylinder2d.vertex:", len(X_array), "points")
