from os import environ
username = environ.get('USER')

# This is an example configuration file
site_configuration = {
    'systems': [
        {
            'name': 'snellius',
            'descr': 'Dutch National Supercomputer',
            'modules_system': 'lmod',
            'hostnames': ['int*','tcn*','hcn*','fcn*','gcn*','srv*'],
            'stagedir': f'/scratch-shared/{username}/reframe_output/staging',
            'partitions': [
                {
                    'name': 'thin',
                    'scheduler': 'slurm',
                    'prepare_cmds': ['source $EESSI_INIT'],
                    'launcher': 'mpirun',
                    'access':  ['-p thin --exclusive'],
                    'environs': ['default'],
                    'max_jobs': 120,
                    'processor': {
                        'num_cpus': 128,
                        'num_sockets': 2,
                        'num_cpus_per_socket': 64,
                        'arch': 'znver2',
                    },
                    'features': [
                        'cpu',
                    ],
                    'descr': 'Test CPU partition with native EESSI stack'
                },
                {
                    'name': 'gpu',
                    'scheduler': 'slurm',
                    'prepare_cmds': ['source $EESSI_INIT'],
                    'launcher': 'srun',
                    'access':  ['-p gpu'],
                    'environs': ['default'],
                    'max_jobs': 60,
                    'processor': {
                        'num_cpus': 72,
                        'num_sockets': 2,
                        'num_cpus_per_socket': 36,
                        'arch': 'icelake',
                    },
                    'devices': [
                        {
                            'type': 'gpu',
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
                        'gpu',
                    ],
                    'descr': 'Test GPU partition with native EESSI stack'
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
                    'append': False
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
