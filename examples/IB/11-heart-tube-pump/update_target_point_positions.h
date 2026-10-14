// update_target_point_positions.h: declares the function that squeezes the
// tube with target points (mode TARGET_VP of example IB/11, Using IB Software).
#ifndef included_update_target_point_positions
#define included_update_target_point_positions
// IBAMR 0.16 needs LData.h for LDataManager.h to compile; 0.19 does not.
#include <ibtk/LData.h>
#include <ibtk/LDataManager.h>
#include <PatchHierarchy.h>
/*
 * Set the target positions of the actuator's points (structures 0 and 1) for
 * this time step: both walls of the actuator move toward the centre of the
 * tube and back with a sinusoidal motion at freq Hz. main.cpp calls this
 * before each time step.
 */
void update_target_point_positions(SAMRAI::tbox::Pointer<SAMRAI::hier::PatchHierarchy<NDIM> > hierarchy,
                                   IBTK::LDataManager* l_data_manager,
                                   double current_time,
                                   double dt,
                                   double freq);
#endif // #ifndef included_update_target_point_positions
