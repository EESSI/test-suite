from eessi.testsuite.common_config import (common_general_config, common_logging_config,
                                           get_sbatch_account, set_common_required_config)
from eessi.testsuite.constants import EXTRAS, FEATURES, DEVICE_TYPES, SCALES, GPU_VENDORS


# Site Configuration
site_configuration = {
    'systems': [
        {
            'name': 'sofia',
            'descr': 'VSC sofia',
            'hostnames': ['*'],
            'modules_system': 'lmod',
            'partitions': [
                {
                    'name': 'zen5_dense',
                    'access': [f'-A {get_sbatch_account()} --partition=zen5_dense'],
                    'descr': '384-core Zen5 CPU partition',
                    'processor': {
                        'num_cpus': 384,
                        'num_sockets': 2,
                        'num_cpus_per_socket': 192,
                        'num_cpus_per_core': 1,
                    },
                    'environs': ['localenv'],
                    'extras': {
                        EXTRAS.MEM_PER_NODE: 42008848,
                    },
                    'features': [
                        FEATURES.CPU,
                    ] + [x for x in SCALES if x not in ['8_nodes', '16_nodes']],
                },
                {
                    'name': 'zen4_h200',
                    'access': [f'-A {get_sbatch_account()} --partition=zen4_h200'],
                    'descr': '8-GPU H200 GPU partition',
                    'processor': {
                        'num_cpus': 192,
                        'num_sockets': 2,
                        'num_cpus_per_socket': 96,
                        'num_cpus_per_core': 1,
                    },
                    'environs': ['localenv'],
                    'extras': {
                        EXTRAS.MEM_PER_NODE: 33030426,
                        EXTRAS.GPU_VENDOR: GPU_VENDORS.NVIDIA,
                    },
                    'features': [
                        FEATURES.GPU,
                        '1_8_node', '1_4_node', '1_2_node', '1_node', '2_nodes',
                    ],
                    'devices': [
                        {
                            'type': DEVICE_TYPES.GPU,
                            'num_devices': 8,
                        }
                    ],
                },
            ],
        },
    ],
    'environments': [
        {
            'name': 'localenv',
        },
    ],
    'general': [
        {
            **common_general_config(),
        }
    ],
    'logging': common_logging_config(),
}

# Additional config options that are the same for all sofia partitions:
common_sofia_config = {
    'scheduler': 'slurm',
    'launcher': 'mpirun',
    'max_jobs': 1,
}
for system in site_configuration['systems']:
    for partition in system['partitions']:
        partition.update(common_sofia_config)

# Set common Slurm config options
eessi_prepare_cmds = [
    'export MODULEPATH=/cvmfs/software.eessi.io/init/modules',
    'export LMOD_IGNORE_CACHE=1',  # workaround for Lmod issue, should be fixed with newer Lmod version
]
set_common_required_config(site_configuration, set_memory=False, eessi_prepare_cmds=eessi_prepare_cmds)
