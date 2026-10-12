// update_target_point_positions.cpp: moves the row of cylinders of example
// IB/04 (moving cylinders, Using IB Software).
//
// Every point of the cylinders is a target point (bristles1024.target).
// Before each time step, main.cpp calls update_target_point_positions(),
// which moves every target point up (in +y) by the distance the row travels
// during the step. The speed ramps up linearly from 0 to V over the first
// time_to_acc seconds and then stays at V. The cylinders follow their target
// points, pulled by the target-point springs.
//
// Changes from the course version (2012-2022):
//   * The IBAMR_config.h and IBTK_config.h includes are removed (see
//     update_target_point_positions.h).
//   * The comments now say that the row moves up, in y. The course comments
//     said the targets move "to the left or right" and called the row "the
//     wing".
//   * Unused variables (pi, L1, N1, level) are removed, and the loop uses
//     the current IBAMR style (a range-based for loop and nullptr).

#include "update_target_point_positions.h"

#include <ibamr/IBTargetPointForceSpec.h>

#include <ibtk/LMesh.h>
#include <ibtk/LNode.h>

#include <utility>
#include <vector>

// Set up application namespace declarations
#include <ibamr/app_namespaces.h>

void
update_target_point_positions(Pointer<PatchHierarchy<NDIM> > hierarchy,
                              LDataManager* const l_data_manager,
                              const double current_time,
                              const double dt)
{
    const int finest_ln = hierarchy->getFinestLevelNumber();

    static const double V = 0.2;           // speed of the row of cylinders after the ramp (m/s)
    static const double time_to_acc = 0.1; // time to accelerate from 0 to V (s)

    // Find out the Lagrangian index range of structure 0, the cylinders (the
    // only structure in this example). The range is [first, second): second
    // is one past the last index.
    const std::pair<int, int> cylinder_lag_idxs = l_data_manager->getLagrangianStructureIndexRange(0, finest_ln);

    // Get the LMesh (which we assume to be associated with the finest level of
    // the patch hierarchy). Note that we need to update both "local" and
    // "ghost" node data.
    Pointer<LMesh> mesh = l_data_manager->getLMesh(finest_ln);
    std::vector<LNode*> nodes = mesh->getLocalNodes();
    nodes.insert(nodes.end(), mesh->getGhostNodes().begin(), mesh->getGhostNodes().end());

    // Update the target point positions in their associated target point force
    // specs.
    for (LNode* const node : nodes)
    {
        IBTargetPointForceSpec* const force_spec = node->getNodeDataItem<IBTargetPointForceSpec>();
        if (force_spec == nullptr) continue; // skip to next node

        // Here we update the position of the target point.
        //
        // NOTES: lag_idx      is the "index" of the Lagrangian point (lag_idx = 0, 1, ..., N-1, where N is the number of Lagrangian points)
        //        X_target     is the target position of the target point
        //        X_target[0]  is the x component of the target position
        //        X_target[1]  is the y component of the target position
        //        X_target[2]  is the z component of the target position (for a 3D simulation)
        //
        // The target position is moved up (in +y) by the distance the row
        // travels in this time step: the current speed times dt.
        const int lag_idx = node->getLagrangianIndex();
        Point& X_target = force_spec->getTargetPointPosition();
        if (cylinder_lag_idxs.first <= lag_idx && lag_idx < cylinder_lag_idxs.second)
        {
            if (current_time <= time_to_acc)
            {
                X_target[1] += current_time / time_to_acc * V * dt; // speeding up
            }
            else
            {
                X_target[1] += V * dt; // constant speed
            }
        }
    }
    return;
} // update_target_point_positions
