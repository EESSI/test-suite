# This is an example configuration file
site_configuration = {
    'systems': [
        {
            'name': 'citc',
            'descr': 'Cluster in the Cloud build and test environment on AWS',
            'modules_system': 'lmod',
    	    'hostnames': ['mgmt', 'login', 'fair-mastodon*'],
            'prefix': f'reframe_logs/',
            'partitions': [
                {
                    'name': 'c4.2xlarge-haswell',
                    'access': ['--constraint shape=c4.2xlarge', '--export=NONE'],
                    'descr': 'Haswell, 8 cores, 15 GiB',
                },
                {
                    'name': 'c4.4xlarge-haswell',
                    'access': ['--constraint shape=c4.4xlarge', '--export=NONE'],
                    'descr': 'Haswell, 16 cores, 30 GiB',
                },
                {
                    'name': 'c5a.2xlarge-zen2',
                    'access': ['--constraint shape=c5a.2xlarge', '--export=NONE'],
                    'descr': 'Zen2, 8 cores, 16 GiB',
                },
                {
                    'name': 'c5a.4xlarge-zen2',
                    'access': ['--constraint shape=c5a.4xlarge', '--export=NONE'],
                    'descr': 'Zen2, 16 cores, 32 GiB',
                },
                {
                    'name': 'c6a.2xlarge-zen3',
                    'access': ['--constraint shape=c6a.2xlarge', '--export=NONE'],
                    'descr': 'Zen3, 8 cores, 16 GiB',
                },
                {
                    'name': 'c6a.4xlarge-zen3',
                    'access': ['--constraint shape=c6a.4xlarge', '--export=NONE'],
                    'descr': 'Zen3, 16 cores, 32 GiB',
                },
                {
                    'name': 'c5.2xlarge-skylake-cascadelake',
                    'access': ['--constraint shape=c5.2xlarge', '--export=NONE'],
                    'descr': 'Skylake/Cascade lake, 8 cores, 16 GiB',
                },
                {
                    'name': 'c5.4xlarge-skylake-cascadelake',
                    'access': ['--constraint shape=c5.4xlarge', '--export=NONE'],
                    'descr': 'Skylake/Cascade lake, 16 cores, 32 GiB',
                },
                {
                    'name': 'c5d.2xlarge-skylake-cascadelake',
                    'access': ['--constraint shape=c5d.2xlarge', '--export=NONE'],
                    'descr': 'Skylake/Cascade lake, 8 cores, 16 GiB, 200GB NVMe',
                },
                {
                    'name': 'c6i.2xlarge-icelake',
                    'access': ['--constraint shape=c6i.2xlarge', '--export=NONE'],
                    'descr': 'Icelake, 8 cores, 16 GiB',
                },
                {
                    'name': 'c6g.2xlarge-graviton2',
                    'access': ['--constraint shape=c6g.2xlarge', '--export=NONE'],
                    'descr': 'Graviton2, 8 cores, 16 GiB',
                },
                {
                    'name': 'c6g.4xlarge-graviton2',
                    'access': ['--constraint shape=c6g.4xlarge', '--export=NONE'],
                    'descr': 'Graviton2, 16 cores, 32 GiB',
                },
                {
                    'name': 'c6g.8xlarge-graviton2',
                    'access': ['--constraint shape=c6g.8xlarge', '--export=NONE'],
                    'descr': 'Graviton2, 32 cores, 64 GiB',
                },
                {
                    'name': 'c7g.2xlarge-graviton3',
                    'access': ['--constraint shape=c7g.2xlarge', '--export=NONE'],
                    'descr': 'Graviton3, 8 cores, 16 GiB',
                },
                {
                    'name': 'c7g.4xlarge-graviton3',
                    'access': ['--constraint shape=c7g.4xlarge', '--export=NONE'],
                    'descr': 'Graviton3, 16 cores, 32 GiB',
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
    'general': [
        {
            'remote_detect': True,
        }
    ],
}

# Add default things to each partition:
partition_defaults = {
    'scheduler': 'squeue',
    # Can't use mpirun, because there is no system mpirun on citc
    # See https://github.com/EESSI/test-suite/pull/53#issuecomment-1590849226
    'launcher': 'mpirun',
    'environs': ['default'],
    'features': ['cpu'],
    'prepare_cmds': ['source /cvmfs/pilot.eessi-hpc.org/latest/init/bash '],
}
for system in site_configuration['systems']:
    for partition in system['partitions']:
        partition.update(partition_defaults)
