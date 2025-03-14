"""
Utility functions for ReFrame tests
"""

import re
import sys
from typing import Iterator

import reframe as rfm
import reframe.core.runtime as rt
from reframe.frontend.printer import PrettyPrinter

from eessi.testsuite.constants import *

printer = PrettyPrinter()


def log(msg, logger=printer.debug):
    funcname = sys._getframe().f_back.f_code.co_name
    logger(f'[{funcname}]: {msg}')


def _get_gpu_list(test: rfm.RegressionTest) -> list:
    return [dev.num_devices for dev in test.current_partition.devices if dev.device_type == DEVICE_TYPES.GPU]


def get_max_avail_gpus_per_node(test: rfm.RegressionTest) -> int:
    """
    Returns the maximum available number of GPUs per node for the current partition,
    taken from 'num_devices' of device GPU_DEV_NAME in the 'devices' attribute of the current partition
    """
    gpu_list = _get_gpu_list(test)
    # If multiple devices have type DEVICE_TYPES.GPU in the current partition,
    # we don't know for which to return the device count...
    if len(gpu_list) != 1:
        partname = test.current_partition.name
        raise ValueError(
            f"{len(gpu_list)} devices defined in config file with name {DEVICE_TYPES.GPU} for partition {partname}. "
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


def find_modules(regex: str, name_only=True) -> Iterator[str]:
    """
    Return all modules matching the regular expression regex. Note that since we use re.search,
    a module matches if the regex matches the module name at any place. I.e. the match does
    not have to be at the start of the smodule name

    Arguments:
    - regex: a regular expression
    - name_only: regular expressions will only be matched on the module name, not the version (default: True).

    Note: the name_only feature assumes anything after the last forward '/' is the version,
    and strips that before doing a match.

    Example

    Suppose we have the following modules on a system:

    gompic/2022a
    gompi/2022a
    CGAL/4.14.3-gompi-2022a

    The following calls would return the following respective modules

    find_modules('gompi') => [gompic/2022a, gompi/2022a]
    find_modules('gompi$') => [gompi/2022a]
    find_modules('gompi', name_only = False) => [gompic/2022a, gompi/2022a, CGAL/4.14.3-gompi-2022a]
    find_modules('^gompi', name_only = False) => [gompic/2022a, gompi/2022a]
    find_modules('^gompi/', name_only = False) => [gompi/2022a]
    find_modules('-gompi-2022a', name_only = False) => [CGAL/4.14.3-gompi-2022a]

    """

    if not isinstance(regex, str):
        raise TypeError("'substr' argument must be a string")

    ms = rt.runtime().modules_system
    # Returns e.g. ['Bison/', 'Bison/3.7.6-GCCcore-10.3.0', 'BLIS/', 'BLIS/0.8.1-GCC-10.3.0']
    modules = ms.available_modules('')
    seen = set()
    dupes = []
    for mod in modules:
        # Exclude anything without version, i.e. ending with / (e.g. Bison/)
        if re.search('.*/$', mod):
            continue
        # The thing we yield should always be the original module name (orig_mod), including version
        orig_mod = mod
        if name_only:
            # Remove trailing slashes from the regex (in case the callee forgot)
            regex = regex.rstrip('/')
            # Remove part after the last forward slash, as we assume this is the version
            mod = re.sub('/[^/]*$', '', mod)
        # Match the actual regular expression
        log(f"Matching module {mod} with regex {regex}")
        if re.search(regex, mod):
            log("Match!")
            if orig_mod in seen:
                dupes.append(orig_mod)
            else:
                seen.add(orig_mod)
            yield orig_mod

    if dupes:
        err_msg = "EESSI test-suite cannot handle duplicate modules. "
        err_msg += "Please make sure that only one is available on your system. "
        err_msg += f"The following modules have a duplicate on your system: {dupes}"
        raise ValueError(err_msg)


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
            "The function utils.check_proc_attribute_defined should only be called after the setup() phase of ReFrame."
            "This is a programming error, please report this issue."
        )
    raise AttributeError(msg)


def check_extras_key_defined(test: rfm.RegressionTest, extra_key) -> bool:
    """
    Checks if a specific key is defined in the 'extras' dictionary for the current partition
    (i.e. if test.current_partition.extras[extra_key] is defined)
    If not, throws an informative error message.
    Note that partition extras are defined by free text keys, so any string is (potentially) valid.

    Arguments:
    - test: the reframe regression test instance for which should be checked if the key is defined in 'extras'
    - extra_key: key for which to check in the 'extras' dictionary

    Return:
    - True (bool) if the key is defined
    - Function does not return (but raises an error) if the attribute is undefined
    """

    if test.current_partition:
        if extra_key in test.current_partition.extras:
            return True
        else:
            msg = (
                f"Key '{extra_key}' missing in the 'extras' dictionary for partition '{test.current_partition.name}'."
                "Please define this key for the relevant partition in the ReFrame configuration file (see "
                "https://reframe-hpc.readthedocs.io/en/stable/config_reference.html#config.systems.partitions.extras)."
            )
    else:
        msg = (
            "This test's current_partition is not set yet. "
            "The function utils.check_extras_key_defined should only be called after the setup() phase of ReFrame."
            "This is a programming error, please report this issue."
        )
    raise AttributeError(msg)
