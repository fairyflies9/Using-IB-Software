// update_springs.cpp: makes the springs of example IB/06 (growing springs,
// Using IB Software) longer.
//
// Before each time step, main.cpp calls update_springs(), which adds
// 0.01*dt to the rest length of every spring, so every rest length grows at
// 0.01 m/s.
//
// IBAMR stores each spring with its "master" point, the first point listed
// for it in the .spring file. A point's IBSpringForceSpec holds the springs
// that the point is the master of, and getParameters()[k] holds the
// parameters of its spring k: [0] is the stiffness and [1] is the rest
// length. Points that are not the master of any spring have no
// IBSpringForceSpec.
//
// The rest length must be changed through a reference, as below. Older copies
// of this example (and the lecture slides) did
//     double resting_length = spring_spec->getParameters()[0][1];
//     resting_length += 0.01*dt;
// which changes only a local copy, so the springs never grew. IBAMR's force
// routine (IBStandardForceGen) reads the rest length from the spec itself, so
// a change made here is used from the next force evaluation on. IBAMR's
// documentation of getParameters() (in ibamr/IBSpringForceSpec.h) says that
// you may change the parameter values but must not resize the vectors.
//
// Changes from the course version (UNC, 2018):
//   * The IBAMR_config.h and IBTK_config.h includes are removed (see
//     update_springs.h).
//   * The loop now changes every spring of each master point. The course
//     version changed only the first one, getParameters()[0]. In this fiber
//     every point is the master of at most one spring, so the result is the
//     same, but the loop below also works when a point is the master of
//     several springs.
//   * Unused variables, an unused index range and old commented-out code are
//     removed, and the loop uses the current IBAMR style (a range-based for
//     loop and nullptr).

#include "update_springs.h"

#include <ibamr/IBSpringForceSpec.h>

#include <ibtk/LMesh.h>
#include <ibtk/LNode.h>

#include <vector>

// Set up application namespace declarations
#include <ibamr/app_namespaces.h>

void
update_springs(Pointer<PatchHierarchy<NDIM> > hierarchy,
               LDataManager* const l_data_manager,
               const double /*current_time*/,
               const double dt)
{
    const int finest_ln = hierarchy->getFinestLevelNumber();

    static const double growth_rate = 0.01; // how fast each rest length grows (m/s)

    // Get the LMesh (which we assume to be associated with the finest level of
    // the patch hierarchy). Note that we need to update both "local" and
    // "ghost" node data.
    Pointer<LMesh> mesh = l_data_manager->getLMesh(finest_ln);
    std::vector<LNode*> nodes = mesh->getLocalNodes();
    nodes.insert(nodes.end(), mesh->getGhostNodes().begin(), mesh->getGhostNodes().end());

    // Update the rest lengths in their associated spring specs.
    for (LNode* const node : nodes)
    {
        IBSpringForceSpec* const spring_spec = node->getNodeDataItem<IBSpringForceSpec>();
        if (spring_spec == nullptr) continue; // this point is not the master of any spring

        // spring[0] is the stiffness and spring[1] is the rest length. The &
        // makes "spring" a reference to the numbers stored in the spec, not a
        // copy of them.
        for (std::vector<double>& spring : spring_spec->getParameters())
        {
            spring[1] += growth_rate * dt;
        }
    }
    return;
} // update_springs
