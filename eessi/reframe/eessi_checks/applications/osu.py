"""
This module tests the binary 'osu' in available modules containing substring 'OSU-Micro-Benchmarks'.
The basic application class is taken from the hpctestlib to which extra features are added.
"""

import reframe as rfm

from hpctestlib.microbenchmarks.mpi.osu import osu_benchmark
from eessi_utils import hooks, utils
from eessi_utils.constants import SCALES, TAGS


@rfm.simple_test
class OSU_EESSI(osu_benchmark):
    scale = parameter(SCALES.keys())
    valid_prog_environs = ['default']
    valid_systems = []
    time_limit = '30m'
    module_name = parameter(utils.find_modules('OSU-Mirco-Benchmarks'))

    @run_after('init')
    def run_after_init(self):
        """hooks to run after init phase"""
        hooks.filter_tests_by_device_type(
                self,
                required_device_type=self.device_buffers)
        hooks.set_modules(self)
        hooks.set_tag_scale(self)

    @run_after('init')
    def set_tag_ci(self):
        if self.benchmark_info[0] =='mpi.pt2pt.osu_latency':
            self.tags.add('CI')

# TODO: Set slurm options per rack, switch.
# TODO: Override already existing message sizes if specified.
    @run_after('init')
    def set_executable_opts(self):
        """
        Add extra executable_opts or ones that override default ones such as
        message sizes, unless specified via --setvar executable_opts=<x>
        """
        bench, bench_metric = self.benchmark_info
        if bench.startswith('mpi.pt2pt'):
            num_default = 8  # normalized number of executable opts added by parent class (osu_benchmark)
        elif self.device_buffers != 'cpu':
            num_default = 10
        else:
            num_default = 6
        hooks.check_custom_executable_opts(self, num_default=num_default)
