import os

from eessi.testsuite.common_config import common_logging_config
from eessi.testsuite.constants import *  # noqa: F403

# This config will write all staging, output and logging to subdirs under this prefix
# Override with RFM_PREFIX environment variable
reframe_prefix = os.path.join(os.environ['HOME'], 'reframe_runs')

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
                    'name': 'thin',
                    'scheduler': 'slurm',
                    'prepare_cmds': ['source /cvmfs/pilot.eessi-hpc.org/latest/init/bash'],
                    'launcher': 'mpirun',
                    'access':  ['-p thin', '--export=None'],
                    'environs': ['default'],
                    'max_jobs': 120,
                    'features': [
                        FEATURES[CPU],
                    ],
                    'descr': 'Test CPU partition with native EESSI stack'
                },
                {
                    'name': 'gpu',
                    'scheduler': 'slurm',
                    'prepare_cmds': ['source /cvmfs/pilot.eessi-hpc.org/latest/init/bash'],
                    'launcher': 'mpirun',
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
                    'extras': {
                        GPU_VENDOR: GPU_VENDORS[NVIDIA],
                    },
                    'descr': 'Test GPU partition with native EESSI stack'
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
            # For autodetect to work, temporarily change:
            # 1. The launchers to srun
            # 2. Add --exclusive to GPU 'access' field above (avoids submission error that no GPUs are requested)
            'remote_detect': True,
        }
    ],
}
