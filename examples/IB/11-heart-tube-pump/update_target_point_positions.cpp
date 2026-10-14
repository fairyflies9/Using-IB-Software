// update_target_point_positions.cpp: valveless suction pumping by target
// points (mode TARGET_VP of example IB/11, Using IB Software).
//
// The actuator is a short piece of each wall of the elastic tube, a quarter
// of the way along it: actuator_top_512 (structure 0) and actuator_bot_512
// (structure 1), every point a target point. Before each time step this
// function SETS their target positions: the top wall's targets move down and
// the bottom wall's up by (amp/2)*(1 + sin(2 pi f t - pi/2)), so the tube is
// squeezed to (1 - pamp) of its diameter once per period and released. The
// elastic tube around the actuator follows, and the asymmetric position of
// the actuator makes the fluid go round the loop (Liebau's valveless pump).
//
// Changes from the course version (Forced-tube-pump, 2014):
//   * The frequency comes from the input file (FRE) through main.cpp instead
//     of a static const freq = 1.0 here.
//   * The geometry numbers come from pump_geometry.h.
//   * Unused variables (pi as 4*atan(1), V, L1, N1) are removed, and the loop
//     uses the current IBAMR style (a range-based for loop and nullptr).

#include "update_target_point_positions.h"

#include "pump_geometry.h"

#include <ibamr/IBTargetPointForceSpec.h>

#include <ibtk/LMesh.h>
#include <ibtk/LNode.h>

#include <cmath>
#include <utility>
#include <vector>

// Set up application namespace declarations
#include <ibamr/app_namespaces.h>

void
update_target_point_positions(Pointer<PatchHierarchy<NDIM> > hierarchy,
                              LDataManager* const l_data_manager,
                              const double current_time,
                              const double /*dt*/,
                              const double freq)
{
    const int finest_ln = hierarchy->getFinestLevelNumber();

    // How far each wall has moved toward the centre at this time: 0 at t = 0
    // (the -pi/2 phase shift starts the motion smoothly from the open tube),
    // amp at the middle of the period.
    const double squeeze = (pump::amp / 2.0) * (1.0 + std::sin(2.0 * M_PI * freq * current_time - M_PI / 2.0));

    // The Lagrangian index ranges of the two actuator pieces: [first, second).
    const std::pair<int, int> actuator_top_idxs = l_data_manager->getLagrangianStructureIndexRange(0, finest_ln);
    const std::pair<int, int> actuator_bot_idxs = l_data_manager->getLagrangianStructureIndexRange(1, finest_ln);

    // The Lagrangian mesh of the finest level: local nodes and ghost nodes.
    Pointer<LMesh> mesh = l_data_manager->getLMesh(finest_ln);
    std::vector<LNode*> nodes = mesh->getLocalNodes();
    nodes.insert(nodes.end(), mesh->getGhostNodes().begin(), mesh->getGhostNodes().end());

    // Set the target positions in their associated target point force specs.
    for (LNode* const node : nodes)
    {
        IBTargetPointForceSpec* const force_spec = node->getNodeDataItem<IBTargetPointForceSpec>();
        if (force_spec == nullptr) continue; // not a target point

        const int lag_idx = node->getLagrangianIndex();
        Point& X_target = force_spec->getTargetPointPosition();
        if (actuator_top_idxs.first <= lag_idx && lag_idx < actuator_top_idxs.second)
        {
            X_target[1] = -pump::R2 - squeeze; // the top wall of the tube is at y = -R2; it moves down
        }
        if (actuator_bot_idxs.first <= lag_idx && lag_idx < actuator_bot_idxs.second)
        {
            X_target[1] = -pump::R1 + squeeze; // the bottom wall is at y = -R1; it moves up
        }
    }
    return;
} // update_target_point_positions
