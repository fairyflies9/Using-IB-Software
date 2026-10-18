"""update_Target_Point_Positions.py: called by pyIB2d's driver every time step when input2d has update_target = 1.

Drags every target point along a zig-zag: always upward at half the speed, and to the right during the first half of
each period, to the left during the second half (the MATLAB example's motion). A Python port of
matIB2d/Examples/Example_Moving_Rubberband/update_Target_Point_Positions.m.

The driver passes and expects back the target table `targets` with one row per target point:
    column 0: the point's index (0-based in pyIB2d)
    column 1: the target x position
    column 2: the target y position
    column 3: the target stiffness
The structure's own positions are not touched here: the points follow their targets through the target force.

As a port of IB2d's MATLAB file, this file is GPL-3.0 (https://www.gnu.org/licenses/gpl-3.0.html), like IB2d, and
not under the repository's LICENSE-CODE.
"""


def update_Target_Point_Positions(dt, current_time, targets):
    period = 0.05            # time of one right-or-left leg
    L = 0.5                  # distance travelled in each direction
    s = L / (period / 2)     # speed
    t = current_time % period
    targets[:, 2] += (s / 2) * dt                    # up, always
    if t < period / 2:
        targets[:, 1] += s * dt                      # right
    else:
        targets[:, 1] -= s * dt                      # left
    return targets
