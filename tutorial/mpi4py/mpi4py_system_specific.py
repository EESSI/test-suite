"""
This module tests mpi4py's MPI_Reduce call
"""

import reframe as rfm
import reframe.utility.sanity as sn

# added only to make the linter happy
from reframe.core.builtins import variable, parameter, run_after, performance_function, sanity_function


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
    module_name = parameter(['mpi4py/3.1.4-gompi-2023a', 'mpi4py/3.1.5-gompi-2023b'])

    # ReFrame will generate a test for each scale
    scale = parameter([2, 128, 256])

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

    # Define a time limit for the scheduler running this test
    # https://reframe-hpc.readthedocs.io/en/stable/regression_test_api.html#reframe.core.pipeline.RegressionTest.time_limit
    time_limit = '5m00s'

    # Using this decorator, we tell ReFrame to run this AFTER the init step of the test
    # https://reframe-hpc.readthedocs.io/en/stable/regression_test_api.html#reframe.core.builtins.run_after
    # See https://reframe-hpc.readthedocs.io/en/stable/pipeline.html for all steps in the pipeline
    # that reframe uses to execute tests. Note that after the init step, ReFrame has generated test instances for each
    # of the combinations of parameters above. Thus, now, there are 6 instances (2 module names * 3 scales). Here,
    # we set the modules to load equal to one of the module names
    # https://reframe-hpc.readthedocs.io/en/stable/regression_test_api.html#reframe.core.pipeline.RegressionTest.modules
    @run_after('init')
    def set_modules(self):
        self.modules = [self.module_name]

    # Similar for the scale, we now set the number of tasks equal to the scale for this instance
    @run_after('init')
    def define_task_count(self):
        # Set the number of tasks, self.scale is now a single number out of the parameter list
        # https://reframe-hpc.readthedocs.io/en/stable/regression_test_api.html#reframe.core.pipeline.RegressionTest.num_tasks
        self.num_tasks = self.scale
        # Set the number of tasks per node to either be equal to the number of tasks, but at most 128,
        # since we have 128-core nodes
        # https://reframe-hpc.readthedocs.io/en/stable/regression_test_api.html#reframe.core.pipeline.RegressionTest.num_tasks_per_node
        self.num_tasks_per_node = min(self.num_tasks, 128)

    # Now, we check if the pattern 'Sum of all ranks: X' with X the correct sum for the amount of ranks is found
    # in the standard output:
    # https://reframe-hpc.readthedocs.io/en/stable/regression_test_api.html#reframe.core.builtins.sanity_function
    @sanity_function
    def validate(self):
        # Sum of 0, ..., N-1 is (N * (N-1) / 2)
        sum_of_ranks = round(self.num_tasks * ((self.num_tasks - 1) / 2))
        # https://reframe-hpc.readthedocs.io/en/stable/deferrable_functions_reference.html#reframe.utility.sanity.assert_found
        return sn.assert_found(r'Sum of all ranks: %s' % sum_of_ranks, self.stdout)

    # Now, we define a pattern to extract a number that reflects the performance of this test
    # https://reframe-hpc.readthedocs.io/en/stable/regression_test_api.html#reframe.core.builtins.performance_function
    @performance_function('s')
    def time(self):
        # https://reframe-hpc.readthedocs.io/en/stable/deferrable_functions_reference.html#reframe.utility.sanity.extractsingle
        return sn.extractsingle(r'^Time elapsed:\s+(?P<perf>\S+)', self.stdout, 'perf', float)
