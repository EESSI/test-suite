"""
Variables and utility functions for ReFrame tests
"""

import re

import reframe as rfm
import reframe.core.runtime as rt
from reframe.utility import OrderedSet

GPU_DEV_NAME = 'gpu'

SCALES = [
    # (scale_tag, nodes)
    ('1_node', 1),
    ('2_nodes', 2),
    ('4_nodes', 4),
    ('8_nodes', 8),
    ('16_nodes', 16),
]


def _get_gpu_list(test: rfm.RegressionTest):
    return [dev.num_devices for dev in test.current_partition.devices if dev.device_type == GPU_DEV_NAME]


def get_num_gpus_per_node(test: rfm.RegressionTest) -> int:
    '''
    Returns the number of GPUs per node for the current partition,
    taken from 'num_devices' of device GPU_DEV_NAME in the 'devices' attribute of the current partition
    '''
    gpu_list = _get_gpu_list(test)
    # If multiple devices are called 'GPU' in the current partition,
    # we don't know for which to return the device count...
    if len(gpu_list) != 1:
        raise ValueError(f"Multiple different devices exist with the name "
                         f"'{GPU_DEV_NAME}' for partition '{test.current_partition.name}'. "
                         f"Cannot determine number of GPUs available for the test. "
                         f"Please check the definition of partition '{test.current_partition.name}' "
                         f"in your ReFrame config file.")

    return gpu_list[0]


def is_gpu_present(test: rfm.RegressionTest) -> bool:
    '''Checks if GPUs are present in the current partition'''
    return len(_get_gpu_list(test)) >= 1


def is_cuda_required_module(module_name: str) -> bool:
    '''Checks if CUDA seems to be required by given module'''
    requires_cuda = False
    if re.search("(?i)cuda", module_name):
        requires_cuda = True
    return requires_cuda


def find_modules(substr: str) -> str:
    """Return all modules in the current system that contain ``substr`` in their name."""
    if not isinstance(substr, str):
        raise TypeError("'substr' argument must be a string")

    ms = rt.runtime().modules_system
    modules = OrderedSet(ms.available_modules(substr))
    for m in modules:
        yield m
