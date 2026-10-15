#!/bin/bash
# Puma (University of Arizona HPC) job script for example IB/13 (the three-level version).
# Submit from this folder with:  sbatch job.slurm
#SBATCH --job-name=ib13-carotid
#SBATCH --account=lauram9          # replace with your PI's group name
#SBATCH --partition=standard
#SBATCH --nodes=1
#SBATCH --ntasks=16
#SBATCH --mem-per-cpu=4gb
#SBATCH --time=06:00:00
#SBATCH --output=%x-%j.out

# The same compiler and MPI modules that were used to build IBAMR.
module load gnu13 openmpi5
# Sets IBAMR_ROOT and the library paths. Change the path if IBAMR is
# installed somewhere else, for example in a shared group folder.
source ~/autoibamr/configuration/enable.sh

cd "$SLURM_SUBMIT_DIR"
# The finer grid: regenerate the walls and the input for it first (the horse case; use --case human for the human one).
python3 vessel_walls.py --case horse --fine 2 && python3 make_input.py horse
mpirun -np "$SLURM_NTASKS" ./build/main2d input2d.horse
