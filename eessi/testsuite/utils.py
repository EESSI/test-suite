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
from reframe.utility import typecheck as typ

from eessi.testsuite.constants import DEVICE_TYPES

printer = PrettyPrinter()

# global variables
_eb_is_available = False
_eb_avail_warning_is_printed = False
_unique_msg_ids = []
_modules_cache = {}
_mod_hierarchies = {}

try:
    from easybuild.framework.easyconfig.easyconfig import get_toolchain_hierarchy
    from easybuild.tools.options import set_up_configuration
    # avoid checking index
    os.environ['EASYBUILD_IGNORE_INDEX'] = '1'
    set_up_configuration(args='')
    _eb_is_available = True
except ImportError:
    pass


def make_red(msg):
    return f'\033[31m{msg}\033[0m'


class EESSIError(ReframeFatalError):
    traceback = os.getenv('TRACEBACK', "0")
    addendum = ''
    if traceback.lower() not in ('1', 'true', 'yes', 'on'):
        # don't show traceback for EESSI errors
        sys.tracebacklimit = 0
        addendum = '\nRerun with `TRACEBACK=1 reframe ...` to show the full traceback.'

    def __str__(self):
        return make_red(super().__str__()) + EESSIError.addendum


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
    - toolchain_name 'llvm-compilers'

    Arguments:
    - module: the full module name
    """
    name, modversion = module.split('/')
    parts = modversion.split('-')
    version = parts[0]
    versionsuffix = ''

    if len(parts) == 1:  # system toolchain, no versionsuffix
        parts.extend(['system', 'system'])

    # special casing intel-compilers and llvm-compilers:
    if parts[1] in ['intel', 'llvm'] and parts[2] == 'compilers':
        parts = [parts[0], '-'.join(parts[1:3])] + parts[3:]

    tcname = parts[1]
    tcversion = parts[2]

    if len(parts) >= 4:
        versionsuffix = '-'.join(parts[3:])

    return name, version, tcname, tcversion, versionsuffix


def find_modules(regex: str, environ_mapping=None, name_only=True) -> Iterator[Tuple[str, str, str]]:
    """
    Similar to reframe.utility.find_modules:
    - adds caching, so that we don't have to do repeated module avail calls
    - adds the name_only argument

    Arguments:
    - regex: regular expression used to find matching modules
    - environ_mapping: environment mapping
    - name_only: whether to match only the name of the module, not the version
    """

    if not isinstance(regex, str):
        raise TypeError("'regex' argument must be a string")

    if (environ_mapping is not None and not isinstance(environ_mapping, typ.Dict[str, str])):
        raise TypeError("'environ_mapping' argument must be of type Dict[str,str]")

    if name_only:
        # Remove trailing slashes from the regex (in case the callee forgot)
        regex = regex.rstrip('/')

    regex_re = re.compile(regex)
    name_only_re = re.compile(r'/[^/]*$')

    def _is_valid_for_env(mod, env):
        if environ_mapping is None:
            return True

        for patt, env in environ_mapping.items():
            if re.match(patt, mod) and env == env:
                return True

        return False

    ms = rt.runtime().modules_system
    current_system = rt.runtime().system
    snap0 = rt.snapshot()

    for part in current_system.partitions:
        if part.fullname not in _modules_cache:
            _modules_cache[part.fullname] = {}
        for env in part.environs:
            if env.name not in _modules_cache[part.fullname]:
                log(f'Getting available modules for ({part.fullname}, {env.name})')
                rt.loadenv(part.local_env, env)
                available_modules = sorted(ms.available_modules())
                _modules_cache[part.fullname][env.name] = [mod for mod in available_modules if not mod.endswith('/')]
                snap0.restore()
            seen = set()
            dupes = []
            for mod in _modules_cache[part.fullname][env.name]:
                modmod = mod
                if name_only:
                    modmod = name_only_re.sub('', mod)
                if regex_re.search(modmod):
                    log(f"Matched module {mod} with regex {regex}")
                    if mod in seen:
                        dupes.append(mod)
                    else:
                        seen.add(mod)
                    if _is_valid_for_env(mod, env.name):
                        yield (part.fullname, env.name, mod)

            if dupes:
                err_msg = (
                    "EESSI test-suite cannot handle duplicate modules. "
                    "Please make sure that only one is available on your system. "
                    f"The following modules have a duplicate on your system: {sorted(dupes)}"
                )
                raise ValueError(err_msg)


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


def select_matching_modules(module_infos: List[tuple], ref_module_info: tuple) -> List[tuple]:
    """
    Return, from a list of module_info tuples, all module_info tuples with modules that match the
    toolchain of a reference module.

    Arguments:
    - module_infos: list of module info tuples from which a selection is made
    - ref_module_info: the reference module info

    Requirements:
    - recent enough easybuild Python package
    """

    selected_mod_infos = []

    ref_syspart, ref_env, ref_mod = ref_module_info

    ref_tcname, ref_tcversion = split_module(ref_mod)[2:4]
    ref_tcdict = {'name': ref_tcname, 'version': ref_tcversion}
    ref_hierarchy = get_tc_hierarchy(ref_tcdict)
    if not ref_hierarchy:
        return []

    for mod_info in module_infos:
        syspart, env, mod = mod_info
        # only select the ones that have the same system:partition and environment as the reference
        if syspart != ref_syspart or env != ref_env:
            continue

        mod_tcname, mod_tcversion = split_module(mod)[2:4]
        mod_tcdict = {'name': mod_tcname, 'version': mod_tcversion}

        if mod not in _mod_hierarchies:
            _mod_hierarchies[mod] = get_tc_hierarchy(mod_tcdict)

        mod_hierarchy = _mod_hierarchies[mod]
        if not mod_hierarchy:
            return []

        # toolchain hierarchy does not contain super-toolchains, only sub-toolchains
        if ref_tcdict in mod_hierarchy or mod_tcdict in ref_hierarchy:
            selected_mod_infos.append(mod_info)

    return selected_mod_infos


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
