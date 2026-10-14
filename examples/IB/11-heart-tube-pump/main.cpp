// Copyright (c) 2002-2014, Boyce Griffith
// All rights reserved.
//
// Redistribution and use in source and binary forms, with or without
// modification, are permitted provided that the following conditions are met:
//
//    * Redistributions of source code must retain the above copyright notice,
//      this list of conditions and the following disclaimer.
//
//    * Redistributions in binary form must reproduce the above copyright
//      notice, this list of conditions and the following disclaimer in the
//      documentation and/or other materials provided with the distribution.
//
//    * Neither the name of The University of North Carolina nor the names of
//      its contributors may be used to endorse or promote products derived from
//      this software without specific prior written permission.
//
// THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
// AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
// IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
// ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
// LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
// CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
// SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
// INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
// CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
// ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
// POSSIBILITY OF SUCH DAMAGE.
//
// Adapted from IBAMR examples/IB/explicit/ex1 by Laura A. Miller for the
// "Using IB Software" tutorials (example IB/11, the heart-tube pump). It is
// the program of IB/01 plus:
//   * two spring force functions of your own, registered with the force
//     generator under the force function indices 1 and 2 (the fifth column
//     of a .spring file), which turn a "spring" into an applied force;
//   * one call per time step to an update function that moves target points
//     or changes spring parameters, chosen by the input key ACTUATION.
//
// Changes from the course version (Forced-tube-pump, 2014, Makefile build):
//   * IBTKInit replaces PetscInitialize + SAMRAIManager::startup()/shutdown().
//   * The deprecated IBAMR_config.h and IBTK_config.h includes are removed.
//   * IBTK::rel_equal_eps and IBTK_MPI replace MathUtilities and SAMRAI_MPI.
//   * The actuation mode is an input-file key instead of commented-out calls,
//     and the pumping frequency FRE is read from the input file instead of
//     being repeated as "freq = 1.0" in every update function; so are the
//     peristaltic packet's width and speed (PERI_WIDTH, PERI_SPEED).
//   * The peristaltic force function is the lecture's F*phase; the 2014 code
//     added an ad-hoc penalty term there (see README.md).
// Tested with IBAMR 0.16.0 and 0.19.0.

// Config files
#include <SAMRAI_config.h>

// Headers for basic PETSc functions
#include <petscsys.h>

// Headers for basic SAMRAI objects
#include <BergerRigoutsos.h>
#include <CartesianGridGeometry.h>
#include <LoadBalancer.h>
#include <StandardTagAndInitialize.h>

// Headers for application-specific algorithm/data structure objects
#include <ibamr/IBExplicitHierarchyIntegrator.h>
#include <ibamr/IBMethod.h>
#include <ibamr/IBStandardForceGen.h>
#include <ibamr/IBStandardInitializer.h>
#include <ibamr/INSCollocatedHierarchyIntegrator.h>
#include <ibamr/INSStaggeredHierarchyIntegrator.h>

#include <ibtk/AppInitializer.h>
#include <ibtk/IBTKInit.h>
#include <ibtk/IBTK_MPI.h>
#include <ibtk/LData.h>
#include <ibtk/LDataManager.h>
#include <ibtk/muParserCartGridFunction.h>
#include <ibtk/muParserRobinBcCoefs.h>

#include <cstdio>

// Set up application namespace declarations
#include <ibamr/app_namespaces.h>

// The functions that drive the pump, one per actuation mode.
#include "update_springs_peri_aforce.h"
#include "update_springs_peri_kwave.h"
#include "update_springs_vp_aforce.h"
#include "update_target_point_positions.h"
#include "update_target_point_positions_peri.h"

// Function prototypes
void output_data(Pointer<PatchHierarchy<NDIM> > patch_hierarchy,
                 Pointer<INSHierarchyIntegrator> navier_stokes_integrator,
                 LDataManager* l_data_manager,
                 const int iteration_num,
                 const double loop_time,
                 const string& data_dump_dirname);

/*
 * A spring force function of our own: an applied force.
 *
 * IBAMR calls a spring force function once per spring per force evaluation
 * with R, the current distance between the spring's two points, and params,
 * the numbers from that spring's line of the .spring file (as many as you
 * wrote). It returns the "tension" T: the force on the first point, directed
 * toward the second point; the second point gets -T (IBSpringForceFunctions.h).
 * The default function (index 0) returns params[0]*(R - params[1]), a Hookean
 * spring with stiffness params[0] and rest length params[1].
 *
 * Here the two numbers mean something else: params[0] is a force magnitude
 * Fmag and params[1] is a phase that the update function sets every step
 * (0.5*(1 + sin(2 pi f t - pi/2)) for the suction pump, a travelling Gaussian
 * for peristalsis). The tension is Fmag*phase whatever R is: a prescribed
 * force that pulls the two walls of the tube toward each other.
 */
inline double
applied_force(double /*R*/, const double* params, int /*lag_mastr_idx*/, int /*lag_slave_idx*/)
{
    const double F = params[0];
    const double phase_fun = params[1];
    return F * phase_fun;
} // applied_force

/*
 * Its derivative with respect to R, which IBAMR uses when it builds the
 * Jacobian of the forces (implicit time stepping, chapter 15). The tension
 * does not depend on R, so the derivative is zero. Passing nullptr instead
 * would make IBAMR estimate it by finite differences, which gives the same
 * answer more slowly.
 */
inline double
applied_force_deriv(double /*R*/, const double* /*params*/, int /*lag_mastr_idx*/, int /*lag_slave_idx*/)
{
    return 0.0;
} // applied_force_deriv

/*******************************************************************************
 * For each run, the input filename and restart information (if needed) must   *
 * be given on the command line.  For non-restarted case, command line is:     *
 *                                                                             *
 *    executable <input file name>                                             *
 *                                                                             *
 * For restarted run, command line is:                                         *
 *                                                                             *
 *    executable <input file name> <restart directory> <restart number>        *
 *                                                                             *
 *******************************************************************************/

int
main(int argc, char* argv[])
{
    // Initialize MPI, PETSc, SAMRAI and IBAMR. IBTKInit also shuts them down
    // when it goes out of scope at the end of main().
    IBTKInit ibtk_init(argc, argv, MPI_COMM_WORLD);

    { // cleanup dynamically allocated objects prior to shutdown

        // Parse command line options, set some standard options from the input
        // file, initialize the restart database (if this is a restarted run),
        // and enable file logging.
        Pointer<AppInitializer> app_initializer = new AppInitializer(argc, argv, "IB.log");
        Pointer<Database> input_db = app_initializer->getInputDatabase();

        // Get various standard options set in the input file.
        const bool dump_viz_data = app_initializer->dumpVizData();
        const int viz_dump_interval = app_initializer->getVizDumpInterval();
        const bool uses_visit = dump_viz_data && app_initializer->getVisItDataWriter();

        const bool is_from_restart = app_initializer->isFromRestart();
        const bool dump_restart_data = app_initializer->dumpRestartData();
        const int restart_dump_interval = app_initializer->getRestartDumpInterval();
        const string restart_dump_dirname = app_initializer->getRestartDumpDirectory();

        const bool dump_postproc_data = app_initializer->dumpPostProcessingData();
        const int postproc_data_dump_interval = app_initializer->getPostProcessingDataDumpInterval();
        const string postproc_data_dump_dirname = app_initializer->getPostProcessingDataDumpDirectory();
        if (dump_postproc_data && (postproc_data_dump_interval > 0) && !postproc_data_dump_dirname.empty())
        {
            Utilities::recursiveMkdir(postproc_data_dump_dirname);
        }

        const bool dump_timer_data = app_initializer->dumpTimerData();
        const int timer_dump_interval = app_initializer->getTimerDumpInterval();

        // How the pump is driven (ACTUATION in the input file) and how fast
        // (FRE, the pumping frequency in Hz, which the input file also uses
        // to set the viscosity from the Womersley number).
        const string actuation = input_db->getStringWithDefault("ACTUATION", "TARGET_VP");
        const double freq = input_db->getDouble("FRE");
        // The peristaltic wave packet (modes FORCE_PERI and STIFFNESS_PERI):
        // its width in m and its speed in lengths of the driven piece per
        // period. The 2014 code had 0.005 m and 1.3 hard-coded; the 2014
        // lecture used 0.025 m and 1.0.
        const double peri_width = input_db->getDoubleWithDefault("PERI_WIDTH", 0.025);
        const double peri_speed = input_db->getDoubleWithDefault("PERI_SPEED", 1.3);
        if (actuation != "TARGET_VP" && actuation != "TARGET_PERI" && actuation != "FORCE_VP" &&
            actuation != "FORCE_PERI" && actuation != "STIFFNESS_PERI")
        {
            TBOX_ERROR("Unsupported ACTUATION: " << actuation << "\n"
                                                 << "Valid options are: TARGET_VP, TARGET_PERI, FORCE_VP, "
                                                    "FORCE_PERI, STIFFNESS_PERI");
        }
        pout << "Heart-tube pump: ACTUATION = " << actuation << ", pumping frequency " << freq << " Hz\n";
        if (actuation == "FORCE_PERI" || actuation == "STIFFNESS_PERI")
        {
            pout << "  wave packet: width " << peri_width << " m, speed " << peri_speed
                 << " piece lengths per period\n";
        }

        // Create major algorithm and data objects that comprise the
        // application.  These objects are configured from the input database
        // and, if this is a restarted run, from the restart database.
        Pointer<INSHierarchyIntegrator> navier_stokes_integrator;
        const string solver_type =
            app_initializer->getComponentDatabase("Main")->getStringWithDefault("solver_type", "STAGGERED");
        if (solver_type == "STAGGERED")
        {
            navier_stokes_integrator = new INSStaggeredHierarchyIntegrator(
                "INSStaggeredHierarchyIntegrator",
                app_initializer->getComponentDatabase("INSStaggeredHierarchyIntegrator"));
        }
        else if (solver_type == "COLLOCATED")
        {
            navier_stokes_integrator = new INSCollocatedHierarchyIntegrator(
                "INSCollocatedHierarchyIntegrator",
                app_initializer->getComponentDatabase("INSCollocatedHierarchyIntegrator"));
        }
        else
        {
            TBOX_ERROR("Unsupported solver type: " << solver_type << "\n"
                                                   << "Valid options are: COLLOCATED, STAGGERED");
        }
        Pointer<IBMethod> ib_method_ops = new IBMethod("IBMethod", app_initializer->getComponentDatabase("IBMethod"));
        Pointer<IBHierarchyIntegrator> time_integrator =
            new IBExplicitHierarchyIntegrator("IBHierarchyIntegrator",
                                              app_initializer->getComponentDatabase("IBHierarchyIntegrator"),
                                              ib_method_ops,
                                              navier_stokes_integrator);
        Pointer<CartesianGridGeometry<NDIM> > grid_geometry = new CartesianGridGeometry<NDIM>(
            "CartesianGeometry", app_initializer->getComponentDatabase("CartesianGeometry"));
        Pointer<PatchHierarchy<NDIM> > patch_hierarchy = new PatchHierarchy<NDIM>("PatchHierarchy", grid_geometry);
        Pointer<StandardTagAndInitialize<NDIM> > error_detector =
            new StandardTagAndInitialize<NDIM>("StandardTagAndInitialize",
                                               time_integrator,
                                               app_initializer->getComponentDatabase("StandardTagAndInitialize"));
        Pointer<BergerRigoutsos<NDIM> > box_generator = new BergerRigoutsos<NDIM>();
        Pointer<LoadBalancer<NDIM> > load_balancer =
            new LoadBalancer<NDIM>("LoadBalancer", app_initializer->getComponentDatabase("LoadBalancer"));
        Pointer<GriddingAlgorithm<NDIM> > gridding_algorithm =
            new GriddingAlgorithm<NDIM>("GriddingAlgorithm",
                                        app_initializer->getComponentDatabase("GriddingAlgorithm"),
                                        error_detector,
                                        box_generator,
                                        load_balancer);

        // Configure the IB solver.
        Pointer<IBStandardInitializer> ib_initializer = new IBStandardInitializer(
            "IBStandardInitializer", app_initializer->getComponentDatabase("IBStandardInitializer"));
        ib_method_ops->registerLInitStrategy(ib_initializer);
        Pointer<IBStandardForceGen> ib_force_fcn = new IBStandardForceGen();
        // Register the applied force under the force function indices that
        // the .spring files use: 1 for the suction pump (vp_aforce_512.spring),
        // 2 for the peristaltic force (peri_aforce_512.spring). Index 0, the
        // Hookean spring, stays as it is and serves the tube's own springs.
        ib_force_fcn->registerSpringForceFunction(1, &applied_force, &applied_force_deriv);
        ib_force_fcn->registerSpringForceFunction(2, &applied_force, &applied_force_deriv);
        ib_method_ops->registerIBLagrangianForceFunction(ib_force_fcn);

        // Create Eulerian initial condition specification objects.
        if (input_db->keyExists("VelocityInitialConditions"))
        {
            Pointer<CartGridFunction> u_init = new muParserCartGridFunction(
                "u_init", app_initializer->getComponentDatabase("VelocityInitialConditions"), grid_geometry);
            navier_stokes_integrator->registerVelocityInitialConditions(u_init);
        }

        if (input_db->keyExists("PressureInitialConditions"))
        {
            Pointer<CartGridFunction> p_init = new muParserCartGridFunction(
                "p_init", app_initializer->getComponentDatabase("PressureInitialConditions"), grid_geometry);
            navier_stokes_integrator->registerPressureInitialConditions(p_init);
        }

        // Create Eulerian boundary condition specification objects (when necessary).
        const IntVector<NDIM>& periodic_shift = grid_geometry->getPeriodicShift();
        vector<RobinBcCoefStrategy<NDIM>*> u_bc_coefs(NDIM);
        if (periodic_shift.min() > 0)
        {
            for (unsigned int d = 0; d < NDIM; ++d)
            {
                u_bc_coefs[d] = nullptr;
            }
        }
        else
        {
            for (unsigned int d = 0; d < NDIM; ++d)
            {
                ostringstream bc_coefs_name_stream;
                bc_coefs_name_stream << "u_bc_coefs_" << d;
                const string bc_coefs_name = bc_coefs_name_stream.str();

                ostringstream bc_coefs_db_name_stream;
                bc_coefs_db_name_stream << "VelocityBcCoefs_" << d;
                const string bc_coefs_db_name = bc_coefs_db_name_stream.str();

                u_bc_coefs[d] = new muParserRobinBcCoefs(
                    bc_coefs_name, app_initializer->getComponentDatabase(bc_coefs_db_name), grid_geometry);
            }
            navier_stokes_integrator->registerPhysicalBoundaryConditions(u_bc_coefs);
        }

        // Create Eulerian body force function specification objects.
        if (input_db->keyExists("ForcingFunction"))
        {
            Pointer<CartGridFunction> f_fcn = new muParserCartGridFunction(
                "f_fcn", app_initializer->getComponentDatabase("ForcingFunction"), grid_geometry);
            time_integrator->registerBodyForceFunction(f_fcn);
        }

        // Set up visualization plot file writers.
        Pointer<VisItDataWriter<NDIM> > visit_data_writer = app_initializer->getVisItDataWriter();
        Pointer<LSiloDataWriter> silo_data_writer = app_initializer->getLSiloDataWriter();
        if (uses_visit)
        {
            ib_initializer->registerLSiloDataWriter(silo_data_writer);
            time_integrator->registerVisItDataWriter(visit_data_writer);
            ib_method_ops->registerLSiloDataWriter(silo_data_writer);
        }

        // Initialize hierarchy configuration and data on all patches.
        time_integrator->initializePatchHierarchy(patch_hierarchy, gridding_algorithm);

        // Deallocate initialization objects.
        ib_method_ops->freeLInitStrategy();
        ib_initializer.setNull();
        app_initializer.setNull();

        // Print the input database contents to the log file.
        plog << "Input database:\n";
        input_db->printClassData(plog);

        // Write restart data before starting main time integration loop.
        if (dump_restart_data && !is_from_restart)
        {
            pout << "\nWriting restart files...\n\n";
            RestartManager::getManager()->writeRestartFile(restart_dump_dirname, 0);
        }

        // Write out initial visualization data.
        int iteration_num = time_integrator->getIntegratorStep();
        double loop_time = time_integrator->getIntegratorTime();
        if (dump_viz_data && uses_visit)
        {
            pout << "\n\nWriting visualization files...\n\n";
            time_integrator->setupPlotData();
            visit_data_writer->writePlotData(patch_hierarchy, iteration_num, loop_time);
            silo_data_writer->writePlotData(iteration_num, loop_time);
        }

        // Main time step loop.
        double loop_time_end = time_integrator->getEndTime();
        double dt = 0.0;
        while (!IBTK::rel_equal_eps(loop_time, loop_time_end) && time_integrator->stepsRemaining())
        {
            iteration_num = time_integrator->getIntegratorStep();
            loop_time = time_integrator->getIntegratorTime();

            pout << "\n";
            pout << "+++++++++++++++++++++++++++++++++++++++++++++++++++\n";
            pout << "At beginning of timestep # " << iteration_num << "\n";
            pout << "Simulation time is " << loop_time << "\n";

            dt = time_integrator->getMaximumTimeStepSize();

            // Drive the pump: move the actuator's target points, or set the
            // phase (or the stiffness) of the "springs" that carry the applied
            // force, to their values for this time step.
            LDataManager* l_data_manager = ib_method_ops->getLDataManager();
            if (actuation == "TARGET_VP")
            {
                update_target_point_positions(patch_hierarchy, l_data_manager, loop_time, dt, freq);
            }
            else if (actuation == "TARGET_PERI")
            {
                update_target_point_positions_peri(patch_hierarchy, l_data_manager, loop_time, dt, freq);
            }
            else if (actuation == "FORCE_VP")
            {
                update_springs_vp_aforce(patch_hierarchy, l_data_manager, loop_time, dt, freq);
            }
            else if (actuation == "FORCE_PERI")
            {
                update_springs_peri_aforce(patch_hierarchy, l_data_manager, loop_time, dt, freq, peri_width, peri_speed);
            }
            else // STIFFNESS_PERI
            {
                update_springs_peri_kwave(patch_hierarchy, l_data_manager, loop_time, dt, freq, peri_width, peri_speed);
            }

            time_integrator->advanceHierarchy(dt);
            loop_time += dt;

            pout << "\n";
            pout << "At end       of timestep # " << iteration_num << "\n";
            pout << "Simulation time is " << loop_time << "\n";
            pout << "+++++++++++++++++++++++++++++++++++++++++++++++++++\n";
            pout << "\n";

            // At specified intervals, write visualization and restart files,
            // print out timer data, and store hierarchy data for post
            // processing.
            iteration_num += 1;
            const bool last_step = !time_integrator->stepsRemaining();
            if (dump_viz_data && uses_visit && (iteration_num % viz_dump_interval == 0 || last_step))
            {
                pout << "\nWriting visualization files...\n\n";
                time_integrator->setupPlotData();
                visit_data_writer->writePlotData(patch_hierarchy, iteration_num, loop_time);
                silo_data_writer->writePlotData(iteration_num, loop_time);
            }
            if (dump_restart_data && (iteration_num % restart_dump_interval == 0 || last_step))
            {
                pout << "\nWriting restart files...\n\n";
                RestartManager::getManager()->writeRestartFile(restart_dump_dirname, iteration_num);
            }
            if (dump_timer_data && (iteration_num % timer_dump_interval == 0 || last_step))
            {
                pout << "\nWriting timer data...\n\n";
                TimerManager::getManager()->print(plog);
            }
            if (dump_postproc_data && (iteration_num % postproc_data_dump_interval == 0 || last_step))
            {
                output_data(patch_hierarchy,
                            navier_stokes_integrator,
                            ib_method_ops->getLDataManager(),
                            iteration_num,
                            loop_time,
                            postproc_data_dump_dirname);
            }
        }

        // Cleanup Eulerian boundary condition specification objects (when
        // necessary).
        for (unsigned int d = 0; d < NDIM; ++d) delete u_bc_coefs[d];

    } // cleanup dynamically allocated objects prior to shutdown
    return 0;
} // main

// Write the Lagrangian positions X and forces F to ASCII files X.NNNNN and
// F.NNNNN in the data_dump_dirname folder, and print the sum of the forces
// ("integral{F}") to the screen. The files are PETSc ASCII vectors with NDIM
// numbers per Lagrangian point. The chapter on forces reads them in MATLAB.
void
output_data(Pointer<PatchHierarchy<NDIM> > patch_hierarchy,
            Pointer<INSHierarchyIntegrator> /*navier_stokes_integrator*/,
            LDataManager* l_data_manager,
            const int iteration_num,
            const double loop_time,
            const string& data_dump_dirname)
{
    plog << "writing hierarchy data at iteration " << iteration_num << " to disk" << endl;
    plog << "simulation time is " << loop_time << endl;

    string file_name;
    char temp_buf[128];

    // Write Lagrangian data.
    const int finest_hier_level = patch_hierarchy->getFinestLevelNumber();
    PetscViewer viewer;

    Pointer<LData> X_data = l_data_manager->getLData("X", finest_hier_level);
    Vec X_petsc_vec = X_data->getVec();
    Vec X_lag_vec;
    VecDuplicate(X_petsc_vec, &X_lag_vec);
    l_data_manager->scatterPETScToLagrangian(X_petsc_vec, X_lag_vec, finest_hier_level);
    file_name = data_dump_dirname + "/" + "X.";
    std::snprintf(temp_buf, sizeof(temp_buf), "%05d", iteration_num);
    file_name += temp_buf;
    PetscViewerASCIIOpen(PETSC_COMM_WORLD, file_name.c_str(), &viewer);
    VecView(X_lag_vec, viewer);
    PetscViewerDestroy(&viewer);
    VecDestroy(&X_lag_vec);

    Pointer<LData> F_data = l_data_manager->getLData("F", finest_hier_level);
    Vec F_petsc_vec = F_data->getVec();
    Vec F_lag_vec;
    VecDuplicate(F_petsc_vec, &F_lag_vec);
    l_data_manager->scatterPETScToLagrangian(F_petsc_vec, F_lag_vec, finest_hier_level);
    file_name = data_dump_dirname + "/" + "F.";
    std::snprintf(temp_buf, sizeof(temp_buf), "%05d", iteration_num);
    file_name += temp_buf;
    PetscViewerASCIIOpen(PETSC_COMM_WORLD, file_name.c_str(), &viewer);
    VecView(F_lag_vec, viewer);
    PetscViewerDestroy(&viewer);
    VecDestroy(&F_lag_vec);

    // Sum up the forces. Springs, beams and the applied cross-tube forces
    // act in equal and opposite pairs, so only the target-point forces add
    // up: the sum is the force that the fixed parts exert on the fluid.
    double F_sum[NDIM];
    for (unsigned int d = 0; d < NDIM; ++d) F_sum[d] = 0.0;
    PetscInt local_sz;
    VecGetLocalSize(F_petsc_vec, &local_sz);
    double* F_array;
    VecGetArray(F_petsc_vec, &F_array);
    for (PetscInt k = 0; k < local_sz / NDIM; ++k)
    {
        for (unsigned int d = 0; d < NDIM; ++d)
        {
            F_sum[d] += F_array[NDIM * k + d];
        }
    }
    VecRestoreArray(F_petsc_vec, &F_array);
    IBTK_MPI::sumReduction(&F_sum[0], NDIM);
    pout << "integral{F} =";
    for (unsigned int d = 0; d < NDIM; ++d)
    {
        pout << " " << F_sum[d];
    }
    pout << "\n";
    return;
} // output_data
