#!/bin/bash
#SBATCH -p genoa
#SBATCH --ntasks-per-node 192
#SBATCH -N 8
#SBATCH --exclusive
#SBATCH --time 00:30:00


# Loading modules
module load 2023
module load OpenFOAM/v2312-foss-2023a


# Copy files
cp -r ~/OpenFOAM/wp2-validation/incompressible/icoFoam/cavity3D/8M/fixedTol ./fixedTol_${SLURM_NTASKS}
cd fixedTol_${SLURM_NTASKS}
echo $(pwd)

# Sourcing FOAM_BASH

source $FOAM_BASH

foamDictionary -entry numberOfSubdomains -set $SLURM_NTASKS system/decomposeParDict

# Generating a block mesh with patches and cells.
blockMesh 2>&1 | tee log.blockMesh

# Using this instead of decomposePar since decomposePar is actually serial itself.
mpirun -np $SLURM_NTASKS redistributePar -decompose -parallel 2>&1 | tee log.decompose

# Renumbering the mesh helps the normalise weights in the coefficient matrix such that the matrix is more conditioned
# for a solution.
mpirun -np $SLURM_NTASKS renumberMesh -parallel -overwrite 2>&1 | tee log.renumberMesh

# Running the application, here icoFoam
mpirun -np $SLURM_NTASKS icoFoam -parallel 2>&1 | tee log.icoFoam
