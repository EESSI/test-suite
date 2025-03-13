"""
This module tests TensorFlow in available modules containing substring 'TensorFlow'.
The test itself is based on an official multi-worker with Keras tutoral at
https://www.tensorflow.org/tutorials/distribute/multi_worker_with_keras
"""

import reframe as rfm
from reframe.core.builtins import deferrable, parameter, run_after, sanity_function, performance_function
import reframe.utility.sanity as sn

from eessi.testsuite import utils
from eessi.testsuite.constants import COMPUTE_UNITS, DEVICE_TYPES
from eessi.testsuite.eessi_mixin import EESSI_Mixin


@rfm.simple_test
class EESSI_TensorFlow(rfm.RunOnlyRegressionTest, EESSI_Mixin):

    # Parameterize over all modules that start with TensorFlow
    module_name = parameter(utils.find_modules('TensorFlow'))

    # Make CPU and GPU versions of this test
    device_type = parameter([DEVICE_TYPES.CPU, DEVICE_TYPES.GPU])

    executable = 'python tf_test.py'
    readonly_files = ['mnist_setup.py', 'tf_test.py']

    time_limit = '30m'

    # This test should be run as part of EESSI CI
    bench_name = bench_name_ci = 'bench_ci'

    readonly_files = ['mnist_setup.py', 'tf_test.py']

    def required_mem_per_node(self):
        return self.num_tasks_per_node * 2048

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

        return sn.assert_eq(n_fit_completed, self.num_tasks)

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
    def set_executable_opts(self):
        """Set executable opts based on device_type parameter"""
        self.executable_opts += ['--device', self.device_type]
        utils.log(f'executable_opts set to {self.executable_opts}')

    @run_after('init')
    def set_test_descr(self):
        self.descr = f'TensorFlow benchmark on {self.device_type}'

    @run_after('init')
    def set_compute_unit(self):
        """
        Set the compute unit to which tasks will be assigned:
        one task per CPU socket for CPU runs, and one task per GPU for GPU runs.
        """
        device_to_compute_unit = {
            DEVICE_TYPES.CPU: COMPUTE_UNITS.CPU_SOCKET,
            DEVICE_TYPES.GPU: COMPUTE_UNITS.GPU,
        }
        self.compute_unit = device_to_compute_unit.get(self.device_type)

    @run_after('setup')
    def set_thread_count_args(self):
        """Set executable opts defining the thread count"""
        self.executable_opts += ['--intra-op-parallelism', '%s' % self.num_cpus_per_task]
        self.executable_opts += ['--inter-op-parallelism', '1']
        utils.log(f'executable_opts set to {self.executable_opts}')
