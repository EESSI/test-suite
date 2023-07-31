"""
Utility functions for ReFrame tests
"""

import re
import sys
from typing import Iterator

import reframe as rfm
import reframe.core.runtime as rt
from reframe.frontend.printer import PrettyPrinter
from reframe.utility import OrderedSet

from eessi.testsuite.constants import *

printer = PrettyPrinter()


def log(msg, logger=printer.debug):
    funcname = sys._getframe().f_back.f_code.co_name
    logger(f'[{funcname}]: {msg}')


def _get_gpu_list(test: rfm.RegressionTest) -> list:
    return [dev.num_devices for dev in test.current_partition.devices if dev.device_type == DEVICE_TYPES[GPU]]


def get_max_avail_gpus_per_node(test: rfm.RegressionTest) -> int:
    """
    Returns the maximum available number of GPUs per node for the current partition,
    taken from 'num_devices' of device GPU_DEV_NAME in the 'devices' attribute of the current partition
    """
    gpu_list = _get_gpu_list(test)
    # If multiple devices have type DEVICE_TYPES[GPU] in the current partition,
    # we don't know for which to return the device count...
    if len(gpu_list) != 1:
        partname = test.current_partition.name
        raise ValueError(
            f"{len(gpu_list)} devices defined in config file with name {DEVICE_TYPES[GPU]} for partition {partname}. "
            "Cannot determine maximum number of GPUs available for the test. "
            f"Please check the definition of partition {partname} in your ReFrame config file."
        )

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


def find_modules(substr: str) -> Iterator[str]:
    """Return all modules in the current system that contain ``substr`` in their name."""
    if not isinstance(substr, str):
        raise TypeError("'substr' argument must be a string")

    ms = rt.runtime().modules_system
    modules = OrderedSet(ms.available_modules(substr))
    for m in modules:
        yield m

def check_proc_attribute_defined(test: rfm.RegressionTest, attribute) -> bool:
    """
    Checks if a processor feature is defined (i.e. if test.current_partition.processor.<somefeature> is defined)
    If not, throws an informative error message. 
    
    Arguments:
    - test: the reframe regression test instance for which should be checked if the processor feature is defined
    - attribute: attribute of the processor object, as defined by systems.partitions.processor

    Return:
    - True (bool) if the attribute is defined
    - Function does not return (but raises an error) if the attribute is undefined

    Current known attributes in ReFrame are arch, num_cpus, num_cpus_per_core and topology, 
    but this may change in the future.

    If ReFrame's autodetect feature is used, all of these should be properly defined, so that's what we advice.
    """

    if test.current_partition:
        if getattr(test.current_partition.processor, attribute):
            return True
        else:
            msg = (
                f"Processor information ({attribute}) missing. "
                "Check that processor information is either autodetected "
                "(see https://reframe-hpc.readthedocs.io/en/stable/configure.html#proc-autodetection), "
                "or manually set in the ReFrame configuration file "
                "(see https://reframe-hpc.readthedocs.io/en/stable/config_reference.html#processor-info)."
            )
    else:
        msg = (
            "This test's current_partition is not set yet. "
            "The function utils.proc_attribute_defined should only be called after the setup() phase of ReFrame."
            "This is a programming error, please report this issue."
        )
        raise AttributeError(msg)
    