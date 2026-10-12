// update_springs.h: declares the function that changes the springs of
// example IB/06 (growing springs, Using IB Software).
//
// The course version included about 20 IBAMR, SAMRAI and PETSc headers here,
// including IBAMR_config.h and IBTK_config.h, which current IBAMR installs no
// longer have, and ibamr/app_namespaces.h, which IBAMR says must not be
// included in header files. Its comment, copied from another example, said
// the function updates target point positions. This header needs only the
// three includes below.

#ifndef included_update_springs
#define included_update_springs

// IBAMR 0.16 needs LData.h for LDataManager.h to compile; 0.19 does not.
#include <ibtk/LData.h>
#include <ibtk/LDataManager.h>

#include <PatchHierarchy.h>

/*
 * Lengthen the rest length of every spring by 0.01*dt. main.cpp calls this
 * before each time step, with the time at the start of the step
 * (current_time) and the step size (dt).
 */
void update_springs(SAMRAI::tbox::Pointer<SAMRAI::hier::PatchHierarchy<NDIM> > hierarchy,
                    IBTK::LDataManager* l_data_manager,
                    double current_time,
                    double dt);

#endif // #ifndef included_update_springs
