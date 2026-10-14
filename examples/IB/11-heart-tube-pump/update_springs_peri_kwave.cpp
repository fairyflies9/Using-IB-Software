// update_springs_peri_kwave.cpp: peristalsis by a travelling wave of spring
// stiffness (mode STIFFNESS_PERI of example IB/11, Using IB Software). This
// is the version the 2014 code actually ran.
//
// The driven piece is peri_kwave_512 (structure 0): the middle 0.32 m of the
// tube, top wall then bottom wall, joined across the tube by ordinary Hookean
// springs (force function 0) with stiffness 0 and rest length
// (1 - pamp)*diameter, one fifth of the tube's diameter. Before each time
// step this function SETS each spring's stiffness (params[0]) to
//     kmax * exp(-(x - xc)^2 / w^2),
// a Gaussian wave packet that travels along the piece once per period.
// Where the packet is, the springs are stiff and pull the two walls toward
// their short rest length; elsewhere they are slack. The squeeze cannot go
// further than the rest length, which the applied-force version
// (update_springs_peri_aforce.cpp) does not guarantee.
//
// Changes from the course version (Forced-tube-pump, 2014):
//   * The frequency comes from the input file (FRE) through main.cpp.
//   * The piece's length is computed from the structure instead of a
//     hard-coded lperi = 0.3 (the piece is 0.32 m).
//   * The packet's width w (m) and speed (piece lengths per period) come
//     from the input file (PERI_WIDTH, PERI_SPEED) through main.cpp; the
//     2014 code had 0.005 m and 1.3 hard-coded. With that narrow packet and
//     the 2014 rest length of 2 cm the walls overshot to 4 mm apart at the
//     first pinch and stuck; see README.md for the values that run.
//   * The stiffness is written through a reference into every spring of the
//     point, and the loop uses the current IBAMR style.
// kmax is the 2014 code's: a tenth of a spring constant of 1 N, divided by
// ds, which is 102.4 in file units (about a twentieth of the tube's own
// springs, 2048).

#include "update_springs_peri_kwave.h"

#include "pump_geometry.h"

#include <ibamr/IBSpringForceSpec.h>

#include <ibtk/LMesh.h>
#include <ibtk/LNode.h>

#include <algorithm>
#include <cmath>
#include <utility>
#include <vector>

// Set up application namespace declarations
#include <ibamr/app_namespaces.h>

void
update_springs_peri_kwave(Pointer<PatchHierarchy<NDIM> > hierarchy,
                          LDataManager* const l_data_manager,
                          const double current_time,
                          const double /*dt*/,
                          const double freq,
                          const double peri_width,
                          const double peri_speed)
{
    const int finest_ln = hierarchy->getFinestLevelNumber();

    const std::pair<int, int> muscle_idxs = l_data_manager->getLagrangianStructureIndexRange(0, finest_ln);
    const int n_springs = (muscle_idxs.second - muscle_idxs.first) / 2;
    const double lperi = n_springs * pump::ds; // length of the driven piece (m)

    const double kappa_spring = 1.0;                        // spring constant used for the wave (N)
    const double kmax = (kappa_spring / 10.0) / pump::ds;   // maximum stiffness, in file units (kappa/ds)
    const double period = 1.0 / freq;
    const double ww = peri_width;                           // width of the Gaussian wave packet (m)
    const double speed = peri_speed * lperi / period;       // wave speed (m/s)
    const int pulse_number = static_cast<int>(std::floor(current_time / period));
    const double pulse_time = current_time - pulse_number * period;
    const double xc = speed * pulse_time - 0.15 * lperi;    // centre of the packet, from the piece's left end

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
            const double x = (lag_idx - muscle_idxs.first) * pump::ds;
            const double stiffness = kmax * std::exp(-(x - xc) * (x - xc) / (ww * ww));
            for (std::vector<double>& spring : spring_spec->getParameters())
            {
                spring[0] = stiffness; // spring[1] is the rest length, from the .spring file
            }
        }
    }
    return;
} // update_springs_peri_kwave
