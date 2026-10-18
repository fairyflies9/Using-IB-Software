"""please_Compute_External_Forcing.py for the starfish channel (pyIB2d), chapter 4f of Using IB Software.

A Python port of matIB2d/Examples/Example_Meshmerize_Me/Flow_Around_Starfish/please_Compute_External_Forcing.m
(IB2d, N. A. Battista; GPL-3.0), same numbers: in the box 0.04 <= x <= 0.06, 0.02 <= y <= 0.22 the fluid is pulled
towards a target velocity with a penalty force -k (u - u_target), k = 1e4. The target is a parabola across the channel
(zero at y = Ly/2 -+ w/2 = 0 and 0.25) times sin(2 pi 5 t) during a 0.2 s pulse, then zero for 0.2 s (rest), repeated:
    uX_Tar = -Umax sin(2 pi freq t) ((Ly/2 + w/2) - y)((Ly/2 - w/2) - y),   Umax = 2.5e3, w = 0.25, freq = 5,
which is 39 sin(2 pi 5 t) on the centre line. The penalty only approaches the target, and here the small box has to
drive the whole channel (incompressible: the flux between the walls is the same at every x), so the centre line reaches
about 1.2 (chapter 4f); measure the speed you get.

A port of IB2d's code, so GPL-3.0 (https://www.gnu.org/licenses/gpl-3.0.html), not this repository's LICENSE-CODE.
"""
import numpy as np


def please_Compute_External_Forcing(dt, current_time, x, y, grid_Info, uX, uY, first, inds):
    Nx, Ny, Lx, Ly, dx, dy = grid_Info[0], grid_Info[1], grid_Info[2], grid_Info[3], grid_Info[4], grid_Info[5]
    kStiff = 1e4
    w = 0.25
    uMax = 2.5e3
    if first == 1:
        inds = give_Me_Indices_To_Apply_Force(x, y, 0.04, 0.06, 0.02, 0.22)
        first = 0
    fx = np.zeros((Ny, Nx))
    fy = np.zeros((Ny, Nx))
    for n in range(inds.shape[0]):
        i = int(inds[n, 0]); j = int(inds[n, 1])
        uX_Tar, uY_Tar = please_Give_Target_Velocity(current_time, y[j], Ly, w, uMax)
        fx[j, i] -= kStiff * (uX[j, i] - uX_Tar)
        fy[j, i] -= kStiff * (uY[j, i] - uY_Tar)
    return (fx, fy, first, inds)


def give_Me_Indices_To_Apply_Force(x, y, xMin, xMax, yMin, yMax):
    iX = np.where((x >= xMin) & (x <= xMax))[0]
    iY = np.where((y >= yMin) & (y <= yMax))[0]
    return np.array([(i, j) for i in iX for j in iY], dtype=float)


def please_Give_Target_Velocity(t, y, Ly, w, Umax):
    freq_P = 5                     # frequency of pulse
    period = 1 / freq_P            # pulsation period
    rest_time = 1 * period         # rest time (no pulsation)
    tot_period = period + rest_time
    t_mod = np.mod(t, tot_period)
    if t_mod <= period:
        uX_Tar = -Umax * np.sin(freq_P * 2 * np.pi * t) * ((Ly / 2 + w / 2) - y) * ((Ly / 2 - w / 2) - y)
    else:
        uX_Tar = 0.0               # during rest
    return (uX_Tar, 0.0)
