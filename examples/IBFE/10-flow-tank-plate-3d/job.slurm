#!/bin/bash
# Puma (University of Arizona HPC) job script for example IBFE/10.
# Submit from this folder with:  sbatch job.slurm
# See README.md for the run time of the default END_TIME and of the course
# version's END_TIME = 2.0.
#SBATCH --job-name=ibfe10-flow-tank-plate-3d
#SBATCH --account=lauram9          # replace with your PI's group name
#SBATCH --partition=standard
#SBATCH --nodes=1
#SBATCH --ntasks=4
#SBATCH --mem-per-cpu=4gb
#SBATCH --time=01:00:00
#SBATCH --output=%x-%j.out

# The same compiler and MPI modules that were used to build IBAMR.
module load gnu13 openmpi5
# Sets IBAMR_ROOT and the library paths. Change the path if IBAMR is
# installed somewhere else, for example in a shared group folder.
source ~/autoibamr/configuration/enable.sh

cd "$SLURM_SUBMIT_DIR"
mpirun -np "$SLURM_NTASKS" ./build/main3d input3d
