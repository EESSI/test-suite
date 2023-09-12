"""
This module tests the binary 'osu' in available modules containing substring 'OSU-Micro-Benchmarks'.
The basic application class is taken from the hpctestlib to which extra features are added.
"""

import os
import reframe as rfm
from reframe.core.meta import parameters
import reframe.utility.sanity as sn

from hpctestlib.microbenchmarks.mpi.osu import osu_benchmark

from eessi.testsuite import hooks, utils
from eessi.testsuite.constants import SCALES, TAGS, DEVICE_TYPES

def my_filtering_function():
    """
    Filtering function for filtering scales for the pt2pt OSU test
    """
    scale_filtered = SCALES.copy()
    for key in list(SCALES):
        if(key == '1_core' or key == '4_cores' or
           SCALES.get(key).get('num_nodes') > 2):
            scale_filtered.pop(key)
        elif('node_part' in SCALES.get(key)):
            if(SCALES.get(key).get('node_part') > 1):
                scale_filtered.pop(key)
    return scale_filtered


def my_filtering_function_coll():
    """
    Filtering function for filtering scales for collective the OSU test
    """
    scale_filtered = SCALES.copy()
    for key in list(SCALES):
        if(key == '1_core'):
            scale_filtered.pop(key)
    return scale_filtered


@rfm.simple_test
class osu_pt_2_pt(osu_benchmark):
    ''' Run-only OSU test '''
    scale = parameter(my_filtering_function())
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
        # of the run list since this test is only meant for pt2pt.
        if not self.benchmark_info[0].startswith('mpi.pt2pt'):
            self.valid_systems = []
        hooks.set_modules(self)

    @run_after('init')
    def set_tag_ci(self):
        if (self.benchmark_info[0] == 'mpi.pt2pt.osu_latency' or
           self.benchmark_info[0] == 'mpi.pt2pt.osu_bw'):
            self.tags.add('CI')


    @run_after('init')
    def set_num_tasks_per_node(self):
        if(SCALES.get(self.scale).get('num_nodes') == 1):
            self.num_tasks_per_node = 2


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
            if(SCALES.get(self.scale).get('num_nodes') == 1):
                self.num_gpus_per_node = 2
            else:
                # The devices section is sort of hard coded. This needs to be
                # amended for a more heterogeneous system with more than one
                # device type.
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
            self.num_gpus_per_node = \
                    self.current_partition.devices[0].num_devices


#    @run_after('setup')
#    def set_executable_opts(self):
#        """
#        Add extra executable_opts or ones that override default ones such as
#        message sizes, unless specified via --setvar executable_opts=<x>
#        """
#        bench, bench_metric = self.benchmark_info
#        if bench.startswith('mpi.pt2pt'):
#            num_default = 8  # normalized number of executable opts added by parent class (osu_benchmark)
#        elif self.device_buffers != 'cpu':
#            num_default = 10
#        else:
#            num_default = 6
#        hooks.check_custom_executable_opts(self, num_default=num_default)

#    @run_after('setup')
#    def run_after_setup(self):
#        """Hooks to run after the setup phase"""
#
#        # Calculate default requested resources based on the scale:
#        # 1 task per CPU for CPU-only tests, 1 task per GPU for GPU tests.
#        # Also support setting the resources on the cmd line.
#        hooks.assign_one_task_per_compute_unit(test=self, compute_unit=self.nb_impl)

# TODO: Set slurm options per rack, switch.
# TODO: Override already existing message sizes if specified.
