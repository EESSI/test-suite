from os import environ, makedirs

from eessi.testsuite.constants import FEATURES, DEVICES

# Get username of current user
homedir = environ.get('HOME')

# This config will write all staging, output and logging to subdirs under this prefix
reframe_prefix = f'{homedir}/reframe_runs'
log_prefix = f'{reframe_prefix}/logs'

# ReFrame complains if the directory for the file logger doesn't exist yet
makedirs(f'{log_prefix}', exist_ok=True)

# This is an example configuration file
site_configuration = {
    'general': [
        {
            # Enable automatic detection of CPU architecture for each partition
            # See https://reframe-hpc.readthedocs.io/en/stable/configure.html#auto-detecting-processor-information
            'remote_detect': True,
        }
    ],
    'systems': [
        {
            'name': 'vega',
            'descr': 'Vega, a EuroHPC JU system',
            'modules_system': 'lmod',
            'hostnames': ['vglogin*','cn*','gn*'],
            'prefix': reframe_prefix,
            'partitions': [
                {
                    'name': 'cpu',
                    'scheduler': 'slurm',
                    'prepare_cmds': [
                        'source /cvmfs/pilot.eessi-hpc.org/latest/init/bash',
                        # Pass job environment variables like $PATH, etc., into job steps
                        'export SLURM_EXPORT_ENV=ALL',
                        # Needed when using srun launcher
                        'export SLURM_MPI_TYPE=pmix',
                        # Avoid https://github.com/EESSI/software-layer/issues/136
                        # Can be taken out once we don't care about old OpenMPI versions anymore (pre-4.1.1)
                        'export OMPI_MCA_pml=ucx',
                    ],
                    'launcher': 'mpirun',  # Needs to be temporarily changed to srun for cpu autodetection
                    # Use --export=None to avoid that login environment is passed down to submitted jobs
                    'access':  ['-p cpu', '--export=None'],
                    'environs': ['default'],
                    'max_jobs': 120,
                    'features': [
                        FEATURES['CPU'],
                    ],
                    'descr': 'CPU partition Standard, see https://en-doc.vega.izum.si/architecture/'
                },
                {
                    'name': 'gpu',
                    'scheduler': 'slurm',
                    'prepare_cmds': [
                        'source /cvmfs/pilot.eessi-hpc.org/latest/init/bash',
                        # Pass job environment variables like $PATH, etc., into job steps
                        'export SLURM_EXPORT_ENV=ALL',
                        # Needed when using srun launcher
                        'export SLURM_MPI_TYPE=pmix',
                        # Avoid https://github.com/EESSI/software-layer/issues/136
                        # Can be taken out once we don't care about old OpenMPI versions anymore (pre-4.1.1)
                        'export OMPI_MCA_pml=ucx',
                    ],
                    'launcher': 'mpirun',  # Needs to be temporarily changed to srun for cpu autodetection
                    # Use --export=None to avoid that login environment is passed down to submitted jobs
                    'access':  ['-p gpu', '--export=None'],
                    'environs': ['default'],
                    'max_jobs': 60,
                    'devices': [
                        {
                            'type': DEVICES['GPU'],
                            'num_devices': 4,
                        }
                    ],
                    'resources': [
                        {
                            'name': '_rfm_gpu',
                            'options': ['--gpus-per-node={num_gpus_per_node}'],
                        }
                    ],
                    'features': [
                        FEATURES['GPU'],
                    ],
                    'descr': 'GPU partition, see https://en-doc.vega.izum.si/architecture/'
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
                    'name': f'{log_prefix}/reframe.log',
                    'level': 'debug',
                    'format': '[%(asctime)s] %(levelname)s: %(check_info)s: %(message)s',   # noqa: E501
                    'append': True,
                    'timestamp': "%Y%m%d_%H%M%S",
                }
            ],
            'handlers_perflog': [
                {
                    'type': 'filelog',
                    'prefix': f'{log_prefix}/%(check_system)s/%(check_partition)s',
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
