// update_springs_vp_aforce.cpp: valveless suction pumping by an applied force
// (mode FORCE_VP of example IB/11, Using IB Software).
//
// The driven piece is vp_aforce_512 (structure 0): the actuator's points,
// top wall then bottom wall, joined across the tube by "springs" whose force
// function index is 1. Force function 1 (applied_force in main.cpp) returns
// the tension Fmag*phase, with Fmag = params[0] from the .spring file and
// phase = params[1], which this function SETS before each time step to
//     0.5*(1 + sin(2 pi f t - pi/2)),
// between 0 (the tube at rest) and 1 (full squeeze), once per period. The
// tension pulls each top point toward the bottom point under it, so the
// walls are pushed together by a force, not moved to a position: how far
// they go depends on Fmag, the tube's stiffness and the fluid.
//
// Each spring is stored with its "master" point, the top point; the bottom
// points have no spring spec. By convention params[0] is a stiffness and
// params[1] a rest length, but a force function of your own may read them
// as anything (chapter 9b); here they are a force and a phase.
//
// Changes from the course version (Forced-tube-pump, 2014):
//   * The frequency comes from the input file (FRE) through main.cpp.
//   * The phase is written through a reference into every spring of the
//     point (the course version changed getParameters()[0][1], the first
//     spring only, which is the same thing here because each point masters
//     one spring).
//   * The loop uses the current IBAMR style (a range-based for loop and
//     nullptr).

#include "update_springs_vp_aforce.h"

#include <ibamr/IBSpringForceSpec.h>

#include <ibtk/LMesh.h>
#include <ibtk/LNode.h>

#include <cmath>
#include <utility>
#include <vector>

// Set up application namespace declarations
#include <ibamr/app_namespaces.h>

void
update_springs_vp_aforce(Pointer<PatchHierarchy<NDIM> > hierarchy,
                         LDataManager* const l_data_manager,
                         const double current_time,
                         const double /*dt*/,
                         const double freq)
{
    const int finest_ln = hierarchy->getFinestLevelNumber();

    // The phase of the applied force at this time.
    const double phase = 0.5 * (1.0 + std::sin(2.0 * M_PI * freq * current_time - M_PI / 2.0));

    // The Lagrangian index range of the driven piece: [first, second).
    const std::pair<int, int> muscle_idxs = l_data_manager->getLagrangianStructureIndexRange(0, finest_ln);

    // The Lagrangian mesh of the finest level: local nodes and ghost nodes.
    Pointer<LMesh> mesh = l_data_manager->getLMesh(finest_ln);
    std::vector<LNode*> nodes = mesh->getLocalNodes();
    nodes.insert(nodes.end(), mesh->getGhostNodes().begin(), mesh->getGhostNodes().end());

    for (LNode* const node : nodes)
    {
        IBSpringForceSpec* const spring_spec = node->getNodeDataItem<IBSpringForceSpec>();
        if (spring_spec == nullptr) continue; // not the master of any spring

        const int lag_idx = node->getLagrangianIndex();
        if (muscle_idxs.first <= lag_idx && lag_idx < muscle_idxs.second)
        {
            // spring[0] is Fmag and spring[1] the phase; the & makes "spring"
            // a reference to the numbers stored in the spec, not a copy.
            for (std::vector<double>& spring : spring_spec->getParameters())
            {
                spring[1] = phase;
            }
        }
    }
    return;
} // update_springs_vp_aforce
