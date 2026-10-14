// update_springs_peri_aforce.h: declares the function that sets the phase of
// the applied peristaltic force (mode FORCE_PERI of example IB/11, Using IB
// Software).
#ifndef included_update_springs_peri_aforce
#define included_update_springs_peri_aforce
// IBAMR 0.16 needs LData.h for LDataManager.h to compile; 0.19 does not.
#include <ibtk/LData.h>
#include <ibtk/LDataManager.h>
#include <PatchHierarchy.h>
/*
 * Set the phase parameter (params[1]) of every cross-tube "spring" of
 * structure 0 (peri_aforce_512) to a Gaussian wave packet that travels along
 * the piece once per period; the force function applied_force in main.cpp
 * multiplies it by Fmag (params[0]). main.cpp calls this before each time
 * step. peri_width is the packet's width (m) and peri_speed its speed in
 * lengths of the driven piece per period (PERI_WIDTH and PERI_SPEED in the
 * input file).
 */
void update_springs_peri_aforce(SAMRAI::tbox::Pointer<SAMRAI::hier::PatchHierarchy<NDIM> > hierarchy,
                                IBTK::LDataManager* l_data_manager,
                                double current_time,
                                double dt,
                                double freq,
                                double peri_width,
                                double peri_speed);
#endif // #ifndef included_update_springs_peri_aforce
