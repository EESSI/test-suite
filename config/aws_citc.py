# This is an example configuration file

# Note that CPU autodetect currently does not work with this configuration file on AWS
# In order to do CPU autodetection, two changes are needed:
# 1. Remove all '--export=NONE'
# 2. Set 'launcher = srun'
# You can run the CPU autodetect by listing all tests (reframe -l ...)
# and then, once all CPUs are autodetected, change the config back for a 'real' run (reframe -r ...)

from os import environ, makedirs

from eessi.testsuite.constants import FEATURES

# CPU topologies for Graviton nodes
# Can be removed once autodetection works on Graviton nodes
citc_aarch64_graviton2_8c_16gb = {
  "arch": "neoverse_n1",
  "topology": {
    "numa_nodes": [
      "0xff"
    ],
    "sockets": [
      "0xff"
    ],
    "cores": [
      "0x01",
      "0x02",
      "0x04",
      "0x08",
      "0x10",
      "0x20",
      "0x40",
      "0x80"
    ],
    "caches": [
      {
        "type": "L2",
        "size": 1048576,
        "linesize": 64,
        "associativity": 0,
        "num_cpus": 1,
        "cpusets": [
          "0x01",
          "0x02",
          "0x04",
          "0x08",
          "0x10",
          "0x20",
          "0x40",
          "0x80"
        ]
      },
      {
        "type": "L1",
        "size": 65536,
        "linesize": 64,
        "associativity": 0,
        "num_cpus": 1,
        "cpusets": [
          "0x01",
          "0x02",
          "0x04",
          "0x08",
          "0x10",
          "0x20",
          "0x40",
          "0x80"
        ]
      },
      {
        "type": "L3",
        "size": 33554432,
        "linesize": 64,
        "associativity": 0,
        "num_cpus": 8,
        "cpusets": [
          "0xff"
        ]
      }
    ]
  },
  "num_cpus": 8,
  "num_cpus_per_core": 1,
  "num_cpus_per_socket": 8,
  "num_sockets": 1
}

citc_aarch64_graviton2_16c_32gb = {
  "arch": "neoverse_n1",
  "topology": {
    "numa_nodes": [
      "0xffff"
    ],
    "sockets": [
      "0xffff"
    ],
    "cores": [
      "0x0001",
      "0x0002",
      "0x0004",
      "0x0008",
      "0x0010",
      "0x0020",
      "0x0040",
      "0x0080",
      "0x0100",
      "0x0200",
      "0x0400",
      "0x0800",
      "0x1000",
      "0x2000",
      "0x4000",
      "0x8000"
    ],
    "caches": [
      {
        "type": "L2",
        "size": 1048576,
        "linesize": 64,
        "associativity": 0,
        "num_cpus": 1,
        "cpusets": [
          "0x0001",
          "0x0002",
          "0x0004",
          "0x0008",
          "0x0010",
          "0x0020",
          "0x0040",
          "0x0080",
          "0x0100",
          "0x0200",
          "0x0400",
          "0x0800",
          "0x1000",
          "0x2000",
          "0x4000",
          "0x8000"
        ]
      },
      {
        "type": "L1",
        "size": 65536,
        "linesize": 64,
        "associativity": 0,
        "num_cpus": 1,
        "cpusets": [
          "0x0001",
          "0x0002",
          "0x0004",
          "0x0008",
          "0x0010",
          "0x0020",
          "0x0040",
          "0x0080",
          "0x0100",
          "0x0200",
          "0x0400",
          "0x0800",
          "0x1000",
          "0x2000",
          "0x4000",
          "0x8000"
        ]
      },
      {
        "type": "L3",
        "size": 33554432,
        "linesize": 64,
        "associativity": 0,
        "num_cpus": 16,
        "cpusets": [
          "0xffff"
        ]
      }
    ]
  },
  "num_cpus": 16,
  "num_cpus_per_core": 1,
  "num_cpus_per_socket": 16,
  "num_sockets": 1
}

citc_aarch64_graviton2_32c_64gb = {
{
  "arch": "neoverse_n1",
  "topology": {
    "numa_nodes": [
      "0xffffffff"
    ],
    "sockets": [
      "0xffffffff"
    ],
    "cores": [
      "0x00000001",
      "0x00000002",
      "0x00000004",
      "0x00000008",
      "0x00000010",
      "0x00000020",
      "0x00000040",
      "0x00000080",
      "0x00000100",
      "0x00000200",
      "0x00000400",
      "0x00000800",
      "0x00001000",
      "0x00002000",
      "0x00004000",
      "0x00008000",
      "0x00010000",
      "0x00020000",
      "0x00040000",
      "0x00080000",
      "0x00100000",
      "0x00200000",
      "0x00400000",
      "0x00800000",
      "0x01000000",
      "0x02000000",
      "0x04000000",
      "0x08000000",
      "0x10000000",
      "0x20000000",
      "0x40000000",
      "0x80000000"
    ],
    "caches": [
      {
        "type": "L2",
        "size": 1048576,
        "linesize": 64,
        "associativity": 0,
        "num_cpus": 1,
        "cpusets": [
          "0x00000001",
          "0x00000002",
          "0x00000004",
          "0x00000008",
          "0x00000010",
          "0x00000020",
          "0x00000040",
          "0x00000080",
          "0x00000100",
          "0x00000200",
          "0x00000400",
          "0x00000800",
          "0x00001000",
          "0x00002000",
          "0x00004000",
          "0x00008000",
          "0x00010000",
          "0x00020000",
          "0x00040000",
          "0x00080000",
          "0x00100000",
          "0x00200000",
          "0x00400000",
          "0x00800000",
          "0x01000000",
          "0x02000000",
          "0x04000000",
          "0x08000000",
          "0x10000000",
          "0x20000000",
          "0x40000000",
          "0x80000000"
        ]
      },
      {
        "type": "L1",
        "size": 65536,
        "linesize": 64,
        "associativity": 0,
        "num_cpus": 1,
        "cpusets": [
          "0x00000001",
          "0x00000002",
          "0x00000004",
          "0x00000008",
          "0x00000010",
          "0x00000020",
          "0x00000040",
          "0x00000080",
          "0x00000100",
          "0x00000200",
          "0x00000400",
          "0x00000800",
          "0x00001000",
          "0x00002000",
          "0x00004000",
          "0x00008000",
          "0x00010000",
          "0x00020000",
          "0x00040000",
          "0x00080000",
          "0x00100000",
          "0x00200000",
          "0x00400000",
          "0x00800000",
          "0x01000000",
          "0x02000000",
          "0x04000000",
          "0x08000000",
          "0x10000000",
          "0x20000000",
          "0x40000000",
          "0x80000000"
        ]
      },
      {
        "type": "L3",
        "size": 33554432,
        "linesize": 64,
        "associativity": 0,
        "num_cpus": 32,
        "cpusets": [
          "0xffffffff"
        ]
      }
    ]
  },
  "num_cpus": 32,
  "num_cpus_per_core": 1,
  "num_cpus_per_socket": 32,
  "num_sockets": 1
}

citc_aarch64_graviton3_8c_16gb = {
  "arch": "neoverse_n1",
  "topology": {
    "numa_nodes": [
      "0xff"
    ],
    "sockets": [
      "0xff"
    ],
    "cores": [
      "0x01",
      "0x02",
      "0x04",
      "0x08",
      "0x10",
      "0x20",
      "0x40",
      "0x80"
    ],
    "caches": [
      {
        "type": "L2",
        "size": 1048576,
        "linesize": 64,
        "associativity": 0,
        "num_cpus": 1,
        "cpusets": [
          "0x01",
          "0x02",
          "0x04",
          "0x08",
          "0x10",
          "0x20",
          "0x40",
          "0x80"
        ]
      },
      {
        "type": "L1",
        "size": 65536,
        "linesize": 64,
        "associativity": 0,
        "num_cpus": 1,
        "cpusets": [
          "0x01",
          "0x02",
          "0x04",
          "0x08",
          "0x10",
          "0x20",
          "0x40",
          "0x80"
        ]
      },
      {
        "type": "L3",
        "size": 33554432,
        "linesize": 64,
        "associativity": 0,
        "num_cpus": 8,
        "cpusets": [
          "0xff"
        ]
      }
    ]
  },
  "num_cpus": 8,
  "num_cpus_per_core": 1,
  "num_cpus_per_socket": 8,
  "num_sockets": 1
}

citc_aarch64_graviton3_16c_32gb = {
  "arch": "neoverse_n1",
  "topology": {
    "numa_nodes": [
      "0xffff"
    ],
    "sockets": [
      "0xffff"
    ],
    "cores": [
      "0x0001",
      "0x0002",
      "0x0004",
      "0x0008",
      "0x0010",
      "0x0020",
      "0x0040",
      "0x0080",
      "0x0100",
      "0x0200",
      "0x0400",
      "0x0800",
      "0x1000",
      "0x2000",
      "0x4000",
      "0x8000"
    ],
    "caches": [
      {
        "type": "L2",
        "size": 1048576,
        "linesize": 64,
        "associativity": 0,
        "num_cpus": 1,
        "cpusets": [
          "0x0001",
          "0x0002",
          "0x0004",
          "0x0008",
          "0x0010",
          "0x0020",
          "0x0040",
          "0x0080",
          "0x0100",
          "0x0200",
          "0x0400",
          "0x0800",
          "0x1000",
          "0x2000",
          "0x4000",
          "0x8000"
        ]
      },
      {
        "type": "L1",
        "size": 65536,
        "linesize": 64,
        "associativity": 0,
        "num_cpus": 1,
        "cpusets": [
          "0x0001",
          "0x0002",
          "0x0004",
          "0x0008",
          "0x0010",
          "0x0020",
          "0x0040",
          "0x0080",
          "0x0100",
          "0x0200",
          "0x0400",
          "0x0800",
          "0x1000",
          "0x2000",
          "0x4000",
          "0x8000"
        ]
      },
      {
        "type": "L3",
        "size": 33554432,
        "linesize": 64,
        "associativity": 0,
        "num_cpus": 16,
        "cpusets": [
          "0xffff"
        ]
      }
    ]
  },
  "num_cpus": 16,
  "num_cpus_per_core": 1,
  "num_cpus_per_socket": 16,
  "num_sockets": 1
}

# Get username of current user
homedir = environ.get('HOME')

# This config will write all staging, output and logging to subdirs under this prefix
reframe_prefix = f'{homedir}/reframe_runs'
log_prefix = f'{reframe_prefix}/logs'

# ReFrame complains if the directory for the file logger doesn't exist yet
makedirs(f'{log_prefix}', exist_ok=True)

# AWS CITC site configuration
site_configuration = {
    'systems': [
        {
            'name': 'citc',
            'descr': 'Cluster in the Cloud build and test environment on AWS',
            'modules_system': 'lmod',
    	    'hostnames': ['mgmt', 'login', 'fair-mastodon*'],
            'prefix': reframe_prefix,
            'partitions': [
                {
                    'name': 'x86_64-haswell-8c-15gb',
                    'access': ['--constraint=shape=c4.2xlarge', '--export=NONE'],
                    'descr': 'Haswell, 8 cores, 15 GiB',
                },
                {
                    'name': 'x86_64-haswell-16c-30gb',
                    'access': ['--constraint=shape=c4.4xlarge', '--export=NONE'],
                    'descr': 'Haswell, 16 cores, 30 GiB',
                },
                {
                    'name': 'x86_64-zen2-8c-16gb',
                    'access': ['--constraint=shape=c5a.2xlarge', '--export=NONE'],
                    'descr': 'Zen2, 8 cores, 16 GiB',
                },
                {
                    'name': 'x86_64-zen2-16c-32gb',
                    'access': ['--constraint=shape=c5a.4xlarge', '--export=NONE'],
                    'descr': 'Zen2, 16 cores, 32 GiB',
                },
                {
                    'name': 'x86_64-zen3-8c-16gb',
                    'access': ['--constraint=shape=c6a.2xlarge', '--export=NONE'],
                    'descr': 'Zen3, 8 cores, 16 GiB',
                },
                {
                    'name': 'X86_64-zen3-16c-32gb',
                    'access': ['--constraint=shape=c6a.4xlarge', '--export=NONE'],
                    'descr': 'Zen3, 16 cores, 32 GiB',
                },
                {
                    'name': 'x86_64-skylake-cascadelake-8c-16gb',
                    'access': ['--constraint=shape=c5.2xlarge', '--export=NONE'],
                    'descr': 'Skylake/Cascade lake, 8 cores, 16 GiB',
                },
                {
                    'name': 'x86_64-skylake-cascadelake-16c-32gb',
                    'access': ['--constraint=shape=c5.4xlarge', '--export=NONE'],
                    'descr': 'Skylake/Cascade lake, 16 cores, 32 GiB',
                },
                {
                    'name': 'x86_64-skylake-cascadelake-8c-16gb-nvme',
                    'access': ['--constraint=shape=c5d.2xlarge', '--export=NONE'],
                    'descr': 'Skylake/Cascade lake, 8 cores, 16 GiB, 200GB NVMe',
                },
                {
                    'name': 'x86_64-icelake-8c-16gb',
                    'access': ['--constraint=shape=c6i.2xlarge', '--export=NONE'],
                    'descr': 'Icelake, 8 cores, 16 GiB',
                },
                {
                    'name': 'aarch64-graviton2-8c-16gb',
                    'access': ['--constraint=shape=c6g.2xlarge', '--export=NONE'],
                    'descr': 'Graviton2, 8 cores, 16 GiB',
                    'processor': citc_aarch64_graviton2_8c_16gb,
                },
                {
                    'name': 'aarch64-graviton2-16c-32gb',
                    'access': ['--constraint=shape=c6g.4xlarge', '--export=NONE'],
                    'descr': 'Graviton2, 16 cores, 32 GiB',
                    'processor': citc_aarch64_graviton2_16c_32gb,
                },
                {
                    'name': 'aarch64-graviton2-32c-64gb',
                    'access': ['--constraint=shape=c6g.8xlarge', '--export=NONE'],
                    'descr': 'Graviton2, 32 cores, 64 GiB',
                    'processor': citc_aarch64_graviton2_32c_64gb,
                },
                {
                    'name': 'aarch64-graviton3-8c-16gb',
                    'access': ['--constraint=shape=c7g.2xlarge', '--export=NONE'],
                    'descr': 'Graviton3, 8 cores, 16 GiB',
                },
                {
                    'name': 'aarch64-graviton3-16c-32gb',
                    'access': ['--constraint=shape=c7g.4xlarge', '--export=NONE'],
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
                    'prefix': f'{log_prefix}/reframe.log',
                    'name': 'reframe.log',
                    'level': 'debug',
                    'format': '[%(asctime)s] %(levelname)s: %(check_info)s: %(message)s',   # noqa: E501
                    'append': True,
                    'timestamp': "%Y%m%d_%H%M%S",
                },
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
    'general': [
        {
            'remote_detect': True,
        }
    ],
}

# Add default things to each partition:
partition_defaults = {
    'scheduler': 'squeue',
    # mpirun causes problems with cpu autodetect, since there is no system mpirun.
    # See https://github.com/EESSI/test-suite/pull/53#issuecomment-1590849226
    # and this feature request https://github.com/reframe-hpc/reframe/issues/2926
    # However, using srun requires either using pmix or proper pmi2 integration in the MPI library
    # See https://github.com/EESSI/test-suite/pull/53#issuecomment-1598753968
    # Thus, we use mpirun for now, and manually swap to srun if we want to autodetect CPUs...
    'launcher': 'mpirun',
    'environs': ['default'],
    'features': [
        FEATURES['cpu']
    ],
    'prepare_cmds': [
        'source /cvmfs/pilot.eessi-hpc.org/latest/init/bash',
        # Required when using srun as launcher with --export=NONE in partition access, in order to ensure job
        # steps inherit environment. It doesn't hurt to define this even if srun is not used
        'export SLURM_EXPORT_ENV=ALL'
    ],
}
for system in site_configuration['systems']:
    for partition in system['partitions']:
        partition.update(partition_defaults)


