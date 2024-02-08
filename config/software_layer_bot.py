# ReFrame configuration file that can be used in GitHub Actions with EESSI

from eessi.testsuite.common_config import common_logging_config
from eessi.testsuite.constants import *  # noqa: F403


site_configuration = {
    'systems': [
        {
            'name': 'Testing in bot Build jobs for EESSI software Layer',
            'descr': 'Software-layer bot',
            'hostnames': ['.*'],
            'modules_system': 'lmod',
            'partitions': [
                {
                    'name': 'default',
                    'scheduler': 'local',
                    'launcher': 'mpirun',
                    'environs': ['default'],
                    'features': [FEATURES[CPU]],
                    'resources': [
                        {
                            'name': 'memory',
                            'options': ['--mem={size}'],
                        }
                    ],
                    'max_jobs': 1
                    }
                ]
            }
        ],
    'environments': [
        {
            'name': 'default',
            'cc': 'cc',
            'cxx': '',
            'ftn': ''
            }
        ],
    'general': [
        {
            'purge_environment': True,
            'resolve_module_conflicts': False,  # avoid loading the module before submitting the job
            # Enable automatic detection of CPU architecture
            # See https://reframe-hpc.readthedocs.io/en/stable/configure.html#auto-detecting-processor-information
            'remote_detect': True,
        }
    ],
    'logging': common_logging_config(),
}
