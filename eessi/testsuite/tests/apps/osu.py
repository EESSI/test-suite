"""
This module tests the binary 'osu' in available modules containing substring 'OSU-Micro-Benchmarks'. The basic
application class is taken from the hpctestlib to which extra features are added.

Note: OSU-Micro-Benchmarks CUDA module binaries must be linked to stubs so that it at the least finds libcuda.so.1 on
non-GPU nodes. Otherwise those tests will FAIL.
"""
import reframe as rfm
from reframe.core.builtins import parameter, run_after  # added only to make the linter happy
from reframe.utility import reframe

from hpctestlib.microbenchmarks.mpi.osu import osu_benchmark

from eessi.testsuite import hooks, utils
from eessi.testsuite.constants import *
from eessi.testsuite.utils import find_modules, log


def filter_scales_pt2pt():
    """
    Filtering function for filtering scales for the pt2pt OSU test
    """
    return [
        k for (k, v) in SCALES.items()
        if v['num_nodes'] * v.get('num_cpus_per_node', 0) == 2
        or (v['num_nodes'] == 2 and v.get('node_part', 0) == 1)
        or (v['num_nodes'] == 1 and v.get('node_part', 0) == 1)
    ]


def filter_scales_coll():
    """
    Filtering function for filtering scales for collective the OSU test
    """
    return [
        k for (k, v) in SCALES.items()
        if (v['num_nodes'] * v.get('num_cpus_per_node', 1) > 1)
        or (v.get('node_part', 0) > 0)
    ]


@rfm.simple_test
class EESSI_OSU_Micro_Benchmarks_pt2pt(osu_benchmark):
    ''' Run-only OSU test '''
    scale = parameter(filter_scales_pt2pt())
    valid_prog_environs = ['default']
    valid_systems = ['*']
    time_limit = '30m'
    module_name = parameter(find_modules('OSU-Micro-Benchmarks'))
    # Device type for non-cuda OSU-Micro-Benchmarks should run on hosts of both node types. To do this the default
    # device type is set to GPU.
    device_type = parameter([DEVICE_TYPES[CPU], DEVICE_TYPES[GPU]])
    # unset num_tasks_per_node from the hpctestlib.
    num_tasks_per_node = None

    # Set num_warmup_iters to 5 to reduce execution time, especially on slower interconnects
    num_warmup_iters = 5
    # Set num_iters to 10 to reduce execution time, especially on slower interconnects
    num_iters = 10

    @run_after('init')
    def filter_scales_2gpus(self):
        """Filter out scales with < 2 GPUs if running on GPUs"""
        if (
            self.device_type == DEVICE_TYPES[GPU]
            and SCALES[self.scale]['num_nodes'] == 1
            and SCALES[self.scale].get('num_gpus_per_node', 2) < 2
        ):
            self.valid_systems = [INVALID_SYSTEM]
            log(f'valid_systems set to {self.valid_systems} for scale {self.scale} and device_type {self.device_type}')

    @run_after('init')
    def filter_benchmark_pt2pt(self):
        """ Filter out all non-mpi.pt2pt benchmarks """
        if not self.benchmark_info[0].startswith('mpi.pt2pt'):
            self.valid_systems = [INVALID_SYSTEM]

    @run_after('init')
    def run_after_init(self):
        """hooks to run after init phase"""

        # Filter on which scales are supported by the partitions defined in the ReFrame configuration
        hooks.filter_supported_scales(self)

        hooks.filter_valid_systems_by_device_type(self, required_device_type=self.device_type)

        hooks.set_modules(self)

        # Set scales as tags
        hooks.set_tag_scale(self)

    @run_after('init')
    def set_device_buffers(self):
        """
        device_buffers is inherited from the hpctestlib class and adds options to the launcher
        commands in a @run_before('setup') hook if not equal to 'cpu'.
        Therefore, we must set device_buffers *before* the @run_before('setup') hooks.
        """
        if self.device_type == DEVICE_TYPES[GPU]:
            self.device_buffers = 'cuda'

        else:
            # If the device_type is CPU then device_buffers should always be CPU.
            self.device_buffers = 'cpu'

    @run_after('init')
    def set_tag_ci(self):
        """ Setting tests under CI tag. """
        if (self.benchmark_info[0] in ['mpi.pt2pt.osu_latency', 'mpi.pt2pt.osu_bw']):
            self.tags.add('CI')
            log(f'tags set to {self.tags}')

        if (self.benchmark_info[0] == 'mpi.pt2pt.osu_bw'):
            self.tags.add('osu_bw')

        if (self.benchmark_info[0] == 'mpi.pt2pt.osu_latency'):
            self.tags.add('osu_latency')

    @run_after('init')
    def set_mem(self):
        """ Setting an extra job option of memory. This test has only 4 possibilities: 1_node, 2_nodes, 2_cores and
        1cpn_2nodes. This is implemented for all cases including full node cases. The requested memory may seem large
        and the test requires at least 4.5 GB per core at the minimum for the full test when run with validation (-c
        option for osu_bw or osu_latency). We run till message size 8 (-m 8) which significantly reduces memory
        requirement."""
        self.extra_resources = {'memory': {'size': '12GB'}}

    @run_after('setup')
    def adjust_executable_opts(self):
        """The option "D D" is only meant for Devices if and not for CPU tests.
        This option is added by hpctestlib in a @run_before('setup') to all pt2pt tests which is not required.
        Therefore we must override it *after* the 'setup' phase
        """
        if self.device_type == DEVICE_TYPES[CPU]:
            self.executable_opts = [ele for ele in self.executable_opts if ele != 'D']

    @run_after('setup')
    def set_num_tasks_per_node(self):
        """ Setting number of tasks per node and cpus per task in this function. This function sets num_cpus_per_task
        for 1 node and 2 node options where the request is for full nodes."""
        if SCALES.get(self.scale).get('num_nodes') == 1:
            hooks.assign_tasks_per_compute_unit(self, COMPUTE_UNIT[NODE], 2)
        else:
            hooks.assign_tasks_per_compute_unit(self, COMPUTE_UNIT[NODE])

    @run_after('setup')
    def set_num_gpus_per_node(self):
        """
        Set number of GPUs per node for GPU-to-GPU tests
        """
        if self.device_type == DEVICE_TYPES[GPU]:
            # Skip single-node tests with less than 2 GPU devices in the node
            self.skip_if(
                SCALES[self.scale]['num_nodes'] == 1 and self.default_num_gpus_per_node < 2,
                "There are < 2 GPU devices present in the node."
                f" Skipping tests with device_type={DEVICE_TYPES[GPU]} involving < 2 GPUs and 1 node."
            )
            if not self.num_gpus_per_node:
                self.num_gpus_per_node = self.default_num_gpus_per_node
                log(f'num_gpus_per_node set to {self.num_gpus_per_node} for partition {self.current_partition.name}')


@rfm.simple_test
class EESSI_OSU_Micro_Benchmarks_coll(osu_benchmark):
    ''' Run-only OSU test '''
    scale = parameter(filter_scales_coll())
    valid_prog_environs = ['default']
    valid_systems = ['*']
    time_limit = '30m'
    module_name = parameter(utils.find_modules('OSU-Micro-Benchmarks'))
    # Device type for non-cuda OSU-Micro-Benchmarks should run on hosts of both node types. To do this the default
    # device type is set to GPU.
    device_type = parameter([DEVICE_TYPES[CPU], DEVICE_TYPES[GPU]])
    # Unset num_tasks_per_node from hpctestlib
    num_tasks_per_node = None

    # Set num_warmup_iters to 5 to reduce execution time, especially on slower interconnects
    num_warmup_iters = 5
    # Set num_iters to 10 to reduce execution time, especially on slower interconnects
    num_iters = 10

    @run_after('init')
    def run_after_init(self):
        """hooks to run after init phase"""
        # Note: device_buffers variable is inherited from the hpctestlib class and adds options to the launcher
        # commands based on what device is set.
        self.device_buffers = 'cpu'
        # Filter on which scales are supported by the partitions defined in the ReFrame configuration
        hooks.filter_supported_scales(self)
        hooks.filter_valid_systems_by_device_type(self, required_device_type=self.device_type)
        is_cuda_module = utils.is_cuda_required_module(self.module_name)
        if is_cuda_module and self.device_type == DEVICE_TYPES[GPU]:
            self.device_buffers = 'cuda'

        # If the device_type is CPU then device buffer should always be CPU.
        if self.device_type == DEVICE_TYPES[CPU]:
            self.device_buffers = 'cpu'
        # This part of the code removes the collective communication calls out of the run list since this test is only
        # meant for collective.
        if not self.benchmark_info[0].startswith('mpi.collective'):
            self.valid_systems = []
        hooks.set_modules(self)

    @run_after('init')
    def set_tag_ci(self):
        if (self.benchmark_info[0] == 'mpi.collective.osu_allreduce'
           or self.benchmark_info[0] == 'mpi.collective.osu_alltoall'):
            self.tags.add('CI')
        if (self.benchmark_info[0] == 'mpi.collective.osu_allreduce'):
            self.tags.add('osu_allreduce')
        if (self.benchmark_info[0] == 'mpi.collective.osu_alltoall'):
            self.tags.add('osu_alltoall')

    @run_after('init')
    def set_mem(self):
        """ Setting an extra job option of memory. The alltoall operation takes maximum memory of 0.1 GB per core for a
        message size of 8 and almost 0.5 GB per core for the maximum message size the test allows. But we limit the
        message sizes to 8 and for a safety net we take 64 GB assuming dense nodes works for all the tests and node
        types."""
        self.extra_resources = {'memory': {'size': '64GB'}}

    @run_after('init')
    def set_num_tasks(self):
        hooks.set_tag_scale(self)

    @run_after('setup')
    def set_num_tasks_per_node(self):
        """ Setting number of tasks per node, cpus per task and gpus per node in this function. This function sets
        num_cpus_per_task for 1 node and 2 node options where the request is for full nodes."""
        max_avail_cpus_per_node = self.current_partition.processor.num_cpus
        if self.device_buffers == 'cpu':
            # Setting num_tasks and num_tasks_per_node for the CPU tests
            if SCALES.get(self.scale).get('num_cpus_per_node', 0):
                hooks.assign_tasks_per_compute_unit(self, COMPUTE_UNIT[NODE],
                                                    self.default_num_cpus_per_node)
            elif SCALES.get(self.scale).get('node_part', 0):
                pass_num_per = int(max_avail_cpus_per_node / SCALES.get(self.scale).get('node_part', 0))
                if pass_num_per > 1:
                    hooks.assign_tasks_per_compute_unit(self, COMPUTE_UNIT[NODE], pass_num_per)
                else:
                    self.skip(msg="Too few cores available for a collective operation.")

            if FEATURES[GPU] in self.current_partition.features:
                max_avail_gpus_per_node = utils.get_max_avail_gpus_per_node(self)
                # Setting number of GPU for a cpu test on a GPU node.
                if SCALES.get(self.scale).get('num_nodes') == 1:
                    self.num_gpus_per_node = 1
                else:
                    self.num_gpus_per_node = max_avail_gpus_per_node
        elif self.device_buffers == 'cuda':
            max_avail_gpus_per_node = utils.get_max_avail_gpus_per_node(self)
            # Setting num_tasks and num_tasks_per_node for the GPU tests
            if max_avail_gpus_per_node == 1 and SCALES.get(self.scale).get('num_nodes') == 1:
                self.skip(msg="There is only 1 device in the node. Skipping collective tests involving only 1 node.")
            else:
                if SCALES.get(self.scale).get('num_gpus_per_node', 0) * SCALES.get(self.scale).get('num_nodes', 0) > 1:
                    hooks.assign_tasks_per_compute_unit(self, COMPUTE_UNIT.get(GPU, FEATURES[GPU]))
                elif SCALES.get(self.scale).get('node_part', 0):
                    pass_num_per = int(max_avail_gpus_per_node / SCALES.get(self.scale).get('node_part', 0))
                    if pass_num_per > 1:
                        hooks.assign_tasks_per_compute_unit(self, COMPUTE_UNIT.get(GPU, FEATURES[GPU]))
                    else:
                        self.skip(msg="Total GPUs (max_avail_gpus_per_node / node_part) is 1 less.")
                else:
                    self.skip(msg="Total GPUs (num_nodes * num_gpus_per_node) = 1")
