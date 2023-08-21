"""
Example configuration file
"""
import os

from eessi.testsuite.common_config import common_logging_config, format_perfvars, perflog_format
from eessi.testsuite.constants import *  # noqa: F403


site_configuration = {
    'systems': [
        {
            'name': 'example',
            'descr': 'Example cluster',
            'modules_system': 'lmod',
            'hostnames': ['*'],
            # Note that the stagedir should be a shared directory available on all nodes running ReFrame tests
            'stagedir': f'/some/shared/dir/{os.environ.get("USER")}/reframe_output/staging',
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
    'logging': common_logging_config,
}

# optional logging to syslog
site_configuration['logging'][0]['handlers_perflog'].append({
    'type': 'syslog',
    'address': '/dev/log',
    'level': 'info',
    'format': f'reframe: {perflog_format}',
    'format_perfvars': format_perfvars,
    'append': True,
})
