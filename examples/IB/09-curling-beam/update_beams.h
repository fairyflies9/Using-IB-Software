// update_beams.h: declares the function that changes the preferred curvature
// of the beams of example IB/09 (the curling beam, Using IB Software).
//
// Like update_target_point_positions.h of IB/07, this header needs only the
// three includes below; the course version included about 20.

#ifndef included_update_beams
#define included_update_beams

// IBAMR 0.16 needs LData.h for LDataManager.h to compile; 0.19 does not.
#include <ibtk/LData.h>
#include <ibtk/LDataManager.h>

#include <PatchHierarchy.h>

/*
 * Set the preferred curvature (the "mesh-dependent curvature" C = (C1, C2)
 * of chapter 10) of every beam of structure 0 to that of a quarter circle
 * whose radius grows linearly from 0 at t = 0 to beam_length/(pi/2) at
 * t = T_curl, so that the beam curls from straight into a quarter circle
 * over T_curl seconds and then holds. main.cpp calls this before each time
 * step, with the time at the start of the step (current_time) and the step
 * size (dt).
 */
void update_beams(SAMRAI::tbox::Pointer<SAMRAI::hier::PatchHierarchy<NDIM> > hierarchy,
                  IBTK::LDataManager* l_data_manager,
                  double current_time,
                  double dt,
                  double T_curl);

#endif // #ifndef included_update_beams
