# ReFrame configuration file for VSC Tier-1 Hortense
# https://docs.vscentrum.be/en/latest/gent/tier1_hortense.html
#
# authors: Samuel Moors (VUB-HPC), Kenneth Hoste (HPC-UGent)

from reframe.core.backends import register_launcher
from reframe.core.launchers import JobLauncher

from eessi.testsuite.common_config import common_logging_config
from eessi.testsuite.constants import *  # noqa: F403

account = "my-slurm-account"

hortense_access = [f'-A {account}', '--export=NONE', '--get-user-env=60L']


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
                    'prepare_cmds': ['source /cvmfs/pilot.eessi-hpc.org/latest/init/bash'],
                    'access': hortense_access + ['--partition=cpu_rome'],
                    'environs': ['default'],
                    'descr': 'CPU nodes (AMD Rome, 256GiB RAM)',
                    'max_jobs': 20,
                    'launcher': 'mympirun',
                    'modules': ['vsc-mympirun'],
                    'processor': {
                        'num_cpus': 128,
                        'num_sockets': 2,
                        'num_cpus_per_socket': 64,
                        'num_cpus_per_core': 1,
                        'arch': 'zen2',
                    },
                    'features': [
                        FEATURES[CPU],
                    ],
                },
                {
                    'name': 'cpu_rome_512gb',
                    'scheduler': 'slurm',
                    'prepare_cmds': ['source /cvmfs/pilot.eessi-hpc.org/latest/init/bash'],
                    'access': hortense_access + ['--partition=cpu_rome_512'],
                    'environs': ['default'],
                    'descr': 'CPU nodes (AMD Rome, 512GiB RAM)',
                    'max_jobs': 20,
                    'launcher': 'mympirun',
                    'modules': ['vsc-mympirun'],
                    'processor': {
                        'num_cpus': 128,
                        'num_sockets': 2,
                        'num_cpus_per_socket': 64,
                        'num_cpus_per_core': 1,
                        'arch': 'zen2',
                    },
                    'features': [
                        FEATURES[CPU],
                    ],
                },
                {
                    'name': 'cpu_milan',
                    'scheduler': 'slurm',
                    'prepare_cmds': ['source /cvmfs/pilot.eessi-hpc.org/latest/init/bash'],
                    'access': hortense_access + ['--partition=cpu_milan'],
                    'environs': ['default'],
                    'descr': 'CPU nodes (AMD Milan, 256GiB RAM)',
                    'max_jobs': 20,
                    'launcher': 'mympirun',
                    'modules': ['vsc-mympirun'],
                    'processor': {
                        'num_cpus': 128,
                        'num_sockets': 2,
                        'num_cpus_per_socket': 64,
                        'num_cpus_per_core': 1,
                        'arch': 'zen3',
                    },
                    'features': [
                        FEATURES[CPU],
                    ],
                },
                {
                    'name': 'gpu_rome_a100_40gb',
                    'scheduler': 'slurm',
                    'prepare_cmds': ['source /cvmfs/pilot.eessi-hpc.org/latest/init/bash'],
                    'access': hortense_access + ['--partition=cpu_rome_a100_40'],
                    'environs': ['default'],
                    'descr': 'GPU nodes (A100 40GB)',
                    'max_jobs': 20,
                    'launcher': 'mympirun',
                    'modules': ['vsc-mympirun'],
                    'processor': {
                        'num_cpus': 48,
                        'num_sockets': 2,
                        'num_cpus_per_socket': 24,
                        'num_cpus_per_core': 1,
                        'arch': 'zen2',
                    },
                    'features': [
                        FEATURES[GPU],
                    ],
                    'extras': {
                        GPU_VENDOR: GPU_VENDORS[NVIDIA],
                    },
                    'resources': [
                        {
                            'name': '_rfm_gpu',
                            'options': ['--gpus-per-node={num_gpus_per_node}'],
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
                    'prepare_cmds': ['source /cvmfs/pilot.eessi-hpc.org/latest/init/bash'],
                    'access': hortense_access + ['--partition=cpu_rome_a100_80'],
                    'environs': ['default'],
                    'descr': 'GPU nodes (A100 80GB)',
                    'max_jobs': 20,
                    'launcher': 'mympirun',
                    'modules': ['vsc-mympirun'],
                    'processor': {
                        'num_cpus': 48,
                        'num_sockets': 2,
                        'num_cpus_per_socket': 24,
                        'num_cpus_per_core': 1,
                        'arch': 'zen2',
                    },
                    'features': [
                        FEATURES[GPU],
                    ],
                    'extras': {
                        GPU_VENDOR: GPU_VENDORS[NVIDIA],
                    },
                    'resources': [
                        {
                            'name': '_rfm_gpu',
                            'options': ['--gpus-per-node={num_gpus_per_node}'],
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
        }
    ],
    'logging': common_logging_config(),
}
