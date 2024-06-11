# ReFrame configuration file that can be used in GitHub Actions with EESSI

from eessi.testsuite.common_config import common_logging_config
from eessi.testsuite.constants import *


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
                    'features': [FEATURES[CPU]] + list(SCALES.keys()),
                    'processor': {
                        'num_cpus': 2,
                        'num_cpus_per_core': 1,
                    },
                    'resources': [
                        {
                            'name': 'memory',
                            'options': ['--mem={size}'],
                        }
                    ],
                    'max_jobs': 1,
                    'extras': {
                        # Make sure to round down, otherwise a job might ask for more mem than is available
                        # per node
                        # This is a fictional amount, GH actions probably has less, but only does --dry-run
                        'mem_per_node': 30 * 1024  # in MiB
                    },
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
