import os

from eessi.testsuite.common_config import (common_logging_config,
                                           common_general_config,
                                           common_eessi_init,
                                           get_sbatch_account)
from eessi.testsuite.constants import *

# Note that we rely on the SBATCH_ACCOUNT environment variable to be specified
# From ReFrame 4.8.1 we can no longer rely on SBATCH_ACCOUNT completely
# ReFrame unsets all `SBATCH_*` evironment variables before running `sbatch`
# See https://github.com/reframe-hpc/reframe/issues/3422
sbatch_account = get_sbatch_account()

site_configuration = {
    'systems': [
        {
            'name': 'marenostrum5',
            'descr': 'MareNostrum5 super computer hosted at BSC',
            'modules_system': 'lmod',
            'hostnames': ['.*'],
            # Note that the stagedir should be a shared directory available on all nodes running ReFrame tests
            'stagedir': f'{os.environ.get("RFM_PREFIX")}/stage',
            'resourcesdir': f'{os.environ.get("RFM_PREFIX")}/resources',
            'partitions': [
                {
                    'name': 'gp_ehpc',
                    'descr': 'CPU partition',
                    'scheduler': 'slurm',
                    'launcher': 'mpirun',
                    'access': ['-q gp_ehpc', '--export=None', f'-A {sbatch_account}'],
                    'env_vars': [],
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
                    'resources': [
                        # memory cannot be set on MareNostrum
                        # The test-suite will give warning which can be ignored
                    ],
                    # list(SCALES.keys()) adds all the scales from eessi.testsuite.constants as valid for thi partition
                    # Can be modified if not all scales can run on this partition, see e.g. the surf_snellius.py config
                    'features': [
                        FEATURES.CPU,
                        FEATURES.OFFLINE,
                    ] + list(SCALES.keys()),
                    'extras': {
                        # EXTRAS.MEM_PER_NODE cannot be set
                        # Because the memory by slurm is set to unlimited
                    },
                },
                {
                    'name': 'acc_ehpc',
                    'descr': 'GPU partition',
                    'scheduler': 'slurm',
                    'launcher': 'mpirun',
                    'access': ['-p acc_ehpc', '--export=None', f'-A {sbatch_account}'],
                    'env_vars': [],
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
                    'resources': [
                        {
                            'name': '_rfm_gpu',
                            'options': ['--gpus-per-node={num_gpus_per_node}'],
                        },
                        # memory cannot be set on MareNostrum
                        # The test-suite will give warning which can be ignored
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
                        FEATURES.OFFLINE,
                    ] + list(SCALES.keys()),
                    'extras': {
                        EXTRAS.GPU_VENDOR: GPU_VENDORS.NVIDIA,
                        # EXTRAS.MEM_PER_NODE cannot be set
                        # Because the memory by slurm is set to unlimited
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
