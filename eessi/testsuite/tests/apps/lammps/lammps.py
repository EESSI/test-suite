"""
This module tests the binary 'lmp' in available modules containing substring 'LAMMPS'.
The tests come from the lammps github repository (https://github.com/lammps/lammps/)
"""

import reframe as rfm
import reframe.utility.sanity as sn

from eessi.testsuite import hooks, utils
from eessi.testsuite.constants import *  # noqa

@rfm.simple_test
class EESSI_LAMMPS(rfm.RunOnlyRegressionTest):
    scale = parameter(SCALES.keys())
    valid_prog_environs = ['default']
    valid_systems = ['*']
    time_limit = '30m'
    tags = {TAGS['CI']}
    device_type = parameter([DEVICE_TYPES[CPU], DEVICE_TYPES[GPU]])

    # Parameterize over all modules that start with LAMMPS
    module_name = parameter(utils.find_modules('LAMMPS'))
    executable = 'lmp -in in.lj'

    # Set sanity step
    # TODO adjust for LAMMPS
    @deferrable
    def assert_tf_config_ranks(self):
        '''Assert that each rank sets a TF_CONFIG'''
        n_ranks = sn.count(sn.extractall(
            '^Rank [0-9]+: Set TF_CONFIG for rank (?P<rank>[0-9]+)', self.stdout, tag='rank'))
        return sn.assert_eq(n_ranks, self.num_tasks)

    @deferrable
    def assert_completion(self):
        '''Assert that the test ran until completion'''
        n_fit_completed = sn.count(sn.extractall('^Rank [0-9]+: Keras fit completed', self.stdout))

        return sn.all([
            sn.assert_eq(n_fit_completed, self.num_tasks),
        ])

    @deferrable
    def assert_convergence(self):
        '''Assert that the network learned _something_ during training'''
        accuracy = sn.extractsingle('^Final accuracy: (?P<accuracy>\S+)', self.stdout, 'accuracy', float)  # noqa: W605
        # mnist is a 10-class classification problem, so if accuracy >> 0.2 the network 'learned' something
        return sn.assert_gt(accuracy, 0.2)

    @sanity_function
    def assert_sanity(self):
        '''Check all sanity criteria'''
        return sn.all([
            self.assert_tf_config_ranks(),
            self.assert_completion(),
            self.assert_convergence(),
        ])

    @performance_function('img/s')
    def perf(self):
        return sn.extractsingle(r'^Performance:\s+(?P<perf>\S+)', self.stdout, 'perf', float)

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
    def run_after_setup(self):
        """hooks to run after the setup phase"""
        # TODO: implement
        # It should bind to socket, but different MPIs may have different arguments to do that...
        # We should at very least prevent that it binds to single core per process,
        # as that results in many threads being scheduled to one core.
        # binding may also differ per launcher used. It'll be hard to support a wide range and still get proper binding
        if self.device_type == 'cpu':
            hooks.assign_tasks_per_compute_unit(test=self, compute_unit=COMPUTE_UNIT['CPU_SOCKET'])
        elif self.device_type == 'gpu':
            hooks.assign_tasks_per_compute_unit(test=self, compute_unit=COMPUTE_UNIT['GPU'])
        else:
            raise NotImplementedError(f'Failed to set number of tasks and cpus per task for device {self.device_type}')

    @run_after('setup')
    def set_omp_num_threads(self):
        """
        Set number of OpenMP threads.
        Set OMP_NUM_THREADS.
        Set default number of OpenMP threads equal to number of CPUs per task.
        """

        omp_num_threads = self.num_cpus_per_task
        self.env_vars['OMP_NUM_THREADS'] = omp_num_threads
        utils.log(f'env_vars set to {self.env_vars}')
