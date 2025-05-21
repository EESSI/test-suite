import os

from eessi.testsuite.common_config import common_logging_config, common_general_config, common_eessi_init
from eessi.testsuite.constants import *  # noqa: F403

# This config will write all staging, output and logging to subdirs under this prefix
# Override with RFM_PREFIX environment variable
reframe_prefix = os.path.join(os.environ['HOME'], 'reframe_runs')

# This is an example configuration file
site_configuration = {
    'systems': [
        {
            'name': 'deucalion',
            'descr': 'Deucalion, a EuroHPC JU system',
            'modules_system': 'lmod',
            'hostnames': ['ln*', 'cn*', 'gn*'],
            'prefix': reframe_prefix,
            'partitions': [
                {
                    'name': 'arm',
                    'scheduler': 'slurm',
                    'prepare_cmds': [
                        'wrap.sh << EOF',
                        # bypass CPU autodetection for now aarch64/a64fx,
                        # see https://github.com/EESSI/software-layer/pull/608
                        'export EESSI_SOFTWARE_SUBDIR_OVERRIDE=aarch64/a64fx',
                        common_eessi_init(),
                        # Pass job environment variables like $PATH, etc., into job steps
                        'export SLURM_EXPORT_ENV=HOME,PATH,LD_LIBRARY_PATH,PYTHONPATH',
                    ],
                    'launcher': 'mpirun',
                    # Use --export=None to avoid that login environment is passed down to submitted jobs
                    'access': ['-p normal-arm', '--export=None'],
                    'environs': ['default'],
                    'max_jobs': 120,
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
                        # NB: Deucalion's MaxMemPerNode is undefined. Experimentally I found you cannot submit with
                        # more than --mem=30000M
                        EXTRAS.MEM_PER_NODE: 30000  # in MiB
                    },
                    'descr': 'CPU ARM A64FX partition, see https://docs.macc.fccn.pt/deucalion/#compute-nodes'
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
    'logging': common_logging_config(reframe_prefix),
    'general': [
        {
            # Enable automatic detection of CPU architecture for each partition
            # See https://reframe-hpc.readthedocs.io/en/stable/configure.html#auto-detecting-processor-information
            'remote_detect': True,
            **common_general_config(reframe_prefix)
        }
    ],
}
