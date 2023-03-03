import reframe as rfm
import eessi_utils.utils as utils

processor_info_missing = '''This test requires the number of CPUs to be known for the partition it runs on.
Check that processor information is either autodetected
(see https://reframe-hpc.readthedocs.io/en/stable/configure.html#proc-autodetection),
or manually set in the ReFrame configuration file
(see https://reframe-hpc.readthedocs.io/en/stable/config_reference.html?highlight=processor%20info#processor-info).
'''


def skip_cpu_test_on_gpu_nodes(test: rfm.RegressionTest):
    '''Skip test if GPUs are present, but no CUDA is required'''
    skip = (utils.is_gpu_cresent(test) and not utils.is_cuda_required(test))
    if skip:
        test.skip_if(True, f"GPU is present on this partition ({test.current_partition.name}), skipping CPU-based test")


def skip_gpu_test_on_cpu_nodes(test: rfm.RegressionTest):
    '''Skip test if CUDA is required, but no GPU is present'''
    skip = (utils.is_cuda_required(test) and not utils.is_gpu_present(test))
    if skip:
        test.skip_if(
            True,
            f"Test requires CUDA, but no GPU is present in this partition ({test.current_partition.name}). "
            "Skipping test..."
        )


def assign_one_task_per_feature(test: rfm.RegressionTest, feature) -> rfm.RegressionTest:
    """assign on task per feature ('gpu' or 'cpu')"""
    test.max_cpus_per_node = test.current_partition.processor.num_cpus
    if test.max_cpus_per_node is None:
        raise AttributeError(processor_info_missing)

    if feature == 'gpu':
        assign_one_task_per_gpu(test)
    else:
        assign_one_task_per_cpu(test)


def assign_one_task_per_cpu(test: rfm.RegressionTest) -> rfm.RegressionTest:
    """
    Sets num_tasks_per_node and num_cpus_per_task such that it will run one task per core,
    unless specified with --setvar num_tasks_per_node=<x> and/or --setvar num_cpus_per_task=<y>
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
    Sets num_tasks_per_node, num_cpus_per_task, and num_gpus_per_node,
        unless specified with
            --setvar num_tasks_per_node=<x> and/or
            --setvar num_cpus_per_task=<y> and/or
            --setvar num_gpus_per_node=<z>
    - default num_gpus_per_node = total nb of GPUs per node available in this partition
    - default num_tasks_per_node = num_gpus_per_node
    - default num_cpus_per_task = total nb of CPUs per GPU available in this partition, divided by num_tasks_per_node
    - if num_tasks_per_node is set, set num_gpus_per_node equal to either num_tasks_per_node or nb of GPUs per node
        available in this partition (whatever is smallest).
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


def auto_assign_num_tasks_MPI(test: rfm.RegressionTest, num_nodes: int) -> rfm.RegressionTest:
    '''
    Automatically sets num_tasks, tasks_per_node and cpus_per_task based on the current partitions num_cpus, number of
    GPUs and test.num_nodes. For GPU tests, one task per GPU is set, and num_cpus_per_task is based on the ratio of CPU
    cores/GPUs. For CPU tests, one task per CPU is set, and num_cpus_per_task is set to 1. Total task count is
    determined based on the number of nodes to be used in the test. Behaviour of this function is (usually) sensible for
    pure MPI tests.
    '''
    if utils.is_cuda_required(test):
        assign_one_task_per_gpu(test, num_nodes)
    else:
        assign_one_task_per_cpu(test, num_nodes)
