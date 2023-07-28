"""
Example configuration file
"""
from os import environ

from eessi.testsuite.constants import *


username = environ.get('USER')

site_configuration = {
    'systems': [
        {
            'name': 'example',
            'descr': 'Example cluster',
            'modules_system': 'lmod',
            'hostnames': ['*'],
            # Note that the stagedir should be a shared directory available on all nodes running ReFrame tests
            'stagedir': f'/some/shared/dir/{username}/reframe_output/staging',
            'partitions': [
                {
                    'name': 'cpu_partition',
                    'scheduler': 'slurm',
                    'launcher': 'mpirun',
                    'access':  ['-p cpu'],
                    'environs': ['default'],
                    'max_jobs': 4,
                    'processor': {
                        'num_cpus': 128,
                        'num_sockets': 2,
                        'num_cpus_per_socket': 64,
                        'arch': 'zen2',
                    },
                    'features': [FEATURES[CPU]],
                    'descr': 'CPU partition'
                },
                {
                    'name': 'gpu_partition',
                    'scheduler': 'slurm',
                    'launcher': 'mpirun',
                    'access':  ['-p gpu'],
                    'environs': ['default'],
                    'max_jobs': 4,
                    'processor': {
                        'num_cpus': 72,
                        'num_sockets': 2,
                        'num_cpus_per_socket': 36,
                        'arch': 'icelake',
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
                    'features': [
                        FEATURES[CPU],
                        FEATURES[GPU],
                    ],
                    'extras': {
                        GPU_VENDOR: GPU_VENDORS[NVIDIA],
                    },
                    'descr': 'GPU partition'
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
    'logging': [
        {
            'level': 'debug',
            'handlers': [
                {
                    'type': 'stream',
                    'name': 'stdout',
                    'level': 'info',
                    'format': '%(message)s'
                },
                {
                    'type': 'file',
                    'name': 'reframe.log',
                    'level': 'debug',
                    'format': '[%(asctime)s] %(levelname)s: %(check_info)s: %(message)s',   # noqa: E501
                    'append': True,
                    'timestamp': "%Y%m%d_%H%M%S",
                }
            ],
            'handlers_perflog': [
                {
                    'type': 'filelog',
                    'prefix': '%(check_system)s/%(check_partition)s',
                    'level': 'info',
                    'format': (
                        '%(check_job_completion_time)s|reframe %(version)s|'
                        '%(check_info)s|jobid=%(check_jobid)s|'
                        '%(check_perf_var)s=%(check_perf_value)s|'
                        'ref=%(check_perf_ref)s '
                        '(l=%(check_perf_lower_thres)s, '
                        'u=%(check_perf_upper_thres)s)|'
                        '%(check_perf_unit)s'
                    ),
                    'append': True
                }
            ]
        }
    ],
}
