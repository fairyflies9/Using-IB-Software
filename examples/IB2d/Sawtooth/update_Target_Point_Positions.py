"""update_Target_Point_Positions.py for the sawtooth pump (pyIB2d), chapter 4c of Using IB Software.

The top row of teeth moves down and up as a sine; the bottom row stays. The targets' y positions are set from the
ORIGINAL positions (read once from sawtooth.vertex), not from the previous step's, so the motion never drifts.
A port of matIB2d/Examples/Example_Sawtooth/update_Target_Point_Positions.m, with N_top taken from the file instead
of typed in (the MATLAB version hard-codes N_top = 3276 for its 1024 x 256 grid and must be edited by hand when the
resolution changes).

The driver passes the target table `targets` (columns: index, x, y, stiffness; 0-based indices) and expects it back.

As a port of IB2d's MATLAB file, this file is GPL-3.0 (https://www.gnu.org/licenses/gpl-3.0.html), like IB2d, and
not under the repository's LICENSE-CODE.
"""
import math

freq = 2.0        # pumping frequency (cycles per unit time)
a = 0.337         # total vertical travel of the top row; the rows' tips are G = 0.325 apart, so a/2 brings the top row to the centreline
_y0 = None        # the original y positions, read once
_N_top = None


def _original_positions(fname="sawtooth.vertex"):
    global _y0, _N_top
    with open(fname) as f:
        n = int(f.readline().split()[0])
        _y0 = [float(line.split()[1]) for line in f][:n]
    _N_top = n // 2                      # the generator writes the top row first, then the bottom row


def update_Target_Point_Positions(dt, current_time, targets):
    if _y0 is None:
        _original_positions()
    shift = (a / 2) * math.sin(2 * math.pi * freq * current_time)
    for i in range(_N_top):
        targets[i, 2] = _y0[i] - shift
    return targets
