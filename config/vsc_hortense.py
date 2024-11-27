# ReFrame configuration file for VSC Tier-1 Hortense
# https://docs.vscentrum.be/en/latest/gent/tier1_hortense.html
#
# authors: Samuel Moors (VUB-HPC), Kenneth Hoste (HPC-UGent), Lara Peeters (HPC-UGent)

# Use generated topology file by ReFrame for CPU partitions
# Cannot use autodetection untill new functionality of `sched_options` is part of
# the ReFrame release https://github.com/reframe-hpc/reframe/issues/2970

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

from reframe.core.backends import register_launcher
from reframe.core.launchers import JobLauncher

from eessi.testsuite.common_config import (common_eessi_init,
                                           common_general_config,
                                           common_logging_config)
from eessi.testsuite.constants import *  # noqa: F403

# Note that we rely on the SBATCH_ACCOUNT environment variable to be specified
hortense_access = ['--export=NONE', '--get-user-env=60L']


@register_launcher('mympirun')
class MyMpirunLauncher(JobLauncher):
    def command(self, job):
        return ['mympirun', '--hybrid', str(job.num_tasks_per_node)]


site_configuration = {
    'systems': [
        {
            'name': 'hortense',
            'descr': 'Hortense',
            'hostnames': ['login.*.dodrio.os'],
            'modules_system': 'lmod',
            'partitions': [
                {
                    'name': 'cpu_rome_256gb',
                    'scheduler': 'slurm',
                    'prepare_cmds': [common_eessi_init()],
                    'access': hortense_access + ['--partition=cpu_rome'],
                    'environs': ['default'],
                    'descr': 'CPU nodes (AMD Rome, 256GiB RAM)',
                    'max_jobs': 20,
                    'launcher': 'mympirun',
                    'modules': ['vsc-mympirun'],
                    'resources': [
                        {
                            'name': 'memory',
                            'options': ['--mem={size}'],
                        }
                    ],
                    'features': [
                        FEATURES[CPU],
                    ] + list(SCALES.keys()),
                    'extras': {
                        # Make sure to round down, otherwise a job might ask for more mem than is available
                        # per node
                        'mem_per_node': 252160,  # in MiB
                    },
                },
                {
                    'name': 'cpu_rome_512gb',
                    'scheduler': 'slurm',
                    'prepare_cmds': [common_eessi_init()],
                    'access': hortense_access + ['--partition=cpu_rome_512'],
                    'environs': ['default'],
                    'descr': 'CPU nodes (AMD Rome, 512GiB RAM)',
                    'max_jobs': 20,
                    'launcher': 'mympirun',
                    'modules': ['vsc-mympirun'],
                    'resources': [
                        {
                            'name': 'memory',
                            'options': ['--mem={size}'],
                        }
                    ],
                    'features': [
                        FEATURES[CPU],
                    ] + list(SCALES.keys()),
                    'extras': {
                        # Make sure to round down, otherwise a job might ask for more mem than is available
                        # per node
                        'mem_per_node': 508160,  # in MiB
                    },
                },
                {
                    'name': 'cpu_milan',
                    'scheduler': 'slurm',
                    'prepare_cmds': [common_eessi_init()],
                    'access': hortense_access + ['--partition=cpu_milan'],
                    'environs': ['default'],
                    'descr': 'CPU nodes (AMD Milan, 256GiB RAM)',
                    'max_jobs': 20,
                    'launcher': 'mympirun',
                    'modules': ['vsc-mympirun'],
                    'resources': [
                        {
                            'name': 'memory',
                            'options': ['--mem={size}'],
                        }
                    ],
                    'features': [
                        FEATURES[CPU],
                    ] + list(SCALES.keys()),
                    'extras': {
                        # Make sure to round down, otherwise a job might ask for more mem than is available
                        # per node
                        'mem_per_node': 252160,  # in MiB
                    },
                },
                {
                    'name': 'gpu_rome_a100_40gb',
                    'scheduler': 'slurm',
                    'prepare_cmds': [common_eessi_init()],
                    'access': hortense_access + ['--partition=gpu_rome_a100_40'],
                    'environs': ['default'],
                    'descr': 'GPU nodes (A100 40GB)',
                    'max_jobs': 20,
                    'launcher': 'mympirun',
                    'modules': ['vsc-mympirun'],
                    'features': [
                        FEATURES[GPU],
                    ] + list(SCALES.keys()),
                    'extras': {
                        GPU_VENDOR: GPU_VENDORS[NVIDIA],
                        # Make sure to round down, otherwise a job might ask for more mem than is available
                        # per node
                        'mem_per_node': 254400,  # in MiB
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
                            'type': DEVICE_TYPES[GPU],
                            'num_devices': 4,
                        }
                    ],

                },
                {
                    'name': 'gpu_rome_a100_80gb',
                    'scheduler': 'slurm',
                    'prepare_cmds': [common_eessi_init()],
                    'access': hortense_access + ['--partition=gpu_rome_a100_80'],
                    'environs': ['default'],
                    'descr': 'GPU nodes (A100 80GB)',
                    'max_jobs': 20,
                    'launcher': 'mympirun',
                    'modules': ['vsc-mympirun'],
                    'features': [
                        FEATURES[GPU],
                    ] + list(SCALES.keys()),
                    'extras': {
                        GPU_VENDOR: GPU_VENDORS[NVIDIA],
                        # Make sure to round down, otherwise a job might ask for more mem than is available
                        # per node
                        'mem_per_node': 510720,  # in MiB
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
                            'type': DEVICE_TYPES[GPU],
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
            'purge_environment': True,
            'resolve_module_conflicts': False,  # avoid loading the module before submitting the job
            **common_general_config()
        }
    ],
    'logging': common_logging_config(),
}
