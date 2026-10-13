// update_beams.h: declares the function that changes the preferred curvature
// of the bell's beams in example IB/10 (the jellyfish bell, Using IB Software).

#ifndef included_update_beams
#define included_update_beams

// IBAMR 0.16 needs LData.h for LDataManager.h to compile; 0.19 does not.
#include <ibtk/LData.h>
#include <ibtk/LDataManager.h>

#include <PatchHierarchy.h>

/*
 * Set the preferred curvature of every beam of the bell (structure 0) to the
 * second difference of the bell shape for the control parameter beta(t):
 * beta falls linearly from beta_0 to beta_m over the first t_contract of
 * every period (the bell contracts) and rises back over the rest of it (the
 * bell expands). main.cpp calls this before each time step, with the time at
 * the start of the step (current_time) and the step size (dt).
 */
void update_beams(SAMRAI::tbox::Pointer<SAMRAI::hier::PatchHierarchy<NDIM> > hierarchy,
                  IBTK::LDataManager* l_data_manager,
                  double current_time,
                  double dt,
                  double period,
                  double t_contract,
                  double beta_0,
                  double beta_m);

#endif // #ifndef included_update_beams
