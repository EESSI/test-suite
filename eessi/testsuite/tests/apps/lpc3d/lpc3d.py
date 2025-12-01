"""
This module tests mpi4py's MPI_Reduce call
"""

import reframe as rfm
import reframe.utility.sanity as sn

# added only to make the linter happy
from reframe.core.builtins import parameter, performance_function, sanity_function, deferrable

# Import the EESSI_Mixin class so that we can inherit from it
from eessi.testsuite.eessi_mixin import EESSI_Mixin
from eessi.testsuite.constants import COMPUTE_UNITS, DEVICE_TYPES, SCALES
from eessi.testsuite.utils import find_modules


def filter_singlenode_scales():
    """
    Filtering function that returns only single node scales.
    """
    return [k for (k, v) in SCALES.items() if v['num_nodes'] == 1]


@rfm.simple_test
class EESSI_LPC3D(rfm.RunOnlyRegressionTest, EESSI_Mixin):
    """
    TODO: insert sensible description of this test case

    LPC3D is an OpenMP parallelized code. As such, this test will only be instantiated on scales up to 1 full node.

    The runtime is in the order of seconds to minutes.

    The input file contains a number of steps on the 9th line. This may be adjusted to adjust the total runtime of
    this test. However, the reference number for the sanity check then also needs to be adjusted.
    """

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
    time_limit = '10m00s'

    is_ci_test = True

    def required_mem_per_node(self):
        """
        Defines the required memory per node to run this test
        """
        return self.num_cpus_per_task * 1 + 800

    @deferrable
    def assert_diffusion(self):
        """
        Assert that the diffusion coefficient at timestep 100 matches to within a certain margin.
        Note that if the number of iterations is changed in the lattice_gas.inpt file, the reference
        for the diffusion coefficient (ref_diffusion_coef) needs to be adjusted.
        """
        regex = r"VACF Diffusion coefficient_1: (?P<diff>\S+)"
        diffusion_coef = sn.extractsingle(regex, self.stdout, 'diff', float)
        ref_diffusion_coef = 5088.891
        diffusion_coef_diff = sn.abs(diffusion_coef - ref_diffusion_coef)
        return sn.assert_lt(diffusion_coef_diff, 0.001)

    @sanity_function
    def validate(self):
        """
        This is the sanity function for this test. Currently, it only checks that assert_diffusion is true,
        but this may be expanded with additional sanity checking if needed.
        """
        return sn.assert_true(self.assert_diffusion())

    @performance_function('s')
    def time(self):
        """
        LPC3D reports total runtime as a performance number. Note that this times an aggregate of both serial
        and parallel sections of the code.
        """
        return sn.extractsingle(r'^The execution time is (?P<perf>\S+) seconds', self.stdout, 'perf', float)
