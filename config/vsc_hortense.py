# ReFrame configuration file for VSC Tier-1 Hortense
# https://docs.vscentrum.be/en/latest/gent/tier1_hortense.html
#
# authors: Samuel Moors (VUB-HPC), Kenneth Hoste (HPC-UGent), Lara Peeters (HPC-UGent)

# Use generated topology file by ReFrame for CPU partitions
# `sched_access_in_submit` does not work with setting `'remote_detect': True,`

# Instructions on generating topology file
# ```
#    module swap cluster/{partition}
#    qsub -I -l nodes=1:ppn=all -l walltime=00:30:00
#
#    python3 -m venv "$TMPDIR"/reframe_venv
#    source "$TMPDIR"/reframe_venv/bin/activate
#    python3 -m pip install --upgrade pip
#    python3 -m pip install reframe-hpc=="4.6.2"
#
#    mkdir -p ~/.reframe/topology/hortense-{partition_name}
#    reframe --detect-host-topology \
#        ~/.reframe/topology/hortense-{partition_name}/processor.json
# ```
import os

from eessi.testsuite.common_config import (common_eessi_init,
                                           common_general_config,
                                           common_logging_config,
                                           get_sbatch_account)
from eessi.testsuite.constants import *  # noqa: F403

hortense_access = ['--export=NONE', '--get-user-env=60L']

# Note that we rely on the SBATCH_ACCOUNT environment variable to be specified
# From ReFrame 4.8.1 we can no longer rely on SBATCH_ACCOUNT completely
# ReFrame unsets all `SBATCH_*` evironment variables before running `sbatch`
# See https://github.com/reframe-hpc/reframe/issues/3422
sbatch_account = get_sbatch_account()
hortense_access.append(f'-A {sbatch_account}')

# These environment need to be set to avoid orte failures when launching application with `mpirun`
common_env_vars = [
    ['OMPI_MCA_plm_base_verbose', '100'],
    ['OMPI_MCA_orte_keep_fqdn_hostnames', '1']
]
# We need to pass `--export=NONE` so that we have a clean environment in the jobs
# We need to unset SLURM_EXPORT_ENV in the job because otherwise this causes problems for `mpirun`
post_init = 'unset SLURM_EXPORT_ENV'
launcher = "mpirun"

eessi_cvmfs_repo = os.getenv('EESSI_CVMFS_REPO', None)
if eessi_cvmfs_repo is not None:
    prepare_eessi_init = "module --force purge"
    mpi_module = "env/vsc/dodrio/{}"
else:
    prepare_eessi_init = ""
    mpi_module = "vsc-mympirun"

site_configuration = {
    'systems': [
        {
            'name': 'hortense',
            'descr': 'Hortense',
            'hostnames': ['login.*.dodrio.os'],
            'modules_system': 'lmod',
            # Need to set the environment variable to be able to submit to GPU_partitions
            # see https://github.com/EESSI/test-suite/issues/242
            'env_vars': [['SLURM_CONF', '/etc/slurm/slurm.conf_dodrio']],
            'partitions': [
                {
                    'name': 'cpu_rome',
                    'scheduler': 'slurm',
                    'prepare_cmds': [
                        prepare_eessi_init,
                        common_eessi_init(),
                        post_init,
                    ],
                    'access': hortense_access + ['--partition=cpu_rome'],
                    'env_vars': common_env_vars,
                    'sched_options': {
                        'sched_access_in_submit': True,
                    },
                    'environs': ['default'],
                    'descr': 'CPU nodes (AMD Rome, 256GiB RAM)',
                    'max_jobs': 20,
                    'launcher': launcher,
                    'modules': [mpi_module.format('cpu_rome')],
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
                        # Make sure to round down, otherwise a job might ask for more mem than is available
                        # per node
                        EXTRAS.MEM_PER_NODE: 243200,  # in MiB
                    },
                },
                {
                    'name': 'cpu_rome_512',
                    'scheduler': 'slurm',
                    'prepare_cmds': [
                        prepare_eessi_init,
                        common_eessi_init(),
                        post_init,
                    ],
                    'access': hortense_access + ['--partition=cpu_rome_512'],
                    'env_vars': common_env_vars,
                    'sched_options': {
                        'sched_access_in_submit': True,
                    },
                    'environs': ['default'],
                    'descr': 'CPU nodes (AMD Rome, 512GiB RAM)',
                    'max_jobs': 20,
                    'launcher': launcher,
                    'modules': [mpi_module.format('cpu_rome_512')],
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
                        # Make sure to round down, otherwise a job might ask for more mem than is available
                        # per node
                        EXTRAS.MEM_PER_NODE: 499200,  # in MiB
                    },
                },
                {
                    'name': 'cpu_milan',
                    'scheduler': 'slurm',
                    'prepare_cmds': [
                        prepare_eessi_init,
                        common_eessi_init(),
                        post_init,
                    ],
                    'access': hortense_access + ['--partition=cpu_milan'],
                    'env_vars': common_env_vars,
                    'sched_options': {
                        'sched_access_in_submit': True,
                    },
                    'environs': ['default'],
                    'descr': 'CPU nodes (AMD Milan, 256GiB RAM)',
                    'max_jobs': 20,
                    'launcher': launcher,
                    'modules': [mpi_module.format('cpu_milan')],
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
                        # Make sure to round down, otherwise a job might ask for more mem than is available
                        # per node
                        EXTRAS.MEM_PER_NODE: 243200,  # in MiB
                    },
                },
                {
                    'name': 'cpu_milan_rhel9',
                    'scheduler': 'slurm',
                    'prepare_cmds': [
                        prepare_eessi_init,
                        common_eessi_init(),
                        post_init,
                    ],
                    'access': hortense_access + ['--partition=cpu_milan_rhel9'],
                    'env_vars': common_env_vars,
                    'sched_options': {
                        'sched_access_in_submit': True,
                    },
                    'environs': ['default'],
                    'descr': 'CPU nodes (AMD Milan, 256GiB RAM)',
                    'max_jobs': 20,
                    'launcher': launcher,
                    'modules': [mpi_module.format('cpu_milan_rhel9')],
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
                        # Make sure to round down, otherwise a job might ask for more mem than is available
                        # per node
                        EXTRAS.MEM_PER_NODE: 243200,  # in MiB
                    },
                },
                {
                    'name': 'gpu_rome_a100_40',
                    'scheduler': 'slurm',
                    'prepare_cmds': [
                        prepare_eessi_init,
                        common_eessi_init(),
                        post_init,
                    ],
                    'access': hortense_access + ['--partition=gpu_rome_a100_40'],
                    'env_vars': common_env_vars,
                    'sched_options': {
                        'sched_access_in_submit': True,
                    },
                    'environs': ['default'],
                    'descr': 'GPU nodes (A100 40GB)',
                    'max_jobs': 20,
                    'launcher': launcher,
                    'modules': [mpi_module.format('gpu_rome_a100_40')],
                    'features': [
                        FEATURES.GPU,
                    ] + list(SCALES.keys()),
                    'extras': {
                        EXTRAS.GPU_VENDOR: GPU_VENDORS.NVIDIA,
                        # Make sure to round down, otherwise a job might ask for more mem than is available
                        # per node
                        EXTRAS.MEM_PER_NODE: 243840,  # in MiB
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
                {
                    'name': 'gpu_rome_a100_80',
                    'scheduler': 'slurm',
                    'prepare_cmds': [
                        prepare_eessi_init,
                        common_eessi_init(),
                        post_init,
                    ],
                    'access': hortense_access + ['--partition=gpu_rome_a100_80'],
                    'env_vars': common_env_vars,
                    'sched_options': {
                        'sched_access_in_submit': True,
                    },
                    'environs': ['default'],
                    'descr': 'GPU nodes (A100 80GB)',
                    'max_jobs': 20,
                    'launcher': launcher,
                    'modules': [mpi_module.format('gpu_rome_a100_80')],
                    'features': [
                        FEATURES.GPU,
                    ] + list(SCALES.keys()),
                    'extras': {
                        EXTRAS.GPU_VENDOR: GPU_VENDORS.NVIDIA,
                        # Make sure to round down, otherwise a job might ask for more mem than is available
                        # per node
                        EXTRAS.MEM_PER_NODE: 499680,  # in MiB
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
            'remote_detect': True,
            'purge_environment': True,
            'resolve_module_conflicts': False,  # avoid loading the module before submitting the job
            **common_general_config()
        }
    ],
    'logging': common_logging_config(),
}
