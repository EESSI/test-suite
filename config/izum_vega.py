# WARNING: for CPU autodetect to work correctly you need to
# 1. Either use ReFrame >= 4.3.3 or temporarily change the 'launcher' for each partition to srun
# 2. Either use ReFrame >= 4.3.3 or run from a clone of the ReFrame repository
# 3. Temporarily change the 'access' field for the GPU partition to
# 'access':  ['-p gpu', '--export=None', '--gres=gpu:1'],

# Without this, the autodetect job fails because
# 1. A missing mpirun command
# 2. An incorrect directory structure is assumed when preparing the stagedir for the autodetect job
# 3. Vega doesn't allow submission to the GPU partition without requesting at least one GPU (change #2)

# Related issues
# 1. https://github.com/reframe-hpc/reframe/issues/2926
# 2. https://github.com/reframe-hpc/reframe/issues/2914

import os

from eessi.testsuite.common_config import common_logging_config, common_general_config, common_eessi_init
from eessi.testsuite.constants import *  # noqa: F403

# This config will write all staging, output and logging to subdirs under this prefix
# Override with RFM_PREFIX environment variable
reframe_prefix = os.path.join(os.environ['HOME'], 'reframe_runs')

# This is an example configuration file
site_configuration = {
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
                        'source %s' % common_eessi_init(),
                        # Pass job environment variables like $PATH, etc., into job steps
                        'export SLURM_EXPORT_ENV=ALL',
                        # Needed when using srun launcher
                        # 'export SLURM_MPI_TYPE=pmix',  # WARNING: this broke the GROMACS on Vega
                        # Avoid https://github.com/EESSI/software-layer/issues/136
                        # Can be taken out once we don't care about old OpenMPI versions anymore (pre-4.1.1)
                        'export OMPI_MCA_pml=ucx',
                    ],
                    'launcher': 'mpirun',
                    # Use --export=None to avoid that login environment is passed down to submitted jobs
                    'access': ['-p cpu', '--export=None'],
                    'environs': ['default'],
                    'max_jobs': 120,
                    'resources': [
                        {
                            'name': 'memory',
                            'options': ['--mem={size}'],
                        }
                    ],
                    'features': [
                        FEATURES[CPU],
                    ] + list(SCALES.keys()),
                    'extras': {
                        # Make sure to round down, otherwise a job might ask for more mem than is available
                        # per node
                        # NB: Vega's MaxMemPerNode is set to 256000, but this MUST be a MB/MiB units mistake
                        # Most likely, it is 256 GB, so 256*1E9/(1024*1024) MiB
                        'mem_per_node': 244140  # in MiB
                    },
                    'descr': 'CPU partition Standard, see https://en-doc.vega.izum.si/architecture/'
                },
                # {
                #     'name': 'gpu',
                #     'scheduler': 'slurm',
                #     'prepare_cmds': [
                #         'source %s' % common_eessi_init(),
                #         # Pass job environment variables like $PATH, etc., into job steps
                #         'export SLURM_EXPORT_ENV=ALL',
                #         # Needed when using srun launcher
                #         # 'export SLURM_MPI_TYPE=pmix',  # WARNING: this broke the GROMACS on Vega
                #         # Avoid https://github.com/EESSI/software-layer/issues/136
                #         # Can be taken out once we don't care about old OpenMPI versions anymore (pre-4.1.1)
                #         'export OMPI_MCA_pml=ucx',
                #     ],
                #     'launcher': 'mpirun',
                #     # Use --export=None to avoid that login environment is passed down to submitted jobs
                #     'access': ['-p gpu', '--export=None'],
                #     'environs': ['default'],
                #     'max_jobs': 60,
                #     'devices': [
                #         {
                #             'type': DEVICE_TYPES[GPU],
                #             'num_devices': 4,
                #         }
                #     ],
                #     'resources': [
                #         {
                #             'name': '_rfm_gpu',
                #             'options': ['--gpus-per-node={num_gpus_per_node}'],
                #         },
                #         {
                #             'name': 'memory',
                #             'options': ['--mem={size}'],
                #         }
                #     ],
                #     'features': [
                #         FEATURES[GPU],
                #     ] + list(SCALES.keys()),
                #     'extras': {
                #         # Make sure to round down, otherwise a job might ask for more mem than is available
                #         # per node
                #         'mem_per_node': 476.837 * 1024  # in MiB (should be checked, its unclear from slurm.conf)
                #     },
                #     'descr': 'GPU partition, see https://en-doc.vega.izum.si/architecture/'
                # },
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
    'logging': common_logging_config(reframe_prefix),
    'general': [
        {
            # Enable automatic detection of CPU architecture for each partition
            # See https://reframe-hpc.readthedocs.io/en/stable/configure.html#auto-detecting-processor-information
            'remote_detect': True,
            **common_general_config(reframe_prefix)
        }
    ],
}
