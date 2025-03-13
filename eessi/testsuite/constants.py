"""
Constants for ReFrame tests
"""
from typing import NamedTuple


class Extras(NamedTuple):
    GPU_VENDOR = 'gpu_vendor'
    MEM_PER_NODE = 'mem_per_node'


class DeviceTypes(NamedTuple):
    "device types"
    CPU = 'cpu'
    GPU = 'gpu'


class ComputeUnits(NamedTuple):
    "compute units"
    CPU = 'cpu'
    CPU_SOCKET = 'cpu_socket'
    GPU = 'gpu'
    HWTHREAD = 'hwthread'
    NODE = 'node'
    NUMA_NODE = 'numa_node'


class Tags(NamedTuple):
    "tags"
    CI = 'CI'


class Features(NamedTuple):
    "features"
    CPU = 'cpu'
    GPU = 'gpu'
    ALWAYS_REQUEST_GPUS = 'always_request_gpus'


class GPUVendors(NamedTuple):
    "GPU vendors"
    AMD = 'amd'
    INTEL = 'intel'
    NVIDIA = 'nvidia'


EXTRAS = Extras()
DEVICE_TYPES = DeviceTypes()
COMPUTE_UNITS = ComputeUnits()
TAGS = Tags()
FEATURES = Features()
GPU_VENDORS = GPUVendors()

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
