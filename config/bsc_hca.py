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

# Most RISC-V partitions only have EESSI mounted on one or two nodes, so limit valid scales
valid_scales_arriesgado = ['1_core', '2_cores', '4_cores']
valid_scales_bananaf3 = ['1_core', '2_cores', '4_cores', '8_cores']
valid_scales_premier = ['1_core', '2_cores', '1_node', '2_nodes']

# This is an example configuration file
site_configuration = {
    'systems': [
        {
            'name': 'HCA',
            'descr': 'BSC RISC-V test cluster',
            'modules_system': 'lmod',
            # Just accept any hostname. List of hostnames can only get outdated, and this is a single-system config
            # file anyway.
            'hostnames': ['.*'],
            'prefix': reframe_prefix,
            'stagedir': os.path.join(os.environ['HOME'], 'reframe_output', 'staging'),
            'partitions': [
                {
                    'name': 'arriesgado',
                    'scheduler': 'slurm',
                    'prepare_cmds': [
                        'export EESSI_VERSION_OVERRIDE=2025.06-001',
                        'source /cvmfs/software.eessi.io/versions/%s/init/bash' % os.getenv('EESSI_VERSION', '2025.06')
                    ],
                    'launcher': 'mpirun',
                    'sched_options': {
                        'use_nodes_option': True,
                    },
                    'access': ['-p arriesgado-hirsute', '--nodelist arriesgado-1', '--export=None', '--time=1:00:00'],
                    'environs': ['default'],
                    'max_jobs': 2,
                    'resources': [
                        {
                            'name': 'memory',
                            'options': ['--mem={size}'],
                        }
                    ],
                    'features': [
                        FEATURES.CPU,
                    ] + valid_scales_arriesgado,
                    'extras': {
                        # Make sure to round down, otherwise a job might ask for more mem than is available
                        # per node
                        EXTRAS.MEM_PER_NODE: 15986  # in MiB
                    },
                    'descr': 'HiFive Unmatched RISC-V board'
                },
                {
                    'name': 'banana',
                    'scheduler': 'slurm',
                    'prepare_cmds': [
                        'export EESSI_VERSION_OVERRIDE=2025.06-001',
                        'source /cvmfs/software.eessi.io/versions/%s/init/bash' % os.getenv('EESSI_VERSION', '2025.06')
                    ],
                    'launcher': 'mpirun',
                    'sched_options': {
                        'use_nodes_option': True,
                    },
                    'access': ['-p bananaf3-k6.6', '--nodelist bananaf3-8', '--export=None', '--time=1:00:00'],
                    'environs': ['default'],
                    'max_jobs': 2,
                    'resources': [
                        {
                            'name': 'memory',
                            'options': ['--mem={size}'],
                        }
                    ],
                    'features': [
                        FEATURES.CPU,
                    ] + valid_scales_bananaf3,
                    'extras': {
                        # Make sure to round down, otherwise a job might ask for more mem than is available
                        # per node
                        EXTRAS.MEM_PER_NODE: 15883  # in MiB
                    },
                    'descr': 'Banana Pi F3 board'
                },
                {
                    'name': 'premier',
                    'scheduler': 'slurm',
                    'prepare_cmds': [
                        'export EESSI_VERSION_OVERRIDE=2025.06-001',
                        'source /cvmfs/software.eessi.io/versions/%s/init/bash' % os.getenv('EESSI_VERSION', '2025.06')
                    ],
                    'launcher': 'mpirun',
                    'sched_options': {
                        'use_nodes_option': True,
                    },
                    'access': ['-p premier', '--export=None', '--time=1:00:00'],
                    'environs': ['default'],
                    'max_jobs': 8,
                    'resources': [
                        {
                            'name': 'memory',
                            'options': ['--mem={size}'],
                        }
                    ],
                    'features': [
                        FEATURES.CPU,
                    ] + valid_scales_premier,
                    'extras': {
                        # Make sure to round down, otherwise a job might ask for more mem than is available
                        # per node
                        EXTRAS.MEM_PER_NODE: 32062  # in MiB
                    },
                    'descr': 'HiFive Premier P550 board'
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
