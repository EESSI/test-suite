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

from eessi.testsuite.common_config import common_logging_config, common_eessi_init
from eessi.testsuite.constants import FEATURES

# This config will write all staging, output and logging to subdirs under this prefix
# Override with RFM_PREFIX environment variable
reframe_prefix = os.path.join(os.environ['HOME'], 'reframe_runs')

# AWS CITC site configuration
site_configuration = {
    'systems': [
        {
            'name': 'citc',
            'descr': 'Cluster in the Cloud build and test environment on AWS',
            'modules_system': 'lmod',
            'hostnames': ['mgmt', 'login', 'fair-mastodon*'],
            'prefix': reframe_prefix,
            'partitions': [
                {
                    'name': 'x86_64-haswell-8c-15gb',
                    'access': ['--constraint=shape=c4.2xlarge', '--export=NONE'],
                    'descr': 'Haswell, 8 cores, 15 GiB',
                    'resources': [
                        {
                            'name': 'memory',
                            'options': ['--mem={size}'],
                        }
                    ],
                },
                {
                    'name': 'x86_64-haswell-16c-30gb',
                    'access': ['--constraint=shape=c4.4xlarge', '--export=NONE'],
                    'descr': 'Haswell, 16 cores, 30 GiB',
                    'resources': [
                        {
                            'name': 'memory',
                            'options': ['--mem={size}'],
                        }
                    ],
                },
                {
                    'name': 'x86_64-zen2-8c-16gb',
                    'access': ['--constraint=shape=c5a.2xlarge', '--export=NONE'],
                    'descr': 'Zen2, 8 cores, 16 GiB',
                    'resources': [
                        {
                            'name': 'memory',
                            'options': ['--mem={size}'],
                        }
                    ],
                },
                {
                    'name': 'x86_64-zen2-16c-32gb',
                    'access': ['--constraint=shape=c5a.4xlarge', '--export=NONE'],
                    'descr': 'Zen2, 16 cores, 32 GiB',
                    'resources': [
                        {
                            'name': 'memory',
                            'options': ['--mem={size}'],
                        }
                    ],
                },
                {
                    'name': 'x86_64-zen3-8c-16gb',
                    'access': ['--constraint=shape=c6a.2xlarge', '--export=NONE'],
                    'descr': 'Zen3, 8 cores, 16 GiB',
                    'resources': [
                        {
                            'name': 'memory',
                            'options': ['--mem={size}'],
                        }
                    ],
                },
                {
                    'name': 'X86_64-zen3-16c-32gb',
                    'access': ['--constraint=shape=c6a.4xlarge', '--export=NONE'],
                    'descr': 'Zen3, 16 cores, 32 GiB',
                    'resources': [
                        {
                            'name': 'memory',
                            'options': ['--mem={size}'],
                        }
                    ],
                },
                {
                    'name': 'x86_64-skylake-cascadelake-8c-16gb',
                    'access': ['--constraint=shape=c5.2xlarge', '--export=NONE'],
                    'descr': 'Skylake/Cascade lake, 8 cores, 16 GiB',
                    'resources': [
                        {
                            'name': 'memory',
                            'options': ['--mem={size}'],
                        }
                    ],
                },
                {
                    'name': 'x86_64-skylake-cascadelake-16c-32gb',
                    'access': ['--constraint=shape=c5.4xlarge', '--export=NONE'],
                    'descr': 'Skylake/Cascade lake, 16 cores, 32 GiB',
                    'resources': [
                        {
                            'name': 'memory',
                            'options': ['--mem={size}'],
                        }
                    ],
                },
                {
                    'name': 'x86_64-skylake-cascadelake-8c-16gb-nvme',
                    'access': ['--constraint=shape=c5d.2xlarge', '--export=NONE'],
                    'descr': 'Skylake/Cascade lake, 8 cores, 16 GiB, 200GB NVMe',
                    'resources': [
                        {
                            'name': 'memory',
                            'options': ['--mem={size}'],
                        }
                    ],
                },
                {
                    'name': 'x86_64-icelake-8c-16gb',
                    'access': ['--constraint=shape=c6i.2xlarge', '--export=NONE'],
                    'descr': 'Icelake, 8 cores, 16 GiB',
                    'resources': [
                        {
                            'name': 'memory',
                            'options': ['--mem={size}'],
                        }
                    ],
                },
                {
                    'name': 'aarch64-graviton2-8c-16gb',
                    'access': ['--constraint=shape=c6g.2xlarge', '--export=NONE'],
                    'descr': 'Graviton2, 8 cores, 16 GiB',
                    'resources': [
                        {
                            'name': 'memory',
                            'options': ['--mem={size}'],
                        }
                    ],
                },
                {
                    'name': 'aarch64-graviton2-16c-32gb',
                    'access': ['--constraint=shape=c6g.4xlarge', '--export=NONE'],
                    'descr': 'Graviton2, 16 cores, 32 GiB',
                    'resources': [
                        {
                            'name': 'memory',
                            'options': ['--mem={size}'],
                        }
                    ],
                },
                {
                    'name': 'aarch64-graviton2-32c-64gb',
                    'access': ['--constraint=shape=c6g.8xlarge', '--export=NONE'],
                    'descr': 'Graviton2, 32 cores, 64 GiB',
                    'resources': [
                        {
                            'name': 'memory',
                            'options': ['--mem={size}'],
                        }
                    ],
                },
                {
                    'name': 'aarch64-graviton3-8c-16gb',
                    'access': ['--constraint=shape=c7g.2xlarge', '--export=NONE'],
                    'descr': 'Graviton3, 8 cores, 16 GiB',
                    'resources': [
                        {
                            'name': 'memory',
                            'options': ['--mem={size}'],
                        }
                    ],
                },
                {
                    'name': 'aarch64-graviton3-16c-32gb',
                    'access': ['--constraint=shape=c7g.4xlarge', '--export=NONE'],
                    'descr': 'Graviton3, 16 cores, 32 GiB',
                    'resources': [
                        {
                            'name': 'memory',
                            'options': ['--mem={size}'],
                        }
                    ],
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
        }
    ],
}

# Add default things to each partition:
partition_defaults = {
    'scheduler': 'squeue',
    'launcher': 'mpirun',
    'environs': ['default'],
    'features': [
        FEATURES.CPU
    ],
    'prepare_cmds': [
        common_eessi_init(),
        # Required when using srun as launcher with --export=NONE in partition access, in order to ensure job
        # steps inherit environment. It doesn't hurt to define this even if srun is not used
        'export SLURM_EXPORT_ENV=ALL'
    ],
}
for system in site_configuration['systems']:
    for partition in system['partitions']:
        partition.update(partition_defaults)
