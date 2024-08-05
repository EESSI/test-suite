# WARNING: for CPU autodetect to work correctly you need to
# 1. Either use ReFrame >= 4.3.3 or temporarily change the 'launcher' for each partition to srun
# 2. Either use ReFrame >= 4.3.3 or run from a clone of the ReFrame repository

# Without this, the autodetect job fails because
# 1. A missing mpirun command
# 2. An incorrect directory structure is assumed when preparing the stagedir for the autodetect job

# Related issues
# 1. https://github.com/reframe-hpc/reframe/issues/2926
# 2. https://github.com/reframe-hpc/reframe/issues/2914

import os

from eessi.testsuite.common_config import common_logging_config, common_general_config, common_eessi_init
from eessi.testsuite.constants import FEATURES, SCALES

# This config will write all staging, output and logging to subdirs under this prefix
# Override with RFM_PREFIX environment variable
reframe_prefix = os.path.join(os.environ['HOME'], 'reframe_runs')

# AWS CITC site configuration
site_configuration = {
    'systems': [
        {
            'name': 'Magic_Castle',
            'descr': 'Magic Castle build and test environment on AWS',
            'modules_system': 'lmod',
            'hostnames': ['login*', '*-node'],
            'prefix': reframe_prefix,
            'partitions': [
                {
                    'name': 'x86_64-generic-16c-30gb',
                    'access': ['--partition=x86-64-generic-node', '--export=NONE'],
                    'descr': 'Generic (Haswell), 16 cores, 30 GB',
                },
                {
                    'name': 'x86_64-haswell-16c-30gb',
                    'access': ['--partition=x86-64-intel-haswell-node', '--export=NONE'],
                    'descr': 'Haswell, 16 cores, 30 GB',
                },
                {
                    'name': 'x86_64-skylake-16c-30gb',
                    'access': ['--partition=x86-64-intel-skylake-node', '--export=NONE'],
                    'descr': 'Skylake, 16 cores, 30 GB',
                },
                {
                    'name': 'x86_64-zen2-16c-30gb',
                    'access': ['--partition=x86-64-amd-zen2-node', '--export=NONE'],
                    'descr': 'Zen2, 16 cores, 30 GB',
                },
                {
                    'name': 'x86_64-zen3-16c-30gb',
                    'access': ['--partition=x86-64-amd-zen3-node', '--export=NONE'],
                    'descr': 'Zen3, 16 cores, 30 GiB',
                },
                {
                    'name': 'aarch64-generic-16c-32gb',
                    'access': ['--partition=aarch64-generic-node', '--export=NONE'],
                    'descr': 'Generic (Neoverse N1), 16 cores, 32 GB',
                },
                {
                    'name': 'aarch64-neoverse-V1-16c-32gb',
                    'access': ['--partition=aarch64-neoverse-v1-node', '--export=NONE'],
                    'descr': 'Neoverse V1, 16 cores, 32 GB',
                },
                {
                    'name': 'aarch64-neoverse-N1-16c-32gb',
                    'access': ['--partition=aarch64-neoverse-n1-node', '--export=NONE'],
                    'descr': 'Neoverse N1, 16 cores, 32 GiB',
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

# Add default things to each partition:
partition_defaults = {
    'scheduler': 'slurm',
    'launcher': 'mpirun',
    'environs': ['default'],
    'features': [
        FEATURES['CPU']
    ] + list(SCALES.keys()),
    'prepare_cmds': [
        'source %s' % common_eessi_init(),
        # Required when using srun as launcher with --export=NONE in partition access, in order to ensure job
        # steps inherit environment. It doesn't hurt to define this even if srun is not used
        'export SLURM_EXPORT_ENV=ALL'
    ],
    'extras': {
        # Node types have somewhat varying amounts of memory, but we'll make it easy on ourselves
        # All should _at least_ have this amount (30GB * 1E9 / (1024*1024) = 28610 MiB)
        'mem_per_node': 28610
    },
}
for system in site_configuration['systems']:
    for partition in system['partitions']:
        partition.update(partition_defaults)
