"""
Constants for ReFrame tests
"""

AMD = 'AMD'
CI = 'CI'
HWTHREAD = 'HWTHREAD'
CPU = 'CPU'
CPU_SOCKET = 'CPU_SOCKET'
NUMA_NODE = 'NUMA_NODE'
GPU = 'GPU'
GPU_VENDOR = 'GPU_VENDOR'
INTEL = 'INTEL'
NODE = 'NODE'
NVIDIA = 'NVIDIA'
ALWAYS_REQUEST_GPUS = 'ALWAYS_REQUEST_GPUS'

DEVICE_TYPES = {
    CPU: 'cpu',
    GPU: 'gpu',
}

COMPUTE_UNIT = {
    HWTHREAD: 'hwthread',
    CPU: 'cpu',
    CPU_SOCKET: 'cpu_socket',
    NUMA_NODE: 'numa_node',
    GPU: 'gpu',
    NODE: 'node',
}

TAGS = {
    CI: 'CI',
}

FEATURES = {
    CPU: 'cpu',
    GPU: 'gpu',
    ALWAYS_REQUEST_GPUS: 'always_request_gpus',
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
    # num_cpus_per_node and num_gpus_per_node are upper limits:
    # the actual count depends on the specific configuration of cores, gpus, and sockets within the node,
    # as well as the specific test being carried out.
    '1_core': {'num_nodes': 1, 'num_cpus_per_node': 1, 'num_gpus_per_node': 1},
    '2_cores': {'num_nodes': 1, 'num_cpus_per_node': 2, 'num_gpus_per_node': 1},
    '4_cores': {'num_nodes': 1, 'num_cpus_per_node': 4, 'num_gpus_per_node': 1},
    # renamed after v0.2.0 from 1_cpn_2_nodes to make more unique
    '1cpn_2nodes': {'num_nodes': 2, 'num_cpus_per_node': 1, 'num_gpus_per_node': 1},
    # renamed after v0.2.0 from 1_cpn_4_nodes to make more unique
    '1cpn_4nodes': {'num_nodes': 4, 'num_cpus_per_node': 1, 'num_gpus_per_node': 1},
    '1_8_node': {'num_nodes': 1, 'node_part': 8},  # 1/8 node
    '1_4_node': {'num_nodes': 1, 'node_part': 4},  # 1/4 node
    '1_2_node': {'num_nodes': 1, 'node_part': 2},  # 1/2 node
    '1_node': {'num_nodes': 1, 'node_part': 1},
    '2_nodes': {'num_nodes': 2, 'node_part': 1},
    '4_nodes': {'num_nodes': 4, 'node_part': 1},
    '8_nodes': {'num_nodes': 8, 'node_part': 1},
    '16_nodes': {'num_nodes': 16, 'node_part': 1},
}

# When tests are filtered by the hooks, the valid_systems is set to this system name:
INVALID_SYSTEM = "INVALID_SYSTEM"
