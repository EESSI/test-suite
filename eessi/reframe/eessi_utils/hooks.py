"""
Hooks for adding tags, filtering and setting job resources in ReFrame tests
"""
import shlex

import reframe as rfm
from eessi_utils import utils

PROCESSOR_INFO_MISSING = '''
This test requires the number of CPUs to be known for the partition it runs on.
Check that processor information is either autodetected
(see https://reframe-hpc.readthedocs.io/en/stable/configure.html#proc-autodetection),
or manually set in the ReFrame configuration file
(see https://reframe-hpc.readthedocs.io/en/stable/config_reference.html#processor-info).
'''


def assign_one_task_per_compute_unit(test: rfm.RegressionTest, compute_unit: str) -> rfm.RegressionTest:
    """
    Assign one task per compute unit ('gpu' or 'cpu').
    Automatically sets num_tasks, num_tasks_per_node, num_cpus_per_task, and num_gpus_per_node,
    based on the current partition's num_cpus, num_gpus_per_node and test.num_nodes.
    For GPU tests, one task per GPU is set, and num_cpus_per_task is based on the ratio of CPU-cores/GPUs.
    For CPU tests, one task per CPU is set, and num_cpus_per_task is set to 1.
    Total task count is determined based on the number of nodes to be used in the test.
    Behaviour of this function is (usually) sensible for MPI tests.
    """

    test.max_cpus_per_node = test.current_partition.processor.num_cpus
    if test.max_cpus_per_node is None:
        raise AttributeError(PROCESSOR_INFO_MISSING)

    if compute_unit == 'gpu':
        assign_one_task_per_gpu(test)
    elif compute_unit == 'cpu':
        assign_one_task_per_cpu(test)
    else:
        raise ValueError(f'compute unit {compute_unit} is currently not supported')


def assign_one_task_per_cpu(test: rfm.RegressionTest) -> rfm.RegressionTest:
    """
    Sets num_tasks_per_node and num_cpus_per_task such that it will run one task per core,
    unless specified with --setvar num_tasks_per_node=<x> and/or --setvar num_cpus_per_task=<y>.
    """
    max_cpus_per_node = test.max_cpus_per_node
    num_tasks_per_node = test.num_tasks_per_node
    num_cpus_per_task = test.num_cpus_per_task

    if not num_tasks_per_node:
        if not num_cpus_per_task:
            num_tasks_per_node = max_cpus_per_node
        else:
            num_tasks_per_node = int(max_cpus_per_node / num_cpus_per_task)

    if not num_cpus_per_task:
        num_cpus_per_task = int(max_cpus_per_node / num_tasks_per_node)

    test.num_tasks_per_node = num_tasks_per_node
    test.num_tasks = test.num_nodes * test.num_tasks_per_node
    test.num_cpus_per_task = num_cpus_per_task


def assign_one_task_per_gpu(test: rfm.RegressionTest) -> rfm.RegressionTest:
    """
    Sets num_tasks_per_node, num_cpus_per_task, and num_gpus_per_node, unless specified with:
    --setvar num_tasks_per_node=<x> and/or
    --setvar num_cpus_per_task=<y> and/or
    --setvar num_gpus_per_node=<z>.

    Default values:
    num_gpus_per_node = total nb of GPUs per node available in this partition
    num_tasks_per_node = num_gpus_per_node
    num_cpus_per_task = total nb of CPUs per GPU available in this partition, divided by num_tasks_per_node

    If num_tasks_per_node is set, set num_gpus_per_node equal to either num_tasks_per_node,
    or nb of GPUs per node available in this partition (whatever is smallest).
    """
    max_gpus_per_node = utils.get_num_gpus_per_node(test)
    max_cpus_per_node = test.max_cpus_per_node
    num_tasks_per_node = test.num_tasks_per_node
    num_gpus_per_node = test.num_gpus_per_node

    if not num_tasks_per_node:
        if not num_gpus_per_node:
            num_gpus_per_node = max_gpus_per_node
        num_tasks_per_node = num_gpus_per_node

    elif not num_gpus_per_node:
        num_gpus_per_node = min(num_tasks_per_node, max_gpus_per_node)

    if not test.num_cpus_per_task:
        test.num_cpus_per_task = int(
            (max_cpus_per_node * num_gpus_per_node) / (num_tasks_per_node * max_gpus_per_node)
        )

    test.num_gpus_per_node = num_gpus_per_node
    test.num_tasks_per_node = num_tasks_per_node
    test.num_tasks = test.num_nodes * num_tasks_per_node


def filter_tests_by_device_type(test: rfm.RegressionTest, required_device_type: str):
    """
    Filter tests by required device type and whether the module supports CUDA,
    unless valid_systems is specified with --setvar valid_systems=<comma-separated-list>.
    """
    if not test.valid_systems:
        is_cuda_module = utils.is_cuda_required_module(test.module_name)
        valid_systems = ''

        if is_cuda_module and required_device_type == 'gpu':
            # CUDA modules and when using a GPU require partitions with 'gpu' feature
            valid_systems = '+gpu'

        elif required_device_type == 'cpu':
            # Using the CPU requires partitions with 'cpu' feature
            # Note: making 'cpu' an explicit feature allows e.g. skipping CPU-based tests on GPU partitions
            valid_systems = '+cpu'

        elif not is_cuda_module and required_device_type == 'gpu':
            # Invalid combination: a module without GPU support cannot use a GPU
            valid_systems = ''

        if valid_systems:
            test.valid_systems = [valid_systems]


def set_modules(test: rfm.RegressionTest):
    """
    Skip this test if module_name is not among a list of modules,
    specified with --setvar modules=<comma-separated-list>.
    """
    if test.modules and test.module_name not in test.modules:
        test.valid_systems = []

    test.modules = [test.module_name]


def set_tag_scale(test: rfm.RegressionTest):
    """Add tag based on scale used"""
    scale_tag, test.num_nodes = test.scale
    test.tags.add(scale_tag)


def check_custom_executable_opts(test: rfm.RegressionTest, num_default: int = 0):
    """"
    Check if custom executable options were added with --setvar executable_opts=<x>.
    """
    # normalize options
    test.executable_opts = shlex.split(' '.join(test.executable_opts))
    test.has_custom_executable_opts = False
    if len(test.executable_opts) > num_default:
        test.has_custom_executable_opts = True
