# the reframe command needs to contain the following in order to help ReFrame with selecting the system since it uses hostname as the selection parameter and it is the same for all clusters.
# `--system $SLURM_CLUSTERS`

import os

from eessi.testsuite.common_config import (common_eessi_init,
                                           common_general_config,
                                           common_logging_config)
from eessi.testsuite.constants import *  # noqa: F403

tier2_access = ['--export=None']

env_vars = [
    # Only set this for debugging purposes
    # ['OMPI_MCA_plm_base_verbose', '100'],
    ['OMPI_MCA_plm_base_verbose', '100'],
    ['OMPI_MCA_orte_keep_fqdn_hostnames', '1'],
    ['PRTE_MCA_prte_keep_fqdn_hostnames', '1']
]
post_eessi_init = 'unset SLURM_EXPORT_ENV'
launcher = 'mpirun'

eessi_cvmfs_repo = os.getenv('EESSI_CVMFS_REPO', None)
if eessi_cvmfs_repo is not None:
    prepare_eessi_init = "module --force purge"
    mpi_module = "env/vsc/{}"
    # Work around "Failed to modify UD QP to INIT on mlx5_0: Operation not permitted" issue
    # until we can resolve this through an LMOD hook in host_injections.
    # (then these OMPI_MCA_btl & mtl can be removed again)
    # See https://github.com/EESSI/software-layer/issues/456#issuecomment-2107755266
    # env_vars = [['OMPI_MCA_pml','ucx'],['OMPI_MCA_mtl',"^ofi"], ['OMPI_MCA_btl',"^ofi"], ['OMPI_MCA_orte_keep_fqdn_hostnames',"1"]]
else:
    prepare_eessi_init = ""
    mpi_module = "vsc-mympirun"

site_configuration = {
    'systems': [
        {
            'name': 'doduo',
            'descr': 'doduo cpu only',
            'hostnames': ['gligar.*.gastly.os'],
            'modules_system': 'lmod',
            'partitions': [
                {
                    'name': 'doduo',
                    'scheduler': 'slurm',
                    'prepare_cmds': [
                        'module swap cluster/doduo',
                        prepare_eessi_init, 
                        common_eessi_init(),
                        post_eessi_init,
                    ],
                    'access': tier2_access + ['--clusters=doduo'],
                    'sched_options': {
                        'sched_access_in_submit': True,
                    },
                    'environs': ['default'],
                    'descr': 'CPU nodes (zen2)',
                    'max_jobs': 128,
                    'launcher': launcher,
                    'env_vars': env_vars,
                    'modules': [mpi_module.format('doduo')],
                    'resources': [
                        {
                            'name': 'memory',
                            'options': ['--mem={size}'],
                        }
                    ],
                    'features': [
                        FEATURES.CPU,
                    ] + list(SCALES.keys()),
                    'extras': {
                        EXTRAS.MEM_PER_NODE: 240000, # in MiB
                    },
                }
            ]
        },
        {
            'name': 'gallade',
            'descr': 'gallade cpu only',
            'hostnames': ['gligar.*.gastly.os'],
            'modules_system': 'lmod',
            'partitions': [
                {
                    'name': 'gallade',
                    'scheduler': 'slurm',
                    'prepare_cmds': [
                        'module swap cluster/gallade',
                        prepare_eessi_init, 
                        common_eessi_init(),
                        post_eessi_init,
                    ],
                    'access': tier2_access + ['--clusters=gallade'],
                    'sched_options': {
                        'sched_access_in_submit': True,
                    },
                    'environs': ['default'],
                    'descr': 'cpu nodes (AMD MILAN, 940GiB RAM)',
                    'max_jobs': 16,
                    'launcher': launcher,
                    'env_vars': env_vars,
                    'modules': [mpi_module.format('gallade')],
                    'resources': [
                        {
                            'name': 'memory',
                            'options': ['--mem={size}'],
                        }
                    ],
                    'features': [
                        FEATURES.CPU,
                    ] + list(SCALES.keys()),
                    'extras': {
                        EXTRAS.MEM_PER_NODE: 949760, # in MiB
                    },
                }
            ]
        },
        {
            'name': 'shinx',
            'descr': 'shinx cluster',
            'hostnames': ['gligar.*.gastly.os'],
            'modules_system': 'lmod',
            'partitions': [
                {
                    'name': 'shinx',
                    'scheduler': 'slurm',
                    'prepare_cmds': [
                        'module swap cluster/shinx',
                        'module use /data/gent/vo/000/gvo00002/vsc46128/easybuild/RHEL9/zen4-ib/modules/all',
                        'echo $MODULEPATH',
                        'unset OMP_PROC_BIND',
                        prepare_eessi_init, 
                        common_eessi_init(),
                        post_eessi_init,
                    ],
                    'access': tier2_access + ['--clusters=shinx'],
                    'sched_options': {
                        'sched_access_in_submit': True,
                    },
                    'environs': ['default'],
                    'descr': 'cpu nodes ()',
                    'max_jobs': 48,
                    'launcher': launcher,
                    'env_vars': env_vars,
                    'modules': [mpi_module.format('shinx')],
                    'features': [
                        FEATURES.CPU,
                    ] + list(SCALES.keys()),
                    'resources': [
                        {
                            'name': 'memory',
                            'options': ['--mem={size}'],
                        }
                    ],
                    'extras': {
                        EXTRAS.MEM_PER_NODE: 368640, # in MiB
                    },
                }
            ]
        },
        { 
            'name': 'donphan',
            'descr': 'donphan debug cluster',
            'hostnames': ['gligar.*.gastly.os'],
            'modules_system': 'lmod',
            'partitions': [
                {
                    'name': 'donphan',
                    'scheduler': 'slurm',
                    'prepare_cmds': [
                        'module swap cluster/donphan',
                        prepare_eessi_init, 
                        common_eessi_init(),
                        post_eessi_init,
                    ],
                    'access': tier2_access + ['--clusters=donphan'],
                    'sched_options': {
                        'sched_access_in_submit': True,
                    },
                    'environs': ['default'],
                    'descr': 'cpu nodes (Intel Cascade Lake, 738GiB RAM)',
                    'max_jobs': 1,
                    'launcher': launcher,
                    'env_vars': env_vars,
                    'modules': [mpi_module.format('donphan')],
                    'features': [
                        FEATURES.GPU,
                        FEATURES.CPU,
                    ] + list(SCALES.keys()),
                    'extras': {
                        EXTRAS.GPU_VENDOR: GPU_VENDORS.NVIDIA,
                        EXTRAS.MEM_PER_NODE: 145136, # = 724680/5 # in MiB
                    },
                    'resources': [
                        {
                            'name': '_rfm_gpu',
                            'options': [],
                        },
                        {
                            'name': 'memory',
                            'options': ['--mem={size}'],
                        }
                    ],
                    'devices': [
                        {
                            'type': DEVICE_TYPES.GPU,
                            'num_devices': 1,
                        }
                    ],
                }
            ]
        },
        {
            'name': 'joltik',
            'descr': 'joltik',
            'hostnames': ['gligar.*.gastly.os'],
            'modules_system': 'lmod',
            'partitions': [
                {
                    'name': 'joltik',
                    'scheduler': 'slurm',
                    'prepare_cmds': [
                        'module swap cluster/joltik',
                        prepare_eessi_init, 
                        common_eessi_init(),
                        post_eessi_init,
                    ],
                    'access': tier2_access + ['--clusters=joltik'],
                    'sched_options': {
                        'sched_access_in_submit': True,
                    },
                    'environs': ['default'],
                    'descr': 'gpu nodes',
                    'max_jobs': 10,
                    'launcher': launcher,
                    'env_vars': env_vars,
                    'modules': [mpi_module.format('joltik')],
                    'features': [
                        FEATURES.GPU,
                    ] + list(SCALES.keys()),
                    'extras': {
                        EXTRAS.GPU_VENDOR: GPU_VENDORS.NVIDIA,
                        EXTRAS.MEM_PER_NODE: 252160, # in MiB
                    },
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

                },
            ]
        },
        {
            'name': 'accelgor',
            'descr': 'accelgor gpu cluster',
            'hostnames': ['gligar.*.gastly.os'],
            'modules_system': 'lmod',
            'partitions': [
                {
                    'name': 'accelgor',
                    'scheduler': 'slurm',
                    'prepare_cmds': [
                        'module swap cluster/accelgor',
                        prepare_eessi_init, 
                        common_eessi_init(),
                        post_eessi_init,
                    ],
                    'access': tier2_access + ['--clusters=accelgor'],
                    'sched_options': {
                        'sched_access_in_submit': True,
                    },
                    'environs': ['default'],
                    'descr': 'gpu nodes',
                    'max_jobs': 9,
                    'launcher': launcher,
                    'env_vars': env_vars,
                    'modules': [mpi_module.format('accelgor')],
                    'features': [
                        FEATURES.GPU,
                    ] + list(SCALES.keys()),
                    'extras': {
                        EXTRAS.GPU_VENDOR: GPU_VENDORS.NVIDIA,
                        EXTRAS.MEM_PER_NODE: 432000, # in MiB
                    },
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
                }
            ]
        },
        {
            'name': 'litleo',
            'descr': 'litleo gpu cluster',
            'hostnames': ['gligar.*.gastly.os'],
            'modules_system': 'lmod',
            'partitions': [
                {
                    'name': 'litleo',
                    'scheduler': 'slurm',
                    'prepare_cmds': [
                        'module swap cluster/.litleo',
                        prepare_eessi_init, 
                        common_eessi_init(),
                        post_eessi_init,
                    ],
                    'access': tier2_access + ['--clusters=litleo'],
                    'sched_options': {
                        'sched_access_in_submit': True,
                    },
                    'environs': ['default'],
                    'descr': 'gpu nodes',
                    'max_jobs': 8,
                    'launcher': launcher,
                    'env_vars': env_vars,
                    'modules': [mpi_module.format('.litleo')],
                    'features': [
                        FEATURES.GPU,
                    ] + list(SCALES.keys()),
                    'extras': {
                        EXTRAS.GPU_VENDOR: GPU_VENDORS.NVIDIA,
                        EXTRAS.MEM_PER_NODE: 305760, # in MiB
                    },
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
                            'num_devices': 2,
                        }
                    ],
                }
            ]
        },
    ],
    'environments': [
        {
            'name': 'default',
            'cc': 'gcc',
            'cxx': 'g++',
            'ftn': 'gfortran',
        },
        {
            'name': 'foss-2021a',
            'cc': 'mpicc',
            'cxx': 'mpicxx',
            'ftn': 'mpif90',
            'modules': ['foss/2021a']
        },
        {
            'name': 'intel-2021a',
            'modules': ['intel'],
            'cc': 'mpiicc',
            'cxx': 'mpiicpc',
            'ftn': 'mpiifort',
        },
        {
            'name': 'CUDA',
            'modules': ['CUDA'],
            'cc': 'nvcc',
            'cxx': 'nvcc',
        },
    ],
    'general': [
        {
            'purge_environment': False,
            'resolve_module_conflicts': False,  # avoid loading the module before submitting the job
            'remote_detect': True,
            **common_general_config()
        }
    ],
    'logging': common_logging_config(),
}
