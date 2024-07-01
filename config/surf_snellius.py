# WARNING: for CPU autodetect to work correctly you need to
# 1. Either use ReFrame >= 4.3.3 or temporarily change the 'launcher' for each partition to srun
# 2. Either use ReFrame >= 4.3.3 or run from a clone of the ReFrame repository
# 3. Temporarily change the 'access' field for the GPU partition to
# 'access':  ['-p gpu', '--export=None', '--exclusive'],

# Without this, the autodetect job fails because
# 1. A missing mpirun command
# 2. An incorrect directory structure is assumed when preparing the stagedir for the autodetect job
# 3. Snellius doesn't allow submission to the GPU partition without requesting at least one GPU

# Related issues
# 1. https://github.com/reframe-hpc/reframe/issues/2926
# 2. https://github.com/reframe-hpc/reframe/issues/2914

import os

from eessi.testsuite.common_config import common_logging_config, common_general_config, common_eessi_init
from eessi.testsuite.constants import *  # noqa: F403

# This config will write all staging, output and logging to subdirs under this prefix
# Override with RFM_PREFIX environment variable
reframe_prefix = os.path.join(os.environ['HOME'], 'reframe_runs')

# Jobs that partially fill multiple nodes are not allowed on the GPU partition
valid_scales_snellius_gpu = [s for s in SCALES if s not in ['1_cpn_2_nodes', '1_cpn_4_nodes']]

# This is an example configuration file
site_configuration = {
    'systems': [
        {
            'name': 'snellius',
            'descr': 'Dutch National Supercomputer',
            'modules_system': 'lmod',
            'hostnames': ['int*', 'tcn*', 'hcn*', 'fcn*', 'gcn*', 'srv*'],
            'prefix': reframe_prefix,
            'stagedir': f'/scratch-shared/{os.environ.get("USER")}/reframe_output/staging',
            'partitions': [
                {
                    'name': 'rome',
                    'scheduler': 'slurm',
                    'prepare_cmds': ['source %s' % common_eessi_init()],
                    'launcher': 'mpirun',
                    'access': ['-p rome', '--export=None'],
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
                        'mem_per_node': 229376  # in MiB
                    },
                    'descr': 'AMD Rome CPU partition with native EESSI stack'
                },
                {
                    'name': 'genoa',
                    'scheduler': 'slurm',
                    'prepare_cmds': ['source %s' % common_eessi_init()],
                    'launcher': 'mpirun',
                    'access': ['-p genoa', '--export=None'],
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
                        'mem_per_node': 344064  # in MiB
                    },
                    'descr': 'AMD Genoa CPU partition with native EESSI stack'
                },

                {
                    'name': 'gpu',
                    'scheduler': 'slurm',
                    'prepare_cmds': ['source %s' % common_eessi_init()],
                    'launcher': 'mpirun',
                    'access': ['-p gpu', '--export=None'],
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
                        },
                        {
                            'name': 'memory',
                            'options': ['--mem={size}'],
                        }
                    ],
                    'features': [
                        FEATURES[GPU],
                        FEATURES[ALWAYS_REQUEST_GPUS],
                    ] + valid_scales_snellius_gpu,
                    'extras': {
                        GPU_VENDOR: GPU_VENDORS[NVIDIA],
                        # Make sure to round down, otherwise a job might ask for more mem than is available
                        # per node
                        'mem_per_node': 491520  # in MiB
                    },
                    'descr': 'Nvidia A100 GPU partition with native EESSI stack'
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
