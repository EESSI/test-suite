"""
This module tests the binary 'gmx_mpi' in available modules containing substring 'GROMACS'.
Test input files are taken from https://www.hecbiosim.ac.uk/access-hpc/benchmarks,
as defined in the ReFrame test library,
see https://github.com/reframe-hpc/reframe/blob/develop/hpctestlib/sciapps/gromacs/benchmarks.py

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
from reframe.core.builtins import parameter, run_after  # added only to make the linter happy

from hpctestlib.sciapps.gromacs.benchmarks import gromacs_check

from eessi.testsuite import hooks
from eessi.testsuite.constants import SCALES, TAGS
from eessi.testsuite.utils import find_modules, log


@rfm.simple_test
class EESSI_GROMACS(gromacs_check):
    scale = parameter(SCALES.keys())
    valid_prog_environs = ['default']
    valid_systems = ['*']
    time_limit = '30m'
    module_name = parameter(find_modules('GROMACS'))

    @run_after('init')
    def run_after_init(self):
        """Hooks to run after the init phase"""

        # Filter on which scales are supported by the partitions defined in the ReFrame configuration
        hooks.filter_supported_scales(self)

        # Make sure that GPU tests run in partitions that support running on a GPU,
        # and that CPU-only tests run in partitions that support running CPU-only.
        # Also support setting valid_systems on the cmd line.
        hooks.filter_valid_systems_by_device_type(self, required_device_type=self.nb_impl)

        # Support selecting modules on the cmd line.
        hooks.set_modules(self)

        # Support selecting scales on the cmd line via tags.
        hooks.set_tag_scale(self)

    @run_after('init')
    def set_tag_ci(self):
        """Set tag CI on smallest benchmark, so it can be selected on the cmd line via --tag CI"""
        # Crambin input is smallest input (20K atoms), cfr. https://www.hecbiosim.ac.uk/access-hpc/benchmarks
        if self.benchmark_info[0] == 'HECBioSim/Crambin':
            self.tags.add(TAGS['CI'])
            log(f'tags set to {self.tags}')

    @run_after('setup')
    def set_executable_opts(self):
        """
        Add extra executable_opts, unless specified via --setvar executable_opts=<x>
        Set default executable_opts and support setting custom executable_opts on the cmd line.
        """

        num_default = 4  # normalized number of executable opts added by parent class (gromacs_check)
        hooks.check_custom_executable_opts(self, num_default=num_default)
        if not self.has_custom_executable_opts:
            self.executable_opts += ['-dlb', 'yes', '-npme', '-1']
            log(f'executable_opts set to {self.executable_opts}')

    @run_after('setup')
    def run_after_setup(self):
        """Hooks to run after the setup phase"""

        # Calculate default requested resources based on the scale:
        # 1 task per CPU for CPU-only tests, 1 task per GPU for GPU tests.
        # Also support setting the resources on the cmd line.
        hooks.assign_tasks_per_compute_unit(test=self, compute_unit=self.nb_impl)

    @run_after('setup')
    def set_omp_num_threads(self):
        """
        Set number of OpenMP threads.
        Set both OMP_NUM_THREADS and -ntomp explicitly to avoid conflicting values.
        Set default number of OpenMP threads equal to number of CPUs per task.
        Also support setting OpenMP threads on the cmd line via custom executable option '-ntomp'.
        """

        if '-ntomp' in self.executable_opts:
            omp_num_threads = self.executable_opts[self.executable_opts.index('-ntomp') + 1]
        else:
            omp_num_threads = self.num_cpus_per_task
            self.executable_opts += ['-ntomp', str(omp_num_threads)]
            log(f'executable_opts set to {self.executable_opts}')

        self.env_vars['OMP_NUM_THREADS'] = omp_num_threads
        log(f'env_vars set to {self.env_vars}')

    @run_after('setup')
    def set_binding_policy(self):
        """
        Default process binding may depend on the launcher used. We've seen some variable performance.
        Better set it explicitely to make sure process migration cannot cause such variations.
        """
        hooks.set_compact_process_binding(self)
