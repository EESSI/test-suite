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

from reframe.core.builtins import parameter, run_after  # added only to make the linter happy
from reframe.utility import reframe

from eessi.testsuite import hooks, utils
from eessi.testsuite.constants import *
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


class EESSI_ESPRESSO(rfm.RunOnlyRegressionTest):
    valid_prog_environs = ['default']
    valid_systems = ['*']
    # Need to check if QuantumESPRESSO also gets listed.
    module_name = parameter(find_modules('ESPResSo'))
    # device type is parameterized for an impending CUDA ESPResSo module.
    device_type = parameter([DEVICE_TYPES[CPU]])

    @run_after('init')
    def run_after_init(self):
        """hooks to run after init phase"""
        # Filter on which scales are supported by the partitions defined in the ReFrame configuration
        hooks.filter_supported_scales(self)

        hooks.filter_valid_systems_by_device_type(self, required_device_type=self.device_type)

        hooks.set_modules(self)

        # Set scales as tags
        hooks.set_tag_scale(self)

    @run_after('setup')
    def set_num_tasks_per_node(self):
        """ Setting number of tasks per node and cpus per task in this function. This function sets num_cpus_per_task
        for 1 node and 2 node options where the request is for full nodes."""
        hooks.assign_tasks_per_compute_unit(self, COMPUTE_UNIT[CPU])

    @run_after('setup')
    def set_mem(self):
        """ Setting an extra job option of memory. Here the assumption made is that HPC systems will contain at
        least 1 GB per core of memory."""
        mem_required_per_node = self.num_tasks_per_node * 0.9
        hooks.req_memory_per_node(test=self, app_mem_req=mem_required_per_node * 1024)

    @run_after('setup')
    def set_binding(self):
        hooks.set_compact_process_binding(self)

    @deferrable
    def assert_completion(self):
        '''Check completion'''
        if self.benchmark_info[0] in ['mpi.ionic_crystals.p3m']:
            cao = sn.extractsingle(r'^resulting parameters:.*cao: (?P<cao>\S+),', self.stdout, 'cao', int)
            return (sn.assert_found(r'^Algorithm executed.', self.stdout) and cao)
        elif self.benchmark_info[0] in ['mpi.particles.lj']:
            return (sn.assert_found(r'^Algorithm executed.', self.stdout))

    @deferrable
    def assert_convergence(self):
        '''Check convergence'''
        check_string = False
        energy = 0.0
        if self.benchmark_info[0] in ['mpi.ionic_crystals.p3m']:
            check_string = sn.assert_found(r'Final convergence met with tolerances:', self.stdout)
            energy = sn.extractsingle(r'^\s+energy:\s+(?P<energy>\S+)', self.stdout, 'energy', float)
        elif self.benchmark_info[0] in ['mpi.particles.lj']:
            check_string = sn.assert_found(r'Final convergence met with relative tolerances:', self.stdout)
            energy = sn.extractsingle(r'^\s+sim_energy:\s+(?P<energy>\S+)', self.stdout, 'energy', float)
        return (check_string and (energy != 0.0))

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
class EESSI_ESPRESSO_P3M_IONIC_CRYSTALS(EESSI_ESPRESSO):
    scale = parameter(filter_scales())
    time_limit = '300m'

    executable = 'python3 madelung.py'

    default_weak_scaling_system_size = 6

    @run_after('init')
    def set_tag_ci(self):
        """ Setting tests under CI tag. """
        if SCALES[self.scale]['num_nodes'] < 2:
            self.tags.add('CI')
            log(f'tags set to {self.tags}')

        self.tags.add('ionic_crystals_p3m')

    @run_after('init')
    def set_executable_opts(self):
        """Set executable opts based on device_type parameter"""
        num_default = 0  # If this test already has executable opts, they must have come from the command line
        hooks.check_custom_executable_opts(self, num_default=num_default)
        # By default we run weak scaling since the strong scaling sizes need to change based on max node size and a
        # corresponding min node size has to be chozen.
        self.executable_opts += ['--size', str(self.default_weak_scaling_system_size), '--weak-scaling']
        utils.log(f'executable_opts set to {self.executable_opts}')

    @run_after('setup')
    def set_mem(self):
        """ Setting an extra job option of memory. Here the assumption made is that HPC systems will contain at
        least 1 GB per core of memory."""
        mem_required_per_node = self.num_tasks_per_node * 0.9
        hooks.req_memory_per_node(test=self, app_mem_req=mem_required_per_node * 1024)

    @deferrable
    def assert_completion(self):
        '''Check completion'''
        cao = sn.extractsingle(r'^resulting parameters:.*cao: (?P<cao>\S+),', self.stdout, 'cao', int)
        return (sn.assert_found(r'^Algorithm executed.', self.stdout) and cao)

    @deferrable
    def assert_convergence(self):
        '''Check convergence'''
        check_string = False
        energy = 0.0
        check_string = sn.assert_found(r'Final convergence met with tolerances:', self.stdout)
        energy = sn.extractsingle(r'^\s+energy:\s+(?P<energy>\S+)', self.stdout, 'energy', float)
        return (check_string and (energy != 0.0))


@rfm.simple_test
class EESSI_ESPRESSO_LJ_PARTICLES(EESSI_ESPRESSO):
    scale = parameter(filter_scales())
    time_limit = '300m'

    executable = 'python3 lj.py'

    @run_after('init')
    def set_tag_ci(self):
        """ Setting tests under CI tag. """
        if SCALES[self.scale]['num_nodes'] < 2:
            self.tags.add('CI')
            log(f'tags set to {self.tags}')

        self.tags.add('particles_lj')

    @run_after('init')
    def set_executable_opts(self):
        """Allow executable opts to be overwritten from command line"""
        num_default = 0  # If this test already has executable opts, they must have come from the command line
        hooks.check_custom_executable_opts(self, num_default=num_default)

    @run_after('setup')
    def set_mem(self):
        """ Setting an extra job option of memory. Here the assumption made is that HPC systems will contain at
        least 1 GB per core of memory. LJ requires much lesser memory than P3M. 200 MB per core is as per measurement,
        therefore 300 should be more than enough. """
        mem_required_per_node = self.num_tasks_per_node * 0.3
        hooks.req_memory_per_node(test=self, app_mem_req=mem_required_per_node * 1024)

    @deferrable
    def assert_completion(self):
        '''Check completion'''
        return (sn.assert_found(r'^Algorithm executed.', self.stdout))

    @deferrable
    def assert_convergence(self):
        '''Check convergence'''
        check_string = False
        energy = 0.0
        check_string = sn.assert_found(r'Final convergence met with relative tolerances:', self.stdout)
        energy = sn.extractsingle(r'^\s+sim_energy:\s+(?P<energy>\S+)', self.stdout, 'energy', float)
        return (check_string and (energy != 0.0))
