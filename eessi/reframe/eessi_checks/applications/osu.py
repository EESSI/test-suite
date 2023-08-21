"""
This module tests the binary 'osu' in available modules containing substring 'OSU-Micro-Benchmarks'.
The basic application class is taken from the hpctestlib to which extra features are added.
"""

import os
import reframe as rfm
import reframe.utility.sanity as sn

from hpctestlib.microbenchmarks.mpi.osu import osu_benchmark

from eessi_utils import hooks, utils
from eessi_utils.constants import SCALES, TAGS, DEVICES

def my_filtering_function():
    """
    Filtering function for filtering scales for the OSU test
    """
    scale_filtered = SCALES
    for key in list(SCALES):
        if(key == '1_core' or key == '4_cores' or
           SCALES.get(key).get('num_nodes') > 2):
            scale_filtered.pop(key)
        elif('node_part' in SCALES.get(key)):
            if(SCALES.get(key).get('node_part') > 1):
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
# This is required by the base class and needs to at least have a default value
# which means that this needs to be assigned or re-assigned in the class based
# on other options
#    osu_benchmark.num_tasks = 2
    @run_after('init')
    def run_after_init(self):
        """hooks to run after init phase"""
        hooks.filter_valid_systems_by_device_type(
               self,
               required_device_type=self.device_buffers)
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
        if('gpu' in self.current_partition.features):
            if(SCALES.get(self.scale).get('num_nodes') == 1):
                self.num_gpus_per_node = 1
            else:
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
