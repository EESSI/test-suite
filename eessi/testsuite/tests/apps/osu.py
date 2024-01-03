"""
This module tests the binary 'osu' in available modules containing substring
'OSU-Micro-Benchmarks'. The basic application class is taken from the
hpctestlib to which extra features are added.

Note: OSU-Micro-Benchmarks CUDA module binaries must be linked to stubs so that
it at the least finds libcuda.so.1 on non-GPU nodes. Otherwise those tests will
FAIL.
"""
import reframe as rfm
from hpctestlib.microbenchmarks.mpi.osu import osu_benchmark

from eessi.testsuite import hooks, utils
from eessi.testsuite.constants import *
from eessi.testsuite.utils import find_modules, log


def my_filtering_function():
    """
    Filtering function for filtering scales for the pt2pt OSU test
    """
    return [
        k for (k, v) in SCALES.items()
        if v['num_nodes'] * v.get('num_cpus_per_node', 0) == 2
        or (v['num_nodes'] == 2 and v.get('node_part', 0) == 1)
        or (v['num_nodes'] == 1 and v.get('node_part', 0) == 1)
    ]


def my_filtering_function_coll():
    """
    Filtering function for filtering scales for collective the OSU test
    """
    return [
        k for (k, v) in SCALES.items()
        if (v['num_nodes'] * v.get('num_cpus_per_node', 1) > 1)
        or (v.get('node_part', 0) > 0)
    ]


@rfm.simple_test
class osu_pt_2_pt(osu_benchmark):
    ''' Run-only OSU test '''
    scale = parameter(my_filtering_function())
    valid_prog_environs = ['default']
    valid_systems = []
    time_limit = '30m'
    module_name = parameter(find_modules('OSU-Micro-Benchmarks'))
    # Device type for non-cuda OSU-Micro-Benchmarks should run on hosts of both
    # node types. To do this the default device type is set to GPU.
    device_type = parameter([DEVICE_TYPES[CPU], DEVICE_TYPES[GPU]])
    # unset num_tasks_per_node from the hpctestlib.
    num_tasks_per_node = None

    @run_after('init')
    def run_after_init(self):
        """hooks to run after init phase"""
        hooks.filter_valid_systems_by_device_type(
               self,
               required_device_type=self.device_type)
        is_cuda_module = utils.is_cuda_required_module(self.module_name)
        # This part of the hook is meant to be for the OSU cpu tests. This is
        # required since the non CUDA module should be able to run in the GPU
        # partition as well. This is specific for this test and not covered by
        # the function above.
        # if not is_cuda_module and self.device_type == DEVICE_TYPES[GPU]:
        #     self.valid_systems = [f'+{FEATURES[GPU]} %{GPU_VENDOR}={GPU_VENDORS[NVIDIA]}']
        #     self.device_buffers = 'cpu'
        # elif is_cuda_module and self.device_type == DEVICE_TYPES[GPU]:
        #     # Currently the device buffer is hard coded to be cuda. More
        #     # options need to be introduced based on vendor and device type.
        #     self.device_buffers = 'cuda'
        if is_cuda_module and self.device_type == DEVICE_TYPES[GPU]:
            # Currently the device buffer is hard coded to be cuda. More
            # options need to be introduced based on vendor and device type.
            self.device_buffers = 'cuda'
        elif is_cuda_module and self.device_type == DEVICE_TYPES[CPU]:
            # This if condition had to be added since the CUDA compiled osu
            # tests do not run on cpu partitions. The binaries need
            # libcuda.so.1 during runtime which can only be found in a
            # partition with CUDA drivers.
            self.valid_systems = [f'+{FEATURES[CPU]} +{FEATURES[GPU]} %{GPU_VENDOR}={GPU_VENDORS[NVIDIA]}']

        # If the device_type is CPU then device buffer should always be CPU.
        if self.device_type == DEVICE_TYPES[CPU]:
            self.device_buffers = 'cpu'

        # This part of the code removes the collective communication calls out
        # of the run list since this test is only meant for pt2pt.
        if not self.benchmark_info[0].startswith('mpi.pt2pt'):
            self.valid_systems = []
        hooks.set_modules(self)

    @run_after('init')
    def set_tag_ci(self):
        """ Setting tests under CI tag. """
        if (self.benchmark_info[0] in ['mpi.pt2pt.osu_latency',
                                       'mpi.pt2pt.osu_bw']):
            self.tags.add('CI')
            log(f'tags set to {self.tags}')

        if (self.benchmark_info[0] == 'mpi.pt2pt.osu_bw'):
            self.tags.add('osu_bw')

        if (self.benchmark_info[0] == 'mpi.pt2pt.osu_latency'):
            self.tags.add('osu_latency')

    @run_after('init')
    def set_mem(self):
        """ Setting an extra job option of memory. This test has only 4
        possibilities: 1_node, 2_nodes, 2_cores and 1_cpn_2_nodes. Only the
        last 2 require the memory to be set. """
        is_cuda_module = utils.is_cuda_required_module(self.module_name)
        if(SCALES.get(self.scale).get('node_part', 0) == 0):
            self.extra_resources = {'memory': {'size': '32GB'}}

    @run_after('init')
    def set_num_tasks(self):
        """ Setting scales as tags. """
        hooks.set_tag_scale(self)

    @run_after('setup')
    def set_num_tasks_per_node(self):
        """ Setting number of tasks per node and cpus per task in this function.
        This function sets num_cpus_per_task for 1 node and 2 node options where
        the request is for full nodes."""
        if(SCALES.get(self.scale).get('num_nodes') == 1):
            hooks.assign_tasks_per_compute_unit(self,
                                                   COMPUTE_UNIT.get(NODE,
                                                                    'node'), 2)
        else:
            hooks.assign_tasks_per_compute_unit(self, COMPUTE_UNIT.get(NODE,
                                                                       'node'))

    @run_after('setup')
    def set_num_gpus_per_node(self):
        """
        This test does not require gpus and is for host to host within GPU
        nodes. But some systems do require a GPU allocation for to perform any
        activity in the GPU nodes.
        """
        if('gpu' in self.current_partition.features and
           not utils.is_cuda_required_module(self.module_name)):
            if(SCALES.get(self.scale).get('num_nodes') == 1):
                self.num_gpus_per_node = 1
            else:
                # The devices section is sort of hard coded. This needs to be
                # amended for a more heterogeneous system with more than one
                # device type.

                # Even for 1_cpn_2_nodes, the gpus requested are for the full
                # nodes. On Snellius 1 GPU card cannot be reserved on 2
                # different nodes which can be different on different systems.
                self.num_gpus_per_node = \
                    self.current_partition.devices[0].num_devices
        elif('gpu' in self.current_partition.features and
             utils.is_cuda_required_module(self.module_name)):
            max_avail_gpus_per_node = \
                    self.current_partition.devices[0].num_devices
            if(SCALES.get(self.scale).get('num_nodes') == 1):
                # Skip the single node test if there is only 1 device in the 
                # node.
                if(max_avail_gpus_per_node == 1):
                    self.skip(msg="There is only 1 device within the node. Skipping tests involving only 1 node.")
                else:
                    self.num_gpus_per_node = 2
            else:
                # The devices section is sort of hard coded. This needs to be
                # amended for a more heterogeneous system with more than one
                # device type.

                # Note these settings are for 1_cpn_2_nodes. In that case we
                # want to test for only 1 GPU per node since we have not
                # requested for full nodes.
                if(SCALES.get(self.scale).get('num_gpus_per_node', 0)):
                    self.num_gpus_per_node = \
                        SCALES.get(self.scale).get('num_gpus_per_node', 0)
                else:
                    self.num_gpus_per_node = \
                        self.current_partition.devices[0].num_devices


@rfm.simple_test
class osu_coll(osu_benchmark):
    ''' Run-only OSU test '''
    scale = parameter(my_filtering_function_coll())
    #scale = parameter(SCALES.keys())
    valid_prog_environs = ['default']
    valid_systems = []
    time_limit = '30m'
    module_name = parameter(utils.find_modules('OSU-Micro-Benchmarks'))
    # Device type for non-cuda OSU-Micro-Benchmarks should run on hosts of both
    # node types. To do this the default device type is set to GPU.
    device_type = DEVICE_TYPES['GPU']


    @run_after('init')
    def run_after_init(self):
        """hooks to run after init phase"""
        hooks.filter_valid_systems_by_device_type(
               self,
               required_device_type=self.device_type)
        is_cuda_module = utils.is_cuda_required_module(self.module_name)
        # This part of the hook is meant to be for the OSU cpu tests.
        if not is_cuda_module and self.device_type == DEVICE_TYPES['GPU']:
            self.valid_systems = ['*']
            self.device_buffers = 'cpu'
        elif is_cuda_module and self.device_type == DEVICE_TYPES['GPU']:
            # Currently the device buffer is hard coded to be cuda. More
            # options need to be introduced based on vendor and device type.
            self.device_buffers = 'cuda'
        # This part of the code removes the collective communication calls out
        # of the run list since this test is only meant for collective.
        if not self.benchmark_info[0].startswith('mpi.collective'):
            self.valid_systems = []
        hooks.set_modules(self)


    @run_after('init')
    def set_tag_ci(self):
        if (self.benchmark_info[0] == 'mpi.collective.osu_allreduce' or
           self.benchmark_info[0] == 'mpi.collective.osu_alltoall'):
            self.tags.add('CI')


    @run_after('init')
    def set_num_tasks(self):
        hooks.set_tag_scale(self)


    @run_after('setup')
    def run_after_setup(self):
        """Hooks to run after the setup phase"""
        # Calculate default requested resources based on the scale:
        # 1 task per CPU for CPU-only tests, 1 task per GPU for GPU tests.
        # Also support setting the resources on the cmd line.
        # CPU settings for cpu based tests
        # Setting num_tasks
        max_avail_cpus_per_node = self.current_partition.processor.num_cpus
        self.num_tasks = max_avail_cpus_per_node * SCALES.get(self.scale).get('num_nodes')
        if (SCALES.get(self.scale).get('node_part') is not None):
            self.num_tasks = int(self.num_tasks/SCALES.get(self.scale).get('node_part'))
        elif (SCALES.get(self.scale).get('num_cpus_per_node') is not None):
            self.num_tasks = SCALES.get(self.scale).get('num_cpus_per_node')

        # Setting num_tasks_per_node
        if (SCALES.get(self.scale).get('num_nodes') == 1):
            self.num_tasks_per_node = self.num_tasks
        else:
            self.num_tasks_per_node = max_avail_cpus_per_node

        # The above setting is for all CPU tests including the ones occurring
        # in the GPU nodes. This section is specifically for GPU tests the
        # num_tasks should be equal to num gpus per node.
        if('gpu' in self.current_partition.features and
           utils.is_cuda_required_module(self.module_name)):
            max_avail_gpus_per_node = \
                    self.current_partition.devices[0].num_devices
            if(max_avail_gpus_per_node == 1 and
                    SCALES.get(self.scale).get('num_nodes') == 1):
                self.skip(msg="There is only 1 device within the node. Skipping collective tests involving only 1 node.")
            else:
                if (SCALES.get(self.scale).get('num_nodes') == 1):
                    if (SCALES.get(self.scale).get('node_part') is not None):
                        self.num_tasks = int(max_avail_gpus_per_node /
                                             SCALES.get(self.scale).get('node_part'))
                        self.skip_if(self.num_tasks <= 1,
                                     msg="There are not enough GPU cards to be divided")
                    elif (SCALES.get(self.scale).get('num_cpus_per_node') is not None):
                        if(SCALES.get(self.scale).get('num_cpus_per_node') >=
                           max_avail_gpus_per_node):
                            self.num_tasks = self.num_tasks_per_node =\
                                    max_avail_gpus_per_node
                        else:
                            self.num_tasks = \
                                    SCALES.get(self.scale).get('num_cpus_per_node')
                            self.num_tasks_per_node = self.num_tasks

                else:
                    self.num_tasks = SCALES.get(self.scale).get('num_nodes') *\
                           max_avail_gpus_per_node
                    self.num_tasks_per_node = max_avail_gpus_per_node

    @run_after('setup')
    def set_num_gpus_per_node(self):
        """
        This test does not require gpus and is for host to host within GPU
        nodes. But some systems do require a GPU allocation for to perform any
        activity in the GPU nodes.
        """
        if('gpu' in self.current_partition.features and
           not utils.is_cuda_required_module(self.module_name)):
            if(SCALES.get(self.scale).get('num_nodes') == 1):
                self.num_gpus_per_node = 1
            else:
                # The devices section is sort of hard coded. This needs to be
                # amended for a more heterogeneous system with more than one
                # device type.
                self.num_gpus_per_node = \
                    self.current_partition.devices[0].num_devices
        elif('gpu' in self.current_partition.features and
             utils.is_cuda_required_module(self.module_name)):
            max_avail_gpus_per_node = \
                    self.current_partition.devices[0].num_devices
            if(max_avail_gpus_per_node == 1 and
                    SCALES.get(self.scale).get('num_nodes') == 1):
                self.skip(msg="There is only 1 device within the node. Skipping collective tests involving only 1 node.")
            else:
                if (SCALES.get(self.scale).get('num_nodes') == 1):
                    if (SCALES.get(self.scale).get('node_part') is not None):
                        self.num_gpus_per_node = int(max_avail_gpus_per_node /
                                                     SCALES.get(self.scale).get('node_part'))
                        self.skip_if(self.num_gpus_per_node <= 1,
                                     msg="There are not enough GPU cards to be divided")
                    elif (SCALES.get(self.scale).get('num_cpus_per_node') is not None):
                        if(SCALES.get(self.scale).get('num_cpus_per_node') >=
                           max_avail_gpus_per_node):
                            self.num_gpus_per_node =\
                                    max_avail_gpus_per_node
                        else:
                            self.num_gpus_per_node = \
                                    SCALES.get(self.scale).get('num_cpus_per_node')

                else:
                    self.num_gpus_per_node = max_avail_gpus_per_node
