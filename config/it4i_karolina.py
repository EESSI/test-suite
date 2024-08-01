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
            'name': 'karolina',
            'descr': 'Karolina, a EuroHPC JU system',
            'modules_system': 'lmod',
            'hostnames': ['login*', 'acn*', 'cn*'],
            'prefix': reframe_prefix,
            'partitions': [
                {
                    'name': 'qcpu',
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
                        # Work around "Failed to modify UD QP to INIT on mlx5_0: Operation not permitted" issue
                        # until we can resolve this through an LMOD hook in host_injections.
                        # (then these OMPI_MCA_btl & mtl can be removed again)
                        # See https://github.com/EESSI/software-layer/issues/456#issuecomment-2107755266
                        'export OMPI_MCA_mtl="^ofi"',
                        'export OMPI_MCA_btl="^ofi"',
                    ],
                    'launcher': 'mpirun',
                    # Use --export=None to avoid that login environment is passed down to submitted jobs
                    'access': ['-p qcpu', '-A DD-23-96', '--export=None'],
                    'environs': ['default'],
                    'max_jobs': 120,
                    'features': [
                        FEATURES[CPU],
                    ] + list(SCALES.keys()),
                    'extras': {
                        # Make sure to round down, otherwise a job might ask for more mem than is available
                        # per node
                        'mem_per_node': 235520  # in MiB
                    },
                    'descr': 'CPU Universal Compute Nodes, see https://docs.it4i.cz/karolina/hardware-overview/'
                },
                # We don't have GPU budget on Karolina at this time
                # {
                #     'name': 'qgpu',
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
                #     'access':  ['-p gpu', '-A DD-23-96', '--export=None'],
                #     'environs': ['default'],
                #     'max_jobs': 60,
                #     'devices': [
                #         {
                #             'type': DEVICE_TYPES[GPU],
                #             'num_devices': 8,
                #         }
                #     ],
                #     'resources': [
                #         {
                #             'name': '_rfm_gpu',
                #             'options': ['--gpus-per-node={num_gpus_per_node}'],
                #         }
                #     ],
                #     'features': [
                #         FEATURES[GPU],
                #     ] + list(SCALES.keys()),
                #     'descr': 'GPU partition with accelerated nodes, https://docs.it4i.cz/karolina/hardware-overview/'
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
