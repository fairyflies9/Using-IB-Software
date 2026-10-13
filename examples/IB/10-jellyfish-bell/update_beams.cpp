// update_beams.cpp: drives the jellyfish bell of example IB/10 (Using IB
// Software) by changing the preferred curvature of its beams before every
// time step.
//
// The bell is one curve of 2n+1 points from the left tip (point 0) through
// the apex (point n) to the right tip (point 2n), joined by springs and
// beams. Its shape is set by one number, beta (bell_geometry.h): the open
// bell has beta_0, the contracted bell beta_m. Every period, beta goes
// linearly from beta_0 to beta_m over t_contract (contraction) and back over
// the rest of the period (expansion), as the 2013 course code did:
//     contract:  beta = beta_0 + (beta_m - beta_0) * (pulse_time / t_contract)
//     expand:    beta = beta_m + (beta_0 - beta_m) * ((pulse_time - t_contract) / (period - t_contract))
// (the course wrote the exponent gamma on the time fractions and set it to
// 1). For each point i the preferred curvature is then the second difference
// X_{i-1} - 2 X_i + X_{i+1} of the bell shape for that beta, so the beams
// pull the bell toward that shape; the fluid is pushed out of the bell as it
// contracts and the jellyfish moves up.
//
// Changes from the course version (Example_jellyfish_curvature, 2013):
//   * One curve, tip to tip, instead of an apex point with two sides hanging
//     from it: every interior point has one beam and one spring on each
//     side, including the apex.
//   * The period, the contraction time and beta_0, beta_m come from the input
//     file through main.cpp. The course code had pulse_time =
//     current_time - floor(current_time) (a period of 1) next to a cycle
//     count ptt = floor(current_time/(2*to)) (a period of 2 to); with
//     to = 0.5 the two agree, which is the shipped setting.
//   * The shape is computed once per step for the half bell and mirrored
//     (r -> -r) for the left half, instead of per node.
//   * The points are numbered from the structure's first Lagrangian index,
//     not from the global index, and the loop uses the current IBAMR style.
//   * The curvature is an IBTK::Vector (Point& in the 2018 slides,
//     TinyVector<double, 2>& in 2013).

#include "update_beams.h"

#include "bell_geometry.h"

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
             const double period,
             const double t_contract,
             const double beta_0,
             const double beta_m)
{
    const int finest_ln = hierarchy->getFinestLevelNumber();

    // Where we are in the pulse: the time since this period began.
    const double pulse_time = current_time - std::floor(current_time / period) * period;
    double beta;
    if (pulse_time < t_contract)
    {
        beta = beta_0 + (beta_m - beta_0) * (pulse_time / t_contract); // contract
    }
    else
    {
        beta = beta_m + (beta_0 - beta_m) * ((pulse_time - t_contract) / (period - t_contract)); // expand
    }

    // The bell shape for this beta: the right half, apex (k = 0) to tip (k = n).
    std::vector<double> r, z;
    bell::shape(beta, r, z);

    // The whole curve, left tip (i = 0) to right tip (i = 2n), apex at i = n.
    const int npts = 2 * bell::n + 1;
    std::vector<double> X(npts), Y(npts);
    for (int i = 0; i < npts; ++i)
    {
        const int k = std::abs(i - bell::n);    // distance from the apex, in points
        X[i] = (i < bell::n ? -r[k] : r[k]);    // the left half is the mirror image
        Y[i] = z[k];
    }

    // The Lagrangian index range of the bell: [first, second).
    const std::pair<int, int> bell_idxs = l_data_manager->getLagrangianStructureIndexRange(0, finest_ln);

    // The Lagrangian mesh of the finest level: local nodes and ghost nodes.
    Pointer<LMesh> mesh = l_data_manager->getLMesh(finest_ln);
    std::vector<LNode*> nodes = mesh->getLocalNodes();
    nodes.insert(nodes.end(), mesh->getGhostNodes().begin(), mesh->getGhostNodes().end());

    for (LNode* const node : nodes)
    {
        IBBeamForceSpec* const beam_spec = node->getNodeDataItem<IBBeamForceSpec>();
        if (beam_spec == nullptr) continue; // not the middle point of any beam

        const int lag_idx = node->getLagrangianIndex();
        if (lag_idx < bell_idxs.first || lag_idx >= bell_idxs.second) continue;
        const int i = lag_idx - bell_idxs.first; // the point's number along the bell
        if (i < 1 || i > npts - 2) continue;     // the tips have no beam

        // The preferred second difference at this point, for every beam of
        // the node (normally one).
        for (IBTK::Vector& curv : beam_spec->getMeshDependentCurvatures())
        {
            curv[0] = X[i - 1] - 2.0 * X[i] + X[i + 1];
            curv[1] = Y[i - 1] - 2.0 * Y[i] + Y[i + 1];
        }
    }
    return;
} // update_beams
