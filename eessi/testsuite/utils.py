"""
Utility functions for ReFrame tests
"""

import inspect
import os
import re
import sys
from typing import Iterator, List, Tuple

import reframe as rfm
from reframe.core.exceptions import ReframeFatalError
from reframe.core.logging import getlogger
import reframe.core.runtime as rt
from reframe.frontend.printer import PrettyPrinter
from reframe.utility import find_modules as rf_find_modules

from eessi.testsuite.constants import DEVICE_TYPES

printer = PrettyPrinter()

# global variables
_available_modules = []
_eb_is_available = False
_eb_avail_warning_is_printed = False
_unique_msg_ids = []

try:
    from easybuild.framework.easyconfig.easyconfig import get_toolchain_hierarchy
    from easybuild.tools.options import set_up_configuration
    # avoid checking index
    os.environ['EASYBUILD_IGNORE_INDEX'] = '1'
    set_up_configuration(args='')
    _eb_is_available = True
except ImportError:
    pass


class EESSIError(ReframeFatalError):
    traceback = os.getenv('TRACEBACK', "0")
    addendum = ''
    if traceback.lower() not in ('1', 'true', 'yes', 'on'):
        # don't show traceback for EESSI errors
        sys.tracebacklimit = 0
        addendum = '\nRerun with `TRACEBACK=1 reframe ...` to show the full traceback.'

    def __str__(self):
        return super().__str__() + EESSIError.addendum


def log(msg, logger=printer.debug):
    funcname = inspect.currentframe().f_back.f_code.co_name
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


def is_cuda_required_module(module_names: list) -> bool:
    '''Checks if CUDA seems to be required by given module'''
    requires_cuda = False
    for module in module_names:
        if re.search("(?i)cuda", module):
            requires_cuda = True
    return requires_cuda


def split_module(module: str) -> tuple:
    """
    Split a full module name into (name, version, toolchain_name, toolchain_version, versionsuffix)
    Assumptions:
    1) the module is formatted as any of the following:
    - <name>/<version>
    - <name>/<version>-<toolchain_name>-<toolchain_version>
    - <name>/<version>-<toolchain_name>-<toolchain_version><versionsuffix>
    The following format is NOT supported unless exceptions are added:
    - <name>/<version><versionsuffix>

    2) there are no hyphens in the version, toolchain_name, or toolchain_version unless exceptions are added
    Exceptions:
    - toolchain_name 'intel-compilers'

    Arguments:
    - module: the full module name
    """
    name, modversion = module.split('/')
    parts = modversion.split('-')
    version = parts[0]
    versionsuffix = ''

    if len(parts) == 1:  # system toolchain, no versionsuffix
        parts.extend(['system', 'system'])

    # special casing intel-compilers:
    if parts[1] == 'intel' and parts[2] == 'compilers':
        parts = [parts[0], '-'.join(parts[1:3])] + parts[3:]

    tcname = parts[1]
    tcversion = parts[2]

    if len(parts) >= 4:
        versionsuffix = '-'.join(parts[3:])

    return name, version, tcname, tcversion, versionsuffix


def get_avail_modules() -> List[str]:
    "get all available modules in the system"
    # use global to avoid recalculating the list of available modules multiple times
    global _available_modules
    if not _available_modules:
        ms = rt.runtime().modules_system
        # Returns e.g. ['Bison/', 'Bison/3.7.6-GCCcore-10.3.0', 'BLIS/', 'BLIS/0.8.1-GCC-10.3.0']
        _available_modules = ms.available_modules('')
        # Exclude anything without version, i.e. ending with / (e.g. Bison/)
        _available_modules = [mod for mod in _available_modules if not mod.endswith('/')]
        log(f"Total number of available modules: {len(_available_modules)}")
    if not _available_modules:
        msg = 'No available modules found on the system.'
        raise EESSIError(msg)
    return _available_modules


def find_modules(substr, environ_mapping=None) -> Iterator[Tuple[str, str, str]]:
    """
    Wraps reframe.utility.find_modules in order to provide caching, so that we don't have to do repeated
    module avail calls.
    """
    # TODO: implement caching to make this function more efficient
    return rf_find_modules(substr, environ_mapping)


def get_tc_hierarchy(tcdict):
    """
    Set up EasyBuild configuration and get toolchain hierarchy from a toolchain dict
    """
    global _eb_avail_warning_is_printed
    if _eb_is_available:
        hierarchy = get_toolchain_hierarchy(tcdict)
        if not hierarchy:
            msg = (f'cannot determine toolchain hierarchy for {tcdict}. '
                   ' You may have to update the easybuild python package.')
            getlogger().warning(msg)
        return hierarchy
    else:
        if not _eb_avail_warning_is_printed:
            msg = ("EasyBuild is not available, so cannot determine toolchain hierarchy."
                   " Make sure the easybuild python package is installed.")
            getlogger().warning(msg)
            _eb_avail_warning_is_printed = True


def select_matching_modules(modules: List[str], ref_module: str) -> List[str]:
    """
    Return from a list of modules all modules that match the
    toolchain of a reference module.

    Arguments:
    - modules: list of modules from which a selection is made
    - ref_module: the reference module

    Requirements:
    - recent enough easybuild Python package
    """

    selected_mods = []

    ref_tcname, ref_tcversion = split_module(ref_module)[2:4]
    ref_tcdict = {'name': ref_tcname, 'version': ref_tcversion}
    ref_hierarchy = get_tc_hierarchy(ref_tcdict)
    if not ref_hierarchy:
        return []

    for mod in modules:
        mod_tcname, mod_tcversion = split_module(mod)[2:4]
        mod_tcdict = {'name': mod_tcname, 'version': mod_tcversion}

        mod_hierarchy = get_tc_hierarchy(mod_tcdict)
        if not mod_hierarchy:
            return []

        # toolchain hierarchy does not contain super-toolchains, only sub-toolchains
        if ref_tcdict in mod_hierarchy or mod_tcdict in ref_hierarchy:
            selected_mods.append(mod)

    return selected_mods


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
                "(see https://reframe-hpc.readthedocs.io/en/stable/config_reference.html#config.systems.partitions.processor), "  # noqa: E501
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

        msg = ' '.join([
            f"Key '{extra_key}' missing in the 'extras' dictionary for partition '{test.current_partition.name}'.",
            "Please define this key for the relevant partition in the ReFrame configuration file (see",
            "https://reframe-hpc.readthedocs.io/en/stable/config_reference.html#config.systems.partitions.extras).",
        ])

    else:
        msg = ' '.join([
            "This test's current_partition is not set yet.",
            "The function utils.check_extras_key_defined should only be called after the setup() phase of ReFrame.",
            "This is a programming error, please report this issue.",
        ])
    raise AttributeError(msg)


def log_once(test: rfm.RegressionTest, msg: str, msg_id: str, level: str = 'info'):
    """
    This function only prints message msg to the reframe logger once for a
    given unique combination of test class and msg_id. In other words: for a
    given test, one can come up with a a unique msg_id, and call this function
    multiple times with the same msg_id - yet only one message will be logged.
    This is useful in e.g. making sure the logging output doesn't get flooded
    when a highly parameterized test has many different test instances.
    """
    unique_id = f'{test.__class__.__name__}_{msg_id}'

    if unique_id in _unique_msg_ids:
        return

    _unique_msg_ids.append(unique_id)
    loglevel = getattr(getlogger(), level)
    loglevel(f'{test.__class__.__name__}: {msg}')
