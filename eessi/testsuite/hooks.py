"""
Hooks for adding tags, filtering and setting job resources in ReFrame tests
"""
import math
import shlex
import warnings

import reframe as rfm
import reframe.core.logging as rflog

from eessi.testsuite.constants import *
from eessi.testsuite.utils import (get_max_avail_gpus_per_node, is_cuda_required_module, log,
                                   check_proc_attribute_defined, check_extras_key_defined)


def _assign_default_num_cpus_per_node(test: rfm.RegressionTest):
    """
    Check if the default number of cpus per node is already defined in the test
    (e.g. by earlier hooks like set_tag_scale).
    If so, check if it doesn't exceed the maximum available.
    If not, set default_num_cpus_per_node based on the maximum available cpus and node_part
    """

    if test.default_num_cpus_per_node:
        # may skip if not enough CPUs
        test.skip_if(
            test.default_num_cpus_per_node > test.max_avail_cpus_per_node,
            f'Requested CPUs per node ({test.default_num_cpus_per_node}) is higher than max available'
            f' ({test.max_avail_cpus_per_node}) in current partition ({test.current_partition.name}).'
        )
    else:
        # no default set yet, so setting one
        test.default_num_cpus_per_node = int(test.max_avail_cpus_per_node / test.node_part)

    log(f'default_num_cpus_per_node set to {test.default_num_cpus_per_node}')


def _assign_default_num_gpus_per_node(test: rfm.RegressionTest):
    """
    Check if the default number of gpus per node is already defined in the test
    (e.g. by earlier hooks like set_tag_scale).
    If so, check if it doesn't exceed the maximum available.
    If not, set default_num_gpus_per_node based on the maximum available gpus and node_part
    """

    test.max_avail_gpus_per_node = get_max_avail_gpus_per_node(test)
    if test.default_num_gpus_per_node:
        # may skip if not enough GPUs
        test.skip_if(
            test.default_num_gpus_per_node > test.max_avail_gpus_per_node,
            f'Number of GPUs per node in selected scale ({test.default_num_gpus_per_node}) is higher than max available'
            f' ({test.max_avail_gpus_per_node}) in current partition ({test.current_partition.name}).'
        )
    else:
        # no default set yet, so setting one
        test.default_num_gpus_per_node = math.ceil(test.max_avail_gpus_per_node / test.node_part)


def assign_tasks_per_compute_unit(test: rfm.RegressionTest, compute_unit: str, num_per: int = 1):
    """
    Assign one task per compute unit (COMPUTE_UNIT[CPU], COMPUTE_UNIT[CPU_SOCKET] or COMPUTE_UNIT[GPU]).
    Automatically sets num_tasks, num_tasks_per_node, num_cpus_per_task, and num_gpus_per_node,
    based on the current scale and the current partition’s num_cpus, max_avail_gpus_per_node and num_nodes.
    For GPU tests, one task per GPU is set, and num_cpus_per_task is based on the ratio of CPU-cores/GPUs.
    For CPU tests, one task per CPU is set, and num_cpus_per_task is set to 1.
    Total task count is determined based on the number of nodes to be used in the test.
    Behaviour of this function is (usually) sensible for MPI tests.

    Arguments:
    - test: the ReFrame test to which this hook should apply
    - compute_unit: a device as listed in eessi.testsuite.constants.COMPUTE_UNIT

    Examples:
    On a single node with 2 sockets, 64 cores and 128 hyperthreads:
    - assign_tasks_per_compute_unit(test, COMPUTE_UNIT[CPU]) will launch 64 tasks with 1 thread
    - assign_tasks_per_compute_unit(test, COMPUTE_UNIT[CPU_SOCKET]) will launch 2 tasks with 32 threads per task

    Future work:
    Currently, on a single node with 2 sockets, 64 cores and 128 hyperthreads, this
    - assign_one_task_per_compute_unit(test, COMPUTE_UNIT[CPU], true) launches 128 tasks with 1 thread
    - assign_one_task_per_compute_unit(test, COMPUTE_UNIT[CPU_SOCKET], true) launches 2 tasks with 64 threads per task
    In the future, we'd like to add an arugment that disables spawning tasks for hyperthreads.
    """
    if num_per != 1 and compute_unit in [COMPUTE_UNIT[GPU], COMPUTE_UNIT[CPU], COMPUTE_UNIT[CPU_SOCKET]]:
        raise NotImplementedError(
            f'Non-default num_per {num_per} is not implemented for compute_unit {compute_unit}.')

    check_proc_attribute_defined(test, 'num_cpus')
    test.max_avail_cpus_per_node = test.current_partition.processor.num_cpus
    log(f'max_avail_cpus_per_node set to {test.max_avail_cpus_per_node}')

    # Check if either node_part, or default_num_cpus_per_node and default_num_gpus_per_node are set correctly
    if not (
        isinstance(test.node_part, int)
        or (isinstance(test.default_num_cpus_per_node, int) and isinstance(test.default_num_gpus_per_node, int))
    ):
        raise ValueError(
            f'Either node_part ({test.node_part}), or default_num_cpus_per_node ({test.default_num_cpus_per_node}) and'
            f' default num_gpus_per_node ({test.default_num_gpus_per_node}) must be defined and have integer values.'
        )

    _assign_default_num_cpus_per_node(test)

    if FEATURES[GPU] in test.current_partition.features:
        _assign_default_num_gpus_per_node(test)

    if compute_unit == COMPUTE_UNIT[GPU]:
        _assign_one_task_per_gpu(test)
    elif compute_unit == COMPUTE_UNIT[CPU]:
        _assign_one_task_per_cpu(test)
    elif compute_unit == COMPUTE_UNIT[CPU_SOCKET]:
        _assign_one_task_per_cpu_socket(test)
    elif compute_unit == COMPUTE_UNIT[NODE]:
        _assign_num_tasks_per_node(test, num_per)
    else:
        raise ValueError(f'compute unit {compute_unit} is currently not supported')

    _check_always_request_gpus(test)

    if test.current_partition.launcher_type().registered_name == 'srun':
        # Make sure srun inherits --cpus-per-task from the job environment for Slurm versions >= 22.05 < 23.11,
        # ensuring the same task binding across all Slurm versions.
        # https://bugs.schedmd.com/show_bug.cgi?id=13351
        # https://bugs.schedmd.com/show_bug.cgi?id=11275
        # https://bugs.schedmd.com/show_bug.cgi?id=15632#c43
        test.env_vars['SRUN_CPUS_PER_TASK'] = test.num_cpus_per_task
        log(f'Set environment variable SRUN_CPUS_PER_TASK to {test.env_vars["SRUN_CPUS_PER_TASK"]}')


def _assign_num_tasks_per_node(test: rfm.RegressionTest, num_per: int = 1):
    """
    Sets num_tasks_per_node and num_cpus_per_task such that it will run
    'num_per' tasks per node, unless specified with:
    --setvar num_tasks_per_node=<x>
    --setvar num_cpus_per_task=<y>.
    In those cases, those take precedence, and the remaining variable, if any
    (num_cpus_per task or num_tasks_per_node respectively), is calculated based
    on the equality test.num_tasks_per_node * test.num_cpus_per_task ==
    test.default_num_cpus_per_node.

    Default resources requested:
    - num_tasks_per_node = num_per
    - num_cpus_per_task = test.default_num_cpus_per_node / num_tasks_per_node
    """

    # neither num_tasks_per_node nor num_cpus_per_task are set
    if not test.num_tasks_per_node and not test.num_cpus_per_task:
        test.num_tasks_per_node = num_per
        test.num_cpus_per_task = int(test.default_num_cpus_per_node / test.num_tasks_per_node)

    # num_tasks_per_node is not set, but num_cpus_per_task is
    elif not test.num_tasks_per_node:
        test.num_tasks_per_node = int(test.default_num_cpus_per_node / test.num_cpus_per_task)

    # num_cpus_per_task is not set, but num_tasks_per_node is
    elif not test.num_cpus_per_task:
        test.num_cpus_per_task = int(test.default_num_cpus_per_node / test.num_tasks_per_node)

    else:
        pass  # both num_tasks_per_node and num_cpus_per_task are already set

    test.num_tasks = test.num_nodes * test.num_tasks_per_node

    log(f'num_tasks_per_node set to {test.num_tasks_per_node}')
    log(f'num_cpus_per_task set to {test.num_cpus_per_task}')
    log(f'num_tasks set to {test.num_tasks}')


def _assign_one_task_per_cpu_socket(test: rfm.RegressionTest):
    """
    Determines the number of tasks per node by dividing the default_num_cpus_per_node by
    the number of cpus available per socket, and rounding up. The result is that for full-node jobs the default
    will spawn one task per socket, with a number of cpus per task equal to the number of cpus per socket.
    Other examples:
    - half a node (i.e. node_part=2) on a 4-socket system would result in 2 tasks per node,
    with number of cpus per task equal to the number of cpus per socket.
    - 2 cores (i.e. default_num_cpus_per_node=2) on a 16 core system with 2 sockets would result in
    1 task per node, with 2 cpus per task

    This default is set unless the test is run with:
    --setvar num_tasks_per_node=<x> and/or
    --setvar num_cpus_per_task=<y>.
    In those cases, those take precedence, and the remaining variable (num_cpus_per task or
    num_tasks_per_node respectively) is calculated based on the equality
    test.num_tasks_per_node * test.num_cpus_per_task == test.default_num_cpus_per_node.

    Default resources requested:
    - num_tasks_per_node = default_num_cpus_per_node
    - num_cpus_per_task = default_num_cpus_per_node / num_tasks_per_node
    """
    # neither num_tasks_per_node nor num_cpus_per_task are set
    if not test.num_tasks_per_node and not test.num_cpus_per_task:
        check_proc_attribute_defined(test, 'num_cpus')
        check_proc_attribute_defined(test, 'num_sockets')
        num_cpus_per_socket = test.current_partition.processor.num_cpus / test.current_partition.processor.num_sockets
        test.num_tasks_per_node = math.ceil(test.default_num_cpus_per_node / num_cpus_per_socket)
        test.num_cpus_per_task = int(test.default_num_cpus_per_node / test.num_tasks_per_node)

    # num_tasks_per_node is not set, but num_cpus_per_task is
    elif not test.num_tasks_per_node:
        check_proc_attribute_defined(test, 'num_cpus')
        check_proc_attribute_defined(test, 'num_sockets')
        num_cpus_per_socket = test.current_partition.processor.num_cpus / test.current_partition.processor.num_sockets
        test.num_tasks_per_node = int(test.default_num_cpus_per_node / test.num_cpus_per_task)

    # num_cpus_per_task is not set, but num_tasks_per_node is
    elif not test.num_cpus_per_task:
        test.num_cpus_per_task = int(test.default_num_cpus_per_node / test.num_tasks_per_node)

    else:
        pass  # both num_tasks_per_node and num_cpus_per_node are already set

    test.num_tasks = test.num_nodes * test.num_tasks_per_node
    log(f'Number of tasks per node set to: {test.num_tasks_per_node}')
    log(f'Number of cpus per task set to {test.num_cpus_per_task}')
    log(f'num_tasks set to {test.num_tasks}')


def _assign_one_task_per_cpu(test: rfm.RegressionTest):
    """
    Sets num_tasks_per_node and num_cpus_per_task such that it will run one task per core,
    unless specified with:
    --setvar num_tasks_per_node=<x> and/or
    --setvar num_cpus_per_task=<y>.

    Default resources requested:
    - num_tasks_per_node = default_num_cpus_per_node
    - num_cpus_per_task = default_num_cpus_per_node / num_tasks_per_node
    """
    # neither num_tasks_per_node nor num_cpus_per_task are set
    if not test.num_tasks_per_node and not test.num_cpus_per_task:
        test.num_tasks_per_node = test.default_num_cpus_per_node
        test.num_cpus_per_task = 1

    # num_tasks_per_node is not set, but num_cpus_per_task is
    elif not test.num_tasks_per_node:
        test.num_tasks_per_node = int(test.default_num_cpus_per_node / test.num_cpus_per_task)

    # num_cpus_per_task is not set, but num_tasks_per_node is
    elif not test.num_cpus_per_task:
        test.num_cpus_per_task = int(test.default_num_cpus_per_node / test.num_tasks_per_node)

    else:
        pass  # both num_tasks_per_node and num_cpus_per_node are already set

    test.num_tasks = test.num_nodes * test.num_tasks_per_node

    log(f'num_tasks_per_node set to {test.num_tasks_per_node}')
    log(f'num_cpus_per_task set to {test.num_cpus_per_task}')
    log(f'num_tasks set to {test.num_tasks}')


def _assign_one_task_per_gpu(test: rfm.RegressionTest):
    """
    Sets num_tasks_per_node, num_cpus_per_task, and num_gpus_per_node, unless specified with:
    --setvar num_tasks_per_node=<x> and/or
    --setvar num_cpus_per_task=<y> and/or
    --setvar num_gpus_per_node=<z>.

    Default resources requested:
    - num_gpus_per_node = default_num_gpus_per_node
    - num_tasks_per_node = num_gpus_per_node
    - num_cpus_per_task = default_num_cpus_per_node / num_tasks_per_node

    If num_tasks_per_node is set, set num_gpus_per_node equal to either num_tasks_per_node or default_num_gpus_per_node
    (whichever is smallest), unless num_gpus_per_node is also set.
    """

    # neither num_tasks_per_node nor num_gpus_per_node are set
    if not test.num_tasks_per_node and not test.num_gpus_per_node:
        test.num_gpus_per_node = test.default_num_gpus_per_node
        test.num_tasks_per_node = test.num_gpus_per_node

    # num_tasks_per_node is not set, but num_gpus_per_node is
    elif not test.num_tasks_per_node:
        test.num_tasks_per_node = test.num_gpus_per_node

    # num_gpus_per_node is not set, but num_tasks_per_node is
    elif not test.num_gpus_per_node:
        test.num_gpus_per_node = min(test.num_tasks_per_node, test.default_num_gpus_per_node)

    else:
        pass  # both num_tasks_per_node and num_gpus_per_node are already set

    # num_cpus_per_task is not set
    if not test.num_cpus_per_task:
        # limit num_cpus_per_task to the maximum available cpus per gpu
        test.num_cpus_per_task = min(
            int(test.default_num_cpus_per_node / test.num_tasks_per_node),
            int(test.max_avail_cpus_per_node / test.max_avail_gpus_per_node)
        )

    test.num_tasks = test.num_nodes * test.num_tasks_per_node

    log(f'num_gpus_per_node set to {test.num_gpus_per_node}')
    log(f'num_tasks_per_node set to {test.num_tasks_per_node}')
    log(f'num_cpus_per_task set to {test.num_cpus_per_task}')
    log(f'num_tasks set to {test.num_tasks}')


def _set_or_append_valid_systems(test: rfm.RegressionTest, valid_systems: str):
    """
    Sets test.valid_systems based on the valid_systems argument.
    - If valid_systems is an empty string, test.valid_systems is set equal to eessi.testsuite.constants.INVALID_SYSTEM
    - If test.valid_systems was an empty list, leave it as is (test should not be run)
    - If test.valid_systems was at the default value ['*'], it is overwritten by [valid_system]
    - If test.valid_systems was already set and is a list of one element, valid_system is appended to it,
    which allows adding requests for multiple partition features by different hooks.
    - If test.valid_systems was already set and is a list of multiple elements, we warn that the use has to take
    care of filtering him/herself. This is typically the case when someone overrides the valid_systems on command line.
    In this scenario, this function leaves test.valid_systems as it is.
    """

    # This indicates an invalid test that always has to be filtered
    if valid_systems == '':
        test.valid_systems = [INVALID_SYSTEM]
        return

    # test.valid_systems wasn't set yet, so set it
    if len(test.valid_systems) == 0 or test.valid_systems == [INVALID_SYSTEM]:
        # test.valid_systems is empty or invalid, meaning all tests are filtered out. This hook shouldn't change that
        return
    # test.valid_systems still at default value, so overwrite
    elif len(test.valid_systems) == 1 and test.valid_systems[0] == '*':
        test.valid_systems = [valid_systems]
    # test.valid_systems was set before, so append
    elif len(test.valid_systems) == 1:
        test.valid_systems[0] = f'{test.valid_systems[0]} {valid_systems}'
    else:
        warn_msg = f"valid_systems has multiple ({len(test.valid_systems)}) items,"
        warn_msg += " which is not supported by this hook."
        warn_msg += " Make sure to handle filtering yourself."
        warnings.warn(warn_msg)
        return


def filter_supported_scales(test: rfm.RegressionTest):
    """
    Filter tests scales based on which scales are supported by each partition in the ReFrame configuration.
    Filtering is done using features, i.e. the current test scale is requested as a feature.
    Any partition that does not include this feature in the ReFrame configuration file will effectively be filtered out.
    """
    valid_systems = f'+{test.scale}'

    # Change test.valid_systems accordingly:
    _set_or_append_valid_systems(test, valid_systems)

    log(f'valid_systems set to {test.valid_systems}')


def filter_valid_systems_by_device_type(test: rfm.RegressionTest, required_device_type: str):
    """
    Filter valid_systems by required device type and by whether the module supports CUDA,
    unless valid_systems is specified with --setvar valid_systems=<comma-separated-list>.

    Any invalid combination (e.g. a non-CUDA module with a required_device_type GPU) will
    cause the valid_systems to be set to an empty string, and consequently the
    test.valid_systems to an invalid system name (eessi.testsuite.constants.INVALID_SYSTEM).
    """
    is_cuda_module = is_cuda_required_module(test.module_name)

    if is_cuda_module and required_device_type == DEVICE_TYPES[GPU]:
        # CUDA modules and when using a GPU require partitions with FEATURES[GPU] feature and
        # GPU_VENDOR=GPU_VENDORS[NVIDIA] extras
        valid_systems = f'+{FEATURES[GPU]} %{GPU_VENDOR}={GPU_VENDORS[NVIDIA]}'

    elif not is_cuda_module and required_device_type == DEVICE_TYPES[CPU]:
        # Using the CPU requires partitions with FEATURES[CPU] feature
        # Note: making FEATURES[CPU] an explicit feature allows e.g. skipping CPU-based tests on GPU partitions
        valid_systems = f'+{FEATURES[CPU]}'

    elif is_cuda_module and required_device_type == DEVICE_TYPES[CPU]:
        # Note: This applies for CUDA module tests that want to test only on cpus on gpu partitions.
        valid_systems = f'+{FEATURES[CPU]} +{FEATURES[GPU]} %{GPU_VENDOR}={GPU_VENDORS[NVIDIA]}'

    elif not is_cuda_module and required_device_type == DEVICE_TYPES[GPU]:
        # Invalid combination: a module without GPU support cannot use a GPU
        valid_systems = ''

    # Change test.valid_systems accordingly:
    _set_or_append_valid_systems(test, valid_systems)

    log(f'valid_systems set to {test.valid_systems}')


def req_memory_per_node(test: rfm.RegressionTest, app_mem_req: float):
    """
    This hook will request a specific amount of memory per node to the batch scheduler.
    First, it computes which fraction of CPUs is requested from a node, and how much the corresponding (proportional)
    amount of memory would be.
    Then, the hook compares this to how much memory the application claims to need per node (app_mem_req).
    It then passes the maximum of these two numbers to the batch scheduler as a memory request.

    Note: using this hook requires that the ReFrame configuration defines system.partition.extras['mem_per_node']
    That field should be defined in GiB

    Arguments:
    - test: the ReFrame test to which this hook should apply
    - app_mem_req: the amount of memory this application needs (per node) in MiB

    Example 1:
    - A system with 128 cores and 64,000 MiB per node.
    - The test is launched on 64 cores
    - The app_mem_req is 40,000 (MiB)
    In this case, the test requests 50% of the CPUs. Thus, the proportional amount of memory is 32,000 MiB.
    The app_mem_req is higher. Thus, 40,000 MiB (per node) is requested from the batch scheduler.

    Example 2:
    - A system with 128 cores per node, 128,000 MiB mem per node.
    - The test is launched on 64 cores
    - the app_mem_req is 40,000 (MiB)
    In this case, the test requests 50% of the CPUs. Thus, the proportional amount of memory is 64,000 MiB.
    This is higher than the app_mem_req. Thus, 64,000 MiB (per node) is requested from the batch scheduler.
    """
    # Check that the systems.partitions.extra dict in the ReFrame config contains mem_per_node
    check_extras_key_defined(test, 'mem_per_node')
    # Skip if the current partition doesn't have sufficient memory to run the application
    msg = f"Skipping test: nodes in this partition only have {test.current_partition.extras['mem_per_node']} MiB"
    msg += " memory available (per node) accodring to the current ReFrame configuration,"
    msg += f" but {app_mem_req} MiB is needed"
    test.skip_if(test.current_partition.extras['mem_per_node'] < app_mem_req, msg)

    # Compute what is higher: the requested memory, or the memory available proportional to requested CPUs
    # Fraction of CPU cores requested
    check_proc_attribute_defined(test, 'num_cpus')
    cpu_fraction = test.num_tasks_per_node * test.num_cpus_per_task / test.current_partition.processor.num_cpus
    proportional_mem = math.floor(cpu_fraction * test.current_partition.extras['mem_per_node'])
    app_mem_req = math.ceil(app_mem_req)

    scheduler_name = test.current_partition.scheduler.registered_name
    if scheduler_name == 'slurm' or scheduler_name == 'squeue':
        # SLURM defines --mem as memory per node, see https://slurm.schedmd.com/sbatch.html
        # SLURM uses MiB units by default
        log(f"Memory requested by application: {app_mem_req} MiB")
        log(f"Memory proportional to the core count: {proportional_mem} MiB")

        # Request the maximum of the proportional_mem, and app_mem_req to the scheduler
        req_mem_per_node = max(proportional_mem, app_mem_req)

        test.extra_resources = {'memory': {'size': f'{req_mem_per_node}M'}}
        log(f"Requested {req_mem_per_node} MiB per node from the SLURM batch scheduler")

    elif scheduler_name == 'torque':
        # Torque/moab requires asking for --pmem (--mem only works single node and thus doesnt generalize)
        # See https://docs.adaptivecomputing.com/10-0-1/Torque/torque.htm#topics/torque/3-jobs/3.1.3-requestingRes.htm
        # Units are MiB according to the documentation
        # We immediately divide by num_tasks_per_node (before rounding), since -pmem specifies memroy _per process_
        app_mem_req_task = math.ceil(app_mem_req / test.num_tasks_per_node)
        proportional_mem_task = math.floor(proportional_mem / test.num_tasks_per_node)

        # Request the maximum of the proportional_mem, and app_mem_req to the scheduler
        req_mem_per_task = max(proportional_mem_task, app_mem_req_task)

        # We assume here the reframe config defines the extra resource memory as asking for pmem
        # i.e. 'options': ['--pmem={size}']
        test.extra_resources = {'memory': {'size': f'{req_mem_per_task}mb'}}
        log(f"Requested {req_mem_per_task} MiB per task from the torque batch scheduler")

    else:
        logger = rflog.getlogger()
        msg = "hooks.req_memory_per_node does not support the scheduler you configured"
        msg += f" ({test.current_partition.scheduler.registered_name})."
        msg += " The test will run, but since it doesn't request the required amount of memory explicitely,"
        msg += " it may result in an out-of-memory error."
        msg += " Please expand the functionality of hooks.req_memory_per_node for your scheduler."
        # Warnings will, at default loglevel, be printed on stdout when executing the ReFrame command
        logger.warning(msg)


def set_modules(test: rfm.RegressionTest):
    """
    Skip current test if module_name is not among a list of modules,
    specified with --setvar modules=<comma-separated-list>.
    """
    if test.modules and test.module_name not in test.modules:
        test.valid_systems = []
        log(f'valid_systems set to {test.valid_systems}')

    test.modules = [test.module_name]
    log(f'modules set to {test.modules}')


def set_tag_scale(test: rfm.RegressionTest):
    """Set resources and tag based on current scale"""
    scale = test.scale
    test.num_nodes = SCALES[scale]['num_nodes']
    test.default_num_cpus_per_node = SCALES[scale].get('num_cpus_per_node')
    test.default_num_gpus_per_node = SCALES[scale].get('num_gpus_per_node')
    test.node_part = SCALES[scale].get('node_part')
    test.tags.add(scale)
    log(f'tags set to {test.tags}')


def check_custom_executable_opts(test: rfm.RegressionTest, num_default: int = 0):
    """"
    Check if custom executable options were added with --setvar executable_opts=<x>.
    """
    # normalize options
    test.executable_opts = shlex.split(' '.join(test.executable_opts))
    test.has_custom_executable_opts = False
    if len(test.executable_opts) > num_default:
        test.has_custom_executable_opts = True
    log(f'has_custom_executable_opts set to {test.has_custom_executable_opts}')


def set_compact_process_binding(test: rfm.RegressionTest):
    """
    This hook sets a binding policy for process binding.
    More specifically, it will bind each process to subsequent domains of test.num_cpus_per_task cores.

    A few examples:
    - Pure MPI (test.num_cpus_per_task = 1) will result in binding 1 process to each core.
      this will happen in a compact way, i.e. rank 0 to core 0, rank 1 to core 1, etc
    - Hybrid MPI-OpenMP, e.g. test.num_cpus_per_task = 4 will result in binding 1 process to subsequent sets of 4 cores.
      I.e. rank 0 to core 0-3, rank 1 to core 4-7, rank 2 to core 8-11, etc

    It is hard to do this in a portable way. Currently supported for process binding are:
    - Intel MPI (through I_MPI_PIN_DOMAIN)
    - OpenMPI (through OMPI_MCA_rmaps_base_mapping_policy)
    - srun (LIMITED SUPPORT: through SLURM_CPU_BIND, but only effective if task/affinity plugin is enabled)
    """

    # Check if hyperthreading is enabled. If so, divide the number of cpus per task by the number
    # of hw threads per core to get a physical core count
    check_proc_attribute_defined(test, 'num_cpus_per_core')
    num_cpus_per_core = test.current_partition.processor.num_cpus_per_core
    physical_cpus_per_task = int(test.num_cpus_per_task / num_cpus_per_core)

    if test.current_partition.launcher_type().registered_name == 'mpirun':
        # Do binding for intel and OpenMPI's mpirun, and srun
        test.env_vars['I_MPI_PIN_CELL'] = 'core'  # Don't bind to hyperthreads, only to physcial cores
        test.env_vars['I_MPI_PIN_DOMAIN'] = '%s:compact' % physical_cpus_per_task
        test.env_vars['OMPI_MCA_rmaps_base_mapping_policy'] = 'slot:PE=%s' % physical_cpus_per_task
        log(f'Set environment variable I_MPI_PIN_CELL to {test.env_vars["I_MPI_PIN_CELL"]}')
        log(f'Set environment variable I_MPI_PIN_DOMAIN to {test.env_vars["I_MPI_PIN_DOMAIN"]}')
        log('Set environment variable OMPI_MCA_rmaps_base_mapping_policy to '
            f'{test.env_vars["OMPI_MCA_rmaps_base_mapping_policy"]}')
    elif test.current_partition.launcher_type().registered_name == 'srun':
        # Set compact binding for SLURM. Only effective if the task/affinity plugin is enabled
        # and when number of tasks times cpus per task equals either socket, core or thread count
        test.env_vars['SLURM_DISTRIBUTION'] = 'block:block'
        test.env_vars['SLURM_CPU_BIND'] = 'verbose'
        log(f'Set environment variable SLURM_DISTRIBUTION to {test.env_vars["SLURM_DISTRIBUTION"]}')
        log(f'Set environment variable SLURM_CPU_BIND to {test.env_vars["SLURM_CPU_BIND"]}')
    else:
        logger = rflog.getlogger()
        msg = "hooks.set_compact_process_binding does not support the current launcher"
        msg += f" ({test.current_partition.launcher_type().registered_name})."
        msg += " The test will run, but using the default binding strategy of your parallel launcher."
        msg += " This may lead to suboptimal performance."
        msg += " Please expand the functionality of hooks.set_compact_process_binding for your parallel launcher."
        # Warnings will, at default loglevel, be printed on stdout when executing the ReFrame command
        logger.warning(msg)


def set_compact_thread_binding(test: rfm.RegressionTest):
    """
    This hook sets a binding policy for thread binding.
    It sets a number of environment variables to try and set a sensible binding for OPENMP tasks.

    Thread binding is supported for:
    - GNU OpenMP (through OMP_NUM_THREADS, OMP_PLACES and OMP_PROC_BIND)
    - Intel OpenMP (through KMP_AFFINITY)
    """

    # Set thread binding
    test.env_vars['OMP_PLACES'] = 'cores'
    test.env_vars['OMP_PROC_BIND'] = 'close'
    # See https://www.intel.com/content/www/us/en/docs/cpp-compiler/developer-guide-reference/2021-8/thread-affinity-interface.html  # noqa
    test.env_vars['KMP_AFFINITY'] = 'granularity=fine,compact,1,0'
    log(f'Set environment variable OMP_PLACES to {test.env_vars["OMP_PLACES"]}')
    log(f'Set environment variable OMP_PROC_BIND to {test.env_vars["OMP_PROC_BIND"]}')
    log(f'Set environment variable KMP_AFFINITY to {test.env_vars["KMP_AFFINITY"]}')


def _check_always_request_gpus(test: rfm.RegressionTest):
    """
    Make sure we always request enough GPUs if required for the current GPU partition (cluster-specific policy)
    """
    if FEATURES[ALWAYS_REQUEST_GPUS] in test.current_partition.features and not test.num_gpus_per_node:
        test.num_gpus_per_node = test.default_num_gpus_per_node
        log(f'num_gpus_per_node set to {test.num_gpus_per_node} for partition {test.current_partition.name}')
