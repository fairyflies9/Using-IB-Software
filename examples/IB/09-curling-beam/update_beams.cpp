// update_beams.cpp: changes the preferred curvature of the beams of example
// IB/09 (the curling beam, Using IB Software) before every time step.
//
// A beam in IBAMR joins three consecutive points X_{i-1}, X_i, X_{i+1} and
// pushes their second difference X_{i-1} - 2 X_i + X_{i+1} toward a preferred
// value C_i = (C1, C2), the "mesh-dependent curvature": the force on the
// middle point is -2 kb (X_{i-1} - 2 X_i + X_{i+1} - C_i) and each neighbor
// gets half of it with the opposite sign (IBStandardForceGen.cpp). C_i is a
// length (ds^2 times the curvature, in m), and it is a vector, so it fixes
// the orientation of the preferred shape, not only its curvature.
//
// Here C_i is the second difference of the points of a quarter circle of
// radius R(t), spaced along it like the points of the beam:
//     X_i = (R sin(phi_i), R (1 - cos(phi_i))),   phi_i = i (pi/2)/(npts-1),
//     C_i = X_{i-1} - 2 X_i + X_{i+1},
// which starts at the origin heading along +x (the clamped end's direction)
// and curls upward. R(t) = R_final * min(t/T_curl, 1) with R_final =
// beam_length/(pi/2), the radius whose quarter circle has the beam's length:
// at t = T_curl the beam's preferred shape is that quarter circle, and before
// that it is a flatter arc with the same spacing (the curvature grows
// linearly in time). This is the course's Example_2Dbeams_curvature ("the
// curvature of a 2D fiber is increased at each time step; at t = 1 it should
// form a quarter circle"), with these changes:
//   * The points are numbered from the structure's first Lagrangian index,
//     not from the global index lag_idx, so the function is right whatever
//     comes before this structure in structure_names (the course version
//     used lag_idx-1, lag_idx, lag_idx+1 and worked only for structure 0).
//   * The angle step is (pi/2)/(npts-1) (npts-1 gaps between npts points);
//     the course version divided by npts.
//   * R_final comes from the beam's length and T_curl from main.cpp instead
//     of the hard-coded 10*pi/2 (a quarter circle of radius 1/(5 pi) at
//     t = 1, which is the same thing for a 0.1 m beam).
//   * Point& (0.19) / TinyVector<double, 2>& (2013): the curvature is an
//     IBTK::Vector in current IBAMR; the course slides showed three
//     versions of this line for three IBAMR generations.
//   * The loop uses the current IBAMR style (a range-based for loop and
//     nullptr) and covers the ghost nodes too, as IB/07 explains.

#include "update_beams.h"

#include <ibamr/IBBeamForceSpec.h>

#include <ibtk/LMesh.h>
#include <ibtk/LNode.h>

#include <cmath>
#include <utility>
#include <vector>

// Set up application namespace declarations
#include <ibamr/app_namespaces.h>

void
update_beams(Pointer<PatchHierarchy<NDIM> > hierarchy,
             LDataManager* const l_data_manager,
             const double current_time,
             const double /*dt*/,
             const double T_curl)
{
    const int finest_ln = hierarchy->getFinestLevelNumber();

    // The Lagrangian index range of the beam: [first, second).
    const std::pair<int, int> beam_idxs = l_data_manager->getLagrangianStructureIndexRange(0, finest_ln);
    const int npts = beam_idxs.second - beam_idxs.first;

    // The beam's length, from the generator (103 points, 0.1 m), and the
    // radius of the quarter circle of that length.
    const double beam_length = 0.1;
    const double R_final = beam_length / (M_PI / 2.0);
    const double R = R_final * std::min(current_time / T_curl, 1.0);
    const double dphi = (M_PI / 2.0) / (npts - 1);

    // The Lagrangian mesh of the finest level: local nodes and ghost nodes.
    Pointer<LMesh> mesh = l_data_manager->getLMesh(finest_ln);
    std::vector<LNode*> nodes = mesh->getLocalNodes();
    nodes.insert(nodes.end(), mesh->getGhostNodes().begin(), mesh->getGhostNodes().end());

    for (LNode* const node : nodes)
    {
        // The beam data stored with this node (it is the master, the middle
        // point, of the beam), or nullptr if the node has no beam.
        IBBeamForceSpec* const beam_spec = node->getNodeDataItem<IBBeamForceSpec>();
        if (beam_spec == nullptr) continue;

        const int lag_idx = node->getLagrangianIndex();
        if (lag_idx < beam_idxs.first || lag_idx >= beam_idxs.second) continue;
        const int i = lag_idx - beam_idxs.first; // the point's number along the beam

        // The three angles of the points i-1, i, i+1 on the quarter circle.
        const double phi0 = (i - 1) * dphi;
        const double phi1 = i * dphi;
        const double phi2 = (i + 1) * dphi;

        // Every beam of this node (normally one): [0] is the first beam,
        // [1] would be the second. getBendingRigidities() would give the
        // stiffnesses the same way, if they were to change too.
        for (IBTK::Vector& curv : beam_spec->getMeshDependentCurvatures())
        {
            curv[0] = R * (std::sin(phi0) - 2.0 * std::sin(phi1) + std::sin(phi2));  // C1
            curv[1] = R * (-std::cos(phi0) + 2.0 * std::cos(phi1) - std::cos(phi2)); // C2
        }
    }
    return;
} // update_beams
