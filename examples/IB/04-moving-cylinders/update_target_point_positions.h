// update_target_point_positions.h: declares the function that moves the
// target points of example IB/04 (moving cylinders, Using IB Software).
//
// The course version included about 20 IBAMR, SAMRAI and PETSc headers here,
// including IBAMR_config.h and IBTK_config.h, which current IBAMR installs no
// longer have, and ibamr/app_namespaces.h, which IBAMR says must not be
// included in header files. This header needs only the three below.

#ifndef included_update_target_point_positions
#define included_update_target_point_positions

// IBAMR 0.16 needs LData.h for LDataManager.h to compile; 0.19 does not.
#include <ibtk/LData.h>
#include <ibtk/LDataManager.h>

#include <PatchHierarchy.h>

/*
 * Move the target points by the distance the cylinders travel in one time
 * step. main.cpp calls this before each time step, with the time at the
 * start of the step (current_time) and the step size (dt).
 */
void update_target_point_positions(SAMRAI::tbox::Pointer<SAMRAI::hier::PatchHierarchy<NDIM> > hierarchy,
                                   IBTK::LDataManager* l_data_manager,
                                   double current_time,
                                   double dt);

#endif // #ifndef included_update_target_point_positions
