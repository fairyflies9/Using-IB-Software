// update_target_point_positions_peri.cpp: prescribed peristalsis by target
// points (mode TARGET_PERI of example IB/11, Using IB Software).
//
// The driven pieces are the middle 0.3 m of each wall of the elastic tube:
// pperi_top_512 (structure 0) and pperi_bot_512 (structure 1), every point a
// target point. Before each time step this function SETS the target of point
// number i (counted from the left end of the piece) to
//     y_wall -/+ amp * c(t) * sin(2 pi (i ds/Lap) - 2 pi f t),
// a sine wave with one wavelength along the piece that travels to the right
// at f wavelengths per second; where the wave is positive the walls move in
// (the tube narrows), where it is negative they move out. c(t) ramps the
// amplitude up linearly over the first half period so that the run does not
// start with a jolt, and the amplitude is tapered to zero over the last
// 5 cm at each end of the piece (a raised-cosine window), so that the driven
// points join the free part of the wall smoothly.
//
// Changes from the course version (Forced-tube-pump, 2014):
//   * The taper is new. Without it the wave does not vanish at the ends of
//     the piece, so the last driven point can sit up to amp = 4 cm from the
//     first free point of the wall, one point spacing away: a kink that the
//     beams answer with a huge force. The 2014 version of this run aborted
//     at t = 0.77 s with "Time step size change encountered" (the CFL limit)
//     when the end displacement peaked.
//   * The frequency comes from the input file (FRE) through main.cpp.
//   * The geometry numbers come from pump_geometry.h; the course file
//     repeated them (and called the section "Let", which is the elastic
//     tube's length in the generator, not this piece's).
//   * Unused variables are removed, and the loop uses the current IBAMR
//     style (a range-based for loop and nullptr).

#include "update_target_point_positions_peri.h"

#include "pump_geometry.h"

#include <ibamr/IBTargetPointForceSpec.h>

#include <ibtk/LMesh.h>
#include <ibtk/LNode.h>

#include <algorithm>
#include <cmath>
#include <utility>
#include <vector>

// Set up application namespace declarations
#include <ibamr/app_namespaces.h>

void
update_target_point_positions_peri(Pointer<PatchHierarchy<NDIM> > hierarchy,
                                   LDataManager* const l_data_manager,
                                   const double current_time,
                                   const double /*dt*/,
                                   const double freq)
{
    const int finest_ln = hierarchy->getFinestLevelNumber();

    // Ramp the amplitude up over the first half period.
    const double s_ramp = 0.5 / freq;
    const double c_amp = (current_time < s_ramp) ? current_time / s_ramp : 1.0;

    // Taper the amplitude to zero over the last L_taper at each end of the
    // piece: a raised-cosine window, 1 in the middle.
    const double L_taper = 0.05;
    auto envelope = [&](double s) {
        double e = 1.0;
        if (s < L_taper) e = 0.5 * (1.0 - std::cos(M_PI * s / L_taper));
        if (s > pump::Lap - L_taper) e = 0.5 * (1.0 - std::cos(M_PI * (pump::Lap - s) / L_taper));
        return std::max(0.0, e);
    };

    // The Lagrangian index ranges of the two driven pieces: [first, second).
    const std::pair<int, int> top_idxs = l_data_manager->getLagrangianStructureIndexRange(0, finest_ln);
    const std::pair<int, int> bot_idxs = l_data_manager->getLagrangianStructureIndexRange(1, finest_ln);

    // The Lagrangian mesh of the finest level: local nodes and ghost nodes.
    Pointer<LMesh> mesh = l_data_manager->getLMesh(finest_ln);
    std::vector<LNode*> nodes = mesh->getLocalNodes();
    nodes.insert(nodes.end(), mesh->getGhostNodes().begin(), mesh->getGhostNodes().end());

    for (LNode* const node : nodes)
    {
        IBTargetPointForceSpec* const force_spec = node->getNodeDataItem<IBTargetPointForceSpec>();
        if (force_spec == nullptr) continue; // not a target point

        const int lag_idx = node->getLagrangianIndex();
        Point& X_target = force_spec->getTargetPointPosition();
        if (top_idxs.first <= lag_idx && lag_idx < top_idxs.second)
        {
            const double s = (lag_idx - top_idxs.first) * pump::ds; // position along the piece (m)
            const double wave = std::sin(-2.0 * M_PI * freq * current_time + 2.0 * M_PI * (s / pump::Lap));
            X_target[1] = -pump::R2 - pump::amp * c_amp * envelope(s) * wave;
        }
        if (bot_idxs.first <= lag_idx && lag_idx < bot_idxs.second)
        {
            const double s = (lag_idx - bot_idxs.first) * pump::ds;
            const double wave = std::sin(-2.0 * M_PI * freq * current_time + 2.0 * M_PI * (s / pump::Lap));
            X_target[1] = -pump::R1 + pump::amp * c_amp * envelope(s) * wave;
        }
    }
    return;
} // update_target_point_positions_peri
