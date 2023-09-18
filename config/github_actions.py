# ReFrame configuration file that can be used in GitHub Actions with EESSI

from eessi.testsuite.common_config import common_logging_config
from eessi.testsuite.constants import *  # noqa: F403


site_configuration = {
    'systems': [
        {
            'name': 'github_actions_eessi',
            'descr': 'GitHub Actions + EESSI',
            'hostnames': ['.*'],
            'modules_system': 'lmod',
            'partitions': [
                {
                    'name': 'default',
                    'scheduler': 'local',
                    'launcher': 'local',
                    'environs': ['default'],
                    'features': [FEATURES[CPU]],
                    'processor': {'num_cpus': 2},
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
        }
    ],
    'logging': common_logging_config(),
}
