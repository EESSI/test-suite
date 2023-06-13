# This is an example configuration file
site_configuration = {
    'systems': [
        {
            'name': 'citc',
            'descr': 'Cluster in the Cloud build and test environment on AWS',
            'modules_system': 'lmod',
    	    'hostnames': ['mgmt', 'login', 'fair-mastodon*'],
            'prefix': f'~/reframe_logs/',
            'partitions': [
                {
                    'name': 'c4.2xlarge (haswell)',
                    'access': ['--constraint shape=c4.2xlarge'],
                    'descr': 'Haswell, 8 cores, 15 GiB',
                },
                {
                    'name': 'c4.4xlarge (haswell)',
                    'access': ['--constraint shape=c4.4xlarge'],
                    'descr': 'Haswell, 16 cores, 30 GiB',
                },
                {
                    'name': 'c5a.2xlarge (ZEN2)',
                    'access': ['--constraint shape=c5a.2xlarge'],
                    'descr': 'Zen2, 8 cores, 16 GiB',
                },
                {
                    'name': 'c5a.4xlarge (ZEN2)',
                    'access': ['--constraint shape=c5a.4xlarge'],
                    'descr': 'Zen2, 16 cores, 32 GiB',
                },
                {
                    'name': 'c6a.2xlarge (ZEN3)',
                    'access': ['--constraint shape=c6a.2xlarge'],
                    'descr': 'Zen3, 8 cores, 16 GiB',
                },
                {
                    'name': 'c6a.4xlarge (ZEN3)',
                    'access': ['--constraint shape=c6a.4xlarge'],
                    'descr': 'Zen3, 16 cores, 32 GiB',
                },
                {
                    'name': 'c5.2xlarge (Skylake or Cascade lake)',
                    'access': ['--constraint shape=c5.2xlarge'],
                    'descr': 'Skylake/Cascade lake, 8 cores, 16 GiB',
                },
                {
                    'name': 'c5.4xlarge (Skylake or Cascade lake)',
                    'access': ['--constraint shape=c5.4xlarge'],
                    'descr': 'Skylake/Cascade lake, 16 cores, 32 GiB',
                },
                {
                    'name': 'c5d.2xlarge (Skylake or Cascade lake)',
                    'access': ['--constraint shape=c5d.2xlarge'],
                    'descr': 'Skylake/Cascade lake, 8 cores, 16 GiB, 200GB NVMe',
                },
                {
                    'name': 'c6i.2xlarge (Icelake)',
                    'access': ['--constraint shape=c6i.2xlarge'],
                    'descr': 'Icelake, 8 cores, 16 GiB',
                },
                {
                    'name': 'c6g.2xlarge (Graviton2)',
                    'access': ['--constraint shape=c6g.2xlarge'],
                    'descr': 'Graviton2, 8 cores, 16 GiB',
                },
                {
                    'name': 'c6g.4xlarge (Graviton2)',
                    'access': ['--constraint shape=c6g.4xlarge'],
                    'descr': 'Graviton2, 16 cores, 32 GiB',
                },
                {
                    'name': 'c6g.8xlarge (Graviton2)',
                    'access': ['--constraint shape=c6g.8xlarge'],
                    'descr': 'Graviton2, 32 cores, 64 GiB',
                },
                {
                    'name': 'c7g.2xlarge (Graviton3)',
                    'access': ['--constraint shape=c7g.2xlarge'],
                    'descr': 'Graviton3, 8 cores, 16 GiB',
                },
                {
                    'name': 'c7g.4xlarge (Graviton3)',
                    'access': ['--constraint shape=c7g.4xlarge'],
                    'descr': 'Graviton3, 16 cores, 32 GiB',
                },
#                 {
#                     'name': 'cpu',
#                     'scheduler': 'squeue',
#                     'launcher': 'mpirun',
#                     # By default, the Magic Castle cluster only allocates a small amount of memory
#                     # Thus we request the full memory explicitely
#                     'access':  ['-C shape=c5a.16xlarge'],
#                     'environs': ['builtin'],
#                     'max_jobs': 4,
#                     'processor': {
#                         'num_cpus': 64,
#                     },
#                     'descr': 'normal CPU partition'
#                 },
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
    'general': [
        {
            'remote_detect': True,
        }
    ],
}

# Add default things to each partition:
partition_defaults = {
    'scheduler': 'squeue',
    'launcher': 'mpirun',
    'environs': ['default'],
    'features': ['cpu'],
    'prepare_cmds': ['source /cvmfs/pilot.eessi-hpc.org/latest/init/bash'],
}
for system in site_configuration['systems']:
    for partition in system['partitions']:
        partition.update(partition_defaults)
