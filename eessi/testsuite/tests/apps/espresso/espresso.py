"""
This module tests Espresso in available modules containing substring 'ESPResSo' which is different from Quantum
Espresso. Tests included:
- P3M benchmark - Ionic crystals
    - Weak scaling
    - Strong scaling Weak and strong scaling are options that are needed to be provided to the script and the system is
      either scaled based on number of cores or kept constant.
"""

import reframe as rfm
import reframe.utility.sanity as sn

from reframe.core.builtins import deferrable, parameter, performance_function, run_after, sanity_function
from reframe.utility import reframe

from eessi.testsuite.constants import DEVICE_TYPES, SCALES, COMPUTE_UNITS
from eessi.testsuite.eessi_mixin import EESSI_Mixin
from eessi.testsuite.utils import find_modules, log


def filter_scales():
    """
    Filtering function for filtering scales for P3M test and the LJ test.
    This is currently required because the 16 node test takes way too long and always fails due to time limit.
    Once a solution to mesh tuning algorithm is found, where we can specify the mesh sizes for a particular scale,
    this function can be removed.
    """
    return [
        k for (k, v) in SCALES.items()
        if v['num_nodes'] != 16
    ]


class EESSI_ESPRESSO_base(rfm.RunOnlyRegressionTest):
    module_name = parameter(find_modules('^ESPResSo$'))
    device_type = DEVICE_TYPES.CPU
    compute_unit = COMPUTE_UNITS.CPU
    time_limit = '300m'

    @run_after('init')
    def set_ci_tag(self):
        """ Setting tests under CI tag. """
        # this test runs longer at larger scales due to mesh tuning
        # thus, we only set CI tag on scales < 2 nodes to limit execution time
        # TODO: revisit this for more recent versions of ESPResSo
        # see also: https://github.com/EESSI/test-suite/issues/154
        if SCALES[self.scale]['num_nodes'] < 2:
            self.bench_name_ci = self.bench_name

    @sanity_function
    def assert_sanity(self):
        '''Check all sanity criteria'''
        return sn.all([
            self.assert_completion(),
            self.assert_convergence(),
        ])

    @performance_function('s/step')
    def perf(self):
        return sn.extractsingle(r'^Performance:\s+(?P<perf>\S+)', self.stdout, 'perf', float)


@rfm.simple_test
class EESSI_ESPRESSO_P3M_IONIC_CRYSTALS(EESSI_ESPRESSO_base, EESSI_Mixin):
    scale = parameter(filter_scales())

    executable = 'python3 madelung.py'
    sourcesdir = 'src/p3m'
    readonly_files = ['madelung.py']
    bench_name = 'ionic_crystals_p3m'

    default_weak_scaling_system_size = 6

    def required_mem_per_node(self):
        return (self.num_tasks_per_node * 0.9) * 1024

    @run_after('init')
    def set_executable_opts(self):
        """Set executable opts based on device_type parameter"""
        # Weak scaling (Gustafson's law: constant work per core): size scales with number of cores
        self.executable_opts += ['--size', str(self.default_weak_scaling_system_size), '--weak-scaling']
        log(f'executable_opts set to {self.executable_opts}')

    @deferrable
    def assert_completion(self):
        '''Check completion'''
        cao = sn.extractsingle(r'^resulting parameters:.*cao: (?P<cao>\S+),', self.stdout, 'cao', int)
        return (sn.assert_found(r'^Algorithm executed.', self.stdout) and cao)

    @deferrable
    def assert_convergence(self):
        '''Check convergence'''
        check_string = sn.assert_found(r'Final convergence met with tolerances:', self.stdout)
        energy = sn.extractsingle(r'^\s+energy:\s+(?P<energy>\S+)', self.stdout, 'energy', float)
        return (check_string and (energy != 0.0))


@rfm.simple_test
class EESSI_ESPRESSO_LJ_PARTICLES(EESSI_ESPRESSO_base, EESSI_Mixin):
    scale = parameter(filter_scales())

    executable = 'python3 lj.py'
    sourcesdir = 'src/lj'
    readonly_files = ['lj.py']
    bench_name = 'particles_lj'

    def required_mem_per_node(self):
        "LJ requires 200 MB per core"
        return (self.num_tasks_per_node * 0.3) * 1024

    @deferrable
    def assert_completion(self):
        '''Check completion'''
        return sn.assert_found(r'^Algorithm executed.', self.stdout)

    @deferrable
    def assert_convergence(self):
        '''Check convergence'''
        check_string = sn.assert_found(r'Final convergence met with relative tolerances:', self.stdout)
        energy = sn.extractsingle(r'^\s+sim_energy:\s+(?P<energy>\S+)', self.stdout, 'energy', float)
        return (check_string and (energy != 0.0))
