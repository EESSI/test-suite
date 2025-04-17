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
from hpctestlib.sciapps.metalwalls.benchmarks import MetalWallsCheck
from reframe.core.builtins import run_after
from reframe.core.parameters import TestParam as parameter

from eessi.testsuite import hooks
from eessi.testsuite.constants import COMPUTE_UNITS, DEVICE_TYPES, SCALES, TAGS
from eessi.testsuite.utils import find_modules, log


@rfm.simple_test
class EESSI_MetalWalls_MW(MetalWallsCheck):
    """MetalWalls benchmark tests.

    `MetalWalls <https://gitlab.com/ampere2/metalwalls>`__ """

    scale = parameter(SCALES.keys())

    valid_systems = ['*']
    valid_prog_environs = ['default']
    time_limit = '60m'
    # input files are downloaded
    readonly_files = ['']

    module_name = parameter(find_modules('MetalWalls'))
    # For now, MetalWalls is being build for CPU targets only
    # compute_device = parameter([DEVICE_TYPES.CPU, DEVICE_TYPES.GPU])
    compute_device = parameter([DEVICE_TYPES.CPU])

    @run_after('init')
    def run_after_init(self):
        """Hooks to run after the init phase"""

        # Filter on which scales are supported by the partitions defined in the ReFrame configuration
        hooks.filter_supported_scales(self)

        # Make sure that GPU tests run in partitions that support running on a GPU,
        # and that CPU-only tests run in partitions that support running CPU-only.
        # Also support setting valid_systems on the cmd line.
        hooks.filter_valid_systems_by_device_type(self, required_device_type=self.compute_device)

        # Support selecting modules on the cmd line.
        hooks.set_modules(self)

        # Support selecting scales on the cmd line via tags.
        hooks.set_tag_scale(self)

    @run_after('init')
    def set_tag_ci(self):
        """Set tag CI on smallest benchmark, so it can be selected on the cmd line via --tag CI"""
        if self.benchmark_info[0] == 'hackathonGPU/benchmark':
            self.tags.add(TAGS.CI)
            log(f'tags set to {self.tags}')

    @run_after('init')
    def set_increased_walltime(self):
        """Increase the amount of time for the largest benchmark, when running with few cores."""
        # List of benchmarks that require more time to run
        large_benchmarks = ['hackathonGPU/benchmark2']
        if self.num_tasks <= 4 and self.benchmark_info[0] in large_benchmarks:
            self.time_limit = '120m'

    @run_after('setup')
    def run_after_setup(self):
        """Hooks to run after the setup phase"""

        # Calculate default requested resources based on the scale:
        # 1 task per CPU for CPU-only tests, 1 task per GPU for GPU tests.
        # Also support setting the resources on the cmd line.
        if self.compute_device == DEVICE_TYPES.GPU:
            hooks.assign_tasks_per_compute_unit(test=self, compute_unit=COMPUTE_UNITS.GPU)
        else:
            hooks.assign_tasks_per_compute_unit(test=self, compute_unit=COMPUTE_UNITS.CPU)

    @run_after('setup')
    def set_binding(self):
        """Set binding to compact to improve performance reproducibility."""
        hooks.set_compact_process_binding(self)

    @run_after('setup')
    def request_mem(self):
        """Request memory per node based on the benchmark."""
        mem_per_task = 0.4
        if self.benchmark_info[0] == 'hackathonGPU/benchmark5':
            mem_per_task = 1.2
        memory_required = self.num_tasks_per_node * mem_per_task + 2
        hooks.req_memory_per_node(test=self, app_mem_req=memory_required * 1024)

    @run_after('setup')
    def skip_max_corecnt(self):
        """Skip tests if number of tasks per node exceeds maximum core count."""
        max_task_cnt = 256
        bench_name = self.benchmark_info[0]
        self.skip_if(
            self.num_tasks > max_task_cnt,
            f'Number of tasks {self.num_tasks} exceeds maximum task count {max_task_cnt} for {bench_name}'
        )

    @run_after('setup')
    def set_omp_num_threads(self):
        """
        Set number of OpenMP threads via OMP_NUM_THREADS.
        Set default number of OpenMP threads equal to number of CPUs per task.
        """
        hooks.set_omp_num_threads(self)
