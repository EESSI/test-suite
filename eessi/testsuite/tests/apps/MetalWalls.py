"""
This module tests the binary 'mw' in available modules containing substring 'MetalWalls'.
Test input files are defined in MetalWalls's repo under hackathonGPU/benchmark*,
see https://github.com/reframe-hpc/reframe/blob/develop/hpctestlib/sciapps/qespresso/benchmarks.py

ReFrame terminology:

"pipeline stages":
https://reframe-hpc.readthedocs.io/en/stable/regression_test_api.html#pipeline-hooks

"test parameter": a list of values, which will generate different test variants.
https://reframe-hpc.readthedocs.io/en/stable/regression_test_api.html#reframe.core.builtins.parameter

"test variant": a version of a test with a specific value for each test parameter
https://reframe-hpc.readthedocs.io/en/stable/regression_test_api.html#test-variants

"concrete test cases": all test combinations that will actually run:
- test variants
- valid system:partition+programming environment combinations
https://reframe-hpc.readthedocs.io/en/stable/tutorial_deps.html#listing-dependencies

Tests can be filtered by name, tag, programming environment, system, partition, or maintainer,
see https://reframe-hpc.readthedocs.io/en/stable/manpage.html#test-filtering

Hooks acting on all possible test combinations (before filtering) are called after the 'init' stage.
Hooks acting on concrete test cases (after filtering) are called after the 'setup' stage.

See also https://reframe-hpc.readthedocs.io/en/stable/pipeline.html
"""
import reframe as rfm
from reframe.core.builtins import run_after
from reframe.core.parameters import TestParam as parameter

from eessi.testsuite.eessi_mixin import EESSI_Mixin
from eessi.testsuite.constants import COMPUTE_UNITS, DEVICE_TYPES
from eessi.testsuite.hpctestlib.sciapps.metalwalls.benchmarks import MetalWallsCheck
from eessi.testsuite.utils import find_modules


@rfm.simple_test
class EESSI_MetalWalls_MW(MetalWallsCheck, EESSI_Mixin):
    """MetalWalls benchmark tests.

    `MetalWalls <https://gitlab.com/ampere2/metalwalls>`__ """

    # input files are downloaded
    readonly_files = ['']

    module_info = parameter(find_modules('MetalWalls'))
    # For now, MetalWalls is being build for CPU targets only
    # compute_device = parameter([DEVICE_TYPES.CPU, DEVICE_TYPES.GPU])
    device_type = parameter([DEVICE_TYPES.CPU])

    def required_mem_per_node(self):
        mem_per_task = 0.4
        if self.benchmark_info[0] == 'hackathonGPU/benchmark5':
            mem_per_task = 1.2
        return self.num_tasks_per_node * mem_per_task + 2

    @run_after('init')
    def run_after_init(self):
        """Hooks to run after the init phase"""
        # Launch 1 task per CPU (when run on CPUs) or 1 task per GPU (when run on GPUs)
        if self.device_type == DEVICE_TYPES.CPU:
            self.compute_unit = COMPUTE_UNITS.CPU
        elif self.device_type == DEVICE_TYPES.GPU:
            self.compute_unit = COMPUTE_UNITS.GPU
        else:
            raise NotImplementedError(
                f"Compute unit {self.compute_unit} was not implement for test {self.name}"
            )

    @run_after('init')
    def set_tag_ci(self):
        """Set tag CI on smallest benchmark, so it can be selected on the cmd line via --tag CI"""
        if self.benchmark_info[0] == 'hackathonGPU/benchmark':
            self.is_ci_test = True

    @run_after('init')
    def set_increased_walltime(self):
        """Increase the amount of time for the largest benchmark, when running with few cores."""
        # List of benchmarks that require more time to run
        large_benchmarks = ['hackathonGPU/benchmark2']
        if self.num_tasks <= 4 and self.benchmark_info[0] in large_benchmarks:
            self.time_limit = '120m'

    @run_after('setup')
    def skip_max_corecnt(self):
        """Skip tests if number of tasks per node exceeds maximum core count."""
        max_task_cnt = 256
        bench_name = self.benchmark_info[0]
        self.skip_if(
            self.num_tasks > max_task_cnt,
            f'Number of tasks {self.num_tasks} exceeds maximum task count {max_task_cnt} for {bench_name}'
        )
