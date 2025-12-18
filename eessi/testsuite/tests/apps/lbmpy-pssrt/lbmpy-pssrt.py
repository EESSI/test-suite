"""
This module tests an lbmpy fork twith additional functionality added within the MultiXscale project.
Long term, the goal is that this will be upstreamed in lbmpy.
"""

import reframe as rfm
import reframe.utility.sanity as sn

# added only to make the linter happy
from reframe.core.builtins import parameter, performance_function, sanity_function, deferrable, run_after

# Import the EESSI_Mixin class so that we can inherit from it
from eessi.testsuite.eessi_mixin import EESSI_Mixin
from eessi.testsuite.constants import COMPUTE_UNITS, DEVICE_TYPES, SCALES
from eessi.testsuite.utils import find_modules
from eessi.testsuite.hooks import set_compact_thread_binding


def filter_singlenode_scales():
    """
    Filtering function that returns only single node scales.
    """
    return [k for (k, v) in SCALES.items() if v['num_nodes'] == 1]


@rfm.simple_test
class EESSI_lbmpy_pssrt(rfm.RunOnlyRegressionTest, EESSI_Mixin):
    """
    This test case simulates the Kelvin-Helmholtz instabilty where an initial hyperbolic tangent velocity profile
    imposed in a fully periodic 2D square box is slightly perturbed to initiate rolling of the shear layers.

    This use case tests a modified version of lbmpy, with additional functionality. This test cases uses lbmpy with
    OpenMP parallelization. As such, this test will only be instantiated on scales up to 1 full node.
    The runtime is in the order of seconds to minutes.

    The test script takes three (optional) arguments: --grid-size, --run-time, --openmp.
    If grid-size or run-time are modified, the reference value in the assert_normalized_average_kinetic_energy sanity
    check needs to be updated. The reference does _not_ change with the number of threads.
    """

    # lbmpy-pssrt is only parallelized with OpenMP, so no multi-node tests should be ran
    scale = parameter(filter_singlenode_scales())

    device_type = DEVICE_TYPES.CPU

    # lbmpy-pssrt is only OpenMP parallel, so launch only one task on a node
    compute_unit = COMPUTE_UNITS.NODE

    launcher = 'local'  # no MPI module is loaded in this test

    module_name = parameter(find_modules('lbmpy-pssrt'))

    readonly_files = ['mixing_layer_2D.py']

    executable = 'python'
    # grid-size of 512 seems to scale reasonable to 128 cores, and completes in reasonable time on one core (< 2 mins)
    executable_opts = ['mixing_layer_2D.py', '--grid-size 512']  # 512 seems to scale _reasonable_ to 128 cores
    time_limit = '10m00s'

    is_ci_test = True

    perf_regex = r'^\s+Median±\(max-min\)\s+=\s+(?P<perf>\S+)±(?P<perf_range>\S+)\s+MLUPS'

    def required_mem_per_node(self):
        """
        Defines the required memory per node to run this test
        """
        return self.num_cpus_per_task * 5 + 250

    @deferrable
    def assert_normalized_average_kinetic_energy(self):
        """
        Assert that the normalized average kinetic energy matches the reference (exactly).
        Note that the reference needs to be adjusted if a different --grid-size or --run-time is used.
        It should, however, be robust against changes in the number of threads.
        """
        regex = r"Normalized Average Kinetic Energy\s+=\s+(?P<energy>\S+)"
        energy = sn.extractsingle(regex, self.stdout, 'energy', float)
        ref_energy = 0.9381
        return sn.assert_eq(energy, ref_energy)

    @sanity_function
    def validate(self):
        """
        This is the sanity function for this test. Currently, it only checks that
        assert_normalized_average_kinetic_energy is true, but this may be expanded with additional sanity checking
        if needed.
        """
        return sn.assert_true(self.assert_normalized_average_kinetic_energy())

    @performance_function('MLU/s')
    def lattice_updates(self):
        """
        This test case reports number of Mega lattice updates per second (and a range) over 5 iterations.
        """
        return sn.extractsingle(self.perf_regex, self.stdout, 'perf', float)

    @performance_function('MLU/s')
    def lattice_updates_range(self):
        """
        This test case reports range (max-min) of number of Mega lattice updates per second, over 5 iterations.
        In other words, it takes the difference in Mega lattice updates per seconds between the slowest and the
        fastest iteration
        """
        return sn.extractsingle(self.perf_regex, self.stdout, 'perf_range', float)

    @run_after('setup')
    def set_openmp_argument(self):
        """
        If the number of cpus_per_task is larger than 1, enable OpenMP by setting the --openmp argument.
        Also, set compact thread binding in this case
        """
        if self.num_cpus_per_task > 1:
            self.executable_opts += ['--openmp']
            set_compact_thread_binding(self)
