"""
This module tests TensorFlow in available modules containing substring 'TensorFlow'.
The test itself is based on an official multi-worker with Keras tutoral at
https://www.tensorflow.org/tutorials/distribute/multi_worker_with_keras
"""

import reframe as rfm
import reframe.utility.sanity as sn

from eessi_utils import hooks, utils
from eessi_utils.constants import DEVICES, SCALES, TAGS

@rfm.simple_test
class TENSORFLOW_EESSI(rfm.RunOnlyRegressionTest):

    # This test can run at any scale, so parameterize over all known SCALES
    scale = parameter(SCALES.keys())
    valid_prog_environs = ['default']
    valid_systems = []

    # Parameterize over all modules that start with TensorFlow
    module_name = parameter(utils.find_modules('TensorFlow'))

    # Make CPU and GPU versions of this test
    device_type = parameter(['cpu', 'gpu'])

    executable = 'python tf_test.py'

    time_limit = '30m'

    # This test should be run as part of EESSI CI
    tags = {TAGS['CI']}

    @deferrable
    def assert_tf_config_ranks(self):
        '''Assert that each rank sets a TF_CONFIG'''
        n_ranks = sn.count(sn.extractall('^Set TF_CONFIG for rank (?P<rank>[0-9]+)', self.stdout, tag='rank'))
        return sn.assert_eq(n_ranks, self.num_tasks)

    @deferrable
    def assert_completion(self):
        '''Assert that the test ran until completion'''
        n_completed_steps = sn.count(sn.extractall('^100/100', self.stdout))
        n_completed_epochs = sn.count(sn.extractall('^Epoch 10/10', self.stdout))
        n_fit_completed = sn.count(sn.extractall('^Keras fit completed', self.stdout))
        
        return sn.all([
            sn.assert_eq(n_completed_steps, 10 * self.num_tasks),
            sn.assert_eq(n_completed_epochs, self.num_tasks),
            sn.assert_eq(n_fit_completed, self.num_tasks),
        ])

    @deferrable
    def assert_convergence(self):
        '''Assert that the network learned _something_ during training'''
        accuracy=sn.extractsingle('^Final accuracy: (?P<accuracy>\S+)', self.stdout, 'accuracy', float)
        return sn.assert_gt(accuracy, 0.5)

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
        """hooks to run after the init phase"""
        hooks.filter_valid_systems_by_device_type(self, required_device_type=self.device_type)
        hooks.set_modules(self)
        hooks.set_tag_scale(self)

    @run_after('init')
    def set_executable_opts(self):
        """Set executable opts based on device_type parameter"""
        num_default = 0  # If this test already has executable opts, they must have come from the command line
        hooks.check_custom_executable_opts(self, num_default=num_default)
        if not self.has_custom_executable_opts:
            self.executable_opts += ['--device', self.device_type]

    @run_after('init')
    def set_test_descr(self):
        self.descr = f'TensorFlow benchmark on {self.device_type}'


    @run_after('setup')
    def run_after_setup(self):
        """hooks to run after the setup phase"""
        # TODO: implement
        # It should bind to socket, but different MPIs may have different arguments to do that...
        # We should at very least prevent that it binds to single core per process, as that results in many threads being scheduled to one core
        # binding may also differ per launcher used. It'll be hard to support a wide range and still get proper binding
        if self.device_type == 'cpu':
            hooks.assign_one_task_per_compute_unit(test=self, compute_unit=DEVICES['CPU_SOCKET'])
        elif self.device_type == 'gpu':
            hooks.assign_one_task_per_compute_unit(test=self, compute_unit=DEVICES['GPU'])
        else:
            raise NotImplementedError(f'Failed to set number of tasks and cpus per task for device {self.device_type}')

        # For now, we hardcode so we can at least have a minimal test run
        #self.num_tasks = 2
        #self.num_tasks_per_node = 2
        #self.num_cpus_per_task = 64

    @run_after('setup')
    def set_binding_policy(self):
        """Set a binding policy"""
        if self.current_partition.processor.num_sockets:
            num_cpus_per_socket = self.max_avail_cpus_per_node / self.current_partition.processor.num_sockets
            # Does a single task fit in a socket? If so, bind to socket
            if self.num_cpus_per_task <= num_cpus_per_socket and self.num_cpus_per_task > 1:
                # Should do binding for intel and OpenMPI's mpirun, and srun
                # Other launchers may or may not do the correct binding
                self.env_vars['I_MPI_PIN_DOMAIN'] = 'socket'
                self.env_vars['OMPI_MCA_hwloc_base_binding_policy'] = 'socket'
                self.env_vars['SLURM_CPU_BIND'] = 'socket'  # Only effective if the task/affinity plugin is enabled

    @run_after('setup')
    def set_omp_num_threads(self):
        """Set number of OpenMP threads"""
        self.env_vars['OMP_NUM_THREADS'] = self.num_cpus_per_task
