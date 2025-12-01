"""
This module tests mpi4py's MPI_Reduce call
"""

import reframe as rfm
import reframe.utility.sanity as sn

# added only to make the linter happy
from reframe.core.builtins import variable, parameter, performance_function, sanity_function

# Import the EESSI_Mixin class so that we can inherit from it
from eessi.testsuite.eessi_mixin import EESSI_Mixin
from eessi.testsuite.constants import COMPUTE_UNITS, DEVICE_TYPES, SCALES
from eessi.testsuite.utils import find_modules

def filter_singlenode_scales():
    """
    Filtering function that makes sure only single node scales are selected,
    since LPC3D is parallelized through OpenMP only.
    """
    return [k for (k, v) in SCALES.items() if v['num_nodes'] == 1]

@rfm.simple_test
class EESSI_LPC3D(rfm.RunOnlyRegressionTest, EESSI_Mixin):

    # LPC3D is only parallelized with OpenMP, so no multi-node tests should be ran
    scale = parameter(filter_singlenode_scales())

    device_type = DEVICE_TYPES.CPU

    # LPC3D is only OpenMP parallel, so launch only one task on a node
    compute_unit = COMPUTE_UNITS.NODE

    # ReFrame will generate a test for each module that matches the regex `mpi4py`
    # This means we implicitly assume that any module matching this name provides the required functionality
    # to run this test
    module_name = parameter(find_modules('LPC3D'))

    readonly_files = ['lattice_gas.inpt', 'pore_dens_freq_2neg.txt', 'psd.txt']

    executable = 'lpc3d'
    executable_opts = ['-i', 'lattice_gas.inpt']
    time_limit = '5m00s'

    is_ci_test = True

    # Define the class method that returns the required memory per node
    def required_mem_per_node(self):
        return self.num_tasks_per_node * 1 + 800

    @deferrable
    def assert_diffusion(self):
        '''Assert that the diffusion coefficient at timestep 1000 matches to within a certain margin'''
        regex = "VACF Diffusion coefficient_1: (?P<diff>\S+)"
        diffusion_coef = sn.extractsingle(regex, self.stdout, 'diff', float)
        # Note that the reference (5088.891) is dependent on the number of iterations
        # This is the reference for 100 iterations. If the iteration count is ever changed, the reference
        # should be updated
        diffusion_coef_diff = sn.abs(diffusion_coef - 5088.891)
        return sn.assert_lt(diffusion_coef_diff, 0.001)

    @sanity_function
    def validate(self):
        # We may want to turn this into an assert_all and check some more numbers later
        # For now, just check the diffusion coefficient
        return sn.assert_true(self.assert_diffusion())

    # Now, we define a pattern to extract a number that reflects the performance of this test
    # https://reframe-hpc.readthedocs.io/en/stable/regression_test_api.html#reframe.core.builtins.performance_function
    @performance_function('s')
    def time(self):
        # https://reframe-hpc.readthedocs.io/en/stable/deferrable_functions_reference.html#reframe.utility.sanity.extractsingle
        return sn.extractsingle(r'^The execution time is (?P<perf>\S+) seconds', self.stdout, 'perf', float)
