#!/bin/bash
#SBATCH --time=00:40:00
#SBATCH --output %j.stdout
#SBATCH --error  %j.stderr
module load spack/default gcc/12.3.0 cuda/12.3.0 openmpi/4.1.6 \
            fftw/3.3.10 boost/1.83.0 python/3.12.1
source ../espresso-4.3/venv/bin/activate
srun --cpu-bind=cores python3 madelung.py --size 6 --weak-scaling
srun --cpu-bind=cores python3 madelung.py --size 9 --strong-scaling
deactivate
