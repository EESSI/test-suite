# ReFrame configuration file for VSC Tier-1 Hortense
# https://docs.vscentrum.be/en/latest/gent/tier1_hortense.html
#
# authors: Sam Moors (VUB-HPC), Kenneth Hoste (HPC-UGent)

from reframe.core.backends import register_launcher
from reframe.core.launchers import JobLauncher

account = "my-slurm-account"

# use 'info' to log to syslog
syslog_level = 'warning'

perf_logging_format = 'reframe: ' + '|'.join([
    'username=%(osuser)s',
    'version=%(version)s',
    'name=%(check_name)s',
    'system=%(check_system)s',
    'partition=%(check_partition)s',
    'environ=%(check_environ)s',
    'num_tasks=%(check_num_tasks)s',
    'num_cpus_per_task=%(check_num_cpus_per_task)s',
    'num_tasks_per_node=%(check_num_tasks_per_node)s',
    'modules=%(check_modules)s',
    'jobid=%(check_jobid)s',
    '%(check_perfvalues)s',
])

format_perfvars = '|'.join([
    'perf_var=%(check_perf_var)s',
    'perf_value=%(check_perf_value)s',
    'unit=%(check_perf_unit)s',
]) + '|'


@register_launcher('mympirun')
class MyMpirunLauncher(JobLauncher):
    def command(self, job):
        return ['mympirun', '--hybrid', str(job.num_tasks)]


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
                    'access': [f'-A {account} --export=NONE --get-user-env=60L --partition=cpu_rome'],
                    'environs': ['default'],
                    'descr': 'CPU nodes (AMD Rome, 256GiB RAM)',
                    'max_jobs': 20,
                    'launcher': 'mympirun',
                    'modules': ['vsc-mympirun'],
                    'processor': {
                        'num_cpus': 128,
                    },
                    'features': [
                        'cpu',
                    ],
                },
                {
                    'name': 'cpu_rome_512gb',
                    'scheduler': 'slurm',
                    'access': [f'-A {account} --export=NONE --get-user-env=60L --partition=cpu_rome_512'],
                    'environs': ['default'],
                    'descr': 'CPU nodes (AMD Rome, 512GiB RAM)',
                    'max_jobs': 20,
                    'launcher': 'mympirun',
                    'modules': ['vsc-mympirun'],
                    'processor': {
                        'num_cpus': 128,
                    },
                    'features': [
                        'cpu',
                    ],
                },
                {
                    'name': 'cpu_milan',
                    'scheduler': 'slurm',
                    'access': [f'-A {account} --export=NONE --get-user-env=60L --partition=cpu_milan'],
                    'environs': ['default'],
                    'descr': 'CPU nodes (AMD Milan, 256GiB RAM)',
                    'max_jobs': 20,
                    'launcher': 'mympirun',
                    'modules': ['vsc-mympirun'],
                    'processor': {
                        'num_cpus': 128,
                    },
                    'features': [
                        'cpu',
                    ],
                },
                {
                    'name': 'gpu_rome_a100_40gb',
                    'scheduler': 'slurm',
                    'access': [f'-A {account} --export=NONE --get-user-env=60L --partition=gpu_rome_a100_40'],
                    'environs': ['default'],
                    'descr': 'GPU nodes (A100 40GB)',
                    'max_jobs': 20,
                    'launcher': 'mympirun',
                    'modules': ['vsc-mympirun'],
                    'processor': {
                        'num_cpus': 48,
                    },
                    'features': [
                        'cpu',
                        'gpu',
                    ],
                    'resources': [
                        {
                            'name': '_rfm_gpu',
                            'options': ['--gpus-per-node={num_gpus_per_node}'],
                        }
                    ],
                    'devices': [
                        {
                            'type': 'gpu',
                            'num_devices': 4,
                        }
                    ],

                },
                {
                    'name': 'gpu_rome_a100_80gb',
                    'scheduler': 'slurm',
                    'access': [f'-A {account} --export=NONE --get-user-env=60L --partition=gpu_rome_a100_80'],
                    'environs': ['default'],
                    'descr': 'GPU nodes (A100 80GB)',
                    'max_jobs': 20,
                    'launcher': 'mympirun',
                    'modules': ['vsc-mympirun'],
                    'processor': {
                        'num_cpus': 48,
                    },
                    'features': [
                        'cpu',
                        'gpu',
                    ],
                    'resources': [
                        {
                            'name': '_rfm_gpu',
                            'options': ['--gpus-per-node={num_gpus_per_node}'],
                        }
                    ],
                    'devices': [
                        {
                            'type': 'gpu',
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
            'keep_stage_files': True,
        }
    ],
    'logging': [
        {
            'level': 'debug',
            'handlers': [
                {
                    'type': 'file',
                    'name': 'reframe.log',
                    'level': 'debug',
                    'format': '[%(asctime)s] %(levelname)s: %(check_name)s: %(message)s',  # noqa: E501
                    'append': False,
                },
                {
                    'type': 'stream',
                    'name': 'stdout',
                    'level': 'info',
                    'format': '%(message)s',
                },
                {
                    'type': 'file',
                    'name': 'reframe.out',
                    'level': 'info',
                    'format': '%(message)s',
                    'append': False,
                },
            ],
            'handlers_perflog': [
                {
                    'type': 'filelog',
                    'prefix': '%(check_system)s/%(check_partition)s',
                    'level': 'info',
                    'format': '%(check_job_completion_time)s ' + perf_logging_format,
                    'format_perfvars': format_perfvars,
                    'append': True,
                },
                {
                    'type': 'syslog',
                    'address': '/dev/log',
                    'level': syslog_level,
                    'format': perf_logging_format,
                    'format_perfvars': format_perfvars,
                    'append': True,
                },
            ],
        }
    ],
}
