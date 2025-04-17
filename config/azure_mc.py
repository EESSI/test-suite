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
from eessi.testsuite.constants import EXTRAS, FEATURES, SCALES

# This config will write all staging, output and logging to subdirs under this prefix
# Override with RFM_PREFIX environment variable
reframe_prefix = os.path.join(os.environ['HOME'], 'reframe_runs')

# AWS CITC site configuration
site_configuration = {
    'systems': [
        {
            'name': 'Magic_Castle_Azure',
            'descr': 'Magic Castle build and test environment on Azure',
            'modules_system': 'lmod',
            'hostnames': ['login.*', '.*-node'],
            'prefix': reframe_prefix,
            'partitions': [
                {
                    'name': 'x86_64-amd-zen4-node',
                    'access': ['--partition=x86-64-amd-zen4-node', '--export=NONE'],
                    'descr': 'Zen4, 16 cores, 30 GB',
                    'prepare_cmds': [
                        # Avoid
                        # https://www.eessi.io/docs/known_issues/eessi-2023.06/#eessi-production-repository-v202306
                        'export OMPI_MCA_btl=^uct,ofi'
                        'export OMPI_MCA_pml=ucx'
                        'export OMPI_MCA_mtl=^ofi'
                        # Use override to avoid fallback to zen3
                        'export EESSI_SOFTWARE_SUBDIR_OVERRIDE=x86_64/amd/zen4',
                        common_eessi_init(),
                        # Required when using srun as launcher with --export=NONE in partition access,
                        # in order to ensure job steps inherit environment. It doesn't hurt to define
                        # this even if srun is not used
                        'export SLURM_EXPORT_ENV=ALL'
                    ],
                    'extras': {
                        # For some reason, we cannot ask for the full amount configured as RealMemory in
                        # /etc/slurm/nodes.conf, so we ask slightly less
                        EXTRAS.MEM_PER_NODE: 767480
                    },
                },
                {
                    'name': 'aarch64-neoverse-N1-16c-62gb',
                    'access': ['--partition=aarch64-neoverse-n1-node', '--export=NONE'],
                    'descr': 'Neoverse N1, 16 cores, 62 GiB',
                    'prepare_cmds': [
                        common_eessi_init(),
                        # Required when using srun as launcher with --export=NONE in partition access,
                        # in order to ensure job steps inherit environment. It doesn't hurt to define
                        # this even if srun is not used
                        'export SLURM_EXPORT_ENV=ALL'
                    ],
                    'extras': {
                        # For some reason, we cannot ask for the full amount configured as RealMemory in
                        # /etc/slurm/nodes.conf, so we ask slightly less
                        EXTRAS.MEM_PER_NODE: 63480
                    },
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
        FEATURES.CPU
    ] + list(SCALES.keys()),
    'resources': [
        {
            'name': 'memory',
            'options': ['--mem={size}'],
        }
    ],
    'max_jobs': 1,
}
for system in site_configuration['systems']:
    for partition in system['partitions']:
        partition.update(partition_defaults)
