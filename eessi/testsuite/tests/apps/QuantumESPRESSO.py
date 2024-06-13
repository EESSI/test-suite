"""
This module tests the binary 'pw.x' in available modules containing substring 'QuantumESPRESSO'.
Test input files are defined in the ReFrame test library,
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
from hpctestlib.sciapps.qespresso.benchmarks import QEspressoPWCheck
from reframe.core.builtins import (  # added only to make the linter happy
    parameter, run_after)

from eessi.testsuite import hooks
from eessi.testsuite.constants import (COMPUTE_UNIT, CPU, DEVICE_TYPES, GPU,
                                       SCALES, TAGS)
from eessi.testsuite.utils import find_modules, log


@rfm.simple_test
class EESSI_QuantumESPRESSO_PW(QEspressoPWCheck):
    scale = parameter(SCALES.keys())
    valid_prog_environs = ['default']
    valid_systems = ['*']
    time_limit = '30m'
    module_name = parameter(find_modules('QuantumESPRESSO'))
    # For now, QE is being build for CPU targets only
    # compute_device = parameter([DEVICE_TYPES[CPU], DEVICE_TYPES[GPU]])
    compute_device = parameter([DEVICE_TYPES[CPU], ])

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
        min_ecut = min(QEspressoPWCheck.ecut.values)
        min_nbnd = min(QEspressoPWCheck.nbnd.values)
        if self.ecut == min_ecut and self.nbnd == min_nbnd:
            self.tags.add(TAGS['CI'])
            log(f'tags set to {self.tags}')

    @run_after('init')
    def set_increased_walltime(self):
        """Increase the amount of time for the largest benchmark, so it can complete successfully."""
        max_ecut = max(QEspressoPWCheck.ecut.values)
        max_nbnd = max(QEspressoPWCheck.nbnd.values)
        if self.ecut == max_ecut and self.nbnd == max_nbnd:
            self.time_limit = '60m'

    @run_after('setup')
    def run_after_setup(self):
        """Hooks to run after the setup phase"""

        # Calculate default requested resources based on the scale:
        # 1 task per CPU for CPU-only tests, 1 task per GPU for GPU tests.
        # Also support setting the resources on the cmd line.
        if self.compute_device == DEVICE_TYPES[GPU]:
            hooks.assign_tasks_per_compute_unit(test=self, compute_unit=COMPUTE_UNIT[GPU])
        else:
            hooks.assign_tasks_per_compute_unit(test=self, compute_unit=COMPUTE_UNIT[CPU])

    @run_after('setup')
    def request_mem(self):
        memory_required = self.num_tasks_per_node * 0.9 + 4
        hooks.req_memory_per_node(test=self, app_mem_req=memory_required * 1024)

    @run_after('setup')
    def set_omp_num_threads(self):
        """
        Set number of OpenMP threads via OMP_NUM_THREADS.
        Set default number of OpenMP threads equal to number of CPUs per task.
        """

        self.env_vars['OMP_NUM_THREADS'] = self.num_cpus_per_task
        log(f'env_vars set to {self.env_vars}')
