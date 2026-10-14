// update_target_point_positions_peri.h: declares the function that drives a
// travelling wave of target points along the tube (mode TARGET_PERI of
// example IB/11, Using IB Software).
#ifndef included_update_target_point_positions_peri
#define included_update_target_point_positions_peri
// IBAMR 0.16 needs LData.h for LDataManager.h to compile; 0.19 does not.
#include <ibtk/LData.h>
#include <ibtk/LDataManager.h>
#include <PatchHierarchy.h>
/*
 * Set the target positions of the peristalsis pieces (structures 0 and 1)
 * for this time step: a sinusoidal wave of wall displacement travels along
 * the piece at freq waves per second, ramped up over the first half period.
 * main.cpp calls this before each time step.
 */
void update_target_point_positions_peri(SAMRAI::tbox::Pointer<SAMRAI::hier::PatchHierarchy<NDIM> > hierarchy,
                                        IBTK::LDataManager* l_data_manager,
                                        double current_time,
                                        double dt,
                                        double freq);
#endif // #ifndef included_update_target_point_positions_peri
