"""
This module tests mpi4py's MPI_Reduce call
"""

import reframe as rfm
import reframe.utility.sanity as sn

# added only to make the linter happy
from reframe.core.builtins import variable, parameter, performance_function, sanity_function

# Import the EESSI_Mixin class so that we can inherit from it
from eessi.testsuite.eessi_mixin import EESSI_Mixin
from eessi.testsuite.constants import COMPUTE_UNITS, DEVICE_TYPES
from eessi.testsuite.utils import find_modules


# This python decorator indicates to ReFrame that this class defines a test
# Our class inherits from rfm.RunOnlyRegressionTest, since this test does not have a compilation stage
# https://reframe-hpc.readthedocs.io/en/stable/regression_test_api.html#reframe.core.pipeline.RunOnlyRegressionTest
@rfm.simple_test
class EESSI_MPI4PY(rfm.RunOnlyRegressionTest, EESSI_Mixin):

    # The device type makes sure this test only gets executed on systems/partitions that can provide this device
    device_type = DEVICE_TYPES.CPU

    # One task is launched per compute unit. In this case, one task per (physical) CPU core
    compute_unit = COMPUTE_UNITS.CPU

    # ReFrame will generate a test for each module that matches the regex `mpi4py`
    # This means we implicitly assume that any module matching this name provides the required functionality
    # to run this test
    module_name = parameter(find_modules('mpi4py'))

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

    # Define the benchmarks that are available in the test.
    # In this test (`EESSI_MPI4PY`) there is only one benchmark. If there are more than one,
    # define them using the `parameter()` function.
    bench_name = 'mpi4pi'

    # Specify the benchmark to be tested in CI (will be marked with a `CI` tag).
    bench_name_ci = 'mpi4pi'

    # Define the files and/or dirs inside sourcesdir (default=src) that should be symlinked into the stage dir
    readonly_files = ['mpi4py_reduce.py']

    # Define the class method that returns the required memory per node
    def required_mem_per_node(self):
        return self.num_tasks_per_node * 100 + 250

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
