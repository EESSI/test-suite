from eessi.testsuite.common_config import common_logging_config
from eessi.testsuite.constants import *  # noqa: F403


site_configuration = {
    'systems': [
        {
            'name': 'BotBuildTests',  # The system HAS to have this name, do NOT change it
            'descr': 'Software-layer bot for RISC-V',
            'hostnames': ['.*'],
            'modules_system': 'lmod',
            'partitions': [
                {
                    'name': 'riscv64_generic',
                    'scheduler': 'local',
                    'launcher': 'mpirun',
                    'environs': ['default'],
                    'features': [
                        FEATURES[CPU]  # We want this to run GPU-based tests from the EESSI test suite
                    ] + list(SCALES.keys()),
                    'resources': [
                        {
                            'name': 'memory',
                            'options': ['--mem={size}'],
                        }
                    ],
                    'extras': {
                        # Make sure to round down, otherwise a job might ask for more mem than is available
                        # per node
                        'mem_per_node': 15486,  # in MiB (512 GB minus some reserved for the OS)
                    },
                    'max_jobs': 1
                },
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
            'remote_detect': True,  # Make sure to automatically detect the CPU topology
        }
    ],
    'logging': common_logging_config(),
}
