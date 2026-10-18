"""update_Target_Point_Positions.py for the pulsing heart (pyIB2d), chapter 4c of Using IB Software.

Every target point moves between two stored shapes: phase 1 (the heart's expanded shape, columns 1-2 of
All_Positions.txt) and phase 2 (the contracted shape, columns 3-4). During the contraction (tP1 = 0.025) the targets
go from phase 1 to phase 2, during the expansion (tP2 = 0.025) back, with a smooth blend g(t) that starts and ends
with zero speed (a quadratic start, a cubic middle, a quadratic end: the polynomial of Nick Battista's examples,
also used by the swimmer's beams). A port of matIB2d/Examples/Example_Pulsing_Heart/32x32/update_Target_Point_Positions.m;
the phase file is read once, not at every step as in the MATLAB version.

The driver passes the target table `targets` (columns: index, x, y, stiffness; 0-based indices) and expects it back.

As a port of IB2d's MATLAB file, this file is GPL-3.0 (https://www.gnu.org/licenses/gpl-3.0.html), like IB2d, and
not under the repository's LICENSE-CODE.
"""
import math

tP1 = 0.025                 # contraction time
tP2 = 0.025                 # expansion time
period = tP1 + tP2
# the blend g(s), s = t / tP in [0, 1]: g = a s^2 for s < 0.1; c s^3 + d s^2 + gg s + h for 0.1 <= s < 0.9; 1 - b (s - 1)^2 after
a = 2.739726027397260
b = 2.739726027397260
c = -2.029426686960933
d = 3.044140030441400
gg = -0.015220700152207
h = 0.000253678335870
_phases = None              # (x1, y1, x2, y2), read once


def _read_phases(fname="All_Positions.txt"):
    global _phases
    x1, y1, x2, y2 = [], [], [], []
    with open(fname) as f:
        for line in f:
            v = line.split()
            if len(v) < 4:
                continue
            x1.append(float(v[0])); y1.append(float(v[1])); x2.append(float(v[2])); y2.append(float(v[3]))
    _phases = (x1, y1, x2, y2)


def blend(s):
    """0 -> 1 over s in [0, 1] with zero slope at both ends."""
    if s < 0.1:
        return a * s * s
    if s < 0.9:
        return c * s ** 3 + d * s * s + gg * s + h
    return 1.0 - b * (s - 1.0) ** 2


def update_Target_Point_Positions(dt, current_time, targets):
    if _phases is None:
        _read_phases()
    x1, y1, x2, y2 = _phases
    t = current_time % period
    if t <= tP1:                                  # contracting: phase 1 -> phase 2
        g = blend(t / tP1)
        for i in range(targets.shape[0]):
            targets[i, 1] = x1[i] + g * (x2[i] - x1[i])
            targets[i, 2] = y1[i] + g * (y2[i] - y1[i])
    else:                                         # expanding: phase 2 -> phase 1
        g = blend((t - tP1) / tP2)
        for i in range(targets.shape[0]):
            targets[i, 1] = x2[i] + g * (x1[i] - x2[i])
            targets[i, 2] = y2[i] + g * (y1[i] - y2[i])
    return targets
