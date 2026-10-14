// update_springs_vp_aforce.h: declares the function that sets the phase of
// the applied suction-pumping force (mode FORCE_VP of example IB/11, Using IB
// Software).
#ifndef included_update_springs_vp_aforce
#define included_update_springs_vp_aforce
// IBAMR 0.16 needs LData.h for LDataManager.h to compile; 0.19 does not.
#include <ibtk/LData.h>
#include <ibtk/LDataManager.h>
#include <PatchHierarchy.h>
/*
 * Set the phase parameter (params[1]) of every cross-tube "spring" of
 * structure 0 (vp_aforce_512) to 0.5*(1 + sin(2 pi f t - pi/2)); the force
 * function applied_force in main.cpp multiplies it by Fmag (params[0]).
 * main.cpp calls this before each time step.
 */
void update_springs_vp_aforce(SAMRAI::tbox::Pointer<SAMRAI::hier::PatchHierarchy<NDIM> > hierarchy,
                              IBTK::LDataManager* l_data_manager,
                              double current_time,
                              double dt,
                              double freq);
#endif // #ifndef included_update_springs_vp_aforce
