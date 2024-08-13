"""
This module tests mpi4py's MPI_Reduce call
"""

import reframe as rfm
import reframe.utility.sanity as sn

from reframe.core.builtins import variable, parameter, run_after  # added only to make the linter happy

from eessi.testsuite import hooks
from eessi.testsuite.constants import SCALES, COMPUTE_UNIT, CPU
from eessi.testsuite.utils import find_modules

# This python decorator indicates to ReFrame that this class defines a test
# Our class inherits from rfm.RunOnlyRegressionTest, since this test does not have a compilation stage
# https://reframe-hpc.readthedocs.io/en/stable/regression_test_api.html#reframe.core.pipeline.RunOnlyRegressionTest
@rfm.simple_test
class EESSI_MPI4PY(rfm.RunOnlyRegressionTest):
    # Programming environments are only relevant for tests that compile something
    # Since we are testing existing modules, we typically don't compile anything and simply define
    # 'default' as the valid programming environment
    # https://reframe-hpc.readthedocs.io/en/stable/regression_test_api.html#reframe.core.pipeline.RegressionTest.valid_prog_environs
    valid_prog_environs = ['default']

    # Typically, we list here the name of our cluster as it is specified in our ReFrame configuration file
    # https://reframe-hpc.readthedocs.io/en/stable/regression_test_api.html#reframe.core.pipeline.RegressionTest.valid_systems
    valid_systems = ['snellius']

    # ReFrame will generate a test for each module
    # https://reframe-hpc.readthedocs.io/en/stable/regression_test_api.html#reframe.core.builtins.parameter
    module_name = parameter(find_modules('mpi4py'))

    # ReFrame will generate a test for each scale
    scale = parameter(SCALES.keys())

    # Our script has two arguments, --n_iter and --n_warmup. By defining these as ReFrame variables, we can
    # enable the end-user to overwrite their value on the command line when invoking ReFrame.
    # Note that we don't typically expose ALL variables, especially if a script has many - we expose
    # only those that we think an end-user might want to overwrite
    # Number of iterations to run (more iterations takes longer, but results in more accurate timing)
    # https://reframe-hpc.readthedocs.io/en/stable/regression_test_api.html#reframe.core.builtins.variable
    n_iterations = variable(int, value=1000)

    # Similar for the number of warmup iterations
    n_warmup = variable(int, value=100)

    # Define which executable to run
    # https://reframe-hpc.readthedocs.io/en/stable/regression_test_api.html#reframe.core.pipeline.RegressionTest.executable
    executable = 'python3'

    # Define which options to pass to the executable
    # https://reframe-hpc.readthedocs.io/en/stable/regression_test_api.html#reframe.core.pipeline.RegressionTest.executable_opts
    executable_opts = ['mpi4py_reduce.py', '--n_iter', f'{n_iterations}', '--n_warmup', f'{n_warmup}']

    # Temporarily define postrun_cmds to make it easy to find out memory useage
    postrun_cmds = ['MAX_MEM_IN_BYTES=$(cat /sys/fs/cgroup/memory/$(</proc/self/cpuset)/memory.max_usage_in_bytes)', 'echo "MAX_MEM_IN_BYTES=$MAX_MEM_IN_BYTES"', 'echo "MAX_MEM_IN_MIB=$(($MAX_MEM_IN_BYTES/1048576))"']

    # Define a time limit for the scheduler running this test
    # https://reframe-hpc.readthedocs.io/en/stable/regression_test_api.html#reframe.core.pipeline.RegressionTest.time_limit
    time_limit = '5m00s'

    @run_after('init')
    def set_modules(self):
        hooks.set_modules(self)

    # Using this decorator, we tell ReFrame to run this AFTER the init step of the test
    # https://reframe-hpc.readthedocs.io/en/stable/regression_test_api.html#reframe.core.builtins.run_after
    # See https://reframe-hpc.readthedocs.io/en/stable/pipeline.html for all steps in the pipeline
    # that reframe uses to execute tests. 
    @run_after('init')
    def run_after_init(self):
        hooks.set_tag_scale(self)

    @run_after('setup')
    def set_num_tasks_per_node(self):
        """ Setting number of tasks per node and cpus per task in this function. This function sets num_cpus_per_task
        for 1 node and 2 node options where the request is for full nodes."""
        hooks.assign_tasks_per_compute_unit(self, COMPUTE_UNIT[CPU])

    # Make sure we request sufficient memory from the scheduler
    @run_after('setup')
    def request_mem(self):
        mem_required = self.num_tasks_per_node * 256
        hooks.req_memory_per_node(self, app_mem_req=mem_required)

    # Set binding strategy
    @run_after('setup')
    def set_binding(self):
        hooks.set_compact_process_binding(self)

    # Now, we check if the pattern 'Sum of all ranks: X' with X the correct sum for the amount of ranks is found
    # in the standard output:
    # https://reframe-hpc.readthedocs.io/en/stable/regression_test_api.html#reframe.core.builtins.sanity_function
    @sanity_function
    def validate(self):
        # Sum of 0, ..., N-1 is (N * (N-1) / 2)
        sum_of_ranks = round(self.num_tasks * ((self.num_tasks-1) / 2))
        # https://reframe-hpc.readthedocs.io/en/stable/deferrable_functions_reference.html#reframe.utility.sanity.assert_found
        return sn.assert_found(r'Sum of all ranks: %s' % sum_of_ranks, self.stdout)

    # Now, we define a pattern to extract a number that reflects the performance of this test
    # https://reframe-hpc.readthedocs.io/en/stable/regression_test_api.html#reframe.core.builtins.performance_function
    @performance_function('s')
    def time(self):
        # https://reframe-hpc.readthedocs.io/en/stable/deferrable_functions_reference.html#reframe.utility.sanity.extractsingle
        return sn.extractsingle(r'^Time elapsed:\s+(?P<perf>\S+)', self.stdout, 'perf', float)

    @performance_function('MiB')
    def max_mem_in_mib(self):
        return sn.extractsingle(r'^MAX_MEM_IN_MIB=(?P<perf>\S+)', self.stdout, 'perf', int)
