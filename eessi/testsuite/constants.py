"""
Constants for ReFrame tests
"""

AMD = 'AMD'
CI = 'CI'
CPU = 'CPU'
CPU_SOCKET = 'CPU_SOCKET'
GPU = 'GPU'
GPU_VENDOR = 'GPU_VENDOR'
INTEL = 'INTEL'
NVIDIA = 'NVIDIA'

DEVICE_TYPES = {
    CPU: 'cpu',
    GPU: 'gpu',
}

COMPUTE_UNIT = {
    CPU: 'cpu',
    CPU_SOCKET: 'cpu_socket',
    GPU: 'gpu',
}

TAGS = {
    CI: 'CI',
}

FEATURES = {
    CPU: 'cpu',
    GPU: 'gpu',
}

GPU_VENDORS = {
    AMD: 'amd',
    INTEL: 'intel',
    NVIDIA: 'nvidia',
}

SCALES = {
        # required keys:
        # - num_nodes
        # - either node_part or (num_cpus_per_node and num_gpus_per_node)
        '1_core': {'num_nodes': 1, 'num_cpus_per_node': 1, 'num_gpus_per_node': 1},
        '2_cores': {'num_nodes': 1, 'num_cpus_per_node': 2, 'num_gpus_per_node': 1},
        '4_cores': {'num_nodes': 1, 'num_cpus_per_node': 4, 'num_gpus_per_node': 1},
        '1_8_node': {'num_nodes': 1, 'node_part': 8},  # 1/8 node
        '1_4_node': {'num_nodes': 1, 'node_part': 4},  # 1/4 node
        '1_2_node': {'num_nodes': 1, 'node_part': 2},  # 1/2 node
        '1_node': {'num_nodes': 1, 'node_part': 1},
        '2_nodes': {'num_nodes': 2, 'node_part': 1},
        '4_nodes': {'num_nodes': 4, 'node_part': 1},
        '8_nodes': {'num_nodes': 8, 'node_part': 1},
        '16_nodes': {'num_nodes': 16, 'node_part': 1},
}
