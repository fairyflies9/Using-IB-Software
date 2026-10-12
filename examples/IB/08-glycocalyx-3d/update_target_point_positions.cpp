// update_target_point_positions.cpp: moving target points for example IB/08.
//
// From the 2014 version of the glycocalyx example (IBAMR-Examples), where the
// target points were moved by V*dt each step with V = 0 written into the code.
// Here V is the input key TARGET_VELOCITY and is passed in as "velocity".
// The unused leftovers of a 2D leaf example (leaf length, domain size, number
// of points and their spacing) are removed.

#include <ibamr/IBTargetPointForceSpec.h>

#include <ibtk/LMesh.h>
#include <ibtk/LNode.h>

#include "update_target_point_positions.h"

#include <utility>
#include <vector>

void
update_target_point_positions(Pointer<PatchHierarchy<NDIM> > hierarchy,
                              LDataManager* const l_data_manager,
                              const double /*current_time*/,
                              const double dt,
                              const double velocity)
{
    const int finest_ln = hierarchy->getFinestLevelNumber();

    // Find out the Lagrangian index range of structure 0, the first (and here
    // the only) structure listed in structure_names in input3d.
    const std::pair<int, int> fiber_lag_idxs = l_data_manager->getLagrangianStructureIndexRange(0, finest_ln);

    // Get the LMesh (which we assume to be associated with the finest level of
    // the patch hierarchy).  Note that we currently need to update both "local"
    // and "ghost" node data.
    Pointer<LMesh> mesh = l_data_manager->getLMesh(finest_ln);
    std::vector<LNode*> nodes;
    nodes.insert(nodes.end(), mesh->getLocalNodes().begin(), mesh->getLocalNodes().end());
    nodes.insert(nodes.end(), mesh->getGhostNodes().begin(), mesh->getGhostNodes().end());

    // Update the target point positions in their associated target point force
    // specs.
    for (LNode* const node_idx : nodes)
    {
        IBTargetPointForceSpec* force_spec = node_idx->getNodeDataItem<IBTargetPointForceSpec>();
        if (force_spec == nullptr) continue; // skip to next node

        // Here we update the position of the target point.
        //
        // NOTES: lag_idx      is the "index" of the Lagrangian point (lag_idx = 0, 1, ..., N-1, where N is the number of Lagrangian points)
        //        X_target     is the target position of the target point
        //        X_target[0]  is the x component of the target position
        //        X_target[1]  is the y component of the target position
        //        X_target[2]  is the z component of the target position (for a 3D simulation)
        //
        // The target position is shifted in the x-direction by the increment
        // dt*velocity.
        const int lag_idx = node_idx->getLagrangianIndex();
        Point& X_target = force_spec->getTargetPointPosition();
        if (fiber_lag_idxs.first <= lag_idx && lag_idx < fiber_lag_idxs.second)
        {
            X_target[0] += velocity * dt;
        }
    }
    return;
} // update_target_point_positions
