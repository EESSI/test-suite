"""
Hooks for adding tags, filtering and setting job resources in ReFrame tests
"""
import math
import shlex

import reframe as rfm
from eessi_utils.constants import DEVICES, FEATURES, SCALES
from eessi_utils import utils

PROCESSOR_INFO_MISSING = '''
This test requires the number of CPUs to be known for the partition it runs on.
Check that processor information is either autodetected
(see https://reframe-hpc.readthedocs.io/en/stable/configure.html#proc-autodetection),
or manually set in the ReFrame configuration file
(see https://reframe-hpc.readthedocs.io/en/stable/config_reference.html#processor-info).
'''


def assign_one_task_per_compute_unit(test: rfm.RegressionTest, compute_unit: str):
    """
    Assign one task per compute unit (DEVICES['CPU'] or DEVICES['GPU']).
    Automatically sets num_tasks, num_tasks_per_node, num_cpus_per_task, and num_gpus_per_node,
    based on the current scale and the current partition’s num_cpus, max_avail_gpus_per_node and num_nodes.
    For GPU tests, one task per GPU is set, and num_cpus_per_task is based on the ratio of CPU-cores/GPUs.
    For CPU tests, one task per CPU is set, and num_cpus_per_task is set to 1.
    Total task count is determined based on the number of nodes to be used in the test.
    Behaviour of this function is (usually) sensible for MPI tests.
    """
    test.max_avail_cpus_per_node = test.current_partition.processor.num_cpus
    if test.max_avail_cpus_per_node is None:
        raise AttributeError(PROCESSOR_INFO_MISSING)

    # Check if either node_part, or default_num_cpus_per_node and default_num_gpus_per_node are set correctly
    if not (
        type(test.node_part) == int or
        (type(test.default_num_cpus_per_node) == int and type(test.default_num_gpus_per_node) == int)
    ):
        raise ValueError(
            f'Either node_part ({test.node_part}), or default_num_cpus_per_node ({test.default_num_cpus_per_node}) and'
            f' default num_gpus_per_node ({test.default_num_gpus_per_node}) must be defined and have integer values.'
        )

    # Check if the default number of cpus per node is already defined in the test
    # (e.g. by earlier hooks like set_tag_scale).
    # If so, check if it doesn't exceed the maximum available.
    # If not, set default_num_cpus_per_node based on the maximum available cpus and node_part
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

    if compute_unit == DEVICES['GPU']:
        _assign_one_task_per_gpu(test)
    elif compute_unit == DEVICES['CPU']:
        _assign_one_task_per_cpu(test)
    else:
        raise ValueError(f'compute unit {compute_unit} is currently not supported')


def _assign_one_task_per_cpu(test: rfm.RegressionTest):
    """
    Sets num_tasks_per_node and num_cpus_per_task such that it will run one task per core,
    unless specified with:
    --setvar num_tasks_per_node=<x> and/or
    --setvar num_cpus_per_task=<y>.

    Variables:
    - default_num_cpus_per_node: default number of CPUs per node as defined in the test
    (e.g. by earlier hooks like set_tag_scale)


    Default resources requested:
    - num_tasks_per_node = default_num_cpus_per_node
    - num_cpus_per_task = default_num_cpus_per_node / num_tasks_per_node
    """
    # neither num_tasks_per_node nor num_cpus_per_node are set
    if not test.num_tasks_per_node and not test.num_cpus_per_task:
        test.num_tasks_per_node = test.default_num_cpus_per_node
        test.num_cpus_per_task = 1

    # num_tasks_per_node is not set, but num_cpus_per_node is
    elif not test.num_tasks_per_node:
        test.num_tasks_per_node = int(test.default_num_cpus_per_node / test.num_cpus_per_task)

    # num_cpus_per_node is not set, but num_tasks_per_node is
    elif not test.num_cpus_per_task:
        test.num_cpus_per_task = int(test.default_num_cpus_per_node / test.num_tasks_per_node)

    else:
        pass  # both num_tasks_per_node and num_cpus_per_node are already set


def _assign_one_task_per_gpu(test: rfm.RegressionTest):
    """
    Sets num_tasks_per_node, num_cpus_per_task, and num_gpus_per_node, unless specified with:
    --setvar num_tasks_per_node=<x> and/or
    --setvar num_cpus_per_task=<y> and/or
    --setvar num_gpus_per_node=<z>.

    Variables:
    - max_avail_gpus_per_node: maximum available number of GPUs per node
    - default_num_gpus_per_node: default number of GPUs per node as defined in the test
    (e.g. by earlier hooks like set_tag_scale)

    Default resources requested:
    - num_gpus_per_node = default_num_gpus_per_node
    - num_tasks_per_node = num_gpus_per_node
    - num_cpus_per_task = default_num_cpus_per_node / num_tasks_per_node

    If num_tasks_per_node is set, set num_gpus_per_node equal to either num_tasks_per_node or default_num_gpus_per_node
    (whichever is smallest), unless num_gpus_per_node is also set.
    """
    max_avail_gpus_per_node = utils.get_max_avail_gpus_per_node(test)

    # Check if the default number of gpus per node is already defined in the test
    # (e.g. by earlier hooks like set_tag_scale).
    # If so, check if it doesn't exceed the maximum available.
    # If not, set default_num_gpus_per_node based on the maximum available gpus and node_part
    if test.default_num_gpus_per_node:
        # may skip if not enough GPUs
        test.skip_if(
            test.default_num_gpus_per_node > max_avail_gpus_per_node,
            f'Requested GPUs per node ({test.default_num_gpus_per_node}) is higher than max available'
            f' ({max_avail_gpus_per_node}) in current partition ({test.current_partition.name}).'
        )
    else:
        # no default set yet, so setting one
        test.default_num_gpus_per_node = math.ceil(max_avail_gpus_per_node / test.node_part)

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
            int(test.max_avail_cpus_per_node / max_avail_gpus_per_node)
        )

    test.num_tasks = test.num_nodes * test.num_tasks_per_node


def filter_valid_systems_by_device_type(test: rfm.RegressionTest, required_device_type: str):
    """
    Filter valid_systems by required device type and by whether the module supports CUDA,
    unless valid_systems is specified with --setvar valid_systems=<comma-separated-list>.
    """
    if not test.valid_systems:
        is_cuda_module = utils.is_cuda_required_module(test.module_name)
        valid_systems = ''

        if is_cuda_module and required_device_type == DEVICES['GPU']:
            # CUDA modules and when using a GPU require partitions with 'gpu' feature
            valid_systems = f'+{FEATURES["GPU"]}'

        elif required_device_type == DEVICES['CPU']:
            # Using the CPU requires partitions with 'cpu' feature
            # Note: making 'cpu' an explicit feature allows e.g. skipping CPU-based tests on GPU partitions
            valid_systems = f'+{FEATURES["CPU"]}'

        elif not is_cuda_module and required_device_type == DEVICES['GPU']:
            # Invalid combination: a module without GPU support cannot use a GPU
            valid_systems = ''

        if valid_systems:
            test.valid_systems = [valid_systems]


def set_modules(test: rfm.RegressionTest):
    """
    Skip current test if module_name is not among a list of modules,
    specified with --setvar modules=<comma-separated-list>.
    """
    if test.modules and test.module_name not in test.modules:
        test.valid_systems = []

    test.modules = [test.module_name]


def set_tag_scale(test: rfm.RegressionTest):
    """Set resources and tag based on current scale"""
    scale = test.scale
    test.num_nodes = SCALES[scale]['num_nodes']
    test.default_num_cpus_per_node = SCALES[scale].get('num_cpus_per_node')
    test.default_num_gpus_per_node = SCALES[scale].get('num_gpus_per_node')
    test.node_part = SCALES[scale].get('node_part')
    test.tags.add(scale)


def check_custom_executable_opts(test: rfm.RegressionTest, num_default: int = 0):
    """"
    Check if custom executable options were added with --setvar executable_opts=<x>.
    """
    # normalize options
    test.executable_opts = shlex.split(' '.join(test.executable_opts))
    test.has_custom_executable_opts = False
    if len(test.executable_opts) > num_default:
        test.has_custom_executable_opts = True
