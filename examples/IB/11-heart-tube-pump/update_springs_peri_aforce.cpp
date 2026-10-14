// update_springs_peri_aforce.cpp: peristalsis by an applied force (mode
// FORCE_PERI of example IB/11, Using IB Software).
//
// The driven piece is peri_aforce_512 (structure 0): the middle 0.32 m of
// the tube, top wall then bottom wall, joined across the tube by "springs"
// with force function index 2. Force function 2 (applied_force in main.cpp)
// returns the tension Fmag*phase; this function SETS phase for each spring
// before each time step to a Gaussian wave packet
//     phase = exp(-(x - xc)^2 / w^2),
// where x is the spring's position along the piece (the point's number times
// ds) and the packet's centre xc moves along the piece at the wave speed c,
// starting a little before the piece at the beginning of every period:
//     xc = c * (time since the start of this period) - 0.15 * lperi.
// "We will determine the time since the beginning of the pulse using
// time - floor(time/period)*period; the pulse number is floor(time/period)"
// (the 2014 note). One packet per period crosses the piece; the squeeze it
// makes runs along the tube and pushes the fluid ahead of it.
//
// Changes from the course version (the 2014 lecture's update_springs_peri_aforce):
//   * The frequency comes from the input file (FRE) through main.cpp.
//   * The lecture's loop over previous pulses used an undefined variable c
//     (meant: speed) and added packets that had long left the piece; one
//     packet per period is the same thing without the loop.
//   * The packet's width w (m) and speed (piece lengths per period) come
//     from the input file (PERI_WIDTH, PERI_SPEED) through main.cpp. The
//     2014 code had 0.005 m and 1.3 hard-coded; the lecture used 0.025 m
//     and 1.0. With the 2014 code's narrow packet and Fmag = 4 the walls
//     met and crossed at the first pinch; see README.md for the values
//     that run.
//   * The phase is written through a reference into every spring of the
//     point, and the loop uses the current IBAMR style.
// The 2014 code shipped a different peristalsis instead: a travelling wave
// of spring STIFFNESS with a short rest length (update_springs_peri_kwave.cpp,
// mode STIFFNESS_PERI), which limits how far the walls close.

#include "update_springs_peri_aforce.h"

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
update_springs_peri_aforce(Pointer<PatchHierarchy<NDIM> > hierarchy,
                           LDataManager* const l_data_manager,
                           const double current_time,
                           const double /*dt*/,
                           const double freq,
                           const double peri_width,
                           const double peri_speed)
{
    const int finest_ln = hierarchy->getFinestLevelNumber();

    // The Lagrangian index range of the driven piece: [first, second). Its
    // springs are stored with the top points, the first half of the range.
    const std::pair<int, int> muscle_idxs = l_data_manager->getLagrangianStructureIndexRange(0, finest_ln);
    const int n_springs = (muscle_idxs.second - muscle_idxs.first) / 2;
    const double lperi = n_springs * pump::ds; // length of the driven piece (m)

    // The wave packet at this time.
    const double period = 1.0 / freq;                       // one packet per period
    const double ww = peri_width;                           // width of the Gaussian wave packet (m)
    const double speed = peri_speed * lperi / period;       // wave speed (m/s)
    const int pulse_number = static_cast<int>(std::floor(current_time / period)); // number of pulses so far
    const double pulse_time = current_time - pulse_number * period;               // time since this pulse began
    const double xc = speed * pulse_time - 0.15 * lperi;    // centre of the packet, from the piece's left end

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
            const double x = (lag_idx - muscle_idxs.first) * pump::ds; // the spring's position along the piece
            const double phase = std::exp(-(x - xc) * (x - xc) / (ww * ww));
            for (std::vector<double>& spring : spring_spec->getParameters())
            {
                spring[1] = phase; // spring[0] is Fmag, from the .spring file
            }
        }
    }
    return;
} // update_springs_peri_aforce
