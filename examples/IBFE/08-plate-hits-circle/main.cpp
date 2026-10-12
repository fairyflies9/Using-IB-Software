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
//    * Neither the name of New York University nor the names of its
//      contributors may be used to endorse or promote products derived from
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
// Course example from the UNC IBFE tutorials (2020, "7-IBFE-Plate-Circle"),
// revised for the "Using IB Software" tutorials as example IBFE/08.
//
// Two structures, each with its own mesh, share a periodic box of fluid. A
// plate (the "beam", 0.5 long and 0.031 wide) stands upright below a disc
// of radius 0.25. A tether (target) force pushes the plate up toward the disc
// for the first second; then the plate is released and coasts. The disc has
// no tether: it moves only because the fluid pushed by the plate moves it.
// Both meshes were made with Trelis (Cubit) and saved as ExodusII files.
//
// Changes from the course version:
//   * IBTKInit starts and stops MPI, PETSc, libMesh and SAMRAI.
//   * The deprecated IBAMR_config.h and IBTK_config.h includes are removed,
//     with several headers that were included but not used.
//   * libMesh::Order replaces the old libMeshEnums::Order.
//   * IBTK::rel_equal_eps replaces MathUtilities<double>::equalEps.
//   * Commented-out code (coordinate mappings and an output function that
//     handled only one mesh) is removed.
//   * The mesh files, shear modulus, and the tether's stiffness, speed and
//     end time can be set in input2d.
//   * The two ExodusII files are named beam_output.ex2 and circle_output.ex2.
//   * Restarted runs save and reload the finite element data of both parts
//     and append to both ExodusII files, as in IBAMR's own examples. Unlike
//     those examples, only processor 0 reopens the ExodusII files; otherwise
//     a restart on more than one process leaves files that cannot be read.
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

// Headers for basic libMesh objects
#include <libmesh/boundary_info.h>
#include <libmesh/equation_systems.h>
#include <libmesh/exodusII_io.h>
#include <libmesh/mesh.h>

// Headers for application-specific algorithm/data structure objects
#include <ibamr/IBExplicitHierarchyIntegrator.h>
#include <ibamr/IBFEMethod.h>
#include <ibamr/INSCollocatedHierarchyIntegrator.h>
#include <ibamr/INSStaggeredHierarchyIntegrator.h>

#include <ibtk/AppInitializer.h>
#include <ibtk/IBTKInit.h>
#include <ibtk/IBTK_MPI.h>
#include <ibtk/libmesh_utilities.h>
#include <ibtk/muParserCartGridFunction.h>
#include <ibtk/muParserRobinBcCoefs.h>

#include <memory>
#include <vector>

// Set up application namespace declarations
#include <ibamr/app_namespaces.h>

// Elasticity model data.
namespace ModelData
{
// Shear modulus of the neo-Hookean material of both parts, the stiffness of
// the tether that pushes the plate, and the speed and duration of the push.
// All can be changed in input2d (SHEAR_MODULUS, KAPPA_S, TETHER_SPEED and
// TETHER_END_TIME).
static double mu = 10.0;
static double kappa_s = 1.0e6;
static double tether_speed = 0.25;
static double tether_end_time = 1.0;

// Target ("tether") force on the plate (part 0), per unit reference area.
//   s is the reference (initial) position of a point in the plate:
//     s(0) is its x-coordinate and s(1) is its y-coordinate.
//   X is where that point is now.
// Until tether_end_time each point is pulled toward a target that moves up
// with speed tether_speed. After that the target is X itself, so the force is
// zero and the plate moves only with the fluid.
void
beam_tether_force_function(VectorValue<double>& F,
                           const TensorValue<double>& /*FF*/,
                           const libMesh::Point& X,
                           const libMesh::Point& s,
                           Elem* const /*elem*/,
                           const std::vector<const std::vector<double>*>& /*var_data*/,
                           const std::vector<const std::vector<VectorValue<double> >*>& /*grad_var_data*/,
                           double time,
                           void* /*ctx*/)
{
    libMesh::Point s_target = X;
    if (time < tether_end_time)
    {
        s_target(0) = s(0);
        s_target(1) = s(1) + tether_speed * time;
    }
    F = kappa_s * (s_target - X);
    return;
} // beam_tether_force_function

// Stress tensor functions, used by both parts. The first Piola-Kirchhoff
// stress of the neo-Hookean material is split into two parts. The deviatoric
// part is mu*FF. The dilational part, -mu*FF^{-T}, makes the undeformed
// structure stress-free: at FF = I the two parts cancel.
void
PK1_dev_stress_function(TensorValue<double>& PP,
                        const TensorValue<double>& FF,
                        const libMesh::Point& /*X*/,
                        const libMesh::Point& /*s*/,
                        Elem* const /*elem*/,
                        const std::vector<const std::vector<double>*>& /*var_data*/,
                        const std::vector<const std::vector<VectorValue<double> >*>& /*grad_var_data*/,
                        double /*time*/,
                        void* /*ctx*/)
{
    PP = mu * FF;
    return;
} // PK1_dev_stress_function

void
PK1_dil_stress_function(TensorValue<double>& PP,
                        const TensorValue<double>& FF,
                        const libMesh::Point& /*X*/,
                        const libMesh::Point& /*s*/,
                        Elem* const /*elem*/,
                        const std::vector<const std::vector<double>*>& /*var_data*/,
                        const std::vector<const std::vector<VectorValue<double> >*>& /*grad_var_data*/,
                        double /*time*/,
                        void* /*ctx*/)
{
    PP = -mu * tensor_inverse_transpose(FF, NDIM);
    return;
} // PK1_dil_stress_function
} // namespace ModelData
using namespace ModelData;

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
    // Initialize MPI, PETSc, libMesh, SAMRAI and IBAMR. IBTKInit also shuts
    // them down when it goes out of scope at the end of main().
    IBTKInit ibtk_init(argc, argv, MPI_COMM_WORLD);
    const LibMeshInit& init = ibtk_init.getLibMeshInit();

    { // cleanup dynamically allocated objects prior to shutdown

        // Parse command line options, set some standard options from the input
        // file, initialize the restart database (if this is a restarted run),
        // and enable file logging.
        Pointer<AppInitializer> app_initializer = new AppInitializer(argc, argv, "IB.log");
        Pointer<Database> input_db = app_initializer->getInputDatabase();

        // Get various standard options set in the input file. Each part gets
        // its own ExodusII file: viz_IB2d/beam_output.ex2 and
        // viz_IB2d/circle_output.ex2.
        const bool dump_viz_data = app_initializer->dumpVizData();
        const int viz_dump_interval = app_initializer->getVizDumpInterval();
        const bool uses_visit = dump_viz_data && app_initializer->getVisItDataWriter();
        const bool uses_exodus = dump_viz_data && !app_initializer->getExodusIIFilename().empty();
        const string beam_exodus_filename = app_initializer->getExodusIIFilename("beam_");
        const string circle_exodus_filename = app_initializer->getExodusIIFilename("circle_");

        const bool dump_restart_data = app_initializer->dumpRestartData();
        const int restart_dump_interval = app_initializer->getRestartDumpInterval();
        const string restart_dump_dirname = app_initializer->getRestartDumpDirectory();
        const string restart_read_dirname = app_initializer->getRestartReadDirectory();
        const int restart_restore_num = app_initializer->getRestartRestoreNumber();

        const bool dump_timer_data = app_initializer->dumpTimerData();
        const int timer_dump_interval = app_initializer->getTimerDumpInterval();

        // Model parameters from the input file.
        // (ModelData:: is written out because another "mu" is also visible here.)
        ModelData::mu = input_db->getDoubleWithDefault("SHEAR_MODULUS", ModelData::mu);
        ModelData::kappa_s = input_db->getDoubleWithDefault("KAPPA_S", ModelData::kappa_s);
        ModelData::tether_speed = input_db->getDoubleWithDefault("TETHER_SPEED", ModelData::tether_speed);
        ModelData::tether_end_time = input_db->getDoubleWithDefault("TETHER_END_TIME", ModelData::tether_end_time);

        // Read the two meshes. libMesh chooses the reader from the file name;
        // .e is an ExodusII file. The order of the meshes in the vector sets
        // the part numbers: the plate is part 0 and the disc is part 1.
        Mesh beam_mesh(init.comm(), NDIM);
        beam_mesh.read(input_db->getStringWithDefault("BEAM_MESH_FILENAME", "beam.e"));
        beam_mesh.prepare_for_use();
        Mesh circle_mesh(init.comm(), NDIM);
        circle_mesh.read(input_db->getStringWithDefault("CIRCLE_MESH_FILENAME", "circle.e"));
        circle_mesh.prepare_for_use();
        std::vector<MeshBase*> meshes = { &beam_mesh, &circle_mesh };

        // Create major algorithm and data objects that comprise the
        // application.  These objects are configured from the input database
        // and, if this is a restarted run, from the restart database.
        Pointer<INSHierarchyIntegrator> navier_stokes_integrator;
        const string solver_type = app_initializer->getComponentDatabase("Main")->getString("solver_type");
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
        Pointer<IBFEMethod> ib_method_ops =
            new IBFEMethod("IBFEMethod",
                           app_initializer->getComponentDatabase("IBFEMethod"),
                           meshes,
                           app_initializer->getComponentDatabase("GriddingAlgorithm")->getInteger("max_levels"),
                           /*register_for_restart*/ true,
                           restart_read_dirname,
                           restart_restore_num);
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

        // Configure the IBFE solver. The last argument of each register call
        // is the part number. Both parts get the same stress functions; only
        // the plate (part 0) gets the tether force.
        IBFEMethod::LagBodyForceFcnData beam_tether_force_data(beam_tether_force_function);
        IBFEMethod::PK1StressFcnData PK1_dev_stress_data(PK1_dev_stress_function);
        IBFEMethod::PK1StressFcnData PK1_dil_stress_data(PK1_dil_stress_function);
        PK1_dev_stress_data.quad_order =
            Utility::string_to_enum<libMesh::Order>(input_db->getStringWithDefault("PK1_DEV_QUAD_ORDER", "THIRD"));
        PK1_dil_stress_data.quad_order =
            Utility::string_to_enum<libMesh::Order>(input_db->getStringWithDefault("PK1_DIL_QUAD_ORDER", "FIRST"));
        ib_method_ops->registerLagBodyForceFunction(beam_tether_force_data, 0);
        ib_method_ops->registerPK1StressFunction(PK1_dev_stress_data, 0);
        ib_method_ops->registerPK1StressFunction(PK1_dil_stress_data, 0);
        ib_method_ops->registerPK1StressFunction(PK1_dev_stress_data, 1);
        ib_method_ops->registerPK1StressFunction(PK1_dil_stress_data, 1);
        ib_method_ops->initializeFEEquationSystems();
        EquationSystems* beam_equation_systems = ib_method_ops->getFEDataManager(0)->getEquationSystems();
        EquationSystems* circle_equation_systems = ib_method_ops->getFEDataManager(1)->getEquationSystems();

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

        // Set up visualization plot file writers: one ExodusII writer per part.
        Pointer<VisItDataWriter<NDIM> > visit_data_writer = app_initializer->getVisItDataWriter();
        if (uses_visit)
        {
            time_integrator->registerVisItDataWriter(visit_data_writer);
        }
        std::unique_ptr<ExodusII_IO> beam_exodus_io =
            uses_exodus ? std::make_unique<ExodusII_IO>(beam_mesh) : nullptr;
        std::unique_ptr<ExodusII_IO> circle_exodus_io =
            uses_exodus ? std::make_unique<ExodusII_IO>(circle_mesh) : nullptr;

        // A restarted run adds its time steps to the existing ExodusII files.
        // Only processor 0 writes the files, so only processor 0 reopens them:
        // libMesh 1.7.8 reopens them on every processor when told to append,
        // and with more than one process the files are then damaged (they can
        // no longer be read).
        if (uses_exodus)
        {
            const bool from_restart = RestartManager::getManager()->isFromRestart();
            beam_exodus_io->append(from_restart && IBTK_MPI::getRank() == 0);
            circle_exodus_io->append(from_restart && IBTK_MPI::getRank() == 0);
        }

        // Initialize hierarchy configuration and data on all patches.
        ib_method_ops->initializeFEData();
        time_integrator->initializePatchHierarchy(patch_hierarchy, gridding_algorithm);

        // Deallocate initialization objects.
        app_initializer.setNull();

        // Print the input database contents to the log file.
        plog << "Input database:\n";
        input_db->printClassData(plog);

        // Write out initial visualization data.
        int iteration_num = time_integrator->getIntegratorStep();
        double loop_time = time_integrator->getIntegratorTime();
        if (dump_viz_data)
        {
            pout << "\n\nWriting visualization files...\n\n";
            if (uses_visit)
            {
                time_integrator->setupPlotData();
                visit_data_writer->writePlotData(patch_hierarchy, iteration_num, loop_time);
            }
            if (uses_exodus)
            {
                beam_exodus_io->write_timestep(
                    beam_exodus_filename, *beam_equation_systems, iteration_num / viz_dump_interval + 1, loop_time);
                circle_exodus_io->write_timestep(circle_exodus_filename,
                                                 *circle_equation_systems,
                                                 iteration_num / viz_dump_interval + 1,
                                                 loop_time);
            }
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
            time_integrator->advanceHierarchy(dt);
            loop_time += dt;

            pout << "\n";
            pout << "At end       of timestep # " << iteration_num << "\n";
            pout << "Simulation time is " << loop_time << "\n";
            pout << "+++++++++++++++++++++++++++++++++++++++++++++++++++\n";
            pout << "\n";

            // At specified intervals, write visualization and restart files
            // and print out timer data.
            iteration_num += 1;
            const bool last_step = !time_integrator->stepsRemaining();
            if (dump_viz_data && (iteration_num % viz_dump_interval == 0 || last_step))
            {
                pout << "\nWriting visualization files...\n\n";
                if (uses_visit)
                {
                    time_integrator->setupPlotData();
                    visit_data_writer->writePlotData(patch_hierarchy, iteration_num, loop_time);
                }
                if (uses_exodus)
                {
                    beam_exodus_io->write_timestep(beam_exodus_filename,
                                                   *beam_equation_systems,
                                                   iteration_num / viz_dump_interval + 1,
                                                   loop_time);
                    circle_exodus_io->write_timestep(circle_exodus_filename,
                                                     *circle_equation_systems,
                                                     iteration_num / viz_dump_interval + 1,
                                                     loop_time);
                }
            }
            if (dump_restart_data && (iteration_num % restart_dump_interval == 0 || last_step))
            {
                pout << "\nWriting restart files...\n\n";
                RestartManager::getManager()->writeRestartFile(restart_dump_dirname, iteration_num);
                ib_method_ops->writeFEDataToRestartFile(restart_dump_dirname, iteration_num);
            }
            if (dump_timer_data && (iteration_num % timer_dump_interval == 0 || last_step))
            {
                pout << "\nWriting timer data...\n\n";
                TimerManager::getManager()->print(plog);
            }
        }

        // Cleanup Eulerian boundary condition specification objects (when
        // necessary).
        for (unsigned int d = 0; d < NDIM; ++d) delete u_bc_coefs[d];

    } // cleanup dynamically allocated objects prior to shutdown
    return 0;
} // main
