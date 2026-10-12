// update_target_point_positions.h: moving target points for example IB/08.
//
// From the 2014 version of the glycocalyx example (IBAMR-Examples), revised
// for the "Using IB Software" tutorials.

#ifndef included_update_target_point_positions
#define included_update_target_point_positions

// LData.h is needed before LDataManager.h with IBAMR 0.16 ("invalid use of
// incomplete type 'class IBTK::LData'" otherwise).
#include <ibtk/LData.h>
#include <ibtk/LDataManager.h>

#include <ibamr/app_namespaces.h>

/*
 * Move the target points of structure 0 (the glycocalyx fiber) in the
 * x-direction by velocity*dt. Called once per time step, before the step is
 * taken, so that during the step from t to t + dt each target point sits at
 * its position for time t + dt.
 */
void update_target_point_positions(Pointer<PatchHierarchy<NDIM> > hierarchy,
                                   LDataManager* l_data_manager,
                                   double current_time,
                                   double dt,
                                   double velocity);

#endif //#ifndef included_update_target_point_positions
