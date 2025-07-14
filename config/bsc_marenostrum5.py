import os

from eessi.testsuite.common_config import (common_logging_config,
                                           common_general_config,
                                           common_eessi_init,
                                           get_sbatch_account)
from eessi.testsuite.constants import *

site_configuration = {
    'systems': [
        {
            'name': 'marenostrum5',
            'descr': 'MareNostrum5 super computer hosted at BSC',
            'modules_system': 'lmod',
            'hostnames': ['.*'],
            # Note that the stagedir should be a shared directory available on all nodes running ReFrame tests
            'stagedir': f'{os.environ.get("RFM_PREFIX")}/stage',
            'partitions': [
                {
                    'name': 'gp_ehpc',
                    'descr': 'CPU partition',
                    'scheduler': 'slurm',
                    'launcher': 'mpirun',
                    'access': ['-q gp_ehpc', '--export=None', f'-A {sbatch_account}'],
                    'env_vars': [
                        ['EESSI_TEST_SUITE_NO_DOWNLOAD', 'True'],
                        [
                            'EESSI_TEST_SUITE_DOWNLOAD_DIR',
                            '/gpfs/projects/ehpc38/EESSI/testing/test-suite-downloads',
                        ],
                    ],
                    'prepare_cmds': [
                        "module unuse /apps/GPP/modulefiles/applications",
                        common_eessi_init(),
                        'export OMPI_MCA_pml=ucx',
                         # Work around "Failed to modify UD QP to INIT on mlx5_0: Operation not permitted" issue
                         # until we can resolve this through an LMOD hook in host_injections.
                         # (then these OMPI_MCA_btl & mtl can be removed again)
                         # See https://github.com/EESSI/software-layer/issues/456#issuecomment-2107755266
                         'export OMPI_MCA_mtl="^ofi"',
                         'export OMPI_MCA_btl="^ofi"',
                    ],
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
                        #{
                        #    'name': 'memory',
                        #    'options': ['--mem={size}'],
                        #}
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
                    'name': 'acc_ehpc',
                    'descr': 'GPU partition',
                    'scheduler': 'slurm',
                    'launcher': 'mpirun',
                    'access': ['-p acc_ehpc', '--export=None', f'-A {sbatch_account}'],
                    'env_vars': [
                        ['EESSI_TEST_SUITE_NO_DOWNLOAD', True],
                        [
                            'EESSI_TEST_SUITE_DOWNLOAD_DIR',
                            '/gpfs/projects/ehpc38/EESSI/testing/test-suite-downloads',
                        ],
                    ],
                    'prepare_cmds': [
                        "module unuse /apps/GPP/modulefiles/applications",
                        common_eessi_init(),
                        'export OMPI_MCA_pml=ucx',
                         # Work around "Failed to modify UD QP to INIT on mlx5_0: Operation not permitted" issue
                         # until we can resolve this through an LMOD hook in host_injections.
                         # (then these OMPI_MCA_btl & mtl can be removed again)
                         # See https://github.com/EESSI/software-layer/issues/456#issuecomment-2107755266
                         'export OMPI_MCA_mtl="^ofi"',
                         'export OMPI_MCA_btl="^ofi"',
                    ],
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
                        #{
                        #    'name': 'memory',
                        #    'options': ['--mem={size}'],
                        #}
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
