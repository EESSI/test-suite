#!/bin/bash

#example job script

#SBATCH --job-name="rfm_job"
#SBATCH --ntasks=8
#SBATCH --ntasks-per-node=8
#SBATCH --cpus-per-task=1
#SBATCH --output=rfm_job.out
#SBATCH --error=rfm_job.err
#SBATCH --time=0:30:0
#SBATCH --clusters=doduo

module load vsc-mympirun
source /cvmfs/software.eessi.io/versions/2023.06/init/bash
module load LAMMPS/2Aug2023_update2-foss-2023a-kokkos

export OMP_NUM_THREADS=1

mympirun --hybrid 8 lmp -in in.lj
