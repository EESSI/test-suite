import os

from eessi.testsuite.common_config import common_logging_config
from eessi.testsuite.constants import *  # noqa: F403

# This config will write all staging, output (and logging with --save-log-files) to subdirs under this prefix
# Override with --prefix
reframe_prefix = f'{os.environ.get("HOME")}/reframe_runs'

# This is an example configuration file
site_configuration = {
    'general': [
        {
            # Enable automatic detection of CPU architecture for each partition
            # See https://reframe-hpc.readthedocs.io/en/stable/configure.html#auto-detecting-processor-information
            'remote_detect': True,
            'save_log_files': True,
        }
    ],
    'systems': [
        {
            'name': 'vega',
            'descr': 'Vega, a EuroHPC JU system',
            'modules_system': 'lmod',
            'hostnames': ['vglogin*', 'cn*', 'gn*'],
            'prefix': reframe_prefix,
            'partitions': [
                {
                    'name': 'cpu',
                    'scheduler': 'slurm',
                    'prepare_cmds': [
                        'source /cvmfs/pilot.eessi-hpc.org/latest/init/bash',
                        # Pass job environment variables like $PATH, etc., into job steps
                        'export SLURM_EXPORT_ENV=ALL',
                        # Needed when using srun launcher
                        # 'export SLURM_MPI_TYPE=pmix',  # WARNING: this broke the GROMACS on Vega
                        # Avoid https://github.com/EESSI/software-layer/issues/136
                        # Can be taken out once we don't care about old OpenMPI versions anymore (pre-4.1.1)
                        'export OMPI_MCA_pml=ucx',
                    ],
                    'launcher': 'mpirun',  # Needs to be temporarily changed to srun for cpu autodetection
                    # Use --export=None to avoid that login environment is passed down to submitted jobs
                    'access':  ['-p cpu', '--export=None'],
                    'environs': ['default'],
                    'max_jobs': 120,
                    'features': [
                        FEATURES[CPU],
                    ],
                    'descr': 'CPU partition Standard, see https://en-doc.vega.izum.si/architecture/'
                },
                {
                    'name': 'gpu',
                    'scheduler': 'slurm',
                    'prepare_cmds': [
                        'source /cvmfs/pilot.eessi-hpc.org/latest/init/bash',
                        # Pass job environment variables like $PATH, etc., into job steps
                        'export SLURM_EXPORT_ENV=ALL',
                        # Needed when using srun launcher
                        # 'export SLURM_MPI_TYPE=pmix',  # WARNING: this broke the GROMACS on Vega
                        # Avoid https://github.com/EESSI/software-layer/issues/136
                        # Can be taken out once we don't care about old OpenMPI versions anymore (pre-4.1.1)
                        'export OMPI_MCA_pml=ucx',
                    ],
                    'launcher': 'mpirun',  # Needs to be temporarily changed to srun for cpu autodetection
                    # Use --export=None to avoid that login environment is passed down to submitted jobs
                    'access':  ['-p gpu', '--export=None'],
                    'environs': ['default'],
                    'max_jobs': 60,
                    'devices': [
                        {
                            'type': DEVICE_TYPES[GPU],
                            'num_devices': 4,
                        }
                    ],
                    'resources': [
                        {
                            'name': '_rfm_gpu',
                            'options': ['--gpus-per-node={num_gpus_per_node}'],
                        }
                    ],
                    'features': [
                        FEATURES[GPU],
                    ],
                    'descr': 'GPU partition, see https://en-doc.vega.izum.si/architecture/'
                },
            ]
        },
    ],
    'environments': [
        {
            'name': 'default',
            'cc': 'cc',
            'cxx': '',
            'ftn': '',
        },
    ],
    'logging': common_logging_config,
}
