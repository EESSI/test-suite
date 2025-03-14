# WARNING: for CPU autodetect to work correctly you need to
# 1. Either use ReFrame >= 4.3.3 or temporarily change the 'launcher' for each partition to srun
# 2. Either use ReFrame >= 4.3.3 or run from a clone of the ReFrame repository
# If your system has a GPU partition, it might force jobs to request at least one GPU. If that is the
# case, you also need to temporarily change 'access' field for the GPU partition to include the request
# for one GPU, e.g. 'access':  ['-p gpu', '--export=None', '--gres=gpu:1'],

# Without this, the autodetect job fails because
# 1. A missing mpirun command
# 2. An incorrect directory structure is assumed when preparing the stagedir for the autodetect job

# Related issues
# 1. https://github.com/reframe-hpc/reframe/issues/2926
# 2. https://github.com/reframe-hpc/reframe/issues/2914


"""
Example configuration file
"""
import os

from eessi.testsuite.common_config import common_logging_config, common_general_config, common_eessi_init
from eessi.testsuite.constants import EXTRAS, FEATURES, SCALES, DEVICE_TYPES, GPU_VENDORS


site_configuration = {
    'systems': [
        {
            'name': 'example',
            'descr': 'Example cluster',
            'modules_system': 'lmod',
            'hostnames': ['.*'],
            # Note that the stagedir should be a shared directory available on all nodes running ReFrame tests
            'stagedir': f'/some/shared/dir/{os.environ.get("USER")}/reframe_output/staging',
            'partitions': [
                {
                    'name': 'cpu_partition',
                    'descr': 'CPU partition',
                    'scheduler': 'slurm',
                    'launcher': 'mpirun',
                    'access': ['-p cpu', '--export=None'],
                    'prepare_cmds': [common_eessi_init()],
                    'environs': ['default'],
                    'max_jobs': 4,
                    # We recommend to rely on ReFrame's CPU autodetection,
                    # and only define the 'processor' field if autodetection fails
                    # 'processor': {
                        # 'num_cpus': 128,
                        # 'num_sockets': 2,
                        # 'num_cpus_per_socket': 64,
                        # 'num_cpus_per_core': 1,
                    # },
                    'resources': [
                        {
                            'name': 'memory',
                            'options': ['--mem={size}'],
                        }
                    ],
                    'extras': {
                        # If you have slurm, check with scontrol show node <nodename> for the amount of RealMemory
                        # on nodes in this partition
                        # Make sure to round down, otherwise a job might ask for more mem than is available
                        # per node
                        EXTRAS.MEM_PER_NODE: 229376  # in MiB
                    },
                    # list(SCALES.keys()) adds all the scales from eessi.testsuite.constants as valid for thi partition
                    # Can be modified if not all scales can run on this partition, see e.g. the surf_snellius.py config
                    'features': [FEATURES.CPU] + list(SCALES.keys()),
                },
                {
                    'name': 'gpu_partition',
                    'descr': 'GPU partition',
                    'scheduler': 'slurm',
                    'launcher': 'mpirun',
                    'access': ['-p gpu', '--export=None'],
                    'prepare_cmds': [common_eessi_init()],
                    'environs': ['default'],
                    'max_jobs': 4,
                    # We recommend to rely on ReFrame's CPU autodetection,
                    # and only define the 'processor' field if autodetection fails
                    # 'processor': {
                    #     'num_cpus': 72,
                    #     'num_sockets': 2,
                    #     'num_cpus_per_socket': 36,
                    #     'num_cpus_per_core': 1,
                    # },
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
                    'devices': [
                        {
                            'type': DEVICE_TYPES.GPU,
                            'num_devices': 4,
                        }
                    ],
                    'features': [
                        FEATURES.CPU,
                        FEATURES.GPU,
                    ] + list(SCALES.keys()),
                    'extras': {
                        # If you have slurm, check with scontrol show node <nodename> for the amount of RealMemory
                        # on nodes in this partition
                        # Make sure to round down, otherwise a job might ask for more mem than is available
                        # per node
                        EXTRAS.MEM_PER_NODE: 229376,  # in MiB
                        EXTRAS.GPU_VENDOR: GPU_VENDORS.NVIDIA,
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
    'logging': common_logging_config(),
    'general': [
        {
            # Enable automatic detection of CPU architecture for each partition
            # See https://reframe-hpc.readthedocs.io/en/stable/configure.html#auto-detecting-processor-information
            'remote_detect': True,
            **common_general_config()
        }
    ],
}
