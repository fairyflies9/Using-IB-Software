// update_springs_peri_kwave.h: declares the function that drives a travelling
// wave of spring stiffness along the tube (mode STIFFNESS_PERI of example
// IB/11, Using IB Software).
#ifndef included_update_springs_peri_kwave
#define included_update_springs_peri_kwave
// IBAMR 0.16 needs LData.h for LDataManager.h to compile; 0.19 does not.
#include <ibtk/LData.h>
#include <ibtk/LDataManager.h>
#include <PatchHierarchy.h>
/*
 * Set the stiffness (params[0]) of every cross-tube spring of structure 0
 * (peri_kwave_512) to kmax times a Gaussian wave packet that travels along
 * the piece once per period. The springs are ordinary Hookean springs (force
 * function 0) with rest length (1 - pamp)*diameter, so where the wave is
 * they pull the walls to that distance apart. main.cpp calls this before
 * each time step. peri_width is the packet's width (m) and peri_speed its
 * speed in lengths of the driven piece per period (PERI_WIDTH and
 * PERI_SPEED in the input file).
 */
void update_springs_peri_kwave(SAMRAI::tbox::Pointer<SAMRAI::hier::PatchHierarchy<NDIM> > hierarchy,
                               IBTK::LDataManager* l_data_manager,
                               double current_time,
                               double dt,
                               double freq,
                               double peri_width,
                               double peri_speed);
#endif // #ifndef included_update_springs_peri_kwave
