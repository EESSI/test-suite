"""
Constants for ReFrame tests
"""
from typing import NamedTuple


class _Extras(NamedTuple):
    "extras keys"
    GPU_VENDOR: str = 'gpu_vendor'
    MEM_PER_NODE: str = 'mem_per_node'


class _DeviceTypes(NamedTuple):
    "device types"
    CPU: str = 'cpu'
    GPU: str = 'gpu'


class _ComputeUnits(NamedTuple):
    "compute units"
    CPU: str = 'cpu'
    CPU_SOCKET: str = 'cpu_socket'
    GPU: str = 'gpu'
    HWTHREAD: str = 'hwthread'
    NODE: str = 'node'
    NUMA_NODE: str = 'numa_node'


class _Tags(NamedTuple):
    "tags"
    CI: str = 'CI'


class _Features(NamedTuple):
    "features"
    CPU: str = 'cpu'
    GPU: str = 'gpu'
    ALWAYS_REQUEST_GPUS: str = 'always_request_gpus'


class _GPUVendors(NamedTuple):
    "GPU vendors"
    AMD: str = 'amd'
    INTEL: str = 'intel'
    NVIDIA: str = 'nvidia'


EXTRAS = _Extras()
DEVICE_TYPES = _DeviceTypes()
COMPUTE_UNITS = _ComputeUnits()
TAGS = _Tags()
FEATURES = _Features()
GPU_VENDORS = _GPUVendors()

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
