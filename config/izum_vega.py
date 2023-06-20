from os import environ
username = environ.get('USER')

# This is an example configuration file
site_configuration = {
    'general': [
        {
            'remote_detect': True,
        }
    ],
    'systems': [
        {
            'name': 'vega',
            'descr': 'Vega, a EuroHPC JU system',
            'modules_system': 'lmod',
            'hostnames': ['vglogin*','cn*','gn*'],
            'stagedir': f'/ceph/hpc/scratch/user/{username}/reframe_runs/staging',
            'outputdir': f'reframe_runs/',
            'partitions': [
                {
                    'name': 'cpu',
                    'scheduler': 'slurm',
                    'prepare_cmds': ['source /cvmfs/pilot.eessi-hpc.org/latest/init/bash'],
                    'launcher': 'srun',
                    'access':  ['-p cpu', '--export=None'],
                    'environs': ['default'],
                    'max_jobs': 120,
                    'features': [
                        'cpu',
                    ],
                    'descr': 'CPU partition Standard, see https://en-doc.vega.izum.si/architecture/'
                },
                {
                    'name': 'gpu',
                    'scheduler': 'slurm',
                    'prepare_cmds': ['source /cvmfs/pilot.eessi-hpc.org/latest/init/bash'],
                    'launcher': 'srun',
                    'access':  ['-p gpu', '--export=None'],
                    'environs': ['default'],
                    'max_jobs': 60,
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
                    'name': 'reframe.log',
                    'level': 'debug',
                    'format': '[%(asctime)s] %(levelname)s: %(check_info)s: %(message)s',   # noqa: E501
                    'append': False,
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
