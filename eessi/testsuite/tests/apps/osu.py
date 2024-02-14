"""
This module tests the binary 'osu' in available modules containing substring 'OSU-Micro-Benchmarks'. The basic
application class is taken from the hpctestlib to which extra features are added.

Note: OSU-Micro-Benchmarks CUDA module binaries must be linked to stubs so that it at the least finds libcuda.so.1 on
non-GPU nodes. Otherwise those tests will FAIL.
"""
import reframe as rfm
from hpctestlib.microbenchmarks.mpi.osu import osu_benchmark
from reframe.utility import reframe

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
    # Note: device_buffers variable is inherited from the hpctestlib class and adds options to the launcher
    # commands based on what device is set.
    device_buffers = 'cpu'

    @run_after('init')
    def run_after_init(self):
        """hooks to run after init phase"""
        # Filter on which scales are supported by the partitions defined in the ReFrame configuration
        hooks.filter_supported_scales(self)

        hooks.filter_valid_systems_by_device_type(self, required_device_type=self.device_type)
        is_cuda_module = utils.is_cuda_required_module(self.module_name)
        # This part of the hook is meant to be for the OSU cpu tests. This is required since the non CUDA module should
        # be able to run in the GPU partition as well. This is specific for this test and not covered by the function
        # above.
        if is_cuda_module and self.device_type == DEVICE_TYPES[GPU]:
            # Sets to cuda as device buffer only if the module is compiled with CUDA.
            self.device_buffers = 'cuda'

        # If the device_type is CPU then device buffer should always be CPU.
        if self.device_type == DEVICE_TYPES[CPU]:
            self.device_buffers = 'cpu'

        # This part of the code removes the collective communication calls out of the run list since this test is only
        # meant for pt2pt.
        if not self.benchmark_info[0].startswith('mpi.pt2pt'):
            self.valid_systems = []
        hooks.set_modules(self)

    @run_after('setup')
    def adjust_executable_opts(self):
        """The option "D D" is only meant for Devices if and not for CPU tests. This option is added by hpctestlib to
        all pt2pt tests which is not required."""
        if(self.device_type == DEVICE_TYPES[CPU]):
            self.executable_opts = [ele for ele in self.executable_opts if ele != 'D']

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
        1_cpn_2_nodes. This is implemented for all cases including full node cases. The requested memory may seem large
        and the test requires at least 4.5 GB per core at the minimum for the full test when run with validation (-c
        option for osu_bw or osu_latency). We run till message size 8 (-m 8) which significantly reduces memory
        requirement."""
        self.extra_resources = {'memory': {'size': '12GB'}}

    @run_after('init')
    def set_num_tasks(self):
        """ Setting scales as tags. """
        hooks.set_tag_scale(self)

    @run_after('setup')
    def set_environment(self):
        """ Setting environment variable for CUDA module tests that run on pure cpu nodes."""
        is_cuda_module = utils.is_cuda_required_module(self.module_name)
        if (is_cuda_module and self.device_type == DEVICE_TYPES[CPU] and
                (not FEATURES[GPU] in self.current_partition.features)):
            self.env_vars = {'LD_LIBRARY_PATH': '$EBROOTCUDA/stubs/lib64:$LD_LIBRARY_PATH'}

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
        This test does not require gpus and is for host to host within GPU nodes. But some systems do require a GPU
        allocation for to perform any activity in the GPU nodes.
        """
        if self.device_type == DEVICE_TYPES[GPU]:
            # Skip scales with only 1 GPU device and single-node tests with only 1 GPU device in the node
            self.skip_if(
                SCALES[self.scale]['num_nodes'] == 1 and self.default_num_gpus_per_node == 1,
                f"There is only 1 GPU device for scale={self.scale} or present in the node."
                f" Skipping tests with device_type={DEVICE_TYPES[GPU]} involving only 1 GPU."
            )
            if not self.num_gpus_per_node:
                self.num_gpus_per_node = self.default_num_gpus_per_node
                log(f'num_gpus_per_node set to {self.num_gpus_per_node} for partition {self.current_partition.name}')


@rfm.simple_test
class EESSI_OSU_Micro_Benchmarks_coll(osu_benchmark):
    ''' Run-only OSU test '''
    scale = parameter(filter_scales_coll())
    valid_prog_environs = ['default']
    valid_systems = []
    time_limit = '30m'
    module_name = parameter(utils.find_modules('OSU-Micro-Benchmarks'))
    # Device type for non-cuda OSU-Micro-Benchmarks should run on hosts of both node types. To do this the default
    # device type is set to GPU.
    device_type = parameter([DEVICE_TYPES[CPU], DEVICE_TYPES[GPU]])
    # Unset num_tasks_per_node from hpctestlib
    num_tasks_per_node = None


    @run_after('init')
    def run_after_init(self):
        """hooks to run after init phase"""
        hooks.filter_valid_systems_by_device_type( self, required_device_type=self.device_type)
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
        if (self.benchmark_info[0] == 'mpi.collective.osu_allreduce' or
           self.benchmark_info[0] == 'mpi.collective.osu_alltoall'):
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
    def set_environment(self):
        """ Setting environment variable for CUDA module tests that run on pure cpu nodes."""
        is_cuda_module = utils.is_cuda_required_module(self.module_name)
        if (is_cuda_module and self.device_type == DEVICE_TYPES[CPU] and
                (not FEATURES[GPU] in self.current_partition.features)):
            self.env_vars = {'LD_LIBRARY_PATH': '$EBROOTCUDA/stubs/lib64:$LD_LIBRARY_PATH'}

    @run_after('setup')
    def set_num_tasks_per_node(self):
        """ Setting number of tasks per node, cpus per task and gpus per node in this function. This function sets
        num_cpus_per_task for 1 node and 2 node options where the request is for full nodes."""
        max_avail_cpus_per_node = self.current_partition.processor.num_cpus
        if(self.device_buffers == 'cpu'):
            # Setting num_tasks and num_tasks_per_node for the CPU tests
            if(SCALES.get(self.scale).get('num_cpus_per_node', 0)):
                hooks.assign_tasks_per_compute_unit(self, COMPUTE_UNIT[NODE],
                                                    self.default_num_cpus_per_node)
            elif(SCALES.get(self.scale).get('node_part', 0)):
                pass_num_per = int(max_avail_cpus_per_node / SCALES.get(self.scale).get('node_part', 0))
                if(pass_num_per > 1):
                    hooks.assign_tasks_per_compute_unit(self, COMPUTE_UNIT[NODE], pass_num_per)
                else:
                    self.skip(msg="Too few cores available for a collective operation.")

            if(FEATURES[GPU] in self.current_partition.features):
                max_avail_gpus_per_node = utils.get_max_avail_gpus_per_node(self)
                # Setting number of GPU for a cpu test on a GPU node.
                if(SCALES.get(self.scale).get('num_nodes') == 1):
                    self.num_gpus_per_node = 1
                else:
                    self.num_gpus_per_node = max_avail_gpus_per_node
        elif(self.device_buffers == 'cuda'):
            max_avail_gpus_per_node = utils.get_max_avail_gpus_per_node(self)
            # Setting num_tasks and num_tasks_per_node for the GPU tests
            if(max_avail_gpus_per_node == 1 and
                    SCALES.get(self.scale).get('num_nodes') == 1):
                self.skip(msg="There is only 1 device within the node. Skipping collective tests involving only 1 node.")
            else:
                if(SCALES.get(self.scale).get('num_gpus_per_node', 0) * SCALES.get(self.scale).get('num_nodes', 0) > 1):
                    hooks.assign_tasks_per_compute_unit(self, COMPUTE_UNIT.get(GPU, FEATURES[GPU]))
                elif(SCALES.get(self.scale).get('node_part', 0)):
                    pass_num_per = int(max_avail_gpus_per_node / SCALES.get(self.scale).get('node_part', 0))
                    if(pass_num_per > 1):
                        hooks.assign_tasks_per_compute_unit(self, COMPUTE_UNIT.get(GPU, FEATURES[GPU]))
                    else:
                        self.skip(msg="Total GPUs (max_avail_gpus_per_node / node_part) is 1 less.")
                else:
                    self.skip(msg="Total GPUs (num_nodes * num_gpus_per_node) = 1")
